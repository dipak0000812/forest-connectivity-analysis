import logging
from celery import shared_task
from django.db import transaction
from .models import PipelineRun, GEEExportJob
from .gee_utils import submit_mspa_job, check_export_status, make_asset_public
from .geoserver_utils import sync_raster_to_geoserver, sync_vector_to_geoserver

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def compute_mspa_task(self, run_id):
    try:
        run = PipelineRun.objects.get(id=run_id)
        
        # Fast exit if somehow queued weirdly
        if run.state != 'pending':
            return "Already picked up"

        with transaction.atomic():
            run.state = 'computing'
            run.save()

        # Submit jobs to GEE Native Python Wrapper
        try:
            jobs = submit_mspa_job(str(run.id), run.parameters)
        except Exception as e:
            logger.error(f"GEE Submission failed for run {run_id}: {e}")
            run.state = 'failed'
            run.error_message = f"GEE Submission Error: {e}"
            run.save()
            raise self.retry(exc=e)

        with transaction.atomic():
            for j in jobs:
                GEEExportJob.objects.create(
                    run=run,
                    export_type=j['type'],
                    gee_task_id=j['id'],
                    asset_path=j['asset_path']
                )
            run.state = 'exporting'
            run.save()

        return "Submitted"

    except PipelineRun.DoesNotExist:
        logger.error(f"Pipeline Run {run_id} does not exist.")
        return "Non-existent run"

@shared_task
def monitor_exports_task():
    """Periodic task to poll Earth Engine exports and finalize pipelines."""
    # Pick up jobs that are submitted or running
    active_jobs = GEEExportJob.objects.filter(status__in=['submitted', 'RUNNING', 'READY'])
    logger.info(f"Checking {active_jobs.count()} active GEE export jobs...")

    for job in active_jobs:
        run = job.run
        ee_state, error_msg = check_export_status(job.gee_task_id)

        # Update job if state changed
        if ee_state != job.status:
            job.status = ee_state
            job.save()

        # Handle Complete
        if ee_state == 'COMPLETED':
            logger.info(f"GEE Task {job.gee_task_id} COMPLETED. Proceeding to sync to GeoServer.")
            
            make_asset_public(job.asset_path)

            try:
                if job.export_type == 'raster':
                    run.asset_raster_path = job.asset_path
                    sync_raster_to_geoserver(job.asset_path, layer_name=f"mspa_raster_{run.id}")
                    run.geoserver_layer = f"mspa_raster_{run.id}"
                else:
                    run.asset_vector_path = job.asset_path
                    sync_vector_to_geoserver(job.asset_path, layer_name=f"mspa_vector_{run.id}")
            except Exception as e:
                logger.error(f"GeoServer sync failed: {e}")
                run.state = 'failed'
                run.error_message = f"GeoServer sync failed: {e}"
                run.save()
                continue

            run.save()

        # Handle Failure
        elif ee_state in ['FAILED', 'CANCELLED', 'UNKNOWN']:
            logger.error(f"GEE Task {job.gee_task_id} failed: {error_msg}")
            run.state = 'failed'
            run.error_message = f"GEE Task {job.gee_task_id} failed: {error_msg}"
            run.save()

    # Check runs that are exporting to see if they're completely done
    exporting_runs = PipelineRun.objects.filter(state='exporting')
    for run in exporting_runs:
        all_jobs = GEEExportJob.objects.filter(run=run)
        
        # If any job failed, the run is already marked failed above.
        if run.state == 'failed':
            continue
            
        # Check if all jobs are strictly COMPLETED
        if all(j.status == 'COMPLETED' for j in all_jobs):
            run.state = 'publishing'
            run.save()
            run.state = 'done' # We merged publishing into completion step
            run.save()
            logger.info(f"PipelineRun {run.id} successfully completed all tasks.")

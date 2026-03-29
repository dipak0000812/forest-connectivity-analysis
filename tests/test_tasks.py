import pytest
from src.forest_connectivity.tasks import compute_mspa_task, monitor_exports_task
from src.forest_connectivity.models import PipelineRun, GEEExportJob

@pytest.mark.django_db
def test_compute_mspa_task_success(mocker):
    run = PipelineRun.objects.create(state='pending')
    
    mocker.patch('src.forest_connectivity.gee_utils.submit_mspa_job', return_value=[
        {'type': 'raster', 'id': 'geetask123', 'asset_path': 'foo'},
        {'type': 'vector', 'id': 'geetask456', 'asset_path': 'bar'}
    ])
    
    res = compute_mspa_task(str(run.id))
    
    assert res == "Submitted"
    run.refresh_from_db()
    assert run.state == 'exporting'
    assert GEEExportJob.objects.count() == 2

@pytest.mark.django_db
def test_monitor_exports_task_completion(mocker):
    run = PipelineRun.objects.create(state='exporting')
    job1 = GEEExportJob.objects.create(run=run, gee_task_id='t1', status='submitted', export_type='raster')
    job2 = GEEExportJob.objects.create(run=run, gee_task_id='t2', status='submitted', export_type='vector')
    
    mocker.patch('src.forest_connectivity.gee_utils.check_export_status', return_value=('COMPLETED', ''))
    mocker.patch('src.forest_connectivity.gee_utils.make_asset_public')
    mocker.patch('src.forest_connectivity.geoserver_utils.sync_raster_to_geoserver')
    mocker.patch('src.forest_connectivity.geoserver_utils.sync_vector_to_geoserver')

    monitor_exports_task()
    
    run.refresh_from_db()
    assert run.state == 'done'

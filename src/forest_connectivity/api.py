import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
# Use simple throttle mapping to drf limits
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from .models import PipelineRun
from django.conf import settings
from .serializers import ForestConnectivityRequestSerializer, PipelineRunSerializer
from .tasks import compute_mspa_task
from django.db import transaction

logger = logging.getLogger(__name__)

class BurstRateThrottle(UserRateThrottle):
    rate = '100/min'

class ForestConnectivityView(APIView):
    """
    POST /api/v1/forest-connectivity/
    Trigger a new MSPA connectivity analysis.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = ForestConnectivityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        params = serializer.validated_data
        
        with transaction.atomic():
            # Idempotency Check
            # Prevent race conditions with select_for_update()
            # Does a pipeline exactly matching these params exist that didn't fail?
            existing_run = PipelineRun.objects.select_for_update().filter(
                parameters__state=params['state'],
                parameters__district=params['district'],
                parameters__block=params['block'],
                parameters__lulc_year=params['lulc_year']
            ).exclude(state='failed').first()

            if existing_run:
                logger.info(f"Idempotency hit - returning run ID {existing_run.id}")
                return Response({
                    "task_id": str(existing_run.id),
                    "status_url": f"/api/v1/forest-connectivity/{existing_run.id}/",
                    "status": existing_run.state,
                    "message": "Found existing execution for these parameters."
                }, status=status.HTTP_200_OK)

            # Create new Pipeline Run
            # Remove notify_email from parameters dict so we don't index PII blindly
            # though standard JSONb is fine, we just pass what's needed for analysis to the parameter blob.
            run = PipelineRun.objects.create(parameters=params)
        
        # Enqueue Task
        compute_mspa_task.delay(str(run.id))
        
        return Response({
            "task_id": str(run.id),
            "status_url": f"/api/v1/forest-connectivity/{run.id}/",
            "status": "queued"
        }, status=status.HTTP_202_ACCEPTED)

class ForestConnectivityDetailView(APIView):
    """
    GET /api/v1/forest-connectivity/<task_id>/
    Gets the state of a running analysis or the assets if completed.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id, *args, **kwargs):
        run = get_object_or_404(PipelineRun, id=task_id)
        serializer = PipelineRunSerializer(run)
        
        response_data = serializer.data
        
        # Format the response specifically as defined in architectural docs
        output = {
            "task_id": str(run.id),
            "status": run.state,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat()
        }
        
        if run.state == 'done':
            output['assets'] = {
                "raster": run.asset_raster_path,
                "vector": run.asset_vector_path
            }
            # Append gs data if published
            # Simplified layer URLs construction:
            gs_url = getattr(settings, 'GEOSERVER_URL', 'http://geoserver/wms').replace('/rest', '')
            workspace = getattr(settings, 'GEOSERVER_WORKSPACE', 'corestack')
            if run.geoserver_layer:
                output['geoserver_layers'] = {
                    "wms": f"{gs_url}/{workspace}/wms?layers={run.geoserver_layer}",
                    "wfs": f"{gs_url}/{workspace}/wfs?typeName={run.geoserver_layer}"
                }
                
        if run.state == 'failed':
            output['error'] = run.error_message
            
        return Response(output, status=status.HTTP_200_OK)

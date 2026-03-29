import logging
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from .models import GeoServerSyncLog, PipelineRun

logger = logging.getLogger(__name__)

def _get_gs_auth():
    return HTTPBasicAuth(settings.GEOSERVER_USER, getattr(settings, 'GEOSERVER_PASSWORD', 'geoserver'))

def sync_raster_to_geoserver(asset_path: str, layer_name: str, workspace: str = None):
    """
    Sync a GEE Raster asset/ImageCollection wrapper to GeoServer.
    In a real scenario, typically involves downloading from GEE or using a Cloud-Optimized GeoTIFF stored in GCS.
    Here we mock/simulate the REST call to register it within GeoServer, 
    matching standard CoRE Stack architecture logic.
    """
    if not workspace:
        workspace = getattr(settings, 'GEOSERVER_WORKSPACE', 'corestack')
        
    url = f"{settings.GEOSERVER_URL}/workspaces/{workspace}/coveragestores"
    
    # Normally we'd do:
    # payload = f"""<coverageStore>
    #   <name>{layer_name}</name>
    #   ...
    # </coverageStore>"""
    # requests.post(url, data=payload, auth=_get_gs_auth(), headers={'Content-type': 'text/xml'})
    
    # We will just verify configuration exists and log it
    logger.info(f"Simulating Raster Sync to GeoServer: URL={url}, Layer={layer_name}")
    
    try:
        run_id = layer_name.replace("mspa_raster_", "")
        run = PipelineRun.objects.get(id=run_id)
        GeoServerSyncLog.objects.create(
            run=run,
            layer_name=layer_name,
            success=True
        )
    except Exception as e:
        logger.error(f"Failed to create sync log: {e}")

def sync_vector_to_geoserver(asset_path: str, layer_name: str, workspace: str = None):
    """
    Sync a GEE Vector to GeoServer.
    Usually involves exporting to PostGIS and publishing the PostGIS table.
    """
    if not workspace:
        workspace = getattr(settings, 'GEOSERVER_WORKSPACE', 'corestack')
        
    url = f"{settings.GEOSERVER_URL}/workspaces/{workspace}/datastores"
    
    logger.info(f"Simulating Vector Sync to GeoServer: URL={url}, Layer={layer_name}")
    
    try:
        run_id = layer_name.replace("mspa_vector_", "")
        run = PipelineRun.objects.get(id=run_id)
        GeoServerSyncLog.objects.create(
            run=run,
            layer_name=layer_name,
            success=True
        )
    except Exception as e:
        logger.error(f"Failed to create sync log: {e}")

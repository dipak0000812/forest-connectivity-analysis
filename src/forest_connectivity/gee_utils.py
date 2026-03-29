import os
import json
import uuid
import logging
import ee
from django.conf import settings

logger = logging.getLogger(__name__)

def ee_initialize():
    """Initialize Earth Engine with Service Account"""
    # Prefer explicit credentials for production
    if getattr(settings, 'GEE_SERVICE_ACCOUNT', None) and getattr(settings, 'GEE_PRIVATE_KEY', None):
        credentials = ee.ServiceAccountCredentials(
            settings.GEE_SERVICE_ACCOUNT,
            key_data=settings.GEE_PRIVATE_KEY
        )
        ee.Initialize(credentials)
    else:
        # Fallback for local development via browser auth
        try:
            ee.Initialize()
        except Exception:
            try:
                # Need to run `earthengine authenticate` in CLI beforehand
                ee.Initialize()
            except Exception as e:
                logger.error(f"Failed to initialize Earth Engine: {e}")
                raise

def get_aoi_for_block(state: str, district: str, block: str) -> ee.Geometry:
    """Mock database lookup for geometries, maps identifiers to Earth Engine Geometries."""
    # In a real deployed CoRE Stack, we would query the spatial DB.
    # We will use Saranda default if exact matches aren't configured yet.
    logger.info(f"Looking up AOI for {state}, {district}, {block}")
    if block.lower() == 'kanke':
        return ee.Geometry.Rectangle([85.25, 23.35, 85.45, 23.55])
    return ee.Geometry.Rectangle([85.1, 22.2, 85.5, 22.5]) # Saranda default

def submit_mspa_job(run_id, params: dict):
    """
    Submits MSPA analysis to GEE natively using Python API port of the JS script.
    """
    ee_initialize()
    
    # Configuration
    lulc_year = params.get('lulc_year', '2023_2024')
    edge_width_m = params.get('edge_width_m', 100)
    edge_width_px = edge_width_m / 30.0 # Convert meters to pixels at 30m resolution
    max_islet_area_ha = params.get('islet_area_ha', 1.0) # max size for an isolated core
    max_islet_px = int((max_islet_area_ha * 10000) / 900) # Area config to pixels
    
    # Setup Paths
    prefix = 'projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_'
    asset_path = f"{prefix}{lulc_year}"
    
    aoi = get_aoi_for_block(params.get('state'), params.get('district'), params.get('block'))
    
    # Build Logic
    lulc = ee.Image(asset_path).clip(aoi).rename('lulc')
    forestMask = lulc.eq(6).byte().rename('forest_mask')
    
    distance = forestMask.fastDistanceTransform(
        neighborhood=256, units='pixels', metric='squared_euclidean'
    ).sqrt()
    
    core = distance.gte(edge_width_px).And(forestMask.eq(1)).rename('core')
    
    background = forestMask.Not()
    connectedBgPixels = background.connectedPixelCount(maxSize=550, eightConnected=True)
    holes = background.And(connectedBgPixels.lt(550)).rename('holes')
    external = background.And(connectedBgPixels.gte(550)).rename('external')
    
    distExternal = external.fastDistanceTransform(neighborhood=256, units='pixels', metric='squared_euclidean').sqrt()
    distHoles = holes.fastDistanceTransform(neighborhood=256, units='pixels', metric='squared_euclidean').sqrt()
    
    edgeCandidate = forestMask.eq(1).And(core.Not()).And(distExternal.lt(edge_width_px))
    perfCandidate = forestMask.eq(1).And(core.Not()).And(distHoles.lt(edge_width_px))
    
    edge = edgeCandidate.rename('edge')
    perforation = perfCandidate.And(edge.Not()).rename('perforation')
    
    forestPatches = forestMask.connectedComponents(connectedness=ee.Kernel.plus(1), maxSize=max_islet_px)
    img_for_reduction = core.addBands(forestPatches.select('labels'))
    patchHasCore = img_for_reduction.reduceConnectedComponents(reducer=ee.Reducer.max(), labelBand='labels')
    islet = forestMask.eq(1).And(patchHasCore.Not()).rename('islet')
    
    mspa = ee.Image(0).uint8()           # uint8 not byte() — consistent with JS
    mspa = mspa.where(edge, 2)           # Edge        = 2
    mspa = mspa.where(perforation, 3)    # Perforation = 3  (unchanged)
    mspa = mspa.where(core, 4)           # Core        = 4
    mspa = mspa.where(islet, 1)          # Islet       = 1
    # Bridge and Branch are Phase 3 — leave as 0 (background)
    mspa = mspa.updateMask(forestMask).rename('mspa_class')
    
    # Vectorization
    mspaVectors = mspa.reduceToVectors(
        geometry=aoi,
        scale=30,
        geometryType='polygon',
        eightConnected=True,           # 8-connected — matches gee/mspa_analyzer.js
        labelProperty='mspa_class',
        maxPixels=1e13
    )
    
    # Output assets path configuration
    raster_asset = f"projects/{settings.GEE_PROJECT_ID}/assets/mspa_raster_{run_id}"
    vector_asset = f"projects/{settings.GEE_PROJECT_ID}/assets/mspa_vector_{run_id}"
    
    # Trigger Tasks
    task_raster = ee.batch.Export.image.toAsset(
        image=mspa,
        description=f'MSPA_Raster_{run_id}',
        assetId=raster_asset,
        region=aoi,
        scale=30,
        maxPixels=1e13
    )
    task_raster.start()
    
    task_vector = ee.batch.Export.table.toAsset(
        collection=mspaVectors,
        description=f'MSPA_Vector_{run_id}',
        assetId=vector_asset
    )
    task_vector.start()
    
    logger.info(f"Submitted GEE tasks for run_id {run_id}: Raster={task_raster.id}, Vector={task_vector.id}")
    
    return [
        {"type": "raster", "id": task_raster.id, "asset_path": raster_asset},
        {"type": "vector", "id": task_vector.id, "asset_path": vector_asset}
    ]

def check_export_status(gee_task_id: str):
    """Checks the status of a specific earth engine task ID."""
    ee_initialize()
    status = ee.data.getTaskStatus(gee_task_id)
    if not status or len(status) == 0:
        return 'UNKNOWN', 'Task not found'
    state = status[0].get('state', 'UNKNOWN')
    error_msg = status[0].get('error_message', '')
    return state, error_msg

def make_asset_public(asset_path: str):
    """Make a GEE asset publicly readable."""
    ee_initialize()
    try:
        acl = {"all_users_can_read": True}
        ee.data.setAssetAcl(asset_path, acl)
        logger.info(f"Asset made public: {asset_path}")
        return True
    except Exception as e:
        logger.warning(f"Could not set asset ACL (may need owner permissions): {e}")
        return False

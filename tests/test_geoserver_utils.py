import pytest
from unittest.mock import patch
from src.forest_connectivity.geoserver_utils import sync_raster_to_geoserver
from src.forest_connectivity.models import PipelineRun, GeoServerSyncLog
import uuid

@pytest.mark.django_db
def test_sync_raster():
    run = PipelineRun.objects.create()
    
    with patch('src.forest_connectivity.geoserver_utils.requests.post') as mock_post:
        mock_post.return_value.status_code = 201
        
        sync_raster_to_geoserver("test/path", f"mspa_raster_{run.id}")
        
    assert GeoServerSyncLog.objects.filter(run=run).exists()

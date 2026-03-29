import pytest
from unittest.mock import MagicMock
from src.forest_connectivity.gee_utils import check_export_status

def test_check_export_status(mocker):
    # Mockee 'ee_initialize'
    mocker.patch('src.forest_connectivity.gee_utils.ee_initialize')
    
    mock_ee_data = mocker.patch('src.forest_connectivity.gee_utils.ee.data')
    mock_ee_data.getTaskStatus.return_value = [{'state': 'RUNNING'}]
    
    status, err = check_export_status("task1")
    assert status == 'RUNNING'
    assert err == ''

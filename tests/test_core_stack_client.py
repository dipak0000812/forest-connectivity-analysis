import pytest
from unittest.mock import Mock, patch
from src.core_stack_client import CoreStackClient

def test_client_initialization():
    client = CoreStackClient(api_key="test_key_123")
    assert client.api_key == "test_key_123"
    assert "Bearer test_key_123" in client.headers["Authorization"]

@patch('requests.get')
def test_get_available_locations(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "states": ["Jharkhand", "Odisha"]
    }
    mock_get.return_value = mock_response
    
    client = CoreStackClient(api_key="test_key")
    result = client.get_available_locations()
    
    assert "states" in result
    assert "Jharkhand" in result["states"]
    
@patch('requests.get')
def test_get_lulc_metadata_fallback(mock_get):
    # Simulate API failure
    mock_get.side_effect = Exception("Connection Refused")
    
    client = CoreStackClient(api_key="test_key")
    metadata = client.get_lulc_metadata()
    
    assert "classes" in metadata
    assert metadata["version"] == "2025-12"
    assert 1 in metadata["classes"]

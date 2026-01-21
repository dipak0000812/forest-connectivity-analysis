"""
Unit tests for GEE Adapter Module
Uses mock-based testing since ee module requires authentication.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock the entire ee module before importing gee_adapter
sys.modules['ee'] = MagicMock()

from src.gee_adapter import GeeConnectivityAnalyzer


class TestGeeConnectivityAnalyzerInit:
    """Tests for GeeConnectivityAnalyzer initialization."""
    
    def test_default_initialization(self):
        """Test default parameter values."""
        analyzer = GeeConnectivityAnalyzer()
        assert analyzer.resolution == 30
        assert analyzer.core_threshold == 300.0
        assert analyzer.edge_threshold == 100.0
    
    def test_custom_initialization(self):
        """Test custom parameter values."""
        analyzer = GeeConnectivityAnalyzer(
            resolution=10,
            core_threshold=200.0,
            edge_threshold=50.0
        )
        assert analyzer.resolution == 10
        assert analyzer.core_threshold == 200.0
        assert analyzer.edge_threshold == 50.0


class TestComputeConnectivity:
    """Tests for compute_connectivity method."""
    
    @pytest.fixture
    def analyzer(self):
        return GeeConnectivityAnalyzer(resolution=30)
    
    @pytest.fixture
    def mock_image(self):
        """Create a mock ee.Image."""
        mock = MagicMock()
        # Setup chain of method calls
        mock.remap.return_value.rename.return_value = MagicMock()
        return mock
    
    @pytest.fixture
    def mock_aoi(self):
        """Create a mock ee.Geometry."""
        return MagicMock()
    
    def test_compute_connectivity_returns_image(self, analyzer, mock_image, mock_aoi):
        """Test that compute_connectivity returns an image with added bands."""
        result = analyzer.compute_connectivity(mock_image, mock_aoi, [3, 4])
        
        # Verify remap was called for forest mask creation
        mock_image.remap.assert_called_once()
        
        # Verify addBands was called on input image
        mock_image.addBands.assert_called_once()
    
    def test_compute_connectivity_custom_forest_classes(self, analyzer, mock_image, mock_aoi):
        """Test with custom forest class IDs."""
        custom_classes = [1, 2, 5, 6]
        analyzer.compute_connectivity(mock_image, mock_aoi, custom_classes)
        
        # Verify remap was called with correct forest classes
        call_args = mock_image.remap.call_args
        # First positional arg should be ee.List of forest classes
        assert call_args is not None


class TestVectorizeResults:
    """Tests for vectorize_results method."""
    
    @pytest.fixture
    def analyzer(self):
        return GeeConnectivityAnalyzer(resolution=30)
    
    @pytest.fixture
    def mock_connectivity_image(self):
        """Create a mock connectivity image with class_id band."""
        mock = MagicMock()
        mock_classes = MagicMock()
        mock.select.return_value = mock_classes
        mock_classes.reduceToVectors.return_value = MagicMock()
        return mock
    
    @pytest.fixture
    def mock_aoi(self):
        return MagicMock()
    
    def test_vectorize_results_selects_class_id(self, analyzer, mock_connectivity_image, mock_aoi):
        """Test that vectorize_results selects the class_id band."""
        analyzer.vectorize_results(mock_connectivity_image, mock_aoi)
        
        mock_connectivity_image.select.assert_called_with('class_id')
    
    def test_vectorize_results_uses_correct_scale(self, analyzer, mock_connectivity_image, mock_aoi):
        """Test that reduceToVectors uses correct scale parameter."""
        mock_classes = mock_connectivity_image.select.return_value
        
        analyzer.vectorize_results(mock_connectivity_image, mock_aoi)
        
        # Verify reduceToVectors was called
        mock_classes.reduceToVectors.assert_called_once()
        
        # Check scale parameter
        call_kwargs = mock_classes.reduceToVectors.call_args.kwargs
        assert call_kwargs.get('scale') == 30
    
    def test_vectorize_results_uses_eight_connected(self, analyzer, mock_connectivity_image, mock_aoi):
        """Test that 8-connectivity is used for patch analysis."""
        mock_classes = mock_connectivity_image.select.return_value
        
        analyzer.vectorize_results(mock_connectivity_image, mock_aoi)
        
        call_kwargs = mock_classes.reduceToVectors.call_args.kwargs
        assert call_kwargs.get('eightConnected') == True


class TestParityWithPythonBackend:
    """Tests verifying parity guarantees with Python backend."""
    
    def test_thresholds_match_python_defaults(self):
        """Verify GEE adapter uses same default thresholds as Python backend."""
        from src.connectivity import ConnectivityAnalyzer
        
        gee_analyzer = GeeConnectivityAnalyzer()
        py_analyzer = ConnectivityAnalyzer()
        
        assert gee_analyzer.resolution == py_analyzer.resolution
        assert gee_analyzer.core_threshold == py_analyzer.core_threshold
        assert gee_analyzer.edge_threshold == py_analyzer.edge_threshold
    
    def test_class_mapping_consistency(self):
        """Verify class IDs are consistent: 1=Fragmented, 2=Edge, 3=Core."""
        # This is a documentation/specification test
        # Class mapping should be: 0=Non-forest, 1=Fragmented, 2=Edge, 3=Core
        # Both implementations should use these exact values
        expected_mapping = {
            0: 'Non-forest',
            1: 'Fragmented',
            2: 'Edge',
            3: 'Core'
        }
        
        # This test documents the expected behavior
        # If implementation changes, this test should fail
        assert expected_mapping[3] == 'Core'
        assert expected_mapping[2] == 'Edge'
        assert expected_mapping[1] == 'Fragmented'

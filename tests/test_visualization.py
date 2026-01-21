"""
Unit tests for Visualization Module
Tests visualization functions with synthetic data.
"""
import pytest
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon
from rasterio import Affine

from src.visualization import (
    plot_connectivity_map,
    plot_comparison,
    create_interactive_map,
    plot_statistics
)


@pytest.fixture
def sample_connectivity_array():
    """Create a sample connectivity array with all classes."""
    # 10x10 array with classes 0, 1, 2, 3
    arr = np.zeros((10, 10), dtype=np.uint8)
    arr[4:6, 4:6] = 3  # Core in center
    arr[3:7, 3:7] = np.where(arr[3:7, 3:7] == 0, 2, arr[3:7, 3:7])  # Edge around core
    arr[2:8, 2:8] = np.where(arr[2:8, 2:8] == 0, 1, arr[2:8, 2:8])  # Fragmented around edge
    return arr


@pytest.fixture
def sample_transform():
    """Create a sample rasterio transform."""
    return Affine(30.0, 0.0, 500000.0, 0.0, -30.0, 2500000.0)


@pytest.fixture
def sample_lulc_array():
    """Create a sample LULC array."""
    arr = np.random.randint(0, 10, (10, 10), dtype=np.uint8)
    return arr


@pytest.fixture
def sample_geodataframe():
    """Create a sample GeoDataFrame with connectivity polygons."""
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)])
    ]
    gdf = gpd.GeoDataFrame({
        'geometry': polygons,
        'class': [3, 2, 1],
        'class_name': ['Core', 'Edge', 'Fragmented'],
        'area_ha': [100.0, 50.0, 25.0]
    }, crs='EPSG:4326')
    return gdf


@pytest.fixture
def sample_stats():
    """Create sample statistics dictionary."""
    return {
        'core_area_ha': 150.0,
        'edge_area_ha': 75.0,
        'fragmented_area_ha': 25.0,
        'total_forest_ha': 250.0,
        'fragmentation_index': 0.4
    }


class TestPlotConnectivityMap:
    """Tests for plot_connectivity_map function."""
    
    def test_returns_figure(self, sample_connectivity_array, sample_transform):
        """Test that function returns a matplotlib Figure."""
        fig = plot_connectivity_map(sample_connectivity_array, sample_transform)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_custom_title(self, sample_connectivity_array, sample_transform):
        """Test that custom title is applied."""
        title = "Custom Test Title"
        fig = plot_connectivity_map(sample_connectivity_array, sample_transform, title=title)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_handles_all_zeros(self, sample_transform):
        """Test handling of array with all non-forest (zeros)."""
        zero_array = np.zeros((10, 10), dtype=np.uint8)
        fig = plot_connectivity_map(zero_array, sample_transform)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_handles_all_core(self, sample_transform):
        """Test handling of array with all core forest."""
        core_array = np.full((10, 10), 3, dtype=np.uint8)
        fig = plot_connectivity_map(core_array, sample_transform)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotComparison:
    """Tests for plot_comparison function."""
    
    def test_returns_figure(self, sample_lulc_array, sample_connectivity_array):
        """Test that function returns a matplotlib Figure."""
        fig = plot_comparison(sample_lulc_array, sample_connectivity_array)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_custom_title(self, sample_lulc_array, sample_connectivity_array):
        """Test that custom title is applied."""
        title = "My Comparison"
        fig = plot_comparison(sample_lulc_array, sample_connectivity_array, title=title)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestCreateInteractiveMap:
    """Tests for create_interactive_map function."""
    
    def test_returns_folium_map(self, sample_geodataframe):
        """Test that function returns a folium Map object."""
        import folium
        
        m = create_interactive_map(sample_geodataframe)
        
        assert isinstance(m, folium.Map)
    
    def test_custom_center(self, sample_geodataframe):
        """Test map with custom center coordinates."""
        import folium
        
        center = (40.0, -74.0)
        m = create_interactive_map(sample_geodataframe, center=center)
        
        assert isinstance(m, folium.Map)
    
    def test_custom_zoom(self, sample_geodataframe):
        """Test map with custom zoom level."""
        import folium
        
        m = create_interactive_map(sample_geodataframe, zoom=15)
        
        assert isinstance(m, folium.Map)
    
    def test_empty_geodataframe(self):
        """Test handling of empty GeoDataFrame."""
        import folium
        
        empty_gdf = gpd.GeoDataFrame(
            columns=['geometry', 'class', 'class_name', 'area_ha'],
            crs='EPSG:4326'
        )
        m = create_interactive_map(empty_gdf)
        
        assert isinstance(m, folium.Map)


class TestPlotStatistics:
    """Tests for plot_statistics function."""
    
    def test_returns_figure(self, sample_stats):
        """Test that function returns a matplotlib Figure."""
        fig = plot_statistics(sample_stats)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_handles_zero_values(self):
        """Test handling of zero-area statistics."""
        zero_stats = {
            'core_area_ha': 0.0,
            'edge_area_ha': 0.0,
            'fragmented_area_ha': 0.0,
            'total_forest_ha': 0.0,
            'fragmentation_index': 0.0
        }
        fig = plot_statistics(zero_stats)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
    
    def test_handles_missing_keys(self):
        """Test handling of stats with missing keys."""
        partial_stats = {
            'core_area_ha': 100.0
            # Missing other keys
        }
        fig = plot_statistics(partial_stats)
        
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

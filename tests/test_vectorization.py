"""
Unit tests for Vectorization
"""
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from src.vectorization import raster_to_polygons, merge_and_simplify

@pytest.fixture
def synthetic_raster():
    # 10x10 raster
    # Class 3 (Core) in center
    data = np.zeros((10, 10), dtype=np.uint8)
    data[3:7, 3:7] = 3
    
    # Transform: Origin at (0, 100), pixel size 10x10
    transform = from_origin(0, 100, 10, 10)
    return data, transform

def test_raster_to_polygons(synthetic_raster):
    data, transform = synthetic_raster
    gdf = raster_to_polygons(data, transform, crs="EPSG:32643")
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert not gdf.empty
    
    # Should have one polygon (the block of 3s)
    # shapes() might return multiple if not connected? 
    # But 3x3 block is connected.
    
    # Check columns
    assert 'class' in gdf.columns
    assert 'class_name' in gdf.columns
    assert 'area_ha' in gdf.columns
    
    # Check values
    assert gdf.iloc[0]['class'] == 3
    assert gdf.iloc[0]['class_name'] == 'Core'
    
    # Area: 4x4 pixels = 16 pixels. 
    # Each pixel 10x10 = 100m2. Total 1600m2.
    # 1600 / 10000 = 0.16 ha.
    assert np.isclose(gdf.iloc[0]['area_ha'], 0.16)

def test_empty_raster():
    data = np.zeros((10, 10), dtype=np.uint8)
    transform = from_origin(0, 100, 10, 10)
    gdf = raster_to_polygons(data, transform, crs="EPSG:32643")
    assert gdf.empty
    assert 'geometry' in gdf.columns

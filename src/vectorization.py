"""
Vectorization Module
Converts connectivity raster to vector polygons
"""

import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import shape, MultiPolygon
from shapely.ops import unary_union
from rasterio.features import shapes
from typing import Optional, Dict

def raster_to_polygons(
    connectivity_raster: np.ndarray,
    transform: rasterio.Affine,
    crs: str
) -> gpd.GeoDataFrame:
    """
    Convert connectivity raster to vector polygons.
    
    Args:
        connectivity_raster: Classification array (0, 1, 2, 3)
        transform: Raster geotransform
        crs: Coordinate reference system string (e.g., 'EPSG:32643')
        
    Returns:
        GeoDataFrame with polygons and attributes
    """
    # Create a mask for valid data (exclude 0 = non-forest)
    mask = connectivity_raster > 0
    
    # Extract shapes
    # shapes() returns an iterator of (geometry, value)
    results = shapes(
        connectivity_raster, 
        mask=mask, 
        transform=transform
    )
    
    geoms = []
    values = []
    
    for geom, val in results:
        geoms.append(shape(geom))
        values.append(int(val))
        
    if not geoms:
        return gpd.GeoDataFrame(columns=['geometry', 'class', 'class_name', 'area_ha'], crs=crs)
        
    gdf = gpd.GeoDataFrame({'geometry': geoms, 'class': values}, crs=crs)
    
    # Map class names
    class_map = {1: 'Fragmented', 2: 'Edge', 3: 'Core'}
    gdf['class_name'] = gdf['class'].map(class_map)
    
    # Calculate area in hectares
    # Assuming CRS is projected in meters
    gdf['area_ha'] = gdf.geometry.area / 10000.0
    
    return gdf

def merge_and_simplify(
    gdf: gpd.GeoDataFrame,
    tolerance: float = 10.0
) -> gpd.GeoDataFrame:
    """
    Merge adjacent polygons of same class and simplify geometries.
    
    Args:
        gdf: Input GeoDataFrame
        tolerance: Simplification tolerance in CRS units (meters usually)
        
    Returns:
        Simplified and dissolved GeoDataFrame
    """
    if gdf.empty:
        return gdf
        
    # Dissolve by class
    dissolved = gdf.dissolve(by='class', as_index=False)
    
    # Re-calculate area after dissolve
    dissolved['area_ha'] = dissolved.geometry.area / 10000.0
    
    # Use unary_union to handle MultiPolygons cleanly before exploding might be safer,
    # but dissolve does that.
    # Now explode back to single polygons if we want distinct patches, 
    # or keep as MultiPolygons per class. 
    # Usually for analysis we want distinct patches.
    exploded = dissolved.explode(index_parts=False).reset_index(drop=True)
    
    # Re-map class names lost during dissolve if not careful, 
    # actually dissolve keeps the 'by' column. 
    # We need to restore 'class_name'
    class_map = {1: 'Fragmented', 2: 'Edge', 3: 'Core'}
    exploded['class_name'] = exploded['class'].map(class_map)
    exploded['area_ha'] = exploded.geometry.area / 10000.0
    
    # Simplify
    exploded['geometry'] = exploded.geometry.simplify(tolerance, preserve_topology=True)
    
    return exploded

def export_results(
    gdf: gpd.GeoDataFrame,
    output_path: str,
    format: str = 'geojson'
):
    """
    Export to file.
    
    Args:
        gdf: GeoDataFrame to save
        output_path: Destination path
        format: Format driver ('geojson' -> 'GeoJSON', 'shp' -> 'ESRI Shapefile')
    """
    driver = 'GeoJSON' if format.lower() == 'geojson' else 'ESRI Shapefile'
    gdf.to_file(output_path, driver=driver)

if __name__ == "__main__":
    print("Verifying vectorization module...")
    # Synthetic test could go here
    try:
        import rasterio.features
        print("Rasterio features import success.")
    except ImportError as e:
        print(f"Import failed: {e}")

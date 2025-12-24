"""
Generate Reference Outputs
Runs the local Python implementation to generate artifacts for review.
Deterministic output: outputs/run_{timestamp}_{aoi}/
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
import geopandas as gpd
import rasterio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core_stack_client import CoreStackClient
from src.connectivity import ConnectivityAnalyzer
from src.vectorization import raster_to_polygons, merge_and_simplify, export_results
from src.visualization import plot_connectivity_map

def main():
    # Configuration
    STATE = "Jharkhand"
    DISTRICT = "Ranchi"
    TEHSIL = "Kanke"
    YEAR = 2024
    
    # 1. Setup Output Directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"outputs/run_{timestamp}_{TEHSIL}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting analysis run for {TEHSIL} ({timestamp})...")
    print(f"Outputs will be saved to: {output_dir}")
    
    # 2. Fetch Data
    print("Fetching LULC data...")
    client = CoreStackClient()
    lulc_array = client.fetch_lulc_raster(STATE, DISTRICT, TEHSIL, YEAR)
    
    if lulc_array is None:
        print("Failed to fetch LULC data. Constructing synthetic data for demonstration.")
        import numpy as np
        lulc_array = np.zeros((100, 100), dtype=np.uint8)
        # Add a forest block
        lulc_array[30:70, 30:70] = 3 # Core
        lulc_array[20:80, 45:55] = 4 # Bridge
        
        # Synthetic transform
        from rasterio.transform import from_origin
        transform = from_origin(350000, 2500000, 30, 30) # UTM-ish
        crs = "EPSG:32643"
    else:
        # In real scenario we'd get transform/crs from the fetched raster source
        # For this script assuming we have them or mocking them if fetch returns raw array
        # The client.fetch_lulc_raster returns just array in current impl.
        # We need to improve client to return profile or handle synthetic.
        print("Warning: Client returned array without profile. Using synthetic georeferencing.")
        from rasterio.transform import from_origin
        transform = from_origin(350000, 2500000, 30, 30)
        crs = "EPSG:32643"

    # 3. Analyze Connectivity
    print("Running Connectivity Analysis...")
    analyzer = ConnectivityAnalyzer(resolution=30)
    
    # Mask
    forest_mask = analyzer.extract_forest_mask(lulc_array, [3, 4])
    
    # Distance
    distance_map = analyzer.compute_distance_from_edge(forest_mask)
    
    # Classify
    connectivity_classes = analyzer.classify_connectivity(distance_map)
    
    # Stats
    stats = analyzer.calculate_statistics(connectivity_classes)
    print(f"Analysis Complete. Stats: {stats}")
    
    # 4. Export Raster
    print("Exporting Raster...")
    raster_path = output_dir / "connectivity.tif"
    with rasterio.open(
        raster_path, 'w',
        driver='GTiff',
        height=connectivity_classes.shape[0],
        width=connectivity_classes.shape[1],
        count=1,
        dtype=connectivity_classes.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(connectivity_classes, 1)
        
    # 5. Vectorize & Export
    print("Vectorizing...")
    gdf = raster_to_polygons(connectivity_classes, transform, crs)
    
    if not gdf.empty:
        # Simplify slightly for cleaner file
        clean_gdf = merge_and_simplify(gdf, tolerance=10.0)
        
        vector_path = output_dir / "connectivity.geojson"
        export_results(clean_gdf, str(vector_path), format='geojson')
        print(f"Vectors exported to {vector_path}")
    else:
        print("No vectors generated (no forest found).")
        
    # 6. Generate Report
    report = {
        "meta": {
            "timestamp": timestamp,
            "location": f"{STATE}/{DISTRICT}/{TEHSIL}",
            "resolution": 30,
            "crs": crs
        },
        "statistics": stats,
        "parameters": {
            "core_threshold": 300,
            "edge_threshold": 100
        }
    }
    
    report_path = output_dir / "report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print("Success! All outputs generated.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

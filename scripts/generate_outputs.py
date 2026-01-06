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
    lulc_array, profile = client.fetch_lulc_raster(STATE, DISTRICT, TEHSIL, YEAR)
    
    if lulc_array is None or profile is None:
        print("CRITICAL ERROR: Failed to fetch valid LULC data or profile.")
        sys.exit(1)

    crs = profile['crs']
    transform = profile['transform']

    # 3. Analyze Connectivity
    print("Running Connectivity Analysis...")
    analyzer = ConnectivityAnalyzer(resolution=30)
    
    # Validation (Fail Fast)
    try:
        analyzer.validate_geospatial_profile(profile)
        print("Geospatial validation passed (CRS Projected, Resolution ~30m).")
    except ValueError as e:
        print(f"GEOSPATIAL INTEGRITY FAILURE: {e}")
        sys.exit(1)
    
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
    
    # Update profile for output
    out_profile = profile.copy()
    out_profile.update({
        'driver': 'GTiff',
        'dtype': connectivity_classes.dtype,
        'count': 1
    })
    
    with rasterio.open(raster_path, 'w', **out_profile) as dst:
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

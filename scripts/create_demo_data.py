
import rasterio
from rasterio.transform import from_origin
import numpy as np
from pathlib import Path

def create_demo_tiff():
    """
    Creates a valid, georeferenced GeoTIFF for demonstration.
    This serves as a known input for verifying the pipeline when API access is restricted.
    """
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "demo_lulc.tif"
    
    # 100x100 pixel grid (3000m x 3000m) at 30m resolution
    height, width = 100, 100
    
    # Create valid transform (UTM Zone 43N - typical for Jharkhand)
    # Origin: 350000E, 2500000N
    transform = from_origin(351350, 2499400, 30, 30)
    crs = "EPSG:32643"
    
    # Create Data with explicit class IDs matching CoRE Stack v2
    # 1: Water, 6: Agriculture, 8: Plantation
    # 3: Deciduous (Natural), 4: Evergreen (Natural)
    arr = np.zeros((height, width), dtype=np.uint8)
    
    # Fill background with Agriculture (6)
    arr[:, :] = 6 
    
    # Add Water body (1)
    arr[0:20, 0:20] = 1
    
    # Add Plantation (8) - SHOULD BE EXCLUDED from connectivity
    arr[10:30, 40:60] = 8
    
    # Add Natural Forest Block (3 & 4) - SHOULD BE INCLUDED
    # Core Block
    arr[40:90, 40:90] = 3 # Deciduous
    
    # Edge Strip
    arr[40:90, 30:40] = 4 # Evergreen
    
    # Fragmented patches
    arr[20:25, 80:85] = 3
    
    # Metadata
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': arr.dtype,
        'crs': crs,
        'transform': transform,
        'nodata': 0
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(arr, 1)
        
    print(f"Created valid demo LULC file at: {output_path}")
    print(f"CRS: {crs}")
    print(f"Contains: Natural Forest (3,4), Plantation (8), Ag (6), Water (1)")

if __name__ == "__main__":
    create_demo_tiff()

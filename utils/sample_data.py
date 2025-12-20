"""
Sample Data Generator
Creates synthetic LULC data for notebook demonstration purposes.
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

def generate_sample_lulc(output_path="data/sample_lulc.tif", size=(500, 500)):
    """
    Generates a synthetic LULC raster.
    Classes:
    1: Water
    2: Built-up
    3: Deciduous Forest
    4: Evergreen Forest
    6: Agriculture
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create base array (Agriculture)
    data = np.full(size, 6, dtype=np.uint8)
    
    # Add some forest patches (Class 3)
    # Simple blobs
    rows, cols = size
    
    # Large core forest
    y, x = np.ogrid[:rows, :cols]
    center_y, center_x = rows//2, cols//2
    mask = ((x - center_x)**2 + (y - center_y)**2) < (rows//4)**2
    data[mask] = 3
    
    # Scattered fragments
    np.random.seed(42)
    for _ in range(20):
        rx, ry = np.random.randint(0, cols), np.random.randint(0, rows)
        r_radius = np.random.randint(5, 20)
        mask = ((x - rx)**2 + (y - ry)**2) < r_radius**2
        data[mask] = 3

    # Add limits metadata
    transform = from_origin(700000, 2500000, 30, 30) # UTM Zone approx
    
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=size[0],
        width=size[1],
        count=1,
        dtype=data.dtype,
        crs='EPSG:32644', # UTM 44N
        transform=transform,
    ) as dst:
        dst.write(data, 1)
        
    print(f"Sample data generated at {output_path}")

if __name__ == "__main__":
    generate_sample_lulc()

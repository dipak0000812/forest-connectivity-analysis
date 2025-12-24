"""
Visualize Latest Run
Finds the latest output folder and generates a PNG map of the connectivity.
"""

import sys
import os
import glob
from pathlib import Path
import rasterio
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.visualization import plot_connectivity_map

def main():
    # 1. Find latest run
    output_base = Path("outputs")
    runs = sorted(list(output_base.glob("run_*")))
    
    if not runs:
        print("No runs found in outputs/")
        return
        
    latest_run = runs[-1]
    print(f"Visualizing latest run: {latest_run}")
    
    tif_path = latest_run / "connectivity.tif"
    if not tif_path.exists():
        print(f"No connectivity.tif found in {latest_run}")
        return
        
    # 2. Load Data
    with rasterio.open(tif_path) as src:
        data = src.read(1)
        transform = src.transform
        
    # 3. Plot
    print("Generating map...")
    fig = plot_connectivity_map(data, transform, title=f"Forest Connectivity: {latest_run.name}")
    
    # 4. Save
    output_png = latest_run / "connectivity_map.png"
    fig.savefig(output_png, bbox_inches='tight', dpi=300)
    print(f"Map saved to: {output_png}")
    plt.close(fig)

if __name__ == "__main__":
    main()

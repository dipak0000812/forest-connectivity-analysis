"""
Visualization Module
Create maps and charts for forest connectivity
"""

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import patches
import rasterio
import numpy as np
import geopandas as gpd
import folium
from typing import Dict, Tuple

def plot_connectivity_map(
    connectivity_array: np.ndarray,
    transform: rasterio.Affine,
    title: str = "Forest Connectivity"
) -> plt.Figure:
    """
    Create static map showing connectivity classes.
    0: None (Transparent), 1: Fragmented (Red), 2: Edge (Yellow), 3: Core (Green)
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Custom colormap
    # 0 = white/transparent, 1=red, 2=yellow, 3=green
    colors = ['white', '#ff4444', '#ffbb33', '#00C851']
    cmap = ListedColormap(colors)
    
    # Mask 0 values for better plot
    masked_array = np.ma.masked_where(connectivity_array == 0, connectivity_array)
    
    im = ax.imshow(masked_array, cmap=cmap, vmin=0, vmax=3, interpolation='nearest')
    
    # Formatting
    ax.set_title(title, fontsize=14)
    ax.axis('off')
    
    # Legend
    legend_elements = [
        patches.Patch(facecolor='#ff4444', edgecolor='black', label='Fragmented'),
        patches.Patch(facecolor='#ffbb33', edgecolor='black', label='Edge'),
        patches.Patch(facecolor='#00C851', edgecolor='black', label='Core')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    return fig

def plot_comparison(
    lulc_array: np.ndarray,
    connectivity_array: np.ndarray,
    title: str = "LULC vs Connectivity"
) -> plt.Figure:
    """
    Side-by-side comparison.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # LULC Plot (Basic)
    ax1.imshow(lulc_array, cmap='tab20', interpolation='nearest')
    ax1.set_title("Original LULC")
    ax1.axis('off')
    
    # Connectivity Plot
    colors = ['white', '#ff4444', '#ffbb33', '#00C851']
    cmap = ListedColormap(colors)
    masked_conn = np.ma.masked_where(connectivity_array == 0, connectivity_array)
    
    ax2.imshow(masked_conn, cmap=cmap, vmin=0, vmax=3, interpolation='nearest')
    ax2.set_title("Connectivity Classes")
    ax2.axis('off')
    
    plt.suptitle(title)
    return fig

def create_interactive_map(
    gdf: gpd.GeoDataFrame,
    center: Tuple[float, float] = (23.34, 85.30), # Default to Ranchi
    zoom: int = 11
) -> folium.Map:
    """
    Interactive web map using Folium.
    """
    m = folium.Map(location=[center[0], center[1]], zoom_start=zoom)
    
    # Function to style features based on class
    def style_function(feature):
        cls = feature['properties'].get('class', 0)
        color = '#000000'
        if cls == 1: color = '#ff4444' # Fragmented
        elif cls == 2: color = '#ffbb33' # Edge
        elif cls == 3: color = '#00C851' # Core
        
        return {
            'fillColor': color,
            'color': color,
            'weight': 1,
            'fillOpacity': 0.6
        }
    
    # Add GeoDataFrame
    folium.GeoJson(
        gdf,
        name='Forest Connectivity',
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['class_name', 'area_ha'],
            aliases=['Class:', 'Area (ha):']
        )
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

def plot_statistics(stats: Dict) -> plt.Figure:
    """
    Bar chart of area by class.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    categories = ['Core', 'Edge', 'Fragmented']
    values = [stats.get('core_area_ha', 0), stats.get('edge_area_ha', 0), stats.get('fragmented_area_ha', 0)]
    colors = ['#00C851', '#ffbb33', '#ff4444']
    
    bars = ax.bar(categories, values, color=colors)
    
    ax.set_ylabel('Area (Hectares)')
    ax.set_title('Forest Connectivity Statistics')
    
    # Label bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom')
                
    return fig

if __name__ == "__main__":
    print("Verifying visualization module...")
    try:
        import matplotlib
        import folium
        print("Visualization libs import success.")
    except ImportError as e:
        print(f"Import failed: {e}")

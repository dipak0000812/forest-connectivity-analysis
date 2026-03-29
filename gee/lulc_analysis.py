"""
Google Earth Engine Script for CoRE Stack LULC Analysis
========================================================

This script provides utilities to load, explore, and extract tree/forest pixels
from the CoRE Stack LULC dataset for forest connectivity analysis using MSPA.

Author: Forest Connectivity Analysis Project
Date: 2026-02-06
"""

import ee
from typing import List, Dict, Tuple, Optional
import sys


def initialize_gee() -> None:
    """
    Initialize Google Earth Engine with authentication handling.
    
    Attempts to initialize GEE. If authentication fails, prompts user to authenticate.
    
    Raises:
        Exception: If initialization fails after authentication attempt.
    """
    try:
        ee.Initialize()
        print("✓ Google Earth Engine initialized successfully")
    except Exception as e:
        print(f"⚠ GEE initialization failed: {e}")
        print("→ Attempting authentication...")
        try:
            ee.Authenticate()
            ee.Initialize()
            print("✓ Authentication successful, GEE initialized")
        except Exception as auth_error:
            print(f"✗ Authentication failed: {auth_error}")
            raise


def explore_lulc_classes(lulc_image: ee.Image, region: ee.Geometry) -> Dict[str, any]:
    """
    Explore and analyze unique LULC classes within a specified region.
    
    This function computes the distribution of LULC classes, helping identify
    which class values represent forest/tree cover.
    
    Args:
        lulc_image: Earth Engine Image containing LULC classification
        region: Earth Engine Geometry defining the area of interest
    
    Returns:
        Dictionary containing class statistics and distribution
    """
    print("\n" + "="*70)
    print("EXPLORING LULC CLASSES")
    print("="*70)
    
    # Reduce the image to get unique values and pixel counts
    class_stats = lulc_image.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=region,
        scale=30,
        maxPixels=1e9
    )
    
    # Get the histogram
    histogram = class_stats.getInfo()
    
    if not histogram or 'b1' not in histogram:
        print("✗ No data found in the specified region")
        return {}
    
    class_counts = histogram['b1']
    
    # Calculate total pixels
    total_pixels = sum(class_counts.values())
    
    # Sort classes by pixel count (descending)
    sorted_classes = sorted(
        class_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print(f"\n📊 Total pixels analyzed: {total_pixels:,}")
    print(f"📊 Unique classes found: {len(sorted_classes)}")
    print("\n" + "-"*70)
    print(f"{'Class ID':<12} {'Pixel Count':<15} {'Percentage':<12} {'Bar Chart'}")
    print("-"*70)
    
    results = {
        'total_pixels': total_pixels,
        'class_distribution': {}
    }
    
    for class_id, count in sorted_classes:
        percentage = (count / total_pixels) * 100
        bar_length = int(percentage / 2)  # Scale for display
        bar = '█' * bar_length
        
        print(f"{class_id:<12} {count:<15,} {percentage:>6.2f}%     {bar}")
        
        results['class_distribution'][int(float(class_id))] = {
            'count': count,
            'percentage': percentage
        }
    
    print("-"*70)
    print("\n💡 TIP: CoRE Stack LULC v3 Legend:")
    print("   Class 6 = 'Trees' (natural forest)")
    print("   Classes 1-4 = Built-up, Water types")
    print("   Class 5 = Crops | Classes 8-11 = Cropping patterns | Class 12 = Shrubs")
    print("="*70 + "\n")
    
    return results


def extract_tree_mask(
    lulc_image: ee.Image,
    tree_class_values: List[int],
    region: ee.Geometry
) -> ee.Image:
    """
    Extract binary tree mask from LULC image.
    
    Creates a binary mask where pixels matching tree class values are set to 1,
    and all other pixels are set to 0.
    
    Args:
        lulc_image: Earth Engine Image containing LULC classification
        tree_class_values: List of class IDs representing tree/forest cover
        region: Earth Engine Geometry defining the area of interest
    
    Returns:
        Binary Earth Engine Image (1 = tree, 0 = non-tree)
    """
    print("\n" + "="*70)
    print("EXTRACTING TREE MASK")
    print("="*70)
    print(f"→ Tree class values: {tree_class_values}")
    
    # Create binary mask using logical OR for multiple classes
    tree_mask = lulc_image.eq(tree_class_values[0])
    
    for class_value in tree_class_values[1:]:
        tree_mask = tree_mask.Or(lulc_image.eq(class_value))
    
    # Convert boolean to integer (0 or 1)
    tree_mask = tree_mask.byte().rename('tree_mask')
    
    # Calculate tree coverage statistics
    stats = tree_mask.reduceRegion(
        reducer=ee.Reducer.sum().combine(
            reducer2=ee.Reducer.count(),
            sharedInputs=True
        ),
        geometry=region,
        scale=30,
        maxPixels=1e9
    )
    
    stats_info = stats.getInfo()
    tree_pixels = stats_info.get('tree_mask_sum', 0)
    total_pixels = stats_info.get('tree_mask_count', 1)
    tree_percentage = (tree_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    
    print(f"\n📊 Tree Coverage Statistics:")
    print(f"   • Total pixels: {total_pixels:,}")
    print(f"   • Tree pixels: {tree_pixels:,}")
    print(f"   • Tree coverage: {tree_percentage:.2f}%")
    print(f"   • Non-tree pixels: {total_pixels - tree_pixels:,}")
    print("="*70 + "\n")
    
    return tree_mask


def create_visualization_layers(
    lulc: ee.Image,
    tree_mask: ee.Image,
    region: ee.Geometry
) -> Dict[str, any]:
    """
    Create visualization parameters and GEE Code Editor snippet.
    
    Generates visualization configurations for LULC, tree mask, and provides
    JavaScript code snippet for visualization in GEE Code Editor.
    
    Args:
        lulc: Original LULC Earth Engine Image
        tree_mask: Binary tree mask Earth Engine Image
        region: Earth Engine Geometry defining the area of interest
    
    Returns:
        Dictionary containing visualization parameters and code snippet
    """
    print("\n" + "="*70)
    print("CREATING VISUALIZATION LAYERS")
    print("="*70)
    
    # LULC visualization (using a generic color scheme)
    lulc_vis = {
        'min': 0,
        'max': 20,
        'palette': [
            '#000000',  # 0 - No data
            '#006400',  # 1 - Dense forest (dark green)
            '#228B22',  # 2 - Forest (forest green)
            '#32CD32',  # 3 - Open forest (lime green)
            '#90EE90',  # 4 - Scrub (light green)
            '#FFFF00',  # 5 - Grassland (yellow)
            '#FFD700',  # 6 - Agriculture (gold)
            '#8B4513',  # 7 - Fallow land (brown)
            '#D2691E',  # 8 - Barren land (chocolate)
            '#A9A9A9',  # 9 - Built-up (dark gray)
            '#0000FF',  # 10 - Water (blue)
            '#87CEEB',  # 11 - Wetland (sky blue)
            '#F0E68C',  # 12 - Sandy area (khaki)
            '#FFFFFF',  # 13 - Snow/Ice (white)
            '#FF69B4',  # 14 - Other (hot pink)
            '#FF1493',  # 15 - Other (deep pink)
            '#C71585',  # 16 - Other (medium violet red)
            '#8B008B',  # 17 - Other (dark magenta)
            '#4B0082',  # 18 - Other (indigo)
            '#483D8B',  # 19 - Other (dark slate blue)
            '#2F4F4F',  # 20 - Other (dark slate gray)
        ]
    }
    
    # Tree mask visualization
    tree_mask_vis = {
        'min': 0,
        'max': 1,
        'palette': ['#808080', '#00FF00']  # Gray for non-tree, green for tree
    }
    
    # Get region bounds for Code Editor
    bounds = region.bounds().getInfo()['coordinates'][0]
    
    # Create GEE Code Editor JavaScript snippet
    code_snippet = f"""
// ============================================================================
// Google Earth Engine Code Editor Visualization
// ============================================================================
// Copy and paste this code into the GEE Code Editor (https://code.earthengine.google.com/)

// Load LULC dataset
var lulc = ee.Image("projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024");

// Define region
var region = ee.Geometry.Rectangle({bounds});

// LULC Visualization
var lulcVis = {lulc_vis};
Map.addLayer(lulc.clip(region), lulcVis, 'LULC Classification');

// Tree Mask Visualization (replace tree_class_values with your actual values)
var treeClasses = [1, 2, 3];  // UPDATE THIS based on your exploration
var treeMask = lulc.eq(treeClasses[0]);
for (var i = 1; i < treeClasses.length; i++) {{
  treeMask = treeMask.or(lulc.eq(treeClasses[i]));
}}
treeMask = treeMask.byte();

var treeMaskVis = {tree_mask_vis};
Map.addLayer(treeMask.clip(region), treeMaskVis, 'Tree Mask');

// Add satellite basemap
Map.setOptions('SATELLITE');

// Center map on region
Map.centerObject(region, 11);

// Print statistics
print('Region bounds:', region.bounds());
print('Tree coverage:', treeMask.reduceRegion({{
  reducer: ee.Reducer.mean(),
  geometry: region,
  scale: 30,
  maxPixels: 1e9
}}));
"""
    
    print("\n📋 Visualization Parameters:")
    print(f"   • LULC palette: {len(lulc_vis['palette'])} colors")
    print(f"   • Tree mask: Gray (non-tree) → Green (tree)")
    print("\n" + "-"*70)
    print("GEE CODE EDITOR SNIPPET")
    print("-"*70)
    print(code_snippet)
    print("-"*70)
    print("\n💡 Copy the code above and paste it into:")
    print("   https://code.earthengine.google.com/")
    print("="*70 + "\n")
    
    return {
        'lulc_vis': lulc_vis,
        'tree_mask_vis': tree_mask_vis,
        'code_snippet': code_snippet
    }


def export_to_drive(
    image: ee.Image,
    region: ee.Geometry,
    description: str,
    folder: str = 'mspa_outputs',
    scale: int = 30
) -> ee.batch.Task:
    """
    Export Earth Engine Image to Google Drive as GeoTIFF.
    
    Args:
        image: Earth Engine Image to export
        region: Earth Engine Geometry defining export bounds
        description: Description for the export task (also used as filename)
        folder: Google Drive folder name (default: 'mspa_outputs')
        scale: Export resolution in meters (default: 30)
    
    Returns:
        Earth Engine Task object
    """
    print("\n" + "="*70)
    print("EXPORTING TO GOOGLE DRIVE")
    print("="*70)
    print(f"→ Description: {description}")
    print(f"→ Folder: {folder}")
    print(f"→ Resolution: {scale}m")
    
    # Create export task
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        fileNamePrefix=description,
        region=region,
        scale=scale,
        maxPixels=1e9,
        fileFormat='GeoTIFF',
        formatOptions={
            'cloudOptimized': True
        }
    )
    
    print(f"\n✓ Export task created: {description}")
    print(f"   Task will appear in: https://code.earthengine.google.com/tasks")
    print(f"   Output location: Google Drive/{folder}/{description}.tif")
    print("\n💡 Remember to call task.start() to begin the export!")
    print("="*70 + "\n")
    
    return task


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CoRE Stack LULC Analysis - Forest Connectivity Project")
    print("="*70 + "\n")
    
    # Initialize Google Earth Engine
    initialize_gee()
    
    # Load LULC dataset
    print("→ Loading CoRE Stack LULC dataset...")
    lulc = ee.Image("projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024")
    print("✓ LULC dataset loaded\n")
    
    # Define Saranda Forest test region
    print("→ Defining Saranda Forest region...")
    region = ee.Geometry.Rectangle([85.1, 22.2, 85.5, 22.5])
    print("✓ Region defined: [85.1, 22.2, 85.5, 22.5] (W, S, E, N)\n")
    
    # Step 1: Explore LULC classes
    print("\n" + "🔍 STEP 1: EXPLORING LULC CLASSES")
    class_info = explore_lulc_classes(lulc, region)
    
    # Step 2: Extract tree mask
    # CoRE Stack LULC v3 Legend:
    # Class 6 = "Trees" (natural forest)
    # Classes 1-4 = Built-up, Water types (NOT forest)
    # Class 5 = Crops
    # Classes 8-11 = Different cropping patterns
    # Class 12 = Shrubs
    print("\n" + "🌲 STEP 2: EXTRACTING TREE MASK")
    print("\n✓ Using CoRE Stack LULC v3 Legend:")
    print("   Class 6 = 'Trees' (natural forest)")
    
    # CoRE Stack LULC v3: Class 6 = Trees (natural forest)
    tree_classes = [6]  # Class 6 represents natural forest/trees
    
    tree_mask = extract_tree_mask(lulc, tree_classes, region)
    
    # Step 3: Create visualization layers
    print("\n" + "🎨 STEP 3: CREATING VISUALIZATIONS")
    vis_params = create_visualization_layers(lulc, tree_mask, region)
    
    # Step 4: Export to Google Drive
    print("\n" + "💾 STEP 4: EXPORTING TO GOOGLE DRIVE")
    
    # Export tree mask (Class 6 = Trees only)
    task_tree_mask = export_to_drive(
        image=tree_mask,
        region=region,
        description="saranda_tree_mask_class6_only",
        folder="mspa_outputs"
    )
    
    # Export original LULC (clipped to region)
    task_lulc = export_to_drive(
        image=lulc.clip(region),
        region=region,
        description="saranda_lulc_original",
        folder="mspa_outputs"
    )
    
    # Start export tasks
    print("\n" + "🚀 STARTING EXPORT TASKS...")
    task_tree_mask.start()
    print(f"✓ Started: {task_tree_mask.id}")
    
    task_lulc.start()
    print(f"✓ Started: {task_lulc.id}")
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE!")
    print("="*70)
    print("\n📌 NEXT STEPS:")
    print("   1. Check export progress: https://code.earthengine.google.com/tasks")
    print("   2. Download GeoTIFFs from Google Drive/mspa_outputs/")
    print("   3. Verify tree mask in QGIS/ArcGIS")
    print("   4. Proceed with MSPA analysis using the tree mask")
    print("\n" + "="*70 + "\n")

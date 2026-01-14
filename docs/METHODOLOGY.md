# Methodology: Forest Structural Connectivity

## Overview
This document details the algorithm used to compute forest structural connectivity at 30m resolution.

## Algorithm Steps

### 1. Forest Masking (Natural Forest Only)
The analysis begins by creating a binary mask from the input Land Use/Land Cover (LULC) raster.
*   **Input**: 30m LULC Raster (Sentinel-2 derived).
*   **Logic**: `Mask = 1 if LULC_Value in [Natural_Forest_IDs] else 0`
*   **Exclusions**: **Plantations** (e.g., commercial monocultures) are explicitly **excluded** from the mask. This ensures that connectivity metrics reflect the ecological integrity of natural forests, not industrial cover.

### 2. Distance Transformation (Morphological Spatial Pattern Analysis)
We compute the Euclidean distance from every forest pixel to the nearest non-forest pixel.
*   **Tool**: `scipy.ndimage.distance_transform_edt` (Python) / `fastDistanceTransform` (GEE).
*   **Metric**: Euclidean distance in meters.
*   **Boundary Handling**: The AOI boundary is treated as "non-forest" (distance = 0) to avoid artificial edge effects at image borders.

### 3. Classification
Pixels are classified based on their distance from the forest edge ($d$):

| Class | Name | Definition | Ecological Signifiance |
| :--- | :--- | :--- | :--- |
| **1** | **Fragmented** | $d < 100m$ | Degraded, edge-exposed, or small isolated patches. High disturbance risk. |
| **2** | **Edge** | $100m \le d < 300m$ | Transition zone. Buffers the core from external disturbance. |
| **3** | **Core** | $d \ge 300m$ | Deep, undisturbed forest. Critical for biodiversity and interior species. |

### 4. Vectorization
The raster classification is converted to vector polygons:
*   **Method**: Connected component analysis (8-connectivity).
*   **Simplification**: Polygons are simplified (tolerance ~10m) to reduce vertex count while preserving shape.
*   **Attributes**:
    *   `connectivity_class`: Core, Edge, or Fragmented.
    *   `area_ha`: Area in hectares.
    *   `patch_size_ha`: Size of the contiguous patch area.

## Parity: Python vs GEE
The algorithm is implemented identically in both environments:
*   **Python**: Uses `numpy` and `scipy` for exact in-memory processing.
*   **GEE**: Uses `ee.Image` methods to replicate the logic on the cloud.
*   **Consistency**: Both implementations use the same thresholds (100m/300m) and the same natural forest class definitions.

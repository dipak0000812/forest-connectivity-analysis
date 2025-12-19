# Methodology: Forest Structural Connectivity Analysis

## Problem Statement
Forest fragmentation reduces biodiversity and ecosystem resilience. Identifying core forests versus edge/fragmented areas is crucial for conservation planning. This project uses 30m LULC data to classify forest areas based on their structural connectivity.

## Algorithm Overview

The analysis is performed on a pixel-by-pixel basis using a standard core-edge model.

1.  **Data Acquisition**: 30m LULC rasters are obtained from CoRE Stack.
2.  **Forest Extraction**: Pixels classified as "Deciduous Forest" (Class 3) or "Evergreen Forest" (Class 4) are extracted to create a binary mask (1 = Forest, 0 = Non-Forest).
3.  **Distance Calculation**: For every forest pixel, we calculate the Euclidean distance to the nearest non-forest pixel (edge).
4.  **Classification**: Pixels are classified based on their distance from the edge:
    *   **Fragmented**: Distance < 100m (Forest pixels very close to edges or in small patches).
    *   **Edge**: 100m ≤ Distance < 300m (Transition zones).
    *   **Core**: Distance ≥ 300m (Deep forest, undisturbed).

## Parameter Justification

*   **Resolution (30m)**: Matching the input LULC data resolution.
*   **Edge Threshold (100m)**: Standard ecological threshold representing the depth of edge effects (microclimate changes, invasive species).
*   **Core Threshold (300m)**: Represents interior forest areas sufficient to support edge-sensitive species. Note: This is an adjustable parameter.

## Vectorization
Raster results are converted to vector polygons to calculate precise areas and integrate with administrative or watershed boundaries. Smoothing is applied to remove pixelation artifacts.

## References
*   Vogt, P., et al. (2007). "Mapping spatial patterns with morphological image processing." Landscape Ecology.
*   Riitters, K., et al. (2002). "Fragmentation of Continental United States Forests." Ecosystems.

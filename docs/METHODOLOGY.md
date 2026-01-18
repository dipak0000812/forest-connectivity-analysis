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

---

## Methodological Context: Distance-Based vs Full MSPA

### Current Implementation (Distance-Based)

**Approach**: Classify pixels based solely on Euclidean distance from forest edge.

**Decision Logic**:
```
if distance < 100m:
    class = "Fragmented"
elif distance < 300m:
    class = "Edge"
else:
    class = "Core"
```

**Strengths**:
- Computationally efficient (O(n) complexity)
- Interpretable thresholds aligned with ecological edge effect literature
- Captures the most critical conservation metric: **Core forest area**

**Limitations**:
- Does not distinguish geometric roles (e.g., bridges vs isolated islets)
- "Fragmented" class is a catch-all for all non-core, non-edge pixels
- Cannot identify linear connectivity features (corridors, stepping stones)

---

### Full MSPA (7-Class Pattern Recognition)

**Approach**: Morphological image processing with foreground/background analysis.

**Pattern Classes**:

| Class | Definition | Connectivity Role |
|-------|------------|-------------------|
| **Core** | Interior area > threshold distance from edge | Primary habitat reservoir |
| **Islet** | Small isolated patches (too small for core) | Stepping stones, genetic exchange |
| **Perforation** | Forest surrounding non-forest openings | Edge around internal gaps |
| **Edge** | Forest adjacent to main non-forest matrix | Transition/buffer zone |
| **Loop** | Forest connecting to itself | Local connectivity |
| **Bridge** | Forest connecting two core areas | Critical corridor |
| **Branch** | Forest extending from core but not connecting | Potential corridor |

**Key Differences**:

| Metric | Distance-Based | Full MSPA |
|--------|----------------|-----------|
| **Islet Detection** | Lumped into "Fragmented" | Explicit class |
| **Bridge Identification** | Lumped into "Fragmented" | Explicit class (critical for corridor planning) |
| **Perforation** | Not detected | Explicit class (important for internal fragmentation) |
| **Computational Cost** | Low | Moderate (requires morphological operators) |
| **Ecological Detail** | Coarse | Fine-grained |

---

### Transition Plan

**Phase Approach**:

1. **Current (Baseline)**: Distance-based 3-class system validated and documented
2. **Next (In Development)**: Full 7-class MSPA with GEE-first implementation
3. **Future**: Integration with CoRE Stack micro-watershed analysis

**Deprecation Notice**:

> ⚠️ **Note on "Fragmented" Class**  
> The current "Fragmented" class (d < 100m) will be **deprecated** in the next major version. It will be replaced with granular classifications:
> - **Islet**: Small isolated patches
> - **Perforation**: Internal edge around gaps
> - **Bridge/Branch**: Linear connectivity features
>
> This change will enable **corridor identification** and **pathway analysis**, which are not possible with the current distance-only approach.

**Why the Transition Matters**:

- **Current**: "This forest has 45% core area" → Useful for prioritization
- **Full MSPA**: "Core patch A connects to patch B via 3 bridge pixels" → Enables targeted corridor restoration

---

### References

- Vogt, P., et al. (2007). "Mapping Spatial Patterns with Morphological Image Processing." *Landscape Ecology* 22(2): 171-177.
- Soille, P., & Vogt, P. (2009). "Morphological segmentation of binary patterns." *Pattern Recognition Letters* 30(4): 456-459.
- Current implementation aligns with edge effect thresholds per Haddad et al. (2015), *Science Advances*.

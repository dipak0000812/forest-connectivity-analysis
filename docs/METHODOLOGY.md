# Methodology: MSPA Forest Structural Connectivity

> **Implementation Status**: GEE-first with Python for validation only.

## Overview

This document describes the **Morphological Spatial Pattern Analysis (MSPA)** algorithm used to classify forest structural connectivity at 30m resolution.

---

## 1. Data Source

**IndiaSAT LULC** assets on CoRE Stack GEE app.

| Parameter | Value |
|-----------|-------|
| Resolution | 30m |
| Source | Sentinel-2 derived |
| CRS | UTM (projected) |

---

## 2. Forest Mask

### Input
IndiaSAT LULC raster with class IDs.

### Logic
```javascript
var forestClasses = [3, 4];  // Deciduous, Evergreen
var mask = lulc.remap(forestClasses, [1, 1], 0);
```

### Exclusions
- **Plantations (Class 8)**: Excluded by design
- Only **natural forest** enters the analysis

---

## 3. Distance Transform

### Method
**Euclidean Distance Transform** via `fastDistanceTransform` (GEE).

### Output
Distance in meters from each forest pixel to nearest non-forest edge.

```javascript
var distance = forestMask.fastDistanceTransform()
  .sqrt()
  .multiply(30);  // Convert pixels to meters
```

---

## 4. MSPA Classification

### 7-Class System (JRC Standard)

| Class | ID | Definition | Detection |
|-------|-----|------------|-----------|
| **Core** | 1 | Distance ≥ 100m | Distance transform |
| **Islet** | 2 | Patch with no core | Connected components |
| **Perforation** | 3 | Edge around internal holes | Hole detection |
| **Edge** | 4 | Distance < 100m, external | Distance + topology |
| **Loop** | 5 | Connects core to itself | Skeleton analysis |
| **Bridge** | 6 | Connects 2+ cores | Skeleton + graph |
| **Branch** | 7 | Dead-end from core | Skeleton endpoints |

### Parameters
- **EdgeWidth**: 100m (JRC default)
- **Connectivity**: 8-connected

---

## 5. Bridge Detection (Priority)

Bridges are **critical corridors** connecting separate core areas.

### Algorithm
1. Label each core with unique ID
2. Extract skeleton of non-core forest
3. For each skeleton pixel:
   - Check adjacent core labels
   - If touches 2+ different labels → **Bridge**

---

## 6. Vectorization

Convert raster to polygons using `reduceToVectors()`.

### Attributes
- `mspa_class`: 1-7
- `class_name`: Core, Bridge, etc.
- `area_ha`: Polygon area in hectares

---

## 7. Validation

### Method
Compare GEE outputs against JRC MSPA Desktop Tool (GuidosToolbox).

### Target
≥95% pixel-wise agreement on test regions.

---

## References

- Soille, P., & Vogt, P. (2009). Morphological segmentation of binary patterns. *Pattern Recognition Letters*, 30(4), 456-459.
- JRC MSPA: https://forest.jrc.ec.europa.eu/en/activities/lpa/mspa/

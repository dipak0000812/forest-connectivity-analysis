# MSPA Methodology — Forest Structural Connectivity
## CoRE Stack Issue #228 | Vogt et al. 2009

---

## 1. Algorithm Overview

This pipeline implements Morphological Spatial Pattern Analysis (MSPA)
as described in Vogt et al. 2009 (Pattern Recognition Letters), adapted
for Google Earth Engine using equivalent operations.

MSPA classifies a binary forest raster into structural components that
reveal the ecological role of each pixel — whether it is interior core
habitat, a fragmentation-vulnerable edge, an isolated fragment, or an
internal clearing edge.

**Reference:** Vogt P. et al. (2009). Mapping spatial patterns with morphological
image processing. Pattern Recognition Letters, 30(4), 456–459.
https://www.sciencedirect.com/science/article/pii/S0167865508003267

---

## 2. Input Data

- **Dataset:** IndiaSAT LULC v4 (Sentinel-2 derived)
- **GEE Asset:** `projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024`
- **Band:** `predicted_label`
- **Tree class:** Class 6 = "Trees"
  - Explicitly excludes: Plantations (11), Crops (5), Shrubs (12),
    Water (2, 3, 4), Built-up (1), Barren (7)
- **Resolution:** 30m (native IndiaSAT resolution)

---

## 3. Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Edge width | 100m (3 pixels at 30m) | Vogt et al. 2009 default |
| Islet threshold | <1ha (<11 pixels at 30m) | Standard MSPA practice |
| Connectivity | 8-connected | Vogt et al. 2009 |
| Perforation hole detection | connectedPixelCount maxSize=1024 | GEE constraint |

---

## 4. Processing Steps

### Step 1 — Forest Mask
```javascript
var forestMask = lulc.eq(6).rename('forest').uint8();
```
Binary raster: 1 = Trees (class 6), 0 = all other classes.

### Step 2 — Euclidean Distance Transform
```javascript
var distToEdge_m = forestMask
  .not()
  .fastDistanceTransform(256, 'pixels')  // returns SQUARED pixel distance
  .sqrt()                                 // → pixel distance
  .multiply(30)                           // → meters
  .updateMask(forestMask);
```
Per-pixel Euclidean distance (meters) from each forest pixel to the nearest
non-forest boundary. GEE's `fastDistanceTransform` returns squared distance,
so `.sqrt()` is required before multiplying by pixel size.

### Step 3 — Perforation (Internal Background) Detection
```javascript
var bgPatchSize = forestMask.not().selfMask()
  .connectedPixelCount({maxSize: 1024, eightConnected: true});
var internalBgMask = bgPatchSize.lt(1024).and(forestMask.not().selfMask());
```
Non-forest pixels completely enclosed within forest patches (internal holes,
clearings, agricultural pockets inside forest) are detected by connected
component analysis. A non-forest component that reaches the maxSize ceiling
(1024px ≈ 9.2ha) is assumed to be connected to the external background and
is NOT classified as a perforation.

**Known limitation:** Genuinely internal holes larger than ~9.2ha will be
missed and their adjacent forest pixels will be classified as Edge instead
of Perforation. This is acceptable at block/tehsil AOI sizes.

### Step 4 — MSPA Classification

**Class priority (Vogt et al. 2009):**
Islet has the HIGHEST priority. Edge is the RESIDUAL class — any forest
pixel not claimed by a higher-priority class becomes Edge.

Priority order: **Islet > Core > Perforation > Edge**

In the GEE `.where()` chain, lower-priority classes are painted first
and overwritten by higher-priority classes:

```javascript
var mspaRaster = ee.Image(0)
  .where(edgeMask,  2)   // Edge painted first (lowest priority / residual)
  .where(perfMask,  3)   // Perforation overwrites Edge where applicable
  .where(coreMask,  4)   // Core overwrites Perforation where applicable
  .where(isletMask, 1);  // Islet painted last (highest priority)
```

This produces a single-band uint8 raster with codes:

| Code | Class | Colour | Definition |
|------|-------|--------|------------|
| 1 | Islet | Orange | Isolated patch <1ha, no core pixels |
| 2 | Edge | Light Green | Within 100m of external non-forest boundary |
| 3 | Perforation | Yellow | Within 100m of internal clearing/hole |
| 4 | Core | Dark Green | ≥100m from any non-forest edge |
| 5 | Bridge | Blue | [Phase 3] Corridor connecting two core patches |
| 6 | Branch | Purple | [Phase 3] Dead-end connector to core |

---

## 5. Phase 3 — Bridge and Branch (Planned)

Bridge and Branch classification requires morphological skeletonization
of the non-core forest zone. The planned GEE approach:

1. Extract non-core forest (edge + perforation pixels)
2. Apply iterative thinning via focal convolutions to produce 1-pixel skeleton
3. Label core patches with unique IDs via `connectedComponents`
4. **Bridge:** skeleton pixels whose neighbourhood touches two DIFFERENT core labels
5. **Branch:** skeleton pixels connected at only ONE end to a core patch (dead-end)

---

## 6. Vectorisation

```javascript
var mspaVectors = mspaRaster.reduceToVectors({
  scale: 30, geometryType: 'polygon', eightConnected: true,
  labelProperty: 'mspa_class', maxPixels: 1e10
});
```

Each polygon includes: `class_code`, `class_label`, `area_ha`,
`source_lulc`, `edge_width_m` — satisfying Issue #228 acceptance criteria.

---

## 7. Validation Approach

Three-level validation:
1. **Visual:** Tree mask (class 6) compared against Google Satellite basemap
2. **Quantitative:** Per-class area statistics from GEE Console
3. **Cross-validation:** Comparison with JRC GuidosToolbox desktop app
   (planned — binary tree mask exported as GeoTIFF, same parameters applied)

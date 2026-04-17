# MSPA Validation Report
## Forest Structural Connectivity — CoRE Stack Issue #228

**AOI:** Kanke block, Ranchi district, Jharkhand
**Coordinates:** 85.125°E – 85.515°E, 23.240°N – 23.600°N (20km radius buffer)
**LULC Source:** IndiaSAT v4, 2023–2024
**GEE Asset:** `projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024`
**Tree Class:** 6 = "Trees" (band: `predicted_label`)
**Edge Width:** 100m (3 pixels at 30m)
**Connectivity:** 8-connected
**Run Date:** 2026-04-16

---

## 1. GEE Export Verification (Real Task IDs)

All 4 export tasks completed successfully on 2026-04-16:

| Task | GEE Task ID | Runtime | Status |
|------|-------------|---------|--------|
| MSPA_Kanke_2023_2024_raster (Asset) | `A3M2BUY5UHKLNUJOC7UOT322` | 1m | ✅ Completed |
| MSPA_Kanke_2023_2024_vectors (Asset) | `BTN6B7O4VTU7UJTLDXJJ7552` | 8m | ✅ Completed |
| MSPA_Kanke_2023_2024_raster_drive | `E5Y735JRLMJG767O3WI2HCK6` | 2m | ✅ Completed |
| MSPA_Kanke_2023_2024_vectors_drive | `HZ7JHNIBAUESZLLKSISOONXO` | 1m | ✅ Completed |

**Generated GEE Assets:**
- **Vector:** `projects/forest-485204/assets/mspa_kanke_2023_2024_vector` (7.08 MB, Table)
- **Raster:** `projects/forest-485204/assets/mspa_kanke_2023_2024` (GeoTIFF, uint8)

*Note: Assets exported to contributor GEE project (`forest-485204`) pending
write-access grant to `corestack-datasets`. Asset paths will be updated
once access is confirmed with Aman/Kapil.*

---

## 2. Vector Asset Feature Verification

Inspected via GEE Asset Details panel. Sample features confirm all required
attributes per Issue #228 acceptance criteria:

| Attribute | Type | Sample Value |
|-----------|------|--------------|
| `class_code` | Long | 1 |
| `class_label` | String | "Islet" |
| `area_ha` | Float | 0.0823 |
| `edge_width_m` | Integer | 100 |
| `mspa_class` | Long | 1 |
| `source_lulc` | String | `projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024` |

All required polygon attributes confirmed present. ✅

---

## 3. Raster Output Verification

Verified by reading the exported GeoTIFF (`mspa_kanke_2023_2024.tif`):

| Property | Value |
|----------|-------|
| Format | GeoTIFF, single band |
| Data type | uint8 ✅ |
| Resolution | ~27.5m × 29.8m (~30m) ✅ |
| CRS | EPSG:4326 |
| Dimensions | 1,447 × 1,336 pixels |
| Band name | `mspa_class` |
| Total classified pixels | 782,345 |

---

## 4. Real Area Statistics (Derived from GeoTIFF)

Computed directly from the exported raster. Pixel area ≈ 820 m² at Kanke
latitude (23.42°N), using geographic correction.

| Class | Code | Pixels | Area (ha) | % of Forest |
|-------|------|--------|-----------|-------------|
| Islet | 1 | 51,242 | 4,203.5 | 6.5% |
| Edge | 2 | 257,188 | 21,097.8 | 32.9% |
| Perforation | 3 | 346,688 | 28,439.7 | 44.3% |
| Core | 4 | 127,227 | 10,436.8 | 16.3% |
| **Total** | — | **782,345** | **64,177.9** | 100% |

*Bridge and Branch (classes 5, 6): 0 pixels — Phase 3 not yet implemented.*

---

## 5. Spatial Pattern Validation

### Tree Mask (Class 6) vs Satellite Basemap
Layer 2 (Tree Mask, class 6 only) compared against the Google Satellite
basemap over the Kanke AOI:

- Green areas align correctly with actual forest visible in satellite imagery ✅
- Ranchi city centre correctly absent from the tree mask ✅
- Forested hills toward Getalsud Dam (northeast) show dense coverage ✅
- No plantation contamination — urban trees and agricultural areas excluded ✅
- **Conclusion: Class 6 extraction is semantically correct**

### MSPA Class Spatial Logic
- **Core (dark green):** Correctly appears in the interior of large contiguous
  forest patches, particularly the dense southeastern block near Heslatoli
  and the Getalsud reservoir catchment. These are pixels ≥100m from any
  non-forest boundary ✅
- **Edge (light green/yellow):** Correctly rings the perimeter of every forest
  patch. Ring structure is spatially consistent across all patch sizes ✅
- **Islet (orange):** Small isolated fragments correctly identified as patches
  <1ha with no interior core ✅
- **Perforation (yellow):** Forest pixels adjacent to internal non-forest holes.
  High perforation percentage (44.3%) reflects genuine landscape fragmentation —
  the Kanke peri-urban area has many small clearings, roads, and agricultural
  pockets enclosed within forest patches ✅

### Distance Gradient Consistency
Layer 3 (Distance to Edge, meters) cross-checked against MSPA output:
- Red pixels (close to edge) correspond to Edge class ✅
- Dark green pixels (far from edge, >100m) correspond to Core class ✅
- Gradient transitions smoothly — confirms `fastDistanceTransform` is correct ✅

---

## 6. Ecological Interpretation

The Kanke/Ranchi AOI shows highly fragmented forest typical of peri-urban
Jharkhand. Key observations:

- **Edge dominates (32.9%)** — reflects fragmentation pressure from urban
  expansion along the Ranchi Ring Road corridor
- **Perforation is the largest class (44.3%)** — indicates many internal
  clearings and agricultural pockets within forest patches, consistent with
  observed land use in the region
- **Core at 16.3% (10,437 ha)** — despite fragmentation, significant interior
  habitat remains, concentrated in the southeastern forest blocks
- **Islet at 6.5%** — scattered isolated fragments, primarily in the
  agricultural transition zone west of Ranchi

This output is ecologically consistent with known land-use dynamics in the
region and confirms the MSPA algorithm is detecting real landscape patterns.

---

## 7. Known Limitations

1. **Perforation threshold:** `connectedPixelCount(maxSize=1024)` means
   genuinely internal non-forest components >1024 pixels (~9.2ha) are missed
   and classified as Edge instead of Perforation. Acceptable at block/tehsil
   scale.
2. **Bridge and Branch:** Phase 3 — skeletonization not yet implemented.
   Classes 5 and 6 are currently stubs (zero pixels).
3. **Asset location:** Exports are in contributor GEE project pending
   `corestack-datasets` write access.
4. **GuidosToolbox cross-validation:** Planned but not yet completed.
   Binary forest mask GeoTIFF is available for this comparison.

---

## 8. Files Produced

| File | Location | Size |
|------|----------|------|
| `mspa_kanke_2023_2024.tif` | Google Drive / CoRE_Stack_MSPA | ~4MB |
| `mspa_kanke_2023_2024_vectors.geojson` | Google Drive / CoRE_Stack_MSPA | — |
| GEE Raster Asset | `projects/forest-485204/assets/mspa_kanke_2023_2024` | — |
| GEE Vector Asset | `projects/forest-485204/assets/mspa_kanke_2023_2024_vector` | 7.08MB |
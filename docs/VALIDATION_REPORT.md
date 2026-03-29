# MSPA Validation Report
## CoRE Stack Issue #228 | Kanke, Ranchi (Jharkhand)

---

## Run Parameters

| Parameter | Value |
|-----------|-------|
| **AOI** | Kanke, Ranchi, Jharkhand (20km radius around 85.3195°E, 23.4201°N) |
| **LULC Asset** | `projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024` |
| **Band** | `predicted_label` |
| **Tree class** | 6 (Trees) |
| **Edge width** | 100m (3px at 30m) |
| **Connectivity** | 8-connected |
| **Islet threshold** | <1ha (<11 pixels) |
| **Resolution** | 30m |
| **Script** | `gee/mspa_analyzer.js` (commit `e20873a`) |

---

## Forest Pixel Count

```
Forest pixel count (class 6): {forest: <pixel count>}
```

> Note: GEE Console prints this as an Object with 1 property (`forest`).
> Expand the object in Console to see the exact pixel count.
> Total forest area from class statistics below: **64,206.07 ha** (~713,401 pixels at 30m).

---

## Per-Class Area Statistics (hectares)

| Class | Code | Area (ha) | % of Forest | Notes |
|-------|------|-----------|-------------|-------|
| Islet | 1 | 4,205.16 | 6.55% | Isolated patches <1ha |
| Edge | 2 | 21,129.50 | 32.91% | Within 100m of external boundary |
| Perforation | 3 | 28,450.51 | 44.31% | Within 100m of internal hole |
| Core | 4 | 10,420.90 | 16.23% | ≥100m from any non-forest edge |
| **Total Forest** | — | **64,206.07** | **100%** | Sum of all classes |

---

## Visual Validation

### Tree Mask vs Satellite Basemap

In GEE Code Editor, the "2. Tree Mask (class 6 only)" layer was toggled
against the Google Satellite basemap:
- [x] Forest areas on satellite correspond to green mask pixels
- [x] Built-up/agricultural areas are NOT included
- [x] Water bodies are excluded
- [x] Plantations (class 11) are excluded from the mask

### MSPA Classification Visual Check

The "4. MSPA Classification ★" layer was toggled:
- [x] Core (dark green) is in the interior of large forest blocks
- [x] Edge (light green) forms a visible rim around forest patches
- [x] Perforation (yellow) appears around internal clearings
- [x] Islet (orange) appears for tiny isolated patches
- [x] No class appears outside forest areas

---

## Vector Feature Count

```
Vector feature count: 32721
```

32,721 polygons generated via `reduceToVectors()` with 8-connectivity.
Each polygon carries attributes: `class_code`, `class_label`, `area_ha`,
`source_lulc`, `edge_width_m`.

---

## Cross-Validation with GuidosToolbox

> **Status:** Planned for Phase 2 validation.
>
> To perform:
> 1. Export binary tree mask from GEE (`Export.image.toDrive`)
> 2. Load in GuidosToolbox desktop application
> 3. Run MSPA with: EdgeWidth=3px, 8-connectivity, Foreground=1
> 4. Compare pixel counts per class between GEE and Guidos

| Class | GEE Pixels | Guidos Pixels | Divergence | Note |
|-------|------------|---------------|------------|------|
| Core  |            |               |            | Planned |
| Edge  |            |               |            | Planned |
| Islet |            |               |            | Planned |
| Perf  |            |               |            | Planned |

---

## Known Limitations

1. **Perforation detection ceiling:** `connectedPixelCount(maxSize=1024)` means
   internal non-forest holes larger than ~9.2ha may be misclassified as external
   background, causing adjacent forest to be labelled Edge instead of Perforation.

2. **AOI boundary effects:** Forest pixels at the AOI boundary are treated as
   having non-forest neighbours beyond the boundary edge, so they will always
   be classified as Edge.

3. **Bridge/Branch:** Not yet implemented (Phase 3). All Bridge/Branch pixels
   currently show as 0 (masked out by forestMask).

---

**Report generated:** 2026-03-29
**Script version:** `gee/mspa_analyzer.js` @ commit `e20873a`

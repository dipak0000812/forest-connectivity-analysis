# Forest Connectivity Analysis (MSPA) for CoRE Stack

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: GEE](https://img.shields.io/badge/Platform-Google%20Earth%20Engine-green.svg)](https://earthengine.google.com/)

## Overview

**Morphological Spatial Pattern Analysis (MSPA)** implementation for forest structural connectivity at 30m resolution, built for Google Earth Engine (GEE).

- **Data Source**: IndiaSAT LULC v4 on CoRE Stack GEE
- **Asset**: `projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024`
- **Band**: `predicted_label`
- **Tree Class**: 6 = "Trees" (explicitly excludes plantations, crops, shrubs, water, built-up)
- **Resolution**: 30 meters

---

## MSPA Classes

| Code | Class | Colour | Description |
|------|-------|--------|-------------|
| 1 | **Islet** | Orange | Isolated forest patch <1ha, no interior core |
| 2 | **Edge** | Light Green | Forest pixels within 100m of non-forest boundary |
| 3 | **Perforation** | Yellow | Forest edge adjacent to internal clearings |
| 4 | **Core** | Dark Green | Interior forest ≥100m from any edge |
| 5 | **Bridge** | Blue | [Phase 3] Core-connecting corridor |
| 6 | **Branch** | Purple | [Phase 3] Dead-end connector to core |

---

## Running the GEE Script

1. Open [Google Earth Engine Code Editor](https://code.earthengine.google.com)
2. Paste the contents of `gee/mspa_analyzer.js`
3. Click **Run** — 4 layers will render on the map
4. Click **Tasks** → Run `MSPA_Kanke_2023_2024_raster_drive` and `MSPA_Kanke_2023_2024_vectors_drive`
5. Exported files appear in Google Drive folder: `CoRE_Stack_MSPA`

**Layer legend:**
- Layer 1: IndiaSAT LULC (all classes)
- Layer 2: Tree Mask (class 6 only) — verify against Satellite basemap
- Layer 3: Distance to Edge gradient (red=near edge, green=far)
- Layer 4: MSPA Classification ★ (primary output)
- Layer 5: Internal holes (perforation source) — validation aid

---

## Quick Start (Docker Deployment)

The backend pipeline runs via Docker Compose:

```bash
cp .env.example .env
# Edit .env and supply your GEE service account credentials
docker-compose up -d --build
```

### Triggering an Analysis
Ensure you have a valid CoRE Stack JWT token:

```bash
curl -X POST http://localhost:8000/api/v1/forest-connectivity/ \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"state": "Jharkhand", "district": "Ranchi", "block": "Kanke", "lulc_year": "2023_2024"}'
```

---

## Project Structure

```
forest-connectivity-analysis/
├── gee/
│   └── mspa_analyzer.js       # PRIMARY GEE implementation ★
├── docs/
│   ├── METHODOLOGY.md          # Algorithm documentation
│   ├── VALIDATION_REPORT.md    # Test results (Kanke AOI)
│   └── API.md                  # REST API documentation
├── src/
│   ├── forest_connectivity/    # Django app (API, Celery tasks, GEE utils)
│   ├── connectivity.py         # Python reference (validation only, DEPRECATED)
│   └── vectorization.py        # Python reference (validation only, DEPRECATED)
├── docker/                     # Dockerfiles
├── monitoring/                 # Prometheus configuration
├── tests/                      # Test suite via pytest
└── requirements/               # Dependencies
```

---

## Algorithm

### Step 1: Forest Mask
Extract natural forest from IndiaSAT LULC (Class 6 = "Trees", band: `predicted_label`).
Classes 3 and 4 in IndiaSAT v4 are water body classes — not forest.
Plantations (class 11), crops (class 5), and shrubs (class 12) are excluded.

### Step 2: Distance Transform
Compute Euclidean distance from each forest pixel to nearest non-forest using
`fastDistanceTransform` (GEE). Result: distance in meters per pixel.

### Step 3: Perforation Detection
Identify internal non-forest holes via connected component analysis.
Forest pixels adjacent to internal holes are classified as Perforation.

### Step 4: MSPA Classification
Assign each forest pixel to a structural class based on Vogt et al. 2009:
- **Islet**: patches <1ha with no core
- **Core**: ≥100m from any non-forest edge
- **Perforation**: adjacent to internal clearing
- **Edge**: residual forest (within 100m of external boundary)

### Step 5: Bridge/Branch (Phase 3 — planned)
Morphological skeletonization of non-core forest to detect corridors.
See `gee/mspa_analyzer.js` lines 397–411 for planned approach.

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Edge width | 100m (3px) | Distance threshold for Core detection |
| Islet threshold | <1ha (<11px) | Maximum area for Islet classification |
| Connectivity | 8-connected | Pixel connectivity rule |
| Resolution | 30m | Pixel size (CoRE Stack standard) |

---

## Outputs

### GEE Assets
- Single-band uint8 raster (class codes 1–6, band: `mspa_class`)
- FeatureCollection vectors with attributes per polygon

### Attributes per Polygon
- `class_code` (1–6)
- `class_label` (Islet, Edge, Perforation, Core, Bridge, Branch)
- `area_ha` (hectares)
- `source_lulc` (asset path)
- `edge_width_m` (100)

---

## Python Reference (Validation Only)

Python code in `src/connectivity.py` and `src/vectorization.py` is for
**local validation only** — it does NOT implement full MSPA. The primary
implementation is `gee/mspa_analyzer.js`.

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## References

- Vogt, P. et al. (2009). Mapping spatial patterns with morphological image processing.
  *Pattern Recognition Letters*, 30(4), 456–459.
  https://www.sciencedirect.com/science/article/pii/S0167865508003267
- Vogt, P., & Riitters, K. (2017). GuidosToolbox. *European Journal of Remote Sensing*.
- JRC MSPA: https://forest.jrc.ec.europa.eu/en/activities/lpa/mspa/

---



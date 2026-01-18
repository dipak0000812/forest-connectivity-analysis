# Forest Connectivity Analysis for CoRE Stack

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

This project provides a backend solution for analyzing **forest structural connectivity** at 30-meter resolution. Structural connectivity is a key ecological indicator used to assess forest health by distinguishing between **Core**, **Edge**, and **Fragmented** forest areas.

The pipeline processes Sentinel-2–derived Land Use / Land Cover (LULC) data (standardized to 30 m) fetched from the **CoRE Stack API**. It provides a Python reference implementation and a Google Earth Engine (GEE) compatibility layer for publishing and visualization.

The system is designed to **fail fast and explicitly** if required inputs (valid credentials, geospatial metadata, or network access) are missing. Synthetic data paths or fabricated georeferencing are intentionally disallowed.

---

- Publish results as **Raster** and **Vector** assets
- Enable integration with **Area of Interest (AoI)** and **Micro-Watershed (MWS)** boundaries

---

## Architecture Overview (Python + GEE)

This project follows a **dual-engine architecture**:

### Python Backend (`src/connectivity.py`)

- **Role:** Reference implementation and primary computation engine
- **Tech Stack:** NumPy, SciPy (ndimage), Rasterio, GeoPandas
- **Use Case:** Standalone processing on local or cloud environments using CoRE Stack LULC assets

### Google Earth Engine Adapter (`src/gee_adapter.py`)

- **Role:** Compatibility and publishing layer
- **Tech Stack:** Earth Engine Python API (`earthengine-api`)
- **Use Case:** Publishing raster and vector outputs as EE assets and enabling visualization

> **Note:** The Python backend is authoritative. The GEE adapter mirrors the same logic to ensure algorithmic parity, not alternative computation.

---

## Methodological Transition

### Current Implementation Status

The current system implements a **distance-based connectivity classification** that provides a coarse approximation of forest structural patterns. This baseline approach:

- Computes Euclidean distance from forest edges
- Classifies pixels into Core (>300m), Edge (100-300m), and Fragmented (<100m)
- Serves as a validated reference for structural connectivity analysis

### Relationship to MSPA

**What is MSPA?**  
Morphological Spatial Pattern Analysis (MSPA) is a comprehensive framework for classifying forest patches into seven geometric pattern classes: Core, Islet, Perforation, Edge, Loop, Bridge, and Branch.

**Current vs. Full MSPA:**

| Aspect | Current Implementation | Full MSPA |
|--------|------------------------|-----------|
| **Pattern Classes** | 3 (Core, Edge, Fragmented) | 7 (Core, Islet, Perforation, Edge, Loop, Bridge, Branch) |
| **Methodology** | Distance-to-edge thresholding | Morphological image processing with foreground/background analysis |
| **Connectivity** | Implicit (distance-based proxy) | Explicit (structural role identification) |
| **Use Case** | Coarse fragmentation assessment | Detailed connectivity pathway analysis |

**Why This Matters:**  
The current implementation captures the most critical metric—**Core forest area**—which is essential for conservation prioritization. However, it does not distinguish between the geometric roles of non-core pixels (e.g., "Bridge" vs "Loop" vs "Branch"), which are relevant for corridor planning and fine-grained connectivity mapping.

### Roadmap

Based on maintainer feedback and CoRE Stack alignment goals:

1. **Phase 1 (Current)**: Distance-based Core/Edge/Fragmented classification
2. **Phase 2 (Planned)**: Full MSPA implementation with 7-class pattern recognition
3. **Phase 3 (Future)**: GEE-first deployment with CoRE Stack integration

**Important Note:**  
The "Fragmented" class in the current implementation is **not equivalent** to MSPA's "Islet" class. It represents **all non-core, non-edge forest**, which may include functional connectivity elements like bridges and branches. This will be refined in the full MSPA transition.

---

## Methodology

The analysis follows a **Morphological Spatial Pattern Analysis (MSPA)** approach:

### 4.1 Forest Masking (Semantic Enforcement)

Forest pixels are extracted using explicitly configured natural forest LULC class IDs. Plantation classes are excluded by design to avoid inflating connectivity metrics. Forest class definitions are configurable and visible in code; no implicit assumptions are made.

### 4.2 Distance Transformation

Euclidean distance is computed for each forest pixel to the nearest non-forest pixel using `scipy.ndimage.distance_transform_edt`.

**CRS Requirement:** Distance calculations are only performed on rasters in a projected CRS (meters). Execution fails if the input CRS is geographic (lat/lon).

### 4.3 Connectivity Classification

- **Fragmented (Class 1):** `distance < 100 m`
- **Edge (Class 2):** `100 m ≤ distance ≤ 300 m`
- **Core (Class 3):** `distance > 300 m`

Thresholds are configurable but default to the above values.

### 4.4 Vectorization

Classified raster outputs are converted into polygons for AoI / MWS-level analysis.

> For detailed technical discussion, see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Outputs

Each run produces the following artifacts:

### 5.1 Connectivity Raster

- **File:** `connectivity.tif`
- **Type:** GeoTIFF
- **Values:**
  - `1` → Fragmented
  - `2` → Edge
  - `3` → Core

### 5.2 Connectivity Polygons

- **File:** `connectivity.geojson`
- **Attributes:**
  - `connectivity_class` (1, 2, 3)
  - `class_name` (Fragmented, Edge, Core)
  - `area_ha` (polygon area in hectares)
  - `patch_size_ha` (connected forest patch size)
  - `distance_from_edge_m` (distance metric used)

### 5.3 Statistical Report

- **File:** `report.json`
- **Contents:**
  - Total forest area
  - Area by connectivity class
  - Fragmentation Index (`1 − Core / Total Forest Area`)

---

## Validation

Validation is performed through:

### Unit Tests

`tests/test_connectivity.py` validates classification thresholds and logical invariants using synthetic matrices.

### Visual Verification

`notebooks/04_validation.ipynb` compares outputs against high-resolution satellite imagery to ensure:

- Core areas are spatially interior
- Edge zones align with boundaries
- Fragmented patches are isolated

> **Note:** Validation notebooks are intended for manual inspection, not automated CI execution.

---

## Google Earth Engine Integration

To satisfy the **Option B** requirement, the GEE adapter guarantees parity with the Python backend:

| Metric             | Python (SciPy)              | GEE                         |
|--------------------|-----------------------------|-----------------------------|
| Distance Transform | `distance_transform_edt`    | `fastDistanceTransform`     |
| Edge Threshold     | 100 m (configurable)        | 100 m                       |
| Core Threshold     | 300 m (configurable)        | 300 m                       |

The adapter supports asset publishing and visualization, not independent computation.

---

## Environment Variables

Create a `.env` file in the project root:

```env
CORE_STACK_API_KEY=your_actual_key_here

# Optional: override API base URL
CORE_STACK_API_URL=https://api.core-stack.org
```

> **Note:** If credentials or network access are unavailable, the pipeline will fail with a clear error. Synthetic or placeholder data is intentionally not used.

---

## How to Run

### Prerequisites

- Python 3.11+
- pip
- (Optional) Google Earth Engine account

### Setup

```bash
git clone https://github.com/dipak0000812/forest-connectivity-analysis.git
cd forest-connectivity-analysis
pip install -r requirements.txt
```

### Run Analysis

```bash
python scripts/generate_outputs.py
```

Outputs are written to:

```
outputs/run_<timestamp>/
```

**Expected Behavior:** The script will fail if valid API credentials or data access are not available.

### Visualization

```bash
python scripts/visualize_latest_run.py
```

---

## Limitations

- **LULC Dependency:** Output quality depends entirely on the accuracy of the input LULC map.
- **AOI Edge Effects:** Core forest near AoI boundaries may be underestimated without buffering.
- **Memory Usage:** Large AoIs may require window-based tiling strategies (e.g., Rasterio windows) in production deployments.

---

## Future Extensions (Out of Scope)

- Temporal connectivity change analysis (e.g., 2020 vs 2024)
- Corridor identification via least-cost path analysis
- API deployment using FastAPI for on-demand queries

---

## Impact

This module enables early detection of forest degradation by distinguishing core forest loss from edge encroachment at field scale. It supports micro-watershed planning, prioritization of conservation interventions, and long-term forest health monitoring within the CoRE Stack ecosystem.

---

## License

MIT

# Forest Connectivity Analysis (MSPA) for CoRE Stack

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: GEE](https://img.shields.io/badge/Platform-Google%20Earth%20Engine-green.svg)](https://earthengine.google.com/)

## Overview

**Morphological Spatial Pattern Analysis (MSPA)** implementation for forest structural connectivity at 30m resolution, built for Google Earth Engine (GEE).

**Data Source**: IndiaSAT LULC assets on CoRE Stack GEE  
**Resolution**: 30 meters  
**Classes**: 7 (Core, Islet, Perforation, Edge, Loop, Bridge, Branch)

---

## MSPA Classes

| Class | ID | Definition | Ecological Role |
|-------|-----|------------|-----------------|
| **Core** | 1 | Interior forest (>100m from edge) | Primary habitat reservoir |
| **Islet** | 2 | Small isolated patches | Stepping stones |
| **Perforation** | 3 | Edge around internal gaps | Interior fragmentation |
| **Edge** | 4 | Forest adjacent to non-forest | Transition zone |
| **Loop** | 5 | Connects core to itself | Local connectivity |
| **Bridge** | 6 | Connects 2+ different cores | **Critical corridors** |
| **Branch** | 7 | Dead-end from core | Potential corridors |

---

## Quick Start (GEE Code Editor)

### 1. Open GEE Code Editor
Go to: https://code.earthengine.google.com/

### 2. Load the Script
Copy contents of `gee/mspa_analyzer.js` into Code Editor.

### 3. Run
Click "Run" to visualize:
- Forest Mask (natural forest only, plantations excluded)
- Distance from Edge
- Core Forest Areas
- MSPA Classification

---

## Project Structure

```
forest-connectivity-analysis/
├── gee/                      # PRIMARY (GEE-first)
│   ├── mspa_analyzer.js      # Main MSPA implementation
│   ├── forest_mask.js        # Forest extraction module
│   └── core_detection.js     # Core detection module
├── src/                      # REFERENCE (Python validation)
│   ├── connectivity.py       # Distance transform logic
│   └── vectorization.py      # Raster to polygon conversion
├── tests/                    # Unit tests
│   ├── test_connectivity.py
│   └── test_vectorization.py
└── docs/
    └── METHODOLOGY.md        # Algorithm documentation
```

---

## Algorithm

### Step 1: Forest Mask
Extract natural forest from IndiaSAT LULC (Classes 3, 4). Plantations excluded.

### Step 2: Distance Transform
Compute Euclidean distance from each forest pixel to nearest non-forest.

### Step 3: Core Detection
Core = forest pixels with distance ≥ EdgeWidth (100m).

### Step 4: Skeleton Analysis
Extract skeleton of non-core forest to detect bridges, branches, loops.

### Step 5: Classification
Assign each pixel to one of 7 MSPA classes based on connectivity role.

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| EdgeWidth | 100m | Distance threshold for Core detection |
| Connectivity | 8-connected | Pixel connectivity rule |
| Resolution | 30m | Pixel size (CoRE Stack standard) |

---

## Outputs

### GEE Assets
- `MSPA_30m_{year}` - 7-class raster
- `MSPA_Vectors_{year}` - Polygons with attributes

### Attributes per Polygon
- `mspa_class` (1-7)
- `class_name` (Core, Bridge, etc.)
- `area_ha` (hectares)

---

## Python Reference (Validation Only)

Python code in `src/` is for **validation against GEE outputs**, not primary execution.

```bash
# Install dependencies (optional, for validation)
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

---

## References

- Vogt, P., & Riitters, K. (2017). GuidosToolbox. *European Journal of Remote Sensing*.
- Soille, P., & Vogt, P. (2009). Morphological segmentation. *Pattern Recognition Letters*.
- JRC MSPA: https://forest.jrc.ec.europa.eu/en/activities/lpa/mspa/

---

## License

MIT

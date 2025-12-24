# Forest Connectivity Analysis for CoRE Stack

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 1. Overview
This project provides a comprehensive solution for analyzing **forest structural connectivity** at a 30-meter resolution. Structural connectivity is a key ecological indicator that reveals forest health by distinguishing between core, edge, and fragmented areas. The solution is designed to work with **CoRE Stack** LULC data and provides both a standalone Python backend and a Google Earth Engine (GEE) compatibility layer.

## 2. Problem Statement (Issue #228)
**Context:** Deforestation is often detected too late. Identifying degradation patterns (fragmentation) within forest boundaries is crucial for early intervention.
**Challenge:** Compute structural connectivity metrics at field level (30m) to:
*   Identify **Core Forest** (deep, undisturbed areas).
*   Identify **Edge Forest** (peripheral transition zones).
*   Identify **Fragmented Forest** (isolated, degraded patches).
*   Publish results as both **Raster** (images) and **Vector** (polygons) assets.

## 3. Architecture Overview (Python + GEE)
This project employs a **Dual-Engine Architecture** to ensure flexibility and scalability:

1.  **Python Backend (`src/connectivity.py`)**:
    *   **Role**: Primary Logic Engine.
    *   **Tech Stack**: NumPy, SciPy (`ndimage`), Rasterio, GeoPandas.
    *   **Use Case**: Standalone processing on local servers or cloud instances (AWS/GCP) using processed LULC assets.

2.  **GEE Adapter (`src/gee_adapter.py`)**:
    *   **Role**: Compatibility Layer.
    *   **Tech Stack**: Google Earth Engine API (`earthengine-api`).
    *   **Use Case**: Direct integration with Earth Engine workflows, enabling analysts to visualize and compute connectivity dynamically on GEE's petabyte-scale catalog.

*Both engines are strictly synchronized to ensure **Algorithmic Parity** (see Section 7).*

## 4. Methodology
The analysis follows a standard morphological spatial pattern analysis (MSPA) approach:

1.  **Forest Masking**: Extract forest pixels based on configurable LULC class IDs (e.g., 3, 4 for CoRE Stack datasets).
2.  **Distance Transformation**: Compute Euclidean distance for every forest pixel to the nearest non-forest edge.
3.  **Classification**:
    *   **Fragmented (Class 1)**: Highly edge-exposed or isolated forest pixels (distance < 100m).
    *   **Edge (Class 2)**: Distance 100m - 300m.
    *   **Core (Class 3)**: Distance > 300m.
4.  **Vectorization**: Convert classified pixels into simplified polygons for watershed-level analysis.

For deep technical details, see [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## 5. Outputs
The system generates three primary artifacts for every run:

1.  **Connectivity Map (Raster)**: A GeoTIFF (`connectivity.tif`) with pixel values 1, 2, 3 representing the connectivity classes.
2.  **Vector Polygons (GeoJSON)**: A `connectivity.geojson` file containing polygons for each class, with attributes:
    *   `class_name`: "Core", "Edge", or "Fragmented"
    *   `area_ha`: Area in hectares.
3.  **Statistical Report (JSON)**: A `report.json` summary of total forest area and the **Fragmentation Index** (`1 - Core/Total`).

## 6. Validation
Validation is ensured through two mechanisms:
1.  **Unit Tests**: `tests/test_connectivity.py` validates the core logical thresholds using synthetic matrices.
2.  **Visual Verification**: `notebooks/04_validation.ipynb` compares the output against visual inspections of high-resolution satellite imagery to ensure that "Core" areas are indeed deep inside forest blocks.

## 7. Google Earth Engine Integration
To support the project's "Option B" requirement, `src/gee_adapter.py` provides a drop-in reference for GEE. It guarantees strict parity with the Python logic:

| Metric | Python (`scipy.ndimage`) | GEE (`ee.Image`) |
| :--- | :--- | :--- |
| **Distance** | `distance_transform_edt` | `fastDistanceTransform` |
| **Edge Threshold** | 100m (Configurable) | 100m (Matched) |
| **Core Threshold** | 300m (Configurable) | 300m (Matched) |

## 8. Environment Variables
The application requires a single environment variable to fetch data from the CoRE Stack API.
Create a `.env` file in the root directory:

```bash
CORE_STACK_API_KEY=your_actual_key_here
# Optional: Override base URL if needed
# CORE_STACK_API_URL=https://api.core-stack.org
```

## 9. How to Run

### Prerequisites
*   Python 3.10+
*   `pip`
*   (Optional) Google Earth Engine account

### Setup
```bash
git clone https://github.com/dipak0000812/forest-connectivity-analysis.git
cd forest-connectivity-analysis
pip install -r requirements.txt
```

### Running the Analysis
To generate outputs for a specific Area of Interest (AoI):
```bash
python scripts/generate_outputs.py
```
*Outputs will be saved to `outputs/run_{timestamp}_{aoi}/`*

To visualize the latest results:
```bash
python scripts/visualize_latest_run.py
```

## 10. Limitations
*   **LULC Dependency**: The accuracy of connectivity analysis is strictly dependent on the quality of the input LULC map.
*   **Memory Usage**: The Python backend loads the LULC raster for the chosen AoI into memory. For extremely large states (e.g., entire MP), tiling strategies (already handled by `rasterio` windows) would be recommended for production.

## 11. Future Extensions
*   **Temporal Analysis**: Extend the pipeline to compare connectivity change over time (e.g., 2020 vs 2024).
*   **Corridor Identification**: Implement Least-Cost Path analysis to identify potential restoration corridors between isolated Core fragments.
*   **API Deployment**: Wrap the `ConnectivityAnalyzer` class in a FastAPI service for real-time requests.

## 12. Impact
This module enables early detection of forest degradation by distinguishing core forest loss from edge encroachment at field scale. It supports micro-watershed–level planning, prioritization of conservation interventions, and long-term forest health monitoring within the CoRE Stack ecosystem.

---
**License**: MIT
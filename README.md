# Forest Connectivity Analysis for CoRE Stack

> Analyzing structural connectivity of forests to identify core, edge, and fragmented areas for conservation planning using CoRE Stack Data.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Project Overview

This project addresses **Issue #228** from the [CoRE Stack Innovation Challenge](https://core-stack.org/core-stack-innovation-challenge-1st-edition/). It computes forest structural connectivity at 30m resolution to help identify degradation patterns.

## 🛠️ Installation

### Prerequisites
*   Python 3.10 or higher
*   Git
*   CoRE Stack API Key ([Register Here](https://core-stack.org/use-apis/))

### Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dipak0000812/forest-connectivity-analysis.git
    cd forest-connectivity-analysis
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key:**
    Create a `.env` file in the root directory:
    ```
    CORE_STACK_API_KEY=your_actual_api_key_here
    ```

## 📖 Usage

### Running Notebooks
Start the Jupyter Notebook server:
```bash
jupyter notebook
```
Navigate to `notebooks/` and run:
*   `00_setup_and_config.ipynb`: Test your environment and API connection.
*   `01_data_exploration.ipynb`: Explore the raw LULC data and visualize classification.
*   **`02_connectivity_analysis.ipynb`**: The main analysis pipeline. Downloads data, computes connectivity, and exports vectors.
*   `04_validation.ipynb`: Validation checks and statistical summaries.

## 📁 Project Structure
```
forest-connectivity-analysis/
├── src/
│   ├── core_stack_client.py  # API Client
│   ├── connectivity.py       # Analysis Logic
│   ├── vectorization.py      # Raster -> Vector
│   └── visualization.py      # Plotting
├── notebooks/                # Interactive Analysis
## 🧮 Definitions & Parameters

### Connectivity Classes
The logic classifies forest pixels based on their distance to the nearest non-forest edge:
*   **Fragmented (Class 1)**: Forest pixels < `edge_threshold` (100m). These are degraded or small patches.
*   **Edge (Class 2)**: Forest pixels between `edge_threshold` (100m) and `core_threshold` (300m). Transition zones.
*   **Core (Class 3)**: Forest pixels > `core_threshold` (300m). Deep, undisturbed forest.

### Fragmentation Index
A simple 0-1 metric indicating the degree of forest disturbance:
`Fragmentation Index = 1.0 - (Core Area / Total Forest Area)`
*   Values closer to **0.0** indicate healthy, intact forest.
*   Values closer to **1.0** indicate highly fragmented or degraded forest.

## 🔬 Methodology
See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for details on the core/edge classification algorithm.

## ⚖️ Python vs. GEE Logic Parity

To support both standalone Python processing and Google Earth Engine workflows, this project maintains strict algorithmic parity between `src/connectivity.py` (NumPy/SciPy) and `src/gee_adapter.py` (Earth Engine API).

| Metric | Python (`scipy.ndimage`) | GEE (`ee.Image`) |
| :--- | :--- | :--- |
| **Distance Transform** | `distance_transform_edt` (Euclidean) | `fastDistanceTransform` (Euclidean) |
| **Edge Threshold** | Configurable (default 100m) | Matched (default 100m) |
| **Core Threshold** | Configurable (default 300m) | Matched (default 300m) |
| **Vectorization** | `rasterio.features.shapes` | `reduceToVectors(scale=30)` |

The `GeeConnectivityAnalyzer` class can be used as a drop-in reference for GEE implementation, ensuring that results produced by the backend match those visualized in Earth Engine.

## 📄 License
MIT License
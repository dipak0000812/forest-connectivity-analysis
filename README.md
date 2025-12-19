# Forest Connectivity Analysis for CoRE Stack

> Analyzing structural connectivity of forests to identify core, edge, and fragmented areas for conservation planning using CoRE Stack Data.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Project Overview

This project addresses **Issue #228** from the [CoRE Stack Innovation Challenge](https://core-stack.org/core-stack-innovation-challenge-1st-edition/). It computes forest structural connectivity at 30m resolution to help identify degradation patterns.

**Key Features:**
*   **Local Processing**: Fully local workflow using Python's scientific stack (NumPy, SciPy, Rasterio).
*   **CoRE Stack Integration**: Direct API integration for fetching pre-processed LULC data.
*   **Connectivity Metrics**: Classifies forests into **Core**, **Edge**, and **Fragmented** zones.
*   **Vectorization**: Converts analysis results into vector polygons for integration with watershed boundaries.

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

4.  **Verify Setup:**
    Run the diagnostic script:
    ```bash
    python check_env.py
    ```

## 📖 Usage

### Quick Start (Python)
```python
from src.core_stack_client import CoreStackClient
from src.connectivity import ConnectivityAnalyzer
from src.visualization import plot_connectivity_map

# 1. Fetch Data
client = CoreStackClient() # Loads key from .env
lulc = client.fetch_lulc_raster("Jharkhand", "Ranchi", "Bundu", 2023)

# 2. Analyze
analyzer = ConnectivityAnalyzer(resolution=30)
forest_mask = analyzer.extract_forest_mask(lulc, forest_classes=[3, 4])
dists = analyzer.compute_distance_from_edge(forest_mask)
connectivity = analyzer.classify_connectivity(dists)

# 3. Visualize
fig = plot_connectivity_map(connectivity, transform=None)
fig.savefig("outputs/connectivity_map.png")
```

### Running Notebooks
Start the Jupyter Notebook server:
```bash
jupyter notebook
```
Navigate to `notebooks/` and run:
*   `00_setup_and_config.ipynb`: Test your environment and API connection.
*   `01_data_exploration.ipynb`: Explore the raw LULC data.
*   **`02_connectivity_analysis.ipynb`**: The main analysis pipeline.

## 📁 Project Structure
```
forest-connectivity-analysis/
├── src/
│   ├── core_stack_client.py  # API Client
│   ├── connectivity.py       # Analysis Logic
│   ├── vectorization.py      # Raster -> Vector
│   └── visualization.py      # Plotting
├── notebooks/                # Interactive Analysis
├── tests/                    # Unit Tests
├── docs/                     # Detailed Docs
│   ├── METHODOLOGY.md
│   └── API_USAGE.md
├── requirements.txt
└── README.md
```

## 🔬 Methodology
See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for details on the core/edge classification algorithm.

## 🤝 Contributing
This is a competition submission, but feedback is welcome!

## 📄 License
MIT License
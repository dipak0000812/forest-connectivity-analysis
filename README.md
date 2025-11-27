# Forest Connectivity Analysis for CoRE Stack

> Analyzing structural connectivity of forests to identify core, edge, and fragmented areas for conservation planning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Project Overview

This project addresses **Issue #228** from the [CoRE Stack Innovation Challenge](https://core-stack.org/core-stack-innovation-challenge-1st-edition/), computing forest structural connectivity at 30m resolution to help identify degradation patterns and guide conservation efforts in rural India.

### Problem Statement

Forest degradation often begins at edges and gradually fragments intact forest areas. By mapping structural connectivity patterns, we can:
- Identify vulnerable edge forests before they degrade
- Locate core forest areas requiring protection
- Detect fragmentation patterns over time
- Guide evidence-based conservation decisions

## 🚀 Features (Planned)

- [x] Project structure and development environment
- [ ] CoRE Stack API integration
- [ ] Forest mask extraction from LULC data
- [ ] Distance-from-edge calculation
- [ ] Core/Edge/Fragmented classification
- [ ] Multi-temporal analysis (2018-2023)
- [ ] Raster to vector conversion
- [ ] Interactive visualizations
- [ ] Validation against reference data

## 📊 Current Status

**Week 1:** Setting up infrastructure and exploring data
- ✅ Repository initialized
- ✅ Development environment configured
- ✅ Exploring CoRE Stack dashboard
- ⏳ Awaiting API key confirmation
- ⏳ Selecting test areas

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Git
- CoRE Stack API key ([register here](https://core-stack.org/use-apis/))

### Setup
```bash
# Clone the repository
git clone https://github.com/dipak0000812/forest-connectivity-analysis.git
cd forest-connectivity-analysis

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your API key
```

## 📖 Usage

*Coming soon - notebooks will demonstrate the full workflow*
```python
from src.core_stack_client import CoreStackClient
from src.connectivity import ConnectivityAnalyzer

# Initialize client
client = CoreStackClient(api_key="your_key")

# Fetch data
data = client.fetch_lulc_data(
    state="Jharkhand",
    district="Ranchi",
    tehsil="Bundu",
    year=2023
)

# Analyze connectivity
analyzer = ConnectivityAnalyzer(resolution=30)
connectivity = analyzer.classify_connectivity(data)
```

## 📁 Project Structure
```
forest-connectivity-analysis/
├── notebooks/          # Jupyter notebooks for analysis
├── src/               # Source code
│   ├── core_stack_client.py  # API wrapper
│   ├── connectivity.py       # Core algorithms
│   ├── vectorization.py      # Raster to vector
│   └── visualization.py      # Plotting utilities
├── data/              # Data storage (gitignored)
├── outputs/           # Generated results
├── docs/              # Documentation
├── tests/             # Unit tests
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## 🔬 Methodology

*Detailed methodology documentation coming soon in `docs/METHODOLOGY.md`*

The analysis follows these steps:
1. **Data Acquisition** - Fetch LULC rasters from CoRE Stack
2. **Forest Extraction** - Identify forest pixels
3. **Distance Calculation** - Compute distance from forest edges
4. **Classification** - Categorize as core/edge/fragmented
5. **Vectorization** - Convert raster to polygon features
6. **Validation** - Cross-check with reference data

##  Target Areas

Focusing on forest-rich regions with available CoRE Stack data:
- Jharkhand (Ranchi, Lohardaga districts)
- Odisha (Mayurbhanj, Keonjhar districts)
- Maharashtra (Gadchiroli, Chandrapur districts)

##  Contributing

This is a competition submission, but feedback and suggestions are welcome! 
- Open an issue for bugs or suggestions
- Check the [CoRE Stack Innovation Challenge](https://core-stack.org/core-stack-innovation-challenge-1st-edition/) for details

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Acknowledgments

- **CoRE Stack Team** for providing the data infrastructure
- **C4GT** for Issue #228 assignment
- Built using [CoRE Stack APIs](https://api-doc.core-stack.org/)

##  Contact

- GitHub: [@dipak0000812](https://github.com/dipak0000812)
- Project Link: [forest-connectivity-analysis](https://github.com/dipak0000812/forest-connectivity-analysis)

---

**Challenge Submission:** CoRE Stack Innovation Challenge 2025  
**Issue:** #228 - Structural Connectivity of Forests  
**Timeline:** November 2025 - December 2025

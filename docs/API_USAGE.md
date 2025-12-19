# CoRE Stack API Usage Guide

This project uses the CoRE Stack API to fetch pre-processed LULC data and watershed boundaries.

## Authentication
You need a CoRE Stack API key.
1.  Register at [core-stack.org](https://core-stack.org).
2.  Get your API Key from the dashboard.
3.  Create a `.env` file in the project root:
    ```
    CORE_STACK_API_KEY=your_api_key_here
    ```

## Python Client
Use the provided `CoreStackClient` to interact with the API.

```python
from src.core_stack_client import CoreStackClient

# Initialize
client = CoreStackClient() # Reads from .env automatically

# Check available locations
locations = client.get_available_locations()
print(locations)

# Fetch LULC Data
# state, district, tehsil names must match available locations
lulc_raster = client.fetch_lulc_raster(
    state="Jharkhand",
    district="Ranchi",
    tehsil="Bundu",
    year=2023
)

# Fetch Watershed Boundaries
boundaries = client.fetch_micro_watershed_boundaries(
    state="Jharkhand",
    district="Ranchi",
    tehsil="Bundu"
)
```

## Troubleshooting
*   **401 Unauthorized**: Check your API key in `.env`.
*   **404 Not Found**: The requested location might not be available. Use `get_available_locations()` to check coverage.

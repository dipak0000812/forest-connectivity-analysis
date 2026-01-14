"""
CoRE Stack API Client
Handles authentication and data fetching from CoRE Stack APIs
"""

import os
import requests
import rasterio
import numpy as np
import geopandas as gpd
from io import BytesIO
from typing import Dict, List, Optional, Union, Tuple
import tempfile
from dotenv import load_dotenv

load_dotenv()

class CoreStackClient:
    """Interface to CoRE Stack APIs for LULC data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key
        
        Args:
            api_key: CoRE Stack API key. If None, tries to read from environment variable 'CORE_STACK_API_KEY'
        """
        self.api_key = api_key or os.getenv("CORE_STACK_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Set CORE_STACK_API_KEY env var or pass explicitly.")
            
        # Allow overriding base URL from env (default to production)
        self.base_url = os.getenv("CORE_STACK_API_URL", "https://api.core-stack.org")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def get_available_locations(self) -> Dict:
        """
        Get list of states/districts/tehsils with data.
        Uses CoRE Stack API endpoint.
        
        Returns:
            JSON with available locations
        """
        endpoint = f"{self.base_url}/v1/locations/active"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching active locations: {e}")
            return {}

    def fetch_lulc_raster(
        self, 
        state: str, 
        district: str, 
        tehsil: str, 
        year: int
    ) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        Download LULC raster for location.
        Streams to temporary file to avoid memory issues.
        
        Args:
            state: State name
            district: District name
            tehsil: Tehsil name
            year: Year of data
            
        Returns:
            Tuple (numpy array, profile_dict) or (None, None)
        """
        endpoint = f"{self.base_url}/v1/lulc/{state}/{district}/{tehsil}"
        params = {"year": year}
        
        try:
            # Stream response to handle large files safely
            with requests.get(endpoint, headers=self.headers, params=params, stream=True) as response:
                response.raise_for_status()
                
                # Use tempfile to store raster on disk
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name
            
            # Read from disk
            try:
                with rasterio.open(tmp_path) as src:
                    array = src.read(1)
                    profile = src.profile.copy()
                    return array, profile
            finally:
                # Cleanup temp file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching LULC data: {e}")
            return None, None
        except Exception as e:
            print(f"Error reading raster data: {e}")
            return None, None

    def fetch_micro_watershed_boundaries(
        self,
        state: str,
        district: str, 
        tehsil: str
    ) -> gpd.GeoDataFrame:
        """
        Get MWS boundary polygons.
        
        Args:
           state: State name
           district: District name
           tehsil: Tehsil name

        Returns:
            GeoDataFrame with geometries, empty GDF on error
        """
        endpoint = f"{self.base_url}/v1/boundaries/mws/{state}/{district}/{tehsil}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            # Assuming API returns GeoJSON
            return gpd.read_file(BytesIO(response.content))
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching micro-watersheds: {e}")
            return gpd.GeoDataFrame()
        except Exception as e:
             print(f"Error parsing GeoJSON: {e}")
             return gpd.GeoDataFrame()

    def get_lulc_metadata(self) -> Dict:
        """
        Get LULC classification metadata.
        Tries to fetch from API, falls back to known values.
        
        Last verified: Dec 2025 from CoRE Stack technical manual.
        """
        # Try API endpoint if available
        try:
            endpoint = f"{self.base_url}/v1/lulc/metadata"
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass # Fallback to known values
            
        # Fallback based on v1 schema
        return {
            "classes": {
                1: {"name": "Water", "color": "#0000FF"},
                2: {"name": "Built-up", "color": "#FF0000"},
                3: {"name": "Deciduous Forest", "color": "#006400"},
                4: {"name": "Evergreen Forest", "color": "#228B22"},
                5: {"name": "Scrub/Degraded Forest", "color": "#FFD700"},
                6: {"name": "Agriculture", "color": "#FFFF00"},
                7: {"name": "Barren Land", "color": "#8B4513"}
                # Note: Plantation class (e.g. 8) if present should be listed here
            },
            # STRICT SEMANTICS: Only natural forest should be analyzed for connectivity.
            # Plantations are excluded by design.
            "natural_forest_classes": [3, 4], 
            "plantation_classes": [], # Explicitly empty/excluded by default
            "version": "2025-12",
            "source": "CoRE Stack Technical Manual v2"
        }

if __name__ == "__main__":
    # verification
    print("Verifying CoreStackClient module...")
    try:
        import rasterio
        import geopandas
        print("Dependencies import success.")
    except ImportError as e:
        print(f"Dependency import failed: {e}")
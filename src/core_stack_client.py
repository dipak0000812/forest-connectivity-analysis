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
from typing import Dict, List, Optional, Union
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
            
        self.base_url = "https://api.core-stack.org"
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
    ) -> Union[np.ndarray, None]:
        """
        Download LULC raster for location.
        
        Args:
            state: State name
            district: District name
            tehsil: Tehsil name
            year: Year of data
            
        Returns:
            numpy array with LULC classifications or None if failed
        """
        endpoint = f"{self.base_url}/v1/lulc/{state}/{district}/{tehsil}"
        params = {"year": year}
        
        try:
            # Note: In a real scenario, this might return a URL to a TIFF or binary content.
            # Assuming binary GeoTIFF content for this implementation as per typical patterns.
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            with rasterio.open(BytesIO(response.content)) as src:
                return src.read(1) # Read first band
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching LULC data: {e}")
            return None
        except Exception as e:
            print(f"Error reading raster data: {e}")
            return None

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
        Get LULC classification scheme.
        Which classes = forest?
        
        Returns:
            Dict with class definitions
        """
        # Hardcoding based on known CoRE Stack schema or fetching if endpoint exists
        # For now, implementing as a static return based on project updates or assumed schema
        # In a real app, this might come from specific metadata endpoint
        return {
            1: "Water",
            2: "Built-up",
            3: "Deciduous Forest",
            4: "Evergreen Forest",
            5: "Scrub/Degraded Forest",
            6: "Agriculture",
            7: "Barren Land"
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
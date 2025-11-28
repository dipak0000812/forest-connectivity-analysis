"""
CoRE Stack API Client
Handles authentication and data fetching from CoRE Stack APIs
"""

import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class CoreStackClient:
    """Client for interacting with CoRE Stack APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoRE Stack API client
        
        Args:
            api_key: API key for authentication. If None, reads from environment.
        """
        self.api_key = api_key or os.getenv("CORE_STACK_API_KEY")
        self.base_url = "https://api.core-stack.org"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_active_locations(self) -> Dict:
        """
        Get list of active locations with available data
        
        Returns:
            Dictionary containing states, districts, and tehsils with data
        """
        endpoint = f"{self.base_url}/v1/locations/active"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching active locations: {e}")
            return {}
    
    def fetch_lulc_data(self, state: str, district: str, tehsil: str, 
                        year: int) -> Dict:
        """
        Fetch LULC (Land Use Land Cover) data for a location
        
        Args:
            state: State name
            district: District name
            tehsil: Tehsil name
            year: Year of data
            
        Returns:
            LULC raster data
        """
        endpoint = f"{self.base_url}/v1/lulc/{state}/{district}/{tehsil}"
        params = {"year": year}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching LULC data: {e}")
            return {}
    
    def fetch_micro_watersheds(self, state: str, district: str, 
                              tehsil: str) -> Dict:
        """
        Fetch micro-watershed boundaries for a location
        
        Args:
            state: State name
            district: District name
            tehsil: Tehsil name
            
        Returns:
            Micro-watershed boundary data
        """
        endpoint = f"{self.base_url}/v1/boundaries/mws/{state}/{district}/{tehsil}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching micro-watersheds: {e}")
            return {}
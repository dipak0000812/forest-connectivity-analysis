"""
Forest Connectivity Analysis
Core algorithms for computing structural connectivity
"""

import numpy as np
from scipy import ndimage
from scipy.ndimage import distance_transform_edt
from skimage.morphology import label
from typing import Tuple, Dict, Optional


class ConnectivityAnalyzer:
    """Analyzes forest structural connectivity from LULC data"""
    
    def __init__(self, resolution: int = 30, core_threshold: float = 300):
        """
        Initialize connectivity analyzer
        
        Args:
            resolution: Spatial resolution in meters (default: 30m)
            core_threshold: Distance threshold for core forest in meters (default: 300m)
        """
        self.resolution = resolution
        self.core_threshold = core_threshold
        self.edge_threshold = 100  # Distance for edge classification
    
    def extract_forest_mask(self, lulc_array: np.ndarray, 
                           forest_classes: Optional[list] = None) -> np.ndarray:
        """
        Extract binary forest mask from LULC classification
        
        Args:
            lulc_array: LULC classification array
            forest_classes: List of LULC class values that represent forest
                          (default: [3, 4] - adjust based on CoRE Stack classes)
            
        Returns:
            Binary mask where 1=forest, 0=non-forest
        """
        if forest_classes is None:
            # Default forest classes - adjust based on actual CoRE Stack LULC
            forest_classes = [3, 4]  # Placeholder values
        
        forest_mask = np.isin(lulc_array, forest_classes).astype(np.uint8)
        return forest_mask
    
    def compute_distance_from_edge(self, forest_mask: np.ndarray) -> np.ndarray:
        """
        Compute Euclidean distance from forest edge for each pixel
        
        Args:
            forest_mask: Binary forest mask (1=forest, 0=non-forest)
            
        Returns:
            Distance array in meters
        """
        # Compute distance transform (in pixels)
        distance_pixels = distance_transform_edt(forest_mask)
        
        # Convert to meters
        distance_meters = distance_pixels * self.resolution
        
        return distance_meters
    
    def classify_connectivity(self, distance_array: np.ndarray) -> np.ndarray:
        """
        Classify pixels into core/edge/fragmented based on distance from edge
        
        Args:
            distance_array: Distance from edge array (in meters)
            
        Returns:
            Connectivity class array:
                0 = Non-forest
                1 = Fragmented forest
                2 = Edge forest
                3 = Core forest
        """
        connectivity_classes = np.zeros_like(distance_array, dtype=np.uint8)
        
        # Classify based on distance thresholds
        connectivity_classes[distance_array > 0] = 1  # Any forest = fragmented
        connectivity_classes[distance_array >= self.edge_threshold] = 2  # Edge forest
        connectivity_classes[distance_array >= self.core_threshold] = 3  # Core forest
        
        return connectivity_classes
    
    def analyze_patches(self, forest_mask: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Identify and analyze individual forest patches
        
        Args:
            forest_mask: Binary forest mask
            
        Returns:
            Tuple of (labeled_patches, patch_statistics)
        """
        # Label connected components
        labeled_patches, num_patches = label(forest_mask, connectivity=2, return_num=True)
        
        # Calculate statistics for each patch
        patch_stats = {}
        for patch_id in range(1, num_patches + 1):
            patch_pixels = (labeled_patches == patch_id)
            area_pixels = np.sum(patch_pixels)
            area_hectares = (area_pixels * self.resolution * self.resolution) / 10000
            
            patch_stats[patch_id] = {
                'area_ha': area_hectares,
                'num_pixels': area_pixels
            }
        
        return labeled_patches, patch_stats
    
    def compute_fragmentation_index(self, forest_mask: np.ndarray) -> float:
        """
        Compute overall fragmentation index for the landscape
        
        Args:
            forest_mask: Binary forest mask
            
        Returns:
            Fragmentation index (0-1, higher = more fragmented)
        """
        labeled_patches, num_patches = label(forest_mask, connectivity=2, return_num=True)
        
        if num_patches == 0:
            return 0.0
        
        total_forest_pixels = np.sum(forest_mask)
        if total_forest_pixels == 0:
            return 0.0
        
        # Simple fragmentation metric: number of patches relative to forest area
        fragmentation = min(1.0, num_patches / (total_forest_pixels ** 0.5))
        
        return fragmentation

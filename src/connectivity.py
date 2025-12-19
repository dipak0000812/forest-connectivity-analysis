"""
Forest Connectivity Analysis
Core algorithms for computing structural connectivity
"""

import numpy as np
from scipy.ndimage import distance_transform_edt
from typing import List, Dict, Optional, Tuple

class ConnectivityAnalyzer:
    """Analyze forest structural connectivity"""
    
    def __init__(
        self, 
        resolution: int = 30,
        core_threshold: float = 300.0,
        edge_threshold: float = 100.0
    ):
        """
        Args:
            resolution: Pixel size in meters (CoRE Stack = 30m)
            core_threshold: Distance for core forest (meters)
            edge_threshold: Distance for edge forest (meters)
        """
        self.resolution = resolution
        self.core_threshold = core_threshold
        self.edge_threshold = edge_threshold
        
    def extract_forest_mask(
        self,
        lulc_array: np.ndarray,
        forest_classes: List[int]
    ) -> np.ndarray:
        """
        Extract forest pixels from LULC.
        
        Args:
            lulc_array: 2D array from CoRE Stack
            forest_classes: Which values = forest (e.g., [3, 4])
            
        Returns:
            Binary mask (1=forest, 0=other)
        """
        mask = np.isin(lulc_array, forest_classes).astype(np.uint8)
        return mask
        
    def compute_distance_from_edge(
        self,
        forest_mask: np.ndarray
    ) -> np.ndarray:
        """
        Calculate distance from forest edge for each pixel.
        Uses scipy.ndimage.distance_transform_edt
        
        Args:
            forest_mask: Binary forest mask (1=forest, 0=non-forest)

        Returns:
            Distance in meters
        """
        # distance_transform_edt calculates distance to the nearest ZERO (background)
        # So we use the forest mask directly: non-forest is 0. 
        # Pixels inside forest (1) will have distance to nearest non-forest (0).
        distance_pixels = distance_transform_edt(forest_mask)
        distance_meters = distance_pixels * self.resolution
        return distance_meters
        
    def classify_connectivity(
        self,
        distance_array: np.ndarray
    ) -> np.ndarray:
        """
        Classify based on distance thresholds.
        
        Args:
            distance_array: Array of distances in meters

        Returns:
            Classification:
            0 = Non-forest
            1 = Fragmented (< edge_threshold)
            2 = Edge (edge_threshold to core_threshold)
            3 = Core (> core_threshold)
        """
        output = np.zeros_like(distance_array, dtype=np.uint8)
        
        # Forest pixels have distance > 0
        is_forest = distance_array > 0
        
        # 1. Fragmented / Inner Edge: < Edge threshold
        # Actually, let's follow the standard:
        # Edge forest is often defined as forest within X meters of non-forest.
        # Core forest is forest > X meters from non-forest.
        # The user spec says:
        # 1 = Fragmented (< edge_threshold)
        # 2 = Edge (edge_threshold to core_threshold)
        # 3 = Core (> core_threshold)
        
        output[is_forest & (distance_array < self.edge_threshold)] = 1
        output[(distance_array >= self.edge_threshold) & (distance_array < self.core_threshold)] = 2
        output[distance_array >= self.core_threshold] = 3
        
        return output
        
    def calculate_statistics(
        self,
        connectivity_array: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate area statistics.
        
        Args:
            connectivity_array: Classified array (0, 1, 2, 3)

        Returns:
            Dictionary with area stats in hectares and indices
        """
        # Pixel area in hectares
        pixel_area_ha = (self.resolution ** 2) / 10000.0
        
        fragmented_pixels = np.sum(connectivity_array == 1)
        edge_pixels = np.sum(connectivity_array == 2)
        core_pixels = np.sum(connectivity_array == 3)
        total_forest_pixels = fragmented_pixels + edge_pixels + core_pixels
        
        stats = {
            'core_area_ha': float(core_pixels * pixel_area_ha),
            'edge_area_ha': float(edge_pixels * pixel_area_ha),
            'fragmented_area_ha': float(fragmented_pixels * pixel_area_ha),
            'total_forest_ha': float(total_forest_pixels * pixel_area_ha)
        }
        
        # Fragmentation Index (0-1)
        # A simple metric: 1 - (Core Area / Total Forest Area)
        # 0 = All Core (Low Fragmentation), 1 = No Core (High Fragmentation)
        if stats['total_forest_ha'] > 0:
            stats['fragmentation_index'] = 1.0 - (stats['core_area_ha'] / stats['total_forest_ha'])
        else:
             stats['fragmentation_index'] = 0.0
             
        return stats

if __name__ == "__main__":
    # Simple verification with synthetic data
    print("Verifying ConnectivityAnalyzer logic...")
    analyzer = ConnectivityAnalyzer(resolution=30)
    
    # Create synthetic 10x10 mask with a 4x4 block of forest in center
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[3:7, 3:7] = 1 
    
    # Distances for center pixel (5,5) should be roughly:
    # It is at index 5. Edges are at index 2 (from low side 3) and 7 (from high side 6).
    # Distance to nearest 0 (at index 2 or 7) is ... wait.
    # Pixels at 3,3 are border. Adjacent to 2,3 (0). Sqrt(1) distance.
    
    dists = analyzer.compute_distance_from_edge(mask)
    classes = analyzer.classify_connectivity(dists)
    stats = analyzer.calculate_statistics(classes)
    
    print(f"Max distance: {dists.max():.2f}m")
    print(f"Stats: {stats}")
    print("Verification complete.")

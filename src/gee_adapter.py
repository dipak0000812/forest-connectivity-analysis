"""
GEE Adapter: forest-connectivity-analysis
Implements strict parity with local Python algorithms using Google Earth Engine.

Parity Guarantees:
- Distance: `fastDistanceTransform` (matches scipy.ndimage.distance_transform_edt)
- Classification: Identical thresholds (Core > 300m, Edge < 300m)
- Vectorization: scale=30, labelProperty='class_id'
"""

import ee

class GeeConnectivityAnalyzer:
    """
    GEE-native implementation of Forest Connectivity logic.
    """
    
    def __init__(
        self, 
        resolution: int = 30,
        core_threshold: float = 300.0,
        edge_threshold: float = 100.0
    ):
        self.resolution = resolution
        self.core_threshold = core_threshold
        self.edge_threshold = edge_threshold

    def compute_connectivity(
        self, 
        image: ee.Image, 
        aoi: ee.Geometry, 
        forest_class_ids: list = [3, 4]
    ) -> ee.Image:
        """
        Compute connectivity classes from LULC image.
        
        Args:
            image: LULC raster (e.g., from CoRE Stack assets)
            aoi: Region of Interest
            forest_class_ids: List of values representing forest
            
        Returns:
            ee.Image with bands: ['distance', 'class_id']
            class_id: 0=Non-forest, 1=Fragmented, 2=Edge, 3=Core
        """
        # 1. Create Forest Mask using remap for configurable classes
        # Remap forest classes to 1, everything else to 0
        forest_mask = image.remap(
            ee.List(forest_class_ids), 
            ee.List.repeat(1, len(forest_class_ids)), 
            0
        ).rename('forest_mask')
        
        # 2. Compute Distance to Edge
        # Invert mask: we want distance to NEAREST NON-FOREST (0)
        # fastDistanceTransform computes distance to nearest value != 0
        # So we want non-forest to be 1 for distance calc?
        # definition: "Computes the distance to the nearest non-zero pixel"
        # We want distance to non-forest. So non-forest should be non-zero.
        inverse_mask = forest_mask.Not().rename('inverse_mask')
        
        # Metric is Euclidean.
        # fastDistanceTransform results in pixels? No, units: 'pixels' (default) or 'meters'?
        # Docs: "The output is the distance in pixels."
        # We need to convert to meters.
        distance_px = inverse_mask.fastDistanceTransform(
            neighborhood=256, # Sufficiently large kernel
            units='pixels',
            metric='squared_euclidean'
        ).sqrt()
        
        distance_m = distance_px.multiply(self.resolution).rename('distance_m')

        # 3. Classify Connectivity
        # Mask out non-forest areas (distance should be 0 there effectively or ignored)
        # Apply strict thresholds
        
        # 0 = Non-forest
        # 1 = Fragmented (< edge_threshold)
        # 2 = Edge (edge_threshold to core_threshold)
        # 3 = Core (>= core_threshold)
        
        class_id = ee.Image(0).byte().rename('class_id')
        
        is_forest = forest_mask.eq(1)
        
        # Logic:
        # If forest AND dist < edge -> 1
        # If forest AND dist >= edge AND dist < core -> 2
        # If forest AND dist >= core -> 3
        
        class_id = class_id.where(is_forest.And(distance_m.lt(self.edge_threshold)), 1)
        class_id = class_id.where(is_forest.And(distance_m.gte(self.edge_threshold)).And(distance_m.lt(self.core_threshold)), 2)
        class_id = class_id.where(is_forest.And(distance_m.gte(self.core_threshold)), 3)
        
        # Mask 0 values for cleaner outputs/vectorization
        class_id = class_id.updateMask(class_id.gt(0))
        
        return image.addBands([distance_m, class_id])

    def vectorize_results(
        self, 
        connectivity_image: ee.Image, 
        aoi: ee.Geometry
    ) -> ee.FeatureCollection:
        """
        Convert connectivity class raster to polygons.
        Using explicit parameters for parity.
        """
        # Extract only the class_id band
        classes = connectivity_image.select('class_id')
        
        vectors = classes.reduceToVectors(
            geometry=aoi,
            scale=self.resolution,
            geometryType='polygon',
            labelProperty='class_id',
            eightConnected=True, # Standard for patch analysis
            bestEffort=False,
            maxPixels=1e13,
            tileScale=4 # Improves stability for large areas
        )
        
        # Add Area and Class Name
        def add_attributes(feature):
            class_id = feature.get('class_id')
            area_m2 = feature.geometry().area()
            area_ha = area_m2.divide(10000)
            
            # Map names using server-side logic if needed, or client side assumes IDs
            # Simple ee.Algorithms.If is verbose, usually simpler to stick to IDs in GEE attributes
            return feature.set({
                'area_ha': area_ha,
                'class_name': ee.Algorithms.If(ee.Number(class_id).eq(1), 'Fragmented',
                               ee.Algorithms.If(ee.Number(class_id).eq(2), 'Edge',
                               ee.Algorithms.If(ee.Number(class_id).eq(3), 'Core', 'Unknown')))
            })
            
        return vectors.map(add_attributes)

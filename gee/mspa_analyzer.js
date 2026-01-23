/*
 * MSPA Forest Connectivity Analysis - GEE Implementation
 * Issue #228: Structural Connectivity of Forests (30m)
 * 
 * This is the PRIMARY implementation (GEE-first).
 * Python backend is for validation only.
 * 
 * Data Source: IndiaSAT LULC assets on CoRE Stack GEE
 * Resolution: 30m
 * Classes: 7 (Core, Islet, Perforation, Edge, Loop, Bridge, Branch)
 */

// ============================================================
// CONFIGURATION
// ============================================================

var CONFIG = {
    // MSPA Parameters (confirmed by Prof. Seth - Jan 18 email)
    edgeWidth: 100,           // meters (default)
    edgeWidthSensitivity: 50, // meters (sensitivity check)
    connectivity: 8,          // 8-connected (forest standard)
    resolution: 30,           // meters

    // Forest class definitions (IndiaSAT schema)
    // Confirmed: Build as SEPARATE LAYER with finer structural labels
    forestClasses: [3, 4],    // Deciduous, Evergreen (natural forest only)
    plantationClasses: [8],   // Excluded by design

    // Minimal MSPA Classes (Phase 1 - confirmed scope)
    // Core, Edge, Islet, Bridge first; expand later
    CLASS_IDS: {
        NON_FOREST: 0,
        CORE: 1,
        ISLET: 2,
        PERFORATION: 3,  // Phase 2
        EDGE: 4,
        LOOP: 5,         // Phase 2
        BRIDGE: 6,
        BRANCH: 7        // Phase 2
    },

    // Visualization palette
    palette: {
        core: '006400',        // Dark green
        islet: 'FFD700',       // Gold
        perforation: '8B4513', // Brown
        edge: '90EE90',        // Light green
        loop: '00CED1',        // Dark cyan
        bridge: 'FF0000',      // Red (critical corridors)
        branch: 'FFA500'       // Orange
    }
};

// ============================================================
// DATA ACCESS (IndiaSAT LULC Assets)
// ============================================================

/**
 * Load IndiaSAT LULC from CoRE Stack GEE assets
 * 
 * NOTE: Confirm exact asset path with maintainers during Friday call.
 * These are placeholder paths based on CoRE Stack conventions.
 */
var DataAccess = {

    /**
     * Get LULC image for a region and year
     * @param {ee.Geometry} aoi - Area of Interest
     * @param {number} year - Year of data
     * @return {ee.Image} LULC raster
     */
    getLULC: function (aoi, year) {
        // Option 1: Try ImageCollection (if time-series available)
        // var lulc = ee.ImageCollection('projects/core-stack/assets/IndiaSAT/LULC')
        //   .filterBounds(aoi)
        //   .filterDate(year + '-01-01', year + '-12-31')
        //   .mosaic();

        // Option 2: Single Image asset per year
        // var lulc = ee.Image('projects/core-stack/assets/IndiaSAT/LULC_30m_' + year);

        // Option 3: Use ESRI Land Cover (publicly available, for testing)
        // This is a FALLBACK if IndiaSAT access isn't confirmed
        var esri = ee.ImageCollection('projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS')
            .filterDate(year + '-01-01', year + '-12-31')
            .mosaic()
            .clip(aoi);

        // ESRI classes: 2 = Trees
        // Remap to match our schema for testing
        var lulc = esri.remap([2], [3], 0).rename('lulc');

        print('WARNING: Using ESRI Land Cover as fallback. Confirm IndiaSAT path.');
        return lulc;
    },

    /**
     * Get AoI/MWS boundaries from Dataset API
     * NOTE: For now, define manually. Later integrate with API.
     */
    getAoI: function (name) {
        // Example: Kanke tehsil, Ranchi, Jharkhand
        var kanke = ee.Geometry.Rectangle([85.25, 23.35, 85.45, 23.55]);
        return kanke;
    }
};

// ============================================================
// FOREST MASK (Natural Forest Only)
// ============================================================

/**
 * Create binary forest mask from LULC
 * CRITICAL: Excludes plantations by design
 */
var ForestMask = {

    /**
     * Extract natural forest pixels
     * @param {ee.Image} lulc - LULC raster
     * @return {ee.Image} Binary mask (1=forest, 0=other)
     */
    create: function (lulc) {
        var mask = lulc.remap(
            CONFIG.forestClasses,
            ee.List.repeat(1, CONFIG.forestClasses.length),
            0
        ).rename('forest_mask');

        return mask;
    }
};

// ============================================================
// MSPA CORE DETECTION
// ============================================================

/**
 * MSPA Step 1: Detect Core forest areas
 * Core = forest pixels with distance >= edgeWidth from any edge
 */
var CoreDetection = {

    /**
     * Compute distance from forest edge
     * @param {ee.Image} forestMask - Binary forest mask
     * @return {ee.Image} Distance raster in meters
     */
    computeDistance: function (forestMask) {
        // fastDistanceTransform computes distance to nearest 0 (non-forest)
        // Result is in pixels, multiply by resolution for meters
        var distancePixels = forestMask.fastDistanceTransform({
            neighborhood: 256,
            units: 'pixels',
            metric: 'squared_euclidean'
        }).sqrt();

        var distanceMeters = distancePixels.multiply(CONFIG.resolution).rename('distance_m');
        return distanceMeters;
    },

    /**
     * Classify core areas
     * @param {ee.Image} distance - Distance raster in meters
     * @param {ee.Image} forestMask - Binary forest mask
     * @return {ee.Image} Core mask (1=core, 0=other)
     */
    detectCore: function (distance, forestMask) {
        var core = distance.gte(CONFIG.edgeWidth)
            .and(forestMask.eq(1))
            .rename('core');
        return core;
    }
};

// ============================================================
// MSPA EDGE & PERFORATION (Placeholder for Week 2)
// ============================================================

var EdgeDetection = {
    // To be implemented in Week 2
    detectEdge: function (distance, forestMask, core) {
        var edge = distance.lt(CONFIG.edgeWidth)
            .and(forestMask.eq(1))
            .and(core.not())
            .rename('edge');
        return edge;
    }
};

// ============================================================
// MSPA ISLET DETECTION (Placeholder for Week 2)
// ============================================================

var IsletDetection = {
    // To be implemented in Week 2
    // Islet = forest patch with NO core pixels
};

// ============================================================
// MSPA SKELETON & CONNECTIVITY (Placeholder for Week 3)
// ============================================================

var SkeletonAnalysis = {
    // To be implemented in Week 3
    // Bridge, Branch, Loop detection via morphological thinning
};

// ============================================================
// SIMPLIFIED 3-CLASS OUTPUT (For Week 1 Demo)
// ============================================================

/**
 * Temporary simplified classification
 * Will be replaced with full 7-class MSPA
 */
var SimplifiedMSPA = {

    classify: function (forestMask, distance) {
        var core = CoreDetection.detectCore(distance, forestMask);
        var edge = EdgeDetection.detectEdge(distance, forestMask, core);

        // Simplified output (not full MSPA yet)
        var classification = ee.Image(0)
            .where(forestMask.eq(1).and(core.not()).and(edge), CONFIG.CLASS_IDS.EDGE)
            .where(core, CONFIG.CLASS_IDS.CORE)
            .rename('mspa_simplified');

        return classification;
    }
};

// ============================================================
// STATISTICS
// ============================================================

var Statistics = {

    compute: function (classification, aoi) {
        var pixelArea = CONFIG.resolution * CONFIG.resolution; // 900 m²

        var stats = classification.reduceRegion({
            reducer: ee.Reducer.frequencyHistogram(),
            geometry: aoi,
            scale: CONFIG.resolution,
            maxPixels: 1e13
        });

        return stats;
    }
};

// ============================================================
// VISUALIZATION
// ============================================================

var Visualization = {

    palette: [
        '000000',  // 0 - Non-forest (black)
        CONFIG.palette.core,        // 1 - Core
        CONFIG.palette.islet,       // 2 - Islet
        CONFIG.palette.perforation, // 3 - Perforation
        CONFIG.palette.edge,        // 4 - Edge
        CONFIG.palette.loop,        // 5 - Loop
        CONFIG.palette.bridge,      // 6 - Bridge
        CONFIG.palette.branch       // 7 - Branch
    ],

    addLayers: function (lulc, forestMask, distance, core, classification, aoi) {
        Map.centerObject(aoi, 11);
        Map.addLayer(lulc, { min: 0, max: 10, palette: ['white', 'green', 'blue'] }, 'LULC', false);
        Map.addLayer(forestMask, { min: 0, max: 1, palette: ['white', 'darkgreen'] }, 'Forest Mask');
        Map.addLayer(distance, { min: 0, max: 500, palette: ['red', 'yellow', 'green'] }, 'Distance from Edge', false);
        Map.addLayer(core, { min: 0, max: 1, palette: ['white', CONFIG.palette.core] }, 'Core Forest');
        Map.addLayer(classification, { min: 0, max: 7, palette: this.palette }, 'MSPA Classification');
    }
};

// ============================================================
// MAIN EXECUTION
// ============================================================

// Define Area of Interest (Kanke, Ranchi, Jharkhand)
var aoi = DataAccess.getAoI('Kanke');
var year = 2024;

// Step 1: Load LULC data
var lulc = DataAccess.getLULC(aoi, year);
print('LULC loaded:', lulc);

// Step 2: Create forest mask (natural forest only)
var forestMask = ForestMask.create(lulc);
print('Forest mask created');

// Step 3: Compute distance from edge
var distance = CoreDetection.computeDistance(forestMask);
print('Distance transform computed');

// Step 4: Detect core areas
var core = CoreDetection.detectCore(distance, forestMask);
print('Core areas detected');

// Step 5: Simplified classification (Week 1)
var classification = SimplifiedMSPA.classify(forestMask, distance);
print('Classification complete');

// Step 6: Compute statistics
var stats = Statistics.compute(classification, aoi);
print('Statistics:', stats);

// Step 7: Visualize
Visualization.addLayers(lulc, forestMask, distance, core, classification, aoi);

// ============================================================
// EXPORTS (For Asset Publishing - Week 4)
// ============================================================

/*
Export.image.toAsset({
  image: classification,
  description: 'MSPA_Classification_Kanke_2024',
  assetId: 'projects/core-stack/assets/MSPA/Jharkhand/Ranchi/Kanke/MSPA_30m_2024',
  region: aoi,
  scale: CONFIG.resolution,
  maxPixels: 1e13
});
*/

print('=== MSPA Analysis Complete ===');
print('Week 1 Demo: Forest Mask + Core Detection');
print('Next: Edge, Perforation, Islet (Week 2)');

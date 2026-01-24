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
// MSPA BACKGROUND CLASSIFICATION (Holes vs External)
// ============================================================

var BackgroundClassification = {

    /**
     * classify background into Internal (Holes) and External
     * @param {ee.Image} forestMask
     * @return {Dictionary} {holes: ee.Image, external: ee.Image}
     */
    classify: function (forestMask) {
        var background = forestMask.not();

        // Use connectedPixelCount to distinguish small holes from large external background
        // Threshold: ~50 hectares (roughly 550 pixels at 30m resolution)
        // If > 550 pixels, assume it's connected to the outside (External)
        // If <= 550 pixels, it's an internal hole
        var maxSize = 550;
        var connectedPixels = background.connectedPixelCount({
            maxSize: maxSize,
            eightConnected: true
        });

        // Holes = background patches smaller than threshold
        var holes = background.and(connectedPixels.lt(maxSize)).rename('holes');

        // External = background patches larger than threshold (likely connected to boundary)
        var external = background.and(connectedPixels.gte(maxSize)).rename('external');

        return { holes: holes, external: external };
    }
};

// ============================================================
// MSPA EDGE & PERFORATION
// ============================================================

var EdgeDetection = {

    /**
     * Detect Edge (External) and Perforation (Internal)
     * @param {ee.Image} forestMask
     * @param {ee.Image} core
     * @param {Object} backgroundLayers - {holes, external}
     */
    detect: function (forestMask, core, backgroundLayers) {
        // Distance to External Background
        var distExternal = backgroundLayers.external
            .fastDistanceTransform({ neighborhood: 256, units: 'pixels', metric: 'squared_euclidean' })
            .sqrt()
            .multiply(CONFIG.resolution);

        // Distance to Internal Holes
        var distHoles = backgroundLayers.holes
            .fastDistanceTransform({ neighborhood: 256, units: 'pixels', metric: 'squared_euclidean' })
            .sqrt()
            .multiply(CONFIG.resolution);

        // Potential Edge pixels (Forest, Non-Core, within distance of External)
        var edgeCandidate = forestMask.eq(1)
            .and(core.not())
            .and(distExternal.lt(CONFIG.edgeWidth));

        // Potential Perforation pixels (Forest, Non-Core, within distance of Hole)
        var perfCandidate = forestMask.eq(1)
            .and(core.not())
            .and(distHoles.lt(CONFIG.edgeWidth));

        // Priority: Edge > Perforation
        // If pixel is close to both, it is Edge (External interface dominates)
        var edge = edgeCandidate.rename('edge');
        var perforation = perfCandidate.and(edge.not()).rename('perforation');

        return { edge: edge, perforation: perforation };
    }
};

// ============================================================
// MSPA ISLET DETECTION
// ============================================================

var IsletDetection = {

    /**
     * Detect Islets (Forest patches with NO core)
     * @param {ee.Image} forestMask
     * @param {ee.Image} core
     */
    detectIslets: function (forestMask, core) {
        // Identify individual forest patches
        var forestPatches = forestMask.connectedComponents({
            connectedness: ee.Kernel.plus(1),
            maxSize: 256
        });

        // Check if each patch contains ANY Class 1 (Core) pixels
        // max() reducer: if patch has core (1), result is 1. If not (0), result is 0.
        var patchHasCore = core.reduceConnectedComponents({
            reducer: ee.Reducer.max(),
            labelBand: forestPatches
        });

        // Islet = Forest Patch AND NOT HasCore
        var islet = forestMask.eq(1)
            .and(patchHasCore.not())
            .rename('islet');

        return islet;
    }
};

// ============================================================
// MSPA SKELETON & CONNECTIVITY (Placeholder for Week 3)
// ============================================================

var SkeletonAnalysis = {
    // To be implemented in Week 3
    // Bridge, Branch, Loop detection via morphological thinning
};

// ============================================================
// 4-CLASS OUTPUT (Week 2 Classification)
// ============================================================

var MSPAClassification = {

    classify: function (forestMask, core, edgeLayer, perfLayer, isletLayer) {
        // Initialize with 0
        var mspa = ee.Image(0);

        // Layer hierarchy (order matters for overwriting, though classes should be mutually exclusive)
        // 1. Core
        // 2. Islet
        // 3. Edge
        // 4. Perforation

        mspa = mspa
            .where(forestMask.eq(1), CONFIG.CLASS_IDS.CORE) // Default forest to Core (will be masked by Islet etc? No, logic separation better)

        // Reset and build up
        mspa = ee.Image(0)
            .where(forestMask.eq(1).and(core.not()), 0) // Non-core forest placeholder?

        // Strict assignment
        mspa = mspa.where(isletLayer, CONFIG.CLASS_IDS.ISLET);
        mspa = mspa.where(perfLayer, CONFIG.CLASS_IDS.PERFORATION);
        mspa = mspa.where(edgeLayer, CONFIG.CLASS_IDS.EDGE);
        mspa = mspa.where(core, CONFIG.CLASS_IDS.CORE);

        // Final mask
        mspa = mspa.updateMask(forestMask);

        return mspa.rename('mspa_class');
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

// Step 3.1: Background Classification (Holes vs External) (Part 2)
var backgroundLayers = BackgroundClassification.classify(forestMask);
print('Background classified:', backgroundLayers);

// Step 3.2: Compute distance from edge
var distance = CoreDetection.computeDistance(forestMask);
print('Distance transform computed');

// Step 4: Detect Core areas
var core = CoreDetection.detectCore(distance, forestMask);
print('Core areas detected');

// Step 5: Detect Islets (Part 2)
var islet = IsletDetection.detectIslets(forestMask, core);
print('Islets detected');

// Step 6: Detect Edge & Perforation (Part 2)
var boundaries = EdgeDetection.detect(forestMask, core, backgroundLayers);
print('Edge & Perforation detected');

// Step 7: Combine into MSPA Classification (Part 2)
var classification = MSPAClassification.classify(
    forestMask,
    core,
    boundaries.edge,
    boundaries.perforation,
    islet
);
print('Classification complete (4-class)');

// Step 8: Compute statistics
var stats = Statistics.compute(classification, aoi);
print('Statistics:', stats);

// Step 9: Visualize
Visualization.addLayers(
    lulc,
    forestMask,
    distance,
    core,
    classification,
    aoi
);
// Bonus: visualize Holes separately for debugging
Map.addLayer(backgroundLayers.holes, { palette: ['red'] }, 'Holes (Internal Background)', false);
Map.addLayer(boundaries.perforation, { palette: [CONFIG.palette.perforation] }, 'Perforation', false);

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

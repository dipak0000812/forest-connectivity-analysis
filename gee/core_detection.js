/*
 * Core Detection Module - GEE Implementation
 * 
 * MSPA Step 1: Identify core forest areas
 * Core = forest pixels with distance >= EdgeWidth from any edge
 * 
 * Based on JRC MSPA methodology:
 * https://forest.jrc.ec.europa.eu/en/activities/lpa/mspa/
 */

/**
 * Default parameters (JRC MSPA standard)
 */
var CORE_CONFIG = {
    edgeWidth: 100,     // meters (default for MSPA)
    resolution: 30,     // meters (CoRE Stack standard)
    maxNeighborhood: 256 // pixels for distance transform
};

/**
 * Compute Euclidean distance from forest edge
 * 
 * Uses GEE fastDistanceTransform which computes distance to nearest
 * background (0) pixel. Result is in pixels, converted to meters.
 * 
 * @param {ee.Image} forestMask - Binary forest mask (1=forest, 0=other)
 * @param {number} resolution - Pixel size in meters (default 30)
 * @return {ee.Image} Distance raster in meters
 */
var computeDistanceFromEdge = function (forestMask, resolution) {
    resolution = resolution || CORE_CONFIG.resolution;

    // fastDistanceTransform computes squared Euclidean distance to nearest 0
    // We need sqrt() to get actual distance, then multiply by resolution
    var distancePixels = forestMask.fastDistanceTransform({
        neighborhood: CORE_CONFIG.maxNeighborhood,
        units: 'pixels',
        metric: 'squared_euclidean'
    }).sqrt();

    var distanceMeters = distancePixels
        .multiply(resolution)
        .rename('distance_from_edge_m');

    return distanceMeters;
};

/**
 * Detect core forest areas
 * 
 * Core definition: Forest pixels with distance >= edgeWidth from any non-forest
 * 
 * @param {ee.Image} distanceRaster - Distance from edge in meters
 * @param {ee.Image} forestMask - Binary forest mask
 * @param {number} edgeWidth - Threshold for core (default 100m)
 * @return {ee.Image} Binary core mask (1=core, 0=other)
 */
var detectCore = function (distanceRaster, forestMask, edgeWidth) {
    edgeWidth = edgeWidth || CORE_CONFIG.edgeWidth;

    var core = distanceRaster.gte(edgeWidth)
        .And(forestMask.eq(1))
        .rename('core_forest')
        .toByte();

    return core;
};

/**
 * Label core areas with unique IDs
 * 
 * Required for Bridge detection (Week 3):
 * A Bridge connects 2+ DIFFERENT core areas
 * 
 * @param {ee.Image} coreMask - Binary core mask
 * @return {ee.Image} Core areas with unique labels
 */
var labelCoreAreas = function (coreMask) {
    var labeled = coreMask.connectedComponents({
        connectedness: ee.Kernel.plus(1),
        maxSize: 256
    }).select('labels').rename('core_labels');

    return labeled;
};

/**
 * Compute core statistics
 * 
 * @param {ee.Image} coreMask - Binary core mask
 * @param {ee.Geometry} aoi - Area of interest
 * @return {Object} Core area statistics
 */
var computeCoreStats = function (coreMask, aoi) {
    var pixelArea = CORE_CONFIG.resolution * CORE_CONFIG.resolution; // m²

    var corePixels = coreMask.reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: aoi,
        scale: CORE_CONFIG.resolution,
        maxPixels: 1e13
    });

    // Convert to hectares
    var coreAreaHa = ee.Number(corePixels.get('core_forest'))
        .multiply(pixelArea)
        .divide(10000);

    return {
        corePixels: corePixels.get('core_forest'),
        coreAreaHa: coreAreaHa
    };
};

// Exports
exports.CORE_CONFIG = CORE_CONFIG;
exports.computeDistanceFromEdge = computeDistanceFromEdge;
exports.detectCore = detectCore;
exports.labelCoreAreas = labelCoreAreas;
exports.computeCoreStats = computeCoreStats;

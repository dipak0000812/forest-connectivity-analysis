/*
 * Forest Mask Module - GEE Implementation
 * 
 * Extracts natural forest from LULC
 * CRITICAL: Plantations are EXCLUDED by design
 * 
 * Data Source: IndiaSAT LULC assets
 */

/**
 * Forest class definitions based on IndiaSAT schema
 * UPDATE after confirming with CoRE Stack maintainers
 */
var FOREST_CONFIG = {
    // Natural forest classes (INCLUDED)
    natural: {
        deciduous: 3,
        evergreen: 4
    },

    // Plantation classes (EXCLUDED)
    plantation: {
        commercial: 8
    },

    // Get array of natural forest class IDs
    getNaturalClasses: function () {
        return [this.natural.deciduous, this.natural.evergreen];
    }
};

/**
 * Create binary forest mask from LULC
 * 
 * @param {ee.Image} lulc - Land use land cover image
 * @param {Array} forestClasses - List of class IDs representing natural forest
 * @return {ee.Image} Binary mask (1=forest, 0=non-forest)
 * 
 * Example:
 *   var mask = createForestMask(lulc, [3, 4]);
 */
var createForestMask = function (lulc, forestClasses) {
    forestClasses = forestClasses || FOREST_CONFIG.getNaturalClasses();

    // Remap: forest classes → 1, everything else → 0
    var mask = lulc.remap(
        ee.List(forestClasses),
        ee.List.repeat(1, forestClasses.length),
        0
    ).rename('forest_mask');

    // Convert to byte for efficiency
    mask = mask.toByte();

    return mask;
};

/**
 * Validate forest mask quality
 * 
 * @param {ee.Image} mask - Binary forest mask
 * @param {ee.Geometry} aoi - Area of interest
 * @return {Object} Validation statistics
 */
var validateMask = function (mask, aoi) {
    var stats = mask.reduceRegion({
        reducer: ee.Reducer.frequencyHistogram(),
        geometry: aoi,
        scale: 30,
        maxPixels: 1e13
    });

    return stats;
};

// Exports
exports.FOREST_CONFIG = FOREST_CONFIG;
exports.createForestMask = createForestMask;
exports.validateMask = validateMask;

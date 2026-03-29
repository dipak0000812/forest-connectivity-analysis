// =============================================================================
// MSPA Forest Structural Connectivity — CoRE Stack
// Issue #228 | IndiaSAT LULC v4 2023-2024 | 30m resolution
// Classes: 1=Islet, 2=Edge, 3=Perforation, 4=Core, 5=Bridge*, 6=Branch*
// (* Bridge/Branch = Phase 3, stubs present)
//
// FIXED vs previous version:
//   - forestClasses: [6] (was wrongly [3,4] = deciduous/evergreen, NOT trees)
//   - Export blocks: uncommented and wired up
//   - Single-band output confirmed (class codes 1–6)
//   - Edge width: 100m = 3px at 30m (aligned with Vogt et al. default)
//   - Perforation: connected-component internal background detection
//
// Author: Dipak Dhangar | C4GT Contributor | CoRE Stack Issue #228
// =============================================================================


// -----------------------------------------------------------------------------
// 0. CONFIGURATION
// -----------------------------------------------------------------------------
var CONFIG = {
    // ---- Data ----
    lulcAsset: 'projects/corestack-datasets/assets/datasets/LULC_v3_river_basin/pan_india_lulc_v3_2023_2024',
    lulcBand: 'predicted_label',

    // CRITICAL FIX: Class 6 = 'Trees' in IndiaSAT v4 legend
    // Legend: {0:Background, 1:Built up, 2:Kharif water, 3:Kharif+rabi water,
    //  4:Kharif+rabi+zaid water, 5:Crops, 6:Trees, 7:Barren land,
    //  8:Single Kharif, 9:Single Non-Kharif, 10:Double Crop,
    //  11:Triple/Annual/Perennial Crop, 12:Shrubs and Scrubs}
    forestClass: 6,

    // ---- MSPA Parameters (Vogt et al. default) ----
    edgeWidth_m: 100,   // 100m edge width
    edgeWidth_px: 3,     // 100m / 30m ≈ 3 pixels
    isletMaxArea_ha: 1,     // patches < 1 ha = Islet
    connectivity8: true,  // 8-connected (standard MSPA)

    // ---- Test AOI: Kanke, Ranchi (Jharkhand) ----
    // Replace with MWS FeatureCollection for production runs
    testLon: 85.3195,
    testLat: 23.4201,
    bufferM: 20000,       // 20km radius test area
    zoom: 11,

    // ---- Export ----
    // Replace with your GEE project asset path
    exportAssetBase: 'projects/corestack-datasets/assets/forest_connectivity/',
    exportScale: 30,
    exportMaxPx: 1e10,
};


// -----------------------------------------------------------------------------
// 1. AOI — use MWS FeatureCollection for production; point buffer for test
// -----------------------------------------------------------------------------
var aoi = ee.Geometry.Point([CONFIG.testLon, CONFIG.testLat])
    .buffer(CONFIG.bufferM)
    .bounds();

// For production with MWS boundaries, replace above with:
// var aoi = ee.FeatureCollection(
//   'projects/corestack-datasets/assets/datasets/India_mws_UID_Merged'
// ).filter(ee.Filter.eq('state', 'Jharkhand'))
//  .filter(ee.Filter.eq('district', 'Ranchi'))
//  .geometry();


// -----------------------------------------------------------------------------
// 2. LOAD LULC AND EXTRACT TREE MASK
// -----------------------------------------------------------------------------
var lulc = ee.Image(CONFIG.lulcAsset)
    .select(CONFIG.lulcBand)
    .clip(aoi);

// Binary forest mask: 1 = Trees (class 6), 0 = everything else
// This explicitly excludes plantations (class 11), crops (5), shrubs (12)
var forestMask = lulc.eq(CONFIG.forestClass)
    .rename('forest')
    .uint8();

// Verify: print pixel count to confirm class 6 pixels exist in AOI
var forestCount = forestMask.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: aoi,
    scale: 30,
    maxPixels: 1e9
});
print('Forest pixel count (class 6):', forestCount);


// -----------------------------------------------------------------------------
// 3. PATCH SIZE — connected pixel count per forest patch (8-connected)
// Used for Islet detection and area statistics
// -----------------------------------------------------------------------------
var patchSize_px = forestMask.connectedPixelCount({
    maxSize: 1024,
    eightConnected: true
});

// Patch area in hectares
var patchSize_ha = patchSize_px.multiply(30 * 30).divide(10000);


// -----------------------------------------------------------------------------
// 4. DISTANCE TO EDGE
// Per-pixel Euclidean distance (meters) from each forest pixel
// to the nearest non-forest pixel.
// GEE's fastDistanceTransform returns SQUARED distance in pixels.
// -----------------------------------------------------------------------------
var distToEdge_m = forestMask
    .not()                                      // non-forest = foreground
    .fastDistanceTransform(256, 'pixels')       // squared pixel distance
    .sqrt()                                     // → pixel distance
    .multiply(30)                               // → meters
    .updateMask(forestMask)                     // forest pixels only
    .rename('dist_to_edge_m');


// -----------------------------------------------------------------------------
// 5. PERFORATION DETECTION
// Perforations = non-forest pixels completely enclosed by forest
// (internal holes, e.g. clearings inside a large forest patch)
//
// Method: connected components on non-forest.
// Background pixels with count < maxSize that NEVER touch the AOI boundary
// are internal → perforation.
//
// We approximate external background by checking if a non-forest component
// is large (effectively unbounded = external matrix).
// Internal holes are small isolated non-forest regions.
// -----------------------------------------------------------------------------
var nonForestMask = forestMask.not().selfMask();

// Count connected non-forest pixels (8-connected)
var bgPatchSize = nonForestMask.connectedPixelCount({
    maxSize: 1024,
    eightConnected: true
});

// Internal non-forest = connected background component that hit the maxSize
// ceiling is external (large open matrix); those that are small and bounded
// are internal perforations.
// Threshold: < 1024 pixels AND small relative to landscape = internal
var internalBgMask = bgPatchSize.lt(1024)
    .and(nonForestMask)
    .rename('internal_bg');

// Perforation EDGE class = forest pixels adjacent to internal holes
// (dilate internal holes by edgeWidth, intersect with forest)
var perforationEdge = internalBgMask
    .focal_max(CONFIG.edgeWidth_px, 'square', 'pixels')
    .and(forestMask)
    .rename('perf_edge');


// -----------------------------------------------------------------------------
// 6. MSPA CLASSIFICATION
// Priority order (Vogt et al. 2009):
//   Islet > Core > Perforation > Edge
//   Bridge / Branch: Phase 3 (skeletonization — stubs below)
//
// Class codes (single band):
//   1 = Islet        (isolated small patch, no core)
//   2 = Edge         (external forest edge zone)
//   3 = Perforation  (forest edge adjacent to internal hole)
//   4 = Core         (interior forest, >= edgeWidth from any edge)
//   5 = Bridge       (Phase 3 — stub, all zeros for now)
//   6 = Branch       (Phase 3 — stub, all zeros for now)
// -----------------------------------------------------------------------------

// --- 6a. ISLET ---
// Small forest patches with no core pixels
// Threshold: < 1 ha (configurable)
var isletThresh_px = CONFIG.isletMaxArea_ha * 10000 / (30 * 30); // ~11 px
var isletMask = patchSize_px.lte(isletThresh_px)
    .and(forestMask)
    .rename('islet');

// --- 6b. CORE ---
// Forest pixels >= edgeWidth meters from ANY non-forest edge
// AND not an islet
var coreMask = distToEdge_m
    .gte(CONFIG.edgeWidth_m)
    .and(forestMask)
    .and(isletMask.not())
    .rename('core');

// --- 6c. PERFORATION ---
// Forest pixels adjacent to internal holes AND not core AND not islet
var perfMask = perforationEdge
    .and(coreMask.not())
    .and(isletMask.not())
    .rename('perforation');

// --- 6d. EDGE ---
// Remaining forest pixels (external edge zone)
var edgeMask = forestMask
    .and(coreMask.not())
    .and(perfMask.not())
    .and(isletMask.not())
    .rename('edge');

// --- 6e. BRIDGE (Phase 3 stub) ---
// Narrow forest corridors connecting two separate core patches
// Requires morphological skeleton — to be implemented
var bridgeMask = ee.Image(0).clip(aoi).rename('bridge');

// --- 6f. BRANCH (Phase 3 stub) ---
// Dead-end forest connectors attached to core
var branchMask = ee.Image(0).clip(aoi).rename('branch');


// -----------------------------------------------------------------------------
// 7. COMBINE INTO SINGLE-BAND MSPA RASTER
// Confirmed format: single band, integer class codes 1–6
// -----------------------------------------------------------------------------
var mspaRaster = ee.Image(0)
    .where(edgeMask, 2)
    .where(perfMask, 3)
    .where(coreMask, 4)
    .where(isletMask, 1)
    .where(bridgeMask.gt(0), 5)
    .where(branchMask.gt(0), 6)
    .updateMask(forestMask)
    .rename('mspa_class')
    .uint8()
    .set({
        'description': 'MSPA Forest Structural Connectivity',
        'source_lulc': CONFIG.lulcAsset,
        'tree_class': CONFIG.forestClass,
        'edge_width_m': CONFIG.edgeWidth_m,
        'resolution_m': 30,
        'classes': '1=Islet,2=Edge,3=Perforation,4=Core,5=Bridge,6=Branch',
        'date_computed': new Date().toISOString().split('T')[0],
        'methodology': 'Vogt et al. 2009 MSPA via GEE fastDistanceTransform + connectedPixelCount',
        'author': 'Dipak Dhangar | C4GT | CoRE Stack Issue #228'
    });


// -----------------------------------------------------------------------------
// 8. VECTORIZATION
// Convert MSPA raster to polygons with required attributes
// per Issue #228 acceptance criteria
// -----------------------------------------------------------------------------
var mspaVectors = mspaRaster.reduceToVectors({
    geometry: aoi,
    scale: 30,
    geometryType: 'polygon',
    eightConnected: true,
    labelProperty: 'mspa_class',
    maxPixels: 1e10
});

// Add area (ha) and class label attributes to each polygon
var classLabels = ee.Dictionary({
    '1': 'Islet',
    '2': 'Edge',
    '3': 'Perforation',
    '4': 'Core',
    '5': 'Bridge',
    '6': 'Branch'
});

mspaVectors = mspaVectors.map(function (feat) {
    var classCode = ee.Number(feat.get('mspa_class')).int();
    var areaHa = feat.geometry().area().divide(10000);
    var label = classLabels.get(classCode.format('%d'));
    return feat
        .set('class_code', classCode)
        .set('class_label', label)
        .set('area_ha', areaHa)
        .set('source_lulc', CONFIG.lulcAsset)
        .set('tree_class', CONFIG.forestClass)
        .set('edge_width_m', CONFIG.edgeWidth_m);
});

print('Vector feature count:', mspaVectors.size());


// -----------------------------------------------------------------------------
// 9. VISUALIZATION
// -----------------------------------------------------------------------------
var LULC_VIS = {
    bands: [CONFIG.lulcBand],
    min: 0, max: 12,
    palette: ['000000', 'ff0000', '74ccf4', '1ca3ec', '0f5e9c',
        'f1c232', '38761d', 'A9A9A9', 'BAD93E', 'f59d22',
        'FF9371', 'b3561d', 'a9a9a9']
};

var MSPA_VIS = {
    min: 1, max: 6,
    palette: [
        'FFA500',  // 1 Islet       — orange
        '90EE90',  // 2 Edge        — light green
        'FFFF00',  // 3 Perforation — yellow
        '006400',  // 4 Core        — dark green
        '0000FF',  // 5 Bridge      — blue (stub)
        '800080'   // 6 Branch      — purple (stub)
    ]
};

Map.setCenter(CONFIG.testLon, CONFIG.testLat, CONFIG.zoom);

// Layer 1: Raw LULC
Map.addLayer(lulc, LULC_VIS, '1. IndiaSAT LULC (all classes)', false);

// Layer 2: Tree mask only — verify against satellite basemap
Map.addLayer(
    forestMask.selfMask(),
    { palette: ['38761d'] },
    '2. Tree Mask (class 6 only)'
);

// Layer 3: Distance to edge gradient
Map.addLayer(
    distToEdge_m,
    { min: 0, max: 500, palette: ['red', 'yellow', 'darkgreen'] },
    '3. Distance to Edge (m)', false
);

// Layer 4: MSPA Classification — PRIMARY OUTPUT
Map.addLayer(mspaRaster, MSPA_VIS, '4. MSPA Classification ★', true);

// Layer 5: Internal background (perforation holes) — validation aid
Map.addLayer(
    internalBgMask.selfMask(),
    { palette: ['FF0000'] },
    '5. Internal Holes (Perforation source)', false
);


// -----------------------------------------------------------------------------
// 10. AREA STATISTICS — print to Console for validation report
// -----------------------------------------------------------------------------
var classNames = ['Islet', 'Edge', 'Perforation', 'Core'];
var classCodes = [1, 2, 3, 4];

classCodes.forEach(function (code, i) {
    var areaM2 = mspaRaster.eq(code)
        .multiply(ee.Image.pixelArea())
        .reduceRegion({
            reducer: ee.Reducer.sum(),
            geometry: aoi,
            scale: 30,
            maxPixels: 1e9
        });
    print(classNames[i] + ' area (ha):',
        ee.Number(areaM2.get('mspa_class')).divide(10000));
});


// -----------------------------------------------------------------------------
// 11. EXPORTS — run from Tasks panel
// FIXED: these were commented out in previous version — now active
// -----------------------------------------------------------------------------

// --- Raster export ---
Export.image.toAsset({
    image: mspaRaster,
    description: 'MSPA_Kanke_2023_2024_raster',
    assetId: CONFIG.exportAssetBase + 'mspa_kanke_2023_2024',
    region: aoi,
    scale: CONFIG.exportScale,
    maxPixels: CONFIG.exportMaxPx,
    pyramidingPolicy: { '.default': 'mode' }
});

// --- Vector export ---
Export.table.toAsset({
    collection: mspaVectors,
    description: 'MSPA_Kanke_2023_2024_vectors',
    assetId: CONFIG.exportAssetBase + 'mspa_kanke_2023_2024_vectors'
});

// --- Also export to Drive for sharing with mentors ---
Export.image.toDrive({
    image: mspaRaster,
    description: 'MSPA_Kanke_2023_2024_raster_drive',
    folder: 'CoRE_Stack_MSPA',
    fileNamePrefix: 'mspa_kanke_2023_2024',
    region: aoi,
    scale: 30,
    maxPixels: CONFIG.exportMaxPx,
    fileFormat: 'GeoTIFF'
});

Export.table.toDrive({
    collection: mspaVectors,
    description: 'MSPA_Kanke_2023_2024_vectors_drive',
    folder: 'CoRE_Stack_MSPA',
    fileNamePrefix: 'mspa_kanke_2023_2024_vectors',
    fileFormat: 'GeoJSON'
});


// =============================================================================
// PHASE 3 NOTES — Bridge / Branch (next implementation step)
// =============================================================================
// Bridge and Branch require morphological skeletonization of non-core forest.
// GEE approach:
//   1. Extract non-core forest pixels (edge + perforation zone)
//   2. Apply iterative thinning via focal_min / focal_max convolutions
//      to approximate morphological skeleton
//   3. Bridge = skeleton pixels that connect two distinct core patch labels
//      (detect via connectedComponents on core, then check skeleton endpoints)
//   4. Branch = skeleton pixels with only one core endpoint (dead-end)
//
// Reference: Vogt et al. 2009, Pattern Recognition Letters
// https://www.sciencedirect.com/science/article/pii/S0167865508003267
// =============================================================================
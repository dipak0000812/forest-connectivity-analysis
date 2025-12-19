"""
Unit tests for Connectivity Analysis
"""
import pytest
import numpy as np
from src.connectivity import ConnectivityAnalyzer

@pytest.fixture
def analyzer():
    return ConnectivityAnalyzer(resolution=10, core_threshold=30, edge_threshold=10)

def test_initialization():
    analyzer = ConnectivityAnalyzer(resolution=30)
    assert analyzer.resolution == 30
    assert analyzer.core_threshold == 300
    assert analyzer.edge_threshold == 100

def test_extract_forest_mask():
    analyzer = ConnectivityAnalyzer()
    # 0, 1, 2, 3, 4. Forest is [3, 4]
    data = np.array([
        [1, 2, 3],
        [4, 5, 0],
        [3, 3, 1]
    ])
    mask = analyzer.extract_forest_mask(data, [3, 4])
    expected = np.array([
        [0, 0, 1],
        [1, 0, 0],
        [1, 1, 0]
    ])
    np.testing.assert_array_equal(mask, expected)

def test_compute_distance_from_edge(analyzer):
    # 5x5 array. Center 3x3 is forest.
    # Resolution = 10m
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[1:4, 1:4] = 1
    
    # Center pixel (2,2) distance to edge (border 0s).
    # Closest 0 is at (0,2), (4,2), (2,0), (2,4) -> distance = 2 pixels ??
    # Wait, distance_transform_edt computes distance to nearest zero.
    # At (2,2):
    # (1,1) is adj to (0,1)-0. Dist 1.
    # (2,2) is adj to (1,2)-1, (2,1)-1...
    # Actually, simplest check:
    # (1,1) is adjacent to (0,1) which is 0. So dist is 1 pixel = 10m.
    # (2,2) is separated from 0 by one layer of 1s.
    # Shortest path to 0: (2,2)->(1,2)->(0,2)=0. Dist 2 pixels = 20m.
    
    dists = analyzer.compute_distance_from_edge(mask)
    
    # Check center
    assert dists[2, 2] == 20.0
    # Check edge forest
    assert dists[1, 1] == 10.0
    # Check non-forest
    assert dists[0, 0] == 0.0

def test_classify_connectivity(analyzer):
    # thresholds: edge=10, core=30
    # 10m resolution
    
    # Distances:
    # 0 -> 0 (non-forest)
    # 5 -> 1 (fragmented < 10)
    # 15 -> 2 (edge >= 10, < 30)
    # 35 -> 3 (core >= 30)
    
    dists = np.array([0, 5, 15, 35])
    classes = analyzer.classify_connectivity(dists)
    
    expected = np.array([0, 1, 2, 3])
    np.testing.assert_array_equal(classes, expected)

def test_calculate_statistics(analyzer):
    # 2x2 pixels. resolution 10m. Area per pix = 100m2 = 0.01 ha.
    # classes: 3, 3, 2, 1
    classes = np.array([[3, 3], [2, 1]])
    
    stats = analyzer.calculate_statistics(classes)
    
    assert stats['core_area_ha'] == 0.02
    assert stats['edge_area_ha'] == 0.01
    assert stats['fragmented_area_ha'] == 0.01
    assert stats['total_forest_ha'] == 0.04
    # Frag index: 1 - (0.02 / 0.04) = 0.5
    assert stats['fragmentation_index'] == 0.5

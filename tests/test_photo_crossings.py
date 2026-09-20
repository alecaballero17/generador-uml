"""Tests for line crossing detection and dashed line recognition in photo_interpreter."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.photo_interpreter import PhotoInterpreter


def test_segment_intersection():
    """Two crossing segments should return their intersection point."""
    pt = PhotoInterpreter._segment_intersection((0, 0, 100, 100), (0, 100, 100, 0))
    assert pt is not None, "Crossing segments should intersect"
    assert abs(pt[0] - 50) <= 1, f"Expected x≈50, got {pt[0]}"
    assert abs(pt[1] - 50) <= 1, f"Expected y≈50, got {pt[1]}"
    print("✓ Crossing segments intersection detected correctly")


def test_parallel_no_intersection():
    """Parallel segments should not intersect."""
    pt = PhotoInterpreter._segment_intersection((0, 0, 100, 0), (0, 50, 100, 50))
    assert pt is None, "Parallel segments should not intersect"
    print("✓ Parallel segments return no intersection")


def test_endpoint_intersection_excluded():
    """Segments sharing an endpoint should not count as crossing (t/u near 0 or 1)."""
    pt = PhotoInterpreter._segment_intersection((0, 0, 50, 50), (50, 50, 100, 0))
    assert pt is None, "Endpoint-touching segments should not count as crossing"
    print("✓ Endpoint intersections are excluded")


def test_segment_near_point():
    """A point close to a segment should be detected."""
    assert PhotoInterpreter._segment_near_point((0, 0), (100, 0), (50, 10), threshold=15)
    assert not PhotoInterpreter._segment_near_point((0, 0), (100, 0), (50, 30), threshold=15)
    print("✓ Segment-near-point check works correctly")


def test_dashed_line_detection():
    """A binary image with alternating on/off pixels should be detected as dashed."""
    import numpy as np
    pi = PhotoInterpreter()
    
    # Create a 200x10 binary image with a solid horizontal line
    solid = np.zeros((10, 200), dtype=np.uint8)
    solid[5, :] = 255  # Solid line at y=5
    assert not pi._is_dashed_line(solid, (0, 5), (199, 5)), "Solid line should not be dashed"
    
    # Create a dashed line: 10 on, 10 off, repeating
    dashed = np.zeros((10, 200), dtype=np.uint8)
    for x in range(200):
        if (x // 10) % 2 == 0:
            dashed[5, x] = 255
    assert pi._is_dashed_line(dashed, (0, 5), (199, 5)), "Dashed line should be detected"
    print("✓ Dashed line detection works correctly")


def test_crossing_detection_excludes_box_interiors():
    """Crossings inside boxes should be excluded."""
    from backend.app.services.photo_interpreter import DetectedBox
    import numpy as np
    pi = PhotoInterpreter()
    
    # Two crossing segments, intersection at (50, 50) which is inside a box
    hough_lines = np.array([
        [[0, 0, 100, 100]],
        [[0, 100, 100, 0]]
    ])
    box = DetectedBox(id='b1', x=30, y=30, w=40, h=40)
    crossings = pi._detect_line_crossings(hough_lines, [box])
    assert len(crossings) == 0, "Crossings inside boxes should be excluded"
    
    # Same crossing but no box covering it
    crossings = pi._detect_line_crossings(hough_lines, [])
    assert len(crossings) == 1, "Crossings outside boxes should be detected"
    print("✓ Crossing detection correctly excludes box interiors")


if __name__ == '__main__':
    test_segment_intersection()
    test_parallel_no_intersection()
    test_endpoint_intersection_excluded()
    test_segment_near_point()
    test_dashed_line_detection()
    test_crossing_detection_excludes_box_interiors()
    print("\nAll photo crossing detection tests passed ✓")

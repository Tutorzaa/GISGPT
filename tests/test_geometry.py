"""ทดสอบ core.geometry (Ticket 02)."""
import pytest

from core import geometry as geo


class TestHaversine:
    def test_known_distance(self):
        # กรุงเทพฯ → เชียงใหม่ ≈ 590–600 km
        d = geo.haversine(13.7563, 100.5018, 18.7883, 98.9853)
        assert 550 < d < 650

    def test_zero_distance(self):
        assert geo.haversine(10.0, 10.0, 10.0, 10.0) == 0.0


class TestBBox:
    def test_center(self):
        lat, lon = geo.bbox_center((100, 14, 104, 18))
        assert abs(lat - 16.0) < 1e-9 and abs(lon - 102.0) < 1e-9

    def test_bad_length_raises(self):
        with pytest.raises(ValueError):
            geo.bbox_center((1, 2, 3))


class TestGrid:
    def test_count_and_bounds(self):
        bbox = (100, 14, 103, 16)
        pts = geo.bbox_grid(bbox, step_km=10)
        assert len(pts) > 0
        for lat, lon in pts:
            assert 14 <= lat <= 16 and 100 <= lon <= 103


class TestPointInPolygon:
    def test_inside_vs_outside(self):
        pts = [[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0], [0.0, 0.0]]
        poly = {"type": "Polygon", "coordinates": [pts]}
        assert geo.point_in_polygon(1.0, 1.0, poly) is True
        assert geo.point_in_polygon(5.0, 5.0, poly) is False


class TestBuffer:
    def test_shape(self):
        b = geo.buffer_bbox(18.0, 100.0, km=50)
        assert b[0] < 100.0 < b[2] and b[1] < 18.0 < b[3]
import unittest
import warnings

from polygon_geohasher.polygon_geohasher import (
    polygon_to_geohashes,
    geohash_to_polygon,
    geohashes_to_polygon,
)
from shapely import geometry
from shapely.errors import ShapelyDeprecationWarning


class TestSimpleMethods(unittest.TestCase):
    def test_one_geohash(self):
        test_geohash = "x1"
        test_polygon = geohash_to_polygon(test_geohash)
        polygon = geohashes_to_polygon(polygon_to_geohashes(test_polygon, 2))

        self.assertEqual(test_polygon.area, polygon.area)
        self.assertTrue(test_polygon.covers(test_polygon.intersection(polygon)))
        self.assertTrue(test_polygon.intersection(polygon).covers(test_polygon))

    def test_triangle(self):
        test_polygon = geometry.Polygon(
            [
                (-99.1795917, 19.432134),
                (-99.1656847, 19.429034),
                (-99.1776492, 19.414236),
                (-99.1795917, 19.432134),
            ]
        )

        polygon = geohashes_to_polygon(polygon_to_geohashes(test_polygon, 7))
        self.assertTrue(polygon.area <= test_polygon.area)
        self.assertTrue(
            all(polygon.covers(geometry.Point(c)) for c in polygon.boundary.coords)
        )

        polygon = geohashes_to_polygon(polygon_to_geohashes(test_polygon, 7, False))

        self.assertTrue(polygon.area >= test_polygon.area)


class TestWarnings(unittest.TestCase):
    def test_no_shapely_deprecation_warnings(self):
        test_geohashes = ["x1", "x2"]

        with warnings.catch_warnings(record=True) as captured_warnings:
            _ = geohashes_to_polygon(test_geohashes)
        
        captured_shapely_warnings = [w for w in captured_warnings if w.category == ShapelyDeprecationWarning]
        failure_message = "".join([
            warnings.formatwarning(w.message, w.category, w.filename, w.lineno, w.line)
            for w in captured_shapely_warnings
        ])
        
        self.assertEqual(
            len(captured_shapely_warnings),
            0,
            msg=failure_message
        )


if __name__ == "__main__":
    unittest.main()

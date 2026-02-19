import unittest

import polygon_geohasher as pgh
from polygon_geohasher.polygon_geohasher import (
    polygon_to_geohashes,
    geohash_to_polygon,
    geohashes_to_polygon,
)
from shapely import geometry


class TestSimpleMethods(unittest.TestCase):
    def test_top_level_exports(self):
        self.assertIs(pgh.polygon_to_geohashes, polygon_to_geohashes)
        self.assertIs(pgh.geohash_to_polygon, geohash_to_polygon)
        self.assertIs(pgh.geohashes_to_polygon, geohashes_to_polygon)

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

    def test_empty_polygon(self):
        test_polygon = geometry.Polygon()
        self.assertTrue(test_polygon.is_empty)
        self.assertEqual(polygon_to_geohashes(test_polygon, 5), set())

    def test_empty_geohashes(self):
        polygon = geohashes_to_polygon(set())
        self.assertTrue(polygon.is_empty)

    def test_inner_geohashes_are_contained(self):
        polygon = geometry.box(-1.0, -1.0, 1.0, 1.0)
        geohashes = polygon_to_geohashes(polygon, 4, True)
        self.assertTrue(geohashes)
        self.assertTrue(
            all(polygon.contains(geohash_to_polygon(g)) for g in geohashes)
        )

    def test_outer_geohashes_intersect(self):
        shell = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0)]
        hole = [
            (-0.2, -0.2),
            (0.2, -0.2),
            (0.2, 0.2),
            (-0.2, 0.2),
            (-0.2, -0.2),
        ]
        polygon = geometry.Polygon(shell, [hole])
        geohashes = polygon_to_geohashes(polygon, 4, False)
        self.assertTrue(geohashes)
        self.assertTrue(
            all(polygon.intersects(geohash_to_polygon(g)) for g in geohashes)
        )

    def test_inner_geohashes_respect_holes(self):
        shell = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0)]
        hole = [
            (-0.2, -0.2),
            (0.2, -0.2),
            (0.2, 0.2),
            (-0.2, 0.2),
            (-0.2, -0.2),
        ]
        polygon = geometry.Polygon(shell, [hole])
        hole_polygon = geometry.Polygon(hole)
        geohashes = polygon_to_geohashes(polygon, 4, True)
        self.assertTrue(geohashes)
        self.assertTrue(all(len(g) == 4 for g in geohashes))
        self.assertTrue(
            all(polygon.contains(geohash_to_polygon(g)) for g in geohashes)
        )
        self.assertTrue(
            all(not hole_polygon.intersects(geohash_to_polygon(g)) for g in geohashes)
        )

    def test_outer_geohashes_intersect_multipolygon(self):
        polygon = geometry.MultiPolygon(
            [
                geometry.box(-2.0, -2.0, -1.0, -1.0),
                geometry.box(1.0, 1.0, 2.0, 2.0),
            ]
        )
        geohashes = polygon_to_geohashes(polygon, 3, False)
        self.assertTrue(geohashes)
        self.assertTrue(all(len(g) == 3 for g in geohashes))
        self.assertTrue(
            all(polygon.intersects(geohash_to_polygon(g)) for g in geohashes)
        )


if __name__ == "__main__":
    unittest.main()

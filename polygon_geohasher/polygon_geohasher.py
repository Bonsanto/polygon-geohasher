from collections import deque

import geohash

from shapely import geometry
from shapely.ops import unary_union
from shapely.prepared import prep


def _geohash_bbox(geo):
    lat_centroid, lng_centroid, lat_offset, lng_offset = geohash.decode_exactly(geo)
    minx = lng_centroid - lng_offset
    maxx = lng_centroid + lng_offset
    miny = lat_centroid - lat_offset
    maxy = lat_centroid + lat_offset
    return minx, miny, maxx, maxy


def geohash_to_polygon(geo):
    """
    :param geo: String that represents the geohash.
    :return: Returns a Shapely's Polygon instance that represents the geohash.
    """
    minx, miny, maxx, maxy = _geohash_bbox(geo)
    return geometry.box(minx, miny, maxx, maxy)


def polygon_to_geohashes(polygon, precision, inner=True):
    """
    :param polygon: shapely polygon.
    :param precision: int. Geohashes' precision that form resulting polygon.
    :param inner: bool, default 'True'. If false, geohashes that are completely outside from the polygon are ignored.
    :return: set. Set of geohashes that form the polygon.
    """
    if polygon.is_empty:
        return set()

    inner_geohashes = set()
    visited = set()
    bounds = polygon.bounds
    minx_bound, miny_bound, maxx_bound, maxy_bound = bounds
    prepared_polygon = prep(polygon)

    centroid = polygon.centroid
    testing_geohashes = deque()
    testing_geohashes.append(geohash.encode(centroid.y, centroid.x, precision))
    neighbors = geohash.neighbors
    contains = prepared_polygon.contains
    intersects = prepared_polygon.intersects

    while testing_geohashes:
        current_geohash = testing_geohashes.popleft()
        if current_geohash in visited:
            continue
        visited.add(current_geohash)

        minx, miny, maxx, maxy = _geohash_bbox(current_geohash)
        if inner:
            if (
                minx < minx_bound
                or miny < miny_bound
                or maxx > maxx_bound
                or maxy > maxy_bound
            ):
                continue
        else:
            if (
                maxx < minx_bound
                or maxy < miny_bound
                or minx > maxx_bound
                or miny > maxy_bound
            ):
                continue

        current_polygon = geometry.box(minx, miny, maxx, maxy)

        if inner:
            if contains(current_polygon):
                inner_geohashes.add(current_geohash)
        else:
            if intersects(current_polygon):
                inner_geohashes.add(current_geohash)

        for neighbor in neighbors(current_geohash):
            if neighbor not in visited:
                testing_geohashes.append(neighbor)

    return inner_geohashes


def geohashes_to_polygon(geohashes):
    """
    :param geohashes: array-like. List of geohashes to form resulting polygon.
    :return: shapely geometry. Resulting Polygon after combining geohashes.
    """
    return unary_union([geohash_to_polygon(g) for g in geohashes])

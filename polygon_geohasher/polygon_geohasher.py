from collections import deque

import geohash

from shapely import geometry
from shapely.ops import unary_union
from shapely.prepared import prep

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def _geohash_bbox(geo):
    lat_centroid, lng_centroid, lat_offset, lng_offset = geohash.decode_exactly(geo)
    minx = lng_centroid - lng_offset
    maxx = lng_centroid + lng_offset
    miny = lat_centroid - lat_offset
    maxy = lat_centroid + lat_offset
    return minx, miny, maxx, maxy


def _bounds_intersect(bounds, other_bounds):
    minx, miny, maxx, maxy = bounds
    ominx, ominy, omaxx, omaxy = other_bounds
    if maxx < ominx or omaxx < minx:
        return False
    if maxy < ominy or omaxy < miny:
        return False
    return True


def _cover_bounds(bounds, precision):
    minx, miny, maxx, maxy = bounds
    center_lat = (miny + maxy) / 2.0
    center_lon = (minx + maxx) / 2.0
    start = geohash.encode(center_lat, center_lon, precision)

    queue = deque([start])
    visited = set()
    results = []
    neighbors = geohash.neighbors

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        current_bounds = _geohash_bbox(current)
        if not _bounds_intersect(current_bounds, bounds):
            continue

        results.append(current)
        for neighbor in neighbors(current):
            if neighbor not in visited:
                queue.append(neighbor)

    return results


def _expand_children(prefix, target_precision, out_set):
    if len(prefix) == target_precision:
        out_set.add(prefix)
        return

    stack = [prefix]
    base32 = _BASE32
    while stack:
        current = stack.pop()
        if len(current) == target_precision:
            out_set.add(current)
            continue
        for char in base32:
            stack.append(current + char)


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

    prepared_polygon = prep(polygon)
    bounds = polygon.bounds
    seed_precision = min(precision, 3)
    seeds = _cover_bounds(bounds, seed_precision)

    results = set()
    stack = list(seeds)
    contains = prepared_polygon.contains
    intersects = prepared_polygon.intersects

    while stack:
        current = stack.pop()
        current_bounds = _geohash_bbox(current)
        if not _bounds_intersect(current_bounds, bounds):
            continue

        current_polygon = geometry.box(*current_bounds)
        if not intersects(current_polygon):
            continue

        if inner:
            if contains(current_polygon):
                if len(current) == precision:
                    results.add(current)
                else:
                    _expand_children(current, precision, results)
            elif len(current) < precision:
                for char in _BASE32:
                    stack.append(current + char)
            continue

        if len(current) == precision:
            results.add(current)
            continue

        if contains(current_polygon):
            _expand_children(current, precision, results)
        else:
            for char in _BASE32:
                stack.append(current + char)

    return results


def geohashes_to_polygon(geohashes):
    """
    :param geohashes: array-like. List of geohashes to form resulting polygon.
    :return: shapely geometry. Resulting Polygon after combining geohashes.
    """
    return unary_union([geohash_to_polygon(g) for g in geohashes])

import argparse
import os
import queue
import statistics
import sys
import time

import geohash
from shapely import geometry

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from polygon_geohasher import polygon_to_geohashes


def legacy_geohash_to_polygon(geo):
    lat_centroid, lng_centroid, lat_offset, lng_offset = geohash.decode_exactly(geo)
    corner_1 = (lat_centroid - lat_offset, lng_centroid - lng_offset)[::-1]
    corner_2 = (lat_centroid - lat_offset, lng_centroid + lng_offset)[::-1]
    corner_3 = (lat_centroid + lat_offset, lng_centroid + lng_offset)[::-1]
    corner_4 = (lat_centroid + lat_offset, lng_centroid - lng_offset)[::-1]
    return geometry.Polygon([corner_1, corner_2, corner_3, corner_4, corner_1])


def legacy_polygon_to_geohashes(polygon, precision, inner=True):
    if polygon.is_empty:
        return set()

    inner_geohashes = set()
    outer_geohashes = set()

    envelope = polygon.envelope
    centroid = polygon.centroid

    testing_geohashes = queue.Queue()
    testing_geohashes.put(geohash.encode(centroid.y, centroid.x, precision))

    while not testing_geohashes.empty():
        current_geohash = testing_geohashes.get()

        if (
            current_geohash not in inner_geohashes
            and current_geohash not in outer_geohashes
        ):
            current_polygon = legacy_geohash_to_polygon(current_geohash)

            condition = (
                envelope.contains(current_polygon)
                if inner
                else envelope.intersects(current_polygon)
            )

            if condition:
                if inner:
                    if polygon.contains(current_polygon):
                        inner_geohashes.add(current_geohash)
                    else:
                        outer_geohashes.add(current_geohash)
                else:
                    if polygon.intersects(current_polygon):
                        inner_geohashes.add(current_geohash)
                    else:
                        outer_geohashes.add(current_geohash)
                for neighbor in geohash.neighbors(current_geohash):
                    if (
                        neighbor not in inner_geohashes
                        and neighbor not in outer_geohashes
                    ):
                        testing_geohashes.put(neighbor)

    return inner_geohashes


def build_polygons():
    triangle = geometry.Polygon(
        [
            (-99.1795917, 19.432134),
            (-99.1656847, 19.429034),
            (-99.1776492, 19.414236),
            (-99.1795917, 19.432134),
        ]
    )

    center = geometry.Point(-99.173, 19.423)
    buffer_small = center.buffer(0.02, resolution=32)
    buffer_large = center.buffer(0.06, resolution=32)

    return {
        "triangle": triangle,
        "buffer_small": buffer_small,
        "buffer_large": buffer_large,
    }


def time_call(fn, *args, iterations=5):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn(*args)
        times.append(time.perf_counter() - start)
    return times


def format_seconds(value):
    if value < 1:
        return f"{value * 1000:.2f} ms"
    return f"{value:.2f} s"


def summarize(times):
    return {
        "min": min(times),
        "median": statistics.median(times),
        "mean": statistics.mean(times),
    }


def run_case(name, polygon, precision, inner, iterations, validate):
    if validate:
        legacy = legacy_polygon_to_geohashes(polygon, precision, inner)
        optimized = polygon_to_geohashes(polygon, precision, inner)
        if legacy != optimized:
            raise RuntimeError(f"Mismatch for {name} (inner={inner})")

    legacy_times = time_call(
        legacy_polygon_to_geohashes, polygon, precision, inner, iterations=iterations
    )
    optimized_times = time_call(
        polygon_to_geohashes, polygon, precision, inner, iterations=iterations
    )

    legacy_stats = summarize(legacy_times)
    optimized_stats = summarize(optimized_times)
    speedup = legacy_stats["median"] / optimized_stats["median"]

    mode = "inner" if inner else "outer"
    print(f"{name} | precision={precision} | mode={mode}")
    print(
        f"  legacy:    {format_seconds(legacy_stats['median'])} median "
        f"(min {format_seconds(legacy_stats['min'])})"
    )
    print(
        f"  optimized: {format_seconds(optimized_stats['median'])} median "
        f"(min {format_seconds(optimized_stats['min'])})"
    )
    print(f"  speedup:   {speedup:.2f}x")
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="Compare legacy vs optimized polygon_to_geohashes performance."
    )
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--precision", type=int, default=7)
    parser.add_argument("--inner", action="store_true", help="Only benchmark inner=True")
    parser.add_argument("--outer", action="store_true", help="Only benchmark inner=False")
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip output validation between legacy and optimized.",
    )
    args = parser.parse_args()

    if args.inner and not args.outer:
        modes = [True]
    elif args.outer and not args.inner:
        modes = [False]
    else:
        modes = [True, False]

    polygons = build_polygons()
    for name, polygon in polygons.items():
        for inner in modes:
            run_case(
                name,
                polygon,
                args.precision,
                inner,
                args.iterations,
                validate=not args.no_validate,
            )


if __name__ == "__main__":
    main()

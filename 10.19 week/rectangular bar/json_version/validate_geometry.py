"""Measure saved rectangular-bar STEP and STL files against JSON dimensions.

Importing this module uses only Python's standard library. ``cadgen`` is loaded
only when STEP validation runs, after the caller has validated its JSON input.
"""

from __future__ import annotations

import math
import struct
from collections import defaultdict
from pathlib import Path


def _xyz(vector):
    return [float(vector.X), float(vector.Y), float(vector.Z)]


def _close_vector(actual, expected, tolerances):
    return all(
        math.isfinite(a) and abs(a - e) <= tolerance
        for a, e, tolerance in zip(actual, expected, tolerances)
    )


def _read_stl_triangles(path):
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if len(data) == 84 + 50 * count:
            triangles = []
            for i in range(count):
                row = struct.unpack_from("<12fH", data, 84 + 50 * i)
                triangles.append((row[3:6], row[6:9], row[9:12]))
            if not triangles:
                raise ValueError("STL contains no triangles")
            return triangles, "binary"
    vertices = []
    for line in data.decode("ascii").splitlines():
        tokens = line.split()
        if tokens and tokens[0].lower() == "vertex":
            if len(tokens) != 4:
                raise ValueError("STL vertex must contain three coordinates")
            vertices.append(tuple(map(float, tokens[1:])))
    if not vertices or len(vertices) % 3:
        raise ValueError("STL did not contain complete triangles")
    return [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)], "ascii"


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _check_step(path, expected_size, expected_volume, length_tolerances, volume_tolerance):
    from cadgen import read_step
    from cadgen.geometry import boundary_edges

    shape = read_step(str(path))
    bounds = shape.bounding_box()
    solids = list(shape.solids())
    shells = list(shape.shells())
    free_edge_counts = [len(boundary_edges(shell)) for shell in shells]
    size = _xyz(bounds.size)
    minimum = _xyz(bounds.min)
    maximum = _xyz(bounds.max)
    volumes = [float(solid.volume) for solid in solids]
    volume = float(shape.volume)
    valid = bool(shape.is_valid)
    checks = {
        "bounding_box_size": _close_vector(size, expected_size, length_tolerances),
        "origin_minimum": _close_vector(minimum, [0.0] * 3, length_tolerances),
        "bounding_box_maximum": _close_vector(maximum, expected_size, length_tolerances),
        "volume": math.isfinite(volume) and abs(volume - expected_volume) <= volume_tolerance,
        "one_solid": len(solids) == 1,
        "valid_brep": valid,
        "positive_solid_volumes": bool(volumes) and all(math.isfinite(v) and v > 0 for v in volumes),
        "closed_shells": bool(shells) and all(n == 0 for n in free_edge_counts),
    }
    return {
        "file": path.name,
        "selected_geometry": "all geometry in saved STEP document",
        "bounding_box_min_mm": minimum,
        "bounding_box_max_mm": maximum,
        "bounding_box_size_mm": size,
        "volume_mm3": volume,
        "solid_count": len(solids),
        "individual_solid_volumes_mm3": volumes,
        "valid_brep": valid,
        "shell_count": len(shells),
        "shell_boundary_edge_counts": free_edge_counts,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _check_stl(path, expected_size, expected_volume, length_tolerances, volume_tolerance):
    triangles, encoding = _read_stl_triangles(path)
    vertices = [vertex for triangle in triangles for vertex in triangle]
    if not all(math.isfinite(x) for vertex in vertices for x in vertex):
        raise ValueError("STL contains non-finite vertex coordinates")
    minimum = [min(v[i] for v in vertices) for i in range(3)]
    maximum = [max(v[i] for v in vertices) for i in range(3)]
    size = [maximum[i] - minimum[i] for i in range(3)]
    # This planar box export shares exactly coincident vertex coordinates.
    unique = {point: i for i, point in enumerate(sorted(set(vertices)))}
    uses = defaultdict(list)
    degenerate = 0
    volume_terms = []
    adjacency = defaultdict(set)
    for face_id, (a, b, c) in enumerate(triangles):
        normal = _cross(_sub(b, a), _sub(c, a))
        # No absolute area threshold: small valid dimensions must remain valid.
        degenerate += all(component == 0.0 for component in normal)
        volume_terms.append(_dot(a, _cross(b, c)) / 6.0)
        ids = [unique[a], unique[b], unique[c]]
        for u, v in zip(ids, ids[1:] + ids[:1]):
            key = (min(u, v), max(u, v))
            uses[key].append((face_id, 1 if u < v else -1))
    signed_volume = math.fsum(volume_terms)
    boundary = sum(len(edge_uses) == 1 for edge_uses in uses.values())
    nonmanifold = sum(len(edge_uses) != 2 for edge_uses in uses.values())
    inconsistent = sum(len(e) == 2 and e[0][1] == e[1][1] for e in uses.values())
    for edge_uses in uses.values():
        ids = [face_id for face_id, _ in edge_uses]
        for face_id in ids:
            adjacency[face_id].update(other for other in ids if other != face_id)
    remaining = set(range(len(triangles)))
    components = 0
    while remaining:
        components += 1
        pending = [remaining.pop()]
        while pending:
            neighbors = adjacency[pending.pop()] & remaining
            remaining.difference_update(neighbors)
            pending.extend(neighbors)
    watertight = nonmanifold == 0 and degenerate == 0
    checks = {
        "bounding_box_size": _close_vector(size, expected_size, length_tolerances),
        "origin_minimum": _close_vector(minimum, [0.0] * 3, length_tolerances),
        "bounding_box_maximum": _close_vector(maximum, expected_size, length_tolerances),
        "volume": math.isfinite(signed_volume) and abs(signed_volume - expected_volume) <= volume_tolerance,
        "positive_signed_volume": signed_volume > 0,
        "watertight": watertight,
        "consistent_winding": inconsistent == 0,
        "one_connected_component": components == 1,
        "nondegenerate_triangles": degenerate == 0,
    }
    return {
        "file": path.name,
        "selected_geometry": "all triangles in saved STL document",
        "encoding": encoding,
        "assumed_units": "mm (STL does not store units)",
        "bounding_box_min_mm": minimum,
        "bounding_box_max_mm": maximum,
        "bounding_box_size_mm": size,
        "signed_volume_mm3": signed_volume,
        "triangle_count": len(triangles),
        "unique_vertex_count": len(unique),
        "boundary_edge_count": boundary,
        "nonmanifold_edge_count": nonmanifold,
        "inconsistently_wound_edge_count": inconsistent,
        "degenerate_triangle_count": degenerate,
        "connected_component_count": components,
        "watertight": watertight,
        "checks": checks,
        "passed": all(checks.values()),
    }


def validate_outputs(directory: Path, dimensions: dict) -> dict:
    """Return measurements/checks for rectangular_bar.step and .stl.

    ``dimensions`` contains ``units='mm'`` and positive numeric ``length``,
    ``width`` and ``height``. This function does not modify files. Import/read
    failures raise an exception; geometric discrepancies set ``passed=False``.
    """
    if dimensions.get("units") != "mm":
        raise ValueError("Validation supports only units='mm'")
    expected_size = []
    for key in ("length", "width", "height"):
        value = dimensions.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Dimension '{key}' must be a positive number")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Dimension '{key}' must be finite and greater than zero")
        expected_size.append(float(value))
    expected_volume = math.prod(expected_size)
    if not math.isfinite(expected_volume) or expected_volume <= 0:
        raise ValueError("Dimension product must be finite and greater than zero")
    # STL stores float32 coordinates; tolerances follow the current JSON scale.
    length_tolerances = [max(1e-6, abs(size) * 1e-6) for size in expected_size]
    volume_tolerance = max(1e-3, expected_volume * 1e-6)
    directory = Path(directory)
    report = {
        "units": {"length": "mm", "volume": "mm^3"},
        "input_dimensions": dict(dimensions),
        "expected_bounding_box_size_mm": expected_size,
        "expected_volume_mm3": expected_volume,
        "length_tolerances_mm": length_tolerances,
        "volume_tolerance_mm3": volume_tolerance,
        "tolerance_policy": {
            "length_absolute_mm": 1e-6,
            "length_relative": 1e-6,
            "volume_absolute_mm3": 1e-3,
            "volume_relative": 1e-6,
            "combination": "maximum of absolute and relative tolerance",
        },
        "step": _check_step(directory / "rectangular_bar.step", expected_size, expected_volume,
                            length_tolerances, volume_tolerance),
        "stl": _check_stl(directory / "rectangular_bar.stl", expected_size, expected_volume,
                          length_tolerances, volume_tolerance),
        "untested": ["material properties", "manufacturing tolerances"],
    }
    report["passed"] = report["step"]["passed"] and report["stl"]["passed"]
    return report

"""Minimal STL reader (binary + ASCII), stdlib-only.

Reads a facet-soup STL and returns a deduplicated, indexed mesh
(vertices + triangle index triples) -- the shape 3MF's <mesh> element
requires. No external geometry ever enters the repo: this only reads
STL files that already live under builds/ in this repository.
"""
from __future__ import annotations

import struct
from pathlib import Path

Vertex = tuple[float, float, float]
Triangle = tuple[int, int, int]


def read_stl(path: str) -> tuple[list[Vertex], list[Triangle]]:
    """Read an ASCII or binary STL file into (vertices, triangles)."""
    data = Path(path).read_bytes()
    if len(data) == 0:
        raise ValueError(f"empty STL file: {path}")
    facets = _read_binary(data) if _is_binary(data) else _read_ascii(data)
    if not facets:
        raise ValueError(f"no facets found in STL file: {path}")
    return _index_facets(facets)


def _is_binary(data: bytes) -> bool:
    """Binary STL: 80-byte header + uint32 triangle count + 50 bytes/tri.
    An ASCII file starting with 'solid' would fail this exact-size check,
    so this is the standard robust discriminator (name-based sniffing is
    not reliable -- some binary exporters also start with 'solid')."""
    if len(data) < 84:
        return False
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 80 + 4 + triangle_count * 50
    return len(data) == expected_size


def _read_binary(data: bytes) -> list[tuple[Vertex, Vertex, Vertex]]:
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    facets = []
    offset = 84
    for _ in range(triangle_count):
        # layout per facet: normal(12B) + v1(12B) + v2(12B) + v3(12B) + attr(2B)
        v1 = struct.unpack_from("<3f", data, offset + 12)
        v2 = struct.unpack_from("<3f", data, offset + 24)
        v3 = struct.unpack_from("<3f", data, offset + 36)
        facets.append((v1, v2, v3))
        offset += 50
    return facets


def _read_ascii(data: bytes) -> list[tuple[Vertex, Vertex, Vertex]]:
    text = data.decode("ascii", errors="replace")
    facets = []
    current: list[Vertex] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            parts = line.split()
            current.append((float(parts[1]), float(parts[2]), float(parts[3])))
            if len(current) == 3:
                facets.append((current[0], current[1], current[2]))
                current = []
    return facets


def _index_facets(
    facets: list[tuple[Vertex, Vertex, Vertex]],
) -> tuple[list[Vertex], list[Triangle]]:
    index_of: dict[Vertex, int] = {}
    vertices: list[Vertex] = []
    triangles: list[Triangle] = []
    for a, b, c in facets:
        idx = []
        for v in (a, b, c):
            key = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
            existing = index_of.get(key)
            if existing is None:
                existing = len(vertices)
                index_of[key] = existing
                vertices.append(key)
            idx.append(existing)
        triangles.append((idx[0], idx[1], idx[2]))
    return vertices, triangles

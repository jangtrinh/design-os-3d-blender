from __future__ import annotations

import json
import struct
from pathlib import Path

from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[2]


def read_stl(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50
    vertices = []
    vertex_ids = {}
    faces = []
    for triangle in range(count):
        values = struct.unpack_from("<12fH", data, 84 + triangle * 50)
        face = []
        for start in (3, 6, 9):
            point = tuple(values[start : start + 3])
            if point not in vertex_ids:
                vertex_ids[point] = len(vertices)
                vertices.append(Vector(point))
            face.append(vertex_ids[point])
        faces.append(tuple(face))
    return vertices, faces


results = []
total_nonadjacent = 0
for path in sorted((ROOT / "parts").glob("*.stl")):
    vertices, faces = read_stl(path)
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=True, epsilon=0.0)
    overlaps = tree.overlap(tree)
    nonadjacent = []
    for a, b in overlaps:
        if a >= b:
            continue
        if set(faces[a]) & set(faces[b]):
            continue
        nonadjacent.append((a, b))
    total_nonadjacent += len(nonadjacent)
    results.append({
        "file": path.name,
        "triangles": len(faces),
        "bvh_overlap_pairs": len(overlaps),
        "nonadjacent_overlap_pairs": len(nonadjacent),
        "examples": nonadjacent[:20],
    })

report = {
    "status": "PASS" if total_nonadjacent == 0 else "REVIEW_NONADJACENT_OVERLAPS",
    "files": len(results),
    "nonadjacent_overlap_pairs": total_nonadjacent,
    "parts_with_nonadjacent_overlaps": [r for r in results if r["nonadjacent_overlap_pairs"]],
    "scope": "Blender BVH triangle-overlap screen on actual binary STL triangles; pairs sharing a mesh vertex are treated as adjacent and excluded. This is not slicer repair or a physical strength check.",
}
Path(__file__).with_name("stl-self-overlap-check.json").write_text(json.dumps(report, indent=2) + "\n")
print("INDEPENDENT_STL_SELF_OVERLAP", json.dumps({k: v for k, v in report.items() if k != "parts_with_nonadjacent_overlaps"}, sort_keys=True))
if total_nonadjacent:
    print("PARTS_WITH_OVERLAPS", [(r["file"], r["nonadjacent_overlap_pairs"]) for r in report["parts_with_nonadjacent_overlaps"]])

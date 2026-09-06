from __future__ import annotations

import collections
import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_triangles(vertices, faces, label):
    edges = collections.Counter()
    signed_six_volume = 0.0
    for index, face in enumerate(faces):
        assert len(face) == 3 and len(set(face)) == 3, (label, "degenerate-index", index)
        a, b, c = (vertices[i] for i in face)
        assert all(math.isfinite(q) for p in (a, b, c) for q in p), (label, "nonfinite", index)
        ux, uy, uz = (b[i] - a[i] for i in range(3))
        vx, vy, vz = (c[i] - a[i] for i in range(3))
        cross = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        assert sum(q * q for q in cross) > 1e-20, (label, "zero-area", index)
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((face[i], face[j])))] += 1
        signed_six_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )
    bad = {edge: count for edge, count in edges.items() if count != 2}
    assert not bad, (label, "nonclosed-edges", len(bad), collections.Counter(bad.values()))
    assert signed_six_volume > 0, (label, "nonpositive-volume", signed_six_volume / 6.0)
    return signed_six_volume / 6.0


def read_binary_stl(path: Path):
    data = path.read_bytes()
    assert len(data) >= 84, (path, "short-stl")
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, (path, len(data), count)
    vertices = []
    ids = {}
    faces = []
    for triangle in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * triangle)
        face = []
        for start in (3, 6, 9):
            point = tuple(values[start : start + 3])
            if point not in ids:
                ids[point] = len(vertices)
                vertices.append(point)
            face.append(ids[point])
        faces.append(tuple(face))
    volume = validate_triangles(vertices, faces, str(path))
    bounds = [
        [min(v[axis] for v in vertices), max(v[axis] for v in vertices)]
        for axis in range(3)
    ]
    return {"triangles": count, "vertices": len(vertices), "volume_mm3": volume, "bounds_mm": bounds}


def read_3mf(path: Path):
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} <= names, (path, names)
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
    assert root.attrib.get("unit") == "millimeter", (path, root.attrib)
    objects = root.findall("m:resources/m:object", NS)
    items = root.findall("m:build/m:item", NS)
    object_ids = [o.attrib["id"] for o in objects]
    item_ids = [o.attrib["objectid"] for o in items]
    assert len(object_ids) == len(set(object_ids)), (path, "duplicate-object-id")
    assert collections.Counter(item_ids) == collections.Counter(object_ids), (path, "build-coverage")
    assert all("transform" not in item.attrib for item in items), (path, "unexpected-transform")
    result = []
    for obj in objects:
        vertex_nodes = obj.findall("m:mesh/m:vertices/m:vertex", NS)
        tri_nodes = obj.findall("m:mesh/m:triangles/m:triangle", NS)
        vertices = [tuple(float(v.attrib[a]) for a in ("x", "y", "z")) for v in vertex_nodes]
        faces = [tuple(int(t.attrib[a]) for a in ("v1", "v2", "v3")) for t in tri_nodes]
        assert faces and all(0 <= i < len(vertices) for face in faces for i in face), (path, obj.attrib)
        volume = validate_triangles(vertices, faces, f"{path}:{obj.attrib.get('name')}")
        bounds = [[min(v[a] for v in vertices), max(v[a] for v in vertices)] for a in range(3)]
        result.append({
            "name": obj.attrib.get("name", ""),
            "triangles": len(faces),
            "vertices": len(vertices),
            "volume_mm3": volume,
            "bounds_mm": bounds,
        })
    return result


manifest = json.loads((REPORTS / "plates-manifest.json").read_text())
export = json.loads((REPORTS / "export-check.json").read_text())
audit = json.loads((REPORTS / "mesh-audit.json").read_text())
freeze = json.loads((REPORTS / "source-freeze.json").read_text())

assert len(manifest["parts"]) == len(audit["parts"]) == export["parts"] == 38
assert collections.Counter(p["material"] for p in manifest["parts"]) == {"PETG": 32, "TPU": 6}
assert freeze["counts"]["print"] == 38
assert freeze["counts"] == manifest["source"]["counts"]
assert manifest["source"]["frozen_sha256"] == sha256(ROOT / "frozen-source.blend")
assert not audit["failed"]

part_rows = {p["id"]: p for p in manifest["parts"]}
part_binary = {}
for part_id, row in part_rows.items():
    path = ROOT / row["stl"]
    assert path.name.startswith(part_id + "-")
    assert sha256(path) == row["stl_sha256"]
    part_binary[part_id] = read_binary_stl(path)

assert len(list((ROOT / "parts").glob("*.stl"))) == 38
assert {p.name for p in (ROOT / "parts").glob("*.stl")} == {Path(r["stl"]).name for r in manifest["parts"]}

plate_export = {p["plate"]: p for p in export["plates"]}
coverage = []
plate_results = []
for index, plate in enumerate(manifest["plates"], 1):
    expected = plate["parts"]
    expected_material = plate["material"]
    export_row = plate_export[index]
    path = ROOT / export_row["file"]
    assert path.name == f"plate-{index:02d}-{expected_material}.3mf"
    assert sha256(path) == export_row["sha256"]
    objects = read_3mf(path)
    observed = [o["name"].split()[0] for o in objects]
    assert len(observed) == len(set(observed)), (path, "duplicate-part", observed)
    assert set(observed) == set(expected) == set(export_row["parts"]), (path, observed, expected)
    assert sum(o["triangles"] for o in objects) == export_row["triangles"]
    for obj, part_id in zip(objects, observed):
        assert obj["triangles"] == part_binary[part_id]["triangles"], (path, part_id)
        assert part_rows[part_id]["material"] == expected_material, (path, part_id, expected_material)
        x, y, z = obj["bounds_mm"]
        assert x[0] >= 6.999 - 1e-6 and x[1] <= 213.001 + 1e-6
        assert y[0] >= 6.999 - 1e-6 and y[1] <= 213.001 + 1e-6
        assert z[0] >= -0.0011
    plate_stl = path.with_suffix(".stl")
    plate_mesh = read_binary_stl(plate_stl)
    assert plate_mesh["triangles"] == export_row["triangles"]
    coverage.extend(observed)
    plate_results.append({
        "plate": index,
        "material": expected_material,
        "objects": len(objects),
        "triangles": export_row["triangles"],
        "bounds_mm": plate_mesh["bounds_mm"],
    })

assert collections.Counter(coverage) == collections.Counter(part_rows.keys())
assert len(list((ROOT / "plates").glob("*.3mf"))) == 5
assert len(list((ROOT / "plates").glob("*.stl"))) == 5

result = {
    "status": "PASS",
    "parts": len(part_binary),
    "part_triangles": sum(p["triangles"] for p in part_binary.values()),
    "materials": dict(collections.Counter(p["material"] for p in manifest["parts"])),
    "plates": plate_results,
    "source_counts": freeze["counts"],
    "frozen_sha256": sha256(ROOT / "frozen-source.blend"),
}
out = Path(__file__).with_name("package-check.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print("INDEPENDENT_PACKAGE_PASS", json.dumps(result, sort_keys=True))

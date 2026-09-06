"""Binary STL export in millimetres and an independent re-import audit.

Writer promoted from an earlier robot-arm build export pass (hand-written
binary STL + sha256 manifest, vertices already in mm). The
re-import uses Blender's own STL reader, so the geometry is parsed by code that
did not produce it; the mesh is then re-run through topology and bbox
predicates. Because the re-import wipes the file (read_homefile), it runs last,
and only ever in the disposable gate process.
"""
from __future__ import annotations

import os
import struct

import bpy

from . import dimensions, meshprep, topology
from .report import check, sha256_file

HEADER = b"production-gate binary STL - millimetres - NOT MANUFACTURING APPROVED"


def write_stl(tris, path):
    """tris: list of (a, b, c) mathutils Vectors already in mm."""
    with open(path, "wb") as fh:
        fh.write(HEADER.ljust(80, b" ")[:80])
        fh.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a)
            n = n.normalized() if n.length_squared > 0 else n
            fh.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z,
                                 b.x, b.y, b.z, c.x, c.y, c.z, 0))
    return {"file": os.path.abspath(path), "triangles": len(tris),
            "sha256": sha256_file(path)}


def export_part(bm, part, export_dir):
    tris = meshprep.triangles(bm)
    path = os.path.join(export_dir, "%s.stl" % part["id"])
    entry = write_stl(tris, path)
    entry.update({"id": part["id"], "object": part["object"],
                  "dims_mm": [round(v, 4) for v in meshprep.bbox_mm(bm)],
                  "units": "mm", "status": "UNRELEASED_DIGITAL_CHECK_ONLY"})
    return entry


def verify_roundtrip(entry, part, prefix=""):
    """Wipe the file, re-import one STL, re-run topology + bbox. Returns checks."""
    bpy.ops.wm.read_homefile(use_empty=True)
    before = set(bpy.data.objects)
    res = bpy.ops.wm.stl_import(filepath=entry["file"], global_scale=1.0,
                                use_scene_unit=False, forward_axis="Y", up_axis="Z")
    new = [o for o in bpy.data.objects if o not in before]
    if res != {"FINISHED"} or len(new) != 1:
        return [check(prefix + "roundtrip_import", "fail",
                      {"result": str(res), "objects": len(new)}, 1,
                      "the exported STL did not re-import as exactly one object")]
    obj = new[0]
    bm = meshprep.raw_mm_bmesh(obj.data, scale=1.0)
    checks = [check(prefix + "roundtrip_import", "pass",
                    {"file": os.path.basename(entry["file"]),
                     "sha256": entry["sha256"], "triangles": entry["triangles"]},
                    None, "written in mm, re-parsed by Blender's STL reader")]
    topo, _m = topology.evaluate(bm, part.get("expected_shells", 1),
                                 prefix=prefix + "roundtrip_")
    checks.extend(topo)
    dim, _m2 = dimensions.bbox_checks(bm, part["target_dims_mm"], part["tol_mm"],
                                      prefix=prefix + "roundtrip_")
    checks.extend(dim)
    bm.free()
    return checks


def manifest(entries):
    return {
        "units": "mm",
        "generated_by": "scripts/production-gate.py",
        "parts": entries,
        "status": "NOT_MANUFACTURING_APPROVED",
        "prohibited_claim": ("A watertight STL that matches its declared dimensions "
                             "does not establish load capability, assembly fit, print "
                             "success or heat endurance."),
    }

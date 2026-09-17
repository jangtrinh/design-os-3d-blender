"""Product-only GLB round-trip geometry verifier for the reference keyboard."""
from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BBOX_TOL_MM = 0.05
SURFACE_TOL_MM = 0.05
MAX_SAMPLES = 500
TRI_QUANT_MM = 1e-5
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
def _bbox(verts):
    return [[min(v[i] for v in verts) for i in range(3)],
            [max(v[i] for v in verts) for i in range(3)]]
def _bbox_error(a, b):
    return max(abs(float(a[r][c]) - float(b[r][c]))
               for r in range(2) for c in range(3))
def _sample_surface(verts, faces, limit=MAX_SAMPLES):
    count = min(len(faces), limit)
    if not count:
        return []
    ids = [0] if count == 1 else [round(i * (len(faces) - 1) / (count - 1))
                                  for i in range(count)]
    out = []
    for idx in ids:
        a, b, c = (Vector(verts[j]) for j in faces[idx])
        out.append((a + b + c) / 3.0)
    return out
def _stats(distances):
    if not distances:
        raise ValueError("surface comparison produced no distances")
    return {"count": len(distances), "max_mm": max(distances),
            "rms_mm": math.sqrt(sum(d * d for d in distances) / len(distances))}
def _bvh(verts, faces):
    if not verts or not faces:
        raise ValueError("surface mesh must contain vertices and triangles")
    return BVHTree.FromPolygons([Vector(v) for v in verts], faces, all_triangles=True)
def _nearest_stats(samples, target_bvh):
    distances = []
    for point in samples:
        hit = target_bvh.find_nearest(point)
        if hit is None:
            raise AssertionError("BVH nearest query returned no hit")
        distances.append(float(hit[3]))
    return _stats(distances)
def _qv(v):
    return tuple(int(round(float(c) / TRI_QUANT_MM)) for c in v)
def _triangles(verts, faces):
    return Counter(tuple(sorted(_qv(verts[i]) for i in face)) for face in faces)
def _vertex_stats(a_verts, a_faces, b_verts, b_faces):
    targets = {}
    for i in {i for face in b_faces for i in face}:
        p = tuple(float(c) for c in b_verts[i])
        targets.setdefault(_qv(p), []).append(p)
    distances = []
    for i in {i for face in a_faces for i in face}:
        p = tuple(float(c) for c in a_verts[i])
        choices = targets.get(_qv(p))
        if not choices:
            return None
        distances.append(min(math.dist(p, q) for q in choices))
    return _stats(distances)
def _triangle_correspondence(src_verts, src_faces, act_verts, act_faces):
    if _triangles(src_verts, src_faces) != _triangles(act_verts, act_faces):
        return None
    s2g = _vertex_stats(src_verts, src_faces, act_verts, act_faces)
    g2s = _vertex_stats(act_verts, act_faces, src_verts, src_faces)
    return (s2g, g2s) if s2g and g2s else None
def _capture_object(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        world = evaluated.matrix_world
        verts = [[c * 1000.0 for c in (world @ v.co)] for v in mesh.vertices]
        faces = [list(tri.vertices) for tri in mesh.loop_triangles]
    finally:
        evaluated.to_mesh_clear()
    if not verts or not faces:
        raise ValueError(f"{obj.name}: evaluated mesh has no surface triangles")
    return {"triangle_count": len(faces), "bbox_mm": _bbox(verts),
            "surface": {"vertices_mm": verts, "triangles": faces}}
def capture_source(object_names, frames=(1,)):
    """Read evaluated world-space product meshes; restore the original frame."""
    names = sorted(set(str(n) for n in object_names))
    frame_list = [int(f) for f in frames]
    if not names or not 1 <= len(frame_list) <= 3:
        raise ValueError("capture needs product mesh names and one to three frames")
    missing = [n for n in names if bpy.data.objects.get(n) is None]
    if missing:
        raise KeyError(f"source objects missing: {missing}")
    non_mesh = [n for n in names if bpy.data.objects[n].type != "MESH"]
    if non_mesh:
        raise TypeError(f"source objects are not meshes: {non_mesh}")
    scene, original_frame = bpy.context.scene, bpy.context.scene.frame_current
    result = {"schema_version": 1, "units": "mm", "fps": scene.render.fps,
              "rest_frame": frame_list[0], "frames": {}}
    try:
        for frame in frame_list:
            scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            result["frames"][str(frame)] = {"objects": {
                name: _capture_object(bpy.data.objects[name], depsgraph) for name in names}}
    finally:
        scene.frame_set(original_frame)
    return result
def _validate_source(source):
    if source.get("schema_version") != 1 or source.get("units") != "mm":
        raise ValueError("source_json requires schema_version=1 and units='mm'")
    frames = source.get("frames") or {}
    if not 1 <= len(frames) <= 3:
        raise ValueError("source_json needs one rest frame and at most two motion frames")
    rest = str(int(source.get("rest_frame", 1)))
    if rest not in frames:
        raise ValueError(f"rest_frame {rest} is absent from source_json.frames")
    expected_names = None
    for frame, block in frames.items():
        objects, names = block.get("objects") or {}, set((block.get("objects") or {}))
        if not names:
            raise ValueError(f"frame {frame} has no product meshes")
        expected_names = names if expected_names is None else expected_names
        if names != expected_names:
            raise ValueError(f"frame {frame} object names differ from rest frame")
        for name, entry in objects.items():
            surface = entry.get("surface") or {}
            verts, faces = surface.get("vertices_mm"), surface.get("triangles")
            if not verts or not faces or int(entry.get("triangle_count", -1)) != len(faces):
                raise ValueError(f"{name} frame {frame}: incomplete/inconsistent surface mesh")
            if _bbox_error(entry["bbox_mm"], _bbox(verts)) > 0.001:
                raise ValueError(f"{name} frame {frame}: bbox disagrees with source surface")
    return sorted(expected_names), sorted(int(f) for f in frames)
def _compare_object(name, source_entry, actual_entry):
    src, act = source_entry["surface"], actual_entry["surface"]
    src_verts, src_faces = src["vertices_mm"], src["triangles"]
    act_verts, act_faces = act["vertices_mm"], act["triangles"]
    correspondence = _triangle_correspondence(src_verts, src_faces, act_verts, act_faces)
    if correspondence:
        s2g, g2s = correspondence
        surface_method = "quantized_triangle_correspondence"
    else:
        s2g = _nearest_stats(_sample_surface(src_verts, src_faces), _bvh(act_verts, act_faces))
        g2s = _nearest_stats(_sample_surface(act_verts, act_faces), _bvh(src_verts, src_faces))
        surface_method = "sampled_bvh"
    bbox_error = _bbox_error(source_entry["bbox_mm"], actual_entry["bbox_mm"])
    tri_match = source_entry["triangle_count"] == actual_entry["triangle_count"]
    surface_error = max(s2g["max_mm"], g2s["max_mm"])
    return {"name": name, "triangle_count_source": source_entry["triangle_count"],
            "triangle_count_glb": actual_entry["triangle_count"],
            "triangle_count_match": tri_match, "bbox_max_abs_error_mm": bbox_error,
            "source_to_glb": s2g, "glb_to_source": g2s,
            "surface_method": surface_method,
            "triangle_quantization_mm": TRI_QUANT_MM if correspondence else None,
            "surface_max_error_mm": surface_error,
            "pass": tri_match and bbox_error <= BBOX_TOL_MM and surface_error <= SURFACE_TOL_MM}
def compare(source_json, glb_path, report_path):
    """Destructively import GLB only in disposable background Blender and report."""
    if not bpy.app.background:
        raise RuntimeError("GLB comparison is destructive; use fresh background Blender")
    source_json, glb_path, report_path = map(os.path.abspath,
                                             (source_json, glb_path, report_path))
    if not os.path.isfile(source_json) or not os.path.isfile(glb_path):
        raise FileNotFoundError("source_json and glb_path must both exist")
    with open(source_json, "r", encoding="utf-8") as fh:
        source = json.load(fh)
    names, frames = _validate_source(source)
    reset = bpy.ops.wm.read_homefile(use_empty=True)
    if reset != {"FINISHED"}:
        raise AssertionError(f"empty-scene reset returned {reset}")
    bpy.context.scene.render.fps = int(source.get("fps", 24))
    imported = bpy.ops.import_scene.gltf(filepath=glb_path)
    if imported != {"FINISHED"}:
        raise AssertionError(f"GLB import returned {imported}")
    imported_meshes = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
    names_match = imported_meshes == names
    report = {"schema_version": 1, "status": "FAIL", "pass": False,
              "source_json": source_json, "source_sha256": _sha256(source_json),
              "glb": glb_path, "glb_sha256": _sha256(glb_path),
              "blender_version": list(bpy.app.version), "fps": bpy.context.scene.render.fps,
              "tolerances_mm": {"bbox": BBOX_TOL_MM, "surface": SURFACE_TOL_MM},
              "max_samples_per_object_direction": MAX_SAMPLES,
              "expected_mesh_names": names, "imported_mesh_names": imported_meshes,
              "mesh_names_match": names_match, "frames": {},
              "limits": ["Sampled bidirectional distance is not a full Hausdorff proof.",
                         "No material pixel, physical fit, load, thermal, electrical, or manufacturing proof."]}
    all_pass = True
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        depsgraph, rows = bpy.context.evaluated_depsgraph_get(), []
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "MESH":
                row = {"name": name, "pass": False, "error": "missing imported mesh"}
            else:
                actual = _capture_object(obj, depsgraph)
                row = _compare_object(name, source["frames"][str(frame)]["objects"][name], actual)
            all_pass, rows = all_pass and bool(row["pass"]), rows + [row]
        report["frames"][str(frame)] = {"objects": rows, "pass": all(r["pass"] for r in rows)}
    report["pass"] = names_match and all_pass
    report["status"] = "PASS" if report["pass"] else "FAIL"
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return report
def _script_args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
if __name__ == "__main__":
    args = _script_args()
    if len(args) != 3:
        raise SystemExit("usage: export_compare.py <source_json> <product.glb> <report.json>")
    result = compare(*args)
    if not result["pass"]:
        raise AssertionError(f"GLB comparison failed; see {os.path.abspath(args[2])}")
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "scripts"))
    import agent_runtime as rt
    rt.emit_ok("reference-keyboard-export-compare", frames=len(result["frames"]),
               meshes=len(result["expected_mesh_names"]), report=os.path.abspath(args[2]))

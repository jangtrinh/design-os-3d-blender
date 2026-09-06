#!/usr/bin/env python3
"""Measure cross-subassembly staging intersections in the frozen refined scene."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARTIFACT = ROOT / "arm-original-refined.blend"
OUTPUT = HERE / "overlap-diagnosis.json"


def bounds(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return low, high


def union_bounds(objects):
    boxes = [bounds(obj) for obj in objects]
    low = Vector(tuple(min(box[0][axis] for box in boxes) for axis in range(3)))
    high = Vector(tuple(max(box[1][axis] for box in boxes) for axis in range(3)))
    return low, high


def aabb_overlap(a, b):
    delta = Vector(tuple(min(a[1][axis], b[1][axis]) - max(a[0][axis], b[0][axis]) for axis in range(3)))
    return delta, max(0.0, delta.x) * max(0.0, delta.y) * max(0.0, delta.z)


def world_bvh(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
        return BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=1e-7)
    finally:
        evaluated.to_mesh_clear()


def main():
    scene = bpy.data.scenes["A5-Original-refined"]
    bpy.context.window.scene = scene
    units = json.loads((ROOT / "reports/units.json").read_text())
    object_info = {}
    for unit in units:
        for name in unit["names"]:
            object_info[name] = {"subassembly": unit["subassembly"], "kind": unit["kind"], "unit": unit["id"], "group": unit["group"]}

    frames = {
        "shoulder": [555, 588, 599, 630, 639, 652, 696, 705],
        "elbow": [1163, 1198, 1207, 1238, 1247, 1260, 1304, 1313],
    }
    records = []
    for module, samples in frames.items():
        for frame in samples:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            visible = []
            for name, info in object_info.items():
                obj = scene.objects[name]
                if info["group"] != module or info["kind"] == "hardware" or obj.hide_render:
                    continue
                visible.append(obj)
            by_subassembly = {}
            for obj in visible:
                by_subassembly.setdefault(object_info[obj.name]["subassembly"], []).append(obj)
            union_overlaps = []
            for left, right in itertools.combinations(sorted(by_subassembly), 2):
                box_left = union_bounds(by_subassembly[left])
                box_right = union_bounds(by_subassembly[right])
                delta, volume = aabb_overlap(box_left, box_right)
                if volume > 0:
                    union_overlaps.append({
                        "subassemblies": [left, right],
                        "aabb_overlap_mm": [value * 1000 for value in delta],
                        "aabb_overlap_mm3": volume * 1e9,
                    })
            exact_pairs = []
            bvhs = {obj.name: world_bvh(obj) for obj in visible}
            for left, right in itertools.combinations(visible, 2):
                info_left, info_right = object_info[left.name], object_info[right.name]
                if info_left["subassembly"] == info_right["subassembly"]:
                    continue
                overlaps = bvhs[left.name].overlap(bvhs[right.name])
                if overlaps:
                    exact_pairs.append({
                        "left": left.name,
                        "left_subassembly": info_left["subassembly"],
                        "right": right.name,
                        "right_subassembly": info_right["subassembly"],
                        "triangle_pair_count": len(overlaps),
                    })
            records.append({
                "module": module,
                "frame": frame,
                "visible_structural_objects": len(visible),
                "subassemblies": {key: [obj.name for obj in value] for key, value in by_subassembly.items()},
                "union_aabb_overlaps": union_overlaps,
                "cross_subassembly_bvh_pairs": exact_pairs,
            })

    result = {
        "status": "MEASURED",
        "artifact_sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
        "method": "Evaluated world-space triangle BVH intersections plus subassembly-union AABB overlap; BVH triangle contact does not prove penetration volume.",
        "records": records,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("OVERLAP_DIAGNOSIS_COMPLETE", len(records))
    for record in records:
        print(record["module"], record["frame"], "aabb", len(record["union_aabb_overlaps"]), "bvh", len(record["cross_subassembly_bvh_pairs"]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Classify fork/servo interface crossings and flange screw direction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARTIFACT = ROOT / "arm-original-refined.blend"
OUTPUT = HERE / "overlap-interface-path.json"


def evaluated_geometry(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices = [vertex.co.copy() for vertex in mesh.vertices]
        triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        return evaluated.matrix_world.copy(), vertices, triangles
    finally:
        evaluated.to_mesh_clear()


def bvh(geometry, delta=Vector()):
    world, vertices, triangles = geometry
    transform = Matrix.Translation(delta) @ world
    return BVHTree.FromPolygons([transform @ vertex for vertex in vertices], triangles, all_triangles=True, epsilon=1e-7)


def center(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return (low + high) / 2, low, high


def main():
    scene = bpy.data.scenes["A5-Original-refined"]
    bpy.context.window.scene = scene
    scene.frame_set(scene.frame_end)
    bpy.context.view_layer.update()
    offsets_mm = [100, 80, 60, 50, 40, 35, 30, 25, 20, 15, 10, 8, 6, 4, 3, 2, 1, 0]
    results = []
    for joint, fork_name, flange_prefix in (
        ("shoulder", "A5-part-lower-U-body", "A5-part-shoulder-drive-flange"),
        ("elbow", "A5-part-upper-U-body", "A5-part-elbow-drive-flange"),
    ):
        fork = [scene.objects[fork_name], scene.objects[f"{flange_prefix}--1"], scene.objects[f"{flange_prefix}-1"]]
        servo = [scene.objects[f"A5-part-{joint}-servo"], scene.objects[f"A5-part-{joint}-output--1"], scene.objects[f"A5-part-{joint}-output-1"]]
        geometry = {obj.name: evaluated_geometry(obj) for obj in fork + servo}
        fixed_bvh = {obj.name: bvh(geometry[obj.name]) for obj in servo}
        link_axis = (scene.objects[fork_name].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        directions = {"vertical_plus_z": Vector((0, 0, 1)), "local_link_plus_z": link_axis}
        paths = {}
        for direction_name, direction in directions.items():
            samples = []
            for offset_mm in offsets_mm:
                delta = direction * offset_mm / 1000.0
                pairs = []
                for moving in fork:
                    moving_bvh = bvh(geometry[moving.name], delta)
                    for fixed in servo:
                        overlaps = moving_bvh.overlap(fixed_bvh[fixed.name])
                        if overlaps:
                            pairs.append({"moving": moving.name, "fixed": fixed.name, "triangle_pairs": len(overlaps)})
                samples.append({"offset_mm": offset_mm, "pairs": pairs})
            paths[direction_name] = samples

        fasteners = []
        for side in ("-1", "1"):
            stem = "lower-flange" if joint == "shoulder" else "upper-flange"
            head = scene.objects[f"A5-part-{stem}-({side}, 0)-head"]
            thread = scene.objects[f"A5-part-{stem}-({side}, 0)-thread-envelope"]
            head_center, head_low, head_high = center(head)
            thread_center, _, _ = center(thread)
            vector = thread_center - head_center
            fasteners.append({
                "side": side,
                "head_center_mm": [value * 1000 for value in head_center],
                "head_y_range_mm": [head_low.y * 1000, head_high.y * 1000],
                "thread_center_mm": [value * 1000 for value in thread_center],
                "head_to_thread_unit": list(vector.normalized()),
                "driver_approach_unit": list((-vector).normalized()),
            })
        results.append({
            "joint": joint,
            "servo_case_part_type": servo[0].get("part_type"),
            "output_part_types": {obj.name: obj.get("part_type") for obj in servo[1:]},
            "local_link_axis": list(link_axis),
            "paths": paths,
            "flange_fasteners": fasteners,
        })
    result = {
        "status": "MEASURED",
        "artifact_sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
        "results": results,
        "limits": "Output meshes are actuator-visual envelopes; intersection timing is presentation geometry evidence, not a certified physical servo interface.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("INTERFACE_PATH_CHECK_COMPLETE")
    for item in results:
        print(item["joint"], item["output_part_types"], item["flange_fasteners"])
        for path, samples in item["paths"].items():
            print(path, [(sample["offset_mm"], [(pair["moving"].split("A5-part-")[-1], pair["fixed"].split("A5-part-")[-1], pair["triangle_pairs"]) for pair in sample["pairs"]]) for sample in samples])


if __name__ == "__main__":
    main()

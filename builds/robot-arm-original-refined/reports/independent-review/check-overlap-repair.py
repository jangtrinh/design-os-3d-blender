#!/usr/bin/env python3
"""Read-only geometric audit of repaired fork/carrier staging and seat motion."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARTIFACT = ROOT / "arm-original-refined.blend"
OUTPUT = HERE / "overlap-repair-check.json"
RIGHT = Vector((1.0, 0.55, 0.0)).normalized()


def bounds(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return low, high, points


def bounds_overlap(left, right):
    return all(min(left[1][axis], right[1][axis]) > max(left[0][axis], right[0][axis]) for axis in range(3))


def bvh(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        return BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=1e-7)
    finally:
        evaluated.to_mesh_clear()


def classify(left, right):
    types = {str(left.get("part_type", "")), str(right.get("part_type", ""))}
    if "actuator-visual" in types:
        return "actuator-visual-mate"
    if "actuator" in types:
        return "actuator-case"
    return "other-body"


def visible_body_objects(scene, names):
    result = []
    for name in names:
        obj = scene.objects[name]
        if obj.hide_render or obj.type != "MESH" or obj.get("part_type") == "hardware":
            continue
        result.append(obj)
    return result


def exact_cross_pairs(moving, fixed):
    moving_bounds = {obj.name: bounds(obj)[:2] for obj in moving}
    fixed_bounds = {obj.name: bounds(obj)[:2] for obj in fixed}
    moving_bvhs = {}
    fixed_bvhs = {}
    result = []
    for left in moving:
        for right in fixed:
            if not bounds_overlap(moving_bounds[left.name], fixed_bounds[right.name]):
                continue
            left_bvh = moving_bvhs.setdefault(left.name, bvh(left))
            right_bvh = fixed_bvhs.setdefault(right.name, bvh(right))
            overlaps = left_bvh.overlap(right_bvh)
            if overlaps:
                result.append({
                    "moving": left.name,
                    "moving_type": left.get("part_type"),
                    "fixed": right.name,
                    "fixed_type": right.get("part_type"),
                    "classification": classify(left, right),
                    "triangle_pairs": len(overlaps),
                })
    return result


def projected_span(objects):
    values = []
    for obj in objects:
        values.extend(RIGHT.dot(point) for point in bounds(obj)[2])
    return min(values), max(values)


def main():
    scene = bpy.data.scenes["A5-Original-refined"]
    bpy.context.window.scene = scene
    units = json.loads((ROOT / "reports/units.json").read_text())
    timing = json.loads((ROOT / "reports/timing.json").read_text())
    source_map = json.loads((ROOT / "reports/source-map.json").read_text())
    unit_by_id = {unit["id"]: unit for unit in units}
    module_names = defaultdict(list)
    for unit in units:
        module_names[unit["group"]].extend(unit["names"])

    seat_events = {}
    for event in timing["events"]:
        if event["type"] == "seat-subassembly" and event.get("module") in {"shoulder", "elbow"}:
            subs = {unit_by_id[key]["subassembly"] for key in event["units"]}
            if len(subs) == 1 and next(iter(subs)) in {"fork", "carrier-left", "carrier-right"}:
                seat_events[(event["module"], subs.pop())] = event

    order = {}
    for module in ("shoulder", "elbow"):
        fork = seat_events[(module, "fork")]
        left = seat_events[(module, "carrier-left")]
        right = seat_events[(module, "carrier-right")]
        assert fork["end"] < left["start"] < left["end"] < right["start"] < right["end"]
        order[module] = {
            "fork_seat": [fork["start"], fork["end"]],
            "carrier_left_seat": [left["start"], left["end"]],
            "carrier_right_seat": [right["start"], right["end"]],
            "fork_before_both_carriers": True,
        }

    waiting = []
    sweeps = []
    for (module, subassembly), event in sorted(seat_events.items()):
        moving_names = [name for key in event["units"] for name in unit_by_id[key]["names"]]
        frame = event["start"] - 1
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        moving = visible_body_objects(scene, moving_names)
        fixed = visible_body_objects(scene, [name for name in module_names[module] if name not in moving_names])
        waiting_pairs = exact_cross_pairs(moving, fixed)
        record = {
            "module": module,
            "subassembly": subassembly,
            "frame": frame,
            "pairs": waiting_pairs,
        }
        if subassembly == "fork":
            moving_span = projected_span(moving)
            fixed_span = projected_span(fixed)
            record["projected_axis"] = list(RIGHT)
            record["moving_span_m"] = list(moving_span)
            record["fixed_span_m"] = list(fixed_span)
            record["projected_gap_mm"] = (moving_span[0] - fixed_span[1]) * 1000.0
        waiting.append(record)

        pair_history = defaultdict(lambda: {"first": None, "last": None, "max_triangle_pairs": 0, "classification": None})
        for sample in range(event["start"], event["end"] + 1):
            scene.frame_set(sample)
            bpy.context.view_layer.update()
            moving = visible_body_objects(scene, moving_names)
            fixed = visible_body_objects(scene, [name for name in module_names[module] if name not in moving_names])
            for pair in exact_cross_pairs(moving, fixed):
                key = (pair["moving"], pair["fixed"])
                item = pair_history[key]
                item["first"] = sample if item["first"] is None else item["first"]
                item["last"] = sample
                item["max_triangle_pairs"] = max(item["max_triangle_pairs"], pair["triangle_pairs"])
                item["classification"] = pair["classification"]
                item["moving_type"] = pair["moving_type"]
                item["fixed_type"] = pair["fixed_type"]
        sweeps.append({
            "module": module,
            "subassembly": subassembly,
            "frames": [event["start"], event["end"]],
            "pairs": [
                {"moving": key[0], "fixed": key[1], **value}
                for key, value in sorted(pair_history.items())
            ],
        })

    scene.frame_set(scene.frame_end)
    bpy.context.view_layer.update()
    errors = []
    for row in source_map["objects"]:
        expected = Matrix(row["final_matrix"])
        actual = scene.objects[row["candidate"]].matrix_world
        error = max(abs(expected[r][c] - actual[r][c]) for r in range(4) for c in range(4))
        errors.append((error, row["candidate"]))
    max_error, max_object = max(errors)
    assert max_error < 1e-6, (max_error, max_object)

    assert all(not item["pairs"] for item in waiting), waiting
    fork_gaps = {item["module"]: item["projected_gap_mm"] for item in waiting if item["subassembly"] == "fork"}
    assert all(gap >= 34.9 for gap in fork_gaps.values()), fork_gaps

    result = {
        "status": "PASS_WITH_PHYSICAL_LIMITS",
        "artifact_sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
        "frames": scene.frame_end,
        "order": order,
        "waiting": waiting,
        "sweeps": sweeps,
        "final_world_matrix_max_error": max_error,
        "final_world_matrix_max_error_object": max_object,
        "limits": [
            "BVH surface intersections do not measure penetration volume.",
            "Actuator-visual output meshes are illustrative and cannot validate physical insertion.",
            "The screen excludes hardware meshes and does not prove fit, tool access, retention, or load capacity.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("OVERLAP_REPAIR_CHECK_PASS")
    print(json.dumps({
        "artifact_sha256": result["artifact_sha256"],
        "fork_gaps_mm": fork_gaps,
        "waiting_pair_counts": {f'{x["module"]}:{x["subassembly"]}': len(x["pairs"]) for x in waiting},
        "sweep_pairs": {f'{x["module"]}:{x["subassembly"]}': len(x["pairs"]) for x in sweeps},
        "final_world_matrix_max_error": max_error,
    }, indent=2))


if __name__ == "__main__":
    main()

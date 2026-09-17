"""Read-only fit evidence for the reference-keyboard native scene.

The public API is ``inspect() -> dict``.  It evaluates the current Blender scene
without changing source objects, modifiers, transforms, frames, or datablocks.
Distances are reported in millimetres.
"""
from __future__ import annotations

import json
import math
import re

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


TRAVEL_SAMPLES_MM = (0.0, 0.5, 1.0, 1.5)
EXPECTED_SWITCHES = 58
EXPECTED_ENVELOPE_MM = (15.6, 15.6, 11.0)
ENVELOPE_TOL_MM = 0.05
_INDEX = re.compile(r"_(\d+)$")


def _indexed(prefix: str) -> dict[int, bpy.types.Object]:
    out = {}
    for obj in bpy.context.scene.objects:
        if not obj.name.startswith(prefix):
            continue
        match = _INDEX.search(obj.name)
        if match:
            out[int(match.group(1))] = obj
    return out


def _bbox_points(points):
    if not points:
        raise ValueError("cannot measure an empty point set")
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return lo, hi


def _bbox_mm(obj: bpy.types.Object):
    graph = bpy.context.evaluated_depsgraph_get()
    owner = obj.evaluated_get(graph)
    mesh = owner.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
    try:
        points = [owner.matrix_world @ v.co for v in mesh.vertices]
    finally:
        owner.to_mesh_clear()
    lo, hi = _bbox_points(points)
    return [v * 1000.0 for v in lo], [v * 1000.0 for v in hi]


def _union_bbox_mm(boxes):
    if not boxes:
        raise ValueError("cannot union an empty bbox list")
    lo = [min(box[0][axis] for box in boxes) for axis in range(3)]
    hi = [max(box[1][axis] for box in boxes) for axis in range(3)]
    return lo, hi


def _dims_mm(box):
    return [box[1][axis] - box[0][axis] for axis in range(3)]


def _evaluated_components_mm(obj: bpy.types.Object):
    """Connected evaluated mesh components as world-space millimetre bboxes."""
    graph = bpy.context.evaluated_depsgraph_get()
    owner = obj.evaluated_get(graph)
    mesh = owner.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.transform(owner.matrix_world)
        bm.verts.ensure_lookup_table()
        seen = set()
        boxes = []
        for seed in bm.verts:
            if seed.index in seen:
                continue
            stack = [seed]
            seen.add(seed.index)
            component = []
            while stack:
                vertex = stack.pop()
                component.append(vertex.co.copy())
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
            lo, hi = _bbox_points(component)
            boxes.append(([v * 1000.0 for v in lo], [v * 1000.0 for v in hi]))
        return boxes
    finally:
        bm.free()
        owner.to_mesh_clear()


def _center_xy(box):
    return ((box[0][0] + box[1][0]) * 0.5, (box[0][1] + box[1][1]) * 0.5)


def _match_components(component_boxes, indexed_reference):
    remaining = list(component_boxes)
    matched = {}
    worst = 0.0
    for index, obj in sorted(indexed_reference.items()):
        ref = _center_xy(_bbox_mm(obj))
        choice, _box = min(
            enumerate(remaining),
            key=lambda pair: math.hypot(_center_xy(pair[1])[0] - ref[0], _center_xy(pair[1])[1] - ref[1]),
        )
        center = _center_xy(remaining[choice])
        distance = math.hypot(center[0] - ref[0], center[1] - ref[1])
        worst = max(worst, distance)
        matched[index] = remaining.pop(choice)
    if remaining:
        raise ValueError(f"unmatched housing components: {len(remaining)}")
    return matched, worst


def _tri_mesh(obj: bpy.types.Object, z_offset_m: float = 0.0):
    graph = bpy.context.evaluated_depsgraph_get()
    owner = obj.evaluated_get(graph)
    mesh = owner.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
    try:
        mesh.calc_loop_triangles()
        shift = Vector((0.0, 0.0, z_offset_m))
        vertices = [owner.matrix_world @ v.co + shift for v in mesh.vertices]
        triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    finally:
        owner.to_mesh_clear()
    if not vertices or not triangles:
        raise ValueError(f"{obj.name} has no evaluated triangles")
    volume = 0.0
    for a, b, c in triangles:
        volume += vertices[a].dot(vertices[b].cross(vertices[c]))
    orientation = 1.0 if volume >= 0.0 else -1.0
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0)
    lo, hi = _bbox_points(vertices)
    return {
        "vertices": vertices,
        "triangles": triangles,
        "tree": tree,
        "orientation": orientation,
        "bbox": (lo, hi),
    }


def _z_overlap(a, b, tol=1e-10):
    lo = max(a["bbox"][0][2], b["bbox"][0][2])
    hi = min(a["bbox"][1][2], b["bbox"][1][2])
    return hi - lo > tol


def _point_inside(solid, point, contact_tol=1e-8):
    lo, hi = solid["bbox"]
    if any(point[axis] < lo[axis] - contact_tol or point[axis] > hi[axis] + contact_tol
           for axis in range(3)):
        return False, False
    hit, normal, _index, distance = solid["tree"].find_nearest(point)
    if hit is None:
        return False, False
    delta = point - hit
    signed = delta.dot(normal) * solid["orientation"]
    if distance <= contact_tol:
        return False, True
    return signed < -contact_tol, False


def _sample_points(mesh):
    points = list(mesh["vertices"])
    for a, b, c in mesh["triangles"]:
        points.append((mesh["vertices"][a] + mesh["vertices"][b] + mesh["vertices"][c]) / 3.0)
    return points


def _intersects(a, b):
    """Surface BVH plus bbox-gated sampled nearest-normal containment heuristic."""
    if not _z_overlap(a, b):
        return False, "no_common_z"
    overlap = a["tree"].overlap(b["tree"])
    if overlap:
        return True, "triangle_surface_intersection"
    for point in _sample_points(a):
        inside, contact = _point_inside(b, point)
        if inside or contact:
            return True, "a_sample_inside_or_contact"
    for point in _sample_points(b):
        inside, contact = _point_inside(a, point)
        if inside or contact:
            return True, "b_sample_inside_or_contact"
    return False, "disjoint"


def _switch_assembly_evidence(housing_components, flanges, tops, stems, contacts_left, contacts_right):
    cells = []
    for index in sorted(flanges):
        objects = (flanges[index], tops[index], stems[index], contacts_left[index], contacts_right[index])
        box = _union_bbox_mm([housing_components[index]] + [_bbox_mm(obj) for obj in objects])
        dims = _dims_mm(box)
        cells.append({
            "index": index,
            "bbox_mm": [[round(v, 5) for v in box[0]], [round(v, 5) for v in box[1]]],
            "dimensions_mm": [round(v, 5) for v in dims],
        })
    ranges = {
        axis: [round(min(row["dimensions_mm"][i] for row in cells), 5),
               round(max(row["dimensions_mm"][i] for row in cells), 5)]
        for i, axis in enumerate(("x", "y", "z"))
    }
    within = all(
        abs(row["dimensions_mm"][axis] - EXPECTED_ENVELOPE_MM[axis]) <= ENVELOPE_TOL_MM
        for row in cells for axis in range(3)
    )
    return {
        "method": "evaluated_per_cell_union_bbox",
        "cells_checked": len(cells),
        "expected_mm": list(EXPECTED_ENVELOPE_MM),
        "tolerance_mm": ENVELOPE_TOL_MM,
        "dimensions_range_mm": ranges,
        "all_within_tolerance": within,
        "cells": cells,
    }


def _collision_evidence(keys, tops, flanges, plate):
    static_cache = {obj.name: _tri_mesh(obj) for obj in list(tops.values()) + list(flanges.values()) + [plate]}
    collided_pairs = set()
    per_travel = []
    for travel_mm in TRAVEL_SAMPLES_MM:
        frame_collisions = {"cover": [], "flange": [], "plate": []}
        common_z = {"cover": 0, "flange": 0, "plate": 0}
        for index in sorted(keys):
            key_mesh = _tri_mesh(keys[index], -travel_mm / 1000.0)
            for category, static_obj in (
                ("cover", tops[index]),
                ("flange", flanges[index]),
                ("plate", plate),
            ):
                static_mesh = static_cache[static_obj.name]
                if _z_overlap(key_mesh, static_mesh):
                    common_z[category] += 1
                collision, reason = _intersects(key_mesh, static_mesh)
                if collision:
                    frame_collisions[category].append({"index": index, "reason": reason})
                    collided_pairs.add(index)
        per_travel.append({
            "travel_mm": travel_mm,
            "common_z_pairs": common_z,
            "collisions": frame_collisions,
            "collision_key_indices": sorted({row["index"] for rows in frame_collisions.values() for row in rows}),
        })
    return {
        "method": "evaluated_mesh_intersection_common_z",
        "predicate": "BVH triangle overlap plus nearest-normal inside-solid/contact samples",
        "pairs_checked": len(keys),
        "collision_pairs": len(collided_pairs),
        "colliding_indices": sorted(collided_pairs),
        "travel_samples_mm": list(TRAVEL_SAMPLES_MM),
        "moving": "RK_KEY_## virtual -Z travel only; source transforms are untouched",
        "static": ["RK_SWITCH_TOP_##", "RK_SWITCH_FLANGE_##", "RK_MAIN_PLATE"],
        "per_travel": per_travel,
    }


def inspect() -> dict:
    """Return revision-local geometry evidence for the currently loaded scene."""
    housing = bpy.data.objects.get("RK_SWITCH_HOUSINGS")
    plate = bpy.data.objects.get("RK_MAIN_PLATE")
    if housing is None or plate is None:
        raise ValueError("scene is missing RK_SWITCH_HOUSINGS or RK_MAIN_PLATE")

    keys = _indexed("RK_KEY_")
    tops = _indexed("RK_SWITCH_TOP_")
    flanges = _indexed("RK_SWITCH_FLANGE_")
    stems = _indexed("RK_SWITCH_STEM_")
    # Contact names end in L/R rather than a numeric suffix; build them explicitly.
    contacts_left = {i: bpy.data.objects.get(f"RK_CONTACT_{i:02d}_L") for i in range(EXPECTED_SWITCHES)}
    contacts_right = {i: bpy.data.objects.get(f"RK_CONTACT_{i:02d}_R") for i in range(EXPECTED_SWITCHES)}
    families = (keys, tops, flanges, stems, contacts_left, contacts_right)
    if any(len(group) != EXPECTED_SWITCHES or any(obj is None for obj in group.values()) for group in families):
        raise ValueError("expected 58 complete key/switch cell families")

    component_boxes = _evaluated_components_mm(housing)
    housing_by_index, match_error = _match_components(component_boxes, flanges)
    assembly = _switch_assembly_evidence(
        housing_by_index, flanges, tops, stems, contacts_left, contacts_right
    )
    collision = _collision_evidence(keys, tops, flanges, plate)
    mesh_groups = {}
    for index, obj in sorted(keys.items()):
        mesh_groups.setdefault(obj.data.name, []).append(index)

    return {
        "switch_housings": {
            "object": housing.name,
            "method": "evaluated_mesh_connected_components",
            "evaluated_connected_shells": len(component_boxes),
            "expected": EXPECTED_SWITCHES,
            "component_to_flange_center_max_error_mm": round(match_error, 6),
            "component_bboxes_mm": [
                [[round(v, 5) for v in box[0]], [round(v, 5) for v in box[1]]]
                for box in component_boxes
            ],
        },
        "switch_assembly_envelope": assembly,
        "switch_keycap_overlap": collision,
        "keycap_mesh_reuse": {
            "mesh_groups": {name: indices for name, indices in sorted(mesh_groups.items())},
            "unique_key_meshes": len(mesh_groups),
            "cells_checked_for_collision": len(keys),
        },
        "keycap_switch_engagement": {
            "status": "NOT_QUALIFIED",
            "reason": "keycaps intentionally have no sourced switch-stem receiver geometry",
        },
        "limits": [
            "This evidence checks digital geometry only; it does not establish Cherry MX compatibility, retention, electrical fit, preload, or physical manufacture.",
            "Press travel is sampled at 0.0, 0.5, 1.0 and 1.5 mm; no continuous-motion proof is claimed between samples.",
            "The inspector reads evaluated scene geometry and does not mutate or save the source scene.",
        ],
    }


if __name__ == "__main__":
    evidence = inspect()
    print(json.dumps({
        "switch_housings": {
            "evaluated_connected_shells": evidence["switch_housings"]["evaluated_connected_shells"],
            "component_to_flange_center_max_error_mm": evidence["switch_housings"]["component_to_flange_center_max_error_mm"],
        },
        "switch_assembly_envelope": {
            "cells_checked": evidence["switch_assembly_envelope"]["cells_checked"],
            "dimensions_range_mm": evidence["switch_assembly_envelope"]["dimensions_range_mm"],
            "all_within_tolerance": evidence["switch_assembly_envelope"]["all_within_tolerance"],
        },
        "switch_keycap_overlap": {
            "pairs_checked": evidence["switch_keycap_overlap"]["pairs_checked"],
            "collision_pairs": evidence["switch_keycap_overlap"]["collision_pairs"],
            "colliding_indices": evidence["switch_keycap_overlap"]["colliding_indices"],
            "per_travel": evidence["switch_keycap_overlap"]["per_travel"],
        },
        "keycap_switch_engagement": evidence["keycap_switch_engagement"],
    }, sort_keys=True, allow_nan=False))

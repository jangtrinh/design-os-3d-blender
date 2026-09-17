"""Read-only fit evidence for the reference-keyboard native scene.

The public API is ``inspect() -> dict``.  It evaluates the current Blender scene
without changing source objects, modifiers, transforms, frames, or datablocks.
Distances are reported in millimetres.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
TRAVEL_STEP_MM = 0.5
ENVELOPE_TOL_MM = 0.05
_INDEX = re.compile(r"_(\d+)$")


def _contracts():
    layout = json.loads((ROOT / "layout.json").read_text(encoding="utf-8"))
    interfaces = json.loads((ROOT / "interfaces.json").read_text(encoding="utf-8"))
    expected = (
        sum(len(row) for row in layout["main_rows"])
        + len(layout["bottom_row"])
        + int(layout["rear_macros"]["count"])
        + len(layout["left_macros_mm"])
    )
    travel = float(layout["key_travel_mm"])
    steps = int(round(travel / TRAVEL_STEP_MM))
    samples = tuple(round(i * TRAVEL_STEP_MM, 6) for i in range(steps + 1))
    envelope = (
        float(layout["switch_width_mm"]),
        float(layout["switch_width_mm"]),
        float(layout["switch_height_mm"]),
    )
    return layout, interfaces, expected, samples, envelope


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
    return _mesh_packet(vertices, triangles)


def _mesh_packet(vertices, triangles):
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


def _transform_mesh(mesh, center_xy, angle=0.0, offset=(0.0, 0.0, 0.0)):
    ca, sa = math.cos(angle), math.sin(angle)
    cx, cy = center_xy
    ox, oy, oz = offset
    points = []
    for point in mesh["vertices"]:
        dx, dy = point.x - cx, point.y - cy
        points.append(Vector((
            cx + ca * dx - sa * dy + ox,
            cy + sa * dx + ca * dy + oy,
            point.z + oz,
        )))
    return _mesh_packet(points, mesh["triangles"])


def _ray_hit(mesh, origin, direction, distance=1.0):
    hit, _normal, _index, _distance = mesh["tree"].ray_cast(
        Vector(origin), Vector(direction), distance
    )
    return None if hit is None else hit


def _z_overlap(a, b, tol=1e-10):
    lo = max(a["bbox"][0][2], b["bbox"][0][2])
    hi = min(a["bbox"][1][2], b["bbox"][1][2])
    return hi - lo > tol


_PARITY_DIRECTIONS = (
    (1.0, 0.371390676, 0.694201),
    (-0.287113, 1.0, 0.529031),
    (0.613271, -0.421113, 1.0),
    (-0.751119, -0.339217, 1.0),
    (1.0, -0.812331, -0.277119),
)


def _ray_parity(solid, point, direction, contact_tol):
    """Return inside parity for one non-axis ray, or None for a grazing ambiguity."""
    direction = Vector(direction).normalized()
    lo, hi = solid["bbox"]
    diagonal = Vector((hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])).length
    max_distance = max(diagonal * 3.0, 0.001)
    step = max(contact_tol * 16.0, 1e-7)
    start = Vector(point)
    cursor = start.copy()
    crossings = 0
    last_t = None
    for _ in range(256):
        travelled = (cursor - start).dot(direction)
        remaining = max_distance - travelled
        if remaining <= 0.0:
            return bool(crossings % 2)
        hit, normal, _index, _distance = solid["tree"].ray_cast(cursor, direction, remaining)
        if hit is None:
            return bool(crossings % 2)
        t = (hit - start).dot(direction)
        if abs(normal.dot(direction)) < 1e-7:
            return None
        if last_t is None or abs(t - last_t) > step * 4.0:
            crossings += 1
            last_t = t
        cursor = hit + direction * step
    return None


def _point_inside(solid, point, contact_tol=1e-8):
    lo, hi = solid["bbox"]
    if any(point[axis] < lo[axis] - contact_tol or point[axis] > hi[axis] + contact_tol
           for axis in range(3)):
        return False, False
    hit, _normal, _index, distance = solid["tree"].find_nearest(point)
    if hit is None:
        return False, False
    if distance <= contact_tol:
        return False, True
    votes = [
        value for value in (
            _ray_parity(solid, point, direction, contact_tol)
            for direction in _PARITY_DIRECTIONS
        )
        if value is not None
    ]
    inside_votes = sum(bool(value) for value in votes)
    outside_votes = len(votes) - inside_votes
    if inside_votes >= 3:
        return True, False
    if outside_votes >= 3:
        return False, False
    raise RuntimeError(
        f"ambiguous point-in-solid ray parity: inside={inside_votes} outside={outside_votes}"
    )


def _sample_points(mesh):
    points = list(mesh["vertices"])
    for a, b, c in mesh["triangles"]:
        points.append((mesh["vertices"][a] + mesh["vertices"][b] + mesh["vertices"][c]) / 3.0)
    return points


def _intersects(a, b):
    """Surface BVH plus bbox-gated sampled multi-ray parity containment."""
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


def _switch_assembly_evidence(housing_components, flanges, tops, stems, contacts_left,
                              contacts_right, expected_envelope):
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
        abs(row["dimensions_mm"][axis] - expected_envelope[axis]) <= ENVELOPE_TOL_MM
        for row in cells for axis in range(3)
    )
    return {
        "method": "evaluated_per_cell_union_bbox",
        "cells_checked": len(cells),
        "expected_mm": list(expected_envelope),
        "tolerance_mm": ENVELOPE_TOL_MM,
        "dimensions_range_mm": ranges,
        "all_within_tolerance": within,
        "cells": cells,
    }


def _collision_evidence(keys, tops, flanges, plate, travel_samples):
    static_cache = {obj.name: _tri_mesh(obj) for obj in list(tops.values()) + list(flanges.values()) + [plate]}
    collided_pairs = set()
    per_travel = []
    for travel_mm in travel_samples:
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
        "predicate": "BVH triangle overlap plus multi-ray parity inside-solid/contact samples",
        "pairs_checked": len(keys),
        "collision_pairs": len(collided_pairs),
        "colliding_indices": sorted(collided_pairs),
        "travel_samples_mm": list(travel_samples),
        "moving": "RK_KEY_## virtual -Z travel only; source transforms are untouched",
        "static": ["RK_SWITCH_TOP_##", "RK_SWITCH_FLANGE_##", "RK_MAIN_PLATE"],
        "per_travel": per_travel,
    }


def _cross_dims_mm(mesh, center_xy, z_m, probe_offset_m=0.0015):
    cx, cy = center_xy
    def span(origin, axis):
        p = _ray_hit(mesh, origin, axis, 0.020)
        n = _ray_hit(mesh, origin, tuple(-v for v in axis), 0.020)
        if p is None or n is None:
            raise ValueError("cross section ray missed evaluated geometry")
        return (p - n).length * 1000.0
    return {
        "span_x": span((cx, cy, z_m), (1.0, 0.0, 0.0)),
        "span_y": span((cx, cy, z_m), (0.0, 1.0, 0.0)),
        "horizontal_arm": span((cx + probe_offset_m, cy, z_m), (0.0, 1.0, 0.0)),
        "vertical_arm": span((cx, cy + probe_offset_m, z_m), (1.0, 0.0, 0.0)),
    }


def _key_stem_interface(keys, stems, tops, flanges, plate, housing, travel_samples, cfg):
    rows = []
    collision_indices = set()
    static_collision_indices = set()
    housing_mesh = _tri_mesh(housing)
    plate_mesh = _tri_mesh(plate)
    top_meshes = {i: _tri_mesh(obj) for i, obj in tops.items()}
    flange_meshes = {i: _tri_mesh(obj) for i, obj in flanges.items()}
    for index in sorted(keys):
        key_mesh = _tri_mesh(keys[index])
        stem_mesh = _tri_mesh(stems[index])
        key_box = _bbox_mm(keys[index])
        stem_box = _bbox_mm(stems[index])
        center = _center_xy(key_box)
        key_bottom = key_box[0][2] / 1000.0
        stem_mid = (stem_box[0][2] + stem_box[1][2]) * 0.0005
        receiver_mid = key_bottom + min(float(cfg["receiver_depth"]) * 0.5, 1.5) / 1000.0
        receiver = _cross_dims_mm(key_mesh, (center[0] / 1000.0, center[1] / 1000.0), receiver_mid)
        stem = _cross_dims_mm(stem_mesh, (center[0] / 1000.0, center[1] / 1000.0), stem_mid)
        ceiling = _ray_hit(
            key_mesh,
            (center[0] / 1000.0, center[1] / 1000.0, key_bottom - 0.001),
            (0.0, 0.0, 1.0),
            0.020,
        )
        if ceiling is None:
            raise ValueError(f"{keys[index].name} receiver ceiling ray missed")
        insertion = stem_box[1][2] - key_box[0][2]
        reserve = ceiling.z * 1000.0 - stem_box[1][2]
        per_travel = []
        for travel_mm in travel_samples:
            offset = (0.0, 0.0, -travel_mm / 1000.0)
            moved_key = _transform_mesh(key_mesh, (center[0] / 1000.0, center[1] / 1000.0), offset=offset)
            moved_stem = _transform_mesh(stem_mesh, (center[0] / 1000.0, center[1] / 1000.0), offset=offset)
            cap_stem, cap_reason = _intersects(moved_key, moved_stem)
            static_hits = []
            for label, target in (
                ("cover", top_meshes[index]),
                ("flange", flange_meshes[index]),
                ("plate", plate_mesh),
                ("lower_housing", housing_mesh),
            ):
                hit, reason = _intersects(moved_stem, target)
                if hit:
                    static_hits.append({"target": label, "reason": reason})
            if cap_stem:
                collision_indices.add(index)
            if static_hits:
                static_collision_indices.add(index)
            per_travel.append({
                "travel_mm": travel_mm,
                "key_material_stem_collision": cap_stem,
                "key_material_stem_reason": cap_reason,
                "stem_static_collisions": static_hits,
            })
        rows.append({
            "index": index,
            "receiver_mm": {k: round(v, 5) for k, v in receiver.items()},
            "stem_mm": {k: round(v, 5) for k, v in stem.items()},
            "receiver_ceiling_z_mm": round(ceiling.z * 1000.0, 5),
            "stem_bbox_z_mm": [round(stem_box[0][2], 5), round(stem_box[1][2], 5)],
            "insertion_mm": round(insertion, 5),
            "ceiling_reserve_mm": round(reserve, 5),
            "per_travel": per_travel,
        })
    expected = {
        "receiver_span": float(cfg["receiver_span"]),
        "receiver_horizontal_arm": float(cfg["receiver_horizontal_arm"]),
        "receiver_vertical_arm": float(cfg["receiver_vertical_arm"]),
        "stem_span": float(cfg["mating_cross_span"]),
        "stem_horizontal_arm": float(cfg["mating_horizontal_arm"]),
        "stem_vertical_arm": float(cfg["mating_vertical_arm"]),
        "receiver_depth": float(cfg["receiver_depth"]),
    }
    dim_ok = all(
        abs(row["receiver_mm"]["span_x"] - expected["receiver_span"]) <= 0.05
        and abs(row["receiver_mm"]["span_y"] - expected["receiver_span"]) <= 0.05
        and abs(row["receiver_mm"]["horizontal_arm"] - expected["receiver_horizontal_arm"]) <= 0.05
        and abs(row["receiver_mm"]["vertical_arm"] - expected["receiver_vertical_arm"]) <= 0.05
        and abs(row["stem_mm"]["span_x"] - expected["stem_span"]) <= 0.05
        and abs(row["stem_mm"]["span_y"] - expected["stem_span"]) <= 0.05
        and abs(row["stem_mm"]["horizontal_arm"] - expected["stem_horizontal_arm"]) <= 0.05
        and abs(row["stem_mm"]["vertical_arm"] - expected["stem_vertical_arm"]) <= 0.05
        for row in rows
    )
    return {
        "method": "evaluated_mesh_rays_and_bvh_virtual_travel",
        "cells_checked": len(rows),
        "travel_samples_mm": list(travel_samples),
        "expected_mm": expected,
        "dimensions_within_0_05_mm": dim_ok,
        "key_material_stem_collision_indices": sorted(collision_indices),
        "stem_static_collision_indices": sorted(static_collision_indices),
        "insertion_range_mm": [round(min(r["insertion_mm"] for r in rows), 5), round(max(r["insertion_mm"] for r in rows), 5)],
        "ceiling_reserve_range_mm": [round(min(r["ceiling_reserve_mm"] for r in rows), 5), round(max(r["ceiling_reserve_mm"] for r in rows), 5)],
        "rows": rows,
        "qualification": "digital prototype geometry only; retention/force and factory interchangeability remain unqualified",
    }


def _spacebar_interface(keys, travel_samples, cfg):
    widths = {i: _dims_mm(_bbox_mm(obj))[0] for i, obj in keys.items()}
    max_width = max(widths.values())
    wide = [(i, keys[i]) for i, width in widths.items() if abs(width - max_width) <= 0.05]
    if len(wide) != 1:
        raise ValueError(f"expected one wide key, got {len(wide)}")
    next_width = max(width for i, width in widths.items() if i != wide[0][0])
    if max_width - next_width <= 0.05:
        raise ValueError("wide key is not geometrically distinct from 1U keys")
    index, cap = wide[0]
    sleeves = [bpy.data.objects.get(f"RK_GUIDE_SLEEVE_{i}") for i in range(2)]
    if any(obj is None for obj in sleeves):
        raise ValueError("missing RK_GUIDE_SLEEVE_0/1")
    cap_mesh = _tri_mesh(cap)
    cap_box = _bbox_mm(cap)
    cx, cy = _center_xy(cap_box)
    rows = []
    any_collision = False
    for guide_index, (dx_mm, sleeve) in enumerate(zip(cfg["guide_offsets_x"], sleeves)):
        gx, gy = (cx + float(dx_mm)) / 1000.0, cy / 1000.0
        bottom = _ray_hit(cap_mesh, (gx, gy, cap_box[0][2] / 1000.0 - 0.005), (0, 0, 1), 0.020)
        if bottom is None:
            raise ValueError(f"spacebar guide {guide_index} bottom ray missed")
        z_probe = bottom.z + 0.001
        pos = _ray_hit(cap_mesh, (gx, gy, z_probe), (1, 0, 0), 0.010)
        neg = _ray_hit(cap_mesh, (gx, gy, z_probe), (-1, 0, 0), 0.010)
        if pos is None or neg is None:
            raise ValueError(f"spacebar guide {guide_index} diameter ray missed")
        pin_diameter = (pos - neg).length * 1000.0
        sleeve_box = _bbox_mm(sleeve)
        sleeve_mesh = _tri_mesh(sleeve)
        per_travel = []
        for travel_mm in travel_samples:
            moved_cap = _transform_mesh(
                cap_mesh, (cx / 1000.0, cy / 1000.0), offset=(0, 0, -travel_mm / 1000.0)
            )
            collision, reason = _intersects(moved_cap, sleeve_mesh)
            any_collision |= collision
            pin_bottom = bottom.z * 1000.0 - travel_mm
            engagement = max(0.0, sleeve_box[1][2] - max(sleeve_box[0][2], pin_bottom))
            per_travel.append({
                "travel_mm": travel_mm,
                "collision": collision,
                "reason": reason,
                "axial_engagement_mm": round(engagement, 5),
            })
        rows.append({
            "guide_index": guide_index,
            "center_xy_mm": [round(gx * 1000, 5), round(gy * 1000, 5)],
            "pin_bottom_z_mm": round(bottom.z * 1000.0, 5),
            "pin_diameter_mm": round(pin_diameter, 5),
            "sleeve_bbox_mm": [[round(v, 5) for v in sleeve_box[0]], [round(v, 5) for v in sleeve_box[1]]],
            "per_travel": per_travel,
        })
    return {
        "method": "actual_wide_cap_union_rays_plus_evaluated_mesh_bvh",
        "wide_key_index": index,
        "guides_checked": len(rows),
        "travel_samples_mm": list(travel_samples),
        "collision_free": not any_collision,
        "rest_engagement_range_mm": [
            round(min(r["per_travel"][0]["axial_engagement_mm"] for r in rows), 5),
            round(max(r["per_travel"][0]["axial_engagement_mm"] for r in rows), 5),
        ],
        "rows": rows,
        "qualification": "custom guide digital sliding geometry only; friction/rattle/load require physical testing",
    }


def _encoder_interface(knobs, interfaces):
    shafts = {i: bpy.data.objects.get(f"RK_ENCODER_SHAFT_{i}") for i in range(1, 6)}
    if len(knobs) != 5 or any(obj is None for obj in shafts.values()):
        raise ValueError("expected five complete knob/encoder-shaft pairs")
    cfg = interfaces["encoder"]
    rows = []
    for index in range(1, 6):
        knob = knobs[index]
        shaft = shafts[index]
        knob_mesh = _tri_mesh(knob)
        shaft_mesh = _tri_mesh(shaft)
        box = _bbox_mm(knob)
        cx, cy = (v / 1000.0 for v in _center_xy(box))
        z_probe = (float(cfg["receiver_flat_start_z"]) + 1.0) / 1000.0
        knob_flat = _ray_hit(knob_mesh, (cx, cy, z_probe), (0, 1, 0), 0.010)
        shaft_flat = _ray_hit(shaft_mesh, (cx, cy, z_probe), (0, 1, 0), 0.010)
        if knob_flat is None or shaft_flat is None:
            raise ValueError(f"encoder {index} flat probe missed")
        matching = []
        for angle in (0.0, 0.6, 1.2):
            moved_knob = _transform_mesh(knob_mesh, (cx, cy), angle=angle)
            moved_shaft = _transform_mesh(shaft_mesh, (cx, cy), angle=angle)
            collision, reason = _intersects(moved_knob, moved_shaft)
            matching.append({"angle_rad": angle, "collision": collision, "reason": reason})
        mismatch_shaft = _transform_mesh(shaft_mesh, (cx, cy), angle=0.6)
        mismatch_collision, mismatch_reason = _intersects(knob_mesh, mismatch_shaft)
        offset_shaft = _transform_mesh(shaft_mesh, (cx, cy), offset=(0.0, 0.0003, 0.0))
        offset_collision, offset_reason = _intersects(knob_mesh, offset_shaft)
        shaft_box = _bbox_mm(shaft)
        engagement = min(shaft_box[1][2], float(cfg["receiver_ceiling_z"])) - max(
            float(cfg["receiver_flat_start_z"]), float(cfg["shaft_flat_start_z"])
        )
        rows.append({
            "index": index,
            "knob_flat_y_mm": round((knob_flat.y - cy) * 1000.0, 5),
            "shaft_flat_y_mm": round((shaft_flat.y - cy) * 1000.0, 5),
            "D_engagement_mm": round(engagement, 5),
            "matching_rotation_probes": matching,
            "negative_mismatch": {"angle_rad": 0.6, "collision": mismatch_collision, "reason": mismatch_reason},
            "negative_offset": {"offset_y_mm": 0.3, "collision": offset_collision, "reason": offset_reason},
        })
    return {
        "method": "evaluated_mesh_D_receiver_rays_and_virtual_common_rotation",
        "pairs_checked": len(rows),
        "matching_rotations_collision_free": all(
            not p["collision"] for row in rows for p in row["matching_rotation_probes"]
        ),
        "negative_controls_detect_collision": all(
            row["negative_mismatch"]["collision"] and row["negative_offset"]["collision"] for row in rows
        ),
        "engagement_range_mm": [round(min(r["D_engagement_mm"] for r in rows), 5), round(max(r["D_engagement_mm"] for r in rows), 5)],
        "rows": rows,
        "qualification": "nominal digital D coupling only; retention, tolerance stack and physical fit remain unqualified",
    }


def inspect(source_sha256=None) -> dict:
    """Return revision-local geometry evidence for the currently loaded scene."""
    layout, interfaces, expected_switches, travel_samples, expected_envelope = _contracts()
    housing = bpy.data.objects.get("RK_SWITCH_HOUSINGS")
    plate = bpy.data.objects.get("RK_MAIN_PLATE")
    if housing is None or plate is None:
        raise ValueError("scene is missing RK_SWITCH_HOUSINGS or RK_MAIN_PLATE")

    keys = _indexed("RK_KEY_")
    tops = _indexed("RK_SWITCH_TOP_")
    flanges = _indexed("RK_SWITCH_FLANGE_")
    stems = _indexed("RK_SWITCH_STEM_")
    knobs = _indexed("RK_KNOB_")
    # Contact names end in L/R rather than a numeric suffix; build them explicitly.
    contacts_left = {i: bpy.data.objects.get(f"RK_CONTACT_{i:02d}_L") for i in range(expected_switches)}
    contacts_right = {i: bpy.data.objects.get(f"RK_CONTACT_{i:02d}_R") for i in range(expected_switches)}
    families = (keys, tops, flanges, stems, contacts_left, contacts_right)
    if any(len(group) != expected_switches or any(obj is None for obj in group.values()) for group in families):
        raise ValueError(f"expected {expected_switches} complete key/switch cell families")

    component_boxes = _evaluated_components_mm(housing)
    housing_by_index, match_error = _match_components(component_boxes, flanges)
    assembly = _switch_assembly_evidence(
        housing_by_index, flanges, tops, stems, contacts_left, contacts_right, expected_envelope
    )
    collision = _collision_evidence(keys, tops, flanges, plate, travel_samples)
    key_stem = _key_stem_interface(
        keys, stems, tops, flanges, plate, housing, travel_samples, interfaces["keycap"]
    )
    guides = _spacebar_interface(keys, travel_samples, interfaces["spacebar"])
    encoders = _encoder_interface(knobs, interfaces)
    mesh_groups = {}
    for index, obj in sorted(keys.items()):
        mesh_groups.setdefault(obj.data.name, []).append(index)

    return {
        "switch_housings": {
            "object": housing.name,
            "method": "evaluated_mesh_connected_components",
            "evaluated_connected_shells": len(component_boxes),
            "expected": expected_switches,
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
            "status": "PASS_DIGITAL_PROTOTYPE" if (
                key_stem["dimensions_within_0_05_mm"]
                and not key_stem["key_material_stem_collision_indices"]
                and not key_stem["stem_static_collision_indices"]
            ) else "FAIL_DIGITAL_PROTOTYPE",
            "compatibility": "NOT_QUALIFIED",
            "reason": "source-guided cross geometry is modeled and inspected; retention/force and complete factory interchangeability remain unqualified",
        },
        "interfaces": {
            "key_stem": key_stem,
            "wide_guides": guides,
            "encoder_dshaft": encoders,
            "source_binding": {
                "caller_scene_sha256": source_sha256,
                "scene_filepath": bpy.data.filepath or None,
                "layout_revision": layout.get("revision"),
                "interfaces_revision": interfaces.get("revision"),
            },
        },
        "limits": [
            "This evidence checks digital geometry only; it does not establish factory switch interchangeability, retention force, electrical fit, preload, or physical manufacture.",
            f"Press travel is sampled at {', '.join(str(v) for v in travel_samples)} mm; no continuous-motion proof is claimed between samples.",
            "D-shaft matching-angle probes and guide/key travel are virtual evaluated-coordinate checks; source objects are not moved or saved.",
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
        "interfaces": {
            "key_stem": {
                "cells_checked": evidence["interfaces"]["key_stem"]["cells_checked"],
                "key_material_stem_collision_indices": evidence["interfaces"]["key_stem"]["key_material_stem_collision_indices"],
                "stem_static_collision_indices": evidence["interfaces"]["key_stem"]["stem_static_collision_indices"],
                "insertion_range_mm": evidence["interfaces"]["key_stem"]["insertion_range_mm"],
                "ceiling_reserve_range_mm": evidence["interfaces"]["key_stem"]["ceiling_reserve_range_mm"],
            },
            "wide_guides": {
                "collision_free": evidence["interfaces"]["wide_guides"]["collision_free"],
                "rest_engagement_range_mm": evidence["interfaces"]["wide_guides"]["rest_engagement_range_mm"],
            },
            "encoder_dshaft": {
                "matching_rotations_collision_free": evidence["interfaces"]["encoder_dshaft"]["matching_rotations_collision_free"],
                "negative_controls_detect_collision": evidence["interfaces"]["encoder_dshaft"]["negative_controls_detect_collision"],
                "engagement_range_mm": evidence["interfaces"]["encoder_dshaft"]["engagement_range_mm"],
            },
            "source_binding": evidence["interfaces"]["source_binding"],
        },
    }, sort_keys=True, allow_nan=False))

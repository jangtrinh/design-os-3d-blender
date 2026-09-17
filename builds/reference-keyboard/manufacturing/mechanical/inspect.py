"""Numeric C02 mechanics/DFM inspection. Physical manufacture remains blocked."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_runtime import emit_ok  # noqa: E402


def bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [min(p[i] for p in pts) * 1000 for i in range(3)]
    hi = [max(p[i] for p in pts) * 1000 for i in range(3)]
    return {"min_mm": lo, "max_mm": hi,
            "dims_mm": [hi[i] - lo[i] for i in range(3)]}


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    out = {
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "non_contiguous_edges": sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous),
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "zero_area_faces": sum(1 for f in bm.faces if f.calc_area() <= 1e-14),
        "signed_volume_mm3": bm.calc_volume(signed=True) * 1e9,
    }
    bm.free()
    return out


def pref(prefix):
    return sorted((o for o in bpy.data.objects if o.name.startswith(prefix)),
                  key=lambda o: o.name)


def close(a, b, tol=.06):
    return abs(a - b) <= tol


def exact_intersection_mm3(a, b):
    copy = a.copy()
    copy.data = a.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    mod = copy.modifiers.new("C02_INSPECT_INTERSECTION", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.solver = "EXACT"
    mod.object = b
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(copy.evaluated_get(graph), depsgraph=graph)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    volume = abs(bm.calc_volume(signed=True)) * 1e9 if bm.faces else 0.0
    bm.free()
    bpy.data.meshes.remove(mesh)
    data = copy.data
    bpy.data.objects.remove(copy, do_unlink=True)
    if not data.users:
        bpy.data.meshes.remove(data)
    return volume


def base_axis_is_clear(base, x, y):
    origin = Vector((x, y, -.005))
    direction = Vector((0, 0, 1))
    hit, _, _, _ = base.ray_cast(origin, direction, distance=.015)
    return not hit


def world_ray_distance_mm(obj, origin_world, direction_world, distance=.02):
    inv = obj.matrix_world.inverted()
    origin = inv @ Vector(origin_world)
    direction = (inv.to_3x3() @ Vector(direction_world)).normalized()
    hit, location, _, _ = obj.ray_cast(origin, direction, distance=distance)
    if not hit:
        return None
    world_hit = obj.matrix_world @ location
    return (world_hit - Vector(origin_world)).length * 1000


def counterbore_radii_mm(base, x, y, z=.00025):
    values = []
    for i in range(8):
        a = i * math.tau / 8
        values.append(world_ray_distance_mm(base, (x, y, z), (math.cos(a), math.sin(a), 0)))
    return values


def lower_support_for(screw):
    if screw.name.startswith("RK_MFG_RISER_LOWER_"):
        suffix = screw.name.removeprefix("RK_MFG_RISER_LOWER_")
        return bpy.data.objects[f"RK_ENCODER_RISER_{suffix}"]
    if screw.name.startswith("RK_MFG_CLAMP_LOWER_"):
        suffix = screw.name.removeprefix("RK_MFG_CLAMP_LOWER_")
        return bpy.data.objects[f"RK_DB_CLAMP_{suffix}"]
    raise AssertionError(screw.name)


def inspect_scene():
    bonds = pref("RK_ENCODER_BOND_")
    tabs = pref("RK_ENCODER_BOARD_SUPPORT_")
    risers = pref("RK_ENCODER_RISER_")
    lower = [o for o in pref("RK_MFG_") if "_LOWER_" in o.name]
    tops = pref("RK_ENCODER_CARRIER_SCREW_")
    clamps = pref("RK_DB_CLAMP_")
    board_screws = pref("RK_DB_BOARD_SCREW_")
    set_screws = pref("RK_KNOB_SET_SCREW_")
    counts = {"old_bonds": len(bonds), "old_bonded_tabs": len(tabs),
              "risers": len(risers), "lower_screws": len(lower),
              "top_screws": len(tops), "clamps": len(clamps),
              "board_screws": len(board_screws), "set_screws": len(set_screws)}
    checks = {
        "no_structural_epoxy_objects": len(bonds) == 0,
        "no_old_bonded_tabs": len(tabs) == 0,
        "riser_count_20": len(risers) == 20,
        "lower_fastener_count_30": len(lower) == 30,
        "carrier_top_fastener_count_20": len(tops) == 20,
        "daughter_clamp_count_10": len(clamps) == 10,
        "daughter_board_fastener_count_10": len(board_screws) == 10,
        "knob_set_screw_count_5": len(set_screws) == 5,
    }

    lower_boxes = {o.name: bbox(o) for o in lower}
    checks["lower_heads_flush_not_below_base"] = min(v["min_mm"][2] for v in lower_boxes.values()) >= -.001
    checks["lower_fasteners_are_NBK_SNZCXS_M1p6_4"] = all(
        o.get("manufacturer_part") == "SNZCXS-M1.6-4" for o in lower)
    checks["lower_screw_tip_z_4p5"] = all(close(v["max_mm"][2], 4.5) for v in lower_boxes.values())
    checks["lower_head_envelope_D2p4"] = all(
        close(v["dims_mm"][0], 2.4) and close(v["dims_mm"][1], 2.4) for v in lower_boxes.values())

    base = bpy.data.objects["RK_BASE"]
    counterbore_samples = {o.name: counterbore_radii_mm(base, o.location.x, o.location.y) for o in lower}
    counterbore_values = [r for rows in counterbore_samples.values() for r in rows if r is not None]
    counterbore_missing = sum(r is None for rows in counterbore_samples.values() for r in rows)
    checks["all_30_lower_counterbores_have_8_radial_walls"] = counterbore_missing == 0
    checks["lower_counterbore_radius_1p25"] = (
        counterbore_missing == 0 and max(abs(r - 1.25) for r in counterbore_values) <= .02)
    counterbore_head_clearances = [r - 1.20 for r in counterbore_values]
    checks["lower_head_counterbore_radial_clearance_positive"] = (
        counterbore_missing == 0 and min(counterbore_head_clearances) >= .049)

    lower_engagements, pilot_reserves = [], []
    for screw in lower:
        support = lower_support_for(screw)
        sb, pb = bbox(screw), bbox(support)
        lower_engagements.append(min(sb["max_mm"][2], pb["max_mm"][2]) - max(.5, pb["min_mm"][2]))
        pilot_hit = world_ray_distance_mm(
            support, (support.location.x, support.location.y, .001), (0, 0, 1), distance=.015)
        assert pilot_hit is not None, support.name
        pilot_ceiling_z = 1.0 + pilot_hit
        pilot_reserves.append(pilot_ceiling_z - sb["max_mm"][2])
    checks["lower_post_engagement_2p5"] = all(close(v, 2.5, .02) for v in lower_engagements)
    checks["lower_pilot_tip_reserve_0p5"] = all(close(v, .5, .02) for v in pilot_reserves)

    tip_gaps, top_knob_gaps, recessed_head_axial_gaps = [], [], []
    for top in tops:
        suffix = top.name.removeprefix("RK_ENCODER_CARRIER_SCREW_")
        bot = bpy.data.objects[f"RK_MFG_RISER_LOWER_{suffix}"]
        tip_gaps.append(bbox(top)["min_mm"][2] - bbox(bot)["max_mm"][2])
        index = int(suffix.split("_")[0])
        knob = bpy.data.objects[f"RK_KNOB_{index}"]
        if top.get("head_recessed"):
            recessed_head_axial_gaps.append(bbox(knob)["min_mm"][2] - bbox(top)["max_mm"][2])
        else:
            dx = (top.location.x - knob.location.x) * 1000
            dy = (top.location.y - knob.location.y) * 1000
            top_knob_gaps.append(math.hypot(dx, dy) - 8.0 - 1.2)
    checks["opposed_screw_tip_gap_at_least_2p1"] = min(tip_gaps) >= 2.099
    critical_tip_gap = (
        bbox(bpy.data.objects["RK_ENCODER_CARRIER_SCREW_1_2"])["min_mm"][2] -
        bbox(bpy.data.objects["RK_MFG_RISER_LOWER_1_2"])["max_mm"][2])
    checks["critical_opposed_screw_tip_gap_at_least_2p6"] = critical_tip_gap >= 2.599
    checks["top_head_knob_radial_clearance_positive"] = min(top_knob_gaps) > 0
    checks["critical_recessed_head_axial_clearance_positive"] = min(recessed_head_axial_gaps) > 0

    chassis = [(-136, -40), (136, -40), (-136, 40), (136, 40)]
    ligaments, screw_clearances = [], []
    for screw in lower:
        x, y = screw.location.x * 1000, screw.location.y * 1000
        d = min(math.hypot(x - cx, y - cy) for cx, cy in chassis)
        ligaments.append(d - 1.70 - 1.25)
        screw_clearances.append(d - 2.70 - 1.20)
    checks["lower_head_to_M3_bore_ligament_positive"] = min(ligaments) > 0
    checks["lower_head_to_M3_bottom_screw_clearance_positive"] = min(screw_clearances) > 0

    axis_clear = [base_axis_is_clear(base, o.location.x, o.location.y) for o in lower]
    checks["all_30_lower_base_axes_are_through"] = all(axis_clear)
    m3_bottom = [bpy.data.objects[f"RK_SCREW_BOTTOM_{i}"] for i in range(4)]
    lower_m3_intersections = {
        f"{o.name}:{m.name}": exact_intersection_mm3(o, m) for o in lower for m in m3_bottom
    }
    checks["lower_heads_clear_actual_M3_bottom_screws"] = max(lower_m3_intersections.values()) <= 1e-5
    post_base_intersections = {o.name: exact_intersection_mm3(o, base) for o in risers}
    checks["encoder_risers_do_not_interpenetrate_base"] = max(post_base_intersections.values()) <= 1e-5
    spacers = [bpy.data.objects[f"RK_SPACER_{i}"] for i in range(4)]
    carriers = [bpy.data.objects[f"RK_ENCODER_CARRIER_{i}"] for i in range(1, 6)]
    post_spacer_intersections = {
        f"{r.name}:{s.name}": exact_intersection_mm3(r, s) for r in risers for s in spacers
    }
    carrier_spacer_intersections = {
        f"{c.name}:{s.name}": exact_intersection_mm3(c, s) for c in carriers for s in spacers
    }
    checks["encoder_risers_clear_all_chassis_spacers"] = max(post_spacer_intersections.values()) <= 1e-5
    checks["encoder_carriers_clear_all_chassis_spacers"] = max(carrier_spacer_intersections.values()) <= 1e-5
    critical = bpy.data.objects["RK_ENCODER_RISER_1_2"]
    checks["critical_riser_center_relocated"] = (
        abs(critical.location.x * 1000 + 134.2) <= .01 and
        abs(critical.location.y * 1000 - 35.2) <= .01)
    checks["critical_riser_clears_encoder_body"] = (
        exact_intersection_mm3(critical, bpy.data.objects["RK_ENCODER_BODY_1"]) <= 1e-5)
    critical_top = bpy.data.objects["RK_ENCODER_CARRIER_SCREW_1_2"]
    checks["critical_top_screw_is_recessed_L4"] = (
        critical_top.get("manufacturer_part") == "SNZCXS-M1.6-4" and
        bool(critical_top.get("head_recessed")))
    carrier1 = bpy.data.objects["RK_ENCODER_CARRIER_1"]
    checks["critical_carrier_counterbore_edge_ligament_ge_0p35"] = (
        carrier1.get("critical_counterbore_edge_ligament_mm", 0) >= .35)

    contact_errors, body_head_gaps = [], []
    for index in range(1, 6):
        board = bpy.data.objects[f"RK_ENCODER_DAUGHTERBOARD_{index}"]
        body = bpy.data.objects[f"RK_ENCODER_BODY_{index}"]
        bb, bodyb = bbox(board), bbox(body)
        for side in ("L", "R"):
            block = bpy.data.objects[f"RK_DB_CLAMP_{index}_{side}"]
            screw = bpy.data.objects[f"RK_DB_BOARD_SCREW_{index}_{side}"]
            contact_errors.append(abs(bbox(block)["max_mm"][1] - bb["min_mm"][1]))
            body_head_gaps.append(bodyb["min_mm"][1] - bbox(screw)["max_mm"][1])
    checks["clamp_contacts_board_back_plane"] = max(contact_errors) <= .01
    checks["board_screw_head_clears_encoder_body"] = min(body_head_gaps) > 0

    tip_errors, recesses = [], []
    for index in range(1, 6):
        knob = bpy.data.objects[f"RK_KNOB_{index}"]
        screw = bpy.data.objects[f"RK_KNOB_SET_SCREW_{index}"]
        sb = bbox(screw)
        cy = knob.location.y * 1000
        tip_errors.append(abs(sb["min_mm"][1] - (cy + 1.5)))
        recesses.append((cy + 8.0) - sb["max_mm"][1])
    checks["set_screw_tip_on_PEC11R_flat"] = max(tip_errors) <= .01
    checks["set_screw_socket_end_recess_0p5"] = min(recesses) >= .499

    acrylic = bpy.data.objects["RK_DIFFUSER"]
    plate = bpy.data.objects["RK_MAIN_PLATE"]
    acrylic_plate_axial_gap = bbox(plate)["min_mm"][2] - bbox(acrylic)["max_mm"][2]
    mount_x, mount_y = -.136, -.040
    acrylic_hole_radii = counterbore_radii_mm(acrylic, mount_x, mount_y, z=.008)
    acrylic_clearance_radius = min(r for r in acrylic_hole_radii if r is not None)
    spacer_radius = bbox(bpy.data.objects["RK_SPACER_0"])["dims_mm"][0] * .5
    acrylic_spacer_radial_clearance = acrylic_clearance_radius - spacer_radius

    representative = {}
    expected = (("RK_BASE", (284, 92, 4)),
                ("RK_ENCODER_RISER_1_2", (2.5, 2.5, 8.6)),
                ("RK_DB_CLAMP_1_L", (3, 3, 8)),
                ("RK_ENCODER_CARRIER_1", (19.6, 15, 1)),
                ("RK_KNOB_1", (16, 16, 18)))
    for name, dims in expected:
        obj = bpy.data.objects[name]
        representative[name] = {"bbox": bbox(obj), "topology": topology(obj)}
        got = representative[name]["bbox"]["dims_mm"]
        checks[f"{name}_bbox"] = all(close(got[i], dims[i]) for i in range(3))
        t = representative[name]["topology"]
        checks[f"{name}_closed_positive"] = (
            t["non_manifold_edges"] == 0 and t["non_contiguous_edges"] == 0 and
            t["loose_verts"] == 0 and t["zero_area_faces"] == 0 and
            t["signed_volume_mm3"] > 0)

    failed = sorted(k for k, v in checks.items() if not v)
    return {
        "status": "pass" if not failed else "fail",
        "manufacture": "BLOCKED",
        "counts": counts,
        "checks": checks,
        "failed": failed,
        "measurements": {
            "minimum_lower_head_to_M3_bore_ligament_mm": min(ligaments),
            "minimum_lower_head_to_M3_bottom_screw_clearance_mm": min(screw_clearances),
            "maximum_lower_vs_M3_bottom_screw_intersection_mm3": max(lower_m3_intersections.values()),
            "minimum_lower_counterbore_to_head_radial_clearance_mm": min(counterbore_head_clearances),
            "maximum_lower_counterbore_radius_error_mm": max(abs(r - 1.25) for r in counterbore_values),
            "minimum_lower_post_engagement_mm": min(lower_engagements),
            "minimum_lower_pilot_tip_reserve_mm": min(pilot_reserves),
            "blocked_lower_base_axes": [o.name for o, clear in zip(lower, axis_clear) if not clear],
            "maximum_encoder_riser_base_intersection_mm3": max(post_base_intersections.values()),
            "encoder_riser_base_intersections_mm3": post_base_intersections,
            "minimum_opposed_screw_tip_gap_mm": min(tip_gaps),
            "critical_opposed_screw_tip_gap_mm": critical_tip_gap,
            "minimum_top_head_to_knob_radial_clearance_mm": min(top_knob_gaps),
            "critical_recessed_head_to_knob_axial_clearance_mm": min(recessed_head_axial_gaps),
            "maximum_encoder_riser_spacer_intersection_mm3": max(post_spacer_intersections.values()),
            "maximum_encoder_carrier_spacer_intersection_mm3": max(carrier_spacer_intersections.values()),
            "encoder_riser_spacer_intersections_mm3": post_spacer_intersections,
            "encoder_carrier_spacer_intersections_mm3": carrier_spacer_intersections,
            "maximum_clamp_to_board_plane_error_mm": max(contact_errors),
            "minimum_board_screw_head_to_encoder_body_gap_mm": min(body_head_gaps),
            "minimum_set_screw_outer_recess_mm": min(recesses),
            "maximum_set_screw_tip_plane_error_mm": max(tip_errors),
            "acrylic_to_plate_axial_gap_mm": acrylic_plate_axial_gap,
            "acrylic_to_spacer_nominal_radial_clearance_mm": acrylic_spacer_radial_clearance,
        },
        "representative": representative,
        "physical_blockers": [
            "Tapped-post strip/pull-out torque and assembly torque have not been measured.",
            "Knob axial/torsional retention has not been physically tested.",
            "Daughterboard clamp retention and copper/electrical keepouts remain unverified.",
            "KS-33 3.2 mm bottom-out and 6.4 mm boss clearance require real-switch fit trials.",
            "Material/process first articles and electrical/powered bench testing remain open."
            " Acrylic axial preload/captive retention remains open: current digital stack has a 1.6 mm plate gap and ~0.2 mm nominal radial spacer clearance."
        ]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = ap.parse_args(argv)
    report = inspect_scene()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    assert report["status"] == "pass", report["failed"]
    emit_ok("mechanics-C02-inspect", checks=len(report["checks"]), manufacture="BLOCKED")


if __name__ == "__main__":
    main()

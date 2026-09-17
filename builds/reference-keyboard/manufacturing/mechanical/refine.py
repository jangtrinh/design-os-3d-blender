"""CK-001 C02 mechanical retention/DFM refinement applied only to a copied B03 scene."""
from __future__ import annotations

import math
from pathlib import Path
import sys

import bpy

BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD / "scripts"))
import encoders as e  # noqa: E402
import mechanics as m  # noqa: E402
import meshkit as g  # noqa: E402

CRITICAL_RISER = "RK_ENCODER_RISER_1_2"
CRITICAL_XY = (-.1342, .0352)
CORNER_M3_XY = (-.136, .040)


def _remove(obj):
    data = obj.data if obj.type == "MESH" else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and not data.users:
        bpy.data.meshes.remove(data)


def _stepped_z(name, xy, rings):
    n = 64
    verts = [(r * math.cos(i * math.tau / n), r * math.sin(i * math.tau / n), z)
             for r, z in rings for i in range(n)]
    faces = [tuple(reversed(range(n))), tuple(range((len(rings) - 1) * n, len(rings) * n))]
    for a in range(len(rings) - 1):
        faces += [(a*n+i, a*n+(i+1)%n, (a+1)*n+(i+1)%n, (a+1)*n+i) for i in range(n)]
    return e._mesh(name, verts, faces, xy)


def _stepped_y(name, x, z, rings):
    n = 64
    verts = [(x + r * math.cos(i * math.tau / n), y, z + r * math.sin(i * math.tau / n))
             for r, y in rings for i in range(n)]
    faces = [tuple(reversed(range(n))), tuple(range((len(rings) - 1) * n, len(rings) * n))]
    for a in range(len(rings) - 1):
        faces += [(a*n+i, a*n+(i+1)%n, (a+1)*n+(i+1)%n, (a+1)*n+i) for i in range(n)]
    return e._mesh(name, verts, faces)


def _riser_axes():
    rows = []
    for obj in sorted((o for o in bpy.data.objects if o.name.startswith("RK_ENCODER_RISER_")), key=lambda q: q.name):
        xy = CRITICAL_XY if obj.name == CRITICAL_RISER else (obj.location.x, obj.location.y)
        rows.append((obj.name, obj.get("encoder_index"), xy))
    assert len(rows) == 20, len(rows)
    return rows


def _clamp_axes():
    rows = []
    for index in range(1, 6):
        body = bpy.data.objects[f"RK_ENCODER_BODY_{index}"]
        cx, cy = body.location.x, body.location.y
        for side, sign in (("L", -1.0), ("R", 1.0)):
            rows.append((index, side, (cx + sign * .005, cy - .0105), cy - .0085))
    return rows


def _lower_screw(name, xy, role):
    # NBK SNZCXS-M1.6-4: cylindrical extra-low head D1=2.4, L1=0.5, L=4.
    # Head is flush with the underside; the shaft ends at z4.5 and engages the
    # post from z2..4.5. No countersink-angle inference remains in C02.
    obj = _stepped_z(name, xy, ((.0012, 0.0), (.0012, .0005),
                                (.0008, .0005), (.0008, .0045)))
    obj["manufacturer_part"] = "SNZCXS-M1.6-4"
    obj["thread"] = "M1.6x0.35 analytical major envelope"
    obj["manufacturer_screw_max_torque_Nm"] = .1
    obj["role"] = role
    obj["physical_torque_status"] = "BENCH_REQUIRED"
    obj["head_geometry"] = "cylindrical extra-low D2.4 x H0.5; NBK SNZCXS"
    obj["head_z_mm"] = [0.0, .5]
    obj["shaft_z_mm"] = [.5, 4.5]
    obj["counterbore_clearance_mm"] = [2.5, .5]
    obj["post_engagement_mm"] = 2.5
    obj["lower_pilot_tip_reserve_mm"] = .5
    return obj


def _top_screw(name, xy, critical=False):
    if critical:
        rings = ((.0008, .0071), (.0008, .0111), (.0012, .0111), (.0012, .0116))
        part = "SNZCXS-M1.6-4"
    else:
        rings = ((.0008, .0066), (.0008, .0116), (.0012, .0116), (.0012, .0121))
        part = "SNZCXS-M1.6-5"
    obj = _stepped_z(name, xy, rings)
    obj["manufacturer_part"] = part
    obj["thread"] = "M1.6x0.35 analytical major envelope"
    obj["manufacturer_screw_max_torque_Nm"] = .1
    obj["physical_torque_status"] = "BENCH_REQUIRED"
    obj["head_recessed"] = bool(critical)
    return obj


def _rebuild_carrier_one():
    old = bpy.data.objects["RK_ENCODER_CARRIER_1"]
    materials = list(old.data.materials)
    body = bpy.data.objects["RK_ENCODER_BODY_1"]
    center = (body.location.x, body.location.y)
    _remove(old)
    carrier = e._ring("RK_ENCODER_CARRIER_1", e._rect_outline(e.CARRIER_X_M, e.CARRIER_Y_M),
                      e._circle(e.CARRIER_HOLE_D_M / 2), e.CARRIER_LOW_Z_M,
                      e.CARRIER_HIGH_Z_M, center)
    for material in materials:
        carrier.data.materials.append(material)
    holes = [
        (body.location.x - .0080, body.location.y - .0050),
        (body.location.x + .0080, body.location.y - .0050),
        CRITICAL_XY,
        (body.location.x + .0080, body.location.y + .0050),
    ]
    cutters = [g.cylinder(f"TMP_CARRIER1_HOLE_{i}", .0009, .0105, .0117, xy, segments=64)
               for i, xy in enumerate(holes)]
    cutters.append(g.cylinder("TMP_CARRIER1_M3_RELIEF", .0029, .0105, .0117,
                              CORNER_M3_XY, segments=96))
    cutters.append(g.cylinder("TMP_CARRIER1_CRITICAL_HEAD_SEAT", .00125, .0111, .0117,
                              CRITICAL_XY, segments=64))
    bpy.context.view_layer.update()
    m.operation(carrier, m.combine_cutters("TMP_CARRIER1_ALL_CUTS", cutters))
    carrier["encoder_index"] = 1
    carrier["component_role"] = "custom 6061-T6 encoder carrier plate"
    carrier["material_design_choice"] = "6061-T6 machined carrier, strength not qualified"
    carrier["plate_clearance_required_m"] = .0164
    carrier["knob_bottom_clearance_m"] = .0004
    carrier["m1_6_clearance_diameter_m"] = .0018
    carrier["edge_ligament_x_m"] = .0007
    carrier["knob_counterbore_diameter_m"] = .0126
    carrier["knob_receiver_flat_y_m"] = .00165
    carrier["knob_receiver_z_m"] = [.0206, .0280]
    carrier["knob_slot_floor_z_m"] = .0292
    carrier["critical_riser_center_mm"] = [CRITICAL_XY[0] * 1000, CRITICAL_XY[1] * 1000]
    carrier["corner_spacer_relief_diameter_mm"] = 5.8
    carrier["critical_head_counterbore_mm"] = [2.5, .5]
    carrier["critical_counterbore_edge_ligament_mm"] = .35
    carrier["critical_counterbore_to_spacer_relief_ligament_mm"] = .976
    carrier["physical_strength_status"] = "BENCH_REQUIRED"
    return carrier


def _board_screw(name, x, cy):
    board_y = cy - .0085
    # Head is in front of the board; 3 mm shaft passes 1 mm board + 2 mm block.
    obj = _stepped_y(name, x, .008, ((.0012, board_y + .0010), (.0012, board_y + .0005),
                                     (.0008, board_y + .0005), (.0008, board_y - .0025)))
    obj["manufacturer_part"] = "SNZCXS-M1.6-3"
    obj["thread"] = "M1.6x0.35 analytical major envelope"
    obj["manufacturer_screw_max_torque_Nm"] = .1
    obj["physical_torque_status"] = "BENCH_REQUIRED"
    return obj


def _set_screw(name, cx, cy):
    # +Y socket end at +7.5; flat tip at +1.5 = PEC11R shaft flat plane.
    obj = _stepped_y(name, cx, .023, ((.001, cy + .0015), (.001, cy + .0075)))
    obj["manufacturer_part"] = "SNTS-M2-6-FP"
    obj["thread"] = "M2x0.4 analytical major envelope; intentional thread-zone overlap"
    obj["manufacturer_screw_max_torque_Nm"] = .2
    obj["flat_tip_plane_y_m"] = cy + .0015
    obj["socket_end_recess_mm"] = .5
    obj["positive_axial_retention"] = "constructed; holding force BENCH_REQUIRED"
    return obj


def apply():
    bonds = [o for o in bpy.data.objects if o.name.startswith("RK_ENCODER_BOND_")]
    tabs = [o for o in bpy.data.objects if o.name.startswith("RK_ENCODER_BOARD_SUPPORT_")]
    old_top = [o for o in bpy.data.objects if o.name.startswith("RK_ENCODER_CARRIER_SCREW_")]
    assert (len(bonds), len(tabs), len(old_top)) == (30, 10, 20), (len(bonds), len(tabs), len(old_top))
    risers = _riser_axes()
    for obj in bonds + tabs + old_top:
        _remove(obj)
    for name, _, _ in risers:
        _remove(bpy.data.objects[name])
    _rebuild_carrier_one()

    # Rebuild 19 posts at original XY plus the corrected corner post.
    for name, index, xy in risers:
        post = g.cylinder(name, .00125, .002, .0106, xy, segments=96)
        upper_low = .0071 if name == CRITICAL_RISER else .0066
        cutters = [g.cylinder(f"TMP_{name}_LOW", .00065, .0019, .0050, xy, segments=64),
                   g.cylinder(f"TMP_{name}_TOP", .00065, upper_low, .0107, xy, segments=64)]
        bpy.context.view_layer.update()
        m.operation(post, m.combine_cutters(f"TMP_{name}_TAPS", cutters))
        post["encoder_index"] = index
        post["component_role"] = "base-fastened brass encoder-carrier riser"
        post["attachment_method"] = "opposed M1.6 screws; no structural adhesive"
        post["tap_drill_diameter_mm"] = 1.30
        post["thread_zones_mm"] = [[2.0, 5.0], [upper_low * 1000, 10.6]]
        post["thread_tip_gap_mm"] = 2.6 if name == CRITICAL_RISER else 2.1
        post["physical_strength_status"] = "BENCH_REQUIRED"

    clamp_axes = _clamp_axes()
    all_lower_axes = [(xy, f"RK_MFG_RISER_LOWER_{name.removeprefix('RK_ENCODER_RISER_')}", "encoder-riser")
                      for name, _, xy in risers]
    all_lower_axes += [(xy, f"RK_MFG_CLAMP_LOWER_{index}_{side}", "daughterboard-clamp")
                       for index, side, xy, _ in clamp_axes]

    # Real base floor holes plus cylindrical counterbores for sourced C02 heads.
    # One stepped cutter per fastener keeps this a single Exact boolean on the
    # inherited B03 base; attempt-0001 showed that a second whole-base boolean
    # could destabilize a pre-existing USB support hole far from the new cuts.
    base = bpy.data.objects["RK_BASE"]
    stepped = [_stepped_z(f"TMP_BASE_FASTENER_{i}", xy,
                          ((.00125, -.0002), (.00125, .0005),
                           (.0009, .0005), (.0009, .0042)))
               for i, (xy, _, _) in enumerate(all_lower_axes)]
    # e._mesh applies XY as object transforms. Force matrix_world current before
    # combine_cutters bakes the per-object transforms into one cutter mesh.
    bpy.context.view_layer.update()
    m.operation(base, m.combine_cutters("TMP_BASE_FASTENER_ALL", stepped))
    base["mfg_lower_fastener_count"] = 30
    base["lower_head_seat"] = "D2.5 x0.5 cylindrical counterbore for NBK SNZCXS-M1.6-4 D2.4 x H0.5 head"
    base["lower_head_counterbore_mm"] = [2.5, .5]
    base["lower_head_nominal_radial_clearance_mm"] = .05

    for xy, name, role in all_lower_axes:
        _lower_screw(name, xy, role)
    for name, _, xy in risers:
        suffix = name.removeprefix("RK_ENCODER_RISER_")
        _top_screw(f"RK_ENCODER_CARRIER_SCREW_{suffix}", xy, critical=name == CRITICAL_RISER)

    # Replace bonded daughterboard tabs with base-fastened blocks and board screws.
    for index in range(1, 6):
        board = bpy.data.objects[f"RK_ENCODER_DAUGHTERBOARD_{index}"]
        body = bpy.data.objects[f"RK_ENCODER_BODY_{index}"]
        cy = body.location.y
        xs = [body.location.x - .005, body.location.x + .005]
        board_y = cy - .0085
        holes = [e._axis_y_cylinder(f"TMP_DB_HOLE_{index}_{j}", .0009,
                                    board_y - .0007, board_y + .0007, (x, .008), (0, 0))
                 for j, x in enumerate(xs)]
        m.operation(board, m.combine_cutters(f"TMP_DB_HOLES_{index}", holes))
        board["mechanical_fastener_holes"] = "2x M1.6 clearance, x=encoder±5 mm, z=8 mm"
        board["electrical_keepout_status"] = "UNQUALIFIED_NO_COPPER_NETLIST"
        for side, x in zip(("L", "R"), xs):
            by = cy - .0105
            block = e._solid_box(f"RK_DB_CLAMP_{index}_{side}", .003, .003, .002, .010, (x, by))
            lower = g.cylinder(f"TMP_CLAMP_LOW_{index}_{side}", .00065, .0019, .0050, (x, by), segments=64)
            horiz = e._axis_y_cylinder(f"TMP_CLAMP_SIDE_{index}_{side}", .00065,
                                       cy - .0111, cy - .0089, (x, .008), (0, 0))
            bpy.context.view_layer.update()
            m.operation(block, m.combine_cutters(f"TMP_CLAMP_TAPS_{index}_{side}", [lower, horiz]))
            block["component_role"] = "base-fastened daughterboard clamp"
            block["attachment_method"] = "SNZCXS-M1.6-4 lower + SNZCXS-M1.6-3 board screw; no structural adhesive"
            block["tap_drill_diameter_mm"] = 1.30
            block["lower_thread_zone_mm"] = [2.0, 5.0]
            block["physical_strength_status"] = "BENCH_REQUIRED"
            _board_screw(f"RK_DB_BOARD_SCREW_{index}_{side}", x, cy)

    # Positive knob retention: radial M2 tap-drill + flat-point set screw to PEC11R D flat.
    for index in range(1, 6):
        knob = bpy.data.objects[f"RK_KNOB_{index}"]
        cx, cy = knob.location.x, knob.location.y
        cutter = e._axis_y_cylinder(f"TMP_KNOB_SET_BORE_{index}", .000825,
                                    cy + .00135, cy + .0082, (cx, .023), (0, 0))
        m.operation(knob, cutter)
        knob["set_screw_part"] = "SNTS-M2-6-FP"
        knob["set_screw_tap_drill_mm"] = 1.65
        knob["set_screw_axis"] = "+Y at world z=23 mm"
        knob["shaft_retention_status"] = "POSITIVE_CLAMP_CONSTRUCTED; HOLDING_FORCE_BENCH_REQUIRED"
        _set_screw(f"RK_KNOB_SET_SCREW_{index}", cx, cy)

    bpy.context.scene["manufacturing_revision"] = "mechanics-C02"
    bpy.context.scene["manufacture_status"] = "BLOCKED_PHYSICAL_EVIDENCE_REQUIRED"
    bpy.context.scene["electrical_status"] = "BLOCKED_DESIGN_AND_BENCH_REQUIRED"
    bpy.context.view_layer.update()
    return {"removed_bonds": 30, "removed_tabs": 10, "risers": 20, "lower_screws": 30,
            "top_screws": 20, "clamps": 10, "board_screws": 10, "set_screws": 5}

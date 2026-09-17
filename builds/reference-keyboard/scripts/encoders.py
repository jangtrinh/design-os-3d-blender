"""Native PEC11R encoder envelopes and the CK-001 custom carrier system.

Units are metres. Manufacturer-sourced dimensions are kept separate from local
carrier/clearance choices through object custom properties. No electrical/netlist
claim is made here.
"""
from __future__ import annotations

import math

import bmesh
import bpy
import mechanics


# Bourns PEC11R-1xxxF-Nxxxx, flatted L15 shaft.
BODY_X_M = 0.0125
BODY_Y_M = 0.0134
BODY_DEPTH_M = 0.0055
SHAFT_DIAMETER_M = 0.0060
SHAFT_L_M = 0.0150
BUSHING_L_M = 0.0050
FLAT_L_M = 0.0070
FLAT_Y_M = 0.0015  # +Y flat plane on the Ø6 shaft => 4.5 mm across-flat.
BUSHING_OD_M = 0.0070
THREAD_PITCH_M = 0.00075
WASHER_OD_M = 0.0120
WASHER_ID_M = 0.0072  # local clearance, source washer hole is 7.1 ± 0.3 mm.
WASHER_T_M = 0.0005
NUT_AF_M = 0.0100
NUT_T_M = 0.0020

# CK-001 carrier revision. It replaces the infeasible plate-mounted concept:
# the Ø16.4 knob/plate opening cannot support a Ø12 washer or 10 AF nut.
MOUNT_Z_M = 0.0106
BODY_BOTTOM_Z_M = MOUNT_Z_M - BODY_DEPTH_M
BUSHING_TOP_Z_M = MOUNT_Z_M + BUSHING_L_M
SHAFT_TIP_Z_M = MOUNT_Z_M + SHAFT_L_M
FLAT_START_Z_M = SHAFT_TIP_Z_M - FLAT_L_M
CARRIER_LOW_Z_M = MOUNT_Z_M
CARRIER_HIGH_Z_M = 0.0116
CARRIER_X_M = 0.0196
CARRIER_Y_M = 0.0150
CARRIER_HOLE_D_M = 0.0072
WASHER_LOW_Z_M = CARRIER_HIGH_Z_M
WASHER_HIGH_Z_M = WASHER_LOW_Z_M + WASHER_T_M
NUT_LOW_Z_M = WASHER_HIGH_Z_M
NUT_HIGH_Z_M = NUT_LOW_Z_M + NUT_T_M
RISER_LOW_Z_M = 0.0020
RISER_RADIUS_M = 0.00125
RISER_X_M = 0.0080
RISER_Y_M = 0.0050
CARRIER_FASTENER_CLEARANCE_D_M = 0.0018
RISER_TAP_BORE_D_M = 0.0014
RISER_TAP_LOW_Z_M = 0.0056
FASTENER_MAJOR_D_M = 0.0016
FASTENER_HEAD_D_M = 0.0024
FASTENER_HEAD_HIGH_Z_M = 0.0122
DAUGHTERBOARD_CENTER_Y_M = -0.0085
DAUGHTERBOARD_HOLE_D_M = 0.0010
DAUGHTERBOARD_PAD_OD_M = 0.0020

# The owner-selected knob interface that this encoder must fit.
KNOB_BOTTOM_Z_M = 0.0120
KNOB_COUNTERBORE_D_M = 0.0126
KNOB_ROUND_LEAD_D_M = 0.0062
KNOB_D_FLAT_Y_M = 0.00165
KNOB_D_START_Z_M = 0.0206
KNOB_RECEIVER_TOP_Z_M = 0.0280
KNOB_SLOT_FLOOR_Z_M = 0.0292
PLATE_CLEARANCE_D_M = 0.0164
MAIN_PCB_CLEARANCE_X_M = 0.0204
MAIN_PCB_CLEARANCE_Y_M = 0.0166

SOURCE = "Bourns PEC11R Series 12 mm Incremental Encoder, current PDF retrieved 2026-09-17"
SOURCE_SHA256 = "ac88f657e611bc82fe79b102426fb5abcb7f40740540f0c681727e2d74784491"


def _mesh(name, verts, faces, xy=(0.0, 0.0)):
    if bpy.data.objects.get(name) is not None:
        raise ValueError(f"object name already exists: {name}")
    data = bpy.data.meshes.new(name + "_Mesh")
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(data)
    bm.free()
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.x, obj.location.y = xy
    return obj


def _prism(name, profile, low, high, xy=(0.0, 0.0)):
    n = len(profile)
    verts = [(x, y, z) for z in (low, high) for x, y in profile]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return _mesh(name, verts, faces, xy)


def _rect(w, d):
    return [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]


def _circle(radius, count=96):
    return [(radius * math.cos(i * math.tau / count), radius * math.sin(i * math.tau / count))
            for i in range(count)]


def _rect_outline(w, d, count=96):
    if count % 4:
        raise ValueError("rectangle outline point count must be divisible by four")
    per = count // 4
    hx, hy = w / 2, d / 2
    corners = [(hx, -hy), (hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy)]
    out = []
    for a, b in zip(corners, corners[1:]):
        out.extend((a[0] + (b[0] - a[0]) * i / per,
                    a[1] + (b[1] - a[1]) * i / per) for i in range(per))
    return out


def _hex_outline(across_flats, count=96):
    if count % 6:
        raise ValueError("hex outline point count must be divisible by six")
    radius = across_flats / math.sqrt(3.0)
    corners = [(radius * math.cos(math.radians(30 + 60 * i)),
                radius * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    corners.append(corners[0])
    per = count // 6
    out = []
    for a, b in zip(corners, corners[1:]):
        out.extend((a[0] + (b[0] - a[0]) * i / per,
                    a[1] + (b[1] - a[1]) * i / per) for i in range(per))
    return out


def _ring(name, outer, inner, low, high, xy=(0.0, 0.0)):
    if len(outer) != len(inner):
        raise ValueError("ring boundaries must have equal point counts")
    n = len(outer)
    verts = ([(x, y, low) for x, y in outer] + [(x, y, low) for x, y in inner] +
             [(x, y, high) for x, y in outer] + [(x, y, high) for x, y in inner])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        bo, bi, to, ti = i, n + i, 2 * n + i, 3 * n + i
        boj, bij, toj, tij = j, n + j, 2 * n + j, 3 * n + j
        faces += [(bo, boj, toj, to), (bij, bi, ti, tij),
                  (boj, bo, bi, bij), (to, toj, tij, ti)]
    return _mesh(name, verts, faces, xy)


def _axis_y_cylinder(name, radius, y_low, y_high, xz, xy):
    ring = _circle(radius, 64)
    verts = ([(xz[0] + x, y_low, xz[1] + z) for x, z in ring] +
             [(xz[0] + x, y_high, xz[1] + z) for x, z in ring])
    n = len(ring)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return _mesh(name, verts, faces, xy)


def _axis_y_ring(name, outer_r, inner_r, y_low, y_high, xz, xy):
    outer, inner = _circle(outer_r, 64), _circle(inner_r, 64)
    n = len(outer)
    verts = ([(xz[0] + x, y_low, xz[1] + z) for x, z in outer] +
             [(xz[0] + x, y_low, xz[1] + z) for x, z in inner] +
             [(xz[0] + x, y_high, xz[1] + z) for x, z in outer] +
             [(xz[0] + x, y_high, xz[1] + z) for x, z in inner])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        bo, bi, to, ti = i, n + i, 2 * n + i, 3 * n + i
        boj, bij, toj, tij = j, n + j, 2 * n + j, 3 * n + j
        faces += [(bo, boj, toj, to), (bij, bi, ti, tij),
                  (boj, bo, bi, bij), (to, toj, tij, ti)]
    return _mesh(name, verts, faces, xy)


def _carrier_screw(name, xy):
    shaft_r, head_r = FASTENER_MAJOR_D_M / 2, FASTENER_HEAD_D_M / 2
    rings = [
        [(shaft_r * math.cos(a), shaft_r * math.sin(a), RISER_TAP_LOW_Z_M)
         for a in (i * math.tau / 64 for i in range(64))],
        [(shaft_r * math.cos(a), shaft_r * math.sin(a), CARRIER_HIGH_Z_M)
         for a in (i * math.tau / 64 for i in range(64))],
        [(head_r * math.cos(a), head_r * math.sin(a), CARRIER_HIGH_Z_M)
         for a in (i * math.tau / 64 for i in range(64))],
        [(head_r * math.cos(a), head_r * math.sin(a), FASTENER_HEAD_HIGH_Z_M)
         for a in (i * math.tau / 64 for i in range(64))],
    ]
    verts = [v for ring in rings for v in ring]
    n = 64
    faces = [tuple(reversed(range(n))), tuple(range(3 * n, 4 * n))]
    for a, b in ((0, 1), (1, 2), (2, 3)):
        faces += [(a * n + i, a * n + (i + 1) % n,
                   b * n + (i + 1) % n, b * n + i) for i in range(n)]
    obj = _mesh(name, verts, faces, xy)
    obj["thread_envelope"] = "M1.6 prototype analytical thread envelope; no helical contact model"
    obj["shaft_length_m"] = CARRIER_HIGH_Z_M - RISER_TAP_LOW_Z_M
    return obj


def _shaft_outlines(radius=SHAFT_DIAMETER_M / 2, flat_y=FLAT_Y_M,
                    arc_count=80, flat_count=16):
    alpha = math.asin(flat_y / radius)
    # Keep the 240 degree circle arc where y <= flat_y: 150° -> 390°.
    arc_span = math.pi + 2 * alpha
    arc = [(radius * math.cos(math.pi - alpha + arc_span * i / (arc_count - 1)),
            radius * math.sin(math.pi - alpha + arc_span * i / (arc_count - 1)))
           for i in range(arc_count)]
    x_right = math.sqrt(radius * radius - flat_y * flat_y)
    flat = [(x_right - 2 * x_right * (i + 1) / (flat_count + 1), flat_y)
            for i in range(flat_count)]
    upper_arc = [(radius * math.cos(alpha + (math.pi - 2 * alpha) * (i + 1) / (flat_count + 1)),
                  radius * math.sin(alpha + (math.pi - 2 * alpha) * (i + 1) / (flat_count + 1)))
                 for i in range(flat_count)]
    return arc + upper_arc, arc + flat, arc_count


def _shaft(index, xy):
    circle, dshape, arc_count = _shaft_outlines()
    n = len(circle)
    verts = ([(x, y, MOUNT_Z_M) for x, y in circle] +
             [(x, y, FLAT_START_Z_M) for x, y in circle])
    bottom = list(range(n))
    lower_top = list(range(n, 2 * n))
    flat_bottom = []
    for x, y in dshape[arc_count:]:
        flat_bottom.append(len(verts))
        verts.append((x, y, FLAT_START_Z_M))
    d_bottom = lower_top[:arc_count] + flat_bottom
    d_top = []
    for x, y in dshape:
        d_top.append(len(verts))
        verts.append((x, y, SHAFT_TIP_Z_M))
    faces = [tuple(reversed(bottom)), tuple(d_top)]
    for i in range(n):
        j = (i + 1) % n
        faces.append((bottom[i], bottom[j], lower_top[j], lower_top[i]))
        faces.append((d_bottom[i], d_bottom[j], d_top[j], d_top[i]))
    # Close the circular segment removed by the D-flat at the exact F datum.
    crescent = ([lower_top[arc_count - 1]] + lower_top[arc_count:] + [lower_top[0]] +
                list(reversed(flat_bottom)))
    faces.append(tuple(crescent))
    shaft = _mesh(f"RK_ENCODER_SHAFT_{index}", verts, faces, xy)
    shaft["source_family"] = "PEC11R flatted shaft L15/LB5/F7"
    shaft["nominal_diameter_m"] = SHAFT_DIAMETER_M
    shaft["flat_y_m"] = FLAT_Y_M
    shaft["flat_start_z_m"] = FLAT_START_Z_M
    shaft["shaft_tip_z_m"] = SHAFT_TIP_Z_M
    shaft["motion_role"] = "rotate_with_matching_RK_KNOB"
    knob = bpy.data.objects.get(f"RK_KNOB_{index}")
    if knob is not None:
        con = shaft.constraints.new("COPY_ROTATION")
        con.name = f"ROTATE_WITH_RK_KNOB_{index}"
        con.target = knob
        con.use_x = con.use_y = False
        con.use_z = True
        con.target_space = con.owner_space = "WORLD"
    else:
        shaft["rotation_target"] = f"RK_KNOB_{index}"
    return shaft


def _solid_box(name, sx, sy, low, high, xy):
    return _prism(name, _rect(sx, sy), low, high, xy)


def _preflight_names(count):
    names = []
    for i in range(1, count + 1):
        names += [f"RK_ENCODER_BODY_{i}", f"RK_ENCODER_SHAFT_{i}", f"RK_ENCODER_BUSHING_{i}",
                  f"RK_ENCODER_WASHER_{i}", f"RK_ENCODER_NUT_{i}", f"RK_ENCODER_CARRIER_{i}",
                  f"RK_ENCODER_DAUGHTERBOARD_{i}"]
        names += [f"RK_ENCODER_PIN_{i}_{p}" for p in ("A", "C", "B")]
        names += [f"RK_ENCODER_PAD_{i}_{p}" for p in ("A", "C", "B")]
        names += [f"RK_ENCODER_EAR_{i}_{side}" for side in ("L", "R")]
        names += [f"RK_ENCODER_RISER_{i}_{k}" for k in range(4)]
        names += [f"RK_ENCODER_CARRIER_SCREW_{i}_{k}" for k in range(4)]
        names += [f"RK_ENCODER_BOARD_SUPPORT_{i}_{side}" for side in ("L", "R")]
    clash = [name for name in names if bpy.data.objects.get(name) is not None]
    if clash:
        raise ValueError(f"encoder build would overwrite existing objects: {clash}")


def build(layout_dict):
    """Build five PEC11R envelopes at layout_dict['knobs_mm']; return all objects."""
    positions = layout_dict.get("knobs_mm") or []
    if len(positions) != 5:
        raise ValueError(f"expected five knob positions, got {len(positions)}")
    _preflight_names(len(positions))
    out = []
    body_gap = min(math.hypot(max(abs(a[0] - b[0]) - BODY_X_M * 1000, 0.0),
                              max(abs(a[1] - b[1]) - BODY_Y_M * 1000, 0.0))
                   for n, a in enumerate(positions) for b in positions[n + 1:])
    for index, point in enumerate(positions, 1):
        encoder_start = len(out)
        xy = tuple(float(v) / 1000.0 for v in point)
        body = _solid_box(f"RK_ENCODER_BODY_{index}", BODY_X_M, BODY_Y_M,
                          BODY_BOTTOM_Z_M, MOUNT_Z_M, xy)
        body["source"] = SOURCE
        body["source_sha256"] = SOURCE_SHA256
        body["source_family"] = "PEC11R-1xxxF-Nxxxx envelope"
        body["neighbor_body_edge_clearance_mm"] = body_gap
        body["mount_plane_z_m"] = MOUNT_Z_M
        body["required_main_pcb_clearance_m"] = [MAIN_PCB_CLEARANCE_X_M, MAIN_PCB_CLEARANCE_Y_M]
        body["design_status"] = "referenced PEC11R envelope; not vendor CAD"
        out.append(body)

        shaft = _shaft(index, xy)
        out.append(shaft)
        bushing = _ring(f"RK_ENCODER_BUSHING_{index}", _circle(BUSHING_OD_M / 2),
                        _circle(KNOB_ROUND_LEAD_D_M / 2), MOUNT_Z_M, BUSHING_TOP_Z_M, xy)
        bushing["thread_envelope"] = "M7 x 0.75 analytical envelope; helical thread not modeled"
        out.append(bushing)

        carrier = _ring(f"RK_ENCODER_CARRIER_{index}", _rect_outline(CARRIER_X_M, CARRIER_Y_M),
                        _circle(CARRIER_HOLE_D_M / 2), CARRIER_LOW_Z_M, CARRIER_HIGH_Z_M, xy)
        riser_centers = [(-RISER_X_M, -RISER_Y_M), (RISER_X_M, -RISER_Y_M),
                         (-RISER_X_M, RISER_Y_M), (RISER_X_M, RISER_Y_M)]
        for k, (dx, dy) in enumerate(riser_centers):
            cutter = _prism(f"TMP_ENCODER_CARRIER_HOLE_{index}_{k}",
                            _circle(CARRIER_FASTENER_CLEARANCE_D_M / 2, 64),
                            CARRIER_LOW_Z_M - 0.001, CARRIER_HIGH_Z_M + 0.001,
                            (xy[0] + dx, xy[1] + dy))
            mechanics.operation(carrier, cutter)
        carrier["component_role"] = "custom 6061-T6 encoder carrier plate"
        carrier["material_design_choice"] = "6061-T6 machined carrier, strength not qualified"
        carrier["plate_clearance_required_m"] = PLATE_CLEARANCE_D_M
        carrier["knob_bottom_clearance_m"] = KNOB_BOTTOM_Z_M - CARRIER_HIGH_Z_M
        carrier["m1_6_clearance_diameter_m"] = CARRIER_FASTENER_CLEARANCE_D_M
        carrier["edge_ligament_x_m"] = CARRIER_X_M / 2 - RISER_X_M - CARRIER_FASTENER_CLEARANCE_D_M / 2
        out.append(carrier)

        washer = _ring(f"RK_ENCODER_WASHER_{index}", _circle(WASHER_OD_M / 2),
                       _circle(WASHER_ID_M / 2), WASHER_LOW_Z_M, WASHER_HIGH_Z_M, xy)
        washer["source_hardware"] = "PEC11R supplied washer envelope; 7.2 mm ID is local clearance"
        out.append(washer)
        nut = _ring(f"RK_ENCODER_NUT_{index}", _hex_outline(NUT_AF_M),
                    _circle(WASHER_ID_M / 2), NUT_LOW_Z_M, NUT_HIGH_Z_M, xy)
        nut["source_hardware"] = "PEC11R supplied 10 AF x 2 mm nut; thread represented as clearance"
        nut["bushing_projection_above_nut_m"] = BUSHING_TOP_Z_M - NUT_HIGH_Z_M
        out.append(nut)

        for k, (dx, dy) in enumerate(riser_centers):
            riser = _prism(f"RK_ENCODER_RISER_{index}_{k}", _circle(RISER_RADIUS_M, 64),
                            RISER_LOW_Z_M, CARRIER_LOW_Z_M, (xy[0] + dx, xy[1] + dy))
            tap = _prism(f"TMP_ENCODER_RISER_TAP_{index}_{k}",
                         _circle(RISER_TAP_BORE_D_M / 2, 64),
                         RISER_TAP_LOW_Z_M, CARRIER_LOW_Z_M + 0.001,
                         (xy[0] + dx, xy[1] + dy))
            mechanics.operation(riser, tap)
            riser["component_role"] = "custom bonded brass standoff prototype for encoder carrier"
            riser["attachment_method"] = (
                "bonded brass standoff prototype; integration adds 0.08 mm epoxy bondline "
                "and lifts lower post datum without changing carrier top Z"
            )
            riser["tap_bore_diameter_m"] = RISER_TAP_BORE_D_M
            riser["tap_zone_z_m"] = [RISER_TAP_LOW_Z_M, CARRIER_LOW_Z_M]
            out.append(riser)
            screw = _carrier_screw(f"RK_ENCODER_CARRIER_SCREW_{index}_{k}",
                                   (xy[0] + dx, xy[1] + dy))
            screw["attachment_role"] = "top-access carrier screw into analytical M1.6 riser tap zone"
            out.append(screw)

        # Side-facing terminal row proxy: centers use the 5 mm A-to-B span from the drawing.
        # Cross-section and row offset remain explicit local interpretation until a PCB drawing is frozen.
        pin_y0 = xy[1] - BODY_Y_M / 2
        pin_y1 = xy[1] - 0.0080
        for label, dx in zip(("A", "C", "B"), (-0.0025, 0.0, 0.0025)):
            pin = _solid_box(f"RK_ENCODER_PIN_{index}_{label}", 0.0008,
                             abs(pin_y1 - pin_y0), 0.0060, 0.0065,
                             (xy[0] + dx, (pin_y0 + pin_y1) / 2))
            pin["local_center_x_m"] = dx
            pin["pin_geometry_status"] = "side-terminal proxy; 5 mm A-B span sourced, section/row height interpreted"
            out.append(pin)

        for side, sign in (("L", -1.0), ("R", 1.0)):
            ear = _solid_box(f"RK_ENCODER_EAR_{index}_{side}", 0.0020, 0.0021,
                             0.0060, 0.0068, (xy[0] + sign * (BODY_X_M / 2 + 0.0010), xy[1]))
            ear["geometry_status"] = "two-place mounting-ear proxy from PEC11R drawing envelope"
            out.append(ear)

        board_y = xy[1] + DAUGHTERBOARD_CENTER_Y_M
        board = _solid_box(f"RK_ENCODER_DAUGHTERBOARD_{index}", 0.0140, 0.0010,
                           0.0035, 0.0100, (xy[0], board_y))
        for label, dx in zip(("A", "C", "B"), (-0.0025, 0.0, 0.0025)):
            cutter = _axis_y_cylinder(f"TMP_ENCODER_BOARD_HOLE_{index}_{label}",
                                      DAUGHTERBOARD_HOLE_D_M / 2, -0.001, 0.001,
                                      (dx, 0.00625), (xy[0], board_y))
            mechanics.operation(board, cutter)
        board["role"] = "mechanical daughterboard with contact holes; no copper/netlist/KiCad claim"
        board["pin_pattern_span_mm"] = [5.0, 3.0]
        board["contact_hole_diameter_m"] = DAUGHTERBOARD_HOLE_D_M
        out.append(board)

        for label, dx in zip(("A", "C", "B"), (-0.0025, 0.0, 0.0025)):
            pad = _axis_y_ring(f"RK_ENCODER_PAD_{index}_{label}",
                               DAUGHTERBOARD_PAD_OD_M / 2, DAUGHTERBOARD_HOLE_D_M / 2,
                               0.00045, 0.00060, (dx, 0.00625), (xy[0], board_y))
            pad["role"] = "solder-pad mechanical envelope; electrical copper stack unqualified"
            out.append(pad)

        for side, sign in (("L", -1.0), ("R", 1.0)):
            tab = _solid_box(f"RK_ENCODER_BOARD_SUPPORT_{index}_{side}", 0.0020, 0.0014,
                             RISER_LOW_Z_M, 0.0035, (xy[0] + sign * 0.0050, board_y))
            tab["attachment_method"] = (
                "bonded chassis support tab prototype; integration adds 0.08 mm epoxy bondline"
            )
            tab["board_contact_z_m"] = 0.0035
            out.append(tab)

        for obj in out[encoder_start:]:
            obj["encoder_index"] = index
            obj["knob_counterbore_diameter_m"] = KNOB_COUNTERBORE_D_M
            obj["knob_receiver_flat_y_m"] = KNOB_D_FLAT_Y_M
            obj["knob_receiver_z_m"] = [KNOB_D_START_Z_M, KNOB_RECEIVER_TOP_Z_M]
            obj["knob_slot_floor_z_m"] = KNOB_SLOT_FLOOR_Z_M
    return out

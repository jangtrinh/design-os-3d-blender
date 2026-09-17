"""Native keyboard control constructors for the reference-keyboard build.

Units are metres. Each constructor returns one linked mesh object whose local
origin is bottom-centre (z == 0). No materials, text, assets or modifiers are
created. Unsourced mechanical interfaces are marked NOT_QUALIFIED.
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


KEYCAP_WALL_M = 0.0012
KEYCAP_DISH_M = 0.0004
KEYCAP_SKIRT_DELTA_M = 0.0022
KEYCAP_RING_SEGMENTS = 72
KEYCAP_VISIBLE_SKIRT_BOTTOM_M = 0.0045
KEYCAP_BOSS_DIAMETER_M = 0.0064
KEYCAP_RECEIVER_SPAN_M = 0.00412
KEYCAP_RECEIVER_HORIZONTAL_ARM_M = 0.00122
KEYCAP_RECEIVER_VERTICAL_ARM_M = 0.00140
KEYCAP_RECEIVER_DEPTH_M = 0.0032
KNOB_SEGMENTS = 96
KNOB_SLOT_WIDTH_M = 0.0018
KNOB_SLOT_DEPTH_M = 0.0012
KNOB_BORE_DIAMETER_M = 0.006
KNOB_BORE_DEPTH_M = 0.008
PEC11R_COUNTERBORE_DIAMETER_M = 0.0126
PEC11R_COUNTERBORE_DEPTH_M = 0.0060
PEC11R_SHAFT_BORE_DIAMETER_M = 0.0062
PEC11R_ROUND_TOP_M = 0.0086
PEC11R_D_FLAT_Y_M = 0.00165
PEC11R_D_TOP_M = 0.0160
PEC11R_SLOT_DEPTH_M = 0.0008


def _positive(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite number")
    return value


def _rounded_rect(width, depth, radius, corner_segments=10):
    hx, hy = width * 0.5, depth * 0.5
    radius = min(_positive(radius, "radius"), hx * 0.95, hy * 0.95)
    corners = (
        (hx - radius, hy - radius, 0.0),
        (-hx + radius, hy - radius, math.pi * 0.5),
        (-hx + radius, -hy + radius, math.pi),
        (hx - radius, -hy + radius, math.pi * 1.5),
    )
    points = []
    for cx, cy, start in corners:
        for i in range(corner_segments + 1):
            angle = start + math.pi * 0.5 * i / corner_segments
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _keycap_outline(width, depth, radius):
    """72-point rounded rectangle with explicit datums on all four straight sides."""
    corner_segments = 14
    base = _rounded_rect(width, depth, radius, corner_segments=corner_segments)
    group = corner_segments + 1
    out = []
    for q in range(4):
        start = q * group
        out.extend(base[start:start + group])
        a = base[start + group - 1]
        b = base[((q + 1) % 4) * group]
        for t in (0.25, 0.5, 0.75):
            out.append((a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t))
    return out


def _radial_points(points, radius):
    out = []
    for x, y in points:
        length = math.hypot(x, y)
        if length <= 1e-12:
            raise ValueError("radial source point must not be at the origin")
        out.append((radius * x / length, radius * y / length))
    return out


def _cross_outline(span, horizontal_arm, vertical_arm, start_angle):
    """Exact 12-corner concave cross boundary.

    The receiver is polygonal by design.  Subdividing its straight edges creates
    collinear vertices that a hole tessellator can turn into zero-area triangles,
    so keep only the dimensional corners here.
    """
    half_span = span * 0.5
    half_h = horizontal_arm * 0.5
    half_v = vertical_arm * 0.5
    corners = [
        (half_span, half_h),
        (half_v, half_h),
        (half_v, half_span),
        (-half_v, half_span),
        (-half_v, half_h),
        (-half_span, half_h),
        (-half_span, -half_h),
        (-half_v, -half_h),
        (-half_v, -half_span),
        (half_v, -half_span),
        (half_v, -half_h),
        (half_span, -half_h),
    ]
    def angle_error(point):
        angle = math.atan2(point[1], point[0])
        return abs(math.atan2(math.sin(angle - start_angle), math.cos(angle - start_angle)))

    start = min(range(len(corners)), key=lambda i: angle_error(corners[i]))
    return corners[start:] + corners[:start]


def _append_ring(verts, points, z):
    ring = []
    for x, y in points:
        ring.append(len(verts))
        verts.append((x, y, z))
    return ring


def _join_rings(faces, ring_a, ring_b):
    if len(ring_a) != len(ring_b):
        raise ValueError("ring vertex counts must match")
    for i in range(len(ring_a)):
        j = (i + 1) % len(ring_a)
        faces.append((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))


def _fan(faces, ring, center_index):
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        faces.append((ring[i], ring[j], center_index))


def _planar_annulus(faces, verts, outer_ring, inner_ring):
    """Triangulate a coplanar outer loop with one concave inner hole."""
    if not outer_ring or not inner_ring:
        raise ValueError("annulus loops must be non-empty")
    z0 = verts[outer_ring[0]][2]
    if any(abs(verts[i][2] - z0) > 1e-12 for i in outer_ring + inner_ring):
        raise ValueError("annulus loops must be coplanar")
    outer = [Vector((verts[i][0], verts[i][1], 0.0)) for i in outer_ring]
    inner_indices = list(reversed(inner_ring))
    inner = [Vector((verts[i][0], verts[i][1], 0.0)) for i in inner_indices]
    mapping = list(outer_ring) + inner_indices
    triangles = tessellate_polygon([outer, inner])
    if not triangles:
        raise RuntimeError("failed to tessellate receiver annulus")
    faces.extend(tuple(mapping[i] for i in tri) for tri in triangles)


def _assert_closed_positive(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bad_edges = [edge.index for edge in bm.edges if not edge.is_manifold]
    bad_winding = [edge.index for edge in bm.edges if edge.is_manifold and not edge.is_contiguous]
    loose_verts = [vert.index for vert in bm.verts if not vert.link_edges]
    zero_faces = [face.index for face in bm.faces if face.calc_area() <= 1e-14]
    volume = bm.calc_volume(signed=True)
    bm.free()
    if bad_edges or bad_winding or loose_verts or zero_faces or volume <= 0.0:
        raise RuntimeError(
            f"{obj.name}: invalid solid edges={len(bad_edges)} winding={len(bad_winding)} "
            f"loose_verts={len(loose_verts)} zero_faces={len(zero_faces)} volume={volume}"
        )


def _make_object(name, verts, faces):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    mesh_name = f"{name}_Mesh"
    if bpy.data.objects.get(name) is not None:
        raise ValueError(f"object name already exists: {name}")
    if bpy.data.meshes.get(mesh_name) is not None:
        raise ValueError(f"mesh name already exists: {mesh_name}")
    # Direct constructors occasionally need geometric helper points that do not
    # survive into the final face set. Compact before creating the Blender mesh so
    # no loose vertices enter the linked production object.
    used = sorted({index for face in faces for index in face})
    if len(used) != len(verts):
        remap = {old: new for new, old in enumerate(used)}
        verts = [verts[index] for index in used]
        faces = [tuple(remap[index] for index in face) for face in faces]
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    if mesh.validate(verbose=True):
        bpy.data.meshes.remove(mesh)
        raise ValueError(f"{name}: generated invalid mesh data")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    _assert_closed_positive(obj)
    return obj


def keycap(
    name,
    width_m=0.014,
    depth_m=0.014,
    height_m=0.0095,
    unit=1,
    visible_skirt_bottom_m=KEYCAP_VISIBLE_SKIRT_BOTTOM_M,
    boss_diameter_m=KEYCAP_BOSS_DIAMETER_M,
    receiver_span_m=KEYCAP_RECEIVER_SPAN_M,
    receiver_horizontal_arm_m=KEYCAP_RECEIVER_HORIZONTAL_ARM_M,
    receiver_vertical_arm_m=KEYCAP_RECEIVER_VERTICAL_ARM_M,
    receiver_depth_m=KEYCAP_RECEIVER_DEPTH_M,
):
    """Low-profile tapered cap with an integral source-guided custom cross receiver.

    The receiver uses Gateron KS-33 Rev-2 male-cross dimensions only as source
    guidance for digital clearance.  The surrounding boss/dust-ring relationship
    remains CK-001 custom geometry and is not a vendor-compatibility claim.
    """
    width_m = _positive(width_m, "width_m")
    depth_m = _positive(depth_m, "depth_m")
    height_m = _positive(height_m, "height_m")
    unit = _positive(unit, "unit")
    visible_skirt_bottom_m = _positive(visible_skirt_bottom_m, "visible_skirt_bottom_m")
    boss_diameter_m = _positive(boss_diameter_m, "boss_diameter_m")
    receiver_span_m = _positive(receiver_span_m, "receiver_span_m")
    receiver_horizontal_arm_m = _positive(receiver_horizontal_arm_m, "receiver_horizontal_arm_m")
    receiver_vertical_arm_m = _positive(receiver_vertical_arm_m, "receiver_vertical_arm_m")
    receiver_depth_m = _positive(receiver_depth_m, "receiver_depth_m")
    top_w, top_d = width_m * unit, depth_m
    if min(top_w, top_d) <= 2.0 * KEYCAP_WALL_M + 0.002:
        raise ValueError("keycap footprint is too small for the declared wall and cavity")
    if height_m <= KEYCAP_WALL_M + KEYCAP_DISH_M + 0.002:
        raise ValueError("keycap height is too small for the declared wall and dish")

    bottom_w, bottom_d = top_w + KEYCAP_SKIRT_DELTA_M, top_d + KEYCAP_SKIRT_DELTA_M
    top_radius = min(0.0030, top_d * 0.24, top_w * 0.24)
    bottom_radius = min(0.0022, bottom_d * 0.20, bottom_w * 0.20)
    cavity_z = height_m - KEYCAP_DISH_M - KEYCAP_WALL_M
    if visible_skirt_bottom_m >= cavity_z - 0.001:
        raise ValueError("visible skirt leaves insufficient inner wall below the roof")
    if receiver_depth_m >= cavity_z - 0.001:
        raise ValueError("receiver depth leaves insufficient material below the roof")
    if max(receiver_horizontal_arm_m, receiver_vertical_arm_m) >= receiver_span_m:
        raise ValueError("receiver arm widths must be smaller than receiver span")
    boss_radius = boss_diameter_m * 0.5
    receiver_tip_wall = boss_radius - receiver_span_m * 0.5
    if receiver_tip_wall < 0.001 - 1e-9:
        raise ValueError("boss leaves less than 1.0 mm material beyond receiver tips")

    verts, faces = [], []
    outer_spec = (
        (visible_skirt_bottom_m, bottom_w, bottom_d, bottom_radius),
        (visible_skirt_bottom_m + 0.00045, bottom_w - 0.00010, bottom_d - 0.00010, bottom_radius + 0.00015),
        (height_m - 0.0009, top_w + 0.00050, top_d + 0.00050, top_radius - 0.00015),
        (height_m, top_w, top_d, top_radius),
    )
    outer_rings = [
        _append_ring(verts, _keycap_outline(width, depth, radius), z)
        for z, width, depth, radius in outer_spec
    ]
    for lower, upper in zip(outer_rings, outer_rings[1:]):
        _join_rings(faces, lower, upper)

    previous = outer_rings[-1]
    for scale in (0.75, 0.50, 0.25):
        z = height_m - KEYCAP_DISH_M * (1.0 - scale * scale)
        ring = _append_ring(
            verts,
            _keycap_outline(
                top_w * scale,
                top_d * scale,
                max(top_radius * scale, 0.00035),
            ),
            z,
        )
        _join_rings(faces, previous, ring)
        previous = ring
    top_center = len(verts)
    verts.append((0.0, 0.0, height_m - KEYCAP_DISH_M))
    _fan(faces, previous, top_center)

    inner_bottom_w, inner_bottom_d = bottom_w - 2 * KEYCAP_WALL_M, bottom_d - 2 * KEYCAP_WALL_M
    inner_top_w, inner_top_d = top_w - 2 * KEYCAP_WALL_M, top_d - 2 * KEYCAP_WALL_M
    inner_bottom_r = max(bottom_radius - KEYCAP_WALL_M, 0.00045)
    inner_top_r = max(top_radius - KEYCAP_WALL_M, 0.00045)
    inner_open_points = _keycap_outline(inner_bottom_w, inner_bottom_d, inner_bottom_r)
    inner_mid_points = _keycap_outline(
        (inner_bottom_w + inner_top_w) * 0.5,
        (inner_bottom_d + inner_top_d) * 0.5,
        (inner_bottom_r + inner_top_r) * 0.5,
    )
    inner_ceiling_points = _keycap_outline(inner_top_w, inner_top_d, inner_top_r)
    inner_open = _append_ring(verts, inner_open_points, visible_skirt_bottom_m)
    inner_mid = _append_ring(
        verts,
        inner_mid_points,
        (visible_skirt_bottom_m + cavity_z) * 0.5,
    )
    inner_ceiling = _append_ring(verts, inner_ceiling_points, cavity_z)
    _join_rings(faces, outer_rings[0], inner_open)
    _join_rings(faces, inner_open, inner_mid)
    _join_rings(faces, inner_mid, inner_ceiling)

    # One integral body: the roof transitions directly from the cavity wall to
    # the boss; the boss bottom closes around the blind cross receiver opening.
    # The roof-aligned boss ring keeps the existing non-crossing one-to-one roof
    # bridge.  Below a short hidden transition, switch to a uniform 72-segment
    # circle: projecting wide-key roof vertices directly down the full boss
    # clusters angles near the long sides and reduces the real receiver wall to
    # ~0.85 mm despite the nominal OD6.4 diameter.
    boss_roof_points = _radial_points(inner_ceiling_points, boss_radius)
    boss_points = [
        (boss_radius * math.cos(i * math.tau / KEYCAP_RING_SEGMENTS),
         boss_radius * math.sin(i * math.tau / KEYCAP_RING_SEGMENTS))
        for i in range(KEYCAP_RING_SEGMENTS)
    ]
    receiver_points = _cross_outline(
        receiver_span_m,
        receiver_horizontal_arm_m,
        receiver_vertical_arm_m,
        math.atan2(boss_points[0][1], boss_points[0][0]),
    )
    boss_top = _append_ring(verts, boss_roof_points, cavity_z)
    boss_uniform = _append_ring(verts, boss_points, cavity_z - 0.0005)
    boss_bottom = _append_ring(verts, boss_points, 0.0)
    receiver_bottom = _append_ring(verts, receiver_points, 0.0)
    receiver_top = _append_ring(verts, receiver_points, receiver_depth_m)
    _join_rings(faces, inner_ceiling, boss_top)
    _join_rings(faces, boss_top, boss_uniform)
    _join_rings(faces, boss_uniform, boss_bottom)
    _planar_annulus(faces, verts, boss_bottom, receiver_bottom)
    _join_rings(faces, receiver_bottom, receiver_top)
    receiver_center = len(verts)
    verts.append((0.0, 0.0, receiver_depth_m))
    _fan(faces, receiver_top, receiver_center)

    obj = _make_object(name, verts, faces)
    obj["control_kind"] = "keycap"
    obj["nominal_top_width_m"] = top_w
    obj["nominal_top_depth_m"] = top_d
    obj["lower_skirt_width_m"] = bottom_w
    obj["lower_skirt_depth_m"] = bottom_d
    obj["nominal_min_wall_m"] = KEYCAP_WALL_M
    obj["dish_depth_m"] = KEYCAP_DISH_M
    obj["visible_skirt_bottom_m"] = visible_skirt_bottom_m
    obj["boss_diameter_m"] = boss_diameter_m
    obj["receiver_span_m"] = receiver_span_m
    obj["receiver_horizontal_arm_m"] = receiver_horizontal_arm_m
    obj["receiver_vertical_arm_m"] = receiver_vertical_arm_m
    obj["receiver_depth_m"] = receiver_depth_m
    obj["receiver_tip_wall_m"] = receiver_tip_wall
    obj["functional_interface"] = "NOT_QUALIFIED"
    obj["stem_receiver"] = (
        "source-guided CK-001 custom cross receiver; Gateron KS-33 Rev-2 male cross "
        "informed nominal clearance; dust-ring fit and physical retention not qualified"
    )
    return obj


def _knob_angles(radius, slot_half):
    """96-segment circle with exact slot/cylinder intersection boundaries."""
    if slot_half >= radius:
        raise ValueError("slot half-width must be smaller than knob radius")
    a = math.asin(slot_half / radius)
    boundaries = (a, math.pi - a, math.pi + a, math.tau - a, math.tau + a)
    counts = (44, 4, 44, 4)  # material arc, slot mouth, material arc, slot mouth
    angles = []
    for start, end, count in zip(boundaries, boundaries[1:], counts):
        angles.extend(start + (end - start) * i / count for i in range(count))
    if len(angles) != KNOB_SEGMENTS:
        raise AssertionError("knob angular partition must contain 96 vertices")
    return angles


def _circle_ring(verts, radius, z, *, slot_half=None, angles=None):
    angles = angles if angles is not None else _knob_angles(radius, slot_half)
    ring = []
    for angle in angles:
        ring.append(len(verts))
        verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    return ring, angles


def _d_ring(verts, radius, flat_y, z, angles, reuse_ring=None):
    """D-profile ring with a +Y flat, indexed to the supplied circular angles."""
    ring = []
    for i, angle in enumerate(angles):
        x = radius * math.cos(angle)
        circle_y = radius * math.sin(angle)
        y = min(circle_y, flat_y)
        if reuse_ring is not None and abs(y - circle_y) <= 1e-12:
            ring.append(reuse_ring[i])
            continue
        ring.append(len(verts))
        verts.append((x, y, z))
    return ring


def _join_transition(faces, ring_a, ring_b):
    """Bridge coincident planar profiles without emitting degenerate quads."""
    if len(ring_a) != len(ring_b):
        raise ValueError("transition ring vertex counts must match")
    for i in range(len(ring_a)):
        j = (i + 1) % len(ring_a)
        raw = [ring_a[i], ring_a[j], ring_b[j], ring_b[i]]
        face = []
        for index in raw:
            if not face or face[-1] != index:
                face.append(index)
        if len(face) > 1 and face[0] == face[-1]:
            face.pop()
        if len(set(face)) >= 3:
            faces.append(tuple(face))


def _pec11r_knob(name, radius_m, height_m):
    """Source-derived PEC11R clearance stack inside the owner OD16 x 18 envelope."""
    slot_half = KNOB_SLOT_WIDTH_M * 0.5
    slot_depth = PEC11R_SLOT_DEPTH_M
    slot_floor = height_m - slot_depth
    counter_r = PEC11R_COUNTERBORE_DIAMETER_M * 0.5
    shaft_r = PEC11R_SHAFT_BORE_DIAMETER_M * 0.5
    if radius_m <= counter_r + 0.0011:
        raise ValueError("PEC11R profile leaves less than 1.1 mm body wall")
    if not (0 < PEC11R_COUNTERBORE_DEPTH_M < PEC11R_ROUND_TOP_M < PEC11R_D_TOP_M < slot_floor):
        raise ValueError("invalid PEC11R staged-bore Z contract")
    if PEC11R_D_FLAT_Y_M >= shaft_r:
        raise ValueError("PEC11R D-flat must lie inside the shaft radius")

    bottom_bevel = min(0.00035, radius_m * 0.08)
    top_bevel = min(0.00045, radius_m * 0.09)
    shared_angles = _knob_angles(radius_m, slot_half)
    verts, faces = [], []

    bottom_outer, _ = _circle_ring(verts, radius_m - bottom_bevel, 0.0, angles=shared_angles)
    bevel_ring, _ = _circle_ring(verts, radius_m, bottom_bevel, angles=shared_angles)
    slot_base, _ = _circle_ring(verts, radius_m, slot_floor, angles=shared_angles)
    _join_rings(faces, bottom_outer, bevel_ring)
    _join_rings(faces, bevel_ring, slot_base)

    counter_bottom, _ = _circle_ring(verts, counter_r, 0.0, angles=shared_angles)
    counter_top, _ = _circle_ring(
        verts, counter_r, PEC11R_COUNTERBORE_DEPTH_M, angles=shared_angles
    )
    round_bottom, _ = _circle_ring(
        verts, shaft_r, PEC11R_COUNTERBORE_DEPTH_M, angles=shared_angles
    )
    round_top, _ = _circle_ring(verts, shaft_r, PEC11R_ROUND_TOP_M, angles=shared_angles)
    d_bottom = _d_ring(
        verts,
        shaft_r,
        PEC11R_D_FLAT_Y_M,
        PEC11R_ROUND_TOP_M,
        shared_angles,
        reuse_ring=round_top,
    )
    d_top = _d_ring(verts, shaft_r, PEC11R_D_FLAT_Y_M, PEC11R_D_TOP_M, shared_angles)
    _join_rings(faces, bottom_outer, counter_bottom)
    _join_rings(faces, counter_bottom, counter_top)
    _join_rings(faces, counter_top, round_bottom)
    _join_rings(faces, round_bottom, round_top)
    _join_transition(faces, round_top, d_bottom)
    _join_rings(faces, d_bottom, d_top)
    bore_center = len(verts)
    verts.append((0.0, 0.0, PEC11R_D_TOP_M))
    _fan(faces, d_top, bore_center)

    top_rings = [slot_base]
    for z, radius in ((height_m - top_bevel, radius_m), (height_m, radius_m - top_bevel)):
        ring, _ = _circle_ring(verts, radius, z, slot_half=slot_half)
        top_rings.append(ring)
    material_ranges = (range(0, 44), range(48, 92))
    for lower, upper in zip(top_rings, top_rings[1:]):
        for indices in material_ranges:
            for i in indices:
                faces.append((lower[i], lower[i + 1], upper[i + 1], upper[i]))
        faces.append((lower[0], lower[44], upper[44], upper[0]))
        faces.append((lower[48], lower[92], upper[92], upper[48]))
    floor_ring = top_rings[0]
    floor_boundary = [floor_ring[0], floor_ring[44]]
    floor_boundary += [floor_ring[i] for i in range(45, 49)]
    floor_boundary += [floor_ring[92]]
    floor_boundary += [floor_ring[i] for i in range(93, 96)]
    floor_center = len(verts)
    verts.append((0.0, 0.0, slot_floor))
    _fan(faces, floor_boundary, floor_center)
    top_ring = top_rings[-1]
    for boundary in ([top_ring[i] for i in range(0, 45)], [top_ring[i] for i in range(48, 93)]):
        cx = sum(verts[i][0] for i in boundary) / len(boundary)
        cy = sum(verts[i][1] for i in boundary) / len(boundary)
        center = len(verts)
        verts.append((cx, cy, height_m))
        _fan(faces, boundary, center)

    obj = _make_object(name, verts, faces)
    obj["control_kind"] = "knob"
    obj["hardware_profile"] = "PEC11R_SOURCE_DERIVED_CLEARANCE"
    obj["nominal_radius_m"] = radius_m
    obj["nominal_height_m"] = height_m
    obj["slot_width_m"] = KNOB_SLOT_WIDTH_M
    obj["slot_depth_m"] = slot_depth
    obj["counterbore_diameter_m"] = PEC11R_COUNTERBORE_DIAMETER_M
    obj["counterbore_depth_m"] = PEC11R_COUNTERBORE_DEPTH_M
    obj["shaft_bore_diameter_m"] = PEC11R_SHAFT_BORE_DIAMETER_M
    obj["round_bore_top_m"] = PEC11R_ROUND_TOP_M
    obj["d_flat_y_m"] = PEC11R_D_FLAT_Y_M
    obj["d_bore_top_m"] = PEC11R_D_TOP_M
    obj["shaft_interface"] = "NOT_QUALIFIED_PHYSICAL_FIT"
    obj["d_flat"] = "+Y flat; source-derived PEC11R clearance geometry"
    return obj


def knob(name, radius_m=0.008, height_m=0.018,
         mount_neck_m=0.0031, neck_radius_m=0.0042, hardware_profile=None):
    """96-segment knob with top slot, blind bore, and optional mounting neck.

    The default uses the build's local 8.4 mm OD x 3.1 mm stack-adaptation neck
    below the 16 mm barrel. Pass ``mount_neck_m=0`` for the earlier full-diameter
    base form. This neck is not a sourced owner-catalog shaft interface.
    """
    radius_m = _positive(radius_m, "radius_m")
    height_m = _positive(height_m, "height_m")
    if hardware_profile is not None:
        if hardware_profile != "PEC11R":
            raise ValueError(f"unsupported hardware_profile: {hardware_profile}")
        return _pec11r_knob(name, radius_m, height_m)
    mount_neck_m = float(mount_neck_m)
    if not math.isfinite(mount_neck_m) or mount_neck_m < 0.0:
        raise ValueError("mount_neck_m must be a non-negative finite number")
    neck_radius_m = _positive(neck_radius_m, "neck_radius_m")
    slot_half = KNOB_SLOT_WIDTH_M * 0.5
    bore_r = KNOB_BORE_DIAMETER_M * 0.5
    if radius_m <= max(slot_half + 0.001, bore_r + 0.0012):
        raise ValueError("knob radius is too small for the fixed slot/bore geometry")
    if height_m <= KNOB_BORE_DEPTH_M + KNOB_SLOT_DEPTH_M + 0.002:
        raise ValueError("knob height is too small for separated bore and slot cavities")

    bottom_bevel = min(0.00035, radius_m * 0.08)
    top_bevel = min(0.00045, radius_m * 0.09)
    slot_floor = height_m - KNOB_SLOT_DEPTH_M
    if mount_neck_m > 0.0:
        if neck_radius_m < bore_r + 0.0012 - 1e-9:
            raise ValueError("neck_radius_m leaves less than the declared 1.2 mm radial wall")
        if neck_radius_m >= radius_m:
            raise ValueError("neck_radius_m must be smaller than the barrel radius")
        if mount_neck_m >= slot_floor - 0.001:
            raise ValueError("mount_neck_m leaves insufficient barrel height")

    verts, faces = [], []
    shared_angles = _knob_angles(radius_m, slot_half)
    if mount_neck_m > 0.0:
        neck_bottom, _ = _circle_ring(verts, neck_radius_m, 0.0, angles=shared_angles)
        neck_top, _ = _circle_ring(verts, neck_radius_m, mount_neck_m, angles=shared_angles)
        barrel_seat, _ = _circle_ring(verts, radius_m, mount_neck_m, angles=shared_angles)
        slot_base, _ = _circle_ring(verts, radius_m, slot_floor, angles=shared_angles)
        _join_rings(faces, neck_bottom, neck_top)
        _join_rings(faces, neck_top, barrel_seat)
        _join_rings(faces, barrel_seat, slot_base)
        bottom_outer = neck_bottom
    else:
        bottom_outer, _ = _circle_ring(
            verts, radius_m - bottom_bevel, 0.0, angles=shared_angles
        )
        bevel_ring, _ = _circle_ring(verts, radius_m, bottom_bevel, angles=shared_angles)
        slot_base, _ = _circle_ring(verts, radius_m, slot_floor, angles=shared_angles)
        _join_rings(faces, bottom_outer, bevel_ring)
        _join_rings(faces, bevel_ring, slot_base)

    inner_bottom, _ = _circle_ring(verts, bore_r, 0.0, angles=shared_angles)
    inner_ceiling, _ = _circle_ring(verts, bore_r, KNOB_BORE_DEPTH_M, angles=shared_angles)
    _join_rings(faces, bottom_outer, inner_bottom)
    _join_rings(faces, inner_bottom, inner_ceiling)
    bore_center = len(verts)
    verts.append((0.0, 0.0, KNOB_BORE_DEPTH_M))
    _fan(faces, inner_ceiling, bore_center)

    top_specs = (
        (slot_floor, radius_m),
        (height_m - top_bevel, radius_m),
        (height_m, radius_m - top_bevel),
    )
    top_rings = [slot_base]
    for z, radius in top_specs[1:]:
        ring, _ = _circle_ring(verts, radius, z, slot_half=slot_half)
        top_rings.append(ring)

    material_ranges = (range(0, 44), range(48, 92))
    for lower, upper in zip(top_rings, top_rings[1:]):
        for indices in material_ranges:
            for i in indices:
                faces.append((lower[i], lower[i + 1], upper[i + 1], upper[i]))
        faces.append((lower[0], lower[44], upper[44], upper[0]))
        faces.append((lower[48], lower[92], upper[92], upper[48]))

    floor_ring = top_rings[0]
    floor_boundary = [floor_ring[0], floor_ring[44]]
    floor_boundary += [floor_ring[i] for i in range(45, 49)]
    floor_boundary += [floor_ring[92]]
    floor_boundary += [floor_ring[i] for i in range(93, 96)]
    floor_center = len(verts)
    verts.append((0.0, 0.0, slot_floor))
    _fan(faces, floor_boundary, floor_center)

    top_ring = top_rings[-1]
    for boundary in (
        [top_ring[i] for i in range(0, 45)],
        [top_ring[i] for i in range(48, 93)],
    ):
        cx = sum(verts[i][0] for i in boundary) / len(boundary)
        cy = sum(verts[i][1] for i in boundary) / len(boundary)
        center = len(verts)
        verts.append((cx, cy, height_m))
        _fan(faces, boundary, center)

    obj = _make_object(name, verts, faces)
    obj["control_kind"] = "knob"
    obj["nominal_radius_m"] = radius_m
    obj["nominal_height_m"] = height_m
    obj["slot_width_m"] = KNOB_SLOT_WIDTH_M
    obj["slot_depth_m"] = KNOB_SLOT_DEPTH_M
    obj["bore_diameter_m"] = KNOB_BORE_DIAMETER_M
    obj["bore_depth_m"] = KNOB_BORE_DEPTH_M
    obj["mount_neck_m"] = mount_neck_m
    obj["mount_neck_radius_m"] = neck_radius_m if mount_neck_m > 0.0 else 0.0
    obj["barrel_seat_z_m"] = mount_neck_m
    obj["neck_nominal_wall_m"] = (neck_radius_m - bore_r) if mount_neck_m > 0.0 else 0.0
    obj["shaft_interface"] = "NOT_QUALIFIED"
    obj["d_flat"] = "omitted; no sourced shaft-flat dimension bound"
    return obj


def encoder_knob(name, radius_m=0.008, height_m=0.018):
    """CK-001 encoder knob using the explicit PEC11R clearance profile."""
    return knob(name, radius_m=radius_m, height_m=height_m, hardware_profile="PEC11R")

"""Native keyboard control constructors for the reference-keyboard build.

Units are metres. Each constructor returns one linked mesh object whose local
origin is bottom-centre (z == 0). No materials, text, assets or modifiers are
created. Unsourced mechanical interfaces are marked NOT_QUALIFIED.
"""
from __future__ import annotations

import math

import bmesh
import bpy


KEYCAP_WALL_M = 0.0012
KEYCAP_DISH_M = 0.0004
KEYCAP_SKIRT_DELTA_M = 0.0022
KNOB_SEGMENTS = 96
KNOB_SLOT_WIDTH_M = 0.0018
KNOB_SLOT_DEPTH_M = 0.0012
KNOB_BORE_DIAMETER_M = 0.006
KNOB_BORE_DEPTH_M = 0.008


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


def keycap(name, width_m=0.014, depth_m=0.014, height_m=0.0095, unit=1):
    """Tapered rounded keycap shell with a 0.4 mm shallow dished top."""
    width_m = _positive(width_m, "width_m")
    depth_m = _positive(depth_m, "depth_m")
    height_m = _positive(height_m, "height_m")
    unit = _positive(unit, "unit")
    top_w, top_d = width_m * unit, depth_m
    if min(top_w, top_d) <= 2.0 * KEYCAP_WALL_M + 0.002:
        raise ValueError("keycap footprint is too small for the declared wall and cavity")
    if height_m <= KEYCAP_WALL_M + KEYCAP_DISH_M + 0.002:
        raise ValueError("keycap height is too small for the declared wall and dish")

    bottom_w, bottom_d = top_w + KEYCAP_SKIRT_DELTA_M, top_d + KEYCAP_SKIRT_DELTA_M
    top_radius = min(0.0030, top_d * 0.24, top_w * 0.24)
    bottom_radius = min(0.0022, bottom_d * 0.20, bottom_w * 0.20)
    verts, faces = [], []
    outer_spec = (
        (0.0, bottom_w, bottom_d, bottom_radius),
        (0.00045, bottom_w - 0.00010, bottom_d - 0.00010, bottom_radius + 0.00015),
        (height_m - 0.0009, top_w + 0.00050, top_d + 0.00050, top_radius - 0.00015),
        (height_m, top_w, top_d, top_radius),
    )
    outer_rings = [
        _append_ring(verts, _rounded_rect(width, depth, radius), z)
        for z, width, depth, radius in outer_spec
    ]
    for lower, upper in zip(outer_rings, outer_rings[1:]):
        _join_rings(faces, lower, upper)

    previous = outer_rings[-1]
    for scale in (0.75, 0.50, 0.25):
        z = height_m - KEYCAP_DISH_M * (1.0 - scale * scale)
        ring = _append_ring(
            verts,
            _rounded_rect(top_w * scale, top_d * scale, max(top_radius * scale, 0.00035)),
            z,
        )
        _join_rings(faces, previous, ring)
        previous = ring
    top_center = len(verts)
    verts.append((0.0, 0.0, height_m - KEYCAP_DISH_M))
    _fan(faces, previous, top_center)

    cavity_z = height_m - KEYCAP_DISH_M - KEYCAP_WALL_M
    inner_bottom_w, inner_bottom_d = bottom_w - 2 * KEYCAP_WALL_M, bottom_d - 2 * KEYCAP_WALL_M
    inner_top_w, inner_top_d = top_w - 2 * KEYCAP_WALL_M, top_d - 2 * KEYCAP_WALL_M
    inner_bottom_r = max(bottom_radius - KEYCAP_WALL_M, 0.00045)
    inner_top_r = max(top_radius - KEYCAP_WALL_M, 0.00045)
    inner_open = _append_ring(verts, _rounded_rect(inner_bottom_w, inner_bottom_d, inner_bottom_r), 0.0)
    inner_mid = _append_ring(
        verts,
        _rounded_rect((inner_bottom_w + inner_top_w) * 0.5,
                      (inner_bottom_d + inner_top_d) * 0.5,
                      (inner_bottom_r + inner_top_r) * 0.5),
        cavity_z * 0.5,
    )
    inner_ceiling = _append_ring(verts, _rounded_rect(inner_top_w, inner_top_d, inner_top_r), cavity_z)
    _join_rings(faces, outer_rings[0], inner_open)
    _join_rings(faces, inner_open, inner_mid)
    _join_rings(faces, inner_mid, inner_ceiling)
    cavity_center = len(verts)
    verts.append((0.0, 0.0, cavity_z))
    _fan(faces, inner_ceiling, cavity_center)

    obj = _make_object(name, verts, faces)
    obj["control_kind"] = "keycap"
    obj["nominal_top_width_m"] = top_w
    obj["nominal_top_depth_m"] = top_d
    obj["lower_skirt_width_m"] = bottom_w
    obj["lower_skirt_depth_m"] = bottom_d
    obj["nominal_min_wall_m"] = KEYCAP_WALL_M
    obj["dish_depth_m"] = KEYCAP_DISH_M
    obj["functional_interface"] = "NOT_QUALIFIED"
    obj["stem_receiver"] = "omitted; no sourced Cherry MX stem dimensions bound"
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


def knob(name, radius_m=0.008, height_m=0.018,
         mount_neck_m=0.0031, neck_radius_m=0.0042):
    """96-segment knob with top slot, blind bore, and optional mounting neck.

    The default uses the build's local 8.4 mm OD x 3.1 mm stack-adaptation neck
    below the 16 mm barrel. Pass ``mount_neck_m=0`` for the earlier full-diameter
    base form. This neck is not a sourced owner-catalog shaft interface.
    """
    radius_m = _positive(radius_m, "radius_m")
    height_m = _positive(height_m, "height_m")
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

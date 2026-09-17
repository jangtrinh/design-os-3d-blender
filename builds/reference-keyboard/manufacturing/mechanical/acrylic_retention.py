"""C03 provisional acrylic compression collars for the CK-001 chassis.

Self-contained so prime can call apply() from a fresh C03 copy without changing C02.
Dimensions are metres; preload, shims, creep and thermal behavior remain physical tests.
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

AXES_M = ((-.136, -.040), (.136, -.040), (-.136, .040), (.136, .040))
OUTER_R_M = .0044
INNER_R_M = .0029
BOTTOM_Z_M = .0120
TOP_Z_M = .0136
SUPPORT_PROBE_R_M = .00435
SEGMENTS = 96


def _bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return ([min(p[i] for p in pts) for i in range(3)],
            [max(p[i] for p in pts) for i in range(3)])


def _annulus(name, xy):
    outer = [(OUTER_R_M * math.cos(i * math.tau / SEGMENTS),
              OUTER_R_M * math.sin(i * math.tau / SEGMENTS)) for i in range(SEGMENTS)]
    inner = [(INNER_R_M * math.cos(i * math.tau / SEGMENTS),
              INNER_R_M * math.sin(i * math.tau / SEGMENTS)) for i in range(SEGMENTS)]
    verts = ([(x, y, BOTTOM_Z_M) for x, y in outer] +
             [(x, y, TOP_Z_M) for x, y in outer] +
             [(x, y, BOTTOM_Z_M) for x, y in inner] +
             [(x, y, TOP_Z_M) for x, y in inner])
    n = SEGMENTS
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend(((i, j, n + j, n + i),
                      (2*n + j, 2*n + i, 3*n + i, 3*n + j),
                      (j, i, 2*n + i, 2*n + j),
                      (n + i, n + j, 3*n + j, 3*n + i)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    assert all(e.is_manifold and e.is_contiguous for e in bm.edges), name
    assert bm.calc_volume(signed=True) > 0, name
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.x, obj.location.y = xy
    return obj


def _support_angles(acrylic, xy):
    good = []
    for deg in range(0, 360, 15):
        angle = math.radians(deg)
        point = Vector((xy[0] + SUPPORT_PROBE_R_M * math.cos(angle),
                        xy[1] + SUPPORT_PROBE_R_M * math.sin(angle), .0135))
        hit, loc, _, _ = acrylic.ray_cast(point, Vector((0, 0, -1)), distance=.005)
        if hit and abs(loc.z - BOTTOM_Z_M) <= 5e-6:
            good.append(deg)
    return good


def _intersection_mm3(a, b):
    copy = a.copy(); copy.data = a.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    mod = copy.modifiers.new("C03_COLLAR_INTERSECTION", "BOOLEAN")
    mod.operation, mod.solver, mod.object = "INTERSECT", "EXACT", b
    graph = bpy.context.evaluated_depsgraph_get()
    result = bpy.data.meshes.new_from_object(copy.evaluated_get(graph), depsgraph=graph)
    bm = bmesh.new(); bm.from_mesh(result)
    volume = abs(bm.calc_volume(signed=True)) * 1e9 if bm.faces else 0.0
    bm.free(); bpy.data.meshes.remove(result)
    data = copy.data; bpy.data.objects.remove(copy, do_unlink=True)
    if not data.users: bpy.data.meshes.remove(data)
    return volume


def apply():
    """Create and return four collars after validating the C02/C03 mating geometry."""
    acrylic = bpy.data.objects["RK_DIFFUSER"]
    plate = bpy.data.objects["RK_MAIN_PLATE"]
    pcb = bpy.data.objects["RK_PCB"]
    assert abs(_bbox(plate)[0][2] - TOP_Z_M) <= 5e-6
    assert (OUTER_R_M - INNER_R_M) >= .0012
    collars = []
    for index, xy in enumerate(AXES_M):
        angles = _support_angles(acrylic, xy)
        assert len(angles) >= 6, (index, angles)
        edge = min(.142 - abs(xy[0]) - OUTER_R_M, .046 - abs(xy[1]) - OUTER_R_M)
        assert edge > 0, (index, edge)
        collar = _annulus(f"RK_ACRYLIC_COLLAR_{index}", xy)
        collar["role"] = "provisional captive acrylic compression collar"
        collar["outer_diameter_mm"] = 8.8
        collar["inner_diameter_mm"] = 5.8
        collar["bottom_z_mm"] = 12.0
        collar["top_z_mm"] = 13.6
        collar["radial_wall_mm"] = 1.5
        collar["support_probe_angles_deg"] = angles
        collar["physical_preload_status"] = "FIRST_ARTICLE_REQUIRED"
        collars.append(collar)
    bpy.context.view_layer.update()

    candidates = [acrylic, plate, pcb]
    candidates += [o for o in bpy.data.objects if o.name.startswith((
        "RK_SPACER_", "RK_SCREW_", "RK_KNOB_", "RK_ENCODER_", "RK_MFG_", "RK_DB_"))]
    max_overlap = 0.0
    for collar in collars:
        clo, chi = _bbox(collar)
        for other in candidates:
            olo, ohi = _bbox(other)
            if any(chi[i] < olo[i] - 1e-7 or ohi[i] < clo[i] - 1e-7 for i in range(3)):
                continue
            max_overlap = max(max_overlap, _intersection_mm3(collar, other))
    assert max_overlap <= 1e-4, max_overlap

    spacer_clearances, knob_clearances = [], []
    spacers = [o for o in bpy.data.objects if o.name.startswith("RK_SPACER_")]
    knobs = [o for o in bpy.data.objects if o.name.startswith("RK_KNOB_")]
    for xy in AXES_M:
        spacer = min(spacers, key=lambda o: math.hypot(o.location.x-xy[0], o.location.y-xy[1]))
        sb = _bbox(spacer); sr = max(sb[1][0]-sb[0][0], sb[1][1]-sb[0][1]) * .5
        spacer_clearances.append(INNER_R_M - sr)
        for knob in knobs:
            kb = _bbox(knob)
            if kb[1][2] < BOTTOM_Z_M or kb[0][2] > TOP_Z_M: continue
            kr = max(kb[1][0]-kb[0][0], kb[1][1]-kb[0][1]) * .5
            knob_clearances.append(math.hypot(knob.location.x-xy[0], knob.location.y-xy[1]) - OUTER_R_M - kr)
    assert min(spacer_clearances) > 0
    assert min(knob_clearances) > 0
    for collar in collars:
        collar["minimum_spacer_radial_clearance_mm"] = min(spacer_clearances) * 1000
        collar["minimum_knob_xy_clearance_mm"] = min(knob_clearances) * 1000
        collar["max_nominal_intersection_mm3"] = max_overlap
    return collars

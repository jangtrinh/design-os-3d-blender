"""Finite numerical fixture for the native reference-keyboard controls."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reference_keyboard_controls", ROOT / "scripts" / "controls.py")
controls = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controls)


def _clean():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _bbox(obj):
    coords = [v.co for v in obj.data.vertices]
    lo = tuple(min(v[i] for v in coords) for i in range(3))
    hi = tuple(max(v[i] for v in coords) for i in range(3))
    return tuple(hi[i] - lo[i] for i in range(3)), lo, hi


def _audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    faces_seen = set()
    shells = 0
    for face in bm.faces:
        if face.index in faces_seen:
            continue
        shells += 1
        stack = [face]
        faces_seen.add(face.index)
        while stack:
            current = stack.pop()
            for edge in current.edges:
                for neighbor in edge.link_faces:
                    if neighbor.index not in faces_seen:
                        faces_seen.add(neighbor.index)
                        stack.append(neighbor)
    result = {
        "nonmanifold": sum(1 for edge in bm.edges if not edge.is_manifold),
        "noncontiguous": sum(1 for edge in bm.edges if edge.is_manifold and not edge.is_contiguous),
        "loose_verts": sum(1 for vert in bm.verts if not vert.link_edges),
        "zero_area": sum(1 for face in bm.faces if face.calc_area() <= 1e-14),
        "shells": shells,
        "volume": bm.calc_volume(signed=True),
    }
    bm.free()
    return result


def _ray_point(obj, origin, direction):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    location, _normal, _index, _distance = tree.ray_cast(Vector(origin), Vector(direction), 1.0)
    value = None if location is None else tuple(float(component) for component in location)
    bm.free()
    return value


def _ray_z(obj, origin, direction):
    point = _ray_point(obj, origin, direction)
    return None if point is None else point[2]


def _assert_solid(obj):
    audit = _audit(obj)
    assert audit["nonmanifold"] == 0, audit
    assert audit["noncontiguous"] == 0, audit
    assert audit["loose_verts"] == 0, audit
    assert audit["zero_area"] == 0, audit
    assert audit["shells"] == 1, audit
    assert audit["volume"] > 0.0, audit
    return audit


_clean()
assert bpy.app.version[:2] == (5, 2), bpy.app.version_string

key_1u = controls.keycap("TEST_KEY_1U")
key_2u = controls.keycap("TEST_KEY_2U", unit=2)
key_wide = controls.keycap("TEST_KEY_WIDE", width_m=0.0328)
knob = controls.knob("TEST_KNOB")
knob_plain = controls.knob("TEST_KNOB_PLAIN", mount_neck_m=0.0)

key_1_audit = _assert_solid(key_1u)
key_2_audit = _assert_solid(key_2u)
key_wide_audit = _assert_solid(key_wide)
knob_audit = _assert_solid(knob)
knob_plain_audit = _assert_solid(knob_plain)

key_1_box, key_1_lo, key_1_hi = _bbox(key_1u)
key_2_box, _, _ = _bbox(key_2u)
key_wide_box, _, _ = _bbox(key_wide)
knob_box, knob_lo, knob_hi = _bbox(knob)
tol = 2e-6
assert all(abs(a - b) < tol for a, b in zip(key_1_box, (0.0162, 0.0162, 0.0095))), key_1_box
assert abs(key_2_box[0] - 0.0302) < tol and abs(key_2_box[1] - 0.0162) < tol, key_2_box
assert abs(key_wide_box[0] - 0.0350) < tol and abs(key_wide_box[1] - 0.0162) < tol, key_wide_box
assert abs(knob_box[0] - 0.016) < tol and abs(knob_box[1] - 0.016) < tol, knob_box
assert abs(knob_box[2] - 0.018) < tol and abs(knob_lo[2]) < tol and abs(knob_hi[2] - 0.018) < tol

# Actual cavity geometry, measured by rays rather than object metadata.
key_cavity_z = _ray_z(key_1u, (0.0, 0.0, -0.001), (0.0, 0.0, 1.0))
key_dish_z = _ray_z(key_1u, (0.0, 0.0, 0.012), (0.0, 0.0, -1.0))
assert abs(key_cavity_z - 0.0079) < tol, key_cavity_z
assert abs(key_dish_z - 0.0091) < tol, key_dish_z

bore_center_z = _ray_z(knob, (0.0, 0.0, -0.001), (0.0, 0.0, 1.0))
bore_inside_z = _ray_z(knob, (0.0029, 0.0, -0.001), (0.0, 0.0, 1.0))
bore_outside_z = _ray_z(knob, (0.0031, 0.0, -0.001), (0.0, 0.0, 1.0))
assert abs(bore_center_z - 0.008) < tol and abs(bore_inside_z - 0.008) < tol
assert abs(bore_outside_z - 0.0) < tol

slot_floor_z = _ray_z(knob, (0.0, 0.0, 0.020), (0.0, 0.0, -1.0))
slot_inside_z = _ray_z(knob, (0.0, 0.00089, 0.020), (0.0, 0.0, -1.0))
slot_outside_z = _ray_z(knob, (0.0, 0.0010, 0.020), (0.0, 0.0, -1.0))
assert abs(slot_floor_z - 0.0168) < tol and abs(slot_inside_z - 0.0168) < tol
assert abs(slot_outside_z - 0.018) < tol

# Local stack-adaptation neck: OD 8.4 x 3.1 mm around the same Ø6 bore.
neck_outer = _ray_point(knob, (0.010, 0.0, 0.0015), (-1.0, 0.0, 0.0))
neck_inner = _ray_point(knob, (0.0, 0.0, 0.0015), (1.0, 0.0, 0.0))
barrel_seat_z = _ray_z(knob, (0.006, 0.0, 0.0045), (0.0, 0.0, -1.0))
assert abs(neck_outer[0] - 0.0042) < tol, neck_outer
assert abs(neck_inner[0] - 0.0030) < tol, neck_inner
assert abs((neck_outer[0] - neck_inner[0]) - 0.0012) < tol
assert abs(barrel_seat_z - 0.0031) < tol, barrel_seat_z

assert key_1u["functional_interface"] == "NOT_QUALIFIED"
assert knob["shaft_interface"] == "NOT_QUALIFIED"
assert len(knob.material_slots) == 0 and len(key_1u.material_slots) == 0
assert len(key_1u.modifiers) == len(key_2u.modifiers) == len(knob.modifiers) == len(knob_plain.modifiers) == 0
slot_floor_outer = [
    vertex for vertex in knob.data.vertices
    if abs(vertex.co.z - 0.0168) < tol
    and abs(math.hypot(vertex.co.x, vertex.co.y) - 0.008) < tol
]
assert len(slot_floor_outer) == controls.KNOB_SEGMENTS == 96, len(slot_floor_outer)

# Negative control: the checker must reject an open triangle.
mesh = bpy.data.meshes.new("NEGATIVE_OPEN_MESH")
mesh.from_pydata([(0, 0, 0), (0.001, 0, 0), (0, 0.001, 0)], [], [(0, 1, 2)])
negative = bpy.data.objects.new("NEGATIVE_OPEN", mesh)
bpy.context.scene.collection.objects.link(negative)
negative_audit = _audit(negative)
assert negative_audit["nonmanifold"] == 3 and math.isclose(negative_audit["volume"], 0.0, abs_tol=1e-15)

# Name collision must fail without deleting or replacing caller-owned data.
foreign_mesh = bpy.data.meshes.new("FOREIGN_CALLER_MESH")
foreign_mesh.from_pydata([(0, 0, 0)], [], [])
foreign = bpy.data.objects.new("FOREIGN_CALLER", foreign_mesh)
bpy.context.scene.collection.objects.link(foreign)
foreign_object_ptr = foreign.as_pointer()
foreign_mesh_ptr = foreign_mesh.as_pointer()
try:
    controls.keycap("FOREIGN_CALLER")
    raise AssertionError("constructor accepted an existing caller-owned object name")
except ValueError as exc:
    assert "object name already exists" in str(exc)
assert bpy.data.objects["FOREIGN_CALLER"].as_pointer() == foreign_object_ptr
assert bpy.data.objects["FOREIGN_CALLER"].data.as_pointer() == foreign_mesh_ptr
assert len(foreign.data.vertices) == 1

print(
    "controls fixture PASS",
    {
        "key_1u_volume_mm3": round(key_1_audit["volume"] * 1e9, 3),
        "key_2u_volume_mm3": round(key_2_audit["volume"] * 1e9, 3),
        "key_wide_volume_mm3": round(key_wide_audit["volume"] * 1e9, 3),
        "knob_volume_mm3": round(knob_audit["volume"] * 1e9, 3),
        "knob_plain_volume_mm3": round(knob_plain_audit["volume"] * 1e9, 3),
        "key_1u_bbox_mm": [round(v * 1000, 3) for v in key_1_box],
        "key_2u_bbox_mm": [round(v * 1000, 3) for v in key_2_box],
        "key_wide_bbox_mm": [round(v * 1000, 3) for v in key_wide_box],
        "knob_bbox_mm": [round(v * 1000, 3) for v in knob_box],
        "knob_neck_wall_mm": round((neck_outer[0] - neck_inner[0]) * 1000, 3),
        "knob_barrel_seat_z_mm": round(barrel_seat_z * 1000, 3),
        "negative_nonmanifold": negative_audit["nonmanifold"],
    },
)

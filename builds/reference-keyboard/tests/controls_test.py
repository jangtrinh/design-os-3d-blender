"""Finite numerical fixture for the native reference-keyboard controls."""
from __future__ import annotations

import importlib.util
import math
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path[:0] = [str(REPO / "scripts"), str(ROOT / "scripts")]
SPEC = importlib.util.spec_from_file_location("reference_keyboard_controls", ROOT / "scripts" / "controls.py")
controls = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controls)
import mechanics
import supports
from production_gate import export_roundtrip, meshprep, topology, walls_overhang


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


def _production_audit(obj, min_wall_mm=1.0):
    bm = meshprep.evaluated_mm_bmesh(obj)
    try:
        checks, measured = topology.evaluate(bm, 1)
        _wall_checks, wall = walls_overhang.wall_checks(bm, min_wall_mm)
    finally:
        bm.free()
    assert measured["self_intersection_pairs"] == 0, (obj.name, measured["sample_self_intersections"])
    assert measured["zero_area_faces"] == 0, (obj.name, measured)
    assert measured["non_manifold_edges"] == 0, (obj.name, measured)
    assert not [row for row in checks if row["status"] == "fail"], (obj.name, checks)
    assert wall["wall_min_mm"] is not None and wall["wall_min_mm"] >= min_wall_mm, (obj.name, wall)
    return measured, wall


_clean()
assert bpy.app.version[:2] == (5, 2), bpy.app.version_string

key_1u = controls.keycap("TEST_KEY_1U")
key_2u = controls.keycap("TEST_KEY_2U", unit=2)
key_wide = controls.keycap("TEST_KEY_WIDE", width_m=0.0328)
knob = controls.knob("TEST_KNOB")
knob_plain = controls.knob("TEST_KNOB_PLAIN", mount_neck_m=0.0)
knob_pec = controls.knob("TEST_KNOB_PEC11R", hardware_profile="PEC11R")
knob_encoder = controls.encoder_knob("TEST_ENCODER_KNOB")

key_1_audit = _assert_solid(key_1u)
key_2_audit = _assert_solid(key_2u)
key_wide_audit = _assert_solid(key_wide)
knob_audit = _assert_solid(knob)
knob_plain_audit = _assert_solid(knob_plain)
knob_pec_audit = _assert_solid(knob_pec)
knob_encoder_audit = _assert_solid(knob_encoder)

# Match the production gate's topology and wall predicates, in world-space mm.
key_1_prod, key_1_wall = _production_audit(key_1u, 1.0)
key_wide_prod, key_wide_wall = _production_audit(key_wide, 1.0)

# The delivered wide key is boolean-unioned with two guide pins.  Exercise that
# exact production path in a disposable checkpoint root, then re-run the same
# production predicates on the post-union mesh.
guided_wide = controls.keycap("TEST_KEY_WIDE_GUIDED", width_m=0.0328)
tmp_build = tempfile.TemporaryDirectory()
mechanics.CHECKPOINTS = Path(tmp_build.name) / "checkpoints"
supports.spacebar_guides(guided_wide)
guided_wide_audit = _assert_solid(guided_wide)
guided_wide_prod, guided_wide_wall = _production_audit(guided_wide, 1.0)

key_1_box, key_1_lo, key_1_hi = _bbox(key_1u)
key_2_box, _, _ = _bbox(key_2u)
key_wide_box, _, _ = _bbox(key_wide)
knob_box, knob_lo, knob_hi = _bbox(knob)
knob_pec_box, knob_pec_lo, knob_pec_hi = _bbox(knob_pec)
knob_encoder_box, _, _ = _bbox(knob_encoder)
tol = 2e-6
assert all(abs(a - b) < tol for a, b in zip(key_1_box, (0.0162, 0.0162, 0.0095))), key_1_box
assert abs(key_2_box[0] - 0.0302) < tol and abs(key_2_box[1] - 0.0162) < tol, key_2_box
assert abs(key_wide_box[0] - 0.0350) < tol and abs(key_wide_box[1] - 0.0162) < tol, key_wide_box
assert abs(knob_box[0] - 0.016) < tol and abs(knob_box[1] - 0.016) < tol, knob_box
assert abs(knob_box[2] - 0.018) < tol and abs(knob_lo[2]) < tol and abs(knob_hi[2] - 0.018) < tol
assert all(abs(a - b) < tol for a, b in zip(knob_pec_box, (0.016, 0.016, 0.018))), knob_pec_box
assert abs(knob_pec_lo[2]) < tol and abs(knob_pec_hi[2] - 0.018) < tol
assert all(abs(a - b) < tol for a, b in zip(knob_encoder_box, knob_pec_box)), knob_encoder_box

# Revision-B keycap: center ray enters the blind cross; an off-axis ray reaches the roof.
key_receiver_z = _ray_z(key_1u, (0.0, 0.0, -0.001), (0.0, 0.0, 1.0))
key_cavity_z = _ray_z(key_1u, (0.005, 0.0, -0.001), (0.0, 0.0, 1.0))
key_dish_z = _ray_z(key_1u, (0.0, 0.0, 0.012), (0.0, 0.0, -1.0))
assert abs(key_receiver_z - 0.0032) < tol, key_receiver_z
assert abs(key_cavity_z - 0.0079) < tol, key_cavity_z
assert abs(key_dish_z - 0.0091) < tol, key_dish_z

# Below z=4.5 mm only the central boss exists; immediately above it the visible
# skirt exists. The boss and source-guided custom cross are measured as geometry.
assert _ray_point(key_1u, (0.010, 0.005, 0.002), (-1.0, 0.0, 0.0)) is None
assert _ray_point(key_1u, (0.010, 0.005, 0.0046), (-1.0, 0.0, 0.0)) is not None
boss_outer = _ray_point(key_1u, (0.010, 0.0, 0.001), (-1.0, 0.0, 0.0))
cross_x = _ray_point(key_1u, (0.0, 0.0, 0.001), (1.0, 0.0, 0.0))
cross_y = _ray_point(key_1u, (0.0, 0.0, 0.001), (0.0, 1.0, 0.0))
h_arm = _ray_point(key_1u, (0.0015, 0.0, 0.001), (0.0, 1.0, 0.0))
v_arm = _ray_point(key_1u, (0.0, 0.0015, 0.001), (1.0, 0.0, 0.0))
assert abs(boss_outer[0] - 0.0032) < tol, boss_outer
assert abs(cross_x[0] - 0.00206) < tol and abs(cross_y[1] - 0.00206) < tol
assert abs(h_arm[1] - 0.00061) < tol, h_arm
assert abs(v_arm[0] - 0.00070) < tol, v_arm
assert abs((0.0032 - cross_x[0]) - 0.00114) < tol
wide_boss = _ray_point(key_wide, (0.010, 0.0, 0.001), (-1.0, 0.0, 0.0))
assert abs(wide_boss[0] - boss_outer[0]) < tol

# Nominal KS-33 Rev-2 male cross against the custom receiver leaves positive
# digital clearance; this is constructor math, not physical retention evidence.
assert key_1u["receiver_span_m"] - 0.00400 > 0
assert key_1u["receiver_horizontal_arm_m"] - 0.00110 > 0
assert key_1u["receiver_vertical_arm_m"] - 0.00128 > 0

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

# PEC11R explicit hardware profile: Ø12.6 counterbore 0..6, Ø6.2 round
# 6..8.6, then D-profile (+Y flat 1.65) to z16. In the final PEC11R
# counterpart stack the knob bottom is world z12, D engagement begins at 20.6,
# shaft tip is 25.6, and the D ceiling is 28.0: 5.0 mm engagement, 2.4 mm reserve.
# Top slot floor is local z17.2 (0.8 mm depth).
pec_counter = _ray_point(knob_pec, (0.0, 0.0, 0.003), (1.0, 0.0, 0.0))
pec_round = _ray_point(knob_pec, (0.0, 0.0, 0.007), (1.0, 0.0, 0.0))
pec_flat = _ray_point(knob_pec, (0.0, 0.0, 0.010), (0.0, 1.0, 0.0))
pec_back = _ray_point(knob_pec, (0.0, 0.0, 0.010), (0.0, -1.0, 0.0))
pec_ceiling = _ray_z(knob_pec, (0.0, 0.0, -0.001), (0.0, 0.0, 1.0))
pec_slot_floor = _ray_z(knob_pec, (0.0, 0.0, 0.020), (0.0, 0.0, -1.0))
assert abs(pec_counter[0] - 0.0063) < tol, pec_counter
assert abs(pec_round[0] - 0.0031) < tol, pec_round
assert abs(pec_flat[1] - 0.00165) < tol, pec_flat
assert abs(pec_back[1] + 0.0031) < tol, pec_back
assert abs((pec_flat[1] - pec_back[1]) - 0.00475) < tol
assert abs(pec_ceiling - 0.0160) < tol, pec_ceiling
assert abs(pec_slot_floor - 0.0172) < tol, pec_slot_floor
assert abs((0.0256 - 0.0206) - 0.0050) < 1e-12
assert abs((0.0120 + 0.0160) - 0.0256 - 0.0024) < 1e-12

assert key_1u["functional_interface"] == "NOT_QUALIFIED"
assert knob["shaft_interface"] == "NOT_QUALIFIED"
assert knob_pec["shaft_interface"] == "NOT_QUALIFIED_PHYSICAL_FIT"
assert knob_pec["hardware_profile"] == "PEC11R_SOURCE_DERIVED_CLEARANCE"
assert knob_encoder["hardware_profile"] == knob_pec["hardware_profile"]
assert math.isclose(knob_encoder_audit["volume"], knob_pec_audit["volume"], rel_tol=0, abs_tol=1e-12)
assert len(knob.material_slots) == 0 and len(key_1u.material_slots) == 0
assert len(key_1u.modifiers) == len(key_2u.modifiers) == len(knob.modifiers) == len(knob_plain.modifiers) == len(knob_pec.modifiers) == 0
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

# Independent binary-STL roundtrip for the actual production predicates. Export
# both parts before verify_roundtrip(), because each verification intentionally
# resets Blender to an empty file before importing its STL.
stl_dir = Path(tmp_build.name) / "stl"
stl_dir.mkdir(parents=True, exist_ok=True)
roundtrip_jobs = []
for part_id, obj, dims in (
    ("TEST_KEY_1U", key_1u, [16.2, 16.2, 9.5]),
    ("TEST_KEY_WIDE_GUIDED", guided_wide, [35.0, 16.2, 9.5]),
):
    part = {
        "id": part_id,
        "object": obj.name,
        "target_dims_mm": dims,
        "tol_mm": 0.05,
        "expected_shells": 1,
    }
    bm = meshprep.evaluated_mm_bmesh(obj)
    try:
        entry = export_roundtrip.export_part(bm, part, str(stl_dir))
    finally:
        bm.free()
    roundtrip_jobs.append((entry, part))

roundtrip_results = []
for entry, part in roundtrip_jobs:
    checks = export_roundtrip.verify_roundtrip(entry, part)
    failures = [row for row in checks if row["status"] == "fail"]
    assert not failures, (part["id"], failures)
    named = {row["name"]: row for row in checks}
    assert named["roundtrip_self_intersection_pairs"]["status"] == "pass", named
    assert named["roundtrip_non_manifold_edges"]["status"] == "pass", named
    assert named["roundtrip_zero_area_faces"]["status"] == "pass", named
    roundtrip_results.append({"id": part["id"], "sha256": entry["sha256"]})
tmp_build.cleanup()

print(
    "controls fixture PASS",
    {
        "key_1u_volume_mm3": round(key_1_audit["volume"] * 1e9, 3),
        "key_2u_volume_mm3": round(key_2_audit["volume"] * 1e9, 3),
        "key_wide_volume_mm3": round(key_wide_audit["volume"] * 1e9, 3),
        "knob_volume_mm3": round(knob_audit["volume"] * 1e9, 3),
        "knob_plain_volume_mm3": round(knob_plain_audit["volume"] * 1e9, 3),
        "knob_pec11r_volume_mm3": round(knob_pec_audit["volume"] * 1e9, 3),
        "key_1u_bbox_mm": [round(v * 1000, 3) for v in key_1_box],
        "key_2u_bbox_mm": [round(v * 1000, 3) for v in key_2_box],
        "key_wide_bbox_mm": [round(v * 1000, 3) for v in key_wide_box],
        "knob_bbox_mm": [round(v * 1000, 3) for v in knob_box],
        "knob_pec11r_bbox_mm": [round(v * 1000, 3) for v in knob_pec_box],
        "key_receiver_span_mm": round(cross_x[0] * 2 * 1000, 3),
        "key_receiver_h_arm_mm": round(h_arm[1] * 2 * 1000, 3),
        "key_receiver_v_arm_mm": round(v_arm[0] * 2 * 1000, 3),
        "key_1u_self_intersections": key_1_prod["self_intersection_pairs"],
        "key_wide_self_intersections": key_wide_prod["self_intersection_pairs"],
        "guided_wide_self_intersections": guided_wide_prod["self_intersection_pairs"],
        "key_1u_wall_min_mm": round(key_1_wall["wall_min_mm"], 4),
        "key_wide_wall_min_mm": round(key_wide_wall["wall_min_mm"], 4),
        "guided_wide_wall_min_mm": round(guided_wide_wall["wall_min_mm"], 4),
        "roundtrip_parts": roundtrip_results,
        "knob_neck_wall_mm": round((neck_outer[0] - neck_inner[0]) * 1000, 3),
        "knob_barrel_seat_z_mm": round(barrel_seat_z * 1000, 3),
        "negative_nonmanifold": negative_audit["nonmanifold"],
    },
)

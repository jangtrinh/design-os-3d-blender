"""Actual-scene revision-B interface regression; run with --blend model.blend."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reference_keyboard_inspect_fit", ROOT / "scripts" / "inspect_fit.py"
)
inspect_fit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_fit)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


assert bpy.app.version[:2] == (5, 2), bpy.app.version_string
scene_path = Path(bpy.data.filepath)
assert scene_path.is_file(), "interfaces_test.py requires an actual saved model via --blend"
before = sha256(scene_path)
layout = json.loads((ROOT / "layout.json").read_text(encoding="utf-8"))
interfaces = json.loads((ROOT / "interfaces.json").read_text(encoding="utf-8"))
assert interfaces["revision"] == "B"

evidence = inspect_fit.inspect(source_sha256=before)
expected_count = (
    sum(len(row) for row in layout["main_rows"])
    + len(layout["bottom_row"])
    + int(layout["rear_macros"]["count"])
    + len(layout["left_macros_mm"])
)
expected_samples = [round(i * 0.5, 1) for i in range(int(round(layout["key_travel_mm"] / 0.5)) + 1)]

# Regression for the old nearest-normal false positive at full travel.  The
# broad 16.2 mm key AABB contains points that are outside the actual lower boss,
# so point-in-solid classification must follow the closed mesh, not the nearest
# face normal.  Keep one actual B03 plate sample that previously misclassified.
key0 = bpy.data.objects["RK_KEY_00"]
key0_mesh = inspect_fit._tri_mesh(key0)
key0_box = inspect_fit._bbox_mm(key0)
key0_center = inspect_fit._center_xy(key0_box)
moved_key0 = inspect_fit._transform_mesh(
    key0_mesh,
    (key0_center[0] / 1000.0, key0_center[1] / 1000.0),
    offset=(0.0, 0.0, -0.003),
)
moved_bottom = key0_box[0][2] / 1000.0 - 0.003
outside_boss = Vector((key0_center[0] / 1000.0 + 0.007, key0_center[1] / 1000.0, moved_bottom + 0.0001))
inside_boss = Vector((key0_center[0] / 1000.0 + 0.0025, key0_center[1] / 1000.0 + 0.0015, moved_bottom + 0.0001))
old_bad_plate_sample = Vector((-0.110665232, 0.008000999, 0.0151))
assert inspect_fit._point_inside(moved_key0, outside_boss) == (False, False)
assert inspect_fit._point_inside(moved_key0, inside_boss) == (True, False)
assert inspect_fit._point_inside(moved_key0, old_bad_plate_sample) == (False, False)

assert evidence["switch_housings"]["evaluated_connected_shells"] == expected_count
assembly = evidence["switch_assembly_envelope"]
assert assembly["cells_checked"] == expected_count and assembly["all_within_tolerance"], assembly
assert assembly["expected_mm"] == [layout["switch_width_mm"], layout["switch_width_mm"], layout["switch_height_mm"]]

collision = evidence["switch_keycap_overlap"]
assert collision["travel_samples_mm"] == expected_samples, collision["travel_samples_mm"]
assert collision["collision_pairs"] == 0, collision["colliding_indices"]

key_stem = evidence["interfaces"]["key_stem"]
assert key_stem["cells_checked"] == expected_count
assert key_stem["travel_samples_mm"] == expected_samples
assert key_stem["dimensions_within_0_05_mm"], key_stem["rows"][0]
assert key_stem["key_material_stem_collision_indices"] == []
assert key_stem["stem_static_collision_indices"] == []
receiver_depth = float(interfaces["keycap"]["receiver_depth"])
stem_length = float(interfaces["keycap"]["stem_top_z"]) - float(interfaces["keycap"]["stem_bottom_z"])
for value in key_stem["insertion_range_mm"]:
    assert abs(value - stem_length) <= 0.05, key_stem["insertion_range_mm"]
for value in key_stem["ceiling_reserve_range_mm"]:
    assert abs(value - (receiver_depth - stem_length)) <= 0.05, key_stem["ceiling_reserve_range_mm"]
assert evidence["keycap_switch_engagement"]["status"] == "PASS_DIGITAL_PROTOTYPE"
assert evidence["keycap_switch_engagement"]["compatibility"] == "NOT_QUALIFIED"

guides = evidence["interfaces"]["wide_guides"]
assert guides["guides_checked"] == 2 and guides["collision_free"], guides
for row in guides["rows"]:
    assert abs(row["pin_diameter_mm"] - float(interfaces["spacebar"]["pin_diameter"])) <= 0.05, row
expected_rest = max(
    0.0,
    float(interfaces["spacebar"]["sleeve_z"][1]) - float(interfaces["spacebar"]["pin_bottom_z"]),
)
for value in guides["rest_engagement_range_mm"]:
    assert abs(value - expected_rest) <= 0.10, (value, expected_rest)
assert all(not item["collision"] for row in guides["rows"] for item in row["per_travel"])

encoders = evidence["interfaces"]["encoder_dshaft"]
assert encoders["pairs_checked"] == 5
assert encoders["matching_rotations_collision_free"], encoders["rows"]
assert encoders["negative_controls_detect_collision"], encoders["rows"]
for value in encoders["engagement_range_mm"]:
    assert abs(value - float(interfaces["encoder"]["nominal_D_engagement"])) <= 0.05, encoders
for row in encoders["rows"]:
    assert abs(row["knob_flat_y_mm"] - float(interfaces["encoder"]["receiver_flat_axis_offset"])) <= 0.05, row
    assert abs(row["shaft_flat_y_mm"] - float(interfaces["encoder"]["shaft_flat_axis_offset"])) <= 0.05, row

binding = evidence["interfaces"]["source_binding"]
assert binding["caller_scene_sha256"] == before
assert binding["layout_revision"] == layout["revision"]
assert binding["interfaces_revision"] == interfaces["revision"]
after = sha256(scene_path)
assert after == before, "read-only interface fixture changed the source scene file"

print("interfaces fixture PASS", {
    "scene_sha256": before,
    "switches": expected_count,
    "travel_samples_mm": expected_samples,
    "stem_insertion_mm": key_stem["insertion_range_mm"],
    "receiver_reserve_mm": key_stem["ceiling_reserve_range_mm"],
    "guide_rest_engagement_mm": guides["rest_engagement_range_mm"],
    "D_engagement_mm": encoders["engagement_range_mm"],
    "D_negative_controls": encoders["negative_controls_detect_collision"],
})

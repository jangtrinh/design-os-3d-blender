"""Headless contract tests for scripts/boilerplates/bp_animation.py on Blender 5.2."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import bpy
from bpy_extras import anim_utils


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "boilerplates" / "bp_animation.py"
sys.path.insert(0, str(ROOT / "scripts"))
from agent_runtime import emit_ok


def load_animation_module():
    spec = importlib.util.spec_from_file_location("bp_animation_contract_target", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


animation = load_animation_module()


def new_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def assigned_channelbag(obj: bpy.types.Object) -> bpy.types.ActionChannelbag:
    assert obj.animation_data is not None
    assert obj.animation_data.action_slot is not None
    channelbag = anim_utils.animdata_get_channelbag_for_assigned_slot(obj.animation_data)
    assert channelbag is not None
    assert channelbag.slot == obj.animation_data.action_slot
    return channelbag


def fcurve_for(obj: bpy.types.Object, data_path: str, index: int) -> bpy.types.FCurve:
    fcurve = assigned_channelbag(obj).fcurves.find(data_path, index=index)
    assert fcurve is not None, (obj.name, data_path, index)
    return fcurve


def key_by_frame(fcurve: bpy.types.FCurve, frame: float) -> bpy.types.Keyframe:
    matches = [key for key in fcurve.keyframe_points if abs(float(key.co[0]) - frame) < 1e-6]
    assert len(matches) == 1, (frame, [tuple(key.co) for key in fcurve.keyframe_points])
    return matches[0]


def curve_snapshot(fcurve: bpy.types.FCurve):
    return [
        (float(key.co[0]), float(key.co[1]), key.interpolation)
        for key in fcurve.keyframe_points
    ]


def test_property_keys_are_slot_scoped_and_rerunnable():
    owner = new_object("AnimContract_Owner")
    neighbor = new_object("AnimContract_Neighbor")
    action = bpy.data.actions.new("AnimContract_SharedAction")
    owner_slot = action.slots.new(id_type="OBJECT", name=owner.name)
    neighbor_slot = action.slots.new(id_type="OBJECT", name=neighbor.name)

    owner_ad = owner.animation_data_create()
    owner_ad.action = action
    owner_ad.action_slot = owner_slot
    neighbor_ad = neighbor.animation_data_create()
    neighbor_ad.action = action
    neighbor_ad.action_slot = neighbor_slot

    owner_cb = anim_utils.action_ensure_channelbag_for_slot(action, owner_slot)
    neighbor_cb = anim_utils.action_ensure_channelbag_for_slot(action, neighbor_slot)

    owner_curve = owner_cb.fcurves.ensure("location", index=0)
    owner_existing = owner_curve.keyframe_points.insert(frame=5.0, value=9.0)
    owner_existing.interpolation = "CONSTANT"
    owner_curve.update()

    neighbor_curve = neighbor_cb.fcurves.ensure("location", index=0)
    neighbor_key = neighbor_curve.keyframe_points.insert(frame=3.0, value=7.0)
    neighbor_key.interpolation = "CONSTANT"
    neighbor_curve.update()
    neighbor_before = curve_snapshot(neighbor_curve)

    animation.animate_property_keys(
        owner,
        "location",
        [(1, 1.25), (10, 4.5)],
        index=0,
        interpolation="LINEAR",
    )

    assert owner.animation_data.action_slot == owner_slot
    assert curve_snapshot(neighbor_curve) == neighbor_before
    assert key_by_frame(owner_curve, 5.0).interpolation == "CONSTANT"
    assert key_by_frame(owner_curve, 1.0).interpolation == "LINEAR"
    assert key_by_frame(owner_curve, 10.0).interpolation == "LINEAR"
    assert len(owner_curve.keyframe_points) == 3

    animation.animate_property_keys(
        owner,
        "location",
        [(1, 2.0), (10, 6.0)],
        index=0,
        interpolation="BEZIER",
    )

    assert len(owner_curve.keyframe_points) == 3, "rerun duplicated keys"
    assert abs(key_by_frame(owner_curve, 1.0).co[1] - 2.0) < 1e-6
    assert abs(key_by_frame(owner_curve, 10.0).co[1] - 6.0) < 1e-6
    assert key_by_frame(owner_curve, 1.0).interpolation == "BEZIER"
    assert key_by_frame(owner_curve, 10.0).interpolation == "BEZIER"
    assert key_by_frame(owner_curve, 5.0).interpolation == "CONSTANT"
    assert curve_snapshot(neighbor_curve) == neighbor_before


def test_indexed_assignment_supports_full_rna_array_range():
    obj = new_object("AnimContract_Quaternion")
    obj.rotation_mode = "QUATERNION"

    animation.animate_property_keys(
        obj,
        "rotation_quaternion",
        [(1, 0.0), (8, 0.75)],
        index=3,
        interpolation="LINEAR",
    )

    fcurve = fcurve_for(obj, "rotation_quaternion", 3)
    assert len(fcurve.keyframe_points) == 2
    assert abs(fcurve.evaluate(1.0) - 0.0) < 1e-6
    assert abs(fcurve.evaluate(8.0) - 0.75) < 1e-6


def test_invalid_index_fails_before_creating_animation_data():
    obj = new_object("AnimContract_InvalidIndex")
    try:
        animation.animate_property_keys(obj, "location", [(1, 2.0)], index=5)
    except (IndexError, ValueError):
        pass
    else:
        raise AssertionError("out-of-range index must fail")
    assert obj.animation_data is None, "invalid assignment must not create animation data"


def test_turntable_preserves_unowned_key_and_reruns_without_duplicates():
    obj = new_object("AnimContract_Turntable")
    obj.rotation_mode = "XYZ"
    obj.rotation_euler[2] = 0.25
    assert obj.keyframe_insert(data_path="rotation_euler", index=2, frame=30)
    fcurve = fcurve_for(obj, "rotation_euler", 2)
    middle = key_by_frame(fcurve, 30.0)
    middle.interpolation = "CONSTANT"
    fcurve.update()

    animation.animate_continuous_turntable(obj, start_frame=1, end_frame=60, axis_index=2)
    assert len(fcurve.keyframe_points) == 3
    assert key_by_frame(fcurve, 30.0).interpolation == "CONSTANT"
    assert key_by_frame(fcurve, 1.0).interpolation == "LINEAR"
    assert key_by_frame(fcurve, 61.0).interpolation == "LINEAR"

    animation.animate_continuous_turntable(obj, start_frame=1, end_frame=60, axis_index=2)
    assert len(fcurve.keyframe_points) == 3, "turntable rerun duplicated endpoint keys"
    assert key_by_frame(fcurve, 30.0).interpolation == "CONSTANT"
    assert abs(key_by_frame(fcurve, 1.0).co[1]) < 1e-6
    assert abs(key_by_frame(fcurve, 61.0).co[1] - 2.0 * animation.math.pi) < 1e-6


def test_driver_rerun_reuses_target_curve():
    source = new_object("AnimContract_DriverSource")
    target = new_object("AnimContract_DriverTarget")

    animation.add_simple_driver(
        target,
        "location",
        0,
        source,
        "location",
        source_array_index=1,
        expression="var * 2.0",
    )
    animation.add_simple_driver(
        target,
        "location",
        0,
        source,
        "location",
        source_array_index=1,
        expression="var * 3.0",
    )

    assert target.animation_data is not None
    drivers = [
        fcurve for fcurve in target.animation_data.drivers
        if fcurve.data_path == "location" and fcurve.array_index == 0
    ]
    assert len(drivers) == 1, "rerun created duplicate driver curves"
    fcurve = drivers[0]
    assert len(fcurve.keyframe_points) == 0
    assert len(fcurve.modifiers) == 0
    assert fcurve.driver.expression == "var * 3.0"
    assert len(fcurve.driver.variables) == 1
    variable = fcurve.driver.variables[0]
    assert variable.name == "var"
    assert variable.targets[0].id == source
    assert variable.targets[0].data_path == "location[1]"

    for source_value, expected in ((2.0, 6.0), (-1.5, -4.5)):
        source.location[1] = source_value
        bpy.context.view_layer.update()
        evaluated = target.evaluated_get(bpy.context.evaluated_depsgraph_get())
        assert abs(evaluated.location[0] - expected) < 1e-6, (
            source_value,
            evaluated.location[0],
            expected,
        )


def main():
    tests = [
        test_property_keys_are_slot_scoped_and_rerunnable,
        test_indexed_assignment_supports_full_rna_array_range,
        test_invalid_index_fails_before_creating_animation_data,
        test_turntable_preserves_unowned_key_and_reruns_without_duplicates,
        test_driver_rerun_reuses_target_curve,
    ]
    for test in tests:
        test()
    measured = {
        "blender": bpy.app.version_string,
        "tests": [test.__name__ for test in tests],
    }
    print("TEST_PASS " + json.dumps(measured, sort_keys=True))
    emit_ok(
        "animation-contract",
        tests=len(tests),
        blender=bpy.app.version_string,
        build_hash=bpy.app.build_hash.decode(),
        manufacture="NOT_REQUESTED",
    )


if __name__ == "__main__":
    assert bpy.app.background, "Run this contract in a disposable headless Blender process"
    main()

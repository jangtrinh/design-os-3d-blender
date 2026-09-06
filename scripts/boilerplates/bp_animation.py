"""
bp_animation.py — Animation & Driver Boilerplate for Blender 5.2+.

Handles:
- Keyframe insertion via data API
- Cyclic continuous turntable animation
- Scripted driver generation (zero keyframe remapping)
- Evaluation at frame steps
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import math
from typing import List, Tuple, Dict, Any, Optional


def animate_property_keys(
    obj: bpy.types.Object,
    data_path: str,
    key_values: List[Tuple[int, float]],
    index: int = -1,
    interpolation: str = 'BEZIER'
) -> None:
    """
    Keys a property across frames and sets interpolation.
    data_path examples: 'location', 'rotation_euler', 'scale'.
    """
    for frame, val in key_values:
        if index >= 0:
            setattr(getattr(obj, data_path), "xyz"[index] if hasattr(getattr(obj, data_path), "xyz") else str(index), val)
            obj.keyframe_insert(data_path=data_path, index=index, frame=frame)
        else:
            setattr(obj, data_path, val)
            obj.keyframe_insert(data_path=data_path, frame=frame)

    # Set interpolation on created fcurves
    if obj.animation_data and obj.animation_data.action:
        # In 5.x, iterate all fcurves across channelbags
        act = obj.animation_data.action
        for layer in act.layers:
            for strip in layer.strips:
                for slot in act.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        for fc in cb.fcurves:
                            if fc.data_path == data_path and (index < 0 or fc.array_index == index):
                                for kp in fc.keyframe_points:
                                    kp.interpolation = interpolation


def animate_continuous_turntable(
    obj: bpy.types.Object,
    start_frame: int = 1,
    end_frame: int = 120,
    axis_index: int = 2  # Z axis
) -> None:
    """
    Creates a linear 360-degree rotation loop on the given axis.
    """
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis_index] = 0.0
    obj.keyframe_insert(data_path="rotation_euler", index=axis_index, frame=start_frame)

    obj.rotation_euler[axis_index] = 2.0 * math.pi
    obj.keyframe_insert(data_path="rotation_euler", index=axis_index, frame=end_frame + 1)

    # Set linear interpolation for seamless looping
    if obj.animation_data and obj.animation_data.action:
        act = obj.animation_data.action
        for layer in act.layers:
            for strip in layer.strips:
                for slot in act.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        for fc in cb.fcurves:
                            if fc.data_path == "rotation_euler" and fc.array_index == axis_index:
                                for kp in fc.keyframe_points:
                                    kp.interpolation = 'LINEAR'


def add_simple_driver(
    target_obj: bpy.types.Object,
    prop_path: str,
    array_index: int,
    source_obj: bpy.types.Object,
    source_prop_path: str,
    source_array_index: int = 0,
    expression: str = "var * 2.0"
) -> bpy.types.Driver:
    """
    Adds a mathematical driver to target property based on a source property.
    Clears auto-created keyframes/modifiers from the driver curve to ensure pure pass-through.
    """
    fcurve = target_obj.driver_add(prop_path, array_index)
    # Clear default keyframe points or modifiers in 5.x
    fcurve.keyframe_points.clear()
    fcurve.modifiers.clear()

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = expression

    # Remove default variables
    for var in list(driver.variables):
        driver.variables.remove(var)

    # Add single variable
    var = driver.variables.new()
    var.name = "var"
    var.type = 'SINGLE_PROP'
    target = var.targets[0]
    target.id = source_obj
    target.data_path = f"{source_prop_path}[{source_array_index}]" if source_array_index >= 0 else source_prop_path

    return driver


if __name__ == '__main__':
    print("Testing bp_animation.py headless...")
    
    mesh = bpy.data.meshes.new("Anim_Test_Mesh")
    obj = bpy.data.objects.new("Anim_Test_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Animate turntable
    animate_continuous_turntable(obj, start_frame=1, end_frame=60, axis_index=2)

    # Test evaluation
    bpy.context.scene.frame_set(1)
    rot_start = obj.rotation_euler[2]
    bpy.context.scene.frame_set(31)
    rot_mid = obj.rotation_euler[2]

    print(f"Frame 1 Rot: {rot_start:.4f} rad, Frame 31 Rot: {rot_mid:.4f} rad")
    assert abs(rot_mid - math.pi) < 0.1, "Turntable rotation did not evaluate correctly!"
    print("bp_animation verified successfully.")

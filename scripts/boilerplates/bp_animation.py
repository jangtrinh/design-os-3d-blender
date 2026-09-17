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
from bpy_extras import anim_utils
from typing import Any, List, Tuple


_FRAME_EPSILON = 1e-6


def _assigned_channelbag(obj: bpy.types.Object):
    """Return only the channelbag assigned to ``obj`` without creating anything."""
    anim_data = obj.animation_data
    if anim_data is None or anim_data.action is None or anim_data.action_slot is None:
        return None
    return anim_utils.animdata_get_channelbag_for_assigned_slot(anim_data)


def _matching_assigned_fcurves(
    obj: bpy.types.Object,
    data_path: str,
    index: int,
):
    """Snapshot matching F-Curves from obj's assigned slot only."""
    channelbag = _assigned_channelbag(obj)
    if channelbag is None:
        return ()
    if index >= 0:
        fcurve = channelbag.fcurves.find(data_path, index=index)
        return (fcurve,) if fcurve is not None else ()
    return tuple(fcurve for fcurve in channelbag.fcurves if fcurve.data_path == data_path)


def _assign_key_value(
    obj: bpy.types.Object,
    data_path: str,
    index: int,
    value: Any,
) -> None:
    """Assign a simple Object RNA property value before key insertion."""
    if index < 0:
        setattr(obj, data_path, value)
        return

    prop = obj.path_resolve(data_path)
    try:
        size = len(prop)
    except TypeError as exc:
        raise ValueError(f"{data_path!r} is not an indexed property") from exc
    if index >= size:
        raise IndexError(f"index {index} out of range for {data_path!r} (size {size})")
    prop[index] = value


def _set_interpolation_on_frames(
    obj: bpy.types.Object,
    data_path: str,
    index: int,
    frames: List[float],
    interpolation: str,
) -> None:
    """Set interpolation only on keys addressed by this helper invocation."""
    fcurves = _matching_assigned_fcurves(obj, data_path, index)
    if not fcurves:
        raise RuntimeError(f"no assigned-slot F-Curve found for {data_path!r} index={index}")

    unique_frames = tuple(dict.fromkeys(float(frame) for frame in frames))
    for fcurve in fcurves:
        found = set()
        for key in tuple(fcurve.keyframe_points):
            key_frame = float(key.co[0])
            for frame in unique_frames:
                if abs(key_frame - frame) <= _FRAME_EPSILON:
                    key.interpolation = interpolation
                    found.add(frame)
                    break
        missing = [frame for frame in unique_frames if frame not in found]
        if missing:
            raise RuntimeError(
                f"missing inserted key(s) for {data_path!r} index={fcurve.array_index}: {missing}"
            )
        fcurve.update()


def animate_property_keys(
    obj: bpy.types.Object,
    data_path: str,
    key_values: List[Tuple[int, Any]],
    index: int = -1,
    interpolation: str = 'BEZIER'
) -> None:
    """
    Keys a property across frames and sets interpolation.
    data_path examples: 'location', 'rotation_euler', 'scale'.

    Interpolation is changed only for the frames keyed by this call and only in
    ``obj.animation_data.action_slot``. Existing keys in other slots are untouched.
    """
    if not key_values:
        return

    keyed_frames: List[float] = []
    for frame, val in key_values:
        _assign_key_value(obj, data_path, index, val)
        kwargs = {"data_path": data_path, "frame": frame}
        if index >= 0:
            kwargs["index"] = index
        if not obj.keyframe_insert(**kwargs):
            raise RuntimeError(f"keyframe_insert failed for {data_path!r} at frame {frame}")
        keyed_frames.append(float(frame))

    _set_interpolation_on_frames(obj, data_path, index, keyed_frames, interpolation)


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
    animate_property_keys(
        obj,
        "rotation_euler",
        [(start_frame, 0.0), (end_frame + 1, 2.0 * math.pi)],
        index=axis_index,
        interpolation='LINEAR',
    )


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
    for modifier in tuple(fcurve.modifiers):
        fcurve.modifiers.remove(modifier)
    fcurve.extrapolation = 'LINEAR'

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
    target.id_type = 'OBJECT'
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

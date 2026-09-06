"""
bp_cam_autoframing.py — Camera Bounding-Box Frustum Auto-Framing Boilerplate.

Standards & Academic Citations:
- Hartley, R., & Zisserman, A. (2004). "Multiple View Geometry in Computer Vision (2nd ed.)." Cambridge University Press. ISBN: 978-0-521-54051-3.
- Blinn, J. F. (1996). "Jim Blinn's Corner: A Trip Down the Graphics Pipeline." Morgan Kaufmann. (Viewing frustum perspective geometry).

Target: Blender 5.2 LTS (Pinhole camera sensor trigonometry).
"""

from __future__ import annotations
import bpy
import math
from mathutils import Vector
from typing import Tuple


def calculate_camera_distance_for_bbox(
    bounding_radius: float,
    focal_length_mm: float = 50.0,
    sensor_width_mm: float = 36.0,
    margin_factor: float = 1.15
) -> float:
    """
    Computes camera distance d to encompass a bounding sphere of radius R:
    half_fov = arctan(sensor_width / (2 * focal_length))
    d = (R * margin) / sin(half_fov)
    """
    half_fov = math.atan(sensor_width_mm / (2.0 * focal_length_mm))
    distance = (bounding_radius * margin_factor) / math.sin(half_fov)
    return distance


def auto_frame_object(
    camera_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    view_direction: Vector = Vector((1.0, -1.0, 0.7)),
    margin_factor: float = 1.20
) -> None:
    """
    Positions and orients camera_obj to perfectly frame target_obj in the render frustum.
    """
    # 1. Compute target bounding sphere
    bbox_corners = [target_obj.matrix_world @ Vector(corner) for corner in target_obj.bound_box]
    center = sum(bbox_corners, Vector((0.0, 0.0, 0.0))) / 8.0
    radius = max((corner - center).length for corner in bbox_corners)

    # 2. Camera optics
    cam_data = camera_obj.data
    focal_length = cam_data.lens
    sensor_width = cam_data.sensor_width

    # 3. Distance calculation
    dist = calculate_camera_distance_for_bbox(radius, focal_length, sensor_width, margin_factor)
    dir_norm = view_direction.normalized()
    camera_obj.location = center + dir_norm * dist

    # 4. Aim camera at center
    track_con = None
    for con in camera_obj.constraints:
        if con.type == 'TRACK_TO':
            track_con = con
            break
    if not track_con:
        track_con = camera_obj.constraints.new('TRACK_TO')
        track_con.track_axis = 'TRACK_NEGATIVE_Z'
        track_con.up_axis = 'UP_Y'
    
    # Target empty
    target_name = f"{target_obj.name}_CamTarget"
    target_empty = bpy.data.objects.get(target_name)
    if not target_empty:
        target_empty = bpy.data.objects.new(target_name, None)
        bpy.context.scene.collection.objects.link(target_empty)
    target_empty.location = center
    track_con.target = target_empty


if __name__ == '__main__':
    print("Testing bp_cam_autoframing.py headless...")
    
    # Test object: 2m x 1m x 0.5m box
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    target = bpy.context.active_object
    target.scale = (2.0, 1.0, 0.5)

    cam_data = bpy.data.cameras.new("AutoCam")
    cam = bpy.data.objects.new("AutoCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)

    auto_frame_object(cam, target, margin_factor=1.25)
    print(f"Camera positioned at: {cam.location}, Distance: {(cam.location - target.location).length:.3f} m")
    assert (cam.location - target.location).length > 2.0
    print("bp_cam_autoframing verified successfully.")

"""Turntable preview render for AI visual feedback.

Renders N frames of the current scene's objects rotating 360° around Z,
using an auto-created camera pivot. Fast Cycles settings for quick QA.

Usage (headless, on a saved .blend):
  scripts/headless-run.sh scripts/turntable-preview.py my_scene.blend
Or via MCP execute_blender_code: exec(open('scripts/turntable-preview.py').read())

Env overrides: TT_FRAMES (16), TT_RES (640), TT_SAMPLES (16), TT_OUT (output/turntable)
"""
import math
import os

import bpy

FRAMES = int(os.environ.get("TT_FRAMES", 16))
RES = int(os.environ.get("TT_RES", 640))
SAMPLES = int(os.environ.get("TT_SAMPLES", 16))
OUT_DIR = os.environ.get(
    "TT_OUT", os.path.join(os.environ.get("AGENT_REPO_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "turntable")
)


def scene_bounds_center_radius():
    """Center + radius of all visible mesh objects, for camera placement."""
    import mathutils

    pts = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.hide_render:
            for corner in obj.bound_box:
                pts.append(obj.matrix_world @ mathutils.Vector(corner))
    if not pts:
        raise RuntimeError("No visible mesh objects to render")
    center = sum(pts, mathutils.Vector()) / len(pts)
    radius = max((p - center).length for p in pts)
    return center, max(radius, 0.5)


def build_turntable_camera(center, radius):
    pivot = bpy.data.objects.new("TT_Pivot", None)
    pivot.location = center
    bpy.context.collection.objects.link(pivot)

    cam_data = bpy.data.cameras.new("TT_Cam")
    cam = bpy.data.objects.new("TT_Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.parent = pivot
    cam.location = (radius * 2.5, 0, radius * 0.9)
    track = cam.constraints.new("TRACK_TO")
    track.target = pivot
    bpy.context.scene.camera = cam
    return pivot


def ensure_light(center, radius):
    if any(o.type == "LIGHT" for o in bpy.context.scene.objects):
        return
    sun = bpy.data.lights.new("TT_Sun", "SUN")
    sun.energy = 3
    light = bpy.data.objects.new("TT_Sun", sun)
    light.location = (center.x + radius, center.y - radius, center.z + radius * 2)
    light.rotation_euler = (math.radians(40), 0, math.radians(45))
    bpy.context.collection.objects.link(light)


def render_turntable():
    os.makedirs(OUT_DIR, exist_ok=True)
    center, radius = scene_bounds_center_radius()
    pivot = build_turntable_camera(center, radius)
    ensure_light(center, radius)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = RES

    for i in range(FRAMES):
        pivot.rotation_euler = (0, 0, 2 * math.pi * i / FRAMES)
        scene.render.filepath = os.path.join(OUT_DIR, f"tt_{i:02d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"rendered {scene.render.filepath}")

    print(f"TURNTABLE_DONE {FRAMES} frames -> {OUT_DIR}")


if __name__ == "__main__":
    render_turntable()

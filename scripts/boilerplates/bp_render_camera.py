"""
bp_render_camera.py — Production Rendering, Camera & Lighting Boilerplate.

Target: Blender 5.2 LTS (Cycles Metal/GPU on macOS, CPU fallback, AgX OCIO).
Safe headless execution without GUI display server.
"""

from __future__ import annotations
import bpy
import math
from mathutils import Vector
from typing import Tuple, Optional


def configure_cycles_headless(
    scene: bpy.types.Scene,
    samples: int = 64,
    use_denoising: bool = True,
    transparent_bg: bool = False
) -> str:
    """
    Configures Cycles for headless execution. Enables GPU (Metal on macOS, CUDA/OptiX on Linux/Windows)
    with automatic CPU fallback.
    """
    scene.render.engine = 'CYCLES'
    cycles = scene.cycles
    cycles.samples = samples
    cycles.preview_samples = min(samples, 32)
    cycles.use_denoising = use_denoising
    if use_denoising:
        cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.render.film_transparent = transparent_bg

    # GPU Device detection
    addons = bpy.context.preferences.addons
    backend = 'CPU'
    if 'cycles' in addons:
        cprefs = addons['cycles'].preferences
        # 5.2: `compute_device_type` is a dynamic enum whose `enum_items` is EMPTY in
        # background mode, so never gate on it. Enumerate real devices per backend instead;
        # `get_devices_for_type` also lists CPU entries, hence the `d.type == cand` filter.
        for cand in ('METAL', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
            try:
                devs = [d for d in cprefs.get_devices_for_type(cand) if d.type == cand]
            except Exception:
                devs = []
            if devs:
                cprefs.compute_device_type = cand
                for d in cprefs.devices:
                    d.use = (d.type == cand)
                cycles.device = 'GPU'
                backend = cand
                break
    if backend == 'CPU':
        cycles.device = 'CPU'

    return backend


def configure_agx_color_management(
    scene: bpy.types.Scene,
    view_transform: str = 'AgX',
    look: str = 'None'
) -> None:
    """Configures modern wide-gamut AgX color management."""
    scene.view_settings.view_transform = view_transform
    scene.view_settings.look = look


def create_targeted_camera(
    name: str,
    location: Vector | Tuple[float, float, float],
    target_point: Vector | Tuple[float, float, float] = (0.0, 0.0, 0.0),
    focal_length: float = 50.0
) -> bpy.types.Object:
    """
    Spawns camera and binds a Track To constraint pointing at target_point.
    """
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    if name in bpy.data.cameras:
        bpy.data.cameras.remove(bpy.data.cameras[name], do_unlink=True)

    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = focal_length
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Create target empty
    target_name = f"{name}_Target"
    if target_name in bpy.data.objects:
        empty = bpy.data.objects[target_name]
    else:
        empty = bpy.data.objects.new(target_name, None)
        bpy.context.scene.collection.objects.link(empty)
    empty.location = target_point

    # Track To constraint
    track = cam_obj.constraints.new('TRACK_TO')
    track.target = empty
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    return cam_obj


def setup_three_point_lighting(
    target_co: Vector | Tuple[float, float, float] = (0.0, 0.0, 0.0),
    distance: float = 2.5,
    key_power: float = 400.0,
    fill_power: float = 120.0,
    rim_power: float = 250.0
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """Creates a classic Key/Fill/Rim 3-point light rig."""
    tx, ty, tz = target_co

    def make_light(name: str, loc: Tuple[float, float, float], power: float, radius: float = 0.25):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        if name in bpy.data.lights:
            bpy.data.lights.remove(bpy.data.lights[name], do_unlink=True)
        l_data = bpy.data.lights.new(name, 'POINT')
        l_data.energy = power
        l_data.shadow_soft_size = radius
        l_obj = bpy.data.objects.new(name, l_data)
        l_obj.location = loc
        bpy.context.scene.collection.objects.link(l_obj)
        return l_obj

    # Key light: 45 deg front-right, elevated
    key_obj = make_light("Key_Light", (tx + distance * 0.7, ty - distance * 0.7, tz + distance * 0.8), key_power, radius=0.3)
    # Fill light: 45 deg front-left, lower power
    fill_obj = make_light("Fill_Light", (tx - distance * 0.8, ty - distance * 0.5, tz + distance * 0.4), fill_power, radius=0.5)
    # Rim light: behind subject
    rim_obj = make_light("Rim_Light", (tx - distance * 0.3, ty + distance * 0.9, tz + distance * 0.9), rim_power, radius=0.2)

    return key_obj, fill_obj, rim_obj


def render_still_headless(filepath: str, resolution: Tuple[int, int] = (1280, 720)) -> None:
    """Renders current frame to disk via bpy.ops.render bare headless."""
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    print("Testing bp_render_camera.py headless...")
    scene = bpy.context.scene
    backend = configure_cycles_headless(scene, samples=16, use_denoising=False)
    configure_agx_color_management(scene, view_transform='AgX')
    cam = create_targeted_camera("RenderCam", location=(2.0, -2.0, 1.5), target_point=(0, 0, 0))
    lights = setup_three_point_lighting(target_co=(0, 0, 0), distance=2.5)

    print(f"Cycles backend: {backend}")
    print(f"Active Camera: {scene.camera.name}, Transform: {scene.view_settings.view_transform}")

    # Postconditions: engine/sampling read back, device choice self-consistent with the
    # reported backend, and the evaluated camera actually points at the target.
    assert scene.render.engine == 'CYCLES', scene.render.engine
    assert scene.cycles.samples == 16, scene.cycles.samples
    assert scene.view_settings.view_transform == 'AgX', scene.view_settings.view_transform
    assert scene.cycles.device == ('CPU' if backend == 'CPU' else 'GPU'), (backend, scene.cycles.device)
    assert scene.camera == cam and len(lights) == 3, "camera/lights not established"
    dg = bpy.context.evaluated_depsgraph_get()
    mw = cam.evaluated_get(dg).matrix_world
    forward = (mw.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    to_target = (Vector((0.0, 0.0, 0.0)) - mw.translation).normalized()
    angle = forward.angle(to_target)
    assert angle < 0.01, f"camera off-target by {angle:.4f} rad"
    print(f"Asserts OK: CYCLES/{backend}, device {scene.cycles.device}, aim error {angle:.5f} rad")
    print("bp_render_camera verified successfully.")

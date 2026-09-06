"""Cameras and diagnostic (clay) renders for the capsule. Restores render settings."""
import math
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.abspath(os.path.join(HERE, ".."))
RENDERS = os.path.join(BUILD, "renders")


def camera(name, collection, location, target, lens=85.0, sensor=36.0, ortho_scale=None,
           parent=None):
    """Idempotent camera looking from `location` at `target` (world, metres)."""
    cam = bpy.data.objects.get(name)
    if cam is None:
        data = bpy.data.cameras.new(name + "_cam")
        cam = bpy.data.objects.new(name, data)
    if cam.name not in collection.objects:
        collection.objects.link(cam)
    cam.parent = parent
    d = cam.data
    d.lens = lens
    d.sensor_width = sensor
    d.sensor_fit = "HORIZONTAL"
    d.clip_start = 0.01
    d.clip_end = 20.0
    if ortho_scale:
        d.type = "ORTHO"
        d.ortho_scale = ortho_scale
    else:
        d.type = "PERSP"
    loc, tgt = Vector(location), Vector(target)
    rot = (loc - tgt).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    cam.matrix_world = Matrix.Translation(loc) @ rot
    return cam


def clay_render(scene, cam, path, res_x=1024, res_y=1024, samples=8):
    """Workbench clay still with matcap-free studio light; restores every setting."""
    r = scene.render
    saved = (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage,
             r.filepath, r.image_settings.file_format, r.image_settings.color_mode,
             scene.camera, r.film_transparent)
    shading = scene.display.shading
    saved_sh = (shading.light, shading.color_type, shading.single_color[:],
                shading.show_cavity, shading.show_shadows, shading.show_object_outline,
                scene.display.render_aa)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        r.engine = "BLENDER_WORKBENCH"
        r.resolution_x, r.resolution_y, r.resolution_percentage = res_x, res_y, 100
        r.filepath = path
        r.film_transparent = False
        r.image_settings.file_format = "PNG"
        r.image_settings.color_mode = "RGB"
        scene.camera = cam
        shading.light = "STUDIO"
        shading.color_type = "SINGLE"
        shading.single_color = (0.6, 0.6, 0.6)
        shading.show_cavity = True
        shading.show_shadows = True
        shading.show_object_outline = True
        scene.display.render_aa = "8"
        with bpy.context.temp_override(scene=scene):
            rc = bpy.ops.render.render(write_still=True)
        assert rc == {"FINISHED"}, f"render returned {rc}"
        assert os.path.exists(path), f"no file written: {path}"
        return path
    finally:
        (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage,
         r.filepath, r.image_settings.file_format, r.image_settings.color_mode,
         scene.camera, r.film_transparent) = saved
        (shading.light, shading.color_type, shading.single_color,
         shading.show_cavity, shading.show_shadows, shading.show_object_outline,
         scene.display.render_aa) = saved_sh


def ortho_views(collection, center, radius_m):
    """Front (-Y), side (+X) and top orthographic diagnostic cameras."""
    c = Vector(center)
    d = radius_m * 4.0
    scale = radius_m * 2.6
    return {
        "front": camera("WW_CAM_ORTHO_FRONT", collection, c + Vector((0, -d, 0)), c, ortho_scale=scale),
        "side": camera("WW_CAM_ORTHO_SIDE", collection, c + Vector((d, 0, 0)), c, ortho_scale=scale),
        "top": camera("WW_CAM_ORTHO_TOP", collection, c + Vector((0, 0, d)), c + Vector((0, 0.0001, 0)),
                      ortho_scale=scale),
    }


def concept_view(collection, center, radius_m, azimuth_deg=-32.0, elevation_deg=14.0,
                 lens=85.0, distance=None):
    """Perspective camera approximating the concept hero angle (front-left, slightly above)."""
    c = Vector(center)
    dist = distance or radius_m * 7.5
    a, e = math.radians(azimuth_deg), math.radians(elevation_deg)
    loc = c + Vector((math.sin(a) * math.cos(e) * dist, -math.cos(a) * math.cos(e) * dist,
                      math.sin(e) * dist))
    return camera("WW_CAM_CONCEPT", collection, loc, c, lens=lens)


def _view3d_context():
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                return win, area, region
    return None, None, None


def viewport_to_camera(cam, shading="SOLID"):
    """GUI only: show the owned scene through `cam` in the 3D viewport (no-op headless)."""
    win, area, region = _view3d_context()
    if area is None:
        return False
    space = area.spaces.active
    space.shading.type = shading
    space.overlay.show_overlays = False
    with bpy.context.temp_override(window=win, area=area, region=region, scene=cam.users_scene[0] if cam.users_scene else bpy.context.scene):
        cam.users_scene[0].camera = cam
        if space.region_3d.view_perspective != "CAMERA":
            bpy.ops.view3d.view_camera()
        bpy.ops.view3d.view_center_camera()
    return True


def gui_screenshot(path, max_size=1600):
    """GUI only: offscreen draw of the 3D viewport (same method as the MCP addon;
    window grabs are black/stale when Blender is driven from a timer). Returns path or None."""
    win, area, region = _view3d_context()
    if area is None:
        return None
    import gpu
    import numpy as np
    space = area.spaces.active
    r3d = space.region_3d
    src_w, src_h = region.width, region.height
    s = min(1.0, max_size / max(src_w, src_h))
    width, height = max(1, int(src_w * s)), max(1, int(src_h * s))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene = win.scene
    layer = win.view_layer
    off = gpu.types.GPUOffScreen(width, height)
    try:
        off.draw_view3d(scene, layer, space, region, r3d.view_matrix, r3d.window_matrix,
                        do_color_management=True)
        buf = off.texture_color.read()
    finally:
        off.free()
    buf.dimensions = width * height * 4
    px = np.asarray(buf, dtype=np.float32) / 255.0
    img = bpy.data.images.new("ww_viewport_shot", width, height, alpha=True)
    try:
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
    finally:
        bpy.data.images.remove(img)
    return path if os.path.exists(path) else None


def viewport_marketing_look():
    """Solid shading with material colours so the clay-glass visor reads translucent."""
    win, area, region = _view3d_context()
    if area is None:
        return False
    sh = area.spaces.active.shading
    sh.type = "SOLID"
    sh.color_type = "MATERIAL"
    sh.light = "STUDIO"
    sh.show_cavity = True
    sh.show_shadows = True
    glass = bpy.data.materials.get("WW_clay_glass")
    if glass:
        glass.diffuse_color = (0.75, 0.88, 1.0, 0.35)
    return True

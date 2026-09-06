"""Cycles stills with explicit, restored settings; neutral 3-point studio; device probe."""
import os
import time

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(os.path.abspath(os.path.join(HERE, "..")), "renders")


def denoiser_choice(scene):
    """The denoiser enum is dynamic (enum_items_static is empty here), so probe by assignment."""
    cy = scene.cycles
    current = cy.denoiser
    items = []
    for cand in ("OPENIMAGEDENOISE", "OPTIX"):
        try:
            cy.denoiser = cand
            items.append(cand)
        except TypeError:
            pass
    cy.denoiser = current
    return ("OPENIMAGEDENOISE" if "OPENIMAGEDENOISE" in items else (items[0] if items else None)), items


def cycles_still(scene, cam, path, res_x, res_y, samples, denoise=True, adaptive_threshold=None, time_limit=0.0):
    """Render one Cycles still; every touched setting is restored. Returns (path, seconds, settings)."""
    r, cy, ims = scene.render, scene.cycles, scene.render.image_settings
    saved = (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath, scene.camera,
             cy.samples, cy.use_denoising, cy.denoiser, cy.use_adaptive_sampling, cy.adaptive_threshold, cy.time_limit,
             ims.file_format, ims.color_mode, ims.color_depth, r.film_transparent)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    den, _ = denoiser_choice(scene)
    try:
        r.engine = "CYCLES"
        r.resolution_x, r.resolution_y, r.resolution_percentage = res_x, res_y, 100
        r.filepath, scene.camera, r.film_transparent = path, cam, False
        cy.samples, cy.use_denoising, cy.time_limit = samples, bool(denoise), time_limit
        if den and denoise:
            cy.denoiser = den
        if adaptive_threshold is not None:
            cy.use_adaptive_sampling, cy.adaptive_threshold = True, adaptive_threshold
        ims.file_format, ims.color_mode, ims.color_depth = "PNG", "RGB", "8"
        settings = {"samples": cy.samples, "denoise": cy.use_denoising, "denoiser": cy.denoiser if denoise else None,
                    "adaptive": cy.use_adaptive_sampling, "adaptive_threshold": round(cy.adaptive_threshold, 5),
                    "device": cy.device, "res": [res_x, res_y], "view_transform": scene.view_settings.view_transform,
                    "look": scene.view_settings.look}
        t0 = time.time()
        with bpy.context.temp_override(scene=scene):
            rc = bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        assert rc == {"FINISHED"}, rc
        assert os.path.exists(path) and os.path.getsize(path) > 1000, path
        return path, round(dt, 2), settings
    finally:
        (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath, scene.camera,
         cy.samples, cy.use_denoising, cy.denoiser, cy.use_adaptive_sampling, cy.adaptive_threshold, cy.time_limit,
         ims.file_format, ims.color_mode, ims.color_depth, r.film_transparent) = saved


def area_light(name, collection, location, target, size_x, size_y, energy, color=(1.0, 1.0, 1.0)):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
    if ob.name not in collection.objects:
        collection.objects.link(ob)
    d = ob.data
    d.shape, d.size, d.size_y, d.energy, d.color = "RECTANGLE", size_x, size_y, energy, color
    loc, tgt = Vector(location), Vector(target)
    rot = (loc - tgt).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(loc) @ rot
    ob.hide_render = False
    return ob


def world_grey(scene, strength=0.4, grey=0.5):
    w = scene.world
    nt = w.node_tree
    bg = next((n for n in nt.nodes if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = nt.nodes.new("ShaderNodeBackground")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_WORLD"), None) or nt.nodes.new("ShaderNodeOutputWorld")
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Color"].default_value = (grey, grey, grey, 1.0)
    bg.inputs["Strength"].default_value = strength
    return bg


def probe_devices():
    prefs = bpy.context.preferences.addons.get("cycles")
    if not prefs:
        return {"compute_device_type": None, "devices": []}
    cp = prefs.preferences
    try:
        cp.get_devices()
    except Exception:  # noqa: BLE001
        pass
    return {"compute_device_type": cp.compute_device_type,
            "devices": [(d.name, d.type, d.use) for d in cp.devices]}

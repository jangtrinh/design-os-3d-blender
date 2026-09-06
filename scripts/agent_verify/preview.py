"""preview_render — cheap render gate that restores every setting it touches."""
import os

import bpy

from . import paths

ENGINE_ALIAS = {"EEVEE": "BLENDER_EEVEE", "BLENDER_EEVEE": "BLENDER_EEVEE",
                "CYCLES": "CYCLES", "WORKBENCH": "BLENDER_WORKBENCH"}


def resolve_engine(engine):
    return ENGINE_ALIAS.get(str(engine).upper(), engine)


def preview_render(path=None, res=256, samples=16, engine="EEVEE"):
    """Render a small still and return its path.

    EEVEE is the default: it renders headless on macOS and is the cheapest
    rung of the verify ladder. Every setting written below is captured first
    and restored in `finally` — on success AND on failure.
    """
    sc = bpy.context.scene
    r = sc.render
    ims = r.image_settings
    if path is None:
        path = os.path.join(paths.out_dir("AGENT_PREVIEW_DIR", "output", "previews"),
                            "agent-preview.png")
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    eng = resolve_engine(engine)
    saved = (r.resolution_x, r.resolution_y, r.resolution_percentage,
             r.filepath, r.engine, r.film_transparent,
             ims.file_format, ims.color_mode,
             sc.cycles.samples, sc.eevee.taa_render_samples)
    try:
        r.resolution_x = r.resolution_y = res
        r.resolution_percentage = 100
        r.filepath = path
        r.engine = eng
        ims.file_format = "PNG"
        ims.color_mode = "RGBA"
        if eng == "CYCLES":
            sc.cycles.samples = samples
        else:
            sc.eevee.taa_render_samples = samples
        rc = bpy.ops.render.render(write_still=True)
        assert rc == {"FINISHED"}, f"render returned {rc}"
        assert os.path.exists(path), f"render wrote nothing to {path}"
        return path
    finally:
        (r.resolution_x, r.resolution_y, r.resolution_percentage,
         r.filepath, r.engine, r.film_transparent) = saved[:6]
        ims.file_format, ims.color_mode = saved[6:8]
        sc.cycles.samples, sc.eevee.taa_render_samples = saved[8:]

"""Shared fixture helper: load the lib and snapshot every setting it may touch.

exec'd by the sibling fixtures; not a standalone script.
"""
import json
import os

import bpy

LIB = os.path.join(os.environ["AGENT_REPO_ROOT"], "scripts", "agent-verify-lib.py")
exec(open(LIB).read())  # noqa: S102 — the documented load path under test


def snapshot():
    sc = bpy.context.scene
    r = sc.render
    return {
        "resolution_x": r.resolution_x, "resolution_y": r.resolution_y,
        "resolution_percentage": r.resolution_percentage,
        "filepath": r.filepath, "engine": r.engine,
        "film_transparent": r.film_transparent,
        "file_format": r.image_settings.file_format,
        "color_mode": r.image_settings.color_mode,
        "cycles_samples": sc.cycles.samples,
        "eevee_samples": sc.eevee.taa_render_samples,
        "unit_system": sc.unit_settings.system,
        "scale_length": round(sc.unit_settings.scale_length, 6),
        "fps": r.fps,
        "objects": sorted(o.name for o in bpy.data.objects),
    }


def emit(**kw):
    print("RESULT " + json.dumps(kw))

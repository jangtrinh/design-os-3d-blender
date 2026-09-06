"""Session setup that reports before it writes, and checkpointing."""
import os

import bpy

from . import paths
from .preview import resolve_engine

# Blender 5.2.0 factory-startup values. A setting still holding its factory
# default is treated as "unset"; anything else is the user's/build's choice.
FACTORY = {"unit_system": "METRIC", "scale_length": 1.0,
           "engine": "BLENDER_EEVEE", "fps": 24}

DEFAULT_COLLECTIONS = ("ASSETS", "LIGHTS", "CAMERAS", "HELPERS")


def _record(report, key, cur, want, setter, force):
    changed = False
    if cur != want and (force or cur == FACTORY[key]):
        setter(want)
        changed = True
    report[key] = {"before": cur, "after": want if changed else cur,
                   "changed": changed}


def scaffold(force=False, unit_scale=1.0, engine="CYCLES", fps=24,
             collections=DEFAULT_COLLECTIONS):
    """Non-destructive session scaffold.

    Reads units / engine / fps / collections and returns
    {setting: {"before", "after", "changed"}}. A setting is written only when
    it still holds its factory default, or when force=True. Nothing is ever
    removed, and the scene is never reset — see
    knowledge/60-pipeline/scene-organization.md for the resetting variant.
    """
    sc = bpy.context.scene
    us = sc.unit_settings
    r = sc.render
    rep = {}
    _record(rep, "unit_system", us.system, "METRIC",
            lambda v: setattr(us, "system", v), force)
    _record(rep, "scale_length", us.scale_length, unit_scale,
            lambda v: setattr(us, "scale_length", v), force)
    _record(rep, "engine", r.engine, resolve_engine(engine),
            lambda v: setattr(r, "engine", v), force)
    _record(rep, "fps", r.fps, fps, lambda v: setattr(r, "fps", v), force)
    before = sorted(c.name for c in sc.collection.children)
    for name in collections:
        col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if col.name not in sc.collection.children:
            sc.collection.children.link(col)
    after = sorted(c.name for c in sc.collection.children)
    rep["collections"] = {"before": before, "after": after,
                          "changed": before != after}
    sc["agent_blender_version"] = list(bpy.app.version)
    return rep


def checkpoint(tag, root=None):
    """Only rollback we have — save before destructive ops (booleans, applies)."""
    root = root or paths.out_dir("AGENT_CHECKPOINT_DIR", "output", "checkpoints")
    os.makedirs(root, exist_ok=True)
    p = os.path.join(root, f"{tag}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, copy=True)
    return p

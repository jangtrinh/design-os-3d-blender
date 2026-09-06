"""Agent sense organs — numeric verification helpers for bpy sessions.

Safety classes:
  read-only  assert_exists, tri_count, world_bbox, has_material, framing,
             frame_stats
  restoring  preview_render — restores every setting it touches, on success
             and on failure
  isolated   verify_export — re-imports in a separate headless Blender; the
             live scene is never touched
  mutating   scaffold (opt-in writes only, never deletes), checkpoint (writes
             a .blend copy), import_any (imports into the current scene)

Rule: if a question can be answered by a number, never spend a screenshot on it.
"""
from .export_check import import_any, verify_export
from .inspect_scene import (assert_exists, frame_stats, framing, has_material,
                            tri_count, world_bbox)
from .paths import lib_sha, repo_root
from .preview import preview_render
from .session import checkpoint, scaffold

__all__ = ["assert_exists", "tri_count", "world_bbox", "has_material",
           "framing", "frame_stats", "preview_render", "verify_export",
           "import_any", "scaffold", "checkpoint", "repo_root", "lib_sha"]

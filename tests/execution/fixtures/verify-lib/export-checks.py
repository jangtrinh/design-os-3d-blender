"""verify_export: missing file raises, real glb passes, live scene untouched."""
import os

import bpy

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "state-snapshot.py")).read())

tmp = os.environ["AGENT_PREVIEW_DIR"]
glb = os.path.join(tmp, "cube.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB")

# unsaved work that must survive both calls
bpy.data.objects.new("UNSAVED_WORK", None)
bpy.context.scene.collection.objects.link(bpy.data.objects["UNSAVED_WORK"])

before = snapshot()
missing_raised = None
try:
    verify_export(os.path.join(tmp, "no-such-file.glb"), 1, 1)
except Exception as exc:
    missing_raised = type(exc).__name__
after_missing = snapshot()

ok = verify_export(glb, 1, 12)
after_ok = snapshot()

emit(before=before, after_missing=after_missing, after_ok=after_ok,
     missing_raised=missing_raised, report=ok, glb_exists=os.path.exists(glb))

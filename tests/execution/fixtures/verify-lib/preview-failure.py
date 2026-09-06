"""preview_render with no camera: raises, and restores everything anyway."""
import os

import bpy

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "state-snapshot.py")).read())

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 960, 720
sc.render.resolution_percentage = 50
sc.render.filepath = "/tmp/ORIGINAL_OUTPUT_"
sc.render.engine = "CYCLES"
sc.cycles.samples = 99
sc.eevee.taa_render_samples = 77
sc.render.image_settings.file_format = "JPEG"

for cam in [o for o in bpy.data.objects if o.type == "CAMERA"]:
    bpy.data.objects.remove(cam, do_unlink=True)
sc.camera = None

before = snapshot()
raised = None
try:
    preview_render(path=os.path.join(os.environ["AGENT_PREVIEW_DIR"], "fail.png"),
                   res=64, samples=4)
except Exception as exc:
    raised = type(exc).__name__
after = snapshot()

emit(before=before, after=after, raised=raised)

"""preview_render success: settings restored, image real, repeat-safe."""
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
sc.render.film_transparent = True

before = snapshot()
out_dir = os.path.join(os.environ["AGENT_PREVIEW_DIR"], "does-not-exist-yet")
p1 = preview_render(path=os.path.join(out_dir, "p1.png"), res=128, samples=8)
mid = snapshot()
p2 = preview_render(res=128, samples=8)  # default path, second call in a row
after = snapshot()
stats = frame_stats(p1)

emit(before=before, mid=mid, after=after,
     path1=p1, path2=p2,
     exists1=os.path.exists(p1), exists2=os.path.exists(p2),
     default_under_env=os.path.abspath(p2).startswith(
         os.path.abspath(os.environ["AGENT_PREVIEW_DIR"])),
     stdev=stats["stdev"], mean=stats["mean"])

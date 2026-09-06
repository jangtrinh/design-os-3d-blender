"""scaffold: non-factory settings survive unless force=True."""
import os

import bpy

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "state-snapshot.py")).read())

sc = bpy.context.scene
sc.unit_settings.scale_length = 0.5
sc.render.fps = 30
sc.render.engine = "CYCLES"

before = snapshot()
soft = scaffold()
after_soft = snapshot()
hard = scaffold(force=True, unit_scale=1.0, engine="CYCLES", fps=24)
after_hard = snapshot()

emit(before=before, soft=soft, after_soft=after_soft,
     hard=hard, after_hard=after_hard)

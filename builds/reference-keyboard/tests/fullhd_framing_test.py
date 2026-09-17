"""Actual saved-scene camera regression, with no rendering or source writes."""
from pathlib import Path
import hashlib
import sys

import bpy
from mathutils import Vector

BUILD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BUILD/'scripts'))
import fullhd,studio
from agent_verify import framing
from agent_runtime import emit_ok

assert bpy.app.background and Path(bpy.data.filepath).is_file()
source=Path(bpy.data.filepath)
before=hashlib.sha256(source.read_bytes()).hexdigest()
sc=bpy.context.scene
sc.frame_set(1)
sc.render.resolution_x,sc.render.resolution_y=1920,1080
sc.render.resolution_percentage=100
rows=[]
for name,scale in [('RK_KEY_00',.039),('RK_KEY_41',.061),('RK_KNOB_5',.037)]:
    obj=bpy.data.objects[name]
    origin=obj.matrix_world.translation.copy()
    settings={'subjects':[name], 'location':tuple(origin+Vector((.018,-.025,-.038))),
              'target':tuple(origin+Vector((0,0,.005))),'scale':scale}
    studio.aim(**{k:v for k,v in settings.items() if k!='subjects'})
    old=framing(obj)['in_frame']
    fitted=fullhd.fit_subjects(settings)
    studio.aim(**{k:v for k,v in fitted.items() if k!='subjects'})
    assert framing(obj)['in_frame'],name
    if name=='RK_KNOB_5':
        assert not old,'original 16:9 crop must be reproduced'
        assert fitted['scale']>scale
    rows.append({'object':name,'original_in_frame':old,'fitted_scale':fitted['scale']})
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
emit_ok('FullHD-detail-framing',scene_sha256=before,shots=rows,source_unchanged=True)

"""Real-scene normal finish and preview; interfaces must remain byte-identical."""
from pathlib import Path
import hashlib
import sys

import bpy

BUILD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BUILD/'scripts'))
import studio
from project import write
from agent_runtime import emit_ok

assert bpy.app.background and Path(bpy.data.filepath).is_file()
source=Path(bpy.data.filepath)
before=hashlib.sha256(source.read_bytes()).hexdigest()
out=BUILD/'runs/control-finish-proof-B01'
out.mkdir(exist_ok=False)
counts=studio.finish_control_normals()
assert counts['meshes']>=7 and counts['smooth_faces']>0 and counts['sharp_edges']>0,counts
bpy.context.scene.frame_set(1)
bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y=512,288
bpy.context.scene.cycles.samples=16
capture=studio.capture(out/'knob.png',subjects=['RK_KNOB_5'],location=(.16,-.10,.11),target=(.125,-.012,.021),scale=.048)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
write(out/'result.json',{'source_sha256':before,'normal_finish':counts,'capture':capture,'source_unchanged':True})
emit_ok('control-normal-finish',**counts,source_unchanged=True)

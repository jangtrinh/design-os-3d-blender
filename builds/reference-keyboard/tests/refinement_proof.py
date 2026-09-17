"""Cheap revision-B visual inspection of the loaded geometry, not delivery media."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from project import BUILD,sha,write
import bpy
import studio,meshkit as g
from agent_runtime import emit_ok

assert bpy.app.background and bpy.data.filepath
source=Path(bpy.data.filepath)
out=BUILD/'runs/inspection-B01'
out.mkdir(exist_ok=False)
palette=studio.palette()
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or not obj.name.startswith('RK_'): continue
    name=obj.name
    role=('key' if name.startswith('RK_KEY_') else 'silver' if name.startswith(('RK_KNOB_','RK_ENCODER_')) or name=='RK_BASE'
          else 'diffuser' if name=='RK_DIFFUSER' else 'black')
    g.assign(obj,palette[role])
studio.setup()
bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y=512,288
view=studio.capture(out/'geometry-proof.png',scale=.365)
write(out/'proof.json',{'source':str(source),'scene_sha256':sha(source),'view':view,
                      'purpose':'cheap geometry inspection while failed gate is being repaired; not delivery'})
emit_ok('refinement-visual-proof',views=1,width=512,height=288)

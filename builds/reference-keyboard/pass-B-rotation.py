"""Prove exported D-shaft/knob rotation at a nonzero pose, beyond press/explosion frames."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import output_context,write,sha
import bpy
from export_compare import capture_source,compare
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
source=next(v for k,v in inputs['project'].items() if k.endswith('/keyboard.blend'))
glb=next(v for k,v in inputs['project'].items() if k.endswith('/keyboard.glb'))
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
bpy.context.scene.frame_set(18)
graph=bpy.context.evaluated_depsgraph_get()
intent=[]
for i in range(1,6):
    knob=bpy.data.objects['RK_KNOB_%d'%i].evaluated_get(graph)
    shaft=bpy.data.objects['RK_ENCODER_SHAFT_%d'%i].evaluated_get(graph)
    assert knob.rotation_euler.z>.79 and abs(knob.rotation_euler.z-shaft.rotation_euler.z)<1e-7
    intent.append({'index':i,'knob_radians':knob.rotation_euler.z,'shaft_radians':shaft.rotation_euler.z})
names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('RK_')]
surface=capture_source(names,(18,))
surface['blend_sha256']=sha(source)
write(out/'rotation-source.json',surface)
write(out/'rotation-intent.json',{'scene_sha256':sha(source),'frame':18,'pairs':intent})
result=compare(out/'rotation-source.json',glb,out/'rotation-roundtrip.json')
assert result['pass'],'Nonzero rotation did not survive GLB roundtrip'
emit_ok('reference-keyboard-rotation-roundtrip',frame=18,encoder_pairs=5,mesh_names=len(names),
        max_error_mm=max(o['surface_max_error_mm'] for o in result['frames']['18']['objects']))

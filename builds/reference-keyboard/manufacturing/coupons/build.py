"""Build masters at local origins and an arranged inspection display of the same meshes."""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
BUILD=HERE.parents[1]
sys.path[:0]=[str(HERE),str(BUILD/'scripts'),str(BUILD.parents[1]/'scripts')]
from project import output_context,write,sha
from agent_runtime import emit_ok
import bpy
import shapes

assert bpy.app.background
out,inputs=output_context()
cfg=json.loads((HERE/'contract.json').read_text())
specimens=json.loads((HERE/'specimens.json').read_text())
scene=bpy.data.scenes.new('CK001_PROCESS_SPECIMENS')
bpy.context.window.scene=scene
scene.unit_settings.system,scene.unit_settings.scale_length='METRIC',1.0
scene.unit_settings.length_unit='MILLIMETERS'
measurements=[]
for i,row in enumerate(specimens):
    obj=shapes.build(row,cfg)
    result=shapes.measure(obj,row)
    obj.hide_render=True
    obj.hide_set(True)
    copy=bpy.data.objects.new('PROOF_'+obj.name,obj.data)
    scene.collection.objects.link(copy)
    copy.location=((i%4)*.024,(i//4)*.024,0)
    result['display_xy_mm']=[copy.location.x*1000,copy.location.y*1000]
    measurements.append(result)
write(out/'measurements.json',{'contract_sha256':sha(HERE/'contract.json'),
                              'specimens':measurements,'physical_results':None,
                              'scope':'Native dimensions only; no physical specimen fabricated'})
assert bpy.ops.wm.save_as_mainfile(filepath=str(out/'specimens.blend'))=={'FINISHED'}
emit_ok('manufacturing-fit-specimens',specimens=len(specimens),measured_interfaces=len(measurements))

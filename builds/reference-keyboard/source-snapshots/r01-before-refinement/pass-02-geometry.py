"""Construct the detailed native assembly before adding presentation materials."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import layout,key_rows,output_context,write,ROOT
import bpy
import json
import controls,mechanics,switches,meshkit as g
from agent_runtime import emit_ok
from boilerplates.bp_parametric_contract import normalize_contract,bind_source_evidence

assert bpy.app.background
out,inputs=output_context()
mechanics.CHECKPOINTS=out/'checkpoints'
sc=bpy.data.scenes.new('CK_001_NATIVE')
bpy.context.window.scene=sc
sc.unit_settings.system,sc.unit_settings.scale_length='METRIC',1
sc.unit_settings.length_unit='MILLIMETERS'
data=layout()
normalized=normalize_contract(json.loads((Path(__file__).resolve().parent/'dimensions-contract.json').read_text()))
assert abs(normalized['parameters']['width_mm']['values_si']['value']-.284)<1e-9
rows=key_rows(data)
parts=mechanics.chassis(data,rows)
mechanics.spacers_and_screws(data)
switches.build(rows)
template=controls.keycap('TEMP_KEY_TEMPLATE')
wide=controls.keycap('TEMP_SPACE_TEMPLATE',width_m=(14+data['pitch_x_mm'])/1000)
for row in rows:
    source=wide if row['units']==2 else template
    obj=bpy.data.objects.new(row['id'],source.data)
    sc.collection.objects.link(obj)
    obj.location=(*[v/1000 for v in row['xy_mm']],.0175)
    obj['label'],obj['key_group']=row['label'],row['group']
    obj['functional_interface']='NOT_QUALIFIED'
for obj in (template,wide):bpy.data.objects.remove(obj,do_unlink=True)
for i,xy in enumerate(data['knobs_mm']):
    obj=controls.knob('RK_KNOB_%d'%(i+1),mount_neck_m=.0031,neck_radius_m=.0042)
    obj.location=(*[v/1000 for v in xy],.012)
for i,(x,y) in enumerate(((-.125,-.034),(.125,-.034),(-.125,.034),(.125,.034))):
    g.slab('RK_FOOT_%d'%i,.014,.005,.002,-.002,0,(x,y))
measurements={'objects':[g.numeric(o) for o in sc.objects if o.type=='MESH' and o.name.startswith('RK_')]}
for row in measurements['objects']:
    if row['name'].startswith('RK_KEY_'):
        obj=bpy.data.objects[row['name']]
        z=max(v.co.z for v in obj.data.vertices)
        points=[obj.matrix_world@v.co for v in obj.data.vertices if abs(v.co.z-z)<1e-7]
        row['top_bbox_mm']=[[min(p[i] for p in points)*1000 for i in range(2)],
                            [max(p[i] for p in points)*1000 for i in range(2)]]
write(out/'geometry.json',measurements)
write(out/'source-inputs.json',inputs)
write(out/'source-evidence.json',bind_source_evidence(normalized,list(inputs['project']),ROOT))
write(out/'contract.json',normalized)
assert bpy.ops.wm.save_as_mainfile(filepath=str(out/'model.blend'))=={'FINISHED'}
emit_ok('reference-keyboard-geometry',keys=len(rows),knobs=5,mesh_objects=len(measurements['objects']),
        gn_width_change_m=bpy.data.objects['RK_SWITCH_HOUSINGS']['gn_measured_width_change_m'])

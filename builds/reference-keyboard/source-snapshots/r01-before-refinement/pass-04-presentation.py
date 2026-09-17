"""Add native finish, readable legends and bounded motion after the form gate."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import ROOT,BUILD,layout,key_rows,output_context,write,sha
import bpy
import studio,details,motion,meshkit as g
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
source=inputs['project'][next(k for k in inputs['project'] if k.endswith('/model.blend'))]
gate_path=inputs['project'][next(k for k in inputs['project'] if k.endswith('/gate-report.json'))]
gate=json.loads(Path(gate_path).read_text())
assert not gate['failed'] and not gate['required_checks_missing']
assert gate['inputs']['scene_sha256']==sha(source),'gate is bound to another scene'
assert gate['inputs']['spec_sha256']==sha(BUILD/'spec.json'),'gate is bound to another spec'
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
materials=studio.palette()
for obj in bpy.context.scene.objects:
    if obj.type!='MESH': continue
    n=obj.name
    role=('silver' if n=='RK_BASE' or n.startswith('RK_KNOB_') else
          'diffuser' if n=='RK_DIFFUSER' else 'key' if n.startswith('RK_KEY_') else
          'rubber' if n.startswith('RK_FOOT_') else 'gold' if n.startswith(('RK_CONTACT_','RK_SPACER_')) else
          'black' if n=='RK_MAIN_PLATE' or n.startswith('RK_SCREW_') else 'switch')
    g.assign(obj,materials[role])
transparent=studio.material('RK_Switch_cover',(.4,.44,.45),0,.18)
transparent.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=.55
orange=studio.material('RK_Switch_stem',(.65,.17,.035),0,.36)
for obj in bpy.context.scene.objects:
    if obj.name.startswith('RK_SWITCH_TOP_'): g.assign(obj,transparent)
    if obj.name.startswith('RK_SWITCH_STEM_'): g.assign(obj,orange)
details.rgb_texture(bpy.data.objects['RK_DIFFUSER'],materials,out)
details.legends(key_rows(),materials)
details.electronics(materials)
motion_manifest=motion.setup()
motion_report=motion.verify()
write(out/'motion-contract.json',motion_manifest)
write(out/'motion-report.json',motion_report)
studio.setup()
views={'hero':studio.capture(out/'hero.png'),
       'top':studio.capture(out/'top.png',location=(0,0,.5),target=(0,0,0),scale=.32)}
views['knob-detail']=studio.capture(out/'knob-detail.png',subjects=['RK_KNOB_5'],
                                    location=(.16,-.10,.11),target=(.125,-.012,.021),scale=.048)
views['key-detail']=studio.capture(out/'key-detail.png',subjects=['RK_KEY_15'],
                                   location=(-.067,-.095,.125),target=(-.050,-.001,.022),scale=.060)
ground=bpy.data.objects['STUDIO_GROUND']
ground.hide_render=True
try:
    views['bottom']=studio.capture(out/'bottom.png',location=(0,0,-.4),target=(0,0,0),scale=.32)
finally:
    ground.hide_render=False
bpy.context.scene.frame_set(60)
views['exploded']=studio.capture(out/'exploded.png',location=(.30,-.43,.33),target=(0,0,.037),scale=.405)
bpy.context.scene.frame_set(1)
studio.aim()
write(out/'views.json',views)
write(out/'provenance.json',{'source_blend':source,'source_sha256':sha(source),'form_gate':gate_path,
                            'form_gate_sha256':sha(gate_path),'declared_inputs':inputs['project'],
                            'limits':['Presentation and motion candidate, final gate/export/review still required.']})
assert bpy.ops.wm.save_as_mainfile(filepath=str(out/'keyboard.blend'))=={'FINISHED'}
emit_ok('reference-keyboard-presentation',meshes=sum(o.type=='MESH' and o.name.startswith('RK_') for o in bpy.context.scene.objects),
        legends=sum(o.name.startswith('RK_LEGEND_') for o in bpy.context.scene.objects),
        sampled_frames=motion_report['sampled_frames'],drivers=58,views=len(views))

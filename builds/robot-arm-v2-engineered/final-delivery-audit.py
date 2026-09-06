"""Final saved-artifact checks, hardware census and honest release status."""
from pathlib import Path
import bpy,bmesh,json,csv,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
for script in ['check-operating-envelope.py','collision-screen.py']:
    exec(compile((ROOT/script).read_text(),str(ROOT/script),'exec'),{'__file__':str(ROOT/script)})
sc=bpy.data.scenes['ARM2-Assembled'];bpy.context.window.scene=sc
rows=[]
for ob in sc.objects:
    if ob.type!='MESH':continue
    rows.append({'name':ob.name,'type':ob.get('part_type',''),'spec':ob.get('assembly_hardware',ob.get('model','')),
      'material':ob.data.materials[0].name if ob.data.materials else '',
      'procurement_gate':ob.get('procurement_gate',ob.get('hardware_note',''))})
with (ROOT/'reports/component-register.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
joint=bpy.data.objects['A2-J06-gripper'];saved=joint.rotation_euler.copy();errors=[]
heads=[o for o in sc.objects if o.name.startswith('A2-moving-jaw-bolt-') and o.name.endswith('-head')]
horn=bpy.data.objects['A2-gripper-output-1'];assert horn.parent==joint
for angle in [-16,0,12]:
    joint.rotation_euler.y=math.radians(angle);bpy.context.view_layer.update()
    for h in heads:
        p=joint.matrix_world.inverted()@h.matrix_world.translation
        errors.append(min(math.hypot(p.x*1000-x,p.z*1000-z) for x,z in [(7,0),(-7,0),(0,7),(0,-7)]))
joint.rotation_euler=saved;bpy.context.view_layer.update()
assert len(heads)==4 and max(errors)<.001
hand={'case_retainer_present':bpy.data.objects.get('A2-hand-case-retainer') is not None,
 'jaw_bolt_count':len(heads),'tested_jaw_angles_deg':[-16,0,12],
 'max_bolt_axis_offset_mm':max(errors),'moving_jaw_modeled_thread_overlap_mm':1.4,
 'tool_lock_nut_count':sum(o.name.startswith('A2-tool-lock-nut-') for o in sc.objects),
 'limit':'axis alignment is verified; pullout, spline engagement, pressure distribution and thermal hold are not'}
assert hand['tool_lock_nut_count']==4
anim=bpy.data.scenes['ARM2-Motion-and-assembly'];state=[]
for frame in [1,384]:
    anim.frame_set(frame);bpy.context.view_layer.update()
    state.append({o.name:tuple(v for row in o.matrix_world for v in row) for o in anim.objects})
return_error=max(abs(a-b) for n in state[0] for a,b in zip(state[0][n],state[1][n]))
assert return_error<1e-6
anim.frame_set(1)
manifest=json.loads((ROOT/'reports/print-prototype-manifest.json').read_text())
for r in manifest['parts']:assert max(r['dimensions_mm'][:2])<=220
result={'release_status':'BLOCKED_FOR_MANUFACTURE','hand':hand,'animation_return_max_matrix_error':return_error,
 'prototype_stl_count':len(manifest['parts']),'bed_220mm_bounds_pass':True,
 'blockers':['Wrist-pitch gravity demand with 50g reserve and factor1.5 exceeds published rated torque.',
 'C01825T / idler adapters are custom geometry; exact spline and supplier-compatible parts remain unverified.',
 'SM105 output M3 usable thread depth is absent from official drawing; modeled M3x6 must not be ordered from visualization alone.',
 'Full-motion collision sweep including all fasteners, printed joint fatigue/creep and 250g multi-minute thermal hold are not validated.',
 'Base requires actual M6 anchors or a designed table clamp; the arm is not a free-standing payload design.']}
(ROOT/'reports/final-delivery-audit.json').write_text(json.dumps(result,indent=2))
print('AGENT_OK final digital checks',json.dumps(result))

from pathlib import Path
import bpy,json,runpy,math
from mathutils import Vector,Matrix
from bpy_extras.anim_utils import action_get_channelbag_for_slot
ROOT=Path(__file__).resolve().parents[1];h=runpy.run_path(str(ROOT/'scripts/studio-helpers.py'));order=runpy.run_path(str(ROOT/'scripts/assembly-order.py'))
source=bpy.data.scenes['A3-Frozen-source'];assert not bpy.data.scenes.get('A3-Step-assembly')
sc=bpy.data.scenes.new('A3-Step-assembly');sc.world=source.world.copy();sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
bpy.context.window.scene=sc;groups={};records=[]
for o in source.objects:
 if o.get('tool_library'):continue
 group,step=order['classify'](o)
 if group not in groups:
  empty=bpy.data.objects.new('A3-assembly-'+group,None);sc.collection.objects.link(empty);groups[group]={'root':empty,'objects':[]}
 cp=o.copy();cp.name=o.name.replace('A3-src-','A3-build-');cp.animation_data_clear();sc.collection.objects.link(cp)
 cp.parent=groups[group]['root'];cp.matrix_parent_inverse=Matrix.Identity(4);cp.matrix_basis=o.matrix_world.copy()
 cp['assembly_group']=group;cp['assembly_step']=step;groups[group]['objects'].append(cp)
 records.append({'object':cp.name,'source':o.name,'group':group,'step':step,'final_matrix':[list(r) for r in o.matrix_world]})
assert len(records)==402,len(records)
def bounds(objects):
 pts=[o.matrix_basis@Vector(v) for o in objects for v in o.bound_box]
 lo=Vector(tuple(min(v[k] for v in pts) for k in range(3)));hi=Vector(tuple(max(v[k] for v in pts) for k in range(3)))
 return (lo+hi)/2,hi-lo
allobjects=[o for g in groups.values() for o in g['objects']];full_center,full_size=bounds(allobjects)
cam=h['camera'](sc,(.7,-1.4,.9),full_center,.78);cam.rotation_mode='QUATERNION'
h['lighting'](sc);sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.fps=24;sc.cycles.samples=6
sc.render.use_persistent_data=True;sc.frame_start=1
floor=h['material']('A3-stage-floor',(.075,.085,.095));h['box'](sc,'A3-stage',(5,5,.012),(0,0,-.008),floor)
clock=25;events=[];chapters=[]
for group in ['base','shoulder','elbow','wrist','hand','finish']:
 g=groups[group];obs=g['objects'];center,size=bounds(obs);start=clock
 offset=Vector((0,0,0)) if group in ['base','finish'] else Vector((.34,-.03,.24))-center
 g['root'].location=offset;g['root'].keyframe_insert('location',frame=1)
 late=14 if group in ['shoulder','elbow','wrist'] else 9 if group=='hand' else 999
 steps=sorted({o['assembly_step'] for o in obs})
 def animate_step(step):
  global clock
  selected=[o for o in obs if o['assembly_step']==step];duration=16 if any(o.get('part_type')=='print' for o in selected) else 12
  for j,o in enumerate(selected):
   anchor=o
   if '-output' in o.name:
    owner=sc.objects.get(o.name.split('-output')[0]+'-servo')
    if owner in selected:anchor=owner
   final=o.location.copy();local_delta=Vector(anchor.get('explode_mm',(0,0,0)))*.001
   delta=anchor.matrix_basis.to_3x3().normalized()@local_delta
   if delta.length<.005:
    dy=anchor.location.y-center.y
    delta=Vector((0,(-1 if dy<=0 else 1)*.055,.045))
   else:delta=delta.normalized()*.07
   o.location=final+delta;o.keyframe_insert('location',frame=clock)
   o.location=final;o.keyframe_insert('location',frame=clock+duration)
   for f,hidden in [(1,True),(clock-1,True),(clock,False)]:
    o.hide_render=hidden;o.hide_viewport=hidden;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
   rec=next(r for r in records if r['object']==o.name);rec.update(start=clock,end=clock+duration)
  events.append({'group':group,'step':step,'start':clock,'end':clock+duration,'objects':[o.name for o in selected]});clock+=duration+4
 for step in [s for s in steps if s<late]:animate_step(step)
 transfer_start=clock;g['root'].location=offset;g['root'].keyframe_insert('location',frame=clock)
 clock+=28 if offset.length else 10;g['root'].location=(0,0,0);g['root'].keyframe_insert('location',frame=clock)
 transfer_end=clock;clock+=6
 for step in [s for s in steps if s>=late]:animate_step(step)
 chapters.append({'group':group,'start':start,'transfer_start':transfer_start,'transfer_end':transfer_end,'end':clock,'focus':list(center+offset),'size':max(size),'offset':list(offset)})
 sc.timeline_markers.new(group.upper(),frame=start)
sc.frame_end=clock+72
for ob in [*allobjects,*[g['root'] for g in groups.values()]]:
 if not ob.animation_data:continue
 cb=action_get_channelbag_for_slot(ob.animation_data.action,ob.animation_data.action_slot)
 for fcu in cb.fcurves:
  for key in fcu.keyframe_points:
   if fcu.data_path=='location':key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
(ROOT/'reports/assembly-timeline.json').write_text(json.dumps({'scene':sc.name,'fps':24,'frames':sc.frame_end,'chapters':chapters,'events':events,'objects':records,'full_center':list(full_center),'full_size':list(full_size),'limits':'Authored order/placement; source retention and tool-access gaps remain. No continuous installation collision or physical validation.'},indent=2))
sc['release']='Assembly presentation / fit prototype, not physical assembly approval';sc.frame_set(sc.frame_end);bpy.context.view_layer.update()
maxerr=max(max(abs(o.matrix_world[a][b]-source.objects[r['source']].matrix_world[a][b]) for a in range(4) for b in range(4)) for r in records for o in [sc.objects[r['object']]])
assert maxerr<1e-6,maxerr
bpy.data.libraries.write(str(ROOT/'arm-step-assembly.blend'),{sc},fake_user=True,compress=True)
print('AGENT_OK',json.dumps({'objects':len(records),'frames':sc.frame_end,'events':len(events),'final_matrix_error':maxerr}))

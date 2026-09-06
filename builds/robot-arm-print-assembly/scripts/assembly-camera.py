from pathlib import Path
import bpy,json,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'reports/assembly-timeline.json').read_text());sc=bpy.data.scenes[m['scene']];bpy.context.window.scene=sc
cam=sc.camera;full=Vector(m['full_center']);fullscale=max(m['full_size'])*1.68;direction=Vector((.55,-1,.60)).normalized()
cam.animation_data_clear();cam.data.animation_data_clear();cam.rotation_mode='QUATERNION'
q=(-direction).to_track_quat('-Z','Y');inv=q.inverted()
def transfer_fit(chapter):
 points=[]
 for r in m['objects']:
  if r['start']>chapter['transfer_start']:continue
  ob=sc.objects[r['object']];offset=Vector(chapter['offset']) if r['group']==chapter['group'] else Vector((0,0,0))
  for v in ob.bound_box:
   from mathutils import Matrix
   points.append(inv@(Matrix(r['final_matrix'])@Vector(v)+offset))
   points.append(inv@(Matrix(r['final_matrix'])@Vector(v)))
 lo=Vector(tuple(min(v[k] for v in points) for k in range(3)));hi=Vector(tuple(max(v[k] for v in points) for k in range(3)))
 return q@((lo+hi)/2),max(fullscale,(hi.y-lo.y)*1.18,(hi.x-lo.x)*.75*1.18)
fits={c['group']:transfer_fit(c) for c in m['chapters']}
def smooth(t):t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
for frame in range(1,sc.frame_end+1):
 chapter=next((c for c in m['chapters'] if c['start']<=frame<=c['end']),None)
 if chapter:
  focus=Vector(chapter['focus']);scale=max(.23,chapter['size']*1.85)
  if chapter['group']=='finish':focus=full;scale=fullscale
  a=smooth((frame-chapter['transfer_start']+10)/18)
  transfer_center,transfer_scale=fits[chapter['group']]
  focus=focus.lerp(transfer_center,a);scale=scale*(1-a)+transfer_scale*a
  b=smooth((frame-chapter['transfer_end'])/6)
  focus=focus.lerp(full,b);scale=scale*(1-b)+fullscale*b
 else:focus=full;scale=fullscale
 cam.location=focus+direction*1.6;cam.rotation_quaternion=(focus-cam.location).to_track_quat('-Z','Y');cam.data.ortho_scale=scale
 cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame);cam.data.keyframe_insert('ortho_scale',frame=frame)
# Start at first actual base-piece arrival; video does not open on an empty stage.
sc.frame_start=25;frames=[e['end'] for e in m['events']];bad=[]
for frame in frames:
 sc.frame_set(frame);bpy.context.view_layer.update()
 event=next(e for e in m['events'] if e['end']==frame)
 for name in event['objects']:
  ob=sc.objects[name]
  for v in ob.bound_box:
   q=world_to_camera_view(sc,cam,ob.matrix_world@Vector(v))
   if q.z<=0 or not -.005<=q.x<=1.005 or not -.005<=q.y<=1.005:bad.append((frame,name));break
assert not bad,bad[:10]
for chapter in m['chapters']:
 for frame in range(chapter['transfer_start']+8,chapter['transfer_end']+1):
  sc.frame_set(frame);bpy.context.view_layer.update()
  for r in m['objects']:
   ob=sc.objects[r['object']]
   if ob.hide_render:continue
   for v in ob.bound_box:
    xy=world_to_camera_view(sc,cam,ob.matrix_world@Vector(v))
    assert 0<=xy.x<=1 and 0<=xy.y<=1,(frame,ob.name,tuple(xy))
sc.frame_set(sc.frame_end);bpy.context.view_layer.update()
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.data.libraries.write(str(ROOT/'arm-step-assembly.blend'),{sc},fake_user=True,compress=True)
(ROOT/'reports/camera-check.json').write_text(json.dumps({'checked_endpoints':len(frames),'outside':bad,'frame_range':[sc.frame_start,sc.frame_end],'predicate':'Every arriving group bounding box inside camera at its seated endpoint; chapter closeups intentionally exclude other modules.'},indent=2))
print('AGENT_OK camera',len(frames),'event endpoints')

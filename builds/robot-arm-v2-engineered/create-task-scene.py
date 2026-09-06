"""Natural task demonstration on the preserved revised native robot geometry."""
from pathlib import Path
import bpy,math,json
from bpy_extras import anim_utils
ROOT=Path(__file__).resolve().parent
p=ROOT/'task-motion-plan.py';exec(compile(p.read_text(),str(p),'exec'),{'__file__':str(p)})
plan=json.loads((ROOT/'reports/task-motion-plan.json').read_text())
source=bpy.data.scenes['ARM2-Assembled'];old=bpy.data.scenes.get('ARM2-Task-demo')
if old:
    for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.scenes.remove(old)
sc=bpy.data.scenes.new('ARM2-Task-demo');mapping={}
for ob in source.objects:
    cp=ob.copy();cp.animation_data_clear();cp.name=ob.name+'-task'
    if ob.type in ['CAMERA','LIGHT']:cp.data=ob.data.copy()
    sc.collection.objects.link(cp);mapping[ob]=cp
for ob,cp in mapping.items():cp.parent=mapping.get(ob.parent)
sc.camera=mapping[source.camera];sc.world=source.world
sc.render.engine='CYCLES';sc.cycles.samples=6;sc.cycles.use_denoising=True
sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.fps=24;sc.frame_start=1;sc.frame_end=720
bpy.context.window.scene=sc
names=['J01-yaw','J02-shoulder','J03-elbow','J04-wrist-pitch','J05-wrist-roll','J06-gripper']
for i,name in enumerate(names):
    ob=mapping[bpy.data.objects['A2-'+name]];ob.rotation_mode='XYZ';ob.rotation_euler=(0,0,0)
    ob.keyframe_insert('rotation_euler',frame=1);ad=ob.animation_data
    cb=anim_utils.action_get_channelbag_for_slot(ad.action,ad.action_slot)
    fc=cb.fcurves.find('rotation_euler',index=2 if i in [0,4] else 1)
    fc.keyframe_points.add(len(plan['frames'])-1)
    fc.keyframe_points.foreach_set('co',[v for row in plan['frames'] for v in [row['frame'],math.radians(row['degrees'][i])]])
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    fc.update()
for frame,label in [(1,'Pick blue'),(108,'Lift and inspect'),(192,'Transfer rear'),(348,'Pick orange'),(480,'Stack'),(648,'Park')]:
    sc.timeline_markers.new(label,frame=frame)
sc['scope']=plan['scope'];sc['load_status']='250g held for minutes NOT validated'
for script in ['task-props.py','task-camera.py']:
    p=ROOT/script;exec(compile(p.read_text(),str(p),'exec'),{'__file__':str(p)})
print('AGENT_OK natural task scene',len(sc.objects))

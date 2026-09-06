"""Check all authored poses, camera margins, grip registration and final stack."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent
plan=json.loads((ROOT/'reports/task-motion-plan.json').read_text())
sc=bpy.data.scenes['ARM2-Task-demo'];bpy.context.window.scene=sc
objects=[o for o in sc.objects if o.type=='MESH' and (o.name.startswith('A2-') or o.get('demo_collision'))]
joint_names=['J01-yaw','J02-shoulder','J03-elbow','J04-wrist-pitch','J05-wrist-roll','J06-gripper']
grip=bpy.data.objects['A2-gripper-fixed-task'];bad=[];minscreen=[1,1];maxscreen=[0,0];grip_error=angle_error=0
for row in plan['frames']:
    f=row['frame'];sc.frame_set(f);bpy.context.view_layer.update()
    for i,name in enumerate(joint_names):
        got=math.degrees(bpy.data.objects['A2-'+name+'-task'].rotation_euler[2 if i in [0,4] else 1])
        angle_error=max(angle_error,abs(got-row['degrees'][i]))
    for ob in objects:
        for corner in ob.bound_box:
            p=world_to_camera_view(sc,sc.camera,ob.matrix_world@Vector(corner))
            for k in range(2):minscreen[k]=min(minscreen[k],p[k]);maxscreen[k]=max(maxscreen[k],p[k])
            if p.x<.045 or p.x>.955 or p.y<.045 or p.y>.955 or p.z<=0:bad.append([f,ob.name,list(p)])
    for label,event in plan['payload_events'].items():
        ob=bpy.data.objects['Task-payload-'+label]
        if event['attach']<=f<=event['release']:
            wanted=grip.matrix_world@Matrix.Translation(plan['grip_local'])
            grip_error=max(grip_error,max(abs(a-b) for r,s in zip(wanted,ob.matrix_world) for a,b in zip(r,s)))
sc.frame_set(720);bpy.context.view_layer.update()
blue=bpy.data.objects['Task-payload-blue'];orange=bpy.data.objects['Task-payload-orange'];seat=bpy.data.objects['Task-seat-C']
def bounds(o):
    vs=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [(min(v[k] for v in vs),max(v[k] for v in vs)) for k in range(3)]
blue_box=bounds(blue);orange_box=bounds(orange);seat_box=bounds(seat)
stack_gap=(orange_box[2][0]-blue_box[2][1])*1000;seat_gap=(blue_box[2][0]-seat_box[2][1])*1000
report={'frames':720,'screen_min':minscreen,'screen_max':maxscreen,'framing_violations':bad,
    'max_angle_error_deg':angle_error,'max_held_transform_error':grip_error,
    'final_stack_gap_mm':stack_gap,'final_seat_gap_mm':seat_gap}
report['passed']=not bad and angle_error<.0001 and grip_error<.00001 and abs(stack_gap)<.01 and abs(seat_gap)<.01
(ROOT/'reports/task-presentation-check.json').write_text(json.dumps(report,indent=2))
print('AGENT_OK task presentation',{k:v for k,v in report.items() if k!='framing_violations'});assert report['passed']

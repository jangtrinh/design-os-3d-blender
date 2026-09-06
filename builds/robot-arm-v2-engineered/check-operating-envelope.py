"""Conservative gravity screen and declared gripper contact assumptions."""
from pathlib import Path
import bpy,math,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
exec(compile((ROOT/'verify-arm.py').read_text(),str(ROOT/'verify-arm.py'),'exec'))
# A real reserve is attached to each link, in addition to modeled hardware mass.
reserves=[(bpy.data.objects['A2-J02-shoulder'],Vector((0,0,.06)),.01,'cable-reserve'),
          (bpy.data.objects['A2-J03-elbow'],Vector((0,0,.075)),.015,'cable-reserve'),
          (bpy.data.objects['A2-tool-coupling'],Vector((.03,0,.03)),.025,'tool-cable-reserve')]
names=['J02-shoulder','J03-elbow','J04-wrist-pitch','J05-wrist-roll']
maximum={n:{'gravity_bound_Nm':0} for n in names}
saved={o:o.rotation_euler.copy() for o in controls}
# Fixed downstream shapes in 75 configurations; bound rotates gravity through all directions.
for elbow in [-90,-45,0,45,90]:
 for pitch in [-80,-40,0,40,80]:
  for roll in [-90,0,90]:
   for n,a,axis_i in [('J02-shoulder',0,1),('J03-elbow',elbow,1),('J04-wrist-pitch',pitch,1),('J05-wrist-roll',roll,2)]:
    ob=bpy.data.objects['A2-'+n];ob.rotation_euler=(0,0,0);ob.rotation_euler[axis_i]=math.radians(a)
   bpy.context.view_layer.update()
   for n in names:
    ob=bpy.data.objects['A2-'+n];origin=ob.matrix_world.translation
    axis=ob.matrix_world.to_3x3()@Vector((0,0,1) if 'roll' in n else (0,1,0));moment=Vector()
    for child,local,m,kind in lumps+[payload]+reserves:
     if descendant(child,ob):moment+=(child.matrix_world@local-origin)*m
    bound=moment.cross(axis).length*9.80665
    if bound>maximum[n]['gravity_bound_Nm']:maximum[n]={'gravity_bound_Nm':bound,'elbow_deg':elbow,'pitch_deg':pitch,'roll_deg':roll}
for ob,rot in saved.items():ob.rotation_euler=rot
bpy.context.view_layer.update()
for n,r in maximum.items():
 r['rated_Nm']=4.903325 if n in names[:2] else .980665
 r['factor1_5_Nm']=r['gravity_bound_Nm']*1.5
 r['rated_over_factored']=r['rated_Nm']/r['factor1_5_Nm']
grip={'payload_kg':.25,'assumed_min_friction':.3,'contact_count':2,'contact_lever_mm':72,
 'normal_per_jaw_N':.25*9.80665/(2*.3),'torque_static_Nm':.25*9.80665/(2*.3)*.072,
 'factor2_torque_Nm':.25*9.80665/(2*.3)*.072*2,'rated_Nm':.980665,
 'scope':'Two opposing pad contacts; no eccentric object moment. Friction and TPU bonding must be tested.',
 'release_status':'UNVERIFIED: spline adapter, clamp preload, contact friction and loaded thermal hold'}
gaps=[]
for angle in [-16,0,12,18]:
 # Projected center clearance at the 72 mm contact station in jaw plane.
 a=math.radians(angle);moving_x=1.52*math.cos(a)+72*math.sin(a)
 gaps.append({'angle_deg':angle,'approx_pad_clearance_mm':28-1.52-moving_x-4})
report={'status':'PREPRODUCTION_NOT_RELEASED','reserve_g':50,'gravity_configuration_count':75,
 'scope':'Gravity-direction bound per sampled downstream pose, NOT collision-free workspace certification or dynamics.',
 'joint_results':maximum,'gripper':grip,'jaw_projected_clearance':gaps,
 'hold_test_required':'250g horizontal, 15min proposed screening; log current, case temperature and drift. Manufacturer thermal limits and actual setup govern stop limits.'}
(ROOT/'reports/operating-envelope.json').write_text(json.dumps(report,indent=2))
print('OPERATING_ENVELOPE',json.dumps(report))

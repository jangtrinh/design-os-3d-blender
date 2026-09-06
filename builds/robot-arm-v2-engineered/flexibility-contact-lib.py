"""Cross-joint surface contact screen, including hardware, in the assembled CAD."""
import bpy,math,json,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sc=bpy.data.scenes[os.environ.get('ARM_CONTACT_SCENE','ARM2-Assembled')];bpy.context.window.scene=sc
suffix=os.environ.get('ARM_CONTACT_SUFFIX','')
joint_names=['J01-yaw','J02-shoulder','J03-elbow','J04-wrist-pitch','J05-wrist-roll','J06-gripper']
joint_objects=[bpy.data.objects['A2-'+n+suffix] for n in joint_names]
original_angles=[o.rotation_euler.copy() for o in joint_objects]
def motion_group(ob):
    if ob.get('demo_payload'):return 100+ob['demo_payload']
    while ob:
        if ob in joint_objects:return joint_objects.index(ob)+1
        ob=ob.parent
    return 0
meshes=[o for o in sc.objects if o.type=='MESH' and (o.name.startswith('A2-') or o.get('demo_collision'))]
geometry={};groups={}
for ob in meshes:
    ob.data.calc_loop_triangles()
    geometry[ob.name]=([v.co.copy() for v in ob.data.vertices],[tuple(t.vertices) for t in ob.data.loop_triangles])
    groups[ob.name]=motion_group(ob)
def set_angles(values):
    for index,(ob,value) in enumerate(zip(joint_objects,values)):
        ob.rotation_euler=(0,0,0);ob.rotation_euler[2 if index in [0,4] else 1]=math.radians(value)
    bpy.context.view_layer.update()
def internal_actuator_pair(a,b):
    for label in ['yaw','shoulder','elbow','wrist','roll','gripper']:
        names=[a.name.removesuffix(suffix) if suffix else a.name,b.name.removesuffix(suffix) if suffix else b.name]
        if 'A2-'+label+'-servo' in names and any(n.startswith('A2-'+label+'-output-') for n in names):return True
    return False
pairs=[(a,b) for i,a in enumerate(meshes) for b in meshes[i+1:] if groups[a.name]!=groups[b.name] and not internal_actuator_pair(a,b)]
def contacts():
    boxes={};trees={}
    for ob in meshes:
        vs,tri=geometry[ob.name];world=[ob.matrix_world@v for v in vs]
        boxes[ob.name]=[(min(v[k] for v in world),max(v[k] for v in world)) for k in range(3)]
        trees[ob.name]=BVHTree.FromPolygons(world,tri,all_triangles=True,epsilon=0)
    found=[]
    for a,b in pairs:
        if not all(min(boxes[a.name][k][1],boxes[b.name][k][1])-max(boxes[a.name][k][0],boxes[b.name][k][0])>.00005 for k in range(3)):continue
        overlap=trees[a.name].overlap(trees[b.name])
        if overlap:found.append({'a':a.name,'b':b.name,'triangles':len(overlap)})
    return found
def restore_angles():
    for ob,angles in zip(joint_objects,original_angles):ob.rotation_euler=angles
    bpy.context.view_layer.update()

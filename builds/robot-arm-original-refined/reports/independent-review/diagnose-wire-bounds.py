import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
for name in ['A5-wire-yaw','A5-wire-shoulder']:
 ob=sc.objects[name]
 for frame in [1,2571,2847]:
  sc.frame_set(frame);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
  points=[ev.matrix_world@Vector(p.co[:3]) for p in ev.data.splines[0].points]
  bb=[ev.matrix_world@Vector(p) for p in ev.bound_box]
  pp=[world_to_camera_view(sc,sc.camera,p) for p in points]
  pb=[world_to_camera_view(sc,sc.camera,p) for p in bb]
  print(name,frame,'matrix',list(map(list,ev.matrix_world)))
  print('pointsworld',list(points[0]),list(points[-1]),'project',[(p.x,p.y,p.z) for p in (pp[0],pp[-1])])
  print('bboxworld',list(bb[0]),list(bb[-1]),'project',[(p.x,p.y,p.z) for p in (pb[0],pb[-1])])

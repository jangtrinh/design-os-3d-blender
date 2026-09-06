import bpy,math
from mathutils import Vector

def material(name,color,rough=.6):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
 nodes=m.node_tree.nodes;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 assert 'Base Color' in bs.inputs and 'Roughness' in bs.inputs
 bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough
 return m

def box(sc,name,size,center,mat):
 x,y,z=[v/2 for v in size]
 vs=[(a*x,b*y,c*z) for c in [-1,1] for b in [-1,1] for a in [-1,1]]
 fs=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob);ob.location=center;return ob

def text(sc,name,value,at,size,mat):
 cu=bpy.data.curves.new(name,'FONT');cu.body=value;cu.size=size;cu.align_x='LEFT'
 ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob);ob.location=at;cu.materials.append(mat);return ob

def camera(sc,at,target,scale):
 data=bpy.data.cameras.new(sc.name+'-camera');data.type='ORTHO';data.ortho_scale=scale;data.clip_start=.001;data.clip_end=50
 cam=bpy.data.objects.new(data.name,data);sc.collection.objects.link(cam);cam.location=at
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;return cam

def lighting(sc):
 for i,(at,power,sz) in enumerate([((.3,-.4,1.5),110,1.0),((-.7,.1,.9),75,.8),((.6,.7,1.0),95,.7)]):
  d=bpy.data.lights.new(sc.name+f'-light-{i}','AREA');d.energy=power;d.shape='DISK';d.size=sz
  o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=at;o.rotation_euler=(Vector((.2,.1,.15))-o.location).to_track_quat('-Z','Y').to_euler()
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.cycles.use_denoising=True
 sc.render.resolution_percentage=100;sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
 sc.render.image_settings.color_mode='RGB';sc.render.use_compositing=False;sc.render.film_transparent=False
 sc.render.threads_mode='FIXED';sc.render.threads=8
 sc.world.color=(.15,.15,.15)

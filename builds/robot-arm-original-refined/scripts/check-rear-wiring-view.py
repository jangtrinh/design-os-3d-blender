"""Disposable rear visual check; never saves or edits the delivered camera."""
from pathlib import Path
import bpy, json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
sc.frame_set(sc.frame_end)
cam=sc.camera;cam.animation_data_clear();cam.data.animation_data_clear()
focus=Vector((-.043,.016,.161));direction=Vector((.55,1,.60)).normalized()
cam.location=focus+direction*1.6;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-direction).to_track_quat('-Z','Y')
cam.data.ortho_scale=.59
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
sc.cycles.device='GPU';sc.cycles.denoising_use_gpu=True;sc.cycles.samples=8
sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(ROOT/'renders/wiring-rear-check.png')
assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
print('REAR_WIRING_VIEW_RENDERED_NO_SAVE')

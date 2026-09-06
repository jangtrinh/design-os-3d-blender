from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
for filename,scene in [('arm-print-plates.blend','A3-Print-plates'),('arm-step-assembly.blend','A3-Step-assembly')]:
 path=ROOT/filename;assert bpy.ops.wm.open_mainfile(filepath=str(path))=={'FINISHED'}
 sc=bpy.data.scenes[scene];bpy.context.window.scene=sc
 for other in list(bpy.data.scenes):
  if other!=sc and not other.objects:bpy.data.scenes.remove(other)
 sc.frame_set(sc.frame_end if scene=='A3-Step-assembly' else 1)
 for a in bpy.context.screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
 assert bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)=={'FINISHED'}
 print('AGENT_OK normalized',filename,scene)

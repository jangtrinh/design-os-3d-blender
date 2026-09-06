from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sc=bpy.data.scenes['A3-Step-assembly'];bpy.context.window.scene=sc
sc.render.resolution_percentage=50;sc.cycles.samples=3;sc.cycles.device='CPU';sc.render.threads_mode='FIXED';sc.render.threads=6
folder=ROOT/'video/animatic';folder.mkdir(exist_ok=True)
for i,frame in enumerate(range(25,1430,8)):
 sc.frame_set(frame);sc.render.filepath=str(folder/f'{i:04d}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
print('AGENT_OK animatic')

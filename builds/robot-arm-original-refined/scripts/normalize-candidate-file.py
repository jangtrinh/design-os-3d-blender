"""Save a normal standalone .blend with the intended active scene."""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined']
bpy.context.window.scene=sc
for other in list(bpy.data.scenes):
    if other!=sc:bpy.data.scenes.remove(other)
sc.frame_set(sc.frame_end)
assert bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'arm-original-refined.blend'),compress=True)=={'FINISHED'}
print('STANDALONE_SCENE_PASS',sc.name,len(sc.objects))

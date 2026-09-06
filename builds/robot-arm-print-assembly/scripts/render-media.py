from pathlib import Path
import bpy,os,json,time
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes[os.environ.get('ARM_SCENE','A3-Step-assembly')];bpy.context.window.scene=sc
sc.render.threads_mode='FIXED';sc.render.threads=int(os.environ.get('ARM_THREADS','8'))
if os.environ.get('ARM_DEVICE')=='METAL':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 enabled=[]
 for d in prefs.devices:d.use=d.type=='METAL';enabled.append((d.name,d.type,d.use))
 assert any(t=='METAL' and u for _,t,u in enabled),enabled
 sc.cycles.device='GPU';sc.cycles.denoising_use_gpu=True;print('DEVICE',enabled,flush=True)
preview=os.environ.get('ARM_PREVIEW')
if preview:
 sc.render.resolution_percentage=int(os.environ.get('ARM_PERCENT','75'));sc.cycles.samples=6
 for frame in map(int,preview.split(',')):
  sc.frame_set(frame);sc.render.filepath=str(ROOT/f'renders/assembly-{frame:04d}-{os.environ.get("ARM_DEVICE","CPU")}.png')
  before=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'};print('FRAME_SECONDS',frame,time.monotonic()-before,flush=True)
else:
 sc.frame_start=int(os.environ.get('ARM_START',str(sc.frame_start)));sc.frame_end=int(os.environ.get('ARM_END',str(sc.frame_end)))
 sc.render.filepath=str(ROOT/'video/frames/frame-');assert bpy.ops.render.render(animation=True)=={'FINISHED'}
print('AGENT_OK rendered',flush=True)

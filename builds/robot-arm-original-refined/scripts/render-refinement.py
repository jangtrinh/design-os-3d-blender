"""Render an isolated original-style candidate, with explicit output identity."""
from pathlib import Path
import bpy, json, os, hashlib, time, runpy, shutil
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
assert any(d.use and d.type=='METAL' for d in prefs.devices)
sc.cycles.device='GPU';sc.cycles.denoising_use_gpu=True
sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
sc.render.threads_mode='AUTO';sc.cycles.seed=0;sc.cycles.use_animated_seed=False
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
sc.render.image_settings.color_mode='RGB';sc.render.resolution_percentage=100
sc.render.use_motion_blur=False
mode=os.environ.get('REFINED_MODE','stills')
if mode=='stills':
    frames=[80,230,280,330,740,825,861,1429,2041,2463,2543,2720,sc.frame_end]
    size=(480,360);samples=4;out=ROOT/'renders/check';fps=None
elif mode=='animatic':
    frames=list(range(int(os.environ.get('REFINED_PREVIEW_START',12)),min(sc.frame_end,int(os.environ.get('REFINED_PREVIEW_END',sc.frame_end)))+1,2));size=(480,360);samples=4;out=ROOT/'video/animatic';fps=12
else:
    frames=list(range(int(os.environ.get('REFINED_FINAL_START',12)),sc.frame_end+1));size=(960,720);samples=6;out=ROOT/'video/frames';fps=24
if os.environ.get('REFINED_OUTPUT'):
    out=ROOT/os.environ['REFINED_OUTPUT']
out.mkdir(exist_ok=True,parents=True)
sc.render.resolution_x,sc.render.resolution_y=size;sc.cycles.samples=samples
identity={'scene_sha256':hashlib.sha256((ROOT/'arm-original-refined.blend').read_bytes()).hexdigest(),
          'mode':mode,'size':size,'samples':samples,'fps':fps,'source_frames':frames,
          'engine':'CYCLES','device':'METAL','fixed_seed':0}
assert identity['scene_sha256']==json.loads((ROOT/'reports/scene-check.json').read_text())['scene_sha256']
identity['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'identity.json').write_text(json.dumps(identity,indent=2))
started=time.monotonic()
cache={};repeats=[]
exact=runpy.run_path(str(ROOT/'scripts/exact-frame-state.py'))
exact['verify_static_render_domain'](sc)
for index,frame in enumerate(frames,1):
    sc.frame_set(frame)
    sc.render.filepath=str(out/f'frame-{index:04d}.png')
    key=exact['state_key'](sc)
    if key in cache:
        donor=cache[key];shutil.copyfile(out/f'frame-{donor:04d}.png',sc.render.filepath)
        repeats.append({'frame':index,'canonical':donor,'state_sha256':key})
    else:
        assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
        cache[key]=index
    if index%100==0:print('PROGRESS',index,len(frames),round(time.monotonic()-started,1),flush=True)
(out/'exact-repeats.json').write_text(json.dumps(repeats,indent=2))
print('REFINED_RENDER_PASS',mode,len(frames),round(time.monotonic()-started,1),'exact repeats',len(repeats),flush=True)

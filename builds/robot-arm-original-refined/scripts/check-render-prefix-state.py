"""Prove exact evaluated states for reusing unchanged rendered prefix frames."""
from pathlib import Path
import bpy,json,runpy,os,hashlib
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
sc.cycles.seed=0;sc.cycles.use_animated_seed=False;sc.render.use_motion_blur=False
lib=runpy.run_path(str(ROOT/'scripts/exact-frame-state.py'))
lib['verify_static_render_domain'](sc)
keys={}
for f in range(12,2943):
    sc.frame_set(f);keys[str(f)]=lib['state_key'](sc)
path=ROOT/'reports'/os.environ['PREFIX_REPORT']
path.write_text(json.dumps({'scene_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'keys':keys},indent=2))
print('PREFIX_CAPTURE_PASS',len(keys))

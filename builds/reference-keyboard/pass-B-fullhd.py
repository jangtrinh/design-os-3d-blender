"""Render approved revision-B stills/video from the exact final-gated Blender file."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import output_context,write,sha
import bpy
import fullhd
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
source=next(v for k,v in inputs['project'].items() if k.endswith('/keyboard.blend'))
gate_path=next(v for k,v in inputs['project'].items() if k.endswith('/final-gate.json'))
gate=json.loads(Path(gate_path).read_text())
assert gate['inputs']['scene_sha256']==sha(source)
assert not gate['failed'] and not gate['required_checks_missing']
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
settings=fullhd.renderer()
views=fullhd.stills(out)
write(out/'stills.json',{'scene_sha256':sha(source),'settings':settings,'views':views})
video=fullhd.movie(out)
write(out/'media-manifest.json',{'scene':source,'scene_sha256':sha(source),'gate_sha256':sha(gate_path),
                               'settings':settings,'views':views,'video':video,
                               'authorization':'Owner requested improved keyboard and rerender of all media in Full HD; native rendering only.'})
emit_ok('reference-keyboard-FullHD',stills=len(views),frames=96,width=1920,height=1080,
        video_bytes=(out/video['file']).stat().st_size)

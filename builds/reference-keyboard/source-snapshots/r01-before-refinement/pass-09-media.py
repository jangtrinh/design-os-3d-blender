"""Bounded delivery stills and a 96-frame animatic from the final-gated scene."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import output_context,write,sha
import bpy
from mathutils import Vector
import studio
from agent_verify import framing
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
source=next(v for k,v in inputs['project'].items() if k.endswith('/keyboard.blend'))
gate_path=next(v for k,v in inputs['project'].items() if k.endswith('/final-gate.json'))
gate=json.loads(Path(gate_path).read_text())
assert not gate['failed'] and not gate['required_checks_missing']
assert gate['inputs']['scene_sha256']==sha(source)
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
sc=bpy.context.scene
sc.frame_set(1)
sc.render.use_persistent_data=False
sc.render.resolution_x,sc.render.resolution_y=1024,768
sc.cycles.samples=32
stills={'hero':studio.capture(out/'CK-001-hero.png',scale=.365)}
sc.frame_set(60)
stills['exploded']=studio.capture(out/'CK-001-exploded.png',target=(0,0,.037),scale=.405)
sc.frame_set(1)
sc.render.resolution_x,sc.render.resolution_y=512,384
sc.cycles.samples=16
ground=bpy.data.objects['STUDIO_GROUND']
ground.hide_render=True
data=bpy.data.lights.new('BOTTOM_INSPECTION_LIGHT','AREA')
data.energy,data.size=4,.25
light=bpy.data.objects.new(data.name,data)
sc.collection.objects.link(light)
light.location=(0,-.10,-.25)
light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
try:
    stills['bottom']=studio.capture(out/'CK-001-bottom.png',location=(0,0,-.4),target=(0,0,0),scale=.32)
finally:
    ground.hide_render=False
    bpy.data.objects.remove(light,do_unlink=True)
    bpy.data.lights.remove(data)
write(out/'stills.json',{'scene_sha256':sha(source),'views':stills,
                        'note':'Bottom uses an explicit temporary inspection light; saved model is unchanged.'})
sc.render.resolution_x,sc.render.resolution_y=384,288
sc.cycles.samples=6
camera=studio.aim(target=(0,0,.037),scale=.405)
frames=out/'frames'
frames.mkdir()
start=time.monotonic()
rows=[]
for frame in range(1,97):
    sc.frame_set(frame)
    for obj in sc.objects:
        if obj.type=='MESH' and obj.name.startswith('RK_') and not obj.hide_render:
            assert framing(obj)['in_frame'],(frame,obj.name,'clipped')
    path=frames/('frame-%04d.png'%frame)
    sc.render.filepath=str(path)
    assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
    rows.append({'frame':frame,'file':path.name,'sha256':sha(path)})
ffmpeg,ffprobe=shutil.which('ffmpeg'),shutil.which('ffprobe')
assert ffmpeg and ffprobe,'ffmpeg/ffprobe must be installed for the declared output'
movie=out/'CK-001-animatic.mp4'
subprocess.run([ffmpeg,'-v','error','-n','-framerate','24','-start_number','1','-i',str(frames/'frame-%04d.png'),
                '-frames:v','96','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],
               check=True,capture_output=True,text=True,timeout=60)
probe=subprocess.run([ffprobe,'-v','error','-select_streams','v:0','-count_frames','-show_entries',
                      'stream=nb_read_frames,r_frame_rate,width,height,duration','-of','json',str(movie)],
                     check=True,capture_output=True,text=True,timeout=30)
stream=json.loads(probe.stdout)['streams'][0]
assert int(stream['nb_read_frames'])==96 and stream['r_frame_rate']=='24/1',stream
subprocess.run([ffmpeg,'-v','error','-i',str(movie),'-f','null','-'],check=True,capture_output=True,timeout=30)
write(out/'media-manifest.json',{'scene':source,'scene_sha256':sha(source),'gate_sha256':sha(gate_path),
                                'frames':rows,'fps':24,'camera':camera,'duration_seconds':4,
                                'video':{'file':movie.name,'sha256':sha(movie),'probe':stream,'full_decode':'pass'},
                                'render_seconds':time.monotonic()-start})
emit_ok('reference-keyboard-media',frames=96,fps=24,stills=3,video_bytes=movie.stat().st_size)

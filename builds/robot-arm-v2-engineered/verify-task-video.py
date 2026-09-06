"""Check the encoded natural-task movie and decode representative story frames."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parent;video=ROOT/'videos/arm-v2-natural-tasks.mp4'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
    '-show_entries','stream=width,height,nb_read_frames,r_frame_rate:format=duration','-of','json',str(video)]))
s=info['streams'][0]
assert (s['width'],s['height'],s['nb_read_frames'],s['r_frame_rate'])==(960,720,'720','24/1')
assert abs(float(info['format']['duration'])-30)<.01
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
folder=ROOT/'renders/task-decoded';folder.mkdir(exist_ok=True)
indices=[0,59,76,107,143,167,239,299,347,431,448,527,599,616,719]
select='+'.join(f'eq(n\\,{n})' for n in indices)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf','select='+select,
    '-fps_mode','vfr',str(folder/'sample-%02d.png')],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
path=json.loads((ROOT/'reports/task-path-check.json').read_text())
presentation=json.loads((ROOT/'reports/task-presentation-check.json').read_text())
assert path['frames_checked']==720 and path['status']=='PASS_SCREEN' and presentation['passed']
report={'status':'ENCODE_PASS_VISUAL_REVIEW_REQUIRED','video':info,'video_sha256':sha(video),
    'blend_sha256':sha(ROOT/'arm-v2-task-demo.blend'),'sampled_frames':[i+1 for i in indices],
    'path_frames_checked':720,'presentation_passed':True,
    'scope':'Scripted task animation, not a physical grasp or250g hold test'}
(ROOT/'reports/task-video-check.json').write_text(json.dumps(report,indent=2))
print('AGENT_OK task encode',info)

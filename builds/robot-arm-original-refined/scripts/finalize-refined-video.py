"""Verify all frames, encode without overlays, and decode the actual delivery."""
from pathlib import Path
import json, hashlib, subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FFMPEG='/opt/homebrew/bin/ffmpeg';FFPROBE='/opt/homebrew/bin/ffprobe'
frames=ROOT/'video/frames'
identity=json.loads((frames/'identity.json').read_text())
scene_hash=hashlib.sha256((ROOT/'arm-original-refined.blend').read_bytes()).hexdigest()
assert identity['scene_sha256']==scene_hash
timing=json.loads((ROOT/'reports/timing.json').read_text())
last=timing['frames']
assert identity['source_frames']==list(range(12,last+1))
assert identity['size']==[960,720] and identity['fps']==24
count=len(identity['source_frames'])
expected={f'frame-{n:04d}.png' for n in range(1,count+1)}
assert {p.name for p in frames.glob('frame-*.png')}==expected
for name in expected:
    with Image.open(frames/name) as im:
        assert im.size==(960,720),(name,im.size)
        im.verify()
repeats=json.loads((frames/'exact-repeats.json').read_text())
for row in repeats:
    assert (frames/f"frame-{row['frame']:04d}.png").read_bytes()==(frames/f"frame-{row['canonical']:04d}.png").read_bytes()
movie=ROOT/'video/arm-step-by-step-refined.mp4'
subprocess.run([FFMPEG,'-y','-v','error','-framerate','24','-i',str(frames/'frame-%04d.png'),
                '-frames:v',str(count),'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',
                '-movflags','+faststart','-an',str(movie)],check=True)
probe=json.loads(subprocess.check_output([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(movie)]))
assert len(probe['streams'])==1
stream=probe['streams'][0]
assert stream['codec_name']=='h264' and stream['r_frame_rate']=='24/1' and int(stream['nb_frames'])==count
assert (stream['width'],stream['height'])==(960,720)
assert abs(float(probe['format']['duration'])-count/24)<.05
subprocess.run([FFMPEG,'-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
decoded=ROOT/'video/decoded-check';decoded.mkdir(exist_ok=True)
samples=[12,150,280,330,538,578,588,615,687,777,933,1214,1258,1295,1367,1457,1567,2185,2607,2687,2864,last]
for source_frame in samples:
    subprocess.run([FFMPEG,'-y','-v','error','-ss',str((source_frame-12)/24),'-i',str(movie),
                    '-frames:v','1',str(decoded/f'{source_frame:04d}.png')],check=True)
report={'status':'PASS_ENCODE_FULL_DECODE','scene_sha256':scene_hash,'frames':count,'fps':24,
        'source_frame_range':[12,last],'dimensions':[960,720],'duration_seconds':count/24,
        'subtitles':False,'audio':False,'full_decode_exit_code':0,'exact_repeat_frames_verified':len(repeats),
        'video_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'decoded_samples':samples,
        'visual_review':'PENDING','ffprobe':probe}
(ROOT/'reports/media-check.json').write_text(json.dumps(report,indent=2))
print('REFINED_MEDIA_PASS',count,movie)

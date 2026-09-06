"""Compose reviewed frame corrections, encode, decode-check, and bind media inputs."""
from pathlib import Path
from PIL import Image
import hashlib, json, shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
repair = json.loads((ROOT/'reports/servo-motion-repair.json').read_text())
base = ROOT/'arm-step-assembly.blend'
candidate = ROOT/'arm-step-assembly-corrected.blend'
assert digest(base) == repair['base_sha256']
assert digest(candidate) == repair['candidate_sha256']
frames = sorted((ROOT/'video/frames').glob('frame-*.png'))
assert [int(p.stem.split('-')[-1]) for p in frames] == list(range(25,1430))
replacement_hashes = {}
for frame in repair['changed_frames']:
    source = ROOT/f'renders/assembly-{frame:04d}-METAL.png'
    destination = ROOT/f'video/frames/frame-{frame:04d}.png'
    replacement_hashes[str(frame)] = {'before':digest(destination),'after':digest(source)}
    shutil.copy2(source,destination)
for path in frames:
    with Image.open(path) as im:
        assert im.size == (960,720), path
        im.verify()
shutil.copy2(base,ROOT/'reports/assembly-before-servo-repair.blend')
shutil.copy2(candidate,base)
movie=ROOT/'video/arm-step-by-step.mp4'
subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-v','error','-framerate','24',
    '-start_number','25','-i',str(ROOT/'video/frames/frame-%04d.png'),
    '-frames:v','1405','-c:v','libx264','-crf','18','-preset','medium',
    '-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],check=True)
probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error',
    '-show_streams','-show_format','-of','json',str(movie)]))
streams=probe['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video'
video=streams[0];assert video['width']==960 and video['height']==720
assert video['nb_frames']=='1405' and video['avg_frame_rate']=='24/1'
assert abs(float(probe['format']['duration'])-1405/24)<.01
subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
report={'status':'PASS_ENCODE_FULL_DECODE','duration_seconds':float(probe['format']['duration']),
        'frames':1405,'fps':24,'size':[960,720],'subtitle_streams':0,
        'movie_sha256':digest(movie),'final_blend_sha256':digest(base),
        'replaced_frames':replacement_hashes,
        'render_provenance':'Base render-identity.json plus servo-motion-repair.json; all37 changed visible frames re-rendered from independently reviewed candidate using the same Metal settings.',
        'visual_review':'pending decoded-video contact sheet inspection'}
(ROOT/'reports/media-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('MEDIA_PASS',movie,report['duration_seconds'],flush=True)

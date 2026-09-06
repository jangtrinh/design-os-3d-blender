"""Reuse prefix only after exact evaluated-state equality; replace final camera shot."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'reports/prefix-before-hero.json').read_text())
new=json.loads((ROOT/'reports/prefix-after-hero.json').read_text())
assert old['keys']==new['keys'] and len(old['keys'])==2931
frames=ROOT/'video/frames';suffix=ROOT/'video/hero-framing-frames'
identity=json.loads((frames/'identity.json').read_text())
tail=json.loads((suffix/'identity.json').read_text())
assert identity['scene_sha256']==old['scene_sha256']
assert tail['scene_sha256']==new['scene_sha256']==hashlib.sha256((ROOT/'arm-original-refined.blend').read_bytes()).hexdigest()
assert tail['source_frames']==list(range(2943,3032))
for field in ('size','samples','fps','engine','device','fixed_seed'):
    assert identity[field]==tail[field],field
assert len(list(suffix.glob('frame-*.png')))==89
for index,frame in enumerate(tail['source_frames'],1):
    shutil.copyfile(suffix/f'frame-{index:04d}.png',frames/f'frame-{frame-11:04d}.png')
repeats=[x for x in json.loads((frames/'exact-repeats.json').read_text()) if x['frame']<=2931]
for row in json.loads((suffix/'exact-repeats.json').read_text()):
    row['frame']+=2931;row['canonical']+=2931;repeats.append(row)
(ROOT/'reports/pre-hero-render-identity.json').write_text(json.dumps(identity,indent=2))
proof={'status':'EXACT_PREFIX_REUSE_PASS','frames':2931,'old_scene_sha256':old['scene_sha256'],
       'new_scene_sha256':new['scene_sha256'],'changed_source_frames':[2943,3031]}
(ROOT/'reports/hero-prefix-reuse.json').write_text(json.dumps(proof,indent=2))
identity['scene_sha256']=new['scene_sha256'];identity['reused_prefix']=proof
identity['script_sha256']=tail['script_sha256']
(frames/'identity.json').write_text(json.dumps(identity,indent=2))
(frames/'exact-repeats.json').write_text(json.dumps(repeats,indent=2))
print('HERO_FRAMES_MERGED',2931,89)

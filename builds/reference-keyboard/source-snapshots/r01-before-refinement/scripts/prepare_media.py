"""Freeze the final scene/gate, render source and explicit output inventory."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write

source,gate=map(lambda x:Path(x).resolve(),sys.argv[1:3])
assert source.is_relative_to(BUILD) and gate.is_relative_to(BUILD)
assert source.is_file() and gate.is_file()
files=[source,gate,BUILD/'scripts/project.py',BUILD/'scripts/studio.py']
files+=list((ROOT/'scripts/agent_verify').glob('*.py'))
files+=[ROOT/'scripts/boilerplates/bp_core.py']
outputs=['CK-001-hero.png','CK-001-exploded.png','CK-001-bottom.png','CK-001-animatic.mp4','stills.json','media-manifest.json']
outputs+=['frames/frame-%04d.png'%n for n in range(1,97)]
write(BUILD/'media-pipeline.json',{'version':1,'pipeline_id':'reference-keyboard-media','steps':[{
    'id':'media','script':'builds/reference-keyboard/pass-09-media.py','inputs':sorted(p.relative_to(ROOT).as_posix() for p in files),
    'depends_on':[],'artifact_inputs':[],'outputs':outputs,'required_postconditions':['frames','fps','stills','video_bytes'],
    'timeout_seconds':300}]})
print('MEDIA_MANIFEST_READY')

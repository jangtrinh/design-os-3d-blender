"""Freeze a fresh revision-B Full HD render manifest and every declared output."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import BUILD,ROOT,write

source,gate=map(lambda s:Path(s).resolve(),sys.argv[1:3])
assert source.is_file() and gate.is_file() and source.is_relative_to(BUILD) and gate.is_relative_to(BUILD)
files=[source,gate]+[BUILD/'scripts'/p for p in ('project.py','studio.py','fullhd.py')]
files+=list((ROOT/'scripts/agent_verify').glob('*.py'))+[ROOT/'scripts/boilerplates/bp_core.py']
shots=['hero','top','knob-detail','key-detail','exploded','bottom','receiver','spacebar-guides','D-receiver','encoder-mount','usb-mount']
outputs=['CK-001-'+s+'.png' for s in shots]+['CK-001-animation-FullHD.mp4','stills.json','media-manifest.json']
outputs+=['frames/frame-%04d.png'%i for i in range(1,97)]
write(BUILD/(sys.argv[3] if len(sys.argv)>3 else 'fullhd-pipeline-B.json'),{'version':1,'pipeline_id':'reference-keyboard-FullHD-B','steps':[{
    'id':'media','script':'builds/reference-keyboard/pass-B-fullhd.py','depends_on':[],
    'inputs':sorted(p.relative_to(ROOT).as_posix() for p in files),'artifact_inputs':[],
    'outputs':outputs,'required_postconditions':['stills','frames','width','height','video_bytes'],
    'timeout_seconds':2400}]})
print('FULLHD_MANIFEST_READY')

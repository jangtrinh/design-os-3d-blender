"""Write a bounded native pipeline for the current layout sources."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write

sources=[BUILD/'layout.json']+[BUILD/'scripts'/name for name in ('project.py','meshkit.py','studio.py')]
sources+=list((ROOT/'scripts/agent_verify').glob('*.py'))
sources+=[ROOT/'scripts/boilerplates/bp_core.py']
write(BUILD/'layout-pipeline.json',{'version':1,'pipeline_id':'reference-keyboard-layout','steps':[{
    'id':'layout','script':'builds/reference-keyboard/pass-01-layout.py','depends_on':[],
    'inputs':sorted(p.relative_to(ROOT).as_posix() for p in sources),'artifact_inputs':[],
    'outputs':['hero.png','top.png','views.json','layout-measurements.json','layout.blend'],
    'required_postconditions':['keys','knobs','width_mm','depth_mm'],'timeout_seconds':120}]})
print('LAYOUT_MANIFEST_READY')

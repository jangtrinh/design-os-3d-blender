"""Write a source-bound downstream pass for an explicitly selected passing form."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write

run=Path(sys.argv[1]).resolve()
assert run.is_relative_to(BUILD)
source=run/'steps/geometry/attempt-0001/model.blend'
gate=run/'steps/gate/attempt-0001/gate-report.json'
assert source.is_file() and gate.is_file()
files=[source,gate,BUILD/'spec.json',BUILD/'layout.json']
files += [BUILD/'scripts'/n for n in ('project.py','meshkit.py','studio.py','details.py','motion.py')]
files += list((ROOT/'scripts/agent_verify').glob('*.py'))
files += [ROOT/'scripts/boilerplates/bp_core.py',ROOT/'scripts/boilerplates/bp_animation.py']
manifest={'version':1,'pipeline_id':'reference-keyboard-presentation','steps':[{
    'id':'presentation','script':'builds/reference-keyboard/pass-04-presentation.py',
    'inputs':sorted(p.relative_to(ROOT).as_posix() for p in files),'depends_on':[],'artifact_inputs':[],
    'outputs':['keyboard.blend','hero.png','top.png','exploded.png','knob-detail.png','key-detail.png','bottom.png','views.json','rgb-gradient.png',
               'motion-contract.json','motion-report.json','provenance.json'],
    'required_postconditions':['meshes','legends','sampled_frames','drivers','views'],'timeout_seconds':240}]}
destination=BUILD/(sys.argv[2] if len(sys.argv)>2 else 'presentation-pipeline.json')
write(destination,manifest)
print('PRESENTATION_MANIFEST_READY')

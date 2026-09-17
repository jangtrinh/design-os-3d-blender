"""Consume a frozen presentation artifact without repeating its successful render."""
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write,spec_path,contract_path

source=Path(sys.argv[1]).resolve()
assert source.is_relative_to(BUILD) and source.is_file()
files=[source,BUILD/'layout.json',BUILD/'interfaces.json',spec_path(),contract_path()]
files += [BUILD/'scripts'/n for n in ('project.py','meshkit.py','inspect_fit.py','verify_layout.py','export_compare.py')]
files += list((ROOT/'scripts/agent_verify').glob('*.py'))
files += list((ROOT/'scripts/production_gate').glob('*.py'))
files += [ROOT/'scripts/boilerplates/bp_core.py',ROOT/'scripts/boilerplates/bp_parametric_contract.py',ROOT/'specs/build-spec.schema.json']
inputs=sorted(set(p.relative_to(ROOT).as_posix() for p in files))
def step(name,script,outputs,post,depends=(),artifacts=()):
    return {'id':name,'script':'builds/reference-keyboard/'+script,'inputs':inputs,'depends_on':list(depends),
            'artifact_inputs':list(artifacts),'outputs':outputs,'required_postconditions':post,'timeout_seconds':240}
spec=json.loads(spec_path().read_text())
steps=[step('inspect','pass-05-inspect.py',['mesh-inventory.json','fit-report.json','layout-checks.json'],
             ['meshes','layout_checks','switch_cells','sampled_key_travels','collision_pairs']),
       step('final-gate','pass-08-final-gate.py',['final-gate.json','stl/manifest.json']+
            ['stl/'+p['id']+'.stl' for p in spec['parts']],['families','failed_parts','stl_files'],['inspect']),
       step('export','pass-06-export.py',['keyboard.glb','source-surfaces.json','export-settings.json','export-evidence.json'],
            ['meshes','source_frames','animations','glb_bytes','embedded_images'],['final-gate']),
       step('reopen','pass-07-reopen.py',['glb-roundtrip.json'],['frames','mesh_names','max_sample_surface_error_mm'],
            ['export'],['export:keyboard.glb','export:source-surfaces.json'])]
destination=BUILD/(sys.argv[2] if len(sys.argv)>2 else 'verification-pipeline.json')
write(destination,{'version':1,'pipeline_id':'reference-keyboard-verification','steps':steps})
print('VERIFICATION_MANIFEST_READY')

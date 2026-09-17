"""Compile the combined authored part contract before the C03 build and tests."""
from copy import deepcopy
import json
from pathlib import Path
import socket
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from production_gate.spec import validate

assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
assert socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
base_spec = json.loads((BUILD / 'spec-B.json').read_text())
mechanical = json.loads((HERE / 'spec.json').read_text())
cfg = json.loads((HERE / 'cap-C03.json').read_text())
spec = deepcopy(mechanical)
parts = {p['id']: deepcopy(p) for p in base_spec['parts']}
for incoming in mechanical['parts']:
    old = parts.get(incoming['id'])
    value = deepcopy(incoming)
    if old:
        value['min_wall_mm'] = max(old['min_wall_mm'], value['min_wall_mm'])
        features = {f['id']: f for f in old['features']}
        features.update({f['id']: f for f in value['features']})
        value['features'] = list(features.values())
    parts[value['id']] = value
collar = cfg['acrylic_retention']
parts['RK_ACRYLIC_COLLAR_0'] = {
    'id': 'RK_ACRYLIC_COLLAR_0', 'object': 'RK_ACRYLIC_COLLAR_0',
    'target_dims_mm': [collar['outer_diameter'], collar['outer_diameter'], collar['top_z'] - collar['bottom_z']],
    'tol_mm': .05, 'min_wall_mm': 1.2, 'expected_shells': 1, 'orientation_up': '+z',
    'features': [{'id': 'spacer-clearance', 'type': 'hole', 'axis': 'z',
                  'center_mm': [-136, -40, 12.8], 'diameter_mm': 5.8, 'tol_mm': .05}],
    'material': collar['material_target'], 'process': 'Machined pilot collar; thickness/shim selected from first article',
}
spec['project'] = 'CK-001 C03 combined geometry screening; 3.2 mm cap clearance and captive acrylic collars'
spec['parts'] = list(parts.values())
spec['physical_evidence'].append(collar['physical_status'])
validate(spec)
with (HERE / 'spec-C03.json').open('x') as handle:
    json.dump(spec, handle, indent=2)
inputs = [ROOT / cfg['source_scene'], HERE / 'cap-C03.json', HERE / 'spec-C03.json',
          HERE / 'acrylic_retention.py', BUILD / 'layout.json', BUILD / 'interfaces.json',
          BUILD / 'scripts/controls.py', BUILD / 'scripts/project.py', BUILD / 'scripts/inspect_fit.py',
          ROOT / 'scripts/boilerplates/bp_core.py', ROOT / 'specs/build-spec.schema.json']
inputs += list((ROOT / 'scripts/production_gate').glob('*.py'))
inputs += list((ROOT / 'scripts/agent_verify').glob('*.py'))
assert all(p.is_file() for p in inputs)
input_names = sorted(set(p.relative_to(ROOT).as_posix() for p in inputs))


def step(ident, script, outputs, required, depends=(), artifacts=()):
    return {'id': ident, 'script': script.relative_to(ROOT).as_posix(), 'inputs': input_names,
            'outputs': outputs, 'required_postconditions': required, 'depends_on': list(depends),
            'artifact_inputs': list(artifacts), 'timeout_seconds': 240}


steps = [step('build', HERE / 'build_C03.py', ['model.blend', 'changes.json'],
              ['caps_replaced', 'unchanged_meshes']),
         step('gate', HERE / 'gate_C03.py', ['gate-report.json', 'stl/manifest.json'] +
              ['stl/' + p['id'] + '.stl' for p in spec['parts']],
              ['representative_families', 'failed', 'stl_files'], ['build'], ['build:model.blend']),
         step('travel', HERE.parent / 'qualification/travel_maximum.py', ['maximum-travel.json'],
              ['keys', 'travel_samples', 'max_travel_mm', 'colliding_keys'],
              ['build', 'gate'], ['build:model.blend'])]
with (HERE / 'pipeline-C03.json').open('x') as handle:
    json.dump({'version': 1, 'pipeline_id': 'CK-001-manufacturing-C03', 'steps': steps}, handle, indent=2)
print(json.dumps({'prepared': 'C03', 'families': len(spec['parts']), 'steps': len(steps)}))

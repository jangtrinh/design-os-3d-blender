"""Bind current digital evidence and an explicitly empty physical record set."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import socket

from evidence_io import file_pin, load, sha
from evidence_gate import assess, validate_assessment

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MFG = HERE.parent


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--travel-run', required=True)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
    assert socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
    run = (ROOT / args.run).resolve()
    travel_run = (ROOT / args.travel_run).resolve()
    destination = (ROOT / args.destination).resolve()
    assert run.is_relative_to(MFG) and destination.is_relative_to(HERE)
    assert travel_run.is_relative_to(MFG)
    assert run.is_dir() and not destination.exists()
    paths = {
        'mechanical_scene': (ROOT / args.scene).resolve(),
        'mechanical_spec': MFG / 'mechanical/spec-C03.json',
        'cap_contract': MFG / 'mechanical/cap-C03.json',
        'electrical_authority': MFG / 'electrical/authority.json',
        'logical_netlist': MFG / 'electrical/logical-netlist.json',
        'power_budget': MFG / 'electrical/power-budget.json',
        'firmware_config': MFG / 'electrical/firmware-config.json',
        'electrical_verification': MFG / 'electrical/verification-E02-final.json',
        'electrical_negative_controls': MFG / 'electrical/negative-controls-E02-final.json',
    }
    assert paths['mechanical_scene'].is_relative_to(MFG)
    assert all(p.is_file() for p in paths.values())
    gate_path = run / 'steps/gate/attempt-0001/gate-report.json'
    travel_path = travel_run / 'steps/travel/attempt-0001/maximum-travel.json'
    electrical_freeze = MFG / 'electrical/freeze-E02-final.json'
    gate, travel, electrical = map(load, (gate_path, travel_path, electrical_freeze))
    assert gate['inputs']['scene_sha256'] == travel['scene_sha256'] == sha(paths['mechanical_scene'])
    assert not gate['failed'] and not gate['required_checks_missing']
    assert travel['status'] == 'pass'
    for name, digest in electrical['authoritative_files'].items():
        assert sha(MFG / 'electrical' / name) == digest, ('stale E02 freeze', name)
    requirements = load(HERE / 'requirements.json')
    prerequisites = {key: {'status': 'not_run'} for key in requirements['digital_release_prerequisites']}
    prerequisites['mechanical_geometry'] = {
        'status': 'pass', 'evidence': file_pin(ROOT, gate_path),
        'bindings': [{'field': ['inputs', 'scene_sha256'], 'input_role': 'mechanical_scene'},
                     {'field': ['inputs', 'spec_sha256'], 'input_role': 'mechanical_spec'}],
        'assertions': [{'field': ['failed'], 'equals': []}, {'field': ['required_checks_missing'], 'equals': []}],
    }
    prerequisites['maximum_travel_geometry'] = {
        'status': 'pass', 'evidence': file_pin(ROOT, travel_path),
        'bindings': [{'field': ['scene_sha256'], 'input_role': 'mechanical_scene'}],
        'assertions': [{'field': ['status'], 'equals': 'pass'}, {'field': ['keys_checked'], 'equals': 58},
                       {'field': ['key_static_collisions', 'collision_pairs'], 'equals': 0},
                       {'field': ['negative_control', 'collision_detected'], 'equals': True}],
    }
    prerequisites['electrical_pin_net_check'] = {
        'status': 'pass', 'evidence': file_pin(ROOT, electrical_freeze),
        'bindings': [{'field': ['authoritative_files', name], 'input_role': role} for name, role in (
            ('authority.json', 'electrical_authority'), ('logical-netlist.json', 'logical_netlist'),
            ('power-budget.json', 'power_budget'), ('firmware-config.json', 'firmware_config'),
            ('verification-E02-final.json', 'electrical_verification'),
            ('negative-controls-E02-final.json', 'electrical_negative_controls'))],
        'assertions': [{'field': ['design_id'], 'equals': 'CK-001-E02'},
                       {'field': ['validation', 'logical'], 'equals': 'PASS_LOGICAL_HOST_VERIFICATION_E02'},
                       {'field': ['validation', 'negative'], 'equals': 'PASS_NEGATIVE_CONTROLS_E02'}],
    }
    snapshot = {'schema_version': 1, 'revision': 'CK-001-C03-E02-pilot',
                'frozen_at': datetime.now(timezone.utc).isoformat(),
                'requirements': file_pin(ROOT, HERE / 'requirements.json'),
                'design_inputs': [dict(file_pin(ROOT, path), role=role) for role, path in paths.items()],
                'test_configurations': {}, 'digital_prerequisites': prerequisites,
                'note': 'No process, physical instrument or specimen configuration is asserted without actual selection.'}
    destination.mkdir(parents=True)
    snapshot_path = destination / 'design-snapshot.json'
    write(snapshot_path, snapshot)
    records = load(HERE / 'bench-records.json')
    assert records['origin'] == 'not_recorded' and not records['observations']
    records['design_snapshot_sha256'] = sha(snapshot_path)
    records_path = destination / 'bench-records.json'
    write(records_path, records)
    result = assess(ROOT, snapshot_path, records_path)
    assert result['status'] == 'INCOMPLETE_MANUFACTURING_EVIDENCE'
    assert result['physical_records'] == 0 and result['passed_metrics'] == 0
    assert validate_assessment(ROOT, result)
    write(destination / 'assessment.json', result)
    print(json.dumps({'snapshot': str(snapshot_path), 'status': result['status'],
                      'physical_records': result['physical_records'], 'required_metrics': result['required_metrics'],
                      'blocked_digital_prerequisites': result['blocked_digital_prerequisites']}))


if __name__ == '__main__':
    main()

"""Check physical records against an immutable design snapshot and pilot criteria."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from evidence_io import sha, load, number, bounded_pin, file_pin, interval_pass, timestamp, field
from record_checks import check_observation, cohort_errors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digital_checks(root, snapshot, requirements):
    invalid = []
    inputs = {pin['role']: pin for pin in snapshot['design_inputs']}
    if len(inputs) != len(snapshot['design_inputs']):
        invalid.append('duplicate design-input role')
    for pin in inputs.values():
        try:
            bounded_pin(root, pin)
        except (ValueError, OSError) as exc:
            invalid.append(str(exc))
    prerequisites = snapshot['digital_prerequisites']
    if set(prerequisites) != set(requirements['digital_release_prerequisites']):
        invalid.append('digital prerequisite set is incomplete')
    blocked = []
    for key, value in prerequisites.items():
        if value.get('status') != 'pass':
            blocked.append(key)
            continue
        try:
            report = load(bounded_pin(root, value['evidence']))
            if not value.get('bindings') or not value.get('assertions'):
                raise ValueError('passing evidence needs source bindings and semantic assertions')
            for binding in value['bindings']:
                if field(report, binding['field']) != inputs[binding['input_role']]['sha256']:
                    raise ValueError('digital evidence binds a different design input')
            for assertion in value['assertions']:
                if field(report, assertion['field']) != assertion['equals']:
                    raise ValueError('digital evidence does not satisfy its acceptance predicate')
        except (ValueError, KeyError, TypeError, OSError) as exc:
            invalid.append(f'{key}: {exc}')
    return blocked, invalid


def all_pins(value):
    if isinstance(value, dict):
        if {'path', 'sha256'} <= value.keys():
            yield {'path': value['path'], 'sha256': value['sha256']}
        for child in value.values():
            yield from all_pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_pins(child)


def assess(root, snapshot_path, records_path):
    snapshot, records = load(snapshot_path), load(records_path)
    requirements_path = bounded_pin(root, snapshot['requirements'])
    requirements = load(requirements_path)
    invalid = [] if snapshot.get('schema_version') == 1 and snapshot.get('design_inputs') else ['incomplete design snapshot']
    try:
        timestamp(snapshot['frozen_at'])
    except (KeyError, ValueError):
        invalid.append('snapshot lacks a valid freeze timestamp')
    blocked_digital, problems = digital_checks(root, snapshot, requirements)
    invalid.extend(problems)
    if records.get('origin') != 'physical_measurement':
        invalid.append('no declared physical measurement set')
    if records.get('design_snapshot_sha256') != sha(snapshot_path):
        invalid.append('bench records are not bound to this design snapshot')
    if not snapshot.get('test_configurations'):
        invalid.append('production-intent hardware/process configurations have not been selected')
    instruments = {}
    for row in records.get('instruments', []):
        if row.get('id') in instruments:
            invalid.append('duplicate instrument id')
        instruments[row.get('id')] = row
    known = {c['id'] for c in requirements['metrics']}
    observations = records.get('observations', [])
    if any(row.get('metric') not in known for row in observations):
        invalid.append('unknown observation metric')
    results, serial_sets = [], {}
    for criterion in requirements['metrics']:
        rows = [r for r in observations if r.get('metric') == criterion['id']]
        serials = [r.get('sample_serial') for r in rows]
        problems = ['insufficient distinct physical samples'] if len(set(serials)) < criterion['samples'] else []
        if len(serials) != len(set(serials)):
            problems.append('duplicate specimen observations; retain repeat curves inside the raw record')
        for row in rows:
            problems.extend(check_observation(root, row, criterion, instruments, snapshot))
        serial_sets[criterion['id']] = set(serials)
        results.append({'id':criterion['id'], 'group':criterion['group'], 'samples':len(rows),
                        'required_samples':criterion['samples'], 'pass':not problems,
                        'problems':problems})
    invalid.extend(cohort_errors(observations, requirements['same_sample_cohorts']))
    pins = {p['path']: p for p in all_pins([snapshot, records])}
    for pin in pins.values():
        try:
            bounded_pin(root, pin)
        except (ValueError, OSError) as exc:
            invalid.append(str(exc))
    complete = not invalid and not blocked_digital and all(r['pass'] for r in results)
    return {'status':'COMPLETE_FOR_DECLARED_PILOT_SCOPE' if complete else 'INCOMPLETE_MANUFACTURING_EVIDENCE',
            'assessed_at':datetime.now(timezone.utc).isoformat(),
            'design_snapshot_sha256':sha(snapshot_path), 'requirements_sha256':sha(requirements_path),
            'records':file_pin(root, records_path), 'snapshot':file_pin(root, snapshot_path),
            'evidence_pins':sorted(pins.values(), key=lambda p:p['path']),
            'physical_records':len(observations), 'passed_metrics':sum(r['pass'] for r in results),
            'required_metrics':len(results), 'invalid_evidence':invalid,
            'blocked_digital_prerequisites':blocked_digital, 'metrics':results,
            'limitations':requirements['limitations']}


def validate_assessment(root, report):
    for pin in [report['records'], report['snapshot'], *report['evidence_pins']]:
        bounded_pin(root, pin)
    fresh = assess(root, root / report['snapshot']['path'], root / report['records']['path'])
    if {k:v for k,v in fresh.items() if k != 'assessed_at'} != {k:v for k,v in report.items() if k != 'assessed_at'}:
        raise ValueError('assessment no longer agrees with current evidence')
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',required=True);parser.add_argument('--records',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    output=(ROOT/args.out).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('report must be a new project-root path')
    source, records = (ROOT/args.snapshot).resolve(), (ROOT/args.records).resolve()
    if not all(path.is_relative_to(ROOT) and path.is_file() for path in (source,records)):
        raise ValueError('snapshot and records must be existing project-root files')
    result=assess(ROOT, source, records)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps({key:result[key] for key in ('status','physical_records','passed_metrics','required_metrics','blocked_digital_prerequisites')}))
    return 0 if result['status']=='COMPLETE_FOR_DECLARED_PILOT_SCOPE' else 1


if __name__=='__main__':
    raise SystemExit(main())

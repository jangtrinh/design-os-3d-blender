"""Read-only completeness/current-byte audit of existing production-gate evidence.

Trust boundary: supplied reports are not authenticated. This verifies declared
coverage and byte bindings; it does not rerun Blender predicates or authorize manufacture.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct

from . import spec as spec_mod
from .coverage_checks import feature_checks, index_rows, inspect_part
from .report import sha256_file

AUDIT_VERSION = '1.0.0'


def load_pinned(path, pins):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    pins[str(path)] = hashlib.sha256(raw).hexdigest()
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    def finite_float(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('non-finite JSON number')
        return value
    def reject(text):
        raise ValueError(f'invalid JSON constant: {text}')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject, parse_float=finite_float)


def export_pin(part, entry, checks, directory, pins):
    if entry['object'] != part['object'] or entry['units'] != 'mm':
        raise ValueError('STL manifest object/units mismatch')
    receipt = checks['roundtrip_import']['value']
    filename = receipt['file']
    if not isinstance(filename, str) or Path(filename).name != filename or '\\' in filename:
        raise ValueError('STL receipt needs a basename, not a path')
    if filename != part['id'] + '.stl' or Path(entry['file']).name != filename:
        raise ValueError('STL name differs from the declared part')
    path = (directory / filename).resolve(strict=True)
    if path.parent != directory:
        raise ValueError('STL escaped the supplied export directory')
    digest = sha256_file(path)
    pins[str(path)] = digest
    if digest != receipt['sha256'] or digest != entry['sha256']:
        raise ValueError('STL bytes changed since the recorded roundtrip')
    triangles = entry['triangles']
    if (type(triangles) is not int or triangles <= 0 or type(receipt['triangles']) is not int
            or triangles != receipt['triangles']):
        raise ValueError('invalid or inconsistent triangle count')
    with path.open('rb') as handle:
        header = handle.read(84)
    if len(header) != 84 or struct.unpack('<I', header[80:84])[0] != triangles:
        raise ValueError('binary STL header count differs from its receipt')
    if path.stat().st_size != 84 + 50 * triangles:
        raise ValueError('binary STL length is incomplete or has extra data')
    return {'path': str(path), 'sha256': digest, 'triangles': triangles}


def audit(scene, spec_path, gate_path, export_dir):
    pins = {}
    code_paths = [Path(__file__).with_name(name) for name in
                  ('coverage.py', 'coverage_checks.py', 'report.py', 'spec.py', '__init__.py')]
    code_paths += [Path(__file__).parents[1] / 'production-gate.py', Path(spec_mod.SCHEMA_PATH)]
    code_hashes = {str(path): sha256_file(path) for path in code_paths}
    scene = Path(scene).resolve(strict=True)
    directory = Path(export_dir).resolve(strict=True)
    if not scene.is_file() or not directory.is_dir():
        raise ValueError('scene file and export directory are required')
    pins[str(scene)] = sha256_file(scene)
    spec = load_pinned(spec_path, pins)
    spec_mod.validate(spec)
    report = load_pinned(gate_path, pins)
    manifest = load_pinned(directory / 'manifest.json', pins)
    if not isinstance(report, dict) or not isinstance(manifest, dict):
        raise ValueError('report and manifest must be JSON objects')
    if any(not isinstance(report.get(key), dict) for key in ('inputs', 'coverage')):
        raise ValueError('report inputs/coverage must be objects')
    if (type(report['schema_version']) is not int or report['schema_version'] != 1
            or report['units'] != 'mm' or manifest['units'] != 'mm'):
        raise ValueError('only production-gate v1 millimetre evidence is supported')
    if not isinstance(report.get('checker'), dict) or not report['checker'].get('version'):
        raise ValueError('source checker identity is missing')
    parts = index_rows(spec['parts'], 'id')
    if len({part['object'] for part in parts.values()}) != len(parts):
        raise ValueError('multiple declared parts point to the same object')
    observed = index_rows(report['parts'], 'id')
    exports = index_rows(manifest['parts'], 'id')
    problems = []
    expected_hashes = {'scene_sha256': pins[str(scene)],
                       'spec_sha256': pins[str(Path(spec_path).resolve())]}
    if any(report['inputs'].get(key) != value for key, value in expected_hashes.items()):
        problems.append('source scene/spec no longer matches the gate report')
    if report.get('failed') != [] or report.get('required_checks_missing') != []:
        problems.append('source gate report failed or has missing required checks')
    if set(observed) != set(parts) or set(exports) != set(parts):
        problems.append('gate/manifest must cover exactly every declared part')
    all_features = set().union(*(feature_checks(p) for p in parts.values()))
    required_names = spec.get('required_checks', [])
    unowned = [name for name in required_names if name.startswith('feature_') and name not in all_features]
    if unowned:
        problems.append('required feature checks have no declared owner: ' + ', '.join(unowned))
    result_parts, files = [], []
    for ident, part in parts.items():
        if ident not in observed or ident not in exports:
            result_parts.append({'id': ident, 'status': 'fail', 'problems': ['part report or export absent']})
            continue
        relevant = feature_checks(part)
        required = [name for name in required_names
                    if not name.startswith('feature_') or name in relevant]
        result, checks = inspect_part(part, observed[ident], required)
        try:
            files.append(export_pin(part, exports[ident], checks, directory, pins))
        except (KeyError, TypeError, ValueError, OSError) as exc:
            result['problems'].append(f'export evidence: {exc}')
        result['status'] = 'fail' if result['problems'] else 'pass'
        result_parts.append(result)
    # Reject inputs altered while this audit was reading them.
    if any(sha256_file(path) != digest for path, digest in {**pins, **code_hashes}.items()):
        raise ValueError('evidence changed during the audit')
    failed = [part['id'] for part in result_parts if part['status'] == 'fail']
    return {'schema_version': 1, 'audit_version': AUDIT_VERSION,
            'status': 'PASS_DECLARED_PART_COVERAGE' if not problems and not failed else 'INCOMPLETE_DECLARED_PART_COVERAGE',
            'manufacture': 'BLOCKED', 'scope': 'Recorded coverage of declared parts and current evidence bytes only',
            'timestamp': datetime.now(timezone.utc).isoformat(), 'source_checker': report['checker'],
            'audit_source_hashes': code_hashes,
            'inputs': {'scene': str(scene), 'spec': str(Path(spec_path).resolve()),
                       'gate_report': str(Path(gate_path).resolve()), 'export_dir': str(directory)},
            'evidence_pins': pins, 'parts': result_parts, 'failed': failed, 'problems': problems,
            'exports': files, 'original_exclusions': report.get('exclusions', []),
            'original_unchecked': report.get('coverage', {}).get('unchecked', []),
            'limits': ['Does not rerun geometric predicates or authenticate reports/source authors.',
                       'Does not prove the declared part/feature list exhausts the assembly or design requirements.',
                       'Wall/feature coverage retains the original sampling limits; no continuous or physical proof.',
                       'Manufacturing, materials, fit, strength, electronics and bench acceptance remain separate.']}


def audit_command(args, emit):
    try:
        if args.parts or not args.export_dir:
            raise ValueError('--audit-report needs --export-dir and does not allow --parts')
        output = Path(args.report).resolve()
        if output.exists() or output.is_relative_to(Path(args.export_dir).resolve()):
            raise ValueError('audit output must be a new file outside the original export directory')
        result = audit(args.scene, args.spec, args.audit_report, args.export_dir)
        if str(output) in result['evidence_pins']:
            raise ValueError('audit output would overwrite an input')
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
        passed = result['status'] == 'PASS_DECLARED_PART_COVERAGE'
        return emit(passed, 0 if passed else 1, result['status'], report=str(output),
                    parts=len(result['parts']), failed=result['failed'], manufacture='BLOCKED')
    except (ValueError, KeyError, TypeError, OverflowError, OSError, spec_mod.SpecError) as exc:
        return emit(False, 2, f'COVERAGE AUDIT INPUT INVALID: {exc}', report=None)

"""Audit real native-gate evidence; mutations are disposable negative controls."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_specs as fs
from gate_harness import GATE, run_gate, tmp
sys.path.insert(0, str(Path(GATE).parent))
from production_gate.coverage import audit
from production_gate.coverage_checks import feature_checks
from production_gate.report import assemble, sha256_file


class TestCoverageAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = Path(tmp()) / 'coverage-source-stl'
        cls.original = Path(tmp()) / 'coverage-source-report.json'
        code, text, report = run_gate('positive', fs.EXAMPLE,
            ['--export-dir', str(cls.exports)], report=str(cls.original))
        if code != 0:
            raise AssertionError(text)
        cls.source_report = report

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coverage-negative-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scene = self.root / 'model.blend'
        shutil.copyfile(Path(tmp()) / 'positive.blend', self.scene)
        self.spec = self.root / 'spec.json'
        shutil.copyfile(fs.EXAMPLE, self.spec)
        self.report = self.root / 'gate.json'
        shutil.copyfile(self.original, self.report)
        self.export = self.root / 'stl'
        shutil.copytree(self.exports, self.export)

    def read(self, path):
        return json.loads(path.read_text())

    def write(self, path, value):
        path.write_text(json.dumps(value, allow_nan=False))

    def inspect(self):
        return audit(self.scene, self.spec, self.report, self.export)

    def reject(self):
        self.assertEqual(self.inspect()['status'], 'INCOMPLETE_DECLARED_PART_COVERAGE')

    def alter(self, name, changes):
        value = self.read(self.report)
        next(c for c in value['parts'][0]['checks'] if c['name'] == name).update(changes)
        self.write(self.report, value)

    def test_real_gate_bytes_pass_and_remain_blocked_for_manufacture(self):
        result = self.inspect()
        self.assertEqual(result['status'], 'PASS_DECLARED_PART_COVERAGE')
        self.assertEqual(result['manufacture'], 'BLOCKED')
        self.assertEqual(len(result['exports']), 1)
        self.assertTrue(result['original_unchecked'])  # Informational overhang is legitimate.

    def test_green_summary_cannot_hide_skipped_wall(self):
        self.alter('wall_thickness_screen', {'status': 'skip'})
        self.reject()

    def test_green_summary_cannot_hide_reported_failure(self):
        self.alter('non_manifold_edges', {'status': 'fail', 'value': 1})
        self.reject()

    def test_passing_wall_status_with_no_samples_is_rejected(self):
        report = self.read(self.report)
        report['parts'][0]['measured']['wall_ray_samples'] = 0
        self.write(self.report, report)
        self.reject()

    def test_reported_wall_below_limit_is_rejected(self):
        report = self.read(self.report)
        report['parts'][0]['measured']['wall_min_mm'] = .01
        self.write(self.report, report)
        self.reject()

    def test_part_and_roundtrip_must_be_present(self):
        for missing in ('roundtrip_import', 'roundtrip_bbox_dims_mm'):
            report = deepcopy(self.source_report)
            report['parts'][0]['checks'] = [c for c in report['parts'][0]['checks'] if c['name'] != missing]
            self.write(self.report, report)
            self.reject()
        report['parts'] = []
        self.write(self.report, report)
        self.reject()

    def test_stale_scene_and_spec_fail(self):
        self.scene.write_bytes(self.scene.read_bytes() + b'changed')
        self.reject()
        shutil.copyfile(Path(tmp()) / 'positive.blend', self.scene)
        self.spec.write_text(self.spec.read_text() + '\n')
        self.reject()

    def test_altered_or_missing_stl_fails(self):
        stl = next(self.export.glob('*.stl'))
        stl.write_bytes(stl.read_bytes() + b'altered')
        self.reject()
        stl.unlink()
        self.reject()

    def test_manifest_identity_and_hash_must_match_receipt(self):
        path = self.export / 'manifest.json'
        for changed in ({'object': 'OTHER'}, {'units': 'm'}, {'sha256': '0' * 64}):
            manifest = self.read(self.exports / 'manifest.json')
            manifest['parts'][0].update(changed)
            self.write(path, manifest)
            self.reject()

    def test_duplicate_checks_parts_and_nonfinite_json_fail_closed(self):
        report = self.read(self.report)
        report['parts'][0]['checks'].append(deepcopy(report['parts'][0]['checks'][0]))
        self.write(self.report, report)
        with self.assertRaises(ValueError):
            self.inspect()
        report = deepcopy(self.source_report)
        report['parts'].append(deepcopy(report['parts'][0]))
        self.write(self.report, report)
        with self.assertRaises(ValueError):
            self.inspect()
        for text in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}', '{"value":1e999}'):
            self.report.write_text(text)
            with self.assertRaises(ValueError):
                self.inspect()

    def test_malformed_mapping_and_boolean_schema_return_cli_error(self):
        for key in ('inputs', 'coverage', 'schema_version'):
            report = deepcopy(self.source_report)
            report[key] = True if key == 'schema_version' else []
            self.write(self.report, report)
            proc = subprocess.run([sys.executable, GATE, '--scene', str(self.scene),
                '--spec', str(self.spec), '--audit-report', str(self.report),
                '--export-dir', str(self.export), '--report', str(self.root / 'error.json')],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertTrue(proc.stdout.splitlines()[-1].startswith('AGENT_FAIL '))
            self.assertNotIn('Traceback', proc.stderr)
            self.assertFalse((self.root / 'error.json').exists())

    def test_feature_specific_requirement_is_not_imposed_on_another_part(self):
        # Two-report structural fixture is synthetic, derived from real gate output.
        spec, report = self.read(self.spec), self.read(self.report)
        second = deepcopy(spec['parts'][0])
        second.update(id='second', object='SecondFixture', features=[])
        spec['parts'].append(second)
        feat = sorted(feature_checks(spec['parts'][0]))[0]
        spec['required_checks'] = ['wall_thickness_screen', feat]
        self.write(self.spec, spec)
        row = deepcopy(report['parts'][0])
        row.update(id='second', object='SecondFixture')
        row['checks'] = [c for c in row['checks'] if not c['name'].startswith('feature_')]
        source_stl = next(self.export.glob('*.stl'))
        shutil.copyfile(source_stl, self.export / 'second.stl')
        next(c for c in row['checks'] if c['name'] == 'roundtrip_import')['value']['file'] = 'second.stl'
        report['parts'].append(row)
        report['inputs']['spec_sha256'] = sha256_file(self.spec)
        self.write(self.report, report)
        manifest_path = self.export / 'manifest.json'
        manifest = self.read(manifest_path)
        entry = dict(manifest['parts'][0], id='second', object='SecondFixture', file=str(self.export / 'second.stl'))
        manifest['parts'].append(entry)
        self.write(manifest_path, manifest)
        self.assertEqual(self.inspect()['status'], 'PASS_DECLARED_PART_COVERAGE')
        # Reproduce the exact aggregation gap: first part passes wall; second skips.
        second.pop('min_wall_mm')
        self.write(self.spec, spec)
        report['parts'][1]['allowed']['min_wall_mm'] = None
        next(c for c in report['parts'][1]['checks'] if c['name'] == 'wall_thickness_screen')['status'] = 'skip'
        assembled = assemble(str(self.scene), str(self.spec), spec, report['parts'], 'mm',
                             'fixture', [], [], 0)
        self.assertEqual(assembled['failed'], [])
        self.assertEqual(assembled['required_checks_missing'], [])
        self.write(self.report, assembled)
        self.reject()

    def test_unowned_feature_and_unsupported_type_cannot_be_blessed_by_pass_labels(self):
        spec, report = self.read(self.spec), self.read(self.report)
        unknown = 'feature_unowned_diameter_mm'
        spec['required_checks'] = [unknown]
        report['parts'][0]['checks'].append({'name': unknown, 'status': 'pass', 'value': 1})
        self.write(self.spec, spec)
        report['inputs']['spec_sha256'] = sha256_file(self.spec)
        self.write(self.report, report)
        self.reject()
        spec['required_checks'] = []
        spec['parts'][0]['features'] = [{'id': 'boss', 'type': 'boss', 'axis': 'z',
            'center_mm': [0, 0, 0], 'diameter_mm': 1, 'tol_mm': .05}]
        report['parts'][0]['checks'].append({'name': 'feature_boss_measured', 'status': 'pass', 'value': 1})
        self.write(self.spec, spec)
        report['inputs']['spec_sha256'] = sha256_file(self.spec)
        self.write(self.report, report)
        self.reject()

    def test_blind_keyed_feature_names_preserve_underscore_ids(self):
        part = {'features': [{'id': 'hole_with_underscores', 'type': 'hole', 'depth_mm': 3,
                             'keyed_flat_mm': 1, 'fastener': {'standard': 'heatset'}}]}
        names = feature_checks(part)
        self.assertNotIn('feature_hole_with_underscores_bore_clear', names)
        self.assertEqual(names, {'feature_hole_with_underscores_' + suffix for suffix in
            ('depth_mm', 'diameter_mm', 'material_around', 'keyed_flat_mm', 'fastener_table', 'heatset_depth')})

    def test_rounding_a_valid_boundary_does_not_tighten_geometry_tolerance(self):
        spec, report = self.read(self.spec), self.read(self.report)
        spec['parts'][0]['target_dims_mm'][0] = 10
        self.write(self.spec, spec)
        report['inputs']['spec_sha256'] = sha256_file(self.spec)
        part = report['parts'][0]
        part['allowed']['target_dims_mm'][0] = 10
        part['allowed']['tol_mm'] = spec['parts'][0]['tol_mm'] = .05
        self.write(self.spec, spec)
        report['inputs']['spec_sha256'] = sha256_file(self.spec)
        part['measured']['bbox_dims_mm'][0] = 10.049999
        for check in part['checks']:
            if check['name'] in ('bbox_dims_mm', 'roundtrip_bbox_dims_mm'):
                check['limit']['target'][0] = 10
                check['limit']['tol'] = .05
                check['value'][0] = 10.05
        self.write(self.report, report)
        self.assertEqual(self.inspect()['status'], 'PASS_DECLARED_PART_COVERAGE')
        part['measured']['bbox_dims_mm'][0] = 10.051
        self.write(self.report, report)
        self.reject()

    def test_cli_audit_needs_no_blender_and_cannot_overwrite_input(self):
        output = self.root / 'audit.json'
        args = [sys.executable, GATE, '--scene', str(self.scene), '--spec', str(self.spec),
                '--audit-report', str(self.report), '--export-dir', str(self.export),
                '--blender', str(self.root / 'not-installed')]
        proc = subprocess.run(args + ['--report', str(output)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(proc.stdout.splitlines()[-1].startswith('AGENT_OK '))
        before = sha256_file(self.report)
        for dest in (output, self.report, self.spec, self.scene, self.export / 'new.json'):
            proc = subprocess.run(args + ['--report', str(dest)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(sha256_file(self.report), before)
        proc = subprocess.run(args + ['--parts', 'one', '--report', str(self.root / 'other.json')],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2, proc.stdout)


if __name__ == '__main__':
    unittest.main()

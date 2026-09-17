"""Run the existing production gate on the current complete C03 family contract."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
sys.path[:0] = [str(BUILD / 'scripts'), str(BUILD.parents[1] / 'scripts')]
from project import output_context, sha
from production_gate.run_in_blender import main as gate
from agent_runtime import emit_ok
import bpy

out, inputs = output_context()
source = inputs['artifacts'].get('build:model.blend')
if source is None:
    models = [p for p in inputs['project'].values() if p.endswith('/model.blend')]
    assert len(models) == 1
    source = models[0]
assert bpy.ops.wm.open_mainfile(filepath=source) == {'FINISHED'}
spec = HERE / 'spec-C03.json'
code = gate(['--scene', source, '--spec', str(spec), '--report', str(out / 'gate-report.json'),
             '--export-dir', str(out / 'stl')])
report = json.loads((out / 'gate-report.json').read_text())
assert code == 0 and not report['failed'] and not report['required_checks_missing'], report['failed']
assert report['inputs']['scene_sha256'] == sha(source)
emit_ok('manufacturing-C03-gate', representative_families=len(report['parts']),
        failed=0, stl_files=len(list((out / 'stl').glob('*.stl'))), manufacture='BLOCKED')

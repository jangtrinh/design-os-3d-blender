"""Spec-bound digital geometry gate and independent STL re-import of part families."""
from pathlib import Path
import sys
import json
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import BUILD,output_context,spec_path
import bpy
from production_gate.run_in_blender import main as gate
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
source=inputs['artifacts']['geometry:model.blend']
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
code=gate(['--scene',source,'--spec',str(spec_path()),
           '--report',str(out/'gate-report.json'),'--export-dir',str(out/'stl')])
report=json.loads((out/'gate-report.json').read_text())
assert code==0,{'failed':report['failed'],'missing':report['required_checks_missing']}
emit_ok('reference-keyboard-digital-gate',part_families=len(report['parts']),
        failed_parts=len(report['failed']),stl_files=len(list((out/'stl').glob('*.stl'))))

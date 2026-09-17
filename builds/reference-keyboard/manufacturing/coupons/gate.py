"""Gate all authored process specimens and independently reimport their STL files."""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
BUILD=HERE.parents[1]
sys.path[:0]=[str(BUILD/'scripts'),str(BUILD.parents[1]/'scripts')]
from project import output_context
from agent_runtime import emit_ok
from production_gate.run_in_blender import main as gate
import bpy

assert bpy.app.background
out,inputs=output_context()
source=inputs['artifacts']['build:specimens.blend']
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
code=gate(['--scene',source,'--spec',str(HERE/'spec.json'),'--report',str(out/'gate-report.json'),
           '--export-dir',str(out/'stl')])
report=json.loads((out/'gate-report.json').read_text())
assert code==0,(report['failed'],report['required_checks_missing'])
emit_ok('manufacturing-specimen-gate',families=len(report['parts']),failures=len(report['failed']),
        reimported_stl=len(list((out/'stl').glob('*.stl'))))

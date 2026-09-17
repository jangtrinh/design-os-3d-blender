"""Final source-bound gate on the saved deliverable scene, with fresh STL re-import."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import BUILD,output_context
import bpy
from production_gate.run_in_blender import main as gate
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
sources=[p for k,p in inputs['project'].items() if k.endswith('/keyboard.blend')]
assert len(sources)==1,'declare exactly one saved keyboard scene'
source=sources[0]
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
bpy.context.scene.frame_set(1)
code=gate(['--scene',source,'--spec',str(BUILD/'spec.json'),'--report',str(out/'final-gate.json'),
           '--export-dir',str(out/'stl')])
report=json.loads((out/'final-gate.json').read_text())
assert code==0,report['failed']
emit_ok('reference-keyboard-final-gate',families=len(report['parts']),failed_parts=len(report['failed']),
        stl_files=len(list((out/'stl').glob('*.stl'))))

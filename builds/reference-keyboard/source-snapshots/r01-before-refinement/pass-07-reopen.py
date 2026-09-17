"""Compare actual imported GLB surfaces and motion against the source scene."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import output_context
from export_compare import compare
from agent_runtime import emit_ok

out,inputs=output_context()
result=compare(inputs['artifacts']['export:source-surfaces.json'],
               inputs['artifacts']['export:keyboard.glb'],out/'glb-roundtrip.json')
assert result['pass'],'GLB surface/motion comparison failed; inspect glb-roundtrip.json'
worst=max(r['surface_max_error_mm'] for f in result['frames'].values() for r in f['objects'])
emit_ok('reference-keyboard-reopen',frames=len(result['frames']),
        mesh_names=len(result['expected_mesh_names']),max_sample_surface_error_mm=worst)

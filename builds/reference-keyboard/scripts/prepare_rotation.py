"""Pin an existing product GLB for one additional nonzero-rotation comparison."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write
source,glb=map(lambda x:Path(x).resolve(),sys.argv[1:3])
assert source.is_file() and glb.is_file() and source.is_relative_to(BUILD) and glb.is_relative_to(BUILD)
files=[source,glb,BUILD/'scripts/project.py',BUILD/'scripts/export_compare.py']
write(BUILD/'rotation-pipeline-B01.json',{'version':1,'pipeline_id':'reference-keyboard-rotation-B','steps':[{
    'id':'rotation','script':'builds/reference-keyboard/pass-B-rotation.py','depends_on':[],
    'inputs':[p.relative_to(ROOT).as_posix() for p in files],'artifact_inputs':[],
    'outputs':['rotation-source.json','rotation-intent.json','rotation-roundtrip.json'],
    'required_postconditions':['frame','encoder_pairs','mesh_names','max_error_mm'],'timeout_seconds':240}]})
print('ROTATION_MANIFEST_READY')

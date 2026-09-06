"""Rebuild the separate motion study from the preserved engineering baseline."""
from pathlib import Path
import bpy,hashlib,os
ROOT=Path(__file__).resolve().parent
source=ROOT/'arm-v2-engineered.blend'
output=Path(os.environ.get('ARM_FLEX_OUTPUT',str(ROOT/'arm-v2-flexibility.blend')))
assert source.resolve()!=output.resolve()
before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
for script in ['flexibility-clearance-refinement.py','flexibility-base-clearance.py',
               'flexibility-wrist-clearance.py','create-flexibility-scene.py','flexibility-stage.py']:
    path=ROOT/script;exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path)})
bpy.ops.wm.save_as_mainfile(filepath=str(output))
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print('AGENT_OK preserved source',before)

"""Inspect maximum source-tolerance travel on the actual saved candidate, without mutation."""
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BUILD=HERE.parents[1]
sys.path[:0]=[str(BUILD/'scripts'),str(BUILD.parents[1]/'scripts')]
import bpy
from project import sha, output_context
import inspect_fit as fit
from agent_runtime import emit_ok

assert bpy.app.background
if os.environ.get('DESIGN_OS_OUTPUT_DIR'):
    directory, inputs = output_context()
    source_path = inputs['artifacts'].get('build:model.blend')
    if source_path is None:
        models = [p for p in inputs['project'].values() if p.endswith('/model.blend')]
        assert len(models) == 1
        source_path = models[0]
    assert bpy.ops.wm.open_mainfile(filepath=source_path) == {'FINISHED'}
else:
    directory = BUILD/'manufacturing/runs/travel-C01'
    directory.mkdir(parents=True,exist_ok=False)
source=Path(bpy.data.filepath).resolve()
assert source.is_file() and source.is_relative_to(BUILD)
before=sha(source)
layout,interfaces,count,nominal_samples,envelope=fit._contracts()
samples=tuple(sorted(set((*nominal_samples,3.2))))
keys,tops,flanges,stems=(fit._indexed(prefix) for prefix in
                        ('RK_KEY_','RK_SWITCH_TOP_','RK_SWITCH_FLANGE_','RK_SWITCH_STEM_'))
assert all(len(group)==count for group in (keys,tops,flanges,stems))
plate=bpy.data.objects['RK_MAIN_PLATE'];housing=bpy.data.objects['RK_SWITCH_HOUSINGS']
collision=fit._collision_evidence(keys,tops,flanges,plate,samples)
engagement=fit._key_stem_interface(keys,stems,tops,flanges,plate,housing,samples,interfaces['keycap'])
guides=fit._spacebar_interface(keys,samples,interfaces['spacebar'])
bad,reason=fit._intersects(fit._tri_mesh(keys[0],-.006),fit._tri_mesh(tops[0]))
assert sha(source)==before,'read-only check changed source file'
passed=(collision['collision_pairs']==0 and not engagement['key_material_stem_collision_indices']
        and not engagement['stem_static_collision_indices'] and guides['collision_free'] and bad)
report={'status':'pass' if passed else 'fail','scene':str(source),'scene_sha256':before,
        'samples_mm':samples,'keys_checked':count,'key_static_collisions':collision,
        'key_stem':engagement,'guides':guides,
        'negative_control':{'virtual_overtravel_mm':6.0,'collision_detected':bad,'method':reason},
        'limits':['Maximum-tolerance digital travel only. The switch cover is a custom B prototype, not an authenticated factory switch mesh.',
                  'Do not force a physical factory switch beyond its own measured stop.',
                  'No force, wear, factory housing compatibility, full-assembly collision or continuous-motion proof.']}
with (directory/'maximum-travel.json').open('x') as handle:
    json.dump(report,handle,indent=2,allow_nan=False)
assert passed, f'maximum travel failed; inspect {directory}/maximum-travel.json'
emit_ok('manufacturing-maximum-travel',keys=count,travel_samples=len(samples),max_travel_mm=3.2,
        colliding_keys=collision['collision_pairs'],guides=guides['guides_checked'],negative_control=bad)

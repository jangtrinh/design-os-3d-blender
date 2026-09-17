"""Measure the saved presentation scene and its actual switch/key travel geometry."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import output_context,layout,write,sha
import bpy
import meshkit as g
import inspect_fit,verify_layout
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
sources=[p for k,p in inputs['project'].items() if k.endswith('/keyboard.blend')]
assert len(sources)==1,'declare exactly one saved keyboard scene'
source=sources[0]
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
bpy.context.scene.frame_set(1)
evidence=inspect_fit.inspect(source_sha256=sha(source))
rows=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or not obj.name.startswith('RK_'): continue
    row=g.numeric(obj)
    if obj.name.startswith('RK_KEY_'):
        from boilerplates.bp_core import evaluated_mesh
        with evaluated_mesh(obj) as (owner,mesh):
            top=max(v.co.z for v in mesh.vertices)
            points=[owner.matrix_world@v.co for v in mesh.vertices if abs(v.co.z-top)<1e-7]
            row['top_bbox_mm']=[[min(p[i] for p in points)*1000 for i in range(2)],
                                [max(p[i] for p in points)*1000 for i in range(2)]]
    if obj.name=='RK_SWITCH_HOUSINGS':
        row['evaluated_connected_shells']=evidence['switch_housings']['evaluated_connected_shells']
    rows.append(row)
inventory={'scene_sha256':sha(source),'units':'mm','frame':1,'objects':rows,'geometry_evidence':evidence}
report=verify_layout.run(inventory,layout())
report['scene_sha256']=sha(source)
evidence['scene_sha256']=sha(source)
write(out/'mesh-inventory.json',inventory)
write(out/'fit-report.json',evidence)
write(out/'layout-checks.json',report)
assert report['status']=='pass',report['failed']
assert evidence['switch_assembly_envelope']['all_within_tolerance']
assert evidence['switch_keycap_overlap']['collision_pairs']==0
interfaces=evidence['interfaces']
assert not interfaces['key_stem']['key_material_stem_collision_indices']
assert not interfaces['key_stem']['stem_static_collision_indices']
assert interfaces['wide_guides']['collision_free']
assert interfaces['encoder_dshaft']['matching_rotations_collision_free']
assert interfaces['encoder_dshaft']['negative_controls_detect_collision']
emit_ok('reference-keyboard-inspect',meshes=len(rows),layout_checks=len(report['checks']),
        switch_cells=evidence['switch_housings']['evaluated_connected_shells'],
        sampled_key_travels=len(evidence['switch_keycap_overlap']['travel_samples_mm']),collision_pairs=0)

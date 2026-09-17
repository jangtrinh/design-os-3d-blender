"""Apply the authored C03 corrections to an immutable C02 engineering scene."""
import hashlib
import json
from pathlib import Path
import socket
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[1]
sys.path[:0] = [str(BUILD / 'scripts'), str(ROOT / 'scripts'), str(HERE)]
import bpy
import controls
from project import output_context, sha, write
from agent_verify import checkpoint
from agent_runtime import emit_ok


def geometry_hash(obj):
    value = {'vertices': [list(v.co) for v in obj.data.vertices],
             'faces': [list(p.vertices) for p in obj.data.polygons],
             'matrix': [list(row) for row in obj.matrix_world]}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


assert bpy.app.background and bpy.app.version[:2] == (5, 2)
assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
assert socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
out, inputs = output_context()
cfg = json.loads((HERE / 'cap-C03.json').read_text())
source = ROOT / cfg['source_scene']
assert sha(source) == cfg['source_sha256']
assert bpy.ops.wm.open_mainfile(filepath=str(source)) == {'FINISHED'}
bpy.context.view_layer.update()
keys = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name.startswith('RK_KEY_')]
one_u = [o for o in keys if o.name != 'RK_KEY_41']
assert len(keys) == 58 and len(one_u) == 57
original = {o.name: geometry_hash(o) for o in bpy.context.scene.objects if o.type == 'MESH' and o not in one_u}
checkpoint('C03-before-keycap-replacement', str(out / 'checkpoints'))
new = controls.keycap('C03_1U_TEMPLATE', visible_skirt_bottom_m=cfg['visible_skirt_bottom'] / 1000)
new.data.name = 'C03_1U_FULL_STROKE_MESH'
new.data.materials.clear()
for mat in one_u[0].data.materials:
    new.data.materials.append(mat)
for obj in one_u:
    obj.data = new.data
    obj['cap_revision'] = cfg['revision']
    obj['physical_fit'] = 'UNQUALIFIED_REQUIRES_FACTORY_SWITCH_AND_PROCESS_SAMPLES'
bpy.data.objects.remove(new, do_unlink=True)
# Collar construction is a separate, explicitly authored mating contract.
import acrylic_retention
assert not any(o.name.startswith('RK_ACRYLIC_COLLAR_') for o in bpy.context.scene.objects)
collars = acrylic_retention.apply()
assert len(collars) == cfg['acrylic_retention']['count']
retention = [{'name': o.name, 'support_probe_angles_deg': list(o['support_probe_angles_deg']),
              'minimum_spacer_radial_clearance_mm': o['minimum_spacer_radial_clearance_mm'],
              'minimum_knob_xy_clearance_mm': o['minimum_knob_xy_clearance_mm'],
              'max_nominal_intersection_mm3': o['max_nominal_intersection_mm3']} for o in collars]
bpy.context.view_layer.update()
assert all(geometry_hash(bpy.data.objects[name]) == digest for name, digest in original.items())
bpy.context.scene['manufacturing_revision'] = 'mechanics-C03'
bpy.context.scene['manufacture_status'] = 'BLOCKED_PHYSICAL_EVIDENCE_REQUIRED'
bpy.context.scene['cap_contract_sha256'] = sha(HERE / 'cap-C03.json')
scene = out / 'model.blend'
assert bpy.ops.wm.save_as_mainfile(filepath=str(scene)) == {'FINISHED'}
assert sha(source) == cfg['source_sha256']
write(out / 'changes.json', {'revision': 'C03', 'scene_sha256': sha(scene),
      'source_sha256': cfg['source_sha256'], 'caps_replaced': len(one_u), 'retention': retention,
      'unchanged_geometry': original, 'declared_inputs': inputs['project'],
      'manufacture': 'BLOCKED', 'physical_measurements': 0})
emit_ok('manufacturing-C03-build', caps_replaced=len(one_u), unchanged_meshes=len(original),
        scene_sha256=sha(scene), manufacture='BLOCKED')

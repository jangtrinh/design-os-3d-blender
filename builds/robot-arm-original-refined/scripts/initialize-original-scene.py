"""Copy the user-selected original studio scene without touching its source."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Matrix
ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / 'robot-arm-print-assembly'
source_path = OLD / 'arm-step-assembly.blend'
expected_hash = '20e27bc6022251d1a07ff6cad86098f11aade295178e9e2af2adfc83b69495ba'
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == expected_hash
assert not bpy.data.scenes.get('A5-Original-refined'), 'Reconcile existing candidate first'
timeline = json.loads((OLD / 'reports/assembly-timeline.json').read_text())
frozen = json.loads((OLD / 'reports/source-freeze.json').read_text())
source_to_frozen = {r['source']: r['frozen'] for r in frozen['objects']}
records = {r['source']: r for r in timeline['objects']}
with bpy.data.libraries.load(str(source_path), link=False) as (src, dst):
    dst.scenes = [timeline['scene']]
sc = dst.scenes[0]
sc.name = 'A5-Original-refined'
bpy.context.window.scene = sc
sc.frame_set(sc.frame_end)
bpy.context.view_layer.update()
found = []
for ob in list(sc.objects):
    if ob.get('source_object'):
        key = source_to_frozen[ob['source_object']]
        row = records[key]
        ob.animation_data_clear()
        ob.parent = None
        ob.matrix_world = Matrix(row['final_matrix'])
        ob.hide_render = ob.hide_viewport = False
        ob.name = key.replace('A3-src-', 'A5-part-')
        ob['original_build_name'] = row['object']
        ob['frozen_name'] = key
        found.append({**row, 'candidate': ob.name})
    elif ob.type == 'EMPTY':
        ob.animation_data_clear()
sc.camera.animation_data_clear()
sc.camera.data.animation_data_clear()
assert len(found) == 402
sc['controller'] = 'root'
sc['source_sha256'] = expected_hash
sc['release'] = 'Original-film refinement; physical release remains unverified'
sc.frame_start = 1
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.overlay.show_overlays = False
(ROOT / 'reports/source-map.json').write_text(json.dumps({'objects': found, 'source_sha256': expected_hash,
    'runtime': bpy.app.version_string, 'scene': sc.name}, indent=2))
bpy.data.libraries.write(str(ROOT / 'original-style-blockout.blend'), {sc}, fake_user=True, compress=True)
print('ORIGINAL_INIT_PASS', sc.name, len(found))

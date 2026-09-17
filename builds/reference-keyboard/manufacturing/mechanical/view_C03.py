"""Native Full-HD engineering captures of a gated C03 file; no scene overwrite."""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[1]
sys.path[:0] = [str(BUILD / 'scripts'), str(ROOT / 'scripts')]
import bpy
from mathutils import Vector
from project import sha, write
import fullhd, studio, meshkit
from agent_runtime import emit_ok

parser = argparse.ArgumentParser()
parser.add_argument('--gate', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
assert bpy.app.background and socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
source = Path(bpy.data.filepath).resolve()
gate_path = (ROOT / args.gate).resolve()
out = (ROOT / args.out).resolve()
assert source.is_relative_to(BUILD) and gate_path.is_relative_to(BUILD) and out.is_relative_to(BUILD)
gate = json.loads(gate_path.read_text())
before = sha(source)
assert gate['inputs']['scene_sha256'] == before and not gate['failed'] and not gate['required_checks_missing']
out.mkdir(parents=True, exist_ok=False)
palette = studio.palette()
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH' or not obj.name.startswith('RK_'):
        continue
    key = ('key' if obj.name.startswith('RK_KEY_') else 'rubber' if obj.name.startswith('RK_FOOT_') else
           'black' if obj.name == 'RK_MAIN_PLATE' else 'switch' if obj.name.startswith('RK_SWITCH_') else 'silver')
    meshkit.assign(obj, palette[key])
studio.setup()
settings = fullhd.renderer()
bpy.context.scene.cycles.samples = 24
views = {'assembly': studio.capture(out / 'assembly-C03.png', scale=.395)}
key = bpy.data.objects['RK_KEY_00']
center = key.matrix_world.translation + Vector((0, 0, .005))
with fullhd.isolated([key.name], center):
    views['cap_receiver'] = studio.capture(out / 'cap-C03.png', subjects=[key.name],
        location=tuple(center + Vector((.02, -.03, -.06))), target=tuple(center), scale=.050)
names = ['RK_ACRYLIC_COLLAR_2', 'RK_SPACER_2']
center = Vector((-.136, .040, .008))
with fullhd.isolated(names, center):
    views['collar_spacer'] = studio.capture(out / 'collar-C03.png', subjects=names,
        location=tuple(center + Vector((.025, -.03, .035))), target=tuple(center), scale=.040)
for path in out.glob('*.png'):
    with path.open('rb') as handle:
        header = handle.read(24)
    assert struct.unpack('>II', header[16:24]) == (1920, 1080)
assert sha(source) == before
write(out / 'view-manifest.json', {'scene_sha256': before, 'gate_sha256': sha(gate_path),
      'settings': settings, 'views': views, 'files': {p.name: sha(p) for p in out.glob('*.png')},
      'scope': 'Engineering geometry captures with temporary neutral materials. No new animation, exact-reference likeness or manufacturing release.',
      'source_unchanged': True})
emit_ok('C03-engineering-views', images=3, width=1920, height=1080, source_unchanged=1)

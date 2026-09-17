"""Real Blender control: an incomplete previous coupon must not be overwritten."""
from pathlib import Path
import sys
import tempfile

import bpy

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/samples'))
import agent_runtime as rt
from native_iteration_coupon import build

assert bpy.app.background
before = sorted(bpy.data.objects.keys())
with tempfile.TemporaryDirectory(prefix='coupon-existing-') as temporary:
    output = Path(temporary)
    proof = output / 'proof.png'
    proof.write_bytes(b'previous incomplete attempt evidence')
    try:
        build(ROOT, output, 'candidate')
    except ValueError as exc:
        assert 'overwrite' in str(exc)
    else:
        raise AssertionError('partial output collision was accepted')
    assert proof.read_bytes() == b'previous incomplete attempt evidence'
    assert not (output / 'model.blend').exists()
assert sorted(bpy.data.objects.keys()) == before
rt.emit_ok('coupon-output-collision', preserved=1, scene_objects=len(before))

"""Verify the already-built C03 artifact; never repeat its completed scene mutation."""
import json
from pathlib import Path
import socket
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[1]
# This folder contains the native Blender inspector named inspect.py. A host
# CLI must not let it shadow Python's inspect module (argparse uses dataclasses).
sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != HERE]
import argparse
sys.path.insert(0, str(BUILD / 'scripts'))
from project import sha

assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
assert socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gate-only', action='store_true')
parser.add_argument('--out', default='verification-C03.json')
args = parser.parse_args()
destination = (HERE / args.out).resolve()
assert destination.parent == HERE.resolve() and not destination.exists()
attempt = HERE.parent / 'runs/mechanics-C03/steps/build/attempt-0001'
source = attempt / 'model.blend'
changes = json.loads((attempt / 'changes.json').read_text())
assert sha(source) == changes['scene_sha256']
assert changes['caps_replaced'] == 57 and len(changes['retention']) == 4
manifest = json.loads((HERE / 'pipeline-C03.json').read_text())
steps = manifest['steps'][1:2] if args.gate_only else manifest['steps'][1:]
for step in steps:
    step['inputs'] = [p for p in step['inputs'] if not p.endswith('/model.blend')]
    step['inputs'] += [source.relative_to(ROOT).as_posix(), (attempt / 'changes.json').relative_to(ROOT).as_posix()]
    step['artifact_inputs'] = []
    step['depends_on'] = [] if step['id'] == 'gate' else ['gate']
    step['required_postconditions'] = [p for p in step['required_postconditions'] if p != 'negative_control']
with destination.open('x') as handle:
    json.dump({'version': 1, 'pipeline_id': 'CK-001-C03-existing-artifact-verification', 'steps': steps}, handle, indent=2)
print(json.dumps({'source_sha256': sha(source), 'steps': len(steps), 'rebuild': False}))

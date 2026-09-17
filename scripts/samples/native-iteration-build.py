"""One pipeline-owned native verification pass, used for three calibrated variants."""
import os
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_runtime as rt
from native_iteration_coupon import build

output = Path(os.environ['DESIGN_OS_OUTPUT_DIR']).resolve()
assert output.is_relative_to(ROOT), 'Coupon output must remain in this checkout'
variant = os.environ['DESIGN_OS_STEP_ID']
context = json.loads(os.environ['DESIGN_OS_INPUTS_JSON'])
for source in context['artifacts'].values():
    previous = json.loads(Path(source).read_text())
    assert previous['manufacture'] == 'NOT_REQUESTED'
    assert previous['height_m'] > 0
summary = build(ROOT, output, variant)
rt.emit_ok('native-iteration-coupon', height_m=summary['height_m'],
           part_count=summary['part_count'], proof_bytes=(output / 'proof.png').stat().st_size)

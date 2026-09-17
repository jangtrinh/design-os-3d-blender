"""Build CK-001 mechanics C02 from immutable geometry-B03 in a fresh headless process."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import sys

import bpy

ROOT = Path(__file__).resolve().parents[4]
BUILD = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(BUILD / "scripts"), str(Path(__file__).resolve().parent)]
from agent_runtime import emit_ok  # noqa: E402
import mechanics  # noqa: E402
import refine  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


assert bpy.app.background
assert bpy.app.version[:2] == (5, 2), bpy.app.version
assert socket.gethostname() == "jangtrinhs-MacBook-Pro-2.local", socket.gethostname()
assert str(ROOT.resolve()) == "/Users/jang/Products/design-os-3d-blender", ROOT.resolve()

source = BUILD / "runs/geometry-B03/steps/geometry/attempt-0001/model.blend"
source_sha = "e4c54bb1eca1a592787b88af4ee25dbbe50dab91837a95bc47aa87e99909aec8"
assert sha(source) == source_sha, (source, sha(source))

attempt = os.environ.get("MECH_C02_ATTEMPT", "0001")
assert attempt.isdigit() and len(attempt) == 4, attempt
run = BUILD / "manufacturing/runs/mechanics-C02" / ("attempt-" + attempt)
assert not run.exists(), ("refusing to overwrite manufacturing evidence", run)
run.mkdir(parents=True)
(run / "checkpoints").mkdir()

assert bpy.ops.wm.open_mainfile(filepath=str(source)) == {"FINISHED"}
mechanics.CHECKPOINTS = run / "checkpoints"
result = refine.apply()
bpy.context.scene["manufacturing_source_scene_sha256"] = source_sha
bpy.context.scene["manufacturing_requirements_sha256"] = sha(BUILD / "manufacturing/mechanical-requirements.json")
bpy.context.scene["manufacturing_spec_sha256"] = sha(BUILD / "manufacturing/mechanical/spec.json")
bpy.context.scene["physical_test_status"] = "NOT_RUN"

scene = run / "model.blend"
assert bpy.ops.wm.save_as_mainfile(filepath=str(scene)) == {"FINISHED"}
summary = {
    "source": str(source), "source_sha256": source_sha,
    "scene": str(scene), "scene_sha256": sha(scene), "changes": result,
    "manufacture": "BLOCKED", "physical_test_status": "NOT_RUN",
    "limits": ["Digital construction only; no physical torque, pull, material, electrical or thermal qualification."]
}
(run / "build-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
emit_ok("mechanics-C02-build", scene_sha256=summary["scene_sha256"],
        removed_bonds=result["removed_bonds"], lower_screws=result["lower_screws"],
        clamps=result["clamps"], set_screws=result["set_screws"], manufacture="BLOCKED")

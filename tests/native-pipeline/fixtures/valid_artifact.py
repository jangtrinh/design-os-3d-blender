"""Tiny no-render Blender fixture for native-pipeline execution receipts."""

import json
import os
from pathlib import Path

import agent_runtime as rt


output_dir = Path(os.environ["DESIGN_OS_OUTPUT_DIR"])
inputs = json.loads(os.environ["DESIGN_OS_INPUTS_JSON"])
payload = json.dumps(
    {
        "pipeline": os.environ["DESIGN_OS_PIPELINE_ID"],
        "step": os.environ["DESIGN_OS_STEP_ID"],
        "attempt": os.environ["DESIGN_OS_ATTEMPT_ID"],
        "headless_raw": os.environ.get("HEADLESS_RAW"),
        "headless_keep_addons": os.environ.get("HEADLESS_KEEP_ADDONS"),
        "project_inputs": sorted(inputs["project"]),
        "artifact_inputs": sorted(inputs["artifacts"]),
    },
    sort_keys=True,
).encode("utf-8")
path = output_dir / "artifact.json"
path.write_bytes(payload)
rt.emit_ok("native-pipeline-valid", artifact_bytes=len(payload), part_count=1)

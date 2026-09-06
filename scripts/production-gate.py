#!/usr/bin/env python3
"""Production gate: does this .blend satisfy its build spec?

    python3 scripts/production-gate.py --scene part.blend --spec build.spec.json \
        --report out/report.json [--parts id,id] [--export-dir out/stl]

Exit codes (frozen contract):
    0  every selected part passed every applicable check
    1  a requirement failed (see report.failed[])
    2  invalid or incomplete input: bad spec, unknown units, missing target
       dimensions, unknown --parts id, missing scene, missing object
    3  execution error (uncaught exception, Blender crash, no sentinel)

The last stdout line is always AGENT_OK <json> or AGENT_FAIL <json>.
A pass is DIGITAL evidence only. See specs/README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from production_gate import CHECKER_VERSION, spec as spec_mod  # noqa: E402
from production_gate.report import sha256_file  # noqa: E402

DEFAULT_BLENDER = os.environ.get(
    "BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")
RUNNER = os.path.join(HERE, "production_gate", "run_in_blender.py")


def emit(ok, exit_code, message, **post):
    payload = {"step": "production-gate", "postconditions": dict(post, exit_code=exit_code),
               "error": None if ok else {"type": "GateFailure", "message": message,
                                         "traceback": None}}
    print(message)
    print(("AGENT_OK " if ok else "AGENT_FAIL ") + json.dumps(payload, default=str))
    return exit_code


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", required=True, help=".blend file to gate")
    ap.add_argument("--spec", required=True, help="build spec JSON")
    ap.add_argument("--report", required=True, help="where to write the report JSON")
    ap.add_argument("--parts", default=None, help="comma separated part ids")
    ap.add_argument("--export-dir", default=None,
                    help="write one binary STL per part (mm) plus manifest.json")
    ap.add_argument("--blender", default=DEFAULT_BLENDER)
    ap.add_argument("--timeout", type=float, default=900.0)
    return ap.parse_args(argv)


def main(argv=None):
    started = time.time()
    args = parse_args(argv)
    wanted = [p.strip() for p in args.parts.split(",")] if args.parts else None
    try:
        if not os.path.isfile(args.scene):
            raise spec_mod.SpecError("scene not found: %s" % args.scene)
        if not os.path.isfile(args.blender):
            raise spec_mod.SpecError("blender binary not found: %s" % args.blender)
        spec = spec_mod.load(args.spec)
        spec_mod.select_parts(spec, wanted)
    except spec_mod.SpecError as exc:
        return emit(False, 2, "GATE INPUT INVALID: %s" % exc, report=None)

    inputs = {"scene_sha256": sha256_file(args.scene),
              "spec_sha256": sha256_file(args.spec)}
    cmd = [args.blender, "--factory-startup", "--disable-autoexec", "-b", args.scene,
           "--python-exit-code", "3", "--python", RUNNER, "--",
           "--scene", args.scene, "--spec", args.spec, "--report", args.report]
    if wanted:
        cmd += ["--parts", ",".join(wanted)]
    if args.export_dir:
        cmd += ["--export-dir", args.export_dir]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return emit(False, 3, "GATE ERROR: blender timed out after %ss" % args.timeout,
                    report=None)
    if os.environ.get("PRODUCTION_GATE_VERBOSE"):
        sys.stderr.write(proc.stdout + proc.stderr)
    line = next((ln for ln in reversed(proc.stdout.splitlines())
                 if ln.startswith(("AGENT_OK ", "AGENT_FAIL "))), None)
    if line is None:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])
        return emit(False, 3, "GATE ERROR: no sentinel from blender (exit %d)\n%s"
                    % (proc.returncode, tail), report=None)
    ok = line.startswith("AGENT_OK ")
    payload = json.loads(line.split(" ", 1)[1])
    code = int(payload.get("postconditions", {}).get("exit_code", 3))
    failed = payload.get("postconditions", {}).get("failed") or []
    summary = _summarise(args, code, failed, payload, inputs, started)
    print(summary)
    payload["postconditions"]["inputs"] = inputs
    payload["postconditions"]["checker_version"] = CHECKER_VERSION
    print(("AGENT_OK " if ok and code == 0 else "AGENT_FAIL ")
          + json.dumps(payload, default=str))
    return code


def _summarise(args, code, failed, payload, inputs, started):
    verdict = {0: "PASS", 1: "FAIL", 2: "INPUT INVALID", 3: "EXECUTION ERROR"}.get(code, "?")
    detail = ""
    if os.path.isfile(args.report):
        with open(args.report, "r", encoding="utf-8") as fh:
            rep = json.load(fh)
        nfail = sum(1 for p in rep["parts"] for c in p["checks"] if c["status"] == "fail")
        detail = (" | %d part(s), %d failing check(s), %d unchecked item(s)"
                  % (len(rep["parts"]), nfail, len(rep["coverage"]["unchecked"])))
    return ("GATE %s%s | failed=%s | scene=%s spec=%s | report=%s | %.1fs | "
            "DIGITAL CHECKS ONLY, not load/fit/print evidence"
            % (verdict, detail, ",".join(failed) or "-", inputs["scene_sha256"][:12],
               inputs["spec_sha256"][:12], args.report, time.time() - started))


if __name__ == "__main__":
    sys.exit(main())

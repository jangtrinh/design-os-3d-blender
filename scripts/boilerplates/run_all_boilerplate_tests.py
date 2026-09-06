#!/usr/bin/env python3
"""run_all_boilerplate_tests.py — sentinel-contract runner for every bp_*.py boilerplate.

Each module is executed in a fresh headless Blender through a generated shim that
runs it as ``__main__``, catches everything, and prints the sentinel line last:

    AGENT_OK   {"step": ..., "postconditions": {...}, "error": null}
    AGENT_FAIL {"step": ..., "postconditions": {}, "error": {type, message, traceback}}

A module PASSES only if the last non-empty stdout line starts with ``AGENT_OK ``.
Printed prose (the old "verified successfully" magic string) decides nothing, and
Blender's own exit code — unreliable in both directions — is recorded, not trusted.

Exit codes: 0 all passed · 1 one or more modules failed · 2 bad invocation/no modules.

Usage:
    python3 scripts/boilerplates/run_all_boilerplate_tests.py
    python3 scripts/boilerplates/run_all_boilerplate_tests.py --list
    python3 scripts/boilerplates/run_all_boilerplate_tests.py --only bp_core.py bp_rigging.py
"""

import argparse
import ast
import glob
import json
import os
import subprocess
import sys
import tempfile
import time

BLENDER_BIN = os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Executed inside Blender. argv after "--" is the module path. os._exit keeps the
# sentinel as the genuinely last stdout line (Blender prints "Blender quit" on a
# normal teardown) and makes the process exit code match the frozen contract.
SHIM_SOURCE = '''
import json, os, runpy, sys, traceback

path = sys.argv[sys.argv.index("--") + 1]
step = os.path.basename(path)

def _emit(tag, payload, code):
    print(tag + " " + json.dumps(payload), flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

try:
    runpy.run_path(path, run_name="__main__")
except AssertionError as exc:
    _emit("AGENT_FAIL", {"step": step, "postconditions": {},
                         "error": {"type": "AssertionError", "message": str(exc),
                                   "traceback": traceback.format_exc()}}, 1)
except BaseException as exc:
    _emit("AGENT_FAIL", {"step": step, "postconditions": {},
                         "error": {"type": type(exc).__name__, "message": str(exc),
                                   "traceback": traceback.format_exc()}}, 3)
_emit("AGENT_OK", {"step": step, "postconditions": {"module_main_completed": True},
                   "error": None}, 0)
'''


def discover(only=None):
    """Return sorted absolute paths of every bp_*.py under this directory."""
    paths = sorted(glob.glob(os.path.join(SCRIPT_DIR, "**", "bp_*.py"), recursive=True))
    if only:
        wanted = set(only)
        paths = [p for p in paths
                 if os.path.basename(p) in wanted or os.path.relpath(p, SCRIPT_DIR) in wanted]
    return paths


def first_doc_line(path):
    """First line of the module docstring, read without importing bpy."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = ast.get_docstring(ast.parse(fh.read(), filename=path)) or ""
    except (OSError, SyntaxError) as exc:
        return "<unreadable: %s>" % type(exc).__name__
    return doc.strip().splitlines()[0].strip() if doc.strip() else ""


def sentinel_of(stdout):
    """Last non-empty stdout line, plus its parsed sentinel tag and payload."""
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    for tag in ("AGENT_OK", "AGENT_FAIL"):
        if last.startswith(tag + " "):
            try:
                return tag, json.loads(last[len(tag) + 1:]), last
            except json.JSONDecodeError:
                return tag + "_BADJSON", None, last
    return None, None, last


def run_one(path, shim_path):
    """Execute one module in a fresh Blender; return a result record."""
    rel = os.path.relpath(path, SCRIPT_DIR)
    cmd = [BLENDER_BIN, "--factory-startup", "-b", "--python-exit-code", "3",
           "--python", shim_path, "--", path]
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    elapsed = round(time.time() - t0, 2)
    tag, payload, last = sentinel_of(proc.stdout)
    rec = {"module": rel, "rc": proc.returncode, "seconds": elapsed,
           "sentinel": tag or "MISSING", "verdict": "PASS" if tag == "AGENT_OK" else "FAIL"}
    if rec["verdict"] == "FAIL":
        err = (payload or {}).get("error") or {}
        rec["error"] = err.get("type", "no-sentinel")
        rec["message"] = (err.get("message") or last)[:300]
        rec["stderr_tail"] = proc.stderr[-400:]
        rec["stdout_tail"] = proc.stdout[-400:]
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true",
                    help="print the generated module registry as JSON and exit")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="run only these modules (basename or path relative to this dir)")
    args = ap.parse_args(argv)

    scripts = discover(args.only)
    if not scripts:
        print("no bp_*.py modules found under %s" % SCRIPT_DIR, file=sys.stderr)
        return 2

    if args.list:
        print(json.dumps({"root": os.path.relpath(SCRIPT_DIR, os.path.dirname(os.path.dirname(SCRIPT_DIR))),
                          "count": len(scripts),
                          "modules": [{"path": os.path.relpath(p, SCRIPT_DIR),
                                       "doc": first_doc_line(p)} for p in scripts]},
                         indent=2))
        return 0

    if not os.path.exists(BLENDER_BIN):
        print("BLENDER_BIN not found: %s" % BLENDER_BIN, file=sys.stderr)
        return 2

    print("=" * 60)
    print("RUNNING %d BOILERPLATE MODULES (sentinel contract: last stdout line)" % len(scripts))
    print("Blender: %s" % BLENDER_BIN)
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="bp_shim_") as tmp:
        shim_path = os.path.join(tmp, "sentinel_shim.py")
        with open(shim_path, "w", encoding="utf-8") as fh:
            fh.write(SHIM_SOURCE)
        results = []
        t0 = time.time()
        for path in scripts:
            rec = run_one(path, shim_path)
            results.append(rec)
            print("[%-4s] %-58s rc=%-3s %5.2fs  %s"
                  % (rec["verdict"], rec["module"], rec["rc"], rec["seconds"], rec["sentinel"]))
            if rec["verdict"] == "FAIL":
                print("        %s: %s" % (rec.get("error"), rec.get("message", "")))
        wall = round(time.time() - t0, 2)

    failed = [r for r in results if r["verdict"] == "FAIL"]
    print("=" * 60)
    print("RESULTS: %d/%d PASSED in %.2fs" % (len(results) - len(failed), len(results), wall))
    if failed:
        print("FAILED: %s" % ", ".join(r["module"] for r in failed))
    summary = {"total": len(results), "passed": len(results) - len(failed),
               "failed": [r["module"] for r in failed], "seconds": wall,
               "blender": BLENDER_BIN, "results": results}
    print("SUMMARY_JSON " + json.dumps(summary))
    ok = not failed
    print(("AGENT_OK " if ok else "AGENT_FAIL ") + json.dumps({
        "step": "run_all_boilerplate_tests",
        "postconditions": {"total": summary["total"], "passed": summary["passed"]},
        "error": None if ok else {"type": "BoilerplateFailure",
                                  "message": "%d module(s) failed" % len(failed),
                                  "traceback": ""}}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

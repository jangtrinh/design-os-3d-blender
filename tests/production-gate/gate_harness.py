"""Shared harness: one generated fixture set for every gate test module."""
import atexit
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_specs as fs  # noqa: E402

ROOT = fs.ROOT
GATE = os.path.join(ROOT, "scripts", "production-gate.py")
MAKER = os.path.join(ROOT, "tests", "production-gate", "make_fixtures.py")
BLENDER = os.environ.get("BLENDER_BIN",
                         "/Applications/Blender.app/Contents/MacOS/Blender")
_TMP = None
_SEQ = itertools.count(1)


def _cleanup():
    if _TMP and os.environ.get("KEEP_GATE_FIXTURES") != "1":
        shutil.rmtree(_TMP, ignore_errors=True)


def tmp():
    """Generate the fixtures once per test process; reused by every module."""
    global _TMP
    if _TMP is None:
        _TMP = tempfile.mkdtemp(prefix="production-gate-")
        atexit.register(_cleanup)
        proc = subprocess.run(
            [BLENDER, "--factory-startup", "-b", "--python-exit-code", "3",
             "--python", MAKER, "--", "--out", _TMP],
            capture_output=True, text=True, timeout=600)
        if "FIXTURES_OK" not in proc.stdout:
            raise RuntimeError("fixture generation failed:\n%s\n%s"
                               % (proc.stdout[-2000:], proc.stderr[-2000:]))
    return _TMP


def write_spec(spec, name):
    return fs.write(spec, os.path.join(tmp(), name))


def run_gate(scene, spec_path, extra=(), report=None):
    root = tmp()
    report = report or os.path.join(root, "report-%s-%d.json" % (scene, next(_SEQ)))
    cmd = [sys.executable, GATE, "--scene", os.path.join(root, scene + ".blend"),
           "--spec", spec_path, "--report", report] + list(extra)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return proc.returncode, proc.stdout, load(report)


def load(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def statuses(rep, part=0):
    return {c["name"]: c["status"] for c in rep["parts"][part]["checks"]}

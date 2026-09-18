"""Contract tests for scripts/check-pass-coverage.py (host Python, no bpy)."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("check_pass_coverage", ROOT / "scripts" / "check-pass-coverage.py")
coverage = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(coverage)


def build_with(tmp: Path, passes, steps, allow=None):
    """Write a throwaway build directory: pass scripts, one manifest, optional allowlist."""
    for name in passes:
        (tmp / name).write_text("# pass\n")
    (tmp / "demo-pipeline.json").write_text(json.dumps({
        "version": 1,
        "pipeline_id": "demo",
        "steps": [{"id": f"s{i}", "script": f"builds/demo/{script}"} for i, script in enumerate(steps)],
    }))
    if allow is not None:
        (tmp / "pass-coverage-allow.json").write_text(json.dumps({"unreferenced": allow}))
    return tmp


class PassCoverageTest(unittest.TestCase):
    def test_every_authored_pass_declared_is_clean(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = build_with(Path(raw), ["pass-01-a.py", "pass-02-b.py"], ["pass-01-a.py", "pass-02-b.py"])
            result = coverage.audit(tmp)
        self.assertEqual(result["unreferenced"], [])
        self.assertEqual(result["missing_scripts"], [])
        self.assertEqual(result["declared"], ["pass-01-a.py", "pass-02-b.py"])

    def test_authored_but_undeclared_pass_is_reported(self):
        """The CK-001 defect: pass-B-rotation.py was written and never run."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = build_with(Path(raw), ["pass-01-a.py", "pass-B-rotation.py"], ["pass-01-a.py"])
            result = coverage.audit(tmp)
        self.assertEqual([entry["pass"] for entry in result["unreferenced"]], ["pass-B-rotation.py"])

    def test_allowlist_entry_with_a_reason_excuses_a_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = build_with(Path(raw), ["pass-01-a.py", "pass-07-reopen.py"], ["pass-01-a.py"],
                             allow={"pass-07-reopen.py": "run inline by pass-06"})
            result = coverage.audit(tmp)
        self.assertEqual(result["unreferenced"], [])
        self.assertEqual(result["excused"], [{"pass": "pass-07-reopen.py", "reason": "run inline by pass-06"}])

    def test_allowlist_entry_without_a_reason_still_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = build_with(Path(raw), ["pass-01-a.py", "pass-09-x.py"], ["pass-01-a.py"],
                             allow={"pass-09-x.py": ""})
            result = coverage.audit(tmp)
        self.assertEqual([entry["pass"] for entry in result["unreferenced"]], ["pass-09-x.py"])
        self.assertTrue(result["unreferenced"][0]["empty_reason"])

    def test_declared_step_without_a_file_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = build_with(Path(raw), ["pass-01-a.py"], ["pass-01-a.py", "pass-99-gone.py"])
            result = coverage.audit(tmp)
        self.assertEqual([entry["pass"] for entry in result["missing_scripts"]], ["pass-99-gone.py"])

    def test_unreadable_manifest_is_reported_not_swallowed(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "pass-01-a.py").write_text("# pass\n")
            (tmp / "broken-pipeline.json").write_text("{not json")
            result = coverage.audit(tmp)
        self.assertEqual(len(result["unreadable_manifests"]), 1)
        self.assertEqual(result["unreadable_manifests"][0][0], "broken-pipeline.json")

    def test_real_builds_are_auditable(self):
        """The shipped builds parse; this asserts the audit runs, not that they are clean."""
        builds = [p for p in (ROOT / "builds").glob("*") if p.is_dir() and any(p.glob("pass-*.py"))]
        self.assertTrue(builds, "no build with pass scripts found")
        for build in builds:
            result = coverage.audit(build)
            self.assertIn("authored", result)
            self.assertEqual(result["unreadable_manifests"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

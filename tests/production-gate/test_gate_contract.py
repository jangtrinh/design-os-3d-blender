"""Gate contract: exit codes, sentinel, hashes, determinism, coverage.

Fixtures are generated from primitives into a temp dir; builds/ is never read.
"""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_specs as fs  # noqa: E402
from gate_harness import GATE, run_gate, statuses, tmp, write_spec  # noqa: E402


class TestContract(unittest.TestCase):
    def test_sentinel_is_last_line(self):
        code, out, _rep = run_gate("positive", fs.EXAMPLE)
        self.assertEqual(code, 0, out)
        self.assertTrue(out.strip().splitlines()[-1].startswith("AGENT_OK "), out)

    def test_incomplete_spec_exits_2(self):
        path = write_spec(fs.incomplete(), "incomplete.spec.json")
        code, out, rep = run_gate("positive", path)
        self.assertEqual(code, 2, out)
        self.assertIn("target_dims_mm", out)
        self.assertIsNone(rep)
        self.assertTrue(out.strip().splitlines()[-1].startswith("AGENT_FAIL "))

    def test_unknown_part_id_exits_2(self):
        code, out, _rep = run_gate("positive", fs.EXAMPLE, ["--parts", "no-such-part"])
        self.assertEqual(code, 2, out)
        self.assertIn("no-such-part", out)

    def test_missing_scene_exits_2(self):
        proc = subprocess.run(
            [sys.executable, GATE, "--scene", os.path.join(tmp(), "nope.blend"),
             "--spec", fs.EXAMPLE, "--report", os.path.join(tmp(), "n.json")],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2, proc.stdout)

    def test_object_absent_from_scene_exits_2(self):
        spec = fs.base()
        spec["parts"][0]["object"] = "not-in-this-scene"
        path = write_spec(spec, "badobject.spec.json")
        code, out, _rep = run_gate("positive", path)
        self.assertEqual(code, 2, out)
        self.assertIn("missing from the scene", out)


class TestPositive(unittest.TestCase):
    def test_pass_and_export_manifest(self):
        exp = os.path.join(tmp(), "exp")
        code, out, rep = run_gate("positive", fs.EXAMPLE, ["--export-dir", exp])
        self.assertEqual(code, 0, out)
        self.assertEqual(rep["failed"], [])
        self.assertEqual(rep["required_checks_missing"], [])
        with open(os.path.join(exp, "manifest.json"), "r", encoding="utf-8") as fh:
            man = json.load(fh)
        self.assertEqual(len(man["parts"]), 1)
        entry = man["parts"][0]
        self.assertEqual(len(entry["sha256"]), 64)
        self.assertGreater(entry["triangles"], 0)
        self.assertTrue(os.path.isfile(entry["file"]))
        for k in range(3):
            self.assertAlmostEqual(entry["dims_mm"][k], [40.0, 20.0, 6.0][k], delta=0.05)
        st = statuses(rep)
        self.assertEqual(st["roundtrip_bbox_dims_mm"], "pass")
        self.assertEqual(st["roundtrip_non_manifold_edges"], "pass")

    def test_report_is_deterministic(self):
        a = os.path.join(tmp(), "det-a.json")
        b = os.path.join(tmp(), "det-b.json")
        run_gate("positive", fs.EXAMPLE, report=a)
        run_gate("positive", fs.EXAMPLE, report=b)
        def _load(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        ra, rb = _load(a), _load(b)
        for r in (ra, rb):
            r.pop("timestamp"), r.pop("duration_s")
        self.assertEqual(ra, rb)

    def test_one_byte_of_spec_changes_the_hash(self):
        spec = fs.base()
        spec["parts"][0]["tol_mm"] = 0.21
        path = write_spec(spec, "tweaked.spec.json")
        _c1, _o1, r1 = run_gate("positive", fs.EXAMPLE, report=os.path.join(tmp(), "h1.json"))
        _c2, _o2, r2 = run_gate("positive", path, report=os.path.join(tmp(), "h2.json"))
        self.assertEqual(r1["inputs"]["scene_sha256"], r2["inputs"]["scene_sha256"])
        self.assertNotEqual(r1["inputs"]["spec_sha256"], r2["inputs"]["spec_sha256"])

    def test_required_check_that_never_runs_fails_the_gate(self):
        spec = fs.base()
        spec["required_checks"] = ["a_check_that_does_not_exist"]
        path = write_spec(spec, "required.spec.json")
        code, out, rep = run_gate("positive", path,
                                  report=os.path.join(tmp(), "required.json"))
        self.assertEqual(code, 1, out)
        self.assertEqual(rep["required_checks_missing"], ["a_check_that_does_not_exist"])
        self.assertIn("required_check", " ".join(rep["coverage"]["unchecked"]))

    def test_coverage_names_what_was_not_checked(self):
        _c, _o, rep = run_gate("positive", fs.EXAMPLE)
        joined = " ".join(rep["coverage"]["unchecked"])
        self.assertIn("export round trip", joined)
        self.assertTrue(any("load capacity" in e for e in rep["exclusions"]))



if __name__ == "__main__":
    unittest.main()

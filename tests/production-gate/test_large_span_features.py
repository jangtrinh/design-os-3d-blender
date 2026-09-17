"""Regression for axial hole probes on parts whose largest span exceeds 200 mm."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_specs as fs  # noqa: E402
from gate_harness import BLENDER, GATE, statuses  # noqa: E402


ROOT = fs.ROOT
MAKER_DIR = os.path.join(ROOT, "tests", "production-gate")


def _spec(path):
    spec = fs.base()
    spec["print_volume_mm"] = [320.0, 200.0, 100.0]
    spec["brim_margin_mm"] = 5.0
    part = spec["parts"][0]
    part["target_dims_mm"] = [284.0, 92.0, 4.0]
    part["tol_mm"] = 0.05
    part.pop("min_wall_mm", None)
    part["features"] = [{"id": "center", "type": "hole", "axis": "z",
                         "center_mm": [0.0, 0.0, 0.0],
                         "diameter_mm": 3.4, "tol_mm": 0.05}]
    spec["required_checks"] = ["feature_center_bore_clear",
                               "feature_center_material_around",
                               "feature_center_diameter_mm"]
    return fs.write(spec, path)


def _make_scene(out_dir, name, with_hole):
    holes = "[(0.0, 0.0, 3.4)]" if with_hole else "[]"
    expr = (
        "import sys; sys.path.insert(0, %r); import make_fixtures as m; "
        "m.reset(); m.plate(length=284.0,width=92.0,thick=4.0,holes=%s); "
        "m.save(%r,%r)" % (MAKER_DIR, holes, out_dir, name))
    proc = subprocess.run([BLENDER, "--factory-startup", "-b", "--python-exit-code", "3",
                           "--python-expr", expr], capture_output=True, text=True,
                          timeout=600)
    if proc.returncode:
        raise RuntimeError("wide fixture generation failed:\n%s\n%s" %
                           (proc.stdout[-2000:], proc.stderr[-2000:]))
    return os.path.join(out_dir, name + ".blend")


def _gate(scene, spec, report):
    proc = subprocess.run([sys.executable, GATE, "--scene", scene, "--spec", spec,
                           "--report", report], capture_output=True, text=True, timeout=600)
    with open(report, "r", encoding="utf-8") as fh:
        return proc.returncode, proc.stdout, json.load(fh)


class TestLargeSpanFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="gate-large-span-")
        cls.spec = _spec(os.path.join(cls.tmp.name, "wide.spec.json"))
        cls.hole = _make_scene(cls.tmp.name, "wide-hole", True)
        cls.filled = _make_scene(cls.tmp.name, "wide-filled", False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_284mm_plate_through_hole_passes_axial_and_radial_checks(self):
        code, out, rep = _gate(self.hole, self.spec,
                               os.path.join(self.tmp.name, "wide-hole-report.json"))
        self.assertEqual(code, 0, out + "\n" + json.dumps(statuses(rep), indent=2))
        st = statuses(rep)
        self.assertEqual(st["feature_center_bore_clear"], "pass")
        self.assertEqual(st["feature_center_material_around"], "pass")
        self.assertEqual(st["feature_center_diameter_mm"], "pass")
        probe = rep["parts"][0]["measured"]["features"]["center"]["axial_probe"]
        self.assertAlmostEqual(probe["projected_max_mm"] - probe["projected_min_mm"],
                               4.0, delta=0.01)
        self.assertGreater(probe["ray_length_mm"], 4.0)

    def test_filled_plate_still_fails_bore_predicate(self):
        code, out, rep = _gate(self.filled, self.spec,
                               os.path.join(self.tmp.name, "wide-filled-report.json"))
        self.assertEqual(code, 1, out)
        st = statuses(rep)
        self.assertEqual(st["feature_center_bore_clear"], "fail")
        self.assertEqual(st["feature_center_material_around"], "pass")
        self.assertEqual(st["feature_center_diameter_mm"], "fail")


if __name__ == "__main__":
    unittest.main()

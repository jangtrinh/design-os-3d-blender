"""Predicate behaviour: every negative fixture, plus falsification of the
self-intersection and bore-diameter measurements against known geometry."""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_specs as fs  # noqa: E402
from gate_harness import GATE, run_gate, statuses, tmp, write_spec  # noqa: E402


class TestNegatives(unittest.TestCase):
    def _fails(self, scene, check_name, spec_path=None):
        code, out, rep = run_gate(scene, spec_path or fs.EXAMPLE)
        self.assertEqual(code, 1, out)
        self.assertEqual(rep["failed"], ["bracket-m3"])
        self.assertEqual(statuses(rep).get(check_name), "fail",
                         json.dumps(statuses(rep), indent=1))
        return rep

    def test_heatset_deeper_than_plate_fails(self):
        """M3 heat-set inserts need 7.0 mm of material; the 6 mm plate cannot hold
        one even when the pilot bore itself is within tolerance. With no depth_mm
        declared the gate derives available depth from the part thickness."""
        spec = fs.base()
        pilot = [f for f in spec["parts"][0]["features"] if f["id"] == "pilot"][0]
        pilot["fastener"] = {"standard": "heatset", "size": "M3"}
        pilot["tol_mm"] = 0.5  # keep diameter/table checks out of the way
        rep = self._fails("positive", "feature_pilot_heatset_depth",
                          write_spec(spec, "heatset-m3-on-6mm"))
        self.assertIn("derived from target_dims_mm",
                      json.dumps(rep["parts"][0]["checks"]))

    def test_non_manifold(self):
        rep = self._fails("nonmanifold", "non_manifold_edges")
        self.assertGreater(rep["parts"][0]["measured"]["non_manifold_edges"], 0)

    def test_wrong_dimension(self):
        rep = self._fails("wrongdim", "bbox_dims_mm")
        self.assertAlmostEqual(rep["parts"][0]["measured"]["bbox_dims_mm"][0], 44.0,
                               delta=0.05)

    def test_thin_wall(self):
        rep = self._fails("thinwall", "wall_thickness_screen")
        self.assertLess(rep["parts"][0]["measured"]["wall_min_mm"], 1.5)

    def test_missing_hole(self):
        rep = self._fails("missinghole", "feature_clear_b_bore_clear")
        self.assertEqual(statuses(rep)["feature_clear_a_diameter_mm"], "pass")

    def test_unapplied_scale_despite_correct_world_dims(self):
        rep = self._fails("unappliedscale", "scale_applied")
        st = statuses(rep)
        self.assertEqual(st["bbox_dims_mm"], "pass")
        self.assertEqual(rep["parts"][0]["measured"]["object_scale"], [2.0, 2.0, 2.0])


class TestExecutionErrors(unittest.TestCase):
    def test_no_sentinel_from_blender_exits_3(self):
        stub = os.path.join(tmp(), "fake-blender")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\necho 'this build prints no sentinel'\nexit 0\n")
        os.chmod(stub, 0o755)
        proc = subprocess.run(
            [sys.executable, GATE, "--scene", os.path.join(tmp(), "positive.blend"),
             "--spec", fs.EXAMPLE, "--report", os.path.join(tmp(), "never.json"),
             "--blender", stub], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3, proc.stdout)
        self.assertIn("no sentinel", proc.stdout)
        self.assertTrue(proc.stdout.strip().splitlines()[-1].startswith("AGENT_FAIL "))


class TestPredicateFalsification(unittest.TestCase):
    def test_known_diameters_within_0_05_mm(self):
        path = write_spec(fs.calibration(), "calib.spec.json")
        code, out, rep = run_gate("calibration", path)
        self.assertEqual(code, 0, out)
        feats = rep["parts"][0]["measured"]["features"]
        self.assertAlmostEqual(feats["known34"]["measured_diameter_mm"], 3.4, delta=0.05)
        self.assertAlmostEqual(feats["known50"]["measured_diameter_mm"], 5.0, delta=0.05)

    def test_overlapping_solids_are_flagged(self):
        path = write_spec(fs.topology_only([40.0, 20.0, 8.0], shells=2), "si.spec.json")
        code, out, rep = run_gate("selfintersect", path)
        self.assertEqual(code, 1, out)
        st = statuses(rep)
        self.assertEqual(st["self_intersection_pairs"], "fail")
        self.assertEqual(st["non_manifold_edges"], "pass")

    def test_clean_torus_is_not_flagged(self):
        path = write_spec(fs.topology_only([50.0, 50.0, 10.0]), "torus.spec.json")
        code, out, rep = run_gate("torus", path)
        self.assertEqual(code, 0, out)
        self.assertEqual(statuses(rep)["self_intersection_pairs"], "pass")



if __name__ == "__main__":
    unittest.main()

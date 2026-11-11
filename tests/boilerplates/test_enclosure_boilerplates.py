#!/usr/bin/env python3
"""Host-side unit tests for bp_enclosure_joints.py and bp_parametric_perforations.py."""

import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
JOINTS_PATH = ROOT / "scripts" / "boilerplates" / "dfam_3dprint" / "bp_enclosure_joints.py"
PERF_PATH = ROOT / "scripts" / "boilerplates" / "dfam_3dprint" / "bp_parametric_perforations.py"

# Dynamic import of modules
spec_j = importlib.util.spec_from_file_location("bp_enclosure_joints", JOINTS_PATH)
mod_joints = importlib.util.module_from_spec(spec_j)
spec_j.loader.exec_module(mod_joints)

spec_p = importlib.util.spec_from_file_location("bp_parametric_perforations", PERF_PATH)
mod_perf = importlib.util.module_from_spec(spec_p)
spec_p.loader.exec_module(mod_perf)


class TestEnclosureJoints(unittest.TestCase):
    def test_hook_insertion_angle_math(self):
        # lip_depth 2.0 mm, hook_height 10.0 mm, clearance 0.25 mm -> tan(theta) = 2.25 / 10.0 = 0.225
        # theta = atan(0.225) ~ 12.68 deg
        angle = mod_joints.calculate_hook_insertion_angle(2.0, 10.0, clearance_mm=0.25)
        expected = math.degrees(math.atan2(2.25, 10.0))
        self.assertAlmostEqual(angle, expected, places=3)

    def test_hook_insertion_angle_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            mod_joints.calculate_hook_insertion_angle(-1.0, 10.0)
        with self.assertRaises(ValueError):
            mod_joints.calculate_hook_insertion_angle(2.0, 0.0)

    def test_button_beam_deflection_strain_and_force(self):
        # 12mm length, 1.5mm thickness, 0.8mm travel, 5mm width, 2.2 GPa PETG
        res = mod_joints.calculate_button_beam_deflection(
            beam_length_mm=12.0,
            beam_thickness_mm=1.5,
            switch_travel_mm=0.8,
            modulus_gpa=2.2,
            beam_width_mm=5.0,
        )
        self.assertIn("actuation_force_n", res)
        self.assertIn("fiber_strain", res)
        self.assertGreater(res["actuation_force_n"], 0.0)
        # Expected strain = 1.5 * 0.8 * 1.5 / (12^2) = 1.8 / 144 = 0.0125 (1.25%)
        self.assertAlmostEqual(res["fiber_strain"], 0.0125, places=4)
        self.assertTrue(res["is_safe_repeated_use"])

    def test_button_beam_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            mod_joints.calculate_button_beam_deflection(0.0, 1.5)


class TestParametricPerforations(unittest.TestCase):
    def test_open_area_ratio_hexagonal_and_square(self):
        # Hexagonal: r = 0.6 mm, pitch = 2.0 mm
        # Area ratio = (2 * pi * 0.36) / (sqrt(3) * 4) = 2.2619 / 6.9282 ~ 0.3265
        hex_ratio = mod_perf.calculate_acoustic_open_area_ratio(0.6, 2.0, pattern="hexagonal")
        expected_hex = (2.0 * math.pi * 0.36) / (math.sqrt(3.0) * 4.0)
        self.assertAlmostEqual(hex_ratio, round(expected_hex, 4), places=4)

        # Square: r = 0.6 mm, pitch = 2.0 mm -> pi * 0.36 / 4 = 1.13097 / 4 ~ 0.2827
        sq_ratio = mod_perf.calculate_acoustic_open_area_ratio(0.6, 2.0, pattern="square")
        expected_sq = (math.pi * 0.36) / 4.0
        self.assertAlmostEqual(sq_ratio, round(expected_sq, 4), places=4)

    def test_open_area_ratio_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            mod_perf.calculate_acoustic_open_area_ratio(1.5, 2.0)  # 2*r > pitch
        with self.assertRaises(ValueError):
            mod_perf.calculate_acoustic_open_area_ratio(0.5, 2.0, pattern="triangle")

    def test_min_ligament_thickness(self):
        res = mod_perf.calculate_min_ligament_thickness(pitch_mm=2.5, hole_diameter_mm=1.2, min_wall_mm=1.2)
        # Ligament = 2.5 - 1.2 = 1.3 mm >= 1.2 mm -> printable
        self.assertAlmostEqual(res["ligament_thickness_mm"], 1.3, places=3)
        self.assertTrue(res["is_printable"])

        res_fail = mod_perf.calculate_min_ligament_thickness(pitch_mm=2.0, hole_diameter_mm=1.2, min_wall_mm=1.2)
        # Ligament = 0.8 mm < 1.2 mm -> not printable
        self.assertFalse(res_fail["is_printable"])

    def test_graded_radial_coords(self):
        rings = [(2.0, 6), (4.0, 12)]
        coords = mod_perf.generate_graded_radial_coords(center_xy=(0.0, 0.0), rings=rings)
        self.assertEqual(len(coords), 18)
        # Radius of first 6 points should be 2.0
        for x, y in coords[:6]:
            r = math.sqrt(x ** 2 + y ** 2)
            self.assertAlmostEqual(r, 2.0, places=3)


if __name__ == "__main__":
    unittest.main()

"""Real Blender regression: sampled wall thickness must survive world translation.

Axial dimensions in these fixtures remain representable at the tested offsets.
Recentring cannot reconstruct detail that an input mesh has already quantized away.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BLENDER = os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")
CHILD = "--blender-child"
OFFSETS = ((0.0, 0.0, 0.0), (0.0, 0.0, 2453.0),
           (120000.0, -95000.0, 32000.0), (-1000000.0, 750000.0, 2453.0))


def _child_main():
    import bmesh

    sys.path[:0] = [str(ROOT / "scripts"), str(Path(__file__).parent)]
    from production_gate import walls_overhang
    from test_small_surface_walls import _annulus_bmesh

    assert walls_overhang.EPS_MM == 1e-4
    assert walls_overhang.MAX_RAY_MM == 50.0
    assert walls_overhang.MIN_FACE_AREA_MM2 == 0.3
    results = {}

    def measure(bm, expected, minimum=12.0):
        before = [tuple(v.co) for v in bm.verts]
        normals_before = [tuple(f.normal) for f in bm.faces]
        checks, measured = walls_overhang.wall_checks(bm, minimum)
        assert checks[0]["status"] == expected, (checks, measured)
        assert measured["wall_sampling_frame"] == "bbox-centered-mm", measured
        assert before == [tuple(v.co) for v in bm.verts]
        assert normals_before == [tuple(f.normal) for f in bm.faces]
        return {"status": checks[0]["status"], "measured": measured,
                "caller_coordinates_and_normals_unchanged": True}

    for index, offset in enumerate(OFFSETS):
        for label, thickness, expected in (("thick", 14.0, "pass"), ("thin", 1.0, "fail")):
            bm = _annulus_bmesh(70.0, height_mm=thickness, outer_radius_mm=215.0)
            try:
                for vertex in bm.verts:
                    vertex.co = tuple(float(vertex.co[i]) + offset[i] for i in range(3))
                bm.normal_update()
                result = measure(bm, expected)
                measured = result["measured"]
                assert measured["wall_candidate_faces"] == 768, measured
                assert measured["wall_ray_samples"] == 384, measured
                assert measured["wall_sampling_mode"] == "area-threshold", measured
                assert measured["wall_face_area_threshold_mm2"] == 0.3, measured
                assert abs(measured["wall_min_mm"] - thickness) < 0.005, measured
                result["offset_mm"] = list(offset)
                result["authored_axial_thickness_mm"] = thickness
                results[f"{label}_{index}"] = result
            finally:
                bm.free()

    for label, both_sheets in (("missing_opposing_wall", False), ("same_facing_sheets", True)):
        bm = bmesh.new()
        try:
            for z in ((2453.0, 2458.0) if both_sheets else (2453.0,)):
                verts = [bm.verts.new((120000.0 + x, -95000.0 + y, z))
                         for x, y in ((-10, -10), (10, -10), (10, 10), (-10, 10))]
                bm.faces.new(verts)  # Both normals deliberately point +Z.
            bm.normal_update()
            result = measure(bm, "fail")
            assert result["measured"]["wall_candidate_faces"] > 0
            assert result["measured"]["wall_ray_samples"] == 0
            results[label] = result
        finally:
            bm.free()

    for label, coordinates in (("empty", ()),
                               ("degenerate", ((120000, 0, 2453), (120001, 0, 2453), (120002, 0, 2453)))):
        bm = bmesh.new()
        try:
            if coordinates:
                bm.faces.new([bm.verts.new(co) for co in coordinates])
            bm.normal_update()
            result = measure(bm, "fail")
            assert result["measured"]["wall_sampling_mode"] == "no-positive-faces"
            assert result["measured"]["wall_ray_samples"] == 0
            results[label] = result
        finally:
            bm.free()

    print("WALL_ORIGIN " + json.dumps(results, sort_keys=True))


@unittest.skipUnless(Path(BLENDER).is_file(), "Blender missing")
class TestWallOrigin(unittest.TestCase):
    def test_actual_blender_translation_and_negative_controls(self):
        proc = subprocess.run(
            [BLENDER, "--factory-startup", "--disable-autoexec", "-b",
             "--python-exit-code", "3", "--python", str(Path(__file__).resolve()),
             "--", CHILD], capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        line = next((line for line in proc.stdout.splitlines() if line.startswith("WALL_ORIGIN ")), None)
        self.assertIsNotNone(line, proc.stdout)
        payload = json.loads(line.split(" ", 1)[1])
        self.assertEqual(len(payload), 12)
        for index in range(len(OFFSETS)):
            self.assertEqual(payload[f"thick_{index}"]["status"], "pass")
            self.assertEqual(payload[f"thin_{index}"]["status"], "fail")
        for name in ("empty", "degenerate", "missing_opposing_wall", "same_facing_sheets"):
            self.assertEqual(payload[name]["status"], "fail")
        print("WALL_ORIGIN_EVIDENCE " + json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    if CHILD in sys.argv:
        _child_main()
    else:
        unittest.main()

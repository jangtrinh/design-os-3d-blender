"""Wall-screen regression for finely faceted surfaces.

The host test launches one real Blender 5.2 background process.  The child builds
96-segment closed annuli whose triangles all fall below the production gate's
0.3 mm^2 primary face-area threshold, then exercises the public wall_checks API.
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


def _annulus_bmesh(radial_wall_mm, height_mm=1.6, outer_radius_mm=4.4, segments=96):
    import bmesh
    import math

    inner = outer_radius_mm - radial_wall_mm
    bm = bmesh.new()
    rings = []
    for z, radius in ((0.0, outer_radius_mm), (0.0, inner),
                      (height_mm, outer_radius_mm), (height_mm, inner)):
        rings.append([bm.verts.new((radius * math.cos(i * math.tau / segments),
                                   radius * math.sin(i * math.tau / segments), z))
                      for i in range(segments)])
    bo, bi, to, ti = rings
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((bo[i], bo[j], to[j], to[i]))
        bm.faces.new((bi[j], bi[i], ti[i], ti[j]))
        bm.faces.new((to[i], to[j], ti[j], ti[i]))
        bm.faces.new((bo[j], bo[i], bi[i], bi[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def _child_main():
    import bmesh

    sys.path.insert(0, str(ROOT / "scripts"))
    from production_gate import walls_overhang

    results = {}
    for name, radial, expected in (("thick", 1.5, "pass"), ("thin", 0.6, "fail")):
        bm = _annulus_bmesh(radial)
        try:
            checks, measured = walls_overhang.wall_checks(bm, 1.2)
            check = checks[0]
            assert check["status"] == expected, (name, check, measured)
            assert measured["wall_sampling_mode"] == "all-positive-faces-fallback", measured
            assert measured["wall_candidate_faces"] > 0, measured
            assert measured["wall_ray_samples"] > 0, measured
            assert measured["wall_primary_face_area_threshold_mm2"] == 0.3, measured
            assert measured["wall_face_area_threshold_mm2"] == 0.0, measured
            legacy_samples = walls_overhang.wall_samples(bm)
            assert isinstance(legacy_samples, list), type(legacy_samples)
            assert len(legacy_samples) == measured["wall_ray_samples"], measured
            tri = walls_overhang.meshprep.triangulated(bm)
            try:
                assert max(f.calc_area() for f in tri.faces) < 0.3
            finally:
                tri.free()
            results[name] = {"status": check["status"], "measured": measured,
                             "note": check["note"]}
        finally:
            bm.free()

    empty = bmesh.new()
    try:
        checks, measured = walls_overhang.wall_checks(empty, 1.2)
        assert checks[0]["status"] == "fail", (checks, measured)
        assert measured["wall_sampling_mode"] == "no-positive-faces", measured
        assert measured["wall_ray_samples"] == 0, measured
        assert measured["wall_candidate_faces"] == 0, measured
        results["empty"] = {"status": checks[0]["status"], "measured": measured,
                            "note": checks[0]["note"]}
    finally:
        empty.free()

    degenerate = bmesh.new()
    try:
        verts = [degenerate.verts.new((0.0, 0.0, 0.0)),
                 degenerate.verts.new((1.0, 0.0, 0.0)),
                 degenerate.verts.new((2.0, 0.0, 0.0))]
        degenerate.faces.new(verts)
        degenerate.normal_update()
        checks, measured = walls_overhang.wall_checks(degenerate, 1.2)
        assert checks[0]["status"] == "fail", (checks, measured)
        assert measured["wall_sampling_mode"] == "no-positive-faces", measured
        assert measured["wall_positive_area_faces"] == 0, measured
        results["degenerate"] = {"status": checks[0]["status"], "measured": measured,
                                 "note": checks[0]["note"]}
    finally:
        degenerate.free()

    coarse = bmesh.new()
    try:
        bmesh.ops.create_cube(coarse, size=4.0)
        coarse.normal_update()
        checks, measured = walls_overhang.wall_checks(coarse, 1.2)
        assert checks[0]["status"] == "pass", (checks, measured)
        assert measured["wall_sampling_mode"] == "area-threshold", measured
        assert measured["wall_face_area_threshold_mm2"] == 0.3, measured
        results["coarse_control"] = {"status": checks[0]["status"], "measured": measured,
                                     "note": checks[0]["note"]}
    finally:
        coarse.free()

    print("SMALL_SURFACE_WALLS " + json.dumps(results, sort_keys=True))


@unittest.skipUnless(Path(BLENDER).is_file(), "Blender missing")
class TestSmallSurfaceWalls(unittest.TestCase):
    def test_actual_blender_small_surface_fallback(self):
        proc = subprocess.run(
            [BLENDER, "--factory-startup", "--disable-autoexec", "-b",
             "--python-exit-code", "3", "--python", str(Path(__file__).resolve()),
             "--", CHILD],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        line = next((line for line in proc.stdout.splitlines()
                     if line.startswith("SMALL_SURFACE_WALLS ")), None)
        self.assertIsNotNone(line, proc.stdout)
        payload = json.loads(line.split(" ", 1)[1])
        self.assertEqual(payload["thick"]["status"], "pass")
        self.assertEqual(payload["thin"]["status"], "fail")
        self.assertEqual(payload["empty"]["status"], "fail")
        self.assertEqual(payload["degenerate"]["status"], "fail")
        self.assertEqual(payload["coarse_control"]["status"], "pass")
        self.assertEqual(payload["coarse_control"]["measured"]["wall_sampling_mode"],
                         "area-threshold")
        self.assertGreater(payload["thick"]["measured"]["wall_min_mm"], 1.2)
        self.assertLess(payload["thin"]["measured"]["wall_min_mm"], 1.2)


if __name__ == "__main__":
    if CHILD in sys.argv:
        _child_main()
    else:
        unittest.main()

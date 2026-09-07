"""Bed-fit preflight: does a part's measured footprint (+ brim) and height fit
inside a printer's build volume? Design-time SCREEN, no slicer involved.

Cases (a)/(b) reuse the "calibration" fixture (real bracket-m3 mesh measures
60x24x6 mm -- see tests/production-gate/gate_harness fixture generation).
Cases (c)/(c2) need footprints (250x250x10, 170x170x10 mm) that do not exist
in any pre-baked fixture, so this module generates its own plain-box .blend
fixtures on demand (mirrors make_fixtures.py::box, kept local so
make_fixtures.py stays untouched).
"""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_specs as fs  # noqa: E402
from gate_harness import BLENDER, run_gate, statuses, tmp  # noqa: E402

_BOX_GENERATOR = """
import sys
import bmesh
import bpy

MM = 0.001
argv = sys.argv[sys.argv.index("--") + 1:]
sx, sy, sz, out = float(argv[0]), float(argv[1]), float(argv[2]), argv[3]
bpy.ops.wm.read_homefile(use_empty=True)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.verts.ensure_lookup_table()
bmesh.ops.scale(bm, vec=(sx * MM, sy * MM, sz * MM), verts=bm.verts[:])
me = bpy.data.meshes.new("bracket-m3")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("bracket-m3", me)
bpy.context.scene.collection.objects.link(ob)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
"""


def _box_scene(name, dims_mm):
    """Generate (once) a plain axis-aligned box .blend of dims_mm, named so
    gate_harness.run_gate(name, ...) can address it directly."""
    root = tmp()
    out_path = os.path.join(root, name + ".blend")
    if os.path.isfile(out_path):
        return name
    script_path = os.path.join(root, "gen_" + name + ".py")
    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(_BOX_GENERATOR)
    proc = subprocess.run(
        [BLENDER, "--factory-startup", "-b", "--python-exit-code", "3",
         "--python", script_path, "--",
         str(dims_mm[0]), str(dims_mm[1]), str(dims_mm[2]), out_path],
        capture_output=True, text=True, timeout=120)
    if not os.path.isfile(out_path):
        raise RuntimeError("box scene %r generation failed:\n%s\n%s"
                           % (name, proc.stdout[-2000:], proc.stderr[-2000:]))
    return name


class TestBedFitFootprint(unittest.TestCase):
    def test_a_default_volume_and_margin_fits(self):
        """60x24x6 part, default bed (256^3) and default 5 mm brim -> fits."""
        path = fs.write(fs.bed([60.0, 24.0, 6.0]),
                        os.path.join(tmp(), "bedfit-a.spec.json"))
        code, out, rep = run_gate("calibration", path)
        self.assertEqual(code, 0, out)
        st = statuses(rep)
        self.assertEqual(st["bed_fit_footprint_mm"], "pass", out)
        self.assertEqual(st["bed_fit_height_mm"], "pass", out)

    def test_b_tiny_declared_volume_fails(self):
        """Same 60x24x6 part, print_volume_mm shrunk to 50^3 -> too big."""
        path = fs.write(fs.bed([60.0, 24.0, 6.0], volume=[50.0, 50.0, 50.0]),
                        os.path.join(tmp(), "bedfit-b.spec.json"))
        code, out, rep = run_gate("calibration", path)
        self.assertEqual(code, 1, out)
        self.assertEqual(rep["failed"], ["bracket-m3"], out)
        self.assertEqual(statuses(rep)["bed_fit_footprint_mm"], "fail", out)

    def test_c_default_bed_default_brim_fails_at_250(self):
        """250x250x10 part vs default 256^3 bed and default 5 mm brim ->
        usable X/Y is 256 - 2*5 = 246 < 250 -> fails."""
        _box_scene("box250", (250.0, 250.0, 10.0))
        path = fs.write(fs.bed([250.0, 250.0, 10.0]),
                        os.path.join(tmp(), "bedfit-c-fail.spec.json"))
        code, out, rep = run_gate("box250", path)
        self.assertEqual(code, 1, out)
        self.assertEqual(statuses(rep)["bed_fit_footprint_mm"], "fail", out)

    def test_c_default_bed_zero_brim_passes_at_250(self):
        """Same 250x250x10 part, brim_margin_mm=0 -> usable 256 >= 250 -> fits."""
        _box_scene("box250", (250.0, 250.0, 10.0))
        path = fs.write(fs.bed([250.0, 250.0, 10.0], margin=0.0),
                        os.path.join(tmp(), "bedfit-c-pass.spec.json"))
        code, out, rep = run_gate("box250", path)
        self.assertEqual(code, 0, out)
        self.assertEqual(statuses(rep)["bed_fit_footprint_mm"], "pass", out)

    def test_c2_170_part_fits_bed_but_a1_mini_info_flips_with_brim(self):
        """170x170x10 part fits the default 256^3 bed either way.
        A1 mini bed is 180^3: with 5 mm brim usable is 180-10=170, exactly
        equal to the footprint -> NOT compatible (info, never fails the
        gate). With 0 mm brim usable is the full 180 -> compatible."""
        _box_scene("box170", (170.0, 170.0, 10.0))
        path_margin = fs.write(fs.bed([170.0, 170.0, 10.0], margin=5.0),
                               os.path.join(tmp(), "bedfit-c2-margin.spec.json"))
        code, out, rep = run_gate("box170", path_margin)
        self.assertEqual(code, 0, out)
        st = statuses(rep)
        self.assertEqual(st["bed_fit_footprint_mm"], "pass", out)
        a1 = [c for p in rep["parts"] for c in p["checks"]
              if c["name"] == "bed_fit_a1_mini_compatible"][0]
        self.assertEqual(a1["status"], "info", out)
        self.assertFalse(a1["value"], out)

        path_no_margin = fs.write(fs.bed([170.0, 170.0, 10.0], margin=0.0),
                                  os.path.join(tmp(), "bedfit-c2-nomargin.spec.json"))
        code2, out2, rep2 = run_gate("box170", path_no_margin)
        self.assertEqual(code2, 0, out2)
        a1_2 = [c for p in rep2["parts"] for c in p["checks"]
               if c["name"] == "bed_fit_a1_mini_compatible"][0]
        self.assertEqual(a1_2["status"], "info", out2)
        self.assertTrue(a1_2["value"], out2)

    def test_d_volume_source_defaults_when_field_absent(self):
        path = fs.write(fs.bed([60.0, 24.0, 6.0]),
                        os.path.join(tmp(), "bedfit-d.spec.json"))
        code, out, rep = run_gate("calibration", path)
        self.assertEqual(code, 0, out)
        src = [c for p in rep["parts"] for c in p["checks"]
              if c["name"] == "bed_fit_volume_source"][0]
        self.assertEqual(src["status"], "info", out)
        self.assertEqual(src["value"], "default", out)


if __name__ == "__main__":
    unittest.main()

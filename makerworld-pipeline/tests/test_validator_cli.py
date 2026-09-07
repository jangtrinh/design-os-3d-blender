"""CLI-level tests for validate_bambu_3mf.py: exit codes, --json shape,
and the "no score key anywhere" contract."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "makerworld-pipeline", "scripts", "validate_bambu_3mf.py")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
TWO_PLATE = os.path.join(FIXTURES, "two-plate-ams.3mf")
TWO_PLATE_EXPECTED = os.path.join(FIXTURES, "two-plate-ams.3mf.expected.json")
SINGLE = os.path.join(FIXTURES, "single-plate.3mf")


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )
    return result


class CliExitCodeTests(unittest.TestCase):
    def test_good_fixture_exits_zero(self):
        result = run_cli(TWO_PLATE, "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_not_a_zip_exits_two(self):
        result = run_cli("/etc/hosts")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_missing_file_exits_two(self):
        result = run_cli("/no/such/path.3mf")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_single_plate_fixture_exits_zero(self):
        result = run_cli(SINGLE, "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_zip_missing_every_required_member_fails_without_crashing(self):
        # A well-formed ZIP that is simply not a Bambu 3MF at all: no
        # 3D/3dmodel.model, no Metadata/*. Every dependent check (3-10)
        # must degrade to a graceful FAIL row, never an uncaught traceback.
        with tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as tmp:
            with zipfile.ZipFile(tmp, "w") as zf:
                zf.writestr("readme.txt", b"not a 3mf at all")
            path = tmp.name
        try:
            result = run_cli(path, "--json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["checks"]), 10)
            statuses = {c["id"]: c["status"] for c in payload["checks"]}
            self.assertEqual(statuses["bambu_project_layout"], "FAIL")
            self.assertEqual(statuses["geometry_resolved"], "FAIL")
            self.assertEqual(statuses["build_items_placed"], "FAIL")
        finally:
            os.unlink(path)


class CliJsonShapeTests(unittest.TestCase):
    def test_json_has_required_top_level_keys(self):
        result = run_cli(TWO_PLATE, "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload.keys()), {"file", "checks", "summary"})
        self.assertEqual(payload["file"], TWO_PLATE)
        self.assertIn("pass", payload["summary"])
        self.assertIn("fail", payload["summary"])
        self.assertIn("skip", payload["summary"])

    def test_each_check_has_id_status_note_measured(self):
        result = run_cli(TWO_PLATE, "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["checks"]), 10)
        for entry in payload["checks"]:
            self.assertEqual(set(entry.keys()), {"id", "status", "note", "measured"})
            self.assertIn(entry["status"], {"PASS", "FAIL", "SKIP", "INFO"})

    def test_no_score_key_anywhere(self):
        result = run_cli(TWO_PLATE, "--json")
        self.assertNotIn("score", json.dumps(json.loads(result.stdout)))

    def test_expect_flag_is_accepted(self):
        result = run_cli(TWO_PLATE, "--expect", TWO_PLATE_EXPECTED, "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        bbox_check = next(c for c in payload["checks"] if c["id"] == "per_plate_bbox_mm")
        self.assertEqual(bbox_check["status"], "PASS")

    def test_bed_flag_is_evaluated_not_only_echoed(self):
        # two-plate-ams.3mf plate 1 footprint is 12x5mm (per its own
        # .expected.json ground truth) -- a 50x50mm bed is NOT small
        # enough to discriminate the fix (fits_bed is True either way),
        # so this uses a 10x10x10mm bed, which the 12x5mm footprint does
        # NOT fit on its long axis: fits_bed must be False, not just
        # bed_requested_mm recorded while 180/256 stay the only real fits.
        result = run_cli(TWO_PLATE, "--bed", "10,10,10", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        bed_fit_check = next(c for c in payload["checks"] if c["id"] == "bed_fit")
        self.assertEqual(bed_fit_check["measured"]["bed_requested_mm"], [10.0, 10.0, 10.0])
        plate1 = bed_fit_check["measured"]["plates"]["1"]
        self.assertIn("fits_bed", plate1)
        self.assertFalse(plate1["fits_bed"])
        # fits_180/fits_256 (hardcoded stock beds) must be unaffected by --bed.
        self.assertTrue(plate1["fits_180"])
        self.assertTrue(plate1["fits_256"])


class CliHumanTableTests(unittest.TestCase):
    def test_default_output_is_human_readable_table(self):
        result = run_cli(TWO_PLATE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("container_zip", result.stdout)
        self.assertIn("PASS", result.stdout)
        # human mode must not accidentally be JSON
        with self.assertRaises(json.JSONDecodeError):
            json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()

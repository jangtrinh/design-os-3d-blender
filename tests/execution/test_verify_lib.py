"""Contract tests for scripts/agent-verify-lib.py.

Each test launches a fresh `--factory-startup -b` Blender running a fixture in
tests/execution/fixtures/verify-lib/ and asserts on the JSON that fixture
prints. Nothing here touches a running Blender GUI.
"""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "execution" / "fixtures" / "verify-lib"
BLENDER = os.environ.get("BLENDER_BIN",
                         "/Applications/Blender.app/Contents/MacOS/Blender")

# every render/scene setting preview_render is allowed to touch
TOUCHED = ("resolution_x", "resolution_y", "resolution_percentage", "filepath",
           "engine", "film_transparent", "file_format", "color_mode",
           "cycles_samples", "eevee_samples")

TIMINGS = {}


def run_fixture(name, timeout=600):
    """Run one fixture headless; return (result_dict, stdout)."""
    tmp = tempfile.mkdtemp(prefix="verify-lib-")
    env = dict(os.environ, AGENT_REPO_ROOT=str(REPO),
               AGENT_PREVIEW_DIR=tmp, AGENT_CHECKPOINT_DIR=tmp)
    try:
        proc = subprocess.run(
            [BLENDER, "--factory-startup", "-b", "--python-exit-code", "3",
             "--python", str(FIXTURES / f"{name}.py")],
            capture_output=True, text=True, timeout=timeout, env=env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    hits = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT ")]
    if not hits:
        raise AssertionError(
            f"{name}: no RESULT line (rc={proc.returncode})\n"
            f"{proc.stdout[-3000:]}\n{proc.stderr[-2000:]}")
    return json.loads(hits[-1][len("RESULT "):]), proc.stdout


@unittest.skipUnless(os.path.exists(BLENDER), f"Blender not found at {BLENDER}")
class VerifyLibTest(unittest.TestCase):

    def assert_settings_equal(self, before, after, keys=TOUCHED):
        for k in keys:
            self.assertEqual(before[k], after[k],
                             f"setting {k} not restored: {before[k]} -> {after[k]}")

    def test_lib_loads_and_prints_sentinel(self):
        _, out = run_fixture("preview-success")
        banner = [ln for ln in out.splitlines() if ln.startswith("AGENT_LIB_OK ")]
        self.assertTrue(banner, "AGENT_LIB_OK banner missing")
        self.assertIn("bpy=(5,", banner[-1])
        sha = banner[-1].split("lib_sha=")[-1].strip()
        self.assertEqual(len(sha), 8, f"bad lib_sha: {banner[-1]}")
        self.assertNotEqual(sha, "unknown")

    def test_preview_render_success_restores_everything(self):
        r, _ = run_fixture("preview-success")
        self.assert_settings_equal(r["before"], r["mid"])
        self.assert_settings_equal(r["before"], r["after"])
        self.assertTrue(r["exists1"], "first preview wrote no file")
        self.assertTrue(r["exists2"], "second preview wrote no file")
        self.assertTrue(r["default_under_env"],
                        f"default path ignored AGENT_PREVIEW_DIR: {r['path2']}")
        self.assertGreater(r["stdev"], 0.01,
                           f"flat frame: stdev={r['stdev']} mean={r['mean']}")

    def test_preview_render_failure_restores_everything(self):
        r, _ = run_fixture("preview-failure")
        self.assertIsNotNone(r["raised"], "no-camera render did not raise")
        self.assert_settings_equal(r["before"], r["after"])

    def test_verify_export_missing_file_raises_and_scene_survives(self):
        r, _ = run_fixture("export-checks")
        self.assertEqual(r["missing_raised"], "AssertionError")
        self.assertEqual(r["before"]["objects"], r["after_missing"]["objects"])
        self.assertIn("UNSAVED_WORK", r["after_missing"]["objects"])
        self.assert_settings_equal(r["before"], r["after_missing"])

    def test_verify_export_real_glb_passes_and_scene_survives(self):
        r, _ = run_fixture("export-checks")
        self.assertTrue(r["glb_exists"])
        self.assertIsNone(r["report"]["error"])
        self.assertGreaterEqual(r["report"]["tris"], 12)
        self.assertEqual(r["before"]["objects"], r["after_ok"]["objects"])
        self.assertIn("UNSAVED_WORK", r["after_ok"]["objects"])
        self.assert_settings_equal(r["before"], r["after_ok"])

    def test_scaffold_keeps_non_factory_settings_unless_forced(self):
        r, _ = run_fixture("scaffold-checks")
        soft, hard = r["soft"], r["hard"]
        for key in ("scale_length", "fps"):
            self.assertFalse(soft[key]["changed"], f"{key} overwritten by scaffold()")
        self.assertEqual(r["after_soft"]["scale_length"], 0.5)
        self.assertEqual(r["after_soft"]["fps"], 30)
        self.assertEqual(soft["scale_length"]["before"], 0.5)
        self.assertEqual(soft["fps"]["before"], 30)
        # collections are added, never removed
        self.assertIn("Collection", soft["collections"]["after"])
        for name in ("ASSETS", "LIGHTS", "CAMERAS", "HELPERS"):
            self.assertIn(name, soft["collections"]["after"])
        # force=True is the only way in
        self.assertTrue(hard["scale_length"]["changed"])
        self.assertTrue(hard["fps"]["changed"])
        self.assertEqual(r["after_hard"]["scale_length"], 1.0)
        self.assertEqual(r["after_hard"]["fps"], 24)

    def test_both_engines_render_a_preview_headless(self):
        r, _ = run_fixture("engine-timing")
        for engine in ("EEVEE", "CYCLES"):
            row = r["engines"][engine]
            self.assertTrue(row["exists"], f"{engine} wrote no image")
            self.assertGreater(row["stdev"], 0.01, f"{engine} frame is flat")
            TIMINGS[engine] = row["seconds"]
        self.assert_settings_equal(r["before"], r["after"])

    @classmethod
    def tearDownClass(cls):
        if TIMINGS:
            print("\n128px/8-sample preview, in-process seconds: "
                  + ", ".join(f"{k}={v}" for k, v in sorted(TIMINGS.items())))


if __name__ == "__main__":
    unittest.main()

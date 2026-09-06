"""Contract tests for scripts/headless-run.sh.

These are the cases the audit proved the old wrapper got wrong: an uncaught
exception exited 0 (false green), a missing script exited 0 in silence, and a
payload that merely handled an operator error could come back red (false red).
Every case here runs a real, fresh `--factory-startup -b` Blender; the live GUI
on port 9876 is never contacted.
"""

import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import agent_runtime as rt  # noqa: E402

HEADLESS = os.path.join(REPO, "scripts", "headless-run.sh")
FIXTURES = os.path.join(REPO, "tests", "execution", "fixtures")
BLENDER = os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")


def headless(*args, **kwargs):
    """Run headless-run.sh with the given arguments and return the CompletedProcess."""
    env = dict(os.environ)
    env.update(kwargs.pop("env", {}))
    return subprocess.run(
        ["bash", HEADLESS] + list(args),
        capture_output=True, text=True, timeout=300, env=env,
    )


def fixture(name):
    return os.path.join(FIXTURES, name)


@unittest.skipUnless(os.path.exists(BLENDER), "Blender not installed at %s" % BLENDER)
class HeadlessRunContractTest(unittest.TestCase):

    def test_raising_payload_exits_3_with_a_traceback_naming_the_payload(self):
        proc = headless(fixture("payload-raises.py"))
        self.assertEqual(proc.returncode, 3, msg=proc.stdout[-2000:])
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(obj["error"]["type"], "RuntimeError")
        self.assertIn("payload-raises.py", obj["error"]["traceback"])
        self.assertIn("MUTATION_DONE", proc.stdout)  # the partial mutation is visible

    def test_clean_payload_exits_0_with_measured_postconditions(self):
        proc = headless(fixture("payload-emit-ok.py"))
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:])
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, rt.SENTINEL_OK)
        self.assertEqual(obj["step"], "fixture-clean")
        self.assertEqual(obj["postconditions"]["dim_x"], 2.0)

    def test_handled_operator_error_still_exits_0(self):
        """The false-red case: handling a bpy.ops failure is not a payload failure."""
        proc = headless(fixture("payload-handled-operator-error.py"))
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:])
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, rt.SENTINEL_OK)
        self.assertTrue(obj["postconditions"]["handled"])

    def test_missing_script_exits_2_and_says_so_on_stderr(self):
        proc = headless("/tmp/definitely-missing-headless-payload.py")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not found", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_failed_requirement_exits_1_not_3(self):
        proc = headless(fixture("payload-assert-fails.py"))
        self.assertEqual(proc.returncode, 1, msg=proc.stdout[-2000:])
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(obj["error"]["type"], "AssertionError")

    def test_forged_sentinel_cannot_turn_a_failure_green(self):
        proc = headless(fixture("payload-liar.py"))
        self.assertEqual(proc.returncode, 3, msg=proc.stdout[-2000:])
        self.assertIn('"step": "forged"', proc.stdout)   # the forgery was printed...
        tag, obj = rt.parse_sentinel(proc.stdout)        # ...and lost, last line wins
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(obj["error"]["message"], "the liar fails after claiming success")

    def test_forged_trailing_sentinel_cannot_hide_a_reported_failure(self):
        """AGENT_OK printed after a real AGENT_FAIL must not turn the run green."""
        proc = headless(fixture("payload-forges-ok-after-failing.py"))
        self.assertNotEqual(proc.returncode, 0, msg=proc.stdout[-2000:])
        self.assertIn("forged-last-line", proc.stdout)
        self.assertIn("refusing to report success", proc.stderr)

    def test_forwards_args_after_double_dash(self):
        proc = headless(fixture("payload-argv-echo.py"), "--", "--parts", "a,b")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:])
        _, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(obj["postconditions"]["argv"], ["--parts", "a,b"])

    def test_legacy_payload_gets_a_sentinel_via_launcher(self):
        """Default mode wraps every payload in agent_runtime.run_file, so even a
        payload that never calls emit_ok ends with a genuine AGENT_OK line."""
        proc = headless(fixture("payload-legacy-no-sentinel.py"))
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:])
        self.assertIn("LEGACY_PAYLOAD_RAN", proc.stdout)
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, "AGENT_OK")
        self.assertNotIn("no AGENT_OK/AGENT_FAIL sentinel", proc.stderr)

    def test_raw_mode_payload_without_a_sentinel_falls_back_and_warns(self):
        """HEADLESS_RAW=1 runs the file directly (legacy); the caller is told the
        verdict is unreliable because no sentinel was printed."""
        proc = headless(fixture("payload-legacy-no-sentinel.py"), env={"HEADLESS_RAW": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("LEGACY_PAYLOAD_RAN", proc.stdout)
        self.assertIn("no AGENT_OK/AGENT_FAIL sentinel", proc.stderr)

    def test_payload_may_import_agent_runtime_without_bootstrap(self):
        """The launcher puts scripts/ on sys.path, matching the MCP snippet."""
        proc = headless(fixture("payload-emit-ok.py"))
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:])

    def test_help_and_bad_arguments(self):
        self.assertEqual(headless("--help").returncode, 0)
        self.assertEqual(headless().returncode, 2)
        self.assertEqual(headless("--blend").returncode, 2)
        missing_blend = headless(fixture("payload-emit-ok.py"), "--blend", "/tmp/none.blend")
        self.assertEqual(missing_blend.returncode, 2)
        self.assertIn("blend file not found", missing_blend.stderr)

    def test_unusable_blender_binary_is_input_error(self):
        proc = headless(fixture("payload-emit-ok.py"), env={"BLENDER_BIN": "/tmp/no-blender"})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not executable", proc.stderr)


if __name__ == "__main__":
    unittest.main()

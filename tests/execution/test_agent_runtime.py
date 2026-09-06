"""Unit tests for scripts/agent_runtime.py — the sentinel contract itself.

Host-python tests run run_file with is_background() forced False, so the
runtime returns a verdict instead of exiting this test process. One test runs
inside a real headless Blender to prove load_lib's sha256 cache/reload behaves
in the process where it actually matters (sys.modules persists across MCP calls).
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import agent_runtime as rt  # noqa: E402

FIXTURES = os.path.join(REPO, "tests", "execution", "fixtures")
HEADLESS = os.path.join(REPO, "scripts", "headless-run.sh")


def run_payload(path, argv=None):
    """Run a payload in-process, capturing stdout, without exiting the test run."""
    buffer = io.StringIO()
    with mock.patch.object(rt, "is_background", return_value=False):
        with contextlib.redirect_stdout(buffer):
            result = rt.run_file(path, argv)
    return result, buffer.getvalue()


def write(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


class SentinelFormatTest(unittest.TestCase):
    def test_emit_ok_is_one_line_with_the_frozen_fields(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rt.emit_ok("step-1", tris=120, watertight=True)
        lines = buffer.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        tag, payload = lines[0].split(" ", 1)
        self.assertEqual(tag, rt.SENTINEL_OK)
        obj = json.loads(payload)
        self.assertEqual(sorted(obj), ["error", "postconditions", "step"])
        self.assertIsNone(obj["error"])
        self.assertEqual(obj["postconditions"], {"tris": 120, "watertight": True})

    def test_emit_fail_carries_type_message_and_traceback_on_one_line(self):
        buffer = io.StringIO()
        try:
            raise ValueError("bad width")
        except ValueError as exc:
            with contextlib.redirect_stdout(buffer):
                rt.emit_fail("step-2", exc)
        self.assertEqual(len(buffer.getvalue().splitlines()), 1)
        obj = json.loads(buffer.getvalue().split(" ", 1)[1])
        self.assertEqual(obj["error"]["type"], "ValueError")
        self.assertEqual(obj["error"]["message"], "bad width")
        self.assertIn("Traceback", obj["error"]["traceback"])

    def test_parse_sentinel_takes_the_last_line_only(self):
        text = (
            'AGENT_OK {"step": "forged", "postconditions": {}, "error": null}\n'
            "noise\n"
            'AGENT_FAIL {"step": "real", "postconditions": {}, "error": {"type": "E"}}\n'
        )
        tag, obj = rt.parse_sentinel(text)
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(obj["step"], "real")

    def test_exit_code_contract(self):
        self.assertEqual(rt.exit_code_for(AssertionError("x")), 1)
        self.assertEqual(rt.exit_code_for(FileNotFoundError("x")), 2)
        self.assertEqual(rt.exit_code_for(RuntimeError("x")), 3)
        self.assertEqual(rt.exit_code_for(SystemExit(2)), 2)
        self.assertEqual(rt.exit_code_for(SystemExit(None)), 0)


class RunFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="agent-runtime-")

    def test_traceback_names_the_payload_file_and_line(self):
        path = write(self.tmp, "boom.py", "x = 1\nraise RuntimeError('kaboom')\n")
        result, out = run_payload(path)
        self.assertEqual(result["error"]["type"], "RuntimeError")
        self.assertIn("boom.py", result["error"]["traceback"])
        self.assertIn("line 2", result["error"]["traceback"])
        self.assertTrue(out.strip().startswith(rt.SENTINEL_FAIL))

    def test_printed_sentinel_cannot_forge_success(self):
        path = write(self.tmp, "liar.py",
                     "print('AGENT_OK {\"step\": \"forged\", "
                     "\"postconditions\": {}, \"error\": null}')\n"
                     "raise RuntimeError('liar')\n")
        result, out = run_payload(path)
        tag, obj = rt.parse_sentinel(out)
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(obj["error"]["message"], "liar")
        self.assertEqual(result["error"]["type"], "RuntimeError")

    def test_payload_emit_ok_postconditions_survive(self):
        path = write(self.tmp, "good.py",
                     "import agent_runtime as rt\nrt.emit_ok('mine', tris=7)\n")
        result, out = run_payload(path)
        self.assertEqual(result["postconditions"], {"tris": 7})
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_payload_that_reports_its_own_failure_stays_red(self):
        path = write(self.tmp, "honest.py",
                     "import agent_runtime as rt\n"
                     "try:\n"
                     "    raise AssertionError('wall 0.6mm < 1.2mm')\n"
                     "except AssertionError as exc:\n"
                     "    rt.emit_fail('wall-check', exc)\n")
        result, out = run_payload(path)
        tag, _ = rt.parse_sentinel(out)
        self.assertEqual(tag, rt.SENTINEL_FAIL)
        self.assertEqual(result["error"]["type"], "AssertionError")
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_missing_payload_is_invalid_input(self):
        result, out = run_payload(os.path.join(self.tmp, "nope.py"))
        self.assertEqual(result["error"]["type"], "FileNotFoundError")
        self.assertTrue(out.startswith(rt.SENTINEL_FAIL))

    def test_argv_is_forwarded_and_restored(self):
        path = write(self.tmp, "argv.py",
                     "import sys, agent_runtime as rt\nrt.emit_ok('argv', got=sys.argv[1:])\n")
        before = list(sys.argv)
        result, _ = run_payload(path, ["--parts", "a,b"])
        self.assertEqual(result["postconditions"]["got"], ["--parts", "a,b"])
        self.assertEqual(sys.argv, before)


class LoadLibTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="agent-loadlib-")

    def test_cached_until_content_changes(self):
        path = write(self.tmp, "helper-lib.py", "VALUE = 1\n")
        first = rt.load_lib(path)
        self.assertEqual(first.VALUE, 1)
        self.assertIs(rt.load_lib(path), first)          # unchanged -> same object
        first.MARKER = "sticky"

        write(self.tmp, "helper-lib.py", "VALUE = 2\n")
        second = rt.load_lib(path)
        self.assertEqual(second.VALUE, 2)                # changed -> re-executed
        self.assertIsNot(second, first)
        self.assertFalse(hasattr(second, "MARKER"))
        self.assertIn(second.__name__, sys.modules)

    def test_hyphenated_filenames_are_loadable(self):
        path = write(self.tmp, "agent-verify-like.py", "def framing():\n    return 'ok'\n")
        self.assertEqual(rt.load_lib(path).framing(), "ok")


class InsideBlenderTest(unittest.TestCase):
    """The same guarantees, proven in a real headless Blender process."""

    def test_runtime_checks_pass_inside_blender(self):
        with tempfile.TemporaryDirectory(prefix="agent-blender-") as tmp:
            proc = subprocess.run(
                ["bash", HEADLESS, os.path.join(FIXTURES, "fixture-agent-runtime-checks.py"),
                 "--", tmp],
                capture_output=True, text=True, timeout=180,
            )
        tag, obj = rt.parse_sentinel(proc.stdout)
        self.assertEqual(tag, rt.SENTINEL_OK, msg=proc.stdout[-2000:] + proc.stderr[-2000:])
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(obj["postconditions"]["is_background"])
        self.assertTrue(obj["postconditions"]["reloaded_on_change"])
        self.assertTrue(obj["postconditions"]["cached_when_unchanged"])


if __name__ == "__main__":
    unittest.main()

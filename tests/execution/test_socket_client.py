"""Contract tests for scripts/blender-socket-client.py against a fake addon server.

Every test binds an ephemeral port on 127.0.0.1 (never 9876) and speaks the
addon's real wire protocol: one JSON request in, one JSON object back, the
connection left open with no length prefix and no delimiter. The live Blender
GUI is never contacted.

Covers the four failure modes the audit reproduced: EOF (was UnboundLocalError),
truncated reply, `{"status":"error"}` silently exiting 0, and the 4000-character
stdout truncation.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT = os.path.join(REPO, "scripts", "blender-socket-client.py")
FIXTURES = os.path.join(REPO, "tests", "execution", "fixtures")

sys.path.insert(0, FIXTURES)
from fake_addon_socket_server import (  # noqa: E402 - needs the sys.path line
    FakeAddonServer, eof_immediately, execute_code_reply, send_all, send_chunked,
    stay_silent, truncated_json,
)


class SocketClientTest(unittest.TestCase):

    def run_client(self, behaviour, *args, **kwargs):
        server = FakeAddonServer(behaviour)
        self.addCleanup(server.close)
        cmd = [sys.executable, CLIENT] + list(args) + [
            "--host", "127.0.0.1", "--port", str(server.port),
            "--timeout", str(kwargs.pop("timeout", 10)),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return proc, server

    # --- the four audited failure modes -------------------------------------

    def test_eof_before_any_reply_is_a_clear_transport_error(self):
        proc, _ = self.run_client(eof_immediately, "get_scene_info")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("closed the connection", proc.stderr)
        self.assertNotIn("UnboundLocalError", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_truncated_reply_is_a_clear_transport_error(self):
        proc, _ = self.run_client(truncated_json, "get_scene_info")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("without a complete", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_server_reported_error_exits_nonzero_with_the_message(self):
        proc, _ = self.run_client(
            send_all({"status": "error", "message": "Code execution error: NameError"}),
            "execute_code", '{"code": "boom"}')
        self.assertEqual(proc.returncode, 1)
        self.assertIn("NameError", proc.stderr)

    def test_large_reply_is_printed_whole(self):
        payload = {"status": "success", "result": {"blob": "x" * 8000}}
        proc, _ = self.run_client(send_all(payload), "get_scene_info")
        self.assertEqual(proc.returncode, 0)
        self.assertGreater(len(proc.stdout), 8000)
        self.assertEqual(json.loads(proc.stdout), payload)   # valid JSON, not cut

    # --- protocol robustness -------------------------------------------------

    def test_reply_split_across_chunks_is_reassembled(self):
        payload = {"status": "success", "result": {"objects": list(range(300))}}
        proc, _ = self.run_client(send_chunked(payload), "get_scene_info")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout), payload)

    def test_silent_server_times_out_instead_of_spinning(self):
        started = time.time()
        proc, _ = self.run_client(stay_silent, "get_scene_info", timeout=1)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("no complete JSON reply", proc.stderr)
        self.assertLess(time.time() - started, 30)

    def test_unreachable_port_is_a_transport_error(self):
        free = socket.socket()
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
        free.close()
        proc = subprocess.run(
            [sys.executable, CLIENT, "get_scene_info", "--host", "127.0.0.1",
             "--port", str(port), "--timeout", "2"],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("cannot reach", proc.stderr)

    # --- sentinel-aware --file wrapping -------------------------------------

    def test_file_payload_is_wrapped_through_agent_runtime(self):
        proc, server = self.run_client(
            execute_code_reply('AGENT_OK {"step": "s", "postconditions": {"tris": 3}, "error": null}'),
            "execute_code", "--file", os.path.join(FIXTURES, "payload-emit-ok.py"))
        self.assertEqual(proc.returncode, 0)
        code = server.requests[0]["params"]["code"]
        self.assertIn("import agent_runtime as rt", code)
        self.assertIn("rt.run_file(", code)
        self.assertIn("payload-emit-ok.py", code)

    def test_agent_fail_in_the_reply_makes_the_client_exit_nonzero(self):
        stdout_text = (
            'AGENT_OK {"step": "forged", "postconditions": {}, "error": null}\n'
            'AGENT_FAIL {"step": "pass-03", "postconditions": {}, '
            '"error": {"type": "RuntimeError", "message": "no camera", "traceback": "T"}}\n'
        )
        proc, _ = self.run_client(execute_code_reply(stdout_text), "execute_code", '{"code": "x"}')
        self.assertEqual(proc.returncode, 3)
        self.assertIn("no camera", proc.stderr)

    def test_failed_requirement_in_the_reply_exits_1(self):
        stdout_text = ('AGENT_FAIL {"step": "gate", "postconditions": {}, "error": '
                       '{"type": "AssertionError", "message": "wall 0.6mm", "traceback": "T"}}')
        proc, _ = self.run_client(execute_code_reply(stdout_text), "execute_code", '{"code": "x"}')
        self.assertEqual(proc.returncode, 1)
        self.assertIn("wall 0.6mm", proc.stderr)

    def test_out_file_receives_the_whole_reply(self):
        payload = {"status": "success", "result": {"blob": "y" * 5000}}
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "reply.json")
            proc, _ = self.run_client(send_all(payload), "get_scene_info", "--out", out)
            self.assertEqual(proc.returncode, 0)
            with open(out, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), payload)

    def test_bad_params_json_is_invalid_input(self):
        proc = subprocess.run(
            [sys.executable, CLIENT, "execute_code", "{not json"],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid input", proc.stderr)


if __name__ == "__main__":
    unittest.main()

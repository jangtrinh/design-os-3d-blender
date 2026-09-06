#!/usr/bin/env python3
"""Direct TCP client for the blender-mcp addon socket (default port 9876).

Bypasses the MCP layer so a running session can drive the live Blender GUI
without a session restart.

Wire contract (read from the addon source): the client sends one JSON object
`{"type": ..., "params": {...}}`; the server replies with one JSON object and
keeps the connection open (no length prefix, no delimiter, no EOF). So the only
correct read strategy is: accumulate until the buffer parses, or time out.
Replies are `{"status":"success","result":...}` or `{"status":"error","message":...}`;
for execute_code the result is `{"executed":true,"result":"<captured stdout>"}`.

Usage:
  blender-socket-client.py <command_type> ['<params-json>']
  blender-socket-client.py execute_code --file <script.py>
  blender-socket-client.py get_scene_info --host 127.0.0.1 --port 9876 --out r.json

--file wraps the payload through agent_runtime, so the captured stdout carries
the AGENT_OK / AGENT_FAIL sentinel (with a real traceback) instead of a bare
"executed successfully".

Exit codes: 0 pass - 1 server-reported error or failed requirement -
2 invalid CLI input - 3 transport failure or payload execution error.
"""

import argparse
import json
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_runtime as rt  # noqa: E402 - needs the sys.path line above

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
DEFAULT_TIMEOUT = 120.0
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


class TransportError(Exception):
    """Anything that stopped one complete JSON reply from arriving."""


def send(command_type, params=None, host=DEFAULT_HOST, port=DEFAULT_PORT,
         timeout=DEFAULT_TIMEOUT):
    """Send one command and return the decoded reply, or raise TransportError."""
    request = json.dumps({"type": command_type, "params": params or {}}).encode("utf-8")
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        try:
            sock.connect((host, port))
            sock.sendall(request)
        except OSError as exc:
            raise TransportError("cannot reach %s:%s (%s)" % (host, port, exc))

        buffer = b""
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                raise TransportError(
                    "no complete JSON reply within %ss; %d bytes buffered"
                    % (timeout, len(buffer))
                )
            except OSError as exc:
                raise TransportError("socket error after %d bytes: %s" % (len(buffer), exc))
            if not chunk:
                raise TransportError(
                    "server closed the connection after %d bytes without a complete "
                    "JSON reply (is the addon still Connected?)" % len(buffer)
                )
            buffer += chunk
            try:
                return json.loads(buffer.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue  # partial reply: keep reading
    finally:
        sock.close()


def wrap_payload(path):
    """Build execute_code source that runs `path` under the sentinel contract."""
    abspath = os.path.abspath(path)
    if not os.path.isfile(abspath):
        raise ValueError("payload not found: %s" % abspath)
    return (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "sys.modules.pop('agent_runtime', None)\n"  # never run a stale runtime
        "import agent_runtime as rt\n"
        "rt.run_file(%r)\n" % (SCRIPTS_DIR, abspath)
    )


def captured_stdout(response):
    """Pull the payload's captured stdout out of an execute_code reply."""
    result = response.get("result")
    if isinstance(result, dict):
        inner = result.get("result")
        if isinstance(inner, str):
            return inner
    return result if isinstance(result, str) else ""


def verdict(response):
    """Return (exit_code, human message) for a decoded reply."""
    if response.get("status") == "error":
        return 1, "server reported an error: %s" % response.get("message", "(no message)")

    tag, obj = rt.parse_sentinel(captured_stdout(response))
    if tag == rt.SENTINEL_FAIL:
        error = (obj or {}).get("error") or {}
        code = 1 if error.get("type") == "AssertionError" else 3
        return code, "%s: %s: %s" % (obj.get("step"), error.get("type"), error.get("message"))
    if tag == rt.SENTINEL_OK:
        return 0, "%s ok %s" % (obj.get("step"), json.dumps(obj.get("postconditions", {})))
    return 0, "ok (no sentinel in reply)"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="blender-socket-client.py",
        description="Send one command to the blender-mcp addon socket.",
    )
    parser.add_argument("command_type", help="e.g. get_scene_info, execute_code")
    parser.add_argument("params_json", nargs="?", help="JSON object of parameters")
    parser.add_argument("--file", dest="payload",
                        help="run this .py payload via execute_code, wrapped in agent_runtime")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="seconds to wait for a complete reply (default %(default)s)")
    parser.add_argument("--out", help="write the full reply JSON to this file")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        if args.payload:
            params = {"code": wrap_payload(args.payload)}
        elif args.params_json:
            params = json.loads(args.params_json)
            if not isinstance(params, dict):
                raise ValueError("params must be a JSON object")
        else:
            params = {}
    except (ValueError, OSError) as exc:
        sys.stderr.write("blender-socket-client: invalid input: %s\n" % exc)
        return 2

    try:
        response = send(args.command_type, params, host=args.host, port=args.port,
                        timeout=args.timeout)
    except TransportError as exc:
        sys.stderr.write("blender-socket-client: transport failure: %s\n" % exc)
        return 3

    # Full reply, never truncated.
    text = json.dumps(response, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        sys.stderr.write("blender-socket-client: reply written to %s\n" % args.out)
    print(text)

    code, message = verdict(response)
    sys.stderr.write("blender-socket-client: %s\n" % message)
    return code


if __name__ == "__main__":
    sys.exit(main())

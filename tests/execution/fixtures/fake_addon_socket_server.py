"""Fake blender-mcp addon server for the socket-client tests.

snake_case because the test module imports it. It speaks the addon's real wire
protocol - one JSON request in, one JSON object back, connection left open with
no length prefix and no delimiter - and always binds an ephemeral port on
127.0.0.1, never the live GUI's 9876.
"""

import json
import socket
import threading
import time

LIVE_GUI_PORT = 9876  # must never be bound or contacted by these tests


class FakeAddonServer:
    """One-shot server that replays a scripted behaviour for a single client."""

    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.requests = []
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        assert self.port != LIVE_GUI_PORT, "refusing to bind the live GUI port"
        self.sock.listen(1)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        try:
            conn, _ = self.sock.accept()
        except OSError:
            return
        try:
            conn.settimeout(10)
            buffer = b""
            while True:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                buffer += chunk
                try:
                    self.requests.append(json.loads(buffer.decode("utf-8")))
                    break
                except ValueError:
                    continue
            self.behaviour(conn)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def send_all(payload):
    """Behaviour: reply with one complete JSON object."""
    def behaviour(conn):
        conn.sendall(json.dumps(payload).encode("utf-8"))
        time.sleep(0.2)          # addon keeps the connection open after replying
    return behaviour


def send_chunked(payload, pieces=3):
    """Behaviour: dribble a valid reply out in pieces (partial JSON in between)."""
    def behaviour(conn):
        raw = json.dumps(payload).encode("utf-8")
        step = max(1, len(raw) // pieces)
        for start in range(0, len(raw), step):
            conn.sendall(raw[start:start + step])
            time.sleep(0.05)
        time.sleep(0.2)
    return behaviour


def eof_immediately(conn):
    """Behaviour: close without replying (the UnboundLocalError case)."""
    conn.close()


def truncated_json(conn):
    """Behaviour: send half a JSON object, then close."""
    conn.sendall(b'{"status": "success", "resu')
    conn.close()


def stay_silent(conn):
    """Behaviour: keep the connection open and never reply (the spin case)."""
    time.sleep(5)


def execute_code_reply(stdout_text):
    """Behaviour: the addon's execute_code success envelope."""
    return send_all({"status": "success", "result": {"executed": True, "result": stdout_text}})

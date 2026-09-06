"""Headless launcher: run one agent payload through agent_runtime.run_file.

Invoked by scripts/headless-run.sh as
  Blender ... --python scripts/agent-run-headless.py -- <payload.py> [payload args]
so every headless payload gets the same namespace, traceback JSON, sentinel line
and exit code as a payload executed over MCP via `rt.run_file(...)`. The payload
may `import agent_runtime` because this launcher puts scripts/ on sys.path first.
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import agent_runtime  # noqa: E402  (needs sys.path above)

# Blender leaves everything after `--` in sys.argv for scripts to consume.
_tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not _tail:
    print("AGENT_FAIL " + '{"step": "launcher", "postconditions": {}, '
          '"error": {"type": "UsageError", "message": "no payload path after --", "traceback": ""}}')
    sys.exit(2)

agent_runtime.run_file(_tail[0], argv=_tail[1:])

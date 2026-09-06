"""Handles a real bpy.ops error, completes, emits AGENT_OK: must exit 0.

This is the false-red case: Blender's own exit status must not be allowed to
turn a successful payload red just because an operator reported an error.
"""
import os
import sys

import bpy

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    import agent_runtime as rt
    handled = []
    try:
        bpy.ops.wm.open_mainfile(filepath="/nonexistent-headless-run-probe.blend")
    except Exception as exc:                      # operator failure is expected here
        handled.append(type(exc).__name__)
    try:
        bpy.ops.object.mode_set(mode="EDIT")      # poll() fails without an active object
    except Exception as exc:
        handled.append(type(exc).__name__)
    assert handled, "expected at least one operator error to handle"
    rt.emit_ok("fixture-handled-op-error", handled=handled)


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)

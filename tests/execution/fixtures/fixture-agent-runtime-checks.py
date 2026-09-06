"""Proves agent_runtime's guarantees inside a real Blender process.

Run: bash scripts/headless-run.sh tests/execution/fixtures/fixture-agent-runtime-checks.py -- <tmpdir>
load_lib's cache lives in sys.modules, which is exactly the thing that persists
between MCP execute_code calls, so it must be exercised in-process.
"""
import os
import sys

import bpy

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def write_lib(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("import bpy\nVALUE = %d\n\n\ndef probe():\n    return VALUE\n" % value)


def main():
    import agent_runtime as rt
    tmp = sys.argv[1]
    lib = os.path.join(tmp, "sample-helper-lib.py")

    write_lib(lib, 1)
    first = rt.load_lib(lib)
    assert first.probe() == 1, "load_lib did not execute the helper"
    cached_when_unchanged = rt.load_lib(lib) is first
    assert first.__name__ in sys.modules, "helper was not cached in sys.modules"

    write_lib(lib, 2)
    second = rt.load_lib(lib)
    reloaded_on_change = (second is not first) and second.probe() == 2

    assert rt.is_background(), "headless run must report is_background() True"
    assert bpy.app.background, "this fixture must run in background Blender"

    rt.emit_ok(
        "agent-runtime-checks",
        is_background=rt.is_background(),
        cached_when_unchanged=cached_when_unchanged,
        reloaded_on_change=reloaded_on_change,
        blender=bpy.app.version_string,
    )


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        rt.run_file(__file__, extra)

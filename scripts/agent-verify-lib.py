"""Agent sense organs — exec-able facade over `scripts/agent_verify/`.

Load either way:
    exec(open("scripts/agent-verify-lib.py").read())        # MCP / inline
    import agent_runtime as rt; rt.load_lib(".../agent-verify-lib.py")

Both bind: assert_exists, tri_count, world_bbox, has_material, framing,
frame_stats, preview_render, verify_export, import_any, scaffold, checkpoint,
repo_root, lib_sha. Contracts and safety classes: `agent_verify/__init__.py`
and knowledge/00-foundations/agent-workflow-loop.md §4.

If the package cannot be located (payload and cwd both outside the repo), set
AGENT_REPO_ROOT to the repo root; the load fails loudly, never silently.
"""
import os
import sys


def _find_agent_verify():
    """Locate the package dir without hardcoding any machine path."""
    cands = []
    here = globals().get("__file__")
    if here and os.path.basename(here) == "agent-verify-lib.py":
        cands.append(os.path.dirname(os.path.abspath(here)))
    if os.environ.get("AGENT_REPO_ROOT"):
        cands.append(os.path.join(os.environ["AGENT_REPO_ROOT"], "scripts"))
    cands += [d for d in sys.path if d]          # MCP inserts <root>/scripts
    starts = [os.getcwd()]
    if here:
        starts.append(os.path.dirname(os.path.abspath(here)))
    starts += [os.path.dirname(os.path.abspath(a)) for a in sys.argv
               if a.endswith(".py")]
    try:
        import bpy
        if bpy.data.filepath:
            starts.append(os.path.dirname(bpy.data.filepath))
    except Exception:
        pass
    for start in starts:
        d = os.path.abspath(start)
        while True:
            cands.append(os.path.join(d, "scripts"))
            cands.append(d)
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    for c in cands:
        if os.path.isfile(os.path.join(c, "agent_verify", "__init__.py")):
            return c
    raise ImportError(
        "agent_verify package not found next to this file, on sys.path, under "
        "$AGENT_REPO_ROOT/scripts, or above the cwd / the running script — "
        "set AGENT_REPO_ROOT to the Blender repo root")


_pkg_dir = _find_agent_verify()
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
for _stale in [m for m in list(sys.modules)
               if m == "agent_verify" or m.startswith("agent_verify.")]:
    del sys.modules[_stale]

import bpy  # noqa: E402
import agent_verify as _agent_verify  # noqa: E402

globals().update({n: getattr(_agent_verify, n) for n in _agent_verify.__all__})
print("AGENT_LIB_OK bpy=%s lib_sha=%s"
      % (tuple(bpy.app.version),
         _agent_verify.lib_sha(globals().get("__file__"))))

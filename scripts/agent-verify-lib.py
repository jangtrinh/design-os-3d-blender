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
import importlib
import importlib.util
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

_agent_verify_dir = os.path.realpath(os.path.join(_pkg_dir, "agent_verify"))
_bp_core_file = os.path.realpath(os.path.join(_pkg_dir, "boilerplates", "bp_core.py"))
__agent_dependency_files__ = tuple(sorted(
    [os.path.abspath(os.path.join(_agent_verify_dir, name))
     for name in os.listdir(_agent_verify_dir)
     if name.endswith(".py") and os.path.isfile(os.path.join(_agent_verify_dir, name))]
    + [os.path.abspath(_bp_core_file)]
))


def _module_file(module):
    path = getattr(module, "__file__", None)
    return os.path.realpath(path) if path else None


def _is_under(path, root):
    if path is None:
        return False
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


_owned_agent_modules = {"agent_verify"}
_owned_agent_modules.update(
    "agent_verify." + os.path.splitext(os.path.basename(_source))[0]
    for _source in __agent_dependency_files__
    if _is_under(_source, _agent_verify_dir)
    and os.path.basename(_source) != "__init__.py"
)
for _name in sorted(_owned_agent_modules):
    _existing = sys.modules.get(_name)
    if _existing is not None and not _is_under(_module_file(_existing), _agent_verify_dir):
        raise ImportError("module name collision outside verify package: %s" % _name)
_existing_bp_core = sys.modules.get("boilerplates.bp_core")
if _existing_bp_core is not None and _module_file(_existing_bp_core) != _bp_core_file:
    raise ImportError("module name collision outside verify package: boilerplates.bp_core")


# Python's timestamp-based bytecode cache can remain valid when a source file is
# edited twice within one second without changing size. Remove only bytecode for
# the dependencies this facade explicitly owns before importing them again.
for _source in __agent_dependency_files__:
    try:
        _bytecode = importlib.util.cache_from_source(_source)
    except (NotImplementedError, ValueError):
        _bytecode = None
    if _bytecode and os.path.isfile(_bytecode):
        os.remove(_bytecode)
importlib.invalidate_caches()


# Re-execution owns only this repository's verification package and its direct
# evaluated-mesh helper. Do not purge unrelated modules with similar names.
for _name, _module in list(sys.modules.items()):
    if ((_name == "agent_verify" or _name.startswith("agent_verify."))
            and _is_under(_module_file(_module), _agent_verify_dir)):
        del sys.modules[_name]
_bp_core_module = sys.modules.get("boilerplates.bp_core")
if _module_file(_bp_core_module) == _bp_core_file:
    del sys.modules["boilerplates.bp_core"]

import bpy  # noqa: E402
import agent_verify as _agent_verify  # noqa: E402

globals().update({n: getattr(_agent_verify, n) for n in _agent_verify.__all__})
print("AGENT_LIB_OK bpy=%s lib_sha=%s"
      % (tuple(bpy.app.version),
         _agent_verify.lib_sha(globals().get("__file__"))))

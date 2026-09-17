"""Disposable Blender proof for dependency-aware load_lib + verify facade reload."""

import os
import shutil
import sys
import types

import bpy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    import agent_runtime as rt

    tmp = os.path.abspath(sys.argv[1])
    scripts = os.path.join(tmp, "scripts")
    package = os.path.join(scripts, "agent_verify")
    boilerplates = os.path.join(scripts, "boilerplates")
    os.makedirs(package, exist_ok=True)
    os.makedirs(boilerplates, exist_ok=True)

    facade = os.path.join(scripts, "agent-verify-lib.py")
    shutil.copy2(os.path.join(SCRIPTS, "agent-verify-lib.py"), facade)
    write(
        os.path.join(package, "__init__.py"),
        "from .inspect_scene import probe\n"
        "from .paths import lib_sha\n"
        "__all__ = ['probe', 'lib_sha']\n",
    )
    write(
        os.path.join(package, "paths.py"),
        "def lib_sha(extra=None):\n    return 'cafebabe'\n",
    )
    write(
        os.path.join(package, "inspect_scene.py"),
        "from boilerplates.bp_core import VALUE\n"
        "def probe():\n    return VALUE\n",
    )
    bp_core = os.path.join(boilerplates, "bp_core.py")
    write(bp_core, "VALUE = 1\n")

    collision = types.ModuleType("agent_verify.inspect_scene")
    collision.__file__ = os.path.join(tmp, "foreign", "agent_verify", "inspect_scene.py")
    sys.modules[collision.__name__] = collision
    try:
        rt.load_lib(facade)
    except ImportError:
        foreign_collision_failed_closed = True
    else:
        foreign_collision_failed_closed = False
    assert sys.modules.get(collision.__name__) is collision
    del sys.modules[collision.__name__]

    foreign = types.ModuleType("agent_verify.foreign")
    foreign.__file__ = os.path.join(tmp, "foreign", "agent_verify", "foreign.py")
    sys.modules[foreign.__name__] = foreign

    first = rt.load_lib(facade)
    assert first.probe() == 1
    assert os.path.realpath(bp_core) in first.__agent_dependency_files__
    cached_when_unchanged = rt.load_lib(facade) is first
    first_bp_core = sys.modules["boilerplates.bp_core"]

    write(bp_core, "VALUE = 2\n")
    second = rt.load_lib(facade)
    dependency_reloaded = second is not first
    bound_dependency_refreshed = (
        second.probe() == 2 and sys.modules["boilerplates.bp_core"] is not first_bp_core
    )
    foreign_module_preserved = sys.modules.get(foreign.__name__) is foreign

    os.unlink(os.path.join(package, "inspect_scene.py"))
    try:
        rt.load_lib(facade)
    except FileNotFoundError:
        missing_dependency_failed_closed = True
    else:
        missing_dependency_failed_closed = False

    assert cached_when_unchanged
    assert dependency_reloaded
    assert bound_dependency_refreshed
    assert missing_dependency_failed_closed
    assert foreign_module_preserved
    assert foreign_collision_failed_closed
    assert bpy.app.background

    rt.emit_ok(
        "dependency-reload-contract",
        blender=bpy.app.version_string,
        cached_when_unchanged=cached_when_unchanged,
        dependency_reloaded=dependency_reloaded,
        bound_dependency_refreshed=bound_dependency_refreshed,
        missing_dependency_failed_closed=missing_dependency_failed_closed,
        foreign_module_preserved=foreign_module_preserved,
        foreign_collision_failed_closed=foreign_collision_failed_closed,
    )


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        rt.run_file(__file__, extra)

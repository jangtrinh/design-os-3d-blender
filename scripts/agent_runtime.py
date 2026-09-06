"""Execution-truth runtime for Blender agent payloads (stdlib only, no bpy needed).

Blender's exit code is unreliable in both directions and MCP `execute_code`
returns only captured stdout, so the one signal that survives both transports is
a line of stdout. Every payload therefore ends with one authoritative sentinel:

    AGENT_OK   {"step": ..., "postconditions": {...}, "error": null}
    AGENT_FAIL {"step": ..., "postconditions": {...}, "error": {"type","message","traceback"}}

Callers decide by the LAST sentinel line, exit code second. A forged sentinel
printed with plain `print()` cannot win: only emit_ok/emit_fail are counted, and
run_file emits the real verdict after the payload has finished.

Exit codes (background only): 0 pass - 1 requirement/assert failed - 2 invalid or
missing input - 3 uncaught execution error.

MCP usage (fresh namespace holding only `bpy`, stdout captured):
    import sys; sys.path.insert(0, "<repo>/scripts")
    import agent_runtime as rt; rt.run_file("<abs>/pass-03.py")
"""

import hashlib
import json
import os
import re
import sys
import traceback
import types

SENTINEL_OK = "AGENT_OK"
SENTINEL_FAIL = "AGENT_FAIL"

EXIT_OK = 0            # pass
EXIT_REQUIREMENTS = 1  # an assert / declared requirement failed
EXIT_INPUT = 2         # invalid or incomplete input (missing payload, bad args)
EXIT_ERROR = 3         # uncaught execution error

# Bookkeeping so run_file can tell a real emit_ok from a printed forgery, and
# so a payload's own postconditions survive into the final verdict.
_STATE = {"seq": 0, "last": None}


def is_background():
    """True when run_file may own the process exit code: Blender `-b`, or any
    process with no bpy at all (host python), where there is no GUI to kill."""
    try:
        import bpy  # noqa: PLC0415 - optional; absent in host python
    except ImportError:
        return True
    return bool(bpy.app.background)


def _sentinel(tag, step, postconditions, error):
    """Print one sentinel line and remember that we (not a print) emitted it."""
    payload = {"step": str(step), "postconditions": postconditions or {}, "error": error}
    # ensure_ascii keeps the record on a single line even for exotic messages.
    line = "%s %s" % (tag, json.dumps(payload, ensure_ascii=True, sort_keys=True))
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    _STATE["seq"] += 1
    _STATE["last"] = (tag, payload)
    return payload


def emit_ok(step, **postconditions):
    """Emit the success sentinel with the postconditions actually measured."""
    return _sentinel(SENTINEL_OK, step, postconditions, None)


def emit_fail(step, exc, **postconditions):
    """Emit the failure sentinel, carrying the exception's real traceback."""
    if isinstance(exc, BaseException):
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        error = {"type": type(exc).__name__, "message": str(exc), "traceback": tb.rstrip()}
    else:  # a plain string reason is accepted for hand-written failures
        error = {"type": "Error", "message": str(exc), "traceback": ""}
    return _sentinel(SENTINEL_FAIL, step, postconditions, error)


def exit_code_for(exc):
    """Map an exception to the frozen exit-code contract."""
    if isinstance(exc, SystemExit):
        code = exc.code
        return EXIT_OK if code is None else (code if isinstance(code, int) else EXIT_ERROR)
    if isinstance(exc, AssertionError):
        return EXIT_REQUIREMENTS
    if isinstance(exc, (FileNotFoundError, IsADirectoryError, PermissionError)):
        return EXIT_INPUT
    return EXIT_ERROR


def _finish(result, code):
    """Return the verdict dict; in background also make the exit code match."""
    if is_background():
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(code)
    return result


def run_file(path, argv=None):
    """Execute a payload file under the sentinel contract.

    The payload runs with a real `__file__`/`__name__` namespace and is compiled
    with its true filename, so tracebacks name the payload's file and line.
    Returns the verdict dict; in background mode the process also exits with the
    contract code (0/1/2/3) instead of returning.
    """
    abspath = os.path.abspath(str(path))
    step = os.path.basename(abspath)

    try:
        with open(abspath, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _finish(emit_fail(step, exc), EXIT_INPUT)

    namespace = {"__name__": "__main__", "__file__": abspath, "__builtins__": __builtins__}
    saved_argv = sys.argv
    sys.argv = [abspath] + list(argv or [])
    seq_before = _STATE["seq"]
    failure = None
    # _finish() itself raises SystemExit, so it must be called only after this
    # block has unwound - otherwise our own exit would be caught as a payload
    # failure and emit a second, bogus sentinel.
    try:
        exec(compile(source, abspath, "exec"), namespace)
    except SystemExit as exc:
        # A payload calling sys.exit(0) means success; anything else is not.
        if exit_code_for(exc) != EXIT_OK:
            failure = exc
    except BaseException as exc:  # noqa: BLE001 - catching everything is the point
        failure = exc
    finally:
        sys.argv = saved_argv

    if failure is not None:
        return _finish(emit_fail(step, failure), exit_code_for(failure))

    # The payload returned without raising. Honour its own verdict when it
    # emitted one - including emit_fail, so a payload that catches its error and
    # reports it honestly still comes back red. A merely printed sentinel is not
    # a verdict: only emit_ok/emit_fail move the counter.
    last = _STATE["last"]
    if _STATE["seq"] > seq_before and last:
        tag, verdict = last
        if tag == SENTINEL_OK:
            return _finish(verdict, EXIT_OK)
        error_type = (verdict.get("error") or {}).get("type")
        code = EXIT_REQUIREMENTS if error_type == "AssertionError" else EXIT_ERROR
        return _finish(verdict, code)
    return _finish(emit_ok(step), EXIT_OK)


def load_lib(path):
    """Exec a helper file into a module cached in sys.modules, keyed by sha256.

    The cache survives across MCP `execute_code` calls (sys.modules lives in the
    Blender process) but re-executes the moment the file's content changes, so
    editing a helper never leaves a stale copy running. Accepts filenames that
    are not valid module names (e.g. `agent-verify-lib.py`).
    """
    abspath = os.path.abspath(str(path))
    with open(abspath, "rb") as handle:
        raw = handle.read()
    digest = hashlib.sha256(raw).hexdigest()

    key = "agent_lib_" + re.sub(r"\W", "_", os.path.splitext(os.path.basename(abspath))[0])

    cached = sys.modules.get(key)
    if (cached is not None
            and getattr(cached, "__agent_lib_sha256__", None) == digest
            and getattr(cached, "__file__", None) == abspath):
        return cached

    module = types.ModuleType(key)
    module.__file__ = abspath
    module.__agent_lib_sha256__ = digest
    exec(compile(raw.decode("utf-8"), abspath, "exec"), module.__dict__)
    sys.modules[key] = module  # only cache a module that executed cleanly
    return module


def parse_sentinel(text):
    """Return (tag, dict) of the LAST sentinel line in `text`, else (None, None).

    Every caller applies this same 'last line wins' rule (the shell wrapper does
    it with `grep | tail -1`), so a forged early sentinel is always overridden.
    """
    tag_out, obj_out = None, None
    for line in str(text).splitlines():
        line = line.strip()
        for tag in (SENTINEL_OK, SENTINEL_FAIL):
            if line.startswith(tag + " "):
                try:
                    obj_out = json.loads(line[len(tag) + 1:])
                    tag_out = tag
                except ValueError:
                    pass
    return tag_out, obj_out

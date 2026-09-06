# Headless Render Check

Title: Headless Render Check
Description: Run a bpy pass or render headless against an explicit .blend
file, parse the AGENT_OK/AGENT_FAIL sentinel, and pull numeric framing/frame
stats before trusting the output. Invoke with `/headless-render-check`.

Read `.agents/rules/blender-agent-operating-rules.md` rules 2, 3, and 8
first. `<ROOT>` = absolute repo path.

## When to use this

Use when the Blender GUI is not open, or when a batch/render/fault-probe job
must not touch the live GUI session (rule 8: one writer per GUI, never bridge
headless to a live GUI file).

## Steps

1. **Confirm no GUI is holding the same file.** If the Blender GUI has this
   `.blend` open, do not run headless against it — either close it in the
   GUI first or work on a copy.

2. **Run headless with an explicit blend file:**
   ```bash
   bash scripts/headless-run.sh <pass.py> --blend <path/to/file.blend>
   ```
   This runs with `--factory-startup`, no autoexec, and an exit code that
   mirrors the sentinel.

3. **Parse the sentinel from stdout — the LAST line only:**
   - `AGENT_OK {json}` → proceed to step 4.
   - `AGENT_FAIL {json}` → read the `traceback`/`error` field in the JSON,
     fix the root cause, and re-run. Do not retry the identical payload
     unchanged. The shell exit code is a secondary signal only — the
     sentinel line is authoritative per rule 2.

4. **Pull numeric evidence before any image:**
   ```python
   import sys; sys.path.insert(0, "<ROOT>/scripts")
   import agent_runtime as rt
   lib = rt.load_lib("<ROOT>/scripts/agent-verify-lib.py")
   framing(obj)
   frame_stats()
   ```
   `frame_stats()` stdev < 0.01 flags a flat/black frame — check camera
   position, light existence, and `persistent_data=False` before assuming
   the render is correct.

5. **If a rendered image is genuinely needed** (composition/appearance a
   number cannot answer), generate it via the headless pass and `open` the
   resulting file so a human can see it — do not silently render and only
   report a verdict with no visual handed back.

6. **Two failures on the same headless job with the same approach → change
   the approach class** (e.g. stop retrying `bpy.ops` boolean ops, switch to
   a data-API/bmesh equivalent). **Three failures → `request-input`.**

## Non-goals

This workflow does not run `production-gate.py` (see `build-printable-part`)
and does not open or drive the interactive MCP session.

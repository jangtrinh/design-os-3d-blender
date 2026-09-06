# Build Printable Part

Title: Build Printable Part
Description: Take a production part from spec to a gated, deliverable build —
spec.json first, then bpy passes, then the production gate, then handoff.
Invoke with `/build-printable-part`.

Read `.agents/rules/blender-agent-operating-rules.md` and `AGENTS.md` before
running this. `<ROOT>` = absolute repo path (e.g. `/Users/jang/Products/Blender`).
`<slug>` = the part's build slug under `builds/`.

## Steps

1. **Contract.** Confirm or write `builds/<slug>/spec.json` against
   `specs/build-spec.schema.json`: dimensions + tolerances, holes/bosses,
   fasteners, material/process, print orientation, min wall, load case. If
   any of these is missing, stop here with verdict `request-input` — do not
   proceed to geometry.

2. **Plan the scene graph.** Write down objects, hierarchy, relative
   positions, materials, camera/lights (if a render is also needed) before
   writing any code.

3. **Write one pass file per step.** Each file
   `builds/<slug>/pass-NN-<purpose>.py`, data-API first (`bpy.ops` only when
   unavoidable), ≤ ~80 lines, ending in `rt.emit_ok(step, **postconditions)`.

4. **Execute each pass.**
   - Interactive (GUI Connected):
     ```python
     import sys; sys.path.insert(0, "<ROOT>/scripts")
     import agent_runtime as rt
     rt.run_file("<ROOT>/builds/<slug>/pass-NN-<purpose>.py")
     ```
     via the MCP `execute_blender_code` tool.
   - Headless (no GUI open):
     ```bash
     bash scripts/headless-run.sh builds/<slug>/pass-NN-<purpose>.py
     ```
   Decide success ONLY from the last stdout line: `AGENT_OK {...}` or
   `AGENT_FAIL {...}`.

5. **Verify each pass** with numeric asserts first (see
   `verify-pass` workflow) before any screenshot/render.

6. **Run the production gate** once all passes complete:
   ```bash
   python3 scripts/production-gate.py --scene builds/<slug>/<slug>.blend \
     --spec builds/<slug>/spec.json --report builds/<slug>/gate-report.json
   ```
   Exit code must be 0. If not, verdict is `refine-code` or `refine-spec`
   depending on whether the gate failure traces to geometry or to the spec
   itself — do not patch around a gate failure without knowing which.

7. **Deliver.** Record separate status for media / motion / fit /
   manufacture in the build's README-equivalent note. Attach
   `gate-report.json`, input hashes, and frame range if animated. Any
   geometry change after this point voids the prior gate report — rerun step
   6.

## Non-goals

Do not call PolyHaven/Sketchfab/Hyper3D/Hunyuan tools, and do not download
any vendor asset — see rule 7 in the operating rules file.

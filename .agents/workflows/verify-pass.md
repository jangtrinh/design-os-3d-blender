# Verify Pass

Title: Verify Pass
Description: Run the cheap-to-expensive verify ladder on one Blender pass —
numeric asserts before any screenshot or render. Invoke with `/verify-pass`.

Read `.agents/rules/blender-agent-operating-rules.md` rule 4 first.
`<ROOT>` = absolute repo path. `<slug>` = build slug under `builds/`.

## Steps

1. **Load the verify library** inside the payload (fresh namespace each
   call — do not assume a prior import persisted):
   ```python
   import sys; sys.path.insert(0, "<ROOT>/scripts")
   import agent_runtime as rt
   lib = rt.load_lib("<ROOT>/scripts/agent-verify-lib.py")
   ```

2. **Numeric asserts first.** Pick what applies to this pass and run it via
   `execute_blender_code` (interactive) or a headless pass file:
   - `assert_exists(name)` — object was actually created.
   - `tri_count(obj)` — mesh complexity in range.
   - `world_bbox(obj)` — dimensions/placement match the spec/plan.
   - `has_material(obj)` — material assigned.
   - fcurve keyframe count — animation data present when expected.
   If any assert fails, stop here — do not proceed to a screenshot to "see
   what happened". Fix the pass first (verdict `refine-code`) or the spec
   (verdict `refine-spec`).

3. **preview_render, only if the asserts above cannot answer the question**
   (e.g. material/lighting appearance, not just geometry existence):
   ```python
   framing(obj)
   preview_render(engine="EEVEE")  # or "CYCLES"
   frame_stats()
   ```
   `frame_stats()` stdev < 0.01 means a flat/likely-black frame — diagnose
   before trusting the render as evidence.

4. **Viewport screenshot — write the expectation BEFORE calling it.**
   State in the response: "Expect: <what should be visible>. Would falsify:
   <what would prove this wrong>." Then call the MCP `get_viewport_screenshot`
   tool and compare against that written expectation, not a vague impression.

5. **Escalate only if still unresolved:** low-sample Cycles preview →
   comparison sheet (when a reference image exists, via
   `scripts/make-comparison-sheet.sh`) → turntable
   (`scripts/turntable-preview.py`).

6. **Record the verdict**: `continue`, `refine-spec`, `refine-code`,
   `request-input`, or `stop`. Two failures on the same step with the same
   approach class → change the approach; three failures total →
   `request-input`.

## Non-goals

This workflow does not run the production gate (see `build-printable-part`
step 6) and does not decide delivery — it only verifies one pass.

---
name: blender-agent-core
description: Core discipline for ANY Blender/bpy work — contract-first, purpose-first (render-only / print / both), knowledge routing, execute-verify-refine loop with the AGENT_OK/AGENT_FAIL sentinel contract, numeric-first verification, Form gate before delivery media, production gate before delivery. Activate for every task that touches Blender, before any domain skill.
---

# Blender Agent Core

This skill is a ROUTER + procedure. The deep knowledge lives in `knowledge/` — load exactly the file you need, do not recall it from memory. The root operating rules are in `AGENTS.md` (precedence: `.project-agent.md` > `AGENTS.md` > this skill). The `.agents/skills/` copy is the source; `.claude/skills/` is a mirror that must be kept in sync.

## 0. Routing by task
| Task | Also load |
|---|---|
| Task starts and the deliverable **purpose** is not stated | Ask once — render-only / 3D print / both, recommendation **both**; record `purpose:` in `state.md` (`AGENTS.md` loop 0b) |
| Purpose `print`/`both`, phase 2 (form + interfaces) is complete | **Form gate**: temporary bake → compare with independent authored spec → `production-gate.py` exit 0; **final gate** at delivery. Existing unknown shapes use [measurement provenance](references/recipes.md#spec-from-measurement), not self-derived acceptance. Verification imagery stays available |
| Part will be printed/manufactured, needs exact dimensions/standards | [Production contract](references/recipes.md#production-contract) → `specs/README.md` |
| Execute via MCP/headless, read errors | [Explicit execution context](references/recipes.md#explicit-execution-context) |
| Reference image available | Skill `blender-image-to-3d` |
| Joints, hands, manipulation, animation tasks | [Articulated task](references/recipes.md#articulated-task) |
| Assembly/exploded view | [Assembly sequences](references/assembly-sequences.md) |
| Load-bearing, duty, working mechanism | [Mechanical evidence](references/recipes.md#mechanical-evidence) |
| Batch render, video, export | [Render delivery](references/recipes.md#render-delivery) |
| Turntable / product shot | `scripts/turntable-preview.py` + `knowledge/60-pipeline/product-viz-and-shots.md` |
| Python API research, evaluated geometry, Action slots or Geometry Nodes inputs | `knowledge/00-foundations/native-api-contracts.md`; route the relevant contract topic through `blender-knowledge-workbench` |
| Multi-pass native work needs resumable evidence, explicit parameters or independent criticism | `knowledge/60-pipeline/native-agent-iteration.md`; use `scripts/native-pipeline.py` for declared execution and `scripts/native-review.py` for revision-bound review |
| Start a production-grade product or conduct a session retro | `docs/product-workflow-template.md`; `native-hard-surface --topic session-retrospective` |
| Surprising bore/wall/collision/export result or a tolerance-extreme failure | `knowledge/60-pipeline/geometry-diagnostic-workflow.md`; `precision-assembly-metrology --topic geometry-diagnostics` |
| Native Full HD, social media or new media after a model revision | `knowledge/60-pipeline/native-render-delivery.md`; `render-export-delivery --topic native-render-delivery` |
| Retention, material/process, electronics or physical manufacturing blocker | `knowledge/60-pipeline/manufacturing-evidence-workflow.md`; `precision-assembly-metrology --topic manufacturing-evidence` |

Read the [hard rules](references/hard-rules.md) every session (state explicitly which are ENFORCED vs MANUAL). Deliver results per [revision-bound acceptance](references/recipes.md#revision-bound-acceptance).

## 1. Knowledge routing (mandatory)
At the start of every Blender task, read the **3 foundation files** if they are not already in context: `knowledge/00-foundations/blender-version-matrix.md`, `bpy-scripting-core.md`, `agent-workflow-loop.md`. Then `python3 scripts/blender-knowledge.py list` → `route <workflow-id>` to obtain the reading pack (skill `blender-knowledge-workbench`); load only the part you need. `knowledge/INDEX.md` is an on-demand lookup, not a must-read. `loads_with` is a one-hop hint, not a recursive load (one hop ≈ 40–50k tokens).

## 2. Loop (R1–R8 condensed — full version in agent-workflow-loop.md)
1. **Contract first** — purpose first (render-only / print / both, default `both`), then spec.json for a production part; fidelity contract for a reference; missing numbers → `request-input`.
2. **Decompose** — scene graph → one file per pass, ≤ ~80 lines, one purpose.
3. **Assert every step** — a pass ends with `rt.emit_ok(step, **postconditions)`; the postcondition must FAIL if the step silently no-ops; operator return must be `{'FINISHED'}`.
3b. **Form gate closes phase 2** when purpose is `print`/`both`: measure a temporary bake against the authored spec. Keep required dimensions/tolerances independent of output. Delivery media needs PASS or an owner waiver; final gate applies at delivery. Verification imagery stays mandatory, available and cheap (≤512 px / low-sample, roughly ≤2 minutes per pass).
4. **Non-destructive scaffold** — the lib's `scaffold()` reads first and writes only when factory-default or `force=True`; never reset the scene being worked on.
5. **Screenshot with intent** — write down the expectation and what would falsify it BEFORE looking.
6. **2 failures on the same step → change the CLASS of approach; 3 failures → `request-input`.**
7. **Checkpoint** (`checkpoint(tag)`) before every destructive op (boolean, apply, join).
8. **Know the handoff boundary** — fine weight painting, facial rig, art direction: flag early.

After a saved artifact and a failed wrapper/journal result, inspect both before any
retry. Correct a metadata/dependency failure without rebuilding valid geometry.
Required pipeline postconditions are finite numbers; hashes belong in receipts.
Check maximal tolerance stroke and a failing control, not only nominal endpoints.
Keep actual component selection, logic/ECAD, firmware and physical qualification
as separate closure rows. A successful pilot-record check cannot authenticate a lab.

The generic production schema also supports partial diagnostics: missing minimum
wall can be skipped, and required-check coverage is aggregated across parts.
For print/both completion, manually confirm every applicable part declares its
wall limit and actually passes its required wall/features/export checks. A stage
waiver does not remove the physical manufacturing scope or turn it into a pass.

## 3. Verify ladder (cheap → expensive; if a number answers the question, do not spend an image)
```python
import sys; sys.path.insert(0, "<ROOT>/scripts")
import agent_runtime as rt; lib = rt.load_lib("<ROOT>/scripts/agent-verify-lib.py")
```
1. Numbers: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys — plus the postconditions in `AGENT_OK`. Bounds use evaluated mesh vertices and transforms; active-view-layer settings, children and instances need an explicit scope. Borrow temporary meshes with `evaluated_mesh()` and copy independent data before leaving its context.
2. Assert `framing(obj)['in_frame']` (image bounds plus front/near/far depth) → `preview_render(engine="EEVEE"|"CYCLES")` (≈0.1–0.2 s at 128–256px on a small scene, restores state) → `frame_stats()` (stdev < 0.01 = flat frame, needs diagnosis). The numeric screen does not prove occlusion, render visibility or render-border coverage.
3. Viewport screenshot (MCP) — composition, "does it look like it".
4. Low-sample Cycles preview — real material/lighting.
5. Comparison sheet (`scripts/make-comparison-sheet.sh`) — when a reference image exists.
6. Turntable (`scripts/turntable-preview.py`) — guards against the "cardboard cutout" look.
7. **Part production:** `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0; attach the report to the build. The gate proves topology/dimensions/screening numbers — it does **not** prove load, real fit, or thermal duty.

Measured on this machine: cold start 0.5 s, 256px preview ≈ 0.4–2 s. Verification is cheap; the ladder order follows information value, not cost.

## 4. Execution modes (check in order)
1. **MCP tools** (addon Connected): `rt.run_file("/abs/pass.py")` — full traceback inside `AGENT_FAIL`; a fresh namespace per call, reload helpers with `rt.load_lib` (cached by sha). Read the scene read-only before mutating.
2. **Socket bridge** when the MCP tool is not loaded: `python3 scripts/blender-socket-client.py execute_code --file pass.py` (exit 0/1/2/3 per the sentinel; output is not truncated).
3. **Headless** for batch/fault-test/gate: `bash scripts/headless-run.sh pass.py` (`--factory-startup --disable-autoexec --python-exit-code 3`; exit follows the sentinel). Supply a sheet/preview after every pass; when the build is finished, open the right file for the user.
General rule: decide from the **last line** `AGENT_OK`/`AGENT_FAIL`; a timeout after sending a mutation = unknown → read the state before resending; a single writer for the GUI.

## 5. Failure quick-map
| Symptom | Read |
|---|---|
| `NameError` on a helper/`__file__` inside "executed successfully" | §4 — import inside the payload, `rt.load_lib` |
| STL/topology assert fails although the mesh looks fine | `production-gate.py` topology; 3d-printing.md §5 |
| Endpoints PASS, parts overlap mid-motion | assembly-sequences.md; sweep per frame |
| Black/flat render | `framing()` + `frame_stats()`; `persistent_data=False`; lighting.md |
| KeyError on socket/enum | version-matrix §renames — introspect `[s.name for s in node.inputs]` |
| Boolean shreds the mesh | modifiers.md §boolean-solver + the checkpoint before it |
| Export breaks in another engine | export-interchange.md + `verify_export()` (separate process) |

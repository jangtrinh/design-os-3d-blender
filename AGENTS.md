# AGENTS.md — Blender AI Orchestration (primary operational file)

**Precedence order on conflict:** `.project-agent.md` (identity + binding rules) > this file > `.agents/skills/*/SKILL.md` + references > `knowledge/` > `docs/` (narrative, not law). `CLAUDE.md` only imports this file. A rule marked `MANUAL` = controller discipline, not yet enforced by code.

## Mission
`<ROOT>` in this file = the absolute path of the repo on the machine currently running (e.g. Jang's local: `/Users/jang/Products/Blender`).

AI builds 3D/animation/render in Blender **5.2.0 LTS** (local = KB target) through 2 routes:
- **Interactive:** MCP server `blender` → addon in the GUI (must Connect). Usable tools: `execute_blender_code`, `get_object_info`, `get_viewport_screenshot`, `get_scene_info` (returns only the first 10 objects — get the full list with bpy). The PolyHaven/Sketchfab/Hyper3D/Hunyuan/`set_texture` tools are **forbidden** by the Native Asset Policy.
- **Headless:** `scripts/headless-run.sh <pass.py>` — new process with `--factory-startup`, used for batch, render, fault-probe, gate.

Product goal (Jang, 2026-09-06): **production level — 3D-printable, dimensionally correct, standards-compliant.** An image/video that "looks right" is not acceptance.

## Mandatory loop for every scene-building task
```
Contract → Plan (scene graph) → Code (pass files) → Critic → Execute → Verify → Verdict
```
0. **Contract before going into detail.** A part that will be printed/manufactured → write `builds/<slug>/spec.json` following `specs/build-spec.schema.json` (dimensions ± tolerances, holes/bosses, standard-compliant fasteners, material/process, print orientation, min wall, declared load case). Missing dimensions/payload/duty → verdict `request-input`, do **not** build detail. Reference image available → fidelity contract (skill `blender-image-to-3d`). History: every full rebuild was caused by the spec arriving after detailing had started.
1. **Plan:** scene graph — objects, hierarchy, positions, materials, camera, lights. Long task → `plans/`.
2. **Code:** data API first, `bpy.ops` is the exception (`knowledge/00-foundations/bpy-scripting-core.md`). Each pass = 1 file `builds/<slug>/pass-NN-<purpose>.py` ≤ ~80 lines, ending with a numeric postcondition via `emit_ok`.
3. **Critic (self-check):** are import/`__file__` inside the payload (the MCP namespace does not persist)? have socket/enum/operator names been introspected at runtime? units (1 BU = 1 m, spec in mm)? mutation before assert? destructive op → `checkpoint()` first?
4. **Execute:**
   - MCP: `import sys; sys.path.insert(0, "<ROOT>/scripts"); import agent_runtime as rt; rt.run_file("/abs/builds/<slug>/pass-NN.py")`
   - Headless: `bash scripts/headless-run.sh builds/<slug>/pass-NN.py`
   - **Decide by the last stdout line** `AGENT_OK {json}` / `AGENT_FAIL {json}`; "Code executed successfully" is only transport. Blender's exit code is wrong in both directions. Timeout after a mutation has already been sent → outcome unknown: read state before sending again.
5. **Verify ladder (cheap → expensive; if a number can answer it, spend no image):** (1) numeric asserts: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys → (2) `framing()` + `preview_render(engine="EEVEE"|"CYCLES")` + `frame_stats()` (≈0.2 s at 256px on a small scene, both engines run headless on macOS; restore state) → (3) viewport screenshot **after writing down the expectation + what would falsify it** → (4) low-sample Cycles preview → (5) comparison sheet when a reference exists → (6) turntable. Production part: `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0 before delivery; attach the report.
6. **Verdict (pick exactly 1):** `continue` · `refine-spec` (root cause is in the spec — fix the spec first) · `refine-code` · `request-input` · `stop` (= tell the user, change direction). 2 failures at the same step → change the approach **class**; 3 failures → `request-input`.

**Owner decision points (MANUAL, mandatory):** blockout sheet before detailing; animatic ≤ 120 frames before any render > 120 frames; long renders only after the owner has seen and signed off. Record: 2 render-then-discard events (~26 minutes, ~3,000 frames) happened after a retro had already written this rule down as prose.

## Failure map (from real records, not theory)
| Symptom | Common cause | What to do |
|---|---|---|
| `NameError` inside "executed successfully" | helper/import from the previous call no longer exists | put the import + `rt.load_lib()` in the payload |
| Geometry/STL assert fails although the mesh looks "clean" | degenerate faces, non-manifold after boolean | `production-gate.py` topology + re-read the STL |
| Endpoint PASS but interpenetration mid-motion | only the final state was verified | per-frame sweep + animatic; `assembly-sequences.md` |
| Black render / black silhouette | persistent_data stale, camera inside a wall, no light | `framing()`, `frame_stats()`, `persistent_data=False` |
| Render correct but owner rejects it | camera/pacing/scope not in the contract | `refine-spec`; ask first, do not blindly re-render |
| `ModuleNotFoundError` (scipy/fitz) | Blender's Python ≠ host Python | `importlib.util.find_spec` in preflight; code must not depend on it |
| MCP connection error | addon not Connected | tell the user, do not retry |

## Visual feedback for the user (MANDATORY)
MCP live: the user watches objects grow in the viewport. Headless: after each pass `open <sheet.png>`; when the build finishes `open -a Blender <file.blend>`. Build > 2 minutes → announce the number of passes + a time estimate up front.

## Delivery
The build's README records **separate** status for media / motion / fit / manufacture; attach `gate-report.json`, input hashes, frame range; geometry changed → old evidence is void. Do not infer load/thermal/strength from numeric checks or video; missing physical evidence → manufacture **BLOCKED**, stated explicitly.

## Resource map
| Need | Read/use |
|---|---|
| Detailed loop, execution modes, verify ladder | `.agents/skills/blender-agent-core/SKILL.md` (+ `references/`) |
| Reference image available | `.agents/skills/blender-image-to-3d/SKILL.md` |
| Reading pack for the task | `python3 scripts/blender-knowledge.py list` / `route <workflow-id>` (skill `blender-knowledge-workbench`) |
| 3 foundation KB files (mandatory) | `knowledge/00-foundations/{blender-version-matrix,bpy-scripting-core,agent-workflow-loop}.md` |
| Production spec/gate | `specs/README.md`, `scripts/production-gate.py` |
| Sense organs inside bpy | `scripts/agent-verify-lib.py` (safe read-only; `preview_render` restores state; `verify_export` runs a separate process) |
| Fast preview / image comparison | `scripts/turntable-preview.py`, `scripts/make-comparison-sheet.sh` |
| Architecture, backlog | `docs/system-architecture.md`, `docs/blender-workflow-improvement-backlog.md` |

Native Asset Policy, QRemeshify gate and the other binding rules: `.project-agent.md` (not repeated here).

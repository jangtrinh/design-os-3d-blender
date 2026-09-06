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
0b. **Purpose, asked before the contract in step 0 (MANUAL).** Ask once, at task start: *render-only / 3D print / both?* — recommendation **both**. Record it in `builds/<slug>/state.md` as `purpose: <answer> (owner <time>)` and in `design-parameters.json`. No answer → `purpose: assumed both` and build print-ready; a later downgrade is noted, never a rebuild. Purpose already stated in the request → do not ask. Purpose fixes the mesh strategy before the first pass:

| Purpose | Solids & booleans | Walls / holes / keys | Curved-surface segments | Scale |
|---|---|---|---|---|
| `render-only` | closed enough for the camera; overlap may stand in for a boolean | relief may be shader-only; blind holes acceptable | as low as the silhouette tolerates | 1 BU = 1 m |
| `print` / `both` (default) | every part one closed solid, signed volume > 0, transforms applied, EXACT boolean + `checkpoint()` — never faked by overlap | real walls ≥ spec `min_wall_mm`, holes modelled through, keyed flats modelled (`keyed_flat_mm`) | ≥ 64 (default, editable per part) on any surface the gate measures a diameter or wall on | 1 BU = 1 m, spec in mm |

Getting this wrong costs a rebuild, not a tweak: `render-only` geometry cannot be gated later without re-modelling the walls.

1. **Plan:** scene graph — objects, hierarchy, positions, materials, camera, lights. Long task → `plans/`.
2. **Code:** data API first, `bpy.ops` is the exception (`knowledge/00-foundations/bpy-scripting-core.md`). Each pass = 1 file `builds/<slug>/pass-NN-<purpose>.py` ≤ ~80 lines, ending with a numeric postcondition via `emit_ok`.
3. **Critic (self-check):** are import/`__file__` inside the payload (the MCP namespace does not persist)? have socket/enum/operator names been introspected at runtime? units (1 BU = 1 m, spec in mm)? mutation before assert? destructive op → `checkpoint()` first? does the mesh match the 0b row for the recorded purpose (closed solids, real walls, segment count)?
4. **Execute:**
   - MCP: `import sys; sys.path.insert(0, "<ROOT>/scripts"); import agent_runtime as rt; rt.run_file("/abs/builds/<slug>/pass-NN.py")`
   - Headless: `bash scripts/headless-run.sh builds/<slug>/pass-NN.py`
   - **Decide by the last stdout line** `AGENT_OK {json}` / `AGENT_FAIL {json}`; "Code executed successfully" is only transport. Blender's exit code is wrong in both directions. Timeout after a mutation has already been sent → outcome unknown: read state before sending again.
5. **Verify ladder (cheap → expensive; if a number can answer it, spend no image):** (1) numeric asserts: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys → (2) `framing()` + `preview_render(engine="EEVEE"|"CYCLES")` + `frame_stats()` (≈0.2 s at 256px on a small scene, both engines run headless on macOS; restore state) → (3) viewport screenshot **after writing down the expectation + what would falsify it** → (4) low-sample Cycles preview → (5) comparison sheet when a reference exists → (6) turntable. Production part: `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0 before delivery; attach the report.
5b. **Two gates when purpose is `print` or `both` (MANUAL).**
   - **Form gate — the closing condition of phase 2 (build phases: 1 blockout · 2 form + interfaces · 3 detail + materials · 4 studio + composition · 5 delivery), before any material, studio or delivery-media work:** temporary identity bake of the printable parts (`pass-NN-print-prep` pattern) → `spec.json` written from measurement (skill `blender-agent-core` → recipes "Spec from measurement") → `production-gate.py` exit 0. **No *delivery* still, film or turntable starts before this gate is PASS or waived.** *Delivery media* = the images/films/turntables produced for the owner in phases 4–5. **Verification imagery is exempt and stays MANDATORY:** verify-ladder rungs 2–6 (`preview_render`, viewport screenshot, low-sample Cycles, comparison sheet, turntable) and per-pass clay/pose renders are how a pass proves itself (see step 5 and §Visual feedback) — they are never blocked by a gate. Verification imagery stays cheap: ≤ 512 px or low-sample, ≤ ~2 min GPU per pass; anything costlier, or anything the owner is asked to accept, is delivery media and needs the gate. Gate ≈ 3 s; the delivery media it protects ≈ 1 h (2026-09-06 watch winder: a 0.9 mm knife edge surfaced only after 16 stills and 2 films — 53 min GPU re-rendered).
   - **Final gate — at delivery**, on the delivered print bake. Both gates must PASS or be waived; a report bound to another scene/spec sha is not reusable.
   - **Gate waiver:** one owner-quoted line in `state.md` — `GATE WAIVED <time> "<owner words>"`. README manufacture then reads NOT_REQUESTED. Silence is never a waiver.
   - Gate fails → `refine-spec` (root cause in the spec) or `refine-code`; max 3 runs, then `request-input`.
   - Purpose `render-only`, or no printable part → both gates are skipped and README manufacture = NOT_REQUESTED. Say so explicitly; do not leave it blank.
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
| Gate `wall_thickness_screen` fails at ~1 mm on a lathe part that is 2.5 mm thick everywhere | a bore/opening meets a curved inner wall → knife edge at the lip (watch winder shell: 0.9 mm) | truncate the cavity with a flat ceiling one wall below the rim; a D-keyed hole needs `keyed_flat_mm` + `keyed_flat_dir` in the spec, not a wider `tol_mm` |
| Boolean cuts a hole with no walls / leaves boundary edges, or `DIFFERENCE` empties the target | target or cutter mesh is inside-out (signed volume < 0 — procedural lathes/fans are the usual culprit) | assert signed volume > 0 and 0 non-contiguous edges on BOTH operands before adding the modifier (`builds/watch-winder-capsule/scripts/ww_mesh.py::orient_outward`) |

## Visual feedback for the user (MANDATORY)
MCP live: the user watches objects grow in the viewport. Headless: after each pass `open <sheet.png>`; when the build finishes `open -a Blender <file.blend>`. Build > 2 minutes → announce the number of passes + a time estimate up front.

## Delivery
The build's README records **separate** status for media / motion / fit / manufacture; attach `gate-report.json`, input hashes, frame range; geometry changed → old evidence is void. Do not infer load/thermal/strength from numeric checks or video; missing physical evidence → manufacture **BLOCKED**, stated explicitly.

**Media evidence void (geometry changed after media exists, MANUAL):** never re-render automatically. The README media rows carry `rendered from <blend sha>` and a `current <blend sha>` line marked *pre-change*; then ask the owner **exactly one** question, with a GPU estimate per media set (stills / film / turntable), and quote the answer in `state.md`. Owner declines → the mismatch line stays in the README permanently, that is the honest record. Owner accepts → archive the old set (`renders/<set>-pre-<tag>/`) and never overwrite it.

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

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
5. **Verify ladder (cheap → expensive; if a number can answer it, spend no image):** (1) numeric asserts: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys → (2) `framing()` + preview with the established working engine + `frame_stats()`; restore state and measure actual cost rather than assume renderer availability/speed → (3) viewport screenshot **after writing down the expectation + what would falsify it** → (4) low-sample Cycles preview → (5) comparison sheet when a reference exists → (6) turntable. Production part: `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0 before delivery, plus the per-part coverage review below; attach the report.
5b. **Two gates when purpose is `print` or `both` (MANUAL).**
   - **Form gate** closes phase 2 before delivery materials/studio/media: temporary identity bake → compare actual measurements with the independently authored `spec.json` → `production-gate.py` exit 0. Do not replace a failed target with the observed output. For pre-existing geometry without a target, follow the recipe "Spec from measurement" and label the resulting dimensions as provisional observations, not proof of design intent. **Verification imagery remains mandatory and exempt:** numeric checks, framing, low-sample previews, comparison sheets and short pose views remain available to diagnose the part. Keep them ≤512 px or low-sample and roughly ≤2 minutes per pass. Costlier or owner-acceptance imagery is delivery media and requires the applicable gate or an explicit waiver.
   - **Final gate — at delivery**, on the delivered print bake. Both gates must PASS or be waived; a report bound to another scene/spec sha is not reusable.
   - **Gate waiver:** record `GATE WAIVED <time> "<owner words>"` and the specific waived stage in `state.md`. A waiver authorizes that stage only; for `print`/`both`, manufacture remains `BLOCKED` while required evidence is absent, and the waived check remains visible. `NOT_REQUESTED` requires an explicit purpose change removing manufacture, or a task with no manufacturing scope. Silence is never a waiver.
   - Gate fails → `refine-spec` (root cause in the spec) or `refine-code`; max 3 runs, then `request-input`.
   - Purpose `render-only`, or no manufacturing scope → manufacturing gates are not requested and README manufacture = NOT_REQUESTED. Machined parts and electrical assemblies still have manufacturing scope even when nothing is 3D printed; use the applicable geometry and domain-specific gates.
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

## Product evidence and recovery

For a new product, use `docs/product-workflow-template.md`. These rules consolidate
the CK-001 session; details route through the existing three skills.

- Keep requirements, measured output and acceptance separate. Source drawings,
  primary photos, generated secondary sheets and local design adaptations have
  different authority. Pin actual bytes; a filename or source URL alone is not a
  verified input. Do not make a rendered concept stand in for the saved model.
- Check nominal and tolerance-extreme interfaces, plus a discriminating negative
  control. Inspect actual common-Z geometry, mating features and access. A sample
  sweep is not continuous clearance; a pre-tap bore is not the final thread wall.
- A surprising result needs a geometry/spec/checker/environment diagnosis before
  changing the part. Do not lower min-wall requirements, remove physical features
  or simplify a measured surface to bypass the checker. Coverage failures need a
  bounded predicate fix and wrong-result regressions on unchanged source geometry.
- `native-pipeline.py` requires finite numerical postconditions and explicit
  producer dependencies. Put SHA strings in evidence metadata. If a saved build
  exists after wrapper/schema failure, inspect its identity and verify that artifact
  through a new declared route; retain the failed journal and do not rebuild just
  to obtain a green history. New run names do not reset the failure budget.
- A saved report is evidence only for its inputs and scope. Treat export, media,
  visual review, electrical logic, ERC/DRC, target firmware and physical pilot
  records as separate domains. Missing physical measurements stay missing; a
  logic checker or role name cannot manufacture them.
- Preflight each view at the requested aspect and apparent scale before batching.
  Check actual image headers and fully decode video. Share-quality review includes
  originals and decoded motion, not only thumbnails or a transport success.

Enforcement is scoped: manifests, runtime helpers, geometry gates and critic packet
bindings are implemented on their declared routes; visual judgment, source
applicability, physical tests and cross-domain release decisions still need the
controller or the responsible engineer. See `docs/ck-001-session-retrospective.md`.

**Production coverage review (MANUAL):** the generic schema permits omitted
`min_wall_mm` for partial diagnostics, and `required_checks` coverage is aggregated
across parts. A green generic report therefore does not establish that every part
received a wall check. Before print/both delivery, require a positive authored
minimum wall for every applicable part, request `wall_thickness_screen`, and
inspect each part's actual non-skipped result along with all other required
features. Keep deliberate partial diagnostics labeled partial; never remove the
wall requirement to bypass a failure. This is a controller completion requirement,
not an unimplemented universal schema invariant.

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

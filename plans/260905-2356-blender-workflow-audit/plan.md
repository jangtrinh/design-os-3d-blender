---
status: implemented-2026-09-06 (E4–E7 open; see reports/impl-00-controller-summary.md)
date: 2026-09-06
owner: Jang (goal) · controller: Claude session blender-9e
goal: Outputs production-level — 3D-printable, dimension-correct, standards-correct. Media that "looks right" is not acceptance.
---

# Blender workflow audit → improvement program

## Evidence (reports/)
- `audit-01-instructions-skills-consistency.md` — entry layer stale (2 dead skill names in the mandatory loop, ~26k-token mandatory load, no precedence, 0 enforced gates).
- `audit-02-knowledge-api-verification.md` — KB facts 62/67 PASS; 4/11 copy-paste helpers fail on 5.2.0 (`set_engine`, `enable_cycles_gpu`→CPU silently, `edit_armature`, glb size gate).
- `audit-03-scripts-boilerplates-tests.md` — exit code unreliable both ways; `headless-run.sh` false green; runner PASS = magic string; `verify_export` wipes scene; 14/19 scripts untested; verify cycle ≈0.9 s.
- `audit-04-session-friction-archaeology.md` — ≈8,400 frames discarded; root class = verification shape + commit-before-contract; owner caught 2 defects after internal PASS; Markdown rules did not bind.
- `research-05-external-state-of-art.md` — ideas only (pre-exec lint, scene-graph JSON, primed VLM verify); its "EEVEE headless unsupported on macOS" is contradicted by a local probe (renders in 2.1 s).
- `astra-06-builder-perspective.md` — builder (Codex gpt-6-astra) ranks: checkable contract > failure propagation > revision-bound gates; wants `tool --scene --spec --report`, exit 0/1/2/3.
- Controller probes: MCP `execute_code` returns only `str(e)` (no traceback), fresh namespace per call, `get_scene_info` capped at 10 objects; EEVEE headless OK; no pyright/fake-bpy locally.

## Root causes → workstreams
| # | Root cause | Workstream | Owner | Files (disjoint) |
|---|---|---|---|---|
| W1 | Execution truth: exit 0 on failure, no traceback via MCP, socket client defects | sentinel contract + `agent_runtime.py` + fixed `headless-run.sh` + socket client + tests | worker A | `scripts/headless-run.sh`, `scripts/blender-socket-client.py`, `scripts/agent_runtime.py` (new), `tests/execution/test_headless_run.py`, `tests/execution/test_socket_client.py` |
| W2 | Verify helpers clobber/wipe state; 3 scaffolds; lib duplicated in KB | rewrite `agent-verify-lib.py` (finally, isolated export, non-destructive scaffold, EEVEE preview), dedupe KB §4 → reference the lib, rename KB destructive scaffold; tests | worker B | `scripts/agent-verify-lib.py`, `knowledge/00-foundations/agent-workflow-loop.md` §4 only, `knowledge/60-pipeline/scene-organization.md` scaffold only, `tests/execution/test_verify_lib.py` |
| W3 | No checkable production contract; print gates scattered per build | `specs/build-spec.schema.json` + `scripts/production-gate.py` + `scripts/production_gate/` predicates + fixtures/tests | worker C | `specs/**`, `scripts/production-gate.py`, `scripts/production_gate/**`, `tests/production-gate/**` |
| W4 | Entry layer stale/heavy/duplicated; no precedence | rewrite `AGENTS.md` (canonical), `CLAUDE.md` → `@AGENTS.md`, fix `.project-agent.md` rule 2, update core skill + hard-rules + recipes, demote INDEX, mirror sync, catalog rebuild | controller | `AGENTS.md`, `CLAUDE.md`, `.project-agent.md`, `.agents/skills/blender-agent-core/**`, `knowledge/INDEX.md`, `docs/*.md`, `.claude/skills` mirror |
| W5 | KB helper code fails on 5.2; runner PASS defeatable; counts drift | fix 4 blockers + 6 GN socket ids + IMAGE_EDITOR + EEVEE-macOS statement; runner uses sentinel + `--python-exit-code`; single generated boilerplate registry | worker D | `knowledge/30-lighting-render/render-engines.md`, `knowledge/40-animation/rigging-armature.md`, `knowledge/60-pipeline/export-interchange.md`, `knowledge/50-procedural/geometry-nodes.md`, `knowledge/00-foundations/bpy-scripting-core.md`, `knowledge/00-foundations/python-agent-boilerplates.md`, `scripts/boilerplates/run_all_boilerplate_tests.py` |
| W6 | Ladder cost model wrong; blockout/animatic not owner decision points | EEVEE preview profile (in W2) + AGENTS.md rule: animatic/blockout = `request-input` decision point before any render >120 frames (MANUAL, labelled) | controller (W4) | — |

## Frozen interfaces (all workers + docs agree on these)
**Sentinel contract.** Last stdout line of every agent payload is `AGENT_OK <json>` or `AGENT_FAIL <json>`. JSON: `{"step": str, "postconditions": {...}, "error": {"type","message","traceback"}|null}`. Exit codes everywhere: `0` pass · `1` requirements/assert failed · `2` invalid/incomplete input · `3` execution error (uncaught exception). Callers decide by sentinel first, exit code second (Blender exit is unreliable both ways).

**`scripts/agent_runtime.py`** (importable inside Blender, no deps): `run_file(path, argv=None) -> dict` executes a payload with `__file__/__name__` namespace, catches everything, prints sentinel, returns dict; `emit_ok(step, **postconditions)`, `emit_fail(step, exc)`; `load_lib(path)` execs a helper file into a module cached in `sys.modules` keyed by path, re-loaded when sha256 changes (persists across MCP calls); `is_background()`. MCP usage: `import sys; sys.path.insert(0, "<root>/scripts"); import agent_runtime as rt; rt.run_file("<abs>/pass-03.py")`.

**`scripts/headless-run.sh <script.py> [-- args]`**: uses `--factory-startup --disable-autoexec --python-exit-code 3`; errors on missing script (exit 2); prints Blender output; final exit = sentinel-derived when present else Blender exit. Env `BLENDER_BIN` override; `HEADLESS_KEEP_ADDONS=1` to drop `--factory-startup`.

**`scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json> [--parts id,...] [--export-dir <dir>]`**: host-python entry that launches an isolated headless Blender; exit 0/1/2/3; report JSON has `schema_version, inputs{scene_sha256, spec_sha256}, checker{version, blender}, units, parts[{id, object, measured, allowed, checks[{name,status,value,limit,note}], status}], failed[], exclusions[], coverage{checked, unchecked}, timestamp`. Predicate modules in `scripts/production_gate/` (each ≤200 lines): `topology`, `dimensions`, `walls_overhang`, `features_fasteners`, `export_roundtrip`, `report`.

**`specs/build-spec.schema.json`** (v1): `{units:"mm", parts:[{id, object, target_dims_mm:[x,y,z], tol_mm, material, process, orientation_up, min_wall_mm, max_overhang_deg, expected_shells, features:[{type: hole|boss|slot, axis, center_mm, diameter_mm, depth_mm?, tol_mm, fastener?:{standard, size}}]}], fasteners:[{standard, size, length_mm, grade}], load_cases:[...declared only], required_checks:[...], physical_evidence:[...]}`. Missing required fields → gate exit 2 (contract incomplete).

**`agent-verify-lib.py`**: keep function names; `preview_render(path, res=256, samples=16, engine="EEVEE"|"CYCLES")` restores every touched setting in `finally`; `verify_export(path, ...)` runs in a subprocess (`--factory-startup -b`) and never touches the live scene; `scaffold(force=False)` reads and reports existing units/engine/fps, only writes when unset or `force=True`; `checkpoint(tag, root=None)` root from env `AGENT_CHECKPOINT_DIR` else `<repo>/output/checkpoints`.

## Acceptance (controller reran after last edit — results 2026-09-06 00:5x)

| # | Result |
|---|---|
| 1 | raise→3 + AGENT_FAIL w/ traceback; missing→2; clean→0 + AGENT_OK; liar→3 (refused) ✅ |
| 2 | tests/execution 45 OK · tests/production-gate 20 OK · tests/knowledge 28 OK ✅ |
| 3 | positive → 0 + STL manifest; wrongdim/nonmanifold/thinwall/missinghole/unapplied-scale → 1; incomplete spec → 2; heat-set M3 on 6 mm → 1 ✅ |
| 4 | E2 table all Restored=yes (test_verify_lib) ✅ |
| 5 | runner: liar FAIL, handled-error PASS, 30/30 ✅ |
| 6 | mandatory load 65,444 B ≈ 16.4k tok (from 25.8k; target <12k NOT met — 3 KB foundations = 10.5k untouched); catalog current; mirror identical ✅/⚠ |
| 7 | set_engine→CYCLES, enable_cycles_gpu→METAL, edit_armature clean, GLB gate — re-executed from edited Markdown ✅ |

### Original acceptance list
1. `bash scripts/headless-run.sh <raising script>` → nonzero + `AGENT_FAIL` with traceback; missing script → 2; clean script → 0 + `AGENT_OK`.
2. `python3 -m unittest discover -s tests/execution` and `-s tests/production-gate` and `-s tests/knowledge` all pass.
3. Gate: positive fixture → exit 0; each negative fixture (non-manifold, wrong dim, thin wall, missing hole, incomplete spec) → documented nonzero code with reason in report.
4. `preview_render` success and injected failure leave all touched settings equal to before.
5. `python3 scripts/boilerplates/run_all_boilerplate_tests.py` uses sentinel; a module that prints the string then raises → FAIL.
6. Mandatory session-start load measured < 12k tokens (bytes/4) with `python3 scripts/blender-knowledge.py check` = current and `.claude/skills` mirror identical.
7. KB blockers re-executed on 5.2.0: `set_engine('CYCLES')`, `enable_cycles_gpu()` → METAL, `edit_armature` on the KB's own example, glb export gate — all pass.

## Non-goals
No git init, no new MCP server/daemon, no hooks in `~/.claude`, no vendor tools, no mechanical redesign of the arm, no change to `builds/`.

## Rollback
Pre-edit snapshot of every touched tree: `plans/260905-2356-blender-workflow-audit/backup/` (rsync 2026-09-06 00:2x).

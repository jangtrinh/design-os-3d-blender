# Audit 03 — scripts/, scripts/boilerplates/, tests/

Read-only execution audit. 2026-09-06. Blender 5.2.0 LTS (`fbe6228777e7`), macOS. All probes ran in fresh `--factory-startup -b` processes; the live GUI (PID 14172, port 9876) was never contacted. Raw logs: `/private/tmp/claude-501/-Users-jang-Products-Blender/770d4c04-83d4-40e0-b3f9-1fe468bcd0b0/scratchpad/scripts-audit/`.

## Verdict

The code **runs**. The **verdicts it produces cannot be trusted**, and two helpers silently destroy scene state.

1. **FACT — Blender's exit code is unreliable in BOTH directions, and every shell-level helper here depends on it.** Unhandled Python exception → exit **0** (false green). Script that *handles* an operator error and completes → exit **1** (false red). Both reproduced. This one fact invalidates `headless-run.sh` as a gate and makes the boilerplate runner's 30/30 partly theatre.
2. **FACT — `headless-run.sh` returns 0 for a script that does not exist**, with no message at all. An agent can typo a path and be told it succeeded.
3. **FACT — `agent-verify-lib.py` has two scene-destroying helpers.** `preview_render()` restores nothing on the failure path and never restores `cycles.samples` even on success; `verify_export()` wipes the entire scene (`read_homefile(use_empty=True)`) *before* validating its argument. Called in a live GUI scene, it deletes unsaved work.
4. **FACT — 30/30 boilerplates pass in 15s and the asserts are real, but shallow.** 26/30 assert something; 4 assert nothing. Most asserts are polygon/vertex counts (`len(x.data.polygons) > 50`), not dimensional or functional correctness. The runner's PASS is decided by a magic substring, which I defeated with a 3-line module.
5. **FACT — 14 of 19 scripts have zero tests.** Every generic execution helper an agent uses daily (headless-run, socket client, verify-lib, turntable, comparison sheet) is untested. All 5 Blender tests are drone-asset acceptance tests, not helper tests.
6. **FACT — verification is nearly free on this machine**: Blender cold start 0.50s, 256px/16-sample Cycles preview 0.36s, `frame_stats` 0.02s. Any prompt/skill that treats a verify step as expensive is calibrated wrong.

## Boilerplate run table

`python3 scripts/boilerplates/run_all_boilerplate_tests.py` → **exit 0, 30/30 PASS, 14.99s wall** (independently re-timed: 14.9s, identical results). Runner docstring says "ALL 21"; `knowledge/00-foundations/python-agent-boilerplates.md:7` says "26 modules"; actual glob finds **30**. Three conflicting counts.

Classification: **A** = asserts real postconditions · **B** = asserts trivia (count > n) · **C** = prints only, asserts nothing.

| Module | s | rc | Class | What the assert actually proves |
|---|---|---|---|---|
| bp_core.py | 0.49 | 0 | **C** | nothing — creates a collection + empty mesh, prints |
| bp_materials_pbr.py | 0.48 | 0 | **C** | nothing |
| bp_render_camera.py | 0.51 | 0 | **C** | nothing |
| bp_rigging.py | 0.50 | 0 | **C** | nothing |
| bp_animation.py | 0.48 | 0 | **A** | fcurve evaluates to π at mid-frame (±0.1) |
| bp_bmesh_cad.py | 0.51 | 0 | **A** | plate is watertight |
| bp_cad_robotics.py | 0.48 | 0 | **A** | volume 0.001 m³ ±1e-6, mass 1.25 kg ±1e-3 |
| bp_physics.py | 0.49 | 0 | **A** | body's z decreased under gravity |
| bp_geonodes.py | 0.51 | 0 | **B** | evaluated verts > 0 |
| cad_mechanics/bp_assembly_collision_audit.py | 0.51 | 0 | **A** | smootherstep endpoints, path peak z=0.120, clash volume 2000 ±5% |
| cad_mechanics/bp_fasteners_iso.py | 0.49 | 0 | **A** | nut == 24 polys, washer == 128 polys (exact) |
| cad_mechanics/bp_ball_bearing.py | 0.51 | 0 | **A** | == 7×80 faces (exact) |
| cad_mechanics/bp_springs.py | 0.50 | 0 | **A/B** | disc == 4×36 exact; spring > 500 polys |
| cad_mechanics/bp_cable_dragchain.py | 0.49 | 0 | **B** | ≥40 verts, ≥30 polys, chain == 14 objects |
| cad_mechanics/bp_connectors_extended.py | 0.48 | 0 | **B** | 5× `verts > 20/50` |
| cad_mechanics/bp_connectors_wiring.py | 0.50 | 0 | **B** | verts > 20; rj45 == 8 verts |
| cad_mechanics/bp_involute_gear.py | 0.48 | 0 | **B** | polys > 100 |
| cad_mechanics/bp_oring_glands.py | 0.48 | 0 | **B** | polys > 100 / > 50 |
| cad_mechanics/bp_shaft_couplings.py | 0.49 | 0 | **B** | verts > 50 ×2 |
| cad_mechanics/bp_flexures.py | 0.56 | 0 | **B** | polys > 10 |
| dfam_3dprint/bp_insert_boss.py | 0.49 | 0 | **B** | verts > 50 ×2 |
| dfam_3dprint/bp_snap_fits.py | 0.49 | 0 | **A** | == 9 polys (exact) |
| dfam_3dprint/bp_teardrop_holes.py | 0.48 | 0 | **B** | polys > 20 |
| geometry_nodes/bp_gn_cables.py | 0.49 | 0 | **B** | verts>0 and faces>0 |
| geometry_nodes/bp_gn_pipe_flange.py | 0.50 | 0 | **B** | verts>0 and faces>0 |
| materials_shading/bp_mat_metals.py | 0.50 | 0 | **B** | node count == 2 |
| materials_shading/bp_mat_thinfilm.py | 0.49 | 0 | **B** | node count == 4 |
| pipeline_render/bp_cam_autoframing.py | 0.49 | 0 | **B** | camera-target distance > 2.0 |
| pipeline_render/bp_export_pipeline.py | 0.54 | 0 | **A** | glTF + STL written AND file exists on disk |
| rigging_kinematics/bp_rig_robot_arm.py | 0.51 | 0 | **A** | == 6 bones (exact) |

**Totals: A=11, B=15, C=4.** No module asserts a *dimension* (mm), a fit/clearance, or a rendered result. `bp_teardrop_holes` asserts "more than 20 polygons" — it does not check the hole is teardrop-shaped or self-supporting, which is the module's entire purpose. Same shape of gap for the o-ring, flexure, coupling, boss and connector modules (E7's "parameters must alter intended dimensions/features" is unaddressed).

### The PASS criterion is defeatable (attack)

Runner logic: `rc == 0 and "verified successfully" in stdout`. Since Blender exits 0 on unhandled exceptions, the `rc == 0` clause detects **no Python failure whatsoever** — the entire gate is the magic string. Reproduced against a scratch copy of the runner (`fake_runner.py`):

| Scratch module | Behavior | Runner verdict | Correct verdict |
|---|---|---|---|
| `bp_liar.py` | prints magic string, then `raise RuntimeError` | **PASS** | FAIL |
| `bp_honest_fail.py` | `assert False` before the print | FAIL | FAIL ✓ |
| `bp_handled_op_error.py` | asserts pass, prints string, but handled an operator error earlier | **FAIL** | PASS |

The summary line prints `RESULTS: 1/3 PASSED (100% HEADLESS SAFE)` — "(100% HEADLESS SAFE)" is a hardcoded literal emitted regardless of results.

## Backlog reproduction

### E1 — exit-code propagation: **CONFIRMED, and worse than filed**

Probe script deletes `Cube` (partial mutation) then raises.

| Invocation | Exit | Mutation happened? |
|---|---|---|
| `scripts/headless-run.sh raiser.py` (as shipped) | **0** | yes — Cube deleted before the raise |
| `blender --factory-startup -b --python-exit-code 23 --python raiser.py` | **23** | yes |
| `blender --factory-startup -b -P raiser.py` (runner's form) | **0** | yes |

Not in the backlog, found here:

* **False red.** A script that catches an operator `RuntimeError` and completes normally still exits **1** (`falsered.py`: prints `SCRIPT_COMPLETED_OK`, exit 1). Control (clean script) exits 0. So `--python-exit-code` alone does not fix the gate — exit status conflates "operator reported an error" with "script failed".
* **Missing file is silent.** `bash scripts/headless-run.sh /tmp/does-not-exist-xyz.py` → **exit 0**, no error line in stdout or stderr. `set -euo pipefail` is useless because Blender itself succeeds.
* **Non-hermetic.** `headless-run.sh` omits `--factory-startup`, so it loads user prefs and add-ons. Confirmed in the log: `BlenderMCP addon registered`. `blender_mcp` **is** enabled in `~/Library/Application Support/Blender/5.2/config/userpref.blend`, and its `register()` auto-starts the server unconditionally (`blendermcp_auto_start_server` default `True`, addon lines 2828–2841). Only the addon's own background-mode guard ("cannot start server in background mode") prevents a port-9876 collision with the live GUI. Port ownership re-checked after the probe: still PID 14172. **The safety here is the addon's, not the script's.** `.agents/skills/blender-agent-core/references/recipes.md:29` documents the correct invocation and line 32 explicitly states the script lacks the flag — docs are honest, the script contradicts them.

### E1 (socket client) — **CONFIRMED, all four modes, reproduced not just read**

`scripts/blender-socket-client.py`. Tested by copying to scratch, rewriting `HOST, PORT` to `127.0.0.1:49871`, and running against a fake server. **The live GUI was not contacted.**

| Server behavior | Result | Cause (cited) |
|---|---|---|
| immediate EOF after request | `UnboundLocalError` at **line 41** `return resp`, exit 1 | `resp` assigned only inside the `try` at lines 36–39; the `if not chunk: break` at line 32–33 skips it |
| truncated JSON then close | same `UnboundLocalError` at line 41 | same |
| valid `{"status":"error",...}` | **exit 0** | lines 52–53 print the response; no status check anywhere |
| 6 KB valid response | stdout cut to **exactly 4000 bytes**, invalid JSON, exit 0 | line 53 `[:4000]` |

Also: a server that stays open without sending parseable JSON spins the `while True` at lines 30–39 until the 120s socket timeout (line 23), with no progress output.

### E2 — helper state preservation: **CONFIRMED, and `verify_export` is worse than filed**

`scripts/agent-verify-lib.py` exec'd into a factory-startup cube scene pre-set to a distinctive "live" state. Full JSON in `e2.log`.

| Call | Setting | Before | After | Restored? |
|---|---|---|---|---|
| `scaffold()` | `unit_settings.scale_length` | 0.5 | **1.0** | no — silently overwritten |
| `scaffold()` | `render.fps` | 30 | **24** | no |
| `scaffold()` | collections | 1 | **5** | n/a (adds ASSETS/LIGHTS/CAMERAS/HELPERS) |
| `preview_render()` **success** | resolution | 960×720 | 960×720 | yes |
| `preview_render()` **success** | `resolution_percentage` | 50 | 50 | yes |
| `preview_render()` **success** | `render.filepath` | `/tmp/ORIGINAL_OUTPUT_` | same | yes |
| `preview_render()` **success** | `cycles.samples` | 99 | **7** | **no** |
| `preview_render()` **failure** (no camera) | resolution | 960×720 | **64×64** | **no** |
| `preview_render()` **failure** | `resolution_percentage` | 50 | **100** | **no** |
| `preview_render()` **failure** | `render.filepath` | `/tmp/ORIGINAL_OUTPUT_` | **`/tmp/e2_fail.png`** | **no** |
| `preview_render()` **failure** | `cycles.samples` | 99 | **7** | **no** |
| `verify_export("/tmp/missing.glb", …)` | objects | 2 | **0** | **no — scene wiped** |
| `verify_export` | engine | CYCLES | **BLENDER_EEVEE** | no |
| `verify_export` | resolution | 960×720 | **1920×1080** | no |
| `verify_export` | `cycles.samples` | 99 | **4096** | no |

Root causes: `preview_render` (lines 86–96) saves 4 values and restores them by straight-line assignment with **no `try/finally`**, and never includes `cycles.samples` in the saved tuple. `verify_export` (line 139) calls `bpy.ops.wm.read_homefile(use_empty=True)` as its **first statement**, before the path is validated — the wipe is unconditional, and the subsequent import then raised `Please select a file`. `scaffold` (lines 17–30) writes defaults over whatever the scene had, with no save/restore and no warning.

`framing()`, `assert_exists()`, `tri_count()`, `world_bbox()`, `has_material()`, `frame_stats()` are read-only and safe (`frame_stats` loads and removes its image in a `finally`). `checkpoint()` writes with `copy=True` — safe. `import_any()` mutates by design.

### E7 (cheap partial check)

Not re-run. Static evidence consistent with the filing: the connector/vent/saddle/cable adapters' only postconditions are vertex-count floors (table above), so a parameter change that alters no dimension still passes. Not verified: whether the diagnostic script still exits 23.

E3–E6 not in scope of this audit surface; not probed.

## Test coverage gaps

**Ran:** `python3 -m unittest discover -s tests/knowledge -v` → **28 tests, all OK, 0.191s, exit 0.** Genuinely strong contract tests (idempotent publish, stale-source rejection, digest drift, resume-without-overwrite).

**Ran:** all 5 `tests/blender/*.py` against copies of their input `.blend` files in scratch. **All 5 pass, all under 1s.**

| Test | Input blend (copied to scratch) | Exit | Result |
|---|---|---|---|
| native-drone-geometry-test.py | fpv-drone-native.blend | 0 | `TEST_PASS` 80 meshes / 35 432 tris |
| native-drone-presentation-test.py | fpv-drone-native.blend | 0 | `TEST_PASS` hero fill 0.795/0.657 |
| rodin-optimized-geometry-test.py | fpv-drone-rodin-optimized.blend | 0 | `TEST_PASS` 0 non-manifold, 505 626 tris |
| rodin-optimized-presentation-test.py | fpv-drone-rodin-optimized.blend | 0 | `TEST_PASS` 4 cameras framed |
| qremeshify-candidate-test.py | fpv-drone-qremesh-manifold-candidate.blend | 0 | `TEST_PASS` quad ratio 0.9993 |

Caveats on these 5: `qremeshify-candidate-test.py` signals failure only via a bare `assert` (line 61) — under `--python` without `--python-exit-code` that yields **exit 0**, i.e. a failing run of the documented CLAUDE.md gate command would report success. The two `-geometry-` tests do `sys.exit(main())` correctly; the two `-presentation-` tests `raise SystemExit(1)`, also swallowed to exit 0 without the flag. `native-drone-presentation-test.py` still calls the deprecated `use_nodes` (warnings visible in its output), contrary to the project rule.

**Untested surfaces — nothing in `tests/` references these (capped at 7; rest in appendix):**

1. `scripts/headless-run.sh` — the primary execution entry point. No test.
2. `scripts/blender-socket-client.py` — no test; all 4 failure modes reproduced above are live.
3. `scripts/agent-verify-lib.py` — the "sense organs". No test; the state-clobbering above would be caught by one.
4. `scripts/turntable-preview.py` — no test (smoke-ran clean here: 2 frames, exit 0).
5. `scripts/make-comparison-sheet.sh` — no test (smoke-ran clean: valid sheet; and correctly exits **1** on a missing input, the only helper with correct failure propagation).
6. Individual boilerplates — each self-smokes under `__main__` only; nothing external asserts their outputs, so a module can be edited to assert less and the suite stays green.
7. `compute-mesh-inertia.py`, `verify-3dprint-tolerances.py`, the 3 `generate-*.py`, and the 4 `qremeshify-*` scripts — 9 scripts, zero tests. The qremeshify *candidate blend* is tested; the scripts that produce it are not.

Coverage summary: **2 of 19 scripts** (`blender-knowledge.py`, `knowledge-pipeline.py`) have real tests. The knowledge/catalog subsystem is well tested; the Blender execution layer is not tested at all.

## Duplication & structure

### Same function, multiple homes

| Function | Locations | Identical? |
|---|---|---|
| `scaffold` | `scripts/agent-verify-lib.py:17` · `knowledge/00-foundations/agent-workflow-loop.md:101` · `knowledge/60-pipeline/scene-organization.md:121` | **No — 3 incompatible versions.** verify-lib ≡ workflow-loop modulo formatting/quotes. scene-organization takes `(reset=True, unit_scale, fps, res)`, uses collection names `00_CAM/10_SUBJECT/20_SET/30_LIGHTS/40_UTIL/90_EXPORT` instead of `ASSETS/LIGHTS/CAMERAS/HELPERS`, and **defaults to `read_homefile(use_empty=True)` — it wipes the scene.** An agent that greps `scaffold` gets a coin flip between a mild config overwrite and total scene loss. |
| `preview_render` | `agent-verify-lib.py:83` · `agent-workflow-loop.md:178` | Same body, **different defaults**: `path=/tmp/agent_preview.png, res=256` vs `path=/tmp/preview.png, res=128`. Neither has `finally`. |
| `checkpoint` | `agent-verify-lib.py:114` · `agent-workflow-loop.md:214` | Same body, **different roots**: `/Users/jang/Products/Blender/output/checkpoints` vs `/tmp/agent_checkpoints` — a rollback written to one is invisible to a caller using the other. |
| `verify_export` | `agent-verify-lib.py:137` · `agent-workflow-loop.md:224` | Divergent — KB version inlines the importer and lacks `.obj`; both wipe the scene first. |
| `assert_exists`, `tri_count`, `world_bbox`, `has_material`, `framing`, `frame_stats` | `agent-verify-lib.py` · `agent-workflow-loop.md:123–207` | Byte-identical modulo whitespace/quotes. |
| `clean_scene`, `get_or_create_collection`, `create_mesh_object`, `safe_get_socket`, `get_evaluated_mesh`, `dump_node_sockets`, `ensure_mode` | `scripts/boilerplates/bp_core.py` only | **Not duplicated — but never imported.** Zero `import bp_core` / `sys.path` lines anywhere in the repo; the other 29 modules are fully standalone. bp_core is referenced only by docs and catalogs. It is a library nothing links against. |

`scripts/agent-verify-lib.py` is a whole-file duplicate of `knowledge/00-foundations/agent-workflow-loop.md` §4.1–4.7 (diff confirms: identical logic, cosmetic reflow, three default-value divergences). E2's fix must touch both or they drift further. Across the 30 boilerplates there are **no duplicated function names** — that layer is clean.

### Structure

**Files over the 200-line project rule (6):**

| Lines | File |
|---|---|
| 277 | `scripts/boilerplates/cad_mechanics/bp_assembly_collision_audit.py` |
| 256 | `scripts/boilerplates/cad_mechanics/bp_connectors_extended.py` |
| 253 | `scripts/compute-mesh-inertia.py` |
| 227 | `scripts/generate-cycloid-drive.py` |
| 217 | `scripts/boilerplates/cad_mechanics/bp_cable_dragchain.py` |
| 210 | `scripts/boilerplates/cad_mechanics/bp_connectors_wiring.py` |

**Hardcoded absolute paths (5):**

| File:line | Path | Note |
|---|---|---|
| `agent-verify-lib.py:114` | `/Users/jang/Products/Blender/output/checkpoints` | breaks in a worktree |
| `turntable-preview.py:21` | `/Users/jang/Products/Blender/output/turntable` | env-overridable (`TT_OUT`) |
| `make-comparison-sheet.sh:9` | `/Users/jang/Products/Blender/output/comparison-sheet.png` | positional-overridable |
| `run-qremeshify.py:17` | `/Users/jang/Downloads/QRemeshify` | env-overridable; **outside the repo** |
| `qremeshify-headless-adapter.py:27` | `/Users/jang/Downloads/QRemeshify` | same |

`knowledge/00-foundations/python-agent-boilerplates.md` and `knowledge/INDEX.md` link modules as `file:///Users/jang/Products/Blender/...` URLs — machine-specific, not repo-relative.

## Agent ergonomics table

| Script | `--help` | Structured output | Nonzero on failure | Declared write path |
|---|---|---|---|---|
| `headless-run.sh` | **No** — forwards `--help` to Blender as the script arg; prints Blender's 200-line help, exit 0 | No | **No** — exit 0 on unhandled exception, exit 0 on missing script, exit 1 on a *handled* operator error | No — whatever the payload writes |
| `turntable-preview.py` | **No** — `import bpy` at module level, so plain `python3 … --help` is `ModuleNotFoundError` | No — `TURNTABLE_DONE n -> dir` sentinel line | Partial — raises on empty scene; exit code then depends on Blender's flags | **Yes**, `TT_OUT` (default hardcoded); env-configurable |
| `make-comparison-sheet.sh` | **No** — but `${1:?Usage: …}` prints a real usage line and exits nonzero | No — `SHEET_DONE <path>` sentinel | **Yes** — verified exit 1 on a missing input image | **Yes** — positional arg 3, default hardcoded |
| `agent-verify-lib.py` | n/a (exec'd, not a CLI) | Returns dicts; prints `AGENT_LIB_OK bpy=(…)` on load | Raises (`assert_exists`, `verify_export`) — but **no `finally`, so failures leave the scene mutated** | Implicit — `preview_render` default `/tmp/agent_preview.png`, `checkpoint` default hardcoded absolute |
| `blender-knowledge.py` | **Yes** — argparse, subcommands, bounded/positive validators | **Yes** — JSON on stdout, JSON error object on stderr | **Yes** — `sys.exit(2)`; verified: bad path → `{"status":"error",…}` exit 2 | **Yes** — atomic `os.replace` into `root/OUTPUT` |
| `blender-socket-client.py` | Docstring only, no flag | JSON, **truncated at 4000 bytes** | **No** — exit 0 on `{"status":"error"}`; `UnboundLocalError` on EOF | n/a |

Only `blender-knowledge.py` meets all four. Only `make-comparison-sheet.sh` reliably fails loudly. Of 19 scripts: 5 use argparse, 0 have the exec bit except the 2 shell scripts, 8 emit JSON.

## Timings

| Measurement | Value |
|---|---|
| Blender cold start, `--factory-startup -b`, trivial script | **0.50 / 0.53 / 0.50 s** |
| Blender cold start, no `--factory-startup` (headless-run.sh path, loads MCP addon) | 0.48 / 0.48 / 0.50 s — **no measurable penalty** |
| Full boilerplate suite, 30 modules | **14.99 s** (0.48–0.56 s each) |
| `preview_render(res=256, samples=16)` Cycles, default cube scene | **0.36 s** |
| `frame_stats()` on that 256px PNG | **0.02 s** |
| Whole render-and-judge cycle in one process | **~0.9 s wall** including start |
| `turntable-preview.py`, 2 frames @128px/8 samples | < 1 s |
| `tests/knowledge` (28 tests) | 0.191 s |
| Each `tests/blender/*.py` on its blend | 0–1 s |

Cost-per-verify-step implication: a numeric assert costs ~0.5s (a process start) and a *rendered* gate costs ~0.9s. The gap between the "cheap" and "expensive" rungs of the verify ladder is ~0.4s on this hardware — the ladder's ordering is justified by *information value*, not by cost.

## Not verified

* **E3, E4, E5, E6** — not probed; outside this surface.
* **E7 diagnostic exit-23 behavior** — not re-run; only the static assert-quality claim was checked.
* Whether the 4 zero-assert modules (`bp_core`, `bp_materials_pbr`, `bp_render_camera`, `bp_rigging`) produce *correct* output — only that they do not crash.
* Whether `bp_*` module **content** is standards-correct (ISO 4762, gear involute geometry, o-ring gland dims). I checked what they assert, not whether the numbers are right.
* Live-GUI behavior of any helper. Every probe was headless. The `preview_render`/`verify_export`/`scaffold` clobbering is therefore proven in a headless scene and **inferred** (high confidence — same code path) for the GUI.
* `blender-socket-client.py` against the real addon. Tested against a fake server on port 49871 only; the addon's actual framing/partial-write behavior is unconfirmed.
* `qremeshify-*` scripts — not executed (would need the external `/Users/jang/Downloads/QRemeshify` dylibs; out of scope for a read-only audit).
* `compute-mesh-inertia.py`, `verify-3dprint-tolerances.py`, the 3 `generate-*.py` — read for ergonomics, **not executed**.
* Whether `--python-exit-code N` also suppresses the false-red case. I confirmed it fixes the false green (exit 23); I did **not** test whether a handled-operator-error script under that flag exits 0 or N.

## Unresolved questions

1. Should `headless-run.sh` add `--factory-startup --disable-autoexec --python-exit-code 23` per `recipes.md:29`? That changes behavior for any caller relying on user add-ons — and given the false-red finding, exit code alone still will not be a sound gate. A stdout sentinel contract (`AGENT_OK <json>` / `AGENT_FAIL <json>`) parsed by the caller may be the only reliable signal. Which one is intended?
2. Is `bp_core.py` meant to be importable? Nothing imports it, and Blender's `-P` gives no package context. If yes, the 29 other modules need a `sys.path` bootstrap; if no, it should be documented as a copy-paste reference, not a "core library".
3. Three `scaffold()` definitions with different collection schemes, one destructive by default. Which is canonical, and should the other two be renamed?
4. `agent-verify-lib.py` vs `knowledge/00-foundations/agent-workflow-loop.md` §4 — which is the source of truth? A fix applied to one and not the other is the likeliest way E2 comes back.
5. The vertex/polygon-count asserts (15 of 30 modules) will pass any mesh of roughly the right size. Is dimensional assertion (bore Ø, wall thickness, clearance) in scope for E7, or is topology-only acceptance intentional?
6. `qremeshify-candidate-test.py` fails only via a bare `assert`, so the CLAUDE.md-documented gate command reports exit 0 on failure. Deliberate (output is parsed) or a defect?

## Appendix — untested surfaces beyond the top 7

`compute-mesh-inertia.py` · `verify-3dprint-tolerances.py` · `generate-cycloid-drive.py` · `generate-procedural-rig.py` · `generate-procedural-geonodes.py` · `prepare-qremeshify-input.py` · `qremeshify-headless-adapter.py` · `render-qremeshify-candidate.py` · `run-qremeshify.py` — all zero test references. `knowledge-catalog.py`, `knowledge-query.py`, `knowledge-topics.py`, `knowledge-playbook.py` are exercised indirectly through `blender-knowledge.py`/`knowledge-pipeline.py` in `tests/knowledge`.

## Appendix — probe artifacts

`boilerplate-run.log` · `timed.json` (per-module rc/sec/traceback) · `e1-a/b/c.log` (exit-code matrix) · `falsered.log` (false-red proof) · `e2.log` (before/after state JSON) · `socket_copy.py` + `fakeserver.py` (4 socket modes) · `fake_runner.py` + `fakebp/` (PASS-criterion attack) · `tt/`, `sheet.png` (turntable + sheet smoke) — all under `/private/tmp/claude-501/-Users-jang-Products-Blender/770d4c04-83d4-40e0-b3f9-1fe468bcd0b0/scratchpad/scripts-audit/`.

# Audit synthesis — Blender AI orchestration (2026-09-06)

Controller: Claude (blender-9e). Inputs: 4 read-only auditors (opus), 1 web researcher, Codex builder Astra (session `01a07092`), controller probes. Goal set by Jang mid-audit: **production-level outputs — printable, dimension-correct, standards-correct.**

## Verdict (3 lines)
1. Project's knowledge layer is strong (KB facts 62/67 verified on 5.2.0; catalog tooling well tested). Its **execution and verification layers cannot be trusted**: exit codes lie both ways, helpers wipe/clobber state, PASS is a magic string, no gate binds results to inputs, and nothing enforces the loop.
2. The expensive failures are not bpy mistakes. They are **false green** (PASS predicate narrower than acceptance) and **commit-before-contract** (spec arrives after detailing). ≈8,400 frames discarded; every full rebuild traces to a late spec; the owner caught the last 2 defects after internal PASS.
3. The entry layer (`CLAUDE.md`≡`AGENTS.md`) was the stalest artifact: dead skill names inside the mandatory loop, ~26k-token mandatory load, no precedence rule, failure protocol aimed at failures that never occurred in the record.

## Ranked findings (severity · source · evidence)
| # | Finding | Src |
|---|---|---|
| 1 | No checkable production contract; print/fit predicates exist only as per-build one-liners (`audit-meshes.py`, `verify-fit-coupon.py`, `export-prototype-parts.py`) and a KB function never promoted to a tool | 04, Astra, controller |
| 2 | `headless-run.sh` exit 0 on exception and on missing file; Blender exit 1 on *handled* operator error (false red); runner PASS = substring; `qremeshify-candidate-test.py` bare assert → exit 0 | 03 |
| 3 | MCP `execute_code`: fresh namespace per call, exception → `str(e)` only (traceback lost), `get_scene_info` capped at 10 objects; upstream 31 commits since 1.6.0 still do not return tracebacks | controller |
| 4 | `agent-verify-lib.py`: `preview_render` restores nothing on failure, never `cycles.samples`; `verify_export` wipes the scene before validating input; 3 incompatible `scaffold()` (one destructive by default); lib duplicates KB §4 with divergent defaults | 03 |
| 5 | KB helpers fail on 5.2.0: `set_engine` raises (gates on static enum), `enable_cycles_gpu` → CPU silently on Metal, `edit_armature` double-link, glb size gate rejects valid export; 6 GN socket idnames rejected; headless `IMAGE_EDITOR` claim false | 02 |
| 6 | Verification shape: gates check final state; owner/physics judge process (paths, rhythm, proportions, load). Blockout/animatic existed as artifacts but not as owner decision points; retro rule did not bind within 90 min | 04 |
| 7 | Entry layer: `blender-bpy-core`/`blender-materials-shading` dead; binding rule 2 mandated screenshot per op (inverting ladder); 25.8k-token load, 12% narrative; no precedence; 81/83 lines hand-duplicated across CLAUDE/AGENTS | 01 |
| 8 | Ladder cost model wrong: verify cycle ≈0.9 s; EEVEE renders headless on macOS 5.2.0 in 2.1 s (docs said impossible; web research repeated the stale claim) | 03, controller |
| 9 | 14/19 scripts untested; all Blender tests are drone-asset acceptance; only `blender-knowledge.py` meets help/JSON/exit/write-path ergonomics | 03 |
| 10 | Retrieval: `loads_with` one hop = 39–51k tokens, 24 mutual cycles; §5 failure tables at 79–88% file depth; boilerplate counts 30/26/17 across three hand lists | 02 |

## What the record says "better" means to the owner (verbatim signals)
"đây là bản thiết kế chuẩn để có thể in 3D và hoạt động chứ không phải làm demo cho vui" · "Ốc và vít thì phải âm vừa vặn vào thân" · "follow 100%" · "Dừng cái video đi, nó chưa đúng ý của tôi" · "đã tự tin bắt đầu task chưa?" — direction/scope corrections 11×, defect catches 2× (both after internal PASS).

## Decisions taken (controller)
- Program of 6 workstreams (`plan.md`): W1 execution truth (sentinel + runtime module + headless-run + socket client), W2 verify-lib, W3 spec schema + production gate, W4 entry layer + precedence + load cut, W5 KB helper fixes + runner, W6 EEVEE preview + owner decision points (MANUAL, labelled).
- Single canonical operational file `AGENTS.md`; `CLAUDE.md` imports it. Precedence sentence added. `knowledge/INDEX.md` demoted to on-demand.
- Success is decided by the last-line sentinel, never by Blender exit code or transport text.
- No git init, no new daemon/MCP server, no vendor tools, no mechanical redesign (Astra: tooling cannot create missing torque/thermal evidence; arm stays BLOCKED).
- Rejected from research: 3D-Agent/BlenderXAlpha (vendor generation), pyright+fake-bpy 5.1 stubs as a gate (advisory only; runtime introspection stays authoritative), VLM harness build-out (defer; adopt the "state expectation before looking" rule which BlenderGym's priming finding supports).

## Not verified by the controller
Auditor claims were spot-checked by rerunning: catalog check, knowledge tests, EEVEE probe, MCP scene probe, addon source read. Not independently rerun: boilerplate suite, socket fake-server modes, KB verbatim blocks (rerun happens in acceptance after W5).

## Unresolved (for Jang)
1. Owner decision points (blockout/animatic) remain MANUAL — do you want a hard stop mechanism (e.g. render scripts refuse > N frames without an `--approved-animatic` path)?
2. `builds/` per-build scripts still carry stronger arm-specific predicates; promoting the assembly/clearance sweep (E6) is out of tonight's scope.
3. blender-mcp upstream (31 commits: safe mode, UTF-8 fix, socket serialization) — upgrade with a regression check, or stay on 1.6.0?

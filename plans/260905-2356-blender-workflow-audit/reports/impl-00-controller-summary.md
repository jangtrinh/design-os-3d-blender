# Controller summary — audit → implementation (2026-09-06, 23:56 → ~01:00)

Controller: Claude blender-9e. Workers: 4 auditors + 1 researcher + Astra (Codex) for audit; 4 implementers (opus) for W1/W2/W3/W5; controller did W4 + verification. No git repo: pre-edit snapshot in `../backup/` (106 files).

## What now works (verified by controller rerun, not by worker report)
| Area | Before | After |
|---|---|---|
| Headless execution | exception → exit 0; missing script → exit 0 silent | `headless-run.sh` → `agent-run-headless.py` → `agent_runtime.run_file`: last-line `AGENT_OK/AGENT_FAIL {json}` with full traceback; exit 0/1/2/3; refuses success when sentinel and Blender exit disagree |
| MCP execution | fresh namespace, `str(e)` only | `rt.run_file(path)` over MCP returns sentinel + traceback (live-tested on the open GUI scene, read-only payload) |
| Socket client | EOF crash, error→exit 0, 4000-char cut | fixed, tested vs fake server (never bound 9876) |
| Verify helpers | preview clobbers settings; `verify_export` wipes scene; 3 scaffolds | facade + `agent_verify/` package; restore-in-finally; isolated export; report-first scaffold; KB §4 deduped |
| Production gate | none (predicates scattered in builds/) | `specs/build-spec.schema.json` + `production-gate.py` + 6 predicates; report bound to scene+spec sha256; exit 0/1/2/3; STL+manifest; heat-set depth gated against part thickness; 20 tests incl. Ø calibration ±0.05 mm |
| Boilerplate runner | PASS = magic string | PASS = sentinel; liar FAIL / handled-error PASS; `--list` registry; 4 zero-assert modules now assert; `bp_render_camera` picks METAL |
| KB helpers | 4/11 verbatim blocks fail on 5.2 | `set_engine`, `enable_cycles_gpu`, `edit_armature`, GLB gate fixed and re-executed from the Markdown; GN socket list corrected; IMAGE_EDITOR claims fixed (+ `uv_editor_context` retypes an area headless) |
| Entry layer | dead skills, 25.8k tok, no precedence | `AGENTS.md` canonical (precedence, contract-first loop, sentinel, usable/banned MCP tools, real failure map); `CLAUDE.md` = `@AGENTS.md`; `.project-agent.md` rules 1/2 fixed + rules 5/6 added; INDEX on-demand; 16.4k tok |
| Knowledge catalog | — | 7 stale topic reviews + 11 annotations refreshed; playbook republished; `check` current, 263 records; mirror identical |

## Test evidence (rerun after last edit)
`tests/execution` 45 OK (12.5 s) · `tests/production-gate` 20 OK (12 s) · `tests/knowledge` 28 OK · boilerplates 30/30 · headless-run hand cases 3/0/0/2 · gate positive 0 / negatives 1 / incomplete 2.

## Not done / open (honest)
- Mandatory load target <12k tok not met (16.4k): the three KB foundations (10.5k) were left intact on purpose — trimming them is a content decision for Jang.
- E4 (validated frame resume), E5 (engineering blockers at delivery — MANUAL), E6 (assembly-state validator), E7 (adapter qualification) remain open; arm stays manufacture-BLOCKED (Astra: tooling cannot create missing torque/thermal evidence).
- Owner decision points (blockout sheet, animatic before >120-frame render) are MANUAL rules in `AGENTS.md`, not code.
- Socket client verified only against a fake server; first real use should be a throwaway payload.
- Gate: blind-hole depth, non-axis-aligned features, counterbore rows, multi-part scenes implemented but not fixture-covered; overhang % informational unless spec sets `max_overhang_area_pct`; no 3MF (Blender 5.2 has no native exporter).
- Two remaining `enum_items`/`hasattr` traps are now documented, not linted: no static pre-check exists (pyright/fake-bpy absent locally; stubs at 5.1).
- blender-mcp upstream 31 commits behind (safe mode, UTF-8 split fix, socket serialization) — not upgraded.

## How to use tomorrow (first 3 commands)
```bash
python3 scripts/blender-knowledge.py route polymer-functional-print          # reading pack
cp specs/examples/bracket-m3.spec.json builds/<slug>/spec.json && $EDITOR builds/<slug>/spec.json
python3 scripts/production-gate.py --scene builds/<slug>/x.blend --spec builds/<slug>/spec.json --report builds/<slug>/reports/gate-report.json --export-dir builds/<slug>/parts
```

## Reflect (one durable lesson)
Prose rules did not bind even 90 minutes after a retro wrote them; the only things that held in the record were checks with a failing exit. Every rule added tonight that could be code became code with a negative test; the rest is labelled MANUAL so nobody mistakes it for a gate.

## Unresolved questions for Jang
1. Trim the three KB foundation files to reach <12k mandatory tokens, or accept 16.4k?
2. Hard-stop for long renders without an approved animatic (script refuses > N frames without `--approved-animatic`), or keep MANUAL?
3. Upgrade blender-mcp to upstream (safe mode may restrict `execute_code`) with a regression run, or stay on 1.6.0?

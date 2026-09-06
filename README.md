# design-os-3d-blender

![Robot arm assembly demo — 126 s film at 4× speed, every part modelled with bpy](docs/media/robot-arm-assembly-4x.gif)

An AI-agent operating system for **Blender 5.2 LTS**: skills, a verified knowledge base, an execution contract, and a production gate — built so an agent (Claude Code, Codex, or any MCP client) can model, rig, animate, render, and ship **3D-printable, dimension-correct parts** rather than pretty demos.

Everything here is Blender-native: no vendor mesh generation, no downloaded assets, no paid model calls.

## What is inside

| Layer | Path | Purpose |
|---|---|---|
| Operating rules | `AGENTS.md` (canonical, Codex) · `CLAUDE.md` (imports it) · `.project-agent.md` (binding rules) | Contract-first loop, sentinel execution contract, verify ladder, failure map from real sessions |
| Skills | `.agents/skills/blender-agent-core`, `blender-image-to-3d`, `blender-knowledge-workbench` (`.claude/skills` mirrors) | Router + recipes; reference-image reconstruction; catalog-driven reading packs |
| Knowledge base | `knowledge/` (28 domain files, 5.2-verified) + `research/` (engineering syntheses) | Data-API-first bpy patterns, decision tables, failure→fix tables, standards for CAD/print/robotics |
| Execution | `scripts/agent_runtime.py`, `scripts/headless-run.sh`, `scripts/blender-socket-client.py` | Every payload ends with `AGENT_OK {json}` / `AGENT_FAIL {json}` (full traceback), exit `0/1/2/3` — Blender's own exit code is unreliable both ways |
| Verification | `scripts/agent-verify-lib.py` (+ `scripts/agent_verify/`) | Numeric "sense organs": framing, frame stats, state-restoring previews, isolated export re-import |
| Production gate | `specs/build-spec.schema.json`, `scripts/production-gate.py` (+ `scripts/production_gate/`) | Spec → manifold/self-intersection/volume, dimensions ± tolerance, wall/overhang screens, hole diameters vs ISO 273 / ISO 4762 / heat-set tables, STL round-trip + sha256 manifest; report bound to scene+spec hashes |
| Boilerplates | `scripts/boilerplates/` (30 modules) | CAD, gears, fasteners, O-rings, connectors, rigs, geometry nodes, render — each self-tests under the sentinel contract |
| Tests | `tests/execution`, `tests/production-gate`, `tests/knowledge` | 93 tests, all run against a real headless Blender |
| Demo | `builds/robot-arm-*` | The robot-arm session: accepted assembly film, 38-part print kit, engineering reports — with their honest limits |

## Proof: the robot arm is real geometry, not a picture

| | |
|---|---|
| ![Blender window](docs/media/robot-arm-blender-window.png) | ![Six angles](docs/media/robot-arm-turntable-sheet.png) |
| The model open in Blender 5.2.0 — scene `A5-Original-refined`, 671 objects, frame 3031/3031, outliner and properties visible (full-window screenshot, not a viewport crop) | Six-angle Cycles orbit of the assembled parts at the final frame, rendered headless from the shipped `.blend` |
| ![Wireframe](docs/media/robot-arm-wireframe-cycles.png) | ![Print plates](docs/media/robot-arm-print-plates.png) |
| Render tessellation of the 402 arm part meshes (114,723 polygons), Cycles Wireframe node — every edge you see is in the file | 38 fit-prototype parts arranged on five 220×220 mm plates (PETG + TPU), exported as STL/3MF |

![Cycles hero render](docs/media/robot-arm-hero-cycles.png)

*Cycles render of the assembled model at the final frame (1600×1200, 96 samples, Metal). The full-speed MP4 of the assembly film is in `builds/robot-arm-original-refined/video/`.*

**Production gate run on the real print kit (2026-09-06).** The 38 exported STLs were re-imported into a metre-scaled scene and gated against a spec generated from `parts-list.csv` (target dimensions ± 0.1 mm, one shell per part, PETG/TPU):

```
GATE PASS | 38 part(s), 0 failing check(s) | scene=72ab501e47bf spec=d88bc836fb3a | Blender 5.2.0 LTS
836 checks pass · 0 fail · 38 skip (no min_wall_mm declared) · 38 info (overhang reported, not gated)
```

Per part: `non_manifold_edges`, `non_contiguous_edges`, `wire_edges`, `loose_verts`, `zero_area_faces`, `self_intersection_pairs`, `shells`, `signed_volume_positive`, `bbox_dims_mm`, `scale_applied`, `scene_unit_system`, `scene_scale_length`, then STL round-trip repeats of the topology and dimension checks. Report, spec and the reproduction script: `builds/robot-arm-print-assembly/reports/gate-report-260906.json`, `gate-spec-260906.json`, `scripts/gate-import-parts.py`. The report's `exclusions` say what this does **not** prove: load capacity, print success, assembly fit, thermal/creep — those remain physical evidence, and the arm stays unreleased for manufacture.

## Quick start

Requirements: macOS/Linux, Blender 5.2.x, Python 3.10+ on the host (stdlib only). Optional interactive path: [blender-mcp](https://github.com/ahujasid/blender-mcp) addon connected in the Blender GUI.

```bash
export BLENDER_BIN=/Applications/Blender.app/Contents/MacOS/Blender   # adjust
python3 -m unittest discover -s tests/execution                      # execution contract
python3 -m unittest discover -s tests/production-gate                # gate on generated fixtures
python3 scripts/blender-knowledge.py check && python3 scripts/blender-knowledge.py list
```

Run any bpy payload headless and get a machine-readable verdict:

```bash
bash scripts/headless-run.sh my-pass.py          # last line: AGENT_OK {...} or AGENT_FAIL {...}; exit 0/1/2/3
```

Over MCP (Claude/Codex with the blender-mcp addon), execute the same payload with the same contract:

```python
import sys; sys.path.insert(0, "<ROOT>/scripts")
import agent_runtime as rt; rt.run_file("<ROOT>/builds/<slug>/pass-01.py")
```

Gate a part for printing (write the spec **before** detailing):

```bash
cp specs/examples/bracket-m3.spec.json builds/my-part/spec.json   # dims ± tol, holes, fasteners, material, min wall
python3 scripts/production-gate.py --scene builds/my-part/part.blend --spec builds/my-part/spec.json \
        --report builds/my-part/reports/gate-report.json --export-dir builds/my-part/parts
```

Exit `0` = every declared check passed (digital evidence only); `1` = a requirement failed; `2` = spec/scene incomplete; `3` = execution error. `specs/README.md` lists exactly what each check proves and does **not** prove (load, fit after shrinkage, thermal duty stay physical evidence).

## The loop agents follow

```
Contract → Plan (scene graph) → Code (pass files ≤ ~80 lines) → Critic → Execute → Verify → Verdict
```

- **Contract first.** A printable part needs `spec.json`; a reference image needs a fidelity contract. Missing numbers → `request-input`, not a guess. (Every full rebuild in our record traced to a spec that arrived after detailing.)
- **Numbers before pixels.** Assert postconditions, then `framing()` + a 0.2 s preview, then a screenshot with the expectation written down first.
- **Verdict is one of** `continue · refine-spec · refine-code · request-input · stop`. Two failures on the same step change the *class* of approach; three escalate.
- **Success is the sentinel**, never "Code executed successfully".

## Robot-arm demo (`builds/`)

- `robot-arm-original-refined/` — the accepted step-by-step assembly film (3,020 frames, Cycles), source `.blend`, clearance/overlap checks, decoded-frame review reports.
- `robot-arm-print-assembly/` — 38 fit-prototype parts on 5 plates (PETG + TPU) as STL/3MF, parts list, assembly-step CSV, mesh audit and export checks.
- `robot-arm-v2-engineered/` — the task-demo scripts the knowledge catalog cites as execution examples (motion plan, path check, STL export with manifest, delivery audit).

Status is deliberately separated per domain: **media accepted · motion checked at sampled poses · fit prototypes exported · manufacture BLOCKED** (wrist torque margin, retention hardware, thermal duty and loaded trials remain open — see the build READMEs). The frame sequences and draft renders (several GB) are not shipped.

## How this was built

The workflow was audited on 2026-09-05/06 by four independent read-only auditors, a web researcher, and the Codex agent that built the arm; findings and the resulting implementation program are in `plans/260905-2356-blender-workflow-audit/`. The single durable lesson: prose rules did not bind; only checks with a failing exit held, so every rule that could become code became code with a negative test, and the rest is labelled `MANUAL`.

## Notes

- `AGENTS.md`, `.project-agent.md` and the core skill are written in Vietnamese with English identifiers; the knowledge base and code are English.
- `<ROOT>` in docs means the absolute path of this repository on your machine.
- `.agents/skills/img2threejs` is a vendored copy of [img2threejs](https://github.com/img2threejs/img2threejs) (Apache-2.0, license included); only its portable review concepts are routed by the catalog.
- `tests/blender/` are acceptance tests for drone builds that are not included in this repository.

## License

MIT — see `LICENSE`.

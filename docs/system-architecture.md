# Blender AI Orchestration Foundation

Current architecture, verified 2026-09-05; execution/gate layer updated 2026-09-06 (audit program `plans/260905-2356-blender-workflow-audit/`). Operational sequence and capability map: [Blender AI workflow](blender-ai-workflow.md). Historical July research remains in `plans/reports/researcher-260728-0918-*.md`; its tool counts, stars and machine timings are not current runtime facts.

## Three layers

| Layer | Owner | Responsibility |
|---|---|---|
| Intent/workflow | `blender-agent-core`, `blender-image-to-3d`, `blender-knowledge-workbench` | Task contract, routing, staged construction, verdict and claim boundaries |
| Domain knowledge | `knowledge/INDEX.md` + generated catalog → KB/research/portable references | bpy/context/API, modeling, shading, animation, export, precision/robotics |
| Execution/evidence | Existing native scripts and task-specific checkers | Live edits, headless batch, geometry/trajectory checks, renders and actual output verification |

`.agents/skills/blender-agent-core/` owns the current operational router and references; `.claude/skills/blender-agent-core/` mirrors it. The image-to-3d router is present identically in both runtime trees. This is mirrored documentation, not two different pipelines.

Retrieval layer: [knowledge workbench](blender-knowledge-workflows.md) owns source inventory, freshness, search and bounded task packs. It never imports or executes indexed code; core still owns live/batch execution.

## Two complementary execution paths

Interactive: available `blender` MCP tools → addon → live Blender GUI. Direct `scripts/blender-socket-client.py` is the existing fallback if MCP tools are not loaded. Check active file/scene/units before mutation. One declared controller writes a GUI instance; independent reviewers read evidence. This ownership is manual, not an enforced lock.

Batch: Blender CLI → reviewed bpy script with explicit source/input/output → raw renders or reports. Fault probes use fresh `--factory-startup` processes and never the user's current scene. Keep external process parallelism separate from bpy main-thread mutation. `scripts/headless-run.sh` runs every payload through `scripts/agent_runtime.py` (namespace, traceback JSON, last-line `AGENT_OK`/`AGENT_FAIL` sentinel, exit 0/1/2/3); it is still not a sandbox or supervisor. Over MCP the same module is used via `rt.run_file(...)` because the addon returns only `str(e)` on error and a fresh namespace per call.

Installed CLI: Blender **5.2.0 LTS**, build `fbe6228777e7`, verified with `--version`. Successful raw render logs and final media checks establish the current task path. Runtime capabilities are inspected when used; do not hard-code a stale MCP tool count or infer connection from addon installation alone.

## Native asset and reference path

User reference/spec → measured native blockout → editable separated parts → form/detail/materials → numeric checks → camera-matched comparison and multi-angle review. Unseen surfaces remain explicit inference. New vendor meshes, hosted generation/retrieval and paid-credit outputs are excluded by `.project-agent.md`.

An already-local scaffold is eligible only when explicitly selected by the user. Copy it into a self-contained native rebuild, remove vendor links/material dependencies, retain provenance and make no further service calls. Optional QRemeshify remains hash/quarantine/input/topology/visual gated; the [local retopology record](../.brv/context-tree/features/blender-ai-orchestration-foundation/qremeshify-local-retopology-gate.md) owns its evidence and fallback. It is not a fidelity generator.

## Render and acceptance

Use purpose-selected numeric checks, then visible previews for the questions numbers cannot answer. Animation requires a semantic/motion preview as well as extreme poses. Raw image sequences decouple Blender rendering from captions, formatting and encoding. A working render profile is a measured scene-specific choice; neither Metal nor any fixed sample count is universal acceptance.

Actual final task film: 960×720, 24 fps, 720 frames, 30 seconds, six Cycles samples with denoising and no overlays. [Video check](../builds/robot-arm-v2-engineered/reports/task-video-check.json) records decode and sampled visual review. Settings describe this artifact, not a default quality guarantee.

Media, motion, sampled surface contact, fit-prototype and manufacturing results stay separate. Geometry changes invalidate affected older evidence. The arm's 250 g multi-minute requirement remains blocked for manufacture despite successful animation; see the [build README](../builds/robot-arm-v2-engineered/README.md).

## Production contract and gate

`specs/build-spec.schema.json` declares parts, target dimensions ± tolerance, features (holes/boss) with fastener standards, material/process/orientation, wall/overhang limits, declared load cases and required physical evidence. `scripts/production-gate.py --scene --spec --report [--export-dir]` runs `scripts/production_gate/` predicates (topology, dimensions, walls/overhang screens, feature diameters vs ISO 273 / ISO 4762 / heat-set tables, STL round-trip + sha256 manifest) in an isolated Blender process and binds the report to scene+spec hashes. A pass is digital evidence only; `exclusions` and `coverage.unchecked` list what remains physical.

## Current gaps

[Backlog E1–E7](blender-workflow-improvement-backlog.md): E1 and E2 implemented, E3 partial (print parts only), E4–E7 open. Owner decision points (blockout sheet, animatic before long renders) remain MANUAL rules in `AGENTS.md`.

Useful task-specific scripts already exist: motion plans, contact library, payload registration, framing and rebuild checks. Their stronger predicates should be preserved. A generic helper import is not proof of correctness; new common code earns adoption through equivalent real-data and negative-case checks.

## State and next entry point

Live construction, native rig/task animation, separate exploded assembly and encoded output have been exercised. General restart-safe execution, automated stale-evidence rejection and manufacturing release are not complete. Future sessions start at the local BRV manifest's newest relevant node, then the current workflow; historical GUI paths and old roadmap labels are not current state.

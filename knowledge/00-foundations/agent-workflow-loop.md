---
name: agent-workflow-loop
domain: foundations
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: The execute-verify-refine loop an agent runs over blender-mcp — how to plan, how to prove a step worked, and when to stop and hand off.
loads_with: [bpy-scripting-core, blender-version-matrix, product-viz-and-shots]
tags: [workflow, verification, feedback-loop, mcp, agent-design, self-critique]
id: agent-workflow-loop
title: "Agent Workflow Loop"
when: [bpy-agent-loop, verify-before-render, framing-check, checkpoint-before-destructive, retry-discipline]
trust_tier: community_reference
sources_checked: 2026-10-13
---
# Agent Workflow Loop

## Purpose

Define the execute-verify-refine loop an agent runs over blender-mcp or headless: small steps, a numeric assertion per step, cheap renders before costly ones, and a hard stop when retrying the same idea.

## When to Use / When NOT

- ALLOWED: planning how to drive Blender through a keyhole (MCP or `scripts/headless-run.sh`) and deciding which instrument proves each step
- ALLOWED: a render or export looks wrong and the failing step is unknown
- NOT ALLOWED: how to write the bpy payload itself — use `bpy-scripting-core` instead
- NOT ALLOWED: which API names exist on 5.2 — use `blender-version-matrix` instead
- NOT ALLOWED: camera/render-review math for hero shots — use `product-viz-and-shots` instead
- NOT ALLOWED: formal numeric contracts of the helpers — use `native-api-contracts` instead

## Core Knowledge Content


### 1. Mental model

An agent driving Blender is working blind through a keyhole. It sends Python and
gets back stdout; it asks for a screenshot and gets back one image. Everything else
about the scene — whether the normals are flipped, whether the material actually
bound, whether the animation is on the right slot — is invisible unless the agent
deliberately measures it.

That asymmetry sets the whole design. The failure that costs the most is not a
traceback; a traceback is *good news*, it arrives immediately and points at a line. <!-- ease:source UNVERIFIED reason="design opinion of the module author" -->
The expensive failure is the **silent** one: an operator returned `{'CANCELLED'}`,
a texture bound to the wrong colour space, an FBX exported with the wrong axis. The
agent proceeds happily for six more steps and only discovers the problem at the
final render, by which point it cannot tell which step broke.

So the loop is: small step → **assert numerically** → occasional visual check →
next step. Numeric assertions are cheap, precise, and machine-readable. Screenshots
are expensive, ambiguous, and necessary — reserve them for things only eyes can
judge (framing, composition, lighting mood, "does this read as a chair").

### 2. Decision first

| Question you need answered | Right instrument |
|---|---|
| Did the object get created / linked? | `assert name in bpy.data.objects` |
| Is the topology valid? | `bmesh` audit → counts (`modeling-topology.md`) |
| Did the material bind, with the right nodes? | walk `mat.node_tree`, assert link count + socket values |
| Is the animation on the right frames? | read fcurve `keyframe_points[i].co` |
| Is the object inside the camera frustum? | `world_to_camera_view()` on bbox corners |
| Is the render non-empty? | render small, load pixels, assert variance > 0 |
| Is the composition good? Does it look right? | **screenshot / render → look at it** |
| Is the mesh printable? | `print_audit()` (`3d-printing.md`) |
| Did the export keep what mattered? | re-import into a fresh scene and assert |

Rule: if a question can be answered by a number, never spend a screenshot on it.

### 3. Rules

R1. Decompose before coding. Produce an explicit plan (scene graph / step list)
    and keep it in context; execute one step per call.
    Why: a 200-line payload that fails at line 140 gives you one traceback and no
    information about lines 1–139.
    Violation: you rerun the whole thing repeatedly, each time changing one guess.

R2. Every step ends with an assertion that would fail if the step silently no-oped. <!-- ease:source S14 anchor="operators return {'CANCELLED'} without raising (probe 3: bake with no valid state)" -->
    Why: `{'CANCELLED'}` and ignored enums produce no traceback.
    Violation: the error surfaces N steps later, attributed to the wrong cause.

R3. Scaffold deterministically at the start: named collections, named objects,
    known units, known engine, known view transform.
    Why: every later lookup and every later judgement depends on these being fixed.
    Violation: `Cube.003`, a scene in centimetres, a render judged under the wrong
    view transform.

R4. Screenshot with intent. Before you look, write down what you expect to see and
    what would falsify it.
    Why: an unprimed VLM look at a render reliably produces "looks good".
    Violation: confirmation bias; you approve a broken frame.

R5. Two failed attempts at the same step ⇒ change **class** of approach, not <!-- ease:source UNVERIFIED reason="'dominant failure mode' is not stated in the MAST abstract (arXiv 2503.13657); only that failure patterns exist" -->
    parameters. Three ⇒ report to the human.
    Why: repeated identical retries is the dominant multi-agent failure mode.
    Violation: burning the budget on the same wrong hypothesis.

R6. Render cheap first. Preview at low samples / low resolution; only go to final <!-- ease:source UNVERIFIED reason="timing figures (seconds vs minutes) are not measured here" -->
    quality after the preview passes.
    Why: a Cycles frame costs minutes; a 128px 16-sample preview costs seconds and
    catches most errors (nothing in frame, black, wrong material).
    Violation: you spend ten minutes rendering a frame with the camera inside a wall.

R7. Save `.blend` checkpoints at milestones.
    Why: it is the only rollback you have; a bad boolean or applied modifier is
    otherwise unrecoverable.
    Violation: an irreversible destructive edit forces a full rebuild.

R8. Know the hand-off boundary and say so early.
    Why: some work (weight-painting polish, facial rigging, art direction on a
    hero frame) is not reliably verifiable through this keyhole.
    Violation: hours spent producing something the human has to redo.

### 4. bpy patterns

These helpers have exactly one implementation: `scripts/agent-verify-lib.py` <!-- ease:source S1 anchor="facade over scripts/agent_verify/" -->
(exec-able facade) over the `scripts/agent_verify/` package. Load it — never
paste a copy into a payload. Pasted copies are how `preview_render` came to
leave `cycles.samples` clobbered and how `verify_export` came to wipe scenes.

```python
# MCP execute_blender_code, or any inline bpy payload
exec(open("<repo>/scripts/agent-verify-lib.py").read())

# inside a headless run that already has the runtime
import agent_runtime as rt
rt.load_lib("<repo>/scripts/agent-verify-lib.py")
```

Loading prints `AGENT_LIB_OK bpy=(5, 2, 0) lib_sha=<8 hex>`. No `AGENT_LIB_OK` <!-- ease:source S1 anchor="line 130 print("AGENT_LIB_OK bpy=%s lib_sha=%s")" -->
line means nothing below is defined.

#### 4.1 The surface

Safety class is the contract: **read-only** touches nothing · **restoring**
saves and restores every setting it writes, on success *and* on failure ·
**isolated** does its work in a separate headless Blender · **mutating**
changes the live scene and says so.

| Function | Purpose | Safety class |
|---|---|---|
| `assert_exists(name)` | object present, returns it | read-only |
| `tri_count(obj)` | evaluated (modifier-applied) triangle count | read-only |
| `world_bbox(obj)` | bounds of evaluated mesh vertices with evaluated world transform | read-only |
| `has_material(obj, must_have_nodes=True)` | material assigned and wired | read-only |
| `framing(obj, cam=None, scene=None)` | `in_frame` including depth; `in_image` / `in_front` / `within_clip` / `fill_u` / `fill_v` | read-only |
| `frame_stats(path)` | `mean` / `stdev` / `black` / `blown` of a rendered PNG | read-only |
| `preview_render(path=None, res=256, samples=16, engine="EEVEE")` | cheap render gate; default path `$AGENT_PREVIEW_DIR` else `<repo>/output/previews/` | restoring |
| `verify_export(path, expect_objects, expect_min_tris)` | re-import check in a fresh `--factory-startup -b` process | isolated |
| `scaffold(force=False, unit_scale=1.0, engine="CYCLES", fps=24)` | reports `{setting: {before, after, changed}}`; writes only a setting still at its factory default, or with `force=True`; never deletes | mutating (opt-in) |
| `checkpoint(tag, root=None)` | `.blend` copy; root `$AGENT_CHECKPOINT_DIR` else `<repo>/output/checkpoints` | mutating (writes a file) |
| `import_any(path)` | version-branched import **into the current scene** | mutating |
<!-- ease:source S5 anchor="def scaffold line 26; def checkpoint(tag, root=None) line 59" -->
<!-- ease:source S4 anchor="def verify_export line 49; import_any line 43" -->
<!-- ease:source S3 anchor="def preview_render(path=None, res=256, samples=16, engine="EEVEE") line 16; saved settings restored (lines 35-55)" -->
<!-- ease:source S2 anchor="def assert_exists / tri_count / world_bbox / has_material / framing / frame_stats" -->

#### 4.2 Scaffolding an existing scene

`scaffold()` reports before it writes and refuses to overwrite a scene that
already carries a non-default unit scale, fps or engine — those are somebody's
decision, and silently resetting them is how measurements go wrong three steps
later. Read the returned `changed` flags; pass `force=True` only deliberately.
For a scene that must start empty, use `scaffold_new_scene(reset=True)` in
`60-pipeline/scene-organization.md` — that one wipes the file.

#### 4.3 Is it actually in frame? (cheapest possible framing check)

Target `fill_u`/`fill_v` around 0.7–0.85 for a hero product shot, with <!-- ease:source UNVERIFIED reason="heuristic framing target, not sourced" -->
`in_front` true. This one function removes the most common reason an agent
wastes a render: the subject is behind the camera, out of frame, or 1000× the
intended size, so the render is technically perfect and useless. It costs no
render at all. Assert `framing(obj)['in_frame']`: it now includes near/far clip
range as well as positive depth and image bounds. `in_image` is XY-only. The
screen measures evaluated mesh vertices in the active scene and supports
perspective/orthographic cameras; it does not check occlusion, render borders,
un-realized instances, children or visibility flags. Read
[native API contracts](native-api-contracts.md) before adapting this screen.

#### 4.4 Is the render non-empty? (catch black/blank frames without looking)

`preview_render(engine="EEVEE")` then `frame_stats()`. `stdev < 0.01` means a <!-- ease:source S2 anchor="frame_stats docstring: 'stdev < 0.01 => flat frame'" -->
flat frame: nothing in view, or a lighting failure. Check this *before*
spending a screenshot round trip. EEVEE is the default because it renders <!-- ease:source UNVERIFIED reason="'renders headless on this machine' was not re-run in this pass" -->
headless on this machine and needs no sample budget; pass `engine="CYCLES"`
when the thing being judged is Cycles-specific shading or light transport.

#### 4.5 Checkpointing

`checkpoint(tag)` writes a `.blend` copy (`copy=True`, so the session's own <!-- ease:source S5 anchor="checkpoint(tag, root=None) in session.py" -->
filepath is untouched). It is the only rollback that exists — take one before
booleans, applies, and any other destructive step.

#### 4.6 Re-import verification for exports

An export is not verified until it has been re-imported. `verify_export` does
that in its own headless process: export settings fail silently by design, and
the check must not be able to damage the scene it is checking. It raises before
launching anything if the file does not exist.

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Everything "works" but the final render is wrong | no per-step assertions; error introduced many steps earlier | R2 — assert after each step; bisect using checkpoints |
| Screenshot looks fine, human says it is wrong | unprimed visual check; VLM confirmed rather than tested | R4 — state the expectation and the falsifier before looking |
| Render is black | camera inside geometry, no lights, wrong view layer, object hidden in render | `framing()` (§4.3) + `frame_stats()` (§4.4) before any full render |
| Render is a flat grey field | object out of frame or scaled 1000× | `framing()` — check `fill_u`/`fill_v` and `in_front` |
| Same error three times running | retrying the same hypothesis with different numbers | R5 — change approach class, then escalate |
| Agent "fixed" the object but the render did not change | edited a duplicate (`Cube.001`) created by a non-idempotent retry | idempotent create (`bpy-scripting-core.md` §4.9) |
| Export looks right in Blender, broken in the engine | never re-imported | §4.6 |
| Cannot get back to a working state | destructive op with no checkpoint | R7 |
| Long render produced garbage | skipped the preview gate | R6 |
| Agent keeps polishing something unverifiable (weights, facial rig) | past the hand-off boundary | R8 — stop, report, hand to human |
<!-- ease:source S7 anchor="AGENTS.md verify ladder step (2): preview before expensive renders" -->

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Preview render res | 256 px | 256 px | 256 px | 320 px | n/a (use audit, not render) |
| Preview samples (Cycles) | 16 | 16 | 16 | 32 | n/a |
| Screenshot cadence | after asset + after export | after blocking, after bake | after first loop cycle | after framing, after lighting | after boolean ops |
| Primary verification | re-import + tri budget | fcurve key positions + 3-frame render | 3-frame loop render (f, f+n/2, f+n) | `framing()` + `frame_stats()` | `print_audit()` |
| Checkpoint frequency | per asset | per rig stage | per node-tree milestone | per lighting change | before every boolean |
| Hand-off boundary | UV polish on hero assets | weight painting, facial rig, acting | art direction | final colour grade | machine-specific tuning |

### 7. Verification checklist

Run this as the standing loop for every step:

- [ ] step is small enough that one traceback identifies the cause
- [ ] `AGENT_OK` / `AGENT_FAIL` sentinel printed
- [ ] every operator return value asserted `{'FINISHED'}`
- [ ] a numeric assertion exists that would fail if this step silently no-oped
- [ ] before any full render: `framing()` passes, then the cheap gate
      `preview_render(engine="EEVEE")` + `frame_stats()['stdev'] > 0.01`
- [ ] before any screenshot: expectation and falsifier written down first
- [ ] checkpoint saved if the step was destructive
- [ ] on second failure: approach class changed, not just parameters
- [ ] on third failure: stopped and reported, with the traceback and what was tried

### 8. Sources

- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — `execute_blender_code` (the repository now redirects to the name `mcp-for-blender`); `get_viewport_screenshot` is confirmed by this repo's `AGENTS.md`, not by the captured page
- [SceneCraft: An LLM Agent for Synthesizing 3D Scenes as Blender Code](https://arxiv.org/html/2403.01248v1) — scene-graph-then-code decomposition
- [LL3M: Large Language 3D Modelers](https://arxiv.org/abs/2508.08228) — plan / retrieve / write / debug / refine agent split (wording corrected to the paper's abstract) <!-- ease:source S9 anchor="abstract: plan, retrieve, write, debug, refine" -->
- [BlenderAlchemy](https://arxiv.org/pdf/2404.17672) — VLM-in-the-loop iterative program search
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/pdf/2503.13657) — repeated-retry failure mode
- [BlenderGym](https://arxiv.org/html/2504.01786v1) — benchmark for graphics-editing agents
- [bpy_extras.object_utils.world_to_camera_view](https://docs.blender.org/api/current/bpy_extras.object_utils.html)

Internal cross-references: `bpy-scripting-core.md` (how to write the payloads),
`blender-version-matrix.md` (what to branch on), `product-viz-and-shots.md`
(framing math and the render-review loop in full).

## Failure Modes (Mandatory)

- **Final render is wrong but every step 'succeeded'** — cause: no per-step numeric assertion, an operator returned `{'CANCELLED'}` many steps earlier — fix: assert after each step, bisect with `checkpoint()` files
- **Render is black or a flat grey field** — cause: camera inside geometry, no light, object out of frame or scaled 1000x — fix: `framing(obj)['in_frame']` then `frame_stats(path)['stdev'] > 0.01` before any full render (repo helpers `inspect_scene.py`)
- **Agent 'fixed' the object but the render did not change** — cause: edited a duplicate (`Cube.001`) created by a non-idempotent retry — fix: idempotent create-or-get (`bpy-scripting-core`)
- **Export looks right in Blender, broken in the engine** — cause: never re-imported — fix: `verify_export` re-imports in a separate `--factory-startup -b` process
- **Exit code says success while the payload failed (or the reverse)** — cause: Blender's own exit code is unreliable — fix: decide by the last `AGENT_OK` / `AGENT_FAIL` stdout line, which `scripts/headless-run.sh` does

## Sources

- [S1] Repo: scripts/agent-verify-lib.py (facade; prints AGENT_LIB_OK at line 130) — scripts/agent-verify-lib.py — captured 2026-10-13 — sha256 9257d42d4d94fcbae46d55e2ad94fdd94861b4225b6203436cc9ff80e8bc1a64
- [S2] Repo: scripts/agent_verify/inspect_scene.py (assert_exists, tri_count, world_bbox, has_material, framing, frame_stats) — scripts/agent_verify/inspect_scene.py — captured 2026-10-13 — sha256 49a1534b4dfb97169c768ce3c320e1d5d46f516ea935475090f376b92d9284b5
- [S3] Repo: scripts/agent_verify/preview.py (preview_render, restores settings) — scripts/agent_verify/preview.py — captured 2026-10-13 — sha256 c732f799d344f413ef079b33d39decef29ed042b75c7151f18d1038b48f831d6
- [S4] Repo: scripts/agent_verify/export_check.py (import_any, verify_export) — scripts/agent_verify/export_check.py — captured 2026-10-13 — sha256 9448d064d27b71b9d7b85af08156c38978bb97a5ef0149d464a9254cbd65a306
- [S5] Repo: scripts/agent_verify/session.py (scaffold, checkpoint) — scripts/agent_verify/session.py — captured 2026-10-13 — sha256 2da68c49638a851e68356d95993b9bef304d8d8a7a80848164a9bc6e9ce6389e
- [S6] Repo: scripts/headless-run.sh (sentinel decides exit code, lines 93-100) — scripts/headless-run.sh — captured 2026-10-13 — sha256 ed73fd8fc8dfb1abbb0879961692f992d462e3a6d8a6a17b1606ede0e177d449
- [S7] Repo: AGENTS.md (mandatory loop, verify ladder, MCP tool list) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7
- [S8] SceneCraft: An LLM Agent for Synthesizing 3D Scene as Blender Code (arXiv 2403.01248) — https://arxiv.org/abs/2403.01248 (frozen copy: knowledge/_evidence/kb-261013/w1-arxiv-2403.01248.html) — captured 2026-10-13 — sha256 d7cbb8693f7026354d6d29970c37756be1c02a7cb98d32182e73d4a877f87c59
- [S9] LL3M: Large Language 3D Modelers (arXiv 2508.08228) — https://arxiv.org/abs/2508.08228 (frozen copy: knowledge/_evidence/kb-261013/w1-arxiv-2508.08228.html) — captured 2026-10-13 — sha256 882f978c88bf6046f3e2c3eec93f02b70ec16fef940a851feb3a93d86ed66d09
- [S10] BlenderAlchemy: Editing 3D Graphics with Vision-Language Models (arXiv 2404.17672) — https://arxiv.org/abs/2404.17672 (frozen copy: knowledge/_evidence/kb-261013/w1-arxiv-2404.17672.html) — captured 2026-10-13 — sha256 e4cd34c992f1c2d2eed895ccb9fb780a733d881e67c55f6a0a62d2e50e253c79
- [S11] Why Do Multi-Agent LLM Systems Fail? (arXiv 2503.13657) — https://arxiv.org/abs/2503.13657 (frozen copy: knowledge/_evidence/kb-261013/w1-arxiv-2503.13657.html) — captured 2026-10-13 — sha256 106aa092d7531f399a71a6866733cba3ae4470739cdf6996dfc4854b6d8403cd
- [S12] BlenderGym (arXiv 2504.01786) — https://arxiv.org/abs/2504.01786 (frozen copy: knowledge/_evidence/kb-261013/w1-arxiv-2504.01786.html) — captured 2026-10-13 — sha256 d9c86cc915ce8b2b61f8dddfa619f161d1c77c652143be3affa7431b4a9299db
- [S13] ahujasid MCP-for-Blender repository page (execute_blender_code) — https://github.com/ahujasid/blender-mcp (frozen copy: knowledge/_evidence/kb-261013/w1-gh-blender-mcp.html) — captured 2026-10-13 — sha256 66c5fb126857f7bc361a07c6dbe8b48cead816c7513b66b9dd449e52b08bc3c6
- [S14] Runtime probe 3 on Blender 5.2.0 LTS (CANCELLED vs exception semantics, bake poll) — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995

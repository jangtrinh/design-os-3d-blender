---
name: agent-workflow-loop
domain: foundations
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: The execute-verify-refine loop an agent runs over blender-mcp — how to plan, how to prove a step worked, and when to stop and hand off.
loads_with: [bpy-scripting-core, blender-version-matrix, product-viz-and-shots]
tags: [workflow, verification, feedback-loop, mcp, agent-design, self-critique]
---

# Agent Workflow Loop

## 1. Mental model

An agent driving Blender is working blind through a keyhole. It sends Python and
gets back stdout; it asks for a screenshot and gets back one image. Everything else
about the scene — whether the normals are flipped, whether the material actually
bound, whether the animation is on the right slot — is invisible unless the agent
deliberately measures it.

That asymmetry sets the whole design. The failure that costs the most is not a
traceback; a traceback is *good news*, it arrives immediately and points at a line.
The expensive failure is the **silent** one: an operator returned `{'CANCELLED'}`,
a texture bound to the wrong colour space, an FBX exported with the wrong axis. The
agent proceeds happily for six more steps and only discovers the problem at the
final render, by which point it cannot tell which step broke.

So the loop is: small step → **assert numerically** → occasional visual check →
next step. Numeric assertions are cheap, precise, and machine-readable. Screenshots
are expensive, ambiguous, and necessary — reserve them for things only eyes can
judge (framing, composition, lighting mood, "does this read as a chair").

## 2. Decision first

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

## 3. Rules

R1. Decompose before coding. Produce an explicit plan (scene graph / step list)
    and keep it in context; execute one step per call.
    Why: a 200-line payload that fails at line 140 gives you one traceback and no
    information about lines 1–139.
    Violation: you rerun the whole thing repeatedly, each time changing one guess.

R2. Every step ends with an assertion that would fail if the step silently no-oped.
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

R5. Two failed attempts at the same step ⇒ change **class** of approach, not
    parameters. Three ⇒ report to the human.
    Why: repeated identical retries is the dominant multi-agent failure mode.
    Violation: burning the budget on the same wrong hypothesis.

R6. Render cheap first. Preview at low samples / low resolution; only go to final
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

## 4. bpy patterns

These helpers have exactly one implementation: `scripts/agent-verify-lib.py`
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

Loading prints `AGENT_LIB_OK bpy=(5, 2, 0) lib_sha=<8 hex>`. No `AGENT_LIB_OK`
line means nothing below is defined.

### 4.1 The surface

Safety class is the contract: **read-only** touches nothing · **restoring**
saves and restores every setting it writes, on success *and* on failure ·
**isolated** does its work in a separate headless Blender · **mutating**
changes the live scene and says so.

| Function | Purpose | Safety class |
|---|---|---|
| `assert_exists(name)` | object present, returns it | read-only |
| `tri_count(obj)` | evaluated (modifier-applied) triangle count | read-only |
| `world_bbox(obj)` | world-space min/max corners | read-only |
| `has_material(obj, must_have_nodes=True)` | material assigned and wired | read-only |
| `framing(obj, cam=None, scene=None)` | `in_frame` / `in_front` / `fill_u` / `fill_v` | read-only |
| `frame_stats(path)` | `mean` / `stdev` / `black` / `blown` of a rendered PNG | read-only |
| `preview_render(path=None, res=256, samples=16, engine="EEVEE")` | cheap render gate; default path `$AGENT_PREVIEW_DIR` else `<repo>/output/previews/` | restoring |
| `verify_export(path, expect_objects, expect_min_tris)` | re-import check in a fresh `--factory-startup -b` process | isolated |
| `scaffold(force=False, unit_scale=1.0, engine="CYCLES", fps=24)` | reports `{setting: {before, after, changed}}`; writes only a setting still at its factory default, or with `force=True`; never deletes | mutating (opt-in) |
| `checkpoint(tag, root=None)` | `.blend` copy; root `$AGENT_CHECKPOINT_DIR` else `<repo>/output/checkpoints` | mutating (writes a file) |
| `import_any(path)` | version-branched import **into the current scene** | mutating |

### 4.2 Scaffolding an existing scene

`scaffold()` reports before it writes and refuses to overwrite a scene that
already carries a non-default unit scale, fps or engine — those are somebody's
decision, and silently resetting them is how measurements go wrong three steps
later. Read the returned `changed` flags; pass `force=True` only deliberately.
For a scene that must start empty, use `scaffold_new_scene(reset=True)` in
`60-pipeline/scene-organization.md` — that one wipes the file.

### 4.3 Is it actually in frame? (cheapest possible framing check)

Target `fill_u`/`fill_v` around 0.7–0.85 for a hero product shot, with
`in_front` true. This one function removes the most common reason an agent
wastes a render: the subject is behind the camera, out of frame, or 1000× the
intended size, so the render is technically perfect and useless. It costs no
render at all.

### 4.4 Is the render non-empty? (catch black/blank frames without looking)

`preview_render(engine="EEVEE")` then `frame_stats()`. `stdev < 0.01` means a
flat frame: nothing in view, or a lighting failure. Check this *before*
spending a screenshot round trip. EEVEE is the default because it renders
headless on this machine and needs no sample budget; pass `engine="CYCLES"`
when the thing being judged is Cycles-specific shading or light transport.

### 4.5 Checkpointing

`checkpoint(tag)` writes a `.blend` copy (`copy=True`, so the session's own
filepath is untouched). It is the only rollback that exists — take one before
booleans, applies, and any other destructive step.

### 4.6 Re-import verification for exports

An export is not verified until it has been re-imported. `verify_export` does
that in its own headless process: export settings fail silently by design, and
the check must not be able to damage the scene it is checking. It raises before
launching anything if the file does not exist.

## 5. Failure modes

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

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Preview render res | 256 px | 256 px | 256 px | 320 px | n/a (use audit, not render) |
| Preview samples (Cycles) | 16 | 16 | 16 | 32 | n/a |
| Screenshot cadence | after asset + after export | after blocking, after bake | after first loop cycle | after framing, after lighting | after boolean ops |
| Primary verification | re-import + tri budget | fcurve key positions + 3-frame render | 3-frame loop render (f, f+n/2, f+n) | `framing()` + `frame_stats()` | `print_audit()` |
| Checkpoint frequency | per asset | per rig stage | per node-tree milestone | per lighting change | before every boolean |
| Hand-off boundary | UV polish on hero assets | weight painting, facial rig, acting | art direction | final colour grade | machine-specific tuning |

## 7. Verification checklist

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

## 8. Sources

- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — `execute_blender_code`, `get_viewport_screenshot`
- [SceneCraft: An LLM Agent for Synthesizing 3D Scenes as Blender Code](https://arxiv.org/html/2403.01248v1) — scene-graph-then-code decomposition
- [LL3M: Large Language 3D Modelers](https://arxiv.org/abs/2508.08228) — plan / retrieve / write / critic / verify agent split
- [BlenderAlchemy](https://arxiv.org/pdf/2404.17672) — VLM-in-the-loop iterative program search
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/pdf/2503.13657) — repeated-retry failure mode
- [BlenderGym](https://arxiv.org/html/2504.01786v1) — benchmark for graphics-editing agents
- [bpy_extras.object_utils.world_to_camera_view](https://docs.blender.org/api/current/bpy_extras.object_utils.html)

Internal cross-references: `bpy-scripting-core.md` (how to write the payloads),
`blender-version-matrix.md` (what to branch on), `product-viz-and-shots.md`
(framing math and the render-review loop in full).

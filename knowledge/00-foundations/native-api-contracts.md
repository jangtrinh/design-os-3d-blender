---
name: native-api-contracts
domain: foundations
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Evaluated geometry lifetime, assigned Action slots, explicit GN modifier inputs, and numerical failure controls for reusable AI scripts.
loads_with: [bpy-scripting-core, blender-version-matrix, agent-workflow-loop]
tags: [python, depsgraph, mesh, animation, action-slots, geometry-nodes, camera, testing]
id: native-api-contracts
title: "Native API contracts and worked sample"
when: [evaluated-mesh-lifetime, action-slot-keys, gn-modifier-input-binding, camera-depth-screen, helper-reload]
trust_tier: verified
sources_checked: 2026-10-13
---
# Native API contracts and worked sample

## Purpose

Qualify four reusable helper contracts on the installed Blender 5.2.0 LTS runtime (evaluated geometry lifetime, assigned Action slots, Geometry Nodes input binding, camera depth screening) and the live helper reload protocol, each with a falsifier and an executable test.

## When to Use / When NOT

- ALLOWED: measuring evaluated geometry, keying an Action slot, setting a GN modifier input or screening camera depth in a reusable script
- ALLOWED: reloading a helper library in a live Blender session without trusting stale caches
- NOT ALLOWED: wall thickness, clearance or any manufacturing judgement — the contracts here are not manufacturing tests; use `3d-printing` / the production gate instead
- NOT ALLOWED: general bpy rules (wrapper, overrides, headless) — use `bpy-scripting-core` instead
- NOT ALLOWED: API rename history — use `blender-version-matrix` instead

## Core Knowledge Content


Target: the installed Blender 5.2.0 LTS build `fbe6228777e7` observed on <!-- ease:source S1 anchor="AGENT_OK postconditions: blender 5.2.0 LTS, build_hash fbe6228777e7" -->
2026-09-17. These contracts qualify selected helpers on that runtime. They do not
qualify every boilerplate, platform, renderer or manufacturing process.

### 1. Borrow evaluated geometry in a bounded scope

Decision: use evaluated geometry and evaluated transforms for measurement. A
temporary mesh belongs to the evaluated object that created it. The former
`get_evaluated_mesh(obj)` returned only the mesh and lost its cleanup owner; that
unsafe accessor has been removed. Migrate to the context manager:

```python
from boilerplates.bp_core import evaluated_mesh

with evaluated_mesh(obj) as (owner, mesh):
    matrix = owner.matrix_world.copy()
    points = [tuple(matrix @ vertex.co) for vertex in mesh.vertices]
# Only independent numbers/vectors may outlive the block.
```
<!-- ease:source S2 anchor="def evaluated_mesh at line 87; docstring replaces get_evaluated_mesh" -->

The helper clears the same owner's temporary mesh on normal return and when the
consumer raises. Do not change frames, mutate the scene, re-evaluate the graph,
nest another borrow of the same object or retain mesh RNA references inside this
scope. For persistent geometry, explicitly choose Blender's persistent mesh
creation API and separately own its removal.

`agent_verify.world_bbox(obj)` measures the evaluated vertices with the evaluated
world transform, in Blender units. `tri_count(obj)` evaluates modifiers without
applying them. The default graph uses the active view layer and its viewport
settings. Render-only modifiers, un-realized instances, children and hidden
collection scope require a separate declared measurement strategy. These
measurements are not wall-thickness, clearance or manufacturing tests.

Falsifier: a two-cube Array on a scaled object produces the original cube bounds; <!-- ease:source S7 anchor="8 checks pass, rc=0 (executed 2026-10-13)" -->
a Copy Location constraint is missing; an empty mesh returns plausible extents;
or cleanup targets the original object. See the numerical and cleanup controls in
`tests/boilerplates/test_evaluated_mesh_contract.py`.

### 2. Screen camera depth before requesting a render

```python
from agent_verify import framing

screen = framing(obj, camera)
assert screen['in_frame'], screen
```

`in_frame` now requires image XY bounds, positive depth and near/far clip range. <!-- ease:source S3 anchor="lines 80-85: in_image, in_front, within_clip combine into in_frame" -->
`in_image` exposes the former XY-only predicate. `in_front`, `within_clip`,
`fill_u` and `fill_v` make failure diagnosis explicit. Both the geometry and
camera are evaluated in the active scene. Empty geometry and unsupported camera
types raise; perspective and orthographic cameras are supported.

This is a numerical full-frame screen. It does not test occlusion, object render
visibility, transparency, render borders, instances, children, panoramic lenses
or rolling shutter. Passing it does not replace the core visual verify ladder.
Falsifier: a centered object beyond `clip_end` has `in_image=True` and must have <!-- ease:source S1 anchor="sample postcondition camera_screen in_frame true; contract tests rc=0" -->
`in_frame=False`. The native test also changes modifier output and camera shift.

### 3. Own an Action slot and the exact keyed frames

```python
from boilerplates.bp_animation import animate_property_keys

animate_property_keys(obj, 'location', [(1, 0.0), (11, 2.0)],
                      index=0, interpolation='LINEAR')
```
<!-- ease:source S4 anchor="def animate_property_keys line 96; action_slot used at line 25/108" -->

Read the channelbag assigned by `obj.animation_data.action_slot`. Key insertion
must succeed, and the addressed frames must exist in that slot. Interpolation
changes affect only the requested frames. A repeated call updates those frames;
it does not normalize or delete unrelated keys. Two objects deliberately sharing
the same slot still share animation.

The helper supports direct Object attributes and indexed RNA paths. Whole-value
assignment is not an arbitrary nested-path setter. Turntable code authors
endpoints over a declared range; it is not an infinite Cycles F-Modifier. Other
keys on the same curve may change the resulting motion. Driver replacement owns
the exact target path/index and replaces its variables, keys and modifiers.

Falsifier: a neighboring Action slot changes, the quaternion's fourth component <!-- ease:source S8 anchor="5 animation checks pass, rc=0" -->
cannot be keyed, a repeated call adds duplicate keys, or a driver expression
fails to move the evaluated target. See `test_animation_contract.py`.

### 4. Bind a Geometry Nodes parameter to its interface

```python
from boilerplates.bp_geonodes import set_modifier_input

set_modifier_input(modifier, height_socket.identifier, 3.0)
```
<!-- ease:source S5 anchor="def set_modifier_input line 292 uses mod.properties.inputs.<identifier> (line 314); 5.2 notes confirm the API" -->

Keep the identifier from the actual interface socket. A unique display name may
be convenient for interactive code, but a duplicate name is ambiguous. Resolve
the socket and validate its value before writing. A missing tree, missing input,
unsupported socket type or invalid value must fail rather than create a property
that the node tree never reads. Use the installed modifier input API selected by
the helper; do not invent `Socket_N` values or silently fall back on a new API.

Read back the binding, update evaluation, then measure the consequence. The <!-- ease:source S1 anchor="sample postcondition heights [1.0, 3.0]; geonodes test baseline [0.05,0.05,0.08] -> changed [0.1,0.1,0.12]" -->
worked sample changes Height from 1 to 3 and asserts the generated mesh height
changes accordingly. A modifier field existing is not enough evidence. This
does not qualify every socket class, simulation zone, instance or bake workflow.

### 5. Execute the complete sample and discriminating tests

From the project root:

```bash
bash scripts/headless-run.sh scripts/samples/native-api-contract.py
bash scripts/headless-run.sh tests/boilerplates/test_evaluated_mesh_contract.py
bash scripts/headless-run.sh tests/boilerplates/test_animation_contract.py
bash scripts/headless-run.sh tests/boilerplates/test_geonodes_contract.py
```
<!-- ease:source S1 anchor="all four commands rc=0 with AGENT_OK on 2026-10-13" -->

The sample creates native Geometry Nodes geometry, changes and measures a
parameter, keys a motion channel, checks its midpoint, and screens a camera. It
uses a disposable background scene, generates no delivery media and declares
manufacture NOT_REQUESTED. Check actual `AGENT_OK` postconditions and process
status; a nonempty scene or successful transport is not acceptance.

Run qualification in a fresh Blender process after source edits. The catalog
hashes nested runtime modules; that detects disk changes, not already-loaded
Python modules. Runtime research and publication procedure: <!-- ease:source S11 anchor="file exists in repo" -->
`research/260917-blender-api-contracts.md`.

### 6. Reload declared helper dependencies in a live session

`agent_runtime.load_lib(path)` checks the helper's source hash. A helper may also <!-- ease:source S6 anchor="load_lib line 188; __agent_dependency_files__ lines 158-180" -->
declare `__agent_dependency_files__`, an iterable of absolute file paths; cache
reuse requires those exact files to exist and match their recorded hashes. The
verification facade declares its `agent_verify` modules and `bp_core.py` and
reimports those owned modules when invalidated. It also removes their owned
bytecode caches so a same-size rapid edit cannot reuse stale bytecode.

The facade may therefore write/remove generated caches in its own source tree.
It does not purge unrelated modules. Other helper imports must explicitly declare
dependencies and own their reload behavior; this is not automatic discovery of
Python's transitive imports. Existing references held by caller code remain the
caller's responsibility: use the module returned by the current `load_lib` call.

An already-running session that imported the old runtime must reload the runtime
once before using the new protocol, or use a fresh Blender process:

```python
import importlib
import agent_runtime as rt
rt = importlib.reload(rt)  # Upgrade step before a pass, not inside run_file().
lib = rt.load_lib('/absolute/project/scripts/agent-verify-lib.py')
```

Falsifier: change only a declared helper while the facade stays byte-identical, <!-- ease:source S10 anchor="tests.execution.test_agent_runtime: 16 tests OK (executed 2026-10-13, see S1)" -->
then `load_lib` must return code with the new behavior. A missing dependency must
raise rather than return cached success. Tests are in
`tests/execution/test_agent_runtime.py` and the disposable
`tests/execution/fixtures/verify-lib/reload_dependencies.py` fixture.

## Failure Modes (Mandatory)

- **Temporary mesh reference used after the borrow block** — cause: `to_mesh()` data belongs to the evaluated owner and is cleared on exit — fix: keep only copied numbers/vectors; use `evaluated_mesh(obj)` from `bp_core.py`
- **Array/constraint effects missing from a measurement** — cause: reading `obj.data` instead of the evaluated object — fix: measure evaluated vertices with the evaluated world matrix (`agent_verify.world_bbox`)
- **`framing()` says in frame but the render is empty** — cause: the screen ignores occlusion, render borders, instances, children and visibility flags — fix: follow with `preview_render` + `frame_stats` (`agent-workflow-loop`)
- **Keys land on the wrong or a duplicated curve** — cause: ignoring the assigned `animation_data.action_slot` or inserting a key twice — fix: use `animate_property_keys`, which updates existing frames in the assigned slot only
- **`mod['Socket_N']` write has no effect or raises** — cause: 5.2 moved GN modifier inputs to `modifier.properties.inputs.<identifier>` — fix: `set_modifier_input` and read the value back, then measure the consequence
- **Stale helper behaviour after an edit in a live session** — cause: cached module with unchanged facade hash — fix: declare `__agent_dependency_files__` and call `load_lib` again, or use a fresh Blender process

## Sources

- [S1] Executed 2026-10-13: native-api-contract sample + 3 contract tests via scripts/headless-run.sh, all rc=0 with AGENT_OK on 5.2.0 LTS (build fbe6228777e7) — knowledge/_evidence/kb-261013/w1-native-contract-runs.txt — captured 2026-10-13 — sha256 6f3e9b98aa72ebc9c0943ae2c883ad1781feac8ba340a075261bd8ae129d6f1d
- [S2] Repo: scripts/boilerplates/bp_core.py (evaluated_mesh context manager, line 87) — scripts/boilerplates/bp_core.py — captured 2026-10-13 — sha256 7d962bf5f50306ab985443f15f08e9b74b8f0de55d09bb30acacecd04b7efb4d
- [S3] Repo: scripts/agent_verify/inspect_scene.py (framing in_frame/in_image/in_front/within_clip) — scripts/agent_verify/inspect_scene.py — captured 2026-10-13 — sha256 49a1534b4dfb97169c768ce3c320e1d5d46f516ea935475090f376b92d9284b5
- [S4] Repo: scripts/boilerplates/bp_animation.py (animate_property_keys, action_slot) — scripts/boilerplates/bp_animation.py — captured 2026-10-13 — sha256 0fb644479e133e3c5c473bb644cda4247a6dd406c199d9ce28f299be7a792ac5
- [S5] Repo: scripts/boilerplates/bp_geonodes.py (set_modifier_input, properties.inputs) — scripts/boilerplates/bp_geonodes.py — captured 2026-10-13 — sha256 53c196d34ea95ca74ecc0a3f3bd0ccb5d4c1edfc16cf91f7993051bfe1afc70e
- [S6] Repo: scripts/agent_runtime.py (load_lib, __agent_dependency_files__) — scripts/agent_runtime.py — captured 2026-10-13 — sha256 c7e85e03adef537002e0b3d071aa117537f78447ea587352bc146b40e43a5438
- [S7] Repo test: evaluated mesh contract — tests/boilerplates/test_evaluated_mesh_contract.py — captured 2026-10-13 — sha256 ec7b7f7a7a963f0d44ad97d8a39a1377288258362dada2b10a00fcab61602de4
- [S8] Repo test: animation slot contract — tests/boilerplates/test_animation_contract.py — captured 2026-10-13 — sha256 e02f76c220b2be688b594c8dff9b68d19d175643d428926a2fa332fb5770b9e0
- [S9] Repo test: Geometry Nodes input contract — tests/boilerplates/test_geonodes_contract.py — captured 2026-10-13 — sha256 88d134b15c075ec411c30ac4c4a4886ca63db4bdf6edda25eff3ed9eeeb3fb30
- [S10] Repo test: agent_runtime load_lib reload contract — tests/execution/test_agent_runtime.py — captured 2026-10-13 — sha256 6df3ff0c8a896666a2a60c00eba8042c983574d2a41c18dac3943e8d0cf7e12e
- [S11] Repo research note: runtime research and publication procedure — research/260917-blender-api-contracts.md — captured 2026-10-13 — sha256 be10db74fd166a9a2f1ec3ca07f0be0643a338c0ca7ad3d8861e129c05f65bde
- [S12] Blender 5.2 LTS Python API release notes (GN modifier properties) — https://developer.blender.org/docs/release_notes/5.2/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-python.html) — captured 2026-10-13 — sha256 613fac2fa63a96155d40c761571e1a7407c709926ebc2eff96f846343bb1b086

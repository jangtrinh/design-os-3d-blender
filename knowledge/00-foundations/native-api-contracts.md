---
name: native-api-contracts
domain: foundations
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Evaluated geometry lifetime, assigned Action slots, explicit GN modifier inputs, and numerical failure controls for reusable AI scripts.
loads_with: [bpy-scripting-core, blender-version-matrix, agent-workflow-loop]
tags: [python, depsgraph, mesh, animation, action-slots, geometry-nodes, camera, testing]
---

# Native API contracts and worked sample

Target: the installed Blender 5.2.0 LTS build `fbe6228777e7` observed on
2026-09-17. These contracts qualify selected helpers on that runtime. They do not
qualify every boilerplate, platform, renderer or manufacturing process.

## 1. Borrow evaluated geometry in a bounded scope

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

Falsifier: a two-cube Array on a scaled object produces the original cube bounds;
a Copy Location constraint is missing; an empty mesh returns plausible extents;
or cleanup targets the original object. See the numerical and cleanup controls in
`tests/boilerplates/test_evaluated_mesh_contract.py`.

## 2. Screen camera depth before requesting a render

```python
from agent_verify import framing

screen = framing(obj, camera)
assert screen['in_frame'], screen
```

`in_frame` now requires image XY bounds, positive depth and near/far clip range.
`in_image` exposes the former XY-only predicate. `in_front`, `within_clip`,
`fill_u` and `fill_v` make failure diagnosis explicit. Both the geometry and
camera are evaluated in the active scene. Empty geometry and unsupported camera
types raise; perspective and orthographic cameras are supported.

This is a numerical full-frame screen. It does not test occlusion, object render
visibility, transparency, render borders, instances, children, panoramic lenses
or rolling shutter. Passing it does not replace the core visual verify ladder.
Falsifier: a centered object beyond `clip_end` has `in_image=True` and must have
`in_frame=False`. The native test also changes modifier output and camera shift.

## 3. Own an Action slot and the exact keyed frames

```python
from boilerplates.bp_animation import animate_property_keys

animate_property_keys(obj, 'location', [(1, 0.0), (11, 2.0)],
                      index=0, interpolation='LINEAR')
```

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

Falsifier: a neighboring Action slot changes, the quaternion's fourth component
cannot be keyed, a repeated call adds duplicate keys, or a driver expression
fails to move the evaluated target. See `test_animation_contract.py`.

## 4. Bind a Geometry Nodes parameter to its interface

```python
from boilerplates.bp_geonodes import set_modifier_input

set_modifier_input(modifier, height_socket.identifier, 3.0)
```

Keep the identifier from the actual interface socket. A unique display name may
be convenient for interactive code, but a duplicate name is ambiguous. Resolve
the socket and validate its value before writing. A missing tree, missing input,
unsupported socket type or invalid value must fail rather than create a property
that the node tree never reads. Use the installed modifier input API selected by
the helper; do not invent `Socket_N` values or silently fall back on a new API.

Read back the binding, update evaluation, then measure the consequence. The
worked sample changes Height from 1 to 3 and asserts the generated mesh height
changes accordingly. A modifier field existing is not enough evidence. This
does not qualify every socket class, simulation zone, instance or bake workflow.

## 5. Execute the complete sample and discriminating tests

From the project root:

```bash
bash scripts/headless-run.sh scripts/samples/native-api-contract.py
bash scripts/headless-run.sh tests/boilerplates/test_evaluated_mesh_contract.py
bash scripts/headless-run.sh tests/boilerplates/test_animation_contract.py
bash scripts/headless-run.sh tests/boilerplates/test_geonodes_contract.py
```

The sample creates native Geometry Nodes geometry, changes and measures a
parameter, keys a motion channel, checks its midpoint, and screens a camera. It
uses a disposable background scene, generates no delivery media and declares
manufacture NOT_REQUESTED. Check actual `AGENT_OK` postconditions and process
status; a nonempty scene or successful transport is not acceptance.

Run qualification in a fresh Blender process after source edits. The catalog
hashes nested runtime modules; that detects disk changes, not already-loaded
Python modules. Runtime research and publication procedure:
`research/260917-blender-api-contracts.md`.

## 6. Reload declared helper dependencies in a live session

`agent_runtime.load_lib(path)` checks the helper's source hash. A helper may also
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

Falsifier: change only a declared helper while the facade stays byte-identical,
then `load_lib` must return code with the new behavior. A missing dependency must
raise rather than return cached success. Tests are in
`tests/execution/test_agent_runtime.py` and the disposable
`tests/execution/fixtures/verify-lib/reload_dependencies.py` fixture.

---
name: bpy-scripting-core
domain: foundations
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: How to write bpy that actually runs — data API over operators, context overrides, headless reality, introspection instead of recall, and the error taxonomy.
loads_with: [blender-version-matrix, agent-workflow-loop]
tags: [bpy, operators, context, headless, introspection, error-handling, core]
---

# bpy Scripting Core

## 1. Mental model

Blender exposes two parallel APIs. `bpy.data` / `bpy.types` is the **data API**:
plain objects and properties, no hidden state, works anywhere. `bpy.ops` is the
**operator API**: it is the UI's button-press layer, and every operator carries an
implicit dependency on *context* — which object is active, what mode you are in,
which editor the mouse is over. Operators also push undo steps and re-evaluate the
dependency graph on every call, so a loop over 1000 objects that uses operators is
not just fragile, it is roughly two orders of magnitude slower than the data-API
equivalent.

An agent writing code it cannot interactively debug should therefore treat
`bpy.ops` as a last resort with a known cost, not as the default vocabulary. Most
LLM-generated Blender code fails not because the logic is wrong but because it
reached for an operator that needed a context it did not have.

One correction to a widespread belief: **Blender 5.2 running `--background` still
has a window with a real `VIEW_3D` area**, so `temp_override` works headlessly and
many operators run bare. "Headless means no operators" is false.
Measured on 5.2.0 (`--factory-startup -b`, 2026-09-06) the default background window
has exactly four areas: `PROPERTIES`, `OUTLINER`, `DOPESHEET_EDITOR`, `VIEW_3D`.
There is **no `IMAGE_EDITOR` area** — an earlier revision of this file claimed one, and
code that searched for it silently found nothing. Enumerate, never assume:
`[a.type for w in bpy.context.window_manager.windows for a in w.screen.areas]`. A few operators genuinely cannot run (`bpy.ops.uv.stitch` segfaults), and
modal/invoke-only operators never work — but the blanket rule is wrong, and
believing it leads agents to write awkward workarounds for problems they do not have.

## 2. Decision first

```
Need to change something in Blender
│
├─ Is there a data-API property or collection for it?
│   └─ YES → use it. Done. (obj.location, mesh.vertices, modifiers.new, …)
│
├─ Is it a mesh topology edit (extrude, bevel, dissolve, merge)?
│   └─ YES → use bmesh.ops on a bmesh, not bpy.ops.mesh.*
│
├─ Is it evaluated/derived data (modifier result, GN output)?
│   └─ YES → obj.evaluated_get(depsgraph) — never "apply then read"
│
└─ Only an operator exists (unwrap, bake, import/export, nla.bake, rigid body)
    ├─ Set the context explicitly first (active object, mode, selection)
    ├─ Wrap in bpy.context.temp_override(...) if it touches an editor
    ├─ Check the return: {'FINISHED'} vs {'CANCELLED'}  ← CANCELLED is silent
    └─ Prefer a bpy_extras / bpy.utils helper if one exists
        (e.g. bpy_extras.anim_utils.bake_action over bpy.ops.nla.bake)
```

## 3. Rules

R1. Prefer the data API. Reach for `bpy.ops` only when no data-API path exists.
    Why: operators depend on context and undo state; data access does not.
    Violation: `RuntimeError: Operator bpy.ops.X.poll() failed, context is incorrect`.

R2. Always check an operator's return value.
    Why: `{'CANCELLED'}` is not an exception. The script continues and produces a
    wrong scene with no traceback.
    Violation: an empty UV map, an unbaked cache, a render of nothing — discovered
    only at the screenshot stage, many steps later.

R3. Set mode explicitly and restore it. Never assume you are in Object Mode.
    Why: half the API is mode-gated (`armature.edit_bones` needs Edit Mode;
    `mesh.vertices` is stale in Edit Mode until you leave or use bmesh).
    Violation: silent stale data, or `AttributeError` on a collection that exists.

R4. Introspect names; do not recall them.
    Why: socket names, enum identifiers and operator arguments changed across
    4.0/4.1/5.0/5.2 (see `blender-version-matrix.md`).
    Violation: `KeyError`, or a silently ignored enum assignment.

R5. Make every script idempotent — check-then-create, and name everything.
    Why: an agent loop re-runs scripts after failures. Unnamed duplicates
    accumulate (`Cube.001`, `Cube.002`) and later lookups grab the wrong one.
    Violation: the fix works, but on a stale duplicate that is not being rendered.

R6. Never mutate a `bpy.data` collection while iterating it.
    Why: the collection is live; removal invalidates the iterator.
    Violation: crash, or a silently partial pass.

R7. Read evaluated geometry via the depsgraph; never apply modifiers to inspect them.
    Why: applying is destructive and needs an operator; `evaluated_get` is neither.
    Violation: an irreversibly flattened stack you then have to rebuild.

R8. Wrap every `execute_blender_code` payload in a try/except that prints the full
    traceback, and end with a machine-readable status line.
    Why: MCP returns you stdout; an uncaught exception may reach you truncated or
    without the frame you need.
    Violation: you retry blind and burn iterations on the wrong hypothesis.

## 4. bpy patterns

### 4.1 The wrapper every agent payload should use

```python
import bpy, sys, traceback, json

def run():
    # ... the actual work ...
    return {"objects": len(bpy.data.objects)}

try:
    result = run()
    print("AGENT_OK " + json.dumps(result))
except Exception:
    traceback.print_exc(file=sys.stdout)
    print("AGENT_FAIL")
```

A single grep-able status line means you never have to guess whether a step
succeeded from prose output.

### 4.2 Version + capability probe (run once per session)

```python
import bpy
V = bpy.app.version
print("blender", V, "python", sys.version_info[:3])
print("background", bpy.app.background)
print("engine", bpy.context.scene.render.engine)
print("gpu_ok", bool(getattr(bpy.types, "gpu", None)))   # see render-engines.md for gpu.init()
```

### 4.3 Data API instead of the operators agents reach for first

```python
import bpy

# DON'T: bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
# DO:
mesh = bpy.data.meshes.new("HeroMesh")
obj  = bpy.data.objects.new("Hero", mesh)
bpy.context.scene.collection.objects.link(obj)
obj.location = (0.0, 0.0, 0.0)

# DON'T: bpy.ops.object.modifier_add(type='SUBSURF')
# DO:
sub = obj.modifiers.new(name="Subdivision", type='SUBSURF')
sub.levels = 1          # viewport
sub.render_levels = 2   # render

# DON'T: bpy.ops.object.delete()
# DO:
bpy.data.objects.remove(obj, do_unlink=True)

# DON'T: bpy.ops.object.select_all(action='DESELECT')
# DO:
for o in bpy.context.view_layer.objects:
    o.select_set(False)
```

### 4.4 Building mesh data directly

```python
import bpy

verts = [(0,0,0), (1,0,0), (1,1,0), (0,1,0)]
faces = [(0,1,2,3)]
mesh = bpy.data.meshes.new("Quad")
mesh.from_pydata(verts, [], faces)
mesh.update()
mesh.validate(verbose=False)          # always: catches malformed input early
obj = bpy.data.objects.new("Quad", mesh)
bpy.context.scene.collection.objects.link(obj)
```

For topology edits use `bmesh` — it is the data-level equivalent of Edit Mode and
needs no context at all:

```python
import bpy, bmesh

obj = bpy.data.objects["Quad"]
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.inset_region(bm, faces=bm.faces[:], thickness=0.1)
bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
```

### 4.5 Context override — the correct form

```python
import bpy

def find_area(area_type):
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == area_type:
                region = next((r for r in a.regions if r.type == 'WINDOW'), None)
                if region:
                    return w, a, region
    return None, None, None

obj = bpy.data.objects["Hero"]
bpy.context.view_layer.objects.active = obj      # many polls check ONLY this
obj.select_set(True)

win, area, region = find_area('VIEW_3D')
override = {"object": obj, "active_object": obj, "selected_objects": [obj],
            "selected_editable_objects": [obj]}
if area:
    override.update({"window": win, "screen": win.screen,
                     "area": area, "region": region})

with bpy.context.temp_override(**override):
    res = bpy.ops.object.shade_smooth()
assert res == {'FINISHED'}, res      # R2
```

Note: in 5.2 `--background` the areas above **do** exist. Some operators need the
editor's *mode* set too, not just its type — e.g. UV ops need
`area.spaces.active.mode = 'UV'`; setting `area.ui_type` is not sufficient.

### 4.6 Mode switching, safely

```python
import bpy
from contextlib import contextmanager

@contextmanager
def in_mode(obj, mode):
    prev_active = bpy.context.view_layer.objects.active
    prev_mode = obj.mode if obj else 'OBJECT'
    bpy.context.view_layer.objects.active = obj
    if obj.mode != mode:
        bpy.ops.object.mode_set(mode=mode)
    try:
        yield obj
    finally:
        if bpy.context.view_layer.objects.active is obj and obj.mode != prev_mode:
            bpy.ops.object.mode_set(mode=prev_mode)
        bpy.context.view_layer.objects.active = prev_active
```

### 4.7 Reading evaluated (modifier/GN) results without applying anything

```python
import bpy

deps = bpy.context.evaluated_depsgraph_get()
obj_eval = bpy.data.objects["Hero"].evaluated_get(deps)
me = obj_eval.to_mesh()
try:
    me.calc_loop_triangles()
    print("evaluated tris:", len(me.loop_triangles))
finally:
    obj_eval.to_mesh_clear()
```

Caveat: the depsgraph you get in a script is the **viewport** one, so
viewport-vs-render modifier settings (subdivision levels, simplify) apply. See
`optimization-realtime.md` for the render-quality workaround.

### 4.8 Introspection — the antidote to hallucinated names

```python
import bpy

# What arguments does this operator take?
print(sorted(bpy.ops.export_scene.gltf.get_rna_type().properties.keys()))

# What values does this enum accept?
prop = bpy.types.BooleanModifier.bl_rna.properties["solver"]
print([e.identifier for e in prop.enum_items])

# What sockets does this node actually have, in this version?
node = mat.node_tree.nodes["Principled BSDF"]
print([(i, s.name, s.type) for i, s in enumerate(node.inputs)])

# Does this operator's poll pass right now?
print(bpy.ops.object.shade_smooth.poll())

# Is an add-on's operator available?
print(hasattr(bpy.ops.pose, "rigify_generate"))

# What node types exist? (dir(bpy.types) scan is the reliable route;
# GeometryNode.__subclasses__() is unreliable — RNA classes are created lazily)
print([n for n in dir(bpy.types) if n.startswith("GeometryNodeDistribute")])
```

Rule of thumb: **if you are about to type a string literal that Blender defined,
print it instead.** One extra round trip beats three failed ones.

### 4.9 Idempotent creation

```python
def ensure_object(name, mesh_name=None):
    obj = bpy.data.objects.get(name)
    if obj is not None:
        return obj
    me = bpy.data.meshes.new(mesh_name or name)
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def ensure_modifier(obj, name, type_):
    m = obj.modifiers.get(name)
    return m if m and m.type == type_ else obj.modifiers.new(name=name, type=type_)
```

### 4.10 Safe removal while iterating

```python
for obj in list(bpy.data.objects):        # list() snapshots the collection
    if obj.name.startswith("tmp_"):
        bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)   # or bpy.data.orphans_purge()
```

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Operator bpy.ops.X.poll() failed, context is incorrect` | operator's poll needs an active object / mode / editor you did not set | set `view_layer.objects.active`, set mode, wrap in `temp_override` with a real area+region (§4.5); check `bpy.ops.X.poll()` first |
| Script "succeeds" but the scene is unchanged | operator returned `{'CANCELLED'}`, which is not an exception | assert on the return value (R2) |
| `AttributeError` on a collection that should exist | wrong mode (`edit_bones` outside Edit Mode) or wrong version (see version matrix) | check mode; check `bpy.app.version` |
| `KeyError: '<socket name>'` | name changed in 4.0/5.0, or you guessed | introspect `node.inputs` (§4.8) |
| Enum assignment has no effect, no error | invalid identifier string silently rejected | read `prop.enum_items` (§4.8) |
| Mesh edits appear to vanish | edited `mesh.vertices` while in Edit Mode (bmesh owns the data there) | edit via `bmesh`, or leave Edit Mode first |
| Vertex/face counts don't match what renders | read base mesh instead of evaluated | `evaluated_get(depsgraph)` (§4.7) |
| Loop over many objects takes minutes | operator per object (undo push + depsgraph re-eval each time) | rewrite with data API / bmesh |
| Crash or freeze mid-script | modal/invoke-only operator, or a known-bad one (`uv.stitch` segfaults headless) | find the data-API or `bpy_extras` equivalent |
| Object lookups grab the wrong thing after a retry | non-idempotent script created `Cube.001` | check-then-create (§4.9) |
| `RuntimeError` during `bpy.data.*.remove()` in a loop | mutating a live collection while iterating | snapshot with `list()` (§4.10) |
| Driver expressions do nothing in `--background` | script auto-execution disabled | run with `--enable-autoexec`, or avoid drivers in the automated path |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Preferred construction path | `bmesh` / `from_pydata` | data API + operators for rig ops | geometry nodes | data API + imported assets | `bmesh` (needs exact topology control) |
| Acceptable `bpy.ops` use | export, bake, UV | `nla.bake`, `mode_set`, weight ops | none typically | render, import | boolean, print-toolbox checks |
| Idempotency importance | high (rebuilds) | very high (long sessions) | medium | medium | very high (destructive edits) |
| Run mode | `--background` batch | GUI + MCP (visual review) | either | `--background` render | `--background` |
| Undo pressure concern | high (batch loops) | medium | low | low | high |

## 7. Verification checklist

- [ ] `print("AGENT_OK ...")` / `AGENT_FAIL` sentinel present in every payload
- [ ] every `bpy.ops.*` call site has `assert res == {'FINISHED'}` or an equivalent check
- [ ] `bpy.ops.X.poll()` printed before any operator whose context you are unsure of
- [ ] `assert obj.name in bpy.data.objects` after every creation step
- [ ] `assert obj.mode == 'OBJECT'` at the end of any block that changed mode
- [ ] no string literal in the script names a socket/enum/operator argument that
      was not first printed by an introspection call in this session
- [ ] script re-run twice in a row produces an identical `len(bpy.data.objects)`
      (proves idempotency)
- [ ] `len(bpy.data.orphans_purge(do_local_ids=False))` == 0 at end of a clean run

## 8. Sources

- [Blender Python API — Best Practice](https://docs.blender.org/api/current/info_best_practice.html)
- [Blender Python API — Gotchas](https://docs.blender.org/api/current/info_gotcha.html)
- [Using Operators (bpy.ops) — gotchas](https://docs.blender.org/api/current/info_gotchas_operators.html)
- [bpy.context.temp_override](https://docs.blender.org/api/current/bpy.types.Context.html)
- [bmesh module](https://docs.blender.org/api/current/bmesh.html)
- [Dependency graph (bpy.types.Depsgraph)](https://docs.blender.org/api/current/bpy.types.Depsgraph.html)
- [Blender command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)

The headless-context claims in §1 and §4.5 were confirmed empirically on Blender
5.2.0 and 4.5.9 running `--background --factory-startup`, not inferred from docs.

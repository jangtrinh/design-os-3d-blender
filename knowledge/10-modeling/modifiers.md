---
name: modifiers
domain: modeling
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: The modifier stack as an ordered evaluation graph — order rules, data-API configuration, headless application via depsgraph, and boolean solver selection.
loads_with: [modeling-topology, uv-unwrapping, geometry-nodes, export-interchange]
tags: [modifiers, stack-order, boolean, subsurf, mirror, depsgraph, headless, non-destructive]
---

# The Modifier Stack

## 1. Mental model

`obj.modifiers` is an **ordered list**, evaluated top→bottom by the depsgraph, each
stage consuming the mesh produced by the previous one. Nothing is written back to
`obj.data`; the result lives only in the evaluated copy that the depsgraph owns.
That single fact drives everything: order is semantics (Mirror-then-Subsurf welds
the seam, Subsurf-then-Mirror does not), "applying" a modifier is really "copy the
evaluated mesh over the original data", and reading a modified mesh headlessly is
`obj.evaluated_get(depsgraph)` — not an operator. Modifiers operate in **object-local
space**, so every metric parameter (`width`, `thickness`, `merge_threshold`,
`voxel_size`) is in local units and gets rescaled by the object matrix afterwards.
The most common agent failure is reaching for `bpy.ops.object.modifier_add` and
`bpy.ops.object.modifier_apply` when `obj.modifiers.new()` and
`bpy.data.meshes.new_from_object()` do the same job with no context dependency at
all. The second most common is treating `to_mesh()` output as render quality — the
only depsgraph Python can get is the **viewport** one, which uses `levels`, not
`render_levels`, and skips modifiers with `show_viewport = False`.

## 2. Decision first

**Should this be a modifier at all?**

| Situation | Answer |
|---|---|
| Parameter may change later, or is driven by the agent's own search loop | Modifier (non-destructive) |
| Result feeds a UV unwrap, a bake, or an exporter | Apply it (destructive) — most exporters evaluate modifiers, but UV/bake operators read `obj.data` |
| Topology must stay editable by later `bmesh` code | Apply it; `bmesh` reads `obj.data`, not the evaluated mesh |
| Cost is high and the shape is final | Apply it; every viewport redraw re-evaluates the stack |
| You need the same operation on 500 objects | Modifier + `new_from_object` in a loop; never `bpy.ops` per object |

**Canonical order** (top of the list = evaluated first):

```
1  Generate topology from little      MIRROR, ARRAY, SCREW, SKIN
2  Cut / combine                      BOOLEAN
3  Add thickness                      SOLIDIFY
4  Round corners                      BEVEL
5  Smooth / densify                   SUBSURF, MULTIRES, REMESH
6  Deform                             ARMATURE, LATTICE, CURVE, SIMPLE_DEFORM, SHRINKWRAP
7  Fix shading                        WEIGHTED_NORMAL, NORMAL_EDIT, "Smooth by Angle" (NODES)
8  Reduce / finalize                  DECIMATE, TRIANGULATE, WELD
```

| Ordering question | Rule | Measured on a 2 m cube |
|---|---|---|
| Mirror vs Subsurf | **Mirror first** | Mirror→Subsurf(2) = 171 v / 176 f (seam welded); Subsurf(2)→Mirror = 196 v / 192 f (duplicated seam ring) |
| Bevel vs Subsurf | **Bevel first** (support loops) unless you want a bevel *on the subdivided* surface | Bevel(0.05, 2 seg)→Subsurf(2) = 866 v; Subsurf(2)→Bevel = 98 v and the corners are already round |
| Array vs Curve | **Array first**, then Curve deforms the whole strip | Array(8)→Curve follows the path (x 0→3.69, y 0→1.0); Curve→Array bends one tile then repeats it straight (y stays ±0.25) |
| Solidify vs Subsurf | **Solidify first** if you want even wall thickness; after Subsurf if you want thickness on the smoothed shell | Solidify→Subsurf = 226 v; Subsurf→Solidify = 178 v |
| Boolean vs Bevel | **Boolean first**, Bevel afterwards to round the cut | — |
| Boolean vs Mirror | **Mirror first** if the cutter is also mirrored; otherwise Boolean first | — |
| Triangulate | **Always last** | — |
| Armature | **After all generative modifiers**, before shading fixes | — |

## 3. Rules

R1. Add and configure modifiers with `obj.modifiers.new(name, type)` and plain attribute assignment.
    Why: no context, no selection, no active object, no mode. Works in `--background` and inside loops over hundreds of objects.
    Violation: `RuntimeError: Operator bpy.ops.object.modifier_add.poll() failed, context is incorrect`.

R2. Read modified geometry with `obj.evaluated_get(depsgraph)` + `to_mesh()` or `bpy.data.meshes.new_from_object()`.
    Why: it is the only headless-safe way and it is what `modifier_apply` does internally.
    Violation: agent inspects `obj.data` and sees the un-modified cage; mesh statistics are wrong by an order of magnitude.

R3. Free every temporary mesh: `to_mesh_clear()` after `to_mesh()`; `bpy.data.meshes.remove()` for `new_from_object()` results you discard.
    Why: `to_mesh()` results are owned by the evaluated object and stack up; `new_from_object()` creates a real datablock with 0 users that survives until file save.
    Violation: memory growth over a batch; stray `Mesh.001…Mesh.412` datablocks in the saved `.blend`.

R4. `bpy.ops.object.modifier_apply` requires an **active object** but not a window — it runs fine in `--background`.
    Why: its poll checks `context.object` and edit-mode state only.
    Violation without an active object: `RuntimeError: Operator bpy.ops.object.modifier_apply.poll() failed, context is incorrect`.

R5. Applying to multi-user mesh data fails; pass `single_user=True` or make the data single-user yourself.
    Why: applying would silently change every other user of the mesh.
    Violation: `RuntimeError: Error: Modifiers cannot be applied to multi-user data`.

R6. Prefer the data-API "apply all" (`new_from_object` → swap `obj.data` → `modifiers.clear()`) over per-modifier `modifier_apply`.
    Why: one depsgraph evaluation instead of N, no ordering hazards, no operator poll, and `preserve_all_data_layers=True` keeps UVs/vertex groups/attributes.
    Violation: none functionally — but N sequential applies are O(N) full re-evaluations.

R7. The only depsgraph Python can obtain is `mode == 'VIEWPORT'`.
    Why: `bpy.context.evaluated_depsgraph_get()` and `view_layer.depsgraph` both return VIEWPORT; the RENDER depsgraph is handed to `RenderEngine` subclasses only.
    Violation: evaluating a Subsurf with `levels=1, render_levels=3` returns 26 verts, not 386. Mirror `render_levels` onto `levels` temporarily (§4.6).

R8. `show_viewport = False` removes a modifier from everything Python can evaluate.
    Why: the viewport depsgraph honours the viewport visibility flag.
    Violation: `to_mesh()` returns the un-subdivided 8-vertex cube while the render would show a smooth one.

R9. Apply object scale before adding metric modifiers.
    Why: `width`, `thickness`, `merge_threshold`, `voxel_size`, `offset` are local-space distances.
    Violation: bevel width 0.2 on a `scale=(1,1,3)` object yields world chamfers of 0.2828 and 0.6325 — a 2.24× discrepancy.

R10. Choose the boolean solver by operand quality, not by taste: `'MANIFOLD'` (fast, refuses non-manifold input) → `'EXACT'` (coplanar-safe, slower) → `'FLOAT'` (fastest, breaks on coplanar/overlapping faces).
    Why: they are three different algorithms with different preconditions.
    Violation: `WARNING Object: "A", Modifier: "Bool", Cannot execute, object(s) 'B' have non-manifold geometry` and the modifier passes the input through unchanged.

R11. The boolean solver enum value changed in 5.0: `'FAST'` → `'FLOAT'`.
    Why: renamed to match its UI label ("Float"). `'EXACT'` and `'MANIFOLD'` are unchanged and exist in both 4.5 and 5.2.
    Violation on 4.5: `enum "FLOAT" not found in ('FAST', 'EXACT', 'MANIFOLD')`. Gate on `bpy.app.version`.

R12. Geometry Nodes modifier inputs moved to real RNA properties in 5.2 — resolve the socket identifier at runtime, never hardcode `"Input_2"`.
    Why: identifiers are assigned when the node group's interface is built and differ per asset/version.
    Violation on 5.x: `TypeError: bpy_struct.keys(): this type doesn't support IDProperties` when using the 4.x `mod["Input_2"]` form.

R13. Booleans need closed, non-self-intersecting, non-coplanar-with-each-other operands; check *both* meshes.
    Why: the target being open is as fatal as the cutter being open.
    Violation: with an open target, `'MANIFOLD'` returns the input untouched (8 v) while `'FLOAT'` and `'EXACT'` each produce a different 14-vertex result.

R14. Reorder with `obj.modifiers.move(from_index, to_index)`; find indices with `obj.modifiers.find(name)`.
    Why: pure data API; `bpy.ops.object.modifier_move_up/down` need context and operate on the active modifier.
    Violation: reordering the wrong modifier because `modifiers.active` was not what you assumed.

## 4. bpy patterns

### 4.1 Build a stack, no operators

```python
import bpy, math

def build_stack(obj, spec):
    """spec: list of (name, type, {prop: value}). Order in the list == stack order."""
    obj.modifiers.clear()
    made = []
    for name, mtype, props in spec:
        m = obj.modifiers.new(name, mtype)
        for k, v in props.items():
            setattr(m, k, v)          # raises AttributeError immediately on a typo
        made.append(m)
    return made

build_stack(obj, [
    ("Mirror",  'MIRROR',  {"use_axis": (True, False, False), "use_clip": True,
                            "use_mirror_merge": True, "merge_threshold": 0.001}),
    ("Bevel",   'BEVEL',   {"width": 0.02, "segments": 2, "limit_method": 'ANGLE',
                            "angle_limit": math.radians(30), "harden_normals": False}),
    ("Subsurf", 'SUBSURF', {"levels": 1, "render_levels": 2,
                            "uv_smooth": 'PRESERVE_BOUNDARIES', "use_limit_surface": True}),
])
```

### 4.2 Discover properties instead of guessing

```python
def modifier_props(mod):
    """Every writable property with its current value. Use before hardcoding a name."""
    out = {}
    for p in mod.bl_rna.properties:
        if p.identifier == "rna_type" or p.is_readonly:
            continue
        out[p.identifier] = getattr(mod, p.identifier)
    return out

def enum_values(mod, prop_name):
    return [i.identifier for i in mod.bl_rna.properties[prop_name].enum_items]

# e.g. enum_values(bool_mod, "solver") -> ['FLOAT','EXACT','MANIFOLD'] on 5.2
#                                      -> ['FAST','EXACT','MANIFOLD']  on 4.5
```

### 4.3 Reordering

```python
def move_modifier(obj, name, index):
    obj.modifiers.move(obj.modifiers.find(name), index)

def enforce_order(obj, preferred=('MIRROR','ARRAY','BOOLEAN','SOLIDIFY','BEVEL',
                                  'SUBSURF','ARMATURE','WEIGHTED_NORMAL','TRIANGULATE')):
    rank = {t: i for i, t in enumerate(preferred)}
    names = [m.name for m in sorted(obj.modifiers,
                                    key=lambda m: rank.get(m.type, len(preferred)))]
    for target, name in enumerate(names):
        obj.modifiers.move(obj.modifiers.find(name), target)
```

### 4.4 Read the evaluated mesh (headless)

```python
import bpy

def evaluated_mesh(obj, keep=False):
    """Temporary read. Caller must call obj.evaluated_get(dg).to_mesh_clear() when done."""
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = obj.evaluated_get(dg)
    return ob_eval.to_mesh(), ob_eval

me, ob_eval = evaluated_mesh(obj)
print(len(me.vertices), len(me.polygons))
ob_eval.to_mesh_clear()

def evaluated_mesh_copy(obj):
    """Real datablock you own. Remember bpy.data.meshes.remove() when finished."""
    dg = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(
        obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
```

### 4.5 Apply modifiers headlessly — three ways

```python
# (a) BEST: apply the whole stack via the data API. No operator, one evaluation.
def apply_all_modifiers(obj):
    if not obj.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(
        obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    new_me.name = obj.data.name
    old = obj.data
    obj.modifiers.clear()
    obj.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)

# (b) One specific modifier, keeping the rest of the stack: the operator is required.
def apply_one(obj, mod_name):
    vl = bpy.context.view_layer
    prev_active = vl.objects.active
    vl.objects.active = obj                     # poll() needs an active object
    obj.select_set(True)
    try:
        with bpy.context.temp_override(object=obj, active_object=obj,
                                       selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod_name, single_user=True)
    finally:
        vl.objects.active = prev_active
# NOTE: on 5.2 --background the bare call also works once the active object is set;
# temp_override just makes the intent explicit and survives being called from a handler.

# (c) Whole stack via operator (also converts curves/text/GN instances to real mesh):
#     bpy.ops.object.convert(target='MESH')   # needs active + selected; works headless
```

### 4.6 Render-quality evaluation without a render depsgraph

```python
def evaluated_at_render_quality(obj):
    saved = [(m, m.levels) for m in obj.modifiers if m.type in {'SUBSURF', 'MULTIRES'}]
    hidden = [m for m in obj.modifiers if m.show_render and not m.show_viewport]
    for m, _ in saved:
        m.levels = m.render_levels
    for m in hidden:
        m.show_viewport = True
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(obj.evaluated_get(dg),
                                               preserve_all_data_layers=True, depsgraph=dg)
    finally:
        for m, lv in saved:
            m.levels = lv
        for m in hidden:
            m.show_viewport = False
# verified: levels=1 -> 26 verts, render_levels=3 -> 386 verts on a cube
```

### 4.7 Booleans

```python
import bpy, bmesh

def is_boolean_ready(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bad = (any(not e.is_manifold for e in bm.edges)
           or any(f.calc_area() < 1e-9 for f in bm.faces))
    bm.free()
    return not bad

def add_boolean(obj, cutter, operation='DIFFERENCE'):
    m = obj.modifiers.new("Boolean", 'BOOLEAN')
    m.operand_type = 'OBJECT'
    m.object = cutter
    m.operation = operation                 # 'DIFFERENCE' | 'UNION' | 'INTERSECT'
    # 4.x: 'FAST' | 5.x: 'FLOAT'  (same algorithm, renamed in 5.0)
    fast = 'FLOAT' if bpy.app.version >= (5, 0, 0) else 'FAST'
    if is_boolean_ready(obj) and is_boolean_ready(cutter):
        m.solver = 'MANIFOLD'               # fastest, refuses non-manifold input
    else:
        m.solver = 'EXACT'
        m.use_self = True                   # allow self-intersecting operands
        m.use_hole_tolerant = True          # slower, survives small holes
    m.material_mode = 'TRANSFER'            # 'INDEX' (default) | 'TRANSFER'
    m.double_threshold = 1e-6               # overlap tolerance, EXACT only
    _ = fast                                # use for throw-away previews
    return m

# A cutter should be hidden from render but must stay enabled for the depsgraph:
cutter.hide_render = True
cutter.display_type = 'WIRE'
# do NOT use cutter.hide_viewport = True  -> that also removes it from evaluation
```

### 4.8 Geometry Nodes modifiers (version-gated)

```python
def gn_socket_identifier(node_group, socket_name, in_out='INPUT'):
    for item in node_group.interface.items_tree:
        if getattr(item, "in_out", None) == in_out and item.name == socket_name:
            return item.identifier
    raise KeyError(f"{socket_name!r} not in {node_group.name!r}")

def gn_set(mod, socket_name, value):
    ident = gn_socket_identifier(mod.node_group, socket_name)
    if bpy.app.version >= (5, 2, 0):
        getattr(mod.properties.inputs, ident).value = value
    else:
        mod[ident] = value                                  # 4.5 – 5.1

def gn_set_attribute_input(mod, socket_name, attr_name):
    ident = gn_socket_identifier(mod.node_group, socket_name)
    if bpy.app.version >= (5, 2, 0):
        sock = getattr(mod.properties.inputs, ident)
        sock.type = 'ATTRIBUTE'
        sock.attribute_name = attr_name
    else:
        mod[ident + "_use_attribute"] = True
        mod[ident + "_attribute_name"] = attr_name

# Diagnostics that only exist on NODES modifiers:
for w in mod.node_warnings:
    print(w)                       # populated after evaluation; empty == clean
```

### 4.9 Profiling the stack

```python
dg = bpy.context.evaluated_depsgraph_get()
ob_eval = obj.evaluated_get(dg)
ob_eval.to_mesh(); ob_eval.to_mesh_clear()          # force one evaluation
for m in ob_eval.modifiers:
    print(f"{m.name:20s} {m.type:16s} {m.execution_time*1000:8.2f} ms")
# execution_time is read-only and only meaningful on the EVALUATED object
```

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Operator bpy.ops.object.modifier_apply.poll() failed, context is incorrect` | No active object (`view_layer.objects.active is None`) or object in Edit Mode | Set `bpy.context.view_layer.objects.active = obj` first, or use §4.5(a) |
| `RuntimeError: Error: Modifiers cannot be applied to multi-user data` | `obj.data.users > 1` | `modifier_apply(..., single_user=True)` or `obj.data = obj.data.copy()` |
| `bpy_struct: item.attr = val: enum "FLOAT" not found in ('FAST', 'EXACT', 'MANIFOLD')` | Running 5.x code on 4.5 | Gate: `'FLOAT' if bpy.app.version >= (5,0,0) else 'FAST'` |
| `WARNING Object: "X", Modifier: "Bool", Cannot execute, object(s) 'Y' have non-manifold geometry` | `solver='MANIFOLD'` with an open/non-manifold operand; result is the *unchanged input* | Repair the operand, or switch to `'EXACT'` + `use_hole_tolerant=True` |
| `TypeError: bpy_struct.keys(): this type doesn't support IDProperties` | 4.x `mod["Input_2"]` access on a 5.2 Geometry Nodes modifier | `getattr(mod.properties.inputs, identifier).value` (§4.8) |
| `to_mesh()` returns the un-modified cage vertex count | `show_viewport = False` on the modifier, or the depsgraph was fetched before the modifier was added | Fetch `evaluated_depsgraph_get()` *after* every stack mutation; check `m.show_viewport` |
| Subsurf result has 26 verts instead of the expected 386 | Viewport depsgraph uses `levels`, not `render_levels` | §4.6 |
| Mirror seam shows a visible crease / doubled vertex ring after Subsurf | Subsurf placed **before** Mirror | `obj.modifiers.move(obj.modifiers.find("Mirror"), 0)` |
| Array along a curve stays straight | Curve placed **before** Array | Move Array above Curve |
| Boolean produces spikes / missing faces around a flat contact | Coplanar faces with `solver='FLOAT'` | `solver='EXACT'`, or offset the cutter by ~1e-3 so the faces are not coplanar |
| Boolean silently does nothing, no warning | `cutter.hide_viewport = True` removed it from the depsgraph | Use `hide_render` + `display_type='WIRE'` instead |
| `.blend` grows, Outliner full of `Mesh.001…Mesh.NNN` | `new_from_object()` results never freed | `bpy.data.meshes.remove(me)` |
| `AttributeError: 'SubsurfModifier' object has no attribute 'use_adaptive_subdivision'` | Adaptive-subdivision properties exist on `SUBSURF` in 5.x only | `getattr(m, "use_adaptive_subdivision", None)` / gate on `bpy.app.version` |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `SUBSURF.levels` / `.render_levels` | 0 / 0 (bake to normal map) | 1 / 2 | 1 / 2 | 2 / 3 | 2 / 3 then apply |
| `SUBSURF.uv_smooth` | `'PRESERVE_BOUNDARIES'` | `'PRESERVE_BOUNDARIES'` | `'SMOOTH_ALL'` | `'PRESERVE_BOUNDARIES'` | `'NONE'` |
| `SUBSURF.boundary_smooth` | `'ALL'` | `'ALL'` | `'ALL'` | `'ALL'` | `'PRESERVE_CORNERS'` |
| `SUBSURF.use_limit_surface` | — | True | True | True | False |
| `BEVEL.width` (m, uniform scale) | 0.002–0.005 | n/a | 0.01–0.05 | 0.0005–0.002 | ≥0.3 (print-safe fillet) |
| `BEVEL.segments` | 1–2 | n/a | 2–3 | 3–5 | 2 |
| `BEVEL.angle_limit` | radians(30) | n/a | radians(30) | radians(30) | radians(30) |
| `BEVEL.harden_normals` | True (with `WEIGHTED_NORMAL`) | False | False | True | False |
| `BOOLEAN.solver` | `'MANIFOLD'` | rarely used | `'FLOAT'`/`'FAST'` (preview) | `'EXACT'` | `'MANIFOLD'` |
| `BOOLEAN.use_hole_tolerant` | False | — | False | True | False |
| `BOOLEAN.double_threshold` | 1e-6 | — | 1e-5 | 1e-6 | 1e-7 |
| `SOLIDIFY.thickness` (m) | 0.005–0.02 | n/a | 0.02–0.1 | 0.001–0.003 | ≥0.0012 (min wall, FDM) |
| `SOLIDIFY.offset` | -1.0 | — | 0.0 | -1.0 | -1.0 |
| `SOLIDIFY.use_even_offset` | True | — | False | True | True |
| `SOLIDIFY.nonmanifold_thickness_mode` | `'CONSTRAINTS'` | — | `'CONSTRAINTS'` | `'CONSTRAINTS'` | `'EVEN'` |
| `MIRROR.merge_threshold` | 0.001 | 0.0001 | 0.001 | 0.0001 | 0.00001 |
| `MIRROR.use_clip` | True | True | False | True | True |
| `ARRAY.use_merge_vertices` | True | — | False | True | True |
| `WELD.merge_threshold` | 0.0001 | 0.00001 | 0.001 | 0.00001 | 0.000001 |
| `DECIMATE.ratio` | 0.3–0.6 (LODs) | 1.0 (never) | 1.0 | 1.0 | 1.0 |
| `TRIANGULATE` in stack | Yes, last | No | No | No | Yes, last |
| `TRIANGULATE.min_vertices` | 4 | — | — | — | 4 |
| Apply before export | Yes (all) | No (keep Armature) | No | Yes | Yes (all) |

## 7. Verification checklist

- [ ] `assert [m.type for m in obj.modifiers] == expected_order` — stack order is what you intended.
- [ ] `assert all(m.show_viewport for m in obj.modifiers)` — nothing is invisible to the depsgraph you are about to read.
- [ ] `dg = bpy.context.evaluated_depsgraph_get(); me = obj.evaluated_get(dg).to_mesh(); assert len(me.polygons) > len(obj.data.polygons)` — a generative stack actually generated something.
- [ ] `assert obj.modifiers.find("Mirror") < obj.modifiers.find("Subsurf")` — the seam will weld.
- [ ] `assert obj.modifiers.find("Triangulate") == len(obj.modifiers) - 1` — triangulation is last.
- [ ] `assert bool_mod.object is not None and not bool_mod.object.hide_viewport` — the cutter still reaches the depsgraph.
- [ ] `assert is_boolean_ready(obj) and is_boolean_ready(cutter)` before setting `solver='MANIFOLD'`.
- [ ] `assert obj.data.users == 1` before `modifier_apply`.
- [ ] `assert not obj.modifiers and len(obj.data.polygons) == expected` after `apply_all_modifiers`.
- [ ] `assert all(not m.node_warnings for m in obj.modifiers if m.type == 'NODES')` after one evaluation.
- [ ] `assert sum(m.execution_time for m in obj.evaluated_get(dg).modifiers) < budget_seconds`.
- [ ] Viewport screenshot: no doubled seam ridge down the mirror plane, no black spikes at boolean intersections.

## 8. Sources

- [Blender 5.2 Python API — `bpy.types.ObjectModifiers`](https://docs.blender.org/api/current/bpy.types.ObjectModifiers.html) (`new`, `remove`, `clear`, `move`, `active`)
- [Blender 5.2 Python API — Object Modifier Type Items](https://docs.blender.org/api/current/bpy_types_enum_items/object_modifier_type_items.html)
- [Blender 5.2 Python API — `bpy.types.BooleanModifier`](https://docs.blender.org/api/current/bpy.types.BooleanModifier.html) (`solver` = `'FLOAT' | 'EXACT' | 'MANIFOLD'`, `material_mode`, `double_threshold`, `use_self`, `use_hole_tolerant`, `operand_type`)
- [Blender 4.5 Python API — `bpy.types.BooleanModifier`](https://docs.blender.org/api/4.5/bpy.types.BooleanModifier.html) (`solver` = `'FAST' | 'EXACT' | 'MANIFOLD'`)
- [Blender 5.2 Python API — `bpy.types.Object`](https://docs.blender.org/api/current/bpy.types.Object.html) (`to_mesh`, `to_mesh_clear`) and [`bpy.types.ID.evaluated_get`](https://docs.blender.org/api/current/bpy.types.ID.html)
- [Blender 5.2 Python API — `bpy.ops.object`](https://docs.blender.org/api/current/bpy.ops.object.html) (`modifier_apply`, `modifier_add`, `modifier_add_node_group`, `convert`)
- [Blender 5.2 Python API — `bpy.types.NodesModifier`](https://docs.blender.org/api/current/bpy.types.NodesModifier.html) (`properties`, `node_warnings`, `is_input_used`)
- [Blender 5.0 release notes — Modeling: "Fast" boolean solver renamed to "Float"; six new Geometry Nodes based modifiers](https://developer.blender.org/docs/release_notes/5.0/modeling/)
- [Blender 5.2 release notes — Python API: Geometry Nodes modifier property access changed to `modifier.properties.inputs.<identifier>`](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- Empirically measured on local `blender-5.2.0-linux-x64` / `blender-4.5.9-linux-x64` in `--background --factory-startup`: all vertex/face counts in §2, the `modifier_apply` poll and multi-user error strings, the `MANIFOLD` non-manifold warning, the viewport-vs-render Subsurf counts (26 / 386), and the full writable-property dumps used in §6.
- `[UNVERIFIED]` The numeric values in §6 are pipeline conventions (LOD ratios, minimum FDM wall thickness, product-viz bevel widths), not Blender-documented defaults. `SOLIDIFY.nonmanifold_thickness_mode='EVEN'` for 3D print is a recommendation, not a documented requirement.

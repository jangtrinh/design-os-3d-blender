---
name: geometry-nodes
domain: procedural
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Build, wire and drive Geometry Node trees entirely from bpy — 4.0+ interface API, fields vs values, zones, instancing, baking.
loads_with: [simulation-physics, modifiers, modeling-topology, render-engines]
tags: [geometry-nodes, fields, nodes, procedural, instancing, zones, modifier, bpy]
---

# Geometry Nodes from Python

## 1. Mental model

A geometry node tree is a **pure function** `GeometrySet -> GeometrySet`, evaluated lazily by the
depsgraph whenever the object is re-evaluated. It is non-destructive: `obj.data` never changes; the
result lives only on the *evaluated* object (`depsgraph.id_eval_get(obj).evaluated_geometry()`).
Two kinds of value flow through links: **single values** (one value for the whole evaluation) and
**fields** (a deferred function of `index`/`position`/`normal`/… that is only *evaluated* when it
reaches a node that owns a geometry + domain, such as Set Position, Store Named Attribute or
Capture Attribute). The single biggest conceptual error an agent makes is treating a field as a
number: reading `node.outputs["Value"].default_value` to "get the result", or feeding a field into
a socket that only accepts a single value (Distribute Points on Faces' *Seed*, a Repeat Zone's
*Iterations*, a mesh primitive's *Vertices*). The second biggest error is memorised pre-4.0 code:
`node_group.inputs.new(...)` **was removed in 4.0** and now raises `AttributeError`. The third is
addressing modifier inputs the old way — **Blender 5.2 replaced the custom-property scheme
(`mod["Socket_2"]`) with real RNA properties (`mod.properties.inputs.<identifier>.value`)**.
Instancing is the performance lever: instances are cheap references, realized geometry is copied
memory. Zones (Repeat / Simulation / For Each Element) are always **two paired nodes**.

## 2. Decision first

| Situation | Choice | Why |
|---|---|---|
| Need per-element variation | Field (Index / Position / Random Value → downstream) | Evaluated once per element on a domain |
| Need one number for the whole tree | Single value (Group Input socket, `Value` node) | Fields are rejected by count/seed/iteration sockets |
| Many copies of the same object | `GeometryNodeInstanceOnPoints`, do **not** realize | O(1) memory per copy; renders via instancing |
| Copies must be booleaned / exported / UV'd / merged | `GeometryNodeRealizeInstances` right before that op | Most mesh ops ignore instance component |
| Fixed count of sequential steps | Repeat Zone | Frame-independent, no cache |
| State must depend on previous frame | Simulation Zone (+ bake) | Frame-order-dependent; see `simulation-physics.md` |
| Same op per element, element-local geometry | For Each Element Zone | Avoids index gymnastics; slower than field math |
| Result reused by other objects / other trees | Named attribute (`GeometryNodeStoreNamedAttribute`) | Survives the modifier boundary |
| Result reused inside this tree only | `GeometryNodeCaptureAttribute` | Anonymous, no name collisions |
| Expensive static generation, animation only downstream | `GeometryNodeBake` (`bake_mode='STILL'`) | Freeze once, skip recompute |
| Motion graphics loop that must tile seamlessly | Drive by `GeometryNodeInputSceneTime` → `ShaderNodeMath` (WRAP/PINGPONG) | Cyclic without keyframes |
| Interactive/viewport-only cheapness | `GeometryNodeIsViewport` → `GeometryNodeSwitch` | Low res in viewport, full res at render |
| Headless one-shot mesh generation | Build tree → evaluate → `evaluated_geometry()` / `to_mesh()` | No UI needed at all |

## 3. Rules

R1. Create trees with `bpy.data.node_groups.new(name, 'GeometryNodeTree')`; never rely on
    `bpy.ops.node.new_geometry_nodes_modifier`.
    Why: the operator needs a node-editor context and silently creates a default Group Input/Output pair you then have to find.
    Violation: `RuntimeError: Operator bpy.ops.node.new_geometry_node_group_assign.poll() failed, context is incorrect`.

R2. Declare group sockets **only** through `tree.interface.new_socket(...)`.
    Why: `NodeTree.inputs` / `.outputs` were removed in 4.0.
    Violation: `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`.

R3. Pass base socket type names to `new_socket` (`'NodeSocketFloat'`), never subtypes (`'NodeSocketFloatFactor'`).
    Why: documented restriction of the 4.0 interface API; set `socket.subtype` afterwards instead.
    Violation: `TypeError: bpy_struct: item.attr = val: enum "NodeSocketFloatFactor" not found` / socket created as generic.

R4. A `GeometryNodeTree` used as a modifier needs a Geometry **input** and a Geometry **output** socket, plus `NodeGroupInput` / `NodeGroupOutput` nodes wired to them.
    Why: the modifier binds to the first geometry input/output of the interface.
    Violation: modifier shows "Node group must have a geometry output"; evaluated object is empty in the screenshot.

R5. Address modifier inputs by **socket identifier**, resolved at runtime from the interface, never by hand-written `"Socket_2"`.
    Why: identifiers are allocated in creation order and are not stable across edits.
    Violation: `AttributeError: 'NodesModifierInputs' object has no attribute 'Socket_5'` or a silent no-op.

R6. Gate modifier-input code on `bpy.app.version >= (5, 2, 0)`.
    Why: 5.2 moved inputs from ID-properties to RNA (`mod.properties.inputs.X.value`); 4.5–5.1 use `mod["Socket_2"]`.
    Violation: on 5.2 `KeyError: 'bpy_struct[key]: key "Socket_2" not found'`; on 4.5 `AttributeError: 'NodesModifier' object has no attribute 'properties'`.

R7. Never link by guessed socket **name**; resolve by name with a fallback to index, and print the real socket list when resolution fails.
    Why: socket labels change between releases (Distribute Points on Faces takes `Mesh`, not `Geometry`).
    Violation: `KeyError: 'bpy_prop_collection[key]: key "Geometry" not found'`.

R8. Build every zone as a pair and call `zone_in.pair_with_output(zone_out)` **before** touching items or sockets.
    Why: the input node's sockets are mirrored from the output node's item list, which only exists once paired.
    Violation: `IndexError: bpy_prop_collection[2]: index 2 out of range` when linking zone sockets.

R9. Add zone/capture/bake state via the node's own item collection (`repeat_items`, `state_items`, `capture_items`, `bake_items`, `input_items`, `generation_items`), using `new(socket_type, name)` with a **Node Socket Data Type** enum value (`'GEOMETRY'`, `'FLOAT'`, `'VECTOR'`, `'MATRIX'`, `'ROTATION'`, `'BUNDLE'`, `'CLOSURE'`, …), not a `NodeSocket*` idname.
    Why: two different enums exist; the item API takes the data-type enum.
    Violation: `TypeError: enum "NodeSocketFloat" not found in ('FLOAT', 'INT', 'BOOLEAN', ...)`.

R10. Realize instances immediately before any operation that needs real topology (boolean, UV unwrap, merge by distance, export), and nowhere else.
    Why: realizing N instances of an M-vert mesh allocates N×M verts.
    Violation: multi-GB RAM, `MemoryError`, or a viewport screenshot showing only one copy where a boolean was expected.

R11. Set `node.location` on every node you create.
    Why: all new nodes default to (0,0) and stack; any screenshot of the node editor is unreadable and `bpy.ops.node.*` layout helpers need UI context.
    Violation: unusable node-editor screenshot; no traceback.

R12. Read results from the **evaluated** object, never from `obj.data`.
    Why: the modifier is non-destructive.
    Violation: `len(obj.data.vertices)` unchanged after scattering 10 000 points.

R13. After changing anything a modifier depends on, tag and re-evaluate: `obj.update_tag()` then `bpy.context.view_layer.update()` (or `depsgraph.update()`).
    Why: `--background` has no event loop to flush the depsgraph.
    Violation: stale geometry in the render / assertion failure with correct-looking node graph.

R14. Simulation Zone output is only correct if frames were stepped from `frame_start`; Repeat Zones are frame-independent.
    Why: sim zones carry state between frames.
    Violation: rendering frame 100 directly yields frame-1 state. See `simulation-physics.md`.

R15. Do not `tree.nodes.new()` an idname you have not verified; probe `getattr(bpy.types, idname, None)` first.
    Why: an unknown idname aborts the whole script mid-build, leaving a half-wired tree.
    Violation: `RuntimeError: Error: Node type GeometryNodeScatterPoints undefined`.

## 4. bpy patterns

### 4.1 Runtime discovery (use this instead of guessing)

```python
import bpy

def gn_node_types(substr=""):
    """All registered node idnames usable in a GeometryNodeTree."""
    out = []
    for name in dir(bpy.types):                       # dir(bpy.types) enumerates all RNA structs
        if not name.startswith(("GeometryNode", "FunctionNode", "ShaderNode", "Node")):
            continue
        cls = getattr(bpy.types, name, None)
        if cls is None or not hasattr(cls, "bl_rna"):
            continue
        if substr.lower() in name.lower():
            out.append(name)
    return sorted(out)

def node_exists(idname):
    return getattr(bpy.types, idname, None) is not None

def dump_sockets(node):
    """Print real socket names/identifiers/types — the only reliable source."""
    print(node.bl_idname, node.name)
    for i, s in enumerate(node.inputs):
        print(f"  IN  [{i}] name={s.name!r} id={s.identifier!r} type={s.type} hide={s.hide}")
    for i, s in enumerate(node.outputs):
        print(f"  OUT [{i}] name={s.name!r} id={s.identifier!r} type={s.type}")

def dump_node_props(idname):
    """Enum values / booleans that switch a node's mode."""
    rna = getattr(bpy.types, idname).bl_rna
    for p in rna.properties:
        if p.identifier in {"rna_type"} or p.is_readonly:
            continue
        if p.type == 'ENUM':
            print(p.identifier, "=", [e.identifier for e in p.enum_items])
        else:
            print(p.identifier, ":", p.type)
```

`bpy.types.GeometryNode.__subclasses__()` is **not** reliable — RNA classes are created lazily, so
it can return a short or empty list. `dir(bpy.types)` is the dependable enumeration. [UNVERIFIED:
exact laziness semantics; the `dir()` form is what this file recommends.]

### 4.2 Tree skeleton + the 4.0+ interface API

```python
import bpy

def new_gn_tree(name="GN"):
    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')   # 4.0+ and 5.x
    tree.is_modifier = True                                     # so it appears in the modifier list

    # NodeTreeInterface.new_socket(name, *, description='', in_out='INPUT',
    #                              socket_type='DEFAULT', parent=None) -> NodeTreeInterfaceSocket
    geo_in  = tree.interface.new_socket("Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
    geo_out = tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    n_in  = tree.nodes.new('NodeGroupInput');  n_in.location  = (-600, 0)
    n_out = tree.nodes.new('NodeGroupOutput'); n_out.location = ( 600, 0)
    tree.links.new(n_out.inputs[0], n_in.outputs[0])
    return tree, n_in, n_out
```

**The 18 socket idnames `new_socket` actually accepts on 5.2** (executed 2026-09-06,
every `NodeSocket*` in `bpy.types` tried one by one against a `GeometryNodeTree`):

`NodeSocketBool`, `NodeSocketBundle`, `NodeSocketClosure`, `NodeSocketCollection`,
`NodeSocketColor`, `NodeSocketFloat`, `NodeSocketFont`, `NodeSocketGeometry`,
`NodeSocketImage`, `NodeSocketInt`, `NodeSocketMaterial`, `NodeSocketMatrix`,
`NodeSocketMenu`, `NodeSocketObject`, `NodeSocketRotation`, `NodeSocketSound`,
`NodeSocketString`, `NodeSocketVector`.

Everything else in `bpy.types` starting with `NodeSocket` (64 names) raises `TypeError`
from `new_socket`. That includes six that this file previously listed as verified and
which are **not** usable here — `NodeSocketTexture`, `NodeSocketScene`,
`NodeSocketVector2D`, `NodeSocketVector4D`, `NodeSocketIntVector2D`,
`NodeSocketIntVector3D` — plus `NodeSocketShader` and `NodeSocketVirtual` (shader/internal
only) and every subtype (`NodeSocketFloatFactor`, `NodeSocketVectorTranslation`, …).
A registered `bpy.types` class is NOT evidence that `new_socket` accepts its name.

For a 2D/4D vector input there is no `new_socket` path in 5.2: create a
`NodeSocketVector` and set `socket.dimensions` / `socket.subtype` if the build exposes
them, or expose the components as separate `NodeSocketFloat` inputs.
[UNVERIFIED: whether `dimensions` is writable on an interface socket in this build.]

Re-derive the accepted list on any other build instead of trusting this one — one
headless probe, ~0.5 s:

```python
import bpy
tree = bpy.data.node_groups.new("probe", "GeometryNodeTree")
ok = []
for name in sorted(n for n in dir(bpy.types) if n.startswith("NodeSocket")):
    try:
        tree.interface.new_socket(name="p_" + name, in_out='INPUT', socket_type=name)
        ok.append(name)
    except TypeError:
        pass
print(len(ok), ok)
```

```python
# Typed exposed inputs with ranges, defaults, and field control
f = tree.interface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat')
f.default_value, f.min_value, f.max_value = 10.0, 0.0, 1000.0
f.subtype = 'NONE'            # inspect allowed values with dump_node_props / f.bl_rna
f.description = "Points per m^2"

# structure_type replaces the deprecated force_non_field (5.x)
# 'AUTO' | 'DYNAMIC' | 'FIELD' | 'GRID' | 'LIST' | 'SINGLE'
f.structure_type = 'SINGLE'   # refuse fields on this input

sel = tree.interface.new_socket("Selection", in_out='INPUT', socket_type='NodeSocketBool')
sel.structure_type = 'FIELD'
sel.default_attribute_name = "sel"      # name pre-filled in the modifier
sel.hide_value = True
sel.default_input = 'INDEX'             # VALUE|INDEX|ID_OR_INDEX|NORMAL|POSITION|
                                        # INSTANCE_TRANSFORM|HANDLE_LEFT|HANDLE_RIGHT|
                                        # SCENE_FRAME|UNIFORM_IMAGE_COORDINATES|SELF_OBJECT
                                        # (requires hide_value = True)

# Field OUTPUT that the modifier writes as an attribute
o = tree.interface.new_socket("Height", in_out='OUTPUT', socket_type='NodeSocketFloat')
o.attribute_domain = 'POINT'            # POINT|EDGE|FACE|CORNER|CURVE|INSTANCE|LAYER
o.default_attribute_name = "height"

# Panels (grouping in the modifier UI)
p = tree.interface.new_panel("Scatter", default_closed=False)
tree.interface.move_to_parent(f, p, 0)
```

### 4.3 Safe node creation + socket resolution

```python
def add(tree, idname, loc, **props):
    if getattr(bpy.types, idname, None) is None:
        raise KeyError(f"{idname} is not a registered node type in Blender {bpy.app.version_string}")
    n = tree.nodes.new(idname)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)          # e.g. distribute_method='POISSON', domain='FACE'
    return n

def sock(collection, key, fallback_index=None):
    """Resolve a socket by name, then identifier, then index. Loud on failure."""
    if isinstance(key, int):
        return collection[key]
    for s in collection:
        if s.name == key or s.identifier == key:
            return s
    if fallback_index is not None:
        return collection[fallback_index]
    raise KeyError(f"{key!r} not in {[ (s.name, s.identifier) for s in collection ]}")

def link(tree, from_node, from_key, to_node, to_key):
    # NodeLinks.new(input, output, *, verify_limits=True, handle_dynamic_sockets=False)
    return tree.links.new(sock(to_node.inputs, to_key), sock(from_node.outputs, from_key))
```

Setting an unconnected input's constant: `sock(n.inputs, "Scale").default_value = (2, 2, 2)`.
Geometry / Bundle / Closure sockets have **no** `default_value`.

### 4.4 Attach as a modifier and drive its inputs

```python
def attach(obj, tree, name="GeometryNodes"):
    mod = obj.modifiers.new(name, 'NODES')      # data API; no operator, background-safe
    mod.node_group = tree
    return mod

def iface_inputs(tree):
    """{socket name: identifier} for every INPUT socket, in interface order."""
    out = {}
    for item in tree.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            out[item.name] = item.identifier    # e.g. "Density" -> "Socket_2"
    return out

def set_gn_input(mod, identifier, value):
    if bpy.app.version >= (5, 2, 0):
        entry = getattr(mod.properties.inputs, identifier)   # runtime-generated RNA struct
        entry.type = 'VALUE'                                 # 'VALUE' | 'ATTRIBUTE' | 'LAYER'
        entry.value = value
    else:                                                    # 4.5 LTS .. 5.1
        mod[identifier] = value
        try:
            mod[identifier + "_use_attribute"] = 0
        except Exception:
            pass
    mod.id_data.update_tag()

def set_gn_input_attribute(mod, identifier, attr_name):
    if bpy.app.version >= (5, 2, 0):
        entry = getattr(mod.properties.inputs, identifier)
        entry.type = 'ATTRIBUTE'
        entry.attribute_name = attr_name
    else:
        mod[identifier + "_use_attribute"] = 1
        mod[identifier + "_attribute_name"] = attr_name
    mod.id_data.update_tag()

def set_gn_output_attribute(mod, identifier, attr_name):
    if bpy.app.version >= (5, 2, 0):
        getattr(mod.properties.outputs, identifier).attribute_name = attr_name
    else:
        mod[identifier + "_attribute_name"] = attr_name
```

`mod.is_input_visible(identifier)` / `mod.is_input_used(identifier)` answer "is this socket actually
live right now" (menu switches can hide inputs). Subscript access on
`mod.properties.inputs["Socket_2"]` is **[UNVERIFIED]** — use `getattr`.

### 4.5 Canonical recipe: scatter on a surface

```python
tree, n_in, n_out = new_gn_tree("Scatter")
d = tree.interface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat')
d.default_value, d.min_value, d.structure_type = 25.0, 0.0, 'SINGLE'

dist = add(tree, 'GeometryNodeDistributePointsOnFaces', (-350,   0),
           distribute_method='RANDOM')          # 'RANDOM' | 'POISSON'
ico  = add(tree, 'GeometryNodeMeshIcoSphere',    (-350, -300))
rnd  = add(tree, 'FunctionNodeRandomValue',      (-350, -520))
iop  = add(tree, 'GeometryNodeInstanceOnPoints', ( -80,   0))
scl  = add(tree, 'GeometryNodeScaleInstances',   ( 150,   0))

link(tree, n_in, 0,     dist, "Mesh")            # verified socket name: "Mesh"
link(tree, n_in, "Density", dist, "Density")
link(tree, dist, "Points",  iop,  "Points")
link(tree, ico,  "Mesh",    iop,  "Instance")
link(tree, dist, "Rotation", iop, "Rotation")    # aligns instances to the surface normal
link(tree, iop,  "Instances", scl, "Instances")
link(tree, rnd,  0,          scl, "Scale")       # field -> per-instance scale
link(tree, scl,  "Instances", n_out, 0)
```

Poisson mode uses different sockets (`Distance Min`, `Density Max`) — call `dump_sockets(dist)`
after setting `distribute_method` because the socket set changes with the mode.

**Instancing vs realizing.** `GeometryNodeInstanceOnPoints` costs ~one 4×4 matrix per copy.
`GeometryNodeRealizeInstances` copies the full mesh per copy. Insert Realize only immediately
before `GeometryNodeMeshBoolean`, `GeometryNodeMergeByDistance`, `GeometryNodeUVUnwrap`,
`GeometryNodeUVPackIslands`, or an export. 100 000 instances of a 500-vert rock = 50 M verts once
realized; the same scene renders fine unrealized in both EEVEE and Cycles.

### 4.6 Curve-based generation

```python
prof = add(tree, 'GeometryNodeCurvePrimitiveCircle', (-350, -250))   # profile
c2m  = add(tree, 'GeometryNodeCurveToMesh',          ( -80,    0))
res  = add(tree, 'GeometryNodeResampleCurve',        (-350,    0))

link(tree, n_in, 0,        res,  "Curve")
link(tree, res,  "Curve",  c2m,  "Curve")           # verified: "Curve", "Profile Curve",
link(tree, prof, "Curve",  c2m,  "Profile Curve")   #           "Scale", "Fill Caps" -> "Mesh"
link(tree, c2m,  "Mesh",   n_out, 0)
```

Taper via `GeometryNodeSetCurveRadius` fed by `GeometryNodeSplineParameter` → `ShaderNodeFloatCurve`.
Twist via `GeometryNodeSetCurveTilt`.

### 4.7 Set Position displacement

```python
pos  = add(tree, 'GeometryNodeInputPosition', (-600, -200))
nor  = add(tree, 'GeometryNodeInputNormal',   (-600, -350))
noi  = add(tree, 'ShaderNodeTexNoise',        (-400, -200))
mul  = add(tree, 'ShaderNodeVectorMath',      (-200, -300), operation='SCALE')
sp   = add(tree, 'GeometryNodeSetPosition',   (   0,    0))

link(tree, pos, "Position", noi, "Vector")
link(tree, nor, "Normal",   mul, 0)
link(tree, noi, "Fac",      mul, "Scale")
link(tree, n_in, 0,   sp, "Geometry")   # verified: Geometry, Selection, Position, Offset
link(tree, mul, "Vector", sp, "Offset")
link(tree, sp,  "Geometry", n_out, 0)
```

`Position` overrides absolute location; `Offset` adds. Both are evaluated against the *pre-node*
positions, so wiring both at once does not chain.

### 4.8 Attribute capture, named attributes, and reading them back

```python
cap = add(tree, 'GeometryNodeCaptureAttribute', (-200, 0), domain='POINT')
cap.capture_items.clear()
it = cap.capture_items.new('VECTOR', "RestPos")   # data-type enum, not NodeSocket* idname
# sockets appear as cap.inputs["RestPos"] / cap.outputs["RestPos"] after the item is added

sto = add(tree, 'GeometryNodeStoreNamedAttribute', (200, 0),
          data_type='FLOAT_VECTOR', domain='POINT')
sock(sto.inputs, "Name").default_value = "rest_pos"
# verified sockets: Geometry, Selection, Name, Value  ->  Geometry

get = add(tree, 'GeometryNodeInputNamedAttribute', (-600, -400), data_type='FLOAT_VECTOR')
sock(get.inputs, "Name").default_value = "rest_pos"
```

`data_type` for store/read uses the **Attribute Type** enum: `FLOAT`, `INT`, `BOOLEAN`,
`FLOAT_VECTOR`, `FLOAT_COLOR`, `QUATERNION`, `FLOAT4X4`, `STRING`, `INT8`, `FLOAT2`, `BYTE_COLOR`,
`INT32_2D`, `INT16_2D`, `FLOAT4`. `domain` uses the **Attribute Domain** enum: `POINT`, `EDGE`,
`FACE`, `CORNER`, `CURVE`, `INSTANCE`, `LAYER`.

Read back after evaluation:

```python
dg  = bpy.context.evaluated_depsgraph_get()
ev  = obj.evaluated_get(dg)
me  = ev.data                                # Mesh, if the output is a mesh
vals = [0.0] * len(me.attributes["rest_pos"].data) * 3
me.attributes["rest_pos"].data.foreach_get("vector", vals)

# Full component access (4.5+): mesh, pointcloud, curves, volume, grease_pencil, instances
gs = ev.evaluated_geometry()
print(gs.mesh, gs.pointcloud, gs.curves)
ipc = gs.instances_pointcloud()              # None if no instances
if ipc is not None:
    refs = gs.instance_references()          # list of Object/Collection/GeometrySet/None
    xf   = ipc.attributes["instance_transform"]
```

`GeometryNodeGetAttributeNames` (5.2) lists names inside the tree; `GeometryNodeRemoveAttribute`
and `GeometryNodeRenameAttribute` clean up before output — do this, or exported meshes carry
dozens of stray attributes.

### 4.9 Zones — all three follow the same shape

```python
def make_zone(tree, in_idname, out_idname, loc_in, loc_out):
    zin  = add(tree, in_idname,  loc_in)
    zout = add(tree, out_idname, loc_out)
    assert zin.pair_with_output(zout), "pair_with_output failed"   # returns bool
    return zin, zout
```

**Repeat Zone** — fixed iteration count, frame-independent:

```python
rin, rout = make_zone(tree, 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput', (-200, 0), (300, 0))
rout.repeat_items.clear()
rout.repeat_items.new('GEOMETRY', "Geometry")      # NodeGeometryRepeatOutputItems.new(socket_type, name)
rout.repeat_items.new('FLOAT',    "Scale")
sock(rin.inputs, "Iterations").default_value = 5   # SINGLE value only — a field here errors
link(tree, n_in, 0, rin, "Geometry")
# ... body between rin.outputs and rout.inputs ...
link(tree, rin, "Geometry", rout, "Geometry")
link(tree, rout, "Geometry", n_out, 0)
# rout.inspection_index selects which iteration the viewer/spreadsheet shows
```

**Simulation Zone** — carries state across frames:

```python
sin, sout = make_zone(tree, 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', (-200, 0), (300, 0))
sout.state_items.clear()
sout.state_items.new('GEOMETRY', "Geometry")       # NodeGeometrySimulationOutputItems.new(...)
sout.state_items.new('VECTOR',   "Velocity")
link(tree, n_in, 0, sin, "Geometry")               # "Geometry" here is the *initial* state
link(tree, sin, "Geometry", sout, "Geometry")
link(tree, sout, "Geometry", n_out, 0)
# sin.inputs also exposes "Delta Time" / "Elapsed Time" outputs on sin — dump_sockets(sin)
```

**For Each Element Zone** — body runs once per element of a domain:

```python
fin, fout = make_zone(tree, 'GeometryNodeForeachGeometryElementInput',
                            'GeometryNodeForeachGeometryElementOutput', (-200, 0), (400, 0))
fout.domain = 'FACE'                     # POINT|EDGE|FACE|CORNER|CURVE|INSTANCE|LAYER
fout.input_items.new('VECTOR', "Center")        # values sampled per element, available on fin
fout.generation_items.new('GEOMETRY', "Geometry")  # geometry produced per element, joined on output
# fout.main_items likewise exists for per-element values written back to the domain
```

Item collections and their `new(socket_type, name)` signature are identical across
`repeat_items`, `state_items`, `capture_items`, `bake_items`, `input_items`, `generation_items`.

**Bundles / Closures (5.0+)** are *not* `GeometryNode*` — they are generic node types shared with
shader trees: `NodeCombineBundle`, `NodeSeparateBundle`, `NodeJoinBundle`, `NodeGetBundleItem`,
`NodeStoreBundleItem`, `NodeClosureInput`, `NodeClosureOutput`, `NodeEvaluateClosure`.
`NodeClosureInput.pair_with_output()` exists, same as the other zones. Geometry-attached bundles
(5.2) use `GeometryNodeSetGeometryBundle` / `GeometryNodeGetGeometryBundle`.

### 4.10 Baking from Python (headless)

```python
# --- Simulation zones: bake the whole modifier stack of the ACTIVE object -------------
obj.use_simulation_cache = True                 # operator poll requires this ("Cache has to be enabled")
mod.bake_target = 'DISK'                        # 'PACKED' | 'DISK'
mod.bake_directory = "//bakes/gn/"              # DISK requires a saved .blend for '//' to resolve
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.simulation_nodes_cache_bake(selected=False)   # has exec() -> synchronous, background-safe

# --- A single Bake node -----------------------------------------------------------
for bake in mod.bakes:                          # NodesModifierBakes[NodesModifierBake]
    bake.bake_mode = 'ANIMATION'                # 'ANIMATION' | 'STILL'
    bake.bake_target = 'INHERIT'                # 'INHERIT' | 'PACKED' | 'DISK'
    bpy.ops.object.geometry_node_bake_single(
        session_uid=obj.session_uid, modifier_name=mod.name, bake_id=bake.bake_id)

# --- Clear ---------------------------------------------------------------------
bpy.ops.object.simulation_nodes_cache_delete(selected=False)
```

`bpy.ops.object.simulation_nodes_cache_calculate_to_frame()` has **no `exec()`** — invoke/modal
only. It cannot run under `--background`; step frames manually instead (see §4.11).

### 4.11 Motion-graphics idioms

```python
# Frame-cyclic driver: t in [0,1) repeating every LOOP frames, no keyframes needed
LOOP = 60
t   = add(tree, 'GeometryNodeInputSceneTime', (-800, 300))     # outputs Seconds, Frame
wrp = add(tree, 'ShaderNodeMath', (-620, 300), operation='WRAP')
sock(wrp.inputs, 1).default_value = float(LOOP)                # Max
sock(wrp.inputs, 2).default_value = 0.0                        # Min
div = add(tree, 'ShaderNodeMath', (-460, 300), operation='DIVIDE')
sock(div.inputs, 1).default_value = float(LOOP)
link(tree, t, "Frame", wrp, 0)
link(tree, wrp, "Value", div, 0)                                # -> 0..1 sawtooth, seamless loop

# Procedural array: mesh line -> instance on points -> per-index offset
line = add(tree, 'GeometryNodeMeshLine', (-600, 0))
idx  = add(tree, 'GeometryNodeInputIndex', (-600, -200))
mapr = add(tree, 'ShaderNodeMapRange', (-400, -200))            # index -> 0..1 for staggering

# Animated text
txt = add(tree, 'GeometryNodeStringToCurves', (-600, 500))      # 5.1+: all options are sockets,
fill = add(tree, 'GeometryNodeFillCurve', (-400, 500))          # incl. a Font socket
# StringToCurves outputs Curve Instances + Line/Pivot/Word index -> feed per-character staggering
```

Stepping frames headlessly (needed for sim zones, viewer previews, and `evaluated_geometry()` at
a specific time):

```python
scene = bpy.context.scene
for f in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(f)                 # runs the depsgraph, advances simulation zones
bpy.context.view_layer.update()
```

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'` | Pre-4.0 API memorised | `tree.interface.new_socket(name, in_out=..., socket_type=...)` |
| `KeyError: 'bpy_struct[key]: key "Socket_2" not found'` on 5.2 | Modifier inputs moved to RNA in 5.2 | `getattr(mod.properties.inputs, ident).value = v` |
| `AttributeError: 'NodesModifier' object has no attribute 'properties'` | Running 5.2 code on 4.5–5.1 | Gate on `bpy.app.version >= (5, 2, 0)` |
| `RuntimeError: Error: Node type GeometryNodeXxx undefined` | Hallucinated / renamed idname | `getattr(bpy.types, idname, None)` probe + `gn_node_types(substr)` |
| `KeyError: 'Geometry' not in [('Mesh','Mesh'), ...]` | Socket label differs per node/mode | `sock()` helper; `dump_sockets()` after setting mode enums |
| `TypeError: enum "NodeSocketFloat" not found in ('FLOAT', 'INT', ...)` | Passed socket idname to a zone item `new()` | Use data-type enum: `'FLOAT'`, `'GEOMETRY'`, … |
| `IndexError: bpy_prop_collection[1]: index out of range` right after creating a zone | `pair_with_output()` not called, or items not added | Pair first, add items, then link |
| Node graph looks right; render/screenshot shows original mesh | Read `obj.data`, or never re-evaluated | `obj.evaluated_get(depsgraph)`; `obj.update_tag()` + `view_layer.update()` |
| Everything renders at frame-1 state | Simulation zone, frame not stepped from start | Loop `scene.frame_set()` or bake (§4.10) |
| `RuntimeError: ... simulation_nodes_cache_bake.poll() failed, Cache has to be enabled` | `obj.use_simulation_cache` is False | Set it True before baking |
| `simulation_nodes_cache_calculate_to_frame` does nothing / poll fails in `--background` | Operator has invoke/modal only, no exec | Step frames manually |
| Blender consumes all RAM then is OOM-killed | `RealizeInstances` on a large scatter | Remove Realize, or reduce density / instance poly count |
| Boolean / UV node silently passes geometry through | Input was instances, not real geometry | Insert `GeometryNodeRealizeInstances` before it |
| Modifier shows "Node group must have a geometry output" | Interface missing a `NodeSocketGeometry` OUTPUT | Add it and wire `NodeGroupOutput` |
| Node-editor screenshot is an unreadable pile at origin | `node.location` never set | Assign locations; ~200 px column pitch |
| Field connected to *Seed* / *Iterations* / *Vertices* turns the link red | Those sockets are single-value only | Feed a constant or a `SINGLE` group input |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `distribute_method` (Distribute Points on Faces) | `RANDOM` | `POISSON` (hair/fur evenness) | `RANDOM` | `POISSON` | n/a |
| Scatter density (pts/m²) | 5–50 | 200–2000 (grooming) | 20–200 | 50–500 | n/a |
| Realize instances? | only for export/atlas bake | no | no (keep instanced) | no | **yes** (manifold required) |
| `GeometryNodeSubdivisionSurface` Level | 0–1 | 1–2 | 1–2 | 2–3 | 2–3 |
| `GeometryNodeResampleCurve` Count | 8–16 | 16–32 | 24–64 | 32–128 | 64–256 |
| Curve-to-Mesh profile Circle *Resolution* | 6–8 | 8–12 | 12–16 | 16–32 | 24–48 |
| `GeometryNodeMergeByDistance` Distance | 1e-3 | 1e-4 | 1e-4 | 1e-5 | 1e-5 (watertight) |
| Repeat Zone *Iterations* budget | ≤ 8 | ≤ 8 | ≤ 32 | ≤ 64 | ≤ 16 |
| Sim zone usage | avoid (bake to keys/vertex anim) | avoid | yes, baked | rarely | n/a |
| `mod.bake_target` | `DISK` (shared cache) | `DISK` | `PACKED` (single .blend) | `DISK` | n/a |
| Bake node `bake_mode` | `STILL` | `STILL` | `ANIMATION` | `STILL` | `STILL` |
| Output attribute domain default | `POINT` | `POINT` | `INSTANCE` | `POINT` | `POINT` |
| Viewport-vs-render switch (`GeometryNodeIsViewport`) | yes | yes | yes | yes | n/a |
| Store extra named attributes on final output | minimal (UV + color only) | as needed | free | free | none (strip before export) |

## 7. Verification checklist

- [ ] `assert bpy.app.version >= (4, 5, 0)` — the interface API in this file exists.
- [ ] `assert tree.bl_idname == 'GeometryNodeTree' and tree.is_modifier` — usable as a modifier.
- [ ] `assert any(i.item_type=='SOCKET' and i.in_out=='OUTPUT' and i.socket_type=='NodeSocketGeometry' for i in tree.interface.items_tree)` — R4 satisfied.
- [ ] `assert all(n.location[:] != (0.0, 0.0) or n == n_in for n in tree.nodes)` — layout was set (R11).
- [ ] `assert not [n for n in tree.nodes if n.mute]` and `assert len(tree.links) >= expected` — nothing silently unwired.
- [ ] `for n in tree.nodes: assert not any(getattr(s, "is_linked", False) is False and s.is_multi_input for s in n.inputs)` — no dangling multi-inputs. *(cheap smoke test; adapt per tree)*
- [ ] `assert mod.node_group is tree and mod.type == 'NODES'` — binding succeeded.
- [ ] `assert len(mod.node_warnings) == 0`, else `print([(w.type, w.message) for w in mod.node_warnings])` — this surfaces red node errors that produce no traceback.
- [ ] `ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); assert len(ev.data.vertices) > len(obj.data.vertices)` — the tree actually generated geometry.
- [ ] `gs = ev.evaluated_geometry(); assert gs.instances_pointcloud() is not None` — instancing path was kept (or assert `is None` after a deliberate Realize).
- [ ] `assert "rest_pos" in ev.data.attributes` — named attribute reached the output.
- [ ] `assert zone_in.paired_output == zone_out` — zone pairing survived (R8).
- [ ] Frame sweep + `assert len(obj.evaluated_get(dg).data.vertices) != first_frame_count` — a Simulation Zone is genuinely accumulating.
- [ ] `get_viewport_screenshot` of the 3D view after `view_layer.update()` — confirms scale/orientation, which no assertion catches.

## 8. Sources

- [bpy.types.NodeTreeInterface (5.2)](https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html) — `new_socket`/`new_panel`/`move`/`move_to_parent`/`remove` signatures
- [bpy.types.NodeTreeInterfaceSocket (5.2)](https://docs.blender.org/api/current/bpy.types.NodeTreeInterfaceSocket.html) — `identifier`, `structure_type`, `default_input`, `attribute_domain`, deprecated `force_non_field`
- [bpy.types.NodeSocket (5.2)](https://docs.blender.org/api/current/bpy.types.NodeSocket.html) — full list of `NodeSocket*` subclasses
- [bpy.types.GeometryNode (5.2)](https://docs.blender.org/api/current/bpy.types.GeometryNode.html) / [FunctionNode](https://docs.blender.org/api/current/bpy.types.FunctionNode.html) — authoritative node idname list
- [bpy.types.NodesModifier (5.2)](https://docs.blender.org/api/current/bpy.types.NodesModifier.html) — `properties`, `bakes`, `bake_target`, `node_warnings`, `is_input_used`
- [bpy.types.GeometrySet (4.5+)](https://docs.blender.org/api/current/bpy.types.GeometrySet.html) — `evaluated_geometry()`, `instances_pointcloud()`
- [bpy.types.GeometryNodeSimulationInput](https://docs.blender.org/api/current/bpy.types.GeometryNodeSimulationInput.html) / [RepeatInput](https://docs.blender.org/api/current/bpy.types.GeometryNodeRepeatInput.html) / [ForeachGeometryElementInput](https://docs.blender.org/api/current/bpy.types.GeometryNodeForeachGeometryElementInput.html) — `pair_with_output()`, `paired_output`
- [bpy.types.NodeGeometryRepeatOutputItems](https://docs.blender.org/api/current/bpy.types.NodeGeometryRepeatOutputItems.html) — `new(socket_type, name)`
- [Node Socket Data Type Items](https://docs.blender.org/api/current/bpy_types_enum_items/node_socket_data_type_items.html), [Node Socket Structure Type Items](https://docs.blender.org/api/current/bpy_types_enum_items/node_socket_structure_type_items.html), [Attribute Domain Items](https://docs.blender.org/api/current/bpy_types_enum_items/attribute_domain_items.html), [Attribute Type Items](https://docs.blender.org/api/current/bpy_types_enum_items/attribute_type_items.html)
- [Blender 4.0 release notes: Python API — Node Groups](https://developer.blender.org/docs/release_notes/4.0/python_api/) — removal of `tree.inputs/.outputs`; base-socket-type-only restriction
- [Blender 5.0 release notes: Python API — Nodes](https://developer.blender.org/docs/release_notes/5.0/python_api/) — interface items looked up by identifier; `scene.node_tree` removal
- [Blender 5.2 LTS release notes: Python API — Geometry Nodes](https://developer.blender.org/docs/release_notes/5.2/python_api/) — modifier input RNA migration
- [Blender 5.0](https://developer.blender.org/docs/release_notes/5.0/geometry_nodes/) / [5.1](https://developer.blender.org/docs/release_notes/5.1/geometry_nodes/) / [5.2](https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/) Geometry Nodes notes — Bundles, Closures, Grids, Lists, Geometry Bundles
- [Manual: Geometry Nodes Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/geometry_nodes.html), [Distribute Points on Faces](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/point/distribute_points_on_faces.html), [Instance on Points](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/instance_on_points.html), [Set Position](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/geometry/write/set_position.html), [Store Named Attribute](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/attribute/store_named_attribute.html), [Curve to Mesh](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/curve/operations/curve_to_mesh.html) — socket names
- `[UNVERIFIED]` subscript access `mod.properties.inputs["Socket_2"]`; reliability of `bpy.types.GeometryNode.__subclasses__()`; exact socket list of the For Each Element zone's `main_items` sockets.

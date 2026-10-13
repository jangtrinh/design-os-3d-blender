---
name: geometry-nodes
domain: procedural
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Build, wire and drive Geometry Node trees entirely from bpy — 4.0+ interface API, fields vs values, zones, instancing, baking.
loads_with: [simulation-physics, modifiers, modeling-topology, render-engines]
tags: [geometry-nodes, fields, nodes, procedural, instancing, zones, modifier, bpy]
id: geometry-nodes
title: "Geometry Nodes from Python"
when: [geometry-nodes-bpy, node-tree-interface, fields-vs-values, zones, instancing, gn-modifier-inputs]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Geometry Nodes from Python

## Purpose
Builds, wires and drives Geometry Node trees from bpy on 5.x: the 4.0+ interface API, the 5.2 modifier-input RNA, fields versus single values, zones, instancing and baking. Socket names, enums, error text and zone behaviour were re-run on Blender 5.2.0 LTS; several earlier statements were corrected.

## When to Use / When NOT
- ALLOWED: Creating a `GeometryNodeTree`, declaring group sockets through `tree.interface`, wiring nodes by resolved socket names, headless.
- ALLOWED: Attaching the tree as a `NODES` modifier and writing inputs through `modifier.properties.inputs.<identifier>` (5.2+) or `mod[identifier]` (4.5-5.1).
- ALLOWED: Using Repeat / Simulation / For Each zones, Bake nodes and instancing; reading evaluated geometry from the evaluated object.
- NOT ALLOWED: Advanced production patterns (catenary cables, slope-masked scattering, SDF volume remeshing) — use `geometry-nodes-advanced-production` instead.
- NOT ALLOWED: Legacy rigid body, cloth, soft body, fluid or particle caches — use `simulation-physics` instead.
- NOT ALLOWED: Modifier stack ordering or applying non-GN modifiers — use `modifiers` instead.
- NOT ALLOWED: Hand-writing `mod['Socket_2']` or `node_group.inputs.new(...)` — both fail on 5.x; resolve identifiers from the interface instead.

## Core Knowledge Content
### 1. Mental model

A geometry node tree is a **pure function** `GeometrySet -> GeometrySet`, evaluated lazily by the <!-- ease:source S7 anchor="Fields (Diamond)" --> <!-- ease:source S6 anchor="Nodes with diamond socket inputs and outputs are field nodes" -->
depsgraph whenever the object is re-evaluated. It is non-destructive: `obj.data` never changes; the
result lives only on the *evaluated* object (`depsgraph.id_eval_get(obj).evaluated_geometry()`).
Two kinds of value flow through links: **single values** (one value for the whole evaluation) and
**fields** (a deferred function of `index`/`position`/`normal`/… that is only *evaluated* when it
reaches a node that owns a geometry + domain, such as Set Position, Store Named Attribute or
Capture Attribute). The single biggest conceptual error an agent makes is treating a field as a
number: reading `node.outputs["Value"].default_value` to "get the result", or feeding a field into
a socket that only accepts a single value (Distribute Points on Faces' *Seed*, a Repeat Zone's
*Iterations*, a mesh primitive's *Vertices*). The second biggest error is memorised pre-4.0 code:
`node_group.inputs.new(...)` **was removed in 4.0** and now raises `AttributeError`. The third is <!-- ease:source S3 anchor="for socket in tree.inputs" --> <!-- ease:source S1 anchor="old tree.inputs attribute" -->
addressing modifier inputs the old way — **Blender 5.2 replaced the custom-property scheme
(`mod["Socket_2"]`) with real RNA properties (`mod.properties.inputs.<identifier>.value`)**. <!-- ease:source S5 anchor="The modifier now has proper RNA properties" -->
Instancing is the performance lever: instances are cheap references, realized geometry is copied
memory. Zones (Repeat / Simulation / For Each Element) are always **two paired nodes**.

### 2. Decision first

| Situation | Choice | Why |
|---|---|---|
| Need per-element variation | Field (Index / Position / Random Value → downstream) | Evaluated once per element on a domain |
| Need one number for the whole tree | Single value (Group Input socket, `Value` node) | Fields are rejected by count/seed/iteration sockets |
| Many copies of the same object | `GeometryNodeInstanceOnPoints`, do **not** realize | O(1) memory per copy; renders via instancing <!-- ease:source S14 anchor="Instance on Points" --> |
| Copies must be booleaned / exported / UV'd / merged | `GeometryNodeRealizeInstances` right before that op | Most mesh ops ignore instance component <!-- ease:source S13 anchor="Realize Instances" --> |
| Fixed count of sequential steps | Repeat Zone | Frame-independent, no cache <!-- ease:source S9 anchor="Repeat" --> |
| State must depend on previous frame | Simulation Zone (+ bake) | Frame-order-dependent; see `simulation-physics.md` <!-- ease:source S8 anchor="Simulation zones allow the result of one frame to influence the next one" --> |
| Same op per element, element-local geometry | For Each Element Zone | Avoids index gymnastics; slower than field math <!-- ease:source S10 anchor="For Each" --> |
| Result reused by other objects / other trees | Named attribute (`GeometryNodeStoreNamedAttribute`) | Survives the modifier boundary <!-- ease:source S1 anchor="StoreNamedAttribute sockets" --> |
| Result reused inside this tree only | `GeometryNodeCaptureAttribute` | Anonymous, no name collisions <!-- ease:source S1 anchor="CaptureAttribute.capture_items.new('VECTOR')" --> |
| Expensive static generation, animation only downstream | `GeometryNodeBake` (`bake_mode='STILL'`) | Freeze once, skip recompute <!-- ease:source S12 anchor="Still : Bakes the geometry data of the current frame" --> |
| Motion graphics loop that must tile seamlessly | Drive by `GeometryNodeInputSceneTime` → `ShaderNodeMath` (WRAP/PINGPONG) | Cyclic without keyframes <!-- ease:source S1 anchor="SceneTime outputs" --> |
| Interactive/viewport-only cheapness | `GeometryNodeIsViewport` → `GeometryNodeSwitch` | Low res in viewport, full res at render <!-- ease:source S1 anchor="idname.GeometryNodeIsViewport" --> |
| Headless one-shot mesh generation | Build tree → evaluate → `evaluated_geometry()` / `to_mesh()` | No UI needed at all |

### 3. Rules

R1. Create trees with `bpy.data.node_groups.new(name, 'GeometryNodeTree')`; never rely on <!-- ease:source S1 anchor="tree.is_modifier.writable" --> <!-- ease:source UNVERIFIED reason="the operator failure text for bpy.ops.node.new_geometry_node_group_assign was not re-run in this pass" -->
    `bpy.ops.node.new_geometry_nodes_modifier`.
    Why: the operator needs a node-editor context and silently creates a default Group Input/Output pair you then have to find.
    Violation: `RuntimeError: Operator bpy.ops.node.new_geometry_node_group_assign.poll() failed, context is incorrect`.

R2. Declare group sockets **only** through `tree.interface.new_socket(...)`. <!-- ease:source S16 anchor="new_socket" --> <!-- ease:source S1 anchor="old tree.inputs attribute" -->
    Why: `NodeTree.inputs` / `.outputs` were removed in 4.0.
    Violation: `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`.

R3. Pass base socket type names to `new_socket` (`'NodeSocketFloat'`), never subtypes (`'NodeSocketFloatFactor'`). <!-- ease:source S3 anchor="socket_type accepts only base socket type names" --> <!-- ease:source S1 anchor="new_socket.accepted.count" -->
    Why: documented restriction of the 4.0 interface API; set `socket.subtype` afterwards instead.
    Violation: `TypeError: bpy_struct: item.attr = val: enum "NodeSocketFloatFactor" not found` / socket created as generic.

R4. A `GeometryNodeTree` used as a modifier needs a Geometry **input** and a Geometry **output** socket, plus `NodeGroupInput` / `NodeGroupOutput` nodes wired to them. <!-- ease:source UNVERIFIED reason="the 'Node group must have a geometry output' text was not re-run in this pass" -->
    Why: the modifier binds to the first geometry input/output of the interface.
    Violation: modifier shows "Node group must have a geometry output"; evaluated object is empty in the screenshot.

R5. Address modifier inputs by **socket identifier**, resolved at runtime from the interface, never by hand-written `"Socket_2"`. <!-- ease:source S1 anchor="socket identifiers" --> <!-- ease:source S1 anchor="getattr(mod.properties.inputs, 'Socket_5') (unknown identifier)" -->
    Why: identifiers are allocated in creation order and are not stable across edits.
    Violation: `AttributeError: 'GeometryNodesInterfaceInputs' object has no attribute 'Socket_5'` (measured class name on 5.2.0) or a silent no-op.

R6. Gate modifier-input code on `bpy.app.version >= (5, 2, 0)`. <!-- ease:source S5 anchor="The modifier now has proper RNA properties" --> <!-- ease:source S1 anchor="mod['Socket_x'] on 5.2" -->
    Why: 5.2 moved inputs from ID-properties to RNA (`mod.properties.inputs.X.value`); 4.5–5.1 use `mod["Socket_2"]`.
    Violation: on 5.2 `mod['Socket_2']` raises `TypeError: this type doesn't support IDProperties` (measured; the earlier text said `KeyError`); on 4.5 `AttributeError: 'NodesModifier' object has no attribute 'properties'` (not re-run: only 5.2.0 is installed).

R7. Never link by guessed socket **name**; resolve by name with a fallback to index, and print the real socket list when resolution fails. <!-- ease:source S1 anchor="distribute.inputs['Geometry'] (wrong name)" -->
    Why: socket labels change between releases (Distribute Points on Faces takes `Mesh`, not `Geometry`).
    Violation: `KeyError: 'bpy_prop_collection[key]: key "Geometry" not found'`.

R8. Build every zone as a pair and call `zone_in.pair_with_output(zone_out)` **before** touching items or sockets. <!-- ease:source S1 anchor="sim pair_with_output" --> <!-- ease:source UNVERIFIED reason="the IndexError text when pairing is skipped was not re-run in this pass" -->
    Why: the input node's sockets are mirrored from the output node's item list, which only exists once paired.
    Violation: `IndexError: bpy_prop_collection[2]: index 2 out of range` when linking zone sockets.

R9. Add zone/capture/bake state via the node's own item collection (`repeat_items`, `state_items`, `capture_items`, `bake_items`, `input_items`, `generation_items`), using `new(socket_type, name)` with a **Node Socket Data Type** enum value (`'GEOMETRY'`, `'FLOAT'`, `'VECTOR'`, `'MATRIX'`, `'ROTATION'`, `'BUNDLE'`, `'CLOSURE'`, …), not a `NodeSocket*` idname. <!-- ease:source S1 anchor="node socket data type items (item API)" --> <!-- ease:source S21 anchor="new" --> <!-- ease:source S1 anchor="CaptureAttribute props" -->
    Why: two different enums exist; the item API takes the data-type enum.
    Violation: `TypeError: enum "NodeSocketFloat" not found in ('FLOAT', 'INT', 'BOOLEAN', ...)`.

R10. Realize instances immediately before any operation that needs real topology (boolean, UV unwrap, merge by distance, export), and nowhere else. <!-- ease:source S13 anchor="Realize All" --> <!-- ease:source S1 anchor="scatter(realized) = instances x 12 ico(1) verts?" -->
    Why: realizing N instances of an M-vert mesh allocates N×M verts.
    Violation: multi-GB RAM, `MemoryError`, or a viewport screenshot showing only one copy where a boolean was expected.

R11. Set `node.location` on every node you create. <!-- ease:source UNVERIFIED reason="layout advice; no source claims node defaults beyond (0,0)" -->
    Why: all new nodes default to (0,0) and stack; any screenshot of the node editor is unreadable and `bpy.ops.node.*` layout helpers need UI context.
    Violation: unusable node-editor screenshot; no traceback.

R12. Read results from the **evaluated** object, never from `obj.data`. <!-- ease:source S18 anchor="evaluated_geometry" -->
    Why: the modifier is non-destructive.
    Violation: `len(obj.data.vertices)` unchanged after scattering 10 000 points.

R13. After changing anything a modifier depends on, tag and re-evaluate: `obj.update_tag()` then `bpy.context.view_layer.update()` (or `depsgraph.update()`). <!-- ease:source UNVERIFIED reason="depsgraph flush behaviour in --background is stated without a primary source" -->
    Why: `--background` has no event loop to flush the depsgraph.
    Violation: stale geometry in the render / assertion failure with correct-looking node graph.

R14. Simulation Zone output is only correct if frames were stepped from `frame_start`; Repeat Zones are frame-independent. <!-- ease:source S1 anchor="sim mean z after direct jump 1 -> 10" --> <!-- ease:source S1 anchor="sim mean z after stepping 1..10" --> <!-- ease:source S8 anchor="Simulation zones allow the result of one frame to influence the next one" -->
    Why: sim zones carry state between frames.
    Violation: rendering frame 100 directly yields frame-1 state. See `simulation-physics.md`.

R15. Do not `tree.nodes.new()` an idname you have not verified; probe `getattr(bpy.types, idname, None)` first. <!-- ease:source S1 anchor="tree.nodes.new('GeometryNodeScatterPoints')" -->
    Why: an unknown idname aborts the whole script mid-build, leaving a half-wired tree.
    Violation: `RuntimeError: Error: Node type GeometryNodeScatterPoints undefined`.

### 4. bpy patterns

#### 4.1 Runtime discovery (use this instead of guessing)

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

`bpy.types.GeometryNode.__subclasses__()` is **not** reliable — RNA classes are created lazily, so <!-- ease:source S1 anchor="GeometryNode.__subclasses__ count" --> <!-- ease:source UNVERIFIED reason="'RNA classes are created lazily' is an explanation, not measured; only the 49-versus-274 count is" -->
it can return a short list (measured on 5.2.0: 49 subclasses versus 274 `GeometryNode*` names in `dir(bpy.types)`, which also include non-node types). `dir(bpy.types)` is the dependable enumeration.

#### 4.2 Tree skeleton + the 4.0+ interface API

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

**The 18 socket idnames `new_socket` actually accepts on 5.2** (executed 2026-09-06, <!-- ease:source S1 anchor="new_socket.accepted == earlier documented 18" -->
every `NodeSocket*` in `bpy.types` tried one by one against a `GeometryNodeTree`):

`NodeSocketBool`, `NodeSocketBundle`, `NodeSocketClosure`, `NodeSocketCollection`,
`NodeSocketColor`, `NodeSocketFloat`, `NodeSocketFont`, `NodeSocketGeometry`,
`NodeSocketImage`, `NodeSocketInt`, `NodeSocketMaterial`, `NodeSocketMatrix`,
`NodeSocketMenu`, `NodeSocketObject`, `NodeSocketRotation`, `NodeSocketSound`,
`NodeSocketString`, `NodeSocketVector`.

Everything else in `bpy.types` starting with `NodeSocket` (64 names) raises `TypeError` <!-- ease:source S1 anchor="new_socket.rejected.count" -->
from `new_socket`. That includes six that this file previously listed as verified and
which are **not** usable here — `NodeSocketTexture`, `NodeSocketScene`,
`NodeSocketVector2D`, `NodeSocketVector4D`, `NodeSocketIntVector2D`,
`NodeSocketIntVector3D` — plus `NodeSocketShader` and `NodeSocketVirtual` (shader/internal
only) and every subtype (`NodeSocketFloatFactor`, `NodeSocketVectorTranslation`, …).
A registered `bpy.types` class is NOT evidence that `new_socket` accepts its name.

For a 2D/4D vector input there is no `new_socket` path in 5.2: create a
`NodeSocketVector` and set `socket.dimensions` / `socket.subtype` if the build exposes
them, or expose the components as separate `NodeSocketFloat` inputs.
[UNVERIFIED: whether `dimensions` is writable on an interface socket in this build.] <!-- ease:source S1 anchor="interface socket has props" -->

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
# 'AUTO' | 'DYNAMIC' | 'FIELD' | 'GRID' | 'LIST' | 'SINGLE' (the accepted subset depends on the socket type;
# measured: NodeSocketGeometry accepts only AUTO | LIST | SINGLE)
f.structure_type = 'SINGLE'   # refuse fields on this input

sel = tree.interface.new_socket("Selection", in_out='INPUT', socket_type='NodeSocketBool')
sel.structure_type = 'FIELD'
sel.default_attribute_name = "sel"      # name pre-filled in the modifier
sel.hide_value = True
# default_input needs hide_value = True and its accepted values depend on the socket type (measured on 5.2.0):
#   Bool / Rotation / Geometry: VALUE only          Float: VALUE | SCENE_FRAME
#   Int: VALUE | INDEX | ID_OR_INDEX | SCENE_FRAME  Vector: VALUE | NORMAL | POSITION | HANDLE_LEFT | HANDLE_RIGHT
#   Matrix: VALUE | INSTANCE_TRANSFORM
idx_in = tree.interface.new_socket("Index", in_out='INPUT', socket_type='NodeSocketInt')
idx_in.structure_type = 'FIELD'
idx_in.hide_value = True
idx_in.default_input = 'INDEX'          # setting 'INDEX' on the Bool socket above raises TypeError

# Field OUTPUT that the modifier writes as an attribute
o = tree.interface.new_socket("Height", in_out='OUTPUT', socket_type='NodeSocketFloat')
o.attribute_domain = 'POINT'            # POINT|EDGE|FACE|CORNER|CURVE|INSTANCE|LAYER
o.default_attribute_name = "height"

# Panels (grouping in the modifier UI)
p = tree.interface.new_panel("Scatter", default_closed=False)
tree.interface.move_to_parent(f, p, 0)
```

#### 4.3 Safe node creation + socket resolution

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

#### 4.4 Attach as a modifier and drive its inputs

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
        entry.type = 'VALUE'                                 # measured on a Float input: 'VALUE' | 'ATTRIBUTE'
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

`mod.is_input_visible(identifier)` / `mod.is_input_used(identifier)` answer "is this socket actually <!-- ease:source S1 anchor="mod.is_input_used / is_input_visible" --> <!-- ease:source S1 anchor="properties.inputs['Socket_2'] subscript" -->
live right now" (menu switches can hide inputs). Subscript access on
`mod.properties.inputs["Socket_2"]` is **[UNVERIFIED]** — use `getattr`.

#### 4.5 Canonical recipe: scatter on a surface

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

Poisson mode uses different sockets (`Distance Min`, `Density Max`) — call `dump_sockets(dist)` <!-- ease:source S1 anchor="DistributePointsOnFaces[POISSON] enabled inputs" --> <!-- ease:source S15 anchor="Distance Min The minimal distance points can have to each other" -->
after setting `distribute_method` because the socket set changes with the mode.

**Instancing vs realizing.** `GeometryNodeInstanceOnPoints` costs ~one 4×4 matrix per copy. <!-- ease:source S13 anchor="Realize Instances" --> <!-- ease:source S1 anchor="scatter(instanced).instance count" -->
`GeometryNodeRealizeInstances` copies the full mesh per copy. Insert Realize only immediately
before `GeometryNodeMeshBoolean`, `GeometryNodeMergeByDistance`, `GeometryNodeUVUnwrap`,
`GeometryNodeUVPackIslands`, or an export. 100 000 instances of a 500-vert rock = 50 M verts once
realized; the same scene renders fine unrealized in both EEVEE and Cycles.

#### 4.6 Curve-based generation

```python
prof = add(tree, 'GeometryNodeCurvePrimitiveCircle', (-350, -250))   # profile
c2m  = add(tree, 'GeometryNodeCurveToMesh',          ( -80,    0))
res  = add(tree, 'GeometryNodeResampleCurve',        (-350,    0))

link(tree, n_in, 0,        res,  "Curve")
link(tree, res,  "Curve",  c2m,  "Curve")           # verified: "Curve", "Profile Curve",
link(tree, prof, "Curve",  c2m,  "Profile Curve")   #           "Scale", "Fill Caps" -> "Mesh"
link(tree, c2m,  "Mesh",   n_out, 0)
```

Taper via `GeometryNodeSetCurveRadius` fed by `GeometryNodeSplineParameter` → `ShaderNodeFloatCurve`. <!-- ease:source S1 anchor="idname.GeometryNodeSetCurveRadius" -->
Twist via `GeometryNodeSetCurveTilt`.

#### 4.7 Set Position displacement

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

`Position` overrides absolute location; `Offset` adds. Both are evaluated against the *pre-node* <!-- ease:source S1 anchor="SetPosition sockets" -->
positions, so wiring both at once does not chain.

#### 4.8 Attribute capture, named attributes, and reading them back

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

`data_type` for store/read uses the **Attribute Type** enum: `FLOAT`, `INT`, `BOOLEAN`, <!-- ease:source S1 anchor="StoreNamedAttribute data_type" --> <!-- ease:source S1 anchor="StoreNamedAttribute domain" -->
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

`GeometryNodeGetAttributeNames` (5.2) lists names inside the tree; `GeometryNodeRemoveAttribute` <!-- ease:source S1 anchor="idname.GeometryNodeGetAttributeNames" -->
and `GeometryNodeRenameAttribute` clean up before output — do this, or exported meshes carry
dozens of stray attributes.

#### 4.9 Zones — all three follow the same shape

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
# sin.outputs exposes "Delta Time" (measured on 5.2.0: no "Elapsed Time" output) — dump_sockets(sin)
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

Item collections and their `new(socket_type, name)` signature are identical across <!-- ease:source S1 anchor="NodeClosureInput.pair_with_output" -->
`repeat_items`, `state_items`, `capture_items`, `bake_items`, `input_items`, `generation_items`.

**Bundles / Closures (5.0+)** are *not* `GeometryNode*` — they are generic node types shared with <!-- ease:source S19 anchor="Bundles offer a new way to organize data" --> <!-- ease:source S1 anchor="idname.NodeCombineBundle" --> <!-- ease:source S20 anchor="Geometry Bundles" -->
shader trees: `NodeCombineBundle`, `NodeSeparateBundle`, `NodeJoinBundle`, `NodeGetBundleItem`,
`NodeStoreBundleItem`, `NodeClosureInput`, `NodeClosureOutput`, `NodeEvaluateClosure`.
`NodeClosureInput.pair_with_output()` exists, same as the other zones. Geometry-attached bundles
(5.2) use `GeometryNodeSetGeometryBundle` / `GeometryNodeGetGeometryBundle`.

#### 4.10 Baking from Python (headless)

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

`bpy.ops.object.simulation_nodes_cache_calculate_to_frame()` has **no `exec()`** — invoke/modal <!-- ease:source S1 anchor="simulation_nodes_cache_calculate_to_frame result" -->
only. It cannot run under `--background`; step frames manually instead (see §4.11).

> Bake storage (measured on 5.2.0): `NodesModifier.bake_target` defaults to `PACKED`; with `bake_target='DISK'` a Simulation Zone bake wrote `<bake_directory>/<id>/meta/*.json` and `<id>/blobs/*.blob` (60 files for 30 frames), not `.vdb` or `.bphys`. <!-- ease:source S1 anchor="disk bake files (extensions)" --> <!-- ease:source S1 anchor="disk bake file count" --> <!-- ease:source S11 anchor="Bake Geometry Node" -->

#### 4.11 Motion-graphics idioms

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

Stepping frames headlessly (needed for sim zones, viewer previews, and `evaluated_geometry()` at <!-- ease:source S1 anchor="sim mean z after stepping 1..10" -->
a specific time):

```python
scene = bpy.context.scene
for f in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(f)                 # runs the depsgraph, advances simulation zones
bpy.context.view_layer.update()
```

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'` | Pre-4.0 API memorised | `tree.interface.new_socket(name, in_out=..., socket_type=...)` <!-- ease:source S1 anchor="old tree.inputs attribute" --> |
| `TypeError: this type doesn't support IDProperties` on `mod['Socket_2']` (5.2) | Modifier inputs moved to RNA in 5.2 | `getattr(mod.properties.inputs, ident).value = v` <!-- ease:source S1 anchor="mod['Socket_x'] on 5.2" --> |
| `AttributeError: 'NodesModifier' object has no attribute 'properties'` | Running 5.2 code on 4.5–5.1 | Gate on `bpy.app.version >= (5, 2, 0)` <!-- ease:source UNVERIFIED reason="4.5-5.1 behaviour cannot be re-run: only 5.2.0 is installed" --> |
| `RuntimeError: Error: Node type GeometryNodeXxx undefined` | Hallucinated / renamed idname | `getattr(bpy.types, idname, None)` probe + `gn_node_types(substr)` <!-- ease:source S1 anchor="tree.nodes.new('GeometryNodeScatterPoints')" --> |
| `KeyError: 'Geometry' not in [('Mesh','Mesh'), ...]` | Socket label differs per node/mode | `sock()` helper; `dump_sockets()` after setting mode enums <!-- ease:source S1 anchor="distribute.inputs['Geometry'] (wrong name)" --> |
| `TypeError: enum "NodeSocketFloat" not found in ('FLOAT', 'INT', ...)` | Passed socket idname to a zone item `new()` | Use data-type enum: `'FLOAT'`, `'GEOMETRY'`, … <!-- ease:source S1 anchor="node socket data type items (item API)" --> |
| `IndexError: bpy_prop_collection[1]: index out of range` right after creating a zone | `pair_with_output()` not called, or items not added | Pair first, add items, then link |
| Node graph looks right; render/screenshot shows original mesh | Read `obj.data`, or never re-evaluated | `obj.evaluated_get(depsgraph)`; `obj.update_tag()` + `view_layer.update()` |
| Everything renders at frame-1 state | Simulation zone, frame not stepped from start | Loop `scene.frame_set()` or bake (§4.10) <!-- ease:source S1 anchor="sim mean z after direct jump 1 -> 10" --> |
| `RuntimeError: ... simulation_nodes_cache_bake.poll() failed, Cache has to be enabled` | `obj.use_simulation_cache` is False | Set it True before baking <!-- ease:source S1 anchor="simulation_nodes_cache_bake without cache enabled" --> |
| `simulation_nodes_cache_calculate_to_frame` does nothing / poll fails in `--background` | Operator has invoke/modal only, no exec | Step frames manually <!-- ease:source S1 anchor="simulation_nodes_cache_calculate_to_frame result" --> |
| Blender consumes all RAM then is OOM-killed | `RealizeInstances` on a large scatter | Remove Realize, or reduce density / instance poly count |
| Boolean / UV node silently passes geometry through | Input was instances, not real geometry | Insert `GeometryNodeRealizeInstances` before it <!-- ease:source UNVERIFIED reason="pass-through behaviour for instance input was not re-run in this pass" --> |
| Modifier shows "Node group must have a geometry output" | Interface missing a `NodeSocketGeometry` OUTPUT | Add it and wire `NodeGroupOutput` |
| Node-editor screenshot is an unreadable pile at origin | `node.location` never set | Assign locations; ~200 px column pitch |
| Field connected to *Seed* / *Iterations* / *Vertices* turns the link red | Those sockets are single-value only | Feed a constant or a `SINGLE` group input <!-- ease:source S6 anchor="drawn as a solid red line indicating that there is an error" --> |

### 6. Parameter defaults by use case

Node, socket and enum names in this table were checked against the 5.2.0 node RNA (`GeometryNodeDistributePointsOnFaces.distribute_method`, `GeometryNodeSubdivisionSurface` `Level`, `GeometryNodeResampleCurve` `Count`, `GeometryNodeCurvePrimitiveCircle` `Resolution`, `GeometryNodeMergeByDistance` `Distance`, `GeometryNodeRepeatInput` `Iterations`, `NodesModifier.bake_target`, `NodesModifierBake.bake_mode`, `GeometryNodeIsViewport`); the numeric values are pipeline conventions. <!-- ease:source S1 anchor="SubdivisionSurface sockets" --> <!-- ease:source S1 anchor="ResampleCurve sockets" --> <!-- ease:source S1 anchor="MergeByDistance sockets" --> <!-- ease:source S1 anchor="CurvePrimitiveCircle sockets" --> <!-- ease:source S1 anchor="RepeatInput.Iterations socket exists" --> <!-- ease:source S1 anchor="NodesModifierBake.bake_mode" --> <!-- ease:source S17 anchor="bake_target" --> <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" -->

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

### 7. Verification checklist

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

### 8. Original reference list (pre-UKMC; the numbered Sources section at the end of this file is authoritative)

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

## Failure Modes (Mandatory)
- **`AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`** — cause: pre-4.0 `node_group.inputs.new()` code — fix: `tree.interface.new_socket(name, in_out=..., socket_type='NodeSocket...')` with a base socket type name. <!-- ease:source S3 anchor="for socket in tree.inputs" --> <!-- ease:source S1 anchor="old tree.inputs attribute" -->
- **`TypeError: this type doesn't support IDProperties` when writing `mod['Socket_2']` on 5.2** — cause: modifier inputs became RNA properties in 5.2 — fix: gate on `bpy.app.version >= (5, 2, 0)` and use `getattr(mod.properties.inputs, identifier).value`, resolving the identifier from the interface. <!-- ease:source S5 anchor="The modifier now has proper RNA properties" --> <!-- ease:source S1 anchor="mod['Socket_x'] on 5.2" -->
- **`TypeError: ... enum "INDEX" not found in ('VALUE')` when setting `default_input`** — cause: the accepted `default_input` values depend on the socket type (Bool accepts only VALUE; INDEX is for Int) — fix: put `INDEX` on an `NodeSocketInt`, `POSITION`/`NORMAL` on a `NodeSocketVector`. <!-- ease:source S1 anchor="default_input accepted for NodeSocketInt" --> <!-- ease:source S1 anchor="default_input accepted for NodeSocketBool" -->
- **`RuntimeError: Error: Node type GeometryNodeScatterPoints undefined` aborts the build half-wired** — cause: a hallucinated or renamed idname — fix: probe `getattr(bpy.types, idname, None)` before `nodes.new` and list candidates from `dir(bpy.types)`. <!-- ease:source S1 anchor="tree.nodes.new('GeometryNodeScatterPoints')" -->
- **Everything renders at the first simulated frame** — cause: a Simulation Zone only advances one step per frame change (measured: jumping 1 -> 10 moved the mean Z from 0.1 to 0.2, stepping 1..10 gave 1.0) — fix: step `scene.frame_set(f)` from `frame_start` or bake. <!-- ease:source S1 anchor="sim mean z after direct jump 1 -> 10" --> <!-- ease:source S1 anchor="sim mean z after stepping 1..10" -->
- **`RuntimeError: ... simulation_nodes_cache_bake.poll() Cache has to be enabled`** — cause: `obj.use_simulation_cache` is False — fix: set it True before baking (measured: the bake then returns FINISHED headless with the default `PACKED` target). <!-- ease:source S1 anchor="simulation_nodes_cache_bake without cache enabled" --> <!-- ease:source S1 anchor="simulation_nodes_cache_bake (packed) result" -->
- **Memory explodes after a scatter** — cause: `Realize Instances` multiplies geometry by the instance count (measured: 408 instances of a 12-vertex icosphere became 4,896 vertices) — fix: keep instances until a boolean, UV or export needs real topology. <!-- ease:source S1 anchor="scatter(realized) = instances x 12 ico(1) verts?" --> <!-- ease:source S13 anchor="Realize All" -->

## Sources
- [S1] Local Blender 5.2.0 LTS Geometry Nodes API probe (script: knowledge/_evidence/kb-261013/w2-gn-api-probe.py) — knowledge/_evidence/kb-261013/w2-gn-api-probe.txt — captured 2026-10-13 — sha256 c83f0e20d36cb3d773e27ac4440a9c8c6648f9a130bcf5933dc66c699648c739
- [S3] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/4.0/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-4-0-python_api.html) — captured 2026-10-13 — sha256 6afa52860e6e9b22fadc662b9cc5da797b315e003e70a27f22f28dc7285b12eb
- [S5] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.2/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-2-python_api.html) — captured 2026-10-13 — sha256 613fac2fa63a96155d40c761571e1a7407c709926ebc2eff96f846343bb1b086
- [S6] Fields - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/fields.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-fields.html) — captured 2026-10-13 — sha256 3f1aa97116d87c129ad1ebf883e1a1aed767036f7c8973a9e88c142055c3a48e
- [S7] Node Parts - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/interface/controls/nodes/parts.html (frozen: knowledge/_evidence/kb-261013/w2-manual-interface-controls-nodes-parts.html) — captured 2026-10-13 — sha256 edbd8ee5ce61e298d88cdd5ad4355d1406c17707c58124274950e69a323b8b2b
- [S8] Simulation Zone - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/simulation_zone.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-simulation-simulation_zone.html) — captured 2026-10-13 — sha256 1dd410eee5592d3bd7a061e7786da27a9db2840bf82b7207cfda971e6d3c55f2
- [S9] Repeat Zone - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/repeat_zone.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-utilities-repeat_zone.html) — captured 2026-10-13 — sha256 07cb41caf2785cbce9da99b217f75426904048babe9cacc41e17251676ca52dd
- [S10] For Each Geometry Element Zone - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/for_each_geometry_zone.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-utilities-for_each_geometry_zone.html) — captured 2026-10-13 — sha256 4c3717612350e5b81de255ae5fbdd6867ad8ba6b7f03ce37ff227129a370759d
- [S11] Baking - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/baking.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-baking.html) — captured 2026-10-13 — sha256 caa42a19577c059d0c1337b9ea5bc4c8fc7d36dcb090b777178968932caec37e
- [S12] Bake Node - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/geometry/operations/bake.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-geometry-operations-bake.html) — captured 2026-10-13 — sha256 ed105a12277b2c5902e632837b5a164e025098788c842f9381696ef6604145ff
- [S13] Realize Instances Node - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/realize_instances.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-instances-realize_instances.html) — captured 2026-10-13 — sha256 a6d6b88949ee0a7fc35e84ebf4c3259a66dde5c030c1fd19b70217702a2eb3a3
- [S14] Instance on Points Node - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/instance_on_points.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-instances-instance_on_points.html) — captured 2026-10-13 — sha256 0933c1f9f0aad3159c24b9dbee2ae316eb8faa6bfeb286e031c869ef246554ac
- [S15] Distribute Points on Faces - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/point/distribute_points_on_faces.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-point-distribute_points_on_faces.html) — captured 2026-10-13 — sha256 12c2cfcd3a5d54be070694900a3deca19444bd689e59a9265c5053a74db4413d
- [S16] NodeTreeInterface(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-NodeTreeInterface.html) — captured 2026-10-13 — sha256 a34738dcd1314831c50299fc58f1c398aaf407f6c62a3447ed4fe83514e7958c
- [S17] NodesModifier(Modifier) - Blender Python API — https://docs.blender.org/api/current/bpy.types.NodesModifier.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-NodesModifier.html) — captured 2026-10-13 — sha256 7d82eeaa495d958fa6bb504b31641ccf194a6259d8d998807b45293ce9a5cc64
- [S18] GeometrySet - Blender Python API — https://docs.blender.org/api/current/bpy.types.GeometrySet.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-GeometrySet.html) — captured 2026-10-13 — sha256 0cb7c6b8201abaf11b32621917b0dcd323f48486b6aa4101faa4c1d177ca2963
- [S19] Geometry Nodes - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.0/geometry_nodes/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-0-geometry_nodes.html) — captured 2026-10-13 — sha256 d373b4f75272e68967055024bf96ce85925c12cc397923c81c6b456a2248ac08
- [S20] Geometry Nodes - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-2-geometry_nodes.html) — captured 2026-10-13 — sha256 44f611b33c2104ba363ac6a5c1646a49b7e219aa1dc1e76f273b83aa0fe5ab26
- [S21] NodeGeometrySimulationOutputItems(bpy_prop_collection) - Blender Python API — https://docs.blender.org/api/current/bpy.types.NodeGeometrySimulationOutputItems.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-NodeGeometrySimulationOutputItems.html) — captured 2026-10-13 — sha256 99bb8e42c253837071da083bd54bd5df850c68d5aa69734f412b92e3f220a611

---
name: modeling-topology
domain: modeling
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Quad-flow, poles, normals/sharpness attributes, transform application, and headless mesh construction/diagnostics via bmesh and from_pydata.
loads_with: [modifiers, uv-unwrapping, export-interchange]
tags: [mesh, topology, normals, bmesh, from_pydata, manifold, transforms, subdivision]
id: modeling-topology
title: "Mesh Topology, Normals & Headless Mesh Construction"
when: [mesh-topology, bmesh, normals-sharp-edges, from-pydata, mesh-diagnostics, apply-transforms]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Mesh Topology, Normals & Headless Mesh Construction

## Purpose
Gives an agent the data-model facts and headless patterns for building meshes (bmesh, from_pydata), controlling shading via sharp attributes and custom normals, and auditing topology without operators. Version-sensitive API behaviour was re-run on Blender 5.2.0 LTS and checked against the 4.1/5.0/5.2 release notes.

## When to Use / When NOT
- ALLOWED: Building or repairing meshes headlessly with `bmesh.ops.*` and `Mesh.from_pydata` instead of `bpy.ops.mesh.primitive_*`.
- ALLOWED: Setting smooth/sharp shading through `sharp_face` / `sharp_edge` / `custom_normal` attributes on 4.1+.
- ALLOWED: Running a read-only topology audit (manifold, flipped, doubles, poles, signed volume) before modifiers, bakes or export.
- NOT ALLOWED: Choosing a decimation mode or a retopology route — use `mesh-optimization-retopology` instead.
- NOT ALLOWED: Ordering or configuring modifiers (Mirror, Subsurf, Boolean, Bevel) — use `modifiers` instead.
- NOT ALLOWED: UV seams, unwrap and packing — use `uv-unwrapping` instead.
- NOT ALLOWED: Engine-ready export conventions and format options — use `export-interchange` instead.

## Core Knowledge Content
### 1. Mental model

A Blender mesh is four index arrays (`vertices`, `edges`, `loops`, `polygons`) plus a
bag of **generic attributes** on the domains POINT / EDGE / FACE / CORNER. Since 4.1
there is no "auto smooth" flag on the mesh: shading is fully described by the <!-- ease:source S3 anchor="use_auto_smooth is removed" --> <!-- ease:source S1 anchor="Mesh.rna_property.use_auto_smooth" -->
`sharp_face` (FACE, BOOLEAN), `sharp_edge` (EDGE, BOOLEAN) and optional
`custom_normal` (CORNER) attributes, and Blender picks vertex/face/corner normals
automatically from what is present. Topology decisions — quad ratio, edge flow,
pole placement — are not aesthetics: they decide whether Catmull-Clark subdivision
stays smooth, whether a deformer produces pinching, and whether a triangulated
export matches what you saw. The single most common agent failure is building
geometry with `bpy.ops.mesh.primitive_*` and then wondering why the object landed
at the 3D cursor, why it was appended into the wrong mesh, or why a script that
worked interactively does nothing in `--background`: operators read context, the
data API does not. The second most common failure is leaving non-uniform object
scale on and then blaming Bevel/Solidify for "uneven" results — modifiers evaluate
in **object-local space**, and the object matrix is applied afterwards.

### 2. Decision first

| Goal | Topology target | Shading | Triangulate? | Apply scale? |
|---|---|---|---|---|
| Game / realtime | Tri budget first; quads only where they help; n-gons banned | `sharp_edge` + Weighted Normal, or hard-surface split | Yes, at export (or `TRIANGULATE` modifier last) | **Mandatory** <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Character anim / deform | ≥95% quads, loops follow muscle/crease lines, poles off deforming areas | smooth everywhere, no custom normals | No | **Mandatory** <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Subdivision (film / high-end) | 100% quads, poles only at valence-3/valence-5 hubs, creases via `crease_edge` | smooth + creases; never `sharp_edge` for form | No | Yes <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Motion graphics | Whatever survives one Subsurf level; n-gons OK on flat caps | Smooth by Angle 30° | No | Recommended <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Product viz | Dense quads on curved shells, n-gons acceptable on flat planar faces | Smooth by Angle 30–40° + Bevel `harden_normals` | No | Yes <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| 3D print | Watertight manifold, quad/tri mix irrelevant, no zero-area faces | irrelevant | Yes (STL forces it) | **Mandatory** <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |

Decision tree for "should this face be an n-gon or triangle": <!-- ease:source UNVERIFIED reason="editorial rule of thumb; S2 only states quads are preferred for animation and subdivision" -->
1. Will it be subdivided? → No n-gons, no triangles anywhere that shows curvature.
2. Will it deform? → No n-gons; triangles allowed only in rigid pockets.
3. Is it flat and terminal (a cap, a bolt head face, a floor tile)? → n-gon is fine.
4. Is it a shading transition on a hard-surface asset? → triangle is fine, hide it
   inside a bevel or against a sharp edge.

### 3. Rules

R1. Build meshes with `bmesh.ops.create_*` + `bm.to_mesh()` or `mesh.from_pydata()`, never `bpy.ops.mesh.primitive_*`. <!-- ease:source S1 anchor="ops.primitive_cube_add.object_location_at_cursor" --> <!-- ease:source S1 anchor="ops.primitive_cube_add_in_editmode.vertex_count(before,after)" -->
    Why: primitive operators place the object at `scene.cursor.location`, link it into the active layer collection, and — if the active object happens to be in Edit Mode — silently *append* the geometry to the existing mesh instead of creating an object.
    Violation: object at an unexpected location; or vertex count jumps (8 → 16) with no new object in `bpy.data.objects`.

R2. Always run `mesh.validate(verbose=True)` after `from_pydata()` with computed data. <!-- ease:source S1 anchor="from_pydata_duplicate_index.validate(verbose=True).returned" --> <!-- ease:source S1 anchor="Face 0 has duplicate vertex 1" -->
    Why: `from_pydata` does no index checking; degenerate faces/edges survive into the depsgraph and crash or corrupt later modifiers.
    Violation: stderr lines like `geom.mesh | ERROR Face 0 has duplicate vertex 2`, and faces silently disappearing.

R3. Apply scale (and rotation for exports) before adding metric modifiers or exporting. <!-- ease:source S1 anchor="measure.bevel_scale133_distinct_edge_lengths_world" -->
    Why: Bevel width, Solidify thickness, Weld/Array merge thresholds, Remesh voxel size and Shrinkwrap offset are all in **local** units; a non-uniform object matrix rescales them anisotropically afterwards.
    Violation: a Bevel with one `width` produces two different world-space widths (measured: `width=0.2` on a cube with `scale=(1,1,3)` → world chamfer edges of 0.2828 and 0.6325).

R4. Read `obj.matrix_world` only after `bpy.context.view_layer.update()` when you just wrote `obj.scale/location/rotation_*`. <!-- ease:source S1 anchor="matrix_world.scale_immediately_after_set" -->
    Why: `matrix_world` is depsgraph-derived and lazily refreshed.
    Violation: `matrix_world.to_scale()` returns `(1.0, 1.0, 1.0)` immediately after `obj.scale = (1,1,3)`.

R5. Never write `mesh.use_auto_smooth` / `mesh.auto_smooth_angle` / `mesh.calc_normals_split()`. <!-- ease:source S3 anchor="calc_normals_split" --> <!-- ease:source S1 anchor="Mesh.attr.use_auto_smooth.error" -->
    Why: removed in 4.1. Replaced by the `sharp_edge` attribute + `Mesh.corner_normals` (read-only cache).
    Violation: `AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'`.

R6. For "smooth by angle", prefer the destructive data-API call `mesh.shade_smooth(); mesh.set_sharp_from_angle(angle=radians(30))` in headless scripts. <!-- ease:source S1 anchor="Mesh.sharp_edge_after_set_sharp_from_angle" --> <!-- ease:source S8 anchor="set_sharp_from_angle" -->
    Why: it is pure data API, needs no context, no asset library, and works identically in 4.5 and 5.2. The non-destructive "Smooth by Angle" modifier is a Geometry Nodes asset (see R7).
    Violation: none — but the result is baked, not editable as a modifier.

R7. If you need the *non-destructive* Smooth by Angle modifier headlessly, append the node group from the bundled essentials `.blend` yourself — do not rely on `bpy.ops.object.shade_auto_smooth()` on 4.5. <!-- ease:source S10 anchor="This is a geometry nodes asset that is included in the bundled" --> <!-- ease:source S1 anchor="ops.object.shade_auto_smooth.result" --> <!-- ease:source UNVERIFIED reason="the 4.5 --background {'CANCELLED'} behaviour could not be re-run: only 5.2.0 is installed here (5.2.0 returns FINISHED)" -->
    Why: in 4.5 `--background`, the essentials asset library never finishes loading; the operator logs `Warning: Asset loading is unfinished` and returns `{'CANCELLED'}` on every retry. It works in 5.2 background.
    Violation: `{'CANCELLED'}` and `len(obj.modifiers) == 0`.

R8. Detect flipped faces with `edge.is_manifold and not edge.is_contiguous`, and whole-mesh inversion with a signed volume. <!-- ease:source S9 anchor="True when this edge is manifold, between two faces with the same winding" --> <!-- ease:source S7 anchor="manifold edges whose two faces disagree on winding" -->
    Why: `is_contiguous` is False exactly when two manifold neighbours disagree on winding. Signed volume flips sign for a fully inverted closed mesh, which per-edge tests cannot see.
    Violation: renders look black/hollow in EEVEE, or a boolean subtracts the wrong half.

R9. Detect doubles with `bmesh.ops.find_doubles` (read-only), merge with `bmesh.ops.remove_doubles`. <!-- ease:source S1 anchor="bmesh.ops.find_doubles.read_only(verts_before,after)" -->
    Why: `find_doubles` returns a `targetmap` without mutating, so you can report before you destroy.
    Violation: merging first destroys hard edges/UV islands you needed.

R10. Keep an n-gon/triangle census before subdividing. <!-- ease:source S2 anchor="Poles are vertices that are connected to either three, five, or more edges" --> <!-- ease:source UNVERIFIED reason="Catmull-Clark pole behaviour is standard subdivision theory; no Blender page checked states it" -->
    Why: Catmull-Clark converts every n-gon into a valence-n pole and every triangle into a valence-3 pole; those are the pinch points.
    Violation: visible star-shaped pinching in a viewport screenshot after adding `SUBSURF`.

R11. Custom split normals and Subsurf are mutually hostile unless `subsurf.use_custom_normals = True`. <!-- ease:source S6 anchor="Interpolates existing Custom Split Normals" --> <!-- ease:source S1 anchor="subsurf.evaluated_has_custom_normals(use_custom_normals=False)" -->
    Why: subdivision recomputes corner normals; the `custom_normal` corner attribute is by default dropped through the modifier.
    Violation: hard-surface shading "resets" to smooth after enabling Subsurf.

R12. Use `foreach_get`/`foreach_set` for any per-element loop over more than a few thousand elements. <!-- ease:source S1 anchor="foreach_get_vs_loop.speedup_x(loop_time/foreach_time)" -->
    Why: per-element Python attribute access through RNA is much slower than the bulk call (measured on 5.2.0: reading `co` of 203,401 vertices in a Python loop took 8.5x the `foreach_get` time; the earlier "~2 orders of magnitude" figure was not reproduced).
    Violation: slow scripts on large meshes; the gap grows with element count and with what is done per element.

R13. Never `del obj['some_addon_prop']` to reset a `bpy.props`-defined property on 5.x. <!-- ease:source S4 anchor="Properties defined by the bpy.props API are no longer stored in the same container" --> <!-- ease:source S4 anchor="property_unset" -->
    Why: 5.0 split `bpy.props` storage from user Custom Properties; the dict-like path no longer reaches it.
    Violation: `TypeError: bpy_struct.keys(): this type doesn't support IDProperties`, or the delete silently affects nothing. Use `obj.property_unset('some_addon_prop')`.

R14. A mesh can hold at most 8 UV layers; `mesh.uv_layers.new()` returns `None` past that — it does not raise. <!-- ease:source S1 anchor="uv_layers.new[8]" -->
    Why: fixed CustomData layer cap.
    Violation: `AttributeError: 'NoneType' object has no attribute 'uv'` one line later.

### 4. bpy patterns

#### 4.1 Primitives without operators

```python
import bpy, bmesh
from mathutils import Matrix

def make_mesh_object(name, build_fn, collection=None):
    """build_fn(bm) -> None. Returns a linked Object. Headless-safe."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(me)
    bm.free()
    me.validate()                       # cheap insurance
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob

# size == full edge length; cube spans -size/2 .. +size/2
cube = make_mesh_object("Cube", lambda bm: bmesh.ops.create_cube(bm, size=2.0))

# UVs from bmesh.ops require the layer to exist FIRST, otherwise calc_uvs is a no-op
def uv_cube(bm):
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=2.0, calc_uvs=True)

sphere = make_mesh_object("Sphere", lambda bm: bmesh.ops.create_uvsphere(
    bm, u_segments=32, v_segments=16, radius=1.0,
    matrix=Matrix.Identity(4), calc_uvs=False))
```

#### 4.2 `from_pydata` — explicit vertex/face lists

```python
me = bpy.data.meshes.new("Plane")
# 5.2 / 4.5 signature: from_pydata(vertices, edges, faces, shade_flat=True)
me.from_pydata(
    [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
    [],                       # empty -> edges inferred from faces
    [(0, 1, 2, 3)],
    shade_flat=False,         # 4.1+: False == smooth, i.e. no `sharp_face` attribute
)
if me.validate(verbose=True):
    print("from_pydata produced invalid geometry; it was corrected/removed")
me.update()
```

> Verified on 5.2.0: `Mesh.from_pydata(vertices, edges, faces, shade_flat=True)` is the signature; `shade_smooth()` removes the `sharp_face` attribute; `set_sharp_from_angle` creates `sharp_edge`; `edges[i].use_seam` writes `uv_seam`; `normals_split_custom_set_from_vertices` creates `custom_normal`; `flip_normals()` does not handle custom normals. <!-- ease:source S8 anchor="from_pydata ( vertices , edges , faces , shade_flat = True )" --> <!-- ease:source S1 anchor="Mesh.sharp_edge_after_set_sharp_from_angle" --> <!-- ease:source S1 anchor="Mesh.edges.use_seam_writes_uv_seam_attr" --> <!-- ease:source S1 anchor="Mesh.custom_normal_attr" --> <!-- ease:source S8 anchor="does not handle custom normals" -->

#### 4.3 Shading / sharpness — data API only

```python
import math

me.shade_smooth()                                   # removes the `sharp_face` attribute
me.shade_flat()                                     # sets  `sharp_face` = True everywhere
me.set_sharp_from_angle(angle=math.radians(30))     # resets+fills the `sharp_edge` attribute

# per-element access (both spellings work in 4.5 and 5.2)
me.polygons[0].use_smooth = True                    # -> `sharp_face` attribute
me.edges[0].use_edge_sharp = True                   # -> `sharp_edge` attribute
me.edges[0].use_seam     = True                     # -> `uv_seam`    attribute

# bulk, via the attribute API (fast)
import array
sharp = me.attributes.get("sharp_edge") or me.attributes.new("sharp_edge", 'BOOLEAN', 'EDGE')
buf = array.array('b', [0]) * len(me.edges)
sharp.data.foreach_get("value", buf)
```

#### 4.4 Non-destructive Smooth by Angle, portable 4.5 ↔ 5.2, headless

```python
import bpy, os, math

def append_essentials_node_group(name):
    """Find `name` in Blender's bundled asset .blends and append it. Works in --background."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    root = os.path.join(bpy.utils.resource_path('LOCAL'), "datafiles", "assets")
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if not f.endswith(".blend"):
                continue
            path = os.path.join(dirpath, f)
            try:
                with bpy.data.libraries.load(path, link=False) as (src, dst):
                    if name in src.node_groups:
                        dst.node_groups = [name]
            except Exception:
                continue
            if bpy.data.node_groups.get(name):
                return bpy.data.node_groups[name]
    return None
# 4.5: <blender>/4.5/datafiles/assets/geometry_nodes/smooth_by_angle.blend
# 5.2: <blender>/5.2/datafiles/assets/nodes/geometry_nodes_essentials.blend

def set_gn_input(mod, socket_name, value):
    """Version-safe write to a Geometry Nodes modifier input."""
    ident = next(i.identifier for i in mod.node_group.interface.items_tree
                 if getattr(i, "in_out", None) == 'INPUT' and i.name == socket_name)
    if bpy.app.version >= (5, 2, 0):
        # 5.2+: real RNA properties            5.2 python_api release notes
        getattr(mod.properties.inputs, ident).value = value
    else:
        mod[ident] = value                    # 4.x-5.1: custom-property storage
    return ident

def add_smooth_by_angle(obj, angle_rad=math.radians(30.0)):
    ng = append_essentials_node_group("Smooth by Angle")
    if ng is None:
        obj.data.shade_smooth()               # fallback: destructive
        obj.data.set_sharp_from_angle(angle=angle_rad)
        return None
    obj.data.shade_smooth()
    mod = obj.modifiers.new("Smooth by Angle", 'NODES')
    mod.node_group = ng
    set_gn_input(mod, "Angle", angle_rad)     # identifiers observed: Angle=Input_1,
    return mod                                # "Ignore Sharpness"=Socket_1 (do not hardcode)
```

> Corrected 2026-10-13: the version gate in `set_gn_input` above was `(5, 0, 0)`; Geometry Nodes modifier inputs moved to `modifier.properties.inputs.<identifier>` in **5.2**, so 5.0 and 5.1 still use `mod[identifier]` (`modifiers` already gated on `(5, 2, 0)`). On 5.2.0 the bundled asset lives at `<blender>/5.2/datafiles/assets/nodes/geometry_nodes_essentials.blend`, contains `Smooth by Angle`, and its inputs are `Mesh=Input_0`, `Angle=Input_1`, `Ignore Sharpness=Socket_1`. <!-- ease:source S5 anchor="modifier now has proper RNA properties" --> <!-- ease:source S1 anchor="mod.properties.inputs.set" --> <!-- ease:source S1 anchor="SmoothByAngle.input_identifiers" -->

#### 4.5 Custom split normals

```python
# read-only cache; length == len(mesh.loops)
n0 = me.corner_normals[0].vector
print(me.has_custom_normals)                  # False until you write them

me.normals_split_custom_set([(0.0, 0.0, 1.0)] * len(me.loops))   # per-corner
# or per-vertex, broadcast to corners:
me.normals_split_custom_set_from_vertices([(0.0, 0.0, 1.0)] * len(me.vertices))
# zero-vectors mean "keep the automatically computed normal"
# creates a CORNER float-vector attribute named `custom_normal`
```

#### 4.6 Topology audit (read-only, headless)

```python
import bmesh
from collections import Counter

def mesh_report(obj, merge_dist=1e-5):
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    valence = Counter(len(v.link_edges) for v in bm.verts)
    r = {
        "verts": len(bm.verts), "faces": len(bm.faces),
        "tris":  sum(1 for f in bm.faces if len(f.verts) == 3),
        "quads": sum(1 for f in bm.faces if len(f.verts) == 4),
        "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
        "nonmanifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "boundary_edges":    sum(1 for e in bm.edges if e.is_boundary),
        "flipped_edges":     sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous),
        "wire_edges":        sum(1 for e in bm.edges if e.is_wire),
        "loose_verts":       sum(1 for v in bm.verts if not v.link_edges),
        "zero_area_faces":   sum(1 for f in bm.faces if f.calc_area() < 1e-9),
        "doubles":           len(bmesh.ops.find_doubles(bm, verts=bm.verts,
                                                        dist=merge_dist)["targetmap"]),
        "poles_3":           valence.get(3, 0),
        "poles_5plus":       sum(n for k, n in valence.items() if k >= 5),
    }
    r["quad_ratio"] = r["quads"] / max(1, r["faces"])
    bm.free()
    return r

def signed_volume(obj):
    """>0 = normals point outward, <0 = whole mesh inverted. Closed meshes only."""
    me = obj.data
    me.calc_loop_triangles()
    return sum(me.vertices[t.vertices[0]].co.dot(
                   me.vertices[t.vertices[1]].co.cross(me.vertices[t.vertices[2]].co))
               for t in me.loop_triangles) / 6.0
```

> Verified on 5.2.0: `bmesh.ops.holes_fill(sides=0)` fills a 4-edge hole while `sides=3` leaves it open; `bmesh.ops.find_doubles` returns `{'targetmap': ...}` and does not mutate the BMesh; `bmesh.ops.create_cube(size=2.0)` spans -1..+1. <!-- ease:source S1 anchor="bmesh.ops.holes_fill(sides=0).faces_for_4_edge_hole" --> <!-- ease:source S11 anchor="holes_fill" --> <!-- ease:source S11 anchor="find_doubles" --> <!-- ease:source S1 anchor="bmesh.ops.find_doubles.keys" --> <!-- ease:source S1 anchor="bmesh.ops.create_cube(size=2.0).x_extent" -->

#### 4.7 Repair (destructive), no operators

```python
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)      # "outside" winding
bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)      # sides=0 -> any hole size
bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(me); bm.free()
me.update()

me.flip_normals()      # invert winding of every polygon; does NOT fix custom normals
```

#### 4.8 Transforms

```python
import bpy

def is_uniform_scale(obj, eps=1e-5):
    bpy.context.view_layer.update()                 # R4
    s = obj.matrix_world.to_scale()
    return (max(s) - min(s)) < eps

def apply_transform(obj, location=False, rotation=True, scale=True):
    """transform_apply needs an active+selected object; no window needed."""
    vl = bpy.context.view_layer
    prev = vl.objects.active
    vl.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
    vl.objects.active = prev

# Pure data-API alternative (no operator, no selection, ignores parenting):
def bake_scale_into_mesh(obj):
    from mathutils import Matrix
    s = obj.scale.copy()
    obj.data.transform(Matrix.Diagonal(s).to_4x4())
    obj.scale = (1.0, 1.0, 1.0)
    obj.data.update()
    if s.x * s.y * s.z < 0.0:                       # negative scale inverts winding
        obj.data.flip_normals()
```

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'` | 4.1 removed Auto Smooth from the mesh | `mesh.shade_smooth(); mesh.set_sharp_from_angle(angle=...)` or the Smooth by Angle GN modifier <!-- ease:source S3 anchor="use_auto_smooth is removed" --> |
| `TypeError: bpy_struct.keys(): this type doesn't support IDProperties` on a Geometry Nodes modifier | 5.0 split `bpy.props` storage from Custom Properties; 5.2 moved GN inputs to real RNA | `getattr(mod.properties.inputs, identifier).value` (5.x) / `mod[identifier]` (4.x) <!-- ease:source S1 anchor="mod.id_prop_access" --> |
| `bpy.ops.object.shade_auto_smooth()` → `{'CANCELLED'}` + `Warning: Asset loading is unfinished` | Essentials asset library never loads in 4.5 `--background` | Append `Smooth by Angle` from `datafiles/assets/**.blend` (§4.4), or use `set_sharp_from_angle` <!-- ease:source UNVERIFIED reason="4.5 background behaviour not re-run; on 5.2.0 the operator returns FINISHED (see R7)" --> |
| stderr `geom.mesh | ERROR Face 0 has duplicate vertex 2` and the face vanishes | `from_pydata` fed an index list with repeats / out-of-range indices | Deduplicate the index tuples, then `mesh.validate(verbose=True)` <!-- ease:source S1 anchor="Face 0 has duplicate vertex 1" --> |
| Object renders black or inside-out in a viewport screenshot | Whole-mesh inverted winding (e.g. after `mesh.transform` with a negative-determinant matrix) | `signed_volume(obj) < 0` → `mesh.flip_normals()` |
| Patchy black facets, some faces lit correctly | Individual faces reversed | `sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous) > 0` → `bmesh.ops.recalc_face_normals` |
| Bevel/Solidify visibly thicker on one axis | Non-uniform object scale | `is_uniform_scale(obj)` → apply scale before adding the modifier |
| `AttributeError: 'NoneType' object has no attribute 'uv'` after `uv_layers.new()` | 9th UV layer requested; `new()` returned `None` | Cap at 8; reuse `mesh.uv_layers.get(name)` first |
| Vertex count doubled, no new object appeared | `bpy.ops.mesh.primitive_*_add` ran while an object was in Edit Mode | Build with `bmesh.ops.create_*` (§4.1) |
| Star-shaped pinch after adding `SUBSURF` | n-gons / triangles subdivided into high-valence poles | `mesh_report()["ngons"]` and `["poles_5plus"]`; retopologise or move the pole |
| Hard edges disappear after enabling Subsurf | Custom normals dropped by subdivision | `subsurf.use_custom_normals = True`, or drive sharpness with `sharp_edge` instead <!-- ease:source S6 anchor="Interpolates existing Custom Split Normals" --> |
| `matrix_world.to_scale()` still `(1,1,1)` right after setting `obj.scale` | Depsgraph not flushed | `bpy.context.view_layer.update()` |

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Target quad ratio (`mesh_report()["quad_ratio"]`) | ≥0.5 (pre-triangulation) | ≥0.95 | ≥0.7 | ≥0.8 | irrelevant <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| n-gons allowed | 0 | 0 | flat caps only | flat faces only | 0 (STL triangulates) <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| `set_sharp_from_angle(angle=)` | radians(45) | n/a (all smooth) | radians(30) | radians(35) | n/a <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Merge distance (`remove_doubles dist=`) | 1e-4 | 1e-5 | 1e-4 | 1e-5 | 1e-6 <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Subsurf `levels` / `render_levels` | 0 / 0 (bake instead) | 1 / 2 | 1 / 2 | 2 / 3 | 2 / 3 then apply <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Subsurf `use_limit_surface` | — | True | True | True | **False** (keeps volume closer to cage) <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Custom split normals | Yes (bake from high-poly) | No | No | Only via Bevel `harden_normals` | No <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| `TRIANGULATE` modifier | Yes, last in stack | No | No | No | Yes <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Apply rotation on export | Yes | Yes | Optional | Yes | Yes <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Scene unit scale | 1.0 (m) | 1.0 (m) | 1.0 | 1.0 | 0.001 (mm workflow) <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |
| Zero-area face tolerance | 1e-8 | 1e-8 | 1e-8 | 1e-9 | 0 (must be none) <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" --> |

### 7. Verification checklist

- [ ] `assert not mesh.validate(verbose=True)` — mesh had no invalid indices to correct.
- [ ] `r = mesh_report(ob); assert r["nonmanifold_edges"] == 0` — closed, printable/booleanable shell.
- [ ] `assert r["flipped_edges"] == 0` — all manifold neighbours share winding.
- [ ] `assert signed_volume(ob) > 0` — normals point outward on a closed mesh.
- [ ] `assert r["doubles"] == 0` — no coincident vertices at the chosen tolerance.
- [ ] `assert r["loose_verts"] == 0 and r["wire_edges"] == 0` — no stray geometry that exporters silently drop.
- [ ] `assert r["zero_area_faces"] == 0` — nothing that produces NaN normals.
- [ ] `assert r["ngons"] == 0` before adding a `SUBSURF` modifier.
- [ ] `assert is_uniform_scale(ob)` before adding `BEVEL`/`SOLIDIFY`/`REMESH`/`WELD`.
- [ ] `assert tuple(round(v, 6) for v in ob.scale) == (1.0, 1.0, 1.0)` before export.
- [ ] `assert len(mesh.corner_normals) == len(mesh.loops)` — normal cache is populated.
- [ ] `assert ("custom_normal" in mesh.attributes) == mesh.has_custom_normals` — custom normal state is what you think it is.
- [ ] Viewport screenshot from two opposing angles: no black facets, no star-pinching at poles.

### 8. Original reference list (pre-UKMC; the numbered Sources section at the end of this file is authoritative)

- [Blender 5.2 Python API — `bpy.types.Mesh`](https://docs.blender.org/api/current/bpy.types.Mesh.html) (`from_pydata`, `shade_smooth`, `shade_flat`, `set_sharp_from_angle`, `split_faces`, `flip_normals`, `validate`, `corner_normals`, `has_custom_normals`, `normals_split_custom_set*`, `transform`)
- [Blender 5.2 Python API — `bmesh.ops`](https://docs.blender.org/api/current/bmesh.ops.html) (`create_cube`, `create_uvsphere`, `remove_doubles`, `find_doubles`, `recalc_face_normals`, `reverse_faces`, `dissolve_degenerate`, `holes_fill`, `triangulate`)
- [Blender 5.2 Python API — `bmesh.types`](https://docs.blender.org/api/current/bmesh.types.html) (`BMEdge.is_manifold` / `is_boundary` / `is_contiguous` / `is_wire` / `seam` / `smooth`)
- [Blender 5.2 Python API — `bpy.ops.object`](https://docs.blender.org/api/current/bpy.ops.object.html) (`shade_smooth`, `shade_flat`, `shade_smooth_by_angle`, `shade_auto_smooth`, `transform_apply`)
- [Blender 4.1 release notes — Modeling: Auto Smooth replaced by a modifier node group asset](https://developer.blender.org/docs/release_notes/4.1/modeling/)
- [Blender 4.1 release notes — Python API: `use_auto_smooth`, `auto_smooth_angle`, `calc_normals_split` removed; `Mesh.corner_normals` added](https://developer.blender.org/docs/release_notes/4.1/python_api/)
- [Blender 5.0 release notes — Python API: `bpy.props` storage split, `property_unset()`, `get_transform`/`set_transform`, bundled modules made private](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.2 release notes — Python API: Geometry Nodes modifier inputs moved to `modifier.properties.inputs.<identifier>`](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- Empirically verified against local `blender-5.2.0-linux-x64` and `blender-4.5.9-linux-x64` in `--background --factory-startup`: measured bevel-width distortion under `scale=(1,1,3)`; `shade_auto_smooth` `{'CANCELLED'}` on 4.5 background; UV-layer cap of 8; `Smooth by Angle` socket identifiers `Input_1` / `Socket_1`; `mesh.validate` stderr text.
- `[UNVERIFIED]` Recommended numeric values in §6 (quad ratios, merge distances, sharp angles) are conventional pipeline targets, not values published by Blender; treat them as starting points, not API facts.

## Failure Modes (Mandatory)
- **`AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'`** — cause: Auto Smooth was removed from Mesh in 4.1 (also `auto_smooth_angle`, `calc_normals_split`) — fix: `mesh.shade_smooth(); mesh.set_sharp_from_angle(angle=...)` or the Smooth by Angle modifier asset. <!-- ease:source S3 anchor="use_auto_smooth is removed" --> <!-- ease:source S1 anchor="Mesh.attr.use_auto_smooth.error" -->
- **Geometry Nodes input write raises `TypeError: this type doesn't support IDProperties` (5.2)** — cause: modifier inputs became RNA properties in 5.2; `mod[identifier]` is the 4.x-5.1 form — fix: gate on `bpy.app.version >= (5, 2, 0)` and use `getattr(mod.properties.inputs, identifier).value`. <!-- ease:source S5 anchor="modifier now has proper RNA properties" --> <!-- ease:source S1 anchor="mod.id_prop_access" -->
- **Vertex count doubles and no new object appears** — cause: `bpy.ops.mesh.primitive_*_add` ran while the object was in Edit Mode and appended to the edit mesh (measured 8 -> 16 vertices); out of Edit Mode the same operator drops the object at the 3D cursor — fix: build with `bmesh.ops.create_*` plus `bm.to_mesh()`. <!-- ease:source S1 anchor="ops.primitive_cube_add_in_editmode.vertex_count(before,after)" -->
- **Bevel or Solidify is thicker on one axis** — cause: non-uniform object scale; modifiers evaluate in local units (measured: `width=0.2` on `scale=(1,1,3)` gave world chamfer lengths 0.2828 and 0.6325) — fix: apply scale before adding the modifier. <!-- ease:source S1 anchor="measure.bevel_scale133_distinct_edge_lengths_world" -->
- **`matrix_world.to_scale()` is still `(1,1,1)` right after setting `obj.scale`** — cause: depsgraph not flushed — fix: `bpy.context.view_layer.update()` before reading `matrix_world`. <!-- ease:source S1 anchor="matrix_world.scale_after_view_layer_update" -->
- **Hard-surface shading resets to smooth after adding Subsurf** — cause: Subsurf drops custom split normals unless `use_custom_normals` is enabled (measured: False by default; evaluated mesh had no custom normals until it was set True) — fix: `subsurf.use_custom_normals = True` or drive sharpness with `sharp_edge`. <!-- ease:source S6 anchor="Use Custom Normals" --> <!-- ease:source S1 anchor="subsurf.evaluated_has_custom_normals(use_custom_normals=True)" -->
- **`mesh.uv_layers.new()` returns `None` and the next line raises `AttributeError`** — cause: a mesh holds at most 8 UV layers and the 9th request does not raise — fix: reuse `mesh.uv_layers.get(name)` and cap at 8. <!-- ease:source S1 anchor="uv_layers.count_after_9_requests" -->

## Sources
- [S1] Local Blender 5.2.0 LTS runtime probe (script: knowledge/_evidence/kb-261013/w2-bpy-52-facts.py) — knowledge/_evidence/kb-261013/w2-bpy-52-facts.txt — captured 2026-10-13 — sha256 2411832c2522b533b8523ee16511805eb0d8a75bc2f2b213663bc0f77f4667af
- [S2] Mesh Structure - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/meshes/structure.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-meshes-structure.html) — captured 2026-10-13 — sha256 87b7221bbd13bdc8b9f2138dc07d7ad9ef92ee2eea84dd5c98005fbd1c18371d
- [S3] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/4.1/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-4-1-python_api.html) — captured 2026-10-13 — sha256 2db69e9f92207f49d043f6e478d9bc05b1588dffe6fc4b409256e5ecb98d979d
- [S4] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-0-python_api.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S5] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.2/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-2-python_api.html) — captured 2026-10-13 — sha256 613fac2fa63a96155d40c761571e1a7407c709926ebc2eff96f846343bb1b086
- [S6] Subdivision Surface Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-generate-subdivision_surface.html) — captured 2026-10-13 — sha256 5d6994d638624e2dd43edb98c2fde53e68e70ef62abbac7e71578b3f0049514b
- [S7] Repo: production gate topology checks — scripts/production_gate/topology.py — captured 2026-10-13 — sha256 8c3b638fc3599f41f6b67b71039d400dc1b88c16d4fd24baa0c2c354888843a4
- [S8] Mesh(ID) - Blender Python API — https://docs.blender.org/api/current/bpy.types.Mesh.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-Mesh.html) — captured 2026-10-13 — sha256 d11d92ac5a01dcff4d935311ab52fad3b53743d398c098fa7929a5fa008af733
- [S9] BMesh Types (bmesh.types) - Blender Python API — https://docs.blender.org/api/current/bmesh.types.html (frozen: knowledge/_evidence/kb-261013/w2-api-bmesh-types.html) — captured 2026-10-13 — sha256 38bc14776291a14763af56ce8565b300c5b7dbd348a3382f8ddcad599371294f
- [S10] Smooth By Angle Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/smooth_by_angle.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-normals-smooth_by_angle.html) — captured 2026-10-13 — sha256 762b5f956cb2a7882cd0bb2f1cf879d190592d13985f23db1e70f3c217595203
- [S11] BMesh Operators (bmesh.ops) - Blender Python API — https://docs.blender.org/api/current/bmesh.ops.html (frozen: knowledge/_evidence/kb-261013/w2-api-bmesh-ops.html) — captured 2026-10-13 — sha256 45f98573a8ee18729eadeb8a5bcc784df770d34ebfe443953f27ebb3932a8555

---
name: uv-unwrapping
domain: modeling
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Seams, unwrap methods, packing margin math, texel density, UDIMs, multi-UV layouts, and the headless operator-context patterns UV work actually requires.
loads_with: [modeling-topology, modifiers, texturing-baking, export-interchange]
tags: [uv, unwrap, seams, packing, texel-density, udim, lightmap, temp-override, headless]
id: uv-unwrapping
title: "UV Unwrapping, Packing & Texel Density"
when: [uv-unwrap, uv-packing, texel-density, udim, lightmap-uv, headless-uv-operators]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# UV Unwrapping, Packing & Texel Density

## Purpose
Covers seams, unwrap methods, margin math, texel density, UDIMs and multi-UV layouts, plus the operator-context patterns UV work needs when Blender runs headless. Operator behaviour was re-run on Blender 5.2.0 LTS (macOS); three earlier claims were corrected.

## When to Use / When NOT
- ALLOWED: Unwrapping and packing UVs headlessly (`bpy.ops.uv.unwrap`, `pack_islands`, `average_islands_scale`, `smart_project`) with a UV layer present.
- ALLOWED: Reading and writing UV coordinates in bulk through `uv_layer.uv[...].vector` / `foreach_get`, computing texel density and UDIM tiles.
- ALLOWED: Choosing a margin in pixels with `margin_method='FRACTION'` and auditing range, overlap and layer flags.
- NOT ALLOWED: Baking maps, bake margins and cage setup — use `texturing-baking` instead.
- NOT ALLOWED: Mesh cleanup, normals and non-manifold repair before unwrapping — use `modeling-topology` instead.
- NOT ALLOWED: Game-engine texel-density tiers and LOD/Nanite decisions — use `game-asset-pipeline-low-to-aaa` instead.
- NOT ALLOWED: Calling `bpy.ops.uv.stitch()` in `--background` — it crashes Blender (measured); weld UVs with bmesh instead.

## Core Knowledge Content
### 1. Mental model

A UV map is a **CORNER-domain float2 attribute**: one (u, v) per *loop*, not per
vertex. Two loops sharing a vertex can hold different UVs — that is exactly what a
seam is. Blender's mesh stores up to 8 such layers (`mesh.uv_layers`), one flagged
`active` (what edit-mode operators write) and one flagged `active_render` (what the
renderer and bakers read when a shader's UV Map node is empty). Unwrapping itself is
a flattening solve: you cut the surface with seams so it can be developed into the
plane with bounded distortion, then you pack the resulting islands into 0..1 (or into
UDIM tiles). Everything downstream — texel density, bake bleed, lightmap quality —
is arithmetic on the island areas and the margin you chose. The trap for an agent
is that essentially all unwrapping lives in `bpy.ops.uv.*`, so it looks like it
cannot run headless. It mostly can: in `--background`, `bpy.context.window_manager.windows[0].screen`
still contains a real `VIEW_3D` area (measured on 5.2.0 macOS `--factory-startup -b`: the window's active screen `Layout` has areas `PROPERTIES, OUTLINER, DOPESHEET_EDITOR, VIEW_3D` — **no `IMAGE_EDITOR`**; other workspaces (Compositing, Rendering, Shading, Texture Paint, UV Editing) do contain one, but only some of them accept a UV override — see §4.4), so `temp_override` works for 3D-view operators; for UV-editor operators create the area by changing an existing area's `type` first (§4.4). <!-- ease:source S2 anchor="workspaces that contain an IMAGE_EDITOR area" --> <!-- ease:source S2 anchor="areas_in_background_screen" -->
The genuine exceptions are few and named in §5. The other trap is Blender 4.5's
default `use_uv_select_sync = False`: `unwrap()` returns `{'FINISHED'}` and writes
UVs of `(0, 0)` because nothing was selected *in UV space*.

### 2. Decision first

| Use case | Method | Packing | Texel density target | UV layers |
|---|---|---|---|---|
| Game / realtime, unique texture | `unwrap(method='ANGLE_BASED')` with hand/heuristic seams | `pack_islands(margin_method='FRACTION', margin=4/tex_size)` | 512–1024 px/m (hero: 2048) | UVMap (+ Lightmap) <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Game, tiling / trim sheet | `cube_project` or `follow_active_quads`, then snap to trim rows | none (deliberately overlapping / out of 0..1) | matched to the trim atlas | UVMap <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Lightmap / second channel | `smart_project(angle_limit=radians(66), island_margin=...)` | `pack_islands` with a large margin | 32–128 px/m | second layer, no overlaps ever <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Character (film) | `unwrap(method='MINIMUM_STRETCH', iterations=30)` | UDIM, one region per body part | 1024–2048 px/m per tile | UVMap <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Product viz | `unwrap(method='CONFORMAL')` (angle-preserving) | `pack_islands` `shape_method='CONCAVE'` | 2048–4096 px/m | UVMap <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Motion graphics | `smart_project` and move on | default | irrelevant | UVMap <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| Baking source (high→low) | must match the low-poly cage's layer exactly | `margin >= 8px` at bake resolution | — | UVMap only <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" --> |
| 3D print | no UVs needed | — | — | none |

**Angle Based vs Conformal vs Minimum Stretch**

| Method | Enum | Optimises | Use when |
|---|---|---|---|
| Angle Based (ABF) | `'ANGLE_BASED'` | angle preservation, decent area | general-purpose; the API docs say it usually gives better results than Conformal but is somewhat slower; organic shells <!-- ease:source S4 anchor="Angle Based usually gives better results than Conformal" --> |
| Conformal (LSCM) | `'CONFORMAL'` | conformality (local angles), fast | few seams, mostly-developable surfaces; **this is the `uv.unwrap` operator default on 5.2.0** <!-- ease:source S1 anchor="uv.unwrap.method.default" --> |
| Minimum Stretch (SLIM) | `'MINIMUM_STRETCH'` | area+angle stretch, iterative | characters, high-distortion shells; costs `iterations` (default 10, use 25–50) <!-- ease:source S4 anchor="iterations = 10" --> <!-- ease:source UNVERIFIED reason="the ABF/LSCM/SLIM acronyms and the 25-50 iteration advice are not stated in the API or manual pages checked" --> |

**Overlapping UVs**: fine (and often required) for tiling materials, trim sheets and <!-- ease:source UNVERIFIED reason="workflow convention; follows from how bakers write pixels but no vendor source checked" -->
mirrored/instanced geometry sharing one texture. **Fatal** for: texture baking
(overlaps write over each other), lightmaps/AO maps, and any per-pixel unique data
(ID masks, vertex-baked curvature). If the asset will be baked, one UV set must be
non-overlapping.

### 3. Rules

R1. Before any `bpy.ops.uv.*` call: object must be **active + selected**, in **Edit Mode**, with mesh elements selected **and** UV elements selected. <!-- ease:source S6 anchor="Sync selection is now enabled by default" --> <!-- ease:source UNVERIFIED reason="the 4.5 symptom (every UV (0,0) with sync off) cannot be re-run: only 5.2.0 is installed" -->
    Why: UV operators poll on the edit-mesh; the flatteners iterate the UV selection.
    Violation: `{'FINISHED'}` with every UV written as `(0.0, 0.0)`.

R2. Always call `bpy.ops.uv.select_all(action='SELECT')` after entering Edit Mode, even on 5.2. <!-- ease:source S6 anchor="Sync selection is now enabled by default" --> <!-- ease:source S2 anchor="uv.select_all.poll in Edit Mode after uv_layers.new()" --> <!-- ease:source S2 anchor="uv.select_all.poll in Edit Mode when the mesh has NO UV layer" -->
    Why: 5.0 turned `use_uv_select_sync` on by default, but 4.5 has it off, and a loaded `.blend` can have either. `uv.select_all` is correct in both. Its poll only succeeds once the mesh **has a UV layer** (measured on 5.2.0: False without one, True after `uv_layers.new()`), so create the layer first as `uv_edit_begin` does.
    Violation on 4.5: `pack_islands` and `average_islands_scale` return `{'CANCELLED'}`; `unwrap` produces zero UVs.

R3. All UV operators write to `mesh.uv_layers.active`. Set it explicitly before every unwrap. <!-- ease:source S2 anchor="two layers after new(): (name, active, active_render)" -->
    Why: operators write to the active layer. *(Corrected 2026-10-13: on 5.2.0 `uv_layers.new()` did NOT change the active layer — after creating `UVMap` then `Lightmap`, `UVMap` stayed `active` and `active_render` — so an unwrap after adding a lightmap layer targets the FIRST layer unless you switch.)*
    Violation: the "diffuse" UVs come out as a lightmap-style atlas.

R4. Set `active_render` on the layer the shader/baker should read; `active` and `active_render` are independent flags. <!-- ease:source S5 anchor="Set the UV map as active for rendering" -->
    Why: renderers use `active_render`; edit-mode ops use `active`.
    Violation: correct-looking UV editor, wrong texture placement in a render.

R5. Use `margin_method='FRACTION'` when you care about pixels. <!-- ease:source S4 anchor="FRACTION Fraction" --> <!-- ease:source S1 anchor="uv.pack_islands[FRACTION].margin=4/1024 on 1024px" -->
    Why: `FRACTION` is a precise fraction of the final UV output — measured: `margin=4/1024` gives exactly 4 px of border and 8 px between islands at 1024². `'ADD'` and `'SCALED'` scale with the pre-pack UV size and are not predictable.
    Violation: bake bleed across islands despite "setting a margin".

R6. Margin budget: `margin = desired_border_px / texture_size`. Island-to-island gap is `2 × margin`. <!-- ease:source S1 anchor="uv.pack_islands[FRACTION].margin=4/1024 on 1024px" -->
    Why: each island gets its own margin band; two adjacent islands contribute one each.
    Violation: mipmapping bleeds neighbouring islands at level 2–3 because 2 px of gap was requested for a 4-mip chain.

R7. Compute texel density as `sqrt(uv_area / world_area) * texture_size`, area-weighted over triangles, using **world-space** triangle areas. <!-- ease:source S2 anchor="texel_density(2 m cube, 0.25x0.25 per-face UVs, 2048 px)" -->
    Why: `uv_area/world_area` is the squared linear ratio; object scale must be in the measurement or the number is meaningless.
    Violation: reporting 1024 px/m for an object with `scale=(2,2,2)` whose real density is 512 px/m.

R8. Equalise density with `bpy.ops.uv.average_islands_scale()` *before* packing, not after. <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" -->
    Why: packing scales the whole layout to fill 0..1; averaging afterwards re-breaks the packing.
    Violation: islands overlap or spill outside 0..1 after the final step.

R9. Address a UDIM tile as `1001 + floor(u) + 10*floor(v)`; `u` must stay in `[0, 10)`. <!-- ease:source S8 anchor="The overall UDIM array is ten tiles wide" --> <!-- ease:source S2 anchor="udim_tile(10.5,0.5)" -->
    Why: the UDIM convention is a 10-wide grid starting at 1001.
    Violation: `u = 10.5` maps to 1011 (row 2, column 1), silently colliding with the second row.

R10. Read/write UVs as `uv_layer.uv[loop_index].vector` on 5.x; `uv_layer.data[loop_index].uv` still works but is documented as deprecated. <!-- ease:source S5 anchor="Deprecated, use" --> <!-- ease:source S2 anchor="legacy uv.data[i].uv still readable" -->
    Why: 5.x exposes UVs as a plain float2 attribute (`Float2AttributeValue.vector`); `.data` is the legacy `MeshUVLoop` wrapper.
    Violation: none yet — but `MeshUVLoopLayer.vertex_selection` / `.edge_selection` **were** removed in 5.0, so any selection code written against `.data` siblings breaks. <!-- ease:source S7 anchor="The following UV selection properties have been removed" --> <!-- ease:source S2 anchor="MeshUVLoopLayer has vertex_selection" -->

R11. Use `foreach_get`/`foreach_set` with the property name `"vector"` for bulk UV I/O. <!-- ease:source S2 anchor="foreach_set vector halves coordinates" --> <!-- ease:source S1 anchor="foreach_get_vs_loop.speedup_x(loop_time/foreach_time)" -->
    Why: bulk access is substantially faster than per-loop Python access (measured on 5.2.0 for vertex `co` over 203,401 elements: 8.5x; not measured for UV layers; the earlier "~100x" was not reproduced); the buffer is flat `[u0,v0,u1,v1,…]` of length `2 * len(mesh.loops)`.
    Violation: slow scripts on large meshes.

R12. Mark seams via the data API (`mesh.edges[i].use_seam` / bmesh `edge.seam`), not `bpy.ops.mesh.mark_seam`. <!-- ease:source S9 anchor="These cuts are the same as seams" --> <!-- ease:source S1 anchor="Mesh.edges.use_seam_writes_uv_seam_attr" -->
    Why: no context, no mode switch, works on `bpy.data` meshes directly. Both spellings write the `uv_seam` EDGE attribute.
    Violation: needless Edit Mode round-trips, and lost selection state.

R13. `mesh.uv_layers.new()` returns `None` past 8 layers instead of raising. <!-- ease:source S1 anchor="uv_layers.new[8]" -->
    Why: fixed CustomData layer cap.
    Violation: `AttributeError: 'NoneType' object has no attribute 'uv'` on the next line.

R14. `bpy.ops.uv.stitch()` **cannot** be run in `--background` — it segfaults Blender, with or without a full context override. <!-- ease:source S3 anchor="exit_code: 139" --> <!-- ease:source UNVERIFIED reason="the 'with a full context override' variant was not re-run; only the no-override call was probed" -->
    Why: it drives a modal 2D-view interaction; no workaround exists from Python.
    Violation: process dies (measured on 5.2.0 macOS: exit code 139), prints `Writing: <tempdir>/blender.crash.txt`, no traceback. Weld the UVs with your own `bmesh` code instead.

### 4. bpy patterns

#### 4.1 Headless preflight — the boilerplate every UV script needs

```python
import bpy, math

def uv_edit_begin(obj, uv_name="UVMap"):
    """Leaves obj in EDIT mode with everything selected. Headless-safe."""
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    vl.objects.active = obj
    obj.select_set(True)
    me = obj.data
    layer = me.uv_layers.get(uv_name) or me.uv_layers.new(name=uv_name)
    if layer is None:
        raise RuntimeError("mesh already has 8 UV layers")
    me.uv_layers.active = layer                 # R3
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')      # R2 — required on 4.5, harmless on 5.2
    return layer

def uv_edit_end():
    bpy.ops.object.mode_set(mode='OBJECT')
```

> Measured on 5.2.0: `uv_edit_begin` returns a layer reference captured *before* `mode_set('EDIT')`; reading `.name` on it afterwards returned an empty string, so re-fetch `mesh.uv_layers.active` after any mode switch instead of keeping the reference. <!-- ease:source S2 anchor="documented uv_edit_begin layer reference name after Edit Mode entry" -->

#### 4.2 Seams from the data API

```python
import bmesh, math

def mark_seams_by_angle(obj, angle=math.radians(66.0), keep_existing=False):
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    for e in bm.edges:
        if not keep_existing:
            e.seam = False
        if e.is_boundary:
            e.seam = True                                   # open borders are always seams
        elif e.is_manifold and e.calc_face_angle(0.0) > angle:
            e.seam = True
    bm.to_mesh(me); bm.free(); me.update()

# object-mode, no bmesh:
for e in obj.data.edges:
    e.use_seam = False
obj.data.edges[17].use_seam = True          # writes the `uv_seam` EDGE bool attribute

# reverse direction: derive seams from an existing UV layout (edit mode)
# bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
```

#### 4.3 Unwrap + equalise + pack, headless

```python
def unwrap_and_pack(obj, texture_size=2048, border_px=4, method='ANGLE_BASED',
                    uv_name="UVMap"):
    uv_edit_begin(obj, uv_name)
    try:
        bpy.ops.uv.unwrap(
            method=method,            # 'ANGLE_BASED' | 'CONFORMAL' | 'MINIMUM_STRETCH'
            iterations=30,            # only used by MINIMUM_STRETCH
            fill_holes=False,
            correct_aspect=True,
            margin_method='FRACTION',
            margin=border_px / texture_size,
        )
        bpy.ops.uv.average_islands_scale(scale_uv=False, shear=False)   # R8
        bpy.ops.uv.pack_islands(
            udim_source='CLOSEST_UDIM',   # 5.2 also has 'ORIGINAL_AABB', 'CUSTOM_REGION'
            rotate=True, rotate_method='ANY',
            scale=True, merge_overlap=False,
            margin_method='FRACTION', margin=border_px / texture_size,   # R5/R6
            shape_method='CONCAVE',       # 'CONVEX' / 'AABB' are faster, waste space
        )
    finally:
        uv_edit_end()

def smart_project(obj, texture_size=1024, border_px=8, uv_name="Lightmap"):
    uv_edit_begin(obj, uv_name)
    try:
        bpy.ops.uv.smart_project(
            angle_limit=math.radians(66.0),
            island_margin=border_px / texture_size,
            margin_method='FRACTION',
            rotate_method='AXIS_ALIGNED_Y',
            area_weight=0.0, correct_aspect=True, scale_to_bounds=False,
        )
    finally:
        uv_edit_end()
```

#### 4.4 Operators that DO need a fabricated context

```python
def uv_editor_context():
    """A context override valid for SpaceImage-polling UV operators, in --background.
    Measured on 5.2.0 (macOS): the window's ACTIVE screen ("Layout") has no IMAGE_EDITOR, but other
    workspaces do (Compositing, Rendering, Shading, Texture Paint, UV Editing) and only some of them
    pass the operator polls. Use the active screen: retype a spare area there, then set mode 'UV'."""
    win = bpy.context.window_manager.windows[0]
    screen = win.screen
    area = next((a for a in screen.areas if a.type == 'IMAGE_EDITOR'), None)
    if area is None:
        area = next(a for a in screen.areas if a.type in ('DOPESHEET_EDITOR', 'OUTLINER'))
        area.type = 'IMAGE_EDITOR'
    space = area.spaces.active
    space.mode = 'UV'              # REQUIRED: the poll checks SpaceImage.mode
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return dict(window=win, screen=screen, area=area, region=region, space_data=space)

def view3d_context():
    win = bpy.context.window_manager.windows[0]
    for ws in bpy.data.workspaces:
        for screen in ws.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                    if region:
                        return dict(window=win, workspace=ws, screen=screen,
                                    area=area, region=region, space_data=area.spaces.active)
    return None

# usage
with bpy.context.temp_override(**uv_editor_context()):
    bpy.ops.uv.snap_selected(target='PIXELS')
    bpy.ops.uv.select_box(xmin=0, xmax=10000, ymin=0, ymax=10000)

with bpy.context.temp_override(**view3d_context()):
    bpy.ops.uv.project_from_view(orthographic=False, camera_bounds=True,
                                 correct_aspect=True, scale_to_bounds=False)
```

#### 4.5 Reading / writing UVs

```python
# single loop
uv = mesh.uv_layers.active
uv.uv[loop_index].vector = (0.25, 0.75)      # 5.x preferred (Float2AttributeValue.vector)
uv.data[loop_index].uv   = (0.25, 0.75)      # legacy, still functional in 5.2

# bulk (R11)
n = len(mesh.loops)
buf = [0.0] * (n * 2)
uv.uv.foreach_get("vector", buf)             # flat [u0,v0,u1,v1,...]
buf = [c * 0.5 for c in buf]                 # e.g. shrink into the lower-left quadrant
uv.uv.foreach_set("vector", buf)
mesh.update()

# per-face access without bmesh
for poly in mesh.polygons:
    for li in poly.loop_indices:
        u, v = uv.uv[li].vector

# in edit mode, via bmesh
import bmesh
bm = bmesh.from_edit_mesh(mesh)
uv_layer = bm.loops.layers.uv.active         # or bm.loops.layers.uv["Lightmap"]
for face in bm.faces:
    for loop in face.loops:
        loop[uv_layer].uv = (loop[uv_layer].uv.x, loop[uv_layer].uv.y)
bmesh.update_edit_mesh(mesh)
```

#### 4.6 Texel density

```python
import math, bpy

def texel_density(obj, texture_size=2048, uv_name=None):
    """Area-weighted px/m over the whole object, world space, modifiers applied."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
    me.calc_loop_triangles()
    uv = me.uv_layers.get(uv_name) if uv_name else me.uv_layers.active
    mw = obj.matrix_world
    a_uv = a_3d = 0.0
    for t in me.loop_triangles:
        p = [mw @ me.vertices[i].co for i in t.vertices]
        a_3d += (p[1] - p[0]).cross(p[2] - p[0]).length * 0.5
        q = [uv.uv[i].vector for i in t.loops]
        a_uv += abs((q[1] - q[0]).cross(q[2] - q[0])) * 0.5
    ev.to_mesh_clear()
    return math.sqrt(a_uv / a_3d) * texture_size if a_3d > 0.0 else 0.0

def scale_uvs_to_density(obj, target_px_per_m, texture_size=2048, uv_name=None):
    cur = texel_density(obj, texture_size, uv_name)
    if cur <= 0.0:
        return
    k = target_px_per_m / cur
    uv = obj.data.uv_layers.get(uv_name) if uv_name else obj.data.uv_layers.active
    buf = [0.0] * (len(obj.data.loops) * 2)
    uv.uv.foreach_get("vector", buf)
    uv.uv.foreach_set("vector", [c * k for c in buf])   # scales about UV origin
    obj.data.update()
# verified: 2 m cube with per-face 0.25x0.25 UVs at 2048 px -> 256.0 px/m;
# doubling object scale halves it to 128.0 px/m.
```

> Verified 2026-10-13 on 5.2.0: a 2 m cube with per-face 0.25 x 0.25 UV islands at 2048 px measures 256.0 px/m; doubling the object scale gives 128.0 px/m; `udim_tile(0.5, 0.5) = 1001`, `udim_tile(10.5, 0.5) = 1011`, `udim_tile(1.5, 2.5) = 1022`. <!-- ease:source S2 anchor="texel_density(2 m cube, 0.25x0.25 per-face UVs, 2048 px)" --> <!-- ease:source S2 anchor="texel_density(same, object scale 2)" --> <!-- ease:source S2 anchor="udim_tile(1.5,2.5)" -->

#### 4.7 UDIM

```python
def udim_tile(u, v):
    """UDIM number for a UV coordinate. u must be in [0, 10)."""
    return 1001 + int(math.floor(u)) + 10 * int(math.floor(v))

def move_island_to_tile(mesh, loop_indices, tile, uv_name=None):
    col = tile - 1001
    du, dv = col % 10, col // 10
    uv = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
    for li in loop_indices:
        x, y = uv.uv[li].vector
        uv.uv[li].vector = (x % 1.0 + du, y % 1.0 + dv)

def tiles_used(mesh, uv_name=None):
    uv = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
    buf = [0.0] * (len(mesh.loops) * 2)
    uv.uv.foreach_get("vector", buf)
    return sorted({udim_tile(buf[i], buf[i + 1]) for i in range(0, len(buf), 2)})
```

#### 4.8 Multiple UV layers

```python
me = obj.data
base = me.uv_layers.get("UVMap")  or me.uv_layers.new(name="UVMap")
lm   = me.uv_layers.get("Lightmap") or me.uv_layers.new(name="Lightmap")
base.active_render = True          # what the renderer/baker reads (R4)
me.uv_layers.active = base         # what edit-mode operators write (R3)
print(me.uv_layers.active_index, [(l.name, l.active, l.active_render) for l in me.uv_layers])

# copy one layer into another without operators
src = [0.0] * (len(me.loops) * 2)
base.uv.foreach_get("vector", src)
lm.uv.foreach_set("vector", src)
me.update()
```

#### 4.9 Overlap / range audit

```python
def uv_audit(mesh, uv_name=None, texture_size=2048):
    uv = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
    buf = [0.0] * (len(mesh.loops) * 2)
    uv.uv.foreach_get("vector", buf)
    us, vs = buf[0::2], buf[1::2]
    zero = all(abs(c) < 1e-9 for c in buf)
    # cheap conservative overlap test: total UV area vs area of the used bounding box
    area = 0.0
    mesh.calc_loop_triangles()
    for t in mesh.loop_triangles:
        q = [uv.uv[i].vector for i in t.loops]
        area += abs((q[1] - q[0]).cross(q[2] - q[0])) * 0.5
    bbox = (max(us) - min(us)) * (max(vs) - min(vs))
    return {
        "u_range": (min(us), max(us)), "v_range": (min(vs), max(vs)),
        "all_zero": zero,
        "outside_0_1": min(us) < -1e-6 or max(us) > 1 + 1e-6
                       or min(vs) < -1e-6 or max(vs) > 1 + 1e-6,
        "uv_area": area, "bbox_area": bbox,
        "likely_overlapping": area > bbox * 1.001,
        "tiles": tiles_used(mesh, uv_name),
        "texels": area * texture_size ** 2,
    }
```

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `unwrap()` returns `{'FINISHED'}` but every UV is `(0.0, 0.0)` | Nothing selected in UV space (`use_uv_select_sync` is `False` — the 4.5 default) | `bpy.ops.uv.select_all(action='SELECT')` after entering Edit Mode (R2) <!-- ease:source UNVERIFIED reason="4.5 default (sync off) cannot be re-run here; on 5.2.0 with sync on the same call produced valid UVs" --> |
| `pack_islands` / `average_islands_scale` return `{'CANCELLED'}` on 4.5 | Same as above | Same as above |
| `Warning: Unwrap failed to solve N of N island(s), edge seams may need to be added` | Closed surface with no seams — it cannot be developed into a plane | Mark seams (§4.2) or use `smart_project` <!-- ease:source S2 anchor="Unwrap failed to solve 1 of 1 island(s)" --> |
| `RuntimeError: Operator bpy.ops.uv.snap_selected.poll() failed, context is incorrect` (even with an area override) | The `IMAGE_EDITOR` space's `mode` is not `'UV'` (setting `area.ui_type` is not enough), **or** the area came from a workspace whose editor does not poll (measured on 5.2.0: Compositing, Rendering and Texture Paint fail; Shading, UV Editing and a retyped area in the active screen pass) | `area.spaces.active.mode = 'UV'` on an area of the window's active screen, then `temp_override` (§4.4) |
| `RuntimeError: Operator bpy.ops.uv.select_box.poll() failed, context is incorrect` | Same — needs a UV-mode SpaceImage | Same |
| `RuntimeError: Operator bpy.ops.uv.project_from_view.poll() failed, context is incorrect` | Needs a `VIEW_3D` area, not an image editor | `temp_override(**view3d_context())` <!-- ease:source S2 anchor="project_from_view poll without override" --> |
| Blender exits with `Writing: /tmp/blender.crash.txt`, no Python traceback | `bpy.ops.uv.stitch()` in `--background` (segfault; no override helps) | Do not call it headlessly; weld UVs with `bmesh` (R14) |
| `RuntimeError: Error: No active face` from `follow_active_quads` | No active face on the edit mesh | In Edit Mode: `bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); bm.faces.active = bm.faces[i]; bmesh.update_edit_mesh(me)` <!-- ease:source S2 anchor="follow_active_quads (no active face)" --> |
| `IndexError: BMElemSeq[index]: outdated internal index table, run ensure_lookup_table() first` | Indexed into `bm.verts`/`edges`/`faces` after a topology change | Call `bm.verts.ensure_lookup_table()` (and the edge/face equivalents) before any `[i]` access |
| `AttributeError: 'NoneType' object has no attribute 'uv'` | `uv_layers.new()` returned `None` (9th layer) | Cap at 8; `me.uv_layers.get(name) or me.uv_layers.new(name=name)` |
| The lightmap layer got overwritten by the diffuse unwrap | The wrong layer was active when the operator ran (on 5.2.0 `new()` leaves the first layer active, so the diffuse layer can be unwrapped twice or the lightmap left empty) | Set `me.uv_layers.active` explicitly before each unwrap (R3) |
| Correct-looking UV editor, wrong texture placement in a render | `active_render` points at a different layer than `active` | `layer.active_render = True` (R4) |
| `AttributeError: 'MeshUVLoopLayer' object has no attribute 'vertex_selection'` | Removed in 5.0 (UV selection is now shared across all UV maps) | Use the mesh selection + `use_uv_select_sync`, or `BMLoop.uv_select_vert` <!-- ease:source S7 anchor="The following UV selection properties have been removed" --> |
| Baked texture bleeds between islands after 2–3 mip levels | Margin too small, or `margin_method='SCALED'` making it unpredictable | `margin_method='FRACTION'`, `margin = 8 / texture_size` (R5/R6) |
| Two objects textured at "the same" density look different | Density measured in local space, or object scale not applied | `texel_density()` uses `matrix_world` (§4.6); apply scale first |
| Some faces render with the wrong UDIM tile | `u >= 10` wrapped into the next row | Keep `0 <= u < 10`; audit with `tiles_used()` |
| `RuntimeError: Operator bpy.ops.uv.select_all.poll() failed, context is incorrect` in Edit Mode | The mesh has no UV layer yet (a bmesh primitive is created without one) | `mesh.uv_layers.new()` before entering Edit Mode <!-- ease:source S2 anchor="uv.select_all.poll in Edit Mode when the mesh has NO UV layer" --> |
| `mesh.uv_layers.active.name` reads `''` after `mode_set('EDIT')` | The layer reference was captured before the mode switch | Re-fetch `mesh.uv_layers.active` after switching modes <!-- ease:source S2 anchor="documented uv_edit_begin layer reference name after Edit Mode entry" --> |

### 6. Parameter defaults by use case

Operator parameter names below were checked against the 5.2.0 operator RNA (`uv.unwrap`, `uv.pack_islands`, `uv.smart_project`, `uv.average_islands_scale`); the numeric targets are pipeline conventions, not Blender defaults. <!-- ease:source S1 anchor="uv.unwrap.props" --> <!-- ease:source S1 anchor="uv.pack_islands.props" --> <!-- ease:source S1 anchor="uv.smart_project.props" --> <!-- ease:source S1 anchor="uv.average_islands_scale.props" --> <!-- ease:source S1 anchor="uv.pack_islands.rotate_method" --> <!-- ease:source S1 anchor="uv.pack_islands.shape_method" --> <!-- ease:source UNVERIFIED reason="industry convention; the module's own Sources note already flags it" -->

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `unwrap(method=)` | `'ANGLE_BASED'` | `'MINIMUM_STRETCH'` | `'CONFORMAL'` | `'CONFORMAL'` | n/a |
| `unwrap(iterations=)` | 10 (unused) | 30–50 | 10 | 10 | n/a |
| `unwrap(fill_holes=)` | False | True | False | False | n/a |
| Texture size assumed | 1024–2048 | 2048–4096/tile | 1024 | 4096 | n/a |
| Target texel density (px/m) | 512–1024 | 1024–2048 | any | 2048–4096 | n/a |
| `margin` (FRACTION) | `4/1024` | `8/2048` | `2/1024` | `8/4096` | n/a |
| `pack_islands(shape_method=)` | `'CONCAVE'` | `'CONCAVE'` | `'AABB'` (fast) | `'CONCAVE'` | n/a |
| `pack_islands(rotate_method=)` | `'CARDINAL'` (mip-friendly) | `'ANY'` | `'ANY'` | `'ANY'` | n/a |
| `smart_project(angle_limit=)` | radians(66) | radians(45) | radians(66) | radians(60) | n/a |
| `average_islands_scale` before pack | Yes | Yes | No | Yes | n/a |
| UDIM tiles | 1 (1001) | 4–20 | 1 | 1–4 | n/a |
| UV layers | UVMap + Lightmap | UVMap | UVMap | UVMap | none |
| Overlapping islands allowed | Yes for tiling/trim; No if baking | No | Yes | No | n/a |
| Lightmap texel density (px/m) | 32–128 | — | — | — | — |
| `correct_aspect` | True | True | True | True | n/a |

### 7. Verification checklist

- [ ] `assert mesh.uv_layers.active is not None` — there is something to write to.
- [ ] `a = uv_audit(mesh); assert not a["all_zero"]` — the unwrap actually produced coordinates.
- [ ] `assert not a["outside_0_1"]` — single-tile layout stayed inside 0..1 (skip for UDIM/tiling).
- [ ] `assert not a["likely_overlapping"]` — required before any bake or lightmap.
- [ ] `assert a["tiles"] == [1001]` for a single-tile asset, or matches the intended UDIM list.
- [ ] `assert abs(texel_density(obj, TEX) - TARGET) / TARGET < 0.15` — density within 15% of target.
- [ ] `assert sum(1 for e in mesh.edges if e.use_seam) > 0` before unwrapping a closed surface.
- [ ] `assert mesh.uv_layers["UVMap"].active_render` — the renderer reads the layer you unwrapped.
- [ ] `assert len(mesh.uv_layers) <= 8`.
- [ ] `assert len(buf) == 2 * len(mesh.loops)` after `uv.foreach_get("vector", buf)` — layer is CORNER-domain as expected.
- [ ] Render/screenshot a UV-grid checker material: squares must look square (no shear) and the same size across the asset (uniform density).
- [ ] After `pack_islands(margin_method='FRACTION', margin=M)`: measured island bounding-box border ≈ `M`, island-to-island gap ≈ `2*M`.

### 8. Original reference list (pre-UKMC; the numbered Sources section at the end of this file is authoritative)

- [Blender 5.2 Python API — `bpy.ops.uv`](https://docs.blender.org/api/current/bpy.ops.uv.html) (`unwrap` methods `ANGLE_BASED`/`CONFORMAL`/`MINIMUM_STRETCH`; `pack_islands` `margin_method`/`shape_method`/`rotate_method`/`udim_source`; `smart_project`; `average_islands_scale(scale_uv, shear)`; `seams_from_islands(mark_seams, mark_sharp)`)
- [Blender 4.5 Python API — `bpy.ops.uv.unwrap`](https://docs.blender.org/api/4.5/bpy.ops.uv.html) (same three methods; default `'CONFORMAL'`)
- [Blender 5.2 Python API — `bpy.types.MeshUVLoopLayer`](https://docs.blender.org/api/current/bpy.types.MeshUVLoopLayer.html) (`uv`, `pin`, `active`, `active_render`; `data` marked deprecated)
- [Blender 4.5 Python API — `bpy.types.MeshUVLoopLayer`](https://docs.blender.org/api/4.5/bpy.types.MeshUVLoopLayer.html) (still has `vertex_selection` / `edge_selection`)
- [Blender 5.2 Python API — `bpy.types.Float2AttributeValue`](https://docs.blender.org/api/current/bpy.types.Float2AttributeValue.html) (`vector`)
- [Blender 5.2 Python API — `bmesh.types`](https://docs.blender.org/api/current/bmesh.types.html) (`BMLoopUV.uv`, `BMLayerAccessLoop.uv`, `BMEdge.seam`, `BMLoop.uv_select_vert`)
- [Blender 5.0 release notes — Mesh: UV selection shared between all UV maps; `MeshUVLoopLayer.vertex_selection`/`edge_selection` removed; `uv_select_*` attributes added](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.0 release notes — Modeling & UV: sync selection enabled by default; per-UV-map selection removed](https://developer.blender.org/docs/release_notes/5.0/modeling/)
- [Blender 5.2 release notes — Modeling & UV: `Original bounding box` unwrap option, select-by-winding, island support for select-overlap](https://developer.blender.org/docs/release_notes/5.2/modeling/)
- Empirically measured on local `blender-5.2.0-linux-x64` and `blender-4.5.9-linux-x64` in `--background --factory-startup`: which `bpy.ops.uv.*` operators poll successfully with no override (unwrap, pack_islands, average_islands_scale, minimize_stretch, align, remove_doubles, cube/sphere/cylinder_project, reset, follow_active_quads, seams_from_islands); which need a UV-mode `SpaceImage` override (snap_selected, snap_cursor, select_box); which need a `VIEW_3D` override (project_from_view); that `uv.stitch` segfaults in background even with a full override; margin semantics (`FRACTION` `4/1024` → 4 px border / 8 px gap; `ADD` → 1 px / 2 px; `SCALED` → 0.4 px / 0.8 px on the same input *(2026-10-13 re-run on a smart-projected 2 m cube: `ADD` → 3.91 px / 7.82 px, `SCALED` → 0.8 px / 1.59 px; both depend on the input UV scale, so the earlier figures are input-specific)*); the 8-layer cap returning `None`; `use_uv_select_sync` defaults (4.5 `False`, 5.2 `True`); the texel-density figures in §4.6.
- `[UNVERIFIED]` Target texel densities (512–1024 px/m for games, 32–128 px/m for lightmaps, 2048–4096 px/m for product viz) and the `rotate_method='CARDINAL'` mip-friendliness claim are industry conventions, not Blender documentation. The `likely_overlapping` heuristic in §4.9 is conservative — it flags any layout whose total UV area exceeds its bounding box, which also catches legitimately L-shaped layouts; use `bpy.ops.uv.select_overlap` interactively for an exact answer.

## Failure Modes (Mandatory)
- **`RuntimeError: Operator bpy.ops.uv.select_all.poll() failed, context is incorrect` in Edit Mode** — cause: the mesh has no UV layer yet (a bmesh primitive carries none; measured poll False without a layer, True after `uv_layers.new()`) — fix: `mesh.uv_layers.new(name='UVMap')` before entering Edit Mode. <!-- ease:source S2 anchor="uv.select_all.poll in Edit Mode when the mesh has NO UV layer" --> <!-- ease:source S2 anchor="uv.select_all.poll in Edit Mode after uv_layers.new()" -->
- **`RuntimeError: ... uv.snap_selected.poll() failed` even with `temp_override`** — cause: the override area came from a workspace whose editor does not poll (Compositing, Rendering, Texture Paint) or the space is not in UV mode — fix: use an area of the window's active screen (retype a spare area to `IMAGE_EDITOR`) and set `space.mode = 'UV'` (measured: polls pass and `snap_selected` / `select_box` return FINISHED). <!-- ease:source S2 anchor="corrected active-screen helper: snap_selected, select_box" --> <!-- ease:source S2 anchor="workspaces that contain an IMAGE_EDITOR area" -->
- **Blender dies with no traceback and prints `Writing: <tempdir>/blender.crash.txt`** — cause: `bpy.ops.uv.stitch()` called in `--background` (measured exit code 139) — fix: never call it headless; weld UVs with bmesh. <!-- ease:source S3 anchor="exit_code: 139" -->
- **`Warning: Unwrap failed to solve 1 of 1 island(s), edge seams may need to be added`** — cause: a closed surface without seams cannot be flattened (measured on a seamless cube) — fix: mark seams (`edges[i].use_seam = True`) or use `smart_project`. <!-- ease:source S2 anchor="Unwrap failed to solve 1 of 1 island(s)" -->
- **The lightmap layer is empty or the diffuse layer was unwrapped twice** — cause: the wrong layer was active; on 5.2.0 `uv_layers.new()` leaves the first layer `active` and `active_render` — fix: set `mesh.uv_layers.active = layer` explicitly before every unwrap. <!-- ease:source S2 anchor="two layers after new(): (name, active, active_render)" -->
- **Bake bleed between islands despite a margin** — cause: a margin method whose size depends on the input UV scale (`ADD`, `SCALED`; measured 3.91 px and 0.8 px border for the same `4/1024` request) — fix: `margin_method='FRACTION'` (measured exactly 4 px border / 8 px gap at 1024). <!-- ease:source S1 anchor="uv.pack_islands[FRACTION].margin=4/1024 on 1024px" --> <!-- ease:source S1 anchor="uv.pack_islands[SCALED].margin=4/1024 on 1024px" -->
- **`mesh.uv_layers.new()` returns `None` and the next line raises `AttributeError`** — cause: a mesh holds at most 8 UV layers; the 9th request does not raise — fix: `me.uv_layers.get(name) or me.uv_layers.new(name=name)` and cap at 8. <!-- ease:source S1 anchor="uv_layers.new[8]" -->

## Sources
- [S1] Local Blender 5.2.0 LTS runtime probe (script: knowledge/_evidence/kb-261013/w2-bpy-52-facts.py) — knowledge/_evidence/kb-261013/w2-bpy-52-facts.txt — captured 2026-10-13 — sha256 2411832c2522b533b8523ee16511805eb0d8a75bc2f2b213663bc0f77f4667af
- [S2] Local Blender 5.2.0 LTS UV-helper probe (script: knowledge/_evidence/kb-261013/w2-uv-helpers-probe.py) — knowledge/_evidence/kb-261013/w2-uv-helpers-probe.txt — captured 2026-10-13 — sha256 a8d8a733fc03d0f59c26852043557376175877401c9e90c20b0c1864d1334802
- [S3] Local Blender 5.2.0 LTS uv.stitch crash probe (script: knowledge/_evidence/kb-261013/w2-uv-stitch-probe.py) — knowledge/_evidence/kb-261013/w2-uv-stitch-probe.txt — captured 2026-10-13 — sha256 d6aff679362c1eefb94552c3b6360137b3b5148ebff6e7ccedcb82bb6d1906d5
- [S4] Uv Operators - Blender Python API — https://docs.blender.org/api/current/bpy.ops.uv.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-ops-uv.html) — captured 2026-10-13 — sha256 5aabbc7ba0d88b3dc6f70762ba82f0c271643ae866eb27641aa14412bf1a3117
- [S5] MeshUVLoopLayer(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.MeshUVLoopLayer.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-MeshUVLoopLayer.html) — captured 2026-10-13 — sha256 23f419796ef3ca86116fc653127151f34a9cd0d1657bc9bb22e2848e7b7b452d
- [S6] Modeling & UV - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.0/modeling/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-0-modeling.html) — captured 2026-10-13 — sha256 c67106d42d474d1a0d5a8302b9c1bd23bda724c20ac4cfe4ca59cb37cfaa6255
- [S7] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-0-python_api.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S8] UDIMs - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/meshes/uv/workflows/udims.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-meshes-uv-workflows-udims.html) — captured 2026-10-13 — sha256 18470133d8bac68ffd1e70293b1e19f7780c27915d1b278b3e5c442170a19bf3
- [S9] Seams - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/meshes/uv/unwrapping/seams.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-meshes-uv-unwrapping-seams.html) — captured 2026-10-13 — sha256 d40bf4dff3874101a5c30e3712393b8ff1063b3d37ffd2f5e78c0cd3a687351f

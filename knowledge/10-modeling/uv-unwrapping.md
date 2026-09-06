---
name: uv-unwrapping
domain: modeling
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Seams, unwrap methods, packing margin math, texel density, UDIMs, multi-UV layouts, and the headless operator-context patterns UV work actually requires.
loads_with: [modeling-topology, modifiers, texturing-baking, export-interchange]
tags: [uv, unwrap, seams, packing, texel-density, udim, lightmap, temp-override, headless]
---

# UV Unwrapping, Packing & Texel Density

## 1. Mental model

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
still contains a real `VIEW_3D` area (measured on 5.2.0 `--factory-startup -b`: areas are `PROPERTIES, OUTLINER, DOPESHEET_EDITOR, VIEW_3D` — **no `IMAGE_EDITOR`**), so `temp_override` works for 3D-view operators; for UV-editor operators create the area by changing an existing area's `type` first (§4.4).
The genuine exceptions are few and named in §5. The other trap is Blender 4.5's
default `use_uv_select_sync = False`: `unwrap()` returns `{'FINISHED'}` and writes
UVs of `(0, 0)` because nothing was selected *in UV space*.

## 2. Decision first

| Use case | Method | Packing | Texel density target | UV layers |
|---|---|---|---|---|
| Game / realtime, unique texture | `unwrap(method='ANGLE_BASED')` with hand/heuristic seams | `pack_islands(margin_method='FRACTION', margin=4/tex_size)` | 512–1024 px/m (hero: 2048) | UVMap (+ Lightmap) |
| Game, tiling / trim sheet | `cube_project` or `follow_active_quads`, then snap to trim rows | none (deliberately overlapping / out of 0..1) | matched to the trim atlas | UVMap |
| Lightmap / second channel | `smart_project(angle_limit=radians(66), island_margin=...)` | `pack_islands` with a large margin | 32–128 px/m | second layer, no overlaps ever |
| Character (film) | `unwrap(method='MINIMUM_STRETCH', iterations=30)` | UDIM, one region per body part | 1024–2048 px/m per tile | UVMap |
| Product viz | `unwrap(method='CONFORMAL')` (angle-preserving) | `pack_islands` `shape_method='CONCAVE'` | 2048–4096 px/m | UVMap |
| Motion graphics | `smart_project` and move on | default | irrelevant | UVMap |
| Baking source (high→low) | must match the low-poly cage's layer exactly | `margin >= 8px` at bake resolution | — | UVMap only |
| 3D print | no UVs needed | — | — | none |

**Angle Based vs Conformal vs Minimum Stretch**

| Method | Enum | Optimises | Use when |
|---|---|---|---|
| Angle Based (ABF) | `'ANGLE_BASED'` | angle preservation, decent area | general-purpose default; organic shells |
| Conformal (LSCM) | `'CONFORMAL'` | conformality (local angles), fast | few seams, mostly-developable surfaces; **this is Blender's default since 4.x** |
| Minimum Stretch (SLIM) | `'MINIMUM_STRETCH'` | area+angle stretch, iterative | characters, high-distortion shells; costs `iterations` (default 10, use 25–50) |

**Overlapping UVs**: fine (and often required) for tiling materials, trim sheets and
mirrored/instanced geometry sharing one texture. **Fatal** for: texture baking
(overlaps write over each other), lightmaps/AO maps, and any per-pixel unique data
(ID masks, vertex-baked curvature). If the asset will be baked, one UV set must be
non-overlapping.

## 3. Rules

R1. Before any `bpy.ops.uv.*` call: object must be **active + selected**, in **Edit Mode**, with mesh elements selected **and** UV elements selected.
    Why: UV operators poll on the edit-mesh; the flatteners iterate the UV selection.
    Violation: `{'FINISHED'}` with every UV written as `(0.0, 0.0)`.

R2. Always call `bpy.ops.uv.select_all(action='SELECT')` after entering Edit Mode, even on 5.2.
    Why: 5.0 turned `use_uv_select_sync` on by default, but 4.5 has it off, and a loaded `.blend` can have either. `uv.select_all` is correct in both.
    Violation on 4.5: `pack_islands` and `average_islands_scale` return `{'CANCELLED'}`; `unwrap` produces zero UVs.

R3. All UV operators write to `mesh.uv_layers.active`. Set it explicitly before every unwrap.
    Why: `uv_layers.new()` makes the new layer active, so an unwrap after adding a lightmap layer silently overwrites the lightmap.
    Violation: the "diffuse" UVs come out as a lightmap-style atlas.

R4. Set `active_render` on the layer the shader/baker should read; `active` and `active_render` are independent flags.
    Why: renderers use `active_render`; edit-mode ops use `active`.
    Violation: correct-looking UV editor, wrong texture placement in a render.

R5. Use `margin_method='FRACTION'` when you care about pixels.
    Why: `FRACTION` is a precise fraction of the final UV output — measured: `margin=4/1024` gives exactly 4 px of border and 8 px between islands at 1024². `'ADD'` and `'SCALED'` scale with the pre-pack UV size and are not predictable.
    Violation: bake bleed across islands despite "setting a margin".

R6. Margin budget: `margin = desired_border_px / texture_size`. Island-to-island gap is `2 × margin`.
    Why: each island gets its own margin band; two adjacent islands contribute one each.
    Violation: mipmapping bleeds neighbouring islands at level 2–3 because 2 px of gap was requested for a 4-mip chain.

R7. Compute texel density as `sqrt(uv_area / world_area) * texture_size`, area-weighted over triangles, using **world-space** triangle areas.
    Why: `uv_area/world_area` is the squared linear ratio; object scale must be in the measurement or the number is meaningless.
    Violation: reporting 1024 px/m for an object with `scale=(2,2,2)` whose real density is 512 px/m.

R8. Equalise density with `bpy.ops.uv.average_islands_scale()` *before* packing, not after.
    Why: packing scales the whole layout to fill 0..1; averaging afterwards re-breaks the packing.
    Violation: islands overlap or spill outside 0..1 after the final step.

R9. Address a UDIM tile as `1001 + floor(u) + 10*floor(v)`; `u` must stay in `[0, 10)`.
    Why: the UDIM convention is a 10-wide grid starting at 1001.
    Violation: `u = 10.5` maps to 1011 (row 2, column 1), silently colliding with the second row.

R10. Read/write UVs as `uv_layer.uv[loop_index].vector` on 5.x; `uv_layer.data[loop_index].uv` still works but is documented as deprecated.
    Why: 5.x exposes UVs as a plain float2 attribute (`Float2AttributeValue.vector`); `.data` is the legacy `MeshUVLoop` wrapper.
    Violation: none yet — but `MeshUVLoopLayer.vertex_selection` / `.edge_selection` **were** removed in 5.0, so any selection code written against `.data` siblings breaks.

R11. Use `foreach_get`/`foreach_set` with the property name `"vector"` for bulk UV I/O.
    Why: ~100× faster than per-loop Python access; the buffer is flat `[u0,v0,u1,v1,…]` of length `2 * len(mesh.loops)`.
    Violation: minutes of runtime on a 500k-loop mesh.

R12. Mark seams via the data API (`mesh.edges[i].use_seam` / bmesh `edge.seam`), not `bpy.ops.mesh.mark_seam`.
    Why: no context, no mode switch, works on `bpy.data` meshes directly. Both spellings write the `uv_seam` EDGE attribute.
    Violation: needless Edit Mode round-trips, and lost selection state.

R13. `mesh.uv_layers.new()` returns `None` past 8 layers instead of raising.
    Why: fixed CustomData layer cap.
    Violation: `AttributeError: 'NoneType' object has no attribute 'uv'` on the next line.

R14. `bpy.ops.uv.stitch()` **cannot** be run in `--background` — it segfaults Blender, with or without a full context override.
    Why: it drives a modal 2D-view interaction; no workaround exists from Python.
    Violation: process dies, `Writing: /tmp/blender.crash.txt`, no traceback. Weld the UVs with your own `bmesh` code instead.

## 4. bpy patterns

### 4.1 Headless preflight — the boilerplate every UV script needs

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

### 4.2 Seams from the data API

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

### 4.3 Unwrap + equalise + pack, headless

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

### 4.4 Operators that DO need a fabricated context

```python
def uv_editor_context():
    """A context override valid for SpaceImage-polling UV operators, in --background.
    In 5.2 --factory-startup background mode NO workspace contains an IMAGE_EDITOR (measured);
    retype an existing area (e.g. DOPESHEET_EDITOR) to IMAGE_EDITOR before overriding, and
    VIEW_3D areas with real WINDOW regions; we only have to switch the space to UV mode."""
    win = bpy.context.window_manager.windows[0]
    # Background mode has no IMAGE_EDITOR: retype a spare area once (measured 5.2.0).
    if not any(a.type == 'IMAGE_EDITOR' for ws in bpy.data.workspaces
               for sc in ws.screens for a in sc.areas):
        spare = next((a for ws in bpy.data.workspaces for sc in ws.screens
                      for a in sc.areas if a.type in ('DOPESHEET_EDITOR', 'OUTLINER')), None)
        if spare is not None:
            spare.type = 'IMAGE_EDITOR'
    for ws in bpy.data.workspaces:
        for screen in ws.screens:
            for area in screen.areas:
                if area.type != 'IMAGE_EDITOR':
                    continue
                space = area.spaces.active
                space.mode = 'UV'          # REQUIRED: the poll checks SpaceImage.mode
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region:
                    return dict(window=win, workspace=ws, screen=screen,
                                area=area, region=region, space_data=space)
    return None

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

### 4.5 Reading / writing UVs

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

### 4.6 Texel density

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

### 4.7 UDIM

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

### 4.8 Multiple UV layers

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

### 4.9 Overlap / range audit

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

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `unwrap()` returns `{'FINISHED'}` but every UV is `(0.0, 0.0)` | Nothing selected in UV space (`use_uv_select_sync` is `False` — the 4.5 default) | `bpy.ops.uv.select_all(action='SELECT')` after entering Edit Mode (R2) |
| `pack_islands` / `average_islands_scale` return `{'CANCELLED'}` on 4.5 | Same as above | Same as above |
| `Warning: Unwrap failed to solve N of N island(s), edge seams may need to be added` | Closed surface with no seams — it cannot be developed into a plane | Mark seams (§4.2) or use `smart_project` |
| `RuntimeError: Operator bpy.ops.uv.snap_selected.poll() failed, context is incorrect` (even with an area override) | The `IMAGE_EDITOR` space's `mode` is not `'UV'` (setting `area.ui_type` is not enough) | `area.spaces.active.mode = 'UV'` before `temp_override` (§4.4) |
| `RuntimeError: Operator bpy.ops.uv.select_box.poll() failed, context is incorrect` | Same — needs a UV-mode SpaceImage | Same |
| `RuntimeError: Operator bpy.ops.uv.project_from_view.poll() failed, context is incorrect` | Needs a `VIEW_3D` area, not an image editor | `temp_override(**view3d_context())` |
| Blender exits with `Writing: /tmp/blender.crash.txt`, no Python traceback | `bpy.ops.uv.stitch()` in `--background` (segfault; no override helps) | Do not call it headlessly; weld UVs with `bmesh` (R14) |
| `RuntimeError: Error: No active face` from `follow_active_quads` | No active face on the edit mesh | In Edit Mode: `bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); bm.faces.active = bm.faces[i]; bmesh.update_edit_mesh(me)` |
| `IndexError: BMElemSeq[index]: outdated internal index table, run ensure_lookup_table() first` | Indexed into `bm.verts`/`edges`/`faces` after a topology change | Call `bm.verts.ensure_lookup_table()` (and the edge/face equivalents) before any `[i]` access |
| `AttributeError: 'NoneType' object has no attribute 'uv'` | `uv_layers.new()` returned `None` (9th layer) | Cap at 8; `me.uv_layers.get(name) or me.uv_layers.new(name=name)` |
| The lightmap layer got overwritten by the diffuse unwrap | `uv_layers.new()` made the new layer active; the operator wrote to it | Set `me.uv_layers.active` explicitly before each unwrap (R3) |
| Correct-looking UV editor, wrong texture placement in a render | `active_render` points at a different layer than `active` | `layer.active_render = True` (R4) |
| `AttributeError: 'MeshUVLoopLayer' object has no attribute 'vertex_selection'` | Removed in 5.0 (UV selection is now shared across all UV maps) | Use the mesh selection + `use_uv_select_sync`, or `BMLoop.uv_select_vert` |
| Baked texture bleeds between islands after 2–3 mip levels | Margin too small, or `margin_method='SCALED'` making it unpredictable | `margin_method='FRACTION'`, `margin = 8 / texture_size` (R5/R6) |
| Two objects textured at "the same" density look different | Density measured in local space, or object scale not applied | `texel_density()` uses `matrix_world` (§4.6); apply scale first |
| Some faces render with the wrong UDIM tile | `u >= 10` wrapped into the next row | Keep `0 <= u < 10`; audit with `tiles_used()` |

## 6. Parameter defaults by use case

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

## 7. Verification checklist

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

## 8. Sources

- [Blender 5.2 Python API — `bpy.ops.uv`](https://docs.blender.org/api/current/bpy.ops.uv.html) (`unwrap` methods `ANGLE_BASED`/`CONFORMAL`/`MINIMUM_STRETCH`; `pack_islands` `margin_method`/`shape_method`/`rotate_method`/`udim_source`; `smart_project`; `average_islands_scale(scale_uv, shear)`; `seams_from_islands(mark_seams, mark_sharp)`)
- [Blender 4.5 Python API — `bpy.ops.uv.unwrap`](https://docs.blender.org/api/4.5/bpy.ops.uv.html) (same three methods; default `'CONFORMAL'`)
- [Blender 5.2 Python API — `bpy.types.MeshUVLoopLayer`](https://docs.blender.org/api/current/bpy.types.MeshUVLoopLayer.html) (`uv`, `pin`, `active`, `active_render`; `data` marked deprecated)
- [Blender 4.5 Python API — `bpy.types.MeshUVLoopLayer`](https://docs.blender.org/api/4.5/bpy.types.MeshUVLoopLayer.html) (still has `vertex_selection` / `edge_selection`)
- [Blender 5.2 Python API — `bpy.types.Float2AttributeValue`](https://docs.blender.org/api/current/bpy.types.Float2AttributeValue.html) (`vector`)
- [Blender 5.2 Python API — `bmesh.types`](https://docs.blender.org/api/current/bmesh.types.html) (`BMLoopUV.uv`, `BMLayerAccessLoop.uv`, `BMEdge.seam`, `BMLoop.uv_select_vert`)
- [Blender 5.0 release notes — Mesh: UV selection shared between all UV maps; `MeshUVLoopLayer.vertex_selection`/`edge_selection` removed; `uv_select_*` attributes added](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.0 release notes — Modeling & UV: sync selection enabled by default; per-UV-map selection removed](https://developer.blender.org/docs/release_notes/5.0/modeling/)
- [Blender 5.2 release notes — Modeling & UV: `Original bounding box` unwrap option, select-by-winding, island support for select-overlap](https://developer.blender.org/docs/release_notes/5.2/modeling/)
- Empirically measured on local `blender-5.2.0-linux-x64` and `blender-4.5.9-linux-x64` in `--background --factory-startup`: which `bpy.ops.uv.*` operators poll successfully with no override (unwrap, pack_islands, average_islands_scale, minimize_stretch, align, remove_doubles, cube/sphere/cylinder_project, reset, follow_active_quads, seams_from_islands); which need a UV-mode `SpaceImage` override (snap_selected, snap_cursor, select_box); which need a `VIEW_3D` override (project_from_view); that `uv.stitch` segfaults in background even with a full override; margin semantics (`FRACTION` `4/1024` → 4 px border / 8 px gap; `ADD` → 1 px / 2 px; `SCALED` → 0.4 px / 0.8 px on the same input); the 8-layer cap returning `None`; `use_uv_select_sync` defaults (4.5 `False`, 5.2 `True`); the texel-density figures in §4.6.
- `[UNVERIFIED]` Target texel densities (512–1024 px/m for games, 32–128 px/m for lightmaps, 2048–4096 px/m for product viz) and the `rotate_method='CARDINAL'` mip-friendliness claim are industry conventions, not Blender documentation. The `likely_overlapping` heuristic in §4.9 is conservative — it flags any layout whose total UV area exceeds its bounding box, which also catches legitimately L-shaped layouts; use `bpy.ops.uv.select_overlap` interactively for an exact answer.

---
name: optimization-realtime
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Poly/draw-call budgets, LODs, atlasing, high-to-low baking, instancing, simplify, and what actually costs time in Cycles.
loads_with: [export-interchange, scene-organization, product-viz-and-shots]
tags: [lod, decimate, budget, baking, atlas, instancing, simplify, cycles-performance]
---

# Optimization for Realtime and for Render Time

## 1. Mental model

Two different optimisation problems share this file because agents conflate
them. **Realtime optimisation** is about what the GPU has to do 60–120 times a
second: vertex count, draw calls, texture memory, overdraw. **Render-time
optimisation** is about what the path tracer has to do once per pixel per
sample: ray depth, shader complexity, volume marching, tessellation. A change
that helps one can hurt the other (adaptive subdivision is great for a Cycles
hero render and catastrophic in a game engine).

For realtime, the binding constraint is almost never triangles on a modern GPU —
it is **draw calls and material count**. One 40k-triangle mesh with one material
is far cheaper than forty 1k-triangle meshes with four materials each. So the
optimisation order is: merge/instance → reduce materials → atlas textures →
*then* reduce triangles.

For Cycles, the binding constraint is **samples × (rays per sample) × (cost per
ray)**. Bounces multiply rays; transparent shadows multiply them again inside
foliage/hair; volumes multiply them per step. Denoising lets you cut samples by
roughly an order of magnitude and is the single largest lever.

The most common agent mistake is decimating first (destroying UVs and normals)
instead of instancing and merging first.

## 2. Decision first

| Situation | Do this | Not this |
|---|---|---|
| Same object repeated N times, same shape | `ob.copy()` + share `ob.data`, or a collection instance | `bpy.ops.object.duplicate(linked=False)` |
| Many varied scatter items | Geometry Nodes instancing / particle instancing | real geometry |
| Need a LOD chain from an existing mesh | Decimate `COLLAPSE` with a ratio schedule | manual deletion |
| Mesh is quad-based, hard-surface, needs clean LOD | Decimate `UNSUBDIV` or manual retopo | `COLLAPSE` (destroys the quad flow) |
| Mesh is mostly flat panels | Decimate `DISSOLVE` (planar) | `COLLAPSE` |
| Mesh is a high-poly sculpt going to game | retopo (manual/Quadriflow) + bake | Decimate — never produces usable UVs |
| Too many materials in the engine | atlas textures, merge into one material | leave as-is |
| Viewport is unusably slow while authoring | `render.use_simplify` + `simplify_subdivision` | lowering modifier levels one by one |
| Cycles render too slow, noise acceptable | enable denoising, cut `samples` 5–10x | raise `samples` |
| Cycles render too slow, interiors | cut `max_bounces`/`diffuse_bounces` | raise `samples` |
| Cycles render too slow, foliage/hair | cut `transparent_max_bounces` | anything else |
| Cycles render too slow, smoke/fire | reduce volume resolution; `volume_biased` + step rate | more samples |

Poly budget reference (triangles, per asset, drawn every frame):

| Asset class | Mobile / WebGL | PC / console realtime | Cinematic realtime | Offline |
|---|---|---|---|---|
| Hero character | 8k–20k | 40k–100k | 150k–500k | unbounded |
| NPC / crowd | 1k–4k | 8k–20k | 30k–60k | unbounded |
| Prop (hand-held) | 300–1.5k | 2k–8k | 10k–30k | unbounded |
| Environment module | 500–3k | 5k–20k | 30k–80k | unbounded |
| Whole scene draw budget | 100k–300k | 3M–8M | 10M–20M | unbounded |
| Draw calls per frame | ≤ 100 | ≤ 2000 | ≤ 5000 | n/a |
| Unique materials per asset | 1–2 | 1–4 | 4–8 | unbounded |
| Texture set per asset | 1× 1–2k ORM+BC+N | 1–2× 2k | 2–4× 4k | 4–8k |

Treat these as starting points to be reported, not laws. Always print the actual
counts (see §4.1) rather than guessing.

## 3. Rules

R1. Measure before optimising: triangles, objects, materials, images, and their memory.
    Why: the agent cannot see the viewport FPS; the only feedback is numbers it prints.
    Violation: hours spent decimating a scene whose real problem was 4,000 draw calls.

R2. Count triangles from `loop_triangles` on the **evaluated** mesh, not from `len(mesh.polygons)`.
    Why: `polygons` are n-gons pre-modifier; the engine sees post-modifier triangles.
    Violation: reported 2k tris, engine reports 34k after subdivision.

R3. Share mesh data for repeats (`ob2.data = ob1.data`) instead of copying it.
    Why: linked duplicates cost one mesh in memory and one GPU buffer; engines can auto-instance them.
    Violation: `.blend` size and GPU memory scale linearly with instance count.

R4. Set both `SubsurfModifier.levels` (viewport) and `.render_levels` deliberately; they are independent.
    Why: `levels` drives interactive cost, `render_levels` drives final cost; the defaults are 1 and 2.
    Violation: a viewport at level 3 that is unusable, or a render at level 1 that looks faceted.

R5. Use `render.use_simplify` for global control instead of editing every modifier.
    Why: `simplify_subdivision` caps every subsurf in the viewport and `simplify_subdivision_render` caps them at render time — `simplify_subdivision_render = 0` flattens all subdivision, which is a common accidental foot-gun.
    Violation: a "fast preview" that is also the final render, delivered flat.

R6. Decimate on a **copy** with a Decimate modifier, never destructively on the source.
    Why: LODs must be regenerable when the source changes; `modifier.face_count` is readable only after evaluation.
    Violation: LOD1 exists, source is gone, art change requires redoing everything.

R7. Bake high-to-low with a cage and a bounded ray distance.
    Why: without `use_cage`/`cage_extrusion`/`max_ray_distance`, rays from concave low-poly regions hit the wrong high-poly surface.
    Violation: normal map with black/rainbow blotches around concave corners.

R8. Give lightmaps their own second UV map, non-overlapping, with margin.
    Why: the first UV map is usually tiled/overlapping for texture reuse; lightmaps must be unique per texel.
    Violation: light bleeding, or one lit patch replicated across the model.

R9. Cut samples with a denoiser before cutting bounces.
    Why: denoising is roughly a 5–10x sample reduction at similar perceived quality; bounce reduction changes the *look* (energy loss, darker interiors).
    Violation: renders that are fast but visibly darker/flatter than the reference.

R10. Never enable adaptive subdivision on assets destined for a realtime engine.
    Why: it produces camera-dependent tessellation; there is no camera at export time and the result is either enormous or degenerate.
    Violation: a 4M-triangle export of a 2k-triangle asset.

R11. Purge and pack-audit before measuring memory.
    Why: orphaned images and meshes still occupy RAM and file size until purged.
    Violation: memory numbers that do not match what the scene actually draws.

## 4. bpy patterns

### 4.1 Scene audit — always run this first

```python
import bpy

def audit(scene=None, view_layer=None):
    scene = scene or bpy.context.scene
    vl = view_layer or bpy.context.view_layer
    dg = bpy.context.evaluated_depsgraph_get()

    tris = verts = 0
    per_object = {}
    for ob in dg.objects:
        if ob.type != 'MESH':
            continue
        me = ob.data
        me.calc_loop_triangles()
        t = len(me.loop_triangles)
        tris += t
        verts += len(me.vertices)
        per_object[ob.name] = t

    # instances actually drawn (includes collection/geo-node instances)
    n_instances = sum(1 for _ in dg.object_instances)

    mats = {m.name for ob in dg.objects if ob.type == 'MESH'
            for m in ob.data.materials if m}
    img_bytes = sum(i.size[0] * i.size[1] * i.channels *
                    (2 if i.is_float else 1) for i in bpy.data.images if i.has_data)

    return dict(
        tris=tris, verts=verts,
        mesh_objects=sum(1 for o in dg.objects if o.type == 'MESH'),
        instances=n_instances,
        unique_meshes=len({o.data.name for o in dg.objects if o.type == 'MESH'}),
        materials=len(mats),
        images=len(bpy.data.images),
        image_bytes=img_bytes,
        heaviest=sorted(per_object.items(), key=lambda kv: -kv[1])[:10],
        statistics=scene.statistics(vl),
    )

print(audit())
bpy.ops.wm.memory_statistics()      # prints allocator totals to stdout
```

`unique_meshes` far below `mesh_objects` means instancing is working.
`instances` far above `mesh_objects` means geometry-node/collection instancing is
in play — that is cheap in Blender but the *engine* may still see one draw call
each.

### 4.2 LOD generation

```python
import bpy

LOD_RATIOS = (1.0, 0.5, 0.25, 0.10, 0.04)   # LOD0..LOD4

def make_lods(src, ratios=LOD_RATIOS, collection=None,
              triangulate=True, symmetry_axis=None):
    col = collection or src.users_collection[0]
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for i, r in enumerate(ratios):
        if i == 0:
            lod = src
        else:
            lod = src.copy()
            lod.data = src.data.copy()          # LODs must NOT share data
            lod.name = "{}_LOD{}".format(src.name.split("_LOD")[0], i)
            lod.data.name = lod.name + "_data"
            col.objects.link(lod)
            m = lod.modifiers.new("LOD", 'DECIMATE')
            m.decimate_type = 'COLLAPSE'        # 'COLLAPSE'|'UNSUBDIV'|'DISSOLVE'
            m.ratio = r
            m.use_collapse_triangulate = triangulate
            if symmetry_axis:
                m.use_symmetry = True
                m.symmetry_axis = symmetry_axis  # 'X'|'Y'|'Z'
        out.append(lod)
    return out

def decimated_face_count(ob):
    """modifier.face_count is only valid after depsgraph evaluation."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    return [(m.name, m.face_count) for m in ev.modifiers if m.type == 'DECIMATE']
```

Decimate type selection, verified enum and semantics:

| `decimate_type` | Controls | Good for | Destroys |
|---|---|---|---|
| `'COLLAPSE'` | `ratio` (0–1), `use_collapse_triangulate`, `vertex_group`, `use_symmetry` | organic meshes, distant LODs | quad flow, edge loops; UVs stretch |
| `'UNSUBDIV'` | `iterations` | meshes that came from subdivision | detail added after subdivision |
| `'DISSOLVE'` (Planar) | `angle_limit` (default 0.0873 rad ≈ 5°) | flat-panelled hard surface, CAD imports | nothing much; produces n-gons |

Use `vertex_group` + `vertex_group_factor` to protect silhouettes and faces:
weight 1.0 = full decimation, 0.0 = protected (invert with
`invert_vertex_group`).

When Decimate is not acceptable — sculpts, anything that will deform, anything
needing clean UVs — retopologise instead (Quadriflow via
`bpy.ops.object.quadriflow_remesh`, or a Remesh modifier as a base) and then
bake the high-poly detail down (§4.4).

### 4.3 Instancing, linked duplicates, and merging

```python
import bpy
from mathutils import Matrix

def linked_dupe(src, name, matrix, col=None):
    ob = src.copy()                 # new Object, SAME mesh data-block
    ob.data = src.data              # explicit: never copy the data
    ob.name = name
    ob.matrix_world = matrix
    (col or src.users_collection[0]).objects.link(ob)
    return ob

def join_for_drawcalls(objects, target=None):
    """Merge meshes that share a material into one object (one draw call)."""
    target = target or objects[0]
    vl = bpy.context.view_layer
    for ob in objects:
        ob.select_set(True)
    vl.objects.active = target
    with bpy.context.temp_override(active_object=target,
                                   selected_editable_objects=list(objects)):
        bpy.ops.object.join()
    return target
```

Cost model to reason with:

| Strategy | Blender RAM | GPU buffers | Engine draw calls | Per-instance variation |
|---|---|---|---|---|
| Full duplicate (`duplicate(linked=False)`) | N × mesh | N | N | full |
| Linked duplicate (shared `ob.data`) | 1 × mesh | 1 | N (or 1 if the engine auto-instances) | transform only |
| Collection instance (Empty) | 1 × mesh | 1 | N | transform only |
| Geometry Nodes instancing | 1 × mesh | 1 | 1–N | transform + attributes |
| Joined into one object | 1 × merged mesh | 1 | 1 | none |

glTF exports collection/geo-node instances as real nodes unless
`export_gpu_instances=True` (writes `EXT_mesh_gpu_instancing`).

### 4.4 High-to-low baking as a pipeline step

```python
import bpy

def bake_high_to_low(low, high, image, bake_type='NORMAL',
                     cage=None, extrusion=0.02, ray_distance=0.05,
                     margin=16, uv_layer=""):
    """Cycles-only. `image` must already be assigned to an Image Texture node
    that is the ACTIVE node in every material on `low`."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1 if bake_type in {'NORMAL', 'UV'} else 64
    scene.cycles.use_denoising = False

    vl = bpy.context.view_layer
    for ob in bpy.data.objects:
        ob.select_set(False)
    high.select_set(True)
    low.select_set(True)
    vl.objects.active = low                       # active == LOW poly target

    kw = dict(type=bake_type,                     # 'NORMAL','AO','DIFFUSE',
                                                  # 'ROUGHNESS','EMIT','COMBINED',
                                                  # 'POSITION','UV','SHADOW', ...
              use_selected_to_active=True,
              cage_extrusion=extrusion,
              max_ray_distance=ray_distance,
              margin=margin, margin_type='EXTEND',
              use_clear=True, target='IMAGE_TEXTURES',
              save_mode='INTERNAL', uv_layer=uv_layer)
    if bake_type == 'NORMAL':
        kw.update(normal_space='TANGENT',
                  normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z')
    if cage is not None:
        kw.update(use_cage=True, cage_object=cage.name)
    bpy.ops.object.bake(**kw)
    return image
```

Verified `bpy.ops.object.bake` signature (5.2):
`type, pass_filter, filepath, width, height, margin, margin_type,
use_selected_to_active, max_ray_distance, cage_extrusion, cage_object,
normal_space, normal_r, normal_g, normal_b, target, save_mode, use_clear,
use_cage, use_split_materials, use_automatic_name, uv_layer`.

Bake order that works: **Normal → AO → Curvature → Diffuse/Albedo → Roughness**.

- **Normal** must be `normal_space='TANGENT'` with `+X +Y +Z` for glTF/Unity/
  Unreal (Unreal flips green on import, not on export).
- **AO** is `type='AO'`; for glTF it belongs in the R channel of the ORM texture.
- **Curvature** has no dedicated bake pass. Bake `type='NORMAL'` and derive
  curvature in the compositor/shader, or bake an `EMIT` pass driven by a
  Geometry ▸ Pointiness node — that is the standard workaround.
- Set the Image Texture node holding the target to **Non-Color** for normal, AO,
  roughness and metallic; sRGB only for base colour.

### 4.5 Atlasing and lightmap UVs

```python
import bpy

def uv_pack_for_atlas(objects, margin=0.005, uv_name="UVMap"):
    vl = bpy.context.view_layer
    for ob in bpy.data.objects:
        ob.select_set(False)
    for ob in objects:
        ob.select_set(True)
        if uv_name not in ob.data.uv_layers:
            ob.data.uv_layers.new(name=uv_name)
        ob.data.uv_layers[uv_name].active = True
    vl.objects.active = objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM',
                            rotate=True, rotate_method='ANY', scale=True,
                            merge_overlap=False,
                            margin_method='SCALED', margin=margin,
                            shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')

def make_lightmap_uv(ob, name="Lightmap", angle_limit=1.15192, margin=0.02):
    """Second, non-overlapping UV set for baked lighting."""
    if name not in ob.data.uv_layers:
        ob.data.uv_layers.new(name=name)
    ob.data.uv_layers[name].active = True
    vl = bpy.context.view_layer
    vl.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle_limit,
                             margin_method='SCALED', island_margin=margin,
                             rotate_method='AXIS_ALIGNED_Y',
                             area_weight=0.0, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
```

`bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_PACK_IN_ONE=True,
PREF_NEW_UVLAYER=True, PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.1)` still exists and
guarantees non-overlap across a whole selection, at the cost of very fragmented
islands. `smart_project` gives better islands but you must verify non-overlap.

UV-mode operators require Edit Mode; under `--background` they still work
because they operate on the mesh, but the object must be made active and the
mode toggled as shown. Wrap in `bpy.context.temp_override(...)` if a specific
area is required.

### 4.6 Simplify and viewport-vs-render subdivision

```python
import bpy

def set_preview_mode(scene, on=True):
    r = scene.render
    r.use_simplify = on
    if on:
        r.simplify_subdivision = 0          # cap viewport subsurf at 0
        r.simplify_child_particles = 0.05
        r.simplify_volumes = 0.25
        r.use_simplify_normals = True       # skip custom normal eval in viewport
    # DANGER: simplify_subdivision_render caps the FINAL render too.
    # r.simplify_subdivision_render = 0  ->  flat final renders.

def set_subsurf(ob, viewport=1, render=2, adaptive=False):
    m = next((m for m in ob.modifiers if m.type == 'SUBSURF'), None) \
        or ob.modifiers.new("Subdivision", 'SUBSURF')
    m.subdivision_type = 'CATMULL_CLARK'
    m.levels = viewport
    m.render_levels = render
    m.use_limit_surface = True
    m.quality = 3
    if adaptive:                             # Cycles only; never for game export
        m.use_adaptive_subdivision = True
        m.adaptive_space = 'PIXEL'           # 'PIXEL' | 'OBJECT'  (5.0+)
        m.adaptive_pixel_size = 1.0          # target polygon size in pixels
        # m.adaptive_space = 'OBJECT'; m.adaptive_object_edge_length = 0.01
    return m
```

Adaptive subdivision left experimental status in Blender 5.0 and now lives
directly on the Subdivision Surface modifier. The `'OBJECT'` space option was
added in 5.0 specifically so instanced meshes can be tessellated once,
independent of camera distance.

### 4.7 What actually costs time in Cycles

Property names are on `scene.cycles` (verified against the Cycles add-on
source); defaults in brackets.

```python
import bpy
c = bpy.context.scene.cycles

# --- sampling: the biggest lever ---------------------------------------
c.samples = 128                   # [4096] final
c.preview_samples = 16            # [1024] viewport
c.use_adaptive_sampling = True    # [True]
c.adaptive_threshold = 0.01       # [0.01] higher = fewer samples, more noise
c.adaptive_min_samples = 0        # [0] = automatic
c.time_limit = 0.0                # seconds; 0 = unlimited
c.use_denoising = True            # [True]
c.denoiser = 'OPENIMAGEDENOISE'   # or 'OPTIX'

# --- ray depth: changes the LOOK, not just the speed -------------------
c.max_bounces = 12                # [12]
c.diffuse_bounces = 4             # [4]
c.glossy_bounces = 4              # [4]
c.transmission_bounces = 12       # [12]
c.volume_bounces = 0              # [0]
c.transparent_max_bounces = 8     # [8]  -- foliage/hair killer
c.min_light_bounces = 0           # [0]
c.min_transparent_bounces = 0     # [0]

# --- cheap wins --------------------------------------------------------
c.caustics_reflective = False     # [True]
c.caustics_refractive = False     # [True]
c.blur_glossy = 1.0               # [1.0] clamps fireflies
c.sample_clamp_indirect = 10.0    # [10.0]
c.light_sampling_threshold = 0.01 # [0.01]
c.use_fast_gi = False             # [False] AO-approximated GI
c.tile_size = 2048                # [2048] lower only if VRAM-bound
bpy.context.scene.render.use_persistent_data = True   # animation re-renders
```

Rough cost multipliers for a typical interior/product scene. These are
order-of-magnitude planning aids, **not measured guarantees** — always A/B with
`time_limit` or wall-clock on the actual scene.

| Change | Approx. time multiplier | Look change |
|---|---|---|
| `samples` ×2 | ×2 (sublinear with adaptive sampling) | −½ noise |
| Denoiser on, `samples` ÷8 | ≈ ÷6 | slight detail softening |
| `adaptive_threshold` 0.01 → 0.05 | ×0.5–0.7 | visible noise in dark areas |
| `max_bounces` 12 → 4 | ×0.5–0.8 | darker interiors, energy loss |
| `diffuse_bounces` 4 → 1 | ×0.6–0.9 | flat interiors, lost colour bleed |
| `transparent_max_bounces` 8 → 2 (dense foliage/hair) | ×0.2–0.5 | leaves/hair go opaque-dark |
| Caustics off | ×0.7–0.95 | no glass/water light patterns |
| Volume in shot (smoke/fog) | ×2–10 | — |
| `volume_bounces` 0 → 2 | ×1.5–3 | correct multiple scattering |
| SSS-heavy skin, 5.0 multi-bounce random walk | ×1.1–1.4 vs 4.5 | less darkening |
| Adaptive subdivision + displacement | ×1.5–5 and large RAM | true silhouette detail |
| Motion blur on | ×1.3–2 | — |
| Resolution ×2 (each axis) | ×4 | — |
| `use_persistent_data=True` on a 250-frame anim | ÷1.2–2 of total | none; costs RAM |
| Hair/curves `shape='RIBBON'` vs 3D | ×0.6–0.8 | no self-shadow thickness |

Blender 5.0 changed volume rendering to unbiased null-scattering by default;
`volume_step_rate` / `volume_max_steps` only apply when
`scene.cycles.volume_biased = True`. If a 4.5 scene renders differently or
slower after upgrade, that is why.

### 4.8 Memory profiling

```python
import bpy, sys

def memory_report():
    imgs = sorted(
        ((i.name, i.size[0], i.size[1], i.channels, i.is_float,
          i.size[0] * i.size[1] * i.channels * (4 if i.is_float else 1))
         for i in bpy.data.images if i.has_data),
        key=lambda t: -t[-1])
    meshes = sorted(((m.name, len(m.vertices), len(m.polygons))
                     for m in bpy.data.meshes), key=lambda t: -t[1])
    return dict(top_images=imgs[:10],
                image_total_bytes=sum(t[-1] for t in imgs),
                top_meshes=meshes[:10],
                n_orphan_meshes=sum(1 for m in bpy.data.meshes if m.users == 0))

print(memory_report())
bpy.ops.wm.memory_statistics()
bpy.data.orphans_purge(do_recursive=True)
```

Blender's own numbers: `scene.statistics(view_layer)` returns the status-bar
string (objects/verts/faces/tris/memory) and `bpy.ops.wm.memory_statistics()`
prints allocator totals to stdout — both are readable in a headless log.

Texture memory is usually the dominant term. A 4096² RGBA 8-bit image is 64 MiB
uncompressed in Blender (no GPU block compression at authoring time); ten of
them is 640 MiB before any geometry. `scene.cycles.texture_limit_render` /
`texture_limit` cap the size Cycles actually uploads.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Reported triangle count is a fraction of the engine's | counted `len(mesh.polygons)` on unevaluated data | `evaluated_get(dg)` + `calc_loop_triangles()` |
| `modifier.face_count == 0` after setting `ratio` | Decimate not evaluated yet | read it from `ob.evaluated_get(depsgraph)` |
| Decimated LOD has torn/stretched textures | `COLLAPSE` on UV-critical geometry | `DISSOLVE`, or retopo + bake |
| Final render comes out flat/faceted | `render.simplify_subdivision_render` left at 0 | set it to ≥ 6 or `use_simplify=False` |
| Baked normal map has black/rainbow blotches | no cage, or ray distance too large | `use_cage=True` + cage object, or lower `max_ray_distance` |
| Bake is entirely black | no active Image Texture node in the material, or wrong active object | make the target image node active on every material; low-poly must be the active object |
| `RuntimeError: Error: No active image found in material ...` | same as above | assign and activate the image node |
| Lightmap shows one patch repeated | overlapping UVs in the lightmap channel | `lightmap_pack` or `pack_islands(merge_overlap=False)` |
| `.blend` grows linearly with copies | `duplicate(linked=False)` or `ob.data = src.data.copy()` | share `ob.data` |
| Cycles render 10x slower after 5.0 upgrade | new unbiased volume sampling | `scene.cycles.volume_biased = True` and tune step rate |
| Out of GPU memory | 4k+ float textures, or `tile_size` too large | `texture_limit_render='2048'`, lower `tile_size` |
| Foliage render crawls | `transparent_max_bounces=8` × alpha-clipped leaves | drop to 2–4, or use alpha-hashed/opaque leaves |
| Viewport unusable, render fine | high `SubsurfModifier.levels` | `use_simplify=True; simplify_subdivision=0` |
| Export is 4M triangles from a 2k asset | adaptive subdivision left on | `use_adaptive_subdivision=False` before export |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Target triangles (hero) | 20k–100k | 60k–150k (render), 20k proxy | task-dependent | 200k–2M | 100k–2M (resolution, not budget) |
| LOD chain ratios | 1 / .5 / .25 / .1 / .04 | 1 / .5 (proxy only) | n/a | n/a | n/a |
| `decimate_type` | `'COLLAPSE'` | `'COLLAPSE'` (proxy) | n/a | `'DISSOLVE'` (cleanup) | `'DISSOLVE'` only |
| Materials per asset | 1–4 | 2–6 | free | free | 1 (irrelevant) |
| Texture resolution | 1k–2k | 2k–4k | 2k | 4k | n/a |
| Atlas / merge draw calls | yes | partial | no | no | n/a |
| `SubsurfModifier.levels` (viewport) | 0 | 1 | 1 | 2 | 2 |
| `SubsurfModifier.render_levels` | 0 (baked) | 2 | 2 | 3 | 3–4 (then apply) |
| `use_adaptive_subdivision` | never | no | no | yes, `adaptive_pixel_size=1.0` | no |
| `render.use_simplify` while authoring | on | on | on | on | off |
| `cycles.samples` | 32 (bakes) | 128 | 128 | 256–512 | n/a |
| `cycles.use_denoising` | True | True | True | True | n/a |
| `cycles.max_bounces` | 4 | 8 | 8 | 12–16 | n/a |
| `cycles.diffuse_bounces` | 2 | 3 | 3 | 4 | n/a |
| `cycles.transparent_max_bounces` | 4 | 8 | 8 | 12 | n/a |
| `cycles.caustics_refractive` | False | False | False | True (glass/liquid) | n/a |
| `render.use_persistent_data` | n/a | True | True | False (single frames) | n/a |
| Bake passes required | Normal, AO, Albedo, Roughness, Metallic | Normal, AO | none | none | none |
| Second UV set (lightmap) | yes | no | no | no | no |

## 7. Verification checklist

- [ ] `a = audit(); assert a["tris"] <= BUDGET` — the scene fits the stated budget.
- [ ] `assert a["unique_meshes"] < a["mesh_objects"]` when repeats exist — instancing is actually happening.
- [ ] `assert a["materials"] <= MAX_MATERIALS` — draw-call proxy is under control.
- [ ] `assert decimated_face_count(lod1)[0][1] <= 0.55 * base_faces` — Decimate really ran.
- [ ] `assert not bpy.context.scene.render.use_simplify or bpy.context.scene.render.simplify_subdivision_render >= 6` — no accidental flat final render.
- [ ] `assert all(not m.use_adaptive_subdivision for ob in export_set for m in ob.modifiers if m.type=='SUBSURF')` — safe to export.
- [ ] `assert len(ob.data.uv_layers) >= 2` for lightmapped assets, and the second layer's island bounds do not overlap.
- [ ] Bake sanity: render a 64-sample flat-lit preview of the low-poly with the baked normal map; silhouette should match the high-poly screenshot.
- [ ] `assert memory_report()["image_total_bytes"] < VRAM_BUDGET`.
- [ ] Time an A/B: render the same frame with `time_limit=30` before and after a change and compare the noise level in the screenshot.

## 8. Sources

- [bpy.types.DecimateModifier — 5.2](https://docs.blender.org/api/current/bpy.types.DecimateModifier.html)
- [bpy.types.SubsurfModifier — 5.2](https://docs.blender.org/api/current/bpy.types.SubsurfModifier.html) (`use_adaptive_subdivision`, `adaptive_space`, `adaptive_pixel_size`, `adaptive_object_edge_length`)
- [bpy.types.RenderSettings — 5.2](https://docs.blender.org/api/current/bpy.types.RenderSettings.html) (`use_simplify`, `simplify_subdivision*`, `use_persistent_data`)
- [bpy.ops.object.bake — 5.2](https://docs.blender.org/api/current/bpy.ops.object.html)
- [bpy.ops.uv (`smart_project`, `pack_islands`, `lightmap_pack`) — 5.2](https://docs.blender.org/api/current/bpy.ops.uv.html)
- [bpy.types.Depsgraph — 5.2](https://docs.blender.org/api/current/bpy.types.Depsgraph.html)
- [Blender 5.0: Cycles release notes](https://developer.blender.org/docs/release_notes/5.0/cycles/) — unbiased volumes, adaptive subdivision out of experimental, multi-bounce SSS
- [Cycles property definitions (`intern/cycles/blender/addon/properties.py`)](https://projects.blender.org/blender/blender/src/branch/main/intern/cycles/blender/addon/properties.py) — verified names and defaults
- `[UNVERIFIED]` All cost multipliers in §4.7 are order-of-magnitude planning heuristics, not benchmarked figures from Blender documentation.
- `[UNVERIFIED]` Poly/draw-call budget tables in §2 are industry practice, not Blender documentation.
- `[UNVERIFIED]` Curvature baking via a Pointiness-driven `EMIT` pass is a community workaround; Blender has no curvature bake pass.

---
name: scene-organization
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Collections, visibility flags, data-block users/orphans, linking vs appending, units, and a deterministic scene scaffold for headless bpy agents.
loads_with: [export-interchange, optimization-realtime, product-viz-and-shots]
tags: [collections, visibility, datablocks, linking, units, naming, scaffold]
id: scene-organization
title: "Scene Organization for Agent-Driven Blender"
when: [collections-visibility, orphan-purge, link-append-override, unit-scale, export-naming, scene-scaffold]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Scene Organization for Agent-Driven Blender

## Purpose
Give a headless bpy agent deterministic rules for building, linking, hiding, purging, naming and saving data-blocks so that render and export walk the scene graph the agent intended.

## When to Use / When NOT
- ALLOWED: creating or restructuring a scene in bpy — data-API construction with explicit collection links (R1-R3, §4.1-4.3).
- ALLOWED: choosing which hide flag to use for render, viewport or exporter — the measured matrix in §4.4 (Blender 5.2.0).
- ALLOWED: purging, fake users, linking, appending and library overrides — §4.5-4.6.
- ALLOWED: unit scale, naming and transform hygiene before handoff — R5-R6, §4.7, §4.9.
- NOT ALLOWED: choosing GLB/USD/FBX export options or validating interchange files — use `export-interchange` instead.
- NOT ALLOWED: poly budgets, LODs, baking or Cycles render cost — use `optimization-realtime` instead.
- NOT ALLOWED: camera, lighting and shot construction — use `product-viz-and-shots` instead.

## Core Knowledge Content

### 1. Mental model

A `.blend` is a database of ID data-blocks (`bpy.data.objects`, `.meshes`,
`.materials`, `.collections`, ...) plus one or more `Scene`s that *reference*
them. An object is only "in the scene" because some Collection links it, and a
Collection is only in the scene because it is a child of `scene.collection` (the
master collection, which is *not* itself in `bpy.data.collections`) <!-- ease:source S15 anchor="scene.collection in bpy.data.collections False" -->. Everything
an agent does — export, render, purge, link — walks that graph, so a mistake in
linking shows up much later as "the exporter wrote an empty file".

The single most common agent error is confusing the **three unrelated hide
flags**: `LayerCollection.exclude` (per view layer, removes objects from the
dependency graph entirely), `Collection.hide_viewport` / `Object.hide_viewport`
(global "disable in viewports", the monitor icon), and
`LayerCollection.hide_viewport` / `Object.hide_set()` (per view layer, the eye
icon). <!-- ease:source S13 anchor="RNA descriptions: exclude, hide_viewport, hide_set" --> Only `exclude` and `hide_render` change what the F12 renderer sees
(measured in 5.2.0, Cycles alpha test) <!-- ease:source S12 anchor="render center_alpha per flag" -->; exporters do not follow
them by default and filter only when their visibility option is on (§4.4) <!-- ease:source S11 anchor="gltf use_visible/use_renderable" --><!-- ease:source S12 anchor="gltf exclude {} has_B True" -->. The second most common error is building a scene
by `bpy.ops.mesh.primitive_*_add()` and then relying on `context.active_object`,
which is fragile under `--background`.

Naming matters because names cross the process boundary into FBX/glTF/USD and
into shader/skeleton lookups downstream. Blender 5.0 raised the ID name limit to
255 bytes <!-- ease:source S5 anchor="Longer Data-Block Names: 63 -> 255 bytes" --> <!-- ease:source S8 anchor="MAX_ID_NAME 258" --> (runtime: a 300-character name is truncated to 255 <!-- ease:source S10 anchor="name300 len 255" -->), but downstream consumers did not <!-- ease:source UNVERIFIED reason="downstream name limits are practice-derived" -->.

### 2. Decision first

| Question | Answer | Python |
|---|---|---|
| Need a group that renders, exports and can be instanced? | Collection | `bpy.data.collections.new()` + `scene.collection.children.link()` <!-- ease:source S15 anchor="new collection users 0" --> |
| Need to *temporarily* stop evaluating a whole branch (fastest) | `exclude` | `view_layer.layer_collection.children["X"].exclude = True` |
| Need it invisible in viewport but still rendered | global viewport disable | `col.hide_viewport = True` |
| Need it visible in viewport but not in the render | render disable | `col.hide_render = True` / `ob.hide_render = True` |
| Need N copies sharing one mesh, N transforms | linked duplicate | `ob2 = ob.copy(); ob2.data = ob.data` |
| Need N copies of a whole *set* of objects | collection instance | Empty with `instance_type='COLLECTION'` |
| Need to reuse an asset from another file, editable | append | `bpy.ops.wm.append` / `libraries.load(link=False)` |
| Need to reuse an asset, stay in sync with source | link (+ library override to pose/animate) | `libraries.load(link=True)` then `id.override_hierarchy_create()` |
| Need physically meaningful sizes (physics, print, export) | metric, 1 BU = 1 m | `scene.unit_settings.system='METRIC'; scale_length=1.0` |
| Need to free memory / shrink file | purge | `bpy.data.orphans_purge(do_recursive=True)` <!-- ease:source S2 anchor="orphans_purge signature, do_recursive default False" --> |

Naming policy by target:

| Target | Safe character set | Hard notes |
|---|---|---|
| USD | `[A-Za-z_][A-Za-z0-9_]*` (ASCII) | Exporter *rewrites* names: every disallowed codepoint becomes `_`, a leading digit gets a `_` prefix <!-- ease:source S7 anchor="make_safe_identifier" --><!-- ease:source S11 anchor="usd '1 Chair' -> _1_Chair" -->. With `allow_unicode=True` (5.0+ default) XID start/continue codepoints also pass <!-- ease:source S6 anchor="allow_unicode true by default" --><!-- ease:source S11 anchor="usd 'Café' allow_unicode True" -->. |
| glTF | anything (JSON strings) | Names are not identifiers, but duplicate names collide in most runtimes' node lookup; keep them unique. |
| FBX | ASCII alnum + `_` recommended | `:` `|` `*` `/` `\` `"` and spaces routinely break Maya/Max/Unity/Unreal name mangling. Not sanitized on the Blender side. <!-- ease:source UNVERIFIED reason="FBX/Unity/Unreal mangling lists are practice-derived, not in Blender docs" --> |
| Unity / Unreal asset names | ASCII alnum + `_` | Leading digits and spaces get renamed on import; renaming breaks prefab/skeleton bindings. |
| STL / PLY / 3MF | irrelevant | Formats carry no object names (STL solid name at most). |

Practical rule for anything that will leave Blender:
`^[A-Za-z_][A-Za-z0-9_]{0,62}$`.

### 3. Rules

R1. Create data-blocks with `bpy.data.*.new()`, then link explicitly; never rely on `bpy.ops.*_add()` for structure.
    Why: `bpy.data.*.new()` is context-free and returns the object; `ops` variants depend on `context.collection`, selection and mode, all of which are undefined-ish in background mode. <!-- ease:source S14 anchor="active_object after empty None" -->
    Violation: `AttributeError: 'NoneType' object has no attribute 'name'` on `context.active_object`, or the object silently lands in the wrong collection.

R2. A new Collection has zero users until linked; link it to `scene.collection.children` (or a parent collection) in the same statement block.
    Why: unlinked collections are orphans and are destroyed by the next `orphans_purge()` or file save/reload. <!-- ease:source S15 anchor="unlinked collection survives purge False" -->
    Violation: collection disappears after save+reload; `bpy.data.collections['Props'].users == 0`.

R3. Never link the same object into two collections unless you mean it.
    Why: `Collection.objects.link()` adds a user <!-- ease:source S15 anchor="object users after 2 collection links 2" -->; measured in 5.2.0: the glTF exporter writes the object once with default options and twice only with `export_hierarchy_full_collections=True` <!-- ease:source S11 anchor="gltf dup {} DUP count 1; full_collections DUP count 2" -->.
    Violation: duplicated meshes in the exported file; `len([c for c in bpy.data.collections if ob.name in c.objects]) > 1`.

R4. Use `exclude` to cut evaluation cost, `hide_render` to cut render content, `hide_viewport` only for authoring comfort.
    Why: `exclude=True` removes the branch from the view layer's depsgraph and from the render <!-- ease:source S12 anchor="exclude center_alpha 0.0" -->; `LayerCollection.hide_viewport` and `Object.hide_set()` leave the object in the render <!-- ease:source S12 anchor="hide_viewport center_alpha 1.0" -->. Measured: `Collection.hide_viewport` and `Object.hide_viewport` also still render (alpha 1.0) although they remove the object from the viewport depsgraph <!-- ease:source S11 anchor="vis Collection.hide_viewport viewport_dg_has_B False" -->.
    Violation: agent sets `hide_viewport=True` "to hide the backdrop" and the backdrop still appears in the F12 render.

R5. Apply object scale (`bpy.ops.object.transform_apply(scale=True)`) before exporting to FBX/glTF/USD or before physics/print.
    Why: non-uniform object scale bakes into node transforms and breaks normals, bone rolls and collision generation downstream. <!-- ease:source UNVERIFIED reason="downstream-engine behaviour, practice-derived" -->
    Violation: normals flipped or lighting inverted after import in Unity/Unreal; `any(abs(v-1.0) > 1e-4 for v in ob.scale)`.

R6. Keep `scene.unit_settings.scale_length == 1.0` and treat 1 Blender unit as 1 metre.
    Why: `scale_length` is a *display/exchange* multiplier <!-- ease:source S13 anchor="UnitSettings.scale_length: scale used when converting between Blender units and dimensions" -->; rigid-body solvers, the Cycles volume/SSS distances and every exporter's unit conversion assume BU→m. <!-- ease:source UNVERIFIED reason="solver and exporter assumptions not stated in Blender docs" -->
    Violation: rigid bodies fall in slow motion; FBX arrives 100x too big in Unreal.

R7. Purge with `bpy.data.orphans_purge(do_recursive=True)` and re-check `users`, not once.
    Why: purging a mesh can orphan its material, which orphans its image; a single pass only removes one layer (`do_recursive` defaults to False <!-- ease:source S2 anchor="orphans_purge do_recursive=False" -->; measured: pass 1 removed the mesh, pass 2 the material <!-- ease:source S14 anchor="non-recursive purge removed 1 ... second pass removed 1" -->).
    Violation: `.blend` stays large; `len(bpy.data.images)` stays high after one purge call.

R8. Prefer `libraries.load(link=True)` + `override_hierarchy_create()` over appending when the source asset will keep changing.
    Why: linked data stays read-only and updates with the library; a library override adds a local, editable delta layer for transforms/pose without copying geometry.
    Violation: appended copies drift out of sync; file size grows by the mesh size per instance.

R9. Set `use_fake_user = True` on any data-block you create but do not link yet.
    Why: `orphans_purge`, saving and file reload drop zero-user IDs (measured: fake-user material kept, zero-user material gone after save+reload <!-- ease:source S14 anchor="after reload FK True ZU False" -->).
    Violation: `KeyError: 'bpy_prop_collection[key]: key "MyMat" not found'` after reload.

R10. Name every ID you create, deterministically, at creation time.
    Why: Blender auto-suffixes duplicates (`Cube.001`) <!-- ease:source S14 anchor="dup name Body Body.001" -->, and the agent's later lookups by name become non-deterministic across runs.
    Violation: `bpy.data.objects["Body"]` raises `KeyError` on the second run because it became `Body.001`.

R11. Do not read `bpy.context.scene` inside functions that may run before `wm.read_homefile`; take `scene` as a parameter.
    Why: the context scene changes when a file is opened/reset, leaving stale references.
    Violation: `ReferenceError: StructRNA of type Scene has been removed` <!-- ease:source S14 anchor="held scene err ReferenceError" -->.

### 4. bpy patterns

#### 4.1 Deterministic new-scene scaffold (destructive when `reset=True`)

```python
import bpy

SCAFFOLD = ("00_CAM", "10_SUBJECT", "20_SET", "30_LIGHTS", "40_UTIL", "90_EXPORT")

def scaffold_new_scene(reset=False, unit_scale=1.0, fps=24, res=(1920, 1080)):
    """New-scene setup. Returns dict name -> Collection.

    WARNING: reset=True DELETES the current scene and every unsaved object in
    it. Use it only when starting a file from nothing. To configure a scene
    you are already working in, use the non-destructive `scaffold()` in
    scripts/agent-verify-lib.py instead.
    """
    if reset:
        # use_empty=True gives a file with no default cube/camera/light.
        bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)

    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'          # 'NONE'|'METRIC'|'IMPERIAL' (enum verified 5.2.0)
    scene.unit_settings.scale_length = unit_scale  # keep 1.0 => 1 BU == 1 m
    scene.unit_settings.system_rotation = 'DEGREES'
    scene.render.fps = fps
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.frame_start, scene.frame_end = 1, 1

    cols = {}
    for name in SCAFFOLD:
        col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if col.name not in scene.collection.children:
            scene.collection.children.link(col)
        cols[name] = col
    return cols

def put(ob, col, scene=None):
    """Link `ob` into exactly one collection."""
    scene = scene or bpy.context.scene
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    if ob.name not in col.objects:
        col.objects.link(ob)
    return ob
```

`scaffold_new_scene()` makes every later lookup (`cols["10_SUBJECT"]`)
name-stable. Numeric prefixes keep the outliner order deterministic. The block was
executed on Blender 5.2.0 and produced the six collections with `scale_length == 1.0` and 24 fps <!-- ease:source S15 anchor="unit enums; scaffold executed in harness" -->.

#### 4.2 Create objects without operators

```python
import bpy

def new_mesh_object(name, verts, faces, col):
    me = bpy.data.meshes.new(name)                  # name the DATA too
    me.from_pydata(verts, [], faces)
    me.update()
    me.validate(verbose=False)                      # returns True if it FIXED something  [ease:source S15 anchor="Mesh.validate returns True when geometry corrected"]
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob

def new_empty(name, col, kind='PLAIN_AXES', size=1.0):
    ob = bpy.data.objects.new(name, None)           # object_data=None -> Empty
    ob.empty_display_type = kind
    ob.empty_display_size = size
    col.objects.link(ob)
    return ob
```

#### 4.3 Nested collections and collection instancing

```python
import bpy

def child_collection(name, parent):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in parent.children:
        parent.children.link(col)
    return col

def instance_collection(col, name, location=(0, 0, 0), into=None):
    """One Empty that renders the whole collection. Cheap: geometry is shared."""
    inst = bpy.data.objects.new(name, None)
    inst.instance_type = 'COLLECTION'          # 'NONE'|'VERTS'|'FACES'|'COLLECTION'
    inst.instance_collection = col
    inst.location = location
    (into or bpy.context.scene.collection).objects.link(inst)
    return inst

# The instance is placed relative to col.instance_offset; set it so the
# collection's "origin" is where you want the empty to sit.
# col.instance_offset = (0.0, 0.0, 0.0)
```

A collection that is *only* used as an instancing source should not also be a
child of `scene.collection`, or it renders twice (measured: 2 instances of the
object while both linked and instanced, 1 after `exclude=True` <!-- ease:source S15 anchor="Q instances 2 then 1" -->). Either unlink it from the
scene, or link it and set `exclude = True` on its layer collection.

#### 4.4 The three visibility axes, resolved

```python
import bpy

def find_layer_collection(layer_col, name):
    if layer_col.collection.name == name:
        return layer_col
    for child in layer_col.children:
        hit = find_layer_collection(child, name)
        if hit:
            return hit
    return None

vl  = bpy.context.view_layer
lc  = find_layer_collection(vl.layer_collection, "20_SET")
col = bpy.data.collections["20_SET"]
ob  = bpy.data.objects["Backdrop"]

# NOTE: A-C are ALTERNATIVES, not a sequence. After A) the object is no longer in
# the view layer, so B) `ob.hide_set()` raises "cannot be hidden because it is not
# in View Layer" (observed 5.2.0).
# A) PER VIEW LAYER, removed from the depsgraph entirely (checkbox in outliner)
lc.exclude = True            # cheapest; objects are not evaluated at all

# B) PER VIEW LAYER, temporary hide (eye icon)
lc.hide_viewport = True      # LayerCollection.hide_viewport  != Collection.hide_viewport
ob.hide_set(True, view_layer=vl)          # object equivalent of the eye  [ease:source S1 anchor="hide_set: per view layer"]
print(ob.hide_get(view_layer=vl))

# C) GLOBAL, stored on the data-block (monitor / camera icons)
col.hide_viewport = True     # "Globally disable in viewports"
col.hide_render   = True     # "Globally disable in renders"
ob.hide_viewport  = True
ob.hide_render    = True

# D) Per view layer compositing helpers (Cycles)
lc.holdout       = True      # punch alpha hole  [ease:source S9 anchor="Holdout: renders as transparent regions"]
lc.indirect_only = True      # contribute only via bounces  [ease:source S13 anchor="rna LayerCollection.indirect_only"]
print(lc.is_visible)         # read-only, resolved against parents
```

Cheat sheet of what each one affects. Measured on Blender 5.2.0 LTS (viewport
depsgraph = `evaluated_depsgraph_get()`; F12 = Cycles render, alpha of a
covering quad; glTF = `export_scene.gltf`, the only exporter tested) <!-- ease:source S11 anchor="vis rows (viewport_dg_has_B)" --><!-- ease:source S12 anchor="render rows (center_alpha)" --><!-- ease:source S12 anchor="gltf exclude/Object.hide_viewport rows" -->:

| Flag | Scope | In viewport depsgraph | F12 render | glTF default options | glTF `use_visible=True` | glTF `use_renderable=True` |
|---|---|---|---|---|---|---|
| `LayerCollection.exclude` | view layer | no | hidden | exported | filtered out | exported |
| `LayerCollection.hide_viewport` | view layer | yes | **visible** | exported | filtered out | exported |
| `Collection.hide_viewport` | global | no | **visible** | exported | filtered out | exported |
| `Collection.hide_render` | global | yes | hidden | exported | exported | filtered out |
| `Object.hide_viewport` | global | no | **visible** | exported | filtered out | exported |
| `Object.hide_render` | global | yes | hidden | exported | exported | filtered out |
| `Object.hide_set()` | view layer | no | **visible** | exported | filtered out | exported |

The glTF exporter exports everything by default, including `exclude`d objects;
`use_visible=True` is what honours the viewport-side flags and
`use_renderable=True` is what honours `hide_render` <!-- ease:source S11 anchor="gltf rows" --><!-- ease:source S12 anchor="gltf exclude {use_visible: True} has_B False" -->. Other exporters (FBX, USD, OBJ) were not measured
<!-- ease:source UNVERIFIED reason="only glTF exporter behaviour measured; other exporters' filter options not tested" -->.

#### 4.5 Users, orphans, purging

```python
import bpy

def report_orphans():
    buckets = {}
    for attr in ("objects", "meshes", "materials", "images", "node_groups",
                 "actions", "collections", "armatures", "curves", "textures"):
        coll = getattr(bpy.data, attr)
        buckets[attr] = [d.name for d in coll if d.users == 0]
    return buckets

# One purge pass removes one "layer" of orphans; do_recursive does the closure.
removed = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
                                 do_recursive=True)
print("purged", removed)

# Who actually uses this datablock?
umap = bpy.data.user_map(subset=[bpy.data.meshes["Body"]])
print({k.name: [u.name for u in v] for k, v in umap.items()})

# Replace every usage of A with B, then A becomes an orphan.
bpy.data.materials["Old"].user_remap(bpy.data.materials["New"])

# Protect something you are not ready to link yet.
bpy.data.materials["Staging"].use_fake_user = True
```

`ID.users` counts the fake user too, so an unlinked-but-protected ID reports
`users == 1`. Use `ID.use_fake_user` to disambiguate.

#### 4.6 Append / link / library override

```python
import bpy

SRC = "/assets/kit.blend"

# --- APPEND (copy into this file, fully editable, no link back) -------------
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.collections = [n for n in src.collections if n.startswith("KIT_")]
    dst.materials   = ["Steel"]
for col in dst.collections:
    bpy.context.scene.collection.children.link(col)   # loaded IDs need linking

# --- LINK (read-only reference; file stays small, stays in sync) -----------
with bpy.data.libraries.load(SRC, link=True) as (src, dst):
    dst.collections = ["KIT_Chair"]
linked = dst.collections[0]

# Instantiate a linked collection: an Empty instancing it (what wm.link does)
inst = bpy.data.objects.new("KIT_Chair_inst", None)
inst.instance_type = 'COLLECTION'
inst.instance_collection = linked
bpy.context.scene.collection.objects.link(inst)

# --- LIBRARY OVERRIDE (linked, but locally transformable/posable) ---------
ov = linked.override_hierarchy_create(
        bpy.context.scene, bpy.context.view_layer,
        reference=None, do_fully_editable=False)
# ov is a local Collection whose members are override IDs; move/pose them.
```

`libraries.load()` full signature (5.2) <!-- ease:source S3 anchor="load signature" --><!-- ease:source S10 anchor="libraries.load doc" -->:
`load(filepath, *, link=False, pack=False, relative=False, set_fake=False,
recursive=False, reuse_local_id=False, assets_only=False,
clear_asset_data=False, create_liboverrides=False, reuse_liboverrides=False,
create_liboverrides_runtime=False)`. Blender 5.0 added *packed linked data* <!-- ease:source S5 anchor="Packed Data: archive libraries" -->;
`src.libraries` entries are `(filepath, is_archive)` named tuples <!-- ease:source S3 anchor="libraries attribute named tuples (filepath, is_archive)" -->, where
`is_archive` marks the new packed-library form <!-- ease:source UNVERIFIED reason="docs name the field but do not define is_archive; inferred from the 5.0 'archive libraries' note" --> — do not assume `filepath` points
at a real file on disk.

Executed on 5.2.0: `link=True` produced a linked `KIT_Chair` and `override_hierarchy_create` returned an override collection whose object could be moved <!-- ease:source S15 anchor="override obj moved 2.0" -->; the linked object's location is also assignable through the instance path, so confirm editability with `override_library` rather than by catching an error <!-- ease:source UNVERIFIED reason="linked-object move did not raise in 5.2.0; the 'is read-only' error text in the failure table is not reproduced" -->.

Operator forms (need `directory` ending in the inner-path, not just filepath):

```python
# bpy.ops.wm.append/link parameters verified  [ease:source S4 anchor="append: link, do_reuse_local_id, instance_collections; link: instance_collections"]
bpy.ops.wm.append(filepath=SRC + "/Collection/KIT_Chair",
                  directory=SRC + "/Collection/", filename="KIT_Chair",
                  link=False, instance_collections=False, do_reuse_local_id=True)
bpy.ops.wm.link(filepath=SRC + "/Collection/KIT_Chair",
                directory=SRC + "/Collection/", filename="KIT_Chair",
                instance_collections=True)
```

Make a linked ID local when you decide to fork it:
`id.make_local(clear_liboverride=True, clear_asset_data=True)`.

#### 4.7 Units and scale sanity

```python
import bpy

def assert_metric(scene=None):
    s = (scene or bpy.context.scene).unit_settings
    assert s.system == 'METRIC', s.system
    assert abs(s.scale_length - 1.0) < 1e-9, s.scale_length

def real_size_mm(ob):
    """World-space bounding box in millimetres, honouring unit scale."""
    k = bpy.context.scene.unit_settings.scale_length * 1000.0
    return tuple(round(d * k, 3) for d in ob.dimensions)
```

The API reference prints `UnitSettings.scale_length` as "default 0.0" <!-- ease:source S13 anchor="rna UnitSettings.scale_length default 0.0" -->; that is a
doc-generation artifact of a dynamically-defaulted float. The factory scene value is
`1.0` (observed 5.2.0 <!-- ease:source S10 anchor="unit.scale_length 1.0" -->) — assert it rather than trusting the printed default.

#### 4.8 Save / load / collection exporters

```python
import bpy

bpy.ops.wm.save_as_mainfile(filepath="/out/shot.blend", compress=True,
                            relative_remap=True, copy=False)
# copy=True writes the file but keeps the session pointing at the old path  [ease:source S15 anchor="save_as_mainfile copy description"].

# open_mainfile / read_homefile REPLACE the whole session: every bpy.data
# reference and collection created above is gone afterwards (ReferenceError or
# KeyError), so run the exporter section below in its own script.
bpy.ops.wm.open_mainfile(filepath="/out/shot.blend", load_ui=False)
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)

# Per-collection export handlers (RNA added in 5.0)  [ease:source S6 anchor="CollectionExports new/remove/move"]
col = bpy.data.collections["90_EXPORT"]
exp = col.exporters.new('IO_FH_gltf2', name="web")
exp.export_properties.filepath = "//export/web.glb"
# col.exporters.remove(exp) ; col.exporters.move(0, 1)
bpy.ops.wm.collection_export_all()
```

Verified file-handler idnames in 5.2: `IO_FH_gltf2`, `IO_FH_fbx`, `IO_FH_obj`,
`IO_FH_stl`, `IO_FH_ply`, `IO_FH_usd`, `IO_FH_alembic` (each accepted by
`col.exporters.new`; `IO_FH_collada` is rejected) <!-- ease:source S11 anchor="exporter IO_FH_* OK, IO_FH_collada ERR" -->. The snippet below, run in 5.2.0, wrote the file and
`collection_export_all` returned FINISHED <!-- ease:source S15 anchor="collection_export_all FINISHED, file written True" -->. **Correction:** the previous advice to discover handlers with
`[t.bl_rna.identifier for t in bpy.types.FileHandler.__subclasses__()]`
lists only Python-registered handlers (in a factory-startup background run it
returned glTF2 plus UI handlers, not fbx/obj/stl/ply/usd/alembic) <!-- ease:source S10 anchor="FileHandlers list" -->. Discover the valid set from the enum error of a
deliberately bad id instead: `col.exporters.new('__BAD__')` raises
`TypeError ... enum "__BAD__" not found in (...)` listing every valid idname <!-- ease:source S11 anchor="exporter IO_FH_collada ERR enum list" -->.

#### 4.9 Safe names

```python
import re, bpy

_SAFE = re.compile(r'[^A-Za-z0-9_]')

def safe_name(name, maxlen=63):
    """Match the strictest consumer (USD ASCII identifier rules)."""
    s = _SAFE.sub('_', name)
    if not s or s[0].isdigit():
        s = '_' + s
    return s[:maxlen]

def rename_all_for_export(collection):
    seen = {}
    for ob in collection.all_objects:
        base = safe_name(ob.name)
        n = seen.get(base, 0); seen[base] = n + 1
        ob.name = base if n == 0 else "{}_{:03d}".format(base, n)
        if ob.data is not None:
            ob.data.name = ob.name + "_data"
```

This mirrors what `blender::io::usd::make_safe_name()` does with
`allow_unicode=False`: every disallowed codepoint becomes `_`, and a leading
digit gets a `_` prefix <!-- ease:source S7 anchor="is_safe_char, need_leading_underscore" --><!-- ease:source S11 anchor="usd 'Chair:Left|x' -> Chair_Left_x" -->. Doing it yourself means the exported hierarchy names
match what you have in `bpy.data`, so round-trips and material lookups line up.

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Error: Object 'X' cannot be selected because it is not in View Layer 'ViewLayer'!` <!-- ease:source S14 anchor="select_set excluded RuntimeError" --> | object linked to a collection that is `exclude=True`, or to no collection | `col.objects.link(ob)`; set `lc.exclude = False` |
| Exporter writes a 0-object file, no traceback | `use_selection=True` with an empty selection (glTF: FINISHED, 0 nodes <!-- ease:source S15 anchor="gltf use_selection empty nodes 0" -->), or `use_visible=True` while everything is `exclude`d | export by `collection=` name instead of selection |
| `KeyError: 'bpy_prop_collection[key]: key "Body" not found'` after reload | ID was orphaned (never linked, no fake user) and dropped on save | link it, or `id.use_fake_user = True` |
| Hidden backdrop still shows up in F12 render | used `hide_viewport` (viewport-only) instead of `hide_render` | `ob.hide_render = True` or `lc.exclude = True` |
| Object appears twice in glTF/FBX | linked into two collections, or the instanced source collection is also scene-linked | `put()` helper in 4.1; `exclude` the source collection |
| `AttributeError: 'NoneType' object has no attribute 'data'` on `context.active_object` | background mode has no active object until you set `view_layer.objects.active` | use `bpy.data` lookups; set active explicitly before ops that need it |
| `ReferenceError: StructRNA of type Object has been removed` | held a Python reference across `open_mainfile` / `read_homefile` / undo | re-fetch by name after any file-level operation |
| Model 100x too large/small in Unity/Unreal | `scale_length != 1.0`, or object scale not applied, or wrong FBX `apply_scale_options` | assert metric+1.0; `transform_apply(scale=True)`; see export-interchange |
| `.blend` keeps growing across runs | single-pass purge, or images packed and never freed | `orphans_purge(do_recursive=True)` in a loop until it returns 0 |
| USD prims named `_1_Chair` when the object was `1 Chair` | USD identifier sanitisation | pre-sanitise names yourself (4.9) |
| Linked asset can't be moved: `AttributeError: ... is read-only` | linked ID without a library override | `id.override_hierarchy_create(scene, view_layer)` |

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `unit_settings.system` | `'METRIC'` | `'METRIC'` | `'METRIC'` | `'METRIC'` | `'METRIC'` |
| `unit_settings.scale_length` | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `unit_settings.length_unit` display | `'METERS'` | `'METERS'` | `'METERS'` | `'CENTIMETERS'` | `'MILLIMETERS'` |
| Working scale of the subject | 0.5–5 m | 1.7–2 m | any | 0.05–0.5 m | 0.01–0.25 m |
| Collection layout | one per material/LOD/export batch | rig / mesh / props / ctrl | per animated element | subject / set / lights / cam | one collection per printable part |
| Object scale applied before handoff | required | required (rig at scale 1) | optional | optional | required |
| `hide_render` on helper geo | yes (colliders, sockets) | yes (ctrl shapes) | yes | yes (light blockers stay renderable) | n/a |
| Instancing strategy | linked dupes + collection instances | linked dupes for props | collection instances + geo nodes | collection instances | avoid (booleans need real geometry) |
| Naming convention | `SM_Part_LOD0`, ASCII only | `DEF_`/`CTRL_` prefixes | free | free | `Part_A_v03` |
| Save `compress=` | True | True | True | True | True |
| Purge before save | yes | yes | yes | yes | yes |
| Fake users on library mats | yes | yes | no | no | n/a |

<!-- ease:source UNVERIFIED reason="section 6 defaults (working scales, naming conventions, per-use-case choices) are practice-derived, not documented by Blender" -->

### 7. Verification checklist

- [ ] `assert bpy.context.scene.unit_settings.scale_length == 1.0` — exporter/physics scale is sane.
- [ ] `assert all(c.name in bpy.context.scene.collection.children for c in SCAFFOLD)` — scaffold really linked.
- [ ] `assert all(len(ob.users_collection) == 1 for ob in bpy.data.objects)` — no accidental double-linking.
- [ ] `assert not [c for c in bpy.data.collections if c.users == 0]` — no orphan collections before save.
- [ ] `assert all(abs(v - 1.0) < 1e-4 for ob in export_set for v in ob.scale)` — scale applied.
- [ ] `assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}', ob.name) for ob in export_set)` — names survive USD/FBX.
- [ ] `dg = bpy.context.evaluated_depsgraph_get(); assert any(o.name == "Subject" for o in dg.objects)` — the subject is actually evaluated (catches `exclude=True`).
- [ ] `assert bpy.data.orphans_purge(do_recursive=True) == 0` on a second call — purge reached a fixed point <!-- ease:source S10 anchor="purge r1 r2 6 0" -->.
- [ ] Viewport screenshot after `lc.exclude = True` shows the branch gone; after `col.hide_viewport = True` it is gone from the viewport but a 16-sample render still contains it.

## Failure Modes (Mandatory)
- **Hidden backdrop still appears in the F12 render** — cause: `hide_viewport` (or `hide_set()`) is viewport-only; measured alpha stayed 1.0 for all viewport-side flags — fix: `ob.hide_render = True` or `lc.exclude = True` <!-- ease:source S12 anchor="render rows" -->.
- **Exported glTF still contains an `exclude`d or hidden object** — cause: the exporter exports everything unless `use_visible`/`use_renderable` is set — fix: pass the matching option (§4.4 matrix) <!-- ease:source S12 anchor="gltf exclude {} has_B True" -->.
- **`ReferenceError: StructRNA of type Collection/Scene has been removed` after `open_mainfile`/`read_homefile`** — cause: held bpy references across a session replacement — fix: re-fetch by name after any file-level operation <!-- ease:source S14 anchor="held scene err" -->.
- **Collection or material vanishes after save+reload** — cause: zero users (no link, no fake user) — fix: link it or set `use_fake_user=True` <!-- ease:source S14 anchor="after reload FK True ZU False" -->.
- **`bpy.data.objects["Body"]` raises KeyError on the second run** — cause: name became `Body.001` <!-- ease:source S14 anchor="dup name Body Body.001" --> — fix: delete or reuse by name before creating.

## Sources
- [S1] bpy.types.Object (Blender Python API) — https://docs.blender.org/api/current/bpy.types.Object.html → knowledge/_evidence/kb-261013/w5-bpy-Object.html — captured 2026-10-13 — sha256 aff5f361c74fa0ec3b89791f20fc2f9acf4f965f0d7b3a38de7936be3501f97d
- [S2] bpy.types.BlendData (orphans_purge, user_map) — https://docs.blender.org/api/current/bpy.types.BlendData.html → knowledge/_evidence/kb-261013/w5-bpy-BlendData.html — captured 2026-10-13 — sha256 957fcc85f3855ae89991759dcac728baf94ae55bb042ea690136307c230f4dd0
- [S3] bpy.types.BlendDataLibraries.load — https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html → knowledge/_evidence/kb-261013/w5-bpy-BlendDataLibraries.html — captured 2026-10-13 — sha256 367599fd3f3d66401cdd2f6e13fd9a359d39f6e183a800893f77445e1494b5f6
- [S4] bpy.ops.wm (append, link, save, open, collection_export_all) — https://docs.blender.org/api/current/bpy.ops.wm.html → knowledge/_evidence/kb-261013/w5-bpy-ops-wm.html — captured 2026-10-13 — sha256 ada74a22a286b954f93ae9389100f8b5ce2ff4f4d9210c355ec95c7d04a395be
- [S5] Blender 5.0 release notes: Core — https://developer.blender.org/docs/release_notes/5.0/core/ → knowledge/_evidence/kb-261013/w5-rn50-core.html — captured 2026-10-13 — sha256 67ec97f066314490d6de2de1a2d1fa10460c43ca6530efbfd443df84a3815f3a
- [S6] Blender 5.0 release notes: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ → knowledge/_evidence/kb-261013/w5-rn50-python.html — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S7] Blender source usd_utils.cc (make_safe_name) — https://projects.blender.org/blender/blender/raw/branch/main/source/blender/io/usd/intern/usd_utils.cc → knowledge/_evidence/kb-261013/w5-usd-utils-src.cc — captured 2026-10-13 — sha256 a9ddd7203b9c0cebb93e35343c9e52f61df24ee7396852a3a99c95212cb8de7e
- [S8] Blender source DNA_ID.h (MAX_ID_NAME) — https://projects.blender.org/blender/blender/raw/branch/main/source/blender/makesdna/DNA_ID.h → knowledge/_evidence/kb-261013/w5-DNA_ID-src.h — captured 2026-10-13 — sha256 844e64cf591d248a141aaf47e1f88b70d34f2edd557c651b5fd4badf2d7d8c31
- [S9] Blender 5.2 Manual: Collections (exclude, holdout) — https://docs.blender.org/manual/en/latest/scene_layout/collections/collections.html → knowledge/_evidence/kb-261013/w5-man-view-layers.html — captured 2026-10-13 — sha256 d86158b82cb3b772368d481e961d4bc1433121207e0cb25629f43f0e1b878569
- [S10] Blender 5.2.0 LTS runtime probe 1 (API shape, defaults, framing math); script w5-probe-blender-52-api.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe-output.txt — captured 2026-10-13 — sha256 9fe8eb4c002bea2338899e4090d52659e26418189a9363838b9dab08fc386974
- [S11] Blender 5.2.0 LTS runtime probe 2 (hide flags, glTF filters, USD names, decimate, alpha); script w5-probe2-blender-52-behaviour.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe2-output.txt — captured 2026-10-13 — sha256 563dd275f28aedc3f35dce792110ba10e400f4467ff7263b1616da0273aa32d1
- [S12] Blender 5.2.0 LTS runtime probe 3 (F12 render alpha test per hide flag, glTF exclude); script w5-probe3-blender-52-render-visibility.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe3-output.txt — captured 2026-10-13 — sha256 7bc31c8d17a854077b7205ff9ca725fdb5aabc12bb871bdfdf37f51f2815e7b0
- [S13] Blender 5.2.0 LTS runtime probe 4 (RNA descriptions, Principled inputs, modifier defaults); script w5-probe4-blender-52-rna-descriptions.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe4-output.txt — captured 2026-10-13 — sha256 bcefc0f57b0b5accab6fe6d589b642ca522734407791b0eb4b795b0280d7c54e
- [S14] Blender 5.2.0 LTS runtime probe 5 (purge, reload, error texts, enums, turntable closure); script w5-probe5-blender-52-misc.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe5-output.txt — captured 2026-10-13 — sha256 2ed858235c4be1a8e6dc98c618b9d757f9e79a72517fb17b92c25d3eb4ca1179
- [S15] Blender 5.2.0 LTS runtime probe 7 (collections, instancing, exporters, linking, overrides); script w5-probe7-blender-52-scene-organization.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe7-output.txt — captured 2026-10-13 — sha256 522111f54f6df6837ed7d9bd1c18886f521475e23230bd1076671d87d1a2b8f0
- Retained unverified note: FBX/Unity/Unreal name-mangling character lists are practice-derived, not stated in Blender docs. <!-- ease:source UNVERIFIED reason="retained from original sources list; no primary source found" -->
- Retained unverified note: `UnitSettings.scale_length` factory value 1.0 (docs print "default 0.0"; treat as a doc artifact and assert at runtime). <!-- ease:source UNVERIFIED reason="retained from original sources list; no primary source found" -->

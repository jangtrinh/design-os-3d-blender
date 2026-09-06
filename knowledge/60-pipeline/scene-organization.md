---
name: scene-organization
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Collections, visibility flags, data-block users/orphans, linking vs appending, units, and a deterministic scene scaffold for headless bpy agents.
loads_with: [export-interchange, optimization-realtime, product-viz-and-shots]
tags: [collections, visibility, datablocks, linking, units, naming, scaffold]
---

# Scene Organization for Agent-Driven Blender

## 1. Mental model

A `.blend` is a database of ID data-blocks (`bpy.data.objects`, `.meshes`,
`.materials`, `.collections`, ...) plus one or more `Scene`s that *reference*
them. An object is only "in the scene" because some Collection links it, and a
Collection is only in the scene because it is a child of `scene.collection` (the
master collection, which is *not* itself in `bpy.data.collections`). Everything
an agent does — export, render, purge, link — walks that graph, so a mistake in
linking shows up much later as "the exporter wrote an empty file".

The single most common agent error is confusing the **three unrelated hide
flags**: `LayerCollection.exclude` (per view layer, removes objects from the
dependency graph entirely), `Collection.hide_viewport` / `Object.hide_viewport`
(global "disable in viewports", the monitor icon), and
`LayerCollection.hide_viewport` / `Object.hide_set()` (per view layer, the eye
icon). Only `exclude` and `hide_render` reliably affect what a renderer or a
depsgraph-based exporter sees. The second most common error is building a scene
by `bpy.ops.mesh.primitive_*_add()` and then relying on `context.active_object`,
which is fragile under `--background`.

Naming matters because names cross the process boundary into FBX/glTF/USD and
into shader/skeleton lookups downstream. Blender 5.0 raised the ID name limit to
255 bytes, but downstream consumers did not.

## 2. Decision first

| Question | Answer | Python |
|---|---|---|
| Need a group that renders, exports and can be instanced? | Collection | `bpy.data.collections.new()` + `scene.collection.children.link()` |
| Need to *temporarily* stop evaluating a whole branch (fastest) | `exclude` | `view_layer.layer_collection.children["X"].exclude = True` |
| Need it invisible in viewport but still rendered | global viewport disable | `col.hide_viewport = True` |
| Need it visible in viewport but not in the render | render disable | `col.hide_render = True` / `ob.hide_render = True` |
| Need N copies sharing one mesh, N transforms | linked duplicate | `ob2 = ob.copy(); ob2.data = ob.data` |
| Need N copies of a whole *set* of objects | collection instance | Empty with `instance_type='COLLECTION'` |
| Need to reuse an asset from another file, editable | append | `bpy.ops.wm.append` / `libraries.load(link=False)` |
| Need to reuse an asset, stay in sync with source | link (+ library override to pose/animate) | `libraries.load(link=True)` then `id.override_hierarchy_create()` |
| Need physically meaningful sizes (physics, print, export) | metric, 1 BU = 1 m | `scene.unit_settings.system='METRIC'; scale_length=1.0` |
| Need to free memory / shrink file | purge | `bpy.data.orphans_purge(do_recursive=True)` |

Naming policy by target:

| Target | Safe character set | Hard notes |
|---|---|---|
| USD | `[A-Za-z_][A-Za-z0-9_]*` (ASCII) | Exporter *rewrites* names: every disallowed codepoint becomes `_`, a leading digit gets a `_` prefix. With `allow_unicode=True` (5.0+ default) XID start/continue codepoints also pass. |
| glTF | anything (JSON strings) | Names are not identifiers, but duplicate names collide in most runtimes' node lookup; keep them unique. |
| FBX | ASCII alnum + `_` recommended | `:` `|` `*` `/` `\` `"` and spaces routinely break Maya/Max/Unity/Unreal name mangling. Not sanitized on the Blender side. |
| Unity / Unreal asset names | ASCII alnum + `_` | Leading digits and spaces get renamed on import; renaming breaks prefab/skeleton bindings. |
| STL / PLY / 3MF | irrelevant | Formats carry no object names (STL solid name at most). |

Practical rule for anything that will leave Blender:
`^[A-Za-z_][A-Za-z0-9_]{0,62}$`.

## 3. Rules

R1. Create data-blocks with `bpy.data.*.new()`, then link explicitly; never rely on `bpy.ops.*_add()` for structure.
    Why: `bpy.data.*.new()` is context-free and returns the object; `ops` variants depend on `context.collection`, selection and mode, all of which are undefined-ish in background mode.
    Violation: `AttributeError: 'NoneType' object has no attribute 'name'` on `context.active_object`, or the object silently lands in the wrong collection.

R2. A new Collection has zero users until linked; link it to `scene.collection.children` (or a parent collection) in the same statement block.
    Why: unlinked collections are orphans and are destroyed by the next `orphans_purge()` or file save/reload.
    Violation: collection disappears after save+reload; `bpy.data.collections['Props'].users == 0`.

R3. Never link the same object into two collections unless you mean it.
    Why: `Collection.objects.link()` adds a user; the object then exports twice with `use_visible`-style options and appears twice in "Full Collection Hierarchy" glTF export.
    Violation: duplicated meshes in the exported file; `len([c for c in bpy.data.collections if ob.name in c.objects]) > 1`.

R4. Use `exclude` to cut evaluation cost, `hide_render` to cut render content, `hide_viewport` only for authoring comfort.
    Why: `exclude=True` removes the branch from the view layer's depsgraph; `hide_viewport` still evaluates the object for the render depsgraph.
    Violation: agent sets `hide_viewport=True` "to hide the backdrop" and the backdrop still appears in the F12 render.

R5. Apply object scale (`bpy.ops.object.transform_apply(scale=True)`) before exporting to FBX/glTF/USD or before physics/print.
    Why: non-uniform object scale bakes into node transforms and breaks normals, bone rolls and collision generation downstream.
    Violation: normals flipped or lighting inverted after import in Unity/Unreal; `any(abs(v-1.0) > 1e-4 for v in ob.scale)`.

R6. Keep `scene.unit_settings.scale_length == 1.0` and treat 1 Blender unit as 1 metre.
    Why: `scale_length` is a *display/exchange* multiplier; rigid-body solvers, the Cycles volume/SSS distances and every exporter's unit conversion assume BU→m.
    Violation: rigid bodies fall in slow motion; FBX arrives 100x too big in Unreal.

R7. Purge with `bpy.data.orphans_purge(do_recursive=True)` and re-check `users`, not once.
    Why: purging a mesh can orphan its material, which orphans its image; a single pass only removes one layer.
    Violation: `.blend` stays large; `len(bpy.data.images)` stays high after one purge call.

R8. Prefer `libraries.load(link=True)` + `override_hierarchy_create()` over appending when the source asset will keep changing.
    Why: linked data stays read-only and updates with the library; a library override adds a local, editable delta layer for transforms/pose without copying geometry.
    Violation: appended copies drift out of sync; file size grows by the mesh size per instance.

R9. Set `use_fake_user = True` on any data-block you create but do not link yet.
    Why: `orphans_purge`, `wm.save_mainfile` and file reload drop zero-user IDs.
    Violation: `KeyError: 'bpy_prop_collection[key]: key "MyMat" not found'` after reload.

R10. Name every ID you create, deterministically, at creation time.
    Why: Blender auto-suffixes duplicates (`Cube.001`), and the agent's later lookups by name become non-deterministic across runs.
    Violation: `bpy.data.objects["Body"]` raises `KeyError` on the second run because it became `Body.001`.

R11. Do not read `bpy.context.scene` inside functions that may run before `wm.read_homefile`; take `scene` as a parameter.
    Why: the context scene changes when a file is opened/reset, leaving stale references.
    Violation: `ReferenceError: StructRNA of type Scene has been removed`.

## 4. bpy patterns

### 4.1 Deterministic new-scene scaffold (destructive when `reset=True`)

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
    scene.unit_settings.system = 'METRIC'          # 'NONE'|'METRIC'|'IMPERIAL'
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
name-stable. Numeric prefixes keep the outliner order deterministic.

### 4.2 Create objects without operators

```python
import bpy

def new_mesh_object(name, verts, faces, col):
    me = bpy.data.meshes.new(name)                  # name the DATA too
    me.from_pydata(verts, [], faces)
    me.update()
    me.validate(verbose=False)                      # returns True if it FIXED something
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

### 4.3 Nested collections and collection instancing

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
child of `scene.collection`, or it renders twice. Either unlink it from the
scene, or link it and set `exclude = True` on its layer collection.

### 4.4 The three visibility axes, resolved

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

# A) PER VIEW LAYER, removed from the depsgraph entirely (checkbox in outliner)
lc.exclude = True            # cheapest; objects are not evaluated at all

# B) PER VIEW LAYER, temporary hide (eye icon)
lc.hide_viewport = True      # LayerCollection.hide_viewport  != Collection.hide_viewport
ob.hide_set(True, view_layer=vl)          # object equivalent of the eye
print(ob.hide_get(view_layer=vl))

# C) GLOBAL, stored on the data-block (monitor / camera icons)
col.hide_viewport = True     # "Globally disable in viewports"
col.hide_render   = True     # "Globally disable in renders"
ob.hide_viewport  = True
ob.hide_render    = True

# D) Per view layer compositing helpers (Cycles)
lc.holdout       = True      # punch alpha hole
lc.indirect_only = True      # contribute only via bounces
print(lc.is_visible)         # read-only, resolved against parents
```

Cheat sheet of what each one affects:

| Flag | Scope | Depsgraph | Viewport | F12 render | Depsgraph-based exporters |
|---|---|---|---|---|---|
| `LayerCollection.exclude` | view layer | removed | hidden | hidden | not exported |
| `LayerCollection.hide_viewport` | view layer | evaluated | hidden | **visible** | exported |
| `Collection.hide_viewport` | global | evaluated | hidden | **visible** | exported (unless option filters visibility) |
| `Collection.hide_render` | global | evaluated | visible | hidden | exported unless "renderable only" |
| `Object.hide_viewport` | global | skipped in viewport eval | hidden | **visible** | usually exported |
| `Object.hide_render` | global | evaluated | visible | hidden | exported unless "renderable only" |
| `Object.hide_set()` | view layer | evaluated | hidden | **visible** | exported |

`use_visible` in the glTF/FBX exporters resolves against the *view layer*
visibility, so `exclude` and `hide_set()` are what actually filter it; the
`hide_render` flag maps to `use_renderable`.

### 4.5 Users, orphans, purging

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

### 4.6 Append / link / library override

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

`libraries.load()` full signature (5.2):
`load(filepath, *, link=False, pack=False, relative=False, set_fake=False,
recursive=False, reuse_local_id=False, assets_only=False,
clear_asset_data=False, create_liboverrides=False, reuse_liboverrides=False,
create_liboverrides_runtime=False)`. Blender 5.0 added *packed linked data*;
`src.libraries` entries are `(filepath, is_archive)` named tuples, where
`is_archive` marks the new packed-library form — do not assume `filepath` points
at a real file on disk.

Operator forms (need `directory` ending in the inner-path, not just filepath):

```python
bpy.ops.wm.append(filepath=SRC + "/Collection/KIT_Chair",
                  directory=SRC + "/Collection/", filename="KIT_Chair",
                  link=False, instance_collections=False, do_reuse_local_id=True)
bpy.ops.wm.link(filepath=SRC + "/Collection/KIT_Chair",
                directory=SRC + "/Collection/", filename="KIT_Chair",
                instance_collections=True)
```

Make a linked ID local when you decide to fork it:
`id.make_local(clear_liboverride=True, clear_asset_data=True)`.

### 4.7 Units and scale sanity

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

The API reference prints `UnitSettings.scale_length` as "default 0.0"; that is a
doc-generation artifact of a dynamically-defaulted float. The factory value is
`1.0` — assert it rather than trusting it.

### 4.8 Save / load / collection exporters

```python
import bpy

bpy.ops.wm.save_as_mainfile(filepath="/out/shot.blend", compress=True,
                            relative_remap=True, copy=False)
# copy=True writes the file but keeps the session pointing at the old path.

bpy.ops.wm.open_mainfile(filepath="/out/shot.blend", load_ui=False)
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)

# Per-collection export handlers (RNA added in 5.0)
col = bpy.data.collections["90_EXPORT"]
exp = col.exporters.new('IO_FH_gltf2', name="web")
exp.export_properties.filepath = "//export/web.glb"
# col.exporters.remove(exp) ; col.exporters.move(0, 1)
bpy.ops.wm.collection_export_all()
```

Verified file-handler idnames in 5.2: `IO_FH_gltf2`, `IO_FH_fbx`, `IO_FH_obj`,
`IO_FH_stl`, `IO_FH_ply`, `IO_FH_usd`, `IO_FH_alembic`. Discover the rest at
runtime with
`[t.bl_rna.identifier for t in bpy.types.FileHandler.__subclasses__()]`.

### 4.9 Safe names

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
digit gets a `_` prefix. Doing it yourself means the exported hierarchy names
match what you have in `bpy.data`, so round-trips and material lookups line up.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Error: Object 'X' can't be selected because it is not in View Layer` | object linked to a collection that is `exclude=True`, or to no collection | `col.objects.link(ob)`; set `lc.exclude = False` |
| Exporter writes a 0-object file, no traceback | `use_selection=True` with an empty selection, or everything is `exclude`d | export by `collection=` name instead of selection |
| `KeyError: 'bpy_prop_collection[key]: key "Body" not found'` after reload | ID was orphaned (never linked, no fake user) and dropped on save | link it, or `id.use_fake_user = True` |
| Hidden backdrop still shows up in F12 render | used `hide_viewport` (viewport-only) instead of `hide_render` | `ob.hide_render = True` or `lc.exclude = True` |
| Object appears twice in glTF/FBX | linked into two collections, or the instanced source collection is also scene-linked | `put()` helper in 4.1; `exclude` the source collection |
| `AttributeError: 'NoneType' object has no attribute 'data'` on `context.active_object` | background mode has no active object until you set `view_layer.objects.active` | use `bpy.data` lookups; set active explicitly before ops that need it |
| `ReferenceError: StructRNA of type Object has been removed` | held a Python reference across `open_mainfile` / `read_homefile` / undo | re-fetch by name after any file-level operation |
| Model 100x too large/small in Unity/Unreal | `scale_length != 1.0`, or object scale not applied, or wrong FBX `apply_scale_options` | assert metric+1.0; `transform_apply(scale=True)`; see export-interchange |
| `.blend` keeps growing across runs | single-pass purge, or images packed and never freed | `orphans_purge(do_recursive=True)` in a loop until it returns 0 |
| USD prims named `_1_Chair` when the object was `1 Chair` | USD identifier sanitisation | pre-sanitise names yourself (4.9) |
| Linked asset can't be moved: `AttributeError: ... is read-only` | linked ID without a library override | `id.override_hierarchy_create(scene, view_layer)` |

## 6. Parameter defaults by use case

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

## 7. Verification checklist

- [ ] `assert bpy.context.scene.unit_settings.scale_length == 1.0` — exporter/physics scale is sane.
- [ ] `assert all(c.name in bpy.context.scene.collection.children for c in SCAFFOLD)` — scaffold really linked.
- [ ] `assert all(len(ob.users_collection) == 1 for ob in bpy.data.objects)` — no accidental double-linking.
- [ ] `assert not [c for c in bpy.data.collections if c.users == 0]` — no orphan collections before save.
- [ ] `assert all(abs(v - 1.0) < 1e-4 for ob in export_set for v in ob.scale)` — scale applied.
- [ ] `assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}', ob.name) for ob in export_set)` — names survive USD/FBX.
- [ ] `dg = bpy.context.evaluated_depsgraph_get(); assert any(o.name == "Subject" for o in dg.objects)` — the subject is actually evaluated (catches `exclude=True`).
- [ ] `assert bpy.data.orphans_purge(do_recursive=True) == 0` on a second call — purge reached a fixed point.
- [ ] Viewport screenshot after `lc.exclude = True` shows the branch gone; after `col.hide_viewport = True` it is gone from the viewport but a 16-sample render still contains it.

## 8. Sources

- [bpy.types.Collection — 5.2](https://docs.blender.org/api/current/bpy.types.Collection.html)
- [bpy.types.LayerCollection — 5.2](https://docs.blender.org/api/current/bpy.types.LayerCollection.html)
- [bpy.types.Object — 5.2](https://docs.blender.org/api/current/bpy.types.Object.html)
- [bpy.types.BlendData (`orphans_purge`, `user_map`) — 5.2](https://docs.blender.org/api/current/bpy.types.BlendData.html)
- [bpy.types.BlendDataLibraries.load — 5.2](https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html)
- [bpy.types.ID (`override_hierarchy_create`, `make_local`, `user_remap`) — 5.2](https://docs.blender.org/api/current/bpy.types.ID.html)
- [bpy.types.UnitSettings — 5.2](https://docs.blender.org/api/current/bpy.types.UnitSettings.html)
- [bpy.ops.wm (append/link/save/open/collection_export_all) — 5.2](https://docs.blender.org/api/current/bpy.ops.wm.html)
- [Blender 5.0 Core release notes — longer ID names, packed linked data](https://developer.blender.org/docs/release_notes/5.0/core/)
- [Blender 5.0 Python API release notes](https://developer.blender.org/docs/release_notes/5.0/python_api/) (`collection.exporters.new/remove/move`, IDProperty storage split)
- [Blender source `source/blender/io/usd/intern/usd_utils.cc`](https://projects.blender.org/blender/blender/src/branch/main/source/blender/io/usd/intern/usd_utils.cc) — USD name sanitisation rules
- [Blender source `source/blender/makesdna/DNA_ID.h`](https://projects.blender.org/blender/blender/src/branch/main/source/blender/makesdna/DNA_ID.h) — `MAX_ID_NAME 258`
- `[UNVERIFIED]` FBX/Unity/Unreal name-mangling character lists are practice-derived, not stated in Blender docs.
- `[UNVERIFIED]` `UnitSettings.scale_length` factory value 1.0 (docs print "default 0.0"; treat as a doc artifact and assert at runtime).

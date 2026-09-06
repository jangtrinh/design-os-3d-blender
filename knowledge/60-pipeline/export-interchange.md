---
name: export-interchange
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Verified 5.2 operator names and arguments for glTF, FBX, USD, OBJ, STL, PLY, Alembic, plus a target-to-settings decision table.
loads_with: [scene-organization, optimization-realtime, 3d-printing]
tags: [gltf, fbx, usd, obj, stl, alembic, export, interchange, draco]
---

# Export & Interchange

## 1. Mental model

Blender's IO layer was rebuilt between 4.2 and 5.0 and the operator namespace no
longer matches what most models remember. OBJ, STL, PLY, USD, Alembic and (since
5.0) FBX **import** are C++ operators in `bpy.ops.wm.*`. Only glTF and FBX
**export** are still Python add-ons, and they live in `bpy.ops.export_scene.*`.
Collada was removed entirely in 5.0. Nothing exports 3MF natively.

An export is a lossy projection of Blender's node-graph world onto a fixed
schema. The agent's job is to decide *what is allowed to be lost* before writing
any code: glTF keeps a metal/rough PBR subset and skinned animation; FBX keeps
hierarchy, skinning and takes but mangles bones and units; USD keeps stage
structure and instancing; OBJ/STL/PLY keep triangles and nothing else; Alembic
keeps baked, per-frame geometry.

The most common agent failure is calling `bpy.ops.export_scene.obj` (removed in
4.0) or `bpy.ops.export_mesh.stl` (removed in 4.2) and then hallucinating a fix.
Second most common: exporting with `use_selection=True` in `--background`, where
nothing is selected, producing a valid but empty file with no traceback.

## 2. Decision first

| Target consumer | Format | Operator (5.2) | Non-obvious settings |
|---|---|---|---|
| Web / three.js / babylon / model-viewer | glTF binary | `bpy.ops.export_scene.gltf` | `export_format='GLB'`, `export_yup=True`, `export_apply=True`, `export_draco_mesh_compression_enable=True` |
| Godot 4 | glTF binary | `export_scene.gltf` | `export_format='GLB'`, `export_animation_mode='ACTIONS'`, no Draco (Godot re-compresses) |
| Unity (URP/HDRP) | FBX | `export_scene.fbx` | `apply_scale_options='FBX_SCALE_ALL'`, `axis_forward='-Z'`, `axis_up='Y'`, `add_leaf_bones=False`, `bake_anim_use_nla_strips=False` |
| Unreal Engine 5 | FBX | `export_scene.fbx` | `global_scale=1.0`, `apply_scale_options='FBX_SCALE_NONE'`, `axis_forward='-Z'`, `axis_up='Y'`, `add_leaf_bones=False`, `primary_bone_axis='Y'`, `secondary_bone_axis='X'`, `use_armature_deform_only=True` |
| Maya / 3ds Max / C4D round-trip | FBX | `export_scene.fbx` | `apply_scale_options='FBX_SCALE_UNITS'`, `mesh_smooth_type='FACE'`, `use_tspace=True` |
| VFX pipeline, layered scene assembly, Omniverse | USD / USDZ | `bpy.ops.wm.usd_export` | `export_materials=True`, `generate_preview_surface=True`, `root_prim_path='/root'`, `convert_scene_units='METERS'` |
| iOS AR Quick Look | USDZ | `bpy.ops.wm.usd_export` (`.usdz` path) | `usdz_downscale_size='2048'`, `generate_preview_surface=True` |
| Baked geometry/animation cache to Houdini/Maya | Alembic | `bpy.ops.wm.alembic_export` | `evaluation_mode='RENDER'`, set `start`/`end`, `flatten=False` |
| 3D printing | STL / OBJ | `bpy.ops.wm.stl_export` | `global_scale=1000` **or** `use_scene_unit=True` — never both. See 3d-printing.md |
| CAD / scan interchange, no materials | PLY / OBJ | `wm.ply_export` / `wm.obj_export` | `export_triangulated_mesh=True` |
| Photogrammetry point clouds | PLY | `wm.ply_export` | `export_colors='SRGB'`, `ascii_format=False` |
| Anything Collada | **impossible in 5.x** | removed in 5.0 | convert via glTF or FBX |
| 3MF | not native | extension `ThreeMF_io` (`bl_ext.blender_org.ThreeMF_io`) | see 3d-printing.md |

Operator name map — memorise this, it is what LLMs get wrong:

| Format | Export | Import | Provider |
|---|---|---|---|
| glTF 2.0 | `bpy.ops.export_scene.gltf` | `bpy.ops.import_scene.gltf` | core add-on `io_scene_gltf2` |
| FBX | `bpy.ops.export_scene.fbx` | `bpy.ops.wm.fbx_import` (default since 5.0) | export: add-on `io_scene_fbx`; import: C++ |
| FBX (legacy import) | — | `bpy.ops.import_scene.fbx` | add-on `io_scene_fbx`, deprecated |
| Wavefront OBJ | `bpy.ops.wm.obj_export` | `bpy.ops.wm.obj_import` | C++ (since 3.3/3.4) |
| STL | `bpy.ops.wm.stl_export` | `bpy.ops.wm.stl_import` | C++ (since 4.2) |
| PLY | `bpy.ops.wm.ply_export` | `bpy.ops.wm.ply_import` | C++ (since 4.0) |
| USD | `bpy.ops.wm.usd_export` | `bpy.ops.wm.usd_import` | C++ |
| Alembic | `bpy.ops.wm.alembic_export` | `bpy.ops.wm.alembic_import` | C++ |
| BVH | `bpy.ops.export_anim.bvh` | `bpy.ops.import_anim.bvh` | core add-on `io_anim_bvh` |
| Collada | **removed in 5.0** | **removed in 5.0** | — |

## 3. Rules

R1. Resolve the operator's real argument list at runtime before trusting any remembered name.
    Why: exporter arguments were added, renamed and removed in 4.2, 5.0 and 5.2 (`export_textures` → `export_textures_mode`, `attr_import_mode` → `property_import_mode`, `visible_objects_only` removed).
    Violation: `TypeError: Converting py args to operator properties: WM_OT_usd_export.export_textures: keyword "export_textures" unrecognized`.

R2. Never export by selection in background mode; export by collection or by explicit visibility.
    Why: `--background` starts with an empty selection and `use_selection=True` then silently writes an empty file.
    Violation: a 900-byte `.glb` with `"meshes": []` and exit code 0.

R3. Enable the IO add-on defensively before calling `export_scene.*`.
    Why: `io_scene_gltf2`/`io_scene_fbx` are user-preference driven; a headless run with a stripped config, or `--factory-startup` on a custom build, may not have them enabled.
    Violation: `AttributeError: module 'bpy.ops.export_scene' has no attribute 'gltf'`.

R4. Apply object scale and rotation before FBX/USD export unless you deliberately want them in the node transforms.
    Why: FBX bakes Blender's Z-up→Y-up conversion into either the node transforms or the FBX unit scale depending on `apply_scale_options`/`bake_space_transform`; unapplied scale multiplies with that.
    Violation: a 1x model that is 0.01x in Unreal, or a mesh rotated -90° on X after import.

R5. Use `export_apply=True` (glTF) / `use_mesh_modifiers=True` (FBX) only when you have already decided modifiers should be destructive.
    Why: `export_apply` evaluates the depsgraph, which drops shape keys on modified meshes.
    Violation: morph targets missing from the `.glb`; `"targets"` array absent on every primitive.

R6. For glTF animation, put every action on its own NLA track and use `export_animation_mode='ACTIONS'`.
    Why: since 4.4 slotted actions, tracks are merged **by action**, not by track name; loose actions that are neither active nor stashed are simply not exported.
    Violation: `.glb` contains one animation named "Animation" or none at all.

R7. Never combine `global_scale` and `use_scene_unit` in the STL/OBJ exporters.
    Why: they multiply. `use_scene_unit=True` already converts via `scene.unit_settings.scale_length`.
    Violation: a 1,000,000x model; slicer reports build volume overflow.

R8. Set `evaluation_mode='RENDER'` for USD/Alembic/STL when the modifier render level differs from the viewport level.
    Why: the default for USD/Alembic is `'RENDER'` but STL's is also `'DAG_EVAL_RENDER'` while OBJ defaults to `'DAG_EVAL_VIEWPORT'` — the inconsistency is real.
    Violation: OBJ exports a subdivision level 1 cage instead of the level 3 render mesh.

R9. Write to an absolute path and verify the file exists and is non-trivial afterwards.
    Why: `//`-relative paths resolve against the current `.blend`, which is unsaved (empty) in a fresh background session.
    Violation: file written to CWD or `/`; `os.path.exists()` False with no traceback.

R10. Prefer `export_materials='EXPORT'` + `export_image_format='AUTO'` for glTF and let the exporter transcode, unless you have already packed ORM textures.
    Why: the exporter can copy an image verbatim only when the node graph matches the glTF packing convention (R in occlusion, G in roughness, B in metallic); otherwise it re-bakes, slowly.
    Violation: exports take minutes and the log shows image conversion warnings.

R11. Triangulate explicitly for realtime targets rather than relying on the importer.
    Why: n-gon triangulation differs between exporters and engines, which changes lightmap seams and normal-map tangents.
    Violation: shading seams that appear only in the engine, not in Blender.

## 4. bpy patterns

### 4.1 Discover a version's real arguments (do this before writing an export call)

```python
import bpy

def op_props(op):
    """op: e.g. bpy.ops.export_scene.gltf -> {name: (type, default)}"""
    rna = op.get_rna_type()                     # BPyOpFunction.get_rna_type()
    out = {}
    for p in rna.properties:
        if p.identifier == "rna_type":
            continue
        default = getattr(p, "default", None)
        if p.type == 'ENUM':
            default = (getattr(p, "default", None),
                       [i.identifier for i in p.enum_items])
        out[p.identifier] = (p.type, default)
    return out

print(sorted(op_props(bpy.ops.export_scene.gltf)))
print(op_props(bpy.ops.wm.usd_export)["export_textures_mode"])
print(bpy.ops.export_scene.gltf.idname(), bpy.ops.export_scene.gltf.bl_options)
print(bpy.ops.export_scene.gltf.__doc__)
```

`get_rna_type()`, `idname()`, `idname_py()`, `poll()` and `bl_options` are all
methods/attributes on the operator callable itself (`BPyOpFunction`). This is
the only reliable way to know what a given build accepts.

### 4.2 Enable the IO add-ons (bundled core add-ons keep plain module names)

```python
import bpy, addon_utils

def ensure_addon(module):
    loaded_default, loaded_state = addon_utils.check(module)
    if not loaded_state:
        addon_utils.enable(module, default_set=False, persistent=True)
    return addon_utils.check(module)[1]

assert ensure_addon("io_scene_gltf2")
assert ensure_addon("io_scene_fbx")
```

In 5.2 the bundled add-ons live in `scripts/addons_core/` and are addressed by
their **plain module name**, not a `bl_ext.*` path: `io_scene_gltf2`,
`io_scene_fbx`, `io_anim_bvh`, `io_curve_svg`, `io_mesh_uv_layout`,
`node_wrangler`, `pose_library`, `rigify`, `hydra_storm`, `bl_pkg`,
`viewport_vr_preview`, `ui_translate`. The glTF add-on itself reads
`bpy.context.preferences.addons['io_scene_gltf2'].preferences`, which confirms
the flat key.

Only add-ons installed **as extensions** get the prefixed module name
`bl_ext.<repo_module>.<extension_id>`; the three default repositories are
`blender_org`, `user_default` and `system`. Example:
`bl_ext.blender_org.print3d_toolbox`. Install one headlessly with:

```python
bpy.ops.extensions.repo_sync_all()
bpy.ops.extensions.package_install(repo_index=0, pkg_id="print3d_toolbox",
                                   enable_on_install=True)
```

### 4.3 glTF 2.0 export — full 5.2 signature, grouped

Verified `bpy.ops.export_scene.gltf` keyword arguments (5.2):

```text
FILE      filepath check_existing filter_glob export_format ui_tab export_copyright
          gltf_export_id will_save_settings export_loglevel
IMAGES    export_image_format export_image_add_webp export_image_webp_fallback
          export_texture_dir export_jpeg_quality export_image_quality
          export_keep_originals export_unused_images export_unused_textures
MESH      export_texcoords export_normals export_tangents export_attributes
          use_mesh_edges use_mesh_vertices export_apply export_shared_accessors
          export_gn_mesh export_gpu_instances
VCOL      export_vertex_color export_vertex_color_name export_all_vertex_colors
          export_active_vertex_color_when_no_material
MATERIAL  export_materials export_original_specular
SCENE     use_selection use_visible use_renderable use_active_collection
          use_active_collection_with_nested use_active_scene collection
          at_collection_center export_extras export_cameras export_lights
          export_yup export_hierarchy_full_collections
COMPRESS  export_draco_mesh_compression_enable export_draco_mesh_compression_level
          export_draco_position_quantization export_draco_normal_quantization
          export_draco_texcoord_quantization export_draco_color_quantization
          export_draco_generic_quantization
          export_meshopt_compression_enable export_meshopt_extension
          export_use_gltfpack export_gltfpack_tc export_gltfpack_tq
          export_gltfpack_si export_gltfpack_sa export_gltfpack_slb
          export_gltfpack_vp export_gltfpack_vt export_gltfpack_vn
          export_gltfpack_vc export_gltfpack_vpi export_gltfpack_noq
          export_gltfpack_kn
SKIN      export_skins export_influence_nb export_all_influences
          export_def_bones export_rest_position_armature
          export_armature_object_remove export_leaf_bone
          export_hierarchy_flatten_bones export_hierarchy_flatten_objs
          export_anim_single_armature export_reset_pose_bones
MORPH     export_morph export_morph_normal export_morph_tangent
          export_morph_animation export_morph_reset_sk_data
          export_try_sparse_sk export_try_omit_sparse_sk
ANIM      export_animations export_animation_mode export_merge_animation
          export_frame_range export_frame_step export_force_sampling
          export_sampling_interpolation_fallback export_bake_animation
          export_current_frame export_anim_slide_to_zero export_negative_frame
          export_anim_scene_split_object export_nla_strips
          export_nla_strips_merged_animation_name export_action_filter
          export_extra_animations export_pointer_animation
          export_convert_animation_pointer
          export_optimize_animation_size export_optimize_animation_keep_anim_armature
          export_optimize_animation_keep_anim_object export_optimize_disable_viewport
LIGHTING  export_import_convert_lighting_mode
```

Enum values verified from the add-on source:

- `export_format`: `'GLB'` (default), `'GLTF_SEPARATE'`, and `'GLTF_EMBEDDED'`
  only when enabled in the add-on preferences. It is a dynamic enum, so the RNA
  default prints as `''`; **always pass it explicitly**.
- `export_image_format`: `'AUTO'`, `'JPEG'`, `'WEBP'`, `'NONE'`.
- `export_materials`: `'EXPORT'`, `'PLACEHOLDER'`, `'VIEWPORT'`, `'NONE'`.
- `export_vertex_color`: `'MATERIAL'`, `'ACTIVE'`, `'NAME'`, `'NONE'`.
- `export_animation_mode`: `'ACTIONS'`, `'ACTIVE_ACTIONS'`, `'BROADCAST'`,
  `'NLA_TRACKS'`, `'SCENE'`.
- `export_merge_animation`: `'ACTION'` (default), `'NLA_TRACK'`, `'NONE'`.
- `export_meshopt_extension`: `'EXT_meshopt_compression'` (default) or
  `'KHR_meshopt_compression'`.
- `export_import_convert_lighting_mode`: `'SPEC'` (default, physical units),
  `'COMPAT'`, `'RAW'`.

```python
import bpy, os

def export_glb(path, collection=None, draco=True, animations=False):
    kw = dict(
        filepath=os.path.abspath(path),
        export_format='GLB',
        export_yup=True,                 # glTF is +Y up; leave True
        export_apply=True,               # evaluate modifiers (drops shape keys!)
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_texcoords=True, export_normals=True, export_tangents=False,
        export_cameras=False, export_lights=False,
        export_extras=True,              # custom props -> glTF "extras"
        use_selection=False, use_visible=False, use_renderable=False,
        export_animations=animations,
        export_draco_mesh_compression_enable=draco,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
    )
    if collection:
        kw.update(use_active_collection=False, collection=collection)
    if animations:
        kw.update(export_animation_mode='ACTIONS',
                  export_merge_animation='ACTION',
                  export_force_sampling=True,
                  export_frame_step=1,
                  export_optimize_animation_size=True,
                  export_rest_position_armature=True,
                  export_leaf_bone=False,
                  export_def_bones=True,
                  export_influence_nb=4)
    bpy.ops.export_scene.gltf(**kw)
    return assert_valid_glb(kw["filepath"])   # defined in the next block
```

**Do not gate on file size.** A correct single-cube GLB is far below any "looks big
enough" threshold: measured on 5.2.0 with exactly the kwargs above, one default cube is
**1120 B with Draco / 1732 B plain** (audit-02 measured 936 B / 1400 B for its own
variant of the scene). The pre-2026-09 gate here was `assert getsize(...) > 2048`, which
reports a perfectly good small asset as a failure. Parse the container instead — it is
cheap, it catches truncation and half-written files, and it proves geometry arrived:

```python
import json, os, struct

def assert_valid_glb(path, min_meshes=1):
    """Validate a .glb by its own header + JSON chunk. Returns (bytes, mesh_count)."""
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        magic, version, total = struct.unpack("<4sII", fh.read(12))
        assert magic == b"glTF", f"not a GLB container: magic={magic!r}"
        assert version == 2, f"GLB container version {version}, expected 2"
        assert total == size, f"header length {total} != file size {size} (truncated?)"
        chunk_len, chunk_type = struct.unpack("<II", fh.read(8))
        assert chunk_type == 0x4E4F534A, "first chunk is not JSON"      # b'JSON'
        doc = json.loads(fh.read(chunk_len).decode("utf-8"))
    n = len(doc.get("meshes", []))
    assert n >= min_meshes, f"GLB contains {n} meshes, expected >= {min_meshes}"
    return size, n
```

Verified 2026-09-06 on 5.2.0: passes on both the Draco and the plain single-cube export
(`(1120, 1)` / `(1732, 1)`); on a file truncated to half its length it fails with
`header length 1732 != file size 866`. For `.gltf` (separate JSON) the same check is
`json.load(open(path))` plus the same `meshes` assertion — there is no binary header.
Stronger still, when you can afford ~0.5 s: re-import into a fresh
`blender --factory-startup -b` and assert the object/vertex counts you exported.

`collection=` names a collection to export without touching selection — the
robust background-safe entry point.

### 4.4 What glTF keeps and what it silently drops

Principled BSDF → glTF metal/rough mapping (verified against the 5.2 manual):

| Principled input | glTF | Survives? |
|---|---|---|
| Base Color (value, RGB node, or Image Texture) | `pbrMetallicRoughness.baseColorFactor` / `baseColorTexture` | yes |
| Metallic, Roughness | `metallicFactor`, `roughnessFactor`, or packed `metallicRoughnessTexture` (B=metal, G=rough) | yes |
| Alpha + material blend mode | `alphaMode` / `alphaCutoff` | yes |
| Normal (via Normal Map node, **Tangent Space only**) | `normalTexture` + `scale` | yes |
| Emission Color + Emission Strength | `emissiveFactor`; >1.0 promotes to `KHR_materials_emissive_strength` | yes |
| IOR | `KHR_materials_ior` (1.5 assumed if absent) | yes |
| Transmission | `KHR_materials_transmission` | yes |
| Coat / Coat Roughness / Coat Normal | `KHR_materials_clearcoat` (R=coat, G=roughness) | yes |
| Sheen Weight / Roughness / Tint | `KHR_materials_sheen` | yes |
| Specular / Specular Tint | `KHR_materials_specular` | yes |
| Anisotropic / Anisotropic Rotation | `KHR_materials_anisotropy` | yes |
| Dispersion (needs `KHR_materials_volume`) | `KHR_materials_dispersion` | yes (5.2) |
| Thin Film Thickness / IOR | `KHR_materials_iridescence` | yes (5.2) |
| Mapping node on a texture | `KHR_texture_transform` | location/rotation/scale only |
| Baked AO via **`glTF Material Output`** node group, `Occlusion` input | `occlusionTexture` (R channel) | only via that node group |
| Subsurface / SSS radius | — | **dropped** |
| Displacement, Bump node | — | **dropped** (bake to a normal map first) |
| Any procedural node (Noise, Voronoi, Musgrave, ColorRamp chains) | — | **dropped** unless it resolves to a constant; bake it |
| Object-space or world-space normal maps | — | **dropped**; tangent space only |
| Volume shaders, Cycles-only nodes | — | **dropped** |
| Non-Principled shaders (Glass, Toon, Diffuse alone) | — | approximated or dropped; use Principled or `KHR_materials_unlit` |
| Multiple UV maps | up to `TEXCOORD_n` | kept if referenced |
| Vertex colors | `COLOR_0`, `COLOR_1`… | see `export_vertex_color` mode |
| Modifiers | — | only with `export_apply=True` |
| Constraints, drivers, physics | — | **dropped**; bake to keyframes |
| Lights | `KHR_lights_punctual` (needs `export_lights=True`) | Sun/Point/Spot only, Area dropped |
| Animated material / light properties | `KHR_animation_pointer` (needs `export_pointer_animation=True`) | limited runtime support |

Compression choice:

| Method | Extension | When |
|---|---|---|
| Draco | `KHR_draco_mesh_compression` | smallest files; needs a Draco-capable loader; slow decode on low-end |
| meshopt | `EXT_meshopt_compression` / `KHR_meshopt_compression` | good ratio, very fast decode, widest modern support (5.2 added export) |
| gltfpack | external `gltfpack` binary via `export_use_gltfpack=True` | full pipeline optimisation (quantisation + meshopt); requires the binary on PATH |

### 4.5 FBX export — full 5.2 signature and the axis/scale problem

```python
bpy.ops.export_scene.fbx(
    filepath='', check_existing=True, filter_glob='*.fbx',
    use_selection=False, use_visible=False, use_active_collection=False,
    collection='',
    global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',
    use_space_transform=True, bake_space_transform=False,
    object_types={'ARMATURE','CAMERA','EMPTY','LIGHT','MESH','OTHER'},
    use_mesh_modifiers=True, use_mesh_modifiers_render=True,
    mesh_smooth_type='OFF', colors_type='SRGB', prioritize_active_color=False,
    use_subsurf=False, use_mesh_edges=False, use_tspace=False,
    use_triangles=False, use_custom_props=False,
    add_leaf_bones=True, primary_bone_axis='Y', secondary_bone_axis='X',
    use_armature_deform_only=False, armature_nodetype='NULL',
    bake_anim=True, bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True, bake_anim_step=1.0,
    bake_anim_simplify_factor=1.0,
    path_mode='AUTO', embed_textures=False,
    batch_mode='OFF', use_batch_own_dir=True, use_metadata=True,
    axis_forward='-Z', axis_up='Y')
```

`axis_forward`/`axis_up` ∈ `{'X','Y','Z','-X','-Y','-Z'}`. Blender is Y-forward,
Z-up. The FBX default `-Z` forward / `Y` up is what Maya, Unity and Unreal
expect — **do not "fix" it**.

`apply_scale_options` (verified enum + semantics):

| Value | Custom scale goes to | Unit scale goes to | Use when |
|---|---|---|---|
| `'FBX_SCALE_NONE'` (default, "All Local") | object transforms | object transforms | Unreal; anything that ignores FBX global scale |
| `'FBX_SCALE_UNITS'` ("FBX Units Scale") | object transforms | FBX global scale | Maya/Max round-trip; DCCs that read FBX units |
| `'FBX_SCALE_CUSTOM'` ("FBX Custom Scale") | FBX global scale | object transforms | rarely |
| `'FBX_SCALE_ALL'` ("FBX All") | FBX global scale | FBX global scale | Unity, which reads the FBX unit header |

Armature/leaf-bone problems and their fixes:

- **Extra `_end` bones in the engine skeleton** → `add_leaf_bones=False`. Blender
  writes a zero-length terminal bone per chain purely to encode bone length; most
  engines import them as real joints.
- **Bones rotated 90° / rolled** → FBX bones are conventionally -X aligned,
  Blender's are Y aligned. Keep `primary_bone_axis='Y'`,
  `secondary_bone_axis='X'` for Unreal/Unity; the importer's "Automatic Bone
  Orientation" handles the rest. Changing these without also changing the import
  side breaks retargeting.
- **Non-deform helper bones cluttering the skeleton** →
  `use_armature_deform_only=True`.
- **Armature appears as a mesh/null oddity** → `armature_nodetype='NULL'` is
  correct for almost everything; `'ROOT'`/`'LIMBNODE'` exist for legacy tools.
- **`bake_space_transform=True` is marked experimental and is known to break
  armatures/animations** — do not enable it for rigged assets.
- **Animation missing** → `bake_anim=True` plus `bake_anim_use_all_actions=True`
  exports every action as a take; `bake_anim_use_nla_strips=True` exports NLA
  strips. For a single clean take set both `use_all_actions` and
  `use_nla_strips` to `False` and rely on the active action.

`mesh_smooth_type`: `'OFF'` (Normals Only — best when the target understands
custom split normals), `'FACE'`, `'EDGE'`, `'SMOOTH_GROUP'`. Unity/Unreal are
happiest with `'FACE'` or `'OFF'`; older Max pipelines want `'SMOOTH_GROUP'`.

FBX **import** in 5.2 is the C++ operator:

```python
bpy.ops.wm.fbx_import(filepath='', directory='', files=None,
    global_scale=1.0, mtl_name_collision_mode='MAKE_UNIQUE',
    import_colors='SRGB', use_custom_normals=True, use_custom_props=True,
    use_custom_props_enum_as_string=True, import_subdivision=False,
    ignore_leaf_bones=False, validate_meshes=True,
    use_anim=True, anim_offset=1.0, filter_glob='*.fbx')
```

### 4.6 USD

Stage/layer mental model: a USD file is a *layer*; layers compose into a
*stage*. Blender exports a single flattened layer rooted at `root_prim_path`
(default `/root`). Prefer USD when the downstream needs (a) references and
instancing preserved, (b) a stable prim-path namespace to override in a later
layer, or (c) MaterialX. Prefer glTF for delivery, USD for assembly.

```python
bpy.ops.wm.usd_export(
    filepath='/out/asset.usdc',           # .usda .usdc .usd .usdz
    selected_objects_only=False, collection='',
    export_animation=False, incremental_frames=0,
    export_meshes=True, export_lights=True, export_cameras=True,
    export_curves=True, export_points=True, export_volumes=True,
    export_hair=False, export_uvmaps=True, rename_uvmaps=True,
    export_mesh_colors=True, export_normals=True,
    export_subdivision='BEST_MATCH',
    export_armatures=True, only_deform_bones=False, export_shapekeys=True,
    use_instancing=False, evaluation_mode='RENDER',
    export_materials=True, generate_preview_surface=True,
    generate_materialx_network=False,
    export_textures_mode='NEW', overwrite_textures=False, relative_paths=True,
    convert_orientation=False,
    export_global_forward_selection='NEGATIVE_Z',
    export_global_up_selection='Y',
    xform_op_mode='TRS', root_prim_path='/root',
    export_custom_properties=True, custom_properties_namespace='userProperties',
    accessibility_label='', accessibility_description='',
    author_blender_name=True, convert_world_material=True, allow_unicode=True,
    triangulate_meshes=False, quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY',
    usdz_downscale_size='KEEP', usdz_downscale_custom_size=128,
    merge_parent_xform=False,
    convert_scene_units='METERS', meters_per_unit=1.0)
```

5.0 removed `export_textures` (superseded by `export_textures_mode`) and
`visible_objects_only`, and flipped `allow_unicode` to default `True`. 5.2 added
color-space tagging on prims/textures and a flush-frequency option to cut peak
memory. `allow_unicode=False` restricts prim names to `[A-Za-z_][A-Za-z0-9_]*`.

### 4.7 OBJ / STL / PLY — the C++ rewrites

```python
bpy.ops.wm.obj_export(filepath='', export_animation=False,
    start_frame=-2147483648, end_frame=2147483647,
    forward_axis='NEGATIVE_Z', up_axis='Y', global_scale=1.0,
    apply_modifiers=True, apply_transform=True,
    export_eval_mode='DAG_EVAL_VIEWPORT',      # note: VIEWPORT default
    export_selected_objects=False, collection='',
    export_uv=True, export_normals=True, export_colors=False,
    export_materials=True, export_pbr_extensions=False, path_mode='AUTO',
    export_triangulated_mesh=False, export_curves_as_nurbs=False,
    export_object_groups=False, export_material_groups=False,
    export_vertex_groups=False, export_smooth_groups=False,
    smooth_group_bitflags=False, filter_glob='*.obj;*.mtl')

bpy.ops.wm.stl_export(filepath='', ascii_format=False, use_batch=False,
    export_selected_objects=False, collection='',
    global_scale=1.0, use_scene_unit=False,
    forward_axis='Y', up_axis='Z',
    apply_modifiers=True,
    evaluation_mode='DAG_EVAL_RENDER',          # option added in 5.2
    filter_glob='*.stl')

bpy.ops.wm.ply_export(filepath='', forward_axis='Y', up_axis='Z',
    global_scale=1.0, apply_modifiers=True,
    export_selected_objects=False, collection='',
    export_uv=True, export_normals=False, export_colors='SRGB',
    export_attributes=True, export_triangulated_mesh=False,
    ascii_format=False, filter_glob='*.ply')
```

Axis enums for these three are the long form: `'X'`, `'Y'`, `'Z'`,
`'NEGATIVE_X'`, `'NEGATIVE_Y'`, `'NEGATIVE_Z'` — **not** the FBX `'-Z'` short
form. Mixing them up raises
`TypeError: enum "-Z" not found in ('X', 'Y', 'Z', 'NEGATIVE_X', ...)`.

Note the inconsistent evaluation defaults: OBJ `export_eval_mode` defaults to
`'DAG_EVAL_VIEWPORT'`; STL `evaluation_mode` defaults to `'DAG_EVAL_RENDER'`.

### 4.8 Alembic — baked caches

```python
bpy.ops.wm.alembic_export(filepath='/cache/shot.abc',
    start=1, end=250, xsamples=1, gsamples=1, sh_open=0.0, sh_close=1.0,
    selected=False, flatten=False, collection='',
    uvs=True, packuv=True, normals=True, vcolors=False, orcos=True,
    face_sets=False, subdiv_schema=False, apply_subdiv=False,
    curves_as_mesh=False, use_instancing=True, global_scale=1.0,
    triangulate=False, quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY',
    export_hair=True, export_particles=True, export_custom_properties=True,
    as_background_job=False, evaluation_mode='RENDER',
    init_scene_frame_range=True)
```

`as_background_job=False` is mandatory in `--background`: with `True` the
operator returns immediately and the process may exit before the cache is
written. 5.0 removed `visible_objects_only` and the deprecated
`Scene.alembic_export` Python method. Alembic is the right answer for cloth/soft
body/geometry-node results that must arrive in another DCC exactly as rendered;
it is the wrong answer for anything that must stay editable or rigged.

### 4.9 Verify the artefact, don't trust the return code

```python
import os, json, struct, bpy

def check_glb(path, min_meshes=1):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        magic, ver, total = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", magic
        clen, ctype = struct.unpack("<I4s", f.read(8))
        assert ctype == b"JSON", ctype
        doc = json.loads(f.read(clen))
    assert len(doc.get("meshes", [])) >= min_meshes, doc.keys()
    return dict(bytes=size, version=ver,
                meshes=len(doc.get("meshes", [])),
                materials=len(doc.get("materials", [])),
                animations=len(doc.get("animations", [])),
                nodes=len(doc.get("nodes", [])),
                extensions=doc.get("extensionsUsed", []))

def check_binary_stl(path):
    n = (os.path.getsize(path) - 84) // 50
    with open(path, "rb") as f:
        f.seek(80)
        assert struct.unpack("<I", f.read(4))[0] == n, "STL triangle count mismatch"
    return n
```

Round-tripping the export back into a fresh scene is the strongest check
available headlessly:

```python
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/out/asset.glb")
tris = sum(len(o.data.loop_triangles) for o in bpy.data.objects
           if o.type == 'MESH' and (o.data.calc_loop_triangles() or True))
```

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: module 'bpy.ops.export_scene' has no attribute 'obj'` | OBJ moved to C++ in 3.x/4.0 | `bpy.ops.wm.obj_export(...)` |
| `AttributeError: module 'bpy.ops.export_mesh' has no attribute 'stl'` | STL moved to C++ in 4.2 | `bpy.ops.wm.stl_export(...)` |
| `AttributeError: module 'bpy.ops.wm' has no attribute 'collada_export'` | Collada removed in 5.0 | use glTF/FBX/USD |
| `TypeError: ... WM_OT_usd_export.export_textures: keyword unrecognized` | renamed in 5.0 | `export_textures_mode='NEW'` |
| `TypeError: ... enum "-Z" not found in ('X','Y','Z','NEGATIVE_X',...)` | FBX short axis names used on OBJ/STL/PLY | `'NEGATIVE_Z'` |
| Export "succeeds", file has `"meshes": []` | `use_selection=True` in background, or the collection is `exclude`d | export via `collection=`; check the depsgraph |
| Model 100x too big in Unreal | `apply_scale_options='FBX_SCALE_ALL'` (Unity setting) | `'FBX_SCALE_NONE'` for Unreal |
| Model 0.01x in Unity | `'FBX_SCALE_NONE'` with a non-1.0 `scale_length` | `'FBX_SCALE_ALL'`, `scale_length=1.0` |
| Skeleton has extra tip joints named `*_end` | `add_leaf_bones=True` | `add_leaf_bones=False` |
| Character animation missing from `.glb` | actions not stashed to NLA tracks; 4.4+ merges by action | stash each action on its own track; `export_animation_mode='ACTIONS'` |
| glTF has no morph targets | `export_apply=True` evaluated the modifiers away | `export_apply=False`, or apply modifiers before shape keys exist |
| Material looks flat grey in the viewer | procedural nodes / non-Principled shader | bake to Base Color + ORM + Normal, rebuild with Principled |
| Occlusion map missing from glTF | AO not wired into the `glTF Material Output` node group's `Occlusion` input | add that node group (Add ▸ Output ▸ glTF Material Output) |
| `.abc` file is 0 bytes after a background run | `as_background_job=True` | set it to `False` |
| USD prims renamed with underscores | USD identifier sanitisation | pre-sanitise names, or accept and remap |
| Export takes minutes, log full of image conversions | textures not in glTF's ORM packing, or non-PNG/JPEG sources | pre-pack ORM; keep sources as PNG/JPEG |
| `RuntimeError: Error: Cannot save image ...` | `path_mode='COPY'`/`export_texture_dir` pointing at a non-writable dir | use an absolute, writable output dir |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Format | glTF `GLB` or FBX | FBX or glTF `GLB` | Alembic or `.blend` | USD / glTF / `.blend` | STL (binary) or 3MF |
| Operator | `export_scene.gltf` | `export_scene.fbx` | `wm.alembic_export` | `wm.usd_export` | `wm.stl_export` |
| Modifiers applied | `export_apply=True` | `use_mesh_modifiers=True` | baked by the cache | `evaluation_mode='RENDER'` | `apply_modifiers=True` |
| Triangulate | yes (`use_triangles=True` / `export_triangulated_mesh=True`) | yes | no | no | yes (STL is triangles) |
| Tangents exported | `export_tangents=True` if normal-mapped | `use_tspace=True` | n/a | n/a | n/a |
| Materials | `export_materials='EXPORT'` | `'EXPORT'` | n/a | `export_materials=True`, `generate_preview_surface=True` | none |
| Compression | Draco or meshopt | none (rig fidelity) | n/a | none | n/a |
| Animation | only if needed | `bake_anim=True`, `bake_anim_step=1.0` | full frame range | n/a | n/a |
| `bake_anim_simplify_factor` | 1.0 | 0.0 (no simplification) | n/a | n/a | n/a |
| Axis (FBX) | `-Z` fwd / `Y` up | `-Z` fwd / `Y` up | n/a | n/a | n/a |
| Axis (OBJ/STL/PLY) | `NEGATIVE_Z`/`Y` | n/a | n/a | n/a | `Y` fwd / `Z` up |
| Scale option (FBX) | Unity `FBX_SCALE_ALL`, Unreal `FBX_SCALE_NONE` | same | n/a | n/a | n/a |
| `global_scale` | 1.0 | 1.0 | 1.0 | 1.0 | 1000 **or** `use_scene_unit=True` |
| Leaf bones | `add_leaf_bones=False` | `add_leaf_bones=False` | n/a | n/a | n/a |
| Deform bones only | True | True | n/a | n/a | n/a |
| Bone influences | 4 | 4 (8 for hero) | n/a | n/a | n/a |
| Cameras / lights | off | off | on | on (`export_cameras=True`) | off |
| Custom properties | `export_extras=True` | `use_custom_props=True` | on | on | off |

## 7. Verification checklist

- [ ] `assert 'gltf' in dir(bpy.ops.export_scene)` — the add-on is enabled.
- [ ] `assert 'collection' in bpy.ops.export_scene.gltf.get_rna_type().properties.keys()` — this build supports collection-scoped export.
- [ ] `assert os.path.getsize(out) > 2048` — the exporter actually wrote geometry.
- [ ] `check_glb(out)["meshes"] >= expected` — mesh count round-trips (§4.9).
- [ ] `check_glb(out)["animations"] == len(expected_clips)` — NLA stashing worked.
- [ ] `assert 'KHR_draco_mesh_compression' in check_glb(out)["extensions"]` — compression really applied.
- [ ] `check_binary_stl(out) == sum(len(m.loop_triangles) ...)` — STL triangle count matches the source.
- [ ] Re-import into an empty file and compare `len(bpy.data.objects)`, `dimensions` and material count against the source.
- [ ] Re-import and assert `max(o.dimensions) / expected_size` is within 1% — catches every unit/scale mistake.
- [ ] Render the re-imported scene at 16 samples and eyeball the screenshot for flipped normals (black facets) and missing textures (magenta/grey).

## 8. Sources

- [bpy.ops.export_scene (gltf, fbx) — 5.2](https://docs.blender.org/api/current/bpy.ops.export_scene.html)
- [bpy.ops.wm (obj/stl/ply/usd/alembic/fbx_import) — 5.2](https://docs.blender.org/api/current/bpy.ops.wm.html)
- [bpy.ops.import_scene — 5.2](https://docs.blender.org/api/current/bpy.ops.import_scene.html)
- [glTF 2.0 — Blender 5.2 LTS Manual](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html)
- [FBX — Blender 5.2 LTS Manual](https://docs.blender.org/manual/en/latest/files/import_export/fbx.html) and [FBX (Legacy)](https://docs.blender.org/manual/en/latest/files/import_export/fbx_legacy.html)
- [Blender 5.0: Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.0/pipeline_io/) — Collada removal, C++ FBX importer becomes default
- [Blender 5.0: Python API](https://developer.blender.org/docs/release_notes/5.0/python_api/) — USD/Alembic option renames and removals
- [Blender 5.1: Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.1/pipeline_io/)
- [Blender 5.2 LTS: Pipeline & I/O](https://developer.blender.org/docs/release_notes/5.2/pipeline_io/) — meshopt, iridescence, dispersion, point clouds, STL eval mode
- [Blender source `scripts/addons_core/io_scene_gltf2/__init__.py`](https://projects.blender.org/blender/blender/src/branch/main/scripts/addons_core/io_scene_gltf2/__init__.py) — enum item values
- [Blender source `source/blender/editors/io/`](https://projects.blender.org/blender/blender/src/branch/main/source/blender/editors/io) — `IO_FH_*` file-handler idnames
- `[UNVERIFIED]` Engine-specific recommendations for Unity/Unreal/Godot import settings are practice-derived; Blender's docs state the mechanism (`apply_scale_options`, `add_leaf_bones`) but not the per-engine choice.
- `[UNVERIFIED]` `export_use_gltfpack` requires an external `gltfpack` binary; the manual does not document the lookup path in 5.2.

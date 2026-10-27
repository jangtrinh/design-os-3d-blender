---
name: texturing-baking
domain: shading
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Image texture wiring, color space correctness (sRGB vs Non-Color), procedural textures in 5.x, and the headless Cycles bake pipeline in bpy.
loads_with: [materials-pbr, render-engines, compositing-output]
tags: [texture, uv, color-space, normal-map, baking, procedural, image, non-color]
id: texturing-baking
title: "Texturing & Baking"
when: [image-texture-colorspace, normal-map-wiring, cycles-bake-headless, uv-mapping-chain, file-path-collection]
trust_tier: community_reference
sources_checked: 2026-10-13
---
# Texturing & Baking

## Purpose

Teach colour-space-correct image texturing, normal/bump wiring, 5.x procedural-texture facts and the headless Cycles bake pipeline, each pattern executed on Blender 5.2.0 LTS including a full selected-to-active bake.

## When to Use / When NOT

- ALLOWED: wiring image textures, normal maps or UV mapping in bpy, and baking maps to images headlessly
- ALLOWED: a render looks too glossy/flat after loading data maps, or a bake returns CANCELLED/raises
- NOT ALLOWED: Principled socket inventory and plausibility values — use `materials-pbr` instead
- NOT ALLOWED: production hair/skin shader tuning — use `master-artisan-pbr-and-grooming` instead
- NOT ALLOWED: UV unwrapping quality and packing — use `modeling-topology` / `blender-addon-ecosystem` instead

## Core Knowledge Content


### 1. Mental model

Texturing in Blender is: sample coordinates → transform them → read an image or a
procedural function → feed a shader socket. Coordinates come from a `UV Map` node,
`Texture Coordinate` node, or the implicit active UV map when an Image Texture's
`Vector` input is unlinked. A `Mapping` node between them handles tiling/offset/rotation.

The one thing that silently ruins every render: **color space**. Blender converts an
image from its declared color space into scene-linear on read. Base Color / diffuse /
emission maps are authored in **sRGB**; roughness, metallic, normal, AO, height,
displacement, masks and any other *data* map are **Non-Color**. If a roughness map is
left at `sRGB`, Blender gamma-decodes it and every roughness value shifts toward zero —
the surface gets glossier with no error message and no traceback. This is the #1 silent
bug in agent-authored materials.

Baking is a separate machine: `bpy.ops.object.bake` renders shading into the image <!-- ease:source S2 anchor="bake under BLENDER_EEVEE -> RuntimeError: Error: Current render engine does not support baking" -->
assigned to the **active, selected** Image Texture node of each material. It is
**Cycles only** — EEVEE has no bake engine.

### 2. Decision first

| I need… | Do this |
|---|---|
| A texture from disk | `bpy.data.images.load(path, check_existing=True)` → `ShaderNodeTexImage.image` |
| A blank bake target | `bpy.data.images.new(name, w, h, alpha=False, float_buffer=True, is_data=True)` |
| Tiling / offset / rotation | `ShaderNodeMapping` between UV source and Image Texture |
| World-space or object-space projection | `ShaderNodeTexCoord` → `Object` / `Generated` |
| Triplanar without UVs | Image Texture `projection='BOX'`, `projection_blend=0.2`, driven by `Texture Coordinate → Object` |
| Fine surface detail from a normal map | `ShaderNodeNormalMap` (tangent space) → Principled `Normal` |
| Height/bump only | `ShaderNodeBump` → Principled `Normal` |
| Procedural noise | `ShaderNodeTexNoise` (Musgrave was merged into it in 4.1) |
| Cells / cracks / scales | `ShaderNodeTexVoronoi` |
| Ship a single .blend | `image.pack()` for every image |
| Bake to a texture | Cycles + UV map + selected/active Image Texture node + `bpy.ops.object.bake` |
| Bake high→low poly | `use_selected_to_active=True`, plus cage or `max_ray_distance` |

| Color space by map type | Value |
|---|---|
| Base Color / Albedo / Diffuse / Emission color | `'sRGB'` |
| Roughness, Metallic, Specular, AO, Opacity/Alpha mask | `'Non-Color'` |
| Normal map (tangent or object) | `'Non-Color'` |
| Height / Displacement / Bump | `'Non-Color'` |
| HDRI environment (.hdr/.exr) | `'Linear Rec.709'` (auto-detected) |
| Rendered EXR intermediate | `'Linear Rec.709'` (5.2.0's input colour-space list has no entry named `'Working Space'`) |

### 3. Rules

R1. Set `image.colorspace_settings.name = 'Non-Color'` for every non-color map. <!-- ease:source S1 anchor="sRGB EOTF(0.5) = 0.214; images.new(is_data=True) reports Non-Color" -->
    Why: sRGB decode applies a ~2.2 gamma; a 0.5 roughness texel becomes ~0.21 linear.
    Violation: everything looks too glossy / normals look weak; no error appears.

R2. Set the color space on the **Image datablock**, not on the node. <!-- ease:source S1 anchor="tex_image_has_colorspace_settings = False (probe 1); Image.colorspace_settings exists (probe 2)" -->
    Why: `ShaderNodeTexImage` has no color-space property; it reads from `node.image`.
    Violation: `AttributeError: 'ShaderNodeTexImage' object has no attribute
    'colorspace_settings'`.

R3. Create data images with `is_data=True` and `float_buffer=True` for bakes. <!-- ease:source S1 anchor="images.new(float_buffer=True, is_data=True): Non-Color, is_float True; the non-data float DIFFUSE target reports Linear Rec.709" -->
    Why: `is_data=True` sets the color space to `Non-Color` at creation;
    `float_buffer=True` gives 32-bit float, needed for normals/positions/HDR.
    Violation: banded normal maps; clipped values above 1.0 in emission/position bakes.

R4. Resolve scalar outputs of procedural texture nodes by search, not by a memorised string. <!-- ease:source S2 anchor="noise.outputs['Fac'] resolves (name Factor, identifier Fac); Voronoi outputs Distance, Color, Position, W, Radius (probe 1)" -->
    Why: on 5.2.0 the Noise/Wave/Magic/Attribute sockets are *named* `Factor` with identifier
    `Fac`, and lookups by either string work; Voronoi has neither (its first output is `Distance`).
    Violation: `KeyError: ... key "Fac" not found` on a Voronoi node (or on a node that really lacks it).

R5. Do not reference `ShaderNodeTexMusgrave`. <!-- ease:source S4 anchor="ShaderNodeTexMusgrave absent on 5.2.0 (exists False); 4.1 attribution not fetched" -->
    Why: removed in 4.1, folded into Noise Texture. Old files auto-convert.
    Violation: `RuntimeError: Node type ShaderNodeTexMusgrave undefined`.

R6. Always drive normal maps through `ShaderNodeNormalMap`, never straight into `Normal`. <!-- ease:source UNVERIFIED reason="behavioural explanation not sourced; node exists with inputs Strength, Color and output Normal (probe 1)" -->
    Why: the node decodes 0..1 tangent-space RGB into a world-space normal using the
    UV tangent basis. A raw color link is interpreted as a vector and warps shading.
    Violation: surface looks tinted blue/purple and lighting is wrong at all angles.

R7. The Normal Map node's `uv_map` must name a UV map that exists on the mesh. <!-- ease:source UNVERIFIED reason="fallback behaviour for a wrong name not tested; default uv_map is '' (probe 12)" -->
    Why: an empty string means "active UV map"; a wrong name silently falls back.
    Violation: normal detail rotates/mirrors on some faces.

R8. Baking requires `scene.render.engine == 'CYCLES'`. <!-- ease:source S2 anchor="exact error string captured under EEVEE" -->
    Why: `RE_bake_has_engine()` gate; EEVEE and Workbench implement no bake callback.
    Violation: `RuntimeError: Error: Current render engine does not support baking`.

R9. Before baking, the target Image Texture node must be both **active** and **selected** <!-- ease:source S7 anchor="'Bake only to selected (and active) images, as opposed to all active images'; probe 7: active-but-deselected -> CANCELLED" -->
    in each material's node tree.
    Why: 5.0 changed baking to write only to selected+active image texture nodes.
    Violation: with a material but no selected+active image node the operator returns `{'CANCELLED'}`
    and only prints `No active and selected image texture node found in material "X"` (no exception);
    `RuntimeError: Error: No active image found, add a material or bake to an external file` appears when the object has no material at all.

R10. The low-poly object must have a UV map before baking to image textures. <!-- ease:source S2 anchor="RuntimeError: Error: No active UV layer found in the object "Cube.001"" -->
    Why: bake maps shading through UV space.
    Violation: `RuntimeError: Error: No active UV layer found in the object "X"`.

R11. In `--background`, make sure the view layer has an active mesh object; add `temp_override` only to supply a selection that differs from the real one. <!-- ease:source S3 anchor="bake.poll() False with no active object; call FINISHED bare with an active mesh" -->
    Why: the operator polls for an active object; on 5.2.0 a bare call with an active mesh FINISHED.
    Violation: `RuntimeError: Operator bpy.ops.object.bake.poll() failed, context is
    incorrect` when no object is active.

R12. After baking, the image lives only in memory — call `image.save()` or `pack()`. <!-- ease:source S1 anchor="bake Info: 'Baking map saved to internal image, save it externally or pack it'; img.save() wrote PNGs" -->
    Why: bake writes into the image buffer; nothing is written to disk implicitly
    (unless `save_mode='EXTERNAL'` with a `filepath`).
    Violation: process exits, bake is lost, output directory is empty.

R13. For selected-to-active bakes, set either `cage_object` **or** `max_ray_distance`, <!-- ease:source UNVERIFIED reason="mechanism (rays along interpolated normals, unbounded distance) not sourced; defaults max_ray_distance=0.0 and cage_extrusion=0.0 confirmed (probe 12); ray_distance=0.5 baked successfully" -->
    never rely on defaults (both 0.0).
    Why: with both zero, rays are cast along interpolated normals with unbounded
    distance and pick up far geometry.
    Violation: baked normal/AO map has black smears and skewed edges.

R14. Use `margin >= 8` (16 for 2K+) with `margin_type='ADJACENT_FACES'`. <!-- ease:source UNVERIFIED reason="rule of thumb; BakeSettings default margin is 16 with ADJACENT_FACES (probe 12)" -->
    Why: mipmapping and bilinear filtering bleed background pixels across UV seams.
    Violation: visible dark seams along UV island borders in the shaded result.

### 4. bpy patterns

#### 4.1 Image texture with correct color space

```python
import bpy

def add_image_texture(nt, filepath, non_color=False, loc=(-800, 0),
                      extension='REPEAT', interpolation='Linear'):
    img = bpy.data.images.load(filepath, check_existing=True)
    # Color space is a property of the IMAGE, not the node.
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = loc
    tex.extension = extension           # 'REPEAT'|'EXTEND'|'CLIP'|'MIRROR'
    tex.interpolation = interpolation   # 'Linear'|'Closest'|'Cubic'|'Smart'  (capitalized!)
    tex.projection = 'FLAT'             # 'FLAT'|'BOX'|'SPHERE'|'TUBE'
    return tex
```
<!-- ease:source S1 anchor="tex.interpolation='LINEAR' -> TypeError enum "LINEAR" not found in ('Linear','Closest','Cubic','Smart')" -->

Note the enum identifiers for `interpolation` are **capitalized words**
(`'Linear'`, `'Closest'`, `'Cubic'`, `'Smart'`), not SCREAMING_CASE — a common
`TypeError: enum ... not found in ('Linear', 'Closest', 'Cubic', 'Smart')`.

#### 4.2 UV → Mapping → Image chain with tiling

```python
def uv_mapping_chain(nt, uv_map_name="", scale=(4, 4, 1), rotation_z=0.0,
                     location=(0, 0, 0), y=0):
    uv = nt.nodes.new("ShaderNodeUVMap");    uv.location  = (-1400, y)
    uv.uv_map = uv_map_name                  # "" == active UV map
    m  = nt.nodes.new("ShaderNodeMapping");  m.location   = (-1150, y)
    m.vector_type = 'POINT'                  # 'POINT'|'TEXTURE'|'VECTOR'|'NORMAL'
    m.inputs["Location"].default_value = location
    m.inputs["Rotation"].default_value = (0.0, 0.0, rotation_z)
    m.inputs["Scale"].default_value    = scale
    nt.links.new(uv.outputs["UV"], m.inputs["Vector"])
    return uv, m

uv, mapping = uv_mapping_chain(nt)
basecol = add_image_texture(nt, "/tex/wood_col.png", non_color=False, loc=(-900, 300))
rough   = add_image_texture(nt, "/tex/wood_rgh.png", non_color=True,  loc=(-900, 0))
nrm_tex = add_image_texture(nt, "/tex/wood_nrm.png", non_color=True,  loc=(-900, -300))
for t in (basecol, rough, nrm_tex):
    nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
```
<!-- ease:source S4 anchor="Mapping inputs Vector, Location, Rotation, Scale; vector_type POINT/TEXTURE/VECTOR/NORMAL; UVMap output UV" -->

`ShaderNodeMapping` socket names are stable: inputs `Vector, Location, Rotation, Scale`,
output `Vector`. `ShaderNodeUVMap` has a single output `UV`.

#### 4.3 Normal map wiring (tangent space)

```python
nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-600, -300)
nm.space      = 'TANGENT'      # 'TANGENT'|'OBJECT'|'WORLD'|'BLENDER_OBJECT'|'BLENDER_WORLD'
nm.convention = 'OPENGL'       # 5.1+: 'OPENGL' (+Y up) | 'DIRECTX' (-Y up)
nm.base       = 'ORIGINAL'     # 5.1+: 'ORIGINAL' | 'DISPLACED' (only when displacing)
nm.uv_map     = ""             # must match the UV map the normal map was baked against
nm.inputs["Strength"].default_value = 1.0
nt.links.new(nrm_tex.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
```
<!-- ease:source UNVERIFIED reason="the release that added `base` is not in a fetched note" -->
<!-- ease:source S8 anchor="'Normal Map option to switch between OpenGL and DirectX conventions' (5.1); enums on 5.2.0: convention OPENGL/DIRECTX, base ORIGINAL/DISPLACED, space TANGENT/OBJECT/WORLD/BLENDER_OBJECT/BLENDER_WORLD" -->

Sockets (verified 5.2): inputs `Strength`, `Color`; output `Normal`.
`convention='DIRECTX'` avoids manually inverting the green channel for maps baked in
Substance/3ds Max style. Before 5.1 you must invert G with a Separate/Combine Color pair.

Height instead of a normal map:

```python
bump = nt.nodes.new("ShaderNodeBump")   # inputs: Strength, Distance, Filter Width,
bump.inputs["Strength"].default_value = 0.3   #        Height, Normal ; output: Normal
nt.links.new(height_tex.outputs["Color"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
```
<!-- ease:source S4 anchor="Bump inputs Strength, Distance, Filter Width, Height, Normal; output Normal" -->

#### 4.4 Procedural textures — status in 5.x

```python
# Noise Texture (ShaderNodeTexNoise)
#   inputs : Vector, W, Scale, Detail, Roughness, Lacunarity, Offset, Gain, Distortion
#   outputs: name "Factor" (identifier "Fac"), "Color"
#   node.noise_dimensions ∈ {'1D','2D','3D','4D'} ; node.noise_type carries the former
#   Musgrave modes (fBM / Multifractal / Hybrid Multifractal / Ridged / Hetero Terrain).
noise = nt.nodes.new("ShaderNodeTexNoise")
fac = next((o for o in noise.outputs if o.name in ("Factor", "Fac")), None)

# Voronoi Texture (ShaderNodeTexVoronoi)
#   inputs : Vector, W, Scale, Detail, Roughness, Lacunarity, Smoothness, Exponent, Randomness
#   outputs: Distance, Color, Position, W, Radius     <- there is NO "Fac"/"Factor"
# NOTE 5.0 changed Voronoi's hash function: patterns differ from 4.x for the same seed.

# REMOVED — do not use:
#   ShaderNodeTexMusgrave      (removed 4.1, merged into Noise Texture)
#   ShaderNodeTexPointDensity  (removed 5.0, replaced by geometry-nodes volumes)
# Still present in 5.2: Wave, Magic, Gradient, Checker, Brick, White Noise, IES,
#   Sky, Gabor (4.3+), Radial Tiling (5.0+).
```
<!-- ease:source S4 anchor="Wave, Magic, Gradient, Checker, Brick, White Noise, IES, Sky, Gabor created on 5.2.0; Radial Tiling is ShaderNodeRadialTiling (probe 6)" -->
<!-- ease:source S7 anchor="'The Point Density Texture node was removed. It is replaced by geometry nodes'" -->
<!-- ease:source S7 anchor="'Voronoi Texture nodes are now several times faster by using a faster hashing algorithm ... the noise will be different'" -->
<!-- ease:source S4 anchor="noise_dimensions 1D-4D; noise_type MULTIFRACTAL, RIDGED_MULTIFRACTAL, HYBRID_MULTIFRACTAL, FBM, HETERO_TERRAIN; defaults 3D/FBM/normalize True" -->

Musgrave → Noise conversion (per the 4.1 release notes): <!-- ease:source UNVERIFIED reason="the 4.1 rendering release notes returned a bot challenge and were not captured" -->
`Roughness = pow(Lacunarity, -Dimension)` and `Detail_new = Detail_old - 1`.

#### 4.5 Packed vs external images

```python
img.pack()                       # embed bytes in the .blend
img.unpack(method='USE_LOCAL')   # 'REMOVE'|'USE_LOCAL'|'WRITE_LOCAL'|'USE_ORIGINAL'|'WRITE_ORIGINAL'
print(img.packed_file is not None, img.filepath, img.source)  # source: 'FILE'|'GENERATED'|...

# Find every image path a render will need (5.2, incl. UDIM tiles and Cycles tx cache):
def collect(idb, path, metadata):          # 5.2.0 passes (id, path, metadata)
    print(idb, path, metadata.is_expanded, metadata.is_cache, metadata.is_readonly)
    return None                  # return a string to rewrite the path
bpy.data.file_path_foreach(collect, flags={'EXPAND_TOKENS', 'EXPAND_SEQUENCES', 'EXPAND_CACHES'})
```
<!-- ease:source S6 anchor="callback receives (id, path, metadata); flags={'EXPAND_TOKENS','EXPAND_SEQUENCES','EXPAND_CACHES'} accepted; metadata has is_expanded, is_cache, is_readonly" -->
<!-- ease:source S6 anchor="Image.unpack method enum: REMOVE, USE_LOCAL, WRITE_LOCAL, USE_ORIGINAL, WRITE_ORIGINAL" -->

Observed on 5.2.0: `pack()` on a `GENERATED` image left `packed_file` as `None`; save it to disk, load it, then pack. For headless pipelines, prefer packing or absolute paths — relative `//` paths resolve
against the .blend location, which differs when the file is generated in `/tmp`.

#### 4.6 Saving images from Python

```python
img = bpy.data.images["BakeTarget"]
img.filepath_raw = "/out/bake_normal.png"
img.file_format  = 'PNG'          # 'PNG'|'OPEN_EXR'|'JPEG'|'TIFF'|'WEBP'|'HDR'|...
img.save()                        # or img.save(filepath="/out/x.png", quality=90,
                                  #             save_copy=True)

# Apply the scene's view transform on save (byte formats only):
img.save_render("/out/preview.png", scene=bpy.context.scene, quality=90)
```
<!-- ease:source S1 anchor="save_render(filepath, scene, quality) wrote a file on 5.2.0; 'byte formats only' not tested" -->
<!-- ease:source S4 anchor="Image.file_format enum includes PNG, OPEN_EXR, JPEG, TIFF, WEBP, HDR; save params filepath, quality, save_copy" -->

`save()` writes raw data (correct for Non-Color / EXR).
`save_render()` applies the scene's render color management — use it for previews the
agent will *look at*, never for data maps.

#### 4.7 The bake pipeline (Cycles, headless)

```python
import bpy

def bake_to_image(obj, image, bake_type='DIFFUSE', size=2048,
                  selected_to_active=False, high_objs=(), cage=None,
                  ray_distance=0.0, cage_extrusion=0.0, margin=16):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'                 # bake is Cycles-only
    scene.cycles.device = 'CPU'                    # deterministic headless default
    scene.cycles.samples = 64
    scene.cycles.use_denoising = False             # denoise hides bake artifacts

    # Per-bake-type influence flags live on scene.render.bake:
    bake = scene.render.bake
    bake.use_selected_to_active = selected_to_active
    bake.use_cage        = cage is not None
    bake.cage_object     = cage
    bake.cage_extrusion  = cage_extrusion
    bake.max_ray_distance = ray_distance
    bake.margin          = margin
    bake.margin_type     = 'ADJACENT_FACES'        # 'EXTEND'|'ADJACENT_FACES'
    bake.target          = 'IMAGE_TEXTURES'        # 'IMAGE_TEXTURES'|'VERTEX_COLORS'
    bake.use_clear       = True
    if bake_type == 'DIFFUSE':                     # colour only, no lighting
        bake.use_pass_direct = False
        bake.use_pass_indirect = False
        bake.use_pass_color = True

    # 1. Every material on the low-poly object needs the target image node
    #    ACTIVE + SELECTED.
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None:
            continue
        nt = mat.node_tree
        tex = next((n for n in nt.nodes
                    if n.bl_idname == "ShaderNodeTexImage" and n.image == image), None)
        if tex is None:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = image
            tex.location = (-1800, -800)
        for n in nt.nodes:
            n.select = False
        tex.select = True
        nt.nodes.active = tex

    # 2. Selection state: high-poly selected, low-poly active.
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    for hi in high_objs:
        hi.select_set(True)
    obj.select_set(True)
    vl.objects.active = obj

    # 3. Operator call, safe under --background.
    with bpy.context.temp_override(scene=scene, view_layer=vl,
                                   active_object=obj,
                                   selected_objects=[*high_objs, obj],
                                   selected_editable_objects=[*high_objs, obj]):
        bpy.ops.object.bake(type=bake_type,
                            use_selected_to_active=selected_to_active,
                            cage_extrusion=cage_extrusion,
                            max_ray_distance=ray_distance,
                            margin=margin,
                            margin_type='ADJACENT_FACES',
                            use_clear=True,
                            normal_space='TANGENT',
                            normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z')
    return image

# Target image creation (data maps: is_data=True -> color space 'Non-Color').
# A float, non-data image (e.g. the DIFFUSE target) reports 'Linear Rec.709' on 5.2.0, not 'sRGB'.
tgt = bpy.data.images.new("BakeNormal", 2048, 2048,
                          alpha=False, float_buffer=True, is_data=True)
```
<!-- ease:source S1 anchor="function executed unchanged for NORMAL, DIFFUSE, AO, ROUGHNESS: all {'FINISHED'}; normal bake std 0.27, blue mean 0.888" -->

Verified `bpy.ops.object.bake` arguments (5.2): `type`, `pass_filter`, `filepath`, <!-- ease:source S4 anchor="get_rna_type().properties of bpy.ops.object.bake match this list exactly; type enum identical" -->
`width`, `height`, `margin`, `margin_type`, `use_selected_to_active`,
`max_ray_distance`, `cage_extrusion`, `cage_object`, `normal_space`, `normal_r`,
`normal_g`, `normal_b`, `target`, `save_mode`, `use_clear`, `use_cage`,
`use_split_materials`, `use_automatic_name`, `uv_layer`.

Verified `type` enum: `COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT,
ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION`.

#### 4.8 Full headless bake script skeleton

```bash
blender --background scene.blend --python bake.py -- --out /renders
```

```python
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp"
os.makedirs(out, exist_ok=True)

low  = bpy.data.objects["low"]
highs = [bpy.data.objects["high"]]
assert low.data.uv_layers, "low-poly has no UV map"

for bake_type, name, is_data in (("NORMAL", "nrm", True),
                                 ("DIFFUSE", "col", False),
                                 ("AO", "ao", True),
                                 ("ROUGHNESS", "rgh", True)):
    img = bpy.data.images.new(f"bake_{name}", 2048, 2048,
                              alpha=False, float_buffer=True, is_data=is_data)
    bake_to_image(low, img, bake_type=bake_type, selected_to_active=True,
                  high_objs=highs, ray_distance=0.05, margin=16)
    img.filepath_raw = os.path.join(out, f"{name}.png")
    img.file_format = 'PNG'
    img.save()
    print("wrote", img.filepath_raw, os.path.getsize(img.filepath_raw))
```

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Surface far too glossy / normal detail too weak, no error | Data map left at `'sRGB'` | `image.colorspace_settings.name = 'Non-Color'` |
| `AttributeError: 'ShaderNodeTexImage' object has no attribute 'colorspace_settings'` | color space set on the node | set it on `node.image` |
| `TypeError: bpy_struct: item.attr = val: enum "LINEAR" not found in ('Linear','Closest','Cubic','Smart')` | interpolation enum is capitalized-word, not uppercase | use `'Linear'` |
| `KeyError: bpy_prop_collection[key]: key "Fac" not found` on a Voronoi node | Voronoi has no `Fac`/`Factor` output at all (Noise/Wave/Magic keep `Fac` as the identifier of the socket named `Factor`) | resolve at runtime; Voronoi's scalar output is `Distance` |
| `RuntimeError: Node type ShaderNodeTexMusgrave undefined` | removed in 4.1 | use `ShaderNodeTexNoise` with `noise_type` |
| Object renders magenta/purple in viewport | Image datablock has `has_data == False` (missing file) | check `img.filepath`, `os.path.exists`, or `img.reload()` |
| `RuntimeError: Error: Current render engine does not support baking` | engine is EEVEE/Workbench | `scene.render.engine = 'CYCLES'` |
| `{'CANCELLED'}` with Info `No active and selected image texture node found in material "X"` (no exception); `RuntimeError: Error: No active image found, ...` if the object has no material | target Image Texture node not selected+active in that material (or no material) | set `nt.nodes.active = tex; tex.select = True` per material; assert the return value |
| `RuntimeError: Error: No active UV layer found in the object "X"` | mesh has no UV map | `mesh.uv_layers.new(name="UVMap")` or unwrap first |
| `RuntimeError: Operator bpy.ops.object.bake.poll() failed, context is incorrect` | no active object in the view layer | set `view_layer.objects.active` (use `temp_override` only for a custom selection) |
| Baked map has black smears / warped edges | selected-to-active with both `cage_extrusion` and `max_ray_distance` at 0 | set one of them, or supply `cage_object` |
| Dark seams along UV island borders after baking | margin too small or `EXTEND` type | `margin=16`, `margin_type='ADJACENT_FACES'` |
| Output directory empty after a successful bake | image never saved/packed | `img.save()` after the bake |
| Baked normal map looks inverted in an external engine | OpenGL vs DirectX green channel | `normal_g='NEG_Y'` at bake, or `nm.convention='DIRECTX'` at read |
| Banded / posterized normal or position bake | 8-bit image target | `bpy.data.images.new(..., float_buffer=True)` |
| Baked AO/normal looks noisy-smooth and hides errors | denoising left on during bake | `scene.cycles.use_denoising = False` |
| Texture tiles at the wrong density on some objects | non-uniform object scale baked into UVs | apply scale, or drive Mapping `Scale` per object |
<!-- ease:source S1 anchor="sRGB decode of a mid value shifts it (0.5 -> 0.214)" -->

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Texture resolution | 1024–2048 | 2048–4096 (4K face) | 512–1024 | 4096–8192 | n/a |
| Bake image bit depth | 8-bit PNG (color), 16-bit (normal) | 16/32-bit float EXR | 8-bit | 32-bit EXR | n/a |
| `float_buffer` on bake target | False for color, True for normal/position | True | False | True | n/a |
| Base color space | `sRGB` | `sRGB` | `sRGB` | `sRGB` | n/a |
| Data map color space | `Non-Color` | `Non-Color` | `Non-Color` | `Non-Color` | n/a |
| Image `interpolation` | `'Linear'` | `'Linear'` | `'Closest'` for pixel-art | `'Cubic'` | n/a |
| Image `extension` | `'REPEAT'` | `'REPEAT'` | `'EXTEND'` | `'EXTEND'` | n/a |
| Bake types needed | NORMAL, DIFFUSE, AO, ROUGHNESS, EMIT | NORMAL, DIFFUSE | none (procedural) | none (render direct) | none |
| Bake samples | 32–128 | 128 | — | 256+ | — |
| Bake margin (px) | 16 | 16 | — | 32 | — |
| `margin_type` | `ADJACENT_FACES` | `ADJACENT_FACES` | — | `ADJACENT_FACES` | — |
| `cage_extrusion` / `max_ray_distance` | 0.02–0.05 m | 0.01 m | — | 0.01 m | — |
| Procedural vs image | image (must bake) | image + procedural detail | procedural | image (measured) | none |
| Pack images into .blend | yes (portability) | no (large) | yes | no | n/a |
| `scene.render.use_texture_cache` (+ `use_auto_generate_texture_cache`, 5.2) | off | on for heavy sets | off | on | off |
<!-- ease:source S5 anchor="scene.render.use_texture_cache, use_auto_generate_texture_cache; prefs.filepaths.texture_cache_directory" -->
<!-- ease:source UNVERIFIED reason="use-case defaults are authoring guidance, not measured" -->

### 7. Verification checklist

- [ ] `assert all(i.colorspace_settings.name == 'Non-Color' for i in data_images)` — no gamma-decoded data maps.
- [ ] `assert bpy.data.images["albedo"].colorspace_settings.name == 'sRGB'` — color maps still sRGB.
- [ ] `assert all(img.has_data for img in bpy.data.images if img.source == 'FILE')` — every referenced file actually loaded (catches the magenta-render case).
- [ ] `assert nm.bl_idname == "ShaderNodeNormalMap" and nm.outputs["Normal"].is_linked` — normal map goes through the decoder node.
- [ ] `assert len(obj.data.uv_layers) > 0` — bake target has UVs.
- [ ] `assert bpy.context.scene.render.engine == 'CYCLES'` — bake will not be rejected. <!-- ease:source S2 anchor="bake rejected under EEVEE" -->
- [ ] `assert mat.node_tree.nodes.active.bl_idname == "ShaderNodeTexImage"` for every slot — bake target resolvable.
- [ ] `import numpy as np; px = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(px); assert px.std() > 1e-4` — the bake actually wrote something (not a flat image).
- [ ] For a normal bake: `assert 0.4 < px[2::4].mean() < 1.01` — blue channel dominated, i.e. tangent-space normals, not garbage.
- [ ] `assert os.path.getsize(img.filepath_raw) > 1024` — the file reached disk.
- [ ] Viewport screenshot in `MATERIAL` shading: texture is visible, tiling density matches intent, no magenta.

### 8. Sources

- [Image Texture node — Blender Manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html)
- [Color Management: Color Spaces (incl. `Non-Color`) — Blender Manual](https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html)
- [Render Baking — Blender Manual](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)
- [Blender 4.1 Release Notes: Rendering — Musgrave Texture replaced by Noise Texture](https://developer.blender.org/docs/release_notes/4.1/rendering/)
- [Blender 5.0 Release Notes: Rendering — Voronoi hashing change, Point Density removal, pass renames](https://developer.blender.org/docs/release_notes/5.0/rendering/)
- [Blender 5.1 Release Notes: Rendering — Normal Map OpenGL/DirectX convention](https://developer.blender.org/docs/release_notes/5.1/rendering/)
- [Blender 5.2 Release Notes: Python API — `bpy.data.file_path_foreach` expansion options](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- [Blender 5.2 Release Notes: Cycles — Texture Cache / `maketx`](https://developer.blender.org/docs/release_notes/5.2/cycles/)
- Node socket names, enum identifiers and bake operator properties cross-checked against
  Blender 5.2 source (`node_shader_tex_image.cc`, `node_shader_tex_noise.cc`,
  `node_shader_tex_voronoi.cc`, `node_shader_normal_map.cc`, `object_bake_api.cc`,
  `rna_nodetree.cc`), tag `v5.2.0`.
- `noise_type` / `noise_dimensions` enum identifier strings on `ShaderNodeTexNoise` were
  were verified against the live 5.2.0 RNA on 2026-10-13 (`MULTIFRACTAL, RIDGED_MULTIFRACTAL, HYBRID_MULTIFRACTAL, FBM, HETERO_TERRAIN`; dimensions `1D`-`4D`); still enumerate at runtime
  with `node.bl_rna.properties['noise_type'].enum_items.keys()` before setting.

## Failure Modes (Mandatory)

- **Surface far too glossy / normal detail weak, no error** — cause: a data map left at `sRGB` (0.5 decodes to 0.214 linear) — fix: `image.colorspace_settings.name = 'Non-Color'`
- **`TypeError: ... enum "LINEAR" not found in ('Linear', 'Closest', 'Cubic', 'Smart')`** — cause: image interpolation identifiers are capitalised words — fix: `'Linear'`
- **Bake returns `{'CANCELLED'}` and the image is unchanged** — cause: the Image Texture node is active but not selected, or absent (Info line: `No active and selected image texture node found in material`) — fix: select and activate the node in every material, assert `res == {'FINISHED'}`
- **`RuntimeError: Error: Current render engine does not support baking`** — cause: engine is EEVEE/Workbench — fix: `scene.render.engine = 'CYCLES'`
- **`RuntimeError: Error: No active UV layer found in the object`** — cause: mesh has no UV map — fix: `mesh.uv_layers.new()` or unwrap (smart_project works headless on 5.2.0)
- **Output directory empty after a successful bake** — cause: the bake only fills the in-memory image — fix: `img.save()` / `pack()`; the bake prints 'save it externally or pack it'
- **`TypeError: file_path_foreach() got an unexpected keyword argument 'expand_tokens'`** — cause: expansion options are flags, and the callback takes `(id, path, metadata)` — fix: `flags={'EXPAND_TOKENS', ...}`

## Sources

- [S1] Runtime probe 12 on Blender 5.2.0 LTS: texturing patterns and the full selected-to-active bake (NORMAL/DIFFUSE/AO/ROUGHNESS) executed as written — knowledge/_evidence/kb-261013/w1-probe12-5.2-runtime-output.txt — captured 2026-10-13 — sha256 b5abf65158c8efb4713da32fbf614dfdb0a48c0975089ed1063ad5f071b2dd5a
- [S2] Runtime probe 6 on 5.2.0: exact bake error strings, Fac/Factor lookup — knowledge/_evidence/kb-261013/w1-probe6-5.2-runtime-output.txt — captured 2026-10-13 — sha256 8d880cd427af7d24ff5a8d483602f721a6b20b830e0caa9c33b6c1b780c4f70e
- [S3] Runtime probe 7 on 5.2.0: bake poll/selection semantics (no active object, active-but-deselected node) — knowledge/_evidence/kb-261013/w1-probe7-5.2-runtime-output.txt — captured 2026-10-13 — sha256 33e1e495bc4fa4803a5cff8ea68d6daa1ce111823b17dca6c62acdf4beedf4a9
- [S4] Runtime probe 1 on 5.2.0: node I/O, noise_type/dimensions enums, bake operator properties and enums — knowledge/_evidence/kb-261013/w1-probe-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3ad8e713a6ecef0926ba15bdbcf92c69a4926d64eed1a7d9c25ba88310591388
- [S5] Runtime probe 4 on 5.2.0: scene.render texture-cache properties, file_path_foreach signature — knowledge/_evidence/kb-261013/w1-probe4-5.2-runtime-output.txt — captured 2026-10-13 — sha256 5a83fe0328bc6a7055a9635f78f69663004cf46e33b07e8628c33d5fc2c335e7
- [S6] Runtime probe 13 on 5.2.0: file_path_foreach corrected call, Image.unpack enum, pack of generated image — knowledge/_evidence/kb-261013/w1-probe13-5.2-runtime-output.txt — captured 2026-10-13 — sha256 6fa125c88aa3e30451fd616d726caef50131727c427fc19fa50e854919a6368b
- [S7] Blender 5.0 Rendering release notes (bake selected+active only, Voronoi hash, Point Density removed) — https://developer.blender.org/docs/release_notes/5.0/rendering/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-0-rendering.html) — captured 2026-10-13 — sha256 07d06fff1b852b431523c1666089e820fa851079b099352e13ed42e363e5b52c
- [S8] Blender 5.1 Rendering release notes (Normal Map OpenGL/DirectX) — https://developer.blender.org/docs/release_notes/5.1/rendering/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-1-rendering.html) — captured 2026-10-13 — sha256 0b70db69a79a6a77c43bfa4ce53f7537279b34981130f703f049189460743c7b
- [S9] Blender 5.2 LTS Python API release notes (file_path_foreach options) — https://developer.blender.org/docs/release_notes/5.2/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-python.html) — captured 2026-10-13 — sha256 613fac2fa63a96155d40c761571e1a7407c709926ebc2eff96f846343bb1b086
- [S10] Blender 5.2 LTS Cycles release notes (Texture Cache) — https://developer.blender.org/docs/release_notes/5.2/cycles/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-cycles.html) — captured 2026-10-13 — sha256 d23b908ff2615545b8fe1222818234efe6b3647e59fbe6aa3a6626f17cdbbf5c
- [S11] Blender Python API: BakeSettings (bpy.types.BakeSettings) — https://docs.blender.org/api/current/bpy.types.BakeSettings.html (frozen copy: knowledge/_evidence/kb-261013/w1-api-bake.html) — captured 2026-10-13 — sha256 e9737543892ea7981e70aca61d4251b1ef4d4067f486d088232ab1572e3380f5
- [S12] Runtime probe 3 on 5.2.0: socket values not clamped by the API — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995

---
name: texturing-baking
domain: shading
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Image texture wiring, color space correctness (sRGB vs Non-Color), procedural textures in 5.x, and the headless Cycles bake pipeline in bpy.
loads_with: [materials-pbr, render-engines, compositing-output]
tags: [texture, uv, color-space, normal-map, baking, procedural, image, non-color]
---

# Texturing & Baking

## 1. Mental model

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

Baking is a separate machine: `bpy.ops.object.bake` renders shading into the image
assigned to the **active, selected** Image Texture node of each material. It is
**Cycles only** — EEVEE has no bake engine.

## 2. Decision first

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
| Rendered EXR intermediate | `'Linear Rec.709'` or `'Working Space'` |

## 3. Rules

R1. Set `image.colorspace_settings.name = 'Non-Color'` for every non-color map.
    Why: sRGB decode applies a ~2.2 gamma; a 0.5 roughness texel becomes ~0.21 linear.
    Violation: everything looks too glossy / normals look weak; no error appears.

R2. Set the color space on the **Image datablock**, not on the node.
    Why: `ShaderNodeTexImage` has no color-space property; it reads from `node.image`.
    Violation: `AttributeError: 'ShaderNodeTexImage' object has no attribute
    'colorspace_settings'`.

R3. Create data images with `is_data=True` and `float_buffer=True` for bakes.
    Why: `is_data=True` sets the color space to `Non-Color` at creation;
    `float_buffer=True` gives 32-bit float, needed for normals/positions/HDR.
    Violation: banded normal maps; clipped values above 1.0 in emission/position bakes.

R4. Never assume `"Fac"` on a procedural texture node in 5.x.
    Why: 5.0 renamed shader-node `Fac` sockets to `Factor` (Noise, Voronoi, Attribute,
    Mix RGB…). Voronoi's first output is `Distance`, not `Factor`.
    Violation: `KeyError: ... key "Fac" not found`.

R5. Do not reference `ShaderNodeTexMusgrave`.
    Why: removed in 4.1, folded into Noise Texture. Old files auto-convert.
    Violation: `RuntimeError: Node type ShaderNodeTexMusgrave undefined`.

R6. Always drive normal maps through `ShaderNodeNormalMap`, never straight into `Normal`.
    Why: the node decodes 0..1 tangent-space RGB into a world-space normal using the
    UV tangent basis. A raw color link is interpreted as a vector and warps shading.
    Violation: surface looks tinted blue/purple and lighting is wrong at all angles.

R7. The Normal Map node's `uv_map` must name a UV map that exists on the mesh.
    Why: an empty string means "active UV map"; a wrong name silently falls back.
    Violation: normal detail rotates/mirrors on some faces.

R8. Baking requires `scene.render.engine == 'CYCLES'`.
    Why: `RE_bake_has_engine()` gate; EEVEE and Workbench implement no bake callback.
    Violation: `RuntimeError: Error: Current render engine does not support baking`.

R9. Before baking, the target Image Texture node must be both **active** and **selected**
    in each material's node tree.
    Why: 5.0 changed baking to write only to selected+active image texture nodes.
    Violation: `RuntimeError: Error: No active image found, add a material or bake to an
    external file` — or a silently unchanged image.

R10. The low-poly object must have a UV map before baking to image textures.
    Why: bake maps shading through UV space.
    Violation: `RuntimeError: Error: No active UV layer found in the object "X"`.

R11. In `--background`, call `bpy.ops.object.bake` inside a `temp_override`.
    Why: the operator polls for an active editable mesh in the view layer.
    Violation: `RuntimeError: Operator bpy.ops.object.bake.poll() failed, context is
    incorrect`.

R12. After baking, the image lives only in memory — call `image.save()` or `pack()`.
    Why: bake writes into the image buffer; nothing is written to disk implicitly
    (unless `save_mode='EXTERNAL'` with a `filepath`).
    Violation: process exits, bake is lost, output directory is empty.

R13. For selected-to-active bakes, set either `cage_object` **or** `max_ray_distance`,
    never rely on defaults (both 0.0).
    Why: with both zero, rays are cast along interpolated normals with unbounded
    distance and pick up far geometry.
    Violation: baked normal/AO map has black smears and skewed edges.

R14. Use `margin >= 8` (16 for 2K+) with `margin_type='ADJACENT_FACES'`.
    Why: mipmapping and bilinear filtering bleed background pixels across UV seams.
    Violation: visible dark seams along UV island borders in the shaded result.

## 4. bpy patterns

### 4.1 Image texture with correct color space

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

Note the enum identifiers for `interpolation` are **capitalized words**
(`'Linear'`, `'Closest'`, `'Cubic'`, `'Smart'`), not SCREAMING_CASE — a common
`TypeError: enum ... not found in ('Linear', 'Closest', 'Cubic', 'Smart')`.

### 4.2 UV → Mapping → Image chain with tiling

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

`ShaderNodeMapping` socket names are stable: inputs `Vector, Location, Rotation, Scale`,
output `Vector`. `ShaderNodeUVMap` has a single output `UV`.

### 4.3 Normal map wiring (tangent space)

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

### 4.4 Procedural textures — status in 5.x

```python
# Noise Texture (ShaderNodeTexNoise)
#   inputs : Vector, W, Scale, Detail, Roughness, Lacunarity, Offset, Gain, Distortion
#   outputs: "Factor" (5.x)  |  "Fac" (<=4.5),  "Color"
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

Musgrave → Noise conversion (per the 4.1 release notes):
`Roughness = pow(Lacunarity, -Dimension)` and `Detail_new = Detail_old - 1`.

### 4.5 Packed vs external images

```python
img.pack()                       # embed bytes in the .blend
img.unpack(method='USE_LOCAL')   # 'USE_LOCAL'|'WRITE_LOCAL'|'USE_ORIGINAL'|'WRITE_ORIGINAL'
print(img.packed_file is not None, img.filepath, img.source)  # source: 'FILE'|'GENERATED'|...

# Find every image path a render will need (5.2, incl. UDIM tiles and Cycles tx cache):
def collect(path, metadata):
    print(path, metadata.is_expanded, metadata.is_cache, metadata.is_readonly)
    return None                  # return a string to rewrite the path
bpy.data.file_path_foreach(collect, expand_tokens=True,
                           expand_sequences=True, expand_caches=True)
```

For headless pipelines, prefer packing or absolute paths — relative `//` paths resolve
against the .blend location, which differs when the file is generated in `/tmp`.

### 4.6 Saving images from Python

```python
img = bpy.data.images["BakeTarget"]
img.filepath_raw = "/out/bake_normal.png"
img.file_format  = 'PNG'          # 'PNG'|'OPEN_EXR'|'JPEG'|'TIFF'|'WEBP'|'HDR'|...
img.save()                        # or img.save(filepath="/out/x.png", quality=90,
                                  #             save_copy=True)

# Apply the scene's view transform on save (byte formats only):
img.save_render("/out/preview.png", scene=bpy.context.scene, quality=90)
```

`save()` writes raw data (correct for Non-Color / EXR).
`save_render()` applies the scene's render color management — use it for previews the
agent will *look at*, never for data maps.

### 4.7 The bake pipeline (Cycles, headless)

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

# Target image creation (data maps: is_data=True -> color space 'Non-Color')
tgt = bpy.data.images.new("BakeNormal", 2048, 2048,
                          alpha=False, float_buffer=True, is_data=True)
```

Verified `bpy.ops.object.bake` arguments (5.2): `type`, `pass_filter`, `filepath`,
`width`, `height`, `margin`, `margin_type`, `use_selected_to_active`,
`max_ray_distance`, `cage_extrusion`, `cage_object`, `normal_space`, `normal_r`,
`normal_g`, `normal_b`, `target`, `save_mode`, `use_clear`, `use_cage`,
`use_split_materials`, `use_automatic_name`, `uv_layer`.

Verified `type` enum: `COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT,
ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION`.

### 4.8 Full headless bake script skeleton

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

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Surface far too glossy / normal detail too weak, no error | Data map left at `'sRGB'` | `image.colorspace_settings.name = 'Non-Color'` |
| `AttributeError: 'ShaderNodeTexImage' object has no attribute 'colorspace_settings'` | color space set on the node | set it on `node.image` |
| `TypeError: bpy_struct: item.attr = val: enum "LINEAR" not found in ('Linear','Closest','Cubic','Smart')` | interpolation enum is capitalized-word, not uppercase | use `'Linear'` |
| `KeyError: bpy_prop_collection[key]: key "Fac" not found` on Noise/Voronoi | 5.0 renamed `Fac` → `Factor`; Voronoi has no such socket at all | resolve at runtime; Voronoi's scalar output is `Distance` |
| `RuntimeError: Node type ShaderNodeTexMusgrave undefined` | removed in 4.1 | use `ShaderNodeTexNoise` with `noise_type` |
| Object renders magenta/purple in viewport | Image datablock has `has_data == False` (missing file) | check `img.filepath`, `os.path.exists`, or `img.reload()` |
| `RuntimeError: Error: Current render engine does not support baking` | engine is EEVEE/Workbench | `scene.render.engine = 'CYCLES'` |
| `RuntimeError: Error: No active image found, add a material or bake to an external file` | target Image Texture node not selected+active in that material | set `nt.nodes.active = tex; tex.select = True` per material |
| `RuntimeError: Error: No active UV layer found in the object "X"` | mesh has no UV map | `mesh.uv_layers.new(name="UVMap")` or unwrap first |
| `RuntimeError: Operator bpy.ops.object.bake.poll() failed, context is incorrect` | no active editable mesh in `--background` | wrap in `bpy.context.temp_override(...)` |
| Baked map has black smears / warped edges | selected-to-active with both `cage_extrusion` and `max_ray_distance` at 0 | set one of them, or supply `cage_object` |
| Dark seams along UV island borders after baking | margin too small or `EXTEND` type | `margin=16`, `margin_type='ADJACENT_FACES'` |
| Output directory empty after a successful bake | image never saved/packed | `img.save()` after the bake |
| Baked normal map looks inverted in an external engine | OpenGL vs DirectX green channel | `normal_g='NEG_Y'` at bake, or `nm.convention='DIRECTX'` at read |
| Banded / posterized normal or position bake | 8-bit image target | `bpy.data.images.new(..., float_buffer=True)` |
| Baked AO/normal looks noisy-smooth and hides errors | denoising left on during bake | `scene.cycles.use_denoising = False` |
| Texture tiles at the wrong density on some objects | non-uniform object scale baked into UVs | apply scale, or drive Mapping `Scale` per object |

## 6. Parameter defaults by use case

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
| `use_texture_cache` (Cycles 5.2) | off | on for heavy sets | off | on | off |

## 7. Verification checklist

- [ ] `assert all(i.colorspace_settings.name == 'Non-Color' for i in data_images)` — no gamma-decoded data maps.
- [ ] `assert bpy.data.images["albedo"].colorspace_settings.name == 'sRGB'` — color maps still sRGB.
- [ ] `assert all(img.has_data for img in bpy.data.images if img.source == 'FILE')` — every referenced file actually loaded (catches the magenta-render case).
- [ ] `assert nm.bl_idname == "ShaderNodeNormalMap" and nm.outputs["Normal"].is_linked` — normal map goes through the decoder node.
- [ ] `assert len(obj.data.uv_layers) > 0` — bake target has UVs.
- [ ] `assert bpy.context.scene.render.engine == 'CYCLES'` — bake will not be rejected.
- [ ] `assert mat.node_tree.nodes.active.bl_idname == "ShaderNodeTexImage"` for every slot — bake target resolvable.
- [ ] `import numpy as np; px = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(px); assert px.std() > 1e-4` — the bake actually wrote something (not a flat image).
- [ ] For a normal bake: `assert 0.4 < px[2::4].mean() < 1.01` — blue channel dominated, i.e. tangent-space normals, not garbage.
- [ ] `assert os.path.getsize(img.filepath_raw) > 1024` — the file reached disk.
- [ ] Viewport screenshot in `MATERIAL` shading: texture is visible, tiling density matches intent, no magenta.

## 8. Sources

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
  not re-verified against 5.2 RNA in this pass — `[UNVERIFIED]`; enumerate at runtime
  with `node.bl_rna.properties['noise_type'].enum_items.keys()` before setting.

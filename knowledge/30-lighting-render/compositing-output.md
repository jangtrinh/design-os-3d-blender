---
name: compositing-output
domain: render
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Building the 5.x compositor node group in Python, enabling passes/AOVs, File Output wiring, scene- vs display-referred color, and VSE stitching.
loads_with: [render-engines, lighting, texturing-baking]
tags: [compositor, passes, aov, exr, file-output, color-management, vse, alpha]
id: compositing-output
title: "Compositing & Output"
when: [compositor-node-group, render-passes-aov, file-output-node, exr-multilayer, scene-vs-display-referred, vse-stitch]
trust_tier: community_reference
sources_checked: 2026-10-13
---


# Compositing & Output

## Purpose

Gives an agent the 5.x compositor data model (node group on `scene.compositing_node_group`), view-layer pass/AOV enabling, File Output wiring and VSE stitching so 4.x-era scripts are not reused blindly and exposure is judged on scene-linear data rather than a tone-mapped PNG.

## When to Use / When NOT

- ALLOWED: building or editing the compositor tree, Render Layers / File Output / Group Output wiring in 5.x — API names verified at tag v5.2.0
- ALLOWED: choosing EXR vs PNG output, alpha handling, cryptomatte/AOV/light-group masks for external comp
- ALLOWED: stitching a rendered image sequence to video through the VSE
- NOT ALLOWED: choosing Cycles vs EEVEE, samples, denoising, devices — use `render-engines` instead
- NOT ALLOWED: light power, HDRI, exposure planning for a scene — use `lighting` instead
- NOT ALLOWED: cinematic camera staging, motion blur, pose-rate vs frame-rate delivery rules — use `video-animation-cinematics` instead

## Core Knowledge Content

### 1. Mental model

Blender 5.0 rewrote the compositor's data model. The compositing graph is no longer <!-- ease:source S1 anchor="scene.node_tree was removed, use scene.compositing_node_group" -->
owned by the scene as `scene.node_tree`; it is an ordinary node-group data-block
assigned to `scene.compositing_node_group`. `scene.node_tree` **was removed** and
`scene.use_nodes` is deprecated (always returns True, setting it does nothing). The <!-- ease:source S1 anchor="scene.use_nodes is deprecated and will be removed in 6.0" -->
`Composite` output node was **removed** as well — the final image now leaves the tree
through a `NodeGroupOutput` whose first input is a Color socket. Any 4.x compositing
script fails immediately on 5.x.

Render passes are enabled per **view layer** (`view_layer.use_pass_*`), not per scene.
Custom AOVs and light groups are collections on the view layer. The compositor only runs <!-- ease:source S3 anchor="rna_def_scene_render_data use_compositing" -->
if `scene.render.use_compositing` is True.

The color-management distinction the agent must internalise: everything inside the
render and the compositor is **scene-referred** — unbounded, linear radiance where 1.0 is
"whatever 1.0 means for your lights", and highlights routinely reach 50 or 500. What you
*see* in a PNG is **display-referred** — bounded 0–1 after the view transform (AgX by
default). So a pixel that reads 0.98 in a PNG could be 1.2 or 40.0 in scene-linear. An
agent that judges "is this blown out?" from a tone-mapped PNG is measuring the tone
mapper, not the render. Judge exposure on EXR data or with the `False Color` view.

### 2. Decision first

| Goal | Approach |
|---|---|
| One image, no post | No compositor. `scene.render.use_compositing = False`. |
| Separate passes for external comp | Enable `view_layer.use_pass_*`, output `OPEN_EXR_MULTILAYER`. |
| Named files per pass, automated pipeline | `CompositorNodeOutputFile` with one `file_output_item` per pass. |
| Object/material masks | Cryptomatte passes (`use_pass_cryptomatte_object` + `pass_cryptomatte_depth`). <!-- ease:source S3 anchor="pass_cryptomatte_depth (RNA name; cryptomatte_levels is the DNA field)" --> |
| Per-shader custom mask | View-layer AOV + `ShaderNodeOutputAOV` in the material. |
| Per-light-group relight in comp | `view_layer.lightgroups.add(name=...)`, assign `object.lightgroup` (Cycles). |
| Alpha over a plate | `scene.render.film_transparent = True` + RGBA output. |
| Simple grade in Blender | Compositor nodes, or `scene.view_settings.look` / `.exposure`. |
| Stitch a rendered PNG sequence to video | VSE: `strips.new_image(...)` in a fresh scene, then render that scene to FFMPEG. <!-- ease:source S10 anchor="new_image" --> |
| Verify own exposure | Render EXR, read pixels, or set `view_transform='False Color'`. |

| I am on… | Compositor API |
|---|---|
| 5.0–5.2 | `scene.compositing_node_group` (a `CompositorNodeTree` node group), output via `NodeGroupOutput` <!-- ease:source S1 anchor="new way of creating a node tree" --> |
| 4.5 and earlier | `scene.use_nodes = True`, `scene.node_tree`, output via `CompositorNodeComposite` |

### 3. Rules

R1. In 5.x, build the compositor as a node group and assign it to <!-- ease:source S1 anchor="scene.node_tree was removed" -->
    `scene.compositing_node_group`.
    Why: `scene.node_tree` was removed in 5.0.
    Violation: `AttributeError: 'Scene' object has no attribute 'node_tree'`.

R2. Terminate the tree with a `NodeGroupOutput` whose first interface socket is a Color. <!-- ease:source S1 anchor="tree.interface.new_socket ... NodeSocketColor + NodeGroupOutput example" -->
    Why: `CompositorNodeComposite` was removed in 5.0; the group's first Color output is <!-- ease:source S2 anchor="no CompositorNodeComposite definition at v5.2.0 (absence)" -->
    the render result.
    Violation: `RuntimeError: Node type CompositorNodeComposite undefined`, or a tree
    that runs but never replaces the render.

R3. Enable passes on the **view layer**, then re-create the Render Layers node's outputs. <!-- ease:source S3 anchor="rna_def_view_layer use_pass_*" -->
    Why: `CompositorNodeRLayers` output sockets appear only after the pass is enabled and
    the depsgraph updates.
    Violation: `KeyError: bpy_prop_collection[key]: key "Normal" not found` on
    `rlayers.outputs`.

R4. Do not hardcode EXR pass names from memory. <!-- ease:source S1 anchor="Many render passes were renamed (DiffCol, IndexMA, Z)" -->
    Why: 5.0 renamed many passes to spell out abbreviations — `DiffCol` → `Diffuse Color`,
    `IndexMA` → `Material Index`, `Z` → `Depth`, and more.
    Violation: a downstream tool looking for `Z` finds nothing; comp scripts break.

R5. `CompositorNodeOutputFile` in 5.x uses `directory` + `file_name` + `file_output_items`. <!-- ease:source S1 anchor="File Output node now takes directory and file_name" -->
    Why: `base_path`, `file_slots` and `layer_slots` were **removed** in 5.0.
    Violation: `AttributeError: 'CompositorNodeOutputFile' object has no attribute
    'file_slots'`.

R6. Many `CompositorNode*` types were replaced by their `ShaderNode*` counterparts in 5.0. <!-- ease:source S1 anchor="CompositorNodeGamma replaced by ShaderNodeGamma" -->
    Why: node unification (e.g. `CompositorNodeGamma` → `ShaderNodeGamma`).
    Violation: `RuntimeError: Node type CompositorNodeGamma undefined`.

R7. `scene.render.use_compositing` must be True for the tree to affect the render. <!-- ease:source S3 anchor="use_compositing; rna_Scene_use_nodes_get comment" -->
    Why: it gates post-processing.
    Violation: File Output nodes write nothing and the render is unchanged; no error.

R8. Judge exposure on scene-referred data, never on a tone-mapped PNG. <!-- ease:source UNVERIFIED reason="the '~16.5 stops' AgX figure is not stated in any fetched source" -->
    Why: AgX compresses ~16.5 stops into 0–1 and desaturates highlights, so a clipped
    render and a correct render can look nearly identical.
    Violation: agent declares the lighting fine, then the EXR shows values of 300.

R9. Set `image_settings.color_management = 'OVERRIDE'` before touching a node's or <!-- ease:source S3 anchor="ImageFormatSettings.color_management enum FOLLOW_SCENE/OVERRIDE" -->
    format's own `view_settings`.
    Why: the default `'FOLLOW_SCENE'` means the per-output view settings are ignored.
    Violation: per-output color settings silently do nothing.

R10. Write EXR with `color_depth='32'` (or `'16'`) and never apply a view transform. <!-- ease:source S2 anchor="File Output node save_as_render property" -->
    Why: EXR is scene-linear storage; baking AgX into it destroys the data for comp.
    Violation: `save_as_render=True` on an EXR output produces a display-referred EXR
    that can never be regraded.

R11. `film_transparent` changes only the alpha of the background, not the lighting.
    Why: the world still contributes illumination; it is just invisible to camera rays.
    Violation: agent deletes the world to get an alpha and loses all ambient light.

R12. In 5.x VSE scripting, remember `context.scene` is not necessarily the sequencer's <!-- ease:source S1 anchor="The VSE now uses a different scene for its context (sequencer_scene)" -->
    scene.
    Why: 5.0 introduced `context.sequencer_scene` /
    `context.workspace.sequencer_scene`.
    Violation: strips added to the wrong scene; sequence renders empty.

R13. Prefer the new VSE strip time property names, but read the old ones defensively. <!-- ease:source S4 anchor="RNA_def_property_deprecated frame_final_start -> left_handle (510, 600)" -->
    Why: 5.1 renamed `frame_final_start` → `left_handle`, `frame_final_end` →
    `right_handle`, `frame_final_duration` → `duration` (old names deprecated, removal in 6.0).
    Violation: code written for 5.1+ breaks on 4.5, and vice versa.

R14. The File Output node's frame-number behaviour differs between still and animation <!-- ease:source UNVERIFIED reason="5.0 compositor release note (developer.blender.org) returned a bot challenge and could not be frozen" -->
    renders in 5.x.
    Why: 5.0 made it append the frame number only for animation renders. Include `####`
    in the file name if you want it in single-frame renders too.
    Violation: still renders overwrite the same file each time.

### 4. bpy patterns

#### 4.1 Version-aware compositor tree access

```python
import bpy

def get_comp_tree(scene, create=True):
    """Return a compositor node tree for `scene` on both 4.5 and 5.x."""
    if hasattr(scene, "compositing_node_group"):            # 5.0+
        tree = scene.compositing_node_group
        if tree is None and create:
            tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
            scene.compositing_node_group = tree
        return tree, "5.x"
    # 4.5 and earlier
    if create:
        scene.use_nodes = True
    return scene.node_tree, "4.x"
```

#### 4.2 Minimal 5.x compositor: Render Layers → (grade) → Group Output

```python
def build_comp_5x(scene):
    tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    scene.compositing_node_group = tree
    scene.render.use_compositing = True

    # The tree's FIRST Color output socket is the final image.
    tree.interface.new_socket(name="Image", in_out='OUTPUT',
                              socket_type='NodeSocketColor')

    rl  = tree.nodes.new("CompositorNodeRLayers");   rl.location  = (-600, 0)
    rl.scene = scene
    # rl.layer = scene.view_layers[0].name        # only if you have several view layers
    gam = tree.nodes.new("ShaderNodeGamma")          # 5.0: shader node, NOT CompositorNodeGamma
    gam.location = (-250, 0)
    gam.inputs["Gamma"].default_value = 1.0
    out = tree.nodes.new("NodeGroupOutput");         out.location = (100, 0)

    tree.links.new(rl.outputs["Image"], gam.inputs["Color"])
    tree.links.new(gam.outputs["Color"], out.inputs[0])
    return tree
```

Nodes that moved to the shader namespace in 5.0 include `ShaderNodeGamma`,
`ShaderNodeInvert`, `ShaderNodeRGBCurve`, `ShaderNodeHueSaturation`, `ShaderNodeMix` and
others. Resolve defensively:

```python
def new_node(tree, *candidates):
    for name in candidates:
        try:
            return tree.nodes.new(name)
        except RuntimeError:
            continue
    raise RuntimeError(f"none of {candidates} exist on this build")

gam = new_node(tree, "ShaderNodeGamma", "CompositorNodeGamma")   # 5.x first
```

#### 4.3 Enabling render passes / AOVs on the view layer

```python
vl = bpy.context.view_layer

# Data passes
vl.use_pass_combined = True
vl.use_pass_z = True                     # EXR layer is now called "Depth" (was "Z")
vl.use_pass_mist = False
vl.use_pass_normal = True
vl.use_pass_position = True
vl.use_pass_vector = False               # motion vectors (needs motion blur off)
vl.use_pass_uv = False
vl.use_pass_object_index = True          # EXR "Object Index" (was "IndexOB")
vl.use_pass_material_index = True        # EXR "Material Index" (was "IndexMA")

# Light passes (Cycles; EEVEE supports a subset)
vl.use_pass_diffuse_direct = True
vl.use_pass_diffuse_indirect = True
vl.use_pass_diffuse_color = True         # EXR "Diffuse Color" (was "DiffCol")
vl.use_pass_glossy_direct = True
vl.use_pass_glossy_indirect = True
vl.use_pass_glossy_color = True
vl.use_pass_transmission_direct = False
vl.use_pass_transmission_indirect = False
vl.use_pass_transmission_color = False
vl.use_pass_subsurface_direct = False
vl.use_pass_subsurface_indirect = False
vl.use_pass_subsurface_color = False
vl.use_pass_emit = True
vl.use_pass_environment = True
vl.use_pass_shadow = False
vl.use_pass_ambient_occlusion = False
vl.use_pass_transparent = False

# Cycles-only volume passes
vl.cycles.use_pass_volume_direct = False
vl.cycles.use_pass_volume_indirect = False
vl.cycles.denoising_store_passes = False   # store noisy + albedo + normal for later denoise

# EEVEE-only
vl.eevee.ambient_occlusion_distance = 0.2  # 5.0: moved here from scene.eevee.gtao_distance

# Cryptomatte
vl.use_pass_cryptomatte_object = True
vl.use_pass_cryptomatte_material = True
vl.use_pass_cryptomatte_asset = False
vl.pass_cryptomatte_depth = 6              # levels; 6 is the usual default
vl.use_pass_cryptomatte_accurate = True

# Custom AOV driven by ShaderNodeOutputAOV in materials
aov = vl.aovs.add()
aov.name = "WearMask"
aov.type = 'VALUE'                         # 'COLOR' | 'VALUE'

# Light groups (Cycles): per-light contribution, relightable in comp
lg = vl.lightgroups.add(name="KeyGroup")
bpy.data.objects["Key"].lightgroup = "KeyGroup"
```

After changing passes, the Render Layers node's outputs only update once the depsgraph
has been evaluated. In a script, re-fetch and check:

```python
bpy.context.view_layer.update()
print([o.name for o in rl.outputs])
```

Never assume a pass socket exists — resolve it:

```python
def out_socket(node, *names):
    have = {s.name: s for s in node.outputs}
    for n in names:
        if n in have:
            return have[n]
    raise KeyError(f"{names} not in {list(have)}")

depth = out_socket(rl, "Depth", "Z")                    # 5.x name first
dcol  = out_socket(rl, "Diffuse Color", "DiffCol")
midx  = out_socket(rl, "Material Index", "IndexMA")
```

#### 4.4 Multilayer EXR output (all passes, one file)

```python
r = bpy.context.scene.render
r.filepath = "//renders/beauty_"
imf = r.image_settings
imf.media_type  = 'MULTI_LAYER_IMAGE'      # 5.0+: MUST precede file_format
imf.file_format = 'OPEN_EXR_MULTILAYER'
imf.color_mode  = 'RGBA'
imf.color_depth = '32'                     # '16' half is fine for most passes
imf.exr_codec   = 'ZIP'                    # 'ZIP','PIZ','DWAA','DWAB','RLE','PXR24','NONE'
imf.color_management = 'FOLLOW_SCENE'      # EXR is scene-linear; never bake the view transform
```

Reading it back to verify:

```python
img = bpy.data.images.load("/renders/beauty_0001.exr")
print(img.is_multiview, img.depth, img.size[:])
# Layer/pass selection when wiring an Image node:
#   image_node.image = img
#   image_node.image_user.multilayer_layer = "ViewLayer"
#   image_node.image_user.multilayer_pass  = "Diffuse Color"
```

#### 4.5 File Output node (5.x API) — one file per pass

```python
def wire_file_output(tree, rl, directory="//passes/", file_name="shot",
                     passes=(("Image", 'RGBA'), ("Depth", 'RGBA'),
                             ("Normal", 'RGBA'), ("Diffuse Color", 'RGBA'))):
    fo = tree.nodes.new("CompositorNodeOutputFile")
    fo.location = (400, -300)
    fo.directory = directory                 # 5.0+: replaces base_path
    fo.file_name = file_name                 # 5.0+
    fo.format.media_type  = 'IMAGE'
    fo.format.file_format = 'OPEN_EXR'
    fo.format.color_depth = '32'
    fo.save_as_render = False                # keep EXR scene-referred
    fo.use_file_extension = True             # 5.2: independent of the scene setting

    # 5.0+: items, not slots. new(socket_type, name)
    for pass_name, sock_type in passes:
        item = fo.file_output_items.new(sock_type, pass_name)   # 'RGBA' == Color
        item.override_node_format = False
        # item.format.<...> if override_node_format = True
    # After creating items the node's input sockets exist with those names:
    for pass_name, _ in passes:
        try:
            src = out_socket(rl, pass_name)
        except KeyError:
            continue                          # pass not enabled on this view layer
        tree.links.new(src, fo.inputs[pass_name])
    return fo
```

Verified 5.2 RNA on `CompositorNodeOutputFile`: `directory`, `file_name`,
`file_output_items` (collection of `NodeCompositorFileOutputItem` with `name`,
`override_node_format`, `save_as_render`, `format`), `active_item_index`, `format`,
`save_as_render`, `use_file_extension`. <!-- ease:source S7 anchor="File Output node now has a File Extension checkbox independent of the scene setting (5.2)" -->
`file_output_items.new(socket_type, name)` — `socket_type` is one of
`'FLOAT','INT','BOOLEAN','VECTOR','RGBA','ROTATION','MATRIX','STRING','MENU', ...`;
use `'RGBA'` for image data.

Removed in 5.0 (do not use): `base_path`, `file_slots`, `layer_slots`.
Item names may contain a subdirectory (`"masks/character"`), restored in 5.1. <!-- ease:source S6 anchor="The File Output node now allows specifying directories in item names (5.1)" -->

#### 4.6 Color management, scene- vs display-referred

```python
sc = bpy.context.scene
vs, ds = sc.view_settings, sc.display_settings

print("display :", ds.display_device)      # 'sRGB','Display P3','Rec.1886','Rec.2020',
                                           # 'Rec.2100-PQ','Rec.2100-HLG'
print("view    :", vs.view_transform)      # DEFAULT 'AgX' since 4.0 (confirmed in 5.2)
print("look    :", vs.look)                # 'None', 'AgX - Punchy', ...
print("exposure:", vs.exposure)            # stops, 2**e, applied BEFORE the view transform
print("gamma   :", vs.gamma)               # applied AFTER the display conversion

# The blend file's scene-linear working space (5.0+, read-only from RNA):
print(bpy.data.colorspace.working_space)              # e.g. 'Linear Rec.709'
print(bpy.data.colorspace.working_space_interop_id)   # 'lin_rec709_scene' | 'lin_rec2020_scene'
                                                      # | 'lin_ap1_scene' (ACEScg)
# Changing it is an operator, not a property:
# bpy.ops.wm.set_working_color_space(working_space='ACEScg')

# Sequencer works in its own space (sRGB by default):
print(sc.sequencer_colorspace_settings.name)
```

Rules of thumb the agent should apply when reading its own render:

| Question | Look at |
|---|---|
| "Is my key light the right brightness?" | scene-linear EXR values, or `view_transform='False Color'` |
| "Is anything actually clipped?" | EXR: `px.max()`; PNG at `Standard`: pixels == 1.0 |
| "Does the composition/silhouette read?" | tone-mapped PNG at AgX — this is what a human sees |
| "Are there NaNs / broken shaders?" | EXR: `np.isnan(px).any()` |
| "Is the colour of the product accurate?" | `view_transform='Khronos PBR Neutral'` |

Per-output override (e.g. a display-referred JPEG preview alongside a linear EXR):

```python
fo.format.media_type = 'IMAGE'
fo.format.file_format = 'JPEG'
fo.format.color_management = 'OVERRIDE'          # required, else the next two are ignored
fo.format.view_settings.view_transform = 'AgX'
fo.format.view_settings.look = 'AgX - Base Contrast'
fo.save_as_render = True                          # apply the transform when writing bytes
```

#### 4.7 Transparent film / alpha

```python
r = bpy.context.scene.render
r.film_transparent = True                    # background alpha = 0, lighting unchanged
r.image_settings.color_mode = 'RGBA'         # otherwise alpha is discarded
bpy.context.scene.cycles.film_transparent_glass = False   # see through transmissive surfaces
bpy.context.scene.cycles.film_transparent_roughness = 0.1

# Alpha convention for compositing: Blender writes PREMULTIPLIED alpha.
# When re-loading a Blender render as an image, set:
img.alpha_mode = 'PREMUL'                    # 'STRAIGHT'|'PREMUL'|'CHANNEL_PACKED'|'NONE'
```

#### 4.8 VSE: stitching a rendered sequence programmatically

```python
import bpy, os, glob

def stitch(frames_dir, out_path, fps=24, res=(1920, 1080)):
    sc = bpy.data.scenes.new("Stitch")
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps, sc.render.fps_base = fps, 1.0
    sc.render.use_sequencer = True
    sc.render.use_compositing = False
    sc.render.filepath = out_path

    imf = sc.render.image_settings
    imf.media_type  = 'VIDEO'                 # 5.0+: before file_format
    imf.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
    sc.render.ffmpeg.audio_codec = 'NONE'

    se = sc.sequence_editor_create()
    files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
    assert files, f"no frames in {frames_dir}"

    strip = se.strips.new_image(name="frames", filepath=files[0],
                                channel=1, frame_start=1,
                                fit_method='ORIGINAL')
    for f in files[1:]:
        strip.elements.append(os.path.basename(f))

    sc.frame_start = 1
    sc.frame_end = len(files)
    # 5.1+ names (old frame_final_* still work, deprecated):
    #   strip.left_handle / right_handle / duration / content_start / content_duration
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(animation=True)
    return out_path
```

Verified 5.2 sequencer API: `scene.sequence_editor_create()` /
`sequence_editor_clear()`; `sequence_editor.strips`, `.strips_all`, `.channels`,
`.active_strip`; factory methods `new_image, new_movie, new_sound, new_clip, new_mask,
new_scene, new_meta, new_effect`, plus `remove, split, move_to_meta, parent_meta`.
`new_image(name, filepath, channel, frame_start, fit_method=...)`.

Type names: `bpy.types.Sequence` and friends were renamed to `bpy.types.Strip` in 4.4. <!-- ease:source S16 anchor="The bpy.types.Sequence and all related types were renamed to bpy.types.Strip" -->

5.1 strip time renames (old names deprecated, removal in 6.0): <!-- ease:source S4 anchor="RNA_def_property_deprecated ... 510, 600" -->
`frame_final_duration → duration`, `frame_final_start → left_handle`,
`frame_final_end → right_handle`, `frame_offset_start → left_handle_offset`,
`frame_offset_end → right_handle_offset`, `frame_duration → content_duration`,
`frame_start → content_start`, `animation_offset_start → content_trim_start`,
`animation_offset_end → content_trim_end`; new read-only `content_end`.

5.0 context change: `context.sequencer_scene` (== `context.workspace.sequencer_scene`)
is the scene the sequence editors act on; `context.scene` is the window's active scene
and may differ.

For a pure encode with no Blender-side processing, `ffmpeg` on the command line is more
predictable than the VSE — use the VSE when you need cross-dissolves, retiming, or an
audio track.

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'Scene' object has no attribute 'node_tree'` | removed in 5.0 | `scene.compositing_node_group` |
| `RuntimeError: Node type CompositorNodeComposite undefined` | removed in 5.0 | `NodeGroupOutput` + Color interface socket |
| `RuntimeError: Node type CompositorNodeGamma undefined` | replaced by shader node | `ShaderNodeGamma` (try/except fallback) <!-- ease:source S1 anchor="CompositorNodeGamma -> ShaderNodeGamma" --> |
| `AttributeError: 'CompositorNodeOutputFile' object has no attribute 'file_slots'` | removed in 5.0 | `file_output_items.new('RGBA', name)` <!-- ease:source S1 anchor="Removed: file_slots, layer_slots, base_path" --> |
| `AttributeError: ... 'base_path'` | removed in 5.0 | `directory` + `file_name` <!-- ease:source S1 anchor="Removed: base_path" --> |
| `KeyError: ... key "Normal" not found` on Render Layers outputs | pass not enabled, or depsgraph not updated | set `view_layer.use_pass_normal = True`, then `view_layer.update()` |
| Downstream tool cannot find the `Z` pass in the EXR | 5.0 renamed it to `Depth` | resolve names defensively; update the consumer |
| Compositor tree built, render unchanged, no files written | `scene.render.use_compositing` False | set it True <!-- ease:source S3 anchor="use_compositing" --> |
| File Output overwrites the same file each still render | 5.0 only appends frame numbers for animation renders | put `####` in `file_name`, or render with `animation=True` |
| Per-output view transform ignored | `image_settings.color_management` left at `'FOLLOW_SCENE'` | set `'OVERRIDE'` |
| EXR looks "already graded" and cannot be regraded | `save_as_render=True` on a linear format | set it False for EXR |
| PNG has a hard black background instead of alpha | `color_mode` is `'RGB'` | `'RGBA'` + `film_transparent = True` |
| Compositing a Blender render over a plate shows dark fringes | premultiplied alpha treated as straight | `img.alpha_mode = 'PREMUL'` |
| Agent says "looks correctly exposed", EXR shows values of 300 | judged a tone-mapped PNG (AgX) | inspect EXR pixels, or use `False Color` |
| `TypeError: ... enum "FFMPEG" not found` | `media_type` not set to `'VIDEO'` first | set `media_type`, then `file_format` <!-- ease:source S3 anchor="ImageFormatSettings media_type enum" --> |
| VSE strips added but the render is blank | strips created on `context.scene` while the sequencer uses another scene, or `use_sequencer` False | use an explicit scene + `temp_override`; `render.use_sequencer = True` |
| `AttributeError: 'Strip' object has no attribute 'frame_final_start'` on very new builds | 5.1 renames; old names deprecated (removal in 6.0) | prefer `left_handle`, fall back with `getattr` <!-- ease:source S4 anchor="deprecated, removal 6.0 (510, 600)" --> |
| Cryptomatte mattes are noisy / miss thin edges | `pass_cryptomatte_depth` too low | raise to 6–8, enable `use_pass_cryptomatte_accurate` |
| AOV socket exists in the material but the pass is empty | AOV name mismatch between `view_layer.aovs` and `ShaderNodeOutputAOV.name` | make the strings identical |

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `use_compositing` | False | True | True | True | False |
| Output format | PNG | `OPEN_EXR_MULTILAYER` | PNG RGBA → FFMPEG | `OPEN_EXR` | PNG |
| `media_type` | `IMAGE` | `MULTI_LAYER_IMAGE` | `IMAGE` then `VIDEO` | `IMAGE` | `IMAGE` <!-- ease:source S3 anchor="media_type enum IMAGE/MULTI_LAYER_IMAGE/VIDEO" --> |
| `color_depth` | `8` | `16` (half) | `16` | `32` | `8` |
| `exr_codec` | — | `ZIP` | — | `PIZ` / `ZIP` | — <!-- ease:source S3 anchor="ImageFormatSettings exr_codec" --> |
| Passes enabled | Combined only | Combined, Depth, Normal, Vector, Cryptomatte Object/Material, Diffuse/Glossy D+I+C | Combined, Depth, Cryptomatte Object | Combined, Depth, Cryptomatte Material, AO, Shadow | Combined |
| `pass_cryptomatte_depth` | — | 6 | 6 | 8 | — <!-- ease:source S3 anchor="range 2-16 step 2; default value UNVERIFIED" --> |
| AOVs | none | wear/ID masks | element masks | material masks | none |
| Light groups | none | key/fill/rim | none | key/rim/HDRI | none |
| `film_transparent` | True | False | True | True | False |
| `color_mode` | `RGBA` | `RGBA` | `RGBA` | `RGBA` | `RGB` |
| `view_transform` | `AgX` | `AgX` | `Standard` | `Khronos PBR Neutral` | `Standard` <!-- ease:source S8 anchor="view transforms list incl. AgX and Khronos PBR Neutral" --> |
| `look` | `None` | `AgX - Base Contrast` | `None` | `None` | `None` <!-- ease:source S14 anchor="looks: AgX - Base Contrast / Medium High Contrast exist; 'AgX - Medium Contrast' does not (Medium Contrast is a Filmic look)" --> |
| `save_as_render` on File Output | True (PNG preview) | False (EXR) | True | False | True |
| VSE used | no | for dailies | yes | no | no |
| FFMPEG codec | — | H264 (dailies) | H264 | — | — |
| `constant_rate_factor` | — | `MEDIUM` | `HIGH` | — | — <!-- ease:source S3 anchor="FFmpegSettings constant_rate_factor" --> |

### 7. Verification checklist

- [ ] `assert bpy.context.scene.compositing_node_group is not None` — a 5.x tree exists.
- [ ] `assert any(s.socket_type == 'NodeSocketColor' for s in tree.interface.items_tree if getattr(s, 'in_out', '') == 'OUTPUT')` — the group has a Color output to carry the render.
- [ ] `assert any(n.bl_idname == "NodeGroupOutput" for n in tree.nodes)` — the tree terminates.
- [ ] `assert bpy.context.scene.render.use_compositing is True` — the tree will actually run.
- [ ] `bpy.context.view_layer.update(); assert "Depth" in {o.name for o in rl.outputs}` — the enabled pass produced a socket under its 5.x name.
- [ ] `assert fo.directory and fo.file_name` — File Output has somewhere to write.
- [ ] `assert all(i.name in {s.name for s in fo.inputs} for i in fo.file_output_items)` — every item has a matching input socket.
- [ ] After rendering: `import os; assert len(os.listdir(bpy.path.abspath(fo.directory))) >= len(fo.file_output_items)` — files actually written.
- [ ] `assert bpy.context.scene.render.image_settings.media_type == 'MULTI_LAYER_IMAGE'` when `file_format == 'OPEN_EXR_MULTILAYER'`.
- [ ] Read the EXR back and `assert not np.isnan(px).any()` and `assert px.max() < 1e4` — no NaNs, no runaway lights hidden by tone mapping.
- [ ] `assert 0.03 < np.median(px[px > 0]) < 0.6` on a well-exposed EXR — the scene-linear midpoint is in a sane band.
- [ ] With `film_transparent = True`: `assert px[..., 3].min() == 0.0` — the background really is transparent.
- [ ] For a VSE stitch: `assert os.path.getsize(out_path) > 100_000` and the frame count matches `scene.frame_end - scene.frame_start + 1`.

### 8. Source notes and unverified items (legacy list)
- [Blender 5.0 Release Notes: Python API — `scene.node_tree` removed, `compositing_node_group`, File Output node API, node type replacements](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.0 Release Notes: Compositor — Composite node removed, File Output redesign, Z Combine → Depth Combine, Alpha Over socket renames](https://developer.blender.org/docs/release_notes/5.0/compositor/)
- [Blender 5.0 Release Notes: Rendering — render pass renames (`DiffCol` → `Diffuse Color`, `IndexMA` → `Material Index`, `Z` → `Depth`)](https://developer.blender.org/docs/release_notes/5.0/rendering/)
- [Blender 5.1 Release Notes: Compositor — File Output subdirectories in item names, metadata](https://developer.blender.org/docs/release_notes/5.1/compositor/)
- [Blender 5.2 Release Notes: Compositor — File Output `use_file_extension`](https://developer.blender.org/docs/release_notes/5.2/compositor/)
- [Blender 5.1 Release Notes: Python API — VSE strip time property renames](https://developer.blender.org/docs/release_notes/5.1/python_api/)
- [Blender 4.4 Release Notes: Python API — `bpy.types.Sequence` → `bpy.types.Strip`](https://developer.blender.org/docs/release_notes/4.4/python_api/)
- [Color Management: Color Spaces / Working Space — Blender Manual](https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html)
- [Color Management: Displays and Views — Blender Manual](https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html)
- RNA names verified against Blender 5.2 source: `rna_nodetree.cc` (File Output node,
  socket data-type enum), `rna_scene.cc` (`use_pass_*`, cryptomatte, `ImageFormatSettings`,
  FFmpeg), `rna_layer.cc`, `rna_sequencer.cc` / `rna_sequencer_api.cc`,
  `rna_main.cc` (`bpy.data.colorspace`), `scripts/startup/bl_ui/properties_render.py`
  (`bpy.ops.wm.set_working_color_space`), tag `v5.2.0`.
- `[UNVERIFIED]`: the complete 5.0 pass-rename table (only `DiffCol`, `IndexMA` and `Z`
  are named in the release notes). Enumerate the actual names at runtime from
  `CompositorNodeRLayers.outputs` or from the EXR header rather than assuming.
- `[UNVERIFIED]`: default value of `view_layer.pass_cryptomatte_depth` — read it before <!-- ease:source S3 anchor="RNA range 2.0-16.0, default not set in RNA" -->
  overriding.

## Failure Modes (Mandatory)

- **`AttributeError: 'Scene' object has no attribute 'node_tree'` when running a 4.x compositing script** — cause: `scene.node_tree` was removed in 5.0 — fix: create a `CompositorNodeTree` group and assign `scene.compositing_node_group` (see 4.1, 4.2).
- **Compositor tree built, render unchanged, no File Output files written, no error** — cause: `scene.render.use_compositing` is False — fix: set it True and assert it in the verification checklist.
- **Agent reports exposure fine from a PNG, EXR pixels reach 300** — cause: judged the AgX display-referred PNG instead of scene-linear data — fix: read EXR pixels or use the `False Color` view transform; cf. repo lesson that numeric and visual gates can pass while the owner still rejects the result. <!-- ease:source S12 anchor="line 37, DC-01 film rejected" -->
- **Animation delivered as a video but frames repeat (poses at 5/s encoded at 30 fps)** — cause: media contract not recorded before render; composite/encode stages hide the pose rate — fix: record frame rate and distinct-state count in the media receipt before rendering (AGENTS.md 'Motion contract'). <!-- ease:source S12 anchor="line 37; lessons line 55" --> <!-- ease:source S13 anchor="Motion contract before any animation render" -->
- **Pass named `Z` not found by a downstream tool after moving to 5.x** — cause: 5.0 renamed `Z` to `Depth` and other passes — fix: enumerate `CompositorNodeRLayers.outputs` at runtime, update the consumer.

## Sources

- [S1] Blender 5.0 Release Notes: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen: knowledge/_evidence/kb-261013/w3-developer-blender-org-docs-release_notes-5-0-python_api-.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S2] Blender source rna_nodetree.cc @ v5.2.0 — https://raw.githubusercontent.com/blender/blender/v5.2.0/source/blender/makesrna/intern/rna_nodetree.cc (frozen: knowledge/_evidence/kb-261013/w3-src-rna_nodetree.cc) — captured 2026-10-13 — sha256 a03c62855eb25780389fb67d16fecdd98c3a27f6899ae262bc4f99610753ce1c
- [S3] Blender source rna_scene.cc @ v5.2.0 — https://raw.githubusercontent.com/blender/blender/v5.2.0/source/blender/makesrna/intern/rna_scene.cc (frozen: knowledge/_evidence/kb-261013/w3-src-rna_scene.cc) — captured 2026-10-13 — sha256 54b6e437b4fae8baaffaf60c97516d29c6f643d37c73d2c695e1a71c1f36a743
- [S4] Blender source rna_sequencer.cc @ v5.2.0 — https://raw.githubusercontent.com/blender/blender/v5.2.0/source/blender/makesrna/intern/rna_sequencer.cc (frozen: knowledge/_evidence/kb-261013/w3-src-rna_sequencer.cc) — captured 2026-10-13 — sha256 43648019cbdbc5ae09a91453f474e40579bb394862a9ee6964bb4b5652362c30
- [S6] Blender 5.1 Release Notes: Compositor — https://developer.blender.org/docs/release_notes/5.1/compositor/ (frozen: knowledge/_evidence/kb-261013/w3-developer-blender-org-docs-release_notes-5-1-compositor-.html) — captured 2026-10-13 — sha256 4eb3230525d37b44a848700d8e8317b4d4ea8327b46eeefa53b686c6811c643f
- [S7] Blender 5.2 Release Notes: Compositor — https://developer.blender.org/docs/release_notes/5.2/compositor/ (frozen: knowledge/_evidence/kb-261013/w3-developer-blender-org-docs-release_notes-5-2-compositor-.html) — captured 2026-10-13 — sha256 e1217cfb3ee7e9a9deb955627f9a948f5e675961e76691bdbfd4defb7d1544b8
- [S8] Color Spaces — Blender Manual — https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html (frozen: knowledge/_evidence/kb-261013/w3-docs-blender-org-manual-en-latest-render-color_management-color_spaces.html) — captured 2026-10-13 — sha256 8176210071982a904cbac1b74b78f09f56538aefc69fb1e8131ddf8f30e2ee0d
- [S10] Blender source rna_sequencer_api.cc @ v5.2.0 — https://raw.githubusercontent.com/blender/blender/v5.2.0/source/blender/makesrna/intern/rna_sequencer_api.cc (frozen: knowledge/_evidence/kb-261013/w3-src-rna_sequencer_api.cc) — captured 2026-10-13 — sha256 ba2959c7075ecaa916dbdcfa4811791a82da5481f39600fa0546a941d32e6410
- [S12] Repo: native build pipeline lessons (DC-01 D05 pose rate) — docs/native-build-pipeline-lessons.md — captured 2026-10-13 — sha256 f3bce9c77b38489998cbf42f9ee068b382a8ad09f782182a5ad61f784c38accb
- [S13] Repo: AGENTS.md (Motion contract, headless route) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7
- [S14] Blender OCIO config.ocio @ v5.2.0 (views, looks) — https://raw.githubusercontent.com/blender/blender/v5.2.0/release/datafiles/colormanagement/config.ocio (frozen: knowledge/_evidence/kb-261013/w3-src-config.ocio) — captured 2026-10-13 — sha256 47a7d83e79c1d21f49ba6c505efe311da723471688c614b5c366e1da7eb8ea3a
- [S16] Blender 4.4 Release Notes: Python API — https://developer.blender.org/docs/release_notes/4.4/python_api/ (frozen: knowledge/_evidence/kb-261013/w3-developer-blender-org-docs-release_notes-4-4-python_api-.html) — captured 2026-10-13 — sha256 d6401ff1d90dff3a0b93c0d583d482203558257980bcf397ecf849809fb0ba33

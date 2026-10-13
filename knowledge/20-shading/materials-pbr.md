---
name: materials-pbr
domain: shading
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Principled BSDF socket inventory for 5.x, physically plausible value ranges, and safe runtime socket resolution when building material node trees in bpy.
loads_with: [texturing-baking, render-engines, lighting]
tags: [material, principled-bsdf, shader-nodes, node-tree, pbr, socket-names, material-slots]
id: materials-pbr
title: "Materials & PBR with the Principled BSDF"
when: [principled-bsdf-sockets, build-material-bpy, socket-name-resolution, material-slots, pbr-value-ranges]
trust_tier: community_reference
sources_checked: 2026-10-13
---
# Materials & PBR with the Principled BSDF

## Purpose

Give an agent the Principled BSDF 5.x socket inventory (read from a live 5.2.0 node), plausible value ranges, and the runtime socket-resolution pattern so material node trees are built without KeyErrors or silently wrong channels.

## When to Use / When NOT

- ALLOWED: creating or editing a material node tree, assigning slots, or choosing physically plausible Principled values in bpy
- ALLOWED: a `KeyError` on a socket name or a material that renders black/grey after a script ran
- NOT ALLOWED: texture wiring, colour spaces and baking — use `texturing-baking` instead
- NOT ALLOWED: film-grade skin, hair, thin-film and Cycles SSS/hair optimisation — use `master-artisan-pbr-and-grooming` instead
- NOT ALLOWED: version rename history across the whole API — use `blender-version-matrix` instead

## Core Knowledge Content


### 1. Mental model

A Blender material is an ID data-block (`bpy.data.materials`) that owns a shader
node tree (`mat.node_tree`). Rendering only ever reads the node linked into the
`Material Output` node's `Surface` input. In 5.x every material is created with a
node tree already present — `mat.use_nodes` is deprecated and has no effect. <!-- ease:source S7 anchor="'material.use_nodes is deprecated and will be removed in 6.0. Currently it always returns True and setting it has no effect'" -->
The Principled BSDF (`ShaderNodeBsdfPrincipled`) is a layered uber-shader based on <!-- ease:source S6 anchor="'It is based on the OpenPBR Surface shading model' (manual); spec v1.1.1 at S11" -->
the OpenPBR Surface model: a base layer (metal / diffuse / subsurface / transmission),
a specular layer, an optional thin film, a coat, a sheen, and emission. The agent's
job is almost always "wire a small graph and set a handful of scalar inputs to
physically plausible numbers", not "invent a shader".

The single dominant failure: **hardcoding socket name strings**. Blender 4.0 renamed
most Principled inputs, and 5.0 renamed the `Fac` socket *name* to `Factor` on shader nodes (the **identifier** stays `Fac`, and on 5.2.0 both `outputs["Fac"]` and `outputs["Factor"]` resolve).
A script written against 3.x silently raises `KeyError` on 5.2; worse, a script that
guesses a name that *happens* to exist writes to the wrong channel and the agent sees
a plausible-but-wrong render. Always resolve sockets at runtime.

### 2. Decision first

| Situation | Shader choice | Notes |
|---|---|---|
| Any opaque surface, any engine | Principled BSDF | Default. 95% of cases. |
| Pure light emitter (area light panel, screen) | `ShaderNodeEmission` | Cheaper; no specular layer. Or Principled with `Emission Strength` > 0. |
| Perfect glass / liquid | Principled, `Transmission Weight`=1, `Roughness`≈0 | Cycles only for correct refraction; EEVEE approximates. |
| Thin sheet (leaf, paper, window pane) | Principled + `Thin Wall`=True | Skips SSS radius/scale; set material `thickness_mode='SLAB'` for EEVEE. |
| Shadow-only / invisible catcher | `ShaderNodeBsdfTransparent` + object flags | See `object.is_shadow_catcher` / `is_holdout` (Cycles). |
| Unlit / flat color for compositing masks | Emission, strength 1 | With `Standard` view transform, output == input color. |
| Many objects, one look | One material + `mesh.polygons[i].material_index` | Do not duplicate materials per object. |

| Axis | Choice |
|---|---|
| Need per-object color variation | Object Info node `Random`/`Color` → drives Base Color. One material, N objects. |
| Need per-face variation | Multiple material slots + `material_index`, or an attribute/vertex color. |
| Reusable shading logic | Node group (`bpy.data.node_groups.new(name, 'ShaderNodeTree')`) + `ShaderNodeGroup`. |
| Exporting to glTF/USD/game engine | Principled only, no procedural nodes, textures baked. |

### 3. Rules

R1. Never hardcode a Principled socket name; resolve it at runtime by search or index.
    Why: 4.0 renamed most Principled sockets (table in `blender-version-matrix`); 5.0 renamed the `Fac` socket name to `Factor` (identifier unchanged); names differ per version and unavailable sockets are not reachable by name.
    Violation: `KeyError: 'bpy_prop_collection[key]: key "Specular" not found'`.

R2. Do not set `mat.use_nodes = True` and expect it to build a tree in 5.x.
    Why: deprecated in 5.0 (removal in 6.0); always returns True, setting is a no-op.
    The default tree is created by `bpy.data.materials.new()` itself. <!-- ease:source S1 anchor="principled_in_default_tree = ShaderNodeBsdfPrincipled + ShaderNodeOutputMaterial; setting use_nodes False reads back True (probe 3)" -->
    Violation: on 4.5 code paths that create a material, then clear nodes, then set
    `use_nodes` again to "restore defaults", the tree stays empty and renders black.

R3. Metallic is 0.0 or 1.0. Never a mid value except across a texture boundary. <!-- ease:source UNVERIFIED reason="authoring convention; the manual describes Metallic as a blend between dielectric and metallic models" -->
    Why: a surface is either a conductor or a dielectric; 0.5 is not a real material.
    Violation: washed-out grey material with wrong Fresnel; base color reads as tint
    rather than albedo.

R4. Never set `Roughness` to exactly 0.0 on a path-traced surface you want to look real. <!-- ease:source UNVERIFIED reason="firefly/mirror behaviour and the 0.03-0.05 floor are practitioner conventions, not measured here" -->
    Why: 0.0 is a mathematically perfect mirror — it produces fireflies at grazing
    angles in Cycles and unstable specular in EEVEE. Floor at 0.03–0.05.
    Violation: single blown-out white pixels ("fireflies") in the render; denoiser
    smears them into blobs.

R5. Dielectric base color luminance must stay in ~0.03–0.9 linear. <!-- ease:source UNVERIFIED reason="albedo bounds are practitioner conventions" -->
    Why: no real non-metal reflects >90% or <2% of light diffusely; pure `(0,0,0)` and
    pure `(1,1,1)` are unphysical and break GI energy balance.
    Violation: rooms that never converge (white walls bouncing forever) or crushed
    black areas with no detail after the view transform.

R6. Set `IOR`, not `Specular IOR Level`, when you know the material. <!-- ease:source S6 anchor="manual: IOR Level '0.5 means no adjustment, 0 removes all reflections, 1 doubles them at normal incidence'" -->
    Why: `Specular IOR Level` (default 0.5 = no adjustment) is a texturing convenience
    that *modulates* IOR; the physical parameter is `IOR`.
    Violation: dialing `Specular IOR Level` to 1.0 doubles reflections at normal
    incidence, giving a plasticky sheen the agent will misread as "too shiny lighting".

R7. Coat / Sheen / Subsurface / Transmission weights are 0 or 1, not sliders. <!-- ease:source S6 anchor="manual states 'typically zero or one' for Subsurface Weight and Coat Weight only; Sheen and Transmission not stated (partly UNVERIFIED)" -->
    Why: they are layer presence, not intensity. Textured variation is the exception.
    Violation: `Coat Weight = 0.3` gives a physically meaningless partial lacquer that
    darkens the base without a readable highlight.

R8. Link the Material Output explicitly; do not assume the default link survives edits.
    Why: `nodes.clear()` removes the output node too.
    Violation: render is fully black/transparent with no traceback.

R9. Assign materials to mesh data (`obj.data.materials`), not to the object slot, <!-- ease:source S2 anchor="MaterialSlot.link enum OBJECT/DATA, default DATA; override sets slot.material while me.materials[0] stays 'a'" -->
    unless you intentionally want per-instance overrides.
    Why: `slot.link` defaults to `'DATA'`; linked duplicates share data materials.
    Violation: material appears on one object but not on its linked copies.

R10. `mesh.polygons[i].material_index` must be `< len(obj.data.materials)`. <!-- ease:source UNVERIFIED reason="out-of-range values are stored unclamped (probe 11: 7 stored with 2 slots); render-time clamping not tested" -->
    Why: out-of-range indices are clamped/undefined and render with slot 0.
    Violation: faces silently render with the wrong material, no error.

R11. Build node graphs with explicit `node.location` values. <!-- ease:source S10 anchor="nodes.new('ShaderNodeTexImage').location == (0.0, 0.0); default-tree nodes sit at (-200,100) and (200,100)" -->
    Why: all new nodes default to (0,0) and overlap; a viewport/node-editor screenshot
    is then unreadable and the agent cannot self-verify the graph.
    Violation: screenshot shows one node stack; agent concludes "graph is empty".

R12. Use `nodes.new(type='ShaderNodeX')` with the *bl_idname*, not the UI label. <!-- ease:source S5 anchor="nodes.new('Principled BSDF') -> RuntimeError: Error: Node type Principled BSDF undefined" -->
    Why: `nodes.new` takes the RNA type string.
    Violation: `RuntimeError: Node type Principled BSDF undefined`.

R13. For a material to work in both Cycles and EEVEE, avoid Cycles-only inputs. <!-- ease:source S6 anchor="manual flags Cycles Only: Diffuse Roughness, Subsurface Random Walk methods, Subsurface IOR, Subsurface Anisotropy, Anisotropic/Rotation, Thin Film" -->
    Why: `Anisotropic`, `Anisotropic Rotation`, `Subsurface IOR`, `Subsurface Anisotropy`,
    `Thin Film *` and the Diffuse `Roughness` (Oren-Nayar) are Cycles-only.
    Violation: EEVEE render silently ignores them; the two engines disagree and the
    agent chases a lighting bug that is actually a shader-feature gap.

### 4. bpy patterns

#### 4.1 The one pattern that matters — runtime socket resolution

```python
import bpy

def find_socket(node, *candidates, inputs=True):
    """Return the first socket whose name matches any candidate (case-insensitive,
    exact then prefix). Returns None if nothing matches — caller decides."""
    coll = node.inputs if inputs else node.outputs
    names = {s.name.lower(): s for s in coll}
    for c in candidates:
        s = names.get(c.lower())
        if s is not None:
            return s
    for c in candidates:                      # prefix fallback: "Coat" -> "Coat Weight"
        for s in coll:
            if s.name.lower().startswith(c.lower()):
                return s
    return None

def set_input(node, value, *candidates):
    s = find_socket(node, *candidates)
    if s is None:
        raise KeyError(f"{node.bl_idname}: none of {candidates} in "
                       f"{[i.name for i in node.inputs]}")
    s.default_value = value
    return s

# Executed on 5.2.0; names for 3.x/4.x follow the rename table:
bsdf = mat.node_tree.nodes["Principled BSDF"]
set_input(bsdf, 0.35, "Specular IOR Level", "Specular")        # 4.0 rename
set_input(bsdf, 0.0,  "Subsurface Weight", "Subsurface")       # 4.0 rename
set_input(bsdf, 1.0,  "Transmission Weight", "Transmission")   # 4.0 rename
set_input(bsdf, 1.0,  "Coat Weight", "Clearcoat", "Coat")      # 4.0 rename
set_input(bsdf, 0.0,  "Sheen Weight", "Sheen")                 # 4.0 rename
set_input(bsdf, (1, 0.4, 0.1, 1), "Emission Color", "Emission")# 4.0 rename
```
<!-- ease:source S2 anchor="set_input resolved all six renamed sockets on 5.2.0; direct inputs['Specular'|'Subsurface Color'|'Clearcoat'] raise KeyError" -->

Always print the inventory before guessing:

```python
print([(i, s.name, s.type, s.is_unavailable) for i, s in enumerate(bsdf.inputs)])
```

#### 4.2 Verified 5.2 Principled BSDF input inventory (index → name) <!-- ease:source S1 anchor="SOCK 0-31 read from a live 5.2.0 Principled node" -->

Index, name, type and default below were read from a live 5.2.0 node (runtime probe 1); indices are declaration order, stable within 5.x but NOT across major versions. Prefer names; use indices only as a fallback.

| # | Name | Type | Default | Range | Panel / notes |
|---|---|---|---|---|---|
| 0 | Base Color | Color | 0.8,0.8,0.8 | — | |
| 1 | Metallic | Float | 0.0 | 0–1 | |
| 2 | Roughness | Float | 0.5 | 0–1 | |
| 3 | IOR | Float | 1.5 | 1–1000 | |
| 4 | Alpha | Float | 1.0 | 0–1 | |
| 5 | Thin Wall | Bool | False | — | switches to thin-walled mode (manual); the release that introduced it is not sourced here |
| 6 | Normal | Vector | hidden | — | |
| 7 | Weight | Float | — | — | internal; `is_unavailable == True` in a normal tree |
| 8 | Diffuse Roughness | Float | 0.0 | 0–1 | Diffuse panel, **Cycles only** (Oren-Nayar) |
| 9 | Subsurface Weight | Float | 0.0 | 0–1 | Subsurface |
| 10 | Subsurface Radius | Vector | (1, 0.2, 0.1) | 0–100 | Subsurface |
| 11 | Subsurface Scale | Float | 0.005 m | 0–10 | Subsurface |
| 12 | Subsurface IOR | Float | 1.4 | 1.01–3.8 | Cycles only; **unavailable (`is_unavailable`, KeyError by name) unless `subsurface_method == 'RANDOM_WALK_SKIN'`** |
| 13 | Subsurface Anisotropy | Float | 0.0 | −1–1 | Cycles only (neg. allowed since 5.2) |
| 14 | Specular IOR Level | Float | 0.5 | 0–1 | was `Specular` pre-4.0 |
| 15 | Specular Tint | Color | white | — | was a **Float** pre-4.0 |
| 16 | Anisotropic | Float | 0.0 | 0–1 | Cycles only |
| 17 | Anisotropic Rotation | Float | 0.0 | 0–1 | Cycles only |
| 18 | Tangent | Vector | hidden | — | |
| 19 | Transmission Weight | Float | 0.0 | 0–1 | was `Transmission` pre-4.0 |
| 20 | Coat Weight | Float | 0.0 | 0–1 | was `Clearcoat` (3.x) → `Coat` (4.0 label) |
| 21 | Coat Roughness | Float | 0.03 | 0–1 | |
| 22 | Coat IOR | Float | 1.5 | 1–4 | new in 4.0 |
| 23 | Coat Tint | Color | white | — | new in 4.0 |
| 24 | Coat Normal | Vector | hidden | — | |
| 25 | Sheen Weight | Float | 0.0 | 0–1 | was `Sheen` pre-4.0 |
| 26 | Sheen Roughness | Float | 0.5 | 0–1 | new in 4.0 (reworked sheen model) |
| 27 | Sheen Tint | Color | white | — | was a **Float** pre-4.0 |
| 28 | Emission Color | Color | white | — | was `Emission` pre-4.0 |
| 29 | Emission Strength | Float | 0.0 | 0–1e6 | default was 1.0 in 3.x |
| 30 | Thin Film Thickness | Float | 0.0 nm | 0–1e5 | Cycles only (4.2+) |
| 31 | Thin Film IOR | Float | 1.33 | 1–1000 | Cycles only |
<!-- ease:source S8 anchor="'Subsurface BSDF and Subsurface component in Principled BSDF now supports negative anisotropy ... from -1 to 1'" -->

The **Range** column is the UI/declaration range quoted from source and is not re-verified: the Python API does not clamp socket values (5.2.0 accepted IOR 5000, Roughness -1, Metallic 1.5). Dispersion inputs appear in the repository-main manual but are absent from this 5.2.0 node. Non-socket properties on the node:
`node.distribution` ∈ `{'GGX','MULTI_GGX'}` (default `MULTI_GGX`);
`node.subsurface_method` ∈ `{'BURLEY','RANDOM_WALK','RANDOM_WALK_SKIN','RANDOM_WALK_LEGACY'}` <!-- ease:source S1 anchor="principled_sss_method = BURLEY, RANDOM_WALK, RANDOM_WALK_SKIN, RANDOM_WALK_LEGACY; default RANDOM_WALK; distribution GGX/MULTI_GGX default MULTI_GGX" -->
(default `RANDOM_WALK`). Files older than 5.2 are auto-converted to `RANDOM_WALK_LEGACY` <!-- ease:source S8 anchor="'older files are automatically converted to use Random Walk (Legacy) mode'" -->
because 5.2 changed the radius/anisotropy→albedo mapping.

#### 4.3 Removed / renamed — do not use

```python
# GONE in 4.0+: "Subsurface Color"  -> use Base Color
# GONE in 4.0+: "Clearcoat", "Clearcoat Roughness" -> "Coat Weight", "Coat Roughness"
# GONE in 4.0+: "Transmission Roughness" (use Roughness)
# GONE in 4.0+: "Emission" as a Color socket name -> "Emission Color"
# 5.0: shader node "Fac" sockets renamed to "Factor"
#      (Noise/Voronoi/Attribute/Mix RGB ...). Resolve with find_socket(n, "Factor", "Fac").
```
<!-- ease:source S9 anchor="4.0 Principled revamp: subsurface uses base color; coat/sheen/specular reworked" -->
<!-- ease:source S5 anchor="node.outputs['Factor'].identifier == 'Fac'; outputs['Fac'] resolves to the Factor socket" -->

#### 4.4 Create a material and set physical values (background-safe)

```python
import bpy

def new_pbr_material(name, base_color=(0.8, 0.8, 0.8, 1.0),
                     roughness=0.4, metallic=0.0, ior=1.5):
    mat = bpy.data.materials.new(name)        # 5.x: node tree already exists here
    mat.use_nodes = True                       # 4.x: needed | 5.x: deprecated no-op
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    out  = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (-300, 0)
    if out is None:
        out = nt.nodes.new("ShaderNodeOutputMaterial");  out.location = (100, 0)
    if not out.inputs["Surface"].is_linked:
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    set_input(bsdf, base_color, "Base Color")
    set_input(bsdf, max(roughness, 0.03), "Roughness")
    set_input(bsdf, 1.0 if metallic >= 0.5 else 0.0, "Metallic")
    set_input(bsdf, ior, "IOR")
    return mat
```
<!-- ease:source S7 anchor="see R2" -->

#### 4.5 Node placement, links, and a reusable node group

```python
def layout_chain(nodes, y=0, x0=-1400, dx=250):
    """Left-to-right placement so a node-editor screenshot is readable."""
    for i, n in enumerate(nodes):
        n.location = (x0 + i * dx, y)

# Node group: build once, instance many times.
grp = bpy.data.node_groups.new("Weathering", "ShaderNodeTree")
grp.interface.new_socket(name="Amount", in_out='INPUT',  socket_type='NodeSocketFloat')
grp.interface.new_socket(name="Color",  in_out='OUTPUT', socket_type='NodeSocketColor')
gin  = grp.nodes.new("NodeGroupInput");  gin.location  = (-300, 0)
gout = grp.nodes.new("NodeGroupOutput"); gout.location = (300, 0)
noise = grp.nodes.new("ShaderNodeTexNoise"); noise.location = (0, 0)
grp.links.new(gin.outputs["Amount"], noise.inputs["Scale"])
# 5.x: "Factor" | 4.x: "Fac"
grp.links.new(find_socket(noise, "Factor", "Fac", inputs=False), gout.inputs["Color"])

inst = mat.node_tree.nodes.new("ShaderNodeGroup")
inst.node_tree = grp
inst.location = (-700, 300)
```
<!-- ease:source S2 anchor="group sockets created and linked on 5.2.0 (find_socket(noise,'Factor','Fac'))" -->

#### 4.6 Material slots and per-face assignment (data API, no ops)

```python
obj = bpy.data.objects["Cube"]
me  = obj.data

me.materials.clear()                 # removes all slots on the MESH
me.materials.append(mat_body)        # slot 0
me.materials.append(mat_trim)        # slot 1

# Per-face assignment, vectorized (fast, background-safe):
import numpy as np
n = len(me.polygons)
idx = np.zeros(n, dtype=np.int32)
idx[::2] = 1                          # every other face uses slot 1
me.polygons.foreach_set("material_index", idx)
me.update()

assert idx.max() < len(me.materials), "material_index out of range"

# Object-level override (per-instance colour without duplicating the mesh):
obj.material_slots[0].link = 'OBJECT'   # 'DATA' (default) | 'OBJECT'
obj.material_slots[0].material = mat_variant
```
<!-- ease:source S2 anchor="foreach_set produced [1,0,1,0,1,0] on a cube" -->

#### 4.7 Engine-relevant material settings

```python
mat.surface_render_method = 'DITHERED'   # EEVEE 4.2+: 'DITHERED' | 'BLENDED'
                                         # 'BLENDED' breaks render passes + raytracing
mat.blend_method = 'OPAQUE'              # DEPRECATED alias, kept for 4.x scripts
mat.use_backface_culling = False
mat.displacement_method = 'BUMP'         # 'BUMP' | 'DISPLACEMENT' | 'BOTH'
mat.use_transparent_shadow = True
mat.thickness_mode = 'SLAB'              # EEVEE thin-wall/refraction
```
<!-- ease:source S6 anchor="manual Thin Wall note: in EEVEE set Thickness 0 and Thickness Mode Slab" -->
<!-- ease:source S2 anchor="surface_render_method DITHERED/BLENDED; displacement_method BUMP/DISPLACEMENT/BOTH; thickness_mode SPHERE/SLAB; blend_method description: 'Deprecated: use surface_render_method'" -->

#### 4.8 Physically plausible reference values

```python
IOR = {  # dielectrics
    "air": 1.000, "ice": 1.31, "water": 1.333, "alcohol": 1.36,
    "glass": 1.50, "quartz": 1.54, "plastic_pvc": 1.52, "polycarbonate": 1.585,
    "amber": 1.55, "ruby": 1.76, "sapphire": 1.77, "diamond": 2.417,
    "skin": 1.40, "eye_cornea": 1.376, "milk": 1.35,
}
# Metals: set Metallic=1 and put the measured reflectance in Base Color (linear sRGB).
METAL_BASE_COLOR = {
    "aluminium": (0.913, 0.922, 0.924), "silver": (0.972, 0.960, 0.915),
    "gold":      (1.000, 0.766, 0.336), "copper": (0.955, 0.638, 0.538),
    "iron":      (0.560, 0.570, 0.580), "chromium": (0.550, 0.556, 0.554),
    "titanium":  (0.542, 0.497, 0.449), "nickel": (0.660, 0.609, 0.526),
}
# Dielectric diffuse albedo bounds (linear): charcoal ~0.02-0.05, asphalt ~0.05-0.08,
# skin ~0.25-0.45, dry sand ~0.35, fresh snow ~0.80-0.90. Never 0.0 or 1.0.
```
<!-- ease:source UNVERIFIED reason="IOR and metal reflectance tables are published-measurement style values; no source fetched (see Sources note)" -->

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `KeyError: bpy_prop_collection[key]: key "Specular" not found` | 4.0 renamed to `Specular IOR Level` | Use `find_socket(bsdf, "Specular IOR Level", "Specular")` |
| `KeyError: ... key "Fac" not found` on a Noise/Voronoi/Attribute node | 5.0 renamed `Fac` → `Factor` | `find_socket(n, "Factor", "Fac", inputs=False)` |
| `RuntimeError: Node type X undefined` from `nodes.new()` | passed the UI label instead of `bl_idname` | Use `"ShaderNodeBsdfPrincipled"`, `"ShaderNodeTexImage"`, … |
| Render is fully black, no traceback | `nodes.clear()` removed the Material Output, or Surface link missing | Recreate `ShaderNodeOutputMaterial` and link `BSDF → Surface` |
| Material looks flat grey / plasticky in render | `Metallic` left at an intermediate value, or `Specular IOR Level` bumped instead of `IOR` | Snap Metallic to 0/1; set `IOR` |
| Single blown-out white pixels (fireflies) | `Roughness == 0.0` on a small bright specular | Floor roughness at 0.03; enable clamping (`scene.cycles.sample_clamp_indirect`) |
| Interior scene never converges / everything glows | Dielectric Base Color at or near 1.0 → energy never absorbed | Cap albedo at ~0.85 linear |
| Assigning a material appears to do nothing | Wrote to `obj.material_slots[i].material` while `slot.link == 'DATA'` | Append to `obj.data.materials` or set `slot.link='OBJECT'` first |
| Faces show the wrong material with no error | `material_index` >= number of slots | Assert `max(index) < len(me.materials)` |
| EEVEE render differs wildly from Cycles for the same material | Cycles-only inputs used (Anisotropic, Thin Film, Subsurface IOR/Anisotropy, Diffuse Roughness) | Restrict to shared inputs, or accept and document the difference |
| Node-editor screenshot shows one node stack | All nodes at `location = (0,0)` | Set `node.location` explicitly (`layout_chain`) |
| Subsurface look changed after loading an old file in 5.2 | 5.2 changed Random Walk radius/anisotropy mapping; old files forced to `RANDOM_WALK_LEGACY` | Re-tune `Subsurface Radius`/`Scale` and set `subsurface_method='RANDOM_WALK'` |
<!-- ease:source S2 anchor="scene.cycles.sample_clamp_indirect exists (default 10.0)" -->
<!-- ease:source S8 anchor="Random Walk radius/anisotropy mapping adjusted; legacy mode auto-applied" -->

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Engine assumed | EEVEE | Cycles | EEVEE | Cycles | Workbench |
| Base Color source | baked texture, sRGB | texture + SSS tint | flat linear color | measured texture / swatch | flat 0.8 grey |
| Roughness floor | 0.10 | 0.15 (skin 0.35–0.5) | 0.20 | 0.03 | 0.5 |
| Metallic | 0 or 1, from map | 0 | 0 or 1 | 0 or 1 | 0 |
| IOR | 1.45 (leave default) | 1.40 (skin) | 1.50 | measured (glass 1.50, plastic 1.52) | 1.50 |
| Specular IOR Level | 0.5 (never touch) | 0.5 | 0.5 | 0.5 | 0.5 |
| Subsurface Weight | 0 | 1.0 (skin) | 0 | 0 (1.0 for wax/jade) | 0 |
| Subsurface Scale | — | 0.01–0.02 m | — | 0.005 | — |
| subsurface_method | — | `RANDOM_WALK_SKIN` | — | `RANDOM_WALK` | — |
| Coat Weight | 0 | 0 | 0 | 1.0 for lacquer/car paint | 0 |
| Coat Roughness | — | — | — | 0.03 | — |
| Sheen Weight | 0 | 1.0 for cloth | 0 | 0 | 0 |
| Transmission Weight | 0 (fake with alpha) | 0 | 0 | 1.0 for glass | 0 |
| Emission Strength | 0–5 (UI/screens) | 0 | 1–20 (glow) | 0 | 0 |
| distribution | `MULTI_GGX` | `MULTI_GGX` | `MULTI_GGX` | `MULTI_GGX` | `GGX` |
| surface_render_method | `DITHERED` | n/a | `DITHERED` (`BLENDED` only if colored glass and no passes) | n/a | n/a |
| Max material slots / object | 1–4 (atlas) | 4–8 | 1–4 | unlimited | 1 |
| displacement_method | `BUMP` | `BUMP` | `BUMP` | `BOTH` (with adaptive subdiv) | n/a |
<!-- ease:source UNVERIFIED reason="use-case defaults are authoring guidance, not measured" -->

### 7. Verification checklist

- [ ] `assert mat.node_tree is not None` — the material has a graph at all.
- [ ] `out = next(n for n in mat.node_tree.nodes if n.bl_idname=="ShaderNodeOutputMaterial"); assert out.inputs["Surface"].is_linked` — proves the surface will not render black.
- [ ] `assert find_socket(bsdf, "Base Color") is not None` — socket resolution works on this build.
- [ ] `assert bsdf.inputs[1].name == "Metallic"` — index map matches the 5.x layout you assumed.
- [ ] `m = find_socket(bsdf,"Metallic").default_value; assert m in (0.0, 1.0)` — metallic is binary.
- [ ] `assert find_socket(bsdf,"Roughness").default_value >= 0.03` — no perfect-mirror fireflies.
- [ ] `bc = find_socket(bsdf,"Base Color").default_value[:3]; assert 0.02 <= max(bc) <= 0.95` — plausible dielectric albedo.
- [ ] `import numpy as np; a=np.empty(len(me.polygons),dtype=np.int32); me.polygons.foreach_get("material_index",a); assert a.max() < len(me.materials)` — no out-of-range face assignment.
- [ ] `assert len({n.location[:] for n in mat.node_tree.nodes}) == len(mat.node_tree.nodes)` — no two nodes stacked at the same point.
- [ ] Viewport screenshot in `MATERIAL` or `RENDERED` shading: the object is not uniformly magenta (missing texture) and not uniformly black (broken output link).

### 8. Sources

- [Principled BSDF — Blender Manual (latest)](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)
- [Blender 4.0 Release Notes: Python API — Principled BSDF socket renames](https://developer.blender.org/docs/release_notes/4.0/python_api/)
- [Blender 5.0 Release Notes: Python API — `use_nodes` deprecation, node changes](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.0 Release Notes: Rendering — shader node changes](https://developer.blender.org/docs/release_notes/5.0/rendering/)
- [Blender 5.2 Release Notes: Cycles — subsurface Random Walk remapping, `RANDOM_WALK_LEGACY`](https://developer.blender.org/docs/release_notes/5.2/cycles/)
- Socket inventory, defaults and ranges cross-checked against Blender 5.2 source
  `source/blender/nodes/shader/nodes/node_shader_bsdf_principled.cc` (tag `v5.2.0`)
  and `source/blender/makesrna/intern/rna_nodetree.cc`.
- Metal base-color and IOR reference values are standard published measurements, not
  Blender documentation. `[UNVERIFIED]` against blender.org — treat as guidance, and
  prefer measured textures when accuracy matters.

## Failure Modes (Mandatory)

- **`KeyError: bpy_prop_collection[key]: key "Specular" not found`** — cause: socket renamed `Specular IOR Level` in 4.0 (also `Subsurface Color` and `Clearcoat` are gone on 5.2.0) — fix: `find_socket(bsdf, "Specular IOR Level", "Specular")`
- **`KeyError ... key "Subsurface IOR"` although the socket is listed at index 12** — cause: the socket is unavailable under `subsurface_method` RANDOM_WALK/BURLEY and unavailable sockets are not reachable by name — fix: set `subsurface_method = 'RANDOM_WALK_SKIN'` first, or ignore the socket
- **`RuntimeError: Error: Node type Principled BSDF undefined`** — cause: UI label passed to `nodes.new` — fix: the bl_idname `ShaderNodeBsdfPrincipled`
- **Render fully black, no traceback** — cause: `nodes.clear()` removed the Material Output or the Surface link is missing — fix: recreate `ShaderNodeOutputMaterial` and link `BSDF -> Surface`
- **Faces show the wrong material, no error** — cause: `material_index` >= slot count (the API stores the value unclamped) — fix: assert `max(index) < len(me.materials)`
- **EEVEE and Cycles disagree for one material** — cause: Cycles-only inputs (Diffuse Roughness, Subsurface Random Walk/IOR/Anisotropy, Anisotropic, Thin Film) — fix: restrict to shared inputs or document the gap

## Sources

- [S1] Runtime probe 1 on Blender 5.2.0 LTS: all 32 Principled BSDF inputs (index, name, type, default, availability), enums, node I/O — knowledge/_evidence/kb-261013/w1-probe-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3ad8e713a6ecef0926ba15bdbcf92c69a4926d64eed1a7d9c25ba88310591388
- [S2] Runtime probe 11 on 5.2.0: find_socket/set_input, new_pbr_material, node group, slots and material settings executed as written — knowledge/_evidence/kb-261013/w1-probe11-5.2-runtime-output.txt — captured 2026-10-13 — sha256 e81fba2fc15923204cb5a00dd5216008713218e437832281e9b45e33958017a6
- [S3] Runtime probe 2 on 5.2.0: Material/World/Scene use_nodes, property presence — knowledge/_evidence/kb-261013/w1-probe2-5.2-runtime-output.txt — captured 2026-10-13 — sha256 fc89a17430ce6e7ba578923a672478bfb042b5adb5eb78b3692126a760e3179c
- [S4] Runtime probe 3 on 5.2.0: socket value assignment is not clamped; use_nodes no-op — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995
- [S5] Runtime probe 6 on 5.2.0: Fac/Factor lookup by name and identifier; 'Node type ... undefined' message — knowledge/_evidence/kb-261013/w1-probe6-5.2-runtime-output.txt — captured 2026-10-13 — sha256 8d880cd427af7d24ff5a8d483602f721a6b20b830e0caa9c33b6c1b780c4f70e
- [S6] Principled BSDF manual source (render/shader_nodes/shader/principled.rst, repository main branch) — https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/render/shader_nodes/shader/principled.rst (frozen copy: knowledge/_evidence/kb-261013/w1-gh-blender-manual-principled.rst) — captured 2026-10-13 — sha256 48ab4a2b1d676bd7bf00795e1882e7e41a4ddda98d6db778bee88b9968591c4a
- [S7] Blender 5.0 Python API release notes (use_nodes deprecation, interface lookup) — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-0.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S8] Blender 5.2 LTS Cycles release notes (SSS remap, negative anisotropy, texture cache) — https://developer.blender.org/docs/release_notes/5.2/cycles/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-cycles.html) — captured 2026-10-13 — sha256 d23b908ff2615545b8fe1222818234efe6b3647e59fbe6aa3a6626f17cdbbf5c
- [S9] Blender 4.0 Shading release notes (Principled revamp, microfiber sheen) — https://developer.blender.org/docs/release_notes/4.0/shading/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-0-shading.html) — captured 2026-10-13 — sha256 501b7b4d502675cde6d006e909cb051f14a619ebdd7acc098c2c68f2ef575f6a
- [S10] Runtime probe 12 on 5.2.0: nodes.new default location, image colour spaces — knowledge/_evidence/kb-261013/w1-probe12-5.2-runtime-output.txt — captured 2026-10-13 — sha256 b5abf65158c8efb4713da32fbf614dfdb0a48c0975089ed1063ad5f071b2dd5a
- [S11] OpenPBR Surface specification (Academy Software Foundation) — https://academysoftwarefoundation.github.io/OpenPBR/ (frozen copy: knowledge/_evidence/kb-261013/w1-openpbr-spec.html) — captured 2026-10-13 — sha256 3bec2edd0abd1f6a626777783f945825d771caf680c2e1e19abe7c3329e1595a
- [S12] Runtime probe 5 on 5.2.0 (file_path_foreach callback arity) — knowledge/_evidence/kb-261013/w1-probe5-5.2-runtime-output.txt — captured 2026-10-13 — sha256 549b79ba7a1419e1bbeaddd0c581b589ee4855e4e9dbc30c0e524749efc50e22

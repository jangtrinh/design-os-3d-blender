---
name: master-artisan-pbr-and-grooming
category: 20-shading
domain: materials_pbr
loads_with: [materials-pbr, lighting, video-animation-cinematics]
tags: [openpbr, principled-bsdf-v2, random-walk-sss, hair-curves, geometry-nodes-hair, thin-film, sheen-microfiber, cycles-opt, production-grade]
id: master-artisan-pbr-and-grooming
title: "Master Artisan PBR Shading & Hair Curves Grooming: OpenPBR, Random Walk SSS & Geometry Nodes Groom"
description: Production-level skin/hair/sheen/thin-film shading and Hair Curves grooming on Blender 5.x, with Cycles hair and SSS settings, checked against a live 5.2.0 build.
when: [skin-sss-shader, hair-bsdf-melanin, sheen-thinfilm, hair-curves-groom-nodes, cycles-hair-settings]
trust_tier: draft
sources_checked: 2026-10-13
---
# Master Artisan PBR Shading & Hair Curves Grooming: OpenPBR, Random Walk SSS & Geometry Nodes Groom

## Purpose

Describe how to shade human skin, hair, sheen and thin-film surfaces and structure a Geometry Nodes hair groom on Blender 5.x, flagging every optical/performance figure that is only guidance.

## When to Use / When NOT

- ALLOWED: film-grade skin, hair, fuzz or iridescent shading beyond the basic Principled values, and bundled-node-asset hair grooms
- ALLOWED: tuning Cycles hair and SSS settings for a hero shot
- NOT ALLOWED: basic Principled sockets, ranges and node wiring — use `materials-pbr` instead
- NOT ALLOWED: creating Hair Curves data and ARKit shape keys via bpy — use `character-creature-modeling` instead
- NOT ALLOWED: texture colour spaces and baking — use `texturing-baking` instead
- NOT ALLOWED: Cycles persistent data and cinematic render setup — use `video-animation-cinematics` instead

## Core Knowledge Content


> Production standard for physically-based shading and digital hair grooming in Blender 4.x/5.x: OpenPBR Principled BSDF v2 architecture, Random Walk v2 Subsurface Scattering, thin-film iridescence, microfiber sheen, Chiang/Marschner hair physics, and Geometry Nodes procedural grooming graphs.

---

### 1. Physical Principles & Optical Governing Equations

#### A. OpenPBR Surface & Principled BSDF v2 Architecture
Blender 4.0+ completely overhauled the Principled BSDF to align with the Academy Software Foundation (ASWF) **OpenPBR Surface** specification: <!-- ease:source S5 anchor="manual: 'It is based on the OpenPBR Surface shading model'; spec v1.1.1 at S7; 4.0 notes: Principled BSDF 'revamped'" -->

```math
F(0^\circ) = \left( \frac{\eta - 1}{\eta + 1} \right)^2, \quad F(\theta) = F_0 + (F_{90} - F_0)(1 - \cos\theta)^5
```
<!-- ease:source UNVERIFIED reason="Fresnel/Schlick relations are standard optics, not taken from a fetched source; F0(1.5)=0.04 checks arithmetically" -->

1. **Dielectric vs Conductor Separation:**
   - **Dielectrics (`Metallic = 0.0`):** Normal incidence reflectance $F_0$ determined strictly by Index of Refraction (IOR). At $\eta = 1.50$ (glass, common plastics; skin is nearer 1.40, see B), $F_0 = 0.04$ ($4\%$ reflectance). Diffuse and specular reflections conserve energy:
     
     ```math
     E_{total} = (1 - F(\theta)) \cdot E_{diffuse} + F(\theta) \cdot E_{specular} \le 1.0
     ```

   - **Conductors (`Metallic = 1.0`):** No subsurface transmission ($E_{diffuse} = 0$). Conductor reflectance is driven by complex IOR $\tilde{n} = n + i \kappa$ where extinction coefficient $\kappa$ dominates, yielding high $F_0 \approx 0.70\text{--}0.98$ tinted by base color.
2. **Multi-Scatter GGX:** <!-- ease:source S5 anchor="manual: Multiscatter GGX 'takes multiple scattering events between microfacets into account ... more energy conserving results'; distribution enum GGX/MULTI_GGX, default MULTI_GGX (probe 1)" -->
   - Single-scatter microfacet models artificially darken at high roughness due to missing inter-microfacet bounces. Blender's Multi-Scatter GGX preserves albedo energy up to roughness $1.0$, preventing black velvet artifacts on matte rough surfaces.

---

#### B. Subsurface Scattering (SSS): Random Walk v2
For organic tissues (human skin, ears, lips, jade, candle wax), incoming light refracts into the medium, scatters multiple times, and exits at an adjacent surface point:

```math
R(r) = \frac{\alpha'}{4 \pi \ell_{mfp}} \cdot \frac{e^{-r / \ell_{mfp}}}{r}
```

- *Note:* the closed-form `R(r)` above is an illustrative falloff; Blender's Random Walk methods do not evaluate it, they path-trace the medium.
- **Random Walk (Skin):** Simulates true volumetric scattering paths inside the mesh while accounting for surface boundary curvature. Unlike Burley dipole approximations, Random Walk preserves crisp geometric details and avoids light bleeding through thin nostrils and eyelids. <!-- ease:source S5 anchor="manual: Random Walk 'accurate results for thin and curved objects'; Skin: 'radius is automatically adjusted based on the color texture ... custom IOR'" -->
- **Mean Free Path ($\ell_{mfp}$) Subsurface Radius:** Defines the average scattering distance per color channel before complete absorption. For Caucasian human skin (in millimeters): <!-- ease:source UNVERIFIED reason="'Caucasian skin, millimetres' is not sourced; the (1.0, 0.2, 0.1) values are Blender's own socket default (probe 1)" -->
  
  ```python
  subsurface_radius = (1.0, 0.2, 0.1)  # Red penetrates 10x deeper than blue
  ```
  
- **IOR Boundary Matching:** the `Subsurface IOR` input (default 1.4; **Cycles only**, and available only with `subsurface_method = 'RANDOM_WALK_SKIN'`) sets the IOR for rays entering the subsurface component and may differ from the global `IOR` (manual); it is not tied to the surface IOR. <!-- ease:source S5 anchor="manual: Subsurface IOR is 'used for rays that enter the subsurface component ... a different value than the global IOR'; Cycles only" -->

---

#### C. Thin-Film Interference (Iridescence) & Sheen Fuzz
1. **Thin-Film Interference (Coating Layer):** <!-- ease:source S5 anchor="manual: Thin Film 'simulates the effect of interference in a thin film', Cycles only; sockets Thin Film Thickness (nm) and Thin Film IOR exist (probe 1); the d = 200-800 nm range is UNVERIFIED" -->
   - Wavefronts reflecting from the top of an ultra-thin dielectric coating ($d \approx 200\text{--}800\,\text{nm}$) interfere with wavefronts reflecting from the substrate:
     
     ```math
     2 \eta_{film} d \cos\theta_t = \left(m + \frac{1}{2}\right) \lambda
     ```
     
   - Phase shifts yield constructive and destructive wavelength reinforcement, producing iridescent reflections on tempered steel, oil slicks, insect wings, and optical AR lenses.
2. **Charlie Microfiber Sheen:** <!-- ease:source S6 anchor="4.0 notes: Sheen BSDF 'Microfiber' model = 'Practical Multiple-Scattering Sheen Using Linearly Transformed Cosines' (Zeltner, Burley, Chiang)" -->
   - Traditional microfacets fail to model grazing-angle light scattering across fibrous cloth (velvet, satin, peach fuzz). Blender's Principled sheen (`Sheen Weight`, `Sheen Roughness`, `Sheen Tint`) and the Sheen BSDF's default `Microfiber` model use the Linearly-Transformed-Cosines multiple-scattering sheen of Zeltner, Burley & Chiang (4.0 release notes), not the Charlie distribution; the 4.0 notes state Sheen BSDF was Cycles-only at that release.

---

### 2. Modern Hair Curves & Geometry Nodes Grooming Architecture

#### A. Curves Object Architecture (Blender 3.5+) <!-- ease:source UNVERIFIED reason="the 3.5 introduction of Curves objects is not in a fetched source; Curves data-block verified on 5.2.0 (probe 10)" -->
Legacy particle hair still exists on 5.2.0 (`ParticleSettings.type` offers `HAIR`, the `PARTICLE_SYSTEM` modifier can be created), but data-API grooming uses **Hair Curves** objects evaluated through Geometry Nodes (bundled `procedural_hair_node_assets.blend`):

```
[Hair Curves Object]
  ├── Attach Hair Curves to Surface / Set Attachment Surface (attachment to animated skin)
  ├── Generate Hair Curves
  ├── Interpolate Hair Curves (Guide-to-child density)
  ├── Clump Hair Curves (Secondary strand clustering)
  ├── Frizz / Curl Hair Curves (Procedural micro-noise)
  └── Trim Hair Curves (Length attenuation)
```
<!-- ease:source S1 anchor="node groups in procedural_hair_node_assets.blend: Generate/Interpolate/Clump/Frizz/Curl/Trim Hair Curves, Attach Hair Curves to Surface, Set Attachment Surface" -->

1. **Surface Attachment & Deformation:** <!-- ease:source UNVERIFIED reason="that roots interpolate from surface_uv_coordinate is not confirmed from a fetched source (see character-creature-modeling)" -->
   - Curves store `surface_uv_coordinate` attributes. During skeletal armature deformation or blendshape morphing, curve roots interpolate their 3D positions directly from surface barycentric coordinates without sliding across the skin.
2. **Guide Curve Clumping:**
   - Primary guide curves (50–500 manual groom strands) guide thousands of interpolated children.
   - Clumping profile $C(t)$ along curve parameter $t \in [0, 1]$ (where $t=0$ is root and $t=1$ is tip):
     
     ```math
     C(t) = t^k \cdot C_{tip} + (1 - t)^k \cdot C_{root}, \quad k \approx 2.0
     ```
<!-- ease:source UNVERIFIED reason="the clumping profile and k≈2.0 are illustrative, not Blender's Clump Hair Curves definition" -->
     
     This maintains a clean parted root while drawing strand tips tightly together into realistic locks.

---

#### B. Chiang & Marschner Hair Physics (Principled Hair BSDF)
Hair strands act as translucent dielectric cylinders with internal reflection modes:

```
Incident Ray ─────┬──> [R]   Primary specular reflection (Cuticle surface, uncolored)
                  ├──> [TT]  Transmitted through strand (Core absorption, tinted)
                  └──> [TRT] Internal bounce reflection (Backscatter highlight)
```

1. **Cuticle Tilt Angle:**
   - Shingles on human hair cuticles tilt by a small angle $\alpha$ toward the root; Blender's Principled Hair exposes it as `Offset` (default 0.0349 rad = $2^\circ$ on 5.2.0). This shifts the primary $[R]$ reflection highlight toward the root, while the internal $[TRT]$ highlight shifts toward the tip. <!-- ease:source S3 anchor="Principled Hair 'Offset' default 0.0349 rad = 2.0 degrees; Marschner lobe shifts are the textbook model (UNVERIFIED here)" -->
2. **Melanin Concentration:**
   - Pure physical coloration parameterized by two biological pigments:
     - Blender exposes `Melanin` (total pigment, default 0.8) and `Melanin Redness` (pheomelanin share, default 1.0), both unavailable until `parametrization = 'MELANIN'`; it does not expose separate eumelanin/pheomelanin concentrations. <!-- ease:source S3 anchor="Principled Hair has 'Melanin' and 'Melanin Redness' inputs, unavailable until parametrization == 'MELANIN' (probe 1/2/10)" -->
     - Total absorption coefficient $\sigma_a = c_{eu} \sigma_{eu} + c_{ph} \sigma_{ph}$.

---

### 3. Production Shader & Grooming Pipeline Script

```python
"""
scripts/artisan_pbr_grooming_builder.py
Headless builder for OpenPBR skin/metal materials and procedural Hair Curves setup.
"""
import bpy
import math

def create_artisan_skin_material(name: str = "MAT_Artisan_Skin") -> bpy.types.Material:
    """Builds an OpenPBR compliant multi-layer skin shader with Random Walk v2."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Material Output & Principled BSDF v2
    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (400, 0)
    
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    
    # Physically-based Skin Parameters
    bsdf.inputs["Base Color"].default_value = (0.85, 0.65, 0.55, 1.0) # Epidermis base
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["IOR"].default_value = 1.42  # Human skin index of refraction
    
    # Subsurface Scattering: Random Walk (Skin)
    bsdf.subsurface_method = "RANDOM_WALK_SKIN"
    bsdf.inputs["Subsurface Weight"].default_value = 1.0
    # Radius is multiplied by Subsurface Scale: with scale 0.005 m the red mean free path is 5 mm, green 1.25 mm, blue 0.5 mm
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.10)
    bsdf.inputs["Subsurface Scale"].default_value = 0.005 # 5mm global scale
    bsdf.inputs["Subsurface IOR"].default_value = 1.40
    
    # Microfiber Peach Fuzz Sheen
    bsdf.inputs["Sheen Weight"].default_value = 0.60
    bsdf.inputs["Sheen Roughness"].default_value = 0.40
    bsdf.inputs["Sheen Tint"].default_value = (1.0, 0.9, 0.8, 1.0)
    
    return mat

def create_principled_hair_material(name: str = "MAT_Hair_Melanin") -> bpy.types.Material:
    """Creates a physically accurate melanin-driven hair shader."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (300, 0)
    
    hair_bsdf = nodes.new(type="ShaderNodeBsdfHairPrincipled")
    hair_bsdf.location = (0, 0)
    links.new(hair_bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    
    # Chiang Model Melanin Settings (Natural Dark Auburn Hair)
    hair_bsdf.parametrization = "MELANIN"
    hair_bsdf.inputs["Melanin"].default_value = 0.85
    hair_bsdf.inputs["Melanin Redness"].default_value = 0.35
    hair_bsdf.inputs["Roughness"].default_value = 0.25
    hair_bsdf.inputs["Radial Roughness"].default_value = 0.40
    hair_bsdf.inputs["Coat"].default_value = 0.15 # Natural hair oil coat
    
    return mat

if __name__ == "__main__":
    skin_mat = create_artisan_skin_material()
    hair_mat = create_principled_hair_material()
    print(f"[OK] Built OpenPBR materials: {skin_mat.name}, {hair_mat.name}")
```
<!-- ease:source S9 anchor="parametrization enum ABSORPTION/MELANIN/COLOR (default COLOR); 'Melanin' raises KeyError under COLOR; model CHIANG/HUANG" -->
<!-- ease:source S2 anchor="script executed unchanged on 5.2.0: RANDOM_WALK_SKIN, radius (1.0,0.25,0.1), scale 0.005, Subsurface IOR 1.4, IOR 1.42" -->

---

### 4. Cycles Engine Hair & SSS Optimization Matrix

| Feature / Setting | Quality Mode (Film/Cinematic) | Production Mode (Animation) | Real-Time / Preview | Performance Impact |
|---|---|---|---|---|
| **Cycles Curve Shape** | **3D Curves** (`THICK`) | **Rounded Ribbons** (`RIBBONS`, the default) | Ribbons | Cylinders consume $3\times$ BVH memory; use Ribbons for distant shots. |
| **Subsurface Samples** | 4–8 per path | 1–2 per path | 1 per path | Volumetric random walk converges quickly; >2 samples yields diminishing returns. |
| **Max Transparent Bounces** | 16–24 | **8–12** | 4–6 | Dense grooms with high transparency cause exponential path tracing stalls. |
| **Fast GI Approximation** | Off (Full global illumination) | **AO Bounce Factor: 0.5** | Fast GI 2-bounce | Reduces interior hair scattering compute time by $35\text{--}50\%$. |
| **Embree Hair BVH** | Enabled with spatial splits | Enabled (Fast build) | Disabled | Intel Embree reduces ray-curve intersection time by $40\%$. |
<!-- ease:source UNVERIFIED reason="only debug_use_hair_bvh / debug_use_spatial_splits exist on scene.cycles; the '40 %' figure is unsourced" -->
<!-- ease:source S10 anchor="scene.cycles.use_fast_gi (default False), fast_gi_method REPLACE/ADD, ao_bounces / ao_bounces_render (integers, default 1); the '35-50 %' saving is UNVERIFIED" -->
<!-- ease:source S3 anchor="scene.cycles.transparent_max_bounces exists, default 8; recommended ranges UNVERIFIED" -->
<!-- ease:source UNVERIFIED reason="no subsurface-samples property exists on scene.cycles in 5.2.0 (probe 1 property scan); all figures in this row are unsourced" -->
<!-- ease:source S3 anchor="scene.cycles_curves.shape enum: RIBBONS (Rounded Ribbons), THICK (3D Curves), THICK_LINEAR (Linear 3D Curves); default RIBBONS; BVH-memory ratio UNVERIFIED" -->

---

### 5. Master Artisan Shading Inspection Checklist

| Checkpoint | Target Standard | Verification Tool / Method | Critical Defect |
|---|---|---|---|
| **Energy Conservation** | $E_{diffuse} + E_{specular} \le 1.0$ | Render False Color view / Zebra lines | Over-bright specular fringes burning to pure white at grazing angles |
| **Subsurface Bleeding** | Natural light falloff through thin cartilage ($<4\,\text{mm}$) | Backlit spotlight test with high contrast | Solid wax-like appearance (too high radius) or black shadows (zero SSS) |
| **Specular Fresnel Curve** | Proper $F_0$ per material class ($0.04$ plastic/skin, $>0.8$ gold/copper) | Node Wrangler material preview ($F_0$ vs $F_{90}$) | Metals shaded with `Metallic = 0.0` or non-metals shaded with `Metallic = 1.0` |
| **Hair Cuticle Shift** | Specular highlight offset towards root by the Offset angle ($2^\circ$ default) | Rotating key light across groomed curve strand | Monolithic plastic highlight without separation between R and TRT lobes |
| **Geometry Nodes Curve Pinning** | Zero sliding of hair roots across deforming skin mesh | Scrubbing 120-frame skeletal playback | Hair roots drifting off scalp during facial blendshape contractions |
<!-- ease:source S3 anchor="Principled Hair Offset default 2 degrees" -->
<!-- ease:source UNVERIFIED reason="inspection thresholds are authoring guidance" -->

---

### See Also
- [materials-pbr](../20-shading/materials-pbr.md) — Fundamental PBR nodetree layouts and procedural texturing.
- [video-animation-cinematics](../30-lighting-render/video-animation-cinematics.md) — Cycles Persistent Data, camera rigs, and render optimization.
- [geometry-nodes-advanced-production](../50-procedural/geometry-nodes-advanced-production.md) — Field evaluations and procedural scatter generation.

## Failure Modes (Mandatory)

- **`KeyError: ... key "Melanin"` on a Principled Hair node** — cause: the socket is unavailable under the default `parametrization = 'COLOR'` — fix: set `parametrization = 'MELANIN'` before touching Melanin sockets (the module script does)
- **`KeyError ... "Subsurface IOR"` on a skin material** — cause: unavailable unless `subsurface_method == 'RANDOM_WALK_SKIN'` — fix: set the method first
- **Skin looks like wax or has black thin areas** — cause: radius × scale too large or SSS weight 0 — fix: radius (1.0, 0.2, 0.1) × scale 0.005 m is the Blender default start; test with a backlit spot (check list §5)
- **Hair looks like one plastic highlight** — cause: no separation of R and TRT lobes (Offset 0) — fix: keep the Principled Hair `Offset` near its 2 degree default and rotate a key light across the strand
- **Roots drift off the scalp during face animation** — cause: curves not bound to the deforming surface (attachment/surface UV workflow) — fix: use the Attach Hair Curves to Surface asset and scrub a 120-frame playback

## Sources

- [S1] Runtime probe 14 on Blender 5.2.0 LTS: this module's script run unchanged (skin and hair materials built) + node groups of the bundled procedural_hair_node_assets.blend — knowledge/_evidence/kb-261013/w1-probe14-5.2-runtime-output.txt — captured 2026-10-13 — sha256 75f804790e0214480f24ae65bafba195e94e5c2ba47165fcab0b1352c7aff639
- [S2] Script extracted verbatim from this module's section 3 and executed in probe 14 — knowledge/_evidence/kb-261013/w1-master-artisan-script-under-test.py — captured 2026-10-13 — sha256 9869e8c7384ed9c523f0ad4044dee90b646cdd4716ac1d50e3a2f4e6eae4d313
- [S3] Runtime probe 1 on 5.2.0: Principled and Principled Hair sockets/defaults/enums, cycles_curves.shape, cycles properties — knowledge/_evidence/kb-261013/w1-probe-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3ad8e713a6ecef0926ba15bdbcf92c69a4926d64eed1a7d9c25ba88310591388
- [S4] Runtime probe 2 on 5.2.0: Subsurface IOR availability by method, Melanin availability by parametrization — knowledge/_evidence/kb-261013/w1-probe2-5.2-runtime-output.txt — captured 2026-10-13 — sha256 fc89a17430ce6e7ba578923a672478bfb042b5adb5eb78b3692126a760e3179c
- [S5] Principled BSDF manual source (render/shader_nodes/shader/principled.rst, repository main branch) — https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/render/shader_nodes/shader/principled.rst (frozen copy: knowledge/_evidence/kb-261013/w1-gh-blender-manual-principled.rst) — captured 2026-10-13 — sha256 48ab4a2b1d676bd7bf00795e1882e7e41a4ddda98d6db778bee88b9968591c4a
- [S6] Blender 4.0 Shading release notes (Principled revamp, microfiber sheen via LTC) — https://developer.blender.org/docs/release_notes/4.0/shading/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-0-shading.html) — captured 2026-10-13 — sha256 501b7b4d502675cde6d006e909cb051f14a619ebdd7acc098c2c68f2ef575f6a
- [S7] OpenPBR Surface specification (Academy Software Foundation) — https://academysoftwarefoundation.github.io/OpenPBR/ (frozen copy: knowledge/_evidence/kb-261013/w1-openpbr-spec.html) — captured 2026-10-13 — sha256 3bec2edd0abd1f6a626777783f945825d771caf680c2e1e19abe7c3329e1595a
- [S8] Blender 5.2 LTS Cycles release notes (Random Walk remap, negative anisotropy) — https://developer.blender.org/docs/release_notes/5.2/cycles/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-cycles.html) — captured 2026-10-13 — sha256 d23b908ff2615545b8fe1222818234efe6b3647e59fbe6aa3a6626f17cdbbf5c
- [S9] Runtime probe 10 on 5.2.0: hair curves and particle-hair availability, hair/skin socket behaviour — knowledge/_evidence/kb-261013/w1-probe10-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3a5488d606231df3343020e528a985fbb3bf0e61aa571e978809882808ab5d36
- [S10] Runtime probe 3 on 5.2.0: cycles fast_gi_method and cycles_curves.shape descriptions — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995

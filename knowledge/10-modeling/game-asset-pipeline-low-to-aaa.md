---
name: game-asset-pipeline-low-to-aaa
category: 10-modeling
domain: modeling
loads_with: [modeling-topology, uv-unwrapping, texturing-baking]
tags: [blender, game-dev, low-poly, aaa-pipeline, baking, lod, nanite, collision]
id: game-asset-pipeline-low-to-aaa
title: "Game Asset Modeling Pipeline: Mobile, Low-Poly to AAA Real-Time Production"
description: Game-asset pipeline in Blender: poly and texel budgets, high-to-low normal baking with per-engine green-channel convention, LOD vs Nanite, Unreal collision naming, pre-export gate.
when: [game-asset, low-poly, normal-map-baking, lod-nanite, collision-hulls, texel-density]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Game Asset Modeling Pipeline: Mobile, Low-Poly to AAA Real-Time Production

## Purpose
Takes a Blender model from high-poly source to an engine-ready low-poly asset: silhouette-driven budgets, bake settings and the normal-map convention per engine, LOD versus Nanite, Unreal collision-hull naming and a pre-export gate. Official engine/Blender facts are sourced; budgets and ratios are marked as conventions.

## When to Use / When NOT
- ALLOWED: Preparing a static or skinned asset for Unreal, Unity or Godot — budgets, bake conventions and export gate below.
- ALLOWED: Choosing the normal-map green-channel convention for a target engine before baking from Blender.
- ALLOWED: Naming Unreal collision hulls (`UBX_`, `USP_`, `UCP_`, `UCX_`) in the Blender outliner before FBX export.
- NOT ALLOWED: Printability, wall thickness or manufacturing checks — use `3d-printing` or `dfam-3dprinting-production` instead.
- NOT ALLOWED: Decimation algorithm choice, retopology strategy or non-manifold repair — use `mesh-optimization-retopology` instead.
- NOT ALLOWED: Bake mechanics in depth (cage, map types, PBR authoring) — use `texturing-baking` instead.
- NOT ALLOWED: Engine-side runtime budgets beyond mesh/texture (draw calls, culling, streaming) — use `optimization-realtime` instead.
- NOT ALLOWED: Choosing an export format or its options — use `export-interchange` instead.

## Core Knowledge Content
> End-to-end technical pipeline for game asset creation in Blender: polygon budgeting, clean low-poly silhouette topology, high-to-low PBR baking, texel density enforcement, LOD generation, and Unreal Engine 5 Nanite optimization.

---

### 1. Technical Framework & Polygon Budgets

#### A. Real-Time Platform Polygon & Draw-Call Budgets

| Target Platform | Hero Character (Tris) | Environmental Prop (Tris) | Weapon / Hero Item (Tris) | Texture Resolution | Max Draw Calls / Frame |
|---|---|---|---|---|---|
| **Mobile / WebGL** | 8,000 – 15,000 | 200 – 1,500 | 1,000 – 3,000 | 1024 x 1024 (Atlas) | 50 – 150 <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **VR / Quest Standalone** | 15,000 – 35,000 | 500 – 3,000 | 2,500 – 7,000 | 2048 x 2048 | 80 – 200 <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **Console / PC (Standard LOD)** | 40,000 – 100,000 | 2,000 – 15,000 | 10,000 – 25,000 | 2048 – 4096 (PBR) | 1,000 – 3,000 <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **PC / UE5 Nanite (Cinematic)** | 500k – 2M (No LOD) | 50,000 – 500,000 | 100,000 – 500,000 | 4096 x 4096 (Virtual) | Governed by Clusters <!-- ease:source UNVERIFIED reason="engine-dependent budget; Epic's Nanite page states limits exist but gives no triangle figures" --> |

#### B. The Low-Poly Silhouette Law
Real-time engines render triangles, not quads. The budget must be allocated where it defines the **silhouette against the background**:
1. **Curved Silhouettes:** Cylinders and round bevels require dense edge loops (e.g. 16-24 sides for hero scope, 8-12 sides for small bolts). <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" -->
2. **Planar Interiors:** Flat coplanar surfaces must have zero unnecessary internal edge loops. Dissolve coplanar edges or collapse triangles.
3. **Deforming vs Non-Deforming Zones:**
   - Deforming joints (elbows, knees) require minimum 3 edge loops spanning the bend axis to prevent volume collapse during skinning. <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" -->
   - Static/hard-surface props can be aggressively triangulated without deformation artifacts.

---

### 2. The AAA High-to-Low Baking Pipeline

```text
[High-Poly Model] (SubD / ZBrush Sculpt / CAD Bevel)
        │
        ▼
[Low-Poly Retopology] (Silhouette matching, tri budget enforcement)
        │
        ▼
[UV Unwrapping & Packing] (Conformal unwrap, Texel Density locked)
        │
        ▼
[Bake Projection Cage] (Push along averaged normals, distance: 0.005–0.02m)
        │
        ▼
[Bake Maps] ──► Tangent-Space Normal (16-bit)
            ──► Ambient Occlusion (AO)
            ──► Curvature / Cavity
            ──► Thickness / Position
```

> Ray distance / cage: Blender exposes these as `scene.render.bake.max_ray_distance` and `scene.render.bake.cage_extrusion` (both default 0.0 on 5.2.0); the 0.005–0.02 m figure in the diagram above is a working heuristic, not a Blender default. <!-- ease:source S6 anchor="render.bake.max_ray_distance.default" --> <!-- ease:source S5 anchor="Max Ray Distance" --> <!-- ease:source S9 anchor="cage_extrusion" -->

#### A. Normal Map Tangent-Space Conventions
- **DirectX (-Y / Inverted Green Channel):** Unreal Engine 5, 3ds Max. *(Corrected 2026-10-13: Unity is Y+ / OpenGL, not DirectX — see the OpenGL line.)* <!-- ease:source UNVERIFIED reason="Epic/Autodesk pages stating the DirectX convention were not found in 3 queries; only third-party tutorials agree" -->
- **OpenGL (+Y / Standard Green Channel):** Blender, Unity, Godot, Maya, WebGL (Three.js). <!-- ease:source S6 anchor="render.bake.normal_(r,g,b).default" --> <!-- ease:source S9 anchor="normal_g" --> <!-- ease:source S1 anchor="Unity uses Y+ normal maps" --> <!-- ease:source S2 anchor="X+, Y+ and Z+" --> <!-- ease:source UNVERIFIED reason="Maya and Three.js conventions not checked against vendor docs" -->
- *Strict Rule:* If baking inside Blender (+Y) for Unreal Engine (-Y), either invert the G channel in the baker or invert green in UE5 texture settings (`Flip Green Channel`). <!-- ease:source UNVERIFIED reason="Unreal's Flip Green Channel texture setting named only in third-party sources; Blender side confirmed by S6" -->

#### B. Smoothing Groups & UV Seams Rule
- **Hard Edge Law:** Every hard/sharp edge (`sharp_edge` in Blender) **MUST** be a UV seam. <!-- ease:source UNVERIFIED reason="bake workflow convention; no vendor source" -->
- *Why:* If a hard edge is not split on the UV map, the normal map baker must interpolate across a $90^\circ$ normal discontinuity inside a single UV island, producing visible black seam artifacts and pixel bleeding. <!-- ease:source UNVERIFIED reason="bake workflow convention; no vendor source" -->
- **Soft Interior Law:** Not every UV seam needs to be a hard edge, but every hard edge must be a UV seam.

#### C. Texel Density (TD) Standardization
Texel density measures the number of texture pixels per meter of world-space geometry:

```math
TD = R \cdot \sqrt{\frac{A_{uv}}{A_{world}}} \quad \left( \frac{\text{px}}{\text{m}} \right)
```
Where $R$ is the texture edge in px, $A_{uv}$ the covered UV area as a fraction of the 0–1 square and $A_{world}$ the world-space surface area in m². *(Corrected 2026-10-13: the earlier formula divided a length-scale by an area, which is dimensionally wrong.)* <!-- ease:source UNVERIFIED reason="derived by dimensional analysis from the definition px/m; no external publisher" -->

| Asset Tier | Standard Texel Density | Standard Texture Size | Use Case |
|---|---|---|---|
| **First-Person Weapon / Cockpit** | 2048 px/m (20.48 px/cm) | 4096 x 4096 | Right in front of player camera <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **Third-Person Hero Character** | 1024 – 1536 px/m | 4096 x 4096 | Full body including gear <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **Environmental Props (Tables, Doors)** | 512 – 1024 px/m | 2048 x 2048 | Medium distance interaction <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **Architectural Modular Walls** | 256 – 512 px/m | 2048 x 2048 | Tilable trimsheets & world decals <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |

---

### 3. LOD Chains vs Unreal Engine 5 Nanite

#### A. Traditional Discrete LOD Generation

| LOD Level | Screen Size (%) | Tri Percentage | Purpose |
|---|---|---|---|
| **LOD 0** | $>50\%$ | $100\%$ | Base hero mesh with full micro-bevels <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **LOD 1** | $25\% – 50\%$ | $50\%$ | Collapse micro-bevels, weld small bolt vertices <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **LOD 2** | $12\% – 25\%$ | $25\%$ | Simplify cylinder segments ($16 \to 8$), remove interior faces <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **LOD 3** | $5\% – 12\%$ | $12\%$ | Box-like silhouette proxy <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |
| **LOD 4** | $<5\%$ | Billboard / Impostor | 2-triangle camera-facing plane <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" --> |

#### B. Nanite Architecture & Modern Considerations
In Unreal Engine 5, Nanite renders geometry using hierarchical micro-polygon clusters (128 triangles/cluster), eliminating manual LOD authoring for rigid meshes: <!-- ease:source S4 anchor="hierarchical clusters of triangle groups" --> <!-- ease:source UNVERIFIED reason="the 128-triangle cluster size is not stated on Epic's overview page" -->
- **What Nanite Loves:** Dense quads/triangles, bevels modeled directly into geometry, film-quality kitbash parts.
- **What Nanite Prohibits:** translucent materials (Nanite materials must be Opaque or Masked) and morph-target deformation. *(Corrected 2026-10-13 against the UE 5.8 docs: skeletal meshes, Masked materials and spline meshes are now supported; the earlier list named them as prohibited. Re-check the Nanite page for the engine version you ship on.)* <!-- ease:source S4 anchor="Nanite supports materials that have their Blend Mode set to Opaque and Masked" --> <!-- ease:source S4 anchor="Deformation with Morph Targets is not supported with Nanite" --> <!-- ease:source S4 anchor="Nanite Skeletal Meshes include support for" --> <!-- ease:source S4 anchor="Nanite-enabled meshes support splines by default" -->
- *Production Guideline:* Author hero characters and weapons with traditional clean topology and LODs; author complex rigid environment architecture directly for Nanite.

---

### 4. Collision Geometry Standards for Game Engines

Game engines require lightweight convex collision hulls to calculate physics without bogging down PhysX/Chaos engines:

#### Naming Conventions (Unreal Engine Automatic Importer)
1. **`UBX_[RenderMeshName]_[Index]`**: Box collision primitive (6 faces, cheapest). <!-- ease:source S3 anchor="UBX_[RenderMeshName]_##" -->
2. **`USP_[RenderMeshName]_[Index]`**: Sphere collision primitive. <!-- ease:source S3 anchor="USP_[RenderMeshName]_##" -->
3. **`UCX_[RenderMeshName]_[Index]`**: Convex hull collision mesh (must be strictly convex, no indentations). <!-- ease:source S3 anchor="UCX_[RenderMeshName]_##" -->
4. **`UCP_[RenderMeshName]_[Index]`**: Capsule collision primitive. <!-- ease:source S3 anchor="UCP_[RenderMeshName]_##" -->

```text
Outliner Hierarchy:
├── SM_SciFi_Generator       (Render Mesh - 25,000 Tris)
├── UCX_SM_SciFi_Generator_01 (Convex Hull base - 32 Tris)
├── UCX_SM_SciFi_Generator_02 (Convex Hull motor - 24 Tris)
└── UBX_SM_SciFi_Generator_03 (Box Hull exhaust - 6 Tris)
```

- *Strict Convexity Rule:* A `UCX` mesh must be a completely closed convex shape; Epic states that automatic decomposition of a non-convex mesh can give unpredictable results. Always break complex concave objects into multiple distinct convex `UCX` pieces. *(Corrected 2026-10-13: the earlier "bounding box or fail" outcome is not stated by Epic.)* Epic also notes boxes and spheres do not work when the Static Mesh is non-uniformly scaled; prefer `UCX`. <!-- ease:source S3 anchor="Breaking up a non-convex mesh into convex primitives is a complex operation" --> <!-- ease:source S3 anchor="spheres and boxes do not work if the StaticMesh is non-uniformly scaled" -->

---

### 5. Production Verification Gate (Pre-Export Checklist)

- [ ] **Transforms:** Location at `(0, 0, 0)`, Rotation at `(0°, 0°, 0°)`, Scale strictly `(1.0, 1.0, 1.0)`.
- [ ] **Geometry:** Zero non-manifold edges, zero internal faces, zero unweighted vertices, all face normals pointing outwards.
- [ ] **UVs:** UV map in Channel 0 named `UVMap`; all islands within $(0, 0) \leftrightarrow (1, 1)$ space; padding $\ge 16\,\text{px}$ for 2K textures. <!-- ease:source S6 anchor="render.bake.margin.default" --> <!-- ease:source S9 anchor="Extends the baked result" -->
- [ ] **Shading:** `sharp_edge` assigned to all hard boundaries; `WeightedNormal` modifier applied before export. <!-- ease:source S8 anchor="Keep Sharp" -->
- [ ] **Triangulation:** Checked with `TRIANGULATE` modifier to ensure no concave n-gon causes diagonal folding in-engine. <!-- ease:source S7 anchor="Minimum Vertices" -->

## Failure Modes (Mandatory)
- **Baked normals look inverted (lighting from the wrong side) in Unity or Godot** — cause: green channel flipped for Unreal's DirectX convention, but Unity and Godot expect Y+ (OpenGL) like Blender's default bake (`normal_r/g/b` = `POS_X/POS_Y/POS_Z`) — fix: flip green only for the Unreal target, never for Unity/Godot. <!-- ease:source S1 anchor="Unity uses Y+ normal maps" --> <!-- ease:source S2 anchor="X+, Y+ and Z+" --> <!-- ease:source S6 anchor="render.bake.normal_(r,g,b).default" -->
- **Dark seams or colour bleed at UV island borders after baking** — cause: bake margin smaller than the mip chain needs (Blender default is 16 px, `ADJACENT_FACES`), or a hard edge that is not a UV seam — fix: keep `scene.render.bake.margin` at or above the default and split UVs on hard edges. <!-- ease:source S6 anchor="render.bake.margin.default" --> <!-- ease:source S5 anchor="Margin" -->
- **Collision hull not picked up or attached to the wrong mesh on Unreal import** — cause: name does not follow `UCX_<RenderMeshName>_##` (also `UBX_`/`USP_`/`UCP_`) or `<RenderMeshName>` differs from the render mesh name — fix: rename the hull to match exactly and export both in the same FBX. <!-- ease:source S3 anchor="RenderMeshName must be identical" -->
- **Box or sphere collision stops working after the asset is scaled non-uniformly in-engine** — cause: Epic documents that boxes and spheres do not work on non-uniformly scaled Static Meshes — fix: use convex `UCX` hulls. <!-- ease:source S3 anchor="spheres and boxes do not work if the StaticMesh is non-uniformly scaled" -->
- **Nanite mesh renders with the engine default material and a warning** — cause: a material that is not Opaque or Masked (for example Translucent) — fix: switch the material blend mode or disable Nanite on that mesh. <!-- ease:source S4 anchor="When an unsupported material type is detected" -->
- **Texel density reported by a script disagrees with the visible texture sharpness** — cause: using the earlier length-over-area formula instead of `R * sqrt(A_uv / A_world)` with world-space areas (object scale applied) — fix: recompute per the corrected formula; see `uv-unwrapping` for a measured implementation. <!-- ease:source UNVERIFIED reason="derived by dimensional analysis; implementation lives in uv-unwrapping" -->

## Sources
- [S1] Unity - Manual: Introduction to normal maps (bump mapping) — https://docs.unity3d.com/6000.0/Documentation/Manual/StandardShaderMaterialParameterNormalMap.html (frozen: knowledge/_evidence/kb-261013/w2-web-unity-6000-0-normal-map-manual.html) — captured 2026-10-13 — sha256 bf5fdbabc1117729f4a8d71c0b1f8cd34c02cdbb524074e1f6c6033f5e1c78f2
- [S2] Standard Material 3D and ORM Material 3D — Godot Engine (stable) documentation in English — https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html (frozen: knowledge/_evidence/kb-261013/w2-web-godot-stable-standard-material-3d.html) — captured 2026-10-13 — sha256 2d393edcc07424faaef018fac99f392c0bfa2180cc5453e84869a762a61985e2
- [S3] FBX Static Mesh Pipeline in Unreal Engine | Unreal Engine 5.8 Documentation | Epic Developer Community — https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine (frozen: knowledge/_evidence/kb-261013/w2-web-unreal-fbx-static-mesh-pipeline.html) — captured 2026-10-13 — sha256 5b337e9afe1892078b2cf672d567412c0aaa73254adb6832a906090efd8dbca5
- [S4] Nanite Virtualized Geometry in Unreal Engine  | Unreal Engine 5.8 Documentation | Epic Developer Community — https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine (frozen: knowledge/_evidence/kb-261013/w2-web-unreal-nanite-overview.html) — captured 2026-10-13 — sha256 575230bf09d96c021e6e2327d71efa73920743a7470b413abfe7d776a2ab22f9
- [S5] Render Baking - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/render/cycles/baking.html (frozen: knowledge/_evidence/kb-261013/w2-manual-render-cycles-baking.html) — captured 2026-10-13 — sha256 4a443e80a7136042d854297a65ea5b92b992c3ad74b869fbef0103e913fb4865
- [S6] Local Blender 5.2.0 LTS runtime probe (script: knowledge/_evidence/kb-261013/w2-bpy-52-facts.py) — knowledge/_evidence/kb-261013/w2-bpy-52-facts.txt — captured 2026-10-13 — sha256 2411832c2522b533b8523ee16511805eb0d8a75bc2f2b213663bc0f77f4667af
- [S7] Triangulate Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/triangulate.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-generate-triangulate.html) — captured 2026-10-13 — sha256 7ef8e5e4272281f8e2c5bfc008137bf6dfc40cad1cc3fde7628b649a42e11532
- [S8] Weighted Normal Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-normals-weighted_normal.html) — captured 2026-10-13 — sha256 1d741bc1cd64d91f47d269b413e0bd3bb29574a0b33b194ab538c278b13d7920
- [S9] BakeSettings(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.BakeSettings.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-BakeSettings.html) — captured 2026-10-13 — sha256 e9737543892ea7981e70aca61d4251b1ef4d4067f486d088232ab1572e3380f5

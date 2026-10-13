---
name: mesh-optimization-retopology
category: 10-modeling
domain: modeling
loads_with: [modeling-topology, modifiers]
tags: [blender, retopology, decimation, quad-remesh, non-manifold, cleanup]
id: mesh-optimization-retopology
title: "Mesh Optimization, Retopology & Non-Manifold Geometry Repair"
description: Decimate modes, native remesh/retopology choices and a headless bmesh non-manifold diagnostic/repair protocol; third-party retopology add-ons are out-of-policy context only.
when: [decimate, retopology, quad-remesh, non-manifold-repair, lod-reduction, mesh-cleanup]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Mesh Optimization, Retopology & Non-Manifold Geometry Repair

## Purpose
Chooses how to reduce or rebuild a mesh with Blender-native tools (Decimate modes, Voxel/Quad remesh, Poly Build + Shrinkwrap) and how to detect and repair duplicate, degenerate and non-manifold geometry headlessly with bmesh. Decimate/remesh behaviour is checked against the 5.2 manual, Blender source and a local 5.2.0 run.

## When to Use / When NOT
- ALLOWED: Reducing triangle count for LODs with the Decimate modifier (`COLLAPSE`, `UNSUBDIV`, `DISSOLVE`) — mode semantics and measured counts below.
- ALLOWED: Choosing Voxel remesh, QuadriFlow quad remesh or manual retopology (Poly Build + Shrinkwrap) for scans and sculpts.
- ALLOWED: Auditing and repairing doubles, degenerate faces and flipped normals headlessly with bmesh before baking, booleans or export.
- NOT ALLOWED: Quad flow, pole placement rules for subdivision/animation and shading attributes — use `modeling-topology` instead.
- NOT ALLOWED: Modifier stack order and non-destructive setup — use `modifiers` instead.
- NOT ALLOWED: Print-specific wall, overhang or watertight acceptance — use `3d-printing` instead.
- NOT ALLOWED: Game-engine budgets, bake maps and LOD screen-size ratios — use `game-asset-pipeline-low-to-aaa` instead.
- NOT ALLOWED: Using RetopoFlow, Quad Remesher, PolyQuilt or MeshMachine as a production route — out-of-policy third-party add-ons (see `.project-agent.md`); use the native tools listed here.

## Core Knowledge Content
> Comprehensive technical guide for mesh decimation, automatic vs manual retopology, edge-flow topology for deformation, and headless non-manifold diagnostic and repair protocols.

---

### 1. Retopology Strategies: Decision Matrix

| Geometry Source | Production Goal | Recommended Pipeline | Target Topology | Key Tools / Add-ons |
|---|---|---|---|---|
| **Raw 3D Scan / Photogrammetry** | Real-Time Game Asset | Voxel Remesh $\to$ Manual Retopo $\to$ Shrinkwrap | Low-Poly Quads/Tris ($\le 15\text{k}$) | RetopoFlow / Quad Remesher *(third-party add-ons, out-of-policy context; native route: Voxel Remesh, QuadriFlow Quad remesh, Poly Build + Snapping)* <!-- ease:source S5 anchor="Voxel remesh has the following settings" --> <!-- ease:source UNVERIFIED reason="third-party add-on named for context only; out-of-policy per .project-agent.md, not evaluated" --> <!-- ease:source UNVERIFIED reason="15k triangle target is a convention: industry convention; no authoritative publisher found in bounded search" --> |
| **High-Poly Sculpt (ZBrush/Blender)** | Deforming Character | Manual Retopology with Muscle Edge Loops | 100% Quads, valence-3/5 poles | BMesh Polyquilt *(third-party add-on, out-of-policy context)* / Shrinkwrap *(native)* <!-- ease:source UNVERIFIED reason="third-party add-on named for context only; out-of-policy per .project-agent.md, not evaluated" --> |
| **Complex Hard-Surface CAD / Booleans** | Film / Product Render | Bevel modifier + Weighted Normal | Dense Quads + Planar N-gons | Quad Remesher / MeshMachine *(third-party add-ons, out-of-policy context; native: QuadriFlow, Bevel + Weighted Normal)* <!-- ease:source UNVERIFIED reason="third-party add-on named for context only; out-of-policy per .project-agent.md, not evaluated" --> |
| **Sculpt Concept Blockout** | Rapid Prototyping | OpenVDB Voxel Remesh ($0.005\,\text{m}$) | Uniform Quad Grid ($100\text{k} - 500\text{k}$) | Native Voxel Remesher (Ctrl+R) <!-- ease:source S5 anchor="Voxel remesh has the following settings" --> <!-- ease:source S6 anchor="Uses an OpenVDB to generate a new manifold mesh" --> <!-- ease:source S11 anchor="Shortcut : Ctrl - R" --> <!-- ease:source UNVERIFIED reason="the 0.005 m voxel size and the 100k-500k face range are conventions; the manual documents Voxel Size but gives no value" --> |
| **High-Res Mesh for Game LOD** | LOD1 – LOD3 Generation | Decimate (Collapse) with Normal Preservation | Optimized Triangles | Native Decimate Modifier <!-- ease:source S2 anchor="Collapse" --> |

> Native Asset Policy: `.project-agent.md` limits production geometry to Blender-native data API, bmesh, modifiers, sculpt and local project scripts; its only add-on exception is the user-selected QRemeshify offline gate (`scripts/run-qremeshify.py`) on a frozen scaffold. The add-on names in the table above are context for reading older workflows, not recommendations.

---

### 2. Decimation Algorithms & Mathematical Principles

Blender's `DECIMATE` modifier provides three distinct reduction modes (`decimate_type` enum: `'COLLAPSE'`, `'UNSUBDIV'` = Un-Subdivide, `'DISSOLVE'` = the **Planar** mode in the UI): <!-- ease:source S1 anchor="DecimateModifier.decimate_type" --> <!-- ease:source S13 anchor="decimate_type" --> <!-- ease:source S2 anchor="Un-Subdivide" -->

#### A. Collapse (Garland-Heckbert Quadric Error Metric)
- **How it works:** Iteratively collapses edges $(v_1, v_2) \to \bar{v}$ that minimize geometric deviation from the original surface planes using 4x4 quadric error matrices ($Q = \sum_p \mathbf{p}\mathbf{p}^T$, with $\mathbf{p}=(a,b,c,d)^T$ the plane $ax+by+cz+d=0$ of a unit normal). *(Corrected 2026-10-13: the earlier $nn^T$ is a 3x3 form that drops the plane offset $d$.)* <!-- ease:source S3 anchor="BLI_quadric.hh" --> <!-- ease:source S4 anchor="Kp = p p^T" -->
- **Best for:** Complex organic surfaces, scans, and high-poly sculpts where quad flow is not required. <!-- ease:source S2 anchor="Merges vertices together progressively" -->
- **Rules:** `delimit` (`NORMAL`, `MATERIAL`, `SEAM`, `SHARP`, `UV`) applies to **Planar (`DISSOLVE`)** only; Collapse has no seam/material/sharp constraint, and its source leaves the UV-seam check disabled. To protect regions during Collapse use `vertex_group` + `vertex_group_factor`, `use_symmetry` and `use_collapse_triangulate`, then inspect UV stretch and material borders afterwards. `ratio` is a target for triangulated output: on quad meshes the face count ends above `ratio x faces` (measured: 150 quads at `ratio=0.5` -> 96 faces). *(Corrected 2026-10-13: the earlier rule told agents to set `delimit` for Collapse, where it has no effect.)* <!-- ease:source S1 anchor="DecimateModifier.delimit" --> <!-- ease:source S2 anchor="Seam Does not dissolve edges marked as UV Seams" --> <!-- ease:source S3 anchor="the seam check would have to be done per layer" --> <!-- ease:source S1 anchor="decimate.COLLAPSE.ratio0.5(v,f)" -->

#### B. Un-Subdivide (Subdivision Inversion)
- **How it works:** Reverses subdivision by removing the edges a subdivide would have added; `iterations=2` equals one subdivide level (measured: Subsurf level-2 cube 98 v / 96 f -> `iterations=2` gives 26 v / 24 f, `iterations=1` gives 50 v / 48 f). <!-- ease:source S2 anchor="Two iterations is the same as one subdivide operation" --> <!-- ease:source S1 anchor="decimate.UNSUBDIV.iterations2(v,f)" -->
- **Best for:** CAD exports or dense grid meshes created by `SUBDIV`.
- **Constraint:** Intended for meshes with mainly grid-based topology (Blender manual); results on irregular or triangulated meshes are unreliable. *(Softened 2026-10-13 from "fails completely", which no source states.)* <!-- ease:source S2 anchor="mainly grid-based topology" -->

#### C. Planar (Coplanar Face Dissolution)
- **How it works:** Merges adjacent coplanar faces whose dihedral angle is below an authored threshold ($\theta \le 2.0^\circ$ to $5.0^\circ$). <!-- ease:source S1 anchor="DecimateModifier.angle_limit.default_deg" -->
- **Best for:** Hard-surface mechanical objects with large flat surfaces. Default `angle_limit` is 5 degrees; faces below the limit are dissolved (measured: a flat-gridded cube, 152 v / 150 f, becomes 8 v / 6 f at 5 degrees while 90-degree corners stay). *(Replaced 2026-10-13: the earlier "up to 85%" bound has no source and was exceeded.)* <!-- ease:source S1 anchor="decimate.DISSOLVE.angle5deg(v,f)" -->

---

### 3. Non-Manifold Geometry: Diagnostic & Repair Protocol

A mesh is **2-manifold** if every edge connects exactly two faces, and the neighborhood of every vertex is topologically homeomorphic to an open disk. Non-manifold errors break 3D printing slicers, boolean operations, and normal map baking. <!-- ease:source S9 anchor="edges not shared by exactly two faces" --> <!-- ease:source S10 anchor="the Manifold Solver will not work at all on non-manifold meshes" --> <!-- ease:source UNVERIFIED reason="effect on slicers and normal-map baking is stated without a source" -->

```text
       Non-Manifold Defects:
  (1) Open Boundary Edge       (2) Internal Shared Face      (3) Non-Manifold Vertex
       ┌───────┐                   ┌───────┬───────┐              ┌───┐
       │ Face  │                   │ Face 1│ Face 2│              │   │
       │       │                   ├───────┼───────┤              └───┴───┐
       └───────┘ (Only 1 face)     │   Internal    │                      │
                                   │    Face 3     │                      └───┘
                                   └───────────────┘ (Edge shared by 3 faces)
```

#### Python BMesh Headless Repair Function

```python
import bpy
import bmesh

def clean_and_repair_mesh(obj: bpy.types.Object, merge_dist: float = 1e-5) -> dict:
    """Headless automated repair of non-manifold, duplicate, and degenerate geometry."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    # 1. Remove duplicate overlapping vertices
    initial_verts = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)
    doubles_removed = initial_verts - len(bm.verts)

    # 2. Dissolve zero-area degenerate faces and zero-length edges
    bmesh.ops.dissolve_degenerate(bm, dist=merge_dist, edges=bm.edges)

    # 3. Detect and delete internal non-manifold faces (edges shared by >2 faces)
    bad_faces = set()
    for edge in bm.edges:
        if len(edge.link_faces) > 2:
            bad_faces.update(edge.link_faces)
    
    # 4. Enforce outward consistent face normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(me)
    bm.free()
    me.update()

    return {
        "doubles_removed": doubles_removed,
        "internal_face_conflicts": len(bad_faces)
    }
```

---

> Verified run (Blender 5.2.0, `knowledge/_evidence/kb-261013/w2-bpy-52-facts.py`): on a cube with one coincident vertex and one fin face on an existing edge, `clean_and_repair_mesh` returned `{'doubles_removed': 1, 'internal_face_conflicts': 3, 'faces_before': 7, 'faces_after': 7}` and one edge with more than two faces remained. Step 3 therefore **detects only** (the earlier comment said "detect and delete"); delete or split the reported faces yourself before trusting a watertight claim. Signatures used: `bmesh.ops.remove_doubles(bm, verts, use_connected, dist)`, `bmesh.ops.dissolve_degenerate(bm, dist, edges)`, `bmesh.ops.recalc_face_normals(bm, faces)`. <!-- ease:source S1 anchor="repair_fn.result" --> <!-- ease:source S12 anchor="remove_doubles" --> <!-- ease:source S12 anchor="dissolve_degenerate" --> <!-- ease:source S1 anchor="bmesh.ops.remove_doubles.sig" --> <!-- ease:source S1 anchor="bmesh.ops.dissolve_degenerate.sig" --> <!-- ease:source S1 anchor="bmesh.ops.recalc_face_normals.sig" -->

### 4. Retopology Edge-Flow for Deformation

When creating characters, creatures, or mechanical joints that articulate:
1. **Concentric Loops:** Place circular edge loops around openings (eyes, mouth, shoulder socket, knee pivot). <!-- ease:source S7 anchor="are therefore preferred for animation and subdivision modeling" -->
2. **Pole Placement:** Limit vertex poles (vertices connected to 3, 5 or more edges; $N=3$ or $N\ge5$) to flat, non-bending surfaces. Never place an E-pole ($N=5$) directly across a high-stress bending creaseline (e.g. elbow crease). <!-- ease:source S7 anchor="Poles are vertices that are connected to either three, five, or more edges" -->
3. **Square Grid Aspect Ratio:** Keep quads as close to $1:1$ aspect ratio as possible. Stretched rectangular quads ($>3:1$) cause severe texture stretching and pinching under deformation. <!-- ease:source UNVERIFIED reason="industry convention; no authoritative publisher found in bounded search" -->

---

### 5. Production Gate Checklist (Topology & Optimization)

- [ ] **Manifold Check:** BMesh check returns zero open boundary edges and zero edges with $>2$ linked faces. <!-- ease:source S9 anchor="edges not shared by exactly two faces" -->
- [ ] **Degenerate Check:** Zero zero-area faces and zero zero-length edges.
- [ ] **Normal Consistency:** 100% of face normals oriented consistently outwards (`recalc_face_normals`). <!-- ease:source S1 anchor="bmesh.ops.recalc_face_normals.sig" -->
- [ ] **Pole Ratio:** For deforming character assets, $\ge 92\%$ of vertices are valence-4 (quad intersections). <!-- ease:source UNVERIFIED reason="92% valence-4 threshold is a convention: industry convention; no authoritative publisher found in bounded search" -->
- [ ] **Delimit Preservation:** Planar (`DISSOLVE`) decimation keeps material boundaries and UV seams via `delimit`; for Collapse, verify UV stretch and material borders by inspection (no seam constraint exists). <!-- ease:source S2 anchor="Seam Does not dissolve edges marked as UV Seams" -->

## Failure Modes (Mandatory)
- **UV seams or material borders get distorted after Decimate in Collapse mode even with `delimit` set** — cause: `delimit` only applies to Planar (`DISSOLVE`); Collapse has no seam constraint — fix: use Planar for flat hard-surface parts, protect areas with `vertex_group`, and check UV stretch afterwards. <!-- ease:source S2 anchor="Delimit Prevent dissolving geometry in certain places" --> <!-- ease:source S3 anchor="the seam check would have to be done per layer" -->
- **Collapse leaves far more faces than `ratio` implies (150 quads at 0.5 give 96 faces)** — cause: `ratio` targets triangulated output and quads whose edges are not collapsed stay unchanged — fix: enable Triangulate if an exact count matters, or read `modifier.face_count` instead of computing it. <!-- ease:source S2 anchor="This is only true if the Triangulate option is disabled" --> <!-- ease:source S1 anchor="decimate.COLLAPSE.ratio0.5.face_count_prop" -->
- **`clean_and_repair_mesh` reports `internal_face_conflicts` but the mesh is still non-manifold** — cause: step 3 only collects faces on edges with more than two faces; nothing deletes them — fix: delete or split those faces (`bmesh.ops.delete` / `split_edges`) and rerun the audit. <!-- ease:source S1 anchor="repair_fn.after.edges_with_gt2_faces" -->
- **Boolean or print gate rejects a mesh that looks closed** — cause: edges not shared by exactly two faces (boundary, fins, wire edges) or inverted winding; the repo gate counts `non_manifold_edges`, `non_contiguous_edges`, `wire_edges` and `signed_volume_positive` — fix: run the same checks before the operation and repair first. <!-- ease:source S9 anchor="non_contiguous_edges" --> <!-- ease:source S10 anchor="the Manifold Solver will not work at all on non-manifold meshes" -->
- **Animated character deforms badly after Voxel remesh** — cause: Voxel remesh produces uniform grid topology that ignores edge flow and the manual says it should not be used for meshes that will be deformed — fix: use QuadriFlow quad remesh as a base, then retopologise manually with Poly Build + Shrinkwrap. <!-- ease:source S5 anchor="Creating topology for a mesh that will be deformed" -->
- **A workflow depends on RetopoFlow, Quad Remesher, PolyQuilt or MeshMachine** — cause: older notes name third-party add-ons that this repo does not permit in production — fix: substitute the native tools above, or use the user-selected QRemeshify offline gate if the owner chose it. <!-- ease:source S8 anchor="Asset construction: Blender-native data API, bmesh, modifiers, sculpt, and local project scripts only." -->

## Sources
- [S1] Local Blender 5.2.0 LTS runtime probe (script: knowledge/_evidence/kb-261013/w2-bpy-52-facts.py) — knowledge/_evidence/kb-261013/w2-bpy-52-facts.txt — captured 2026-10-13 — sha256 2411832c2522b533b8523ee16511805eb0d8a75bc2f2b213663bc0f77f4667af
- [S2] Decimate Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/decimate.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-generate-decimate.html) — captured 2026-10-13 — sha256 7b4a3934c1bf8fc0d2ec7d84d1ee2a92a470e10c065f4db3f3da1638a86a4962
- [S3] Blender source: source/blender/bmesh/tools/bmesh_decimate_collapse.cc (main branch, fetched raw) — https://projects.blender.org/blender/blender/raw/branch/main/source/blender/bmesh/tools/bmesh_decimate_collapse.cc (frozen: knowledge/_evidence/kb-261013/w2-src-blender-bmesh-decimate-collapse.cc) — captured 2026-10-13 — sha256 1ac83c2cb61910760f1dac80773dc77ba16a1edaa0235f8083c857320e6576c4
- [S4] Garland & Heckbert, Surface Simplification Using Quadric Error Metrics (1997) — fetch record — https://www.cs.cmu.edu/~./garland/Papers/quadrics.pdf (frozen: knowledge/_evidence/kb-261013/w2-src-garland-heckbert-1997-meta.txt) — captured 2026-10-13 — sha256 9f23090db718e9e28f2dc9345ec158556f8e92fb837e514bc6b03024e1df493b
- [S5] Remeshing - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-meshes-retopology.html) — captured 2026-10-13 — sha256 1de500b7e0507bd27fba9263327aa5a5f3146b7da68a62edf0d5c1350ed4b320
- [S6] Remesh Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/remesh.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-generate-remesh.html) — captured 2026-10-13 — sha256 a64b75048e68676cac2c94eedee1bcdaa2e3bad8d916b847773d5023c68497db
- [S7] Mesh Structure - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/meshes/structure.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-meshes-structure.html) — captured 2026-10-13 — sha256 87b7221bbd13bdc8b9f2138dc07d7ad9ef92ee2eea84dd5c98005fbd1c18371d
- [S8] Project binding rules — Native Asset Policy (Tech Stack section) — .project-agent.md — captured 2026-10-13 — sha256 8cde6609763c6f287717b23587c6f542f195e506e1c9fa283f40b3eaf65af82c
- [S9] Repo: production gate topology checks — scripts/production_gate/topology.py — captured 2026-10-13 — sha256 8c3b638fc3599f41f6b67b71039d400dc1b88c16d4fd24baa0c2c354888843a4
- [S10] Boolean Modifier - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-modifiers-generate-booleans.html) — captured 2026-10-13 — sha256 2432a856d431db80eb8708eedabc40fbfeaaaa64d2c110b0a6ca62cdf7cd2f4e
- [S11] Remesh - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/sculpt_paint/sculpting/tool_settings/remesh.html (frozen: knowledge/_evidence/kb-261013/w2-manual-sculpt_paint-sculpting-tool_settings-remesh.html) — captured 2026-10-13 — sha256 471f3026f45cee6c26afa4c704643a8517d72d839164d4a6ce21f131be7ecccf
- [S12] BMesh Operators (bmesh.ops) - Blender Python API — https://docs.blender.org/api/current/bmesh.ops.html (frozen: knowledge/_evidence/kb-261013/w2-api-bmesh-ops.html) — captured 2026-10-13 — sha256 45f98573a8ee18729eadeb8a5bcc784df770d34ebfe443953f27ebb3932a8555
- [S13] DecimateModifier(Modifier) - Blender Python API — https://docs.blender.org/api/current/bpy.types.DecimateModifier.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-DecimateModifier.html) — captured 2026-10-13 — sha256 05660eb194441ab7ebe7f9a17bd4063566367159329d737dbf982028bd3a33a3

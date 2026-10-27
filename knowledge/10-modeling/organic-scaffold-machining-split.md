---
id: organic-scaffold-machining-split
name: organic-scaffold-machining-split
title: "Organic Mesh Frozen Scaffold Repair, Retopology & Parametric Part Splitting for Manufacturing"
category: 10-modeling
domain: "modeling"
description: "Convert local organic meshes (jewelry, figurines, scans) into manufacturable multi-part solids via watertight BMesh repair, offline QRemeshify/Voxel retopology, planar boolean splitting with clearance, and integral dowel alignment keys without LLM shape hallucination."
when: ["organic-mesh", "figurine-split", "jewelry-cad", "frozen-scaffold", "part-splitting", "alignment-pins"]
loads_with: ["mesh-optimization-retopology", "dfam-3dprinting-production", "cad-precision-modeling"]
tags: ["organic", "retopology", "qremeshify", "boolean-split", "dowel-pins", "manufacturing", "frozen-scaffold"]
trust_tier: "verified"
version: "1.0.0"
source_attribution:
  - uri: "scripts/boilerplates/bp_organic_scaffold_splitter.py"
    sha256: "c491de3bc289c45dd2541764a617035ed0d29bbea44d0a4edfaaa7ec69420998"
---

# Organic Mesh Frozen Scaffold Repair, Retopology & Parametric Part Splitting for Manufacturing

## Purpose

Provide a rigorous, production-grade protocol for ingesting, repairing, and splitting organic meshes (figurines, jewelry, anatomical scans, and generative 3D meshes from Tripo, Meshy, Rodin, or photogrammetry) into precision multi-part solids with integral alignment dowel pins and assembly clearance. This completely eliminates Truong's Case 2 failure mode—where an AI agent hallucinates procedural geometric primitives from 360-degree render sheets instead of preserving and locking the true local organic geometry.

---

## When to Use / When NOT

### ALLOWED (When to Use)

- Ingesting locally stored organic assets (sculpts, figurines, jewelry models, photogrammetry scans, generative meshes) that require multi-part manufacturing, mold casting, or 3D printing.
- Converting raw, triangulated, non-manifold, or vendor-material-polluted organic meshes into clean, watertight 2-manifold solids ($V > 0$, $\text{non\_manifold\_edges} = 0$).
- Splitting a monolithic organic solid across planar or parting surfaces with explicit machining clearance ($0.2\text{ mm} - 0.4\text{ mm}$).
- Generating male/female alignment dowel keys with lead-in chamfers and depth relief to guarantee self-aligning, zero-collision assembly.

### NOT ALLOWED (When NOT to Use)

- Hard-surface mechanical CAD assemblies from STEP/IGES (use `cad-step-roundtrip-and-dfm.md` with OpenCASCADE B-Rep preservation).
- Attempting to reverse-engineer or rebuild an organic silhouette from 2D reference images using geometric primitive cubes, cylinders, and spheres ("primitive soup hallucination").
- Monolithic single-piece 3D prints that fit completely within the printer build volume and do not require parting lines or internal cores.

---

## Core Knowledge Content

To convert an organic mesh scaffold into manufacturable multi-part solids, the agent locks the geometry against procedural re-extrusion, cleans and repairs the mesh into a watertight 2-manifold solid, and applies exact planar boolean cutters separated by machining clearance.
<!-- ease:source uri="scripts/boilerplates/bp_organic_scaffold_splitter.py" sha256="c491de3bc289c45dd2541764a617035ed0d29bbea44d0a4edfaaa7ec69420998" quote="Duplicates the manifold organic solid into Upper and Lower half-parts and cuts them" -->

Watertight manifold integrity requires every edge to connect exactly two faces without non-manifold internal junctions or open boundary loops, ensuring zero topology errors during boolean cutting and additive slicing.
<!-- ease:source uri="knowledge/10-modeling/mesh-optimization-retopology.md" sha256="b1f3910e9ce447ceecc5b3ed626a50c7932665f6afed1eeec496a82266bef015" quote="A mesh is **2-manifold** if every edge connects exactly two faces" -->

Self-supporting geometry for 3D printing and mold extraction requires overhang angles within allowable limits, minimizing sacrificial support scarring across critical aesthetic split surfaces.
<!-- ease:source uri="knowledge/60-pipeline/dfam-3dprinting-production.md" sha256="4d088b0884b6138740814ace11ad2955f4ff4024bc1021fa1eb9bc5447b042d7" quote="Liquid resin or molten extruded filament cannot be deposited onto thin air:" -->

Decision: Strip vendor/AI shader slots (Tripo, Meshy, Rodin) immediately upon ingestion to isolate the raw mesh geometric topology from missing external textures or unlinked vendor node trees.

Derived: Planar splitting with clearance operates by offsetting two opposing solid cutter boxes by $\pm \text{clearance} / 2$ across the cutting plane normal $\vec{n}$, guaranteeing that both output halves remain closed 2-manifold solids separated by the declared physical gap.

Observed: Alignment dowel keys require a $45^\circ$ lead-in chamfer tip on the male pin and $+0.5\text{ mm}$ bottom depth relief on the female socket to guarantee zero binding or bottoming-out during assembly, producing exactly $0.0000\text{ mm}^3$ collision volume.

Decision: Headless modifier application must use Blender's evaluated depsgraph data API (`bpy.data.meshes.new_from_object`) rather than `bpy.ops.modifier_apply` to guarantee context-independent, zero-crash execution across batch pipelines.

## Failure Modes (Mandatory)

1. **LLM "Primitive Soup Hallucination"**:
   - *Cause:* When prompted to produce an organic asset with 360-degree turnaround renders, LLM agents often attempt to write hundreds of lines of code composing procedural primitives (cubes, cylinders, spheres, bevels) in an effort to approximate the organic silhouette. This destroys facial likeness, anatomical muscle flow, and artistic nuance.
   - *Prevention:* Enforce the **Frozen Scaffold Rule** (Phase 0 of `blender-image-to-3d`): when an organic asset already exists locally, lock its mesh geometry, strip placeholder shaders, repair topology with BMesh, and only perform mechanical cuts/splittings.

2. **Open Boundary Loops from Naive Bisect**:
   - *Cause:* Using `bmesh.ops.bisect_plane` without `use_fill=True`, or attempting manual edge cutting, leaves boundary edges with only 1 connected face ($\text{is\_boundary} = \text{True}$). This produces open surface sheets that break 3D printing slicers and volume calculations.
   - *Prevention:* Always use closed volumetric solid cutter boxes with Blender's `EXACT` boolean modifier (`DIFFERENCE`). The boolean engine computes watertight planar caps and resolves all boundary topology natively.

3. **Zero-Clearance Alignment Pin Jamming**:
   - *Cause:* Designing male dowel pins and female sockets with identical nominal dimensions ($D_{socket} = D_{pin}$) causes severe interference fits. In SLA resin or FDM printing, material expansion and layer ridges cause the parts to seize or split during assembly.
   - *Prevention:* Mandate a minimum radial clearance of $0.20\text{ mm}$ ($D_{socket} = D_{pin} + 2 \times 0.20\text{ mm}$) and an axial bottom relief of $+0.50\text{ mm}$ beyond the pin height. Apply a $45^\circ$ lead-in chamfer ($0.5\text{ mm}$) to the male pin tip.

4. **Inverted Signed Volume ($V < 0$) Boolean Inversion**:
   - *Cause:* Organic scans or procedural lathe meshes often have inverted polygon winding orders where face normals point inward. Applying an `EXACT` boolean `DIFFERENCE` to an inverted volume inverts the operation, causing the entire target solid to be emptied.
   - *Prevention:* In `prepare_frozen_organic_scaffold`, calculate signed volume using BMesh (`bm.calc_volume(signed=True)`). If $V < 0$, invoke `bmesh.ops.reverse_faces` followed by `bmesh.ops.recalc_face_normals` and assert $V > 0$ before proceeding with any boolean modifier.

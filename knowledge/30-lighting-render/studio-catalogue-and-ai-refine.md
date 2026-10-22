---
id: studio-catalogue-and-ai-refine
name: studio-catalogue-and-ai-refine
title: "Commercial Studio Catalogue 6-Shot Pipeline, Decoupled PBR Shaders & Hybrid AI Refinement"
category: 30-lighting-render
domain: "lighting_render"
description: "Render CAD assemblies with 100% geometry lockdown, decoupled wood-grain vs color-stain OpenPBR shaders, automatic Face vs CutEdge normal slotting, standardized 6-angle studio cameras, and provenance-bound Nano Banana Pro AI refinement kits."
when: ["text-2-render", "studio-catalogue", "plywood-shader", "decoupled-tint", "ai-refine", "nano-banana"]
loads_with: ["product-viz-and-shots", "native-render-delivery", "materials-pbr"]
tags: ["studio-render", "catalogue", "openpbr", "bevel-shader", "agx", "ai-refine", "cad-render"]
trust_tier: "verified"
version: "1.0.0"
source_attribution:
  - uri: "scripts/boilerplates/bp_studio_catalogue_render.py"
    sha256: "7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8"
---

# Commercial Studio Catalogue 6-Shot Pipeline, Decoupled PBR Shaders & Hybrid AI Refinement

## Purpose

This standard establishes the commercial product design rendering architecture connecting CAD assemblies (e.g. Fusion 360, STEP, OBJ) directly into Blender 5.2 LTS Cycles with 100% geometry lockdown, decoupled wood-grain versus color-stain OpenPBR shading, automated normal-based multiplex plywood slotting, 6 standardized studio catalogue cameras, and provenance-bound AI refinement kits.

## When to Use / When NOT

### ALLOWED (When to Use)
- Commercial studio catalogue rendering for furniture, enclosures, and precision mechatronics assemblies.
- Multiplex plywood components requiring distinct shading between flat veneer faces and 24-ply cut edges.
- Color variations of stained wood or anodized metals where texture, roughness, and grain contrast must remain 100% identical.
- Multi-tier rendering pipelines where native Blender Cycles outputs serve as base composition for AI refinement.

### NOT ALLOWED (When NOT to Use)
- Real-time low-poly game assets requiring single-drawcall atlas baking.
- Structural CAD simulation or finite element analysis (FEA) where optical shaders provide no physical data.
- Replacing physical manufacturing verification with AI-generated concept images.

## Core Knowledge Content

Precision CAD rendering strictly enforces absolute CAD geometry lockdown without vertex displacement or destructive boolean modifications.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="1. CAD Geometry Lockdown (100% vertex coordinate preservation)." -->

The production pipeline verifies that vertex coordinates before and after shading operations match with zero drift.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="compute_mesh_vertex_sha256" -->

Automated slotting classifies plywood polygons into veneer faces versus peripheral multiplex cut edges using normal vectors without modifying CAD coordinates.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="def slot_plywood_face_vs_cutedge(" -->

Wood grain relief and color tint are controlled on two independent shader branches so that changing stain colors preserves all surface micro-relief and roughness.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="Decoupled PBR shader architecture (grain/bump/roughness vs color tint)." -->

Non-destructive micro-bevel highlights are composited using shader nodes rather than topological mesh bevel modifiers.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="build_decoupled_stain_pbr_material(" -->

Standardized studio product rendering relies on a seamless backdrop, shadow-catcher ground plane, and structured camera framing.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="3-point grazing chiaroscuro area light triad + shadow-catcher ground plane + AgX." -->

The studio camera rig establishes 6 standardized catalogue angles including front, side, top, 3/4 beauty, overview, and macro details.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="setup_six_shot_studio_rig(" -->

Structured AI refinement manifests bind native renders to multimodal generative prompts while explicitly enforcing provenance boundaries.
<!-- ease:source uri="scripts/boilerplates/bp_studio_catalogue_render.py" sha256="7f0e5ac12c0089113758ba11f84fb9f6b2a6d4612b66eff69a83057b3fa932d8" quote="build_ai_refine_kit_manifest(" -->

Derived: In multiplex plywood furniture, cut edges expose alternating cross-grain veneers with different porosity; isolating cut edges into a dedicated material slot allows independent roughness and micro-bump tuning without affecting face veneers.

Decision: The 6 studio camera shots must evaluate the combined world-space bounding box of all target objects to prevent subject clipping and ensure consistent focal framing across product revisions.

Observed: Applying a 0.6 mm ShaderNodeBevel into the Bump normal input catches specular highlights along 90-degree CAD edges without introducing non-manifold geometry or artifacting CAD triangulation.

## Failure Modes (Mandatory)

1. **Baking color tint into wood grain textures**:
   - *Symptom*: When changing wood stain color (e.g. from natural birch to royal blue), grain contrast is washed out or inverted, and surface highlights lose definition.
   - *Root Cause*: Color tint was multiplied directly into the noise or bitmap texture prior to driving the roughness and bump channels.
   - *Remedy*: Decouple into two independent branches: procedural noise drives bump ($0.45$), roughness ($0.25 - 0.45$), and coat ($0.25$), while `ShaderNodeMix` (`MULTIPLY`, `data_type='RGBA'`) modulates an independent `tint_rgba` parameter into Principled BSDF Base Color.

2. **Applying uniform wood face texture to 24-ply multiplex cut edges**:
   - *Symptom*: End-grain and perimeter cuts show flat veneer wood grain stretching unnaturally over cut edges instead of striped alternating multiplex laminations.
   - *Root Cause*: Single material slot assigned uniformly to the entire CAD solid.
   - *Remedy*: Run `slot_plywood_face_vs_cutedge(obj, dominant_axis='Z', dot_threshold=0.85)` to automatically partition polygons into slot 0 (`Plywood_Face`) and slot 1 (`Plywood_CutEdge_Multiplex`) based on polygon normal dot product.

3. **Using destructive mesh Bevel modifiers on imported CAD triangles**:
   - *Symptom*: Surface artifacts, pinched shading, non-planar polygons, and vertex coordinate drift on imported STEP/CAD geometry.
   - *Root Cause*: Applying geometric `Bevel` modifiers or manual edge beveling across triangulated CAD surfaces destroys planar topology.
   - *Remedy*: Maintain 100% CAD Geometry Lockdown. Insert `ShaderNodeBevel` (`samples=4`, `radius=0.0006`) feeding into `Bump.inputs['Normal']` -> `Principled BSDF.inputs['Normal']` for non-destructive render-time edge highlights.

4. **Treating AI-refined Nano Banana Pro imagery as geometric verification evidence**:
   - *Symptom*: Dimensional discrepancies, hole displacement, or altered wall thickness accepted based on AI-generated beauty shots.
   - *Root Cause*: Conflating presentation marketing imagery with authoritative engineering verification.
   - *Remedy*: Enforce repo provenance policy: AI refinement kits must tag `"media_authority": "POST_RENDER_CONCEPT_MEDIA"` and maintain native Blender Cycles renders as the sole `"geometry_authority": "NATIVE_BLENDER_RENDER_LOCKED"`.

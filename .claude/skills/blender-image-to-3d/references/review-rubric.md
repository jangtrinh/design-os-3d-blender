# Review Rubric & Quantitative Gates (distilled from the img2threejs source, 260728)

## 1. Suitability rubric (Step 0.1)

**PASS:** one clear object · fills enough of the frame · strong silhouette · main material visible · hidden faces inferable (symmetry) · approximable with primitives.
**CONDITIONAL:** only one viewing angle but the object is rotationally symmetric · partially occluded but the main masses are clear · organic but the user accepts stylized · no exact logo/text required.
**REJECT:** ambiguous object · the image is a scene, not an object · an important part of the shape is occluded/blurred/cropped · manufacturing accuracy demanded · the object is mostly smoke/liquid/glass caustics/mesh lace (no procedural route).
Reject → `request-input` (ask for more angles, a sharper image or a dimensioned drawing); if reduced fidelity has already been accepted, switch to a different Blender-native construction. Do not use external generation/retrieval as a fallback.

## 2. Complexity tier → targetMinDetails (quantitative spec gate)

| Tier | Min details in the inventory | Example |
|---|---|---|
| simple | 3 | mug, box, simple table |
| moderate | 6 | office chair, desk lamp |
| complex | 10 | bicycle, vintage speaker, camera |
| ultra | 16 | multi-part machinery, gun, watch |

Scan by `component-zones` (once parts are split) or `grid-3x3` (not yet split). Each detail records: region + kind + confidence (0-1) + **mapsTo** (a specific component/material). A detail described in prose only = gate FAIL. Do not inflate confidence to reach the count.

## 3. Detail taxonomy → Blender technique

| Kind | Blender technique |
|---|---|
| gloss (specular area) | low roughness 0.05-0.2 in that area (vertex group/texture mask); brushed metal → anisotropy |
| bevel (edge rounding) | **Bevel modifier — real geometry**, not a normal map, if the image shows a sharp highlight line along the edge |
| fastener (screw/rivet) | instancing: Array modifier / Geometry Nodes distribute — do NOT model each one |
| linework | 3 techniques, chosen by evidence: engraved → groove geometry; painted → texture/decal; panel-line → dark AO seam with no depth |
| seam | thin groove/ridge + dark AO inside the gap |
| stain/wear | procedural texture override: dirtAmount, cavityBias (dirt settling in crevices → AO/pointiness mask), gravity-aligned streaks, patinaColor |
| scratch/chip | local roughness/normal perturbation; a chip that changes the silhouette → small boolean |
| decal | area texture (UV project); add geometry only if it has thickness |
| emissive | Emission shader + consider adding a real light next to it for spill |
| hole | Boolean — a real hole changes topology, it is not a dark patch |
| groove/ridge | curve + profile, or displacement along a path |

## 4. Vision review — how to score each pass

- Score each pass from **a single comparison sheet**; pick ≤5 systems critical to that pass to scrutinize (do not scrutinize everything in every pass).
- Tier the features: `critical` (must pass) / `important` / `detail`.
- **Threshold:** global score ≥ 0.7; every critical feature must meet its own threshold. Below → refine.
- Uncertain (the score fluctuates when you re-score it yourself) → treat it as a "probe": look at another angle before issuing a verdict.

## 5. Fidelity scale (report honestly)

0.2 rough placeholder · 0.4 recognizable silhouette · 0.6 macro/meso masses correct, weak material · 0.75 the object reads correctly, details approximate · 0.85 good procedural match · 0.95 close to the reference (usually needs several image angles). **Do not claim ≥0.9 from a single ambiguous image.**

## 6. Root cause: refine-spec vs refine-code

**refine-spec when:** a component is missing/invented · wrong primitive family · wrong proportions/coordinate system from the start · material layer under-specified · a detail is missing from the spec · image evidence contradicts the spec.
**refine-code when:** the spec is clear but the geometry is wrong · material params not implemented · mask/wear missing in the code · hierarchy/pivot deviates from the spec · the render has artifacts.
**request-input when:** the image hides an important shape · the material cannot be inferred from this angle · exact branding/text is required · the demanded fidelity exceeds what one image can support.
**stop when:** the goal is met · the user accepts the approximation · the remainder needs new references/manual modeling/a different route.

## 7. Confirmed traps (from their production log)

1. **Pixel-comparing against a photograph is meaningless** — framing/background/lighting overwhelm fidelity (a faithful BMX was scored reject 0.53). DO NOT try to pixel-match a photo; score against each pass's goal: does the silhouette read? are the parts present? is the color in the right tone?
2. **A 2D gate is blind to 3D realism** — a matching silhouette can still be "cardboard": razor-sharp edges with no taper, metal that looks like plastic. ALWAYS render an extra **3/4 angle** before reporting done; a passing front-on sheet is not the finish line.
3. **Do not infer features from the name** — for an object with a specific identity (a real product), ask for a front-on image + the exact name; do not guess the construction from a description.

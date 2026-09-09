# Reference reconstruction review rubric

## 1. Suitability

**Proceed:** the visible primary shape, critical features, target use, and acceptable unknowns can be stated. **Conditional:** an object is partly occluded or has only one view, but the owner accepts the bounded inference. **Request input:** a critical section, identity, text, dimension, or function is unavailable and would change the build. Do not use generation or retrieval as a fallback.

## 2. Evidence inventory is a planning aid

Record each reference feature with its source crop, named object/interface, expected visible construction, proof shot, and falsifier. The inventory prevents omissions; it is not a fidelity gate. Mesh count, detail count, confidence score, or a mapped row does not prove visual likeness. A primary view controls visible count, placement, facing, and silhouette. Close-ups establish local profile and construction. Mechanical routing and installation logic require applicable drawings or official technical documents.

## 3. Technique follows observed construction

| Observed feature | Native Blender treatment |
|---|---|
| Highlighted edge or real seam | Bevel, groove, ridge, or distinct panel geometry when the reference supports it |
| Fastener or bore | Instanced semantic hardware or a real opening when it changes the visible construction |
| Panel or louver | Layered frame, return, and recess where the close-up shows them |
| Material highlight | Local material response only after the underlying profile is known |
| Unseen surface | Explicit inference or `UNKNOWN`, never a hidden claim |

## 4. Manual review verdict

1. Write the expected critical features before opening the candidate.
2. Review the primary image, every supplied close-up, and a corroborating 3/4 or opposing view where it can falsify the construction.
3. Give every critical feature a named `PASS`, `FAIL`, or `UNKNOWN` verdict with its proof view and falsifier. Do not substitute a global score or invented decimal fidelity number.
4. Review construction layers for close hardware. A cabinet, for example, needs door return/seal, hinge leaves/pin/knuckles, opposed lock, HMI bezel/recess, operator head/collar/stem, and framed louver/filter construction when the evidence calls for them.
5. Compare fasteners by family at the matched camera. Check apparent scale and containment as well as contact; a seated fastener may still read too small.

If a judgment is uncertain, obtain a discriminating view or keep it `UNKNOWN`. Numeric topology, a clean silhouette in one view, readable labels, or an unclipped distant object do not pass the missing construction review.

## 5. Root cause and verdict

Use `refine-spec` when evidence, a critical feature, a construction hypothesis, or an interface contract is missing or contradicted. Use `refine-code` when the reviewed contract is clear but its geometry, hierarchy, material, or output has failed. Use `request-input` when the necessary evidence is unavailable. Use `stop` only when the scoped target is met or the owner accepts the documented approximation.

## 6. Traps to test

- Pixel similarity is not a fidelity test: framing, background, and lighting can dominate.
- A single front view can hide cardboard form, missing transitions, and bad material response; inspect a discriminating 3/4 view.
- Do not infer construction from a product name. Record what the source actually shows and what a technical document actually requires.
- Do not repair a surprising measurement until the measurement itself has been tested. Tiny far-from-origin meshes need local-centroid float64 signed-volume arithmetic.
- Receipt validation can run without `--launch`; `--launch` guards only its child render. Direct Blender, MCP, or direct headless output bypasses that launch guard and must be reported as such.

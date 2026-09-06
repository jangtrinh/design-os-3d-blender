---
name: blender-image-to-3d
description: Reconstruct assets in Blender from reference images using only native Blender geometry, local skills, and project workflows; includes fidelity contracts, staged passes, and visual verification.
---

# Image → 3D (v3 — Blender native)

Build from supplied references without new generated/retrieved vendor meshes, hosted model calls, paid credits, or third-party downloads. Load `blender-agent-core` first and use `references/review-rubric.md` for visual verdicts.

## Phase -1 — Fidelity contract

Record before construction:

1. Target use: hero still, turntable, animation, realtime, or print.
2. Observable fidelity target and critical features in each supplied view.
3. Treatment of unseen surfaces: mirrored/plausible inference or more references required.
4. Production constraints: editability, topology, materials, dimensions, and output views.

Do not promise exact hidden geometry from insufficient evidence. Visible reference fidelity has priority.

## Phase 0 — Native reconstruction mode

| Evidence | Native mode | Required gate |
|---|---|---|
| Hard-surface, symmetric, dimensionable | Parametric/data API + mirrored SubD cage | silhouette and edge-control overlays |
| Organic continuous form | Blender sculpt/curve/SubD | multi-view silhouette and curvature review |
| Repeated modular parts | Geometry Nodes or reusable mesh constructors | instance count and transform checks |
| User-selected artifact already stored locally | Frozen scaffold: copy, strip vendor materials, repair/retopo in Blender | provenance, zero-service-call, topology, and visual audit |

If references cannot constrain the requested fidelity, stop at the contract and request the missing views. External generation/retrieval is not a fallback.

## Phase 1 — Evidence specification

- Measure normalized extents and landmark ratios from every reference.
- List critical visible components; every item maps to a named Blender object or surface region.
- Define scene graph, symmetry, units, material groups, cameras, and render outputs.
- Store the plan under `plans/`; build idempotently under `builds/<slug>/`.

## Phase 2 — Staged construction

1. Blockout: primary silhouette, proportions, camera match.
2. Form: shared surfaces, duct/body transitions, bevel hierarchy, panel boundaries.
3. Detail: functional parts, apertures, fasteners, ribbing, seams.
4. Materials: local Blender node materials only; neutral diagnostic lighting first.
5. Polish: production naming, transforms, topology, render settings, outputs.

Use data API/bmesh first. Render and file-save operators are allowed where necessary. Keep components separate when editability or animation requires it.

### Phase 2.5 — Offline retopology gate (frozen scaffold only)

QRemeshify 1.1.0 may be used only when the user selected an already-local scaffold. First create a manifold bounded input with `scripts/prepare-qremeshify-input.py`; then run `scripts/run-qremeshify.py`. The wrapper must pass pinned-library hashes, macOS quarantine approval, a 1k–100k triangle input budget, and a hard wall timeout. For highly fragmented or fused scan/generated scaffolds, start without sharp guidance; dense boundary features can crash the native field stage.

Run `tests/blender/qremeshify-candidate-test.py`, restore/project materials if needed, then render hero and top comparison sheets with `scripts/render-qremeshify-candidate.py`. Accept the candidate only when topology improves without dimension, silhouette, aperture, propeller, or feature loss. Otherwise keep the Blender-native repaired scaffold. Prefer retopology before components are fused; whole-object retopology of a monolithic drone can smooth or tear small mechanics even when numeric topology passes. QRemeshify changes topology; it does not repair inaccurate reference geometry.

## Phase 3 — Verify every pass

Run numeric checks before image checks. Then generate a camera-matched comparison sheet:

```bash
scripts/make-comparison-sheet.sh <reference> <render> <sheet>
```

Choose one verdict: `continue`, `refine-spec`, `refine-code`, `request-input`, or `stop`. Two repeats of the same visible failure require changing the modeling approach, not another parameter tweak.

## Delivery gate

- Deterministic rebuild succeeds twice with stable counts.
- Critical components, transforms, topology, materials, camera framing, and render settings pass automated tests.
- Hero and secondary reference sheets are inspected at output resolution.
- Opposite, underside, and turntable renders expose no missing surfaces or camera failures.
- Report remaining visible deltas and inferred surfaces explicitly; do not inflate fidelity.
- If QRemeshify was used, record version, library hashes, settings, elapsed time, topology metrics, comparison verdict, and fallback result.

No live vendor link may remain in delivery. A user-selected local scaffold must be appended as a copy, repaired into a self-contained asset, provenance-tagged, and verified with `external-service-calls = 0`.

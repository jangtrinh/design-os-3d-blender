---
name: blender-image-to-3d
description: Reconstruct assets in Blender from reference images using only native Blender geometry, local skills, and project workflows; includes fidelity contracts, staged passes, and visual verification.
---

# Image → 3D (v3 — Blender native)

Build from supplied references without new generated/retrieved vendor meshes, hosted model calls, paid credits, or third-party downloads. Load `blender-agent-core` first and use `references/review-rubric.md` for visual verdicts.

## Phase -1 — Pre-Contract Discovery, Multi-Modal Dossier & Socratic Gate (MANDATORY)

Before writing `spec.json` or running any Blender construction pass, execute this 4-step pre-contract sequence (`knowledge/60-pipeline/visual-fidelity-image-to-3d-matching.md` §2):

1. **Phase -1A — Pin Primary Reference Bytes & Internet Datasheet Research (`engineering-research.md`):**
   - Pin all supplied reference images in `builds/<slug>/references/` with SHA-256 hashes recorded in `source-registry.json`.
   - For any mechanical, industrial, or COTS-based product, research the web for manufacturer datasheets and standard part specifications (actuators, gas springs, bearings, fasteners, stroke envelopes) and save `builds/<slug>/engineering-research.md`.
2. **Phase -1B — Super-Detailed Engineering & CMF Prompt (`super-detail-prompt.md`):**
   - Deconstruct every visible and occluded sub-assembly into `builds/<slug>/super-detail-prompt.md`: exact millimeter envelopes, asymmetry (e.g., Double-Y vs X-base, rear-offset column), internal ribs/bosses, coaxial pivot coordinates, kinematic invariants, and OpenPBR CMF parameters.
3. **Phase -1C — 4-Sheet Multi-Modal Technical Dossier (`secondary_generated_sheet`):**
   - Generate and pin the 4 technical dossier sheets in `builds/<slug>/references/` (subordinate to primary photos/CAD in authority, used to resolve occluded angles and assembly hierarchy before modeling):
     1. **4-View Orthographic Blueprint** (`Front, Side, Top, Back` with millimeter bounding dimensions).
     2. **360° Turnaround Sheet** (resolving rear, opposite flank, and underside views).
     3. **Mechanical Exploded View** (discrete sub-assemblies, pins, bushings, and axial assembly vectors).
     4. **Parts Catalog & CMF Matrix Sheet** (knolling layout of all individual parts with IDs, dimensions, and material finishes).
4. **Phase -1D — Socratic Gate with Owner (before locking `master-contract.md` & `spec.json`):**
   - Present the extracted dossier (`super-detail-prompt.md`, `engineering-research.md`, and the 4 technical sheets) and ask the owner (`ask_question`) to confirm:
     1. **Target Purpose (`AGENTS.md` §0b):** `both` (recommended: 3D-printable closed solids + studio media), `print`, or `render-only`.
     2. **Mechanical & Component Scope:** primary structural parts vs full functional mechanical / internal COTS hardware discovery and working kinematics.
     3. **Motion & Media Contract:** frame rate (`30 fps`), distinct rendered states (`<= 120` frames animatic cap), stroke/exploded choreography, and camera views.
   - Lock `builds/<slug>/master-contract.md`, `design-parameters.json`, and `spec.json` only after the Socratic Gate is answered (or explicitly waived by the owner).

For a mechanical or industrial reference, designate one primary view for visible count, facing, placement, and silhouette; use close-ups for local section and construction. Before choosing functional routing, ports, instrument stations, or connection anatomy, read the applicable project drawings or official installation/technical documents. Record whether each rule is a fact, a design choice, or unknown. CAD can support a profile or architecture only when its match and units are recorded; it never establishes identity, dimensions, selection, or compliance by itself.

For a multi-component site, declare one common scale and shared units/axes. Record sourced physical envelopes separately from display envelopes, protrusions and service allowance; mark proxy/analogue dimensions provisional. Name external ports with their elevation, orientation and role, and verify the modules together before final integration. An illustrative scale does not establish equipment selection or capacity.

Do not promise exact hidden geometry from insufficient evidence. Visible reference fidelity has priority.

Pin local reference bytes with source roles before comparison. An original photo,
an owner-supplied dimension, a generated blueprint/360 sheet and a manufacturer
drawing have different authority. Preserve conflicts and label local adaptations;
later generated views cannot authenticate unseen switch, shaft or PCB geometry.
When only inline images are visible, disclose missing byte provenance and obtain
the real file rather than inventing a local path or hash.

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

For a new geometry family, the controller first proves the identity-risk prototype at the target apparent scale. Promote a constructor only after its explicit axes, pivot, ports, accepted parameter range, and regression proof have passed for a second real consumer. Treat an instrument body and its process adapter as separate contracts; a camera-visible head is not placement evidence.

### Phase 2.5 — Offline retopology gate (frozen scaffold only)

QRemeshify 1.1.0 may be used only when the user selected an already-local scaffold. First create a manifold bounded input with `scripts/prepare-qremeshify-input.py`; then run `scripts/run-qremeshify.py`. The wrapper must pass pinned-library hashes, macOS quarantine approval, a 1k–100k triangle input budget, and a hard wall timeout. For highly fragmented or fused scan/generated scaffolds, start without sharp guidance; dense boundary features can crash the native field stage.

Run `tests/blender/qremeshify-candidate-test.py`, restore/project materials if needed, then render hero and top comparison sheets with `scripts/render-qremeshify-candidate.py`. Accept the candidate only when topology improves without dimension, silhouette, aperture, propeller, or feature loss. Otherwise keep the Blender-native repaired scaffold. Prefer retopology before components are fused; whole-object retopology of a monolithic drone can smooth or tear small mechanics even when numeric topology passes. QRemeshify changes topology; it does not repair inaccurate reference geometry.

## Phase 3 — Verify every pass

Run numeric checks before image checks. Then generate a camera-matched comparison sheet:

```bash
scripts/make-comparison-sheet.sh <reference> <render> <sheet>
```

Choose one verdict: `continue`, `refine-spec`, `refine-code`, `request-input`, or `stop`. Two repeats of the same visible failure require changing the modeling approach, not another parameter tweak.

For every declared critical feature, review the primary and supporting views manually at a comparable apparent scale. Name the feature, expected construction layers, source/object/interface, proof shot, and falsifier. A numeric count, clean topology, or an unreadable distant object is not a visual pass. Check risky bores, coplanar joins, fastener families, lettering, dial marks, and specular edges at the final output density before the full batch. Preserve source, camera/settings, and media hashes; a changed source, camera, or resolution invalidates affected proof.

The HQ coverage checker can validate declared receipt bindings with or without `--launch`. Its guarded `--launch` route validates first and then controls only its child render. Direct Blender, MCP, and headless renders bypass that launch guard; record the route accurately and do not imply a universal pre-HQ interception.

For Full HD/social delivery, load `knowledge/60-pipeline/native-render-delivery.md`.
Render the actual saved model. Preflight every shot at final aspect, check curved
metal surfaces and legends at delivery density, and inspect original images plus
decoded animation. A concept-generation image, thumbnail or enlarged screenshot
does not qualify a native Blender render. Changes to normals/materials still
invalidate affected shading and media proofs even when vertices are unchanged.

## Delivery gate

For repeated reference refinement, use the target-bound critic packet in
`knowledge/60-pipeline/native-agent-iteration.md`. Freeze the target/reference,
candidate sources and actual proof captures; ask a separate reviewer for one
PASS/FAIL/UNKNOWN observation and actionable correction per contracted feature.
`scripts/native-review.py` checks the declared evidence bindings and missing
findings. It does not judge images itself or authenticate reviewer independence.
A repeated failed feature calls for a different approach; changing the target
starts a new contract revision. The controlled native coupon illustrates a missing
detail that passes overall dimensions; it is not a general reconstruction benchmark.

Separate contracted feature acceptance from exact likeness. Retain omitted legends,
camera differences, RGB tuning and inferred underside details as visible deltas.
Missing critical evidence remains UNKNOWN; never weaken the rubric after seeing a
failed candidate. A completed still review does not approve unreviewed motion or
the physical/electrical design.

- Deterministic rebuild succeeds twice with stable counts.
- Critical components, transforms, topology, materials, camera framing, and render settings pass automated tests.
- Hero and secondary reference sheets are inspected at output resolution.
- Opposite, underside, and turntable renders expose no missing surfaces or camera failures.
- Report remaining visible deltas and inferred surfaces explicitly; do not inflate fidelity.
- If QRemeshify was used, record version, library hashes, settings, elapsed time, topology metrics, comparison verdict, and fallback result.

No live vendor link may remain in delivery. A user-selected local scaffold must be appended as a copy, repaired into a self-contained asset, provenance-tagged, and verified with `external-service-calls = 0`.

---
name: geometry-diagnostic-workflow
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Diagnose geometry and verifier failures by separating code, specification and checker causes, choosing predicates that match the geometric question, and preserving physical-evidence boundaries.
loads_with: [blender-version-matrix, bpy-scripting-core, agent-workflow-loop]
tags: [geometry, verification, diagnostics, production-gate, bmesh, bvh, tolerance, manufacturing]
id: geometry-diagnostic-workflow
title: "Geometry diagnostic workflow"
when: [geometry-check-disagrees-with-visual, gate-fails-on-valid-mesh, tolerance-extreme-collision, export-roundtrip-mismatch, wall-screen-small-surface, bmesh-crash-lifetime]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Geometry diagnostic workflow

## Purpose

Decide whether a surprising geometry or verifier result is a code, spec or checker fault before changing anything: freeze identity, match the sampling shape to the geometric question, separate contact from positive-volume overlap, test tolerance extremes, and keep physical-evidence claims blocked. Every numeric statement is tied to the repo predicate, test or build record that contains it; none is an external standard.

## When to Use / When NOT

- ALLOWED: a numeric check disagrees with visual evidence, a production gate fails on apparently valid geometry, or a collision appears only at a tolerance extreme — classify the fault as code, spec or checker first.
- ALLOWED: choosing between cardinal probes, angular rays, projection and Exact Boolean volume for a clearance/containment question.
- NOT ALLOWED: first-time print preparation or the unit contract — use `3d-printing`; process wall/overhang minimums — use `dfam-3dprinting-production`.
- NOT ALLOWED: closing physical evidence (preload, thread strip, bearing, lifetime) — use `manufacturing-evidence-workflow`; lowering `min_wall_mm` or weakening a gate to get green is never a diagnosis (AGENTS.md).
- NOT ALLOWED: running a pass pipeline or critic loop — use `native-agent-iteration`.

## Core Knowledge Content

### 1. When to activate this workflow

Use this workflow when a numeric geometry check disagrees with visual evidence, a production gate fails on apparently valid geometry, a collision appears only at a tolerance extreme, an export/reopen comparison changes after tessellation, or a manufacturing interface passes nominal CAD checks but still lacks physical qualification.

The objective is not to make a gate green. The objective is to identify which of three classes is wrong:

1. **code** — the modeled geometry or transform is wrong;
2. **spec** — the declared dimensions, tolerance, load case or manufacturing intent is wrong or incomplete;
3. **checker** — the measurement predicate does not answer the geometric question it claims to answer.

For a surprising result, validate the checker against a known positive and negative control before deciding whether the part is wrong. A correct checker can expose a real geometry defect. Do not weaken a specification just because the current mesh fails it.

### 2. Freeze identity before diagnosis

Record the exact scene, spec/checker source and report hashes before changing anything. Geometry-dependent evidence belongs to that identity only.

Read the saved scene in a disposable Blender process and measure evaluated geometry in world space. For constrained/animated objects, use the evaluated owner's matrix with `bp_core.evaluated_mesh`. The production gate's `meshprep.evaluated_mm_bmesh` evaluates modifiers but currently multiplies by the input object's `matrix_world`; use a verified identity bake for that gate rather than claiming general evaluated-transform parity. <!-- ease:source S14 anchor="evaluated_mesh context manager yields (owner, mesh)" --> <!-- ease:source S3 anchor="evaluated_mm_bmesh: bm.transform(Matrix.Scale(scale,4) @ obj.matrix_world)" -->

If a builder combines several transformed cutters, force dependency-graph/view-layer updates before baking object transforms. A session in this project produced a combined cutter at the origin because freshly assigned locations had not propagated before the transform bake; the resulting gate failure was real evidence about the generated scene, but the root cause was construction code rather than the part specification. <!-- ease:source UNVERIFIED reason="session anecdote (cutter at origin before transform bake) is not recorded in a repo document read in this pass" -->

### 3. Match the sampling shape to the question

A geometric predicate is only as strong as its sampling pattern.

| Question | Appropriate screen | Current implementation/example | Limitation |
|---|---|---|---|
| Is material present around a nominal bore? | cardinal probes around the axis | `features_fasteners.py` uses four axial probes at 90° | four directions do not establish full circumferential support |
| What is a bore diameter/roundness screen? | angular radial rays | 24 directions, three nearby rays per direction, median retained | sampled ring only; local defects between rays remain possible |
| Does an axial feature ray cross a long part? | project vertices onto the feature axis | `_axial_probe_range()` | projection is axis-specific, not a generic clearance proof |
| Does a rectangular or irregular support area exist? | project actual surface/vertices into the relevant plane and test the requested footprint | manual/task-specific | four cardinal rays are not a substitute for area coverage |
| Do two closed parts occupy positive common volume? | Exact Boolean intersection plus signed volume | task-specific mechanical inspectors | coplanar contact is zero volume and must be classified separately |

<!-- ease:source UNVERIFIED reason="Exact Boolean INTERSECT plus signed volume is recommended practice (S17 calc_volume signed); no shipped inspector frozen here" -->

<!-- ease:source UNVERIFIED reason="task-specific projection technique; no frozen implementation cited" -->

<!-- ease:source S1 anchor="_axial_probe_range(bm, center, axis)" -->

<!-- ease:source S1 anchor="RING_RAYS = 24; three samples per direction, median kept" -->

<!-- ease:source S1 anchor="material_around: for k in range(4), ang = pi/2*k, four axial probes" -->

Use cardinal probes for a cardinal question, angular probes for a circular question, and a projected rectangle/polygon for an area question. Do not promote a sparse sample into a claim about the unsampled surface.

The bore ring implementation intentionally offsets directions by half a step and takes three nearby rays because a ray through a tessellated vertex or edge can miss all adjacent triangles numerically. This is a checker robustness technique, not a change to the declared bore tolerance. <!-- ease:source S1 anchor="_ring docstring: three samples inside a small angular window, median, half-step offset" -->

### 4. Derive ray reach from the measured axis

Never choose ray length from the largest global XYZ span when checking an arbitrary feature axis.

`scripts/production_gate/features_fasteners.py::_axial_probe_range()` projects every evaluated vertex relative to the feature center onto the feature axis. It uses the resulting minimum and maximum plus an approach margin to choose origin and reach. <!-- ease:source S1 anchor="_axial_probe_range projects vertices onto feature axis; AXIAL_APPROACH_MM = 10.0" -->

This change was required after a long-span part exposed a false failure: a thin plate could be much wider than the fixed ray cap even though the checked hole was through the thin axis. The generic regression is:

```bash
python3 tests/production-gate/test_large_span_features.py -v
```

The positive fixture is a 284 mm × 92 mm × 4 mm plate with a Z-axis through hole. The control fixture fills the hole and must still fail the bore predicate. <!-- ease:source S6 anchor="target_dims_mm [284.0, 92.0, 4.0]; plate(length=284,width=92,thick=4)" -->

### 5. Separate surface contact from positive-volume overlap

BVH triangle overlap is useful for surface intersection, but it does not by itself classify containment or intended coplanar mating. <!-- ease:source S16 anchor="BVHTree.overlap" -->

For collision screening in the keyboard task, `builds/reference-keyboard/scripts/inspect_fit.py::_intersects()` uses three layers: <!-- ease:source S4 anchor="_intersects: no_common_z, triangle_surface_intersection, a/b_sample_inside_or_contact" -->

1. reject pairs with no common Z extent;
2. detect triangle-surface overlap with BVHs;
3. sample vertices and triangle centroids, then use multi-ray parity to distinguish inside/contact from outside.

That is stronger than endpoint-only or nearest-normal checks, but it remains sampled containment.

When the engineering question is “do these closed solids share positive volume?”, use an `EXACT` Boolean `INTERSECT` on a disposable copy and calculate signed volume of the result. This catches same-Z/interior overlap that an AABB-only screen can miss. <!-- ease:source UNVERIFIED reason="Exact INTERSECT + signed volume is a recommended technique; no shipped receipt in this pass" --> <!-- ease:source S17 anchor="BMesh.calc_volume(signed=True) may return negative values" -->

Do not treat zero Exact-intersection volume as “no relationship.” Two parts may intentionally touch on a plane. This project observed PCB/support and collar/mating surfaces with zero volumetric penetration but coplanar contact. Contact, clearance and interference are three different states. <!-- ease:source UNVERIFIED reason="zero-volume coplanar contact observation lives in local plans/reports and runs, not shipped docs" -->

### 6. Test tolerance extremes, not only nominal values

If a source dimension is `nominal ± tolerance`, include the relevant extremes in digital motion/clearance tests.

The keyboard switch source specified nominal total travel 3.0 mm with a 0.2 mm tolerance (worst-case maximum 3.2 mm). The final travel diagnostic therefore sampled: <!-- ease:source S9 anchor="total_travel_mm nominal 3.0, tolerance 0.2, worst_case_max 3.2" -->

`0, 0.5, 1, 1.5, 2, 2.5, 3.0, 3.2 mm`. <!-- ease:source S10 anchor="samples = sorted(set((*nominal_samples, 3.2)))" --> <!-- ease:source UNVERIFIED reason="the exact seven nominal values come from inspect_fit._contracts(), not read in this pass; S8 confirms eight samples through 3.2 mm" -->

The C03 saved-scene diagnostic checked all 58 keys at all eight travel samples and retained a deliberately invalid negative control at 6 mm. This is stronger than re-running the nominal 3.0 mm endpoint. <!-- ease:source S8 anchor="all 58 caps clear at eight sampled travels through 3.2 mm; 6.0 mm overtravel control still detects collision" -->

For a real physical component, do not force hardware past its actual hard stop just because the drawing tolerance permits a theoretical maximum. Use a separate tolerance fixture/gauge when necessary and measure the real part's bottom-out independently.

### 7. Diagnose small-surface wall screens without weakening the wall spec

The production wall screen triangulates the evaluated BMesh and casts a ray from each selected face centroid along the reverse normal. A sample is accepted only when the hit normal opposes the source normal (`hit_normal.dot(face_normal) < -0.5`). <!-- ease:source S2 anchor="_wall_sample_details: triangulate, ray from face centre along -normal, hit accepted when hn.dot(n) < -0.5" -->
Primary mode retains `MIN_FACE_AREA_MM2 = 0.3`. <!-- ease:source S2 anchor="MIN_FACE_AREA_MM2 = 0.3" -->
The reusable fallback in `scripts/production_gate/walls_overhang.py` activates only when **zero** nondegenerate triangles meet that primary threshold. It then samples every positive-area triangle with the same ray predicate. <!-- ease:source S2 anchor="mode all-positive-faces-fallback only when primary list is empty" -->
It does not:

- lower `min_wall_mm`;
- change the opposing-normal acceptance condition;
- reduce segmentation of the source geometry;
- make empty or degenerate meshes pass.

The regression command is:
```bash
python3 tests/production-gate/test_small_surface_walls.py -v
```
The test contains a 96-segment thick annulus that must pass, a thin annulus that must fail, empty and degenerate meshes that must fail, and a coarse control that must remain on the original threshold path. <!-- ease:source S7 anchor="_annulus_bmesh(radial_wall_mm, height 1.6, outer radius 4.4, segments=96)" -->
The checker records its sampling mode and active area threshold in the measured result so downstream review can distinguish primary and fallback coverage. <!-- ease:source S2 anchor="details: wall_sampling_mode, wall_face_area_threshold_mm2" -->

### 8. Keep BMesh owners alive while iterating

Blender Python wrappers can reference C-side BMesh data whose owner has already been freed or garbage-collected. Never iterate `temporary_bmesh().faces` when the temporary owner is not retained.

This project produced a Blender crash in a regression test with exactly that pattern. The fix was to store the triangulated BMesh in a variable, read its faces while the owner remained alive, then call `.free()` explicitly. <!-- ease:source S11 anchor="Temporary BMesh owner was lost inside a generator expression; hold and free the allocation" -->

Treat a native crash as an execution failure until the crash stack identifies whether production code or the test fixture owned the invalid lifetime.

### 9. Do not equate triangulation identity with vertex identity

Exports may split or reorder vertices while preserving the same triangle surface.

`builds/reference-keyboard/scripts/export_compare.py` therefore compares evaluated world-space surfaces rather than raw vertex indices: <!-- ease:source S5 anchor="TRI_QUANT_MM = 1e-5; _triangles quantised correspondence" -->

1. compare triangle counts and bounding boxes;
2. try quantized triangle-coordinate correspondence at `1e-5 mm`; <!-- ease:source S5 anchor="TRI_QUANT_MM = 1e-5" -->
3. if correspondence is unavailable, sample up to 500 triangle centroids in both directions and measure nearest-surface distance with BVHs. <!-- ease:source S5 anchor="MAX_SAMPLES = 500; _sample_surface returns triangle centroids; _nearest_stats via find_nearest" -->

Triangle-coordinate correspondence is appropriate when the two triangulated surfaces are the same even if indices differ.

The BVH fallback is a sampled bidirectional distance, not a Hausdorff proof. It can miss small localized defects between sampled triangles. Keep that limitation in the report. <!-- ease:source S5 anchor="limits: Sampled bidirectional distance is not a full Hausdorff proof" -->

### 10. Interpret thread geometry at the correct manufacturing state

A pilot-hole wall is not the final threaded wall.

For a cylindrical post with outside radius `R`:
- pre-tap pilot radial wall = `R - pilot_diameter/2`;
- final nominal major-thread radial wall = `R - major_thread_diameter/2`.
In the keyboard mechanical prototype, a 2.5 mm OD post with a 1.30 mm pilot showed about 0.60 mm wall in the mesh screen, while the analytical M1.6 major diameter leaves only about 0.45 mm nominal radial material after tapping. <!-- ease:source S9 anchor="outer_diameter_mm 2.5; tap_drill_diameter_mm 1.30; pre_tap_pilot_radial_wall_mm 0.60" --> <!-- ease:source S9 anchor="thread M1.6x0.35; derived: 1.25 - 0.8 = 0.45 mm (arithmetic, not a measured wall)" -->

The production gate can prove the modeled pilot geometry. It cannot prove thread strip torque, thread form, surface condition or post strength after machining. Keep those as physical evidence requirements.

### 11. Geometry support is not preload, bearing or strength evidence

Finding a support shoulder or adding a compression collar closes a nominal load path in geometry. It does not prove preload or bearing performance.

The acrylic-retention investigation ray-probed the actual mating surface around each chassis axis. Only discrete angular sectors retained the upper shoulder; other sectors were lowered by a PCB rebate. A collar could be modeled on the surviving shoulder and checked for zero positive-volume overlap, but the digital model still could not establish: <!-- ease:source S15 anchor="_support_angles: ray_cast probes around the axis at listed angles" -->
- uniform bearing stress;
- manufactured surface flatness;
- preload after tolerance stack-up;
- acrylic creep/thermal expansion;
- plate deflection;
- clamp torque.

These remain first-article/bench requirements even when topology, clearances and nominal contact geometry pass.

### 12. Failure classification and next action

| Evidence | Classification | Action |
|---|---|---|
| Exact overlap or invalid topology on the intended part | code | change geometry/construction and invalidate dependent evidence |
| Geometry matches source, but declared requirement is contradicted or incomplete | spec | revise the contract first; new revision invalidates old acceptance |
| Known-good and known-bad fixtures show the predicate is wrong | checker | repair predicate with positive + negative controls; do not weaken product geometry/spec |
| Sparse screen passes but the claim requires continuous/whole-area coverage | missing evidence | add a stronger predicate or narrow the claim |
| Digital contact/load path exists but physical response is unknown | physical blocker | prototype and measure; keep manufacture blocked |

Two failed attempts at the same diagnostic step should change the approach class. Examples: surface BVH → Exact intersection volume; cardinal probes → angular ring; global span → axis projection; nominal endpoint → tolerance-extreme sweep.

### 13. Generic commands to run after checker changes

Use the smallest regression that exercises the changed predicate first:

```bash
python3 tests/production-gate/test_gate_predicates.py -v
python3 tests/production-gate/test_large_span_features.py -v
python3 tests/production-gate/test_small_surface_walls.py -v
```

Then let the owning integration flow rerun its bound production gate. Do not rebuild a product scene merely to test a checker change when the saved scene is the intended immutable fixture.

For an existing report and exported parts, audit recorded completeness with <!-- ease:source S12 anchor="production-gate.py --audit-report <existing-gate.json>" -->
`production-gate.py --audit-report` as documented in `specs/README.md`. This host
route requires positive per-part wall limits and passing non-skipped results,
the exact declared part set, correctly owned feature checks, current scene/spec
hashes and matching STL/roundtrip byte receipts. It does not rerun Blender.
A globally green report cannot supply a missing wall result on another part.
Unsupported feature types remain incomplete; unowned required feature names fail.

The audit is not a geometric remeasurement or report-authentication system. It <!-- ease:source S13 anchor="Production coverage: audit automates recorded coverage, not source authenticity or engineering adequacy" -->
retains original sampling limits and manufacturing blockers. Verify that the
declared part/feature list actually covers the intended product; a twelve-family <!-- ease:source S11 anchor="final 12-family spec" -->
spec does not cover every assembly object. Reuse is limited to the pinned inputs.

### 14. Useful falsifiers

- A bore check passes when the hole is filled.
- A radial ring reports fewer than all required directions but still returns a diameter pass.
- A long thin part fails because the axial ray starts outside a fixed reach derived from another axis.
- A wall screen passes an empty or zero-area-only mesh.
- The small-surface fallback activates even though at least one face meets the primary area threshold.
- A collision screen reports “disjoint” while an Exact intersection has positive volume.
- Coplanar contact is reported as positive-volume interference.
- A 3.0 mm nominal motion pass is presented as evidence for a 3.2 mm tolerance maximum without testing 3.2.
- A pilot-hole wall measurement is cited as final thread wall or thread-strength evidence.
- A nominal support contact is cited as proof of preload, creep, thermal or bearing strength.
- An export pass relies only on vertex indices after a format is allowed to split vertices.
- A sampled BVH comparison is described as exhaustive surface equivalence.

### 15. Runtime enforcement versus manual discipline

**Runtime today:** evaluated mesh geometry with the declared transform/bake scope; topology checks; feature-axis projection; 24-ray bore screen; four-side material screen; wall threshold/fallback metadata; production-gate spec/hash binding; task-specific keyboard multi-ray travel diagnostics; task-specific export surface comparison.

The explicit coverage-audit route additionally enforces per-declared-part report
completeness and current export bindings. It leaves generic partial diagnostic
behavior unchanged and never grants physical manufacturing acceptance.

**Manual today:** deciding that the sample pattern matches the claim; escalating to Exact volume for ambiguous contact/containment; choosing tolerance extrema; deciding whether evidence from an unchanged dependency can be reused; distinguishing pilot from finished thread geometry; keeping support/bearing/preload/strength claims blocked until physical evidence exists.

### 16. Source and evidence availability

- `scripts/production_gate/meshprep.py`
- `scripts/production_gate/features_fasteners.py`
- `scripts/production_gate/walls_overhang.py`
- `scripts/production_gate/topology.py`
- `tests/production-gate/test_gate_predicates.py`
- `tests/production-gate/test_large_span_features.py`
- `tests/production-gate/test_small_surface_walls.py`
- `builds/reference-keyboard/scripts/inspect_fit.py`
- `builds/reference-keyboard/scripts/export_compare.py`
- `builds/reference-keyboard/manufacturing/mechanical/acrylic_retention.py`

The listed implementation/tests are source files. Detailed mechanical, small-wall
and collar session reports under `plans/260917-keyboard-manufacturing/reports/`
and product `runs/` are local history, not shipped public evidence. The public
summary is `docs/ck-001-session-retrospective.md`. None is an external standard or
a certificate of physical manufacture.

## Failure Modes (Mandatory)

- **A long thin part fails the bore check although the hole is fine** — cause: axial ray length derived from the largest global XYZ span instead of the feature axis — fix: project vertices onto the feature axis (`_axial_probe_range`); regression `test_large_span_features.py` (284 x 92 x 4 mm plate).
- **Wall screen fails on a finely tessellated closed ring although the wall is thick** — cause: no triangle reaches the primary 0.3 mm^2 area threshold, so zero samples — fix: the bounded all-positive-faces fallback with the same opposing-normal ray predicate; never lower `min_wall_mm`; regression `test_small_surface_walls.py`.
- **Disjoint verdict while the solids share volume (or a coplanar contact is reported as interference)** — cause: BVH surface overlap and sampled parity cannot classify containment/contact exactly — fix: Exact Boolean `INTERSECT` on a disposable copy plus signed volume; classify contact, clearance and interference separately.
- **Nominal travel passes but the tolerance maximum collides** — cause: only the nominal endpoint was swept (3.0 mm presented as covering 3.2 mm) — fix: sample nominal intermediates plus the worst-case maximum and keep an overtravel negative control (S8: 58 caps, eight travels, 6 mm control).
- **Blender crashes inside a regression fixture iterating `temporary_bmesh().faces`** — cause: the temporary BMesh owner was lost, so the wrapper points at freed C data — fix: hold the BMesh in a variable, read while it lives, then `.free()` explicitly; treat the crash as an execution failure until the stack names the owner.

## Sources

- [S1] Repo: scripts/production_gate/features_fasteners.py (RING_RAYS=24, three-ray median, four axial probes, _axial_probe_range) — scripts/production_gate/features_fasteners.py — captured 2026-10-13 — sha256 dc01148370ad6ae8c78ab8c65900409e504d095ed7e45e823f4ed70a68f610ad
- [S2] Repo: scripts/production_gate/walls_overhang.py (MIN_FACE_AREA_MM2=0.3, fallback, opposing-normal ray predicate) — scripts/production_gate/walls_overhang.py — captured 2026-10-13 — sha256 488c61bf10979a47074a94c61d56ad72f2bb69b51abd4a06bfa54e59096a9f4f
- [S3] Repo: scripts/production_gate/meshprep.py (evaluated_mm_bmesh multiplies obj.matrix_world) — scripts/production_gate/meshprep.py — captured 2026-10-13 — sha256 c75f0725a7222557c079bed0527583af440760c9d44708c95d735f6740e042a4
- [S4] Repo: builds/reference-keyboard/scripts/inspect_fit.py (_intersects: Z-overlap, BVH overlap, sampled parity) — builds/reference-keyboard/scripts/inspect_fit.py — captured 2026-10-13 — sha256 13d512c94843ef3583aaacacf3fd554d06baa1b3f116deacfcc7a694af16fa71
- [S5] Repo: builds/reference-keyboard/scripts/export_compare.py (TRI_QUANT_MM=1e-5, MAX_SAMPLES=500, sampled bidirectional distance) — builds/reference-keyboard/scripts/export_compare.py — captured 2026-10-13 — sha256 906a0cbfb1a196c469c0f38bc45bd3ef5c2ce978e7dc87b35ddcb913b24be6cf
- [S6] Repo: tests/production-gate/test_large_span_features.py (284 x 92 x 4 mm plate) — tests/production-gate/test_large_span_features.py — captured 2026-10-13 — sha256 01774639f20a361bcabcb6b7ff44656383b90fbfb5b886506a39119714895712
- [S7] Repo: tests/production-gate/test_small_surface_walls.py (96-segment annulus fixtures) — tests/production-gate/test_small_surface_walls.py — captured 2026-10-13 — sha256 f3fa0c23e4fcf4a36a536228456d1b8e856b40ffbeaa7f95bd2bb7078fc804d3
- [S8] Repo: builds/reference-keyboard/manufacturing/README.md (58 caps, eight travels through 3.2 mm, 6 mm control) — builds/reference-keyboard/manufacturing/README.md — captured 2026-10-13 — sha256 bf8bf8a6ca1f4c4246e8b652a3f5a946ad355c9ed646ebd803fd736fe1c9a0e6
- [S9] Repo: builds/reference-keyboard/manufacturing/mechanical-requirements.json (travel 3.0 +-0.2 mm, 2.5 mm post, 1.30 mm pilot, 0.60 mm pilot wall) — builds/reference-keyboard/manufacturing/mechanical-requirements.json — captured 2026-10-13 — sha256 6770b0ee0572eec4d271235350957df693adf505d75f1c12a1627290ddac415c
- [S10] Repo: builds/reference-keyboard/manufacturing/qualification/travel_maximum.py (samples = nominal samples plus 3.2 mm) — builds/reference-keyboard/manufacturing/qualification/travel_maximum.py — captured 2026-10-13 — sha256 25a0ddd1aff5ed57baf353f0d68c742b82140b8e08e1fa81a30954cc444d2b94
- [S11] Repo: docs/ck-001-session-retrospective.md (BMesh owner lifetime lesson, 12-family spec, tolerance-extreme lesson) — docs/ck-001-session-retrospective.md — captured 2026-10-13 — sha256 9b3a2cfedbb2fe84af493543b55d03282513a870d36d9e74f37585d3e4950c4e
- [S12] Repo: specs/README.md (production-gate.py --audit-report route) — specs/README.md — captured 2026-10-13 — sha256 6c032881cd113f59cdba8a37a871b73db0bf9b97327de32c17e64ec920e1cc84
- [S13] Repo: AGENTS.md (production coverage audit scope, failure map) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7
- [S14] Repo: scripts/agent_verify/inspect_scene.py (evaluated_mesh context manager) — scripts/agent_verify/inspect_scene.py — captured 2026-10-13 — sha256 49a1534b4dfb97169c768ce3c320e1d5d46f516ea935475090f376b92d9284b5
- [S15] Repo: builds/reference-keyboard/manufacturing/mechanical/acrylic_retention.py (_support_angles ray probes) — builds/reference-keyboard/manufacturing/mechanical/acrylic_retention.py — captured 2026-10-13 — sha256 7cbf629b80062055e59575c6a0c3e79e4d304f338c5498a97ca502a05051fd5e
- [S16] mathutils.bvhtree — BVHTree overlap, ray_cast, find_nearest (Blender API current) — https://docs.blender.org/api/current/mathutils.bvhtree.html — captured 2026-10-13 — sha256 ab5d8dd9e0e67bec21fbbc828dee03c72071eab2941f658d309a39b3e681c1bd — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bvhtree.html`
- [S17] bmesh.types — BMesh.calc_volume(signed) (Blender API current) — https://docs.blender.org/api/current/bmesh.types.html — captured 2026-10-13 — sha256 38bc14776291a14763af56ce8565b300c5b7dbd348a3382f8ddcad599371294f — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bmesh-types.html`

---
name: geometry-diagnostic-workflow
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Diagnose geometry and verifier failures by separating code, specification and checker causes, choosing predicates that match the geometric question, and preserving physical-evidence boundaries.
loads_with: [blender-version-matrix, bpy-scripting-core, agent-workflow-loop]
tags: [geometry, verification, diagnostics, production-gate, bmesh, bvh, tolerance, manufacturing]
---

# Geometry diagnostic workflow

## 1. When to activate this workflow

Use this workflow when a numeric geometry check disagrees with visual evidence, a production gate fails on apparently valid geometry, a collision appears only at a tolerance extreme, an export/reopen comparison changes after tessellation, or a manufacturing interface passes nominal CAD checks but still lacks physical qualification.

The objective is not to make a gate green. The objective is to identify which of three classes is wrong:

1. **code** — the modeled geometry or transform is wrong;
2. **spec** — the declared dimensions, tolerance, load case or manufacturing intent is wrong or incomplete;
3. **checker** — the measurement predicate does not answer the geometric question it claims to answer.

For a surprising result, validate the checker against a known positive and negative control before deciding whether the part is wrong. A correct checker can expose a real geometry defect. Do not weaken a specification just because the current mesh fails it.

## 2. Freeze identity before diagnosis

Record the exact scene, spec/checker source and report hashes before changing anything. Geometry-dependent evidence belongs to that identity only.

Read the saved scene in a disposable Blender process and measure evaluated geometry in world space. For constrained/animated objects, use the evaluated owner's matrix with `bp_core.evaluated_mesh`. The production gate's `meshprep.evaluated_mm_bmesh` evaluates modifiers but currently multiplies by the input object's `matrix_world`; use a verified identity bake for that gate rather than claiming general evaluated-transform parity.

If a builder combines several transformed cutters, force dependency-graph/view-layer updates before baking object transforms. A session in this project produced a combined cutter at the origin because freshly assigned locations had not propagated before the transform bake; the resulting gate failure was real evidence about the generated scene, but the root cause was construction code rather than the part specification.

## 3. Match the sampling shape to the question

A geometric predicate is only as strong as its sampling pattern.

| Question | Appropriate screen | Current implementation/example | Limitation |
|---|---|---|---|
| Is material present around a nominal bore? | cardinal probes around the axis | `features_fasteners.py` uses four axial probes at 90° | four directions do not establish full circumferential support |
| What is a bore diameter/roundness screen? | angular radial rays | 24 directions, three nearby rays per direction, median retained | sampled ring only; local defects between rays remain possible |
| Does an axial feature ray cross a long part? | project vertices onto the feature axis | `_axial_probe_range()` | projection is axis-specific, not a generic clearance proof |
| Does a rectangular or irregular support area exist? | project actual surface/vertices into the relevant plane and test the requested footprint | manual/task-specific | four cardinal rays are not a substitute for area coverage |
| Do two closed parts occupy positive common volume? | Exact Boolean intersection plus signed volume | task-specific mechanical inspectors | coplanar contact is zero volume and must be classified separately |

Use cardinal probes for a cardinal question, angular probes for a circular question, and a projected rectangle/polygon for an area question. Do not promote a sparse sample into a claim about the unsampled surface.

The bore ring implementation intentionally offsets directions by half a step and takes three nearby rays because a ray through a tessellated vertex or edge can miss all adjacent triangles numerically. This is a checker robustness technique, not a change to the declared bore tolerance.

## 4. Derive ray reach from the measured axis

Never choose ray length from the largest global XYZ span when checking an arbitrary feature axis.

`scripts/production_gate/features_fasteners.py::_axial_probe_range()` projects every evaluated vertex relative to the feature center onto the feature axis. It uses the resulting minimum and maximum plus an approach margin to choose origin and reach.

This change was required after a long-span part exposed a false failure: a thin plate could be much wider than the fixed ray cap even though the checked hole was through the thin axis. The generic regression is:

```bash
python3 tests/production-gate/test_large_span_features.py -v
```

The positive fixture is a 284 mm × 92 mm × 4 mm plate with a Z-axis through hole. The control fixture fills the hole and must still fail the bore predicate.

## 5. Separate surface contact from positive-volume overlap

BVH triangle overlap is useful for surface intersection, but it does not by itself classify containment or intended coplanar mating.

For collision screening in the keyboard task, `builds/reference-keyboard/scripts/inspect_fit.py::_intersects()` uses three layers:

1. reject pairs with no common Z extent;
2. detect triangle-surface overlap with BVHs;
3. sample vertices and triangle centroids, then use multi-ray parity to distinguish inside/contact from outside.

That is stronger than endpoint-only or nearest-normal checks, but it remains sampled containment.

When the engineering question is “do these closed solids share positive volume?”, use an `EXACT` Boolean `INTERSECT` on a disposable copy and calculate signed volume of the result. This catches same-Z/interior overlap that an AABB-only screen can miss.

Do not treat zero Exact-intersection volume as “no relationship.” Two parts may intentionally touch on a plane. This project observed PCB/support and collar/mating surfaces with zero volumetric penetration but coplanar contact. Contact, clearance and interference are three different states.

## 6. Test tolerance extremes, not only nominal values

If a source dimension is `nominal ± tolerance`, include the relevant extremes in digital motion/clearance tests.

The keyboard switch source specified nominal total travel 3.0 mm with a +0.2 mm upper tolerance. The final travel diagnostic therefore sampled:

`0, 0.5, 1, 1.5, 2, 2.5, 3.0, 3.2 mm`.

The C03 saved-scene diagnostic checked all 58 keys at all eight travel samples and retained a deliberately invalid negative control at 6 mm. This is stronger than re-running the nominal 3.0 mm endpoint.

For a real physical component, do not force hardware past its actual hard stop just because the drawing tolerance permits a theoretical maximum. Use a separate tolerance fixture/gauge when necessary and measure the real part's bottom-out independently.

## 7. Diagnose small-surface wall screens without weakening the wall spec

The production wall screen triangulates the evaluated BMesh and casts a ray from each selected face centroid along the reverse normal. A sample is accepted only when the hit normal opposes the source normal.
Primary mode retains `MIN_FACE_AREA_MM2 = 0.3`.
The reusable fallback in `scripts/production_gate/walls_overhang.py` activates only when **zero** nondegenerate triangles meet that primary threshold. It then samples every positive-area triangle with the same ray predicate.
It does not:

- lower `min_wall_mm`;
- change the opposing-normal acceptance condition;
- reduce segmentation of the source geometry;
- make empty or degenerate meshes pass.

The regression command is:
```bash
python3 tests/production-gate/test_small_surface_walls.py -v
```
The test contains a 96-segment thick annulus that must pass, a thin annulus that must fail, empty and degenerate meshes that must fail, and a coarse control that must remain on the original threshold path.
The checker records its sampling mode and active area threshold in the measured result so downstream review can distinguish primary and fallback coverage.

## 8. Keep BMesh owners alive while iterating

Blender Python wrappers can reference C-side BMesh data whose owner has already been freed or garbage-collected. Never iterate `temporary_bmesh().faces` when the temporary owner is not retained.

This project produced a Blender crash in a regression test with exactly that pattern. The fix was to store the triangulated BMesh in a variable, read its faces while the owner remained alive, then call `.free()` explicitly.

Treat a native crash as an execution failure until the crash stack identifies whether production code or the test fixture owned the invalid lifetime.

## 9. Do not equate triangulation identity with vertex identity

Exports may split or reorder vertices while preserving the same triangle surface.

`builds/reference-keyboard/scripts/export_compare.py` therefore compares evaluated world-space surfaces rather than raw vertex indices:

1. compare triangle counts and bounding boxes;
2. try quantized triangle-coordinate correspondence at `1e-5 mm`;
3. if correspondence is unavailable, sample up to 500 triangle centroids in both directions and measure nearest-surface distance with BVHs.

Triangle-coordinate correspondence is appropriate when the two triangulated surfaces are the same even if indices differ.

The BVH fallback is a sampled bidirectional distance, not a Hausdorff proof. It can miss small localized defects between sampled triangles. Keep that limitation in the report.

## 10. Interpret thread geometry at the correct manufacturing state

A pilot-hole wall is not the final threaded wall.

For a cylindrical post with outside radius `R`:
- pre-tap pilot radial wall = `R - pilot_diameter/2`;
- final nominal major-thread radial wall = `R - major_thread_diameter/2`.
In the keyboard mechanical prototype, a 2.5 mm OD post with a 1.30 mm pilot showed about 0.60 mm wall in the mesh screen, while the analytical M1.6 major diameter leaves only about 0.45 mm nominal radial material after tapping.

The production gate can prove the modeled pilot geometry. It cannot prove thread strip torque, thread form, surface condition or post strength after machining. Keep those as physical evidence requirements.

## 11. Geometry support is not preload, bearing or strength evidence

Finding a support shoulder or adding a compression collar closes a nominal load path in geometry. It does not prove preload or bearing performance.

The acrylic-retention investigation ray-probed the actual mating surface around each chassis axis. Only discrete angular sectors retained the upper shoulder; other sectors were lowered by a PCB rebate. A collar could be modeled on the surviving shoulder and checked for zero positive-volume overlap, but the digital model still could not establish:
- uniform bearing stress;
- manufactured surface flatness;
- preload after tolerance stack-up;
- acrylic creep/thermal expansion;
- plate deflection;
- clamp torque.

These remain first-article/bench requirements even when topology, clearances and nominal contact geometry pass.

## 12. Failure classification and next action

| Evidence | Classification | Action |
|---|---|---|
| Exact overlap or invalid topology on the intended part | code | change geometry/construction and invalidate dependent evidence |
| Geometry matches source, but declared requirement is contradicted or incomplete | spec | revise the contract first; new revision invalidates old acceptance |
| Known-good and known-bad fixtures show the predicate is wrong | checker | repair predicate with positive + negative controls; do not weaken product geometry/spec |
| Sparse screen passes but the claim requires continuous/whole-area coverage | missing evidence | add a stronger predicate or narrow the claim |
| Digital contact/load path exists but physical response is unknown | physical blocker | prototype and measure; keep manufacture blocked |

Two failed attempts at the same diagnostic step should change the approach class. Examples: surface BVH → Exact intersection volume; cardinal probes → angular ring; global span → axis projection; nominal endpoint → tolerance-extreme sweep.

## 13. Generic commands to run after checker changes

Use the smallest regression that exercises the changed predicate first:

```bash
python3 tests/production-gate/test_gate_predicates.py -v
python3 tests/production-gate/test_large_span_features.py -v
python3 tests/production-gate/test_small_surface_walls.py -v
```

Then let the owning integration flow rerun its bound production gate. Do not rebuild a product scene merely to test a checker change when the saved scene is the intended immutable fixture.

## 14. Useful falsifiers

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

## 15. Runtime enforcement versus manual discipline

**Runtime today:** evaluated mesh geometry with the declared transform/bake scope; topology checks; feature-axis projection; 24-ray bore screen; four-side material screen; wall threshold/fallback metadata; production-gate spec/hash binding; task-specific keyboard multi-ray travel diagnostics; task-specific export surface comparison.

**Manual today:** deciding that the sample pattern matches the claim; escalating to Exact volume for ambiguous contact/containment; choosing tolerance extrema; deciding whether evidence from an unchanged dependency can be reused; distinguishing pilot from finished thread geometry; keeping support/bearing/preload/strength claims blocked until physical evidence exists.

## 16. Source and evidence availability

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

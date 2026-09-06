# W3 — production contract + gate (implementation report)

**Conclusion (FACT).** The gate exists, is enforceable by code, and is revision-bound.
`python3 -m unittest discover -s tests/production-gate -v` → **19 tests, OK, 11.1 s**.
Positive fixture → exit 0 with a one-STL manifest carrying sha256; each negative
fixture → the documented nonzero code with the expected `failed[]` entry and the
expected failing check name. Every report states in `exclusions[]` and
`coverage.unchecked[]` what it did not prove.

## Deliverables

| Path | What |
|---|---|
| `specs/build-spec.schema.json` | v1 contract, every field documented, required vs optional explicit |
| `specs/README.md` | how to write a spec before detailing + the proves / does-NOT-prove table |
| `specs/examples/bracket-m3.spec.json` | matches the positive fixture exactly |
| `scripts/production-gate.py` | host entry (124 lines); validates, hashes, launches isolated Blender, prints summary + sentinel, exits 0/1/2/3 |
| `scripts/production_gate/` | `spec, meshprep, topology, dimensions, walls_overhang, features_fasteners, fastener_tables, export_roundtrip, report, run_in_blender` — all ≤ 170 lines |
| `tests/production-gate/` | `make_fixtures.py` (9 fixtures from primitives), `fixture_specs.py`, `gate_harness.py`, `test_gate_contract.py`, `test_gate_predicates.py` |

Frozen interfaces honoured: CLI shape, exit codes 0/1/2/3, sentinel as last stdout
line, report fields `schema_version, inputs{scene_sha256, spec_sha256}, checker{version,
blender}, units, parts[…], failed[], exclusions[], coverage{checked, unchecked},
timestamp`, spec v1 field names, predicate module names.

## Promoted predicates (source cited, nothing weakened)

| Promoted from | What was taken | Where it lives now |
|---|---|---|
| `knowledge/60-pipeline/3d-printing.md` `print_audit` | depsgraph-evaluated mesh, `bm.transform(matrix_world)`, non-manifold / non-contiguous / wire / loose / zero-area, BVH self-overlap minus face-adjacent pairs, shell flood fill, signed volume | `topology.py`, `meshprep.evaluated_mm_bmesh` |
| `builds/robot-arm-print-assembly/scripts/audit-meshes.py` | wall ray screen from face centroids along `-normal`, accepted only on opposing hit normal; 0.3 mm² area floor; `min` and `p01` reporting | `walls_overhang.wall_samples` |
| `builds/robot-arm-reference-v2/verify-fit-coupon.py` | STL round trip in an isolated process, ray-cast surface measurement (bore clear ⇒ no axial hit; seat depth from first hit), bbox dimension asserts | `export_roundtrip.py`, `features_fasteners.py`, `dimensions.bbox_checks` |
| `builds/robot-arm-v2-engineered/export-prototype-parts.py` | hand-written binary STL (80-byte header + `<12fH` per triangle) in mm, sha256 manifest, "not manufacturing approved" wording | `export_roundtrip.write_stl` / `manifest` |
| `scripts/verify-3dprint-tolerances.py` | overhang area share vs build axis; `HEATSET_SPECS` pilot/depth/boss table | `walls_overhang.overhang_checks`, `fastener_tables.HEATSET` |
| `scripts/boilerplates/cad_mechanics/bp_fasteners_iso.py` | ISO metric fastener table shape (that file has **no** clearance-hole data, so ISO 273 / ISO 4762 head / DIN 974-1 rows were added and each carries an explicit `table_source` string) | `fastener_tables.py` |

Deliberately **not** promoted: the reference audits' `remove_doubles` /
`dissolve_degenerate` / `recalc_face_normals` clean-up before counting. The gate must
report the mesh it was given, not a silently repaired one.

## Verification performed (runtime, not recall)

- **API probe before writing anything** (Blender 5.2.0 LTS): `wm.stl_export` /
  `wm.stl_import` property lists (`global_scale`, `use_scene_unit`, `forward_axis`,
  `up_axis`, `apply_modifiers` all present), `BMEdge.is_contiguous`,
  `BVHTree.FromBMesh(...).overlap`, 4-tuple `ray_cast`, `unit_settings` = METRIC /
  1.0, `wm.read_homefile(use_empty=True)` → `{'FINISHED'}` with 0 objects.
  `bmesh.ops.intersect_boolean` does **not** exist in 5.2 — fixtures use the Boolean
  modifier under `temp_override` instead.
- **Falsification of the bore measurement:** known Ø3.4 and Ø5.0 bores measured
  3.400 and 5.000 within 0.05 mm (`test_known_diameters_within_0_05_mm`). On the
  example part: 3.397 / 3.397 / 3.9965 mm (errors 0.003 / 0.003 / 0.0035 mm).
- **Falsification of self-intersection:** two overlapping boxes welded into one mesh
  → flagged `fail` while `non_manifold_edges` stays `pass`; a 64×24 torus → `pass`.
- **Determinism attack:** two runs on identical inputs produce byte-identical reports
  except `timestamp` and `duration_s` (asserted in test).
- **Revision binding attack:** changing one field of the spec changes
  `inputs.spec_sha256` while `scene_sha256` is unchanged (asserted).
- **Input attacks:** unknown `--parts` id → 2; spec part with no `target_dims_mm` → 2
  (message names the field); object absent from the scene → 2; missing scene → 2;
  a Blender that prints no sentinel → 3.
- **Real bug found and fixed at root cause, not patched around:** a radial ray aimed
  exactly at a bore vertex is rejected by both adjacent triangles and flies on to the
  outer wall, inflating Ø3.4 to 4.09 mm. Fix: ring directions offset by half a step
  and each direction sampled three times inside a small angular window, keeping the
  **median** — one degenerate sample per direction cannot move the result, and a
  genuinely oval bore still shows its full spread. Documented in the code.

## check → what it proves → what it does NOT prove

| Check | Proves | Does NOT prove |
|---|---|---|
| `non_manifold_edges` / `non_contiguous_edges` / `wire_edges` / `loose_verts` / `zero_area_faces` | closed, consistently wound, no degenerate elements — a slicer can read it | correctness of the shape, printability, strength |
| `self_intersection_pairs` | no two non-adjacent triangles overlap | wall soundness; report capped at 200 pairs |
| `shells` | the declared number of separate closed surfaces | that they are the right ones |
| `signed_volume_positive` | outward normals, enclosed volume | any dimensional or structural property |
| `bbox_dims_mm` | world bbox within tolerance of the declared size | interior geometry — a bbox is three numbers |
| `scale_applied` | object scale is 1,1,1 so local data equals world geometry | anything else — but without it correct world dims can hide a wrong mesh |
| `scene_unit_system` / `scene_scale_length` | "mm" in the report really is mm | — |
| `wall_thickness_screen` | **SCREEN**: no sampled centroid found material thinner than `min_wall_mm` | not exhaustive — unsampled regions and faces < 0.3 mm² are invisible |
| `overhang_area_pct` | **SCREEN**: area share facing within `max_overhang_deg` of build-down | not a printability verdict; no bridging/support/slicer model |
| `feature_*_bore_clear` | the axial probe passes through (or reaches a blind floor) | hole position relative to anything else |
| `feature_*_diameter_mm` | modelled bore diameter at `center_mm`, verified to 0.05 mm | printed diameter (FDM comes out undersize); roundness away from `center_mm` |
| `feature_*_depth_mm` | depth from entry surface to first axial hit | thread engagement, insert seating |
| `feature_*_material_around` | material on four sides just outside the bore | adequate edge distance under load |
| `feature_*_fastener_table` | the **declared** diameter equals the published table value, `table_source` named | that the measured hole matches the table (separate check), or that a fastener fits |
| `roundtrip_*` | the exported STL re-imports as one object and re-measures identically | slicer acceptance |

Structural exclusions repeated in every report: load capacity, print success,
assembly fit, thermal/creep, surface finish and shrinkage, plus every declared
`load_case` and `physical_evidence` item — all "not evaluated".

## Timings (macOS, Blender 5.2.0 LTS, Cycles not used)

| Step | Time |
|---|---|
| Full gate run, 1 part, with `--export-dir` (incl. Blender startup) | **0.54 s** (repeat 0.55 s) |
| Predicate work inside Blender (`report.duration_s`) | 0.018 s |
| Fixture generation, 9 `.blend` files, one Blender process | ≈ 2 s |
| `python3 -m unittest discover -s tests/production-gate` (19 tests, 21 Blender launches) | **11.1 s** |

## NOT verified

- No physical part was printed, measured, fitted, torqued or loaded. Every claim in
  this report is digital.
- 3MF is not produced: Blender 5.2 has no native 3MF exporter and no new dependency
  was allowed. STL in mm is the only export path.
- `boss` and `slot` feature types are accepted by the schema but **not measured** in
  v1; they are reported `skip` and listed in `coverage.unchecked`.
- Blind-hole depth measurement is implemented and unit-shaped but exercised only by a
  through-hole fixture set; no fixture in this suite declares `depth_mm`. Treat
  `feature_*_depth_mm` as UNVERIFIED until a blind-hole fixture exists.
- Counterbore / ISO 4762 head and DIN 974-1 rows are loaded and cited but no check
  consumes them yet — only clearance and heat-set pilot lookups are wired in.
- Multi-part scenes are supported by the code path but every fixture has one part;
  multi-part behaviour is INFERENCE, not FACT.
- The overhang screen was never falsified against a hand-computed value; it is a
  direct promotion of the existing implementation.
- Non-axis-aligned (`axis` as an arbitrary vector) features are implemented but only
  the `"z"` form is covered by tests.

## Unresolved questions

1. Should `overhang_area_pct` become a hard gate by default (spec would need a
   default `max_overhang_area_pct`), or stay informational until someone has a
   printed part to calibrate it against?
2. The wall screen's 0.3 mm² face-area floor is inherited from the arm audit. On
   small parts that threshold may skip real thin features — should it scale with part
   size rather than being a constant?
3. `required_checks` currently matches check names literally. Do we want globs
   (`feature_*_diameter_mm`) so a spec cannot silently miss a renamed check?
4. Should the gate refuse a spec whose `physical_evidence` list is empty, on the
   grounds that a part with no owed physical trial is a part nobody intends to make?
5. Heat-set M3 wants 7.0 mm of depth; the example part is a 6.0 mm plate. The gate
   reports this as `info` because no `depth_mm` is declared. Should a declared
   heat-set fastener force `depth_mm` to be mandatory (exit 2 when absent)?

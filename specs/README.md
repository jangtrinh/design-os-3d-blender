# Build specs and the production gate

A build spec is the **contract you write before you model the detail**. It says
what the physical part must measure. `scripts/production-gate.py` then reads a
`.blend` and answers one question with an exit code: *does this geometry satisfy
that contract?*

The spec exists to stop the failure this repository has already paid for: a
scene that looks right, is committed, and only later turns out to be the wrong
size, unprintable, or missing a hole. Media that "looks right" is not acceptance.

## Read this first: what a PASS is, and is not

A green gate is **digital evidence about the checks actually run**. It is not
manufacturing approval. Topology and declared dimensions are checked; unlisted
features are not. Wall and overhang settings can be omitted for partial diagnostic
work, and STL roundtrip runs only when `--export-dir` is supplied. Read the per-part
results and coverage before claiming any of those outcomes.

It proves **nothing** about:

- load capacity, stiffness, or fatigue — no FEA, no coupon, no test rig;
- print success — no slicer is run; supports, adhesion, warping, bridging and
  per-printer shrinkage are all outside the gate;
- assembly fit — no mating part is checked for interference or clearance;
- thermal behaviour, creep, chemical resistance, surface finish;
- whether a real screw or heat-set insert actually goes in.

Every report repeats this in `exclusions[]`, and every unmeasured thing is
listed in `coverage.unchecked[]`. If a claim is not in `coverage.checked[]`, the
gate did not make it.

## Writing a spec

1. Write the spec **before** detailing. Start from
   `specs/examples/bracket-m3.spec.json`.
2. `units` must be `"mm"`. Every number in the file is millimetres.
3. Every part needs `id`, `object` (the exact Blender object name),
   `target_dims_mm` and `tol_mm`. A part with no target dimensions is a broken
   contract and the gate refuses to run (exit 2), on purpose: it will not
   pretend to gate a part nobody dimensioned.
4. Declare the printability envelope you actually care about: `min_wall_mm`,
   `orientation_up`, `max_overhang_deg`, and — if you want the overhang figure
   to be a gate rather than a note — `max_overhang_area_pct`.
5. List every bore that matters under `features`. **A feature you do not list is
   not measured.** Give `fastener` when the diameter comes from a standard; the
   gate then also checks the declared diameter against the published table and
   prints the `table_source` it used.
6. Put the trials you still owe in `physical_evidence`, and any load case in
   `load_cases`. The gate never evaluates them; it copies them into
   `exclusions[]` so the gap stays visible in the record.
7. Name non-negotiable checks in `required_checks`. If a name never runs anywhere,
   the gate fails. This field is aggregated across parts; it does not require that
   every part ran that check. Use the explicit audit below for per-part recorded coverage.

The generic schema intentionally supports partial diagnostics and does not require
`min_wall_mm`. For the project's print/both completion procedure, every applicable
production part must nevertheless have an independently authored positive wall
limit and an actual passing `wall_thickness_screen` result. The same per-part
review applies to required features and exports. Removing a requirement to bypass
a failure is not an acceptable diagnostic or release procedure. A waiver for a
stage remains visible and does not remove physical manufacturing requirements.

The field-by-field contract is `specs/build-spec.schema.json`; it is the single
source of truth and `scripts/production_gate/spec.py` validates against it.

## Running the gate

```bash
python3 scripts/production-gate.py \
  --scene path/to/part.blend \
  --spec  specs/examples/bracket-m3.spec.json \
  --report out/gate-report.json \
  [--parts bracket-m3] [--export-dir out/stl]
```

Exit codes: `0` pass · `1` a requirement failed (`report.failed[]`) · `2`
invalid or incomplete input · `3` execution error. The last stdout line is
always `AGENT_OK <json>` or `AGENT_FAIL <json>`.

The gate never touches your open Blender session: it launches its own
`--factory-startup -b` process, and that process is disposable because the
export round trip wipes the file it runs in. The report records the sha256 of
both the scene and the spec, so a result is bound to exactly the revision that
produced it.

`--export-dir` writes one binary STL per part **in millimetres** plus a
`manifest.json` with sha256, triangle count and measured dimensions, and turns
on the round-trip audit: the STL is re-imported by Blender's own reader and
re-measured, so an export bug cannot hide behind a passing in-scene check.

## What each check proves — and does not

### Audit existing coverage without rebuilding

After the geometry gate has exported and reimported the declared parts:

```bash
python3 scripts/production-gate.py \
  --audit-report out/gate-report.json \
  --scene path/to/part.blend \
  --spec path/to/build.spec.json \
  --export-dir out/stl \
  --report out/coverage-audit.json
```

This route uses host Python only. It reads existing evidence and writes one new
report; it neither starts Blender nor changes the original report, scene or STLs.
`--parts` is not allowed: all parts in the supplied spec must appear exactly once
in the report and export manifest, with matching objects and current byte hashes.

Every declared part needs a positive authored wall limit, actual passing wall
samples, topology/dimensions/units/scales/bed screens, declared feature checks and
STL roundtrip results. Declared overhang limits must pass too. Additional generic
`required_checks` apply per part. Explicit `feature_*` names require declared owners
and apply to those parts only. Unsupported boss/slot measurements and skipped
fastener-table checks remain incomplete. Legitimate informational exclusions, such
as unconfigured overhang or no declared features, are retained rather than hidden.

Exit 0 produces `PASS_DECLARED_PART_COVERAGE`; exit 1 produces
`INCOMPLETE_DECLARED_PART_COVERAGE`; invalid input or an existing output path returns
2. The output must be new and outside the original export directory. It records
the source checker version, current auditor source hashes and all inspected input
pins. Original checker code is not retrospectively authenticated by these hashes.

The audit checks raw source bounds where available. The original v1 roundtrip
report retains four-decimal display bounds only; their half-unit reporting interval
is checked for consistency without tightening the original geometry tolerance.
This does not re-measure the STL. Its current bytes must match both the manifest
and the original roundtrip receipt, including binary-STL length and triangle count.

**Trust and scope:** no report-only audit can authenticate a fabricated report,
establish missing design requirements, or prove that representative parts exhaust
the assembly. It audits declared coverage, not all geometry, physics or a machine
process. `manufacture` remains `BLOCKED` even when this audit passes. Keep actual
source review, visual judgment and physical qualification separate.

### Geometry predicates

| Check | Proves | Does NOT prove |
|---|---|---|
| `non_manifold_edges`, `non_contiguous_edges`, `wire_edges`, `loose_verts`, `zero_area_faces` | The surface is closed, consistently wound and free of degenerate elements — a slicer can interpret it | That the shape is correct, printable, or strong |
| `self_intersection_pairs` | No two non-adjacent triangles overlap: no hidden interpenetrating solid | Nothing about wall soundness; the BVH test is capped at 200 reported pairs |
| `shells` | The part is the declared number of separate closed surfaces | That the shells are the *right* ones |
| `signed_volume_positive` | Normals point outward and the solid encloses volume | Any dimensional or structural property |
| `bbox_dims_mm` | The world-space bounding box matches the declared size within tolerance | That interior geometry is right — a bounding box is three numbers |
| `scale_applied` | Object scale is 1,1,1, so local mesh data equals world geometry | Nothing else; but without it, correct world dimensions can hide a mesh that exports wrong |
| `scene_unit_system`, `scene_scale_length` | Millimetres in the report mean millimetres | — |
| `wall_thickness_screen` | **SCREEN.** Opposing-normal rays from sampled centroids meet the declared wall limit | Not exhaustive: primary selection uses faces at least 0.3 mm²; only an empty primary set enables the all-positive-face fallback in 1.0.2. Mixed-size faces can leave thin regions unsampled |
| `overhang_area_pct` | **SCREEN.** The share of surface area facing within `max_overhang_deg` of build-down | Not a printability verdict — bridging, support generation and slicer settings are not modelled |
| `feature_*_bore_clear` | The axial probe passes through a through hole, or reaches the floor of a blind one | That the hole is in the right place relative to anything else |
| `feature_*_diameter_mm` | The modelled bore measures that diameter at `center_mm` (median-filtered radial rays, verified to 0.05 mm against known 3.4 and 5.0 mm bores) | Printed diameter — FDM holes come out undersize; nothing about roundness away from `center_mm` |
| `feature_*_keyed_flat_mm` | For a D-hole (`keyed_flat_mm` + `keyed_flat_dir` declared): the axis-to-flat distance from the rays that land on the flat; the diameter check then uses the round part only | Orientation of the flat relative to the mating shaft |
| `feature_*_depth_mm` | Depth from the entry surface to the first axial hit | Thread engagement or insert seating |
| `feature_*_material_around` | Material exists on four sides just outside the bore | Adequate edge distance for a load |
| `feature_*_fastener_table` | The **declared** diameter matches the published table value (`table_source` names it) | That the measured hole matches the table — that is the separate diameter check — or that the fastener fits |
| `roundtrip_*` | The exported STL re-imports as one object and re-measures identically | Slicer acceptance |
| `bed_fit_footprint_mm` | **SCREEN.** Sorted footprint (plus brim margin) fits within usable bed X/Y: `min(footprint_xy) < min(bed_xy - 2*brim)` and `max(footprint_xy) < max(bed_xy - 2*brim)`. 90° in-plane rotation is allowed (slicer may swap X/Y) | That a diagonal or off-centre placement is possible; that the part will adhere; that supports will fit |
| `bed_fit_height_mm` | **SCREEN.** Part height (Z axis) fits within bed Z dimension: `height < bed_z` | Print success, bridging, slicing behaviour, or support clearance |
| `bed_fit_volume_source` | **INFO.** `print_volume_mm` resolved from part override, spec-level declaration, or default `[256, 256, 256]` (X1C/P1S/A1 shared bed) | — |
| `bed_fit_a1_mini_compatible` | **INFO.** Part footprint (plus brim margin) and height also fit within A1 mini bed `[180, 180, 180]` mm. Informational only; **never fails the gate** | Actual A1 mini print success or compatibility with other machines |

Tables in use: ISO 273 clearance holes, ISO 4762 socket-head cap screw heads,
DIN 974-1 counterbores, and the CNC Kitchen / Ruthex heat-set insert table
promoted from `scripts/verify-3dprint-tolerances.py`. A size absent from a table
is reported as unchecked, never guessed.

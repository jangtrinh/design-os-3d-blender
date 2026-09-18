# DC01 P03 print kit

This package contains the 18 print parts from frozen I06, their gated STL exports,
and two geometry-only core 3MF plates. The files preserve the authored dimensions
and wall limits. Physical manufacturing remains **BLOCKED**.

| Deliverable | Result |
|---|---|
| Native print geometry | 18/18 form, wall, declared feature and STL roundtrip checks PASS |
| Declared-part coverage |PASS_DECLARED_PART_COVERAGE |
| PETG plate | 17 parts, 113,602 triangles |
| TPU 95A prototype plate | One diaphragm, 2,540 triangles |
| Package reopening |All local triangles exactly match the gated STL coordinates; closed edges, winding, volumes, dimensions and placements PASS |
| Source preservation | All 18 native vertex/polygon fingerprints match I06 after the declared signed-axis rotations |
| Media | Two reviewed 512 px native verification views; Full HD delivery belongs to the separate presentation package |
| Motion and assembled fit |Separate frozen I06 evidence; the plate checks make no new motion or assembled-fit claim |
| Manufacturing process |No slicer, supports, printer profile, G-code or physical printing performed |

## Files to open

- `plates/plate-01-PETG.3mf`: 17 separate PETG objects on the declared 256 × 256 mm bed.
- `plates/plate-02-TPU.3mf`: one TPU diaphragm on its own 256 × 256 mm bed.
- `gated-stl/`: 18 individually named millimetre STL files and their hash manifest.

`print.blend` contains the active `DC01_PRINT_LAYOUT` scene with 18 print-oriented
meshes. Those meshes retain their original datum, so they are not arranged as a
bed layout in that scene. Their separate plate translations are in
`orientation.json`; the 3MF build items contain the usable per-plate placements.
Do not print the source-only scene or add the original rotation a second time.

## Print preparation

Open each 3MF as geometry at 100% scale and check that it contains 17 PETG objects
or one TPU object. Assign the matching material using the actual printer and
filament profiles. No profile is embedded. The authored 0.4 mm nozzle and 0.2 mm layer
values are prototype assumptions, not a validated machine setup.

Retain the supplied orientation while evaluating supports and the first layer.
The compact plate is a placement proposal: check support and brim footprints in
the selected slicer and rearrange objects when those footprints require more
room. The rigid PETG parts have nominal 7 mm separation. Plate placement does not
establish that overhangs, thin contact areas or bridges will print successfully.

Individual STLs use millimetres and are already rotated for the proposed print
direction. Drop each imported STL to the bed and arrange it as needed; do not
scale it to fit. Select the TPU material separately for `DC01_BUTTON_DIAPHRAGM`.
Review any automatic mesh repair before accepting it because modified geometry
is outside the recorded gate and hash evidence.

Before using a printed assembly, establish the physical fit, retention and
material/process results that remain open in the source evidence. TPU button
force, return, fatigue and safe switch overtravel remain unmeasured.

## Checks that should reject a damaged package

Reject missing or duplicate build items, altered STL/3MF hashes, a TPU part
placed 280 mm outside its own plate, or any changed local triangle coordinates.
The independent checker detected a missing item, an introduced 280 mm offset and
a 0.1 mm vertex displacement in disposable copies of the parsed package.

Reject a displayed scale or part size inconsistent with `spec.json`. The TPU
diaphragm should be 32 × 14 × 7.85 mm in its print orientation. The lower shell is
80.4 × 64 × 62 mm. The original PETG 2.0 mm and TPU 1.2 mm wall requirements remain in the
spec; no wall requirement was relaxed to obtain a pass.

## Measured placement and evidence

PETG occupied bounds are `(8,8,0)` to approximately
`(243.800005,150.600002,62.000004) mm`. The minimum measured axis gap is
`6.999996573 mm`; the independent comparison records a 0.00005 mm placement epsilon.
TPU occupied bounds are `(8,8,0)` to approximately `(40,22,7.850000381) mm`.
This epsilon applies only to floating-point placement comparisons, not the
authored wall or dimension requirements.

`final-gate.json` and `coverage-audit.json` bind the print scene, spec and STL
bytes. `source-to-print.json` binds every native print part to I06.
`package-manifest.json` binds the source, requirements, 18 STLs and two 3MF files.
`package-check.json` records independent ZIP/XML/STL reopening and the three
falsifiers. `handoff.json` and `SHA256SUMS` freeze the delivered file set.

`verification/plate-01-PETG.png` was viewed at its original 512 px size: all 17
separate object silhouettes are present, with visible gaps and no obvious
overlap. Small keeper details are below reliable visual metrology at that scale.
`verification/plate-02-TPU.png` shows the complete diaphragm, raised button and
both mounting holes. Numerical evidence establishes placement; these views do
not prove first-layer contact, supports or slicer readiness.

## Source identity

After extracting the archive, verify the frozen files from the `DC01-P03` folder:

```bash
shasum -a 256 -c SHA256SUMS
```

I06 assembly SHA256:
`37e66375aa4b158b42ebe2031b60330e27c32f0eb3c91bf45d5ce61783d215b1`

I06 authored spec SHA256:
`de02529f524aba173d040a4e43d45b55f74bc77feb0afe85ce143b0900d0ea2b`

P03 native print scene SHA256:
`8bd48a75877127596f8ce70742301ef36921801b952ee1ada215b825e345b6de`

P03 transformed spec SHA256:
`609214e082e338bffd2b8547ebed9eebd435a17de35e0411f6ac7f96d9cec746`

The source-spec copy and source handoff are retained in `source/`. I06, its
electronics and the shared checkers were not modified during packaging.

Core 3MF implementation reference: 3MF Consortium Core Specification 1.4.0,
sections 3.3, 3.4.3 and Appendix C, inspected 2026-09-18:
https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md

The package uses separate translation-only build items and preserves local
mesh coordinates exactly. This is a bounded implementation and independent
geometry check, not a 3MF conformance certificate or slicer interoperability test.

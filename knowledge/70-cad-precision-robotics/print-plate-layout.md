---
name: print-plate-layout
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Laying printable parts out on build plates — default beds, material/process buckets, spacing and margin, guillotine free-rectangle packing, per-part orientation, STL per plate.
loads_with: [polymer-3dprinting-cad, 3d-printing, export-interchange]
tags: [3d-printing, print-plates, nesting, packing, orientation, stl]
id: print-plate-layout
title: "Print-Plate Layout: Buckets, Packing and Orientation"
when: [print-plate-layout, material-bucket-plates, guillotine-packing, part-orientation, stl-per-plate]
trust_tier: draft
sources_checked: 2026-10-13
---

# Print-Plate Layout: Buckets, Packing and Orientation

## Purpose
Turns a set of printable parts into plates: bucket by material and process, orient each part, then pack rectangles and export one file per plate. Design-reference note, not certification: a packed plate proves arrangement only, never manifoldness, wall thickness, fit or strength.

## When to Use / When NOT
- ALLOWED: preparing plates for a finished build where each plate is one machine run with one material and process
- ALLOWED: auditing a layout manifest for margin, overflow and part count
- NOT ALLOWED: hole oversize, chamfers, inserts and wall rules — use `polymer-3dprinting-cad` instead
- NOT ALLOWED: manifold checks and STL/3MF export mechanics — use `3d-printing` instead
- NOT ALLOWED: production DFAM review with measured gates — use `dfam-3dprinting-production` instead

## Core Knowledge Content

### 1. Mental model

A finished printable build is not a folder of loose STLs — it is a small set of **plates**, each one a single
machine run with one material, one process and one exposure/temperature profile. Layout is therefore three
decisions taken in this order, and only the third one is packing:

1. **Bucket** the parts by material + process. A bucket never shares a plate with another bucket.
2. **Orient** each part for supports, surface finish and load direction. Orientation fixes the 2D footprint.
3. **Pack** the resulting rectangles onto the bucket's plate, opening a new plate when the rest does not fit.

Doing this in the other order (pack first, orient later) invalidates every placement, because rotating a part
changes the footprint the packer just placed. Layout is also **not** a substitute for the final gate: a packed
plate proves arrangement, never manifoldness, wall thickness or fit.

### 2. Decision first

| Question | Default | Where it comes from |
| :--- | :--- | :--- |
| FDM bed | **256 × 256 × 256 mm** (Bambu X1C/P1S class) — **ASSUMPTION** | owner printers unknown; recompute when named | <!-- ease:source UNVERIFIED reason="printer class naming not checked against vendor spec; repo value 256 x 256 mm is in S1 PLATE_SIZES" -->
| Resin bed | **218 × 123 × 220 mm** (Elegoo Saturn-4-Ultra 12K class) — **ASSUMPTION** | 16K variant is 211.7 × 118.4; recompute when named | <!-- ease:source UNVERIFIED reason="printer class naming not checked; repo value 218 x 123 mm is in S1 PLATE_SIZES" -->
| Smaller-bed alternatives | Prusa MK4S 250 × 210 · Bambu A1 mini 180 × 180 · Elegoo Mars 5 143 × 90 · Anycubic Photon Mono M7 223 × 126 | all **ASSUMPTION** until the owner names a machine | <!-- ease:source UNVERIFIED reason="vendor spec pages not captured; research report absent" -->
| Part spacing | **6 mm** between inflated rectangles | PrusaSlicer/OrcaSlicer auto-arrange default | <!-- ease:source S1 anchor="SPACING_MM = 6.0; the slicer-default origin is UNVERIFIED (research report absent)" -->
| Plate margin | **8 mm**, shrinkable and *reported* (see R3) | `ww_plates.py::MARGIN_MM` | <!-- ease:source S1 anchor="MARGIN_MM = 8.0" -->
| Rotation freedom | **0° / 90° only** | keeps the footprint a rectangle; no free-angle nesting | <!-- ease:source S1 anchor="pack_shelf docstring: 0/90 rotation only" -->
| Export | **one STL per plate**, parts pre-placed | Blender 5.2 has no native 3MF (§7) | <!-- ease:source S2 anchor="per-plate "stl" and "stl_sha256" fields" -->

**Bed sizes above are ASSUMPTIONS, not measurements.** They are the largest common consumer footprints, chosen so
the packer never has to reject a part. Re-run the layout with the real bed the moment the owner names a printer —
a 180 × 180 A1 mini or a 143 × 90 Mars 5 changes plate count, not just spacing.

Repo proof that these defaults are per-build: the robot-arm build assumed a **220 × 220 mm** bed with a **7 mm** edge margin and **8 mm** part gap (S3, S4), while the watch-winder build used 256 × 256 mm, 8 mm margin and 6 mm spacing (S1, S2).

### 3. Rules

R1. Bucket by **material + process**, never mix buckets on one plate. <!-- ease:source S1 anchor="BUCKETS: fdm-petg, fdm-abs, fdm-tpu, sla-proxy, sla-clear" -->
    Why: different nozzle/bed temperatures, chamber requirements, resins and exposure times. The watch-winder
    capsule uses five buckets — `fdm-petg`, `fdm-abs`, `fdm-tpu`, `sla-proxy`, `sla-clear`
    (`builds/watch-winder-capsule/scripts/ww_plates.py::BUCKETS`).
    Violation: a plate that physically cannot be printed in one run.

R2. Orient before packing; record the orientation as an explicit rotation, never as "as modelled".
    Why: the packer consumes the XY bbox produced by the orientation. An orientation decided afterwards
    silently invalidates every placed rectangle.
    Violation: overlapping parts, or supports discovered after the plate is exported.

R3. Margin may shrink, but a reduced margin must be **reported**, never applied silently. <!-- ease:source S2 anchor="sla-proxy-01 margin_mm 5.5, margin_reduced true, margin_requested_mm 8.0" -->
    Why: when a part is wider than `plate − 2·margin`, the honest response is the largest margin that still fits
    (`ww_plates.py::effective_margin`), recorded as `margin_reduced: true` with `margin_requested_mm` beside it.
    In the watch-winder run the 112 mm `front_rim` on the 123 mm resin axis forced 8.0 → **5.5 mm**.
    Violation: a plate that the owner believes has 8 mm of clearance and does not.

R4. A part that does not fit the plate **at all** raises — it is a spec problem, not a layout problem.
    Why: opening a new plate for an oversize part hides the fault and produces an unprintable STL.
    Violation: an "arranged" plate whose part is off the bed.

R5. Overflow is returned, never hidden. <!-- ease:source S1 anchor="pack_shelf returns (placements, overflow)" -->
    Why: `pack_shelf` returns `(placements, overflow)`; the caller opens the next plate for the overflow or
    reports it. Dropping the overflow list is how a part disappears between layout and export.
    Violation: a plate manifest with fewer parts than the build has.

### 4. Recipe: the packer that actually ran

**Guillotine free-rectangle bin pack, 0/90 rotation, stdlib only (no scipy)** — <!-- ease:source S1 anchor="pack_shelf docstring" -->
`builds/watch-winder-capsule/scripts/ww_plates.py::pack_shelf`:

- inflate each item by `spacing` on its +x/+y sides;
- place it into the free rectangle with the **best short-side fit** (ties broken by the long side);
- **split** the used rectangle into a right and a top remainder along the *shorter* leftover axis, so the larger
  remainder stays whole; then drop free rectangles fully contained in another.

This is what fills the strip beside a tall part. A plain shelf packer cannot, and that is not theory: the first <!-- ease:source UNVERIFIED reason="the 1.6 percent shelf-packer result is historical and not preserved in the repo; final utilisations are in S2" -->
watch-winder resin plate came out at **1.6 % utilisation** with a shelf packer. The guillotine packer on the same
parts gives 6 plates at **30.6 / 25.8 / 4.3 / 59.7 / 34.4 / 40.3 %** <!-- ease:source S2 anchor="utilisation_pct 30.6/25.79/4.34/59.73/34.37/40.34" -->
(`builds/watch-winder-capsule/plates/manifest.json`). Low utilisation is acceptable when one part dominates a
bucket (the 4.3 % TPU plate) — it is not acceptable when it is an artifact of the packer.

Do not copy pseudocode from research into the build: implement it, run it on the real footprints, and read the
utilisation and `overflow` before believing it.

#### Per-part orientation

Orientation is a per-part decision with a written reason, not a global setting. The heuristics that recur:

| Shape | Orientation | Why |
| :--- | :--- | :--- |
| Domed shell with a flat rim | **rim-down** | uses its own flat rim as the base; pole-down needs full-hemisphere support on a visible surface. Large flat PETG footprint → brim against warping | <!-- ease:source UNVERIFIED reason="orientation reasons come from the absent research report" -->
| Cup / open cavity | **mouth-up** | no support trapped inside an unremovable cavity | <!-- ease:source UNVERIFIED reason="orientation reasons come from the absent research report" -->
| Turned or knurled cylinder | **axis vertical** | round layers, knurl pitch resolved along Z; horizontal prints faceted | <!-- ease:source UNVERIFIED reason="orientation reasons come from the absent research report" -->
| Thin disc / tab | **flat-down** | trivially printable, no supports | <!-- ease:source UNVERIFIED reason="orientation reasons come from the absent research report" -->
| Large flat or hollow resin part | **tilt 12–30°** | breaks the flat plane against FEP suction and lets resin drain (12° rim, 17° relief plate, 25° dome in the watch-winder run) | <!-- ease:source S1 anchor="ORIENTATIONS: front_rim 12.0, guilloche 17.0, visor 25.0 degrees" -->

The full 20-row table with per-part reasoning and sources lives in <!-- ease:source UNVERIFIED reason="referenced report not found in the repo" -->
`plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md` §"Per-part table" — link it, do not
copy it. Every row there is standard practice cross-referenced against sources, **not** a print-verified result
for that geometry.

### 5. Anti-patterns & Traps

1. **Adopting packer pseudocode verbatim from research.** Research sketches are unmeasured. Implement, run,
   read the utilisation. *Fix:* treat a packer as code under test, with `check_placements` and a utilisation number.
2. **Hiding an overflow** (or a reduced margin) to make a run look clean. *Fix:* both belong in the manifest.
3. **Compensating an undersized FDM hole in the model** because the plate is being prepared anyway. Hole
   shrinkage is corrected after a physical fit trial, or by the DFAM oversize rules in
   `polymer-3dprinting-cad.md` — never by an ad-hoc edit at layout time.
4. **Treating a passing SLA proxy as evidence for the metal part.** A grey-resin stand-in proves shape and fit
   only; load, wear and strength stay unproven and the build README must say so.
5. **Modelling the tilt into the exported geometry.** See §7.

### 6. Production edge cases

*   **Tilt and supports are slicer-side.** The manifest records `recommended_tilt_deg` and a `supports_note`;
    `ww_plates.py` applies only the 0/90 rotation that the footprint depends on. Baking a 25° tilt into the STL
    would make the exported part disagree with `spec.json` and with every gate report bound to it.
*   **No native 3MF in Blender 5.2.** 3MF exists only as a community extension, so **one STL per plate** with <!-- ease:source UNVERIFIED reason="Blender 5.2 core 3MF support not verified here; see `3d-printing`" -->
    parts pre-placed as transformed copies needs no new dependency and matches
    `scripts/production-gate.py --export-dir`, which already writes per-part STL in mm with a manifest.
    Per-plate 3MF is a later nice-to-have that costs an install. (Updated 2026-10-13: the robot-arm build already ships per-plate core 3MF written with stdlib zip/XML, no extension, from checked STL bytes (S4, S5); the claim that 3MF needs an install is therefore not required for core 3MF.)
*   **Layout does not clear the final gate.** Plates are arrangement evidence. Manufacture stays BLOCKED until <!-- ease:source S6 anchor="gate verdict is from production-gate.py, not from layout" -->
    the gate report and the physical evidence the build's purpose requires exist.

### 7. Verification & diagnostics

```python
def check_placements(plate, spacing):
    """After packing one bucket: every part inside the plate, no pair closer than `spacing`."""
    x0, y0 = 0.0, 0.0
    pw, ph = plate["size_mm"]
    boxes = [(p["position_mm"][0], p["position_mm"][1], *p["bbox_mm"][:2]) for p in plate["parts"]]
    for x, y, w, h in boxes:
        assert x0 <= x and y0 <= y and x + w <= pw and y + h <= ph, "part outside the plate"
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            gap_x = max(a[0] - (b[0] + b[2]), b[0] - (a[0] + a[2]))
            gap_y = max(a[1] - (b[1] + b[3]), b[1] - (a[1] + a[3]))
            assert max(gap_x, gap_y) >= spacing - 1e-6, "parts closer than the spacing"
```

Numeric checks that must pass before a plate is called done: `overflow == []`; part count on plates equals the
build inventory; every `margin_reduced: true` carries `margin_requested_mm`; the per-plate STL re-imports at the
right scale in mm; utilisation recorded per plate (a suspiciously low number means the packer, not the parts).

### 8. Sources & References

- `plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md` (not present in the repository on 2026-10-13; its claims are UNVERIFIED here) — 19 cited sources: bed sizes
  (Bambu, Prusa, Elegoo, Anycubic spec pages), PrusaSlicer/OrcaSlicer 6 mm arrange spacing, Formlabs SLA
  orientation and drain-hole guidance, PETG warping, absence of 3MF in core Blender.
- `builds/watch-winder-capsule/scripts/ww_plates.py` — the packer that ran: `BUCKETS`, `PLATE_SIZES`,
  `effective_margin`, `pack_shelf`, `pack_bucket`, `check_placements`.
- `builds/watch-winder-capsule/plates/manifest.json` — measured result: 6 plates, spacing 6 mm, resin margin
  reduced to 5.5 mm, per-plate utilisation.
- `knowledge/70-cad-precision-robotics/polymer-3dprinting-cad.md` — DFAM rules (holes, chamfers, inserts,
  wall thickness). This note owns plates, packing and orientation only.
- `specs/README.md`, `scripts/production-gate.py` — what a gate report does and does not prove.

## Failure Modes (Mandatory)
- **Part count on plates is below the build inventory** — cause: overflow list dropped after packing — fix: caller opens the next plate or reports overflow (R5, S1)
- **Owner believes 8 mm clearance but the plate has 5.5 mm** — cause: margin silently shrunk to fit a 112 mm part on a 123 mm axis — fix: record `margin_reduced: true` with `margin_requested_mm` (S1, S2)
- **Plate layout is correct for one printer and wrong for another** — cause: bed size is a per-build assumption: 256 x 256 mm / 8 mm margin / 6 mm spacing in the watch-winder build vs 220 x 220 mm / 7 mm / 8 mm in the robot-arm build (S1-S4) — fix: re-run layout with the named printer
- **Very low plate utilisation** — cause: shelf packing leaves strips beside tall parts — fix: guillotine free-rectangle packing; check the reported utilisation (S2)
- **Exported part disagrees with its spec** — cause: a slicer-side tilt was baked into the STL — fix: record `recommended_tilt_deg` in the manifest only (S1)

## Sources
- [S1] Repo: watch-winder plate packer (BUCKETS, PLATE_SIZES, effective_margin, pack_shelf, check_placements, ORIENTATIONS) — builds/watch-winder-capsule/scripts/ww_plates.py — captured 2026-10-13 — sha256 aae47ba267d1f748506bba926cd23ca4d0751651ef85c477ef9b0b2f38cf248d
- [S2] Repo: watch-winder plate manifest (6 plates, margins, utilisation, STL hashes) — builds/watch-winder-capsule/plates/manifest.json — captured 2026-10-13 — sha256 8017b0ac8fca0648491ccc20d95879bb04acd7cebf9b527f67fa854b44de537b
- [S3] Repo: robot-arm plate builder (bed 220 mm, margin 7 mm, gap 8 mm) — builds/robot-arm-print-assembly/scripts/build-plates.py — captured 2026-10-13 — sha256 3b18f5478f18187fbdb66cf836c6f3b4a1791e0f7a93ae69ca5826ab0080876c
- [S4] Repo: robot-arm README (38 parts, 5 plates, per-plate 3MF and STL) — builds/robot-arm-print-assembly/README.md — captured 2026-10-13 — sha256 c9740d502671634374f36eaebffcbcfac2cfeab04c221f814594b287bae3d0b2
- [S5] Repo: robot-arm core-3MF exporter (stdlib zip/XML, no extension) — builds/robot-arm-print-assembly/scripts/export-plate-packages.py — captured 2026-10-13 — sha256 d5b760146c3f952e29f05c7cb0acd58bdf98af5c2d3b092fe612b6ca0bb37f15
- [S6] Repo: production gate (what a gate report proves) — scripts/production-gate.py — captured 2026-10-13 — sha256 85ba67d838058a3419e29b951d7f2e8c31aaa07057a4e20bdd001230e95d7294

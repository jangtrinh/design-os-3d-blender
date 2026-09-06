---
name: print-plate-layout
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Laying printable parts out on build plates — default beds, material/process buckets, spacing and margin, guillotine free-rectangle packing, per-part orientation, STL per plate.
loads_with: [polymer-3dprinting-cad, 3d-printing, export-interchange]
tags: [3d-printing, print-plates, nesting, packing, orientation, stl]
---

# Print-Plate Layout: Buckets, Packing and Orientation

## 1. Mental model

A finished printable build is not a folder of loose STLs — it is a small set of **plates**, each one a single
machine run with one material, one process and one exposure/temperature profile. Layout is therefore three
decisions taken in this order, and only the third one is packing:

1. **Bucket** the parts by material + process. A bucket never shares a plate with another bucket.
2. **Orient** each part for supports, surface finish and load direction. Orientation fixes the 2D footprint.
3. **Pack** the resulting rectangles onto the bucket's plate, opening a new plate when the rest does not fit.

Doing this in the other order (pack first, orient later) invalidates every placement, because rotating a part
changes the footprint the packer just placed. Layout is also **not** a substitute for the final gate: a packed
plate proves arrangement, never manifoldness, wall thickness or fit.

## 2. Decision first

| Question | Default | Where it comes from |
| :--- | :--- | :--- |
| FDM bed | **256 × 256 × 256 mm** (Bambu X1C/P1S class) — **ASSUMPTION** | owner printers unknown; recompute when named |
| Resin bed | **218 × 123 × 220 mm** (Elegoo Saturn-4-Ultra 12K class) — **ASSUMPTION** | 16K variant is 211.7 × 118.4; recompute when named |
| Smaller-bed alternatives | Prusa MK4S 250 × 210 · Bambu A1 mini 180 × 180 · Elegoo Mars 5 143 × 90 · Anycubic Photon Mono M7 223 × 126 | all **ASSUMPTION** until the owner names a machine |
| Part spacing | **6 mm** between inflated rectangles | PrusaSlicer/OrcaSlicer auto-arrange default |
| Plate margin | **8 mm**, shrinkable and *reported* (see R3) | `ww_plates.py::MARGIN_MM` |
| Rotation freedom | **0° / 90° only** | keeps the footprint a rectangle; no free-angle nesting |
| Export | **one STL per plate**, parts pre-placed | Blender 5.2 has no native 3MF (§7) |

**Bed sizes above are ASSUMPTIONS, not measurements.** They are the largest common consumer footprints, chosen so
the packer never has to reject a part. Re-run the layout with the real bed the moment the owner names a printer —
a 180 × 180 A1 mini or a 143 × 90 Mars 5 changes plate count, not just spacing.

## 3. Rules

R1. Bucket by **material + process**, never mix buckets on one plate.
    Why: different nozzle/bed temperatures, chamber requirements, resins and exposure times. The watch-winder
    capsule uses five buckets — `fdm-petg`, `fdm-abs`, `fdm-tpu`, `sla-proxy`, `sla-clear`
    (`builds/watch-winder-capsule/scripts/ww_plates.py::BUCKETS`).
    Violation: a plate that physically cannot be printed in one run.

R2. Orient before packing; record the orientation as an explicit rotation, never as "as modelled".
    Why: the packer consumes the XY bbox produced by the orientation. An orientation decided afterwards
    silently invalidates every placed rectangle.
    Violation: overlapping parts, or supports discovered after the plate is exported.

R3. Margin may shrink, but a reduced margin must be **reported**, never applied silently.
    Why: when a part is wider than `plate − 2·margin`, the honest response is the largest margin that still fits
    (`ww_plates.py::effective_margin`), recorded as `margin_reduced: true` with `margin_requested_mm` beside it.
    In the watch-winder run the 112 mm `front_rim` on the 123 mm resin axis forced 8.0 → **5.5 mm**.
    Violation: a plate that the owner believes has 8 mm of clearance and does not.

R4. A part that does not fit the plate **at all** raises — it is a spec problem, not a layout problem.
    Why: opening a new plate for an oversize part hides the fault and produces an unprintable STL.
    Violation: an "arranged" plate whose part is off the bed.

R5. Overflow is returned, never hidden.
    Why: `pack_shelf` returns `(placements, overflow)`; the caller opens the next plate for the overflow or
    reports it. Dropping the overflow list is how a part disappears between layout and export.
    Violation: a plate manifest with fewer parts than the build has.

## 4. Recipe: the packer that actually ran

**Guillotine free-rectangle bin pack, 0/90 rotation, stdlib only (no scipy)** —
`builds/watch-winder-capsule/scripts/ww_plates.py::pack_shelf`:

- inflate each item by `spacing` on its +x/+y sides;
- place it into the free rectangle with the **best short-side fit** (ties broken by the long side);
- **split** the used rectangle into a right and a top remainder along the *shorter* leftover axis, so the larger
  remainder stays whole; then drop free rectangles fully contained in another.

This is what fills the strip beside a tall part. A plain shelf packer cannot, and that is not theory: the first
watch-winder resin plate came out at **1.6 % utilisation** with a shelf packer. The guillotine packer on the same
parts gives 6 plates at **30.6 / 25.8 / 4.3 / 59.7 / 34.4 / 40.3 %**
(`builds/watch-winder-capsule/plates/manifest.json`). Low utilisation is acceptable when one part dominates a
bucket (the 4.3 % TPU plate) — it is not acceptable when it is an artifact of the packer.

Do not copy pseudocode from research into the build: implement it, run it on the real footprints, and read the
utilisation and `overflow` before believing it.

### Per-part orientation

Orientation is a per-part decision with a written reason, not a global setting. The heuristics that recur:

| Shape | Orientation | Why |
| :--- | :--- | :--- |
| Domed shell with a flat rim | **rim-down** | uses its own flat rim as the base; pole-down needs full-hemisphere support on a visible surface. Large flat PETG footprint → brim against warping |
| Cup / open cavity | **mouth-up** | no support trapped inside an unremovable cavity |
| Turned or knurled cylinder | **axis vertical** | round layers, knurl pitch resolved along Z; horizontal prints faceted |
| Thin disc / tab | **flat-down** | trivially printable, no supports |
| Large flat or hollow resin part | **tilt 12–30°** | breaks the flat plane against FEP suction and lets resin drain (12° rim, 17° relief plate, 25° dome in the watch-winder run) |

The full 20-row table with per-part reasoning and sources lives in
`plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md` §"Per-part table" — link it, do not
copy it. Every row there is standard practice cross-referenced against sources, **not** a print-verified result
for that geometry.

## 5. Anti-patterns & Traps

1. **Adopting packer pseudocode verbatim from research.** Research sketches are unmeasured. Implement, run,
   read the utilisation. *Fix:* treat a packer as code under test, with `check_placements` and a utilisation number.
2. **Hiding an overflow** (or a reduced margin) to make a run look clean. *Fix:* both belong in the manifest.
3. **Compensating an undersized FDM hole in the model** because the plate is being prepared anyway. Hole
   shrinkage is corrected after a physical fit trial, or by the DFAM oversize rules in
   `polymer-3dprinting-cad.md` — never by an ad-hoc edit at layout time.
4. **Treating a passing SLA proxy as evidence for the metal part.** A grey-resin stand-in proves shape and fit
   only; load, wear and strength stay unproven and the build README must say so.
5. **Modelling the tilt into the exported geometry.** See §7.

## 6. Production edge cases

*   **Tilt and supports are slicer-side.** The manifest records `recommended_tilt_deg` and a `supports_note`;
    `ww_plates.py` applies only the 0/90 rotation that the footprint depends on. Baking a 25° tilt into the STL
    would make the exported part disagree with `spec.json` and with every gate report bound to it.
*   **No native 3MF in Blender 5.2.** 3MF exists only as a community extension, so **one STL per plate** with
    parts pre-placed as transformed copies needs no new dependency and matches
    `scripts/production-gate.py --export-dir`, which already writes per-part STL in mm with a manifest.
    Per-plate 3MF is a later nice-to-have that costs an install.
*   **Layout does not clear the final gate.** Plates are arrangement evidence. Manufacture stays BLOCKED until
    the gate report and the physical evidence the build's purpose requires exist.

## 7. Verification & diagnostics

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

## 8. Sources & References

- `plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md` — 19 cited sources: bed sizes
  (Bambu, Prusa, Elegoo, Anycubic spec pages), PrusaSlicer/OrcaSlicer 6 mm arrange spacing, Formlabs SLA
  orientation and drain-hole guidance, PETG warping, absence of 3MF in core Blender.
- `builds/watch-winder-capsule/scripts/ww_plates.py` — the packer that ran: `BUCKETS`, `PLATE_SIZES`,
  `effective_margin`, `pack_shelf`, `pack_bucket`, `check_placements`.
- `builds/watch-winder-capsule/plates/manifest.json` — measured result: 6 plates, spacing 6 mm, resin margin
  reduced to 5.5 mm, per-plate utilisation.
- `knowledge/70-cad-precision-robotics/polymer-3dprinting-cad.md` — DFAM rules (holes, chamfers, inserts,
  wall thickness). This note owns plates, packing and orientation only.
- `specs/README.md`, `scripts/production-gate.py` — what a gate report does and does not prove.

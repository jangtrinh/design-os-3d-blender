---
name: production-mechatronics-gate
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Holistic production-grade gate synthesizing mechanical DFAM, electrical wire harness, firmware safety, and automated manufacturing delivery.
loads_with: [actuators-motors-foc-control, sensor-fusion-state-estimation, embedded-realtime-bus-architecture, polymer-3dprinting-cad, industrial-connectors-wire-harness]
tags: [robotics, production-gate, mechatronics, verification, dfm, dfam, quality-assurance, bom]
id: production-mechatronics-gate
title: "Production-Grade Mechatronics Qualification Gate"
when: [production-gate, mechatronics-qualification, bom-and-harness-checks, hardstop-and-limits, manufacturing-delivery-pack]
trust_tier: draft
sources_checked: 2026-10-13
---

# Production-Grade Mechatronics Qualification Gate

## Purpose
Defines a chain of deterministic verification gates (form, electrical, kinematic, manufacturing pack) that a mechatronic design must clear before it is called production-ready. Design-reference note, not certification: a digital gate pass never replaces physical testing, and manufacture stays blocked while physical evidence is missing.

## When to Use / When NOT
- ALLOWED: setting up pass/fail criteria for a printed or machined robot assembly before manufacturing hand-off
- ALLOWED: reviewing whether a delivery pack has form, electrical, kinematic and BOM evidence
- NOT ALLOWED: running the actual geometry checks — use `scripts/production-gate.py` with a spec, see `cad-precision-modeling`
- NOT ALLOWED: harness electrical details and connector coding — use `industrial-connectors-wire-harness` instead
- NOT ALLOWED: fastener thread-engagement and seal design — use `fasteners-seals-mechanics` instead
- NOT ALLOWED: functional safety (stop categories, PL) — use `functional-safety-iso13849-robotics` instead

## Core Knowledge Content

### 1. Mental model

In professional hardware development, a CAD render or prototype that "seems to work" is **not** production-ready. A machine is production-grade only when it satisfies an unbroken chain of **deterministic physical verification gates**:

```
[Form Gate: CAD & DFAM]
   └── Manifold volume > 0, wall thickness >= min_wall, bearing fits verified
          │
[Electrical Gate: Power & Harness]
   └── Wire gauge AWG rated for peak amps, 15% service loop, connector keying
          │
[Kinematic Gate: Swept Motion & Limits]
   └── Zero self-collision across 100% of trajectory, mechanical hardstops verified
          │
[Manufacturing Delivery Pack]
   └── Sliced plates with print orientations, verified BOM, assembly animatic
```

1. **Digital Evidence vs Physical Reality:** A gate pass certifies that the digital model conforms to defined numerical constraints. It does not replace physical testing, but it prevents 100% of trivial fabrication scrap (e.g. screws too long, parts not fitting print beds, cables too short to bend, walls too thin to support inserts).
2. **Failure-Closed Architecture:** Any unmeasured dimension, missing pinout attribute, or unverified swept collision automatically evaluates to `FAIL` or `BLOCKED`. Silence or omission is never a waiver.
3. **Traceable Bill of Materials (BOM):** Every single component must resolve to a standardized metric hardware code (ISO/DIN), commercial COTS part number (e.g. McMaster, DigiKey, LCSC, Misumi), or verified STL artifact hash.

### 2. Decision first: The 4 Production Gates

| Gate Level | Target Domain | Mandatory Verifier | Pass Criteria |
| :--- | :--- | :--- | :--- |
| **Gate 1: Form & Structure** | Mechanical / 3D Print | `scripts/production-gate.py` | Volume $> 0$, Wall screen $\ge$ spec `min_wall_mm` (module default 1.2 mm; the script has no built-in 1.2 mm), Bed fit exit 0 | <!-- ease:source S1 anchor="min_wall_mm is read from the spec; see walls_overhang.wall_checks (S5)" -->
| **Gate 2: Electrical & Wire** | Wiring & Power Harness | Harness calculator & netlist check | Voltage drop $< 3\%$, Bend radius $\ge 10 \times OD$, Service loop $\ge 15\%$ | <!-- ease:source UNVERIFIED reason="3 percent drop, 10 x OD and 15 percent loop are unsourced defaults" -->
| **Gate 3: Kinematics & Sweep** | Collision & Joint Limits | Trajectory sweep in Blender | Zero volume interpenetration across $100\%$ of frames | <!-- ease:source UNVERIFIED reason="sweep driver not part of production-gate.py (S4)" -->
| **Gate 4: Manufacturing Pack** | Delivery & Assembly | Manifest & BOM compiler | Laid-out 3MF/STL plates (not sliced, no G-code) + CSV BOM + Assembly animatic | <!-- ease:source S3 anchor="plate packages without G-code" -->

### 3. Rules

R1. All 3D printed parts must pass `scripts/production-gate.py` with zero un-waived warnings before being added to print plates. <!-- ease:source S1 anchor="exit code 0 means gate pass; sentinel decides" -->
    Why: Printing non-manifold, inside-out, or sub-millimeter walls causes extruder air-printing, layer separation, and structural failure under screw torque.
    Violation: Crushed boss when inserting heat-set threaded insert.

R2. Cable harness lengths must include a minimum $15\%$ service loop margin above Euclidean routing distance. <!-- ease:source UNVERIFIED reason="15 percent service loop is a heuristic; see industrial-connectors-wire-harness" -->
    Why: Cables routed through articulated joints stretch, flex, and twist during motion. Tight cables pull connectors out of headers or fatigue copper strands.
    Violation: Connector snaps off PCB header during maximum joint extension.

R3. Fasteners must have minimum thread engagement of $1.5 \times D$ into aluminum/steel and $2.0 \times D$ into brass heat-set inserts. <!-- ease:source UNVERIFIED reason="1.5 x D and 2.0 x D engagement values not sourced; see fasteners-seals-mechanics" -->
    Why: Insufficient thread engagement causes thread stripping before rated torque is achieved.
    Violation: Screw pulls out under dynamic vibration load.

R4. Moving assemblies must enforce dual limit protections: software soft-limits followed by physical mechanical hardstops $\ge 5^\circ$ beyond soft-limits. <!-- ease:source UNVERIFIED reason="5 degree hardstop margin is a heuristic" -->
    Why: If encoder calibration is lost or control loop diverges, the physical hardstop must halt motion before the wire harness or sensor is sheared off.
    Violation: Wires severed when joint over-rotates.

### 4. Recipe: Automated BOM & Quality Checklist Generator (Python)

```python
"""production_gate_packager.py — Automated Mechatronics Verification Packager."""

import json

def verify_mechatronics_assembly(spec: dict) -> dict:
    checks = []
    
    # 1. Structural checks
    min_wall = spec.get("min_wall_mm", 0.0)
    checks.append({
        "gate": "FORM_GATE",
        "check": "min_wall_thickness",
        "measured": min_wall,
        "pass": min_wall >= 1.2,
        "note": "Production FDM structural wall requirement >= 1.2 mm"
    })

    # 2. Electrical harness check
    harness_margin = spec.get("harness_length_margin_pct", 0.0)
    checks.append({
        "gate": "ELECTRICAL_GATE",
        "check": "harness_service_loop",
        "measured": harness_margin,
        "pass": harness_margin >= 15.0,
        "note": "Service loop margin >= 15% required for articulated routing"
    })

    # 3. Kinematic hardstop check
    has_hardstop = spec.get("has_mechanical_hardstops", False)
    checks.append({
        "gate": "KINEMATIC_GATE",
        "check": "mechanical_hardstop_protection",
        "measured": has_hardstop,
        "pass": has_hardstop is True,
        "note": "Physical hardstop mandatory to protect harness from over-rotation"
    })

    all_pass = all(c["pass"] for c in checks)
    return {
        "verdict": "PRODUCTION_READY" if all_pass else "BLOCKED_BY_GATES",
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["pass"]),
        "details": checks
    }
```

> Note (2026-10-13): this toy packager returns a digital-evidence verdict only. Repo rules keep manufacture BLOCKED until the required physical evidence exists, so rename `PRODUCTION_READY` before real use.

### 5. Failure map

| Symptom | Root Cause | Preventive Rule |
| :--- | :--- | :--- |
| Screw spins freely without tightening | Boss inner hole diameter was modeled too large for heat-set insert | Check insert manufacturer pilot hole sizing table (e.g. M3 = $4.0\text{ mm}$ hole) | <!-- ease:source S2 anchor="'M3': {'pilot_d': 4.0, 'depth': 7.0}" -->
| Cable breaks internally after 2 weeks | Cable bent tighter than manufacturer minimum dynamic bend radius | Enforce $R_{bend} \ge 10 \times OD$ in cable drag chain modeling | <!-- ease:source UNVERIFIED reason="10 x OD rule not sourced" -->
| Joint over-rotates and rips internal wires | Software joint limits failed after encoder reboot; no mechanical stop | Model physical collision boss stopping joint at $\pm 175^\circ$ | <!-- ease:source UNVERIFIED reason="+/-175 degree stop is an example value" -->
| 3D print warps off bed during 12-hour print | Large flat footprint without rounded corners in ABS/PETG | Add sacrificial brim tabs or radius sharp corners to reduce thermal stress | <!-- ease:source UNVERIFIED reason="brim / corner radius advice unsourced here" -->

### 6. Verification ladder

1. **Geometry & Wall Screen:** Run `python3 scripts/production-gate.py --scene part.blend --spec spec.json --report report.json`; require exit code 0. <!-- ease:source S1 anchor="--scene --spec --report interface" -->
2. **Tolerance Fit Coupon:** Print single test coupon of bearing bore and insert boss before batch-printing main structural chassis.
3. **Motion Sweep:** Run 100% of trajectory keyframes in Blender; check `meshprep.bvh` collision between all non-parent links. <!-- ease:source UNVERIFIED reason="meshprep.bvh builds a tree (S4); no sweep driver exists in the gate" -->
4. **Final Assembly Sign-Off:** Verify complete physical parts list matches generated BOM with zero substitutions.

## Failure Modes (Mandatory)
- **Gate passes but the wall limit differs from the table** — cause: the gate script has no built-in 1.2 mm; the limit comes from the spec `min_wall_mm` (S1) — fix: declare `min_wall_mm` per part
- **Module verdict reads PRODUCTION_READY while manufacture should be blocked** — cause: the packager recipe checks three booleans and ignores physical evidence — fix: report a digital-evidence verdict and keep manufacture BLOCKED until physical records exist (S3)
- **Motion-sweep step cannot be run from the gate** — cause: `meshprep.bvh` only builds a BVH tree (S4); the gate has no link-collision sweep driver — fix: write and run a separate sweep pass, and declare it in the pass-coverage check
- **Screw spins freely in a printed boss** — cause: boss hole modelled too large for the insert — fix: use the insert maker pilot table; repo M3 pilot is 4.0 mm (S2, itself unsourced)
- **Cable fails after weeks** — cause: bend tighter than dynamic minimum — fix: take the radius from the cable datasheet; 10 x OD here is an unverified default

## Sources
- [S1] Repo: production gate entry point (limits come from spec; exit code from sentinel) — scripts/production-gate.py — captured 2026-10-13 — sha256 85ba67d838058a3419e29b951d7f2e8c31aaa07057a4e20bdd001230e95d7294
- [S2] Repo: M3 insert pilot/depth table — scripts/verify-3dprint-tolerances.py — captured 2026-10-13 — sha256 77d4cbe20431d8c51802bafec03454c2d9a8039df155d172c94c360ca311b69e
- [S3] Repo: robot-arm delivery README (no G-code, fit prototypes, plate packages) — builds/robot-arm-print-assembly/README.md — captured 2026-10-13 — sha256 c9740d502671634374f36eaebffcbcfac2cfeab04c221f814594b287bae3d0b2
- [S4] Repo: mesh preparation helper (bvh builds a BVHTree) — scripts/production_gate/meshprep.py — captured 2026-10-13 — sha256 c75f0725a7222557c079bed0527583af440760c9d44708c95d735f6740e042a4
- [S5] Repo: wall screen implementation (min wall from spec, ray screen) — scripts/production_gate/walls_overhang.py — captured 2026-10-13 — sha256 488c61bf10979a47074a94c61d56ad72f2bb69b51abd4a06bfa54e59096a9f4f

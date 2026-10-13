---
name: joint-bearing-preload-fatigue-life
category: 70-cad-precision-robotics
domain: precision_cad_dfam
loads_with: [gears-transmission-modeling, cad-precision-modeling, production-mechatronics-gate]
tags: [robotics, bearings, cross-roller, preload, fatigue-life, iso281, iso16281, production-grade]
id: joint-bearing-preload-fatigue-life
title: "Precision Joint Bearings, Preload Discipline & ISO 16281 Fatigue Life"
description: Cross-roller and angular-contact joint bearing load, preload and rating-life reference for robot joints (design reference, not certification).
when: [robot-joint-bearing, cross-roller-bearing, bearing-preload, rating-life-l10, tilting-stiffness, joint-housing-fit]
trust_tier: draft
sources_checked: 2026-10-13
---

# Precision Joint Bearings, Preload Discipline & ISO 16281 Fatigue Life

## Purpose
Gives the equations and gates for sizing robot-joint bearings (equivalent load, L10 life, preload, tilting stiffness) so joint CAD and build packs carry checkable numbers. This is a design-reference note, not certification or a manufacturer calculation; confirm every load rating and preload against the bearing manufacturer catalog.

## When to Use / When NOT
- ALLOWED: sizing a cross-roller or angular-contact joint bearing: equivalent load P, L10 hours, static factor fs — formulas from the manufacturer-style equations below
- ALLOWED: choosing a preload method (ground shim vs locknut) and its drag-torque acceptance gate
- NOT ALLOWED: modelling gear teeth or flexspline geometry — use `gears-transmission-modeling` instead
- NOT ALLOWED: bolt counterbores, O-ring glands, bearing seat shoulders in CAD — use `fasteners-seals-mechanics` instead
- NOT ALLOWED: a certified life or safety claim — use the bearing manufacturer calculation tool and the full ISO 281/ISO 16281 text

## Core Knowledge Content

> UKMC review 2026-10-13: P_eq formula corrected to the catalog form (X multiplies the bracket; Y 0.7 -> 0.45/0.67 pair); static check per NSK added; the 1800 MPa Hertz limit demoted to UNVERIFIED. Remaining numeric tables are design targets, tagged UNVERIFIED.

> Mechanical engineering principles for robotic joint bearings (Cross-Roller & Angular Contact pairs), negative clearance preload calculation, tilting moment stiffness ($K_\theta$), and ISO 16281 modified rating life.

---

### 1. Physical Principles & Governing Equations

#### A. Cross-Roller Bearing (CRB) Mechanics
Robotic articulation joints experience high cantilever tilting moments ($M$) alongside combined radial ($F_r$) and axial ($F_a$) loads. Cross-roller bearings arrange cylindrical rollers orthogonally ($90^\circ$ V-groove) in alternating sequence:

```math
P_{eq} = X \left( F_r + \frac{2 \cdot M}{d_{pitch}} \right) + Y \cdot F_a
```
<!-- ease:source S2 anchor="N Series Crossed Roller Bearings, Dynamic Equivalent Load" -->


Where:
- $d_{pitch}$: Bearing roller pitch circle diameter ($m$).
- $X, Y$: Dynamic radial and axial load factors, per manufacturer. NSK catalog lists two pairs, ($X=1.0, Y=0.45$) and ($X=0.67, Y=0.67$), split at $F_a/(F_r+2M/d_{pitch}) = 1.5$; which pair applies on which side of 1.5 is ambiguous in the extracted PDF text, so read it from the catalog before use (UNVERIFIED side assignment). The earlier draft value $Y=0.7$ is not what the catalog lists. <!-- ease:source S2 anchor="Dynamic Equivalent Load X,Y table" -->
- $d_{pitch}$ here equals NSK's $D_{pw} \approx (d + D)/2$ (bore + outside diameter, halved). <!-- ease:source S2 anchor="Dpw definition" -->

#### B. ISO 281 & ISO 16281 Rating Life
The basic $L_{10h}$ rating life (operating hours with $90\%$ reliability) for roller bearings; the load-life exponent is 10/3 for roller bearings and 3 for ball bearings, and $L_{10}$ in millions of revolutions equals $(C/P)^{p}$: <!-- ease:source S1 anchor="Basic Life Calculation Formula" -->

```math
L_{10h} = \frac{10^6}{60 \cdot n} \left( \frac{C}{P_{eq}} \right)^{10/3}
```

- **ISO 16281 Advanced Modified Life:** Standard ISO 281 assumes rigid rings and uniform roller load. Under ISO 16281, each individual roller's Hertzian contact deformation is integrated:
  ```math
  \delta_i = \left( \frac{Q_i}{c_k \cdot l^{0.8}} \right)^{1/1.1}
  ```
  Where $Q_i$ is individual roller load and $l$ is effective roller length. Tilting moments and negative internal clearance (preload) directly distribute loads across a wider arc of rollers. <!-- ease:source UNVERIFIED reason="ISO 16281 is paywalled; deformation-exponent form (1/1.1) and the contact-constant notation not confirmed against a free primary source" -->

#### C. Preload & Tilting Moment Stiffness ($K_\theta$)
Preload eliminates internal clearance ($\Delta r < 0$), ensuring all rollers share initial load. The angular tilting stiffness $K_\theta$ ($\text{Nm/rad}$):

```math
K_\theta = \frac{\partial M}{\partial \theta} \approx \frac{1}{4} \sum_{i=1}^Z c_\delta \cdot d_{pitch}^2 \cdot \cos^2(\alpha) \cdot \delta_i^{1/2}
```

Preload increases $K_\theta$ by $2.5\times$ to $4.0\times$ compared to zero-clearance bearings, suppressing arm cantilever tip deflection. <!-- ease:source UNVERIFIED reason="stiffness-gain factor and K_theta summation formula not found in a free manufacturer source; use catalog moment-rigidity curves" -->

#### D. Maximum Hertzian Contact Stress Limit
To avoid permanent subsurface plastic indentation (brinelling) during robot emergency stops. Verified static check form (NSK crossed roller bearings): $P_0 = F_r + 2M/D_{pw} + 0.44\,F_a$ and static safety factor $f_s = C_{0r}/P_0$ with the recommended $f_s$ taken from the manufacturer table. <!-- ease:source S2 anchor="Static Equivalent Load; Permissible Static Load Factor" -->

The 1800 MPa limit below is NOT verified: <!-- ease:source UNVERIFIED reason="1800 MPa and S0>=2.5 are not an ISO 76 definition found in any fetched source; reviewer recollection (UNVERIFIED) is that the ISO 76 static rating C0 corresponds to a much higher contact stress, so do not treat 1800 MPa as an ISO 76 limit. Use manufacturer fs and C0r instead" -->

```math
\sigma_{Hertz,max} \le 1800 \, \text{MPa} \quad (\text{ISO 76 Static Safety Factor } S_0 \ge 2.5)
```

---

### 2. Quantitative Interface Specifications

| Parameter | Nominal Specification | Strict Engineering Limit | Unit | Standard / Grade |
|---|---|---|---|---|
| Bearing Precision Class | P4 / P2 | Min P5 | Class | ISO 492 / ABEC 7 |
| Radial / Axial Runout | 2.5 | Max 4.0 | $\mu\text{m}$ | Measured on outer/inner face |
| Internal Preload Clearance | $-0.005$ to $-0.012$ | Min $-0.002$, Max $-0.020$ | mm | Negative clearance (Class C1/C2) |
| Shaft Seat Tolerance | h5 / h6 | Max runout $<3\,\mu\text{m}$ | ISO fit | ISO 286-1 |
| Housing Seat Tolerance | H6 / H7 | Max runout $<4\,\mu\text{m}$ | ISO fit | ISO 286-1 |
| Drag Torque ($T_{drag}$) | 0.20 to 0.60 | Max 1.20 | $\text{Nm}$ | Rotational resistance at $20^\circ\text{C}$ |
| Breakaway Torque Ratio | $1.20 \times T_{drag}$ | Max $1.50 \times T_{drag}$ | ratio | Smooth transition without stick-slip |
| Tilting Stiffness ($K_\theta$) | 45.0 | Min 25.0 | $\text{kNm/rad}$ | For $\varnothing 80\,\text{mm}$ joint bearing |

<!-- ease:source UNVERIFIED reason="table values are design targets carried over from an unsourced draft, not from a manufacturer catalog; the "Class C1/C2 = negative clearance" entry is questionable because C-groups are radial clearance classes, check the catalog preload code instead" -->

---

### 3. Preload Setting Methods & Mechanical Architecture

```text
Robot Link Housing (CNC 6061 / 7075)
  │
  ├── [Ground Precision Spacer Shim] (Thickness t ground to ±0.002mm)
  │     │
  │     ▼
  ├── [Cross-Roller Bearing Inner/Outer Ring]
  │     │
  │     ▼
  └── [Precision Threaded Retaining Ring / Spieth Locknut]
        (Torqued with calibrated socket + Loctite 243)
```

#### A. Ground Precision Shims vs Threaded Preload Nuts
1. **Matched Precision Ground Shims:** The highest-reliability method for production robotics. Inner and outer ring standoffs are measured on a CMM; shims are surface-ground to exact thickness ($\pm 0.002\,\text{mm}$) to enforce desired axial deflection.
2. **Precision Locknuts with Locking Pins (e.g. Spieth M-W):** Allows fine micro-adjustment of preload by tightening to a specified drag torque ($T_{drag}$) measured by a torque watch.

#### B. Thermal Preload Expansion Hazard
- Stator heat from adjacent BLDC motors warms the inner ring faster than the outer housing ($\Delta T = T_{inner} - T_{outer} \approx 15 - 25\,\text{K}$).
- Differential expansion ($\Delta d = d \cdot \alpha_{steel} \cdot \Delta T$) increases negative clearance.
- *Strict Rule:* Never combine heavy preload ($>0.08\,C$) with uncooled high-speed joints, or thermal runaway and bearing seizure will occur within 30 minutes. <!-- ease:source UNVERIFIED reason="0.08C threshold, 15-25 K gradient and 30 minute time scale are unsourced engineering heuristics" -->

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Bearing Seizure from Over-Preload | Thermal expansion clamping rollers during continuous high-speed motion | Bearing locks up, motor stalls | Specify light/medium preload ($0.02 - 0.04\,C$); allocate thermal expansion gap in outer housing fit. |
| Harmonic Drive Tooth Wear | Insufficient bearing tilting stiffness allowing flexspline to cock | Rapid gear tooth stripping, angular backlash | Enforce $K_\theta \ge 35\,\text{kNm/rad}$ through preloaded CRB directly supporting gear hub. |
| False Brinelling / Fretting | Robot subjected to road vibration during shipping while unpowered | Raceway indentation marks, noisy operation | Lock robot joints with shipping transport brackets or ship in compliant foam cradles. |
| Non-Uniform Preload Arcing | Bolted flange clamping torque uneven across circumference | Roller pinching in tight spots, rough rotation | Cross-pattern tightening sequence using calibrated torque wrench in 3 incremental stages. |

<!-- ease:source UNVERIFIED reason="DFMEA guardrail numbers (0.02-0.04C light preload, K_theta >= 35 kNm/rad) are unsourced design heuristics" -->

---

### 5. Production Verification Gate

#### Level 1: Form, Runout & Fit Verification
<!-- ease:source UNVERIFIED reason="Levels 1-4 acceptance thresholds (roundness 0.004 mm, TIR 0.005 mm, drag torque 0.20-0.70 Nm, 50 Nm test moment) are project gate targets, not manufacturer or standard values" -->
- [ ] Bearing seats on shaft and housing inspected with 3-point bore micrometer: Roundness and cylindricity $<0.004\,\text{mm}$.
- [ ] Assembled bearing axial and radial runout measured with dial test indicator ($0.001\,\text{mm}$ resolution) over $360^\circ$ rotation: Max total indicated runout (TIR) $\le 0.005\,\text{mm}$.

#### Level 2: Drag Torque & Smoothness Qualification
- [ ] Rotational drag torque measured across full rotation at $5\,\text{rpm}$ with calibrated torque watch: Drag torque within $0.20 - 0.70\,\text{Nm}$ with fluctuation $<20\%$.
- [ ] Breakaway static torque does not exceed $1.4 \times$ running torque (no sticking or binding).

#### Level 3: Cantilever Tilting Stiffness Test
- [ ] Known moment load ($M = 50\,\text{Nm}$) applied to joint lever arm ($r = 0.25\,\text{m}$, $F = 200\,\text{N}$):
- [ ] Deflection measured at lever tip; angular tilt $\theta = \frac{\Delta y}{r}$ verified: Calculated stiffness $K_\theta = \frac{M}{\theta} \ge 25.0\,\text{kNm/rad}$.

#### Level 4: Assembly Traceability & Manufacturing Pack
- [ ] Ground shim thickness, measured drag torque, and flange bolt torque serialized and recorded in joint build traveler.
- [ ] Lubrication grease type (e.g. Klüberquiet BQ 72-72 or Mobil Polyrex EM) and exact fill volume ($15\% - 20\%$ of free bearing space) certified. <!-- ease:source UNVERIFIED reason="grease brands and fill fraction not checked against a lubricant datasheet; take fill from the bearing manufacturer" -->

## Failure Modes (Mandatory)
- **Joint runs hot or seizes after preload** — cause: preload set heavy and inner ring warms 15-25 K above housing (unsourced heuristic, see Core 3B) — fix: set preload by measured drag torque and leave a thermal gap in the housing fit
- **Computed L10 far longer than field life** — cause: the moment term 2M/d_pitch was omitted from P, or the wrong Y was used — fix: use the catalog form P = X(Fr + 2M/Dpw) + Y Fa with the manufacturer X, Y
- **Brinelling marks after transport** — cause: unpowered joint vibrated on the road (false brinelling) — fix: lock joints with transport brackets before shipping
- **Uneven rotation torque around the circumference** — cause: flange bolts tightened out of sequence or unevenly — fix: cross-pattern torque in 3 stages and re-measure drag torque

## Sources
- [S1] NSK, Dynamic Load Ratings and Fatigue Life (ABC of bearings) — https://www.nsk.com/tools-resources/abc-bearings/dynamic-load-ratings-and-fatigue-life/ (frozen copy: knowledge/_evidence/kb-261013/w6-nsk-dynamic-load-ratings.html) — captured 2026-10-13 — sha256 6c3aa6875414f40be1a952d498c3cdf0f76012276f5d5bf18fb65116924bf2a6
- [S2] NSK, N Series Crossed Roller Bearings catalog E1226 (equivalent load, static load factor) — https://www.nsk.com/content/dam/nsk/common/catalogs/ctrgPdf/bearings/e1226.pdf (frozen copy: knowledge/_evidence/kb-261013/w6-nsk-catalog-e1226.pdf) — captured 2026-10-13 — sha256 8f92401a56ebb6d8e9a259fe26a0eaa9348915945a8a925b6b5fac83a7e1f0a6

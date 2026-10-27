---
name: thermal-management-actuator-cooling
category: 70-cad-precision-robotics
domain: thermal_structural
loads_with: [actuators-motors-foc-control, production-mechatronics-gate]
tags: [robotics, thermal, actuation, cooling, production-grade]
id: thermal-management-actuator-cooling
title: "Thermal Management & Actuator Heat Dissipation"
description: Thermal design of robot joint actuators: two-node lumped thermal network, continuous and intermittent (S3) current limits, polymer-chassis heat paths, potting and winding temperature sensing.
when: [actuator-thermal-model, continuous-torque-rating, s3-duty-peak-current, polymer-chassis-heat-path, winding-temperature-sensing]
trust_tier: draft
sources_checked: 2026-10-13
---

# Thermal Management & Actuator Heat Dissipation

> Comprehensive engineering discipline for thermal dissipation, Lumped-Parameter Thermal Networks (LPTN), potting encapsulation, and IEC 60034-1 duty cycle validation in high-density robotic actuators.

---

## Purpose
Models heat flow in a robot joint actuator with a two-node lumped thermal network and turns it into continuous-torque and intermittent-duty current limits, plus housing, potting and sensor guidance. Design-reference note, not certification: the formulas were re-derived and numerically checked here, but material and rating figures are unverified; confirm against motor, magnet and insulation datasheets and a thermal soak test.

## When to Use / When NOT
- ALLOWED: estimating continuous and intermittent current limits of a BLDC joint from winding-to-ambient thermal resistance
- ALLOWED: deciding whether a printed polymer chassis can carry motor heat (it cannot without a metal spreader)
- NOT ALLOWED: motor model, FOC and torque constants — use `actuators-motors-foc-control` instead
- NOT ALLOWED: PCB thermal vias and FET heat spreading — use `robot-pcb-layout-power-electronics` instead
- NOT ALLOWED: printed-part design rules — use `polymer-3dprinting-cad` instead
- NOT ALLOWED: EMC and environmental qualification — use `emc-emi-environmental-qualification` instead

## Core Knowledge Content

### 1. Physical Principles & Governing Equations

#### A. Lumped-Parameter Thermal Network (LPTN)
Heat generated inside motor windings transfers across an analog resistance-capacitance ladder: <!-- ease:source UNVERIFIED reason="two-node RC ladder is a standard LPTN form derived in-module; no external source captured" -->

```math
C_{th,w} \frac{dT_w}{dt} = P_{loss} - \frac{T_w - T_c}{R_{th,wc}}
```
```math
C_{th,c} \frac{dT_c}{dt} = \frac{T_w - T_c}{R_{th,wc}} - \frac{T_c - T_{amb}}{R_{th,ca}}
```

Where:
- $T_w, T_c, T_{amb}$: Temperatures of stator winding, motor casing, and ambient ($^\circ\text{C}$).
- $C_{th,w}, C_{th,c}$: Thermal capacitances ($\text{J/K}$).
- $R_{th,wc}$: Winding-to-case thermal resistance ($\text{K/W}$).
- $R_{th,ca}$: Case-to-ambient thermal resistance ($\text{K/W}$).

#### B. Temperature-Dependent Joule Losses
Stator winding phase resistance increases linearly with copper temperature: <!-- ease:source S1 anchor="copper temperature coefficient 3.93e-3 per K at 20 C (NBS Copper Wire Tables) in the resistivity table" -->

```math
R_{ph}(T) = R_{20} \left[ 1 + \alpha_{Cu} (T - 20) \right], \quad \alpha_{Cu} = 0.00393 \, \text{K}^{-1}
```

Total copper dissipation under 3-phase Field-Oriented Control:

```math
P_{joule} = \frac{3}{2} I_q^2 R_{ph}(T_w)
```

#### C. Continuous Torque Rating ($S1$ Duty)
Continuous torque is strictly bounded by the total thermal resistance to ambient $R_{th,tot} = R_{th,wc} + R_{th,ca}$. (Corrected 2026-10-13: the former formula omitted the 3/2 factor of $P_{joule}$ and overestimated torque by $\sqrt{1.5}$ = 1.2247, S2/S3; $K_t$ is torque per q-axis amplitude current.) <!-- ease:source S3 anchor="ratio without/with 3/2 factor = 1.2247 = sqrt(1.5)" -->

```math
T_{cont} = K_t \cdot \sqrt{\frac{T_{max} - T_{amb}}{\tfrac{3}{2}\, R_{th,tot} \cdot R_{ph}(T_{max})}}
```

#### D. Intermittent Periodic Duty ($S3$ Duty)
For robotic picking or walking gait cycles governed by IEC 60034-1 S3 (the duty-type definition itself is not captured, S4). Corrected 2026-10-13: the former exact expression had an extra CDF in the denominator, so it did not reduce to its own approximation; in a first-order check it gave 4.0 x the allowed temperature rise (S2/S3): <!-- ease:source S3 anchor="corrected Ipk 18.613 A gives simulated peak rise 1.000 of limit; former expression 4.000" -->

```math
\text{CDF} = \frac{t_{on}}{t_{on} + t_{off}} \times 100\%
```
```math
I_{peak,allowed} = I_{cont} \cdot \sqrt{\frac{1 - e^{-t_{cycle}/\tau_{th}}}{1 - e^{-t_{on}/\tau_{th}}}} \approx \frac{I_{cont}}{\sqrt{\text{CDF}}} \quad (\text{for } t_{cycle} \ll \tau_{th})
```

---

### 2. Quantitative Interface Specifications

| Parameter | Nominal Specification | Strict Engineering Limit | Unit | Standard / Reference |
|---|---|---|---|---|
| Max Winding Temp ($T_{max}$) | 110.0 | 130.0 (Class F margin) | $^\circ\text{C}$ | IEC 60085 Class F ($155^\circ\text{C}$) | <!-- ease:source UNVERIFIED reason="IEC 60085 Class F 155 C not captured (S4); 110/130 C are project margins" -->
| Casing Touch Temp | 55.0 | Max 70.0 | $^\circ\text{C}$ | ISO 13732-1 (Ergonomics/Safety) | <!-- ease:source UNVERIFIED reason="ISO 13732-1 (S4) not captured; 55/70 C are project values" -->
| TIM Thermal Conductivity | 3.5 | Min 1.8 | $\text{W}/(\text{m}\cdot\text{K})$ | ASTM D5470 | <!-- ease:source UNVERIFIED reason="ASTM D5470 (S4) not captured; values are project targets" -->
| Potting Resin Conductivity | 1.4 | Min 1.0 | $\text{W}/(\text{m}\cdot\text{K})$ | Alumina-filled epoxy | <!-- ease:source UNVERIFIED reason="datasheet not captured" -->
| TIM Compression Deflection | 25.0 | 20.0 to 35.0 | % | Prevents PCB/die mechanical stress | <!-- ease:source UNVERIFIED reason="project target" -->
| Winding-Case Resistance ($R_{th,wc}$) | 0.8 | Max 1.4 | $\text{K/W}$ | Frameless BLDC 60-90mm OD | <!-- ease:source UNVERIFIED reason="project estimate for 60-90 mm frameless motors" -->
| Case-Ambient Resistance ($R_{th,ca}$) | 1.2 (Heatsink coupled) | Max 3.5 (Uncooled) | $\text{K/W}$ | Mounted on structural link | <!-- ease:source UNVERIFIED reason="project estimate" -->

---

### 3. Structural & Material Integration

#### A. Housing Conduction vs 3D Printed Structures
- **Direct Aluminum Heat Path:** Motor stator must press-fit directly into CNC 6061-T6 aluminum structural mounts ($k \approx 167\,\text{W}/(\text{m}\cdot\text{K})$). <!-- ease:source UNVERIFIED reason="6061-T6 conductivity 167 W/(m K) is a handbook value, not captured" -->
- **Polymer Chassis Isolation:** If mounting into 3D-printed filaments (PA12-CF, PETG, ABS), thermal conductivity drops to $k \approx 0.3 - 0.7\,\text{W}/(\text{m}\cdot\text{K})$ (insulator). <!-- ease:source UNVERIFIED reason="0.3-0.7 W/(m K) polymer conductivity range and 2.5 mm spreader thickness are unsourced" -->
  - *Mandatory Guardrail:* Never sink high-power motor heat into polymer parts without an intermediate aluminum heat spreader ($>2.5\,\text{mm}$ thick).
  - *Creep Warning:* PETG softens at $75^\circ\text{C}$ ($T_g$). Sustained motor casing at $80^\circ\text{C}$ causes fastener preload relaxation and joint misalignment. <!-- ease:source UNVERIFIED reason="PETG glass transition near 75 C varies by grade; datasheet not captured" -->

#### B. Vacuum Potting Encapsulation
- High torque-density robot joints utilize vacuum-degassed epoxy potting (e.g. Stycast 2850FT or resin with $Al_2O_3$ micro-fillers). <!-- ease:source UNVERIFIED reason="Stycast 2850FT and the 40-55 percent R_th reduction are unsourced" -->
- Thermal conductivity increases from air ($0.026\,\text{W}/(\text{m}\cdot\text{K})$) to cured epoxy ($>1.2\,\text{W}/(\text{m}\cdot\text{K})$), reducing $R_{th,wc}$ by 40% to 55%.

#### C. Temperature Sensor Placement
- Embedded PT1000 platinum RTD or KTY84 silicon sensor placed directly inside the hottest winding slot end-turn. <!-- ease:source UNVERIFIED reason="sensor choice and 10 Hz sampling are design practice" -->
- Firmware thermal monitoring loop must sample temperature at $\ge 10\,\text{Hz}$ and execute dynamic current foldback when $T_w \ge 110^\circ\text{C}$.

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Magnet Demagnetization | Rotor temperature exceeds the magnet grade's maximum working temperature (demagnetisation knee). Flagged 2026-10-13: this is not the Curie point, which is much higher; the former 120 C figure is UNVERIFIED | Permanent loss of $K_t$, motor runaway | Use high-temp NdFeB magnets (SH or UH grade, rated $\ge 150^\circ\text{C}$). |
| Winding Insulation Burnout | Prolonged stall current exceeding Class F limits | Phase-to-phase or phase-to-ground short | Real-time $I^2t$ software fuse + hardware thermistor shutdown at $125^\circ\text{C}$. | <!-- ease:source UNVERIFIED reason="125 C shutdown is a project choice" -->
| Joint Bearing Seizure | Differential thermal expansion between inner/outer races | Ball pinch, excessive friction, stalled actuator | Specify C3 internal radial clearance for high-speed/hot joints. | <!-- ease:source UNVERIFIED reason="C3 clearance advice generic; see joint-bearing-preload-fatigue-life" -->
| Chassis Fastener Loosening | Thermal expansion cycling ($20^\circ\text{C} \leftrightarrow 80^\circ\text{C}$) in polymer | Screw looseness, structural play | Belleville spring washers (DIN 6796) + Loctite 243 threadlocker. | <!-- ease:source UNVERIFIED reason="Belleville washer and threadlocker advice unsourced" -->

---

### 5. Production Verification Gate

#### Level 1: Form & Fit
- [ ] Contact surfaces between motor stator and aluminum chassis show flatness $<0.05\,\text{mm}$ and surface roughness $Ra \le 1.6\,\mu\text{m}$.
- [ ] Thermal interface material (TIM) pad thickness selected to achieve exactly 20%–30% compression under nominal screw torque.

#### Level 2: Sensor & Electrical Integrity
- [ ] Thermistor readouts verified against calibrated infrared thermal camera within $\pm 2.0^\circ\text{C}$ across $25^\circ\text{C} - 100^\circ\text{C}$ range.
- [ ] Dielectric withstand test: $1000\,\text{V} + 2 \times V_{bus}$ applied between phase windings and motor frame for 60s with leakage current $<1.0\,\text{mA}$. <!-- ease:source UNVERIFIED reason="1000 V + 2 x V_bus pattern attributed to IEC 60034-1 (S4) not verified" -->

#### Level 3: Dynamic & Thermal Equilibrium Qualification
- [ ] Actuator run at rated continuous torque ($T_{cont}$) for 90 minutes (until $\frac{dT}{dt} < 1^\circ\text{C} / 10\,\text{min}$). Steady-state winding temperature must remain below $110^\circ\text{C}$ in $25^\circ\text{C}$ ambient. <!-- ease:source UNVERIFIED reason="90 minute duration and 110 C limit are project targets" -->
- [ ] Dynamic overload test: 300% peak torque applied for 5 seconds at $10\%$ CDF; temperature rise per pulse measured and verified against thermal model. <!-- ease:source UNVERIFIED reason="300 percent for 5 s at 10 percent CDF is a project test; check against the corrected S3 formula" -->

#### Level 4: Manufacturing Documentation Pack
- [ ] Engineering assembly drawing specifies TIM pad part number, thickness, and exact installation pattern.
- [ ] Potting process standard defines vacuum level ($<5\,\text{mbar}$), mix ratio by weight, and oven cure temperature profile. <!-- ease:source UNVERIFIED reason="5 mbar is a project value" -->

## Failure Modes (Mandatory)
- **Continuous torque overestimated by about 22 percent** — cause: the original T_cont formula omitted the 3/2 factor that its own P_joule contains — fix: use the corrected formula (check S2)
- **Intermittent peak current far above the thermal limit** — cause: the original exact S3 formula had an extra CDF in the denominator, giving 2x too high a peak in the check case (simulated 4.0 x the limit, S2) — fix: use the corrected expression
- **Winding hot while the case feels warm** — cause: heat path through a polymer chassis or poor stator contact — fix: metal spreader and a winding-slot temperature sensor with current foldback
- **Magnet loses strength after a stall** — cause: rotor temperature above the magnet grade working limit (not the Curie point) — fix: pick the grade for the hottest rotor temperature
- **Fasteners loosen in a warm printed chassis** — cause: polymer creep and thermal cycling — fix: spring washers and a metal insert path (values unverified)

## Sources
- [S1] Wikipedia, "Electrical resistivity and conductivity" (raw wikitext; copper temperature coefficient row citing NBS Copper Wire Tables) — https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity — knowledge/_evidence/kb-261013/w7-wiki-resistivity.txt — captured 2026-10-13 — sha256 4bbbb550663e2ec37f90019ab4000c666a27766ea741ebf31b65670e5f92f42b
- [S2] First-order thermal model check of the S3 duty formula and T_cont (script) — knowledge/_evidence/kb-261013/w7-thermal-s3-and-tcont-formula-check.py — captured 2026-10-13 — sha256 d11addcc8c892741d19beac85e7c5b43f14b7ae4a602a4d0a29eaa266a7b9470
- [S3] Check output (corrected Ipk 18.613 A -> 1.000 of limit; module-as-written 37.226 A -> 4.000; 3/2 factor ratio 1.2247) — knowledge/_evidence/kb-261013/w7-thermal-s3-and-tcont-formula-check-output.txt — captured 2026-10-13 — sha256 a43f4d0fc4ea7119745d73ae02c2857380a1afea625e1b1f215925ff898b38f3
- [S4] IEC 60034-1 (rotating machines rating and duty types), IEC 60085 (insulation classes), ISO 13732-1 (touch temperatures), ASTM D5470 (thermal interface materials) — standards; publisher pages returned HTTP 403/404 to automated fetch, not captured — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)

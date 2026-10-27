---
name: functional-safety-iso13849-robotics
category: 70-cad-precision-robotics
domain: embedded_firmware
loads_with: [embedded-realtime-bus-architecture, production-mechatronics-gate]
tags: [robotics, functional-safety, iso13849, cobot, iso15066, production-grade]
id: functional-safety-iso13849-robotics
title: "Functional Safety, ISO 13849-1 & Cobot Contact Limits (ISO/TS 15066)"
description: Functional-safety architecture notes for cobots: ISO 13849-1 PL parameters, dual-channel STO supervision and ISO/TS 15066 contact-limit inputs (design reference, not certification).
when: [cobot-safety, iso13849-performance-level, iso-ts-15066-contact-limits, safe-torque-off, dual-channel-ossd, power-force-limiting]
trust_tier: draft
sources_checked: 2026-10-13
---

# Functional Safety, ISO 13849-1 & Cobot Contact Limits (ISO/TS 15066)

## Purpose
Collects the parameters and acceptance gates a cobot designer needs for the safety function: ISO 13849-1 parameter bands, ISO/TS 15066 body-model inputs and dual-channel stop supervision. This is a design-reference note, NOT certification or a substitute for the standards, a risk assessment or SISTEMA: every PL claim and contact limit must be taken from the licensed standard text.

## When to Use / When NOT
- ALLOWED: looking up ISO 13849-1 parameter bands (DC, MTTFd, CCF) and the ISO/TS 15066 body-model force, spring and mass inputs (sourced table in 2.A)
- ALLOWED: structuring a dual-channel STO supervision architecture and its test gates (design targets, UNVERIFIED numbers tagged)
- NOT ALLOWED: claiming a Performance Level, a contact-force limit or a pressure limit for a product — use the licensed ISO 13849-1 / ISO/TS 15066 text and SISTEMA instead
- NOT ALLOWED: motor control or encoder design — use `actuators-motors-foc-control` instead
- NOT ALLOWED: bus timing, watchdogs and CAN wiring — use `embedded-realtime-bus-architecture` instead

## Core Knowledge Content

> Industrial functional safety architecture for collaborative robots, Performance Levels ($PL_d, PL_e$), dual-channel OSSD supervision, and ISO/TS 15066 Power and Force Limiting (PFL) biomechanical thresholds.

---

### 1. Physical Principles & Governing Equations

#### A. Power and Force Limiting (ISO/TS 15066)
When a collaborative robot collides with a human operator, contact is classified into two distinct physical regimes:

1. **Transient Contact (Unconstrained Dynamic Impact):**
   The human body region is free to recoil or deflect. Kinetic energy transfer determines peak force:
   ```math
   F_{transient} = v_{rel} \cdot \sqrt{\frac{m_{robot} \cdot m_{body}}{m_{robot} + m_{body}} \cdot k_{contact}}
   ```
2. **Quasi-Static Contact (Constrained Clamping/Crushing):**
   The body region is trapped against a rigid barrier or fixture. Static actuator torque directly dictates clamping force:
   ```math
   F_{clamp} \le F_{max,quasi} \quad \text{and} \quad P_{clamp} = \frac{F_{clamp}}{A_{contact}} \le P_{max,quasi}
   ```
   *Biomechanical Rule:* Maximum allowable transient force is generally **$2.0 \times$** the quasi-static threshold ($F_{transient,max} = 2 \cdot F_{quasi,max}$). <!-- ease:source UNVERIFIED reason="2x transient factor and the per-region exceptions (a secondary summary not frozen here suggests skull/forehead and face are not scaled) must be read from ISO/TS 15066 Annex A; do not rely on the 2x column below" -->
   The effective-mass and spring-constant inputs to the transient formula ARE sourced: see the body-model table in section 2.A. <!-- ease:source S2 anchor="Table 1 body-model parameters" -->

#### B. Safety Performance Level ($PL$) Calculation (ISO 13849-1)
Performance Level ($PL_a$ to $PL_e$) is evaluated via three orthogonal parameters:
- **Category:** Architecture redundancy (Cat B, 1, 2, 3, 4). Cat 3/4 requires dual-channel redundancy.
- **Mean Time to Dangerous Failure ($MTTF_d$)** (series-sum formula and DC_avg weighted formula below are from ISO 13849-1 Annex D/E, text paywalled): <!-- ease:source UNVERIFIED reason="formulas not confirmed against a free primary source" -->
  ```math
  \frac{1}{MTTF_{d,channel}} = \sum_{i=1}^N \frac{1}{MTTF_{d,i}}
  ```
- **Average Diagnostic Coverage ($DC_{avg}$):**
  ```math
  DC_{avg} = \frac{\sum \frac{DC_i}{MTTF_{d,i}}}{\sum \frac{1}{MTTF_{d,i}}} \times 100\%
  ```
  Parameter bands: $DC_{avg}$ none <60 %, low 60 to <90 %, medium 90 to <99 %, high >=99 %; $MTTF_d$ low 3 to <10 y, medium 10 to <30 y, high 30 to <100 y; CCF score must be >= 65. <!-- ease:source S1 anchor="PL Parameters: DC, MTTFd and CCF tables" -->
  The attained PL for a given Category/DC/MTTFd cell is read from ISO 13849-1 Figure 5 and Annex K; PL bands are PFHd bands (PL a < 1e-4 down to PL e >= 1e-8 per hour). <!-- ease:source S3 anchor="Performance levels" --> <!-- ease:source UNVERIFIED reason="Which PL a Category 3 channel with medium DCavg and high MTTFd attains (d vs e) was not confirmed from a free text version of Figure 5; the earlier draft said PL d. Read the cell in the standard or in SISTEMA before claiming a PL" -->

---

### 2. Quantitative Interface Specifications

#### A. ISO/TS 15066 Biomechanical Contact Thresholds (Annex A)

| Human Body Region | Max Quasi-Static Force ($F_q$) | Max Transient Force ($F_t$) | Max Pressure Limit ($P_q$) UNVERIFIED | Unit |
|---|---|---|---|---|
| Skull / Forehead | 130.0 | 260.0 | 30.0 | $\text{N} \, / \, \text{N/cm}^2$ |
| Face | 65.0 | 130.0 | 20.0 | $\text{N} \, / \, \text{N/cm}^2$ |
| Chest / Torso | 140.0 | 280.0 | 45.0 | $\text{N} \, / \, \text{N/cm}^2$ |
| Hands / Fingers | 140.0 | 280.0 | 60.0 | $\text{N} \, / \, \text{N/cm}^2$ |
| Upper Arms / Elbow | 150.0 | 300.0 | 50.0 | $\text{N} \, / \, \text{N/cm}^2$ |
| Thighs / Knees | 220.0 | 440.0 | 70.0 | $\text{N} \, / \, \text{N/cm}^2$ |

<!-- ease:source S2 anchor="Table 1: maximum permissible force 130/65/140/140(hands)/150/220 N for skull/face/chest/hands/upper arm/thigh" --> <!-- ease:source UNVERIFIED reason="pressure column (30/20/45/60/50/70) is NOT supported by any fetched source and probably does not match Annex A; transient column is the draft 2x rule. Do not use pressures or transient forces from this table in a risk assessment; read ISO/TS 15066 Annex A" -->

Sourced body-model parameters (ISO/TS 15066 Table 1 as reproduced in S2): maximum permissible force N / effective spring constant K N/mm / effective mass kg.

| Body region | F max (N) | K (N/mm) | Effective mass (kg) |
|---|---|---|---|
| Skull and forehead | 130 | 150 | 4.4 |
| Face | 65 | 75 | 4.4 |
| Neck | 150 | 50 | 1.2 |
| Back and shoulders | 210 | 35 | 40 |
| Chest | 140 | 25 | 40 |
| Abdomen | 110 | 10 | 40 |
| Pelvis | 180 | 25 | 40 |
| Upper arms and elbow joints | 150 | 30 | 3 |
| Lower arms and wrist joints | 160 | 40 | 2 |
| Hands and fingers | 140 | 75 | 0.6 |
| Thighs and knees | 220 | 50 | 75 |
| Lower legs | 130 | 60 | 75 |
<!-- ease:source S2 anchor="Table 1" -->

#### B. Safety Circuit Electrical Ratings
<!-- ease:source UNVERIFIED reason="This whole table (OSSD voltage window, test pulse width, 8 ms STO response, SS1 ramp, 250 mm/s SLS) is a design-target set; IEC 61131-2 and IEC 61800-5-2 are paywalled and the drive-level STO response time is set by the drive datasheet. IEC 61800-5-2:2016 is the product standard for safety-related power drive systems incl. STO (scope confirmed)." --> <!-- ease:source S4 anchor="IEC 61800-5-2:2016 scope" -->

| Parameter | Nominal Specification | Strict Engineering Margin | Unit | Standard / Reference |
|---|---|---|---|---|
| Dual OSSD Voltage | 24.0 | Min 19.2, Max 28.8 | V (DC) | IEC 61131-2 Type 1/3 |
| OSSD Test Pulse Width | 200.0 | Max 500.0 | $\mu\text{s}$ | High-side pulsing without load drop |
| STO Response Time | 8.0 | Max 15.0 | ms | EN 61800-5-2 |
| Safe Stop 1 (SS1) Ramp Time | 150.0 | Max 300.0 | ms | Controlled deceleration to STO |
| Safely-Limited Speed (SLS) | 250.0 | Max 250.0 | mm/s | Collaborative teaching mode |

---

### 3. Hardware Architecture & Dual-Channel Supervision

#### A. Dual-Channel OSSD Safety Relays
```text
Safety E-Stop / Laser Scanner
  │
  ├── Channel A (24V OSSD_1 with test pulses) ──► Safety MCU Core 1 ──► STO Gate Driver A
  └── Channel B (24V OSSD_2 with test pulses) ──► Safety MCU Core 2 ──► STO Gate Driver B
                                                    │
                                                    ▼ Cross-Monitoring Comparator
                                            (Discrepancy Fault if Δt > 50ms)
```

- **Cross-Fault Monitoring:** Dual channels must switch within $\Delta t \le 50\,\text{ms}$ <!-- ease:source UNVERIFIED reason="50 ms discrepancy window is a project design target, not a standard value" -->. If only one channel triggers, the system enters a latched lockout state requiring a manual power-cycle reset.
- **Galvanic Gate Disconnection:** The STO circuit must physically remove bias supply from high-side and low-side gate driver optocouplers, ensuring PWM pulses cannot energize MOSFET bridges regardless of firmware corruption.

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Latent Channel Failure | One contactor welds closed undetected | Loss of redundancy, failure to stop on next demand | Test pulses periodically cycle output FETs for $200\,\mu\text{s}$ to detect short circuits. |
| Human Crushing Injury | Robot moving at full speed ($>1\,\text{m/s}$) in shared workspace | Force exceeds ISO/TS 15066 limits | Dynamic speed zones: laser scanner switches robot to SLS ($<250\,\text{mm/s}$) when human enters warning zone. |
| Contact Chatter in E-Stop | Vibration causing intermittent switch contact | Spurious safety tripping, contactor arcing | Filter inputs with 10ms hardware RC debouncing + software discrepancy time window. |
| Firmware Lockup During Runaway | Controller hard-faults while motor is accelerating | High-speed crash into mechanical endstop | Independent external windowed hardware watchdog resets STO if strobe absent for $>10\,\text{ms}$. |

---

### 5. Production Verification Gate

#### Level 1: Form & Mechanical Guarding
- [ ] Robot exterior surfaces have round radii $\ge 5.0\,\text{mm}$ to prevent concentrated pressure spikes on contact.
- [ ] No finger pinch points with gaps between $4\,\text{mm}$ and $25\,\text{mm}$ under full joint articulation (EN 349). <!-- ease:source UNVERIFIED reason="EN 349 minimum-gap values paywalled; not confirmed" -->

#### Level 2: Electrical & Safety Pulse Integrity
- [ ] Oscilloscope verifies dual OSSD test pulses are $\le 300\,\mu\text{s}$ and do not cause false dropout on downstream safety relays.
- [ ] Discrepancy time test: Disconnect channel A while keeping channel B closed; system must trip within $50\,\text{ms}$ and refuse restart.

#### Level 3: Dynamic Force & Impact Validation
- [ ] Calibrated Biofidelic Impact Measurement Device (e.g. GTE CBSF-75 / Pilz PROFox) positioned at critical pinch points.
- [ ] Transient impact measured at nominal operating speed: peak force strictly below ISO/TS 15066 limits for targeted body region.

#### Level 4: Safety Technical File & Certification Pack
<!-- ease:source UNVERIFIED reason="Gate Levels 1-3 numbers (5 mm radii, 300 us pulse, 50 ms trip) are project targets. Biofidelic device model names are examples only." -->
- [ ] SISTEMA calculation report submitted documenting achieved $PL_d$ or $PL_e$ with verified $MTTF_d$ and $DC_{avg}$.
- [ ] Safety manual and labeling compliant with ISO 13849-1 and ISO 10218-1/-2.

## Failure Modes (Mandatory)
- **Cobot exceeds a contact limit in the lab** — cause: pressure or transient limits copied from an unsourced table, or the effective mass/spring of the body region ignored — fix: recompute with Annex A values and the sourced K and mass in 2.A, then measure with a calibrated device
- **PL claim collapses in audit** — cause: PL read from a Category label instead of the DC/MTTFd/CCF cell — fix: evaluate Figure 5 / Annex K or SISTEMA with the sourced parameter bands
- **Latent channel failure (welded contactor)** — cause: no test pulse or discrepancy monitoring on one channel — fix: periodic output test pulses and a discrepancy fault that latches
- **Spurious E-stop trips under vibration** — cause: contact chatter without debounce — fix: hardware RC filter plus a software discrepancy window

## Sources
- [S1] KEYENCE Safety Knowledge, PL Parameters (ISO 13849-1 DC, MTTFd, CCF bands) — https://www.keyence.com/ss/products/safetyknowledge/performance/parameter/ (frozen copy: knowledge/_evidence/kb-261013/w6-keyence-iso13849-parameters.html) — captured 2026-10-13 — sha256 6d42a34cc308864f177ac1bcc3a29493c0a23b588465df794484540ae5a82595
- [S2] Safe Physical Human-Robot Interaction through Variable Impedance Control based on ISO/TS 15066 (arXiv 2311.13814), Table 1 body-model parameters — https://arxiv.org/pdf/2311.13814 (frozen copy: knowledge/_evidence/kb-261013/w6-arxiv-2311-13814-iso-ts-15066.pdf) — captured 2026-10-13 — sha256 d633ec39ce53e77259dd55f3234c62251037f9d4467cec6f4c2849ad6c9a7da0
- [S3] Wikipedia, ISO 13849 — https://en.wikipedia.org/wiki/ISO_13849 (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-iso-13849.html) — captured 2026-10-13 — sha256 5fb8c1d4a72642890ac78cffd9d0d7d687559d336c59e4691454af7bb6b20bb0
- [S4] IEC Webstore, IEC 61800-5-2:2016 abstract (safety-related power drive systems, STO family) — https://webstore.iec.ch/en/publication/24556 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-61800-5-2-2016.html) — captured 2026-10-13 — sha256 d77dfd7c60305a3547aa97c39cfa848478c57dda57dc05e720c2a2acc60b5d77

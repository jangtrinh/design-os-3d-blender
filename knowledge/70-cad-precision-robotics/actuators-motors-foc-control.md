---
name: actuators-motors-foc-control
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Actuator selection, torque-inertia matching, Field-Oriented Control (FOC), driver selection (DRV830x/TMC6300), and encoder integration.
loads_with: [gears-transmission-modeling, robotics-urdf-mechanisms, industrial-connectors-wire-harness]
tags: [robotics, bldc, foc, actuators, torque, simplefoc, drivers, motor-control, inertia-ratio]
id: actuators-motors-foc-control
title: "Actuators, Motor Sizing & Field-Oriented Control (FOC)"
when: [actuator-sizing, inertia-matching, field-oriented-control, bldc-motor-selection, encoder-for-foc, motor-driver-selection]
trust_tier: draft
sources_checked: 2026-10-13
---

# Actuators, Motor Sizing & Field-Oriented Control (FOC)

## Purpose
Helps pick a motor/reduction/encoder/control scheme for a robot joint and size torque and reflected inertia with a checkable script. This is a design-reference note, not certification; thermal and torque limits must come from the motor datasheet.

## When to Use / When NOT
- ALLOWED: sizing joint torque and reflected inertia (script in section 4) and choosing a motor topology and feedback type
- ALLOWED: checking FOC fundamentals (d-q frame, Id=0, current-loop calibration steps)
- NOT ALLOWED: gearbox or tooth geometry — use `gears-transmission-modeling` instead
- NOT ALLOWED: CAN-FD timing, watchdogs and E-stop wiring — use `embedded-realtime-bus-architecture` instead
- NOT ALLOWED: contact/impedance control of the arm — use `impedance-admittance-contact-control` instead

## Core Knowledge Content

### 1. Mental model

In precision robotics, an actuator is not merely a motor that spins—it is a **dynamically matched torque transducer** operating under closed-loop electromagnetic control.

1. **Inertia Matching Rule ($J_L / J_m$):** The ratio of reflected load inertia ($J_L = J_{load} / N^2$ where $N$ is gearbox reduction) to motor rotor inertia ($J_m$) determines dynamic control bandwidth. Sourced anchor: most servo sizing guidelines aim for a load-to-motor inertia ratio of 10:1 or lower, a higher compliance (belts, couplings) calls for a lower ratio, and above 10:1 the motor may struggle to control the load. <!-- ease:source S3 anchor="What is an Ideal Ratio?" --> The tiered bands below (1:1 ideal, <=5:1 acceptable) are the draft's own tiers: <!-- ease:source UNVERIFIED reason="1:1 and 5:1 tiers are not in the fetched guideline; limit-cycle claim for >10:1 unsourced; the 5:1 hard rule R1 below is stricter than the sourced 10:1 guideline" -->
   * **Ideal (High Bandwidth / Agile Robots):** $J_L / J_m \approx 1:1$.
   * **Acceptable (Industrial / Trajectory Tracking):** $J_L / J_m \le 5:1$.
   * **Unstable (Sluggish / Resonant):** $J_L / J_m > 10:1$ leads to limit-cycle oscillations and aggressive PID detuning.
2. **Field-Oriented Control (FOC):** Transforms three-phase AC stator currents ($i_a, i_b, i_c$) into an orthogonal rotating rotor frame:
   * **Direct current ($I_d$):** Magnetic flux generation (held at $0\text{ A}$ for non-salient surface PMSM to maximize efficiency). <!-- ease:source S1 anchor="d axis aligned with field flux component" --> <!-- ease:source UNVERIFIED reason="Id = 0 policy for surface PMSM is standard practice but not confirmed on a fetched page" -->
   * **Quadrature current ($I_q$):** Pure electromagnetic torque ($T_e = \frac{3}{2} p \lambda_m I_q$ where $p$ is pole pairs, $\lambda_m$ is permanent magnet flux linkage). The torque component of the stator current is aligned with the q axis in the d-q frame (sourced); the 3/2 p lambda_m scaling assumes the amplitude-invariant Clarke convention <!-- ease:source UNVERIFIED reason="constant 3/2 depends on the Clarke transform scaling; confirm with the SimpleFOC or motor datasheet convention" -->. <!-- ease:source S1 anchor="q axis torque component of current" --> <!-- ease:source S2 anchor="Clarke and Park transforms" -->
3. **Thermal vs Dynamic Envelope:** Continuous torque ($T_{cont}$) is thermally limited by winding insulation class (Class B: $130^\circ\text{C}$, Class F: $155^\circ\text{C}$); peak torque ($T_{peak} \approx 2\text{--}3 \times T_{cont}$) is magnetically limited by stator core saturation and demagnetization threshold ($B_{sat}$). <!-- ease:source UNVERIFIED reason="insulation-class temperatures and the 2-3x peak ratio are motor-datasheet facts not frozen here; take from the motor datasheet" -->

### 2. Decision first

| Application | Motor Topology | Reduction Type | Sensor Feedback | Control Paradigm |
| :--- | :--- | :--- | :--- | :--- |
| **Direct-Drive Gimbal / Pan-Tilt** | High-pole BLDC (e.g. 4008/5010) | 1:1 (Direct) | On-axis magnetic (AS5600 / MT6701) | Voltage-mode or Current FOC |
| **Robot Arm Joint (Base/Elbow)** | Frameless BLDC / Outrunner | 30:1–100:1 Cycloid or Strain-Wave | Dual encoder (Motor + Joint output) | Cascade Current-Velocity-Position FOC |
| **Precision Linear Actuator** | NEMA 17/23 Closed-Loop Stepper | Ball screw / Lead screw | Integrated magnetic encoder | Closed-loop Field-Oriented Stepper |
| **Mobile Robot Wheel (AMR)** | In-wheel Hub BLDC or Planetary DC | 10:1–20:1 Planetary | Incremental ABZ or Hall sensors | Velocity-mode FOC with anti-slip |

Decision tree for motor selection:
1. Is high torque at low speed required with zero backlash? → Choose High-pole BLDC + Strain-Wave/Cycloid gearbox.
2. Is holding torque without power required? → Choose Stepper + Worm drive or mechanical spring-applied brake.
3. Is acoustic silence and smooth slow-speed rotation mandatory? → Choose BLDC with Space Vector PWM (SVPWM) FOC, never 6-step trapezoidal commutation.

### 3. Rules

R1. Motor reflected inertia must not exceed $5 \times$ rotor inertia ($J_{reflected} \le 5 \cdot J_{rotor}$). (Project rule; the sourced general guideline is 10:1 or lower, see 1.1. <!-- ease:source UNVERIFIED reason="5:1 is a stricter project choice, not a vendor limit" -->)
    Why: Excessive inertia mismatch causes control loop phase lag, severe overshoot, and unstable resonance under disturbance.
    Violation: Violent oscillations during step position commands.

R2. Encoders for FOC must have $\ge 12\text{-bit}$ resolution ($4096\text{ cpr}$) and zero axial runout.
    Why: FOC angle estimation error degrades torque per ampere by $\cos(\theta_{err})$ (arithmetic: 1 degree electrical loses 0.015 %, 10 degrees 1.5 %, 30 degrees 13 %; the earlier "> 1 degree degrades torque and overheats" was overstated at 1 degree) and the same current then carries a d-axis component that only heats the winding. <!-- ease:source UNVERIFIED reason="12-bit / 4096 cpr minimum is a design rule of thumb, not a standard" -->
    Violation: Motor draws stall current but produces zero usable torque; rapid overheating.

R3. Shunt resistor traces for current sensing must be Kelvin-connected and routed differentially.
    Why: High-current switching transients ($di/dt > 10\text{ A}/\mu\text{s}$) induce false voltage spikes into ground references, corrupting $I_d, I_q$ measurements.
    Violation: Current loop fails to close, motor emits harsh grinding whine.

R4. 3D-printed motor mounts must account for continuous winding heat ($60\text{--}80^\circ\text{C}$).
    Why: PLA creeps at $55^\circ\text{C}$. Under motor operating temperature, belt tension or gear mesh collapses. Use PETG-CF, ABS, or PA-CF with aluminum thermal standoffs. <!-- ease:source UNVERIFIED reason="PLA creep temperature and material choices are unsourced; check filament datasheets" -->
    Violation: Motor shifts out of alignment during continuous 30-minute run.

### 4. Recipe: Rotor Inertia & Torque Calculation (Python)

```python
"""actuator_sizing_calculator.py — Sizing motor torque and reflected inertia."""

def size_rotary_actuator(
    load_mass_kg: float,
    load_radius_m: float,
    gear_ratio: float,
    accel_rad_s2: float,
    friction_torque_nm: float = 0.5,
    motor_rotor_inertia_kgm2: float = 3.5e-5
) -> dict:
    # 1. Solid-disc load inertia about its own axis: J = 0.5 * m * r^2
    #    (a point mass at radius r would be m * r^2; pick the model that matches the load)
    j_load = 0.5 * load_mass_kg * (load_radius_m ** 2)
    # 2. Reflected inertia through gearbox: J_ref = J_load / N^2
    j_reflected = j_load / (gear_ratio ** 2)
    # 3. Inertia ratio
    inertia_ratio = j_reflected / motor_rotor_inertia_kgm2
    # 4. Acceleration torque required at motor shaft
    t_accel_motor = (motor_rotor_inertia_kgm2 + j_reflected) * (accel_rad_s2 * gear_ratio)
    # 5. Total motor torque required
    t_motor_total = t_accel_motor + (friction_torque_nm / gear_ratio)
    
    return {
        "j_load_kgm2": round(j_load, 6),
        "j_reflected_kgm2": round(j_reflected, 6),
        "inertia_ratio": round(inertia_ratio, 2),
        "inertia_match_status": "PASS" if inertia_ratio <= 5.0 else "FAIL_EXCESSIVE_RATIO",
        "required_motor_torque_nm": round(t_motor_total, 3),
        "recommended_motor_stall_torque_nm": round(t_motor_total * 1.5, 3) # 1.5x safety margin
    }
```

### 5. Failure map

| Symptom | Root Cause | Preventive Rule |
| :--- | :--- | :--- |
| Motor shakes violently without spinning | Phase wiring order swapped ($U, V, W$) relative to encoder direction | Run FOC electrical angle calibration routine at boot |
| Motor gets burning hot while stationary | Voltage-mode FOC driving open-loop current into winding resistance | Switch to closed-loop current control ($I_q$ target) |
| Position drifts over multiple rotations | Magnetic encoder chip detecting external magnetic field from motor stator | Place shield plate or use off-axis shielded encoder |
| Motor mount warps after 1 hour | Mount printed in standard PLA with no heatsink | Require PETG-CF or aluminum mounting faceplate |

### 6. Verification ladder

1. **Static Resistance & Inductance:** Verify phase-to-phase resistance ($R_{phase}$) and inductance ($L_{phase}$) are balanced within $5\%$.
2. **Back-EMF Waveform:** Spin motor externally; check the waveform on an oscilloscope (a sinusoidal shape indicates a PMSM/BLAC machine suited to sine-wave FOC; a trapezoidal shape indicates a BLDC machine). <!-- ease:source UNVERIFIED reason="waveform-to-motor-type mapping is general motor knowledge, not from a fetched source" -->
3. **Inertia Gate:** Run `size_rotary_actuator()`; enforce `inertia_ratio <= 5.0`.
4. **Thermal Bench Test:** Run continuous 100% duty cycle for 20 minutes; verify motor surface temperature $< 75^\circ\text{C}$.

## Failure Modes (Mandatory)
- **Motor shakes violently without spinning** — cause: phase order (U,V,W) swapped relative to encoder direction — fix: run the FOC electrical-angle calibration at boot
- **Motor very hot while stationary** — cause: voltage-mode FOC driving open-loop current into winding resistance — fix: switch to closed-loop Iq current control
- **Position drifts over multiple turns** — cause: magnetic encoder sees the stator field — fix: shield plate or off-axis shielded encoder
- **Mount warps after an hour** — cause: standard PLA mount near a warm stator — fix: PETG-CF or aluminum faceplate

## Sources
- [S1] Wikipedia, Field-oriented control — https://en.wikipedia.org/wiki/Vector_control_(motor) (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-field-oriented-control.html) — captured 2026-10-13 — sha256 106c059c6fb5a1c31925dee15c0abef1ebd9380589e42aa72e01c639314a50be
- [S2] SimpleFOC docs, Coordinate Transformations in FOC — https://docs.simplefoc.com/foc_theory (frozen copy: knowledge/_evidence/kb-261013/w6-simplefoc-docs-foc.html) — captured 2026-10-13 — sha256 c082600c914e8cf54d74d6e6bb7962ab3e8baa3079ef6dba9746ff5661ec9622
- [S3] Rexel USA, Inertia Ratio: Avoiding an Inertia Mismatch (servo sizing guideline) — https://pages.rexelusa.com/blog/automation/inertia-ratio (frozen copy: knowledge/_evidence/kb-261013/w6-rexel-inertia-ratio.html) — captured 2026-10-13 — sha256 6f8942a5b04860eb75ac9252f6f08045d7286b3fba0c5344cb1cc50498332493

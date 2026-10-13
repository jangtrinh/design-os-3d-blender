---
name: impedance-admittance-contact-control
category: 70-cad-precision-robotics
domain: actuation_control
loads_with: [actuators-motors-foc-control, sensor-fusion-state-estimation]
tags: [robotics, impedance-control, admittance-control, contact-stability, passivity, production-grade]
id: impedance-admittance-contact-control
title: "Impedance, Admittance & Physical Contact Interaction Control"
description: Impedance and admittance contact-control reference for robot arms: governing equations, tuning ranges, passivity and contact-stability gates (design reference, not certification).
when: [impedance-control, admittance-control, contact-stability, passivity-controller, force-torque-sensing, peg-in-hole-compliance]
trust_tier: draft
sources_checked: 2026-10-13
---

# Impedance, Admittance & Physical Contact Interaction Control

## Purpose
Gives the impedance/admittance equations, tuning starting points and contact-stability gates for robots that touch stiff environments. This is a design-reference note, NOT a safety certification: human-contact force limits belong to the safety module and the licensed standards.

## When to Use / When NOT
- ALLOWED: choosing between impedance (torque-controlled) and admittance (position-controlled) contact control and setting starting K, D, M
- ALLOWED: writing contact-stability and peg-in-hole acceptance gates
- NOT ALLOWED: human contact force/pressure limits or Performance Level claims — use `functional-safety-iso13849-robotics` and the licensed ISO/TS 15066 instead
- NOT ALLOWED: motor current loops and encoder setup — use `actuators-motors-foc-control` instead
- NOT ALLOWED: state estimation for the F/T or joint signals — use `sensor-fusion-state-estimation` instead

## Core Knowledge Content

> UKMC review 2026-10-13: damping-ratio rule corrected to zeta >= 1 (0.707 is not critical damping); the Hogan 1984 origin is sourced; tuning ranges and gates are design targets tagged UNVERIFIED.

> Advanced dynamic interaction control based on Neville Hogan's impedance formulation, admittance filtering, passivity guarantees, and stable contact transition against stiff environments.

---

### 1. Physical Principles & Governing Equations

#### A. Neville Hogan Impedance Formulation
Pure position control fails upon contact with rigid environments because infinite force is commanded for infinitesimal displacement errors; impedance control (Hogan, "Impedance Control: An Approach to Manipulation", American Control Conference 1984) relates force and position and is the usual choice when a manipulator interacts with its environment. <!-- ease:source S1 anchor="Impedance control overview; Hogan 1984 reference" --> By establishing a virtual mass-spring-damper impedance relationship <!-- ease:source UNVERIFIED reason="sign convention of F_ext and the 6x6 symmetric-positive-definite requirement not checked against Hogan primary text" -->:

```math
M_d \left( \ddot{x} - \ddot{x}_d \right) + D_d \left( \dot{x} - \dot{x}_d \right) + K_d \left( x - x_d \right) = -F_{ext}
```

Where:
- $x, \dot{x}, \ddot{x}$: Actual end-effector Cartesian pose, twist, and acceleration ($6 \times 1$).
- $x_d, \dot{x}_d, \ddot{x}_d$: Nominal reference trajectory.
- $M_d, D_d, K_d$: Desired virtual inertia ($6 \times 6$), damping ($6 \times 6$), and stiffness ($6 \times 6$) matrices (strictly symmetric positive definite).
- $F_{ext}$: External contact wrench ($6 \times 1$) measured or estimated from joint torques.

#### B. Joint Torque Control Implementation
For torque-controlled robots (Quasi-Direct Drive or joint torque sensors):

```math
\tau_c = J^T(q) \left[ K_d (x_d - x) + D_d (\dot{x}_d - \dot{x}) \right] + g(q) + C(q, \dot{q})\dot{q}
```

Where $J(q)$ is the geometric manipulator Jacobian, $g(q)$ is gravity compensation, and $C(q,\dot{q})$ represents Coriolis/centrifugal forces.

#### C. Admittance Control (Position-Controlled Robots)
For stiff industrial arms with non-backdrivable high-ratio gearboxes (cycloidal/harmonic drives), an outer force loop modulates reference trajectory fed to an inner high-gain position controller:

```math
x_r(s) = x_d(s) + \frac{F_{ext}(s)}{M_d s^2 + D_d s + K_d}
```

#### D. Contact Stability & Passivity Condition
To prevent contact limit-cycle oscillations (chatter) against stiff environmental boundaries ($K_{env} > 10^5\,\text{N/m}$):

```math
\int_0^t \dot{x}^T(\tau) F_{ext}(\tau) \, d\tau \ge -E_0 \quad (\forall t \ge 0)
```

The virtual damping ratio $\zeta$ must be tuned to critical damping or slight overdamping, i.e. $\zeta \ge 1$ (CORRECTED: the earlier draft wrote $\zeta \ge 0.707$, which is lightly underdamped and still overshoots about 4.3 % in a 2nd-order step response, exp(-pi) by arithmetic; zero overshoot needs $\zeta \ge 1$):

```math
\zeta = \frac{D_d}{2 \sqrt{M_d K_d}} \ge 1.0
```
<!-- ease:source UNVERIFIED reason="passivity integral and the zeta rule are standard textbook results but not confirmed against a free primary source in this pass" -->

---

### 2. Quantitative Interface Specifications

| Parameter | Nominal Translational | Nominal Rotational | Unit | Tuning Guideline |
|---|---|---|---|---|
| Virtual Stiffness ($K_d$) | 200.0 to 800.0 | 5.0 to 25.0 | $\text{N/m} \, / \, \text{Nm/rad}$ | Soft assembly: 150 N/m; Rigid holding: 1500 N/m |
| Virtual Damping ($D_d$) | 40.0 to 120.0 | 1.0 to 5.0 | $\text{N}\cdot\text{s/m} \, / \, \text{Nm}\cdot\text{s/rad}$ | Maintain $\zeta \ge 1.0$ (was 0.8; aligned with the zero-overshoot gate in Level 2) |
| Virtual Mass ($M_d$) | 1.5 to 5.0 | 0.05 to 0.20 | $\text{kg} \, / \, \text{kg}\cdot\text{m}^2$ | Match physical arm inertia to avoid saturation |
| F/T Sensor Loop Frequency | 1000.0 | 1000.0 | Hz | Minimum 1 kHz for stable contact transition |
| Force Measurement Noise | $<0.10$ | $<0.005$ | $\text{N (RMS)} \, / \, \text{Nm (RMS)}$ | 2nd-order Butterworth low-pass ($f_c \approx 80\,\text{Hz}$) |
| Maximum Contact Force Error | 1.5 | 0.05 | N / Nm | Steady-state contact regulation |

<!-- ease:source UNVERIFIED reason="Table 2 tuning ranges (K_d, D_d, M_d, 1 kHz F/T loop, 80 Hz Butterworth, force error) are starting-point heuristics, not sourced values; tune per robot" -->

---

### 3. Control Architecture & Sensor Integration

#### A. Dual Sensing Modalities
- **Wrist 6-Axis Force/Torque Sensor (e.g. ATI Axia80, Robotiq FT300)** <!-- ease:source UNVERIFIED reason="sensor models are examples; specs not checked" -->: Measures external interaction forces directly at the tool flange. Sensor noise must be filtered off-line using a gravity-compensated payload model:
  ```math
  F_{tool} = F_{raw} - R_{base}^{tool} \cdot m_{tool} \cdot g - F_{bias}
  ```
- **Proprioceptive Joint Motor Sensing:** In quasi-direct drive motors ($K_t \cdot I_q$), joint torques are estimated without expensive wrist sensors, enabling collision detection across the entire robot arm structure.

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Contact Limit-Cycle Chatter | Sensor delay or discrete-time integration injecting energy | Violent oscillation when touching metal fixture | Passivity observer / passivity controller (PO/PC) dynamically injects damping when non-passive behavior detected. |
| Tool Center Point Force Drift | Temperature changes causing strain gauge zero drift | Unintended creeping force or contact false-alarm | Auto-zero / tare routine executed whenever robot is stationary in free-space. |
| Inversion Singularity Instability | Jacobian $J(q)$ rank deficiency near workspace boundary | Infinite commanded joint velocities | Damped Least-Squares (Levenberg-Marquardt) Jacobian inverse: $J^* = J^T (J J^T + \lambda^2 I)^{-1}$. |

<!-- ease:source UNVERIFIED reason="DFMEA guardrails (passivity observer, 50 mm/s velocity cap) are practice heuristics; no primary source fetched" -->
| Runaway on Sudden Loss of Contact | Pushing with high target force when workpiece breaks/slips | Robot accelerates violently forward | Virtual velocity saturation limit ($v_{max} \le 50\,\text{mm/s}$) during force control mode. |

---

### 5. Production Verification Gate

#### Level 1: Static Gravity & Sensor Compensation
<!-- ease:source UNVERIFIED reason="Gate Levels 1-4 thresholds (0.5 N residual, +-1 N, 99.5 % over 100 cycles, 25 um clearance H7/g6 peg) are project targets, not standard values" -->
- [ ] 6-axis F/T sensor payload identification: Rotate end-effector across full sphere; compensated force magnitude remains $<0.5\,\text{N}$ in free air.

#### Level 2: Step Contact Stability Qualification
- [ ] Robot in impedance mode approaches a rigid steel plate ($K_{env} \approx 10^6\,\text{N/m}$) at $100\,\text{mm/s}$: Zero overshoot bounce, zero sustained chatter.
- [ ] Steady-state contact force matches commanded value within $\pm 1.0\,\text{N}$ without integral windup.

#### Level 3: Assembly Benchmark (Peg-in-Hole)
- [ ] $20\,\text{mm}$ steel cylinder inserted into bore with $25\,\mu\text{m}$ clearance (H7/g6 fit) using compliant search spiral: Success rate $\ge 99.5\%$ over 100 consecutive cycles.

#### Level 4: Production Parameter Registry
- [ ] Impedance parameters ($M_d, D_d, K_d$) for every operational mode (Free-space, Approach, Contact, Retract) logged and version-controlled.

## Failure Modes (Mandatory)
- **Chatter or bouncing on a steel fixture** — cause: sensor delay or discrete-time integration injects energy, or damping ratio below 1 — fix: raise D_d to zeta >= 1, add a passivity observer/controller, keep the F/T loop at or above 1 kHz
- **Force reading creeps while stationary** — cause: strain-gauge zero drift with temperature — fix: tare in free space whenever the robot is stationary
- **Violent joint velocities near a singularity** — cause: plain Jacobian inverse near rank loss — fix: damped least-squares inverse with lambda scheduled near the boundary
- **Robot lunges when the workpiece slips** — cause: force target kept high after contact loss — fix: velocity saturation (about 50 mm/s) in force mode and contact-loss detection

## Sources
- [S1] Wikipedia, Impedance control (cites Hogan 1984 ACC paper) — https://en.wikipedia.org/wiki/Impedance_control (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-impedance-control.html) — captured 2026-10-13 — sha256 e8bea92ad4f4cc6430b7042014a26a4509fcd58ce370e1fe5f79786b08ffef5e

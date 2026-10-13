---
name: kinematic-calibration-dh-metrology
category: 70-cad-precision-robotics
domain: kinematics_dynamics
loads_with: [robotics-urdf-mechanisms, production-mechatronics-gate]
tags: [robotics, calibration, dh-parameters, hayati, metrology, tcp-calibration, production-grade]
id: kinematic-calibration-dh-metrology
title: "Kinematic Calibration, Hayati Parameters & ISO 9283 Metrology"
description: Industrial arm kinematic calibration: Hayati-Mirmirani error model, parameter identification, pose selection and 4-point TCP calibration, with ISO 9283 metrology targets.
when: [robot-calibration, dh-hayati-parameters, tcp-calibration, iso-9283-metrology, kinematic-identification]
trust_tier: draft
sources_checked: 2026-10-13
---

# Kinematic Calibration, Hayati Parameters & ISO 9283 Metrology

> Industrial calibration pipeline bridging repeatability and absolute Cartesian accuracy via Hayati-Mirmirani error modeling, Levenberg-Marquardt parameter identification, and 4-point Tool Center Point (TCP) calibration.

---

## Purpose
Explains how to close the gap between a robot arm's repeatability and its absolute Cartesian accuracy with an identified kinematic model and a tool-center-point calibration. Design-reference note, not certification: numeric targets below are mostly unverified engineering heuristics, and ISO 9283 conformance must be established against the standard itself.

## When to Use / When NOT
- ALLOWED: calibrating a physical arm built from CAD/URDF kinematics — identification Jacobian, pose selection, TCP touch routine
- ALLOWED: writing a metrology acceptance plan (what to measure, how many poses, which residuals to reject)
- NOT ALLOWED: authoring the URDF/joint frames themselves — use `robotics-urdf-mechanisms` instead
- NOT ALLOWED: motor/thermal sizing or drive commissioning — use `thermal-management-actuator-cooling` or `actuators-motors-foc-control` instead
- NOT ALLOWED: claiming ISO 9283 conformance — the standard text is paywalled and not captured; use an accredited lab

## Core Knowledge Content

### 1. Physical Principles & Governing Equations

#### A. Repeatability vs Absolute Accuracy (ISO 9283)
Industrial robotic arms inherently exhibit sub-millimeter **pose repeatability** ($RP \le 0.03\,\text{mm}$) due to precision encoders and bearings, but exhibit poor **absolute pose accuracy** ($AP \ge 2.0 - 5.0\,\text{mm}$) due to machining tolerances, zero-position encoder offsets, and joint elastic deflection. Kinematic calibration reduces absolute error to $<0.25\,\text{mm}$. <!-- ease:source UNVERIFIED reason="typical AP/RP magnitudes are an unsourced rule of thumb; ISO 9283 defines the metrics, not these values" -->

#### B. Denavit-Hartenberg Singularity & Hayati-Mirmirani Formulation
Standard 4-parameter Denavit-Hartenberg (DH) modeling is ill-conditioned for calibration when adjacent joint axes are parallel (e.g. Joint 2 and Joint 3 in an articulated 6-DOF arm): the common normal is not unique, so the offset `d` is arbitrary along the axis and a tiny axis-angle error moves the common normal discontinuously, making identified parameters jump. (Corrected 2026-10-13 from "infinite coordinate shifts": this is a parametrization discontinuity, not a literally infinite shift.) <!-- ease:source S5 anchor=""If there is no unique common normal (parallel z axes), then d ... is arbitrary" in the DH-parameters article" -->

The **Hayati-Mirmirani** model eliminates this singularity by replacing $d_i$ with an extra rotation about the Y-axis ($\beta_i$): <!-- ease:source UNVERIFIED reason="formulation recalled from S2 (paywalled); not re-read this session" -->

```math
T_i = \text{Rot}_z(\theta_i) \cdot \text{Trans}_x(a_i) \cdot \text{Rot}_x(\alpha_i) \cdot \text{Rot}_y(\beta_i)
```

The differential Cartesian pose error $\Delta x \in \mathbb{R}^6$ maps to parameter variations $\Delta \Phi \in \mathbb{R}^{5N}$ via the Identification Jacobian $J_k$:

```math
\Delta x = J_k \cdot \Delta \Phi
```

Where $\Delta \Phi = [\Delta \theta_1, \Delta \alpha_1, \Delta a_1, \Delta \beta_1, \dots]^T$.

> Flagged inconsistency (2026-10-13): the vector lists four parameters per joint, so its length is 4N, not the 5N used elsewhere in this note. 5N holds only if a fifth parameter (for example `d`) is kept for non-parallel axes in a hybrid model. Treat `5N` as unresolved until the solver is derived.

#### C. Parameter Identification (Non-Linear Least Squares)
Given $M$ measured Cartesian poses ($M \gg 5N$), parameters are identified using damped Gauss-Newton (Levenberg-Marquardt):

```math
\Delta \Phi = \left( J_k^T J_k + \lambda^2 I \right)^{-1} J_k^T \cdot \Delta x
```

#### D. 4-Point Tool Center Point (TCP) Calibration
To calibrate the tool tip offset $p_{TCP} \in \mathbb{R}^3$ relative to the tool flange without a laser tracker, the robot touches a fixed reference needle from $K \ge 4$ widely different approach orientations ($R_i$): <!-- ease:source UNVERIFIED reason="standard pivot-calibration least-squares identity derived in-module; no external text captured" -->

```math
R_i \cdot p_{TCP} + t_i = p_{world,target} \quad (i = 1, \dots, K)
```

Solving for $p_{TCP}$ and $p_{world,target}$ simultaneously yields the exact tool overhang vector.

---

### 2. Quantitative Metrology Specifications

| Metric / Parameter | Uncalibrated Robot | Production Calibrated | Unit | Standard / Instrument |
|---|---|---|---|---|
| Absolute Position Accuracy ($AP$) | 2.50 to 5.00 | $<0.25$ | mm | ISO 9283 (Full Workspace) | <!-- ease:source UNVERIFIED reason="table values unsourced; ISO 9283 (S4) not readable" -->
| Pose Repeatability ($RP$) | 0.03 | $\le 0.02$ | mm | ISO 9283 (30 cycles) | <!-- ease:source UNVERIFIED reason="table values unsourced; "30 cycles" attributed to ISO 9283 not verified" -->
| TCP Sphere Fitting Residual | 0.80 | $\le 0.12$ | mm | 4-point or 6-point needle touch | <!-- ease:source UNVERIFIED reason="heuristic" -->
| Joint Zero Offset Error ($\Delta \theta_0$) | $\pm 0.50^\circ$ | $\le \pm 0.01^\circ$ | deg | Optical encoder indexing | <!-- ease:source UNVERIFIED reason="heuristic" -->
| Link Length Error ($\Delta a$) | $\pm 0.30$ | $\le \pm 0.02$ | mm | Machining tolerance compensation | <!-- ease:source UNVERIFIED reason="heuristic" -->
| Joint Axis Skew ($\Delta \alpha$) | $\pm 0.20^\circ$ | $\le \pm 0.005^\circ$ | deg | Bearing seat boring alignment | <!-- ease:source UNVERIFIED reason="heuristic" -->
| Measurement Sample Size | N/A | $\ge 40$ non-collinear poses | points | Optimal observability index $O_1$ | <!-- ease:source UNVERIFIED reason=""40 poses" is a heuristic; S3 gives the O1 criterion, not a count" -->

---

### 3. Metrology Workflow & Pose Selection

```text
CAD / URDF Model
  │
  ▼
[Generate Optimal Calibration Poses] (Maximize SVD Observability Index O_1)
  │
  ▼
[Physical Measurement via Laser Tracker / Optical CMM / Touch Probe]
  │
  ▼
[Identification Jacobian Solver] ──► Residual Filter (Reject Outliers >3σ)
  │
  ▼
[Calibrated Kinematic Matrix] ──► Controller Firmware Flash / Corrected URDF
```

- **Observability Metric ($O_1$):**
  ```math
  O_1 = \frac{\left( \prod_{i=1}^{5N} \sigma_i \right)^{\frac{1}{5N}}}{\sqrt{5N}}
  ```
  Poses must be chosen to maximize $O_1$ so that all geometric error components are excited and identifiable.

  > Flagged (2026-10-13): the observability measure of Borm & Menq (S3) is normalised by the square root of the number of measured poses, to my recollection; the `\sqrt{5N}` above is therefore doubtful. Re-check against S3 before implementing.

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Localized Overfitting | Calibration poses clustered in a small sub-volume | High accuracy inside cluster, catastrophic errors ($>10\,\text{mm}$) elsewhere | Mandate pose distribution covering $\ge 80\%$ of spherical reachable envelope. | <!-- ease:source UNVERIFIED reason="80 percent envelope coverage is a heuristic" -->
| Ill-Conditioned Jacobian | Joint axes aligned in singular configurations | Numerical divergence, false parameter corrections | SVD condition number check ($\kappa(J_k) < 100$); reject poses violating threshold. | <!-- ease:source UNVERIFIED reason="kappa < 100 threshold is a heuristic" -->
| Thermal Link Expansion | Ambient workshop temperature shifting during calibration | False link length scaling ($\Delta a \approx 12\,\mu\text{m/m/K}$ for steel) | Perform metrology in climate-controlled cell ($20 \pm 1^\circ\text{C}$) or apply real-time CTE compensation. | <!-- ease:source UNVERIFIED reason="steel thermal expansion coefficient quoted without a source; typical handbook value only" -->
| Joint Elastic Deflection | Heavy end-effector causing arm sag under gravity | Gravitational flexure mistaken for kinematic error | Joint stiffness modeling: identify joint compliance matrix $K_q$ alongside kinematics. |

---

### 5. Production Verification Gate

#### Level 1: TCP Needle Touch Qualification
- [ ] 4-point TCP routine executed: Residual sphere radius must be $\le 0.12\,\text{mm}$.
- [ ] Flange reoriented by $90^\circ$ in pitch and yaw while holding TCP: physical tip deviation must remain within a $0.20\,\text{mm}$ boundary.

#### Level 2: ISO 9283 Cube Trajectory Benchmark
- [ ] Robot traverses a standardized diagonal cube path across diagonal corners ($500 \times 500 \times 500\,\text{mm}$ cube). <!-- ease:source UNVERIFIED reason="cube size and 0.25 mm pass limit not verified against ISO 9283 (S4)" -->
- [ ] Measured position points logged with external laser tracker: maximum absolute error $<0.25\,\text{mm}$ across all edges.

#### Level 3: Joint Compliance & Backlash Verification
- [ ] Known $10\,\text{kg}$ test weight applied to end-effector: joint deflection matches theoretical stiffness model within $5\%$.
- [ ] Hysteresis test: approach same point from opposite directions; directional repeatability gap must be $<0.04\,\text{mm}$.

#### Level 4: Parameter Release & Configuration Serialization
- [ ] Corrected kinematic parameters encoded into signed calibration XML/JSON tied to robot chassis serial number.
- [ ] Robot firmware confirms checksum match at boot before enabling high-speed path interpolation.

## Failure Modes (Mandatory)
- **Accuracy good inside the calibration cluster, wrong elsewhere** — cause: calibration poses covered a small sub-volume — fix: spread poses over most of the reachable envelope, hold out validation poses
- **Identification diverges or parameters jump between runs** — cause: ill-conditioned identification Jacobian (parallel/aligned axes, too few poses) — fix: check the SVD condition number and use a model without the redundant `d` for parallel axes
- **Link-length fit drifts through the day** — cause: temperature change during measurement — fix: climate-controlled cell or explicit thermal-expansion compensation
- **Gravity sag absorbed into kinematic parameters** — cause: no joint-compliance term — fix: identify compliance alongside kinematics or measure at low payload
- **Module formulas disagree with their own text** — cause: `5N` parameter count vs four listed parameters per joint, O1 normalisation unverified (see flagged notes) — fix: re-derive before coding the solver

## Sources
- [S1] Denavit, J. & Hartenberg, R. S. (1955), "A kinematic notation for lower-pair mechanisms based on matrices", Journal of Applied Mechanics 22(2) — bibliographic entry (no free full text captured) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S2] Hayati, S. & Mirmirani, M. (1985), "Improving the absolute positioning accuracy of robot manipulators", Journal of Robotic Systems 2(4) — bibliographic entry (paywalled, not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S3] Borm, J.-H. & Menq, C.-H. (1991), "Determination of optimal measurement configurations for robot calibration based on observability measure", Int. J. Robotics Research 10(1) — bibliographic entry (paywalled, not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S4] ISO 9283:1998 Manipulating industrial robots — Performance criteria and related test methods — https://www.iso.org/standard/22244.html (abstract page returned HTTP 403 to automated fetch; not captured) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S5] Wikipedia, "Denavit–Hartenberg parameters" (raw wikitext; community reference) — https://en.wikipedia.org/wiki/Denavit%E2%80%93Hartenberg_parameters — knowledge/_evidence/kb-261013/w7-wiki-dh-params.txt — captured 2026-10-13 — sha256 c9e3fe8f0eb4d6801858f4a30fe3b900036ba64b2862ab8250e66f5966ebf08b

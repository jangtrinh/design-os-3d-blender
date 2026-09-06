# Cable-Driven Transmissions, Tendon Routing & Capstan Drives

**Date:** 2026-09-05  
**Scope:** Mechanics of capstan drives, Euler-Eytelwein belt friction equations, synthetic HMPE (Dyneema DM20) vs. stainless steel cable selection, pulley D/d fatigue ratios, and antagonistic tendon routing for dexterous robot hands.

---

## 1. Mechanics of Capstan Drives

A **capstan drive** uses a high-strength cable or metallic tape wrapped around a small driving drum (capstan) and anchored to a larger output sector or pulley.

```
                  Capstan Drive Architecture
                  
             Driven Output Sector (Radius R)
                   ╭─────────────╮
                  │       O       │
                   ╰──────┬──────╯
                       \  │  /
                        \ │ / Cable Wrap (Tension T1, T2)
                         ▼▼▼
                        ( o ) Driving Drum (Radius r)
                        Motor Shaft
```

### 1.1 Engineering Merits
*   **Absolute Zero Backlash:** Continuous metallic or synthetic cable under tension eliminates tooth backlash entirely.
*   **Extreme Mechanical Efficiency ($> 95\text{–}98\%$):** Eliminates sliding tooth friction; losses are governed only by rolling bearing friction and slight cable internal bending hysteresis.
*   **Backdrivability & Force Transparency:** Near-zero static friction allows external forces to be sensed directly by the motor without torque sensors.

### 1.2 The Euler-Eytelwein Capstan Formula
The tension ratio across a cable wrapped around a circular cylinder over contact angle $\theta$ (in radians) before slipping occurs is:
$$\frac{T_2}{T_1} = e^{\mu \cdot \theta}$$
Where:
*   $T_2$: Holding / High tension.
*   $T_1$: Slack / Low tension.
*   $\mu$: Static coefficient of friction between cable and drum (e.g., $\mu \approx 0.15\text{–}0.25$ for steel-on-steel, $\mu \approx 0.10$ for Dyneema on smooth aluminum).
*   $\theta$: Total wrap angle in radians ($\theta = 2\pi \cdot n_{turns}$).

*Example:* With $\mu = 0.20$ and 3 complete wraps ($\theta = 6\pi \approx 18.85\text{ rad}$):
$$\frac{T_2}{T_1} = e^{0.20 \times 18.85} = e^{3.77} \approx \mathbf{43.4}$$
A tiny holding tension of $10\text{ N}$ on the termination side holds an operating load of $434\text{ N}$ without slip.

---

## 2. Cable Selection & Fatigue Life: Dyneema vs. Stainless Steel

```
             Dyneema DM20 (HMPE)                       Stainless Steel Cable (7x19)
   ┌─────────────────────────────────────┐        ┌─────────────────────────────────────┐
   │ High tensile strength (3000 MPa)    │        │ High elastic modulus (110 GPa)      │
   │ Density = 0.97 g/cm³ (Floats)       │        │ Density = 7.9 g/cm³ (Heavy)         │
   │ D/d ratio ≥ 12–15 (Compact)         │        │ D/d ratio ≥ 25–30 (Bulky pulleys)   │
   │ Zero creep (DM20 cross-linked)      │        │ Zero creep                          │
   └─────────────────────────────────────┘        └─────────────────────────────────────┘
```

### 2.1 The $D/d$ Pulley-to-Cable Diameter Ratio
The $D/d$ ratio is the outer diameter of the pulley or capstan ($D$) divided by the cable diameter ($d$):
$$\text{Ratio} = \frac{D_{pulley}}{d_{cable}}$$
*   **Stainless Steel Wire Rope (7x7 / 7x19 construction):**
    *   Bending a wire rope around a tight radius induces severe cyclic bending fatigue stresses on the outer wire filaments:
        $$\sigma_{bend} \approx E_{wire} \cdot \frac{d_{wire}}{D_{pulley}}$$
    *   **Minimum Threshold:** $D/d \ge 25\text{–}30$ for continuous cyclic robotic service. Ratios below 20 cause individual strands to snap within thousands of cycles.
*   **Dyneema (UHMWPE):**
    *   Polymer chains are molecularly flexible and do not suffer metal crystalline fatigue fracture.
    *   Permits much more compact pulleys: $D/d \ge 12\text{–}15$.

### 2.2 The Creep Challenge in Synthetic Tendons
*   **The Creep Trap:** Standard UHMWPE (Dyneema SK75 / SK78) exhibits cold plastic flow ("creep") under permanent static load, gradually lengthening over days and weeks until joint tension is lost.
*   **The Solution:** Use **Dyneema DM20**. DM20 is chemically synthesized with ultra-long, highly entangled molecular chains that exhibit **near-zero measurable creep** ($< 0.05\%$ over years at $20^\circ\text{C}$ under $20\%$ breaking load).

---

## 3. Tendon Routing in Dexterous Robotic Hands

Because cables can only transmit **tensile forces** (they cannot push), an $N$-DOF robotic joint mechanism requires an **antagonistic configuration**.

```
                   Antagonistic 1-DOF Tendon Joint
                   
           Motor A (Flexor) ───► [ Flexor Cable ] ───╮
                                                     │ Joint Disk (R)
                                                     ├───► [ Finger Link ]
                                                     │
         Motor B (Extensor) ───► [ Extensor Cable ] ─╯
```

### 3.1 Actuator-to-Joint Coupling ($2N$ vs. $N+1$)
*   **$2N$ Antagonistic Architecture:** Every joint has two independent motors (one flexor, one extensor). Permits independent control of joint position AND joint co-contraction stiffness.
*   **$N+1$ Coupled Architecture:** $N$ degrees of freedom driven by $N+1$ actuators through a coupled tendon routing matrix. Minimizes actuator weight in the forearm.

### 3.2 Tendon Kinematic Mapping (The Coupling Matrix $\mathbf{R}$)
The relationship between tendon excursion velocities $\mathbf{\dot{l}}$ and joint angular velocities $\boldsymbol{\dot{\theta}}$:
$$\mathbf{\dot{l}} = \mathbf{R} \cdot \boldsymbol{\dot{\theta}}$$
Where $\mathbf{R}$ is the routing radius matrix. By the Principle of Virtual Work, joint torques $\boldsymbol{\tau}$ map to tendon tensions $\mathbf{f}$:
$$\boldsymbol{\tau} = \mathbf{R}^T \mathbf{f}$$
*Constraint:* All tendon tensions must satisfy strictly positive bounds:
$$f_i \ge f_{min} > 0 \quad (\text{prevents cable slackening and derailment})$$

### 3.3 Routing Pathways: Bowden Sheaths vs. Redirect Pulleys
1.  **PTFE-Lined Bowden Sheaths:**
    *   Flexible routing around complex robot bodies.
    *   *Trade-off:* Introduces position-dependent Coulomb friction and hysteresis: $F_{out} = F_{in} e^{-\mu \Sigma |\Delta \theta|}$.
2.  **Ball-Bearing Idle Redirect Pulleys:**
    *   Near-zero friction ($> 99\%$ efficiency).
    *   *Trade-off:* Requires dedicated bearing mounting bosses, increasing component count and volume.

---

## 4. References & Standards

1.  **Townsend, W. T., & Salisbury, J. K. (1988).** *The effect of Coulomb friction and stiction on force-guided robot manipulation.* IEEE International Conference on Robotics and Automation, 883–889. (Capstan drive kinematics and WAM arm cable transmission design).
2.  **Grebenstein, M., et al. (2011).** *The DLR Hand Arm System.* IEEE International Conference on Robotics and Automation (ICRA), 3175–3182. (State of the art in high-density antagonistic tendon drive routing, non-linear stiffness, and Dyneema durability).
3.  **Costello, G. A. (1997).** *Theory of Wire Rope* (2nd ed.). Springer-Verlag, New York. (Contact stress, bending fatigue, and D/d ratio mechanics of twisted wire cables).
4.  **Euler, L. (1769) / Eytelwein, J. A. (1808).** *Capstan equation (Belt friction theorem).* (Governing exponential mechanics of wrap angles and friction).
5.  **Palli, G., Melchiorri, C., & Vassura, G. (2008).** *Kinematic and dynamic model of tendon-driven robotic mechanisms.* IEEE Transactions on Robotics, 24(2), 268–279.


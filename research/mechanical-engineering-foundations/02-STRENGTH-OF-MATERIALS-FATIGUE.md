# Strength of Materials, Failure Criteria & Fatigue Life

**Date:** 2026-09-05  
**Scope:** Stress-strain tensors, Mohr's circle, Von Mises vs. Tresca failure criteria, Wöhler S-N fatigue curves, Marin endurance limit factors, Goodman/Soderberg mean stress diagrams, and beam deflection/torsion.

---

## 1. Stress, Strain & Principal Stresses

When mechanical components transmit forces, internal stresses develop. The 3D state of stress at any infinitesimal point is represented by the symmetric Cauchy Stress Tensor:
$$\boldsymbol{\sigma} = \begin{bmatrix} \sigma_x & \tau_{xy} & \tau_{xz} \\ \tau_{yx} & \sigma_y & \tau_{yz} \\ \tau_{zx} & \tau_{zy} & \sigma_z \end{bmatrix}$$

```
                3D State of Stress at a Point
                         σz
                         ▲
                         │   τzy
                   ┌─────┼─────┐
                  /│     │    /│
                 / │     │   / │
          σy ◄───┼─┼─────┼───┼─┼──► σy
                 │ └─────┼───┼─┘
                 │/      │   │/  ▲ τxy
                 └───────┼───┘   │
                        / \      │
                       /   ▼     │
                      ▼     τxz  ▼
                     σx
```

### 1.1 Hooke's Law & Elastic Moduli
In the linear elastic regime:
$$\epsilon_x = \frac{1}{E} \left[ \sigma_x - \nu (\sigma_y + \sigma_z) \right], \quad \gamma_{xy} = \frac{\tau_{xy}}{G}$$
Where:
*   $E$: Young's Modulus of Elasticity ($210\text{ GPa}$ for steel, $69\text{ GPa}$ for aluminum).
*   $\nu$: Poisson's Ratio ($\sim 0.28\text{–}0.33$ for structural metals).
*   $G$: Shear Modulus:
    $$G = \frac{E}{2(1 + \nu)}$$

### 1.2 Principal Stresses & Mohr's Circle
Rotating the coordinate frame to eliminate shear stresses yields the three **Principal Stresses** ($\sigma_1 \ge \sigma_2 \ge \sigma_3$):
$$\det(\boldsymbol{\sigma} - \sigma \mathbf{I}) = \sigma^3 - I_1 \sigma^2 + I_2 \sigma - I_3 = 0$$
For 2D plane stress ($\sigma_z = \tau_{xz} = \tau_{yz} = 0$):
$$\sigma_{1, 2} = \frac{\sigma_x + \sigma_y}{2} \pm \sqrt{\left(\frac{\sigma_x - \sigma_y}{2}\right)^2 + \tau_{xy}^2}$$
$$\tau_{max} = \frac{\sigma_1 - \sigma_3}{2}$$

---

## 2. Static Failure Criteria: Ductile vs. Brittle Materials

A material fails statically when applied loads exceed its elastic carrying capacity.

```
       Ductile Failure Envelopes (Plane Stress)
       
                σ2 ▲
                   │    ┌───────────┐  Tresca (Hexagon)
                   │  /             \
                   │ /   ╭─────────╮ \  Von Mises (Ellipse)
                   ││   /           \ │
         ──────────┼───/─────────────\┼──────────► σ1
                   ││  \             /│
                   │ \   ╰─────────╯ /
                   │  \             /
                   │    └───────────┘
```

### 2.1 Ductile Materials (Yield-Governed)

1.  **Von Mises Criterion (Maximum Distortion Energy Theory):**
    Predicts yielding occurs when the shear distortion energy reaches the distortion energy at yield in simple uniaxial tension.
    $$\sigma_{vm} = \sqrt{\frac{1}{2} \left[(\sigma_1 - \sigma_2)^2 + (\sigma_2 - \sigma_3)^2 + (\sigma_3 - \sigma_1)^2\right]} \le \frac{S_y}{n_s}$$
    For 2D plane stress:
    $$\sigma_{vm} = \sqrt{\sigma_x^2 - \sigma_x \sigma_y + \sigma_y^2 + 3\tau_{xy}^2}$$
    *Status:* The most accurate predictive model for metals (steels, aluminum, titanium).

2.  **Tresca Criterion (Maximum Shear Stress Theory - MSS):**
    Assumes yielding is caused strictly by maximum shear stress sliding along slip planes:
    $$\tau_{max} = \frac{\sigma_1 - \sigma_3}{2} \le \frac{S_y}{2 n_s} \implies \sigma_1 - \sigma_3 \le \frac{S_y}{n_s}$$
    *Status:* Conservative by $\sim 15\%$ compared to Von Mises; preferred for high-liability structural safety codes.

### 2.2 Brittle Materials (Fracture-Governed)
Brittle materials (gray cast iron, ceramics, unreinforced plastics) do not yield plastically; they fracture abruptly along cleavage planes.
1.  **Maximum Normal Stress Theory (Rankine):**
    Fracture occurs when $\sigma_1 \ge S_{ut}$ or $\sigma_3 \le -S_{uc}$.
2.  **Mohr-Coulomb / Modified Mohr:**
    Accounts for the fact that brittle materials possess compressive strengths $3\text{–}5\times$ higher than tensile strengths ($S_{uc} \gg S_{ut}$).

---

## 3. Dynamic Fatigue & Durability Analysis

Over $90\%$ of mechanical failures in machines are caused by **cyclic fatigue**, occurring at stress levels well below the static yield strength ($S_y$).

```
                Wöhler S-N Curve for Structural Steel
        Stress (S)
            ▲
            │ \
     S_ut ──┤  \  Low Cycle Fatigue
            │   \
            │    \
            │     \  High Cycle Fatigue
            │      \────────────────────────── Endurance Limit (Se)
            │
            └───────────┬───────────────┬──────► Cycles (N, Log scale)
                       10³             10⁶
```

### 3.1 The Endurance Limit ($S_e'$) & The Wöhler S-N Curve
*   **Ferrous Steels:** Exhibit a true endurance limit $S_e'$ (typically at $N = 10^6$ cycles). Stresses kept below $S_e'$ will theoretically never fail:
    $$S_e' \approx 0.50 \cdot S_{ut} \quad (\text{for } S_{ut} \le 1400\text{ MPa})$$
*   **Aluminum & Copper Alloys:** **Do not have an endurance limit.** The S-N curve continues downward indefinitely. Fatigue strength must always be quoted at a specified cycle life (e.g. $S_f$ at $5 \times 10^8$ cycles).

### 3.2 Marin Modification Factors
The ideal polished lab specimen endurance limit ($S_e'$) must be derated for real-world machine parts:
$$S_e = k_a \cdot k_b \cdot k_c \cdot k_d \cdot k_e \cdot k_f \cdot S_e'$$
1.  **Surface Condition Factor ($k_a = a \cdot S_{ut}^b$):**
    *   Ground: $k_a \approx 0.90\text{–}0.95$
    *   Machined / Cold-drawn: $k_a \approx 0.70\text{–}0.80$
    *   Hot-rolled / As-forged: $k_a \approx 0.30\text{–}0.60$
2.  **Size Factor ($k_b$):** For bending and torsion of diameter $d$:
    $$k_b = 1.24 d^{-0.107} \quad (\text{for } 2.79\text{ mm} \le d \le 51\text{ mm})$$
3.  **Load Factor ($k_c$):**
    *   Bending: $k_c = 1.0$
    *   Axial: $k_c = 0.85$
    *   Torsion: $k_c = 0.59$
4.  **Temperature Factor ($k_d$):** $k_d = 1.0$ for $T \le 71^\circ\text{C}$; drops at elevated temperatures.
5.  **Reliability Factor ($k_e$):** $90\% = 0.897$, $99\% = 0.814$, $99.9\% = 0.753$.
6.  **Fatigue Notch Factor ($k_f = 1 / K_f$):**
    $$K_f = 1 + q (K_t - 1)$$
    Where $K_t$ is geometric stress concentration, $q$ is notch sensitivity ($0 \le q \le 1$).

### 3.3 Fluctuating Stresses: The Goodman & Soderberg Diagrams
When load fluctuates between $\sigma_{max}$ and $\sigma_{min}$:
$$\sigma_a = \left|\frac{\sigma_{max} - \sigma_{min}}{2}\right| \quad (\text{Alternating Stress})$$
$$\sigma_m = \frac{\sigma_{max} + \sigma_{min}}{2} \quad (\text{Mean Stress})$$

```
          Alternating Stress (σa)
                   ▲
                Se ┼───╮ Soderberg Line
                   │    \ (Guards Yield)
                   │     \   Modified Goodman Line
                   │      \  (Industry Standard)
                   │       \
                   └────────┴────────────┴──────► Mean Stress (σm)
                           Sy           Sut
```

*   **Modified Goodman Relation:**
    $$\frac{\sigma_a}{S_e} + \frac{\sigma_m}{S_{ut}} = \frac{1}{n_f}$$
*   **Soderberg Relation (Conservative, prevents yielding):**
    $$\frac{\sigma_a}{S_e} + \frac{\sigma_m}{S_y} = \frac{1}{n_f}$$

---

## 4. Beam Deflection & Torsional Shaft Mechanics

### 4.1 Euler-Bernoulli Beam Bending Equations
$$E I \frac{d^4 y}{dx^4} = q(x) \quad (\text{Distributed Load})$$
$$M(x) = E I \frac{d^2 y}{dx^2}, \quad \sigma_{bending} = \frac{M(x) \cdot y}{I}$$
*   **Cantilever with End Load $F$:**
    $$y_{max} = \frac{F L^3}{3 E I}, \quad \theta_{max} = \frac{F L^2}{2 E I}$$
*   **Simply Supported Beam with Center Load $F$:**
    $$y_{max} = \frac{F L^3}{48 E I}$$

### 4.2 Shaft Torsion & Angle of Twist
For a solid circular shaft of diameter $d$:
$$\tau_{max} = \frac{T \cdot r}{J} = \frac{16 T}{\pi d^3}$$
$$\theta = \frac{T \cdot L}{G \cdot J} \quad (\text{radians})$$
Where the polar moment of inertia is $J = \frac{\pi d^4}{32}$.
*Warning on Non-Circular Shafts:* A rectangular or square beam under torsion does NOT follow polar moment formulas. Cross-sections warp out-of-plane. For a narrow rectangle ($b \times t$, $b \gg t$), effective torsional constant is $J_{eff} \approx \frac{1}{3} b t^3$, leading to severe loss of torsional stiffness.

---

## 5. References & Standards

1.  **Norton, R. L. (2020).** *Machine Design: An Integrated Approach* (6th ed.). Pearson. (Stress concentrations, multiaxial fatigue theories, and modified Goodman/ASME-elliptic criteria).
2.  **Timoshenko, S., & Goodier, J. N. (1970).** *Theory of Elasticity* (3rd ed.). McGraw-Hill. (Foundational continuum stress tensor equations and Saint-Venant torsional warping).
3.  **Pilkey, W. D., Pilkey, D. F., & Bi, Z. (2020).** *Peterson's Stress Concentration Factors* (4th ed.). John Wiley & Sons. (Authoritative $K_t$ charts for stepped shafts, shoulder fillets, transverse holes, and keyways).
4.  **Marin, J. (1962).** *Mechanical Behavior of Engineering Materials.* Prentice-Hall, Englewood Cliffs, NJ. (Theoretical derivation of environmental, size, and surface modification factors for endurance limits).
5.  **ASTM E466-21.** *Standard Practice for Conducting Force Controlled Constant Amplitude Axial Fatigue Tests of Metallic Materials.* ASTM International.
6.  **Goodman, J. (1899).** *Mechanics Applied to Engineering.* Longmans, Green & Co., London.


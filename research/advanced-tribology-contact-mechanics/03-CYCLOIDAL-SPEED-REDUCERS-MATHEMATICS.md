# Cycloidal Speed Reducers: Mathematics, Epitrochoids & Dynamics

In heavy-payload dynamic robotics, traditional involute gears fail due to single-tooth bending overload under shock impacts. **Cycloidal Speed Reducers (Cyclo Drives)** achieve extreme shock load resistance ($> 500\%$ momentary overload) because **up to $50\%$ of all rollers share the transmission load simultaneously**.

---

## 1. Kinematic Architecture & Working Principle

```
                   Cycloidal Drive Component Architecture
                   
                 ┌──────────────────────────────────────┐
                 │       Stationary Ring Pin Ring       │
                 │             (Z_p Rollers)            │
                 │                                      │
                 │        ╭──────────────────╮          │
                 │       (   Cycloid Disc     )         │
                 │        \  (Z_c = Z_p - 1) /          │
                 │         ╰────────┬───────╯           │
                 │                  │                   │
                 │        [ Eccentric Cam (e) ] ◄────── High-Speed Input Motor Shaft
                 │                  │
                 └──────────────────┼───────────────────┘
                                    ▼
                         Output Drive Pins (Wobble Output -> Pure Rotation)
```

### 1.1 Gear Ratio Formulation
For a ring containing $Z_p$ stationary pins and a cycloid disc with $Z_c$ lobes ($Z_c = Z_p - 1$):
*   Every full $360^\circ$ revolution of the eccentric input shaft wobbles the cycloid disc through one eccentricity orbit.
*   Because the disc has one fewer lobe than the pin ring, the disc is forced to rotate backward by exactly one lobe:
    $$\Delta \theta_{disc} = -\frac{2\pi}{Z_c}$$
*   **Gear Reduction Ratio ($i$):**
    $$i = \frac{\omega_{in}}{\omega_{out}} = -Z_c = -(Z_p - 1)$$
    *(Example: A disc with $Z_c = 29$ lobes orbiting inside a ring of $Z_p = 30$ pins delivers an exact **$29:1$ reduction** in a single compact stage!).*

---

## 2. Epitrochoid Parametric Curve Equations

The contour of the cycloid disc is an **equidistant curve parallel to an epitrochoid**.

```
              Coordinate Geometry for Cycloid Disc Profile
              
                     y ▲
                       │      • Pin Center (R_p, θ)
                       │     /
                       │    / Normal Vector n
                       │   /
                       │  /
                       │ /
                       └───────────────────► x
                       Eccentric Center (e cos θ, e sin θ)
```

### 2.1 The Generating Equations
Let:
*   $R_p$: Radius of the pin ring pitch circle.
*   $r_p$: Radius of the stationary pins/rollers.
*   $e$: Eccentricity (cam offset distance).
*   $Z_p$: Number of pins in the ring.
*   $Z_c = Z_p - 1$: Number of lobes on the cycloid disc.
*   $K_1 = \frac{e Z_p}{R_p}$: Dimensionless eccentricity parameter ($K_1 < 1.0$ for non-cusping curves).

The coordinates $(x, y)$ of the cycloid disc profile as parameter $\theta \in [0, 2\pi]$ varies:
$$x(\theta) = R_p \cos\theta - e \cos(Z_p \theta) - r_p \cos(\theta + \psi)$$
$$y(\theta) = R_p \sin\theta - e \sin(Z_p \theta) - r_p \sin(\theta + \psi)$$
Where the contact normal angle $\psi$ is defined by:
$$\tan \psi = \frac{\sin[(Z_p - 1)\theta]}{\frac{R_p}{e Z_p} - \cos[(Z_p - 1)\theta]} = \frac{\sin(Z_c \theta)}{\frac{1}{K_1} - \cos(Z_c \theta)}$$

### 2.2 Cusping & Undercut Avoidance Condition
To ensure the profile does not intersect itself or produce sharp corner cusps:
$$K_1 = \frac{e Z_p}{R_p} \le \frac{1}{\sqrt{1 + (Z_c / \sin\psi)^2}} \implies \mathbf{K_1 \le 0.70\text{–}0.85}$$

---

## 3. Dynamic Centrifugal Balance: Dual Opposed Discs

A single eccentric disc of mass $M_{disc}$ orbiting at high motor speed ($\omega_{in} = 3000\text{ rpm}$) generates a violent rotating centrifugal force vector:
$$F_{centrifugal} = M_{disc} \cdot e \cdot \omega_{in}^2$$
For $M_{disc} = 0.5\text{ kg}$, $e = 1.5\text{ mm}$, $\omega = 314\text{ rad/s}$:
$$F_{cent} = (0.5)(0.0015)(314)^2 \approx \mathbf{74\text{ N}} \quad (\text{causes violent shaking and bearing destruction!})$$

```
          Dual 180° Balanced Cycloid Discs
          
                  Eccentric Cam A (0°)        Eccentric Cam B (180°)
                       [+e]                        [-e]
                     ┌───────┐                   ┌───────┐
                     │Disc A │                   │Disc B │
                     └───────┘                   └───────┘
                     Centrifugal Vector          Centrifugal Vector
                     ───────► (+F)               ◄─────── (-F)
                     ★ NET TRANSLATIONAL CENTRIFUGAL FORCE = 0!
```

*   **Dual Disc Solution:** Every production cycloid drive stacks **two identical discs** driven by a double-eccentric camshaft with lobes phased exactly **$180^\circ$ apart**.
*   The equal and opposite inertia forces cancel out completely ($\Sigma \mathbf{F} = 0$).
*   *(Note on Dynamic Couples:* The axial offset distance between discs creates a small rocking couple $\mathbf{M} = \mathbf{F} \times \Delta z$; balanced counterweights on the motor shaft cancel this residual moment).

---

## 4. Output Mechanism: Wobble Extraction

Because the cycloid disc wobbles on its eccentric orbit, the output stage must transmit pure planetary rotation while absorbing the radial orbit motion $e$.

```
         Pin-in-Hole Constant-Velocity Output Mechanism
         
               Cycloid Disc Bore (D_hole)
                 ╭───────────────────╮
                (     ┌─────────┐     )
                │     │ Output  │     │ ◄── Output Pin / Roller (d_pin)
                (     │   Pin   │     )
                 ╰────┴─────────┴────╯
           Hole Diameter: D_hole = d_pin + 2 · e
```

### 4.1 Output Pin Sizing Rule
The cycloid disc contains $N_{out}$ circular holes drilled at pitch circle radius $R_{out}$.
*   Each hole receives a rigid drive pin cantilevered from the output flange.
*   **Exact Hole Clearance Dimension:**
    $$D_{hole} = d_{pin} + 2 \cdot e$$
*   This exact diameter difference allows the disc to translate radially in any direction by offset $e$ without jamming the output shaft.

---

## 5. Multi-Tooth Load Sharing vs. Involute Gears

| Performance Metric | Standard Involute Spur Gear Pair | Cycloidal Reducer | Harmonic Drive |
| :--- | :---: | :---: | :---: |
| **Simultaneous Meshing Teeth** | $1\text{–}2\text{ teeth}$ ($100\%$ load on single root) | **$30\%\text{–}50\%\text{ of pins}$** | $10\%\text{–}15\%\text{ of teeth}$ |
| **Shock Load Capacity** | Low ($150\%\text{ nominal}$) | **Immense ($500\%\text{ nominal}$)** | Moderate ($200\%\text{ nominal}$) |
| **Backlash** | $3\text{–}10\text{ arcmin}$ | **$< 1.0\text{ arcmin}$ (Preloadable)** | **Zero Backlash** |
| **Torsional Stiffness** | Medium | **Extremely High** | Low (Flexible cup) |
| **Backdrivability** | High | **Medium to Low (High inertia)** | High |
| **Catastrophic Failure Mode** | Tooth shear fracture $\implies$ Free-wheel | Roller indent $\implies$ Degraded motion | Flexspline fatigue break $\implies$ Jam |

---

## 6. References & Standards

1.  **Blanche, J. G., & Yang, D. C. (1989).** *Cycloid Drives with Machining Tolerances: Error Analysis, Tolerance Allocation, and Backlash.* Journal of Mechanisms, Transmissions, and Automation in Design, 111(3), 337–344. [DOI: 10.1115/1.3258999] (Seminal analytical tolerance stackup and contact equations).
2.  **Malhotra, V. N., & Parameswaran, M. A. (1983).** *Analysis of a cycloidal speed reducer of novel design.* Mechanism and Machine Theory, 18(3), 191–199. (Parametric epitrochoid equations and multi-pin contact load sharing).
3.  **Sensinger, J. W. (2010).** *Unified approach to cycloid drive profile, stress, and efficiency analysis.* ASME Journal of Mechanical Design, 132(2), 024503. [DOI: 10.1115/1.4001128] (Unified closed-form curvature equations and roller force distribution).
4.  **Kudryavtsev, V. N. (1966).** *Planetary Gears (Planetarnye Peredachi).* Mashinostroenie, Moscow. (Foundational kinematic synthesis of epicyclic and cycloidal mechanisms).
5.  **Nabtesco Corporation. (2022).** *Precision Reduction Gear RV Series Technical Manual.* Tokyo, Japan. (Commercial standard for dual-disc robot base cycloidal actuators).

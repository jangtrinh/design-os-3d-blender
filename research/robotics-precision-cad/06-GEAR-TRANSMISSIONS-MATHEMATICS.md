# Advanced Gear Geometry, Cycloidal Profiling & Transmission Mathematics

**Date:** 2026-09-05  
**Scope:** Mathematical derivations of involute gear teeth, trochoidal root fillets, cycloidal (epitrochoid) pin-wheel profiles, strain-wave kinematics, planetary epicyclic Willis equations, and backlash elimination mechanisms.

---

## 1. Involute Gear Geometry & Parametric Formulations

The fundamental law of gearing requires a constant angular velocity ratio between mating gears. The **involute of a circle** is the only profile that maintains a constant pressure angle and uniform conjugate action even when center-to-center distance fluctuates.

```
                  Involute Generation from Base Circle
                                  .  P (x, y)
                              .  /
                          .     /  Involute Curve
                      .        /
                  .           / Roll Line (Taut String)
              .              /
           ┌────────────────┐
          │   Base Circle   │ Radius rb
           └────────────────┘
```

### 1.1 Involute Parametric Equations
For a base circle of radius $r_b = r \cdot \cos(\alpha)$ (where $r = \frac{m \cdot z}{2}$ is pitch radius, $m$ is module, $z$ is tooth count, and $\alpha$ is pressure angle, typically $20^\circ$):
Using roll angle $\psi$ in radians:
$$x(\psi) = r_b \cdot (\cos \psi + \psi \sin \psi)$$
$$y(\psi) = r_b \cdot (\sin \psi - \psi \cos \psi)$$

In polar coordinates $(r_{inv}, \theta)$:
$$r_{inv}(\psi) = r_b \sqrt{1 + \psi^2}$$
$$\theta(\psi) = \psi - \arctan(\psi) = \text{inv}(\alpha_P)$$
Where $\text{inv}(\alpha_P) = \tan(\alpha_P) - \alpha_P$ is the **involute function**.

### 1.2 Tooth Proportions (ISO 53 Standard Module System)
For module $m$ (all dimensions in mm):
*   **Pitch Diameter ($d$):** $d = m \cdot z$
*   **Base Diameter ($d_b$):** $d_b = d \cdot \cos(\alpha)$
*   **Addendum ($h_a$):** $h_a = 1.0 \cdot m$
*   **Dedendum ($h_f$):** $h_f = 1.25 \cdot m$ (includes $0.25 \cdot m$ bottom clearance $c$)
*   **Tip Diameter ($d_a$):** $d_a = d + 2 h_a = m(z + 2)$
*   **Root Diameter ($d_f$):** $d_f = d - 2 h_f = m(z - 2.5)$
*   **Circular Pitch ($p$):** $p = \pi \cdot m$
*   **Tooth Thickness on Pitch Circle ($s$):** $s = \frac{p}{2} = \frac{\pi m}{2}$

### 1.3 Undercutting & Minimum Tooth Count ($z_{min}$)
If the tooth count is too low, the tip of the cutter gouges into the dedendum of the gear during generation, removing material at the root and drastically weakening tooth bending strength.
$$z_{min} = \frac{2}{\sin^2(\alpha)}$$
*   For standard $\alpha = 20^\circ$: $z_{min} = \frac{2}{\sin^2(20^\circ)} = \frac{2}{0.116978} \approx 17.1 \implies \mathbf{17\text{ teeth}}$.
*   For $\alpha = 25^\circ$: $z_{min} \approx 12\text{ teeth}$.
*   *Profile Shift Coefficient ($x$):* To manufacture gears with $z < 17$ without undercutting, apply a positive profile shift ($x > 0$):
    $$x_{min} = \frac{17 - z}{17}$$

---

## 2. Cycloidal (Epitrochoid) Drive Tooth Profiling

Cycloidal drives eliminate catastrophic tooth fracture because multiple teeth are engaged simultaneously, operating primarily under rolling Hertzian compression rather than cantilever bending shear.

```
       Pin Ring (R, N pins, radius Rr)
           ╭─────────────╮
       ╭───╯   O    O    ╰───╮
      │   O   ┌───────┐   O   │
      │  O    │ Cyclo │    O  │
      │   O   │ Disk  │   O   │
       ╰───╮   O    O    ╭───╯
           ╰─────────────╯
```

### 2.1 Geometric Parameters
*   $N$: Number of ring pins.
*   $Z_c$: Number of lobes on the cycloid disc ($Z_c = N - 1$).
*   $R$: Pitch radius of the pin ring.
*   $R_r$: Radius of each individual pin (or needle roller).
*   $e$: Eccentricity (offset of input cam shaft from central axis).
*   $K_1$: Shortening ratio / epicycloid coefficient:
    $$K_1 = \frac{e \cdot N}{R} < 1 \quad (\text{typically } 0.5\text{–}0.8)$$

### 2.2 Analytical Rotor Profile Equations
Parametric curve coordinates $(x(\theta), y(\theta))$ as rotation angle $\theta \in [0, 2\pi]$:
$$x(\theta) = (R - e) \cos(\theta) - R_r \cos\left(\theta + \phi(\theta)\right)$$
$$y(\theta) = -(R - e) \sin(\theta) + R_r \sin\left(\theta + \phi(\theta)\right)$$
Where the contact normal angle function $\phi(\theta)$ is:
$$\phi(\theta) = \arctan\left( \frac{\sin((1 - N)\theta)}{\frac{R}{N e} - \cos((1 - N)\theta)} \right)$$

### 2.3 Single-Stage Reduction Ratio ($R_{gear}$)
The reduction ratio of a stationary pin ring with cycloidal disc output is:
$$R_{gear} = \frac{Z_c}{N - Z_c} = \frac{N - 1}{N - (N - 1)} = N - 1$$
*Example:* With $N = 41$ pins, $Z_c = 40$ lobes $\implies R_{gear} = \mathbf{40:1}$ in a single compact stage.

---

## 3. Planetary (Epicyclic) Gearbox Mathematics

A planetary gearbox consists of Sun gear ($S$), Planet gears ($P$), Ring gear ($R$), and Planet Carrier ($C$).

```
                ┌────────────────┐ (Ring: Zr)
                │    ╭─────╮     │
                │   ( Planet)    │ (Planet: Zp)
                │    ╰──┬──╯     │
                │    ╭──┴──╮     │
                │   (  Sun  )    │ (Sun: Zs)
                │    ╰─────╯     │
                └────────────────┘
```

### 3.1 Geometric Constraints
1.  **Pitch Diameter Relationship:**
    $$d_r = d_s + 2 d_p \implies Z_r = Z_s + 2 Z_p$$
2.  **Assembly Symmetry Condition (for $N_p$ equally spaced planets):**
    $$\frac{Z_s + Z_r}{N_p} = \text{Integer}$$

### 3.2 Willis Kinematic Velocity Equation
The general relative motion equation:
$$\frac{\omega_s - \omega_c}{\omega_r - \omega_c} = -\frac{Z_r}{Z_s}$$

**Standard Planetary Configurations:**
| Input | Output | Fixed Member | Gear Ratio Formula ($i = \omega_{in}/\omega_{out}$) | Typical Range |
| :--- | :--- | :--- | :---: | :---: |
| **Sun ($S$)** | **Carrier ($C$)** | **Ring ($R$, fixed)** | $i = 1 + \frac{Z_r}{Z_s}$ | $3:1\text{ to }10:1$ |
| **Carrier ($C$)** | **Sun ($S$)** | **Ring ($R$, fixed)** | $i = \frac{1}{1 + Z_r/Z_s}$ (Step-up) | $0.1:1\text{ to }0.33:1$ |
| **Sun ($S$)** | **Ring ($R$)** | **Carrier ($C$, fixed)** | $i = -\frac{Z_r}{Z_s}$ (Reverse) | $-2:1\text{ to }-9:1$ |

---

## 4. Backlash Elimination & Preloading Techniques

Backlash causes limit-cycle oscillations, chattering, and dead-zones in closed-loop servo positioning.

### 4.1 Mechanical Backlash Elimination Methods
1.  **Dual-Path Scissor / Split Gears:**
    *   One gear is split axially into two halves coupled by internal torsional coil or wave springs.
    *   The spring forces the two halves to expand in opposite rotational directions, simultaneously contacting both the forward and reverse flanks of the mating pinion tooth.
    *   *Trade-off:* High sliding friction; lowers transmission efficiency from $95\%$ to $80\text{–}85\%$.
2.  **Center-Distance Eccentric Bushing:**
    *   Mount the pinion or intermediate shaft on an eccentric bearing housing.
    *   Rotating the housing adjusts center distance $a$ until backlash is dialed to $< 0.01\text{ mm}$ without tooth binding.
3.  **Cross-Roller Preloaded Harmonic Drives:**
    *   Elastic flexspline radial pre-deflection against the circular spline achieves continuous zero backlash across $360^\circ$.

---

## 5. References & Standards

1.  **Townsend, D. P. (1992).** *Dudley's Gear Handbook* (2nd ed.). McGraw-Hill, New York. (The definitive standard for gear tooth geometry, involute generation, rating standards, and manufacturing).
2.  **Litvin, F. L., & Fuentes, A. (2004).** *Gear Geometry and Applied Theory* (2nd ed.). Cambridge University Press. (Mathematical foundation of gear meshing, coordinate transformations, and conjugate surface generation).
3.  **ISO 53:1998.** *Cylindrical gears for general and heavy engineering — Standard basic rack tooth profile.* International Organization for Standardization.
4.  **ISO 1328-1:2013.** *Cylindrical gears — ISO system of flank tolerance classification — Part 1: Definitions and allowable values of deviations relevant to flanks of gear teeth.* International Organization for Standardization.
5.  **DIN 3960:1987-03.** *Definitions, parameters and equations for involute cylindrical gears and gear pairs.* Deutsches Institut für Normung.
6.  **Sensinger, J. W. (2010).** *Selecting proportional gains for robotic actuators to achieve desired backdrivability while maintaining stability.* IEEE Transactions on Robotics, 26(4), 742–748. (Planetary vs cycloidal vs harmonic actuator inertia and backdrivability tradeoffs).


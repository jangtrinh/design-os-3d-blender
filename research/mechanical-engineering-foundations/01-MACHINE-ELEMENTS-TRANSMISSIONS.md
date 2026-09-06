# Machine Elements & Power Transmission Systems

**Date:** 2026-09-05  
**Scope:** Shafts, keys and keyways (DIN 6885), involute splines (DIN 5480), flexible/rigid couplings, timing belts, roller chains, lead screws, and ball screws (critical speed, column buckling).

---

## 1. Shafts, Keys, Keyways & Splines

Shafts transmit rotational power and bending moments between machine elements. Fastening components to rotating shafts requires standardized positive-locking features.

```
       DIN 6885 Parallel Key Connection          DIN 5480 Involute Spline Shaft
            ┌──────────────────┐                     . - - - ' ' ' - - - .
            │    Hub / Pulley  │                  . '   ▲   ▲   ▲   ▲     ' .
            └───┬──────────┬───┘                .      │   │   │   │         .
             [=== Parallel Key ===]             │     Multiple Involute   │
            ┌───┴──────────┴───┐                │     Teeth Distributed   │
            │   Shaft (d)      │                 .     Across 360°       .
            └──────────────────┘                  .                     .
                                                    ' .             . '
```

### 1.1 Parallel Drive Keys (DIN 6885 / ISO 773)
*   **Geometry:** Rectangular or square key with rounded ends (Form A) seated in a milled shaft keyway and mating hub keyway.
*   **Standard Key Sizing (Metric):**

| Shaft Diameter ($d$, mm) | Key Width $b$ (mm) | Key Height $h$ (mm) | Shaft Depth $t_1$ (mm) | Hub Depth $t_2$ (mm) |
| :---: | :---: | :---: | :---: | :---: |
| **$6\text{–}8$** | $2$ | $2$ | $1.2$ | $1.0$ |
| **$> 8\text{–}10$** | $3$ | $3$ | $1.8$ | $1.4$ |
| **$> 10\text{–}12$** | $4$ | $4$ | $2.5$ | $1.8$ |
| **$> 12\text{–}17$** | $5$ | $5$ | $3.0$ | $2.3$ |
| **$> 17\text{–}22$** | $6$ | $6$ | $3.5$ | $2.8$ |
| **$> 22\text{–}30$** | $8$ | $7$ | $4.0$ | $3.3$ |
| **$> 30\text{–}38$** | $10$ | $8$ | $5.0$ | $3.3$ |
| **$> 38\text{–}44$** | $12$ | $8$ | $5.0$ | $3.3$ |

*   **Failure Modes & Sizing Formulas:**
    1.  **Shear Failure:** Shear stress across the key mid-plane:
        $$\tau = \frac{2 T}{d \cdot b \cdot L} \le \tau_{allow} \approx 0.5 \frac{\sigma_{yield}}{S_f}$$
    2.  **Compressive Surface Crushing:** Bearing stress against keyway flank:
        $$\sigma_{bearing} = \frac{2 T}{d \cdot (h - t_1) \cdot L} \le \sigma_{allow, bearing}$$

### 1.2 Involute Splines (DIN 5480 / ANSI B92.1)
*   **Architecture:** Multiple teeth ($Z = 10\text{–}40$) with an involute flank profile ($30^\circ$ or $37.5^\circ$ pressure angle) broached into the shaft and hub.
*   **Engineering Merits:**
    *   Torque capacity is $5\text{–}10\times$ higher than a single keyway of identical diameter.
    *   Self-centering under load; preserves dynamic balance at high RPM.
    *   No single stress concentration notch (distributes shear load uniformly around the perimeter).

---

## 2. Shaft Couplings: Rigid vs. Flexible

Couplings connect two independent rotating shafts, accommodating manufacturing misalignments (radial, axial, angular) while transmitting torque.

```
       Radial Misalignment Δr           Angular Misalignment Δθ           Axial Float Δz
          ──────┐                           ───────\                         ◄───►
                └──────                     ───────/                   ───────   ───────
```

### 2.1 Coupling Comparison Matrix

| Coupling Type | Max Angular Misalignment | Max Radial Misalignment | Torsional Stiffness | Backlash | Best Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rigid Sleeve / Clamp** | $0.0^\circ$ | $0.0\text{ mm}$ | Infinite | Zero | Precision co-axial shafts, precision line shafts |
| **Bellows Coupling** | $1.5^\circ\text{–}2.0^\circ$ | $0.15\text{–}0.30\text{ mm}$ | Extremely High | Zero | Servo motors, optical encoders, ball screws |
| **Curved Jaw (Spider)** | $1.0^\circ$ | $0.10\text{–}0.20\text{ mm}$ | Medium (damping) | Zero (curved preloaded polyurethane) | General motion control, vibration damping |
| **Oldham Coupling** | $0.5^\circ$ | Up to $1.5\text{ mm}$ | Moderate | Low | Large radial offset parallel shafts |
| **Disc Pack (Flexible)** | $1.0^\circ$ | $0.10\text{–}0.25\text{ mm}$ | Very High | Zero | High-speed turbomachinery, CNC spindles |

---

## 3. Synchronous Timing Belts & Chain Drives

### 3.1 Timing Belts: GT2, GT3, and HTD Profiles
Synchronous toothed belts provide positive, non-slip power transmission with zero lubrication and low acoustic noise.

```
          Trapezoidal (Legacy T-Series)             Curvilinear (Gates GT2 / GT3)
                ┌───┐                                     ╭───╮
               /     \                                   /     \
              /       \                                 (       )
          ───┴─────────┴───                         ───┴─────────┴───
          High tooth-corner stress                  Uniform stress, deep tooth
          Prone to ratcheting                       Zero backlash tooth engagement
```

*   **Pitch Standards:**
    *   **GT2 (2.0 mm pitch):** The gold standard for 3D printers, laser cutters, and lightweight robotics.
    *   **GT3 (3.0 mm / 5.0 mm pitch):** Industrial automation, medium robot arm joints.
    *   **HTD (3M, 5M, 8M):** High torque drives, heavy industrial conveyors.
*   **Center Distance Calculation ($C$):**
    $$L_{belt} \approx 2C + \frac{\pi (D_1 + D_2)}{2} + \frac{(D_2 - D_1)^2}{4C}$$
*   **Minimum Teeth in Mesh (TIM):**
    $$\text{TIM} = Z_{small} \cdot \left(0.5 - \frac{D_2 - D_1}{6 C}\right) \ge \mathbf{6\text{ teeth}}$$
    If $\text{TIM} < 6$, derate the maximum permissible belt torque proportionally.

### 3.2 Roller Chains (ISO 606 / ANSI B29.1)
*   **Chordal Action (Polygonal Effect):** Roller chain links are rigid chords. As the chain enters the sprocket, the effective pitch radius oscillates between $r_{max} = \frac{p}{2 \sin(180^\circ/Z)}$ and $r_{min} = \frac{p}{2 \tan(180^\circ/Z)}$.
*   *Design Rule:* Sprocket tooth count $Z \ge 17$ (recommended $Z \ge 19\text{–}21$ for high-speed drives) to suppress chordal velocity ripple and vibration.

---

## 4. Lead Screws & Ball Screws: Kinematics, Critical Speed & Buckling

Linear screws convert rotational torque into linear thrust force:
$$F = \frac{2 \pi \cdot T \cdot \eta}{p}$$
Where $p$ is lead (travel per revolution), $\eta$ is mechanical efficiency ($\eta \approx 0.30\text{–}0.50$ for acme lead screws; $\eta \ge 0.90$ for precision ball screws).

### 4.1 Critical Whirling Speed ($n_c$)
At high rotational speeds, centrifugal forces cause the slender screw shaft to vibrate violently at its transverse natural bending frequency.
$$n_c = k \cdot \frac{d_r}{L^2} \times 10^7 \quad (\text{rpm})$$
Where:
*   $d_r$: Root diameter of the screw thread (mm).
*   $L$: Unsupported screw length between bearings (mm).
*   $k$: Support bearing fixity factor:
    *   **Fixed – Fixed:** $k = 25.5$
    *   **Fixed – Supported:** $k = 17.7$
    *   **Supported – Supported:** $k = 11.5$
    *   **Fixed – Free:** $k = 3.9$
*   *Operating Limit:* Operating speed must satisfy $n_{max} \le 0.80 \cdot n_c$.

### 4.2 Column Buckling (Euler Critical Load $P_{cr}$)
When the screw is subjected to compressive axial thrust loads, it can buckle elastically.
$$P_{cr} = f_p \cdot \frac{\pi^2 E I}{L^2} = f_p \cdot \frac{\pi^3 E d_r^4}{64 L^2}$$
Where:
*   $E$: Young's modulus ($2.1 \times 10^5\text{ MPa}$ for alloy steel).
*   $I = \frac{\pi d_r^4}{64}$: Second moment of area of the root core.
*   $f_p$: End fixity buckling coefficient:
    *   **Fixed – Fixed:** $f_p = 4.0$
    *   **Fixed – Supported:** $f_p = 2.0$
    *   **Supported – Supported:** $f_p = 1.0$
    *   **Fixed – Free:** $f_p = 0.25$
*   *Safety Factor:* Maximum allowable operating compression force $P_{max} \le 0.50 \cdot P_{cr}$.

---

## 5. References & Standards

1.  **Budynas, R. G., & Nisbett, J. K. (2020).** *Shigley's Mechanical Engineering Design* (11th ed.). McGraw-Hill Education, New York. (Comprehensive standards for shaft stress, fatigue design, keys, bearings, and lead screws).
2.  **DIN 6885-1:1968-08.** *Drive Type Fastenings without Taper Action; Parallel Keys, Keyways, Deep Pattern.* Deutsches Institut für Normung. (Standard dimensions and torque capacities for drive keys).
3.  **DIN 5480-1:2006-03.** *Involute splines based on reference diameters — Generalities and fundamentals.* Deutsches Institut für Normung.
4.  **ISO 281:2007.** *Rolling bearings — Dynamic load ratings and rating life.* International Organization for Standardization. (L10 bearing life formulas and reliability factors).
5.  **ISO 3408-3:2006.** *Ball screws — Part 3: Acceptance conditions and acceptance tests.* International Organization for Standardization. (Whirling speed and permissible axial buckling calculations).
6.  **ISO 606:2015.** *Short-pitch transmission precision roller and bush chains, attachments and associated chain sprockets.* International Organization for Standardization.


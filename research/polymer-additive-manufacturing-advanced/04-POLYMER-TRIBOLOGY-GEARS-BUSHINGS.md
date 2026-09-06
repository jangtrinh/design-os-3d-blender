# Tribology of 3D Printed Polymers: Gears, Bushings & Sliding Mechanisms

Designing dry, unlubricated 3D printed mechanical components (actuator gears, linear guide bushings, gimbal pivots) requires balancing **contact pressure ($P$)**, **sliding velocity ($V$)**, **frictional heating**, and **adhesive/abrasive wear**.

---

## 1. The Pressure-Velocity ($PV$) Operating Limit

Polymer sliding contacts are not limited by mechanical shear yield, but by **frictional heat dissipation**:

$$q_{fric} = \mu \cdot P \cdot V \quad \left[\frac{\text{W}}{\text{m}^2}\right]$$

Because plastics have low thermal conductivity ($k \approx 0.2\text{ W/m}\cdot\text{K}$), heat generated at microscopic asperity contact junctions cannot conduct away quickly.

```
                         PV Operating Boundary
         Pressure (P) [MPa]
                ▲
                │  \  Thermal Melting Failure Zone
                │   \  (Contact surface temperature exceeds Tg/Tm)
                │    \
                │ Safe \
                │ Oper. \  PV_max Boundary Curve
                │ Zone   \
                └─────────┴────────────────► Sliding Velocity (V) [m/s]
```

### 1.1 The Steady-State Surface Temperature Formula
For a polymer bushing of wall thickness $t$ operating against a steel shaft of radius $R$:
$$\Delta T = T_{surface} - T_{ambient} = \mu \cdot P \cdot V \cdot \left( \frac{t}{k_{polymer}} + R_{th, shaft} \right)$$
*Failure Criterion:* If $T_{surface} \ge T_g$ (for amorphous plastics) or $T_{surface} \ge \text{HDT}$ (for semi-crystalline plastics), the polymer softens, the true contact area expands catastrophically, friction spikes, and the part seizes or melts.

### 1.2 Quantitative $PV_{max}$ Limits by Material

| Polymer | Dynamic Coeff. of Friction ($\mu$ dry) | Max Continuous $P$ | Max Sliding $V$ | $PV_{max}$ Limit (Dry) |
| :--- | :---: | :---: | :---: | :---: |
| **Standard PLA** | $0.38\text{–}0.50$ | $4\text{ MPa}$ | $0.2\text{ m/s}$ | $0.08\text{ MPa}\cdot\text{m/s}$ (Poor, softens at $55^\circ\text{C}$) |
| **PETG** | $0.35\text{–}0.45$ | $6\text{ MPa}$ | $0.3\text{ m/s}$ | $0.12\text{ MPa}\cdot\text{m/s}$ |
| **Nylon PA12** | $0.20\text{–}0.28$ | $15\text{ MPa}$ | $1.0\text{ m/s}$ | $0.35\text{ MPa}\cdot\text{m/s}$ (Good natural lubricity) |
| **POM / Polyacetal (Delrin)** | **$0.15\text{–}0.22$** | **$20\text{ MPa}$** | **$1.5\text{ m/s}$** | **$0.60\text{ MPa}\cdot\text{m/s}$ (The Gear Standard)** |
| **igus iglidur I150 / I180 (3D)** | **$0.12\text{–}0.18$** | **$25\text{ MPa}$** | **$1.2\text{ m/s}$** | **$0.85\text{ MPa}\cdot\text{m/s}$ (Tribo-Optimized)** |
| **PEEK (Unfilled)** | $0.25\text{–}0.32$ | $40\text{ MPa}$ | $2.5\text{ m/s}$ | $1.50\text{ MPa}\cdot\text{m/s}$ |
| **PEEK + 10% PTFE + 10% CF** | **$0.10\text{–}0.14$** | **$65\text{ MPa}$** | **$3.5\text{ m/s}$** | **$3.20\text{ MPa}\cdot\text{m/s}$ (Extreme Performance)** |

---

## 2. Wear Rates & The Archard-Lancaster Wear Model

Material volumetric loss $\Delta V$ over total sliding distance $L$ under normal load $W$:

$$\Delta V = k_w \cdot W \cdot L$$

Where $k_w$ is the **Specific Wear Rate** (units: $\text{mm}^3 / (\text{N}\cdot\text{m})$ or $10^{-6}\text{ mm}^3 / \text{J}$).

```
              Archard Asperity Wear at Sliding Interface
              
         Polymer Slider ───► Velocity V
         ┌──────────────────────────────────────┐
         │       ▲             ▲        ▲       │
         │      / \           / \      / \      │
         └─────┴───┴─────────┴───┴────┴───┴─────┘
                 •             •        •  ◄── Real Contact Junctions (True Area Ar << A_nom)
         ┌─────┬───┬─────────┬───┬────┬───┬─────┐
         │      \ /           \ /      \ /      │
         │       ▼             ▼        ▼       │
         └──────────────────────────────────────┘
         Hard Ground Steel Shaft (Ra = 0.2 µm)
```

### 2.1 Depth of Wear Calculation for Bushings
For a radial bushing of bore diameter $D$, length $B$, carrying radial load $F_{rad}$ over operational hours $t_{hours}$ at shaft speed $n$ (rpm):
*   Sliding velocity: $V = \pi D \frac{n}{60}$.
*   Total sliding distance: $L = V \cdot (t_{hours} \times 3600)$.
*   Radial wear depth ($\Delta r$):
    $$\Delta r = \frac{\Delta V}{A_{projected}} = \frac{k_w \cdot F_{rad} \cdot L}{D \cdot B} = k_w \cdot P \cdot L$$
*   *Design Target:* For a robot joint requiring $< 50\ \mu\text{m}$ radial play over $2000\text{ hours}$ of continuous operation:
    $$k_w \le \frac{0.050\text{ mm}}{P \cdot L}$$

---

## 3. The Carbon Fiber Shaft Abrasion Trap

While Carbon-Fiber reinforced filaments (PA-CF, PET-CF) provide exceptional structural stiffness ($E > 8\text{–}12\text{ GPa}$), **chopped carbon fibers are harder than most metals** ($\approx 70\text{ HRC}$ equivalent micro-hardness).

```
   Polymer Matrix           Broken Carbon Fiber Ends Act as Micro-Lathe Chisels!
   ┌──────────────┐                       ▼
   │  PA12 Resin  │              ┌─────────────────┐
   │              │              │  / / / / / / /  │
   └──────────────┘              └─────────────────┘
   ───────────────────────────────────────────────── ◄── Scratches & Gouges!
   Soft 304 Stainless Steel or Aluminum Shaft (Ra > 1.5 µm within hours)
```

### 3.1 Counter-Face Hardness Matching Rules
1.  **Never run CF-reinforced polymers directly against unhardened 300-series stainless steel, brass, or aluminum shafts.** The microscopic broken needle ends of carbon fibers gouge the metal surface through three-body abrasive wear, destroying shaft roundness.
2.  **Required Counter-Face Specs for CF Polymers:**
    *   Hardness: **$\ge 58\text{–}62\text{ HRC}$** (e.g., Case-hardened AISI 1060 or 52100 bearing steel).
    *   Surface finish: Superfinished / ground to **$R_a \le 0.1\text{–}0.2\ \mu\text{m}$**.
    *   *Alternative:* Press an off-the-shelf sintered bronze bushing or Delrin sleeve into the 3D printed PA-CF housing to decouple structural loads from the sliding interface.

---

## 4. Solid Lubricant Additives in Filament Formulations

To achieve true dry running with zero external grease (essential in optical instruments, space mechanisms, and cleanrooms):
*   **PTFE (Teflon) Particles ($5\text{–}15\%\text{ wt}$):**
    *   During initial sliding (run-in period), soft PTFE shears microscopically and transfers onto the steel counterface, creating a protective **low-friction transfer film**.
    *   Drops friction $\mu$ from $0.35$ down to $0.12$.
*   **Molybdenum Disulfide ($\text{MoS}_2$) & Graphite:**
    *   Lamellar solid lubricants; atomic hexagonal sheets slip easily over one another under shear stress.
    *   Resist extreme contact pressures ($> 100\text{ MPa}$) where liquid oil would be squeezed out.
*   **Silicone Oil Micro-Encapsulation:**
    *   Microscopic droplets of silicone oil are emulsified within the polymer resin pellets.
    *   As the surface wears, fresh micro-droplets rupture, continuously replenishing liquid lubrication at the contact asperities.

---

## 5. Gear Tooth Wear & Scoring (Flash Temperature)

For 3D printed spur and helical gears:
*   **Blok's Flash Temperature Formula ($\Theta_{flash}$):**
    $$\Theta_{flash} = \frac{1.11 \mu W_{bt} (v_1^{1/2} - v_2^{1/2})}{\sqrt{k \rho C_p} \cdot b_H^{1/2}}$$
    Where $v_1, v_2$ are rolling/sliding surface velocities at the gear pitch point, $b_H$ is Hertzian half-width.
*   *Design Practice:* 3D printed plastic gears run best in **dissimilar material pairs**:
    *   Pair a **POM/Delrin pinion** with a **PA12/Nylon bull gear**.
    *   Identical plastics (e.g. POM running against POM, or PLA on PLA) exhibit high mutual adhesion and rapid scuffing/galling.

---

## 6. References & Standards

1.  **Archard, J. F. (1953).** *Contact and Rubbing of Flat Surfaces.* Journal of Applied Physics, 24(8), 981–988. [DOI: 10.1063/1.1721448] (Foundational theory of adhesive contact and specific wear coefficients).
2.  **Lancaster, J. K. (1969).** *Relationships between the wear of polymers and their mechanical properties.* Proceedings of the Institution of Mechanical Engineers, 183(16), 98–104. (Wear of engineering polymers and transfer film formation on steel).
3.  **Blok, H. (1937).** *Theoretical study of temperature rise at surfaces of actual contact under oiliness conditions.* General Discussion on Lubrication, Institution of Mechanical Engineers, 2, 222–235. (Original flash temperature equations for gear teeth scuffing).
4.  **ASTM G99-17.** *Standard Test Method for Wear Testing with a Pin-on-Disk Apparatus.* ASTM International. (Standard methodology for measuring dry friction coefficients and wear rates).
5.  **DIN 50324:1992-07.** *Tribology; testing of friction and wear; model test for sliding friction of solids (ball-on-prism, pin-on-disk).* Deutsches Institut für Normung.
6.  **igus GmbH. (2023).** *iglidur Polymer Tribology and Bearing Design Manual.* Cologne, Germany. (Empirical PV maps, wear rates against various shaft materials, and temperature correction factors).

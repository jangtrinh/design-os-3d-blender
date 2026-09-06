# Hertzian Contact Stress, Subsurface Shear & Spalling Fatigue

When curved machine elements press against each other under heavy loads (gear teeth meshing, ball/roller bearing raceways, cam-followers), the contact area starts as a theoretical point or line of zero area, yielding singular stresses before elastic deformation creates a small contact footprint. **Hertzian Contact Mechanics** governs this regime.

---

## 1. Effective Radii & Equivalent Elastic Modulus

```
              Contact Between Two General Curved Bodies (1 & 2)
              
                 Body 1 (R1x, R1y, E1, ν1)
                     ╭─────────────╮
                    (       ▲       )
                     ╰──────▼──────╯
                    ═════════════════ ◄── Contact Footprint (Ellipse or Strip)
                     ╭──────▲──────╮
                    (       ▼       )
                 Body 2 (R2x, R2y, E2, ν2)
```

### 1.1 Equivalent Elastic Modulus ($E^*$)
Both bodies deform elastically according to their Young's modulus ($E$) and Poisson's ratio ($\nu$):
$$\frac{1}{E^*} = \frac{1 - \nu_1^2}{E_1} + \frac{1 - \nu_2^2}{E_2}$$
For two identical bearing steel bodies ($E_1 = E_2 = 210\text{ GPa}$, $\nu_1 = \nu_2 = 0.30$):
$$\frac{1}{E^*} = \frac{1 - 0.09}{210 \times 10^9} + \frac{1 - 0.09}{210 \times 10^9} = \frac{1.82}{210 \times 10^9} \implies \mathbf{E^* \approx 115.4\text{ GPa}}$$

### 1.2 Equivalent Relative Curvature Radius ($R^*$)
$$\frac{1}{R^*} = \frac{1}{R_1} + \frac{1}{R_2}$$
*(Sign convention: Convex surface is positive $+R$; concave conforming raceway is negative $-R$).*

---

## 2. Line Contact Mechanics (Cylindrical Rollers, Spur Gears)

Two parallel cylinders of radii $R_1, R_2$ pressed together along contact length $L$ by normal force $F$:

```
               Line Contact Pressure Distribution
               
                 Normal Load F
                      ▼
               ╭─────────────╮
               │ Cylinder 1  │
               ╰──────┬──────╯
         -b ──────────┼────────── +b
         ( \        p0 (Peak)   / )  ◄── Semi-Elliptical Pressure Profile
         ───────────────────────────
               │ Cylinder 2  │
               ╰─────────────╯
```

### 2.1 Contact Half-Width ($b$)
$$b = \sqrt{\frac{4 F R^*}{\pi L E^*}}$$

### 2.2 Maximum Contact Pressure ($p_0$)
$$p_0 = \frac{2 F}{\pi b L} = \sqrt{\frac{F E^*}{\pi L R^*}}$$
Pressure distribution across the strip $-b \le x \le +b$:
$$p(x) = p_0 \sqrt{1 - \left(\frac{x}{b}\right)^2}$$

---

## 3. Point Contact Mechanics (Ball Bearings, Crossed Rollers)

Two spheres of radii $R_1, R_2$ pressed together by force $F$ deform into a circular contact area of radius $a$:

### 3.1 Contact Radius ($a$)
$$a = \left( \frac{3 F R^*}{4 E^*} \right)^{1/3}$$

### 3.2 Maximum Peak Contact Pressure ($p_0$)
$$p_0 = \frac{3 F}{2 \pi a^2} = \left( \frac{6 F {E^*}^2}{\pi^3 {R^*}^2} \right)^{1/3}$$
*Notice the cubic root:* Tripling the load $F$ increases peak contact pressure $p_0$ by only $3^{1/3} \approx 1.44\times$ ($+44\%$), but exponentially escalates fatigue damage.

---

## 4. Subsurface Shear Stress & The Spalling Fatigue Mechanism

The most critical, counter-intuitive insight in contact mechanics: **Maximum shear stress does NOT occur on the surface contact plane, but at a depth $z_{max}$ BELOW the surface!**

```
   Surface Contact Plane (z = 0) ───► Maximum Hydrostatic Compression (p0)
   ────────────────────────────────────────────────────────────────────────
   Depth z = 0.48 b              ───► ★ MAXIMUM SHEAR STRESS (τ_max = 0.300 p0)
                                      Micro-crack initiates at material inclusions!
   ────────────────────────────────────────────────────────────────────────
   Deep Substrate (z > 2 b)      ───► Stresses decay to zero
```

### 4.1 Subsurface Stress Distribution Under Line Contact
At depth $z$ beneath the center axis of contact:
*   $\sigma_x = -p_0 \left( \frac{1 + 2 z^2/b^2}{\sqrt{1 + z^2/b^2}} - 2 \frac{z}{b} \right)$
*   $\sigma_z = -\frac{p_0}{\sqrt{1 + z^2/b^2}}$
*   Maximum Shear Stress ($\tau_{max} = \frac{|\sigma_z - \sigma_x|}{2}$):
    $$\tau_{max} \approx \mathbf{0.300 \cdot p_0} \quad \text{at depth } \mathbf{z \approx 0.786 \cdot b}$$
    *(For point contact: $\tau_{max} \approx \mathbf{0.310 \cdot p_0}$ at depth $\mathbf{z \approx 0.48 \cdot a}$).*

### 4.2 The Spalling (Flaking) Fatigue Failure Process
1.  **Inclusion Shear Fatigue:** Steel is not perfectly pure; it contains microscopic aluminum oxide ($Al_2O_3$) and manganese sulfide ($MnS$) non-metallic inclusions.
2.  **Subsurface Void Nucleation:** Because $\tau_{max}$ peaks $\sim 0.2\text{–}0.5\text{ mm}$ beneath the polished raceway, high cyclic shear strains initiate microscopic fatigue micro-cracks at these internal inclusions.
3.  **Crack Propagation:** Under millions of rolling load cycles, the micro-crack propagates horizontally parallel to the surface.
4.  **Spalling Ejection:** Hydraulic pressure from lubricating oil forces the crack to turn upward toward the surface. A chunk of metal tears out, forming a crater ("spall" or pit), destroying the bearing or gear.

```
       Step 1: Subsurface Crack         Step 2: Upward Branching        Step 3: Metal Spall Ejection
       ────────────────────────         ───────╮        ╭───────        ───────\              /───────
          • Micro-crack at depth                \      /                        \   Pit / Spall/
          ─── ─── ─── (τ_max)                    \────/                          \____________/
```

---

## 5. Permissible Hertzian Stress Design Limits

| Component / Material Pairing | Hardness | Max Allowable Static $p_0$ | Max Dynamic $p_0$ ($10^7$ cycles) |
| :--- | :---: | :---: | :---: |
| **High-Precision Bearing Steel (52100)** | $60\text{–}64\text{ HRC}$ | **$4,000\text{ MPa}$** | **$1,800\text{–}2,200\text{ MPa}$** |
| **Carburized Alloy Steel Gears (8620/4320)**| $58\text{–}62\text{ HRC}$ | $2,800\text{ MPa}$ | $1,400\text{–}1,600\text{ MPa}$ |
| **Nitrided Tool Steel (4140/H13)** | $55\text{–}60\text{ HRC}$ | $2,200\text{ MPa}$ | $1,100\text{–}1,300\text{ MPa}$ |
| **Through-Hardened Carbon Steel (1045)** | $45\text{–}50\text{ HRC}$ | $1,400\text{ MPa}$ | $750\text{ MPa}$ |
| **Structural Aluminum (6061-T6)** | $95\text{ HB}$ | $350\text{ MPa}$ | $180\text{ MPa}$ (Brunelling occurs easily) |
| **Engineering Polymer (POM / Delrin)** | $120\text{ R-scale}$ | $120\text{ MPa}$ | $45\text{ MPa}$ |

---

## 6. References & Standards

1.  **Hertz, H. (1881).** *Ueber die Berührung fester elastischer Körper (On the contact of rigid elastic solids).* Journal für die reine und angewandte Mathematik, 92, 156–171. (The foundational paper establishing contact mechanics).
2.  **Johnson, K. L. (1985).** *Contact Mechanics.* Cambridge University Press. (The comprehensive classical treatise on elastic and plastic contact, rolling friction, and subsurface stress tensors).
3.  **ISO 281:2007.** *Rolling bearings — Dynamic load ratings and rating life.* International Organization for Standardization. (Basic rating life $L_{10}$ based on subsurface shear stress volume integrals).
4.  **AGMA 2001-D04.** *Fundamental Rating Factors and Calculation Methods for Involute Spur and Helical Gear Teeth.* American Gear Manufacturers Association. (Pitting resistance and Hertzian contact stress limits).
5.  **Lundberg, G., & Palmgren, A. (1947).** *Dynamic capacity of rolling bearings.* Acta Polytechnica, Mechanical Engineering Series, 1(3), 1–50. (Statistical theory of bearing fatigue initiated by subsurface shear stresses).

# Continuous Fiber Reinforced Thermoplastics (CFRTP) & Co-Extrusion

While short chopped carbon fibers ($10\text{–}20\%\text{ by weight}$, fiber length $L < 150\ \mu\text{m}$) only modestly increase tensile modulus, **Continuous Fiber Co-Extrusion** (Markforged CFF, Anisoprint CFC) embeds continuous carbon, Kevlar, or continuous fiberglass strands inside thermoplastic matrices, achieving specific tensile strength comparable to 6061-T6 aluminum.

---

## 1. Chopped vs. Continuous Fiber Mechanics

```
   Short Chopped Fibers (Discontinuous)          Continuous Fiber Towpreg (Endless)
   ┌───────────────────────────────────┐        ┌───────────────────────────────────┐
   │  ───  ╱   │   ╲   ───   │   ╱     │        │ ═════════════════════════════════ │
   │   ╱   ───  ╲   ───   │   ───   ╲  │        │ ═════════════════════════════════ │
   └───────────────────────────────────┘        └───────────────────────────────────┘
   Fibers pull out of matrix below critical     Fibers carry 95%+ of axial tension directly;
   transfer length Lc (Shear Lag failure).      Tensile strength governed by fiber fracture.
```

### 1.1 The Kelly-Tyson Shear-Lag Model & Critical Length ($L_c$)
Load is transferred from the soft polymer matrix to an embedded fiber via interfacial shear stress $\tau_i$:
$$L_c = \frac{\sigma_f^* \cdot d_f}{2 \tau_i}$$
Where:
*   $\sigma_f^*$: Ultimate tensile strength of the fiber ($\approx 3500\text{–}4000\text{ MPa}$ for high-strength PAN carbon fiber).
*   $d_f$: Filament fiber diameter ($5\text{–}7\ \mu\text{m}$).
*   $\tau_i$: Matrix shear yield strength or interfacial bond strength ($\approx 30\text{–}50\text{ MPa}$ for polyamide).
*   *Calculation:* For carbon fiber in nylon, $L_c \approx \frac{4000 \times 7\ \mu\text{m}}{2 \times 40} \approx 350\ \mu\text{m} = 0.35\text{ mm}$.
*   *Failure Mode of Chopped Fibers:* Average fiber length in commercial FDM filaments is only $50\text{–}120\ \mu\text{m} \ll L_c$. Because the fiber length is shorter than $L_c$, fibers cannot be stressed to their ultimate strength; failure occurs by **fiber pull-out and matrix debonding**, limiting tensile strength to $< 80\text{–}110\text{ MPa}$.
*   *Continuous Fibers:* Length $L \gg L_c$ across the entire component; tensile strength reaches **$600\text{–}900\text{ MPa}$**.

---

## 2. Micromechanics: Voigt-Reuss Rule of Mixtures

For a composite with fiber volume fraction $V_f$ and matrix volume fraction $V_m = 1 - V_f$:

```
                   Longitudinal Tension (E1)          Transverse Tension (E2)
                        Load Direction                     Load Direction
                              ──►                                ▲
                    ┌───────────────────────┐                    │
                    │ ═════════════════════ │                    │ Matrix Governed
                    │ ═════════════════════ │                    ▼
```

### 2.1 Longitudinal Modulus ($E_1$ - Voigt Isostrain Model)
In the fiber direction, both phases experience equal strain ($\epsilon_1 = \epsilon_f = \epsilon_m$):
$$E_1 = V_f E_f + (1 - V_f) E_m \approx V_f E_f \quad (\text{since } E_f \gg E_m)$$
For continuous carbon fiber towpreg ($E_f = 230\text{ GPa}$) in Nylon PA6 ($E_m = 2.0\text{ GPa}$) at $V_f = 0.35$:
$$E_1 = (0.35)(230) + (0.65)(2.0) = 80.5 + 1.3 = \mathbf{81.8\text{ GPa}} \quad (\text{vs. 6061-T6 Aluminum: } 69\text{ GPa})$$

### 2.2 Transverse Modulus ($E_2$ - Reuss Isostress Model)
Perpendicular to the fibers, both phases experience equal stress ($\sigma_2 = \sigma_f = \sigma_m$):
$$\frac{1}{E_2} = \frac{V_f}{E_f} + \frac{1 - V_f}{E_m} \implies E_2 = \frac{E_f E_m}{V_f E_m + (1 - V_f) E_f}$$
At $V_f = 0.35$:
$$E_2 = \frac{230 \times 2.0}{(0.35)(2.0) + (0.65)(230)} = \frac{460}{0.7 + 149.5} = \mathbf{3.06\text{ GPa}}$$
*Orthotropic Ratio:* $E_1 / E_2 \approx 81.8 / 3.06 \approx \mathbf{26.7 : 1}$. Continuous fiber composites are ultra-rigid in the fiber direction but compliant transversely.

---

## 3. Toolpath Strategies: Concentric vs. Isotropic Fill

```
      Concentric Reinforcement Rings              Isotropic Quasi-Isotropic (0°/45°/90°/-45°)
      ┌──────────────────────────────────┐        ┌──────────────────────────────────┐
      │  ╭────────────────────────────╮  │        │ //////////////////////////////// │
      │  │  ╭──────────────────────╮  │  │        │ \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ │
      │  │  │   Hole Clearance     │  │  │        │ ──────────────────────────────── │
      │  │  │      (   )           │  │  │        │ |||||||||||||||||||||||||||||||| │
      │  │  ╰──────────────────────╯  │  │        │                                  │
      │  ╰────────────────────────────╯  │        │ Quasi-isotropic planar stiffness │
      └──────────────────────────────────┘        └──────────────────────────────────┘
      Fibers wrap continuously around holes;      Eliminates directional weakness;
      Zero interrupted fibers, max pull-out!      mimics balanced aerospace prepreg.
```

### 3.1 Concentric Fiber Rings
*   Continuous fiber tows are looped around exterior perimeters and internal bolt clearance holes.
*   **Drilled Hole vs. Molded-In Fiber Loop:**
    *   *Drilling* an aftermarket hole cuts through structural continuous fibers, creating severe stress concentration factor $K_t \ge 3.0$.
    *   *Molded-in 3D printed concentric fiber rings* guide continuous fibers seamlessly around the hole without cutting. Hoop tensile forces flow smoothly around the fastener shank.

### 3.2 Classical Laminate Theory (CLT) for Isotropic Layups
By stacking layers at balanced symmetric angles ($[0^\circ / +45^\circ / 90^\circ / -45^\circ]_s$), the in-plane stiffness matrix $[A]$ becomes isotropic:
$$E_x = E_y = \frac{A_{11} A_{22} - A_{12}^2}{A_{22} \cdot h_{total}}$$
This eliminates planar warping and thermal curl during ambient cooling.

---

## 4. Sandwich Panel Theory for High Flexural Rigidity

Bending rigidity $D$ scales with the cube of distance from the neutral axis ($I = \frac{b h^3}{12}$). Solid continuous fiber printing is expensive and heavy.

```
                  CFRTP Sandwich Beam Architecture
                  
      ══════════════════════════════════════ ◄── Top Carbon Face Sheet (Tension)
      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
      ░░░░ Lightweight Infill Core ░░░░░░░░░ ◄── Absorbs Transverse Shear Stress
      ░░░░ (Cellular Gyroid / Honeycomb) ░░░░     Thickness = c
      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
      ══════════════════════════════════════ ◄── Bottom Carbon Face Sheet (Compression)
```

### 4.1 Bending Stiffness Formulation
For two face sheets of thickness $t_f$ separated by core of thickness $c$:
$$D = E_f \cdot \frac{b \cdot t_f \cdot (c + t_f)^2}{2} + E_c \cdot \frac{b c^3}{12}$$
Since $E_f \gg E_c$ ($80\text{ GPa}$ vs. $0.5\text{ GPa}$):
$$D \approx \frac{E_f \cdot b \cdot t_f \cdot c^2}{2}$$
*Key Insight:* Doubling the core thickness $c$ quadruples the bending stiffness with zero added high-cost carbon fiber!

---

## 5. Continuous Fiber Material Selection Matrix

| Fiber Reinforcement | Tensile Strength | Elastic Modulus | Elongation at Break | Impact Absorption | Primary Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Continuous Carbon Fiber** | $800\text{ MPa}$ | $60\text{–}85\text{ GPa}$ | $1.5\%$ | Low (Brittle) | Robot arm structural links, chassis brackets, drone arms. |
| **Continuous Kevlar (Aramid)** | $610\text{ MPa}$ | $27\text{ GPa}$ | $2.7\%$ | **Maximum (Tough)** | Robotic end-effector bumpers, gripper fingers, impact shields. |
| **High-Strength High-Temp Fiberglass (HSHT)** | $590\text{ MPa}$ | $21\text{ GPa}$ | $3.8\%$ | High | High operating temperature fixtures ($> 140^\circ\text{C}$), autoclave tooling. |
| **Standard Continuous Glass Fiber** | $590\text{ MPa}$ | $21\text{ GPa}$ | $3.8\%$ | High | Cost-effective structural reinforcement ($1/3$ cost of Carbon). |

---

## 6. References & Standards

1.  **Hull, D., & Clyne, T. W. (1996).** *An Introduction to Composite Materials* (2nd ed.). Cambridge University Press. (Definitive derivation of Kelly-Tyson shear lag, critical fiber length, and rule of mixtures).
2.  **Jones, R. M. (1999).** *Mechanics of Composite Materials* (2nd ed.). CRC Press / Taylor & Francis. (Classical Laminate Theory, ABD stiffness matrices, and failure criteria: Tsai-Hill, Tsai-Wu).
3.  **Mark, G. T., & Gozdz, A. S. (2016).** *Apparatus and Method for Additive Manufacturing of Continuous Fiber Reinforced Parts.* US Patent 9,149,988. MarkForged Inc. (Core patents on fiber ironing nozzles and cutting mechanics).
4.  **Matsuzaki, R., et al. (2016).** *Three-dimensional printing of continuous-fiber composites by in-nozzle impregnation.* Scientific Reports, 6, 23058. [DOI: 10.1038/srep23058] (Open-source co-extrusion thermodynamics and void content characterization).
5.  **ASTM D3039/D3039M-17.** *Standard Test Method for Tensile Properties of Polymer Matrix Composite Materials.* ASTM International.
6.  **ISO 14125:1998.** *Fibre-reinforced plastic composites — Determination of flexural properties.* International Organization for Standardization.

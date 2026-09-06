# Additive Anisotropy, Interlayer Bonding & Slicing Mechanics

**Date:** 2026-09-05  
**Scope:** Orthotropic constitutive modeling of FDM components, polymer chain reptation kinetics at the layer weld line, bead cross-section geometry, and perimeter-to-infill structural optimization.

---

## 1. Orthotropic Material Mechanics & The Z-Axis Penalty

Fused Deposition Modeling (FDM) does not produce isotropic solid bodies. Parts behave mechanically as **transversely isotropic (orthotropic) laminates**.

```
              Coordinate Axes in Additive Manufacturing
              
                      Z (Build Axis - Interlayer Weld)
                      ▲
                      │  Tensile Strength: 30%–60% of XY
                      │
                      │       Y (Transverse Bead Axis)
                      │      /
                      │     /
                      └────┼─────► X (Longitudinal Toolpath Axis)
                                  Tensile Strength: 100%
```

### 1.1 The Orthotropic Stiffness Tensor
The elastic constitutive matrix relating stresses $\boldsymbol{\sigma}$ to strains $\boldsymbol{\epsilon}$:
$$\begin{bmatrix} \epsilon_{xx} \\ \epsilon_{yy} \\ \epsilon_{zz} \\ \gamma_{yz} \\ \gamma_{zx} \\ \gamma_{xy} \end{bmatrix} = \begin{bmatrix} 1/E_x & -\nu_{yx}/E_y & -\nu_{zx}/E_z & 0 & 0 & 0 \\ -\nu_{xy}/E_x & 1/E_y & -\nu_{zy}/E_z & 0 & 0 & 0 \\ -\nu_{xz}/E_x & -\nu_{yz}/E_y & 1/E_z & 0 & 0 & 0 \\ 0 & 0 & 0 & 1/G_{yz} & 0 & 0 \\ 0 & 0 & 0 & 0 & 1/G_{zx} & 0 \\ 0 & 0 & 0 & 0 & 0 & 1/G_{xy} \end{bmatrix} \begin{bmatrix} \sigma_{xx} \\ \sigma_{yy} \\ \sigma_{zz} \\ \tau_{yz} \\ \tau_{zx} \\ \tau_{xy} \end{bmatrix}$$
Where:
*   $E_x \approx E_y \gg E_z$
*   Tensile yield strength normal to layers: $S_{y, Z} \approx 0.35\text{–}0.60 \cdot S_{y, XY}$ for neat polymers.
*   **The Carbon Fiber Paradox:** In short carbon-fiber filled filaments (PA-CF, PET-CF), fibers align exclusively along the XY extrusion road. Fibers **cannot bridge the Z-axis layer boundary**. Consequently, while XY strength jumps to $> 110\text{ MPa}$, Z-axis strength remains at $25\text{–}35\text{ MPa}$ ($S_{ut, Z} \approx 0.25 \cdot S_{ut, XY}$).

---

## 2. Polymer Reptation Kinetics at the Layer Weld Interface

Interlayer strength is governed by the thermal diffusion of macromolecular chains across the interface of two adjacent deposited beads (de Gennes' Reptation Theory).

```
         Bead n+1 (Hot, freshly deposited)
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( ( )
         ═════ Interfacial Weld Line ═════ ◄── Molecular Entanglement Depth (χ)
         ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) )
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         Bead n (Cooled below Tg / Tm)
```

### 2.1 Degree of Interfacial Healing ($D_h$)
The ratio of weld fracture toughness to virgin bulk polymer toughness:
$$D_h(t) = \frac{K_{Ic, weld}}{K_{Ic, bulk}} = \left( \frac{t_{contact}}{\tau_{reptation}(T)} \right)^{1/4}$$
Where:
*   $\tau_{reptation}(T)$: Polymer chain relaxation time (follows Arrhenius temperature dependence):
    $$\tau(T) = \tau_0 \cdot \exp\left( \frac{E_a}{R T} \right)$$
*   **Engineering Takeaways:**
    1.  **Print Hot:** Increasing nozzle temperature by $15^\circ\text{C}$ drops polymer melt viscosity exponentially, accelerating molecular diffusion across the seam.
    2.  **Part Cooling Fan Management:** Aggressive auxiliary cooling fans freeze the bead surface below $T_g$ in milliseconds, halting chain diffusion and crippling Z-strength. Turn fans OFF or set to minimum ($\le 20\text{–}30\%$) for functional mechanical parts.
    3.  **Heated Chamber:** A heated chamber ($50\text{–}70^\circ\text{C}$) keeps the substrate layer warm, dramatically extending the thermal diffusion window.

---

## 3. Extruded Bead Geometry & The Flattening Ratio

The cross-section of an FDM road is approximated as a flat rectangle with semicircular ends (stadium shape).

```
                            Extrusion Road Cross-Section
                            
                              ◄──────── Width (w) ────────►
                              ┌───────────────────────────┐  ───
                            ( │     Bond Contact (wb)     │ ) ▲
                             (│                           │)  │ Layer Height (h)
                            ( │                           │ ) ▼
                              └───────────────────────────┘  ───
```

### 3.1 Geometric Equations
*   **Cross-Sectional Area ($A$):**
    $$A = (w - h) \cdot h + \pi \left(\frac{h}{2}\right)^2 = w \cdot h - h^2 \left(1 - \frac{\pi}{4}\right)$$
*   **Interlayer Contact Bond Width ($w_b$):**
    $$w_b = w - h \left(1 - \frac{\pi}{4}\right) \approx w - 0.2146 \cdot h$$
*   **Optimal Layer Height to Nozzle Ratio:**
    $$\frac{h}{d_{nozzle}} \approx 0.40\text{–}0.50$$
    *   *Example:* For a standard $0.4\text{ mm}$ nozzle, optimal layer height is **$0.16\text{–}0.20\text{ mm}$** with an extrusion width of **$0.45\text{–}0.50\text{ mm}$**.
    *   *Violation:* If $h / d > 0.75$ (e.g. $0.35\text{ mm}$ on a $0.4\text{ mm}$ nozzle), the nozzle flat cannot exert downward ironing pressure; beads deposit as loose circular cylinders with tiny contact lines, causing instantaneous layer delamination under load.

---

## 4. Wall Perimeters vs. Infill Density: Structural Optimization

A ubiquitous failure in 3D printing is increasing infill percentage to make a part "stronger". In solid mechanics, beam bending stress is:
$$\sigma = \frac{M \cdot y}{I}$$
The outermost fibers carry $90\%$ of the bending load.

```
       Bending Stress Distribution Across a 3D Printed Beam
       
           Maximum Tension (+) ◄─── Outer Perimeters Carry Primary Load
           ═══════════════════
           ░░░░░░░░░░░░░░░░░░░
           ─── Neutral Axis ── ◄── Infill in Center Carries Zero Bending Stress
           ░░░░░░░░░░░░░░░░░░░
           ═══════════════════
           Maximum Compression (-)
```

### 4.1 Quantitative Efficiency Comparison

| Configuration | Material Used | Print Time | Flexural Rigidity | Failure Load (Bending) |
| :--- | :---: | :---: | :---: | :---: |
| **2 Walls + 20% Infill** | $100\text{ g}$ (baseline) | $2.0\text{ hrs}$ | $1.0\times$ | $150\text{ N}$ |
| **2 Walls + 80% Infill** | $210\text{ g}$ ($+110\%$) | $4.2\text{ hrs}$ ($+110\%$) | $1.3\times$ | $210\text{ N}$ |
| **6 Walls + 25% Infill** | **$135\text{ g}$ ($+35\%$)** | **$2.4\text{ hrs}$ ($+20\%$)** | **$3.8\times$** | **$540\text{ N}$** |

*Rule of Thumb for Mechanical Parts:* **Walls provide strength; infill merely supports top layers.** Always specify **4 to 6 perimeter loops** ($1.8\text{–}2.5\text{ mm}$ solid shell) and **5 top/bottom solid layers** before increasing infill above $25\%$.

---

## 5. Infill Topologies & Mechanical Behavior

```
     Gyroid (Isotropic TPMS)            Cubic (High Multi-Axis)           Grid (Anisotropic)
        ╭─╮   ╭─╮                        ┌───┬───┐                         ┌───┬───┐
       (   ) (   )                       │ \ │ / │                         │   │   │
        ╰─╯   ╰─╯                        ├───┼───┤                         ├───┼───┤
    Uniform shear in all axes           Tension/Compression               Weak shear along 45°
```

### 5.1 Pattern Evaluation
1.  **Gyroid (Triply Periodic Minimal Surface - TPMS):**
    *   *Mechanics:* Uniform, isotropic shear and compression resistance in X, Y, and Z.
    *   *Advantage:* Continuous sinusoidal path; nozzle never crosses previously printed extrusion lines (zero nozzle collisions/thumping); internal channels are fully open (ideal for liquid drainage or polyurethane foam back-filling).
2.  **Cubic / 3D Honeycomb:**
    *   Creates closed 3D polyhedral cells; high specific stiffness under multi-axis impact.
3.  **Rectilinear / Grid:**
    *   Fastest printing; highly anisotropic (strong along $0^\circ/90^\circ$, weak along $45^\circ$). Crossings knock the nozzle at high speeds. Avoid for structural components.

---

## 6. References & Standards

1.  **de Gennes, P. G. (1971).** *Reptation of a Polymer Chain in the Presence of Fixed Obstacles.* The Journal of Chemical Physics, 55(2), 572–579. [DOI: 10.1063/1.1675789] (Foundational physics of inter-filament weld strength and thermal chain diffusion).
2.  **Wool, R. P., & O'Connor, K. M. (1981).** *A Theory of Crack Healing in Polymers.* Journal of Applied Physics, 52(10), 5953–5963. [DOI: 10.1063/1.328526] (Isothermal autohesion kinetics governing layer-to-layer weld interfaces).
3.  **Bellini, A., & Güçeri, S. (2003).** *Mechanical Characterization of Parts Fabricated Using Fused Deposition Modeling.* Rapid Prototyping Journal, 9(4), 252–264. [DOI: 10.1108/13552540310489631] (Experimental demonstration of transverse isotropy and meso-void stress concentration factors).
4.  **ASTM D638-14.** *Standard Test Method for Tensile Properties of Plastics.* ASTM International, West Conshohocken, PA. (Standardized dogbone orientation protocols for verifying X/Y vs Z-axis tensile properties).
5.  **ISO 527-2:2012.** *Plastics — Determination of tensile properties — Part 2: Test conditions for moulding and extrusion plastics.* International Organization for Standardization.
6.  **Ahn, S. H., Montero, M., Odell, D., Roundy, S., & Wright, P. K. (2002).** *Anisotropic material properties of fused deposition modeling ABS.* Rapid Prototyping Journal, 8(4), 248–257. [DOI: 10.1108/13552540210441166] (Empirical mapping of raster angle, layer thickness, and air gaps on part strength).


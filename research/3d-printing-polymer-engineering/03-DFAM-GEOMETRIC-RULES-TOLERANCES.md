# Design for Additive Manufacturing (DFAM): Geometry & Tolerancing

**Date:** 2026-09-05  
**Scope:** Geometric design rules for polymers, overhang mechanics ($45^\circ$ rule), bridge spans, hole shrinkage physics, tear-drop horizontal bores, and additive tolerance classes across FDM, SLA, and SLS.

---

## 1. Overhang Mechanics & The $45^\circ$ Self-Supporting Rule

FDM deposits molten thermoplastic beads on top of preceding layers. When a layer extends outward into free air without support, gravity and bead surface tension cause sagging and curling.

```
       Supported Overhang (θ ≤ 45°)               Failed Overhang (θ > 60°)
       
               Layer n+1                                   Layer n+1
            ┌─────────────┐                             ┌─────────────┐
            │   Bead      │                             │   Bead      │
         ┌──┴──────────┐  │                          ┌──┴───────┐     │ Droops
         │   Layer n   │  │                          │ Layer n  │     ▼ into air
         └─────────────┘  ▼                          └──────────┘
```

### 1.1 The Bead Overhang Criterion
Let $w$ be bead width, $h$ be layer height, and $\theta$ be the angle of the wall measured from the vertical build axis:
*   **Maximum Overhang Offset per Layer ($\Delta x$):**
    $$\Delta x = h \cdot \tan(\theta)$$
*   **Critical Support Ratio:** To prevent the molten bead from rolling off the edge, at least **$50\%$ of the bead width ($w/2$)** must rest solidly on the layer below:
    $$\Delta x \le \frac{w}{2} \implies h \cdot \tan(\theta) \le \frac{w}{2} \implies \tan(\theta_{max}) \approx \frac{w}{2h}$$
    *Example:* With $w = 0.45\text{ mm}$ and $h = 0.20\text{ mm}$:
    $$\tan(\theta_{max}) = \frac{0.45}{2 \times 0.20} = 1.125 \implies \theta_{max} \approx \mathbf{48.4^\circ}$$

### 1.2 The Chamfer vs. Fillet Rule for Bottom Edges
A classic failure mode is applying a traditional CAD round fillet to the bottom edge of a part resting on the build plate:

```
        Round Fillet at Bed (FAILS)                 45° Chamfer at Bed (SUCCEEDS)
        
             ┌────────────┐                              ┌────────────┐
             │            │                              │            │
             │     Fillet │                              │    Chamfer │
             │    (R)     │                              │    (45°)   │
             │        ╭───┘                              │        /───┘
        ─────┴───────(────┴─────                    ─────┴───────/────┴─────
            90° Overhang at Start                     Constant 45° Self-Supporting
            Severe Droop & Spaghetti                  Flawless Clean Print
```

*   *The Fillet Trap:* A circular fillet begins tangent to the print bed at **$90^\circ$ overhang**. The first $3\text{–}5$ layers are extruded in mid-air, resulting in drooping, rough, stepped edges.
*   *Design Rule:* **Replace all bottom horizontal edge fillets with $45^\circ$ chamfers.**

---

## 2. Horizontal Hole Shrinkage Physics & Compensation

Every mechanical engineer discovers that a $\varnothing 5.0\text{ mm}$ hole modeled in CAD prints at $\varnothing 4.6\text{–}4.7\text{ mm}$ on an FDM 3D printer. This shrinkage is caused by three compounding physical phenomena:

```
                  Causes of Internal Hole Shrinkage
                  
          1. Polygonization Error          2. Molten Bead Inward Tension
               . - - ' ' - - .                          ╭───────────╮
            . '    Chord      ' .                      /   ◄──┬──►   \
           /     Sagitta h       \                    │   Tensile     │
          │     ┌─────────┐       │                   │   Bead Hoop   │
           \    │         │      /                     \  Stress     /
            ' . └─────────┘   . '                       ╰───────────╯
                ' - - . . - - '                    Molten loop pulls inward
```

1.  **Polygonization (Chordal Error):** Slicers discretize circles into $N$ linear G1 chords. The straight chords slice inside the true circular diameter by the sagitta $h = r(1 - \cos(\pi/N))$.
2.  **Viscoelastic Hoop Tension:** When the nozzle traces a circular toolpath, it stretches the molten polymer thread around an arc. Surface tension and thermal contraction pull the molten bead radially inward toward the hole center before it freezes.
3.  **Thermal Contraction:** Bulk volumetric cooling shrinkage pulls material inward.

### 2.1 Diameter Compensation Table (Vertical Holes)

| Nominal Hole Size | CAD Modeled Diameter (Drill Clearance) | CAD Modeled Diameter (Tight Locating) |
| :---: | :---: | :---: |
| **M2 ($\varnothing 2.0$)** | **$\varnothing 2.5\text{ mm}$** ($+0.50\text{ mm}$) | **$\varnothing 2.3\text{ mm}$** ($+0.30\text{ mm}$) |
| **M3 ($\varnothing 3.0$)** | **$\varnothing 3.6\text{ mm}$** ($+0.60\text{ mm}$) | **$\varnothing 3.3\text{ mm}$** ($+0.30\text{ mm}$) |
| **M4 ($\varnothing 4.0$)** | **$\varnothing 4.7\text{ mm}$** ($+0.70\text{ mm}$) | **$\varnothing 4.4\text{ mm}$** ($+0.40\text{ mm}$) |
| **M5 ($\varnothing 5.0$)** | **$\varnothing 5.8\text{ mm}$** ($+0.80\text{ mm}$) | **$\varnothing 5.4\text{ mm}$** ($+0.40\text{ mm}$) |
| **M6 ($\varnothing 6.0$)** | **$\varnothing 6.9\text{ mm}$** ($+0.90\text{ mm}$) | **$\varnothing 6.5\text{ mm}$** ($+0.50\text{ mm}$) |

---

## 3. Horizontal Bores: The Tear-Drop & Diamond Rule

When a cylindrical bore is oriented horizontally (parallel to the print bed), the top $10\text{–}20\%$ of the circular arch exceeds $60^\circ\text{–}90^\circ$ overhang. Molten plastic droops down from the crown, turning circular holes into rough ellipses.

```
       Standard Horizontal Hole (DROOPS)            Tear-Drop Geometry (CLEAN)
       
                 ┌───┬───┐                                   /\  45° Peak
                /  Droop  \                                 /  \ (Self-supporting)
               │     ▼     │                               /    \
               │           │                              │      │
                \         /                                \    /
                 └───┴───┘                                  └──┘
```

*   **The Tear-Drop Geometry:** Replace the top semicircle with a **$45^\circ$ pointed triangular gable roof**.
*   **The Diamond Hole:** For smaller pin holes ($\le \varnothing 10\text{ mm}$), rotate a square cutout by $45^\circ$ to form a diamond. All four walls print at an optimal $45^\circ$ self-supporting angle with zero sag and zero support material required.

---

## 4. Bridging Limits & Parameter Control

A **bridge** is an unsupported horizontal extrusion spanning between two solid pillars.
*   **Maximum Reliable Span:**
    *   Standard PLA / PETG: $15\text{–}25\text{ mm}$
    *   ABS / ASA / PC: $10\text{–}15\text{ mm}$ (hotter chamber reduces sag control)
    *   Flexible TPU: $\le 5\text{ mm}$ (cannot bridge reliably due to low modulus)
*   **Bridging Slicing Rules:**
    *   Print bridges at $100\%$ fan speed to freeze the filament string instantaneously.
    *   Set bridge flow ratio to $0.85\text{–}0.90$ (slight underextrusion creates axial tension that pulls the bridge straight).

---

## 5. Additive Process Tolerance Matrix

| Dimension / Feature | FDM Desktop (0.4mm nozzle) | Industrial FDM (Fortus) | SLA Resin (Formlabs) | SLS (Nylon PA12) |
| :--- | :---: | :---: | :---: | :---: |
| **XY Positional Tolerance** | $\pm 0.20\text{ mm}$ | $\pm 0.10\text{ mm}$ | $\pm 0.05\text{ mm}$ | $\pm 0.15\text{ mm}$ |
| **Z-Height Tolerance** | $\pm 0.10\text{ mm}$ | $\pm 0.05\text{ mm}$ | $\pm 0.03\text{ mm}$ | $\pm 0.10\text{ mm}$ |
| **Moving Clearance Gap** | $0.40\text{–}0.50\text{ mm}$ | $0.30\text{–}0.35\text{ mm}$ | $0.15\text{–}0.20\text{ mm}$ | $0.25\text{–}0.30\text{ mm}$ |
| **Press-Fit Clearance** | $0.10\text{–}0.15\text{ mm}$ | $0.05\text{–}0.08\text{ mm}$ | $0.02\text{–}0.05\text{ mm}$ | $0.08\text{–}0.12\text{ mm}$ |
| **Minimum Wall Thickness** | $1.2\text{ mm}$ (3 perimeters) | $1.0\text{ mm}$ | $0.6\text{ mm}$ | $0.8\text{ mm}$ |
| **Minimum Pin Diameter** | $2.0\text{ mm}$ | $1.5\text{ mm}$ | $0.5\text{ mm}$ | $1.0\text{ mm}$ |

---

## 6. References & Standards

1.  **ISO/ASTM 52910:2018.** *Additive manufacturing — Design — Requirements, guidelines and recommendations.* International Organization for Standardization / ASTM International. (Authoritative standard defining geometric overhang limits, self-supporting thresholds, and feature constraints).
2.  **ISO/ASTM 52900:2021.** *Additive manufacturing — General principles — Fundamentals and vocabulary.* ISO/ASTM International.
3.  **Diegel, O., Nordin, A., & Motte, D. (2019).** *A Practical Guide to Design for Additive Manufacturing.* Springer Nature Singapore. [DOI: 10.1007/978-981-13-8281-9] (Systematic design rules for polymer FDM/SLS feature sizing and print-in-place clearances).
4.  **Gibson, I., Rosen, D., Stucker, B., & Khorasani, M. (2021).** *Additive Manufacturing Technologies* (3rd ed.). Springer Cham. [DOI: 10.1007/978-3-030-56127-7] (Extrusion dynamics, stair-stepping formulas, and chordal hole error analyses).
5.  **Wohlers, T., Campbell, I., Diegel, O., Kowen, J., & Caffrey, T. (2023).** *Wohlers Report 2023: 3D Printing and Additive Manufacturing State of the Industry.* Wohlers Associates. (Industrial benchmark datasets on commercial manufacturing tolerances across AM platforms).


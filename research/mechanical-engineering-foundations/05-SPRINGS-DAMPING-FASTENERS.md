# Springs, Dampers & Bolted Joint Mechanics

**Date:** 2026-09-05  
**Scope:** Helical compression springs (Wahl factor, spring rate, solid height), Belleville disc spring stacks, bolted joint diagrams, preload torque ($T = K \cdot F \cdot d$), and fatigue protection via clamping stiffness.

---

## 1. Helical Compression & Extension Spring Mechanics

Helical springs store mechanical energy through the elastic **torsion** of a coiled wire.

```
                  Helical Spring Dimensional Architecture
                  
                          ◄────── Mean Diameter D ──────►
                          ┌─┐                         ┌─┐
                          │ │◄── Wire Diam d          │ │
                          └─┘                         └─┘
                          │◄──────── Free Length L0 ────►│
```

### 1.1 Spring Rate (Stiffness $k$) Formula
For a spring with wire diameter $d$, mean coil diameter $D$, and active coil count $n_a$:
$$k = \frac{F}{\Delta L} = \frac{G \cdot d^4}{8 \cdot D^3 \cdot n_a} \quad (\text{N/mm or N/m})$$
Where $G$ is the shear modulus of elasticity ($G \approx 79.3\text{ GPa}$ for ASTM A228 Music Wire; $G \approx 70.3\text{ GPa}$ for 302 Stainless Steel).

### 1.2 Spring Index ($C$) & The Wahl Stress Factor ($K_w$)
The **Spring Index** is the ratio of mean coil diameter to wire diameter:
$$C = \frac{D}{d}$$
*   **Recommended Engineering Range:** **$4 \le C \le 12$** ($C \approx 6\text{–}9$ optimal).
    *   $C < 4$: High internal stress concentration during coiling; wire cracking.
    *   $C > 12$: Floppy spring, prone to tangling and buckling.

Because the wire is curved, inner fibers experience both direct transverse shear and curvature stress concentration. A.M. Wahl derived the **Wahl Curvature Correction Factor ($K_w$)**:
$$K_w = \frac{4C - 1}{4C - 4} + \frac{0.615}{C}$$
**Maximum Torsional Shear Stress ($\tau_{max}$):**
$$\tau_{max} = K_w \cdot \frac{8 F D}{\pi d^3} \le \tau_{allow} \approx 0.45\text{–}0.50 \cdot S_{ut}$$

### 1.3 End Types & Solid Height ($H_s$)
For **Squared & Ground Ends** (standard industrial compression spring):
*   Total coils: $n_t = n_a + 2$
*   **Solid Height ($H_s$):** The length when all coils touch solidly:
    $$H_s = d \cdot n_t = d \cdot (n_a + 2)$$
*   *Safety Clearance:* Maximum working stroke must leave at least $10\text{–}15\%$ clash allowance before hitting solid height.

---

## 2. Belleville Disc Springs (Conical Washers - DIN 2093)

Belleville springs deliver astronomical spring rates ($> 10\text{ kN/mm}$) in ultra-compact axial spaces.

```
       Series Stacking (Opposing)                 Parallel Stacking (Nested)
           High Deflection                           High Load Capacity
               ╭─────╮                                   ╭─────╮
               │     │                                   │     │
               ╰─────╯                                   ╭─────╮
               ╭─────╮                                   │     │
               │     │                                   ╰─────╯
               ╰─────╯
```

### 2.1 Stacking Rules
*   **Series Stacking ($n$ opposing washers):**
    *   Total Deflection: $\Delta h_{total} = n \cdot \Delta h$
    *   Total Force: $F_{total} = F$
    *   Equivalent Stiffness: $k_{total} = \frac{k}{n}$
*   **Parallel Stacking ($m$ nested washers):**
    *   Total Deflection: $\Delta h_{total} = \Delta h$
    *   Total Force: $F_{total} = m \cdot F$
    *   Equivalent Stiffness: $k_{total} = m \cdot k$

---

## 3. Bolted Joint Mechanics & The Joint Diagram

Bolts are not rigid pins—they are **pre-tensioned elastic springs** holding clamped structural members in permanent compression.

```
               The Classic Bolted Joint Diagram
       Load (F)
          ▲
          │    Bolt Tension Curve (Slope kb)
       Fi ┼────────────╮
          │           / \
          │          /   \
          │         /     \  Clamped Member Decompression (Slope km)
          │        /       \
          └───────┴─────────┴──────────► Deflection (δ)
                  ▲
               Preload Fi
```

### 3.1 Clamping Preload ($F_i$) & Tightening Torque ($T$)
To prevent joint separation and bolt fatigue, pre-tension bolts to $75\text{–}90\%$ of proof strength:
$$F_i = 0.75 \cdot A_t \cdot S_p$$
Where $A_t$ is the bolt tensile stress area (e.g., $A_t = 5.03\text{ mm}^2$ for M3; $A_t = 20.1\text{ mm}^2$ for M6).

**Tightening Torque Formula:**
$$T = K \cdot F_i \cdot d$$
Where:
*   $T$: Tightening torque ($\text{N}\cdot\text{m}$).
*   $d$: Nominal bolt diameter (meters).
*   $K$: Torque nut factor:
    *   $K \approx 0.20$ for clean, dry, as-received steel fasteners.
    *   $K \approx 0.15$ for machine oil lubricated threads.
    *   $K \approx 0.12$ with molybdenum disulfide ($\text{MoS}_2$) or anti-seize paste.

### 3.2 Joint Stiffness Ratio ($C_j$) & Fatigue Immunity
The bolt has stiffness $k_b$; the clamped metal plates have stiffness $k_m$.
**Joint Stiffness Ratio ($C_j$):**
$$C_j = \frac{k_b}{k_b + k_m}$$
Because clamped flanges are thick and wide compared to the slender bolt shank, **$k_m \gg k_b$** (typically $k_m \approx 4\text{–}6 \times k_b$), resulting in:
$$C_j \approx 0.15\text{–}0.25$$

### 3.3 Why Properly Preloaded Bolts Never Fail from Fatigue
When an external cyclic service load $P_{ext}$ is applied to pull the joint apart:
*   The tension increase felt by the bolt is only:
    $$\Delta F_{bolt} = C_j \cdot P_{ext} \approx \mathbf{0.20 \cdot P_{ext}}$$
*   The remaining **$80\%$** of the load is absorbed by the elastic decompression of the clamped plates!
*   *Conclusion:* The cyclic alternating stress range on the bolt ($\Delta \sigma = \Delta F_b / A_t$) is kept minimal, isolating the bolt from fatigue failure as long as the joint does not separate ($P_{ext} < \frac{F_i}{1 - C_j}$).

---

## 4. References & Standards

1.  **Bickford, J. H. (2007).** *An Introduction to the Design and Behavior of Bolted Joints* (4th ed.). CRC Press. (Definitive treatise on bolt preloading, joint stiffness diagrams, torque-tension scattering, and fatigue isolation).
2.  **VDI 2230 Blatt 1:2015-11.** *Systematic calculation of high duty bolted joints — Joints with one cylindrical bolt.* Verein Deutscher Ingenieure. (The globally accepted engineering guideline for bolted joint elastic compliance and clamp load margins).
3.  **Wahl, A. M. (1963).** *Mechanical Springs* (2nd ed.). McGraw-Hill, New York. (Original derivation of the Wahl curvature shear stress correction factor $K_w$ for helical compression springs).
4.  **DIN EN 13906-1:2013.** *Cylindrical helical springs made from round wire and bar — Calculation and design — Part 1: Compression springs.* Deutsches Institut für Normung.
5.  **DIN 2093:2013-12.** *Disc springs (Belleville springs) — Quality specifications — Dimensions.* Deutsches Institut für Normung. (Standard nested and inverted Belleville pack formulas).
6.  **ISO 898-1:2013.** *Mechanical properties of fasteners made of carbon steel and alloy steel — Part 1: Bolts, screws and studs with specified property classes.* International Organization for Standardization.

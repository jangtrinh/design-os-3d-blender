# Fluid Power Systems, Pneumatics, Hydraulics & O-Ring Sealing

**Date:** 2026-09-05  
**Scope:** Fluid power physics (Pascal, Continuity, Darcy-Weisbach), pneumatic & hydraulic actuator sizing, AS568 / ISO 3601 O-ring gland geometry (squeeze, gland fill, stretch), extrusion gaps, and rotary shaft lip seals.

---

## 1. Fluid Power Fundamentals

Fluid power systems transmit immense forces and mechanical work via pressurized liquids (hydraulics) or compressed gases (pneumatics).

```
          Pascal's Hydrostatic Multiplication
          
          Force F1                            Force F2 = F1 * (A2 / A1)
             ▼                                           ▲
          ┌─────┐                                     ┌─────────────┐
          │ A1  │                                     │     A2      │
          └──┬──┘                                     └───┬─────────┘
             │                                            │
             └────────────────── Fluid ───────────────────┘
                               Pressure P
```

### 1.1 Core Hydrostatic & Hydrodynamic Formulas
1.  **Pascal's Principle:** Pressure applied to an enclosed, static fluid is transmitted equally in all directions:
    $$P = \frac{F_1}{A_1} = \frac{F_2}{A_2} \implies F_2 = F_1 \cdot \frac{A_2}{A_1}$$
2.  **Volumetric Continuity:** For incompressible fluids:
    $$Q = A_1 \cdot v_1 = A_2 \cdot v_2 \quad (\text{m}^3/\text{s})$$
3.  **Hydraulic Fluid Power:**
    $$\text{Power (Watts)} = P \cdot Q = \Delta P (\text{Pa}) \times Q (\text{m}^3/\text{s})$$
    $$\text{Power (kW)} = \frac{P (\text{bar}) \times Q (\text{L/min})}{600}$$

---

## 2. Pneumatic Actuation & Valve Sizing

Pneumatics is preferred for high-speed, lightweight, non-contaminating industrial automation (typically operating at $P = 6.0\text{ bar} = 0.6\text{ MPa} \approx 87\text{ psi}$).

### 2.1 Cylinder Force Equations
For a pneumatic cylinder with bore diameter $D$ and piston rod diameter $d$:
*   **Theoretical Extension Thrust ($F_{ext}$):**
    $$F_{ext} = P \cdot A_{bore} = P \cdot \frac{\pi D^2}{4}$$
*   **Theoretical Retraction Pull ($F_{ret}$):**
    $$F_{ret} = P \cdot (A_{bore} - A_{rod}) = P \cdot \frac{\pi (D^2 - d^2)}{4}$$
*   **The Dynamic Load Sizing Factor ($\eta_{load}$):**
    Never size a cylinder at $100\%$ theoretical force. Internal seal friction and dynamic line pressure drops demand an operating factor:
    $$F_{actual} = \eta_{load} \cdot F_{theoretical}$$
    *   Slow, smooth clamping: $\eta_{load} \approx 0.70$
    *   Fast dynamic stroke: $\eta_{load} \approx 0.50$ (cylinder utilizes $50\%$ for payload, $50\%$ for rapid acceleration).

---

## 3. Hydraulic Systems: High-Density Actuation

Hydraulics operates at ultra-high pressures ($140\text{–}350\text{ bar} = 14\text{–}35\text{ MPa}$), delivering power densities unmatched by electric motors.

| Pump Type | Max Continuous Pressure | Mechanical Efficiency | Acoustic Noise | Primary Duty |
| :--- | :---: | :---: | :---: | :--- |
| **External Gear** | $210\text{ bar}$ | $85\text{–}90\%$ | High | Low-cost mobile equipment, lubrication |
| **Vane Pump** | $175\text{–}250\text{ bar}$ | $88\text{–}92\%$ | Very Low | Quiet industrial factory machinery |
| **Axial Piston (Swashplate)** | **$350\text{–}420\text{ bar}$** | **$93\text{–}96\%$** | Medium | Heavy earthmoving, aerospace, high-force presses |

---

## 4. O-Ring Gland Design: AS568 & ISO 3601 Standards

An O-ring seal works through initial mechanical compression (squeeze) combined with system fluid pressure activation.

```
       Initial Mechanical Squeeze (Static)             System Pressure Activation
       
             Gland Width (W)
          ┌───────────────────┐                     ┌───────────────────┐
          │      ╭─────╮      │                     │        ╭───╮      │
          │     (   O   )     │ Squeeze             │ ────► (  O  )     │◄── High Pressure
          │      ╰─────╯      │   (h < CS)          │  P     ╰───╯      │    Pushes Ring
          └───────┬───┬───────┘                     └─────────┬─┬───────┘
                  │   │                                       │ │
                  ◄ h ►                                       ▲ Extrusion Gap (g)
```

### 4.1 The Three Classical Gland Configurations
1.  **Static Axial / Face Seal:** Clamped between two flat bolting flanges. Zero sliding friction; largest squeeze tolerance allowed.
2.  **Static Radial Seal:** Plug seated inside an internal cylindrical bore.
3.  **Dynamic Reciprocating / Rotary Radial Seal:** Piston or rod sliding axially inside a cylinder bore.

### 4.2 Critical Design Parameters

1.  **Squeeze ($S$):** Percentage compression of O-ring cross-section ($CS$):
    $$S = \frac{CS - h}{CS} \times 100\%$$
    *   **Static Seals:** **$15\%\text{–}30\%$** ($20\%\text{–}25\%$ nominal target).
    *   **Dynamic Seals:** **$10\%\text{–}20\%$** ($12\%\text{–}15\%$ nominal target). Lower squeeze minimizes friction, heat generation, and stick-slip chatter.

2.  **Gland Fill ($GF$):** The ratio of the O-ring volume to the void space inside the rectangular groove:
    $$GF = \frac{V_{O-ring}}{V_{groove}} = \frac{\frac{\pi^2}{4} d_{mean} \cdot CS^2}{\pi D_{groove} \cdot W \cdot h} \approx \frac{\frac{\pi}{4} CS^2}{W \cdot h} \times 100\%$$
    *   **Mandatory Rule:** **Maximum Gland Fill $\le 80\%\text{–}85\%$**.
    *   *Why:* Elastomers are nearly incompressible (Poisson's ratio $\nu \approx 0.499$). If temperature rises or hydraulic fluid swells the polymer, a gland fill of $100\%$ causes hydraulic lock, splits the metal housing, or shears the ring.

3.  **Stretch ($E_s$):** Circumferential stretch of the inside diameter ($ID$):
    $$E_s = \frac{d_{groove\_bottom} - ID_{ring}}{ID_{ring}} \times 100\%$$
    *   **Permissible Range:** **$1\%\text{–}5\%$** ($2\%\text{–}3\%$ recommended). Stretch $> 5\%$ causes the cross-section to neck down, reducing squeeze.

4.  **Groove Width ($W$):**
    $$W \approx 1.25\text{–}1.50 \times CS$$
    Provides void space for the squished elastomer to expand laterally.

### 4.3 Standard AS568 Cross-Section Classes

| AS568 Dash Range | Nominal Cross-Section ($CS$, inch) | Metric Equiv ($CS$, mm) | Recommended Static Depth ($h$, mm) | Recommended Groove Width ($W$, mm) |
| :---: | :---: | :---: | :---: | :---: |
| **001 – 050** | $0.070"$ | $1.78\text{ mm}$ | $1.30\text{–}1.37\text{ mm}$ | $2.3\text{–}2.5\text{ mm}$ |
| **102 – 178** | $0.103"$ | $2.62\text{ mm}$ | $2.00\text{–}2.10\text{ mm}$ | $3.5\text{–}3.8\text{ mm}$ |
| **201 – 284** | $0.139"$ | $3.53\text{ mm}$ | $2.75\text{–}2.90\text{ mm}$ | $4.7\text{–}5.0\text{ mm}$ |
| **309 – 395** | $0.210"$ | $5.33\text{ mm}$ | $4.25\text{–}4.45\text{ mm}$ | $7.1\text{–}7.5\text{ mm}$ |
| **401 – 475** | $0.275"$ | $6.99\text{ mm}$ | $5.65\text{–}5.90\text{ mm}$ | $9.5\text{–}10.0\text{ mm}$ |

### 4.4 Extrusion Gap & Backup Rings
Under high pressure ($> 70\text{–}100\text{ bar}$), the elastomer flows plastically into the diametral clearance gap between the mating metal parts, leading to seal "nibbling" and extrusion tearing.
*   *Solution:* Use **PTFE or hard polyurethane Backup Rings** on the low-pressure side of the O-ring for pressures exceeding $100\text{ bar}$.

---

## 5. References & Standards

1.  **Parker Hannifin Corporation. (2018).** *Parker O-Ring Handbook (ORD 5700).* Cleveland, OH. (The primary engineering reference for gland dimensions, squeeze ratios, void volumes, and fluid compatibility).
2.  **SAE AS568D:2020-04.** *Aerospace Size Standard for O-Rings.* SAE International. (Standard dash numbering, inner diameters, and cross-section tolerances).
3.  **ISO 3601-1:2012.** *Fluid power systems — O-rings — Part 1: Inside diameters, cross-sections, tolerances and designation codes.* International Organization for Standardization.
4.  **ISO 3601-2:2016.** *Fluid power systems — O-rings — Part 2: Housing dimensions for general applications.* International Organization for Standardization.
5.  **Merritt, H. E. (1967).** *Hydraulic Control Systems.* John Wiley & Sons, New York. (Electrohydraulic servo systems, compressibility bulk modulus, and flow orifices).
6.  **ISO 4413:2010.** *Hydraulic fluid power — General rules and safety requirements for systems and their components.* International Organization for Standardization.


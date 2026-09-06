# Polymer Melt Rheology, Nozzle Flow Dynamics & Pressure Advance

High-speed FDM/FFF printing ($> 300\text{ mm/s}$, flow rates $> 30\text{ mm}^3\text{/s}$) pushes thermoplastic polymers far beyond steady-state laminar Newtonian flow into complex non-Newtonian viscoelastic behavior.

---

## 1. Viscoelastic Polymer Melt Rheology

Molten thermoplastics (PLA, PETG, ABS, PC, PEEK) are **pseudoplastic (shear-thinning) non-Newtonian fluids**. Their dynamic viscosity $\eta$ drops by orders of magnitude as shear rate $\dot{\gamma}$ increases.

```
          Log Viscosity (η) [Pa·s]
                   ▲
             η₀ ───┼────────╮  Newtonian Plateau (Low Shear / Reservoir)
                   │         \
                   │          \  Power-Law Shear Thinning Region (Nozzle Orifice)
                   │           \   Slope = (n - 1)
                   │            \
                   └─────────────┴──────────► Log Shear Rate (γ̇) [s⁻¹]
```

### 1.1 The Cross-WLF Viscosity Model
The viscosity $\eta(T, \dot{\gamma})$ is governed across temperature and shear rate by the Cross-WLF equation:
$$\eta(T, \dot{\gamma}) = \frac{\eta_0(T)}{1 + \left( \frac{\eta_0 \dot{\gamma}}{\tau^*} \right)^{1 - n}}$$
Where:
*   $\eta_0(T)$: Zero-shear viscosity at temperature $T$, defined by the Williams-Landel-Ferry (WLF) equation:
    $$\eta_0(T) = D_1 \exp\left( \frac{-A_1 (T - T^*)}{A_2 + (T - T^*)} \right)$$
*   $\tau^*$: Characteristic shear stress at the onset of shear-thinning ($\sim 20\text{–}60\text{ kPa}$).
*   $n$: Power-law shear-thinning index ($0 < n < 1$). For standard polymers:
    *   **PLA:** $n \approx 0.35\text{–}0.45$
    *   **PETG:** $n \approx 0.40\text{–}0.50$
    *   **ABS:** $n \approx 0.25\text{–}0.35$ (strongly shear-thinning)
    *   **PC:** $n \approx 0.50\text{–}0.65$ (retains high viscosity even under shear)

### 1.2 Shear Rate Inside the Nozzle Orifice
For a circular capillary nozzle of radius $R = D_{nozzle} / 2$ and volumetric flow rate $Q$:
*   **Apparent Wall Shear Rate ($\dot{\gamma}_{app}$):**
    $$\dot{\gamma}_{app} = \frac{4 Q}{\pi R^3} = \frac{32 Q}{\pi D^3}$$
*   **Weissenberg-Rabinowitsch Correction (True Wall Shear Rate $\dot{\gamma}_w$):**
    $$\dot{\gamma}_w = \dot{\gamma}_{app} \cdot \left( \frac{3n + 1}{4n} \right)$$
    *Example:* At $Q = 30\text{ mm}^3\text{/s}$ through a $D = 0.4\text{ mm}$ ($R = 0.2\text{ mm}$) nozzle with $n = 0.35$:
    $$\dot{\gamma}_{app} = \frac{4 \times 30}{\pi (0.2)^3} \approx 4775\text{ s}^{-1}, \quad \dot{\gamma}_w = 4775 \times \left(\frac{3(0.35)+1}{4(0.35)}\right) \approx 6991\text{ s}^{-1}$$
    At shear rates approaching $10^4\text{ s}^{-1}$, the apparent viscosity of PLA drops from $\eta_0 \approx 2000\text{ Pa}\cdot\text{s}$ to $< 40\text{ Pa}\cdot\text{s}$.

---

## 2. Nozzle Pressure Drop & Hagen-Poiseuille Limitations

The extruder motor must generate sufficient axial drive force $F_{drive}$ on the solid filament rod ($D_{fil} = 1.75\text{ mm}$) to overcome the pressure drop $\Delta P_{total}$ across the hotend:
$$F_{drive} = \Delta P_{total} \cdot A_{fil} = \Delta P_{total} \cdot \frac{\pi D_{fil}^2}{4}$$

```
   Filament (1.75mm) ──► ║ Melt Chamber ║ ──► \ Converging Nozzle Cone / ──► | Orifice |
                         ▲                ▲                                   ▲
                         │                │                                   │
                      ΔP_barrel        ΔP_entry                            ΔP_orifice
```

### 2.1 Pressure Drop Components
$$\Delta P_{total} = \Delta P_{barrel} + \Delta P_{entry} + \Delta P_{orifice}$$
1.  **Melt Barrel Friction ($\Delta P_{barrel}$):** Laminar flow through the cylindrical melt tube ($D \approx 2.0\text{ mm}$, length $L_b \approx 15\text{–}25\text{ mm}$).
2.  **Cogswell Extensional Entry Pressure Drop ($\Delta P_{entry}$):**
    As molten polymer enters the conical contraction (transition angle $\alpha \approx 60^\circ\text{–}120^\circ$), polymer chains stretch along the flow direction. This extensional flow produces large elastic normal stresses:
    $$\Delta P_{entry} \propto \dot{\epsilon}^{m} \quad (\text{where } \dot{\epsilon} \text{ is extensional strain rate})$$
3.  **Capillary Orifice Drop ($\Delta P_{orifice}$):**
    $$\Delta P_{orifice} = \frac{2 L_{or}}{R} \cdot \tau_w = \frac{2 L_{or}}{R} \cdot K \dot{\gamma}_w^n$$

### 2.2 Extruder Hobbed Gear Tooth Biting Force Limit
Standard dual-drive hardened steel gears (Bondtech BMG style) can apply a maximum axial force $F_{max} \approx 70\text{–}100\text{ N}$ before the gear teeth strip and grind into the $1.75\text{ mm}$ filament:
$$P_{max} = \frac{F_{max}}{\pi (1.75\text{ mm} / 2)^2} = \frac{80\text{ N}}{2.405 \times 10^{-6}\text{ m}^2} \approx 33.2\text{ MPa} \quad (\mathbf{332\text{ bar}})$$
*Consequence:* If volumetric flow demand exceeds the melt rate, hotend backpressure reaches $300\text{ bar}$, causing stepper motor step loss (clicking) or filament grinding.

---

## 3. High-Flow Melt Core Architectures

To increase maximum volumetric speed ($Q_{max}$) without drastically increasing nozzle temperature (which thermally degrades polymers):

```
       Standard Nozzle                   Core-Heating / CHT Geometry
      ┌───────────────┐                       ┌───────┬───────┐
      │               │                       │  (A)  │  (B)  │
      │   Cold Core   │                       │ Melt  │ Melt  │  3 Parallel Melt Channels
      │   Molten Ring │                       │ Split │ Split │  Path Length halved,
      └───────┬───────┘                       └───────┼───────┘  Heat transfer area tripled
              ▼                                       ▼
```

### 3.1 The Radial Thermal Conduction Bottleneck
Plastics are poor thermal conductors ($k \approx 0.15\text{–}0.25\text{ W/m}\cdot\text{K}$). The Fourier thermal penetration time $\tau_{heat}$ across radius $R$ is:
$$\tau_{heat} \approx \frac{R^2}{\alpha_{th}} = \frac{R^2 \cdot \rho \cdot C_p}{k}$$
For $1.75\text{ mm}$ filament ($R = 0.875\text{ mm}$), complete core melting takes $\sim 2.5\text{–}3.5\text{ seconds}$.
*   At $Q = 10\text{ mm}^3\text{/s}$, filament resides in a $20\text{ mm}$ melt zone for $4.8\text{ s}$ $\implies$ **Fully molten**.
*   At $Q = 40\text{ mm}^3\text{/s}$, residence time drops to $1.2\text{ s}$ $\implies$ **Unmolten solid core enters nozzle orifice**, triggering an exponential spike in backpressure.

### 3.2 High-Flow Solutions Comparison
1.  **Bondtech CHT (Coaxial Heat Technology):** Three internal bore splitters divide the single $1.75\text{ mm}$ input into three smaller strands of effective radius $r_{eff} \approx 0.4\text{ mm}$. Reduces thermal diffusion time by $(0.4 / 0.875)^2 \approx 4.8\times$. Boosts $Q_{max}$ by $+70\text{–}100\%$.
2.  **Extended Melt Zone (Volcano / SuperVolcano / Bambu HF):** Increases melt length $L_b$ from $12\text{ mm}$ to $20\text{–}50\text{ mm}$. Increases residence time proportionally, but increases required retraction distance due to larger molten volume.

---

## 4. Die Swell (Barus Effect) & Nozzle Geometry

When an elastic polymer melt exits the restrictive nozzle capillary into ambient air, it expands radially. This is **Die Swell (The Barus Effect)**:

$$B = \frac{D_{extrudate}}{D_{nozzle}} > 1.0$$

```
   Nozzle Capillary (D_nozzle)              Free Air Extrudate (D_extrudate)
      │               │                                   │
      │ ═════════════ │                             ╭─────┴─────╮
      │ Polymer coils │                             │           │
      │ stretched     │     ════════════►           │ Relaxed   │  B = 1.15–1.35
      │ under shear   │                             │ Random    │
      │ ═════════════ │                             │ Coils     │
      │               │                             ╰─────┬─────╯
```

### 4.1 Underlying Elastic Mechanics
1.  Inside the capillary, molecular chains are uncoiled and oriented along the flow direction, storing elastic strain energy (first normal stress difference $N_1 = \sigma_{xx} - \sigma_{yy} > 0$).
2.  Upon exiting the constraint of the rigid metal nozzle wall, the chains snap back elastically into random thermodynamic coil conformations, expanding the bead diameter ($B \approx 1.10\text{–}1.35$) while contracting longitudinally.
3.  **Capillary Aspect Ratio Effect ($L_{or} / D_{or}$):**
    *   Short land ($L/D < 1$): Maximum die swell ($B \approx 1.35$).
    *   Long land ($L/D \ge 2.5$): Entropic relaxation occurs inside the nozzle; die swell drops to $B \approx 1.05\text{–}1.10$.
    *   *Slicer compensation:* Slicers assume volumetric conservation ($Q = v \cdot w \cdot h$); excessive die swell produces bulging corners and over-extruded surface ridges unless calibrated.

---

## 5. Dynamic Pressure Advance (Linear Advance) Physics

During high-speed direction changes, toolhead velocity decelerates to corner velocity $v_{corner}$ and accelerates back to $v_{cruise}$.

```
                 Toolhead Acceleration & Pressure Phase Lag
                 
   Velocity (v)  ┌──────────────────┐
                 │                  │
                 ┘                  └──────────  Corner Decel / Accel
                 
   Extrusion     ┌─────────────────▲┐ (Bulging Corner without PA)
   Pressure (P)  │                / │\
                 │  Lag Behind   /  │ \  Extrusion continues after motor stops
                 ┘  Velocity    /   └─ \────────
```

### 5.1 The Hydraulic Compliance Equation
The molten polymer reservoir acts as an elastic spring in series with a viscous damper. The mass of molten polymer stored under compression in the hotend is:
$$M_{melt} = \rho(P) \cdot V_{melt} = \rho_0 (1 + \beta P) \cdot V_{melt}$$
Where $\beta$ is isothermal compressibility ($\beta \approx 10^{-9}\text{ Pa}^{-1}$).
To keep nozzle exit flow $Q_{out}(t)$ strictly proportional to instantaneous toolhead velocity $v(t)$:
$$P(t) = R_{fluid} \cdot Q(t) = R_{fluid} \cdot (w \cdot h \cdot v(t))$$
Differentiating with respect to time shows that extruder displacement $E(t)$ must anticipate pressure changes:
$$E_{corrected}(t) = E_{nominal}(t) + k_{PA} \cdot \frac{dv}{dt}$$
Where $k_{PA}$ is the **Pressure Advance Coefficient** (units: seconds).

### 5.2 Typical $k_{PA}$ Values by Extruder Architecture

| Hotend / Extruder Setup | Bowden Tube Length | Filament Type | Typical $k_{PA}$ Value |
| :--- | :---: | :--- | :---: |
| **Direct Drive (Compact Pancake Stepper)** | $< 30\text{ mm}$ | PLA / PETG | $0.020\text{–}0.035\text{ s}$ |
| **Direct Drive (All-Metal Hotend)** | $< 30\text{ mm}$ | TPU 95A (Flexible) | $0.080\text{–}0.150\text{ s}$ |
| **Direct Drive (High-Flow Volcano)** | $< 30\text{ mm}$ | PLA / ABS | $0.035\text{–}0.055\text{ s}$ |
| **Bowden System (Voron Switchwire style)** | $350\text{ mm}$ | PLA / PETG | $0.150\text{–}0.350\text{ s}$ |
| **Bowden System (Long PTFE tube)** | $600\text{ mm}$ | ABS / PETG | $0.400\text{–}0.750\text{ s}$ |

---

## 6. References & Standards

1.  **Bird, R. B., Armstrong, R. C., & Hassager, O. (1987).** *Dynamics of Polymeric Liquids, Volume 1: Fluid Mechanics* (2nd ed.). John Wiley & Sons, New York. (Definitive treatise on non-Newtonian polymer melt rheology, Cross model, and normal stress differences).
2.  **Cogswell, F. N. (1972).** *Converging flow of polymer melts in extrusion dies.* Journal of Non-Newtonian Fluid Mechanics / Polymer Engineering & Science, 12(1), 64–73. (Mathematical formulation of entry pressure loss and extensional viscosity in converging nozzles).
3.  **Osswald, T. A., & Rudolph, N. (2015).** *Polymer Processing: Modeling and Simulation.* Carl Hanser Verlag, Munich. (Viscoelastic constitutive equations, WLF temperature shifts, and die swell mechanics).
4.  **Tanner, R. I. (1970).** *A Theory of Die-Swell.* Journal of Polymer Science Part A-2: Polymer Physics, 8(12), 2067–2078. [DOI: 10.1002/pol.1970.160081203] (Closed-form elastic recovery equations relating first normal stress difference to swell ratio $B$).
5.  **ISO 1133-1:2022.** *Plastics — Determination of the melt mass-flow rate (MFR) and melt volume-flow rate (MVR) of thermoplastics — Part 1: Standard method.* International Organization for Standardization.
6.  **Klipper Firmware Project. (2024).** *Pressure Advance Kinematics and Extruder Tuning Architecture.* https://www.klipper3d.org/Pressure_Advance.html

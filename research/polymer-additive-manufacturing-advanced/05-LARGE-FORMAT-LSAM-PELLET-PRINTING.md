# Large Scale Additive Manufacturing (LSAM) & Direct Pellet Extrusion (FGF)

When mechanical components exceed $1\text{ meter}$ in build volume (humanoid chassis, aerospace molds, heavy industrial robot bases), filament-based FDM becomes economically and technically infeasible ($> 30\text{ days}$ print times). **Fused Granulate Fabrication (FGF / Direct Pellet Extrusion)** increases deposition rates from $0.1\text{ kg/h}$ to $> 10\text{–}50\text{ kg/h}$ using raw injection-molding thermoplastic pellets.

---

## 1. Filament vs. Direct Pellet Extrusion Economics & Throughput

```
                     Throughput & Raw Material Cost Scaling
                     
     Throughput [kg/h]                              Raw Material Cost [$/kg]
            ▲                                              ▲
       50 kg ┼───────────────╮ (FGF Pellets)        $80 ───┼── (Spool Filament)
             │               │                             │
             │               │                      $30 ───┼── (Technical CF Spools)
        5 kg ┼───────╮       │                             │
       0.1 kg┼── (FDM)       │                      $4–$8 ─┼───────────── (FGF Bulk Pellets)
             └───────┴───────┴────────►                    └─────────────┴────────►
```

### 1.1 Fundamental Comparative Metrics

| Attribute | Desktop / Industrial FDM (Filament) | Large Format FGF / LSAM (Direct Pellet) |
| :--- | :---: | :---: |
| **Feedstock Format** | $1.75\text{ mm}$ or $2.85\text{ mm}$ extruded filament spool | Standard $3\text{ mm}$ spherical/cylindrical pellets |
| **Material Cost (PA6/PA12-CF)** | $\$60\text{–}\$120\text{ / kg}$ | **$\$8\text{–}\$18\text{ / kg}$ ($5\text{–}8\times$ cheaper)** |
| **Max Volumetric Flow Rate** | $15\text{–}40\text{ mm}^3\text{/s}$ | **$2,000\text{–}25,000\text{ mm}^3\text{/s}$** |
| **Nozzle Orifice Diameter** | $0.4\text{–}0.8\text{ mm}$ | **$4.0\text{–}15.0\text{ mm}$** |
| **Typical Bead Dimensions** | $0.45\text{ mm}$ wide $\times 0.2\text{ mm}$ high | **$8.0\text{–}18.0\text{ mm}$ wide $\times 2.5\text{–}5.0\text{ mm}$ high** |
| **Extrusion Mechanism** | Dual hobbed drive gears pushing solid wire | **Reciprocating / continuous rotating Archimedes screw** |

---

## 2. Single-Screw Plasticizing Extruder Physics

Direct pellet extruders miniaturize industrial plasticating extrusion technology onto a gantry or robotic arm.

```
       Pellet Hopper
             │
             ▼
      ┌──────────────┬──────────────────┬─────────────────┬──────────┐
      │  FEED ZONE   │ COMPRESSION ZONE │  METERING ZONE  │ DIE TIP  │
      │  (Solid Bed) │ (Melting & Vent) │ (High Pressure) │ (Nozzle) │
      └──────────────┴──────────────────┴─────────────────┴──────────┘
      ◄───────────── Flight Depth Decreases (h_feed > h_meter) ────────►
```

### 2.1 Screw Geometry Ratios
1.  **Length-to-Diameter Ratio ($L/D$):**
    Must satisfy **$L/D \ge 18:1\text{ to }24:1$** to ensure complete, homogenous melting of plastic pellets before reaching the nozzle orifice.
2.  **Compression Ratio ($CR$):**
    $$CR = \frac{h_{feed}}{h_{meter}} \approx 2.5:1\text{–}3.5:1$$
    As the channel depth $h$ narrows from feed to metering, air voids between pellets are compressed out backward through the hopper, preventing porosity in the extruded bead.
3.  **Drive Torque Equation:**
    $$T = \frac{Q \cdot \Delta P}{\eta_{screw} \cdot \omega}$$
    Extruding $15\text{ kg/h}$ of viscous high-temperature carbon-fiber reinforced resin requires high-torque servo gearmotors producing $> 50\text{–}150\text{ Nm}$.

---

## 3. The Thermal Cooling Window & Critical Layer Time

In large-format printing, if a new layer is deposited **too quickly**, the previous bead has not solidified and collapses under the weight of upper layers ($T > T_g$).
If deposited **too slowly**, the previous bead cools below the crystallization/autohesion threshold ($T < T_{weld}$), resulting in **zero interlayer bond strength (cold joints)**.

```
                    The "Goldilocks" Thermal Layer Window
                    
      Temperature (T)
             ▲
      T_melt ┼─ ── ── ── ── ── ── ── ── ── ── ── ── ──
             │   \
             │    \  Too Fast: Bead Slumps & Sags!
      T_weld ┼─ ─ ─ \ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
             │       \   ★ OPTIMAL WELD ZONE (Bond Strength > 85%)
      T_crys ┼─ ─ ─ ─ \ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
             │         \  Too Slow: Cold Joint / Delamination!
             └──────────┴───────────┴────────────────► Layer Cycle Time (t_layer)
                      t_min        t_max
```

### 3.1 Mathematical Formulation of Layer Time Window
*   **Minimum Layer Solidification Time ($t_{min}$):**
    $$t_{min} = \frac{\rho C_p A_{bead}}{h_{conv} P_{perim}} \ln\left( \frac{T_{nozzle} - T_{ambient}}{T_{solid} - T_{ambient}} \right)$$
*   **Maximum Layer Autohesion Time ($t_{max}$):**
    The interface must remain above $T_{weld}$ ($> 180^\circ\text{C}$ for PA6) for long enough to allow polymer chain reptation:
    $$t_{welding} \ge \tau_{reptation}(T)$$
*   *Industrial Fix:* Large LSAM systems (Cincinnati Inc., Ingersoll) utilize **traveling infrared heaters** directly ahead of the extruder nozzle to pre-heat the top surface of the substrate immediately before the new bead is deposited.

---

## 4. Residual Thermal Stress & Non-Linear Scaling

Thermal strain $\epsilon_{th} = \alpha \cdot \Delta T$ is constant regardless of size. However, **elastic strain energy ($U$) scales with total part volume ($L^3$)**:

$$U = \iiint_V \frac{1}{2} E \epsilon_{th}^2 \, dV \propto L^3$$

*   In a $100\text{ mm}$ desktop part, internal strain energy is absorbed elastically without detaching from the build plate.
*   In a $2000\text{ mm}$ LSAM part, the accumulated strain energy exceeds the critical fracture toughness ($G_{Ic}$) of the plastic, causing:
    1.  **Explosive bed detachment:** Parts tear up heavy aluminum or steel build plates.
    2.  **Transverse cracking:** Massive horizontal fissures rip through the middle of the part during cooling.
*   *Solution:* **High-Aspect Ratio Chopped Carbon Fiber ($20\text{–}30\%\text{ wt}$):**
    CF drops the coefficient of thermal expansion ($\alpha$) from $100 \times 10^{-6}\text{ /K}$ to $< 15 \times 10^{-6}\text{ /K}$, suppressing thermal shrinkage moments by $> 80\%$.

---

## 5. Near-Net-Shape Hybrid Manufacturing Pipeline

FGF deposition produces thick, ribbed structures with $R_a \approx 50\ \mu\text{m}$. Precision mechanical parts (bearings seats, bolt flanges) require a **Hybrid Additive-Subtractive Pipeline**:

```
      Step 1: Near-Net Deposition           Step 2: Post-Machining Precision Surfaces
      (12mm Nozzle Bead, +3mm Stock)        (5-Axis CNC Mill Trims Bearing Bores)
          ╭─────────────────╮                   ┌─────────────────┐
         (   ~ ~ ~ ~ ~ ~ ~   )       ════►      │   H7 Bore 0.01  │  H7 Bore / Ra 0.4 µm
          ╰─────────────────╯                   └─────────────────┘
```

1.  **Additive Near-Net Stage (Blender CAD):**
    *   Model structural geometry with a **$+3.0\text{ mm}\text{ to }+5.0\text{ mm}$ sacrificial machining envelope** on all functional faces.
2.  **Subtractive 5-Axis Finish Milling:**
    *   Once cooled and thermally stabilized, the part is probed on a 5-axis CNC gantry router.
    *   Bearing seats are milled to **ISO H7**, sealing glands to **$R_a \le 0.8\ \mu\text{m}$**, and dowel locating holes are reamed in a single setup.

---

## 6. References & Standards

1.  **Love, L. J., et al. (2014).** *The importance of carbon fiber to large scale additive manufacturing.* Journal of Materials Research, 29(17), 1893–1898. [DOI: 10.1557/jmr.2014.212] (Oak Ridge National Laboratory BAAM system architecture and thermal stress mitigation).
2.  **Compton, B. G., & Lewis, J. A. (2014).** *3D-printing of lightweight cellular composites.* Advanced Materials, 26(34), 5930–5935. [DOI: 10.1002/adma.201401804] (Fiber alignment dynamics in high-aspect-ratio extrusion nozzles).
3.  **Tadmor, Z., & Gogos, C. G. (2006).** *Principles of Polymer Processing* (2nd ed.). John Wiley & Sons. (Plasticating screw mechanics, solids conveying, melting models, and die pressure drops).
4.  **Duty, C. E., et al. (2018).** *Structure and properties of big area additive manufacturing (BAAM) materials.* Rapid Prototyping Journal, 24(6), 1045–1056. [DOI: 10.1108/RPJ-04-2017-0067]
5.  **ISO/ASTM 52900:2021.** *Additive manufacturing — General principles — Fundamentals and vocabulary.* ISO/ASTM International.

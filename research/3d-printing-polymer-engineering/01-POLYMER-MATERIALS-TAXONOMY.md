# Polymer Materials Taxonomy & Thermal-Mechanical Properties for 3D Printing

**Date:** 2026-09-05  
**Scope:** Exhaustive material science taxonomy of additive manufacturing polymers (commodity, functional, high-temperature, fiber-reinforced, elastomers, and photopolymer resins) with quantitative mechanical, thermal, and chemical performance data.

---

## 1. Polymer Classification & Molecular Architecture

Polymers in additive manufacturing are divided into two fundamental thermal-rheological classes:
1.  **Thermoplastics (FDM / FFF / SLS):** Linear or branched molecular chains held together by weak intermolecular van der Waals forces. Reversibly melt upon heating and solidify upon cooling.
    *   **Amorphous:** Randomly entangled molecular coils (e.g., ABS, ASA, PC, PMMA, Ultem PEI). Soften gradually above Glass Transition Temperature ($T_g$); low, isotropic thermal shrinkage ($0.4\text{–}0.8\%$); optical clarity; susceptible to solvent cracking.
    *   **Semi-Crystalline:** Possess distinct ordered crystalline lamellae dispersed in an amorphous matrix (e.g., PLA, PETG, PA/Nylon, POM, PEEK, PP). Exhibit sharp melting points ($T_m$); higher chemical and fatigue resistance; high volumetric shrinkage ($1.2\text{–}2.5\%$) as polymer chains pack densely into crystal lattices.
2.  **Thermosets (SLA / DLP / MSLA / PolyJet):** Liquid monomers and oligomers photopolymerized via UV cross-linking into a permanent 3D covalent network. Do not melt upon heating; decompose at extreme temperatures.

```
                         POLYMER MORPHOLOGY TREE
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
       AMORPHOUS                                      SEMI-CRYSTALLINE
   - Glass Transition Tg                             - Melting Temp Tm
   - Low shrinkage (0.4–0.8%)                        - High shrinkage (1.2–2.5%)
   - Examples: ABS, ASA, PC, PEI                     - Examples: PLA, PA, PEEK, PP
```

---

## 2. Quantitative Material Properties Database

All data reflects standard 3D printed specimens (printed in XY orientation at optimal parameters):

| Polymer Material | Tensile Strength XY (MPa) | Tensile Modulus (GPa) | Elongation at Break | Heat Deflection Temp HDT @ 0.45 MPa | Glass Transition $T_g$ | Volumetric Shrinkage | Moisture Uptake (Equil.) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standard PLA** | $55\text{–}65$ | $3.5\text{–}3.8$ | $4\text{–}6\%$ | $52\text{–}55^\circ\text{C}$ | $58^\circ\text{C}$ | $0.2\text{–}0.4\%$ | $0.3\%$ |
| **Tough PLA / PLA+** | $45\text{–}55$ | $2.8\text{–}3.2$ | $12\text{–}20\%$ | $55\text{–}58^\circ\text{C}$ | $60^\circ\text{C}$ | $0.3\text{–}0.5\%$ | $0.3\%$ |
| **PETG** | $48\text{–}52$ | $2.0\text{–}2.2$ | $15\text{–}25\%$ | $70\text{–}74^\circ\text{C}$ | $78^\circ\text{C}$ | $0.4\text{–}0.6\%$ | $0.2\%$ |
| **ABS** | $38\text{–}44$ | $2.1\text{–}2.4$ | $10\text{–}20\%$ | $90\text{–}98^\circ\text{C}$ | $105^\circ\text{C}$ | $0.7\text{–}0.9\%$ | $0.4\%$ |
| **ASA** | $40\text{–}46$ | $2.2\text{–}2.4$ | $15\text{–}25\%$ | $95\text{–}102^\circ\text{C}$ | $108^\circ\text{C}$ | $0.6\text{–}0.8\%$ | $0.3\%$ |
| **Polycarbonate (PC)** | **$68\text{–}75$** | $2.3\text{–}2.5$ | $30\text{–}50\%$ | **$135\text{–}142^\circ\text{C}$** | $147^\circ\text{C}$ | $0.6\text{–}0.8\%$ | $0.2\%$ |
| **Nylon PA12** | $45\text{–}50$ | $1.4\text{–}1.7$ | **$50\text{–}120\%$** | $85\text{–}95^\circ\text{C}$ | $50^\circ\text{C}$ | $1.2\text{–}1.6\%$ | $1.5\%$ |
| **Nylon PA6** | $60\text{–}70$ | $1.8\text{–}2.3$ | $40\text{–}80\%$ | $110\text{–}130^\circ\text{C}$ | $55^\circ\text{C}$ | $1.5\text{–}2.0\%$ | **$7.0\text{–}9.0\%$** |
| **PA12-CF (15% CF)** | $75\text{–}85$ | **$5.5\text{–}7.0$** | $4\text{–}7\%$ | **$160\text{–}175^\circ\text{C}$** | $60^\circ\text{C}$ | **$0.1\text{–}0.2\%$** | $0.8\%$ |
| **PA6-CF (20% CF)** | **$105\text{–}120$** | **$8.5\text{–}10.5$** | $3\text{–}5\%$ | **$190\text{–}215^\circ\text{C}$** | $70^\circ\text{C}$ | **$0.1\text{–}0.2\%$** | $3.5\%$ |
| **PEEK (Neat)** | $95\text{–}100$ | $3.8\text{–}4.2$ | $15\text{–}30\%$ | $155^\circ\text{C}$ ($250^\circ\text{C}$ ann.) | $143^\circ\text{C}$ | $1.8\text{–}2.4\%$ | $0.1\%$ |
| **Ultem 9085 (PEI)** | $80\text{–}85$ | $2.5\text{–}2.7$ | $8\text{–}12\%$ | $165\text{–}173^\circ\text{C}$ | $186^\circ\text{C}$ | $0.5\text{–}0.7\%$ | $0.3\%$ |
| **TPU 95A** | $35\text{–}45$ | $0.15\text{–}0.25$ | **$450\text{–}600\%$** | $45^\circ\text{C}$ | $-40^\circ\text{C}$ | $0.8\text{–}1.2\%$ | $0.5\%$ |
| **Standard SLA Resin** | $50\text{–}65$ | $2.5\text{–}3.0$ | $4\text{–}8\%$ | $50\text{–}58^\circ\text{C}$ | N/A | $1.5\text{–}2.5\%$ | $0.4\%$ |
| **Tough SLA Resin** | $40\text{–}50$ | $1.8\text{–}2.2$ | $20\text{–}35\%$ | $60\text{–}70^\circ\text{C}$ | N/A | $1.2\text{–}1.8\%$ | $0.3\%$ |

---

## 3. Engineering Material Profiles & Selection Rules

### 3.1 Polylactic Acid (PLA)
*   **Physics:** Bioderived, highly rigid ($E \approx 3.6\text{ GPa}$), high tensile strength, zero odor.
*   **The Creep & Thermal Failure Mode:** Glass transition occurs at only $55^\circ\text{C}$. In an enclosed car or under continuous mechanical spring load at room temperature, PLA undergoes cold viscoelastic flow (**creep**) within weeks.
*   *Verdict:* Prototyping, aesthetic models, non-stressed brackets. Never use for motor mounts or pressurized housings.

### 3.2 PETG (Polyethylene Terephthalate Glycol-Modified)
*   **Physics:** Amorphous copolymer with glycol modifier preventing crystallization; superior layer adhesion; water and acid resistant.
*   **Mechanics:** Moderate stiffness ($E \approx 2.1\text{ GPa}$); yields ductilely without shattering.
*   *Verdict:* Water fittings, snap-fit clips, general outdoor enclosures up to $65^\circ\text{C}$.

### 3.3 ABS & ASA (Acrylonitrile Butadiene Styrene / Acrylonitrile Styrene Acrylate)
*   **Physics:** Terpolymers combining chemical resistance (acrylonitrile), elastomeric impact toughness (butadiene/acrylate rubber phase), and rigidity (styrene).
*   **ASA Superiority:** ASA replaces butadiene rubber with acrylic ester, eliminating UV degradation. ASA parts survive 10+ years of direct sunlight without yellowing or embrittlement.
*   *Processing:* High thermal shrinkage ($0.8\%$). Mandatory heated chamber ($45\text{–}60^\circ\text{C}$) to prevent corner warping and layer delamination.

### 3.4 Polycarbonate (PC)
*   **Physics:** The highest impact strength of any transparent thermoplastic (bulletproof glass standard). Retains ductility at $-40^\circ\text{C}$.
*   *Processing:* Requires nozzle temperatures of $280\text{–}310^\circ\text{C}$, bed temperatures $> 110^\circ\text{C}$, and an enclosed chamber $> 60^\circ\text{C}$.

### 3.5 Polyamide (Nylon PA6 vs. PA12)
*   **The Water Equilibrium Reality:**
    *   **PA6:** Exceptional tensile strength and fatigue life when dry, but absorbs up to **$9\%$ water** from ambient air. Absorbed water acts as an internal plasticizer, cutting tensile strength by $50\%$ while increasing elongation by $300\%$.
    *   **PA12:** Longer carbon backbone reduces moisture uptake to **$< 1.5\%$**, making it far more dimensionally stable in humid environments.
*   *Printing Requirement:* Must be dried in a desiccant oven at $80^\circ\text{C}$ for $\ge 8\text{ hours}$ before printing. Wet filament boils in the nozzle, creating porous, foaming, structurally useless parts.

### 3.6 Carbon-Fiber Reinforced Polymers (PA-CF, PET-CF, PC-CF)
*   **Microstructure:** Short chopped carbon fibers ($10\text{–}20\%$ weight, length $\approx 100\text{–}200\ \mu\text{m}$) embedded in the polymer matrix.
*   **Anisotropy Transformation:** Fibers align along the extrusion path, reducing in-plane thermal expansion to near zero. **Eliminates warping completely** while tripling stiffness ($E \to 10\text{ GPa}$).
*   *Hardware Mandate:* Carbon fibers destroy standard brass nozzles in $< 200\text{ grams}$ of extrusion. Requires **hardened steel, tungsten carbide, or ruby nozzles**.

---

## 4. References & Primary Standards

1. **ASTM D638-14:** *Standard Test Method for Tensile Properties of Plastics*. ASTM International, West Conshohocken, PA.
2. **ASTM D648-18:** *Standard Test Method for Deflection Temperature of Plastics Under Flexural Load in the Edgewise Position (HDT)*.
3. **ISO 527-1:2019 / ISO 527-2:2012:** *Plastics — Determination of tensile properties — Part 2: Test conditions for moulding and extrusion plastics*.
4. **Markforged Materials Engineering Data Sheet:** *Onyx (Micro-carbon fiber filled nylon)* & *Continuous Fiber Performance Specs* (2022).
5. **Stratasys Technical Whitepaper:** *ULTEM™ 9085 Resin Material Characterization for Aerospace Applications* (Document No. C-10118).
6. **3DXTECH Technical Data Sheets:** *CarbonX™ Carbon Fiber PA6 & CarbonX™ Carbon Fiber PA12 Mechanical Profiles* (2023).
7. **Callister, W. D., & Rethwisch, D. G. (2018):** *Materials Science and Engineering: An Introduction* (10th ed.). John Wiley & Sons. ISBN: 978-1119405498.

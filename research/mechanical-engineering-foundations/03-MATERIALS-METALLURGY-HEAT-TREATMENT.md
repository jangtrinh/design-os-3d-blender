# Materials Science, Engineering Alloys & Heat Treatment

**Date:** 2026-09-05  
**Scope:** Ferrous alloys (carbon, alloy, tool, and stainless steels), non-ferrous structural alloys (aluminum, titanium, bronze), engineering polymers (Delrin, PEEK, Nylon), heat treatment metallurgy, and surface finishes.

---

## 1. Ferrous Alloys: Steels, Tool Steels & Stainless Steels

Iron-carbon alloys are the backbone of load-bearing mechanical engineering. Mechanical properties depend on carbon content, alloying elements, and microstructural phase (Ferrite, Pearlite, Bainite, Martensite, Austenite).

```
                 The Steel Selection Decision Matrix
                                   │
             ┌─────────────────────┴─────────────────────┐
             ▼                                           ▼
      General Structural                          Specialized Duty
      ├─ 1018: Low carbon, cold rolled            ├─ 4140: High fatigue shafts
      ├─ 1045: Medium carbon, induction           ├─ D2: High wear die tooling
      └─ A36: Welded frames / plates              ├─ 17-4PH: High strength stainless
                                                  └─ 8620: Case-carburized gears
```

### 1.1 Structural Carbon & Alloy Steels

| Alloy Grade | Tensile Yield $S_y$ (MPa) | Ultimate $S_{ut}$ (MPa) | Elongation | Typical Hardness | Best Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **AISI 1018** | $370$ | $440$ | $15\%$ | $126\text{ HB}$ | Turned pins, weldments, general brackets |
| **AISI 1045** | $450$ | $570$ | $12\%$ | $170\text{ HB}$ | Hydraulic cylinder rods, induction-hardened axles |
| **AISI 4140 (Cr-Mo)** | $655\text{–}950$ | $850\text{–}1080$ | $15\text{–}20\%$ | $28\text{–}34\text{ HRC}$ | Highly loaded shafts, motor flanges, studs |
| **AISI 4340 (Ni-Cr-Mo)** | $860\text{–}1200$ | $1000\text{–}1350$ | $12\text{–}15\%$ | $32\text{–}40\text{ HRC}$ | Aerospace rotating shafts, severe shock axles |
| **AISI 8620** | $385$ (core) | $530$ (core) | $15\%$ | $60\text{ HRC}$ (case) | High-performance gears, camshafts, drive pins |

### 1.2 Tool Steels (High Wear & Impact Tooling)
*   **AISI D2 (Air-Hardening, High-Carbon High-Chromium):**
    *   *Hardness:* $58\text{–}62\text{ HRC}$.
    *   *Properties:* Extreme abrasive wear resistance; excellent dimensional stability during heat treatment (minimal quench distortion).
    *   *Use:* Punches, shear blades, stamping dies, precision guide rails.
*   **AISI O1 (Oil-Hardening):**
    *   *Hardness:* $57\text{–}62\text{ HRC}$.
    *   *Properties:* High general-purpose wear resistance; available as precision ground flat stock ("gauge plate").
*   **AISI H13 (Hot-Work):**
    *   *Hardness:* $46\text{–}52\text{ HRC}$.
    *   *Properties:* Retains strength at high temperatures ($500\text{–}600^\circ\text{C}$); resists thermal fatigue cracking ("heat checking"). Standard for injection molds and die-casting tooling.

### 1.3 Stainless Steels
1.  **Austenitic 304 (1.4301 / 18-8):** Non-magnetic, general food/chemical corrosion resistance, excellent weldability. Cannot be heat treated (hardens only via cold work).
2.  **Austenitic 316 (1.4401 / Marine Grade):** $2\text{–}3\%$ Molybdenum addition provides pitting resistance against chlorides and acids.
3.  **Martensitic 410 / 420:** Magnetic, high carbon; heat treatable up to $50\text{–}54\text{ HRC}$. Surgical instruments, pump shafts, turbine blades.
4.  **Precipitation Hardening 17-4PH (AISI 630):**
    *   *Properties:* Yield strength up to **$1170\text{ MPa}$** in H900 condition.
    *   *Advantage:* Shipped in Solution Annealed Condition A (easily machined); heat treated at low temperature ($480^\circ\text{C}\text{–}620^\circ\text{C}$) with **near-zero scaling and distortion**.

---

## 2. Non-Ferrous Structural Alloys

### 2.1 Aluminum Alloys Comparison

| Alloy & Temper | Yield $S_y$ (MPa) | Ultimate $S_{ut}$ (MPa) | Weldability | Corrosion | Dominant Application |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **6061-T6** | $276$ | $310$ | Excellent | Good | Universal standard: CNC frames, robot links, housings |
| **7075-T651** | **$503$** | $572$ | Poor | Moderate | Aerospace, high-stress gears, suspension uprights |
| **5052-H32** | $193$ | $228$ | Excellent | Superior (Marine) | Sheet metal enclosures, chassis, tanks |
| **2024-T3** | $345$ | $483$ | Poor | Fair | High cyclic fatigue aircraft skins, tension links |

*Engineering Rule:* 7075-T6 approaches structural steel strength at $1/3$ the density ($\rho = 2.81\text{ g/cm}^3$), but requires hard anodizing (Type III) in outdoor environments due to copper/zinc galvanic corrosion.

### 2.2 Titanium Alloys (Ti-6Al-4V / Grade 5)
*   *Density:* $4.43\text{ g/cm}^3$ | *Tensile Yield:* $880\text{ MPa}$ | *Elastic Modulus:* $114\text{ GPa}$.
*   *Specific Strength:* Twice that of 6061-T6 aluminum.
*   *Thermal Conductivity:* Extremely low ($6.7\text{ W/m}\cdot\text{K}$ vs. $167\text{ W/m}\cdot\text{K}$ for aluminum). Generates intense cutting temperatures during CNC machining; requires rigid tooling and flood high-pressure coolant.

### 2.3 Bearing Bronzes & Brasses
*   **SAE 660 Bronze (CuSn7Zn4Pb7):** The universal bushing material. The lead/tin phase acts as a solid lubricant during boundary lubrication regimes.
*   **C36000 Free-Cutting Brass:** Machinability rating is the $100\%$ baseline index against which all other metals are evaluated.

---

## 3. Engineering Polymers & Performance Plastics

```
           Mechanical Strength vs. Operating Temperature
       
      300°C ▲
            │                                  [ PEEK ]
      200°C │                 [ PTFE ]
            │   [ Delrin / POM ]  [ Nylon PA66 ]
      100°C │
            │   [ Polycarbonate ]   [ ABS ]
        0°C └──────────────┬──────────────────┬──────────► Tensile Strength
                          50 MPa            100 MPa
```

### 3.1 Polymer Profiles
1.  **Delrin / Acetal (POM-C Copolymer / POM-H Homopolymer):**
    *   *Friction:* $\mu \approx 0.15\text{–}0.20$ against steel. Zero stick-slip.
    *   *Moisture Absorption:* Negligible ($0.2\%$). Preserves sub-millimeter precision in humid environments.
    *   *Use:* Precision gears, sliding bushings, conveyor wear strips.
2.  **PEEK (Polyether Ether Ketone):**
    *   *Thermal:* Continuous service up to $250^\circ\text{C}$ ($300^\circ\text{C}$ short term).
    *   *Strength:* Tensile yield $100\text{ MPa}$. Resists radiation, steam, hydrocarbons.
    *   *Use:* Downhole drilling tools, aerospace cable brackets, medical implants.
3.  **Nylon (Polyamide PA6 / PA66 / PA12):**
    *   *Properties:* High impact toughness and damping.
    *   *The Moisture Trap:* Absorbs up to **$2.5\text{–}8.0\%$ atmospheric water**, causing dimensional swelling ($\Delta L \approx 1\text{–}3\%$) and dropping elastic modulus by $50\%$. Never use raw PA6 for precision bearing seats.

---

## 4. Metallurgy of Heat Treatment & Surface Hardening

```
           Through-Hardening                     Case-Hardening (Carburizing)
     ┌───────────────────────────┐               ┌───────────────────────────┐
     │                           │               │ ░░░░░ 60 HRC Hard Case ░░░│ (0.5–2.0mm)
     │  58 HRC Uniform Hardness  │               │                           │
     │   Throughout Core         │               │   32 HRC Ductile Core     │
     │                           │               │                           │
     └───────────────────────────┘               └───────────────────────────┘
```

### 4.1 Through-Hardening (Quench and Temper)
1.  **Austenitizing:** Heat steel above $A_{c3}$ ($800\text{–}880^\circ\text{C}$) to dissolve carbon into Face-Centered Cubic (FCC) austenite.
2.  **Quenching:** Rapidly cool in oil or water below the Martensite Start ($M_s$) temperature to trap carbon in Body-Centered Tetragonal (BCT) **martensite** ($60\text{–}65\text{ HRC}$).
3.  **Tempering:** Reheat between $200\text{–}600^\circ\text{C}$ to relieve internal micro-strains and restore fracture toughness.

### 4.2 Surface Hardening Processes
*   **Carburizing (Case Hardening):** Diffuses carbon into low-carbon steel (8620, 1018) at $900^\circ\text{C}$, followed by quenching. Yields a $60\text{ HRC}$ glass-hard wear surface with a ductile $32\text{ HRC}$ shock-resistant core.
*   **Nitriding (Ferritic Nitrocarburizing / QPQ):** Nitrogen diffused into steel at $500\text{–}550^\circ\text{C}$.
    *   *Advantage:* Operates below the transformation temperature, resulting in **zero quench distortion or volumetric shrinkage**. Surface hardness reaches $> 65\text{–}70\text{ HRC}$ equivalent.

---

## 5. Protective & Functional Surface Finishes

| Surface Finish | Substrate | Layer Thickness | Primary Functional Purpose |
| :--- | :--- | :---: | :--- |
| **Anodize Type II** | Aluminum | $10\text{–}25\ \mu\text{m}$ | Atmospheric corrosion protection, color dying. |
| **Anodize Type III (Hardcoat)** | Aluminum | $50\ \mu\text{m}$ | Severe wear resistance ($65\text{ HRC}$ equivalent surface), dielectric insulation. |
| **Electroless Nickel Plating (ENP)** | Steels, Aluminum | $10\text{–}30\ \mu\text{m}$ | **100% uniform thickness** across complex internal blind holes; corrosion & wear barrier. |
| **Black Oxide (MIL-DTL-13924)** | Carbon Steels | $< 1.0\ \mu\text{m}$ | Zero dimensional change; mild corrosion resistance with oil retention. |
| **PVD Coatings (TiN, TiAlN, DLC)** | Tool Steels | $2\text{–}5\ \mu\text{m}$ | Extreme hardness ($> 2500\text{ HV}$), ultra-low friction, cutting tools and guide pins. |

---

## 6. References & Standards

1.  **Callister, W. D., & Rethwisch, D. G. (2020).** *Materials Science and Engineering: An Introduction* (10th ed.). John Wiley & Sons, New York. (Phase diagrams, TTT transformation kinetics, and galvanic cell potentials).
2.  **ASM International Handbook Committee. (1991).** *ASM Handbook, Volume 4: Heat Treating.* ASM International, Materials Park, OH. (Standard austenitizing, quenching, tempering, carburizing, and nitriding recipes).
3.  **MIL-A-8625F.** *Anodic Coatings for Aluminum and Aluminum Alloys.* US Department of Defense. (Type II sulfuric and Type III hardcoat anodize thickness and wear specifications).
4.  **ASTM B733-22.** *Standard Specification for Autocatalytic (Electroless) Nickel-Phosphorus Coatings on Metal.* ASTM International. (Uniform coating deposition on complex machined surfaces).
5.  **Fontana, M. G. (1986).** *Corrosion Engineering* (3rd ed.). McGraw-Hill. (Electrochemical series, galvanic couple tables, and passivation mechanisms).
6.  **ISO 18265:2013.** *Metallic materials — Conversion of hardness values.* International Organization for Standardization. (Vickers, Brinell, Rockwell B/C conversion matrices).


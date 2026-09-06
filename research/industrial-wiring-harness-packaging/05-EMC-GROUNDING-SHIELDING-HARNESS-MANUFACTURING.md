# Industrial EMC, Grounding, Shield Termination & Harness Manufacturing

> **Document ID:** `RES-ELEC-PKG-05`  
> **Status:** Production Architecture Specification  
> **Applicable Standards:** IEC 61000-5-2, EN 50174-2, IEC 62153-4-3, IPC/WHMA-A-620E, UL 486A-B, IEC 60352-2, SAE-AMS-DTL-23053/4, IEEE 1100 (Emerald Book).

---

## 1. Physical Mechanisms of Electromagnetic Interference (EMI)

### 1.1 Inductive (Magnetic) and Capacitive (Electric) Coupling
Industrial factory floors feature extreme $di/dt$ switching transients from Pulse Width Modulation (PWM) Variable Frequency Drives (VFDs) and inductive contactor dropouts:
$$\frac{di}{dt} \ge 10^7\text{ A/s}, \quad \frac{dv}{dt} \ge 10^9\text{ V/s}$$

The noise voltage induced on a signal victim circuit by an adjacent aggressor conductor is governed by mutual inductance $M$ and mutual capacitance $C_m$:

#### Inductive (Magnetic Field) Coupling:
$$V_{ind} = -M \frac{di_{aggressor}}{dt} = -\left(\frac{\mu_0 \cdot \ell}{2\pi} \ln\left[1 + \left(\frac{h}{d}\right)^2\right]\right) \frac{di}{dt}$$
*Where:*
- $\ell$ = Parallel run length ($\text{m}$)
- $d$ = Center-to-center conductor separation ($\text{m}$)
- $h$ = Height of loop above reference ground plane ($\text{m}$)
- $\mu_0 = 4\pi \times 10^{-7}\text{ H/m}$

#### Capacitive (Electric Field) Coupling:
$$I_{cap} = C_m \frac{dv_{aggressor}}{dt}$$
Noise voltage across victim terminal load $R_L$:
$$V_{noise, cap} = \frac{j\omega R_L C_m}{1 + j\omega R_L (C_m + C_{victim})} V_{aggressor}$$

```
Aggressor Cable (VFD Inverter Output)
 ───────► I_aggressor(t) (high di/dt) ────────►
    │                               ▲
    │ C_m (Capacitive)             │ M (Mutual Inductance)
    ▼                               │
 ───────► I_victim(t) (Sensor / Fieldbus) ────►
```

---

## 2. Cable Shielding Physics: Skin Depth & Transfer Impedance

### 2.1 Skin Depth ($\delta$)
At high frequencies, current concentrates along the conductor surface due to eddy currents counteracting the interior magnetic field:
$$\delta = \sqrt{\frac{\rho}{\pi \cdot f \cdot \mu_r \cdot \mu_0}}$$
*Parameters for Tinned Copper Braid ($\rho = 1.72 \times 10^{-8}\,\Omega\cdot\text{m}$, $\mu_r = 1$):*
- At $50\text{ Hz}$: $\delta = 9.35\text{ mm}$ (Entire cross-section conducts; zero magnetic shielding).
- At $1\text{ MHz}$: $\delta = 66.1\,\mu\text{m}$.
- At $100\text{ MHz}$: $\delta = 6.61\,\mu\text{m}$.
- At $1\text{ GHz}$: $\delta = 2.09\,\mu\text{m}$.

### 2.2 Surface Transfer Impedance ($Z_T$) per IEC 62153-4-3
Shield effectiveness is quantified by Surface Transfer Impedance $Z_T$, defined as internal open-circuit longitudinal voltage gradient ($dV_i / dz$) per unit external shield interference current ($I_s$):
$$Z_T = \frac{1}{I_s} \left|\frac{dV_i}{dz}\right| \quad \left[\Omega/\text{m}\right]$$

| Cable Shield Construction | $Z_T$ at $100\text{ kHz}$ ($\text{m}\Omega/\text{m}$) | $Z_T$ at $10\text{ MHz}$ ($\text{m}\Omega/\text{m}$) | $Z_T$ at $100\text{ MHz}$ ($\text{m}\Omega/\text{m}$) | Industrial Protocol Fit |
|---|---|---|---|---|
| Single Tinned Copper Braid ($85\%$ cov.) | $15\text{–}25$ | $30\text{–}50$ | $200\text{–}500$ | IO-Link, CAN, RS-485 |
| Dual Braid (Outer + Inner, $>95\%$ cov.) | $5\text{–}10$ | $8\text{–}15$ | $50\text{–}100$ | PROFIBUS DP, DeviceNet |
| Braid + Aluminum/Polyester Foil (SF/UTP) | $8\text{–}12$ | $4\text{–}8$ | $15\text{–}30$ | Industrial Ethernet, PROFINET |
| Foil per pair + Overall Braid (S/FTP) | $2\text{–}5$ | $1\text{–}3$ | $5\text{–}15$ | Cat6A / Cat7 EtherCAT / 10GbE |

---

## 3. The Pigtail Failure Mechanism vs $360^\circ$ Circumferential Clamping

### 3.1 Parasitic Inductance of "Pigtail" Drain Wires
Terminating a cable braid shield by stripping it back, twisting it into a wire ("pigtail"), and fastening it under a terminal screw ruins shield performance at high frequencies.
A wire has intrinsic self-inductance:
$$L_{wire} \approx 1.0\text{–}1.2\text{ nH/mm}$$

For a $50\text{ mm}$ twisted braid pigtail:
$$L_{pigtail} \approx 50\text{ nH}$$
$$Z_{pigtail} = 2\pi \cdot f \cdot L$$
- At $100\text{ kHz}$: $Z_{pigtail} = 2\pi \times 10^5 \times 50 \times 10^{-9} = 0.031\,\Omega$.
- At $10\text{ MHz}$: $Z_{pigtail} = 3.14\,\Omega$.
- At $100\text{ MHz}$: $Z_{pigtail} = 31.4\,\Omega$.

A noise shield current $I_s = 200\text{ mA}$ from a nearby VFD switching transient develops:
$$V_{shield\_ground} = I_s \cdot Z_{pigtail} = 0.2\text{ A} \times 31.4\,\Omega = 6.28\text{ V}$$
This ground bounce injects common-mode noise directly onto differential receiver inputs, causing CRC errors and bus drops.

```
WRONG: Pigtail Drain Wire (High Inductance L ~ 1 nH/mm)
==================[ Outer Jacket ]
 ────────┐   ┌──────────────────────── Core Wires
   Braid └───┴───► [Twisted Pigtail] ───► L_pigtail ───► Terminal Screw Ground
                  (Destroys RF shielding above 1 MHz)

CORRECT: 360° Circumferential Bond (IEC 61000-5-2)
==================[ Outer Jacket ]
   [Braid 360° Flare]
      ▼
 ┌──────────┐◄── Full Circumferential Conductive Iris / EMC Cable Gland
 │  Gland   │    Ground Path Impedance < 0.005 Ohm up to 1 GHz
 └──────────┘───► Direct Chassis Face Grounding
```

### 3.2 $360^\circ$ EMC Termination Hardware
- **EMC Cable Glands (DIN EN 62444):** Utilize a conical brass clamping iris or spring-loaded stainless-steel fingers contacting the full circumference of the exposed braid.
- **M12 / M8 Metal Backshells:** The braided shield is crimped between a metal ferrule and the connector zinc die-cast outer shell. Transfer impedance through shell: $< 5\,\text{m}\Omega$.

---

## 4. Physical Route Segregation per EN 50174-2

To prevent crosstalk between power, motor, and signal circuits, cables are classified into 4 electromagnetic immunity/emission categories:

| Category | Description | Voltage & Signal Type | Typical Factory Cables |
|---|---|---|---|
| **Cat 1** | Very Sensitive / High Immunity Required | Low voltage analog / digital ($\le 24\text{ VDC}$, $< 100\text{ mA}$) | Thermocouples, load cells, 4-20mA, IO-Link |
| **Cat 2** | Moderately Sensitive / Fieldbuses | Digital communication ($\le 24\text{ VDC}$, $> 100\text{ kHz}$) | PROFINET, EtherCAT, CAN, RS-485, 24V I/O |
| **Cat 3** | Disturbance Sources (Low-Medium) | Auxiliary AC/DC power ($24\text{–}400\text{ VAC}$, $\le 16\text{ A}$) | Solenoid valves, motor contactors, linear actuators |
| **Cat 4** | High Disturbance Emitters | High power switched circuits, unshielded VFDs | Servo drive cables, inverter outputs, welding power |

### 4.1 Required Clearances (Air vs Partitioned Metallic Trays)

```
   Open Air Tray (Minimum Separation A)
   [Cat 1 / Cat 2] <──────── A ────────> [Cat 3 / Cat 4]

   Continuous Steel Partition Tray (Minimum Separation reduced by 75%)
   ┌───────────────┬───────────────┐
   │ Cat 1 & Cat 2 │ Cat 3 & Cat 4 │  (Solid steel baffle bonded to ground)
   └───────────────┴───────────────┘
```

| Segregation Pair | Air Spacing (No Shield) | Air Spacing (Shielded Bus) | Solid Steel Divider ($t \ge 1.5\text{ mm}$) |
|---|---|---|---|
| **Cat 1 vs Cat 2** | $50\text{ mm}$ | $0\text{ mm}$ (Touch permitted) | $0\text{ mm}$ |
| **Cat 1 vs Cat 3** | $200\text{ mm}$ | $100\text{ mm}$ | $20\text{ mm}$ |
| **Cat 1 vs Cat 4** | $500\text{ mm}$ | $300\text{ mm}$ | $50\text{ mm}$ |
| **Cat 2 vs Cat 4** | $300\text{ mm}$ | $150\text{ mm}$ | $25\text{ mm}$ |

*Per EN 50174-2 Section 5.3:* When signal cables must cross power cables, they **must cross strictly at right angles ($90^\circ \pm 5^\circ$)** to eliminate inductive coupling ($\cos 90^\circ = 0$).

---

## 5. Industrial Harness Manufacturing Standards: IPC/WHMA-A-620E

### 5.1 Terminal Crimp Mechanics & Tensile Pull-Out Force
Per **IPC/WHMA-A-620E Class 3** (High Performance / Mission Critical) and **UL 486A-B**:
- **Crimp Height ($H_c$)**: Dimension between upper and lower crimp indent surfaces. Tolerance: $\pm 0.05\text{ mm}$ ($\pm 0.002\text{ in}$).
- **Crimp Width ($W_c$)**: Controlled by precision die geometry.
- **Wire Strand Compaction**: Solid polygon extrusion with zero inter-strand voids ($> 95\%$ cross-sectional fill).

| Wire Size (AWG) | Wire Size ($\text{mm}^2$) | Minimum Pull-Out Force UL 486A-B ($\text{N}$) | Minimum Pull-Out Force IEC 60352-2 ($\text{N}$) |
|---|---|---|---|
| **26 AWG** | $0.14\text{ mm}^2$ | $13.4\text{ N}$ ($3.0\text{ lbf}$) | $15\text{ N}$ |
| **24 AWG** | $0.22\text{ mm}^2$ | $22.3\text{ N}$ ($5.0\text{ lbf}$) | $28\text{ N}$ |
| **22 AWG** | $0.34\text{ mm}^2$ | $35.6\text{ N}$ ($8.0\text{ lbf}$) | $40\text{ N}$ |
| **20 AWG** | $0.50\text{ mm}^2$ | $57.9\text{ N}$ ($13.0\text{ lbf}$) | $60\text{ N}$ |
| **18 AWG** | $0.75\text{ mm}^2$ | $89.0\text{ N}$ ($20.0\text{ lbf}$) | $85\text{ N}$ |
| **16 AWG** | $1.50\text{ mm}^2$ | $133.5\text{ N}$ ($30.0\text{ lbf}$) | $150\text{ N}$ |
| **14 AWG** | $2.50\text{ mm}^2$ | $222.5\text{ N}$ ($50.0\text{ lbf}$) | $230\text{ N}$ |

```
Crimp Cross-Section Inspection (IPC/WHMA-A-620 Target):
      ┌───────────┐
   ┌──┘  Terminal └──┐
   │   ┌─────────┐   │  <- Symmetrical crimp wings folded inward
   │  ( ● ● ● ● )   │  <- Hexagonal strand deformation (>95% metal density)
   │   ( ● ● ● )    │  <- No loose strands; zero serration extrusion
   └───┴─────────┴───┘
```

### 5.2 Heat Shrink Tubing Specification (SAE-AMS-DTL-23053)
- **Class 1 (Thin Wall Polyolefin, 2:1 Shrink):** Operating temperature $-55^\circ\text{C}$ to $+135^\circ\text{C}$. Used for wire bundle identification and basic strain relief.
- **Class 4 (Dual-Wall Adhesive Lined, 3:1 / 4:1 Shrink):** Inner layer melts into hot-melt polyamide adhesive during heating, creating an IP67 hermetic barrier sealing against moisture creep along stranded wire.

---

## 6. Manufacturing Deliverables: Formboard & Wire Run Lists

Production-grade harness manufacturing requires two unified data structures:

### 6.1 Wire Run List (From-To Table)
```
HARNESS_ID: WH-ROBOT-WRIST-01
REV: C.1
========================================================================================
Wire ID | Signal / Function | From Conn | Pin | To Conn | Pin | AWG | Color    | Length (mm)
--------+-------------------+-----------+-----+---------+-----+-----+----------+------------
W01     | +24VDC Main Logic | J1 (Han8) | 1   | J2 (M12)| 1   | 18  | BN       | 850
W02     | 0VDC GND Return   | J1 (Han8) | 2   | J2 (M12)| 3   | 18  | BU       | 850
W03     | CAN_H (High)      | J1 (Han8) | 3   | J3 (M12)| 4   | 24  | WH (Tw)  | 920
W04     | CAN_L (Low)       | J1 (Han8) | 4   | J3 (M12)| 5   | 24  | BL (Tw)  | 920
W05     | Chassis Earth PE  | J1 (Han8) | PE  | LUG-01  | -   | 16  | GNYE     | 450
========================================================================================
```

### 6.2 Formboard (Nailboard) Coordinate Topology
In Blender 3D CAD to Formboard flattening:
1. 3D spatial Bézier curve is partitioned at branch nodes.
2. Segment arc lengths $s_i = \int_0^1 \|\mathbf{r}'(t)\| dt$ are measured.
3. Network is unrolled onto a 2D $XY$ drawing canvas ($1:1$ scale plot) with guide pegs (nails) placed at radii $R \ge R_{min}$.
4. Breakout angles must adhere to $\theta_{breakout} \le 45^\circ$ to prevent inner jacket tear.

---

## 7. Mathematical & Standards Citations

1. **IEC 61000-5-2:2019** — *Electromagnetic compatibility (EMC) - Part 5-2: Installation and mitigation guidelines - Earthing and cabling.*
2. **EN 50174-2:2018** — *Information technology - Cabling installation - Part 2: Installation planning and practices inside buildings.*
3. **IEC 62153-4-3:2013** — *Metallic communication cable test methods - Part 4-3: Electromagnetic compatibility (EMC) - Surface transfer impedance - Triaxial method.*
4. **IPC/WHMA-A-620E:2022** — *Requirements and Acceptance for Cable and Wire Harness Assemblies.*
5. **UL 486A-486B:2018** — *Wire Connectors.*
6. **IEC 60352-2:2006+AMD1:2013** — *Solderless connections - Part 2: Crimped connections - General requirements, test methods and practical guidance.*
7. **SAE-AMS-DTL-23053/4** — *Insulation Sleeving, Electrical, Heat Shrinkable, Polyolefin, Dual-Wall, Outer Wall Crosslinked.*
8. **Ott, H. W. (2009)** — *Electromagnetic Compatibility Engineering*, John Wiley & Sons, Inc., ISBN 978-0-470-18930-6.
9. **Paul, C. R. (2006)** — *Introduction to Electromagnetic Compatibility*, 2nd Edition, Wiley-Interscience, ISBN 978-0-471-75500-5.

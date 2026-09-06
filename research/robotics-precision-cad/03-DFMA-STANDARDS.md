# Design for Manufacturing and Assembly (DFMA) Standards

**Date:** 2026-09-05  
**Scope:** CNC machining rules, 3D printing tolerances and hardware integration, sheet metal design standards, and precision metric fastener rules for robotic assemblies.

---

## 1. CNC Machining Design Rules (Milling & Turning)

Subtractive manufacturing removes material with rotating cutting tools. Violating tool geometry constraints causes chatter, broken tooling, or astronomical machining costs.

### 1.1 Internal Corner Radii & The "Dogbone" Rule
*   **The Physics:** Endmills are cylindrical. A standard 3-axis CNC mill cannot cut a sharp internal $90^\circ$ vertical corner.
*   **Rule:** Internal corner radius $R_{corner} \ge \frac{D_{cutter}}{2} + 0.5\text{ mm}$.
    *   *Why the $+0.5\text{ mm}$ margin?* If $R_{corner} == R_{cutter}$, the tool engages $90^\circ$ of its circumference at the vertex, causing instantaneous tool deflection, surface chatter, and tool break. Allowing the tool to arc around the corner maintains a continuous chip load.
*   **Interlocking Reliefs (Dogbone / T-bone):** When mating rectangular parts (e.g., electronic boards or battery packs) into a pocket, use circular overcut reliefs (dogbone fillets) at corners:

```
    Standard CNC Pocket            Dogbone Relief for Square Inserts
       ┌──────────┐                         ┌───╮ ╭───┐
       │          │                         │   ╰─╯   │
       │    R     │                         │         │
       │          │                         │   ╭─╮   │
       └──────────┘                         └───╯ ╰───┘
   (Leaves unmachined corner)         (Allows 100% square mating)
```

### 1.2 Tool Reach & Pocket Aspect Ratios
*   **Aspect Ratio Formula:** $AR = \frac{\text{Depth } L}{\text{Diameter } D_{cutter}}$
*   **Engineering Limits:**
    *   $AR \le 3$: Standard milling. High feed rates, optimal surface finish ($Ra \le 0.8\ \mu\text{m}$).
    *   $3 < AR \le 6$: Extended reach. Requires reduced feeds, multiple step-downs; increases cost by $30\text{–}60\%$.
    *   $AR > 8$: Extreme risk of tool chatter and taper error due to cantilever deflection ($\delta \propto L^3 / D^4$). Requires specialized EDM (Electrical Discharge Machining).

### 1.3 Wall Thickness & Floor Thickness
| Material | Minimum Unsupported Wall | Recommended Rigid Wall | Minimum Floor |
| :--- | :---: | :---: | :---: |
| **Aluminum (6061-T6 / 7075-T6)** | $0.8\text{ mm}$ | $\ge 1.5\text{ mm}$ | $1.0\text{ mm}$ |
| **Stainless Steel (304 / 316)** | $0.6\text{ mm}$ | $\ge 1.2\text{ mm}$ | $0.8\text{ mm}$ |
| **Plastics (Delrin / PEEK)** | $1.5\text{ mm}$ | $\ge 2.5\text{ mm}$ | $1.5\text{ mm}$ |

---

## 2. Additive Manufacturing (3D Printing: FDM / SLA / SLS)

Additive manufacturing eliminates tool clearance constraints but introduces anisotropic layer bonding and thermal shrinkage.

### 2.1 Mechanical Anisotropy & Print Orientation
*   **The Layer Adhesion Trap:** In Fused Deposition Modeling (FDM), tensile strength along the build plane (XY) is $100\%$, but interlayer tensile strength along the Z-axis is only **$40\text{–}60\%$** due to thermal fusion boundaries.
*   **Design Rule:** Orient load vectors and bending moments so that tensile stresses act **parallel to the print bed (XY)**, never in peel/tension across layer lines (Z).

### 2.2 Fits & Operating Clearances for 3D Printing

```
 3D Print Diametral Fit Gap (Total Clearance ΔD = Hole Ø - Shaft Ø)
 ─────────────────────────────────────────────────────────────────
 FDM (0.4mm nozzle):    0.15mm (Light Press)  │ 0.35–0.45mm (Smooth Running)
 SLA / Resin:           0.08mm (Press)        │ 0.20mm (Sliding)
 SLS (Nylon PA12):      0.12mm (Press)        │ 0.25–0.30mm (Sliding)
```

### 2.3 Fastener Integration: Heat-Set Threaded Inserts
Never tap female threads directly into 3D printed thermoplastics for structural connections. Use brass **tapered heat-set threaded inserts** (Ruthex / CNC Kitchen standard).

```
          Heat-Set Insert Installation Boss Geometry
          
                 Lead-in Chamfer (60°)
                     ▼
          │◄──── Ø Hole (A) ────►│
          ┌───┐               ┌───┐ ───
          │   │               │   │  ▲
          │   │               │   │  │  Insert Length (L)
          │   │               │   │  │  + 1.0mm Clearance
          │   │               │   │  ▼
          └───┴───────────────┴───┴ ───
          │◄────── Boss Ø (B) ───►│
```

**Standard Dimensions Table for Metric Inserts (Plastics: PLA, PETG, ABS, PA):**

| Thread Size | Outer Insert Length ($L$) | Hole Pilot $\varnothing$ ($A$) | Minimum Boss Wall $\varnothing$ ($B$) | Minimum Hole Depth |
| :---: | :---: | :---: | :---: | :---: |
| **M2** | $3.0\text{ mm}$ | $3.2\text{ mm}$ | $\ge 5.0\text{ mm}$ | $4.0\text{ mm}$ |
| **M2.5** | $4.0\text{ mm}$ | $3.6\text{ mm}$ | $\ge 6.0\text{ mm}$ | $5.2\text{ mm}$ |
| **M3 (Standard)** | $5.7\text{ mm}$ | $4.0\text{ mm}$ | $\ge 7.0\text{ mm}$ | $7.0\text{ mm}$ |
| **M4** | $8.1\text{ mm}$ | $5.6\text{ mm}$ | $\ge 9.0\text{ mm}$ | $9.5\text{ mm}$ |
| **M5** | $9.5\text{ mm}$ | $6.4\text{ mm}$ | $\ge 11.0\text{ mm}$ | $11.0\text{ mm}$ |

---

## 3. Sheet Metal Design Standards

Sheet metal fabrication forms 3D parts from flat sheet stock via punching, laser cutting, and press-brake bending.

### 3.1 Minimum Bend Radius & The Neutral Axis
Bending metal compresses the inner surface and tensions the outer surface. Bending sharper than the minimum radius causes surface tearing along grain boundaries.
*   **Rule of Thumb:** Minimum internal bend radius $R_{min} \ge 1.0 \times t$ for 5052-H32 aluminum and mild steel ($t = \text{sheet thickness}$). For 6061-T6 aluminum, use $R_{min} \ge 2.0\text{–}2.5 \times t$.

### 3.2 K-Factor & Flat Pattern Unfolding
The neutral axis shifts inward during bending. The **K-factor** is the ratio of neutral axis distance ($t_{neutral}$) to sheet thickness ($t$):
$$K = \frac{t_{neutral}}{t} \quad (0 < K < 0.5)$$
*   Standard air-bending of mild steel / 5052 aluminum: **$K \approx 0.38\text{–}0.42$**.
*   **Bend Allowance ($BA$):**
    $$BA = \pi \left(R + K \cdot t\right) \frac{A}{180^\circ}$$
    Where $R$ is internal bend radius, $A$ is bend angle in degrees.

### 3.3 Relief Notches & Hole Placement
1.  **Bend Relief Notches:** When a bend is adjacent to an unbent flange, a relief notch is mandatory to prevent tearing at the corner.
    *   Relief Width $W \ge t$.
    *   Relief Depth $D \ge R + t$.
2.  **Distance of Holes from Bends:**
    *   To prevent elliptical hole distortion from plastic deformation, distance from edge of hole to bend tangent must satisfy:
        $$Dist \ge 2.5 \times t + R$$

---

## 4. Standard Precision Fasteners & Locating Pins

Robot structures must withstand dynamic shock vibrations without loosening.

### 4.1 Metric Fasteners: ISO 4762 Socket Head Cap Screws (SHCS)
Standardizing on ISO 4762 metric socket heads simplifies toolkits and ensures high clamping preloads (Grade 8.8 or 10.9 steel).

| Fastener | Clearance Hole (Normal) | Counterbore $\varnothing$ ($D_{cb}$) | Counterbore Depth ($H_{cb}$) | Tightening Torque (8.8 / 10.9) |
| :---: | :---: | :---: | :---: | :---: |
| **M2** | $\varnothing 2.4\text{ mm}$ | $\varnothing 4.4\text{ mm}$ | $2.4\text{ mm}$ | $0.4\text{ Nm} / 0.6\text{ Nm}$ |
| **M2.5** | $\varnothing 2.9\text{ mm}$ | $\varnothing 5.5\text{ mm}$ | $2.9\text{ mm}$ | $0.8\text{ Nm} / 1.2\text{ Nm}$ |
| **M3** | $\varnothing 3.4\text{ mm}$ | $\varnothing 6.5\text{ mm}$ | $3.4\text{ mm}$ | $1.4\text{ Nm} / 2.0\text{ Nm}$ |
| **M4** | $\varnothing 4.5\text{ mm}$ | $\varnothing 8.0\text{ mm}$ | $4.4\text{ mm}$ | $3.1\text{ Nm} / 4.4\text{ Nm}$ |
| **M5** | $\varnothing 5.5\text{ mm}$ | $\varnothing 10.0\text{ mm}$ | $5.4\text{ mm}$ | $6.2\text{ Nm} / 8.8\text{ Nm}$ |
| **M6** | $\varnothing 6.6\text{ mm}$ | $\varnothing 11.5\text{ mm}$ | $6.4\text{ mm}$ | $10.5\text{ Nm} / 15.0\text{ Nm}$ |

### 4.2 Minimum Thread Engagement Length ($L_e$)
To ensure the screw breaks before threads strip:
*   **Steel in Steel:** $L_e \ge 1.0 \times D_{screw}$ (e.g., $6\text{ mm}$ engagement for M6).
*   **Steel in 6061-T6 Aluminum:** $L_e \ge 1.5\text{–}2.0 \times D_{screw}$ (e.g., $9\text{–}12\text{ mm}$ engagement for M6).
*   **Steel in Cast Iron:** $L_e \ge 1.25 \times D_{screw}$.
*   **Steel in Thermoplastics (direct tap):** $L_e \ge 2.5\text{–}3.0 \times D_{screw}$ (avoid if possible; prefer heat-set inserts).

### 4.3 Locating Dowel Pins (The Diamond Pin Trick)
*   **Fasteners clamp; dowel pins locate.** Never rely on bolts/screws for precision radial alignment because bolt clearance holes have $0.2\text{–}0.5\text{ mm}$ play.
*   **The Two-Pin Rule:** To fully constrain a planar joint without overconstraining center-to-center hole distance tolerances:
    *   Pin 1: **Cylindrical Dowel Pin** (constrains $T_x, T_y$).
    *   Pin 2: **Diamond Dowel Pin** (relieved sides; constrains only rotation $R_z$ around Pin 1, allowing axial thermal expansion and hole distance tolerance without binding).

---

## 5. References & Standards

1.  **Boothroyd, G., Dewhurst, P., & Knight, W. A. (2010).** *Product Design for Manufacture and Assembly* (3rd ed.). CRC Press / Taylor & Francis. (The seminal methodology for part count reduction, handling efficiency, and assembly time minimization).
2.  **Bralla, J. G. (1998).** *Design for Manufacturability Handbook* (2nd ed.). McGraw-Hill Education. (Tool accessibility, milling corner radii, draft angles, and sheet metal bend relief rules).
3.  **ISO 4762:2004.** *Hexagon socket head cap screws.* International Organization for Standardization.
4.  **ISO 273:1979.** *Fasteners — Clearance holes for bolts and screws.* International Organization for Standardization.
5.  **DIN 8752 / ISO 8734:1997.** *Parallel pins, of hardened steel and martensitic stainless steel (Dowel pins).* International Organization for Standardization.
6.  **Slocum, A. H. (1992).** *Precision Machine Design.* Prentice Hall. (Diamond pin kinematic alignment principles and overconstraint prevention).


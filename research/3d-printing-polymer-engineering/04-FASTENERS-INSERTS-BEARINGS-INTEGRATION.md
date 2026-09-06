# Fastener Integration, Threaded Inserts, Bearings & Snap-Fits

**Date:** 2026-09-05  
**Scope:** Heat-set threaded inserts (boss sizing, pull-out force, strip torque), captive nut pockets, bearing retention in viscoelastic polymers, and cantilever snap-fit design (Bayer formula).

---

## 1. Mechanical Fastening in Thermoplastics

Directly tapping standard machine threads ($60^\circ$ metric) into 3D printed plastics fails because cyclic clamping loads and shear stresses strip the soft polymer threads, while viscoelastic stress relaxation destroys bolt preload within days.

```
       Direct Tapped Plastic Thread              Heat-Set Brass Insert (Herringbone)
             (FAILS RAPIDLY)                           (HIGH STRENGTH & REUSABLE)
             ┌──────────────┐                              ┌──────────────┐
             │\  Stripped  /│                              │ █▓▒ Opposing ▒▓█│
             │ \  Plastic / │                              │ █▓▒ Knurls   ▒▓█│ Plastic flows
             │  \ Flakes /  │                              │ █▓▒ & Grooves▒▓█│ into undercuts
             └──────────────┘                              └──────────────┘
```

### 1.1 Fastener Comparison Matrix

| Fastening Method | Tensile Pull-Out Strength | Strip-Out Torque | Assembly Cycles | Cost / Complexity | Best Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Direct Plastic Tapping** | Very Low ($< 300\text{ N}$) | Low ($< 0.5\text{ Nm}$) | $1\text{–}2$ cycles | Zero hardware | Disposable prototypes only |
| **Plastite / PT Screws** | Moderate ($600\text{–}900\text{ N}$) | Medium ($1.2\text{–}1.5\text{ Nm}$) | $3\text{–}5$ cycles | Low | Consumer electronics enclosures |
| **Captive Hex Nut Pocket** | High ($1200\text{–}1800\text{ N}$) | High (Nut breaks bolt) | Unlimited | Moderate (manual slot insertion) | Heavy structural frames, printer chassis |
| **Heat-Set Brass Insert** | **Very High ($1000\text{–}1500\text{ N}$)** | **High ($2.5\text{–}3.5\text{ Nm}$)** | **Unlimited** | Low (soldering iron press) | **Production robotics, motor mounts, joints** |

---

## 2. Brass Heat-Set Threaded Inserts: Sizing & Performance

Tapered brass inserts with opposed diagonal knurling (Ruthex / CNC Kitchen standard) use thermal conduction to melt the surrounding thermoplastic during insertion. Upon cooling, the plastic solidifies inside the undercuts, creating a structural mechanical interlock.

```
                 Heat-Set Insert Boss Design Architecture
                 
                       60° Lead-In Chamfer
                               ▼
                 │◄────── Pilot Hole Ø (A) ──────►│
                 ┌────┐                       ┌────┐  ───
                 │    │                       │    │   ▲
                 │    │                       │    │   │ Insert Length (L)
                 │    │                       │    │   ▼
                 │    ├───────────────────────┤    │  ───
                 │    │ Molten Plastic Relief │    │   ▲ 1.0mm Minimum
                 │    │ Reservoir             │    │   ▼
                 └────┴───────────────────────┴────┘  ───
                 │◄─────── Outer Boss Ø (B) ──────►│
```

### 2.1 Boss Sizing Rules & Dimensions Table
1.  **Outer Boss Diameter ($B$):** Must satisfy $B \ge 2.0 \times \text{Insert Outer Diameter}$ (or wall thickness $t_{wall} \ge \text{Insert Outer Diameter} / 2$). Thinner bosses burst radially during installation or bolt tightening.
2.  **Depth Reservoir:** The hole depth must exceed the insert length by **at least $1.0\text{–}1.5\text{ mm}$**. Molten plastic pushed ahead of the insert collects in this cavity. Without this reservoir, displaced plastic wells up around the top, ruining planar mating surfaces.

**CNC Kitchen / Ruthex Standard Dimension Reference:**

| Screw Thread | Insert Length ($L$) | Hole Top Pilot $\varnothing$ ($A$) | Hole Depth ($H$) | Minimum Boss $\varnothing$ ($B$) | Typical Pull-Out Force (PLA) | Strip Torque (PLA) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M2** | $3.0\text{ mm}$ | $\varnothing 3.2\text{ mm}$ | $4.2\text{ mm}$ | $\ge 5.2\text{ mm}$ | $650\text{ N}$ | $0.8\text{ Nm}$ |
| **M2.5** | $4.0\text{ mm}$ | $\varnothing 3.6\text{ mm}$ | $5.2\text{ mm}$ | $\ge 6.2\text{ mm}$ | $950\text{ N}$ | $1.4\text{ Nm}$ |
| **M3 (Standard)** | $5.7\text{ mm}$ | $\varnothing 4.0\text{ mm}$ | $7.0\text{ mm}$ | $\ge 7.8\text{ mm}$ | **$1450\text{ N}$ ($145\text{ kg}$)** | **$3.2\text{ Nm}$** |
| **M3 (Short)** | $3.0\text{ mm}$ | $\varnothing 4.0\text{ mm}$ | $4.2\text{ mm}$ | $\ge 7.0\text{ mm}$ | $850\text{ N}$ | $1.8\text{ Nm}$ |
| **M4** | $8.1\text{ mm}$ | $\varnothing 5.6\text{ mm}$ | $9.5\text{ mm}$ | $\ge 10.0\text{ mm}$ | **$2100\text{ N}$** | **$5.8\text{ Nm}$** |
| **M5** | $9.5\text{ mm}$ | $\varnothing 6.4\text{ mm}$ | $11.0\text{ mm}$ | $\ge 11.5\text{ mm}$ | **$2800\text{ N}$** | **$8.5\text{ Nm}$** |

### 2.2 Installation Best Practice: The 90/10 Rule
*   Set soldering iron temperature to **$10\text{–}20^\circ\text{C}$ above the filament print temperature** (e.g. $230^\circ\text{C}$ for PLA, $260^\circ\text{C}$ for PETG, $280^\circ\text{C}$ for ABS/PA).
*   **The 90/10 Rule:** Press the insert $90\%$ of the way into the hole using the iron tip. Remove the iron, and immediately press the final $10\%$ flush using a flat, cold aluminum block. The cold metal cools the brass rapidly, quenching the molten plastic and locking the insert perpendicular to the surface.

---

## 3. Retaining Ball Bearings in Viscoelastic Polymer Housings

### 3.1 The Stress Relaxation Failure Mode
In CNC steel or aluminum housings, an interference press fit ($H7/p6$) maintains permanent radial holding force.
*   **The Thermoplastic Creep Trap:** Polymers under permanent static strain undergo continuous molecular slip (**viscoelastic stress relaxation**). Within weeks, an interference press fit relaxes its radial clamping stress to zero. The bearing outer ring loosens and spins inside the plastic bore under operating torque ("fretting bore destruction").

```
      Failed: Pure Press-Fit                   Succeeded: Axial Clamping Flange
      
         ┌──────────────┐                          ┌───────┬──────┐
         │ Bearing Ring │                          │ Screw │ Flange Plate
         │ Loosens Over │                          └───────┴──────┘
         │ Time & Spins │                              ▼ Clamps Outer Ring
         └──────────────┘                          ┌──────────────┐
                                                   │ Bearing Ring │
                                                   └──────────────┘
                                                   ──────────────── Solid Shoulder
```

### 3.2 Robust Mechanical Retention Solutions
1.  **Axial Clamp Flange (Recommended):**
    *   Seat the bearing against a solid internal printed shoulder ($1.0\text{–}1.5\text{ mm}$ step).
    *   Clamp the outer ring axially from the top using a 3-bolt retaining plate or washer screwed into heat-set inserts.
2.  **Split-Clamp Clamp Block:**
    *   Slit the bearing housing along one side; tighten a tangential cross-bolt to clamp the bore around the bearing outer ring.

---

## 4. Cantilever Snap-Fit Design (Bayer MaterialScience Formulation)

Cantilever snap-fits provide instantaneous, toolless, zero-fastener assembly for modular robotic panels and sensor clips.

```
                  Cantilever Snap-Fit Geometry
                  
                  ◄────────── Length L ──────────►
                  ┌───────────────────────────────┐
                  │                                \   Undercut (Y)
                  │                                 \  ▼
                  └───────────────────────────────┐  \───┐
                  │                               │  /   │  ───
                  │ Root Thickness (h)            │ /    │   ▲ Push-Off Angle α
                  └───┬───────────────────────────┴/─────┘  ───
                      ▼
                  Fillet Radius R ≥ 0.5h
```

### 4.1 Maximum Surface Strain Formula
For a rectangular cantilever beam of uniform thickness $h$, length $L$, and tip deflection $Y$:
$$\epsilon_{max} = \frac{1.5 \cdot h \cdot Y}{L^2} \cdot Q \le \epsilon_{allowable}$$
Where:
*   $\epsilon_{max}$: Maximum outer fiber strain at the root.
*   $Q$: Deflection magnification factor ($Q \approx 1.2\text{–}1.4$ for compliant plastic mounting walls).
*   **Fillet Requirement:** The root must have a generous radius $R \ge 0.5 \cdot h$ to eliminate stress notch concentrations ($K_t \to 1.2$).

### 4.2 Allowable Strain Limits ($\epsilon_{allowable}$) by Polymer

| Material | Maximum Strain (Single Assembly) | Maximum Strain (Repeated Assembly) | Toughness Behavior |
| :--- | :---: | :---: | :--- |
| **Standard PLA** | $1.0\text{–}1.2\%$ | $\le 0.5\%$ | Very brittle; snaps easily |
| **PETG** | $2.5\text{–}3.0\%$ | $1.2\text{–}1.5\%$ | Ductile; good snap performance |
| **ABS / ASA** | $3.0\text{–}3.5\%$ | $1.5\text{–}1.8\%$ | Excellent; tough and forgiving |
| **Nylon (PA12 / PA6)** | **$5.0\text{–}8.0\%$** | **$3.0\text{–}4.0\%$** | **The Gold Standard for Snap-Fits** |
| **PC (Polycarbonate)** | $3.5\text{–}4.0\%$ | $1.5\text{–}2.0\%$ | Extreme impact resistance |

---

## 5. References & Standards

1.  **Bayer MaterialScience (Covestro). (2000).** *Snap-Fit Joints for Plastics: A Design Guide.* Leverkusen, Germany. (Definitive engineering standard for cantilever beam strain equations, root stress concentration factors, and allowable elongation limits).
2.  **DIN 16903:1974-07.** *Open and closed threaded inserts for plastics mouldings.* Deutsches Institut für Normung. (Dimensional specifications, pull-out knurl profiles, and recommended boss wall ratios).
3.  **ISO 4762:2004.** *Hexagon socket head cap screws.* International Organization for Standardization. (Standard clearance hole and counterbore depths used for clamping polymer structures).
4.  **ISO 273:1979.** *Fasteners — Clearance holes for bolts and screws.* International Organization for Standardization.
5.  **Sanatgar, R. H., Campagne, C., & Nierstrasz, V. (2017).** *Investigation of the adhesion properties of direct 3D printing of polymers and nanocomposites on textiles and inserts.* Journal of Applied Polymer Science, 134(37), 45298. [DOI: 10.1002/app.45298]
6.  **CNC Kitchen (Schorr, S.). (2019–2023).** *Empirical Test Series on Heat-Set Inserts, Pull-Out Force vs Installation Temperature, and Perimeter Optimization in FDM Polymers.* Published open benchmark datasets (cnckitchen.com).


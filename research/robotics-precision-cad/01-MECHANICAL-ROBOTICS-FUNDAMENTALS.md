# Robotics & Mechanical Design Fundamentals

**Date:** 2026-09-05  
**Scope:** Kinematic chains, joint mechanisms, actuator architectures, motor sizing dynamics, bearing configurations, and structural load paths for precision robotics.

---

## 1. Kinematic Architectures & Degrees of Freedom (DOF)

### 1.1 Mechanism Topology
*   **Serial Manipulators:** Open kinematic chains (e.g., standard 6-DOF industrial arms). High workspace volume-to-footprint ratio; errors accumulate additively down the chain; lower payload-to-weight ratio.
*   **Parallel Manipulators:** Closed kinematic chains (e.g., Delta robots, Stewart platforms). Actuators mounted on base; high stiffness, payload, and speed; limited workspace and complex singularities.
*   **Hybrid / Tree Mechanisms:** Humanoid robots and multi-legged platforms combining serial limbs with closed-loop linkages (e.g., 4-bar ankle linkages or parallel push-rod wrist mechanisms).

### 1.2 Mobility Analysis (Chebychev-Grübler-Kutzbach Formula)
For a spatial mechanism in 3D ($d = 6$):
$$M = 6(n - j - 1) + \sum_{i=1}^j f_i$$
Where:
*   $M$: Mobility (Degrees of Freedom of the mechanism).
*   $n$: Total number of links (including ground/base link).
*   $j$: Number of joints.
*   $f_i$: Number of relative degrees of freedom allowed by joint $i$.

**Lower Pair Joint Classification:**
| Joint Type | Relative DOFs ($f_i$) | Constrained DOFs ($6 - f_i$) | Permitted Motion |
| :--- | :---: | :---: | :--- |
| **Revolute ($R$)** | 1 | 5 | 1 Rotation around joint Z-axis |
| **Prismatic ($P$)** | 1 | 5 | 1 Translation along joint Z-axis |
| **Helical ($H$)** | 1 | 5 | Coupled translation and rotation (lead screw) |
| **Cylindrical ($C$)** | 2 | 4 | 1 Translation + 1 independent rotation |
| **Universal ($U$)** | 2 | 4 | 2 Orthogonal rotations (Hooke's joint) |
| **Spherical ($S$)** | 3 | 3 | 3 Rotations (ball-and-socket) |
| **Planar ($E$)** | 3 | 3 | 2 Translations in plane + 1 rotation normal |

### 1.3 Kinematic Parameterizations: DH vs. Screw Theory
1.  **Denavit-Hartenberg (DH / Modified DH):**
    *   Parameters: Joint angle $\theta_i$, link offset $d_i$, link length $a_i$, link twist $\alpha_i$.
    *   *Failure Mode:* Singularity when consecutive joint axes are parallel (small misalignment causes coordinate frames to diverge to infinity).
2.  **Product of Exponentials (PoE) / Modern Screw Theory:**
    *   Frame-independent formulation using Lie groups $SE(3)$ and Lie algebras $se(3)$.
    *   Each joint is represented by a spatial screw axis twist $\mathcal{S} = [\omega, v]^T \in \mathbb{R}^6$:
        $$T(\theta) = e^{[\mathcal{S}_1]\theta_1} e^{[\mathcal{S}_2]\theta_2} \dots e^{[\mathcal{S}_n]\theta_n} M$$
    *   *Advantage:* Mathematically smooth through singularities; no discontinuous coordinate frame jumps; cleanly maps to robot dynamics (spatial inertia tensors).

---

## 2. Actuator Selection & Transmission Architectures

In robotics, actuator selection dictates system bandwidth, control strategy (position vs. force/torque impedance), and survivability.

### 2.1 Comparison Matrix

| Actuator Type | Ratio ($N$) | Backdrivability | Backlash | Shock Tolerance | Torque Density | Primary Application |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Direct Drive (DD)** | 1:1 | Perfect ($100\%$) | 0 arcmin | Exceptional | Low ($1\text{–}3\text{ Nm/kg}$) | Direct-drive turntables, haptic interfaces |
| **Quasi-Direct Drive (QDD)** | 4:1 – 10:1 | High ($>90\%$) | Low ($<1\text{–}3\text{ arcmin}$) | High | Medium ($10\text{–}25\text{ Nm/kg}$) | Quadruped / humanoid legs, dynamic arms |
| **Planetary (Epicyclic)** | 10:1 – 50:1 | Moderate | 3 – 10 arcmin | Good | High ($20\text{–}40\text{ Nm/kg}$) | Mobile robot wheel hubs, utility arms |
| **Harmonic Drive (Strain Wave)** | 50:1 – 160:1 | Very Low | Zero ($<0.1\text{ arcmin}$) | Moderate / Fragile | Extreme ($30\text{–}60\text{ Nm/kg}$) | Cobot joints, precision wrists, pan-tilts |
| **Cycloidal / RV Reducer** | 30:1 – 300:1 | Negligible | Low ($<1\text{ arcmin}$) | Extreme ($500\%\text{ shock}$) | Very High ($35\text{–}70\text{ Nm/kg}$) | Industrial robot waist/shoulder, high-payload |

### 2.2 Detailed Operating Principles

#### 1. Quasi-Direct Drive (QDD)
*   **Concept:** Large-diameter, flat "pancake" BLDC motor (high pole count, e.g., 28 poles) paired with a low single-stage planetary or timing-belt reduction ($N \le 10$).
*   **Mechanical Transparency:** The reflected motor inertia is proportional to $N^2$. Because $N$ is small, motor inertia felt at the output is minimal:
    $$J_{reflected} = N^2 \cdot J_{motor}$$
*   **Force Control:** External collision forces backdrive the motor directly into its magnetic circuit. Motor phase currents reflect external torques ($T_{ext} \approx \tau / N$), enabling high-frequency virtual spring-damper impedance control without expensive 6-axis F/T sensors.

#### 2. Harmonic Drive (Strain Wave Gearing)
*   **Concept:** Three concentric components: Wave Generator (elliptical ball bearing cam), Flexspline (thin, flexible cup with external teeth), and Circular Spline (rigid outer ring with internal teeth, typically 2 more teeth than Flexspline).
*   **Reduction Formula:**
    $$R = \frac{Z_{flex}}{Z_{flex} - Z_{circ}} = -\frac{Z_{flex}}{2}$$
*   **Precision vs. Fragility:** True zero backlash and kinematic positioning accuracy. However, flexspline fatigue life is bounded, and external impact loads exceeding $200\text{–}300\%$ rated torque cause flexspline tooth skipping ("ratcheting") or catastrophic fatigue fracture.

#### 3. Cycloidal / RV Reducers
*   **Concept:** Eccentric shaft drives cycloidal discs that orbit inside a stationary housing lined with precision cylindrical pins.
*   **Load Distribution:** Simultaneously engages up to $30\text{–}50\%$ of the teeth/pins under load, compared to $1\text{–}2$ teeth in spur gears.
*   **Shock Resistance:** Can absorb shock loads of $500\%$ of rated torque without mechanical failure. Ideal for base joints subject to high bending moments and acceleration forces.

---

## 3. Motor Sizing & Dynamic Load Matching

### 3.1 Speed-Torque Characteristics
A permanent-magnet brushless motor (BLDC/PMSM) operates within two envelopes:
1.  **Continuous Operating Region (S1):** Bounded by motor thermal dissipation ($T_{cont}$). Safe for indefinite continuous operation.
2.  **Intermittent / Peak Region (S2/S3):** Bounded by inverter maximum current, magnetic core saturation, and thermal time constant ($T_{peak} \approx 2\text{–}3 \times T_{cont}$). Allowed for short acceleration bursts ($<1\text{–}5\text{ s}$).

### 3.2 RMS Torque Calculation
For a robot operating a repeating motion profile of $k$ segments:
$$T_{RMS} = \sqrt{\frac{\sum_{i=1}^k T_i^2 \cdot t_i}{\sum_{i=1}^k t_i}} \le T_{continuous}$$
If $T_{RMS} > T_{cont}$, the motor windings will overheat and degrade insulation (Class F: $155^\circ\text{C}$, Class H: $180^\circ\text{C}$).

### 3.3 Inertia Ratio Matching
Total effective inertia seen at the motor rotor:
$$J_{total} = J_{rotor} + J_{gearbox} + \frac{J_{load}}{N^2}$$
**Inertia Ratio ($I_R$):**
$$I_R = \frac{J_{load}}{N^2 \cdot J_{rotor}}$$
*   **$I_R \le 1$:** Ideal for ultra-high-bandwidth positioning and dynamic agility (quadrupeds, pick-and-place deltas).
*   **$1 < I_R \le 5$:** Standard engineering sweet spot for robotics manipulators (balanced energy consumption and control stability).
*   **$I_R > 10$:** High sensitivity to external disturbances; requires aggressive derivative gain and state observers; risk of servo hunting and limit-cycle oscillation.

---

## 4. Bearing Selection & Joint Load Paths

Robot joints experience multi-axis loading: radial shear forces, axial thrust, and overturning tilting moments ($M_x, M_y$).

```
       Overturning Moment (M)
             ↺      ↻
       ┌────────────────┐
  ────►│  Joint Shaft   │◄──── Axial Force (Fa)
       └────────────────┘
             ▲      ▼
        Radial Force (Fr)
```

### 4.1 Bearing Configuration Architecture

1.  **Crossed Roller Bearings (CRB / RU / RA / RB series):**
    *   *Geometry:* Cylindrical rollers arranged orthogonally ($90^\circ$ V-groove raceways) in a 1:1 alternating pattern.
    *   *Performance:* A single crossed roller bearing simultaneously absorbs **radial, axial, and moment loads**.
    *   *Stiffness:* Contact line is a line contact (vs. point contact in ball bearings), delivering $3\text{–}4\times$ higher rigidity.
    *   *Use case:* Output stage of harmonic drives, robot arm wrists, rotary tables.

2.  **Angular Contact Ball Bearings (Duplex Pairs):**
    *   Used when high rotational speed exceeds crossed roller limits.
    *   **Back-to-Back (DB / O-arrangement):** Diverging contact lines. Maximizes effective bearing spread distance ($L_{eff}$), providing **maximum overturning moment rigidity**. Preferred for cantilevered robot shafts.
    *   **Face-to-Face (DF / X-arrangement):** Converging contact lines. Accommodates slight angular misalignment; lower moment rigidity.
    *   **Tandem (DT):** Parallel contact lines. Doubles axial capacity in one direction only.

3.  **Thin-Section Bearings (Kaydon Reali-Slim series):**
    *   Constant cross-section (e.g., $1/4"\times 1/4"$ or $8\text{ mm} \times 8\text{ mm}$) regardless of bore diameter ($25\text{ mm}$ to $1000\text{ mm}$).
    *   Essential for hollow-shaft joint designs allowing cable routing, slip rings, and optical encoder pass-throughs.

### 4.2 Shaft and Housing Preload Design
*   **Fixed-Floating Arrangement:** One end axial fixed (locating bearing absorbs bidirectional axial forces), the other end free to float axially (non-locating bearing, e.g., cylindrical roller or clearance fit deep groove ball) to accommodate thermal shaft expansion without binding.
*   **Rigid Preload vs. Spring Preload:**
    *   *Rigid (Ground spacer rings / locknuts):* Highest stiffness; sensitive to thermal gradients.
    *   *Spring / Wave washer preload:* Constant preload force regardless of thermal dimensional drift; ideal for high-speed small BLDC motor shafts.

---

## 5. Structural Load Paths & Stiffness Sizing

### 5.1 The Principle of Direct Load Paths
Force must flow from the end-effector to the base through the shortest, stiffest geometric path without inducing bending moments on thin plates.
*   **Torsion & Bending Rigidity:** Thin-walled closed tubular/box sections have orders-of-magnitude higher polar moment of inertia ($J_z$) and second moment of area ($I_x, I_y$) than open C-channels or flat plates of identical mass:
    $$I_{tube} = \frac{\pi}{64}(D_o^4 - D_i^4) \gg I_{plate}$$
*   **Ribbing & Gusseting:** Position triangular gussets along the principal stress vectors connecting the bearing housing to the link beam. Never terminate a rib in the center of an unsupported flat plate (creates stress concentration and plate oil-canning).

---

## 6. References & Standards

1.  **Lynch, K. M., & Park, F. C. (2017).** *Modern Robotics: Mechanics, Planning, and Control.* Cambridge University Press. (Authoritative treatment of screw theory, product of exponentials, joint coordinates, and spatial rigid body dynamics).
2.  **Slocum, A. H. (1992).** *Precision Machine Design.* Society of Manufacturing Engineers / Prentice Hall, Englewood Cliffs, NJ. (Structural loop stiffness, Saint-Venant principles, kinematic constraint, and bearing configurations).
3.  **Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G. (2009).** *Robotics: Modelling, Planning and Control.* Springer Science & Business Media. (Kinematics, dynamics, Newton-Euler recursions, and link inertia tensors).
4.  **ISO 9283:1998.** *Manipulating industrial robots — Performance criteria and related test methods.* International Organization for Standardization. (Pose repeatability, path accuracy, and compliance testing).
5.  **Harris, T. A., & Kotzalas, M. N. (2006).** *Essential Concepts of Bearing Technology* (5th ed.). CRC Press / Taylor & Francis. (Crossed roller and angular contact bearing preload, contact stresses, and stiffness curves).


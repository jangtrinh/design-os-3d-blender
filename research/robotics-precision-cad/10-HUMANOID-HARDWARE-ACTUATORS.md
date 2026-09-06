# Humanoid Robot Hardware Architectures & Thermal Management

**Date:** 2026-09-05  
**Scope:** Modern humanoid robotic hardware architectures (Tesla Optimus, Unitree H1/G1, Figure 01/02), Inverted Planetary Roller Screws (IPRS) vs. rotary actuators, dual-encoder sensing, and thermal dissipation modeling.

---

## 1. System Anatomy & Mass Distribution in Bipedal Humanoids

In legged and humanoid robotics, the single most critical architectural metric is **distal mass minimization**.

```
                           Mass Concentration Strategy
                 ┌──────────────────────────────────────┐
                 │  TORSO / PELVIS (Heavy Mass Center)  │
                 │  - Battery Pack (48V / 100V, 2-3 kWh)│
                 │  - Compute / Inverters / IMUs        │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │  PROXIMAL JOINTS (Hips / Shoulders)  │
                 │  - High-torque rotary actuators      │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │  DISTAL LIMBS (Lower Legs / Forearms)│
                 │  - Inverted Planetary Roller Screws  │
                 │  - Lightweight carbon-fiber tubes    │
                 │  - Remote push-rods / cable linkages │
                 └──────────────────────────────────────┘
```

### 1.1 The Distal Inertia Penalty
The effective swing torque required to accelerate a leg during the swing phase is proportional to the moment of inertia about the hip:
$$I_{hip} = \sum m_i \cdot r_i^2$$
*   Adding $1.0\text{ kg}$ to the pelvis requires minimal additional swing torque.
*   Adding $1.0\text{ kg}$ to the ankle ($r \approx 0.8\text{ m}$) increases swing inertia by:
    $$\Delta I = 1.0\text{ kg} \times (0.8\text{ m})^2 = \mathbf{0.64\text{ kg}\cdot\text{m}^2}$$
*   *Design Imperative:* Actuators for knees and ankles are placed as high up on the thigh/shin as possible, driving the joint through **four-bar linkages, push-rods, or planetary roller screws**.

---

## 2. Linear Actuation: Inverted Planetary Roller Screws (IPRS)

Modern humanoids (e.g. Tesla Optimus, Figure 02) deploy linear electro-mechanical actuators for high-load joints (knee flexion/extension, ankle pitch/roll).

```
          Inverted Planetary Roller Screw (IPRS) Mechanism
          
                   Threaded Planetary Rollers (Engaged)
                        ┌─┬─┬─┬─┬─┬─┐
       Outer Nut        │ │ │ │ │ │ │  Linear Output Rod
    ┌──────────────┐ ───┴─┴─┴─┴─┴─┴─┴─── ◄──────────────►
    │ Rotor Sleeve │    Central Threaded
    └──────────────┘ ───┬─┬─┬─┬─┬─┬─┬───
                        │ │ │ │ │ │ │
                        └─┴─┴─┴─┴─┴─┴
```

### 2.1 Why Planetary Roller Screws Beat Ball Screws
*   **Contact Mechanics:** A ball screw transmits force through **point contacts** across rolling spheres. A planetary roller screw uses multiple threaded cylindrical rollers that engage along **continuous helical line contacts**.
*   **Load Rating:** A roller screw delivers **$3\text{–}5\times$ higher dynamic load capacity ($C_{dyn}$)** and up to **$15\times$ higher static load capacity ($C_0$)** than a ball screw of identical envelope.
*   **Shock Resistance:** Tolerates violent impact spikes ($> 15\text{–}25\text{ kN}$) during dynamic heel strike without brinelling (denting) the raceways.
*   **Compact Inversion (IPRS):** The nut is elongated and integrated directly into the rotor of a frameless BLDC motor; the shaft translates linearly through the hollow core, eliminating intermediate gear couplings.

---

## 3. Rotary Joint Architecture & Dual-Encoder Sensing

Rotary actuators in humanoid shoulders, elbows, and wrists integrate four core elements into a single sealed "puck":

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 MODERN INTEGRATED ROTARY ACTUATOR                      │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 1. Frameless BLDC Motor (Stator pressed into outer aluminum housing)   │
  │ 2. Primary High-Res Encoder (Directly on rotor for FOC commutation)   │
  │ 3. Zero-Backlash Reducer (Harmonic Drive or Cycloidal Gearset)        │
  │ 4. Secondary Output Absolute Encoder (Directly on link output flange)  │
  │ 5. Crossed-Roller Bearing (Carries all combined joint moments)        │
  │ 6. Central Hollow Bore (Routes internal power buses and CAN-FD/EtherCAT)│
  └────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Dual-Encoder Necessity
A single encoder on the motor rotor cannot measure:
1.  Torsional deflection of the gear teeth under load.
2.  Gearbox backlash or thermal expansion.
*   *Solution:* **Dual-Encoder Feedback**.
    *   Encoder 1 (Motor shaft, $17\text{–}20\text{ bit}$): Provides high-bandwidth phase angle for Field-Oriented Control (FOC) current commutation.
    *   Encoder 2 (Output shaft, absolute magnetic/optical): Measures the true link position in Cartesian space.
    *   *Virtual Torque Sensing:* The difference between the two scaled angles measures joint deflection $\Delta \theta = \theta_{out} - \frac{\theta_{rotor}}{N}$, yielding joint torque:
        $$\tau_{joint} = K_{torsional} \cdot \Delta \theta$$

---

## 4. Thermal Resistance Modeling & Structural Heat Sinking

In continuous operation, motor winding copper losses ($P_{loss} = I_{rms}^2 R$) generate intense heat inside sealed actuator cavities.

```
       Thermal Resistance Network (Equivalent Electrical Circuit)
       
       P_loss (W)
          │
          ▼
        ( Tj ) Winding Junction Temperature
          │
         [Rth_jc] Internal Conduction
          │
          ▼
        ( Tc ) Motor Stator Case
          │
         [Rth_ch] Thermal Interface Material (Graphite Pad)
          │
          ▼
        ( Th ) Aluminum Structural Link (Heat Sink)
          │
         [Rth_ha] Natural Convection + Radiation to Ambient
          │
          ▼
        ( Ta ) Ambient Air Temperature (25°C)
```

### 4.1 Thermal Equilibrium Formula
The steady-state winding junction temperature ($T_j$) is:
$$T_j = T_a + P_{loss} \cdot \left( R_{th, j-c} + R_{th, c-h} + R_{th, h-a} \right)$$
Where:
*   $T_j \le 155^\circ\text{C}$ (Class F insulation limit) or $\le 180^\circ\text{C}$ (Class H).
*   $R_{th, j-c}$: Junction-to-case thermal resistance ($\approx 0.3\text{–}0.8\ ^\circ\text{C/W}$).
*   $R_{th, c-h}$: Case-to-housing resistance (minimized using high-conductivity thermal paste or graphite pads, $k \ge 5\text{ W/m}\cdot\text{K}$).
*   $R_{th, h-a}$: Housing-to-ambient resistance.

### 4.2 Structural Chassis Heat Dissipation
Humanoids do not have space for heavy cooling fans or liquid radiators in their limbs.
*   **The Chassis Heat Sink Strategy:** Structural aluminum limb bones (6061-T6, thermal conductivity $k \approx 167\text{ W/m}\cdot\text{K}$) act as the primary heat sink.
*   The actuator housing is thermally bonded directly to the structural link tube with high-contact surface area, allowing leg swing airflow to dissipate up to $150\text{–}300\text{ W}$ of continuous thermal losses via forced convection during locomotion.

---

## 5. References & Standards

1.  **Wensing, P. M., Wang, A., Seok, S., Otten, D., Lang, J., & Kim, S. (2017).** *Proprioceptive actuator design in the MIT Cheetah: Impact mitigation and high-bandwidth physical interaction for dynamic robots.* IEEE Transactions on Robotics, 33(3), 509–522. [DOI: 10.1109/TRO.2016.2640183] (Foundational theory of high-torque-density, low-inertia proprioceptive actuators).
2.  **Seok, S., Wang, A., Chuah, M. Y., Otten, D., Lang, J., & Kim, S. (2015).** *Design principles for energy-efficient legged locomotion and implementation on the MIT Cheetah robot.* IEEE/ASME Transactions on Mechatronics, 20(3), 1117–1129. (Motor thermal modeling and planetary gear backdrivability).
3.  **Tesla, Inc. (2022–2024).** *Tesla AI Day & Optimus Humanoid Actuator Architecture Disclosures.* (Integrated rotary actuators, roller screw linear actuators, load cell placement, and chassis thermal dissipation paths).
4.  **Katz, B. (2018).** *A low cost modular actuator for dynamic robots.* Master's thesis, Massachusetts Institute of Technology. (Quasi-direct drive motor parameters, thermal dissipation in robotic chassis, and custom planetary reducer design).
5.  **IEC 60034-1:2022.** *Rotating electrical machines — Part 1: Rating and performance.* International Electrotechnical Commission. (Thermal classes F and H winding insulation temperature standards).


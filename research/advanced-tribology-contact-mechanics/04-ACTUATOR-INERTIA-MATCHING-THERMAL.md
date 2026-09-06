# Actuator Dynamic Optimization: Inertia Matching & Thermal Sizing

Selecting electric actuators for high-acceleration robotics (humanoid legs, quadruped jumps, robotic arm pick-and-place) requires resolving a fundamental physics tradeoff: **gear reduction multiplies motor torque ($T_{out} = G \cdot T_m$), but multiplies reflected rotor inertia by the square of the ratio ($J_{refl} = G^2 \cdot J_m$)**.

---

## 1. Inertia Matching & Optimal Gear Ratio Selection

```
       Motor Rotor (J_m)         Gearbox (Ratio G:1)         Link & Payload Load (J_L)
       ┌───────────────┐               ┌─────┐               ┌────────────────────────┐
       │ Rotor Inertia │ ────────────► │ G:1 │ ────────────► │ Total Reflected Load   │
       └───────────────┘               └─────┘               └────────────────────────┘
       Reflected Rotor Inertia Felt at Link Output = G² · J_m!
```

### 1.1 The Classical Maximum Acceleration Rule
For a system driven by motor torque $T_m$ to accelerate load inertia $J_L$:
$$\alpha_{load} = \frac{T_{load, total}}{J_{total}} = \frac{G \cdot T_m}{J_L + G^2 \cdot J_m}$$
To find the gear ratio $G$ that maximizes load acceleration $\alpha_{load}$, take $\frac{d\alpha_{load}}{dG} = 0$:
$$G^* = \sqrt{\frac{J_L}{J_m}}$$
*When $G = G^*$:* Reflected motor inertia equals load inertia ($G^2 J_m = J_L$). This is the classical **Impedance Match Condition**.

### 1.2 The Minimum Energy Dissipation Ratio (Roos et al., 2006)
In dynamic robots executing continuous trajectory cycles, matching for pure peak acceleration causes excessive motor ohmic heating. Minimizing $I^2 R$ electrical energy over a specified cyclic trajectory yields:
$$G_{opt} = \left( \frac{\int \dot{\theta}_L^2 \, dt}{\int \ddot{\theta}_L^2 \, dt} \cdot \frac{T_{ext}^2}{J_m^2} \right)^{1/4}$$
*Key Shift in Modern Robotics (QDD Philosophy):*
*   Traditional industrial robots (KUKA, FANUC) use high ratios ($G \approx 100\text{–}160:1$), prioritizing position holding with low electrical current.
*   Dynamic humanoids (Boston Dynamics Atlas, MIT Cheetah, Unitree) use **Quasi-Direct Drive (QDD)** with ultra-low ratios (**$G \approx 6:1\text{ to }10:1$**), yielding:
    1.  **Low Reflected Inertia ($G^2 \ll 100$):** High mechanical transparency and shock compliance during ground impacts.
    2.  **High Backdrivability:** High-bandwidth proprioceptive force sensing directly from motor phase current without expensive joint torque sensors.

---

## 2. Motor Power Losses: Copper vs. Iron Losses

Total power dissipated as heat inside a permanent magnet synchronous motor (PMSM / BLDC):

$$P_{loss} = P_{copper} + P_{iron} + P_{mechanical}$$

```
                Copper vs. Iron Loss Characteristics
                
       Power Loss [W]
             ▲
             │       /  Iron Core Losses (P_fe ∝ ω_e² - Dominates at High RPM)
             │      /
             │     /
             │    /
             │   /__________ Copper Ohmic Losses (P_cu ∝ T² - Dominates at Stall)
             └──────────────────────────────► Rotor Electrical Speed (ω_e)
```

### 2.1 Copper (Joule) Ohmic Losses ($P_{cu}$)
Generated in the 3-phase stator copper windings by current flow:
$$P_{cu} = 3 \cdot I_{rms}^2 \cdot R_{phase}(T)$$
Where winding resistance increases linearly with temperature according to the thermal coefficient of copper ($\alpha_{cu} \approx 0.00393\text{ /K}$):
$$R(T) = R_{20^\circ\text{C}} \cdot [1 + 0.00393 \cdot (T_{winding} - 20)]$$
*Thermal Runaway Danger:* At $140^\circ\text{C}$, stator resistance is **$+47\%$ higher** than at room temperature, increasing heat generation by $+47\%$ for identical output torque!

### 2.2 Iron Core Losses ($P_{iron}$ - Steinmetz Equation)
Generated in the laminated silicon steel stator teeth by magnetic flux alternation:
$$P_{iron} = P_{hysteresis} + P_{eddy}$$
$$P_{iron} = k_h \cdot f_{e} \cdot B_{peak}^{1.6} + k_e \cdot f_{e}^2 \cdot B_{peak}^2$$
Where $f_e = \frac{p \cdot n}{120}$ is electrical frequency (Hz), $p$ is pole count, and $B_{peak}$ is flux density.
*Robot Joint Implication:* High pole-count "pancake" outrunner motors ($p = 28\text{ or }42\text{ poles}$) generate severe eddy current heating when spun at high RPM, even under zero output load.

---

## 3. Transient Thermal Differential Equations & Duty Cycles

Motor winding temperature $T_w(t)$ does not change instantaneously; it follows a first-order thermal differential equation:

$$C_{th} \frac{dT_w}{dt} + \frac{T_w(t) - T_{ambient}}{R_{th}} = P_{loss}(t)$$

Where:
*   $C_{th}$: Thermal capacitance of the stator copper mass ($\approx 50\text{–}200\text{ J/K}$).
*   $R_{th}$: Total thermal resistance from stator to motor casing to ambient ($\approx 0.5\text{–}1.5\text{ K/W}$).
*   **Thermal Time Constant ($\tau_{th}$):**
    $$\tau_{th} = R_{th} \cdot C_{th} \approx \mathbf{5\text{ to }15\text{ minutes}}$$

```
                       Transient Thermal Step Response
                       
       Winding Temp (Tw)
              ▲
      T_max ──┼──────────────────────────── Continuous Stall Limit (S1)
              │                     ╭──────
              │                   ╭─╯
              │                 ╭─╯  Thermal Time Constant τ_th
              │               ╭─╯
        Ta  ──┼───────────────╯
              └─────────────────────────────► Time (t)
```

### 3.1 IEC 60034-1 Duty Cycles: Continuous (S1) vs. Intermittent (S3)
*   **Continuous Duty (S1):** Motor runs indefinitely without exceeding insulation class temperature ($T_{max} \le 155^\circ\text{C}$ for Class F):
    $$T_{cont} = K_t \cdot \sqrt{\frac{T_{max} - T_a}{3 R_{phase} R_{th}}}$$
*   **Intermittent Periodic Duty (S3 - Jumping / Impact):**
    If the peak current burst lasts for time $t_{burst} \ll \tau_{th}$ (e.g. a $200\text{ ms}$ robot jump):
    $$I_{peak} = I_{cont} \cdot \sqrt{\frac{1}{1 - \exp(-t_{burst} / \tau_{th})}} \approx \mathbf{3\text{ to }5 \times I_{cont}}$$
    *Rule of Thumb:* High-performance robotic actuators safely deliver **$3\text{–}5\times$ rated continuous torque** for short pulses $< 1.0\text{ second}$ without thermal damage, provided the average RMS torque over the complete gait cycle remains below $T_{cont}$.

---

## 4. Voltage Limits, Back-EMF & Field Weakening

At high rotational velocities $\omega_m$, the spinning permanent magnets induce a counter-voltage (**Back-Electromotive Force - BEMF**):
$$V_{bemf} = K_e \cdot \omega_m$$
Where $K_e$ is the back-EMF constant ($K_e \approx K_t$ in SI units).

```
                     Voltage Limit & Torque Boundary
                     
       Torque (T)
            ▲
      T_max ┼──────────────╮ (Constant Torque / Inverter Current Limited)
            │              │
            │              │ \
            │              │  \  Back-EMF Reaches Bus Voltage V_bus
            │              │   \  (Field Weakening Zone - Torque Drops)
            └──────────────┴────\──────────► Motor Speed (ω_m)
                         ω_base  ω_max
```

*   **Base Speed ($\omega_{base}$):** The maximum speed where full peak torque is achievable:
    $$\omega_{base} \approx \frac{V_{bus} / \sqrt{3}}{K_e}$$
*   Beyond $\omega_{base}$, motor current is voltage-limited.
*   **Field Weakening Control:** The motor inverter injects negative direct-axis current ($i_d < 0$) to partially demagnetize the rotor field, allowing the motor to spin up to $1.5\text{–}2.0 \times \omega_{base}$ at the expense of degraded electrical efficiency and additional heating.

---

## 5. References & Standards

1.  **Roos, F., et al. (2006).** *A methodology for gear ratio selection in dynamic mechatronic systems.* IEEE/ASME Transactions on Mechatronics, 11(3), 282–289. [DOI: 10.1109/TMECH.2006.875567] (Mathematical optimization of gear ratios for minimum energy consumption).
2.  **Wensing, P. M., Wang, A., Seok, S., Otten, D., Lang, J., & Kim, S. (2017).** *Proprioceptive Actuator Design in the MIT Cheetah.* IEEE Transactions on Robotics, 33(3), 509–522. [DOI: 10.1109/TRO.2016.2640183] (Low gear ratio, low-inertia motor design principles for explosive legged robotics).
3.  **Hanselman, D. C. (2006).** *Brushless Permanent Magnet Motor Design* (2nd ed.). The Writers' Collective. (Winding layouts, copper/iron loss formulations, and thermal modeling).
4.  **IEC 60034-1:2022.** *Rotating electrical machines — Part 1: Rating and performance.* International Electrotechnical Commission. (Standard duty cycle classes: S1 continuous, S2 short-time, S3 intermittent periodic).
5.  **Katz, B. (2018).** *A low cost modular actuator for dynamic robots.* Master's thesis, MIT Department of Mechanical Engineering. (Detailed thermal time constant measurements and custom planetary transmission benchmarking).

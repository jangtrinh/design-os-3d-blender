---
name: embedded-realtime-bus-architecture
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Real-time multi-axis bus networks (CAN-FD, RS-485), cascade control loop timing, trajectory generation, and hardware E-Stop safety architectures.
loads_with: [actuators-motors-foc-control, sensor-fusion-state-estimation, industrial-connectors-wire-harness]
tags: [robotics, can-fd, canopen, realtime, control-loops, safety, e-stop, watchdog, trajectory]
id: embedded-realtime-bus-architecture
title: "Real-Time Bus Architecture & Safety Systems in Robotics"
when: [can-fd-bus, bus-termination, control-loop-timing, jerk-limited-trajectory, estop-and-watchdog, multi-axis-networking]
trust_tier: draft
sources_checked: 2026-10-13
---

# Real-Time Bus Architecture & Safety Systems in Robotics

## Purpose
Gives bus-topology, termination, loop-timing and trajectory-profile guidance for multi-axis robots, with verification steps for bus resistance and watchdog behaviour. This is a design-reference note, not certification of any safety function.

## When to Use / When NOT
- ALLOWED: choosing CAN-FD vs RS-485 vs Ethernet for joint networks and wiring/terminating a CAN trunk
- ALLOWED: setting node watchdog, heartbeat and jerk-limited trajectory defaults (project targets tagged UNVERIFIED)
- NOT ALLOWED: claiming a safety function or Performance Level — use `functional-safety-iso13849-robotics` instead
- NOT ALLOWED: motor current-loop and encoder details — use `actuators-motors-foc-control` instead
- NOT ALLOWED: connector selection and cable routing mechanics — use `industrial-connectors-wire-harness` instead

## Core Knowledge Content

### 1. Mental model

In a multi-axis automated machine or articulated robot, distributed microcontrollers must synchronize deterministic actuation commands and telemetry over shared physical buses without jitter or collision.

1. **Deterministic Bus Topology (CAN-FD vs RS-485 vs EtherCAT):**
   * **CAN-FD (Flexible Data-Rate):** Standard for distributed robotics ($64\text{ byte}$ payload; payload data rates of 5 to 8 Mbit/s are possible but the achievable rate depends on bus length and transceivers; arbitration phase limited to 1 Mbit/s; hardware arbitration by message ID priority, non-destructive bitwise arbitration). Earlier draft said "up to 5 Mbps": ISO 11898-2 high-speed CAN is quoted at 5 Mbit/s for CAN-FD, while CAN FD itself allows 5-8 Mbit/s. <!-- ease:source S1 anchor="64-byte payload; 5-8 Mbit/s possible; arbitration limited to 1 Mbit/s" --> <!-- ease:source S2 anchor="ISO 11898-2: 1 Mbit/s CAN, 5 Mbit/s CAN-FD" --> <!-- ease:source UNVERIFIED reason="which transceiver grades reach 5 vs 8 Mbit/s is device-specific; check the transceiver datasheet" -->
   * **Termination Law:** Every high-speed differential bus must be terminated at both physical cable ends with $120\ \Omega \pm 1\%$ split-termination resistors to absorb signal reflections. High-speed CAN uses a linear bus terminated at each end with a 120 ohm resistor and a 120 ohm nominal twisted pair. <!-- ease:source S2 anchor="ISO 11898-2 linear bus terminated at each end with 120 ohm" --> <!-- ease:source UNVERIFIED reason="+-1 % tolerance and split-termination requirement are practice, not in the fetched text" -->
2. **Cascade Real-Time Loop Hierarchy:**
   * <!-- ease:source UNVERIFIED reason="loop-rate tiers (20-50 kHz / 1-5 kHz / 200-1000 Hz) and WDT <= 50 ms are design guidance, not standard values" --> **Tier 1 — Current / Torque Loop ($20\text{--}50\text{ kHz}$):** Hardware-triggered directly by PWM timer center-point interrupt. Directly regulates MOSFET gate switching.
   * **Tier 2 — Velocity Loop ($1\text{--}5\text{ kHz}$):** Estimates derivative of position; calculates target torque $I_q$.
   * **Tier 3 — Position / Trajectory Loop ($200\text{--}1000\text{ Hz}$):** Interpolates trajectory waypoints; runs kinematic transforms.
3. **Fail-Safe Principle (Defense in Depth):**
   * **Hardware Level:** Dedicated normally-closed (NC) Emergency Stop (E-Stop) loop cutting power to motor driver gate-enable pins (Safe Torque Off / STO), independent of software.
   * **Firmware Level:** Hardware watchdog timers ($WDT \le 50\text{ ms}$), bus heartbeat loss cutoffs, stall current monitoring.

### 2. Decision first

| System Architecture | Bus Standard | Transceiver Type | Cable Spec | Maximum Nodes |
| :--- | :--- | :--- | :--- | :--- |
| **Modular Robotic Arm (6-DOF)** | CAN-FD ($1\text{--}5\text{ Mbps}$) | Isolated CAN-FD (TCAN1044 / ISO1042) | Shielded Twisted Pair ($120\ \Omega$ Zo) | $8\text{--}16\text{ joints}$ |
| **Mobile Robot Chassis (AMR)** | Dual CAN 2.0B / CAN-FD | Isolated CAN Transceiver | JST-GH / Molex Micro-Fit | 4 wheel pods + IMU |
| **High-Channel Gripper / Haptics** | RS-485 Half-Duplex | Max485 / THVD1450 | Cat6 UTP or silicone twisted pair | Up to 32 nodes |
| **High-Bandwidth Multi-Cam / LiDAR** | Ethernet 100/1000BASE-T | Magnetic RJ45 / M12 | Cat6A Shielded | Switched star topology |

Decision tree for bus architecture:
1. Are microcontrollers operating on different ground potentials (e.g. separate batteries or high-power motor drivers)? → Use galvanic isolation (optocoupler or capacitive isolator) on the bus transceiver.
2. Can a single wire break safely halt the entire machine? → Wire all E-Stop switches in a series normally-closed (NC) loop.

### 3. Rules

R1. The CAN-FD bus must be wired as a linear daisy-chain trunk, never in a star or tree topology.
    Why: Unterminated stubs $> 300\text{ mm}$ create transmission line signal reflections that corrupt the sampling point during high-speed data-phase transmission. <!-- ease:source UNVERIFIED reason="300 mm stub figure is the classic 1 Mbit/s guideline from memory of ISO 11898; CAN-FD data phase needs shorter stubs, take the limit from the transceiver datasheet. No free primary source frozen" -->
    Violation: Intermittent bit-stuffing errors, node drops into Error Passive or Bus-Off state.

R2. Every node must enforce a communication watchdog timeout ($\le 50\text{ ms}$) that triggers zero-torque shutdown if heartbeat packets stop.
    Why: If the master trajectory controller crashes or disconnects while a joint is moving at speed, the joint will run away until mechanical impact.
    Violation: High-speed mechanical collision with physical environment.

R3. Safe Torque Off (STO) hardware circuits must cut gate-driver power or disable pull-down transistors directly, never relying on software interrupt handlers. (Safety-function claims need the safety module and licensed standards: see `functional-safety-iso13849-robotics`.)
    Why: Software locks (deadlocks, memory corruption, infinite loops) can prevent software-only E-Stop routines from executing.
    Violation: Machine fails to stop when software freezes.

R4. Trajectory generators must enforce S-curve (jerk-limited) profiling ($\dddot{\theta} \le J_{max}$), never pure trapezoidal acceleration steps.
    Why: Step changes in acceleration (infinite jerk) excite the fundamental mechanical resonance of the robot structure and gearbox teeth.
    Violation: Severe structural vibration, gearbox tooth fatigue, and premature cycloid bearing failure.

### 4. Recipe: Jerk-Limited S-Curve Trajectory Profile (Python)

```python
"""scurve_trajectory.py — S-curve motion profile generator with bounded jerk."""

import math

def calculate_scurve_motion(
    target_displacement_rad: float,
    max_velocity_rad_s: float,
    max_accel_rad_s2: float,
    jerk_rad_s3: float
) -> dict:
    """Calculate minimum time profile with bounded jerk."""
    # Time to ramp acceleration from 0 to max_accel: t_j = a_max / j
    t_j = max_accel_rad_s2 / jerk_rad_s3
    
    # Velocity reached during jerk phase
    v_j = 0.5 * jerk_rad_s3 * (t_j ** 2)
    
    # Known limitation: for short moves (target < distance needed to reach max velocity)
    # the cruise time is clamped to 0 but the profile is not re-derived, so the duration is
    # overestimated. Validate with a numeric simulation before using it for short moves.
    # Check if max velocity is reached
    if max_velocity_rad_s > 2 * v_j:
        t_a = (max_velocity_rad_s - 2 * v_j) / max_accel_rad_s2
    else:
        # Triangular acceleration profile
        t_j = math.sqrt(max_velocity_rad_s / jerk_rad_s3)
        t_a = 0.0
        max_accel_rad_s2 = jerk_rad_s3 * t_j

    total_accel_time = 2 * t_j + t_a
    dist_accel = max_velocity_rad_s * total_accel_time

    if target_displacement_rad > dist_accel:
        t_cruise = (target_displacement_rad - dist_accel) / max_velocity_rad_s
    else:
        t_cruise = 0.0

    total_duration = 2 * total_accel_time + t_cruise

    return {
        "jerk_time_tj_s": round(t_j, 4),
        "const_accel_time_ta_s": round(t_a, 4),
        "cruise_time_tc_s": round(t_cruise, 4),
        "total_trajectory_duration_s": round(total_duration, 4),
        "peak_jerk_rad_s3": jerk_rad_s3
    }
```

### 5. Failure map

| Symptom | Root Cause | Preventive Rule |
| :--- | :--- | :--- |
| CAN bus error counter increases rapidly during motor spin | Motor phase cables run in parallel with unshielded CAN bus lines | Maintain $\ge 20\text{ mm}$ spacing or use shielded twisted pair grounded at chassis |
| One node fails to communicate while others work | Missing $120\ \Omega$ termination or double termination ($< 45\ \Omega$ measured bus resistance) | Measure resistance between CAN_H and CAN_L with power OFF (must be $60\ \Omega$) |
| Robot arm jerks violently at start and stop | Trajectory planner sending raw position step targets without jerk limiting | Always filter setpoints through S-curve profile |
| Master MCU hangs when USB cable is connected | Ground loop between PC USB ground and battery negative through motor controller | Use galvanic USB isolator on debugging cables |

### 6. Verification ladder

1. **Bus Resistance Check:** Measure resistance between CAN_H and CAN_L with system unpowered (must read $60\ \Omega \pm 5\%$ for two parallel $120\ \Omega$ terminators; arithmetic 120 || 120 = 60 ohm). <!-- ease:source UNVERIFIED reason="+-5 % acceptance band is a project choice" -->
2. **Differential Voltage Levels:** Check CAN_H and CAN_L with oscilloscope under transmission (Recessive: $2.5\text{ V}$, Dominant: CAN_H $3.5\text{ V}$, CAN_L $1.5\text{ V}$, $\Delta V = 2.0\text{ V}$). Dominant drive to about 3.5 V / 1.5 V is sourced; in the recessive state both lines tend weakly toward mid-rail (2.5 V is that midpoint on a 5 V transceiver). <!-- ease:source S2 anchor="CANH toward 3.5 V and CANL toward 1.5 V when dominant; recessive near mid-rail" -->
3. <!-- ease:source UNVERIFIED reason="50 ms watchdog and 5 ms gate-voltage drop are project acceptance targets" --> **Heartbeat Watchdog Gate:** Disconnect master controller cable; verify all joint nodes enter safe torque-off within $\le 50\text{ ms}$.
4. **E-Stop Hardware Cut:** Press physical E-Stop; verify motor gate voltage drops to $0\text{ V}$ within $\le 5\text{ ms}$.

## Failure Modes (Mandatory)
- **CAN error counter climbs while the motor spins** — cause: motor phase cables parallel to unshielded CAN lines — fix: separate or shield the CAN pair and ground it at chassis
- **One node silent while others work** — cause: missing or doubled 120 ohm termination — fix: measure CAN_H to CAN_L unpowered, expect 60 ohm
- **Arm jerks at start/stop** — cause: raw position steps without jerk limiting — fix: filter setpoints through the S-curve profile (check the short-move limitation)
- **Master hangs when USB is plugged in** — cause: ground loop through the PC USB ground and battery negative — fix: isolate the debug link

## Sources
- [S1] Wikipedia, CAN FD — https://en.wikipedia.org/wiki/CAN_FD (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-can-fd.html) — captured 2026-10-13 — sha256 b48d08bbaa9e285286d389d0d294acc64403a05c42324e1eba9e8fcec9d797db
- [S2] Wikipedia, CAN bus — https://en.wikipedia.org/wiki/CAN_bus (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-can-bus.html) — captured 2026-10-13 — sha256 6790851e3e16b6de7efc256449a0ac97f508f2a2c0e9e98322cfa732f2a23fe7

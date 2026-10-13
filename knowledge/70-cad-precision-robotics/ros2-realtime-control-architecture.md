---
name: ros2-realtime-control-architecture
category: 70-cad-precision-robotics
domain: embedded_firmware
loads_with: [embedded-realtime-bus-architecture, impedance-admittance-contact-control, production-mechatronics-gate]
tags: [ros2, ros2-control, preempt-rt, cia402, ethercat, canopen, micro-ros, real-time, production-grade]
id: ros2-realtime-control-architecture
title: "Real-Time ROS 2 Control, PREEMPT_RT Kernel & CiA 402 Drive Integration"
description: Real-time ROS 2 control architecture: PREEMPT_RT host tuning, ros2_control hardware interface, CiA 402 drive state machine and fault handling for multi-axis robots.
when: [ros2-control-hardware-interface, preempt-rt-tuning, cia402-state-machine, realtime-jitter-budget, fieldbus-drive-integration]
trust_tier: draft
sources_checked: 2026-10-13
---

# Real-Time ROS 2 Control, PREEMPT_RT Kernel & CiA 402 Drive Integration

> Production architecture for hard real-time robot control: Linux PREEMPT_RT kernel tuning, ros2_control SystemInterface implementation, CiA 402 drive state machine (CST/CSV), and micro-ROS MCU integration.

---

## Purpose
Describes a real-time ROS 2 control stack for a multi-axis robot: a PREEMPT_RT Linux host, a ros2_control SystemInterface that reads and writes CiA 402 drive objects, and safe handling of drive faults. Design-reference note, not certification: timing limits are unverified project targets; measure them on the target hardware and treat safety functions as a separate certified design.

## When to Use / When NOT
- ALLOWED: designing or reviewing a 500-1000 Hz ros2_control hardware interface over EtherCAT or CANopen CiA 402 drives
- ALLOWED: writing the Controlword/Statusword handshake and fault-handling rules for a drive adapter
- NOT ALLOWED: URDF/link modelling — use `robotics-urdf-mechanisms` instead
- NOT ALLOWED: bus topology, CAN/EtherCAT electrical and timing design — use `embedded-realtime-bus-architecture` instead
- NOT ALLOWED: impedance and contact control laws — use `impedance-admittance-contact-control` instead
- NOT ALLOWED: safety-rated stop functions (STO, SS1) and performance level — use `functional-safety-iso13849-robotics` instead

## Core Knowledge Content

### 1. Physical Principles & Real-Time Determinism

#### A. Deterministic Execution & Jitter Deadlines
In multi-axis robotics, high-bandwidth impedance and torque control loops run at a fixed period $T = 1.0\,\text{ms}$ ($1000\,\text{Hz}$). Non-deterministic latency jitter causes phase lag, velocity estimator instability, and violent joint shaking: <!-- ease:source UNVERIFIED reason="1 kHz period and 50 us jitter are project targets; cyclictest evidence required" -->

```math
t_{exec} + t_{comm} + t_{jitter} \le T_{period} \quad \implies \quad t_{jitter,max} \le 50 \, \mu\text{s}
```

> Flagged (2026-10-13): the inequality above does not by itself imply a 50 microsecond jitter bound; 50 us is a 5 percent budget choice for a 1 ms period.

#### B. Linux PREEMPT_RT Real-Time OS Tuning
Standard Linux kernels interrupt user threads for kernel housekeeping, causing hundreds of milliseconds of random latency. A **PREEMPT_RT** kernel is designed for bounded worst-case latency, which still depends on hardware, firmware and configuration (the kernel's PREEMPT_RT document lists hardware, cache, bus and firmware considerations, S5): <!-- ease:source UNVERIFIED reason=""hundreds of milliseconds" is unsourced; measure with cyclictest" -->
- **Thread Scheduling:** Set FIFO real-time priority: `SCHED_FIFO` with priority 95–98 (`chrt -f 98`). <!-- ease:source UNVERIFIED reason="SCHED_FIFO priority 95-98 is a convention, not a documented requirement" -->
- **Memory Locking:** Prevent page faults by locking all process virtual memory into physical RAM: <!-- ease:source S4 anchor="mlockall flags MCL_CURRENT and MCL_FUTURE" -->
  ```c
  mlockall(MCL_CURRENT | MCL_FUTURE);
  ```
- **CPU Core Isolation:** Reserve dedicated CPU cores exclusively for real-time control threads via Linux kernel boot parameters: <!-- ease:source S3 anchor="isolcpus= "Isolate a given set of CPUs from disturbance"; nohz_full and rcu_nocbs take CPU lists" -->
  ```text
  isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3
  ```

---

### 2. Quantitative Interface Specifications

| Parameter | Nominal Specification | Strict Engineering Limit | Unit | Standard / Metric |
|---|---|---|---|---|
| Control Loop Rate | 1000.0 | Min 500.0, Preferred 1000.0 | Hz | ros2_control update rate | <!-- ease:source UNVERIFIED reason="rate window is a project target; ros2_control update_rate not verified here" -->
| Worst-Case Latency Jitter | 15.0 | Max 50.0 | $\mu\text{s}$ | Cyclictest 24-hour benchmark | <!-- ease:source UNVERIFIED reason="project target" -->
| CiA 402 Operating Mode | Mode 10 (CST) | Modes: 8 (CSP), 9 (CSV), 10 (CST) | enum | ETG.6010 / CiA 402 | <!-- ease:source UNVERIFIED reason="mode numbers 8/9/10 not seen in S6; S6 lists the CSP, CSV and CST mode names" -->
| Comm Bus Jitter (EtherCAT) | 2.0 | Max 10.0 | $\mu\text{s}$ | Distributed Clocks (DC) sync | <!-- ease:source UNVERIFIED reason="project target" -->
| CAN-FD PDO Transmit Cycle | 1.0 | Max 2.0 | ms | Multi-axis synchronized PDO | <!-- ease:source UNVERIFIED reason="project target" -->
| Safety Heartbeat Timeout | 50.0 | Max 100.0 | ms | Triggers E-Stop if lost | <!-- ease:source UNVERIFIED reason="project target; not a safety-rated figure" -->

---

### 3. Hardware Abstraction & State Machine Architecture

#### A. `ros2_control` SystemInterface Implementation
```text
[ROS 2 Controller Manager] (Runs at 1 kHz inside PREEMPT_RT thread)
        │
        ├── read()  ◄── Reads Statusword (0x6041), Actual Pos (0x6064), Actual Torque (0x6077)
        │
        ├── update() ── Evaluates Joint Trajectory / Impedance Controller
        │
        └── write() ──► Writes Controlword (0x6040), Target Torque (0x6071)
```

- **Zero-Allocation Law:** Inside `read()` and `write()`, **NEVER** call `malloc()`, `new`, print to `std::cout`, or invoke non-thread-safe libraries. Any dynamic allocation triggers a potential page fault or mutex wait, destroying real-time determinism. <!-- ease:source S1 anchor="update_hardware_status_message "must be fast and non-allocating"; extension to read()/write() is this module's rule" -->

#### B. CiA 402 Drive State Machine Progression
Drives comply with the standardized ETG.6010 / CiA 402 finite state machine: <!-- ease:source S6 anchor="controlword table and statusword masks (0x0006, 0x0007, 0x000F; x1xx 0000, x01x 0001, x01x 0011, x01x 0111)" -->

```text
[Power On] ──► [Switch On Disabled] (Statusword & 0x004F == 0x0040)
                     │
                     ▼ Write Controlword: 0x0006
               [Ready to Switch On] (Statusword & 0x006F == 0x0021)
                     │
                     ▼ Write Controlword: 0x0007
               [Switched On]        (Statusword & 0x006F == 0x0023)
                     │
                     ▼ Write Controlword: 0x000F
               [Operation Enabled]  (Statusword & 0x006F == 0x0027) ──► Accepts Target Torque (0x6071)
```

- *STO Fault Guardrail:* If hardware Safe Torque Off (STO) is triggered, the drive transitions immediately to *Fault* (Statusword bit 3 high). The hardware interface must recognize this state, disallow automatic reset, and report a latched diagnostic alert to ROS 2. <!-- ease:source UNVERIFIED reason="drive reaction to STO (Fault vs Switch on disabled) is manufacturer specific; Fault bit 3 pattern x0xx 1000 is in S6" -->

---

### 4. Failure Modes & Mitigation Matrix (DFMEA)

| Failure Mode | Root Cause | Failure Effect | Engineering Guardrail |
|---|---|---|---|
| Latency Deadline Miss (Overrun) | Page fault or non-RT thread preemption | Motor jerks violently, FOC current loop instability | Hard-realtime supervisor thread terminates command and engages hardware mechanical brake if overrun occurs twice consecutively. | <!-- ease:source UNVERIFIED reason="two-consecutive-overrun rule is a project choice" -->
| Inadvertent Drive Enable with Active Fault | Initializing `write()` loop while STO or over-temperature bit set | Drive lockup, controller timeout crash | Query Statusword (`0x6041`) before issuing Controlword transition; require explicit clearing of bit 7 (Fault Reset). | <!-- ease:source S6 anchor="fault reset is a rising edge of controlword bit 7" -->
| Unbounded Joint Position Drift | Running Cyclic Synchronous Torque (CST) without software limiters | Arm hits physical hardstop at full torque | Multi-layer limiters: Software soft-limits in ROS 2 controller + hardware limit switches + motor firmware threshold. | <!-- ease:source UNVERIFIED reason="layered-limit advice is a design practice" -->
| Packet Loss on Fieldbus | EMI noise from motor phase cables corrupting EtherCAT/CAN frames | Out-of-sync multi-axis motion | CRC error counters monitored; 3 consecutive dropped frames forces Safe Stop 1 (SS1). | <!-- ease:source UNVERIFIED reason="three dropped frames and SS1 mapping are project choices" -->

---

### 5. Production Verification Gate

#### Level 1: PREEMPT_RT Kernel Benchmark
- [ ] System tested under 100% CPU and I/O stress using `stress-ng` for 24 hours: `cyclictest` verifies max latency $\le 45.0\,\mu\text{s}$ with zero overruns. <!-- ease:source UNVERIFIED reason="45 us acceptance value is a project target" -->

#### Level 2: CiA 402 State Machine Compliance
- [ ] Automated transition test: Drive transitions cleanly through *Ready to Switch On* $\to$ *Switched On* $\to$ *Operation Enabled* within $\le 200\,\text{ms}$. <!-- ease:source UNVERIFIED reason="200 ms and 15 ms limits are project targets" -->
- [ ] Fault injection: Disconnect STO during motion; verify drive drops to zero torque in $<15\,\text{ms}$ and flags *Fault* status.

#### Level 3: Dynamic Multi-Axis Synchronous Trajectory
- [ ] 6-DOF arm moves through high-speed coordinated spiral trajectory: Trajectory tracking error across all axes $\le 0.05\,\text{rad}$ with zero bus timing jitter flags. <!-- ease:source UNVERIFIED reason="0.05 rad tracking limit is a project target" -->

#### Level 4: Configuration & Package Release
- [ ] URDF `/ros2_control` tag configured with explicit command and state interfaces (`position`, `velocity`, `effort`). <!-- ease:source S2 anchor="hardware component description and interfaces" -->
- [ ] Lifecycle management nodes verified with standard ROS 2 bringup launch scripts.

## Failure Modes (Mandatory)
- **Control loop jerks or overruns occasionally** — cause: page fault, allocation or non-RT preemption inside read/write — fix: lock memory, isolate cores, keep the loop allocation-free (principle: S1 for the status callback, S4 for mlockall)
- **Drive ignores the enable sequence** — cause: Controlword written without checking the masked Statusword state — fix: compare Statusword & 0x006F with 0x0040/0x0021/0x0023/0x0027 before each transition (S6)
- **Drive stays in Fault after the cause is gone** — cause: fault reset is a rising edge on Controlword bit 7, so holding the bit does nothing (S6) — fix: pulse bit 7 once, then re-run the enable sequence
- **Arm runs into a hard stop at full torque in CST mode** — cause: no layered limits — fix: soft limits in the controller, drive-side limits and a mechanical stop
- **Multi-axis motion falls out of sync** — cause: lost or corrupted fieldbus frames — fix: monitor CRC/error counters and define a stop reaction after N missed cycles (N is a project choice)
- **Latency budget appears justified but is not** — cause: the 50 microsecond jitter limit does not follow from the period inequality — fix: state it as a 5 percent budget choice and measure it

## Sources
- [S1] ros2_control, "Writing a Hardware Component" (Rolling) — https://control.ros.org/rolling/doc/ros2_control/hardware_interface/doc/writing_new_hardware_component.html — knowledge/_evidence/kb-261013/w7-ros2-control-hwif.html — captured 2026-10-13 — sha256 0b78a472181206a298a07ef5e4c6171aa3c20e2e63414dbfbd51153454c6ad93
- [S2] ros2_control, "Hardware Components User Documentation" (Rolling) — https://control.ros.org/rolling/doc/ros2_control/hardware_interface/doc/hardware_components_userdoc.html — knowledge/_evidence/kb-261013/w7-ros2control-hw-userdoc.html — captured 2026-10-13 — sha256 ff02cdfdfc4f9ceedcfd30265ddf33202b2f73cdcb2d1d1c9ae1911a7990e49b
- [S3] Linux kernel documentation, "The kernel's command-line parameters" (isolcpus, nohz_full, rcu_nocbs) — https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html — knowledge/_evidence/kb-261013/w7-kernel-isolcpus.html — captured 2026-10-13 — sha256 4b19f89eacf6225cb15772a7690660c4f8766a0029059f674e3ecb4e11981e4e
- [S4] Linux man-pages, mlock(2) / mlockall (MCL_CURRENT, MCL_FUTURE) — https://man7.org/linux/man-pages/man2/mlock.2.html — knowledge/_evidence/kb-261013/w7-mlockall.html — captured 2026-10-13 — sha256 a85b6353ffe650837dd9c216d727fef04eb4321b0e3affd1b947d475ba2c6459
- [S5] Linux kernel documentation, "Real-time preemption" (PREEMPT_RT; captured page is the section index only) — https://docs.kernel.org/core-api/real-time/index.html — knowledge/_evidence/kb-261013/w7-kernel-rt-core-api.html — captured 2026-10-13 — sha256 be7c8e6b4e5b2d30bf4e82ddb86aa4d35b2feb6e349709abcb0f30fc2d90a9af
- [S6] Nanotec NP5 manual, "CiA 402 Power State Machine" (controlword/statusword tables) — https://nanotec.com/eu/it/prodotti/manuale/m/np5-spi-en/p/general%2Fds402_power_state_machine.html — knowledge/_evidence/kb-261013/w7-nanotec-cia402-state-machine.html — captured 2026-10-13 — sha256 950570ae38b918d166b62a7786a5684921e309cfeb57655b973d6ea8c17f8044
- [S7] ros2_canopen documentation (CiA 402 driver, ros2_control integration; index page) — https://ros-industrial.github.io/ros2_canopen/manual/rolling/ — knowledge/_evidence/kb-261013/w7-cia402-ros2canopen.html — captured 2026-10-13 — sha256 c6416daf963e6e403d9bd1d5471c4064ba1333ac00d0d6e5e4629c69ccdc0050
- [S8] CiA 402 drive profile and EtherCAT ETG.6010 implementation directive — paywalled/member documents, not captured — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)

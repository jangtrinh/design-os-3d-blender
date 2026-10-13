---
name: sensor-fusion-state-estimation
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Sensor selection, magnetic/optical encoder architectures, 6-DOF IMU filtering, and Extended Kalman Filter (EKF) state estimation.
loads_with: [actuators-motors-foc-control, robotics-urdf-mechanisms, industrial-connectors-wire-harness]
tags: [robotics, sensors, encoders, imu, kalman-filter, ahrs, odometry, state-estimation]
id: sensor-fusion-state-estimation
title: "Sensor Fusion & State Estimation in Robotic Mechanisms"
when: [encoder-selection, imu-attitude-filter, complementary-filter, gyro-bias-calibration, joint-position-sensing]
trust_tier: draft
sources_checked: 2026-10-13
---

# Sensor Fusion & State Estimation in Robotic Mechanisms

## Purpose
Explains how to pick joint and body sensors and fuse accelerometer and gyro data into an attitude estimate, with encoder mounting and noise rules. Design-reference note, not certification: sensor part numbers, protocols and thresholds are unverified here; confirm them against the current datasheets before a design is frozen.

## When to Use / When NOT
- ALLOWED: choosing encoder placement (motor shaft vs joint output) and IMU filtering for a robot joint or body
- ALLOWED: sizing a first complementary filter and checking its time constant
- NOT ALLOWED: kinematic parameter identification of the arm — use `kinematic-calibration-dh-metrology` instead
- NOT ALLOWED: URDF frames and inertia — use `robotics-urdf-mechanisms` instead
- NOT ALLOWED: motor current/FOC loops — use `actuators-motors-foc-control` instead
- NOT ALLOWED: connectors and shielding — use `industrial-connectors-wire-harness` instead

## Core Knowledge Content

### 1. Mental model

In autonomous robotics, raw sensor readings are noisy, biased, and latency-lagged approximations of reality. **State estimation** fuses complementary physical signals to reconstruct the true state vector ($x = [p, v, q, \omega]^T$).

1. **Complementary Physics Principle:**
   * **Accelerometers:** Measure gravitational vector $+g$ accurately at steady-state (low frequency), but are corrupted by linear vibration and high-frequency dynamic accelerations. <!-- ease:source UNVERIFIED reason="standard inertial-sensing physics; Mahony (S1) and Madgwick (S2) are the primary references, not re-read" -->
   * **Gyroscopes:** Measure angular rate $\omega$ accurately at high frequency, but suffer from low-frequency bias drift ($b_{gyro}$) that integrates to infinite angle error over time.
   * **Fusion Solution:** A complementary filter or **Extended Kalman Filter (EKF)** blends the low-drift gravity vector with the high-bandwidth gyro integration.
2. **Encoder Architectures (Dual-Encoder Principle):**
   * **Primary Encoder (Motor Shaft):** High-speed, high-resolution feedback directly to the FOC current loop ($12\text{--}14\text{ bit}$). <!-- ease:source UNVERIFIED reason="12-14 bit resolution is a typical value" -->
   * **Secondary Encoder (Joint Output):** Mounted after the gearbox to measure actual joint position, bypassing gearbox backlash, elasticity, and tooth deformation.
3. **Bandwidth Matching:** Sensor sampling rate must be $\ge 10 \times$ the mechanical Nyquist frequency of the physical joint resonance. <!-- ease:source UNVERIFIED reason="10 x Nyquist rule is a heuristic" -->

### 2. Decision first

| Measurement Goal | Sensor Choice | Typical Protocol | Update Rate | Noise Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **Motor Electrical Angle** | On-axis Hall/Magnet (AS5600/MT6701) | SPI / SSI / BiSS-C (flagged 2026-10-13: AS5600 is, per a search snippet, an I2C/analog/PWM part, not SPI/SSI/BiSS-C; check each datasheet) | $\ge 20\text{ kHz}$ | Differential signaling, shielded twisted pair | <!-- ease:source UNVERIFIED reason="part/protocol mapping not verified; datasheets not captured" -->
| **Joint Absolute Angle** | Off-axis Hollow-ring (RLS / AksIM) | BiSS-C / CAN | $1\text{--}5\text{ kHz}$ | Shielded ring ground, zero eccentric runout | <!-- ease:source UNVERIFIED reason="RLS/AksIM and rates not verified" -->
| **Robot Body Orientation** | 6-DOF IMU (ICM-42688 / LSM6DSOX) | SPI (up to $10\text{ MHz}$) | $1\text{--}4\text{ kHz}$ | Hardware low-pass filter (LPF), thermal calibration | <!-- ease:source UNVERIFIED reason="ICM-42688/LSM6DSOX SPI rates not verified; TDK datasheet not captured" -->
| **Obstacle / Proximity** | Time-of-Flight (VL53L1X / ToF laser) | I2C / UART | $30\text{--}50\text{ Hz}$ | Optical cover-glass calibration, median filter | <!-- ease:source UNVERIFIED reason="VL53L1X rate not verified" -->

Decision tree for sensor protocol selection:
1. Is the sensor located across an active rotating joint? → Choose high-speed SPI or BiSS-C over twisted pair; never use standard single-ended I2C due to bus lockup risk from ground bounce.
2. Is multi-drop daisy chaining required across multiple joints? → Choose CAN-FD or RS-485 with differential transceivers.

### 3. Rules

R1. Magnetic encoder magnets must be diametrically polarized with axial air gap strictly maintained within $0.5\text{--}1.5\text{ mm}$. <!-- ease:source UNVERIFIED reason="0.5-1.5 mm gap; a search snippet of an AS5600 datasheet mirror gives 0.5-3 mm, magnet dependent (not captured)" -->
    Why: Axial runout $> 0.2\text{ mm}$ causes non-linear angle distortion and periodic velocity ripple ($N$-per-revolution torque ripple).
    Violation: High-frequency acoustic vibration and position error in the FOC drive.

R2. Gyroscope bias must be calibrated at zero-motion startup before engaging state estimation. <!-- ease:source UNVERIFIED reason="bias integration is first-principles (theta = b x t); no source captured" -->
    Why: Uncalibrated bias ($b_0 \ne 0$) integrates into linear drift rate ($\theta_{drift} = b_0 \times t$), causing robot orientation to diverge rapidly.
    Violation: Drone drifts laterally or robot arm drops out of level within 30 seconds.

R3. Sensor ground lines must connect directly to clean logic ground, never sharing high-current motor ground return traces. <!-- ease:source UNVERIFIED reason="layout practice; see power-distribution-bms-protection for grounding" -->
    Why: Large motor ground currents ($I_{motor} > 5\text{ A}$) through shared trace resistance induce ground potential shifts ($V = I R$), corrupting digital SPI/I2C voltage levels.
    Violation: Bus hangup, communication timeouts, and spurious reset events.

R4. Mechanical endstops and optical interrupters must feature hardware RC low-pass filters ($R = 1\text{ k}\Omega, C = 100\text{ nF}, \tau = 100\ \mu\text{s}$) or software Schmitt triggers. <!-- ease:source UNVERIFIED reason="RC = 1 kOhm x 100 nF = 100 us is arithmetic; 5-20 bounce edges over 2 ms is unsourced" -->
    Why: Mechanical switch contact bounce produces $5\text{--}20$ false trigger edges over $2\text{ ms}$, corrupting homing routines.
    Violation: Joint homes at different physical zero positions on every power cycle.

### 4. Recipe: Complementary Filter for IMU roll/pitch (Python; Euler angles, not a quaternion filter)

```python
"""imu_complementary_filter.py — Discrete-time attitude estimation."""

import math

class AttitudeEstimator:
    def __init__(self, alpha: float = 0.98, dt: float = 0.005):
        self.alpha = alpha  # Gyro weight (high frequency)
        self.dt = dt        # 200 Hz sample rate
        self.pitch = 0.0
        self.roll = 0.0

    def update(self, ax: float, ay: float, az: float, gx_rad_s: float, gy_rad_s: float):
        # 1. Accelerometer tilt angles (low frequency reference)
        accel_roll = math.atan2(ay, az)  # ease:source S4 anchor="recipe constants alpha 0.98, dt 0.005 s give tau 0.245 s"
        accel_pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2))

        # 2. Integrate gyroscope angular rates
        gyro_roll = self.roll + gx_rad_s * self.dt
        gyro_pitch = self.pitch + gy_rad_s * self.dt

        # 3. Complementary blend
        self.roll = self.alpha * gyro_roll + (1.0 - self.alpha) * accel_roll
        self.pitch = self.alpha * gyro_pitch + (1.0 - self.alpha) * accel_pitch

        return {"roll_deg": math.degrees(self.roll), "pitch_deg": math.degrees(self.pitch)}
```

### 5. Failure map

| Symptom | Root Cause | Preventive Rule |
| :--- | :--- | :--- |
| Encoder position jumps by $180^\circ$ intermittently | Magnetic field strength too low or magnet centered improperly | Check magnet field strength diagnostic bit (`MAGNET_TOO_WEAK` register) | <!-- ease:source UNVERIFIED reason="magnet-strength diagnostic register names not verified" -->
| I2C bus locks low permanently during motor acceleration | Inductive voltage transient pulling SDA/SCL below ground | Route sensors on differential bus or add Schottky clamping diodes | <!-- ease:source UNVERIFIED reason="anecdotal failure mode" -->
| IMU pitch angle explodes when robot starts driving | Linear vehicle acceleration mistaken for gravity vector | Use EKF with dynamic acceleration gating or visual/wheel odometry | <!-- ease:source UNVERIFIED reason="standard behaviour of accelerometer-referenced filters" -->
| Homing position shifts by $1\text{--}2\text{ mm}$ between boots | Optical sensor triggered at shallow angle without sharp blade edge | Use high-contrast knife-edge interrupter blade | <!-- ease:source UNVERIFIED reason="anecdotal failure mode" -->

### 6. Verification ladder

1. **Encoder Runout Check:** Rotate joint $360^\circ$ manually; verify read angle increases monotonically without backward step glitches.
2. **Gyro Noise Density:** Sample IMU stationary for 60 seconds; calculate standard deviation ($< 0.05^\circ/\text{s}$ root-mean-square). <!-- ease:source UNVERIFIED reason="0.05 deg/s RMS acceptance value is a project heuristic; ICM-42688 noise figure not captured" -->
3. **Step Response:** Apply sudden $90^\circ$ orientation step; verify complementary filter settles within $150\text{ ms}$ without underdamped ringing. (Flagged 2026-10-13: 150 ms is reachable only for the gyro-tracked part of the step; the accelerometer correction has tau = alpha x dt / (1 - alpha) = 0.245 s for alpha 0.98 at 200 Hz, and its 98 percent settling time is 0.97 s, S3/S4.)
4. **Homing Repeatability:** Run homing cycle 10 times; verify zero position deviation $< \pm 0.05\text{ mm}$. <!-- ease:source UNVERIFIED reason="0.05 mm acceptance value is a project heuristic" -->

## Failure Modes (Mandatory)
- **Attitude angle drifts steadily at standstill** — cause: gyro bias not calibrated before integration — fix: average the gyro at zero motion at start-up
- **Pitch/roll jumps when the robot accelerates** — cause: linear acceleration taken as gravity by the accelerometer path — fix: gate the accelerometer correction or use an EKF with odometry
- **Filter responds slower than the test says** — cause: alpha 0.98 at 200 Hz gives tau = 0.245 s; accelerometer-path 98 percent settling is 0.97 s (S3), not 150 ms — fix: choose alpha from the required time constant
- **Angle from the 3-axis rates is wrong at large tilt** — cause: the recipe adds body rates directly to Euler angles (valid only near level) — fix: use a quaternion or rotation-matrix filter for large angles
- **Homing position changes between boots** — cause: switch bounce or shallow-angle optical trigger — fix: hardware RC filter plus a sharp-edged interrupter blade

## Sources
- [S1] Mahony, R., Hamel, T. & Pflimlin, J.-M. (2008), "Nonlinear complementary filters on the special orthogonal group", IEEE Transactions on Automatic Control 53(5) — bibliographic entry (not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S2] Madgwick, S. (2010), "An efficient orientation filter for inertial and inertial/magnetic sensor arrays", technical report, University of Bristol — bibliographic entry; the x-io.co.uk URL tried returned 404 — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S3] Numeric check of the module complementary filter (script) — knowledge/_evidence/kb-261013/w7-complementary-filter-time-constant-check.py — captured 2026-10-13 — sha256 60d48403f01bcf0e93151147152e0618bb2a7255fa0076a08c2d1e0e80d07e8a
- [S4] Numeric check output (tau 0.245 s; 63 percent at 0.250 s; 98 percent at 0.970 s) — knowledge/_evidence/kb-261013/w7-complementary-filter-time-constant-check-output.txt — captured 2026-10-13 — sha256 8e2d6309b9288be1f4fcc95c01fe2f950928949c11a56668851bfd577de9290b

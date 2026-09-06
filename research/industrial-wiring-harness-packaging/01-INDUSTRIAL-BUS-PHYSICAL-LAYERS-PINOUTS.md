# 01. Industrial Bus Physical Layers, Differential Signaling & Connector Pinouts

Exhaustive engineering specification of industrial communication physical layers, transmission line reflection physics, termination networks, and pinout schematics for mechanical packaging and connector integration.

---

## 1. Transmission Line Fundamentals & Differential Signaling

```
                  DIFFERENTIAL TRANSMISSION LINE (Z_0 = 120 Ohm)
       +--------+                                               +--------+
       | Driver |====== Wire A (Non-inverting / +) =============| Rcv    |
       |        |                                               |        |
       |        |------ R_T (120 Ohm) ------------------- R_T --|        |
       |        |                                               |        |
       |        |====== Wire B (Inverting / -) =================|        |
       +--------+                                               +--------+
            |                                                        |
         Ground                                                   Ground
```

### A. Transmission Line Reflection & Characteristic Impedance
When signal transition time $t_r$ is less than twice the one-way cable propagation delay $t_{pd}$ ($t_r < 2 \cdot t_{pd} \cdot L$), the cable acts as a distributed transmission line governed by the telegrapher's equations:
$$Z_0 = \sqrt{\frac{L'}{C'}} \quad [\Omega]$$
Where:
- $L'$ is loop inductance per meter ($H/m$).
- $C'$ is mutual capacitance per meter ($F/m$).
- Typical values: RS-485 / CAN $Z_0 = 120 \pm 12\ \Omega$; Industrial Ethernet $Z_0 = 100 \pm 15\ \Omega$.

If the transmission line is terminated with load impedance $Z_L$, the voltage reflection coefficient $\Gamma$ is:
$$\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}$$
- If open circuit ($Z_L = \infty$): $\Gamma = +1.0$ (signal doubles in amplitude, ringing corrupts bits).
- If short circuit ($Z_L = 0$): $\Gamma = -1.0$ (inverted reflection cancels signal).
- If matched ($Z_L = Z_0$): $\Gamma = 0$ (zero reflection, pure energy absorption).

### B. Common-Mode Rejection Ratio (CMRR)
Differential signaling transmits equal and opposite voltages: $V_A = V_{cm} + \frac{V_d}{2}$, $V_B = V_{cm} - \frac{V_d}{2}$.
The receiver senses only the differential voltage:
$$V_{diff} = V_A - V_B = V_d$$
Any coupled noise from external servo switching ($V_{noise}$) affects both twisted wires equally ($V_{cm}' = V_{cm} + V_{noise}$), canceling out at the receiver:
$$\text{CMRR} = 20 \log_{10} \left| \frac{A_d}{A_{cm}} \right| \quad (\text{typically } > 70\text{ dB})$$

---

## 2. Industrial Protocol Physical Layers & Pinout Specifications

```
+---------------------------------------------------------------------------------------------------------+
| Protocol        | Standard          | Baud Rate      | Impedance | Top Connector | Pins / Polarities    |
+-----------------+-------------------+----------------+-----------+---------------+----------------------+
| Modbus RTU      | TIA/EIA-485-A     | Up to 115 kbps | 120 Ohm   | Screw / RJ45  | A (+), B (-), GND    |
| Modbus TCP      | IEEE 802.3u       | 100 Mbps       | 100 Ohm   | RJ45 / M12 D  | TX+, TX-, RX+, RX-   |
| PROFINET RT/IRT | 100BASE-TX        | 100 Mbps       | 100 Ohm   | M12 D-coded   | 1:TX+, 2:RX+, 3:TX-, 4:RX-|
| PROFIBUS DP     | EN 50170 / RS-485 | Up to 12 Mbps  | 150 Ohm   | DB9 Male/Fem  | 3:RxD/TxD-P, 8:RxD/TxD-N|
| EtherNet/IP     | IEEE 802.3ab      | 1000 Mbps      | 100 Ohm   | M12 X-coded   | 8-pin gigabit pairs  |
| CAN 2.0B / FD   | ISO 11898-2:2016  | Up to 5 Mbps   | 120 Ohm   | Phoenix / DB9 | 2:CAN_L, 7:CAN_H, 3:GND|
| DeviceNet       | ODVA Specification| 125 - 500 kbps | 121 Ohm   | 5-pin Micro   | V-, CAN_L, SH, CAN_H, V+|
| HART            | Bell 202 FSK      | 1200 baud      | 250 Ohm   | Screw Gland   | 4-20mA loop (+ / -)  |
| IO-Link         | IEC 61131-9       | Up to 230 kbps | Point-Pt  | M12 A-coded   | 1:L+, 3:L-, 4:C/Q    |
| EtherCAT        | IEC 61158-2       | 100 Mbps       | 100 Ohm   | M8 / M12 D    | In / Out daisy chain |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Pinout & Termination Schematics

### A. PROFIBUS DP Active Termination Network (DB9 Connector)
To prevent line floating in tri-state mode, PROFIBUS requires an active termination network at both physical ends of the segment:
```
           +5V Bus (Pin 6)
              |
             [390 Ohm] (Pull-up resistor: defines idle state A > B)
              |
              +---- Pin 3: Data Line B (RxD/TxD-P, Red wire)
              |
             [220 Ohm] (Characteristic termination matching resistor)
              |
              +---- Pin 8: Data Line A (RxD/TxD-N, Green wire)
              |
             [390 Ohm] (Pull-down resistor)
              |
           GND Bus (Pin 5)
```

### B. CAN / CANopen Split Termination (ISO 11898-2)
Split termination provides superior common-mode noise suppression by creating an AC ground for high-frequency common-mode noise:
```
       CAN_H (Pin 7) -------+
                            |
                          [60 Ohm]  (1% metal film)
                            |
                            +-------||------- GND (Pin 3)
                            |      4.7 nF
                          [60 Ohm]  (1% metal film)
                            |
       CAN_L (Pin 2) -------+
```
- Total differential DC termination: $60\ \Omega + 60\ \Omega = 120\ \Omega$.
- Common-mode corner frequency: $f_c = \frac{1}{2 \pi \cdot (R/2) \cdot C} = \frac{1}{2 \pi \cdot 30 \cdot 4.7 \times 10^{-9}} \approx 1.13\text{ MHz}$.

### C. DeviceNet 5-Conductor Wire & Connector Mapping (ODVA Standard)
DeviceNet combines 24V DC auxiliary logic power with isolated CAN differential signals in a single shielded multi-conductor jacket:
```
+-----+---------------+------------+-------------------+----------------------------+
| Pin | Signal Name   | Wire Color | Conductor Gauge   | Function                   |
+-----+---------------+------------+-------------------+----------------------------+
| 1   | V- (Drain/GND)| Black      | 15 AWG (Thick)    | Negative 24V Power / Return|
| 2   | CAN_L         | Blue       | 18 AWG (Thick)    | Dominant Low Signal Line   |
| 3   | SHIELD        | Bare/Braid | Drain wire        | Chassis ground termination |
| 4   | CAN_H         | White      | 18 AWG (Thick)    | Dominant High Signal Line  |
| 5   | V+            | Red        | 15 AWG (Thick)    | Positive +24V DC Bus Power |
+-----+---------------+------------+-------------------+----------------------------+
```

### D. M12 D-Coded Industrial Ethernet (PROFINET / Modbus TCP 100BASE-TX)
Pinout per IEC 61076-2-101:
```
           Top View (Female Socket)
                     (2)
                  /   |   \
              (1)     |     (3)       Pin 1: Yellow (TX +)
               \      |      /        Pin 2: White  (RX +)
                      |               Pin 3: Orange (TX -)
                     (4)              Pin 4: Blue   (RX -)
```

### E. M12 X-Coded Gigabit Industrial Ethernet (EtherNet/IP 1000BASE-T)
Pinout per IEC 61076-2-109 (Shielded cross separator isolating 4 differential pairs):
- Pair 1 (1-2): White-Orange / Orange (DA+ / DA-)
- Pair 2 (3-4): White-Green / Green (DB+ / DB-)
- Pair 3 (7-8): White-Brown / Brown (DC+ / DC-)
- Pair 4 (5-6): White-Blue / Blue (DD+ / DD-)

---

## 4. HART Protocol & 4–20 mA Current Loop Dynamics

The Highway Addressable Remote Transducer (HART) protocol superimposes digital Frequency Shift Keying (FSK) signals on an analog $4\text{–}20\text{ mA}$ DC current loop without interrupting the measurement:
- **Analog Carrier**: $4\text{ mA} = 0\%$ range (live zero, distinguishes $0\%$ from broken cable); $20\text{ mA} = 100\%$ range.
- **NAMUR NE 43 Fault Levels**: Sensor failure signaled at $I \le 3.6\text{ mA}$ (downscale burnout) or $I \ge 21.0\text{ mA}$ (upscale burnout).
- **FSK Modulation (Bell 202)**:
  - Logic '1': $1200\text{ Hz}$ sine wave ($\pm 0.5\text{ mA}$ amplitude).
  - Logic '0': $2200\text{ Hz}$ sine wave ($\pm 0.5\text{ mA}$ amplitude).
  - Average DC contribution of FSK is zero: $\int_0^T I_{FSK}(t) dt = 0$.
- **Minimum Loop Resistance**: $R_{loop} \ge 250\ \Omega$ required across the shunt resistor for the HART modem to develop the required voltage drop ($\Delta V = 250\ \Omega \times 1\text{ mA}_{p-p} = 250\text{ mV}_{p-p}$).

---

## 5. Mechanical Enclosure & PCB Integration Requirements

1. **Clearance for Plug Insertion / Mating**:
   - M12 straight molded plug: Requires $\ge 50\text{ mm}$ clear axial envelope from panel face.
   - M12 right-angle plug: Requires $\ge 35\text{ mm}$ radial clearance, orientable in $90^\circ$ increments.
   - RJ45 booted patch cord: Requires $\ge 65\text{ mm}$ axial clearance before bend radius begins.
2. **PCB Edge Connector Standoff**:
   - Right-angle board-to-panel connectors require panel cutout centerline positioned exactly $H_{center} = 3.5\text{–}4.5\text{ mm}$ above PCB top copper surface.
3. **Panel Clamping Thickness**:
   - Standard bulkhead connector threaded barrels provide clamping for panel thickness $t = 1.5\text{ mm to } 4.0\text{ mm}$. If machining a plastic or thick aluminum casting, a spotface counterbore is mandatory.

---

## 6. Academic & Standards Citations

1. **TIA/EIA-485-A (1998)**: *Electrical Characteristics of Generators and Receivers for Use in Balanced Digital Multipoint Systems*. Telecommunications Industry Association.
2. **ISO 11898-2:2016**: *Road vehicles — Controller area network (CAN) — Part 2: High-speed medium access unit*.
3. **IEC 61076-2-101:2021**: *Connectors for electrical and electronic equipment — Detail specification for M12 connectors with screw-locking*.
4. **IEC 61076-2-109:2014**: *Detail specification for circular connectors with M12x1 screw-locking, for data transmission frequencies up to 500 MHz (X-coding)*.
5. **ODVA (2014)**: *Volume 3: DeviceNet Adaptation of CIP (Edition 1.15)*. Open DeviceNet Vendors Association.
6. **HART Communication Foundation (2007)**: *HART Field Communication Protocol Specification (Revision 7.0)*.
7. **NAMUR NE 43 (2003)**: *Standardisation of the Signal Level for the Failure Information of Digital Transmitters*.
8. **Johnson, H. W., & Graham, M. (1993)**: *High-Speed Digital Design: A Handbook of Black Magic*. Prentice Hall. ISBN: 978-0-133-95724-2.
9. **Paul, C. R. (2006)**: *Introduction to Electromagnetic Compatibility (2nd ed.)*. John Wiley & Sons. ISBN: 978-0-471-75500-5.

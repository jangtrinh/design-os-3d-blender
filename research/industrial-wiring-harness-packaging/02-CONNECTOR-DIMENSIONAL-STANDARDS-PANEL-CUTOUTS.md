# 02. Industrial Connector Dimensional Standards, Panel Cutouts & Sealing Interfaces

Complete dimensional engineering reference for creating precision chassis cutouts, anti-rotation flats, O-ring seal faces, and PCB connector footprints in CAD.

---

## 1. M12 & M8 Circular Bulkhead Connectors (IEC 61076-2-101 / IEC 61076-2-104)

```
                       M12 PANEL D-CUT CHASSIS GEOMETRY
                                  +---------+
                              _--'     |     `--_
                           .-'         |         `-.
                          /            |            \
                         |             |             |
                         |      +------+------+      | ---
                         |      |  (0,0)|     |      |  |
                         |      +------+------+      |  | W_flat = 10.5 mm
                          \            |            /|  |
                           `-.         |         .-' | ---
                              `--_     |     _--'    |
                                  +----+----+        |
                                       |<---- D ---->|
                                       D_bore = 12.2 mm
```

### A. M12 Bulkhead Cutout Dimensions (Metric Thread M12x1.0)
*   **Through-Bore Diameter ($D_{bore}$)**: $12.20^{+0.10}_{-0.00}\text{ mm}$.
*   **Anti-Rotation Flat Width ($W_{flat}$)**: $10.50 \pm 0.05\text{ mm}$ (distance from arc crest to flat chord).
*   **O-Ring Sealing Boss Counterbore**: Minimum diameter $\varnothing \ge 18.0\text{ mm}$, depth $0.5\text{ mm}$, surface finish $Ra \le 1.6\ \mu\text{m}$.
*   **Panel Clamping Thickness ($t_{panel}$)**: Standard rear-mount $1.5\text{–}4.0\text{ mm}$; Front-mount $1.0\text{–}3.5\text{ mm}$.
*   **Hex Locknut Clearance**: Across-flats $s = 17.0\text{ mm}$ (requires socket wrench access envelope $\varnothing \ge 22.0\text{ mm}$).

### B. M8 Bulkhead Cutout Dimensions (Metric Thread M8x1.0 / M8x0.75)
*   **Through-Bore Diameter**: $8.20^{+0.10}_{-0.00}\text{ mm}$.
*   **Anti-Rotation Flat Width**: $7.10 \pm 0.05\text{ mm}$.
*   **Sealing Flange Boss**: $\varnothing \ge 13.0\text{ mm}$.
*   **Locknut Hex Size**: $s = 11.0\text{ mm}$.

---

## 2. D-Subminiature Panel Cutouts (IEC 60807-3 / DIN 41652)

```
                            D-SUB 9 (DE-9) CUTOUT
               |<------------------ C = 25.00 mm ------------------>|
               (o) 3.2 mm                                           (o) 3.2 mm
                    |<------------ A = 19.80 mm ------------>|
                    +----------------------------------------+
                    \                                        /  ---
                     \                                      /    |  H = 11.4 mm
                      +------------------------------------+    ---
                       |<---------- B = 16.50 mm --------->|
```

### Detailed D-Sub Cutout Dimensions (Front / Rear Panel Mounting)
All dimensions in millimeters ($mm \pm 0.10\text{ mm}$):

```
+-----------+--------+--------+--------+--------+-------------+---------------------+
| Shell     | Pins   | Dim A  | Dim B  | Dim H  | Screw Spac C| Jack Screw Thread   |
+-----------+--------+--------+--------+--------+-------------+---------------------+
| DE-9      | 9-pin  | 19.80  | 16.50  | 11.40  | 25.00       | 4-40 UNC or M3x0.5  |
| DA-15     | 15-pin | 28.10  | 24.80  | 11.40  | 33.32       | 4-40 UNC or M3x0.5  |
| DB-25     | 25-pin | 41.80  | 38.50  | 11.40  | 47.04       | 4-40 UNC or M3x0.5  |
| DC-37     | 37-pin | 58.30  | 55.00  | 11.40  | 63.50       | 4-40 UNC or M3x0.5  |
+-----------+--------+--------+--------+--------+-------------+---------------------+
```
*Note*: Screw holes are $\varnothing 3.20\text{ mm}$ for M3 screws or 4-40 UNC clearance. For rear panel mounting, add $+0.50\text{ mm}$ to Dim A, B, and H to clear the metal stamped flange shell.

---

## 3. Industrial Ethernet RJ45 Cutouts (IEC 60603-7 / IEC 61076-3-106)

### A. Standard IP20 Keystone Jack Rectangular Cutout
*   **Cutout Width**: $14.50 \pm 0.10\text{ mm}$.
*   **Cutout Height**: $16.00 \pm 0.10\text{ mm}$.
*   **Snap-Latching Panel Lip**: Thickness must be $1.20\text{ to } 1.60\text{ mm}$. Thicker chassis walls require a recessed pocket on the interior face.

### B. Circular IP67 Industrial Bayonet Bulkhead (e.g., Amphenol / Phoenix)
*   **Center Pass-Through Hole**: $\varnothing 25.40\text{ mm}$ ($1.0\text{ inch}$).
*   **Flange Mounting Hole Pattern**: 4x $\varnothing 3.2\text{ mm}$ at $24.0\text{ mm} \times 24.0\text{ mm}$ square centers.
*   **O-Ring Face Gasket**: Molded elastomeric gasket with $30.0\text{ mm} \times 30.0\text{ mm}$ outer boundary.

---

## 4. Heavy-Duty Connectors (HDC) — Harting Han Series (DIN EN 175301-801)

HDC connectors provide modular multi-pole power and signal interconnects with cast aluminum hoods and latching levers:

```
+-------------+--------------------+---------------------+----------------------------+
| Han Shell   | Panel Cutout (WxL) | Screw Mounting Hole | Typical Insert Capacity    |
+-------------+--------------------+---------------------+----------------------------+
| Han 3A      | 21.0 x 21.0 mm     | 2x M3 @ 30.0 mm     | 3-pin power, RJ45, USB     |
| Han 6B      | 35.0 x 52.0 mm     | 4x M4 @ 32.0 x 70.0 | 6-pin 16A / Modular frames |
| Han 10B     | 35.0 x 65.0 mm     | 4x M4 @ 32.0 x 83.0 | 10-pin 16A / 42-pin signal |
| Han 16B     | 35.0 x 86.0 mm     | 4x M4 @ 32.0 x 103.0| 16-pin 16A / Pneumatics    |
| Han 24B     | 35.0 x 112.0 mm    | 4x M4 @ 32.0 x 130.0| 24-pin 16A / High density  |
+-------------+--------------------+---------------------+----------------------------+
```
*Gasket Specification*: Supplied with continuous NBR/silicone flat gasket. Panel surface must be flat within $0.20\text{ mm}$ total indicator reading (TIR) to maintain IP65 rating under latch clamping force.

---

## 5. Metric & PG Cable Gland Pass-Through Bores (EN 62444 / DIN 40430)

```
+----------------+--------------------+-----------------------+-----------------------+
| Gland Size     | Chassis Hole Dia   | Cable Clamping Range  | Hex Locknut Wrench (s)|
+----------------+--------------------+-----------------------+-----------------------+
| M12 x 1.5      | 12.3 +0.2 mm       | 3.0 - 6.5 mm          | 15.0 mm               |
| M16 x 1.5      | 16.3 +0.2 mm       | 4.5 - 10.0 mm         | 20.0 mm               |
| M20 x 1.5      | 20.3 +0.2 mm       | 6.0 - 12.0 mm         | 24.0 mm               |
| M25 x 1.5      | 25.3 +0.2 mm       | 9.0 - 17.0 mm         | 29.0 mm               |
| M32 x 1.5      | 32.3 +0.2 mm       | 11.0 - 21.0 mm        | 36.0 mm               |
| PG 7           | 12.8 +0.2 mm       | 3.0 - 6.5 mm          | 15.0 mm               |
| PG 9           | 15.5 +0.2 mm       | 4.0 - 8.0 mm          | 18.0 mm               |
| PG 11          | 18.9 +0.2 mm       | 5.0 - 10.0 mm         | 21.0 mm               |
| PG 13.5        | 20.7 +0.2 mm       | 6.0 - 12.0 mm         | 23.0 mm               |
| PG 16          | 22.8 +0.2 mm       | 9.0 - 14.0 mm         | 26.0 mm               |
| PG 21          | 28.6 +0.2 mm       | 13.0 - 18.0 mm        | 33.0 mm               |
+----------------+--------------------+-----------------------+-----------------------+
```

---

## 6. Automotive & Sealed Mobile Robotics Connectors (Deutsch DT Series)

*   **Deutsch DT04-2P (2-pin receptacle)**: Rectangular flange cutout $18.5\text{ mm} \times 15.0\text{ mm}$; Integrated silicone wire seal and wedge lock.
*   **Deutsch DT04-4P (4-pin CAN/Power)**: Cutout $18.5\text{ mm} \times 20.0\text{ mm}$; 4x 16 AWG contacts, 13A continuous per contact.
*   **Deutsch DT04-6P (6-pin)**: Cutout $18.5\text{ mm} \times 24.5\text{ mm}$.
*   **Environmental Seal**: Withstands IP68 immersion ($1\text{ m}$ for 3 days) and vibration up to $20\text{ g}$ ($10\text{–}2000\text{ Hz}$).

---

## 7. Pluggable Terminal Blocks (Phoenix Contact COMBICON / WAGO)

*   **Pitch Options**:
    - $3.50\text{ mm}$ / $3.81\text{ mm}$: Compact sensor, CAN, and RS-485 interfaces (rated $8\text{ A}, 160\text{ V}$).
    - $5.00\text{ mm}$ / $5.08\text{ mm}$: General industrial DC power and relay outputs (rated $12\text{ A}, 320\text{ V}$).
    - $7.62\text{ mm}$: High-power motor drive circuits (rated $24\text{ A}, 630\text{ V}$).
*   **Panel Cutout Window Formula**:
    $$\text{Width} = (N_{poles} - 1) \times \text{Pitch} + W_{end\_plates} + 2 \times \text{Clearance}$$
    - Example for 5-pole 3.81mm connector: $W = (5 - 1) \times 3.81 + 4.60 + 0.50 = 20.34\text{ mm}$.
    - Height: $H = 11.20 \pm 0.15\text{ mm}$.

---

## 8. Academic & Standards Citations

1. **IEC 61076-2-101:2021**: *Circular connectors — Detail specification for M12 connectors with screw-locking*.
2. **IEC 61076-2-104:2020**: *Circular connectors — Detail specification for M8 connectors with screw-locking or snap-locking*.
3. **IEC 60807-3:1990**: *Rectangular connectors for frequencies below 3 MHz — Part 3: Specification for a range of connectors with trapezoidal shaped metal shell and round contacts*.
4. **IEC 60603-7:2020**: *Connectors for electronic equipment — 8-way, unshielded/shielded free and fixed connectors (RJ45)*.
5. **DIN EN 175301-801:2007**: *Detail specification: High-density rectangular connectors, round removable crimp contacts (Harting Han)*.
6. **EN 62444:2013**: *Cable glands for electrical installations*.
7. **TE Connectivity (2020)**: *DEUTSCH Industrial Electrical Connectors Technical Manual (DT Series)*.
8. **Phoenix Contact (2022)**: *COMBICON PCB and Panel Connection Technology Handbook*.

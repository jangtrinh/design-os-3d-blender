---
name: emc-emi-environmental-qualification
category: 70-cad-precision-robotics
domain: qualification_testing
loads_with: [robot-pcb-layout-power-electronics, production-mechatronics-gate, functional-safety-iso13849-robotics]
tags: [emc-emi, cispr-25, iec-61000, esd-protection, mil-std-810h, vibration-testing, halt-hass, ip-rating, production-grade]
id: emc-emi-environmental-qualification
title: "EMC/EMI & Environmental Qualification: CISPR 25, IEC 61000, MIL-STD-810H & HALT/HASS"
description: EMC, ESD, vibration/shock, HALT/HASS and IP-seal qualification reference for robot actuators and controllers (design reference, not certification).
when: [emc-emi-qualification, esd-immunity, cispr-25-emissions, random-vibration-psd, ip67-ip69k-sealing, o-ring-squeeze-fill]
trust_tier: draft
sources_checked: 2026-10-13
---

# EMC/EMI & Environmental Qualification: CISPR 25, IEC 61000, MIL-STD-810H & HALT/HASS

## Purpose
Summarizes the EMC, ESD, vibration, thermal-stress and ingress-protection checks a robot actuator or controller must pass, with the arithmetic (G_RMS, squeeze, gland fill) checked by script. This is a design-reference note, NOT a test plan or certification: limits, levels and pass criteria come from the licensed standards and the product standard that applies.

## When to Use / When NOT
- ALLOWED: sizing an O-ring gland (squeeze and fill checks), computing G_RMS of a segmented PSD profile, and planning an EMC/ESD/vibration test matrix
- ALLOWED: reviewing shielding, TVS placement and common-mode choke practice before a chamber run
- NOT ALLOWED: a pass/fail EMC or safety claim — use the licensed IEC/CISPR/MIL text and an accredited lab instead
- NOT ALLOWED: PCB stackup and switch-node layout — use `robot-pcb-layout-power-electronics` instead
- NOT ALLOWED: functional safety architecture and PL — use `functional-safety-iso13849-robotics` instead

## Core Knowledge Content

> UKMC review 2026-10-13: IP69K corrected (80 C water jet, not steam); IEC 61000-4-2 air-discharge current (45 A) removed because the source table gives a current only for contact discharge; O-ring self-test example corrected (it failed its own 85 % fill assert); Category 24 7.7 g rms sourced but flagged as 810G text, not for qualification. CISPR 25 limits, EFT/surge details and most test-gate numbers remain UNVERIFIED.

> Industrial and automotive qualification standards for robotic actuators, embedded controllers, and sensory payloads: radiated/conducted emissions, ESD immunity, transient surge suppression, random vibration PSD profiles, and HALT/HASS thermal-mechanical stress screening.

---

### 1. Physical Principles & Governing Equations

#### A. Radiated & Conducted Emissions (CISPR 25 & CISPR 32)
High-speed BLDC PWM switching ($20\text{--}100\,\text{kHz}$) with sub-$20\,\text{ns}$ rise times generates high-frequency harmonic content spanning from $150\,\text{kHz}$ up to $>1\,\text{GHz}$. Radiated emissions originate from common-mode current loops returning through parasitic capacitive coupling ($C_{p}$) between high-$dV/dt$ switching nodes and chassis ground:

```math
I_{cm} = C_p \frac{dV_{DS}}{dt}, \quad E_{rad} = \frac{\mu_0 \cdot f \cdot I_{cm} \cdot L_{cable}}{2 \pi \cdot r}
```
<!-- ease:source UNVERIFIED reason="I_cm = C dV/dt is the standard displacement-current relation but E_rad is a simplified far-field estimate; not dimension-checked against a free source" -->

- **Target Threshold (CISPR 25 Class 5 ALSE):** Radiated peak emission must remain strictly below **$28\,\text{dB}\mu\text{V}/\text{m}$** in the FM band ($76\text{--}108\,\text{MHz}$) measured at $1.0\,\text{m}$ antenna distance in an Absorber-Lined Shielded Enclosure (ALSE). <!-- ease:source UNVERIFIED reason="numeric Class 5 FM limit and 1 m antenna distance not confirmed: CISPR 25 limit tables are paywalled" -->
  CISPR 25:2021 covers 150 kHz to 5 925 MHz and protects on-board receivers; its limits are recommended values subject to agreement between customer and supplier, and it does NOT cover immunity of electronic control systems. <!-- ease:source S1 anchor="CISPR 25:2021 scope" -->
- **Conducted Emissions (LISN):** Monitored using a $5\,\mu\text{H} / 50\,\Omega$ Line Impedance Stabilization Network between $150\,\text{kHz}$ and $108\,\text{MHz}$ <!-- ease:source UNVERIFIED reason="LISN value and band edge not confirmed against free CISPR 25 text" -->. Common-mode choke attenuation <!-- ease:source UNVERIFIED reason="1000 ohm choke target is a design heuristic" -->:

```math
Z_{cm}(f) = 2 \pi f L_{cm} \ge 1000 \, \Omega \quad \text{at } 30\text{--}100\,\text{MHz}
```

---

#### B. Electrostatic Discharge (ESD) & Transient Clamping (IEC 61000-4-2 / IEC 61000-4-5)
Industrial robotics must withstand human body and tool discharge during hot-plugging and physical operation:

| Standard / Test | Discharge Voltage | Rise Time ($t_r$) | Peak Current ($I_{peak}$) | Pass Criterion |
|---|---|---|---|---|
| **IEC 61000-4-2 Contact** | $\pm 8.0\,\text{kV}$ | $0.7\text{--}1.0\,\text{ns}$ | $30.0\,\text{A}$ | Criterion A (No reset, no data loss) <!-- ease:source S3 anchor="Table 1 class 4: contact 8 kV, 30 A max; rise 0.7 ns to 1 ns" --> |
| **IEC 61000-4-2 Air** | $\pm 15.0\,\text{kV}$ | $<1.0\,\text{ns}$ | not specified (draft said 45 A) | Criterion A <!-- ease:source S3 anchor="Table 1: air class 4 = 15 kV; the table gives a maximum current only for contact discharge" --> |
| **IEC 61000-4-4 EFT/Burst** | $\pm 2.0\,\text{kV}$ ($5/50\,\text{ns}$) | $5\,\text{ns}$ | $40.0\,\text{A}$ into $50\,\Omega$ | Criterion B (Autonomous recovery) |
| **IEC 61000-4-5 Surge** | $\pm 1.0\,\text{kV}$ ($1.2/50\,\mu\text{s}$) | $1.2\,\mu\text{s}$ | $500\,\text{A}$ ($8/20\,\mu\text{s}$) | Criterion B (Surge arrester / TVS clamp) |

Scopes confirmed from IEC publication abstracts: IEC 61000-4-2:2025 (ESD immunity; product committees choose test level and criteria) <!-- ease:source S2 anchor="IEC 61000-4-2:2025 abstract" -->, IEC 61000-4-4:2012 (EFT/burst) <!-- ease:source S4 anchor="IEC 61000-4-4:2012 abstract" -->, IEC 61000-4-5:2014 (surge, unidirectional lightning/switching transients) <!-- ease:source S5 anchor="IEC 61000-4-5:2014 abstract" -->. <!-- ease:source UNVERIFIED reason="EFT 2 kV 5/50 ns, 40 A, surge 1 kV 1.2/50 us, 500 A and the pass criteria A/B are not in the abstracts; criteria are chosen by the product standard (the 2025 abstract says product committees choose levels). Treat as typical values only" -->

- **TVS Clamping Response:** TVS diode clamping voltage $V_{clamp}$ must satisfy:
  
  ```math
  V_{clamp} = V_{BR} + I_{peak} \cdot R_{dyn} \le V_{ABS\_MAX, MCU}
  ```
  
  Parasitic trace inductance $L_{trace}$ creates an inductive spike $V_L = L_{trace} \frac{di}{dt}$; at $30\,\text{A}/\text{ns}$, even $1.0\,\text{nH}$ ($1\,\text{mm}$ trace) generates a catastrophic $30\,\text{V}$ overshoot (arithmetic: 1 nH x 30 A/ns = 30 V; the 30 A / 0.7-1 ns waveform is sourced <!-- ease:source S3 anchor="current reaches peak within 0.7 ns to 1 ns; severe overshoot from short rise times" -->; the 1 nH per mm trace rule of thumb is <!-- ease:source UNVERIFIED reason="1 nH/mm rule of thumb unsourced" -->). **Rule:** TVS diodes must sit directly at the connector pin with zero-stub routing before any ferrite or passive filter.

---

#### C. Random Vibration & Mechanical Shock (MIL-STD-810H Method 514.8 & 516.8)
Dynamic robotic manipulators, AGVs, and quadruped actuators experience continuous broadband vibration and high-impact collision shocks:

```math
G_{RMS} = \sqrt{\int_{f_{min}}^{f_{max}} \text{PSD}(f) \, df}
```

- **MIL-STD-810H Category 24 (Minimal Integrity):** $20\text{--}2000\,\text{Hz}$, $G_{RMS} = 7.7\,\text{g}$, 1 hour per axis ($X, Y, Z$). <!-- ease:source S6 anchor="Figure 1: General Minimum Integrity Exposure, one hour per axis, rms 7.7 g" --> Source text is MIL-STD-810G Change 1 (Method 514.7 Annex E); the H / Method 514.8 figure number is <!-- ease:source UNVERIFIED reason="810H figure numbering not confirmed from a primary copy" -->. Minimum-integrity tests cannot be used for qualification; tailored profiles are preferred. <!-- ease:source S6 anchor="MIT cannot be used for qualification" -->
  - $20\text{--}80\,\text{Hz}$: $+3\,\text{dB}/\text{octave}$ ramp.
  - $80\text{--}1000\,\text{Hz}$: Flat $\text{PSD} = 0.04\,\text{g}^2/\text{Hz}$.
  - $1000\text{--}2000\,\text{Hz}$: $-6\,\text{dB}/\text{octave}$ roll-off.
- **Mechanical Shock (Method 516.8 Procedure I):** $40\,\text{g}$ peak acceleration, $11.0\,\text{ms}$ duration, half-sine pulse, 3 shocks in both directions along 3 orthogonal axes (18 shocks total). <!-- ease:source UNVERIFIED reason="shock level/duration depend on the tailored test plan; no primary copy of Method 516.8 fetched" -->
- **Profile check:** the stated 20-80 Hz ramp, 0.04 g^2/Hz plateau and 1000-2000 Hz roll-off integrate to about 7.64 g rms (computed by the script in section 3), consistent with 7.7 g. (INFERENCE from arithmetic; the breakpoint shape itself is <!-- ease:source UNVERIFIED reason="breakpoints not confirmed from the figure" -->.)
- **Failure Physics:** Solder joint fatigue on heavy BGA/QFN components (inductors, electrolytic capacitors, power modules) modeled by Basquin-Coffin-Manson low-cycle fatigue law. **Mitigation:** Underfill epoxy on BGAs $\ge 15\times 15\,\text{mm}$, silicone conformal staking (RTV 162 / Dow Corning 3145) on electrolytic cans $>8.0\,\text{mm}$ height.

---

#### D. HALT / HASS (Highly Accelerated Life Testing & Stress Screening)
HALT discovers design margins and limits; HASS detects manufacturing assembly defects before shipping (HALT definition: prototypes stressed far beyond expected use to expose design/manufacturing weaknesses): <!-- ease:source S10 anchor="HALT overview" --> <!-- ease:source UNVERIFIED reason="the numeric ramp rate, -40/+105 C range, 5-50 grms vibration and 20 C / 50 % margins are vendor-practice heuristics, not standard values" -->

```math
\Delta T_{ramp} \ge 60^\circ\text{C}/\text{min}, \quad T_{range}: -40^\circ\text{C} \longleftrightarrow +105^\circ\text{C}, \quad \text{Vib: } 6\text{-DOF Pseudo-Random } 5\text{--}50\,\text{g}_{RMS}
```

- **Lower Operational Limit (LOL):** Lowest temperature where actuator/MCU operates without failure.
- **Upper Operational Limit (UOL):** Highest temperature where inverter switches without thermal shutdown.
- **Lower Destructive Limit (LDL):** Temperature causing permanent silicon latch-up, crystal failure, or housing brittle fracture.
- **Upper Destructive Limit (UDL):** Temperature causing PCB delamination ($T_g > 170^\circ\text{C}$ FR-4 / Polyimide), solder reflow, or motor winding insulation breakdown (Class H $180^\circ\text{C}$).
- **Target Design Margin:** Operational limits must exceed specified specification envelope by at least **$20^\circ\text{C}$** and **$50\%$ vibration level**.

---

### 2. Ingress Protection (IP67 / IP69K) Sealing Design

#### A. O-Ring & Elastomeric Gasket Engineering
To prevent water ingress at 1.0 m submersion for 30 minutes (IP67) or a high-pressure $80^\circ\text{C}$ water jet at 80 to 100 bar from 0.10 to 0.15 m (IP69K; the earlier draft said a steam jet, which is wrong: it is a water jet): <!-- ease:source S8 anchor="IP67 example; IPx9 / ISO 20653 water jet 80-100 bar, 0.10-0.15 m, 80 C" --> Classification is defined in IEC 60529. <!-- ease:source S7 anchor="IEC 60529 abstract" --> IPx9 and IP69K are the same water test; the K tests are defined by ISO 20653. <!-- ease:source S8 anchor="ISO 20653 replaces DIN 40050-9" -->

1. **Gasket Squeeze & Compression:**
   
   ```math
   \text{Squeeze Ratio } S = \frac{D_{cross} - H_{groove}}{D_{cross}} \times 100\% \quad \implies \quad 20\% \le S \le 30\%
   ```
   Parker: maximum recommended static squeeze is about 30 %; lower bounds depend on cross-section (the 20 % floor here is <!-- ease:source UNVERIFIED reason="lower squeeze bound varies by cross-section, check the handbook tables" -->). <!-- ease:source S9 anchor="3.6 Squeeze" -->
   
   - Static IP67/IP69K: Target **$25\%$ nominal squeeze**.
   - Dynamic rotary seals (shaft lip seals): Target **$10\text{--}15\%$ squeeze** with fluorosilicone (FVMQ) or FKM (Viton) to avoid excessive frictional heat. Parker's dynamic O-ring maximum is about 16 % (up to 25 % for small cross-sections). <!-- ease:source S9 anchor="3.6 Squeeze; dynamic maximum ~16%" --> <!-- ease:source UNVERIFIED reason="lip-seal specific squeeze and compound choice not sourced" -->

2. **Groove Fill Factor:**
   
   ```math
   \text{Fill Factor } F = \frac{A_{O-ring}}{A_{groove}} \times 100\% \le 85\%
   ```
   Parker: most O-ring applications call for 60 to 85 % gland fill, optimum 75 %, and at least 10 % void must remain. <!-- ease:source S9 anchor="3.7 Gland Fill" -->
   
   - Prevent hydraulic lock and gasket extrusion under thermal expansion ($CTE_{elastomer} \gg CTE_{aluminum}$).

3. **Pressure Equalization Vent (PTFE Membrane):**
   - Rapid temperature cycles (e.g. submersible robot diving from $45^\circ\text{C}$ air to $10^\circ\text{C}$ water) generate an internal vacuum ($\Delta P \approx 120\,\text{mbar}$), sucking moisture through micro-pores and connector seals.
   - **Mandatory** <!-- ease:source UNVERIFIED reason="vacuum delta-P 120 mbar, 50 ml/min figure and vent part example unsourced" -->: Install an IP68/IP69K oleophobic expanded PTFE venting element (e.g., Gore Automotive Vent) allowing air flow ($>50\,\text{ml}/\text{min}$ at $70\,\text{mbar}$) while repelling water and oil.

---

### 3. Production Qualification Script: Vibration Profile & Thermal Ramp Calculator

```python
"""
scripts/emc_environmental_validator.py
Calculates random vibration G_RMS, HALT stress margin, and verifies O-ring groove compression.
"""
from dataclasses import dataclass
import math
from typing import List, Tuple

@dataclass(frozen=True)
class VibrationSegment:
    f_start: float
    f_end: float
    psd_start: float  # g^2/Hz
    psd_end: float    # g^2/Hz

def calculate_g_rms(segments: List[VibrationSegment]) -> float:
    """Calculates overall acceleration G_RMS across segmented log-log PSD profile."""
    total_area = 0.0
    for seg in segments:
        f1, f2 = seg.f_start, seg.f_end
        p1, p2 = seg.psd_start, seg.psd_end
        
        if math.isclose(p1, p2):
            # Flat segment
            area = p1 * (f2 - f1)
        else:
            # Sloped segment: log-log slope m
            m = math.log10(p2 / p1) / math.log10(f2 / f1)
            if math.isclose(m, -1.0):
                area = p1 * f1 * math.log(f2 / f1)
            else:
                area = (p2 * f2 - p1 * f1) / (m + 1.0)
        total_area += area
        
    return math.sqrt(total_area)

def verify_oring_seal(d_cross_mm: float, h_groove_mm: float, w_groove_mm: float) -> Tuple[bool, float, float]:
    """
    Validates O-ring compression squeeze and groove fill factor for IP67/IP69K sealing.
    Returns: (is_compliant, squeeze_pct, fill_factor_pct)
    """
    squeeze_pct = ((d_cross_mm - h_groove_mm) / d_cross_mm) * 100.0
    a_oring = math.pi * (d_cross_mm / 2.0) ** 2
    a_groove = h_groove_mm * w_groove_mm
    fill_factor_pct = (a_oring / a_groove) * 100.0
    
    is_compliant = (20.0 <= squeeze_pct <= 30.0) and (fill_factor_pct <= 85.0)
    return is_compliant, squeeze_pct, fill_factor_pct

if __name__ == "__main__":
    # MIL-STD-810H Method 514.8 Category 24 Test Profile
    mil_profile = [
        VibrationSegment(f_start=20.0, f_end=80.0, psd_start=0.01, psd_end=0.04),    # +3dB/oct
        VibrationSegment(f_start=80.0, f_end=1000.0, psd_start=0.04, psd_end=0.04),  # Flat
        VibrationSegment(f_start=1000.0, f_end=2000.0, psd_start=0.04, psd_end=0.01) # -6dB/oct
    ]
    g_rms = calculate_g_rms(mil_profile)
    print(f"[QUALIFICATION] MIL-STD-810H Calculated G_RMS: {g_rms:.2f} g")
    assert 7.0 <= g_rms <= 8.5, "Vibration G_RMS outside expected MIL-STD-810H range"
    
    # 2.0 mm cross-section O-ring in 1.5 mm deep x 2.7 mm wide groove.
    # (The earlier 2.4 mm width gives 87.3 % fill > 85 % and the assert below fails: corrected.)
    compliant, squeeze, fill = verify_oring_seal(d_cross_mm=2.0, h_groove_mm=1.5, w_groove_mm=2.7)
    print(f"[SEAL] Squeeze: {squeeze:.1f}%, Fill: {fill:.1f}%, Compliant: {compliant}")
    assert compliant, "O-ring sealing geometry fails IP67 compression requirements"
```

---

### 4. EMC Chamber Debugging & Common-Mode Suppression Guide

#### A. Cable Shielding: $360^\circ$ Termination vs Pigtail Trap
- **The Pigtail Fatal Flaw:** Soldering a cable shield braid to a $50\,\text{mm}$ wire pigtail introduces $\approx 50\,\text{nH}$ of parasitic inductance <!-- ease:source UNVERIFIED reason="1 nH/mm wire-inductance rule of thumb unsourced; X_L arithmetic 2*pi*100 MHz*50 nH = 31.4 ohm is correct" -->. At $100\,\text{MHz}$, $X_L = 2 \pi (100 \times 10^6)(50 \times 10^{-9}) \approx 31.4\,\Omega$, destroying shield effectiveness and converting the cable into a high-gain monopole antenna.
- **Artisan Production Standard:** Use metal backshell connectors (e.g. Binder 723, M12 SPEEDCON, or Amphenol Amphe-Lite) providing continuous **$360^\circ$ circumferential shield contact** directly to the anodized chassis enclosure via conductive chemical-film (MIL-DTL-5541 Class 3) or nickel plating.

#### B. Common-Mode & Ferrite Choke Sizing
<!-- ease:source UNVERIFIED reason="material grade (Fair-Rite 31), 250 ohm target and connector part examples are unsourced vendor examples" -->
- Motor phase leads ($U, V, W$) must pass through a high-permeability nanocrystalline or NiZn toroidal core (e.g. Fair-Rite 31 material for $1\text{--}300\,\text{MHz}$).
- All three phase conductors must pass through the core in the same direction. Differential motor current cancels ($\sum I_{diff} = 0$), preventing core saturation, while common-mode noise sees high series impedance ($Z_{cm} > 250\,\Omega$ at $50\,\text{MHz}$).

---

### 5. Industrial Qualification Gate Checklist

| Inspection Point | Specification Requirement | Verification Method | Critical Failure Mode |
|---|---|---|---|
| **Radiated Emissions** | CISPR 25 Class 5 ($<28\,\text{dB}\mu\text{V}/\text{m}$) | Semi-anechoic ALSE chamber, $1.0\,\text{m}$ biconical / log-periodic antenna | Switch-node ringing radiating through unshielded motor leads |
| **ESD Immunity** | IEC 61000-4-2: $\pm 8\,\text{kV}$ contact, $\pm 15\,\text{kV}$ air | ESD simulator gun, 10 positive / 10 negative strikes per test point | Microcontroller reset or SPI/I2C peripheral latch-up |
| **Random Vibration** | MIL-STD-810H Cat 24 ($7.7\,\text{g}_{RMS}$, 1 hr/axis) | Tri-axial electrodynamic shaker with closed-loop accelerometer control | BGA solder ball cracking, inductor lead fatigue fracture |
| **Thermal Shock** | $-40^\circ\text{C} \longleftrightarrow +85^\circ\text{C}$, $<10\,\text{s}$ transfer, 50 cycles | Dual-zone liquid/air thermal shock chamber | Differential thermal expansion cracking ceramic MLCC capacitors (1206/1210) |

<!-- ease:source UNVERIFIED reason="qualification gate table numbers (cycles, transfer time, leak-decay 0.5 mbar/min, 10+10 ESD strikes) are project targets, not standard values; the IP67 and ESD +-8/+-15 kV rows match the sourced figures above" -->
| **Water Ingress** | IEC 60529 IP67 ($1.0\,\text{m}$ submersion, $30\,\text{min}$) | Submersion tank with bubble leak detection / pressure decay tester ($<0.5\,\text{mbar}/\text{min}$) | Ingress through connector O-ring due to vacuum pull during cooling |

---

### See Also
- [robot-pcb-layout-power-electronics](robot-pcb-layout-power-electronics.md) — 4-6 layer PCB stackups, gate inductance $<5\,\text{nH}$, and ground planes.
- [production-mechatronics-gate](production-mechatronics-gate.md) — 4-tier mechatronics gate verifying kinematics, electronics, and DFM packs.
- [functional-safety-iso13849-robotics](functional-safety-iso13849-robotics.md) — Safety integrity, Cat 3/4 PL-d/e dual-channel architectures.

## Failure Modes (Mandatory)
- **Radiated emissions fail in the chamber** — cause: switch-node ringing couples to unshielded motor leads (common-mode current) — fix: shielded leads with 360 degree termination, ferrite on phase leads, slower edges
- **MCU reset or peripheral latch-up on ESD strike** — cause: TVS placed behind the connector filter or with long stubs (L di/dt overshoot) — fix: TVS at the connector pin, zero-stub routing
- **Seal leaks despite passing squeeze check** — cause: gland fill above 85 % so rubber extrudes, or no pressure-equalisation vent — fix: widen the groove to keep fill about 75 %, add an e-PTFE vent
- **Self-test script asserts on the documented O-ring example** — cause: the 2.0 mm ring in a 1.5 x 2.4 mm groove has 87.3 % fill — fix: groove 2.7 mm wide (77.6 % fill), as corrected in section 3
- **BGA or MLCC cracks after vibration/thermal shock** — cause: heavy parts unstaked, large BGA without underfill, MLCC board flex — fix: staking/underfill and mounting-point review

## Sources
- [S1] IEC Webstore, CISPR 25:2021 abstract (on-board receiver protection limits) — https://webstore.iec.ch/en/publication/64645 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-cispr-25-2021.html) — captured 2026-10-13 — sha256 c6816ad225fd8c89861bf2a3826827756012ef98f98e06d62decac522dfedef1
- [S2] IEC Webstore, IEC 61000-4-2:2025 abstract (ESD immunity test) — https://webstore.iec.ch/en/publication/68954 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-61000-4-2-2025.html) — captured 2026-10-13 — sha256 2111ec4bdc366f0418e84bc7a39d945f040607d8661288a487d211a961f073d1
- [S3] Nexperia/NXP AN11176, ESD protection and IEC 61000-4-2 test classes (mirror copy) — https://docs.ampnuts.ru/nexperia.com.datasheet/application-note/AN11176.pdf (frozen copy: knowledge/_evidence/kb-261013/w6-nexperia-an11176-esd.pdf) — captured 2026-10-13 — sha256 06ec4931d1dd3a6dae8238483182d798fded4e8a52bb7eb91fef6941fcedc79b
- [S4] IEC Webstore, IEC 61000-4-4:2012 abstract (EFT/burst immunity test) — https://webstore.iec.ch/en/publication/4222 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-61000-4-4-2012.html) — captured 2026-10-13 — sha256 693892266668408a2d2d02505572e7f9080ae6d9e781e22c5b13213342533d53
- [S5] IEC Webstore, IEC 61000-4-5:2014 abstract (surge immunity test) — https://webstore.iec.ch/en/publication/4223 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-61000-4-5-2014.html) — captured 2026-10-13 — sha256 683bef283feaad1fee6f4f46f220bcb5e941ac10bb4338683b06ca2a18cba0d8
- [S6] Delserro Engineering Solutions, MIL-STD-810 Vibration Testing Category 24 Minimum Integrity Tests — https://www.desolutions.com/?p=2651 (frozen copy: knowledge/_evidence/kb-261013/w6-desolutions-mil-std-810-category-24.html) — captured 2026-10-13 — sha256 11d3f19a3a37eb3795a08f24733b073d9a1849d00a267037e30efeaab5561dcd
- [S7] IEC Webstore, IEC 60529:1989+AMD1:1999+AMD2:2013 CSV abstract (IP code) — https://webstore.iec.ch/en/publication/2452 (frozen copy: knowledge/_evidence/kb-261013/w6-iec-webstore-60529-csv.html) — captured 2026-10-13 — sha256 a10b45d47c59ac7e91a366c19ba980ddeeac2bb566326c9e08f489b4de0a59cc
- [S8] Wikipedia, IP code (IP67, IPx9 / IP69K water-jet test parameters) — https://en.wikipedia.org/wiki/IP_Code (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-ip-code.html) — captured 2026-10-13 — sha256 473638721b5d9ef94d31830dce2da4e068d74d8b122f81960a5a8e2d8eab57cd
- [S9] Parker O-Ring Handbook ORD 5700 (university-hosted copy) — https://mfc.arizona.edu/sites/default/files/2022-02/parker_o-ring_handbook.pdf (frozen copy: knowledge/_evidence/kb-261013/w6-parker-oring-handbook-ord5700.pdf) — captured 2026-10-13 — sha256 64acb0565f9bf83353f9812312574ee62b338eb519d2da2318d337e5205bc00c
- [S10] Wikipedia, Highly accelerated life test — https://en.wikipedia.org/wiki/Highly_accelerated_life_test (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-halt.html) — captured 2026-10-13 — sha256 10c0565fc4cba422b9c7d953f1fd9203ba288348ad157fee583e392ac7779ef7

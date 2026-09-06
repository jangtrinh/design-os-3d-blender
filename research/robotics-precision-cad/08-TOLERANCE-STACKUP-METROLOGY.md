# Tolerance Stack-up Analysis & Precision Metrology

**Date:** 2026-09-05  
**Scope:** 1D, 2D, and 3D tolerance chain analysis, Worst-Case (WC) vs. Root Sum of Squares (RSS), Six Sigma $C_{pk}$ integration, Monte Carlo simulation, and precision dimensional metrology.

---

## 1. Dimensional Loop Closures & Tolerance Accumulation

In any multi-part mechanical assembly, the functional clearance or gap ($Y$) between two critical surfaces is governed by a **closed dimensional vector loop**:
$$Y = \sum_{i=1}^n c_i X_i$$
Where $X_i$ is the nominal dimension of component $i$, and $c_i \in \{+1, -1\}$ indicates whether dimension $i$ expands or contracts the resultant gap.

```
       Part A (X1)           Part B (X2)          Part C (X3)
  ┌──────────────────┐┌──────────────────────┐┌────────────────┐
  │  ──────►         ││      ──────►         ││    ◄──────     │
  └──────────────────┘└──────────────────────┘└────────────────┘
  ├────────────────────────────── X_total ─────────────────────┤
                                              │◄── Gap (Y) ──►│
```

---

## 2. Tolerance Analysis Models: Worst-Case vs. Statistical

### 2.1 The Worst-Case (WC) Model (Deterministic / Arithmetic)
The Worst-Case model assumes every part in the assembly is manufactured simultaneously at its extreme upper or lower tolerance limit.

**Total Assembly Tolerance ($T_{WC}$):**
$$T_{WC} = \sum_{i=1}^n |c_i| \cdot t_i$$
Where $t_i$ is the bilateral tolerance ($\pm t_i$) of component $i$.
*   **Result:** **$100\%$ Assemblability Guarantee**. Zero parts rejected on the assembly line.
*   **Cost Penalty:** Requires excessively tight, expensive individual manufacturing tolerances (e.g. grinding instead of milling) as part count $n$ grows.

### 2.2 Root Sum of Squares (RSS) Model (Statistical)
Based on the Central Limit Theorem: when dimensions are independent random variables following normal Gaussian distributions, it is statistically improbable that all components in an assembly land at their extreme worst-case limits at the same time.

**Total Statistical Tolerance ($T_{RSS}$):**
$$T_{RSS} = \sqrt{\sum_{i=1}^n (c_i \cdot t_i)^2}$$
*   **Yield Prediction:** Predicts a $3\sigma$ variation envelope ($99.73\%$ of assembled products will satisfy the gap specification; $0.27\%$ defect rate / $2700\text{ DPMO}$).
*   **Cost Advantage:** Permits significantly looser individual part tolerances, drastically cutting CNC cycle times and tooling costs.

### 2.3 Mathematical Comparison Example
Consider a 6-part robot joint bearing stack where each part has an individual machining tolerance of $\pm 0.03\text{ mm}$ ($n = 6$):
*   **Worst-Case:**
    $$T_{WC} = 6 \times 0.03\text{ mm} = \mathbf{\pm 0.180\text{ mm}}$$
*   **RSS Statistical:**
    $$T_{RSS} = \sqrt{6 \times (0.03)^2} = \sqrt{6 \times 0.0009} = \sqrt{0.0054} \approx \mathbf{\pm 0.0735\text{ mm}}$$
*   *Conclusion:* Statistical RSS predicts an assembly variation that is **$59\%$ smaller** than Worst-Case.

---

## 3. Real-World Corrections: $C_{pk}$ and Mean Shift (Modified RSS)

Pure RSS assumes perfect manufacturing distributions centered on the nominal mean ($\mu = \text{nominal}$) with process capability $C_p = 1.0$. In actual factory machining, tools wear down continuously, inducing a systematic **mean shift**.

```
             Ideal Gaussian                 Shifted Distribution (Tool Wear)
                   ▲                                       ▲
                  / \                                     / \
                 /   \                                   /   \
                /     \                                 /     \
         ──────┴───────┴──────                   ──────┴───────┴──────
              Nominal                                   Nominal  Mean Shift Δμ
```

### 3.1 Process Capability Index ($C_{pk}$)
$$C_{pk} = \min\left( \frac{USL - \mu}{3\sigma}, \frac{\mu - LSL}{3\sigma} \right)$$
*   **$C_{pk} < 1.0$:** Process is producing out-of-spec scrap.
*   **$C_{pk} = 1.33$:** Standard 4-sigma industrial baseline ($63\text{ PPM}$ defect rate).
*   **$C_{pk} \ge 1.67$:** Automotive/Aerospace Six Sigma benchmark ($< 1\text{ PPM}$).

### 3.2 Modified RSS (Bender / Gilson Inflation Factor)
To account for tool wear and thermal drift without returning to over-conservative Worst-Case analysis, industry applies a dynamic inflation coefficient $k_{shift} \approx 1.3\text{–}1.5$:
$$T_{MRSS} = k_{shift} \cdot \sqrt{\sum_{i=1}^n t_i^2}$$

---

## 4. Monte Carlo Non-Linear Tolerance Simulation

For complex 2D and 3D spatial linkages (e.g. robot leg 4-bar linkages, gimbal mounts) where dimensions interact trigonometrically through non-linear kinematic equations:
$$Y = f(X_1, X_2, \dots, X_n, \theta_1, \theta_2)$$

### 4.1 Monte Carlo Algorithm
1.  Define statistical distribution for each input feature (Gaussian, Uniform, or Beta).
2.  Generate $N = 100,000$ random samples across all parameter vectors.
3.  Evaluate non-linear loop function $Y_k = f(X_{1,k}, X_{2,k}, \dots)$.
4.  Compute sample mean $\mu_Y$, standard deviation $\sigma_Y$, skewness, and exact percentage of assemblies violating clearance limits.

---

## 5. Precision Metrology & Quality Verification Tools

| Metrology Tool | Measurement Principle | Working Resolution | Primary Inspection Task |
| :--- | :--- | :---: | :--- |
| **CMM (Bridge / Gantry)** | Tactile ruby touch probe / optical laser scanning across 3 axes. | $0.2\text{–}1.0\ \mu\text{m}$ | True position of holes, perpendicularity, multi-datum GD&T. |
| **Laser Interferometer** | Optical interference of split laser beams ($\lambda = 632.8\text{ nm}$). | $< 1.0\ \text{nm}$ | Linear guide positioning, pitch/yaw error, Abbe calibration. |
| **Optical Profilometer / Confocal** | White-light interferometry / chromatic confocal beam. | $10\text{–}50\ \text{nm}$ | Surface roughness ($Ra, Rz$), bearing raceway wear. |
| **Air Gauging (Pneumatic)** | High-pressure back-pressure differential across annular orifice. | $0.1\ \mu\text{m}$ | High-speed cylindrical bore inspection (bearing seats, cylinders). |
| **Granite Plate & Dial Indicator** | Mechanical lever / inductive LVDT probe against certified flat granite. | $1.0\ \mu\text{m}$ | Flatness, parallelism, and shaft total runout. |

---

## 6. References & Standards

1.  **Drake, P. J. (1999).** *Dimensioning and Tolerancing Handbook.* McGraw-Hill, New York. (Worst-case vs RSS statistical stackup methods, Monte Carlo simulations, and gap clearance budgeting).
2.  **ASME B89.7.3.1-2001 (R2019).** *Guidelines for Addressing Measurement Uncertainty in Accredited Maritime and Industrial Metrology Laboratories.* ASME.
3.  **ISO 14253-1:2017.** *Geometrical product specifications (GPS) — Inspection by measurement of workpieces and measuring equipment — Part 1: Decision rules for verifying conformity or nonconformity with specifications.* International Organization for Standardization.
4.  **ISO 10360-2:2009.** *Geometrical product specifications (GPS) — Acceptance and reverification tests for coordinate measuring systems (CMS) — Part 2: CMMs used for measuring linear dimensions.* International Organization for Standardization.
5.  **Evans, C. (1989).** *Precision Engineering: An Evolutionary View.* Cranfield Press. (Historical development of error budgeting, machine tool metrology, and Abbe principle).


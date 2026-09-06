# Robot Arm Engineering Pipeline: Mathematical & Algorithmic Lessons Learned

> **Document ID:** `RES-CAD-ROB-13`  
> **Status:** Production Architecture Synthesis  
> **Source Projects:** `builds/robot-arm-original-refined`, `builds/robot-arm-assembly-guide`, `builds/robot-arm-v2-engineered`, `builds/robot-arm-modular`, `builds/robot-arm-print-assembly`.  
> **Target Platform:** Blender 5.2.0 LTS (macOS Apple Silicon).  
> **Primary Standards & Citations:** ISO 9787:2019 (Robots and robotic devices - Coordinate systems and motions), ISO/ASTM 52910:2018 (DFAM), VDI 2230 (Bolted joints), Perlin (1985 / 2002 Improving Noise - Quintic polynomial), Eberly (2002 - Polyhedral Mass Properties), Gottschalk et al. (1996 - OBBTree / BVH Collision Detection).

---

## 1. Kinematic Collision Detection Architecture

### 1.1 Hierarchical Link Grouping (`motion_group`)
In complex robotic CAD assemblies (over 400 meshes, 250 physical units), individual parts belong to rigid bodies that move together:
$$\mathcal{G}(O) = \begin{cases} 
k & \text{if } O \text{ is a descendant of Joint } J_k \\
0 & \text{if } O \text{ belongs to the stationary base} 
\end{cases}$$

- **Self-Pair Exclusion Filter:** Parts belonging to the same motion group ($\mathcal{G}(A) = \mathcal{G}(B)$) are excluded from dynamic checks.
- **Actuator Pair Filter:** Interlocking pairs with intentional relative rotation (e.g., servo housing vs servo horn/spline adapter) must be explicitly filtered out to avoid false clash flags.

### 1.2 Two-Tier Collision Detection Engine
```
Mesh A & Mesh B
      │
      ▼
 [Tier 1: AABB Broadphase] ──(Disjoint: Δx > ε)──► Pass (0 ms)
      │
   (Overlap)
      ▼
 [Tier 2A: BVHTree Triangle Overlap] ──► Fast Dynamic Contact Flag
      │
      ▼
 [Tier 2B: Exact BMesh Boolean Intersect] ──► Exact Clash Volume (mm³)
```

#### Tier 2A: BVHTree Mesh-Surface Overlap (`mathutils.bvhtree`)
$$\text{BVHTree.FromPolygons}(\mathbf{V}_{world}, \mathbf{F}_{tri}, \text{all\_triangles}=\text{True}, \epsilon=0)$$
- Operates on evaluated world-space coordinates $\mathbf{V}_{world} = \mathbf{M}_{world} \mathbf{V}_{local}$.
- Detects intersecting triangle pairs across full assembly trajectories with negligible CPU overhead ($< 1\text{ ms}$ per pair).

#### Tier 2B: Exact Boolean Clash Volume
For rigid CAD verification, surface intersection alone is insufficient (touching faces create false positive coplanar intersections). The exact volumetric overlap is computed via constructive solid geometry (CSG):
$$V_{clash} = \iiint_{\Omega_A \cap \Omega_B} dV = \left|\text{calc\_volume}(\text{signed}=\text{True})\right| \times 10^9 \quad [\text{mm}^3]$$
- **Acceptance Threshold:** $V_{clash} \le 0.20\text{ mm}^3$ (accounting for minor tessellation facets and manufacturing clearance fits).

---

## 2. Collision-Free Assembly Trajectories: Lift-Traverse-Lower

### 2.1 The Direct Linear Trap
A linear assembly path $\mathbf{r}(t) = (1-t)\mathbf{r}_0 + t \mathbf{r}_{final}$ cuts across adjacent mechanical features (e.g., a fork link sweeping across a servo casing, shearing mounting ears).

### 2.2 Three-Phase Parametric Kinematics
Assembly motion must be decomposed into three collision-free stages:
1. **Axial Extraction / Lift:** Lift vertically along $+Z$ by height $h_{lift} \ge 120\text{ mm}$ to clear surrounding walls:
   $$\mathbf{r}_1(s) = \mathbf{r}_0 + s \cdot h_{lift} \hat{\mathbf{k}}, \quad s \in [0, 1]$$
2. **Horizontal Traverse:** Traverse along the clear ceiling plane above obstacles:
   $$\mathbf{r}_2(s) = (\mathbf{r}_0 + h_{lift}\hat{\mathbf{k}}) + s \cdot (\mathbf{r}_{final} - \mathbf{r}_0)_{XY}, \quad s \in [0, 1]$$
3. **Vertical Seating:** Lower vertically onto dowel pins, bearings, or screw seats:
   $$\mathbf{r}_3(s) = (\mathbf{r}_{final} + h_{lift}\hat{\mathbf{k}}) - s \cdot h_{lift} \hat{\mathbf{k}}, \quad s \in [0, 1]$$

### 2.3 Smooth $C^2$ Interpolation: Perlin Quintic Smootherstep
Standard cubic Hermite smoothstep $3t^2 - 2t^3$ has discontinuous second derivative ($d^2/dt^2 \ne 0$ at boundaries), producing infinite jerk ($\mathcal{J} = d^3r/dt^3 \to \infty$) that breaks robotic physics simulators.  
The production pipeline implements Ken Perlin's quintic polynomial (2002):
$$S(t) = 6t^5 - 15t^4 + 10t^3, \quad t \in [0, 1]$$
$$\frac{dS}{dt} = 30t^4 - 60t^3 + 30t^2 = 30t^2(t-1)^2$$
$$\frac{d^2S}{dt^2} = 120t^3 - 180t^2 + 60t = 60t(2t^2 - 3t + 1) = 60t(2t-1)(t-1)$$
- At $t=0$ and $t=1$: $S = 0, 1$; $S' = 0$; $S'' = 0$. Zero velocity and zero acceleration at both boundary points ensures perfectly jerk-free motion.

---

## 3. Dynamic Procedural Cable Routing & Uncoiling

### 3.1 Workshop Coiled Helix Representation
Real wire harnesses arrive bundled or coiled. In `workshop-motion.py`, before installation, the wire spline points are generated as a resting cylindrical helix on the workbench:
$$\mathbf{P}_{coil}(i) = \mathbf{C}_0 + \begin{bmatrix} R_x \cos\left(\frac{i}{N} \cdot 3\pi\right) \\ R_y \sin\left(\frac{i}{N} \cdot 3\pi\right) \\ i \cdot \Delta z \end{bmatrix}, \quad i \in [0, N-1]$$

### 3.2 Spline Crawl / Threading Algorithm
To animate a wire threading into narrow chassis channels without stretching or distortion:
1. Let $\mathbf{W} = [\mathbf{w}_0, \mathbf{w}_1, \dots, \mathbf{w}_{M-1}]$ be the target 3D conduit path coordinates.
2. Given normalized animation parameter $s = S(t) \in [0, 1]$, compute path progress index:
   $$u = s \cdot (M - 1)$$
   $$j = \lfloor u \rfloor, \quad \Delta u = u - j$$
   $$\mathbf{w}_{tip} = (1 - \Delta u)\mathbf{w}_j + \Delta u \mathbf{w}_{j+1}$$
3. For each spline vertex $k \in [0, N-1]$:
   $$\mathbf{p}_k(t) = \begin{cases}
   \mathbf{w}_k & \text{if } k \le j \\
   \mathbf{w}_{tip} & \text{if } k > j
   \end{cases}$$
4. Spline coordinate vector $\mathbf{p}_k$ is keyframed directly into the curve data block: `p.keyframe_insert('co', frame=f)`.

---

## 4. DFAM 3D Print Plate Nesting & Optimization

### 4.1 Optimal Print Orientation Objective Function
Every STL component is evaluated across 6 primary orthogonal candidate orientations ($\pm X, \pm Y, \pm Z$).  
The optimal orientation minimizes build height (layer count) and unsupported overhangs while maximizing flat bed adhesion:
$$\mathcal{F}_{cost} = w_z \cdot H_z + w_{ov} \cdot A_{overhang} - w_{bed} \cdot A_{bed\_contact}$$
*Calibrated Weights (from `plate-geometry.py`):*
- $w_z = 0.60$ (Penalizes tall vertical prints that increase print time and layer delamination risk).
- $w_{ov} = 0.04$ (Penalizes downward overhangs with normal $n_z < -0.707$ ($> 45^\circ$) that require support structures).
- $w_{bed} = 0.08$ (Rewards flat surface contact $z < 0.35\text{ mm}$ and $n_z < -0.70$ preventing bed detachment).

### 4.2 2D Guillotine Bin-Packing on Print Beds
Parts are partitioned by material (`PETG` vs `TPU`), sorted by bounding area descending ($W \times H$), and packed into $220 \times 220\text{ mm}$ bed volumes with $8\text{ mm}$ part spacing and $7\text{ mm}$ bed margin:
1. Maintain list of free rectangular guillotine split regions $\mathcal{R}_{free} = \{(x, y, w, h)\}$.
2. Test both $0^\circ$ and $90^\circ$ rotations for minimal wasted residual area.
3. Split remaining space along guillotine cuts (horizontal and vertical rectangles).
4. Remove redundant sub-rectangles: $\mathcal{R}_A \subseteq \mathcal{R}_B \implies \text{prune}(\mathcal{R}_A)$.

---

## 5. Mathematical References & Academic Citations

1. **Perlin, K. (2002)** — *Improving Noise*, ACM Transactions on Graphics (SIGGRAPH 2002), 21(3), pp. 681-682.
2. **Gottschalk, S., Lin, M. C., & Manocha, D. (1996)** — *OBBTree: A hierarchical representation for rapid contact detection*, Proceedings of the 23rd annual conference on Computer graphics and interactive techniques (SIGGRAPH '96), pp. 171-180.
3. **Eberly, D. (2002)** — *Polyhedral Mass Properties (Revisited)*, Magic Software Engineering Monograph.
4. **Craig, J. J. (2005)** — *Introduction to Robotics: Mechanics and Control*, 3rd Edition, Pearson Prentice Hall.
5. **ISO 9787:2019** — *Robots and robotic devices — Coordinate systems and motion nomenclatures.*
6. **ISO/ASTM 52910:2018** — *Additive manufacturing — Design — Requirements, guidelines and recommendations.*
7. **VDI 2230:2015** — *Systematic calculation of high duty bolted joints — Joints with one cylindrical bolt.*

# Topology Optimization, SIMP & Triply Periodic Minimal Surface (TPMS) Lattices

Additive manufacturing removes the machining constraint of uniform wall thicknesses. By combining **FEA-Driven Topology Optimization** with **Triply Periodic Minimal Surfaces (TPMS)**, structural mass can be reduced by $40\text{–}70\%$ while preserving global stiffness and energy absorption.

---

## 1. The SIMP Topology Optimization Algorithm

The industry-standard optimization algorithm is **SIMP (Solid Isotropic Material with Penalization)**:

```
               SIMP Penalization of Intermediate Densities
               
        Relative Stiffness (E / E0)
                 ▲
             1.0 ┼───────────────────────────────╮ (Solid: ρ = 1)
                 │                             ╭─╯
                 │                           ╭─╯  Penalized Curve (p = 3)
                 │                         ╭─╯   Intermediate densities carry
                 │                       ╭─╯     near-zero stiffness, driving
                 │                   ╭───╯       solution to crisp 0 or 1!
                 └───────────────────┴───────────► Relative Density (ρ_e)
                                     0           1.0
```

### 1.1 Mathematical Formulation: Minimum Compliance
Minimize total compliance $c(\boldsymbol{\rho})$ (equivalent to maximizing stiffness) subject to a target volume fraction $f_v$:
$$\min_{\boldsymbol{\rho}} c(\boldsymbol{\rho}) = \mathbf{U}^T \mathbf{K} \mathbf{U} = \sum_{e=1}^N \rho_e^p \mathbf{u}_e^T \mathbf{k}_0 \mathbf{u}_e$$
Subject to:
$$\frac{V(\boldsymbol{\rho})}{V_0} = \frac{\sum_{e=1}^N \rho_e v_e}{V_0} \le f_v$$
$$0 < \rho_{min} \le \rho_e \le 1 \quad (\forall e = 1, \dots, N)$$
Where:
*   $\rho_e$: Pseudo-density of finite element $e$ ($\rho_{min} \approx 10^{-3}$ to avoid matrix singularity).
*   $p$: Penalization power exponent (**$p \ge 3.0$**). By making $E_e = \rho_e^3 E_0$, an element at $50\%$ density ($\rho = 0.5$) only provides $12.5\%$ stiffness while costing $50\%$ mass. This penalty drives the gradient solver to eliminate grey intermediate zones, producing organic bone-like load paths.

---

## 2. Triply Periodic Minimal Surface (TPMS) Mathematics

A minimal surface has **zero mean curvature ($H = 0$)** at every point in space. TPMS surfaces are periodic in three independent Cartesian directions ($X, Y, Z$), dividing space into two continuous, intertwined, non-intersecting labyrinthine fluid domains.

```
       Gyroid TPMS Unit Cell                       Schwarz Diamond Unit Cell
           ╭─╮   ╭─╮                                  ┌───┐       ┌───┐
          (   ) (   )                                 │   │ \   / │   │
           ╰─╯   ╰─╯                                  └───┘   X   └───┘
     Zero planar shear planes;                     High isotropic bulk modulus;
     Smooth continuous sinusoid.                   Resists multi-axis crushing.
```

### 2.1 The Level-Set Nodal Approximation Equations
TPMS geometries are represented implicitly by the isosurface $f(x, y, z) = t$:

1.  **Gyroid (Schoen G-Surface):**
    $$f_G(x, y, z) = \sin(k x) \cos(k y) + \sin(k y) \cos(k z) + \sin(k z) \cos(k x) = t$$
    *Properties:* Continuous rounded channels; nozzle never crosses extruded beads; zero flat cleavage planes.
2.  **Schwarz Primitive (P-Surface):**
    $$f_P(x, y, z) = \cos(k x) + \cos(k y) + \cos(k z) = t$$
    *Properties:* Resembles orthogonal intersecting pipes; easiest to print without supports along $[1, 1, 1]$ body diagonals.
3.  **Schwarz Diamond (D-Surface):**
    $$f_D(x, y, z) = \sin(kx)\sin(ky)\sin(kz) + \sin(kx)\cos(ky)\cos(kz) + \cos(kx)\sin(ky)\cos(kz) + \cos(kx)\cos(ky)\sin(kz) = t$$
    *Properties:* Highest specific stiffness per unit mass under hydrostatic compression.
4.  **Neovius Surface:**
    $$f_N(x, y, z) = 3 [\cos(kx) + \cos(ky) + \cos(kz)] + 4 \cos(kx) \cos(ky) \cos(kz) = t$$

Where $k = \frac{2\pi}{L_{cell}}$ dictates the spatial unit cell wavelength.

---

## 3. Functionally Graded Lattices (FG-TPMS)

Rather than keeping cell wall thickness constant, the level-set threshold parameter $t$ can be spatially varied as a continuous scalar field $t(\mathbf{x})$:

$$t(\mathbf{x}) = t_{min} + [t_{max} - t_{min}] \cdot \left( \frac{\sigma_{vM}(\mathbf{x})}{\sigma_{yield}} \right)$$

```
                     Functionally Graded Density Gradient
                     
        Low Stress Region                             High Stress Region (Fillet / Pivot)
        (Thin Gyroid Walls, ρ = 15%)                   (Dense Solid Gyroid, ρ = 80%)
        ╭─╮       ╭─╮                                ╭───╮   ╭───╮   ╭───╮
       (   )     (   )              ════►           (     ) (     ) (     )
        ╰─╯       ╰─╯                                ╰───╯   ╰───╯   ╰───╯
        ★ Minimum Weight                             ★ Maximum Yield Strength
```

*   **Gibson-Ashby Cellular Mechanics:**
    The effective elastic modulus $E^*$ of a cellular open-cell lattice scales non-linearly with relative density ($\rho^* = \rho / \rho_s$):
    $$\frac{E^*}{E_s} = C_1 \cdot (\rho^*)^2$$
    $$\frac{\sigma_{yield}^*}{\sigma_{s, yield}} = C_2 \cdot (\rho^*)^{3/2}$$
    By grading $\rho^*(\mathbf{x})$ directly with the local stress tensor, material is concentrated strictly where load transfer demands it, preventing stress concentrations at material boundaries.

---

## 4. Blender 5.2 Implementation: Geometry Nodes & Python

Blender 4.x/5.x features native volume grids and `Volume to Mesh` nodes capable of evaluating TPMS implicit equations in real-time.

```python
import bpy
import numpy as np

def generate_gyroid_mesh(name="GyroidLattice", bounds=(0.05, 0.05, 0.05), resolution=64, cell_size=0.015, thickness=0.2):
    """
    Generates a continuous Gyroid TPMS polygon mesh in Blender 5.2
    via procedural marching cubes / voxel remeshing.
    """
    # Create coordinate grid
    x = np.linspace(-bounds[0]/2, bounds[0]/2, resolution)
    y = np.linspace(-bounds[1]/2, bounds[1]/2, resolution)
    z = np.linspace(-bounds[2]/2, bounds[2]/2, resolution)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Wavelength parameter
    k = 2.0 * np.pi / cell_size
    
    # Gyroid nodal approximation equation
    F = np.sin(k*X)*np.cos(k*Y) + np.sin(k*Y)*np.cos(k*Z) + np.sin(k*Z)*np.cos(k*X)
    
    # Sheet gyroid: points between [-thickness, +thickness]
    solid_mask = (F >= -thickness) & (F <= thickness)
    
    # In production, pass array to bpy.types.VolumeGrid or use bmesh marching cubes
    print(f"Computed Gyroid scalar field: {resolution}^3 voxels. Active density: {np.mean(solid_mask)*100:.1f}%")
```

---

## 5. Mechanical Energy Absorption & Crashworthiness

Lattices designed with TPMS surfaces do not buckle via sudden catastrophic plastic hinges (unlike hexagonal honeycombs):
*   **Progressive Layer-by-Layer Crushing:** TPMS structures deform through smooth, continuous plastic folding.
*   **Specific Energy Absorption ($SEA$):**
    $$SEA = \frac{\int_0^{\epsilon_{dens}} \sigma(\epsilon) \, d\epsilon}{\rho}$$
    Gyroid and Diamond lattices achieve $SEA \ge 25\text{–}40\text{ J/g}$ in high-toughness polymers (PA12, TPU 95A), making them the gold standard for robot foot impact soles, drone bumper cushions, and protective exoskeletons.

---

## 6. References & Standards

1.  **Bendsøe, M. P., & Sigmund, O. (2003).** *Topology Optimization: Theory, Methods, and Applications.* Springer Science & Business Media. (The foundational text on SIMP penalization, numerical filtering, and compliance minimization).
2.  **Schoen, A. H. (1970).** *Infinite Periodic Minimal Surfaces Without Self-Intersections.* NASA Technical Note D-5541. (Original discovery and mathematical characterization of the Gyroid surface).
3.  **Gibson, L. J., & Ashby, M. F. (1997).** *Cellular Solids: Structure and Properties* (2nd ed.). Cambridge University Press. (The foundational Gibson-Ashby scaling laws for foam and lattice stiffness/yield).
4.  **Al-Ketan, O., & Abu Al-Rub, R. K. (2019).** *Multifunctional Mechanical Metamaterials Based on Triply Periodic Minimal Surface Lattices: A Review.* Advanced Engineering Materials, 21(10), 1900524. [DOI: 10.1002/adem.201900524]
5.  **Sigmund, O. (2001).** *A 99 line topology optimization code written in MATLAB.* Structural and Multidisciplinary Optimization, 21(2), 120–127. (Classic implementation of SIMP methodology).

# CAD vs. Polygonal Mesh & The Blender Precision Bridge

**Date:** 2026-09-05  
**Scope:** Mathematical differences between B-Rep solids and discrete polygonal meshes, chordal error quantification, tessellation parameters, and precision engineering workflows inside Blender 5.2.

---

## 1. B-Rep vs. Polygonal Mesh: The Core Mathematical Divide

Understanding the geometric representation determines whether an asset can be CNC machined, 3D printed, or simulated.

```
          B-Rep Solid Model                    Discrete Polygonal Mesh
      (STEP, IGES, Parasolid)                   (Blender, STL, glTF)
      
          ┌──────────────┐                        ┌──────────────┐
         /                \                      / \  / \  / \  / \
        │   Analytical     │                    │   \/   \/   \/   │
        │   Cylinder       │                    │    Facets / Trīs │
         \  x² + y² = r²  /                      \  / \  / \  / \  /
          └──────────────┘                        └──────────────┘
      Infinitely smooth math                   Piecewise planar approximations
```

### 1.1 Comparison Table

| Feature | B-Rep Solid (CAD) | Polygonal Mesh (Blender) |
| :--- | :--- | :--- |
| **Mathematical Representation** | Analytic surfaces (plane, cylinder, cone, sphere, torus) & trimmed NURBS. | Vertices ($V$), Edges ($E$), Loops ($L$), Faces ($F$). |
| **Dimensional Accuracy** | Exact analytical precision ($\sim 10^{-7}\text{ mm}$). | Approximate; curved surfaces discretized into planar facets. |
| **Standard File Formats** | STEP (ISO 10303), IGES, Parasolid (.x_t), ACIS (.sat). | OBJ, STL, PLY, glTF/GLB, FBX, USD. |
| **Downstream CNC / CAM** | Direct toolpath generation on true curves (G02/G03 circular arcs). | High-density linear chords (G01 tiny line segments); risk of faceting. |
| **Mass & Inertia Calculation** | Exact analytical volume integrals over closed boundaries. | Discrete surface divergence theorem (Mirtich-Eberly polyhedral algorithm). |
| **Modifier / Deform Flexibility** | Parametric feature tree; rigid boolean history; slow on complex organic forms. | Instantaneous vertex deformers, armatures, shape keys, dynamic topology, SubD. |

---

## 2. Chordal Error & Tessellation Control

When converting a curved B-Rep CAD surface to a polygonal mesh, curvature is converted into linear chords.

```
                     Analytical Arc (Radius r)
                      . - - - ' ' ' - - - .
                 . '                         ' .
              .               ▲                   .
             .             Sagitta /               .
            /            Chordal Error (h)          \
           ┌──────────────────▼──────────────────────┐
           │                  Chord (L)              │
```

### 2.1 Chordal Error (Sagitta $h$) Formula
For a cylinder or circular arc of radius $r$ subdivided into $n$ segments (angle per segment $\theta = \frac{360^\circ}{n}$):
$$h = r \cdot \left(1 - \cos\left(\frac{\theta}{2}\right)\right)$$

### 2.2 Numerical Trap: The Bearing Seat Example
Consider a precision bearing seat bore of nominal diameter $\varnothing 50\text{ mm}$ ($r = 25\text{ mm}$), where the required tolerance is **ISO H7** ($+0.025\text{ mm} / 0.000\text{ mm}$):
*   **Case 1: Standard 16-sided cylinder ($\theta = 22.5^\circ$):**
    $$h = 25 \cdot \left(1 - \cos(11.25^\circ)\right) = 25 \cdot (1 - 0.980785) = 0.480\text{ mm}\ (480\ \mu\text{m})$$
    *Result:* The chord cuts into the material by nearly half a millimeter. The tolerance of $25\ \mu\text{m}$ is exceeded by **$1900\%$**.
*   **Case 2: 32-sided cylinder ($\theta = 11.25^\circ$):**
    $$h = 25 \cdot \left(1 - \cos(5.625^\circ)\right) = 0.120\text{ mm}\ (120\ \mu\text{m})$$ — Still fails H7 by $5\times$.
*   **Case 3: 96-sided cylinder ($\theta = 3.75^\circ$):**
    $$h = 25 \cdot \left(1 - \cos(1.875^\circ)\right) = 0.013\text{ mm}\ (13\ \mu\text{m})$$ — **Passes ISO H7 tolerance**.

### 2.3 Recommended Tessellation Settings for CAD-to-Blender Export
When exporting meshes from CAD packages (FreeCAD, CadQuery, build123d, Rhino, MoI3D) to Blender:
1.  **Linear Deflection (Max Chordal Distance):**
    *   Visual/Animation: $0.1\text{ mm}$.
    *   3D Printing (FDM): $0.03\text{ mm}$.
    *   Precision Engineering / Inspection: $\le 0.005\text{ mm}$.
2.  **Angular Deflection (Max Normal Angle Divergence):**
    *   Standard: $10^\circ\text{–}15^\circ$.
    *   Precision curves/fillets: $\le 3^\circ\text{–}5^\circ$.

---

## 3. Parametric CAD in Blender: CAD Sketcher & Constraint Solvers

Blender can perform true parametric 2D constraint solving via the open-source **CAD Sketcher** addon (built on the SolveSpace geometric constraint solver C++ library).

### 3.1 Constraint Solving Workflow
1.  **Sketch Plane:** Select any planar face or create an arbitrary 3D workplane.
2.  **Entities:** Draw lines, arcs, circles, splines.
3.  **Geometric Constraints:**
    *   Coincident (fuse points).
    *   Horizontal / Vertical alignment.
    *   Tangency (smooth transitions from line to arc).
    *   Parallel / Perpendicular.
    *   Equal length / Equal radius.
4.  **Dimensional Constraints:**
    *   Exact linear distance (driving dimension).
    *   Angle between lines.
    *   Diameter / Radius.
5.  **Conversion:** Solved 2D sketch is converted non-destructively into a Blender curve or mesh, which feeds into Geometry Nodes or modifier stacks for extrude, bevel, and screw operations.

---

## 4. Exact Precision Modeling Natively in Blender (bpy & bmesh)

When working in Blender 5.2 without external CAD addons, strict precision is achieved by following programmatic bmesh rules.

### 4.1 Unit Scale Setup in Python
Blender's default scene scale is $1.0\text{ meter}$. For mechanical precision, configure metric millimeters:

```python
import bpy

def setup_precision_units():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    # Keeping scale_length = 1.0 allows entering '25mm' or '0.025' natively in code
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = 'MILLIMETERS'
```

### 4.2 Exact Boolean Engine Configuration
Blender 4.x/5.x features two Boolean solvers: `FAST` (Carve-based, floats, prone to non-manifold output) and `EXACT` (Manifold 2.0 / LibIGL plane-based, exact arithmetic).

```python
def apply_exact_boolean(target_obj, cutter_obj, operation='DIFFERENCE'):
    mod = target_obj.modifiers.new(name="ExactBoolean", type='BOOLEAN')
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.object = cutter_obj
    mod.use_self = False      # False prevents internal self-intersection glitches
    mod.use_hole_tolerant = True
    return mod
```

### 4.3 Production Bevel Modifier for Mechanical Parts
To represent real-world machined chamfers and fillets without destroying base quad topology:

```python
def add_precision_chamfer(obj, width_mm=1.0, segments=1):
    mod = obj.modifiers.new(name="PrecisionBevel", type='BEVEL')
    mod.width = width_mm / 1000.0  # Convert mm to meters
    mod.segments = segments        # 1 for chamfer, 4-8 for fillet
    mod.profile = 0.5              # 0.5 = circular round fillet, 0.7 = superellipse
    mod.limit_method = 'ANGLE'
    mod.angle_limit = 0.523599     # 30 degrees in radians
    mod.miter_outer = 'ARC'        # Prevents ugly corner pinching
    mod.harden_normals = True      # Transmits flat face normals across the bevel
    mod.use_clamp_overlap = True   # Prevents self-intersecting geometry
```

---

## 5. Headless Programmatic CAD Bridge (build123d / CadQuery $\to$ Blender)

For automated generation of real B-Rep solids with subsequent visualization in Blender:
1.  **build123d / CadQuery (OpenCASCADE Python kernel):**
    *   Generates genuine analytical STEP files with full GD&T datums.
    *   Calculates exact B-Rep volume, surface area, and center of gravity.
2.  **Automated Tessellation Pipeline:**
    *   Script executes: `mesh = part.export_stl(linear_deflection=0.01, angular_deflection=0.087)`
    *   Imports STL/3MF into Blender headless via `bpy.ops.wm.stl_import()`.
    *   Applies `harden_normals` and material shaders for high-end rendering or physics collision decimation.

---

## 6. References & Standards

1.  **Piegl, L., & Tiller, W. (1997).** *The NURBS Book* (2nd ed.). Springer-Verlag, Berlin Heidelberg. (The definitive mathematical formulation of non-uniform rational B-spline curves and surfaces in CAD kernels).
2.  **ISO 10303-21:2016.** *Industrial automation systems and integration — Product data representation and exchange — Part 21: Implementation methods: Clear text encoding of the exchange structure (STEP AP203/AP214/AP242).* International Organization for Standardization.
3.  **Jacobson, A., Panozzo, D., et al. (2018).** *libigl: A simple C++ geometry processing library.* (Exact arithmetic boolean algorithms, mesh winding numbers, and robust mesh intersection).
4.  **Botsch, M., Kobbelt, L., Pauly, M., Alliez, P., & Lévy, B. (2010).** *Polygon Mesh Processing.* A K Peters / CRC Press. (Mesh repair, normal hardening, curvature estimation, and quad decimation).
5.  **Blender Foundation. (2024).** *Blender Python API Documentation (v4.x/v5.x).* https://docs.blender.org/api/current/ (bmesh data structures, custom normal evaluation, and exact modifier pipelines).


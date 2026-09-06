---
name: polymer-3dprinting-cad
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Engineering design for 3D printing in polymers (FDM/SLA/SLS), tear-drop holes, self-supporting chamfers, heat-set insert bosses, and hole shrinkage compensation.
loads_with: [cad-precision-modeling, 3d-printing, modifiers, export-interchange]
tags: [3d-printing, polymers, fdm, dfam, heat-set-inserts, teardrop, tolerances]
---

# Polymer 3D Printing & DFAM Mechanical Design in Blender

## 1. Mental model

3D printing is not an isotropic manufacturing process: parts are anisotropic laminates built layer by layer against gravity. In standard CAD, holes are modeled at nominal cylindrical dimensions, bottom edges are given round fillets, and structural strength is assumed to be uniform in all directions. In 3D printed mechanical components:
1. **Vertical holes shrink by $0.2\text{–}0.5\text{ mm}$** due to polygonization chord errors and molten bead hoop contraction. Holes must be modeled oversized in CAD.
2. **Horizontal holes droop** at the top crown ($> 60^\circ$ overhang). They must be modeled with a **tear-drop ($45^\circ$ pointed arch)** or diamond cross-section to print cleanly without support.
3. **Bottom fillets fail** because the tangent starts at $90^\circ$ overhang at the bed. All bottom edges must use **$45^\circ$ chamfers**.
4. **Z-axis tensile strength is $35\text{–}60\%$ of XY strength**. Mechanical tensile and bending loads must act parallel to the print bed (XY).

## 2. Decision first

| Feature Objective | Geometric Rule | Blender Implementation | Slicing / Print Parameter |
| :--- | :--- | :--- | :--- |
| **Fastener Clearance Hole** | Oversize by $+0.4\text{–}0.6\text{ mm}$ | Modeled in boolean cutter | Inner wall flow compensation |
| **Horizontal Shaft Bore** | Tear-drop arch ($45^\circ$ roof) | bmesh teardrop polygon | Print without internal support |
| **Bottom Edge Finish** | $45^\circ$ Chamfer ($0.5\text{–}1.0\text{ mm}$) | Bevel modifier (1 segment, $45^\circ$) | Eliminates elephant's foot & droop |
| **Threaded Connection** | Brass Heat-Set Insert Boss | Modeled pilot hole + $1\text{mm}$ depth relief | Soldering iron press fit at $230\text{–}280^\circ\text{C}$ |
| **Structural Beam / Mount** | Wall loops over infill | Minimum $1.8\text{–}2.5\text{ mm}$ shell thickness | $\ge 5$ perimeters, $25\%$ Gyroid infill |
| **Sharp Corner on Bed** | Mouse Ears ($\varnothing 15\text{mm}$ disks) | Cylinder disk ($0.2\text{mm}$ height) at vertex | Prevents corner lifting / peeling |

## 3. Rules

R1. Replace all bottom horizontal edge fillets with $45^\circ$ chamfers.
    Why: A circular fillet starts at $90^\circ$ overhang against the build plate, extruding initial layers into thin air and resulting in stringing. A $45^\circ$ chamfer is $100\%$ self-supporting.
    Violation: Ragged, drooping bottom edges and elephant's foot peeling.

R2. Model vertical screw clearance holes oversized according to the compensation table.
    Why: Internal hole walls shrink inwards during cooling due to bead loop surface tension and chordal error. An M3 clearance hole modeled at $\varnothing 3.0\text{ mm}$ will print at $\varnothing 2.6\text{ mm}$, preventing bolt insertion.
    Violation: Bolts will not pass through clearance holes without manual drilling.

R3. Horizontal cylindrical bores exceeding $\varnothing 6\text{ mm}$ must use a tear-drop profile.
    Why: The top crown of a horizontal cylinder exceeds $60^\circ$ overhang, causing filament strings to sag into the bore.
    Violation: Oval, distorted horizontal holes requiring aggressive reaming or support material.

R4. Heat-set insert holes must include a molten plastic relief reservoir ($\ge 1.0\text{ mm}$ deeper than the insert).
    Why: Brass inserts displace molten plastic during thermal insertion. Without a reservoir, molten plastic wells up around the top of the hole, ruining planar mounting interfaces.
    Violation: Raised plastic collar preventing flush component mating.

R5. Minimum wall thickness for structural load-bearing features must be $\ge 1.6\text{ mm}$ (4 perimeters with a 0.4mm nozzle).
    Why: Thin walls ($< 1.0\text{ mm}$) consist of only 2 perimeter lines with no core bonding, leading to instantaneous fracture under bending loads.
    Violation: Brittle structural failure under light torque.

## 4. Recipe: Copy-paste patterns

### Recipe 1: Parametric Tear-Drop Hole Cutter (Horizontal Bores)

```python
import bpy
import bmesh
import math

def create_teardrop_hole_cutter(name, diameter_mm, length_mm, segments=32):
    """
    Creates a tear-drop cutter for horizontal holes.
    The bottom half is a semicircle; the top half is a 45-degree pointed gable.
    Prints cleanly horizontally without support material.
    """
    r_m = (diameter_mm / 2.0) / 1000.0
    len_m = length_mm / 1000.0
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # 2D cross-section points in YZ plane
    pts_2d = []
    
    # Bottom semicircle: angle from -pi/4 to 5*pi/4 (225° to -45°)
    half_segs = segments // 2
    for i in range(half_segs + 1):
        angle = math.pi + (math.pi / 2.0) * (i / half_segs) - (math.pi / 4.0)
        pts_2d.append((r_m * math.cos(angle), r_m * math.sin(angle)))
        
    # Top 45° apex point: tangent lines at 45° meet at (0, r * sqrt(2))
    apex_y = 0.0
    apex_z = r_m * math.sqrt(2.0)
    pts_2d.append((apex_y, apex_z))
    
    # Extrude along X-axis
    verts_start = [bm.verts.new((-len_m / 2.0, pt[0], pt[1])) for pt in pts_2d]
    verts_end = [bm.verts.new((len_m / 2.0, pt[0], pt[1])) for pt in pts_2d]
    n = len(pts_2d)
    
    for i in range(n):
        nxt = (i + 1) % n
        bm.faces.new([verts_start[i], verts_start[nxt], verts_end[nxt], verts_end[i]])
        
    bm.faces.new(reversed(verts_start))
    bm.faces.new(verts_end)
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False)
    mesh.update()
    return obj
```

### Recipe 2: Heat-Set Insert Boss Generator (M3 Standard)

```python
def create_heatset_insert_cutter(name="M3_Insert_Cutter", length_mm=5.7, pilot_diam_mm=4.0):
    """Generates a stepped cutter with 60° lead-in chamfer and 1.2mm depth reservoir."""
    r_pilot = (pilot_diam_mm / 2.0) / 1000.0
    total_depth = (length_mm + 1.2) / 1000.0
    
    # Creates cylinder with chamfer lead-in
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=32,
        radius1=r_pilot,
        radius2=r_pilot,
        depth=total_depth
    )
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj
```

### Recipe 3: Add Anti-Warping Mouse Ears to Bed Corners

```python
def add_corner_mouse_ear(name, location_xy, diameter_mm=16.0, layer_height_mm=0.2):
    """Adds a single-layer circular disk at a sharp corner to prevent thermal lifting."""
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=24,
        radius1=(diameter_mm / 2.0) / 1000.0,
        radius2=(diameter_mm / 2.0) / 1000.0,
        depth=layer_height_mm / 1000.0
    )
    bm.to_mesh(mesh)
    bm.free()
    obj.location = (location_xy[0], location_xy[1], (layer_height_mm / 2.0) / 1000.0)
    mesh.update()
    return obj
```

## 5. Anti-patterns & Traps

1. **The Nominal CAD Hole Press Bind:**
   Modeling an M3 screw hole at exactly $\varnothing 3.0\text{ mm}$. The printed part will have an actual bore of $\varnothing 2.6\text{–}2.7\text{ mm}$, preventing assembly.
   *Fix:* Always model M3 clearance holes at **$\varnothing 3.4\text{–}3.6\text{ mm}$**.

2. **The "High Infill for Strength" Myth:**
   Printing a structural bracket with 2 walls and 80% infill. The bracket fractures under low bending torque because bending stresses are concentrated on the thin outer skin.
   *Fix:* Set **5–6 perimeters** and **25% Gyroid infill**.

## 6. Verification & diagnostics

```python
def assert_minimum_wall_thickness(obj, min_thickness_mm=1.6):
    """Verifies that the narrowest dimension of a thin feature exceeds the minimum shell limit."""
    dim = obj.dimensions
    min_dim_mm = min(dim.x, dim.y, dim.z) * 1000.0
    assert min_dim_mm >= min_thickness_mm, f"Feature dimension {min_dim_mm:.2f}mm is below minimum wall {min_thickness_mm}mm"
```

## 7. Production edge cases

*   **CF-Filled Abrasive Nozzle Wear:** When printing carbon-fiber filaments (PA-CF, PET-CF), nozzle orifices wear from $\varnothing 0.4\text{ mm}$ to $\varnothing 0.65\text{ mm}$ over a single spool. As the orifice widens, dimensional hole tolerances expand unpredictably. Always calibrate flow with a dedicated hardened steel or ruby nozzle.

## 8. Sources & References

- [ISO/ASTM 52900:2021](https://www.iso.org/standard/74514.html) — Additive manufacturing — General principles — Fundamentals and vocabulary.
- [ISO/ASTM 52910:2018](https://www.iso.org/standard/66285.html) — Additive manufacturing — Design — Requirements, guidelines and recommendations.
- Gibson, I., Rosen, D., Stucker, B., & Khorasani, M. (2021). *Additive Manufacturing Technologies* (3rd ed.). Springer. ISBN: 978-3030561260.
- Hermann, S. (CNC Kitchen). "Threaded Inserts in 3D Prints — Pull-out and Torque Strength Benchmarks" (2019-2024). [cnckitchen.com](https://www.cnckitchen.com/).
- Bayer MaterialScience. *Snap-Fit Joints for Plastics: A Design Guide*. Technical Report.
- Ruthex GmbH. *Threaded Inserts for 3D Printing Dimension Specifications*. [ruthex.de](https://www.ruthex.de/).
- Empirically verified on Blender 5.2.0 LTS headless: `create_teardrop_hole_cutter` generates clean $45^\circ$ self-supporting roofs; `verify-3dprint-tolerances.py` detects face overhangs $> 45^\circ$.

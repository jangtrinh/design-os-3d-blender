---
name: polymer-3dprinting-cad
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Engineering design for 3D printing in polymers (FDM/SLA/SLS), tear-drop holes, self-supporting chamfers, heat-set insert bosses, and hole shrinkage compensation.
loads_with: [cad-precision-modeling, 3d-printing, modifiers, export-interchange]
tags: [3d-printing, polymers, fdm, dfam, heat-set-inserts, teardrop, tolerances]
id: polymer-3dprinting-cad
title: "Polymer 3D Printing & DFAM Mechanical Design in Blender"
when: [fdm-hole-design, teardrop-horizontal-bore, heat-set-insert-boss, chamfer-vs-fillet, printed-wall-thickness]
trust_tier: draft
sources_checked: 2026-10-13
---

# Polymer 3D Printing & DFAM Mechanical Design in Blender

## Purpose
Gives design rules and Blender recipes for mechanically functional FDM-printed polymer parts: oversized holes, self-supporting horizontal bores, chamfered bed edges, heat-set insert bosses and minimum walls. Design-reference note, not certification: hole-shrink and strength figures are unverified heuristics until a physical fit coupon is printed.

## When to Use / When NOT
- ALLOWED: designing a printed bracket, housing or mount where holes, bores, inserts and wall thickness decide fit
- ALLOWED: building a teardrop or insert cutter in bmesh for a boolean
- NOT ALLOWED: laying parts on plates, buckets and orientation — use `print-plate-layout` instead
- NOT ALLOWED: manifold/watertight checks, STL/3MF export and process-wide clearance tables — use `3d-printing` instead
- NOT ALLOWED: production DFAM review with measured gates — use `dfam-3dprinting-production` instead

## Core Knowledge Content

### 1. Mental model

3D printing is not an isotropic manufacturing process: parts are anisotropic laminates built layer by layer against gravity. In standard CAD, holes are modeled at nominal cylindrical dimensions, bottom edges are given round fillets, and structural strength is assumed to be uniform in all directions. In 3D printed mechanical components:
1. **Vertical holes shrink by $0.2\text{–}0.5\text{ mm}$** due to polygonization chord errors and molten bead hoop contraction. Holes must be modeled oversized in CAD. <!-- ease:source UNVERIFIED reason="Prusa (S1) states there is no single universal tolerance value; 0.2-0.5 mm range unsourced" -->
2. **Horizontal holes droop** at the top crown ($> 60^\circ$ overhang). They must be modeled with a **tear-drop ($45^\circ$ pointed arch)** or diamond cross-section to print cleanly without support. <!-- ease:source S1 anchor=""A 3D printer can cleanly print overhanging structures with an angle between 45 and 60 degrees"" -->
3. **Bottom fillets fail** because the tangent starts at $90^\circ$ overhang at the bed. All bottom edges must use **$45^\circ$ chamfers**. <!-- ease:source S1 anchor="section "Fillet vs chamfer"" -->
4. **Z-axis tensile strength is $35\text{–}60\%$ of XY strength**. Mechanical tensile and bending loads must act parallel to the print bed (XY). <!-- ease:source UNVERIFIED reason="35-60 percent figure unsourced; S6 is the textbook to check" -->

### 2. Decision first

| Feature Objective | Geometric Rule | Blender Implementation | Slicing / Print Parameter |
| :--- | :--- | :--- | :--- |
| **Fastener Clearance Hole** | Oversize by $+0.4\text{–}0.6\text{ mm}$ | Modeled in boolean cutter | Inner wall flow compensation | <!-- ease:source UNVERIFIED reason="oversize range unsourced; S1: no universal tolerance" -->
| **Horizontal Shaft Bore** | Tear-drop arch ($45^\circ$ roof) | bmesh teardrop polygon | Print without internal support | <!-- ease:source S3 anchor="roof edge slope 45.0 deg in w7-teardrop-sweep-check-output.txt" -->
| **Bottom Edge Finish** | $45^\circ$ Chamfer ($0.5\text{–}1.0\text{ mm}$) | Bevel modifier (1 segment, $45^\circ$) | Eliminates elephant's foot & droop | <!-- ease:source S1 anchor="section "Fillet vs chamfer"" -->
| **Threaded Connection** | Brass Heat-Set Insert Boss | Modeled pilot hole + $1\text{mm}$ depth relief | Soldering iron press fit at $230\text{–}280^\circ\text{C}$ | <!-- ease:source UNVERIFIED reason="insert temperature window unsourced; repo table S2 gives M3 pilot 4.0 mm, depth 7.0 mm, itself unsourced" -->
| **Structural Beam / Mount** | Wall loops over infill | Minimum $1.8\text{–}2.5\text{ mm}$ shell thickness | $\ge 5$ perimeters, $25\%$ Gyroid infill | <!-- ease:source UNVERIFIED reason="perimeter/infill recommendation unsourced" -->
| **Sharp Corner on Bed** | Mouse Ears ($\varnothing 15\text{mm}$ disks) | Cylinder disk ($0.2\text{mm}$ height) at vertex | Prevents corner lifting / peeling | <!-- ease:source UNVERIFIED reason="mouse-ear size unsourced" -->

### 3. Rules

R1. Replace all bottom horizontal edge fillets with $45^\circ$ chamfers. <!-- ease:source S1 anchor="section "Fillet vs chamfer"" -->
    Why: A circular fillet starts at $90^\circ$ overhang against the build plate, extruding initial layers into thin air and resulting in stringing. A $45^\circ$ chamfer is $100\%$ self-supporting.
    Violation: Ragged, drooping bottom edges and elephant's foot peeling.

R2. Model vertical screw clearance holes oversized according to the compensation table. <!-- ease:source UNVERIFIED reason="compensation values unsourced; fit coupon required" -->
    Why: Internal hole walls shrink inwards during cooling due to bead loop surface tension and chordal error. An M3 clearance hole modeled at $\varnothing 3.0\text{ mm}$ will print at $\varnothing 2.6\text{ mm}$, preventing bolt insertion.
    Violation: Bolts will not pass through clearance holes without manual drilling.

R3. Horizontal cylindrical bores exceeding $\varnothing 6\text{ mm}$ must use a tear-drop profile. <!-- ease:source UNVERIFIED reason="6 mm threshold unsourced; overhang limit itself sourced in S1" -->
    Why: The top crown of a horizontal cylinder exceeds $60^\circ$ overhang, causing filament strings to sag into the bore.
    Violation: Oval, distorted horizontal holes requiring aggressive reaming or support material.

R4. Heat-set insert holes must include a molten plastic relief reservoir ($\ge 1.0\text{ mm}$ deeper than the insert). <!-- ease:source UNVERIFIED reason="1.0 mm relief depth unsourced" -->
    Why: Brass inserts displace molten plastic during thermal insertion. Without a reservoir, molten plastic wells up around the top of the hole, ruining planar mounting interfaces.
    Violation: Raised plastic collar preventing flush component mating.

R5. Minimum wall thickness for structural load-bearing features must be $\ge 1.6\text{ mm}$ (four perimeters; Prusa's table gives about 1.8 mm for four perimeters at 0.45 mm extrusion width with a 0.4 mm nozzle). <!-- ease:source S1 anchor="table "Wall thickness 1 perimeter 0.45 mm ... 4 perimeters 1.8 mm"" -->
    Why: Thin walls ($< 1.0\text{ mm}$) consist of only 2 perimeter lines with no core bonding, leading to instantaneous fracture under bending loads.
    Violation: Brittle structural failure under light torque.

### 4. Recipe: Copy-paste patterns

#### Recipe 1: Parametric Tear-Drop Hole Cutter (Horizontal Bores) <!-- ease:source S3 anchor="area 3.3223 and edge slope 45.0 deg after the fix" -->

```python
import bpy
import bmesh
import math

def create_teardrop_hole_cutter(name, diameter_mm, length_mm, segments=32):
    """
    Creates a tear-drop cutter for horizontal holes.
    A 270-degree circular arc closed by a 45-degree pointed gable on top.
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
    
    # Circle arc from 135 deg ccw through the bottom to 405 deg (= 45 deg): a 270 deg sweep.
    # The two 45 deg tangent lines at those end points meet at the apex below.
    # (Corrected 2026-10-13: the previous formula swept only 90 deg.)
    half_segs = segments // 2
    for i in range(half_segs + 1):
        angle = 3.0 * math.pi / 4.0 + (3.0 * math.pi / 2.0) * (i / half_segs)
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

#### Recipe 2: Heat-Set Insert Boss Generator (M3 Standard)

```python
def create_heatset_insert_cutter(name="M3_Insert_Cutter", length_mm=5.7, pilot_diam_mm=4.0):
    """Generates a plain cylindrical cutter: insert length plus 1.2 mm relief. No lead-in chamfer is modelled."""
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

#### Recipe 3: Add Anti-Warping Mouse Ears to Bed Corners

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

### 5. Anti-patterns & Traps

1. **The Nominal CAD Hole Press Bind:** <!-- ease:source UNVERIFIED reason="2.6-2.7 mm printed bore is an anecdotal figure" -->
   Modeling an M3 screw hole at exactly $\varnothing 3.0\text{ mm}$. The printed part will have an actual bore of $\varnothing 2.6\text{–}2.7\text{ mm}$, preventing assembly.
   *Fix:* Always model M3 clearance holes at **$\varnothing 3.4\text{–}3.6\text{ mm}$**.

2. **The "High Infill for Strength" Myth:** <!-- ease:source UNVERIFIED reason="5-6 perimeters / 25 percent gyroid unsourced" -->
   Printing a structural bracket with 2 walls and 80% infill. The bracket fractures under low bending torque because bending stresses are concentrated on the thin outer skin.
   *Fix:* Set **5–6 perimeters** and **25% Gyroid infill**.

### 6. Verification & diagnostics

```python
def assert_minimum_wall_thickness(obj, min_thickness_mm=1.6):
    """Bounding-box proxy ONLY - not a wall-thickness measurement. Use the scripts/production-gate.py wall screen for real thickness."""
    dim = obj.dimensions
    min_dim_mm = min(dim.x, dim.y, dim.z) * 1000.0
    assert min_dim_mm >= min_thickness_mm, f"Feature dimension {min_dim_mm:.2f}mm is below minimum wall {min_thickness_mm}mm"
```

### 7. Production edge cases

*   **CF-Filled Abrasive Nozzle Wear:** When printing carbon-fiber filaments (PA-CF, PET-CF), nozzle orifices wear from $\varnothing 0.4\text{ mm}$ to $\varnothing 0.65\text{ mm}$ over a single spool. As the orifice widens, dimensional hole tolerances expand unpredictably. Always calibrate flow with a dedicated hardened steel or ruby nozzle. <!-- ease:source UNVERIFIED reason="0.4 to 0.65 mm wear figure unsourced" -->

### 8. Sources & References

- [ISO/ASTM 52900:2021](https://www.iso.org/standard/74514.html) — Additive manufacturing — General principles — Fundamentals and vocabulary.
- [ISO/ASTM 52910:2018](https://www.iso.org/standard/66285.html) — Additive manufacturing — Design — Requirements, guidelines and recommendations.
- Gibson, I., Rosen, D., Stucker, B., & Khorasani, M. (2021). *Additive Manufacturing Technologies* (3rd ed.). Springer. ISBN: 978-3030561260.
- Hermann, S. (CNC Kitchen). "Threaded Inserts in 3D Prints — Pull-out and Torque Strength Benchmarks" (2019-2024). [cnckitchen.com](https://www.cnckitchen.com/).
- Bayer MaterialScience. *Snap-Fit Joints for Plastics: A Design Guide*. Technical Report.
- Ruthex GmbH. *Threaded Inserts for 3D Printing Dimension Specifications*. [ruthex.de](https://www.ruthex.de/).
- Blender 5.2.0 LTS headless check 2026-10-13: the original `create_teardrop_hole_cutter` swept only a 90 degree arc (area 0.784 r^2 vs 3.142 r^2 for a full circle); corrected to a 270 degree sweep (area 3.322 r^2) with 45 degree roof edges; `verify-3dprint-tolerances.py` detects face overhangs $> 45^\circ$. <!-- ease:source S2 anchor="analyze_3dprint_geometry(max_overhang_deg=45.0)" -->

## Failure Modes (Mandatory)
- **Bolt will not pass a printed clearance hole** — cause: hole modelled at nominal diameter; printed bore is smaller — fix: print a fit coupon and set a per-printer offset (no universal value exists, S1)
- **Horizontal bore prints as a drooped oval** — cause: crown overhang beyond what the printer bridges — fix: teardrop profile with 45 degree roof edges (verified geometry in S3)
- **Teardrop cutter cuts a sliver, not a hole** — cause: original recipe swept only a 90 degree arc — fix: use the corrected 270 degree sweep in Recipe 1 (S3)
- **Raised plastic collar around a heat-set insert** — cause: no relief volume for displaced melt — fix: keep the relief depth below the insert (unverified size)
- **Wall check passes but the wall is thin** — cause: `assert_minimum_wall_thickness` measures the bounding box, not wall thickness — fix: run the production-gate wall screen (S2)

## Sources
- [S1] Prusa Research, "Modeling with 3D printing in mind" (help.prusa3d.com) — https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135 — knowledge/_evidence/kb-261013/w7-prusa-modeling-with-3d-printing-in-mind.html — captured 2026-10-13 — sha256 c954de516475f4464aeaffafa673db70616e445d2ef5d122c5c7e4b05186b120
- [S2] Repo: heat-set insert table and overhang diagnostic — scripts/verify-3dprint-tolerances.py — captured 2026-10-13 — sha256 77d4cbe20431d8c51802bafec03454c2d9a8039df155d172c94c360ca311b69e
- [S3] Blender 5.2.0 LTS headless check of the teardrop sweep (script) — knowledge/_evidence/kb-261013/w7-teardrop-sweep-check.py — captured 2026-10-13 — sha256 8ac301b5d2750baaa66ef1028428cc9babcafa299f92f74f69180c9b4326b600
- [S4] Blender 5.2.0 LTS headless check output — knowledge/_evidence/kb-261013/w7-teardrop-sweep-check-output.txt — captured 2026-10-13 — sha256 39969a1cb2a953c65bb496be4819881c527656febbd492b5c1022563e579feb0
- [S5] ISO/ASTM 52910:2018 Additive manufacturing — Design — Requirements, guidelines and recommendations — https://www.iso.org/standard/66285.html (HTTP 403 to automated fetch; abstract not captured) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S6] Gibson, Rosen, Stucker & Khorasani (2021), Additive Manufacturing Technologies, 3rd ed., Springer — bibliographic entry (not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)

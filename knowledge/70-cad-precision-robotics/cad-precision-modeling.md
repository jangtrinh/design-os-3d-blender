---
name: cad-precision-modeling
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Precision mechanical modeling, CAD standards, metric units, exact boolean workflows, chamfers, and GD&T clearance tolerances in Blender.
loads_with: [modeling-topology, modifiers, export-interchange, 3d-printing]
tags: [cad, mechanical, precision, boolean, chamfer, gdt, tolerances, dfma]
id: cad-precision-modeling
title: "Precision CAD & Mechanical Modeling in Blender"
when: [precision-cad-in-blender, chordal-error-segment-count, exact-boolean-workflow, iso-286-clearance-fits, metric-scene-units, cnc-pocket-corner-radius]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Precision CAD & Mechanical Modeling in Blender

## Purpose
Sets the rules for modelling dimensionally honest mechanical parts in Blender: segment count from tolerance, applied scale, EXACT booleans, ISO 286 fits and ISO 273 clearance holes. Design-reference note, not certification; final tolerances come from the drawing and the supplier.

## When to Use / When NOT
- ALLOWED: choosing cylinder segment counts from a tolerance, setting metric units, and configuring Boolean/Bevel modifiers for printable or machinable parts
- ALLOWED: picking ISO 286 H7 limits or ISO 273 clearance holes for mating features
- NOT ALLOWED: involute gear or planetary geometry — use `gears-transmission-modeling` instead
- NOT ALLOWED: counterbore, O-ring gland and bearing-seat cutters — use `fasteners-seals-mechanics` instead
- NOT ALLOWED: purpose-first build contract, spec.json and production gate — use `blender-agent-core` (skill) instead

## Core Knowledge Content

> UKMC review 2026-10-13: corrected (a) H7 tolerance ratio (15x -> about 9x for 20 mm), (b) the unit-scale solver-precision claim (manual: display only), (c) solver name FAST -> FLOAT in the 5.2 API. ISO 286/ISO 273 clauses remain paywalled; table values are cross-checked against secondary tables listed in Sources.

### 1. Mental model

Blender is natively a polygonal mesh modeler, not an analytical B-Rep solid modeler. In standard polygonal modeling, a circle or cylinder is a regular prism whose facets deviate from true circular curvature by the **chordal error (sagitta $h$)**:
$$h = r \cdot \left(1 - \cos\left(\frac{180^\circ}{n}\right)\right)$$
If an agent models a $\varnothing 20\text{ mm}$ pin hole with 16 segments, the chordal error is $0.19\text{ mm}$ (arithmetic: 10 mm x (1 - cos 11.25 deg) = 0.192 mm), which is about $9\times$ the ISO H7 tolerance band for that size ($0.021\text{ mm}$: the 18-30 mm H7 limit deviation is +21 um / 0). CORRECTED: the earlier draft used $0.012\text{ mm}$ (the H7 value for 3-6 mm) and so claimed $15\times$. <!-- ease:source S1 anchor="ISO 286-2 H7 table row Above 18 to 30: +21 / 0; row Above 3 to 6: +12 / 0" --> Precision mechanical design in Blender requires treating vertices as **discrete boundary samples of exact analytical geometry**:
1. Every critical hole or cylindrical surface must calculate its segment count from tolerance requirements ($n \ge 64\text{–}128$ for bearing bores; arithmetic check for r = 10 mm: n=64 gives h = 0.012 mm, n=128 gives h = 0.003 mm, n=16 gives 0.192 mm).
2. All transforms must have scale applied ($[1.0, 1.0, 1.0]$) immediately; unapplied scale corrupts boolean offsets and bevel metric dimensions.
3. Mechanical edges must maintain explicit planar face normals using the `harden_normals` Bevel modifier or Weighted Normal attributes, never blind auto-smooth angles that distort flat mounting planes.

### 2. Decision first

| Objective | Cylinder Segments ($n$) | Boolean Solver | Bevel Profile | Normal Treatment |
| :--- | :---: | :---: | :---: | :--- |
| **Precision Bearing Bore (H7)** | $64\text{–}128$ | `EXACT` | $1\text{ segment chamfer (0.5mm)}$ | `harden_normals = True` |
| **Fastener Clearance Hole (M3/M4)** | $24\text{–}32$ | `EXACT` | $1\text{ segment chamfer (0.3mm)}$ | Face normal planar |
| **CNC Machined Pocket** | Tool radius match | `EXACT` | Internal fillet ($R \ge D_{tool}/2$) | Weighted Normal |
| **3D Print Structural Shell** | $32\text{–}64$ | `EXACT` | $45^\circ\text{ chamfer (no overhang)}$ | Flat / angle $30^\circ$ |
| **Sheet Metal Flange** | N/A | Modifier | Bend radius ($R \ge t$) | Flat |

Decision tree for precision mechanical feature creation:
1. Is it a hole or shaft? → Calculate minimum vertices: $n \ge \frac{\pi}{\arccos(1 - h_{tol}/r)}$.
2. Is it joining or cutting parts? → Use `modifier.solver = 'EXACT'` with `use_hole_tolerant = True`. The Boolean solver enum in Blender 5.2 is FLOAT / EXACT / MANIFOLD; EXACT is the slower solver with the best results for coplanar faces, MANIFOLD is fastest but only for manifold meshes, `use_hole_tolerant` gives better results when there are holes (slower). <!-- ease:source S2 anchor="solver and use_hole_tolerant property descriptions" -->
3. Is it an edge finish? → Chamfer ($45^\circ$, 1 segment) for assembly lead-ins; Fillet ($\ge 3$ segments) only for CNC stress reliefs or fluid flow.
4. Are parts mating? → Apply ISO 286 clearance offsets directly to the mesh (do not rely on nominal sizing). Example limit deviations for H7 holes: +12 um (3-6 mm), +15 (6-10), +18 (10-18), +21 (18-30), +25 (30-50) all with lower deviation 0. <!-- ease:source S1 anchor="ISO 286-2 table, H7 column" -->

### 3. Rules

R1. Configure scene units to metric with `scale_length = 1.0` before creating geometry.
    Why: `scale_length = 1.0` maintains 1 unit = 1 meter, so `0.025` is exactly $25\text{ mm}$. CORRECTED: the earlier claim that `scale_length = 0.001` truncates float precision in solvers is not supported; the Blender manual states Unit Scale only changes the values displayed in the user interface and not how things behave internally. Keep 1.0 for this repo's 1 BU = 1 m convention, not for solver precision. <!-- ease:source S3 anchor="Unit Scale: only influences the values displayed in the user interface" -->
    Violation: Floating-point precision wobble in boolean cutters and unexpected physics scales.

R2. Apply Object Scale (`bpy.ops.object.transform_apply(scale=True)`) before adding Bevel or Boolean modifiers.
    Why: Modifiers evaluate in object-local coordinates. A cylinder scaled non-uniformly $(1.0, 1.0, 0.5)$ will create elliptical bevels and uneven wall thicknesses.
    Violation: Asymmetric chamfers and non-uniform clearance gaps.

R3. Always use `solver = 'EXACT'` on Boolean modifiers for mechanical parts.
    Why: The float solver (enum value `FLOAT` in Blender 5.2; the earlier draft called it `FAST`, which is not an enum value in the 5.2 API) is a simple solver without support for overlapping geometry and is weak on coplanar faces. `EXACT` gives the best results for coplanar faces. `MANIFOLD` is a faster option when all operands are closed manifold meshes. <!-- ease:source S2 anchor="FLOAT: good performance, without support for overlapping geometry; EXACT: best for coplanar; MANIFOLD: fastest, manifold only" -->
    Violation: Non-manifold edges, missing cutouts, or crashes during 3D print export.

R4. Internal CNC pocket corners must have a radius $R \ge \frac{D_{tool}}{2} + 0.5\text{ mm}$ <!-- ease:source UNVERIFIED reason="+0.5 mm margin is a shop heuristic; confirm with the supplier" -->.
    Why: Cylindrical endmills cannot mill sharp $90^\circ$ inside corners. Forcing sharp corners requires expensive wire EDM.
    Violation: Unmanufacturable CNC parts or massive supplier surcharges.

R5. Never mate components at nominal zero-clearance CAD dimensions.
    Why: Real components have manufacturing tolerances. Nominal zero fit creates interference in 3D prints and galling in machined metals.
    Violation: Parts physically cannot assemble.

### 4. Recipe: Copy-paste patterns

#### Recipe 1: Setup Metric Mechanical Scene & Verify Manifoldness

```python
import bpy
import bmesh

def setup_mechanical_environment():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.mass_unit = 'KILOGRAMS'

def assert_is_manifold(obj):
    assert obj.type == 'MESH', f"{obj.name} is not a mesh"
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    bm.free()
    assert len(non_manifold_verts) == 0, f"{obj.name} has {len(non_manifold_verts)} non-manifold vertices"
    assert len(non_manifold_edges) == 0, f"{obj.name} has {len(non_manifold_edges)} non-manifold edges"
```

#### Recipe 2: Precision Metric Hole Cutter (Fastener Clearance)

```python
import bpy
import math

def create_precision_hole_cutter(name, diameter_mm, depth_mm, segments=32):
    radius_m = (diameter_mm / 2.0) / 1000.0
    depth_m = depth_mm / 1000.0
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    # Generate exact cylinder via from_pydata
    verts = []
    faces = []
    
    # Bottom circle (z = -depth/2)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        verts.append((radius_m * math.cos(angle), radius_m * math.sin(angle), -depth_m / 2.0))
    # Top circle (z = +depth/2)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        verts.append((radius_m * math.cos(angle), radius_m * math.sin(angle), depth_m / 2.0))
        
    # Side faces
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([i, nxt, segments + nxt, segments + i])
        
    # Bottom cap
    faces.append([i for i in reversed(range(segments))])
    # Top cap
    faces.append([segments + i for i in range(segments)])
    
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    return obj
```

#### Recipe 3: Non-Destructive Mechanical Chamfer & Normal Hardening

```python
def apply_mechanical_chamfer(obj, width_mm=0.5):
    mod = obj.modifiers.new(name="MachinedChamfer", type='BEVEL')
    mod.width = width_mm / 1000.0
    mod.segments = 1
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(30.0)
    mod.miter_outer = 'ARC'
    mod.harden_normals = True
    mod.use_clamp_overlap = True
    return mod
```

### 5. Anti-patterns & Traps

1. **The Fast Boolean Float Collapse:**
   Using the float solver (`mod.solver = 'FLOAT'`; written `'FAST'` in the earlier draft) on coplanar boolean cuts (e.g. cutting a hole through a plate where cutter ends flush with plate face). The float solver does not support overlapping geometry and can leave degenerate triangles and non-manifold holes. <!-- ease:source S2 anchor="solver descriptions" -->
   *Fix:* Use `solver = 'EXACT'`, and extend the cutter by $+1.0\text{ mm}$ on top and bottom so cutter faces do not sit coplanar with the target boundary.

2. **The "Shading Looks Smooth" Illusion:**
   Relying on Blender viewport smooth shading to judge cylinder quality. A 16-sided cylinder shaded smooth looks round in the viewport, but 3D prints or exports as a faceted hexadecagon.
   *Fix:* Always inspect in wireframe mode and calculate chordal deviation.

3. **Nominal Bolt Diameter Clearance Trap:**
   Modeling an M3 screw clearance hole as $\varnothing 3.0\text{ mm}$. A nominal M3 screw requires a **$\varnothing 3.4\text{ mm}$** hole for medium-series clearance (ISO 273 series: close 3.2, medium 3.4, free 3.6 mm; M4: 4.3 / 4.5 / 4.8; M5: 5.3 / 5.5 / 5.8; M6: 6.4 / 6.6 / 7.0), <!-- ease:source S4 anchor="ISO 273 close / medium / free columns" --> or $\varnothing 4.0\text{ mm}$ for heat-set insert pilot holes <!-- ease:source UNVERIFIED reason="heat-set pilot diameter depends on the insert; take from the insert datasheet" -->.
   *Fix:* Reference standard ISO fastener clearance tables.

### 6. Verification & diagnostics

```python
def verify_clearance_gap(inner_obj, outer_obj, expected_gap_mm, tolerance_mm=0.05):
    """Numerically verifies radial gap between mating bounding boxes/radii."""
    inner_dim = inner_obj.dimensions
    outer_dim = outer_obj.dimensions
    gap_x = ((outer_dim.x - inner_dim.x) / 2.0) * 1000.0
    gap_y = ((outer_dim.y - inner_dim.y) / 2.0) * 1000.0
    assert abs(gap_x - expected_gap_mm) <= tolerance_mm, f"Gap X {gap_x}mm deviates from {expected_gap_mm}mm"
    assert abs(gap_y - expected_gap_mm) <= tolerance_mm, f"Gap Y {gap_y}mm deviates from {expected_gap_mm}mm"
```

### 7. Production edge cases

*   <!-- ease:source UNVERIFIED reason="Solidify modifier property names (nonmanifold_thickness_mode, use_rim_only, use_quality_normals) and the self-intersection claim were not verified against the 5.2 API page (docs.blender.org API pages for other modifiers returned a bot-check page)" --> **Thin Sheet Warping:** When solidifying thin sheet metal shells ($< 1.0\text{ mm}$), the `SOLIDIFY` modifier can self-intersect at sharp concave corners. Set `modifier.nonmanifold_thickness_mode = 'CONSTRAINTS'` and enable `use_rim_only = False` with `use_quality_normals = True`.
*   **Thread Representation:** Never model actual helical screw threads with polygons unless printing giant custom leadscrews ($> M20$) <!-- ease:source UNVERIFIED reason="face-count (>50k) and M20 threshold are rules of thumb" -->. Helical threads explode vertex count ($> 50\text{k}$ faces per screw) and ruin boolean performance. Model fasteners as cylindrical clearance shanks with counterbores; add threads via bump/normal maps if visual rendering is needed.

### 8. Sources & References

- [ISO 286-1:2010](https://www.iso.org/standard/45975.html) — Geometrical product specifications (GPS) — ISO code system for tolerances on linear sizes — Part 1: Basis of tolerances, deviations and fits.
- [ISO 286-2:2010](https://www.iso.org/standard/45976.html) — Geometrical product specifications (GPS) — ISO code system for tolerances on linear sizes — Part 2: Tables of standard tolerance grades and limit deviations for holes and shafts.
- [ASME Y14.5-2018](https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing) — Dimensioning and Tolerancing. American Society of Mechanical Engineers.
- [ISO 1101:2017](https://www.iso.org/standard/66777.html) — Geometrical product specifications (GPS) — Geometrical tolerancing — Tolerances of form, orientation, location and run-out.
- Slocum, A. H. (1992). *Precision Machine Design*. Society of Manufacturing Engineers / Prentice Hall. ISBN: 978-0872634923. (Exact constraint design, kinematic couplings, Abbe principle).
- Smith, S. T., & Chetwynd, D. G. (1992). *Foundations of Ultraprecision Mechanism Design*. CRC Press. ISBN: 978-2881248443.
- [Blender 5.2 Python API — `bpy.types.BooleanModifier`](https://docs.blender.org/api/current/bpy.types.BooleanModifier.html) (`solver='EXACT'`, `use_hole_tolerant`, `use_self`)
- [Blender 5.2 Python API — `bpy.types.BevelModifier`](https://docs.blender.org/api/current/bpy.types.BevelModifier.html) (`harden_normals`, `miter_outer='ARC'`, `use_clamp_overlap`)
- Empirically verified on Blender 5.2.0 LTS headless: Boolean exact manifold solver preserves watertightness across coplanar cylinder penetrations; `bmesh.ops.create_cone` generates exact circle boundary chords adhering to $h = r(1-\cos(\pi/N))$. <!-- ease:source UNVERIFIED reason="no frozen run log for this older claim exists in the repo; re-run before relying on it" -->
- `[UNVERIFIED]` Recommended default clearance offsets ($0.05\text{–}0.10\text{ mm}$) are empirical machine shop best practices; verify against specific supplier tolerance sheets.

## Failure Modes (Mandatory)
- **Hole is faceted when exported/printed** — cause: 16-segment cylinder looks round only with smooth shading — fix: compute segments from the tolerance (n >= pi / arccos(1 - h/r)) and inspect in wireframe
- **Boolean leaves missing cutouts or non-manifold edges** — cause: float solver on coplanar cutter faces — fix: EXACT solver and extend the cutter 1 mm beyond both faces
- **Fasteners do not fit** — cause: nominal 3.0 mm hole for an M3 screw — fix: ISO 273 medium clearance 3.4 mm
- **Asymmetric bevels/chamfers** — cause: object scale not applied before Bevel/Boolean — fix: apply scale first
- **Chordal-error claim off by a factor** — cause: the H7 band used was for the wrong nominal size — fix: look the H7 limit up for the actual size range (21 um for 18-30 mm)

## Sources
- [S1] Wevolver, H7 Tolerance Explained: ISO 286 hole tolerance charts (ISO 286-2 limit deviations table) — https://www.wevolver.com/article/h7-tolerance-explained-iso-286-hole-tolerance-charts (frozen copy: knowledge/_evidence/kb-261013/w6-wevolver-h7-tolerance.html) — captured 2026-10-13 — sha256 27f8bd5bc869cbb9e2590b6e9fd39afbbda75e8c02f1e63d60c9f6faee32416a
- [S2] Blender Python API, BooleanModifier — https://docs.blender.org/api/current/bpy.types.BooleanModifier.html (frozen copy: knowledge/_evidence/kb-261013/w6-blender-api-boolean-modifier.html) — captured 2026-10-13 — sha256 5d44c0ec1116e27a787ea3db9007798a084658b9a0caf74cb05406bf40035486
- [S3] Blender 5.2 LTS Manual, Scene Properties (Units, Unit Scale) — https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html (frozen copy: knowledge/_evidence/kb-261013/w6-blender-manual-scene-units.html) — captured 2026-10-13 — sha256 5e686e9f0b3d401fb97cf2479609aa976863fc77d22cf513db5aff17e6100422
- [S4] Optimas, Tapping Drill & Clearance Hole Sizes (ISO 273 close/medium/free series) — https://optimas.com/technical-resources/tapping-sizes/ (frozen copy: knowledge/_evidence/kb-261013/w6-optimas-clearance-holes.html) — captured 2026-10-13 — sha256 10100056bf75e3c803c05507bcb16adc2638160fe7877991f1b4c8f723a6815b

---
name: cad-precision-modeling
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Precision mechanical modeling, CAD standards, metric units, exact boolean workflows, chamfers, and GD&T clearance tolerances in Blender.
loads_with: [modeling-topology, modifiers, export-interchange, 3d-printing]
tags: [cad, mechanical, precision, boolean, chamfer, gdt, tolerances, dfma]
---

# Precision CAD & Mechanical Modeling in Blender

## 1. Mental model

Blender is natively a polygonal mesh modeler, not an analytical B-Rep solid modeler. In standard polygonal modeling, a circle or cylinder is a regular prism whose facets deviate from true circular curvature by the **chordal error (sagitta $h$)**:
$$h = r \cdot \left(1 - \cos\left(\frac{180^\circ}{n}\right)\right)$$
If an agent models a $\varnothing 20\text{ mm}$ pin hole with 16 segments, the chordal error is $0.19\text{ mm}$, which is $15\times$ larger than an ISO H7 machining tolerance ($0.012\text{ mm}$). Precision mechanical design in Blender requires treating vertices as **discrete boundary samples of exact analytical geometry**:
1. Every critical hole or cylindrical surface must calculate its segment count from tolerance requirements ($n \ge 64\text{–}128$ for bearing bores).
2. All transforms must have scale applied ($[1.0, 1.0, 1.0]$) immediately; unapplied scale corrupts boolean offsets and bevel metric dimensions.
3. Mechanical edges must maintain explicit planar face normals using the `harden_normals` Bevel modifier or Weighted Normal attributes, never blind auto-smooth angles that distort flat mounting planes.

## 2. Decision first

| Objective | Cylinder Segments ($n$) | Boolean Solver | Bevel Profile | Normal Treatment |
| :--- | :---: | :---: | :---: | :--- |
| **Precision Bearing Bore (H7)** | $64\text{–}128$ | `EXACT` | $1\text{ segment chamfer (0.5mm)}$ | `harden_normals = True` |
| **Fastener Clearance Hole (M3/M4)** | $24\text{–}32$ | `EXACT` | $1\text{ segment chamfer (0.3mm)}$ | Face normal planar |
| **CNC Machined Pocket** | Tool radius match | `EXACT` | Internal fillet ($R \ge D_{tool}/2$) | Weighted Normal |
| **3D Print Structural Shell** | $32\text{–}64$ | `EXACT` | $45^\circ\text{ chamfer (no overhang)}$ | Flat / angle $30^\circ$ |
| **Sheet Metal Flange** | N/A | Modifier | Bend radius ($R \ge t$) | Flat |

Decision tree for precision mechanical feature creation:
1. Is it a hole or shaft? → Calculate minimum vertices: $n \ge \frac{\pi}{\arccos(1 - h_{tol}/r)}$.
2. Is it joining or cutting parts? → Use `modifier.solver = 'EXACT'` with `use_hole_tolerant = True`.
3. Is it an edge finish? → Chamfer ($45^\circ$, 1 segment) for assembly lead-ins; Fillet ($\ge 3$ segments) only for CNC stress reliefs or fluid flow.
4. Are parts mating? → Apply ISO 286 clearance offsets directly to the mesh (do not rely on nominal sizing).

## 3. Rules

R1. Configure scene units to metric with `scale_length = 1.0` before creating geometry.
    Why: `scale_length = 1.0` maintains 1 unit = 1 meter, so `0.025` is exactly $25\text{ mm}$. Tampering with `scale_length = 0.001` can cause float precision truncation in modifier solvers.
    Violation: Floating-point precision wobble in boolean cutters and unexpected physics scales.

R2. Apply Object Scale (`bpy.ops.object.transform_apply(scale=True)`) before adding Bevel or Boolean modifiers.
    Why: Modifiers evaluate in object-local coordinates. A cylinder scaled non-uniformly $(1.0, 1.0, 0.5)$ will create elliptical bevels and uneven wall thicknesses.
    Violation: Asymmetric chamfers and non-uniform clearance gaps.

R3. Always use `solver = 'EXACT'` on Boolean modifiers for mechanical parts.
    Why: The `FAST` solver uses float tolerances and frequently yields non-manifold self-intersecting meshes when faces are coplanar. `EXACT` handles coplanar faces deterministically.
    Violation: Non-manifold edges, missing cutouts, or crashes during 3D print export.

R4. Internal CNC pocket corners must have a radius $R \ge \frac{D_{tool}}{2} + 0.5\text{ mm}$.
    Why: Cylindrical endmills cannot mill sharp $90^\circ$ inside corners. Forcing sharp corners requires expensive wire EDM.
    Violation: Unmanufacturable CNC parts or massive supplier surcharges.

R5. Never mate components at nominal zero-clearance CAD dimensions.
    Why: Real components have manufacturing tolerances. Nominal zero fit creates interference in 3D prints and galling in machined metals.
    Violation: Parts physically cannot assemble.

## 4. Recipe: Copy-paste patterns

### Recipe 1: Setup Metric Mechanical Scene & Verify Manifoldness

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

### Recipe 2: Precision Metric Hole Cutter (Fastener Clearance)

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

### Recipe 3: Non-Destructive Mechanical Chamfer & Normal Hardening

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

## 5. Anti-patterns & Traps

1. **The Fast Boolean Float Collapse:**
   Using `mod.solver = 'FAST'` on coplanar boolean cuts (e.g. cutting a hole through a plate where cutter ends flush with plate face). Fast solver produces zero-area degenerate triangles and non-manifold holes.
   *Fix:* Use `solver = 'EXACT'`, and extend the cutter by $+1.0\text{ mm}$ on top and bottom so cutter faces do not sit coplanar with the target boundary.

2. **The "Shading Looks Smooth" Illusion:**
   Relying on Blender viewport smooth shading to judge cylinder quality. A 16-sided cylinder shaded smooth looks round in the viewport, but 3D prints or exports as a faceted hexadecagon.
   *Fix:* Always inspect in wireframe mode and calculate chordal deviation.

3. **Nominal Bolt Diameter Clearance Trap:**
   Modeling an M3 screw clearance hole as $\varnothing 3.0\text{ mm}$. A nominal M3 screw requires a **$\varnothing 3.4\text{ mm}$** hole for normal clearance (ISO 273), or $\varnothing 4.0\text{ mm}$ for heat-set insert pilot holes.
   *Fix:* Reference standard ISO fastener clearance tables.

## 6. Verification & diagnostics

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

## 7. Production edge cases

*   **Thin Sheet Warping:** When solidifying thin sheet metal shells ($< 1.0\text{ mm}$), the `SOLIDIFY` modifier can self-intersect at sharp concave corners. Set `modifier.nonmanifold_thickness_mode = 'CONSTRAINTS'` and enable `use_rim_only = False` with `use_quality_normals = True`.
*   **Thread Representation:** Never model actual helical screw threads with polygons unless printing giant custom leadscrews ($> M20$). Helical threads explode vertex count ($> 50\text{k}$ faces per screw) and ruin boolean performance. Model fasteners as cylindrical clearance shanks with counterbores; add threads via bump/normal maps if visual rendering is needed.

## 8. Sources & References

- [ISO 286-1:2010](https://www.iso.org/standard/45975.html) — Geometrical product specifications (GPS) — ISO code system for tolerances on linear sizes — Part 1: Basis of tolerances, deviations and fits.
- [ISO 286-2:2010](https://www.iso.org/standard/45976.html) — Geometrical product specifications (GPS) — ISO code system for tolerances on linear sizes — Part 2: Tables of standard tolerance grades and limit deviations for holes and shafts.
- [ASME Y14.5-2018](https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing) — Dimensioning and Tolerancing. American Society of Mechanical Engineers.
- [ISO 1101:2017](https://www.iso.org/standard/66777.html) — Geometrical product specifications (GPS) — Geometrical tolerancing — Tolerances of form, orientation, location and run-out.
- Slocum, A. H. (1992). *Precision Machine Design*. Society of Manufacturing Engineers / Prentice Hall. ISBN: 978-0872634923. (Exact constraint design, kinematic couplings, Abbe principle).
- Smith, S. T., & Chetwynd, D. G. (1992). *Foundations of Ultraprecision Mechanism Design*. CRC Press. ISBN: 978-2881248443.
- [Blender 5.2 Python API — `bpy.types.BooleanModifier`](https://docs.blender.org/api/current/bpy.types.BooleanModifier.html) (`solver='EXACT'`, `use_hole_tolerant`, `use_self`)
- [Blender 5.2 Python API — `bpy.types.BevelModifier`](https://docs.blender.org/api/current/bpy.types.BevelModifier.html) (`harden_normals`, `miter_outer='ARC'`, `use_clamp_overlap`)
- Empirically verified on Blender 5.2.0 LTS headless: Boolean exact manifold solver preserves watertightness across coplanar cylinder penetrations; `bmesh.ops.create_cone` generates exact circle boundary chords adhering to $h = r(1-\cos(\pi/N))$.
- `[UNVERIFIED]` Recommended default clearance offsets ($0.05\text{–}0.10\text{ mm}$) are empirical machine shop best practices; verify against specific supplier tolerance sheets.

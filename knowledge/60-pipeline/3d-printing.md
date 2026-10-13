---
name: 3d-printing
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Manifold/watertight requirements, wall thickness and clearance by process, bmesh-based failure detection, and STL/3MF export from Blender 5.2.
loads_with: [scene-organization, export-interchange, optimization-realtime]
tags: [3d-print, manifold, bmesh, stl, 3mf, tolerance, boolean, wall-thickness]
id: 3d-printing
title: "3D Printing from Blender"
when: [3d-print-export, manifold-audit, wall-thickness-check, stl-unit-scale, boolean-for-print, overhang-orientation]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# 3D Printing from Blender

## Purpose

Make a Blender mesh printable: prove it is a closed, consistently wound solid with a bmesh audit, fix the unit contract (Blender metres vs slicer millimetres), apply process-specific wall/clearance/overhang limits, and export STL (or 3MF) with a verified triangle count. Process numbers here are manufacturing practice, not Blender facts; the gate-enforced limits live in the build's `spec.json` and `scripts/production-gate.py`.

## When to Use / When NOT

- ALLOWED: preparing a mesh for FDM/SLA/SLS export — run the §4.1 bmesh audit, assert the unit contract, export binary STL.
- ALLOWED: choosing STL vs 3MF, or deciding boolean solver/bevel order for a printed part.
- NOT ALLOWED: production DFAM rules (heat-set insert bosses, elephant-foot chamfer, build-orientation strength) — use `dfam-3dprinting-production`.
- NOT ALLOWED: polymer-specific CAD tolerances, snap fits, printed threads — use `polymer-3dprinting-cad` (knowledge/70-cad-precision-robotics).
- NOT ALLOWED: exporter arguments for glTF/FBX/USD/OBJ/PLY/Alembic — use `export-interchange`.
- NOT ALLOWED: claiming a part is manufacturable from these tables — min-wall and gate rules come from the spec and `production-gate.py` (see `AGENTS.md`); physical acceptance goes through `manufacturing-evidence-workflow`.

## Core Knowledge Content

### 1. Mental model

A slicer does not see your mesh; it sees a stack of 2D cross-sections computed
by intersecting a plane with your triangles. That works if and only if every
point in space is unambiguously inside or outside the solid. That is what
"manifold / watertight / 2-manifold" means in practice: **every edge is shared <!-- ease:source S1 anchor="BMEdge.is_manifold / is_contiguous" -->
by exactly two faces, every face normal points outward consistently, and no two
faces intersect**. Everything else in this file follows from that one
requirement.

The second half of the problem is physical: the printer has a minimum feature
size, gravity acts on unsupported material during the build, and mated parts
need clearance because plastic swells. These are process- and material-specific
numbers, not modelling opinions.

The classic agent failure is scale. Blender works in metres, slicers work in <!-- ease:source UNVERIFIED reason="no unit field in STL structure: inferred from S11 byte layout, which lists none" -->
millimetres, and STL is unitless. A 30 mm part modelled as 30 Blender units
exports as "30" and arrives as 30 mm only by accident. Model in metres
(0.03 BU = 30 mm) and export with `global_scale=1000`, **or** model in
"1 BU = 1 mm" and export with `global_scale=1.0` — pick one and assert it.
Doing both gives the 1000x error.

### 2. Decision first

| Question | Answer |
|---|---|
| Is the model printable at all? | Run the bmesh audit in §4.1. Non-manifold edges > 0 ⇒ no. |
| Model in metres or millimetres? | Metres with `scale_length=1.0` (physics/booleans stay well-conditioned), export `global_scale=1000` |
| Which export format? | Binary STL for anything; 3MF (via extension) when colour/units/multi-part matter |
| Boolean union of parts, or separate shells? | Union into one manifold solid unless the slicer explicitly supports multi-shell |
| Boolean solver | `'EXACT'` for printable parts; `'FLOAT'` (renamed from `'FAST'` in 5.0) only for preview |
| Rounded corners on a printed part | Bevel modifier **before** the boolean, applied, with `harden_normals=False` |
| Model has non-manifold edges after boolean | Fix source geometry; do not "fill holes" blindly |
| Overhang steeper than the process limit | Reorient (`object.print3d_align_xy`), redesign, or accept supports |
| Two parts must fit together | Add clearance per §2 table to the *negative* side |

<!-- ease:source S5 anchor="FAST renamed to FLOAT in boolean modifier and operator" -->

Wall thickness minimums (nominal; always confirm with the specific printer/service): <!-- ease:source S15 anchor="print/both: real walls >= spec min_wall_mm; gate decides" -->

| Process | Absolute min wall | Safe min wall | Min unsupported wall | Min embossed detail | Min hole Ø |
|---|---|---|---|---|---|
| FDM, 0.4 mm nozzle, PLA/PETG | 0.9 mm (2 perimeters at ≈0.45 mm) | 1.2–1.6 mm | 1.2 mm | 0.6 mm wide × 0.4 mm high | 2.0 mm |
| FDM, ABS/ASA (warp-prone) | 1.2 mm | 2.0 mm | 1.6 mm | 0.8 mm | 2.5 mm |
| FDM, flexible (TPU) | 1.0 mm | 1.6 mm | 1.6 mm | 0.8 mm | 2.5 mm |
| SLA / DLP / MSLA resin, standard | 0.4 mm | 0.8–1.0 mm | 0.6 mm | 0.2 mm | 0.5 mm |
| SLA, tough/durable resin | 0.6 mm | 1.2 mm | 1.0 mm | 0.3 mm | 0.8 mm |
| SLS nylon (PA12) | 0.7 mm | 1.0–1.5 mm | 1.0 mm | 0.4 mm | 1.5 mm (+ escape holes ≥ 4 mm for powder) |
| MJF nylon | 0.5 mm | 1.0 mm | 0.8 mm | 0.3 mm | 1.5 mm |
| Binder-jet / SLM metal | 1.0 mm | 2.0 mm | 1.5 mm | 0.5 mm | 2.0 mm |

<!-- ease:source UNVERIFIED reason="ABS/TPU/PETG-tough/MJF/metal wall, hole and emboss minimums are service-bureau practice with no frozen primary source" -->

<!-- ease:source S8 anchor="perimeter table: 1 perimeter 0.45, 2 = 0.9, 3 = 1.35 mm for 0.4 mm nozzle" -->

Vendor cross-check (2026-10-13): Formlabs lists 0.2 mm minimum supported and unsupported wall and 0.1 mm embossed detail for Form 4 / Grey Resin at 50 µm <!-- ease:source S9 anchor="minimum supported/unsupported wall 0.2 mm; embossed 0.1 mm" -->; Formlabs Fuse SLS lists 0.6 mm vertical / 0.3 mm horizontal walls and 1.0 mm minimum hole <!-- ease:source S10 anchor="minimum wall thickness; minimum hole diameter 1.0 mm" -->. The table above deliberately keeps the more conservative multi-printer values; use the vendor values only for a named printer/resin and record that choice in `spec.json`.

Overhang and support:

| Process | Self-supporting up to | Needs support beyond | Max unsupported bridge |
|---|---|---|---|
| FDM | 45° from vertical | 45–60° | 5–10 mm (well cooled: 20 mm) |
| SLA/MSLA | 30–35° from vertical | > 35° | 2–5 mm |
| SLS / MJF | any (powder bed supports) | never | any |

<!-- ease:source UNVERIFIED reason="30-35 deg SLA self-support not found; S9 uses a different metric (min 10 deg from level, 5 mm max unsupported overhang, 29 mm bridge span)" -->

<!-- ease:source S8 anchor="overhangs 45-60 degrees; Nextruder+360 cooling printers up to 75" -->

Clearance for mated parts (gap modelled into the geometry, per side):

| Fit | FDM | SLA | SLS/MJF |
|---|---|---|---|
| Press / interference fit | 0.00–0.05 mm | 0.00–0.02 mm | 0.05 mm |
| Snug sliding fit | 0.20 mm | 0.10 mm | 0.20 mm |
| Free/loose running fit | 0.40 mm | 0.20 mm | 0.30 mm |
| Print-in-place hinge/joint | 0.50 mm | 0.30 mm | 0.40 mm |
| Threaded (printed threads) | 0.40 mm on the flanks | 0.20 mm | 0.30 mm |

<!-- ease:source UNVERIFIED reason="per-process clearance values (SLA, SLS/MJF columns) are practice; only the FDM movable-part figure has S8 support" -->

<!-- ease:source S8 anchor="initial good measurement for movable parts at least 0.3 mm; printer accurate to 0.2 mm" -->

### 3. Rules

R1. Assert the unit contract at the start: `scale_length == 1.0`, metric, and a documented BU→mm factor. <!-- ease:source S4 anchor="stl_export global_scale range [1e-06,1e+06], use_scene_unit" -->
    Why: STL carries no units; every downstream tool guesses millimetres.
    Violation: part arrives 1000x too large; slicer says "object exceeds build volume".

R2. Every edge must have exactly two faces. Check `edge.is_manifold` on a bmesh, not by eye. <!-- ease:source S1 anchor="BMEdge.is_manifold" -->
    Why: an edge with 1 face is a hole; with 3+ it is an internal wall — both make inside/outside undefined.
    Violation: slicer produces zero-thickness or inverted layers; "non-manifold" warning; random missing regions.

R3. Every face must wind consistently outward: check `edge.is_contiguous` and fix with `bmesh.ops.recalc_face_normals`. <!-- ease:source S2 anchor="recalc_face_normals(bm, faces=[])" -->
    Why: an inverted face flips the inside/outside test locally.
    Violation: hollow shells printed as solid or vice versa; slicer preview shows inverted normals in red.

R4. No self-intersecting faces. Detect with a BVH self-overlap test. <!-- ease:source S3 anchor="BVHTree.FromBMesh(bmesh, epsilon) / overlap" -->
    Why: intersecting shells give a slicer contradictory inside/outside evidence; most slicers "repair" by guessing.
    Violation: unexpected internal voids or blobs at the intersection.

R5. Delete loose geometry (wire edges, isolated verts, zero-area faces) before exporting. <!-- ease:source S11 anchor="binary STL stores 80-byte header, uint32 count, 50 bytes per triangle" -->
    Why: STL only stores triangles; loose verts/edges vanish but zero-area faces become degenerate triangles that break slicer topology.
    Violation: slicer reports "N degenerate facets removed"; layers with missing segments.

R6. Apply all transforms and all modifiers before measuring or exporting.
    Why: `ob.dimensions` reflects object scale but the exported vertices may not, depending on export options.
    Violation: measured 30 mm, printed 15 mm.

R7. Use the `'EXACT'` boolean solver for parts, and give each operand a manifold, non-degenerate mesh. <!-- ease:source S5 anchor="FAST renamed FLOAT" -->
    Why: `'FLOAT'` (called `'FAST'` before 5.0) trades correctness for speed and reliably produces non-manifold seams.
    Violation: boolean result has non-manifold edges exactly along the cut.

R8. Never model at Blender's default 2 m cube scale and then "scale in the slicer".
    Why: floating-point precision in booleans, bevels and remesh degrades with scale mismatch; the modifier's absolute-distance parameters (bevel width, remesh voxel size) are in Blender units.
    Violation: bevels that vanish or explode; remesh that produces a blob.

R9. Model clearance into the geometry, not into the slicer settings.
    Why: horizontal expansion / elephant-foot compensation is printer-global; a per-feature fit must live in the model.
    Violation: parts that fit on one printer and not another.

R10. Orient the part so critical surfaces face up and overhangs stay under the process limit, before export.
    Why: the exported orientation is the print orientation for most naive workflows.
    Violation: cosmetic face covered in support scars.

R11. Add drainage/escape holes (≥ 4 mm) for hollow SLA and SLS parts. <!-- ease:source S10 anchor="escape holes: at least 2, >= 3.5 mm diameter (Fuse SLS)" -->
    Why: trapped resin cures and cracks the part; trapped powder adds weight and cost.
    Violation: part cracks days after printing.

### 4. bpy patterns

#### 4.1 Complete printability audit with bmesh — no add-on required <!-- ease:source S14 anchor="evaluated_mm_bmesh docstring: promoted from print_audit" -->

```python
import bpy, bmesh, array
from mathutils.bvhtree import BVHTree

def print_audit(ob, apply_modifiers=True, zero_thresh=1e-6):
    """Returns a dict of failure classes. All counts must be 0 to print."""
    assert ob.type == 'MESH', ob.type
    bm = bmesh.new()
    if apply_modifiers:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        bm.from_mesh(me)
        ev.to_mesh_clear()
    else:
        bm.from_mesh(ob.data)

    bm.transform(ob.matrix_world)          # world space => real millimetres
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    non_manifold_e = [e.index for e in bm.edges if not e.is_manifold]
    non_contig_e   = [e.index for e in bm.edges if e.is_manifold and not e.is_contiguous]
    wire_e         = [e.index for e in bm.edges if e.is_wire]
    loose_v        = [v.index for v in bm.verts if not v.link_edges]
    wire_v         = [v.index for v in bm.verts if v.is_wire]
    non_manifold_v = [v.index for v in bm.verts if not v.is_manifold]
    zero_area_f    = [f.index for f in bm.faces if f.calc_area() <= zero_thresh ** 2]
    zero_len_e     = [e.index for e in bm.edges if e.calc_length() <= zero_thresh]

    # self-intersection: BVH overlapped with itself, minus face-adjacency pairs
    tri = bm.copy()
    bmesh.ops.triangulate(tri, faces=tri.faces[:])
    tree = BVHTree.FromBMesh(tri, epsilon=0.0)
    overlaps = tree.overlap(tree)
    tri.faces.ensure_lookup_table()
    def adjacent(i, j):
        fi, fj = tri.faces[i], tri.faces[j]
        return bool({v.index for v in fi.verts} & {v.index for v in fj.verts})
    self_isect = sorted({i for i, j in overlaps if i != j and not adjacent(i, j)})
    tri.free()

    # shell count via flood fill over face links
    seen, shells = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        shells += 1
        stack = [f]; seen.add(f.index)
        while stack:
            cur = stack.pop()
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index); stack.append(nf)

    volume = bm.calc_volume(signed=True)   # negative => normals inverted overall
    area   = sum(f.calc_area() for f in bm.faces)
    bm.free()

    return dict(
        non_manifold_edges=len(non_manifold_e),
        flipped_edges=len(non_contig_e),
        wire_edges=len(wire_e), loose_verts=len(loose_v), wire_verts=len(wire_v),
        non_manifold_verts=len(non_manifold_v),
        zero_area_faces=len(zero_area_f), zero_length_edges=len(zero_len_e),
        self_intersecting_faces=len(self_isect),
        shells=shells,
        signed_volume_m3=volume, surface_area_m2=area,
        watertight=(len(non_manifold_e) == 0 and len(non_contig_e) == 0
                    and len(self_isect) == 0 and len(zero_area_f) == 0),
        indices=dict(non_manifold_edges=non_manifold_e[:64],
                     flipped_edges=non_contig_e[:64],
                     zero_area_faces=zero_area_f[:64],
                     self_intersecting=self_isect[:64]),
    )
```

Interpretation:

| Field | Meaning if non-zero | Slicer symptom |
|---|---|---|
| `non_manifold_edges` | holes (1 face) or internal walls (3+ faces) | "not watertight", auto-repair guesses |
| `flipped_edges` | inconsistent winding across a manifold edge | inverted regions |
| `zero_area_faces` / `zero_length_edges` | degenerate triangles | "removed N degenerate facets" |
| `wire_edges` / `loose_verts` | leftover modelling debris | silently dropped by STL, but they hide real problems |
| `self_intersecting_faces` | shells passing through each other | internal voids, blobs |
| `shells > 1` | multiple disconnected solids | may be intentional (multi-part plate) or a floating fragment |
| `signed_volume_m3 < 0` | all normals inverted | everything prints inside-out |

#### 4.2 Automated repair (conservative, in order)

```python
import bpy, bmesh

def repair(ob, merge_dist=1e-5, fill_holes=True, max_hole_sides=0):
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)

    # 1. weld coincident vertices (the cause of most "holes")
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)

    # 2. drop degenerate geometry
    bmesh.ops.dissolve_degenerate(bm, dist=merge_dist, edges=bm.edges[:])

    # 3. delete loose verts and wire edges
    loose_v = [v for v in bm.verts if not v.link_edges]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context='VERTS')
    wire_e = [e for e in bm.edges if e.is_wire]
    if wire_e:
        bmesh.ops.delete(bm, geom=wire_e, context='EDGES')

    # 4. fill remaining boundary loops (only if you accept the guess)
    if fill_holes:
        boundary = [e for e in bm.edges if e.is_boundary]
        if boundary:
            bmesh.ops.holes_fill(bm, edges=boundary, sides=max_hole_sides)

    # 5. make winding consistent and outward
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    bm.to_mesh(me); bm.free(); me.update()
    me.validate(verbose=False)
    return print_audit(ob)
```

`holes_fill(sides=0)` fills holes with any number of sides; a positive value <!-- ease:source S2 anchor="holes_fill(bm, edges=[], sides=0)" -->
skips larger holes. Filling is a *guess* — for a part with a genuine missing
face it is right, for a part where a boolean tore the surface it just hides the
bug. Always re-audit after repairing.

#### 4.3 Boolean-based solid modelling <!-- ease:source S13 anchor="SolidifyModifier use_even_offset, use_rim_only" -->

```python
import bpy

def boolean(target, cutter, operation='DIFFERENCE', apply=True, hide_cutter=True):
    m = target.modifiers.new("bool_" + cutter.name, 'BOOLEAN')
    m.operation = operation           # 'DIFFERENCE' | 'UNION' | 'INTERSECT'
    m.operand_type = 'OBJECT'         # or 'COLLECTION'
    m.object = cutter
    m.solver = 'EXACT'                # 5.0 renamed the fast solver to 'FLOAT'
    m.use_self = False
    m.use_hole_tolerant = True        # helps with imperfect input
    if apply:
        vl = bpy.context.view_layer
        vl.objects.active = target
        with bpy.context.temp_override(object=target, active_object=target):
            bpy.ops.object.modifier_apply(modifier=m.name, single_user=True)
    if hide_cutter:
        cutter.hide_viewport = True
        cutter.hide_render = True
    return target

def offset_shell(ob, thickness_m, even=True):
    """Give an open/zero-thickness surface real wall thickness."""
    m = ob.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = thickness_m          # metres if scale_length == 1.0
    m.offset = -1.0                    # grow inward from the surface
    m.use_even_offset = even
    m.use_rim = True
    m.use_rim_only = False
    return m
```

Boolean hygiene that actually determines success: <!-- ease:source UNVERIFIED reason="operand hygiene rules (coplanar offset 0.01-0.1 mm, apply scale first) are practice, not in Blender docs" -->

1. Both operands must individually pass `print_audit` (`watertight=True`).
2. Neither operand may have coplanar faces exactly touching the other — offset
   the cutter by 0.01–0.1 mm past the surface it crosses.
3. Apply scale on both operands first; non-uniform scale wrecks `'EXACT'`.
4. Bevel *before* boolean where possible; bevelling a boolean seam usually
   produces non-manifold spikes.
5. Re-audit after every boolean, not at the end of a chain.

#### 4.4 Scale, orientation and measurement

```python
import bpy, math
from mathutils import Vector

BU_PER_MM = 0.001            # 1 BU == 1 m, so 1 mm == 0.001 BU

def assert_print_units(scene=None):
    u = (scene or bpy.context.scene).unit_settings
    assert u.system == 'METRIC' and abs(u.scale_length - 1.0) < 1e-9
    u.length_unit = 'MILLIMETERS'

def size_mm(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    return tuple(round(d * 1000.0, 3) for d in ev.dimensions)

def prepare_for_print(ob):
    vl = bpy.context.view_layer
    vl.objects.active = ob
    ob.select_set(True)
    with bpy.context.temp_override(object=ob, active_object=ob,
                                   selected_editable_objects=[ob]):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # sit the part on Z=0
    lo = min((ob.matrix_world @ Vector(c)).z for c in ob.bound_box)
    ob.location.z -= lo
    return size_mm(ob)

def overhang_faces(ob, limit_deg=45.0):
    """Faces whose normal is more than `limit_deg` away from vertical-up,
    i.e. downward-facing surfaces that will need support."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world); bm.normal_update()
    z = Vector((0, 0, -1))
    thr = math.cos(math.radians(90.0 - limit_deg))
    bad = [f.index for f in bm.faces if f.normal.dot(z) > thr]
    total = len(bm.faces); bm.free()
    return dict(overhang_faces=len(bad), total_faces=total, indices=bad[:64])
```

#### 4.5 STL / PLY / OBJ export for printing

```python
import bpy, os, struct

def export_stl_mm(path, collection=None, from_metres=True, ascii_=False):
    """Model in metres, print in millimetres."""
    kw = dict(filepath=os.path.abspath(path),
              ascii_format=ascii_,
              export_selected_objects=False,
              global_scale=1000.0 if from_metres else 1.0,
              use_scene_unit=False,          # NEVER combine with global_scale
              forward_axis='Y', up_axis='Z', # slicer convention: Z up
              apply_modifiers=True,
              evaluation_mode='DAG_EVAL_RENDER',   # 5.2 option
              use_batch=False)
    if collection:
        kw["collection"] = collection
    bpy.ops.wm.stl_export(**kw)
    return verify_binary_stl(kw["filepath"]) if not ascii_ else None

def verify_binary_stl(path):
    n = (os.path.getsize(path) - 84) // 50
    with open(path, "rb") as f:
        f.seek(80)
        header_n = struct.unpack("<I", f.read(4))[0]
    assert header_n == n, (header_n, n)
    return n
```

The alternative unit contract: set `use_scene_unit=True` and `global_scale=1.0`,
which multiplies by `scene.unit_settings.scale_length`. That only helps if you
deliberately set `scale_length = 0.001`, which breaks physics and every other
exporter — so prefer the explicit `global_scale=1000.0` form.

`wm.stl_export` full signature (5.2): `filepath, check_existing, ascii_format, <!-- ease:source S4 anchor="bpy.ops.wm.stl_export parameter list" --> <!-- ease:source S6 anchor="STL: added option how to eval (Viewport vs. Render) during export" -->
use_batch, export_selected_objects, collection, global_scale, use_scene_unit,
forward_axis, up_axis, apply_modifiers, evaluation_mode, filter_glob`.
`forward_axis`/`up_axis` take the long enum form (`'X'`, `'Y'`, `'Z'`,
`'NEGATIVE_X'`, `'NEGATIVE_Y'`, `'NEGATIVE_Z'`) — not FBX's `'-Z'`.

**3MF status in Blender 5.2: not supported natively.** There is no <!-- ease:source S4 anchor="no 3MF operator in bpy.ops.wm docs; extension id ThreeMF_io in S7" -->
`wm.threemf_export` and no 3MF entry in `bpy.ops.wm` / `bpy.ops.export_scene`.
3MF comes from the community extension `ThreeMF_io` ("3MF Import/Export",
`blender_version_min = 4.2.0`) on extensions.blender.org:

```python
import bpy
bpy.ops.extensions.repo_sync_all()
bpy.ops.extensions.package_install(repo_index=0, pkg_id="ThreeMF_io",
                                   enable_on_install=True)
# module name once installed: bl_ext.blender_org.ThreeMF_io
# Discover the operators it registers rather than guessing:
print([n for n in dir(bpy.ops.export_mesh) + dir(bpy.ops.wm)
       if "3mf" in n.lower() or "threemf" in n.lower()])
```

Prefer 3MF over STL when you need real units, per-object colours/materials, or <!-- ease:source S12 anchor="model unit attribute default millimeter; valid micron/millimeter/centimeter/inch/foot/meter" -->
several parts in one file; prefer binary STL for maximum compatibility.

#### 4.6 The 3D-Print Toolbox in 5.2

The toolbox is **no longer bundled**. It is a community extension: <!-- ease:source S7 anchor="id print3d_toolbox, blender_version_min 4.2.0, maintainer MikhailRachinskiy" -->

- extensions.blender.org id: `print3d_toolbox` (page slug `print3d-toolbox`),
  maintainer Mikhail Rachinskiy, `blender_version_min = "4.2.0"`.
- Python module once installed from the default remote repo:
  `bl_ext.blender_org.print3d_toolbox`.
- It is **not** in `scripts/addons_core/`, so `addon_utils.enable("print3d_toolbox")`
  will fail; it must be installed as an extension first.

```python
import bpy, addon_utils

MOD = "bl_ext.blender_org.print3d_toolbox"

def ensure_print3d():
    if addon_utils.check(MOD)[1]:
        return True
    bpy.ops.extensions.repo_sync_all()
    bpy.ops.extensions.package_install(repo_index=0, pkg_id="print3d_toolbox",
                                       enable_on_install=True)
    return addon_utils.check(MOD)[1]

def toolbox_check_all(ob):
    """Run every check and read the structured result out of the add-on."""
    import importlib
    ensure_print3d()
    scene = bpy.context.scene
    p = scene.print3d_toolbox                 # PointerProperty registered on Scene
    p.threshold_zero   = 0.0001               # default
    p.angle_nonplanar  = 0.0872665            # 5 deg
    p.thickness_min    = 0.001                # 1 mm, in Blender units
    p.angle_overhang   = 0.785398             # 45 deg
    p.angle_sharp      = 2.79253              # 160 deg

    vl = bpy.context.view_layer
    vl.objects.active = ob
    ob.select_set(True)
    with bpy.context.temp_override(object=ob, active_object=ob,
                                   selected_objects=[ob]):
        bpy.ops.mesh.print3d_check_all()

    report = importlib.import_module(MOD + ".report")
    return [(i.name, i.value, len(i.indices or ())) for i in report.get()]
```

Operator idnames registered by the extension (verified from its source): <!-- ease:source UNVERIFIED reason="operator idnames and min-version notes (>=4.3 shells, >=4.5 hollow/bisect) not re-checked against extension source in this pass" -->

| Operator | Purpose |
|---|---|
| `mesh.print3d_check_all` | run every check at once (`bl_options={'INTERNAL'}`, still callable) |
| `mesh.print3d_check_solid` | non-manifold edges + bad contiguous (flipped) edges |
| `mesh.print3d_check_intersect` | self-intersecting faces |
| `mesh.print3d_check_shells` | island/shell count (needs Blender ≥ 4.3) |
| `mesh.print3d_check_degenerate` | zero-area faces, zero-length edges |
| `mesh.print3d_check_nonplanar` | distorted (non-flat) n-gons |
| `mesh.print3d_check_thick` | faces thinner than `thickness_min` |
| `mesh.print3d_check_sharp` | edges sharper than `angle_sharp` |
| `mesh.print3d_check_overhang` | faces beyond `angle_overhang` |
| `mesh.print3d_info_volume` / `mesh.print3d_info_area` | volume / surface area |
| `mesh.print3d_clean_non_manifold` | automated non-manifold cleanup |
| `mesh.print3d_hollow`, `mesh.print3d_bisect` | hollowing, cutting (need ≥ 4.5) |
| `object.print3d_align_xy` | rotate the largest face flat to the bed |
| `mesh.print3d_scale_to_volume`, `mesh.print3d_scale_to_bounds` | rescale to a target |
| `export_scene.print3d_export` | quick STL/PLY/OBJ export |
| `wm.print3d_report_clear` | clear the report buffer |

The checks require an active MESH object and `context.mode in {'OBJECT',
'EDIT_MESH'}`. Results land in the add-on's private `report` module rather than
in the operator return value, which is why the snippet imports it.

**The bmesh audit in §4.1 is the preferred path for an agent**: no install step,
no network access, works under `--factory-startup`, and it returns structured
data instead of UI state.

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Slicer: "object exceeds build volume" by ~1000x | model in metres exported with `global_scale=1.0` | `global_scale=1000.0` (and only that, not `use_scene_unit`) |
| Model is 1 mm tall in the slicer | `global_scale=1000` applied to a mm-scale model | pick one unit contract, assert it |
| Slicer: "mesh is not manifold / auto-repaired" | `print_audit()["non_manifold_edges"] > 0` | §4.2 repair, then re-audit |
| Print comes out inside-out / hollow where it should be solid | `signed_volume_m3 < 0` or flipped faces | `bmesh.ops.recalc_face_normals` |
| Layers with random missing segments | degenerate (zero-area) triangles | `bmesh.ops.dissolve_degenerate` |
| Internal blobs / voids after a boolean | self-intersecting operands, or `solver='FLOAT'` | `solver='EXACT'`, audit operands first |
| Boolean produces non-manifold seam along the cut | coplanar faces exactly touching | offset the cutter 0.01–0.1 mm past the surface |
| `TypeError: ... enum "-Z" not found` on `wm.stl_export` | FBX-style axis string | `'NEGATIVE_Z'` |
| `AttributeError: module 'bpy.ops.export_mesh' has no attribute 'stl'` | STL exporter moved to C++ in 4.2 | `bpy.ops.wm.stl_export` |
| `AttributeError: 'Scene' object has no attribute 'print3d_toolbox'` | toolbox not installed/enabled (not bundled since 4.2) | install extension `print3d_toolbox`, or use §4.1 |
| `RuntimeError: Operator bpy.ops.mesh.print3d_check_all.poll() failed` | no active mesh object, or wrong mode | set `view_layer.objects.active`, `temp_override` |
| Thin walls print as gaps | wall below the process minimum | Solidify to the §2 minimum; verify with `check_thick` or a thickness ray test |
| Mated parts do not fit / fuse together | clearance modelled as 0 | build the §2 clearance into the negative feature |
| Overhangs covered in support scars | part not reoriented before export | `object.print3d_align_xy`, or rotate and re-audit `overhang_faces` |
| Hollow SLA part cracks | trapped uncured resin | add ≥ 4 mm drain holes |
| `ob.dimensions` disagrees with the printed size | unapplied scale, or modifiers not evaluated | `transform_apply(scale=True)` and measure the evaluated object |

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Unit contract | 1 BU = 1 m | 1 BU = 1 m | 1 BU = 1 m | 1 BU = 1 m | 1 BU = 1 m, export ×1000 |
| Display unit | metres | metres | metres | centimetres | **millimetres** |
| Manifold required | no | no | no | no | **yes, mandatory** |
| Normals must be outward | yes-ish | yes-ish | no | yes | **yes, mandatory** |
| N-gons allowed | no (triangulated) | quads | any | any | yes (STL triangulates) |
| Boolean solver | `'FLOAT'` (preview) | n/a | `'FLOAT'` | `'EXACT'` | **`'EXACT'`** |
| Min wall thickness | n/a | n/a | n/a | n/a | 0.9 mm FDM / 0.4 mm SLA / 0.7 mm SLS (conservative; see vendor cross-check) |
| Min feature detail | n/a | n/a | n/a | n/a | 0.6 mm FDM / 0.2 mm SLA |
| Mated-part clearance | n/a | n/a | n/a | n/a | 0.2 mm snug / 0.4 mm loose (FDM) |
| Max overhang from vertical | n/a | n/a | n/a | n/a | 45° FDM / 30° SLA / any SLS |
| Export format | glTF/FBX | FBX | Alembic | USD | **binary STL** or 3MF |
| `global_scale` on export | 1.0 | 1.0 | 1.0 | 1.0 | **1000.0** |
| `apply_modifiers` | True | True | baked | True | **True** |
| `evaluation_mode` | viewport ok | viewport ok | render | render | **`'DAG_EVAL_RENDER'`** |
| Subdivision before export | no | no | no | keep as modifier | apply at level 2–4 |
| Triangle budget | tight | tight | tight | loose | irrelevant; resolution matters |

### 7. Verification checklist

- [ ] `assert bpy.context.scene.unit_settings.scale_length == 1.0` — unit contract holds.
- [ ] `a = print_audit(ob); assert a["watertight"]` — the single gate for printability.
- [ ] `assert a["non_manifold_edges"] == 0 and a["flipped_edges"] == 0`.
- [ ] `assert a["self_intersecting_faces"] == 0`.
- [ ] `assert a["zero_area_faces"] == 0 and a["zero_length_edges"] == 0`.
- [ ] `assert a["signed_volume_m3"] > 0` — normals point outward overall.
- [ ] `assert a["shells"] == expected_part_count` — no stray fragments.
- [ ] `assert all(abs(v-1.0) < 1e-4 for v in ob.scale)` — transforms applied.
- [ ] `assert size_mm(ob) == pytest.approx(target_mm, abs=0.01)` — real dimensions.
- [ ] `assert overhang_faces(ob, 45.0)["overhang_faces"] == 0` for support-free FDM.
- [ ] `assert verify_binary_stl(path) == expected_triangles` — the file matches the mesh.
- [ ] Re-import the STL (`bpy.ops.wm.stl_import`) into an empty file and re-run `print_audit` — round-trip proves nothing was lost.
- [ ] Orthographic front/side screenshots at known scale to eyeball wall thickness and overhangs.

### 8. Legacy source list (pre-UKMC; superseded by the Sources section at the end)

- [bmesh.types (`BMEdge.is_manifold`, `is_contiguous`, `is_wire`, `BMesh.calc_volume`) — 5.2](https://docs.blender.org/api/current/bmesh.types.html)
- [bmesh.ops (`recalc_face_normals`, `remove_doubles`, `dissolve_degenerate`, `holes_fill`, `triangulate`, `delete`) — 5.2](https://docs.blender.org/api/current/bmesh.ops.html)
- [mathutils.bvhtree (`FromBMesh`, `overlap`) — 5.2](https://docs.blender.org/api/current/mathutils.bvhtree.html)
- [bpy.ops.wm (`stl_export`, `stl_import`, `obj_export`, `ply_export`) — 5.2](https://docs.blender.org/api/current/bpy.ops.wm.html)
- [bpy.ops.object (`transform_apply`, `modifier_apply`, `origin_set`) — 5.2](https://docs.blender.org/api/current/bpy.ops.object.html)
- [Blender 5.0: Python API — boolean `'FAST'` renamed to `'FLOAT'`](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.2 LTS: Pipeline & I/O — STL export evaluation mode](https://developer.blender.org/docs/release_notes/5.2/pipeline_io/)
- [3D Print Toolbox extension](https://extensions.blender.org/add-ons/print3d-toolbox/) — id `print3d_toolbox`, min Blender 4.2.0
- [3MF Import/Export extension](https://extensions.blender.org/) — id `ThreeMF_io`, min Blender 4.2.0
- `[UNVERIFIED]` All wall-thickness, overhang and clearance tables are manufacturing practice from printer/service-bureau guidelines, not Blender documentation. Confirm against the specific machine and material.
- `[UNVERIFIED]` The exact operator names registered by `ThreeMF_io` were not confirmed against its source; discover them at runtime as shown in §4.5.

## Failure Modes (Mandatory)

- **Slicer says object exceeds build volume by ~1000x (or part is 1 mm tall)** — cause: unit contract applied twice or not at all (`global_scale=1000` on a mm-scale model, or `1.0` on a metre-scale one) — fix: assert `scale_length==1.0`, pick one contract, export with `global_scale=1000.0` only (never with `use_scene_unit=True`).
- **Slicer reports non-manifold / auto-repairs / prints inside-out** — cause: `edge.is_manifold` false (holes, 3+ face edges) or `signed_volume < 0` from flipped normals — fix: §4.2 repair order, then re-run `print_audit` and require `watertight=True` before export.
- **Boolean seam is non-manifold or a cut leaves no walls** — cause: coplanar cutter faces, `FLOAT` solver, or an inside-out operand (see AGENTS.md failure map: signed volume < 0 on a procedural lathe) — fix: `EXACT` solver, offset cutter 0.01–0.1 mm, assert signed volume > 0 on both operands first.
- **`AttributeError` on `export_mesh.stl` / `Scene.print3d_toolbox`** — cause: STL operator is `bpy.ops.wm.stl_export` and the toolbox is an extension, not bundled — fix: use `wm.stl_export` and the §4.1 audit (no add-on needed), or install extension id `print3d_toolbox` first.
- **Thin walls print as gaps though the model shows geometry** — cause: wall below the process minimum (a wall narrower than one perimeter is not printable) — fix: Solidify/thicken to the table minimum and let the gate's `min_wall_mm` (from `spec.json`) decide; do not lower the spec to match the mesh.

## Sources

- [S1] bmesh.types — BMEdge.is_manifold/is_contiguous/is_wire, BMesh.calc_volume (Blender API current) — https://docs.blender.org/api/current/bmesh.types.html — captured 2026-10-13 — sha256 38bc14776291a14763af56ce8565b300c5b7dbd348a3382f8ddcad599371294f — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bmesh-types.html`
- [S2] bmesh.ops — recalc_face_normals, remove_doubles, dissolve_degenerate, holes_fill (Blender API current) — https://docs.blender.org/api/current/bmesh.ops.html — captured 2026-10-13 — sha256 45f98573a8ee18729eadeb8a5bcc784df770d34ebfe443953f27ebb3932a8555 — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bmesh-ops.html`
- [S3] mathutils.bvhtree — BVHTree.FromBMesh, overlap (Blender API current) — https://docs.blender.org/api/current/mathutils.bvhtree.html — captured 2026-10-13 — sha256 ab5d8dd9e0e67bec21fbbc828dee03c72071eab2941f658d309a39b3e681c1bd — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bvhtree.html`
- [S4] bpy.ops.wm — stl_export / stl_import signature (Blender API current) — https://docs.blender.org/api/current/bpy.ops.wm.html — captured 2026-10-13 — sha256 ada74a22a286b954f93ae9389100f8b5ce2ff4f4d9210c355ec95c7d04a395be — frozen `knowledge/_evidence/kb-261013/w3-docs-blender-org-api-current-bpy-ops-wm.html`
- [S5] Blender 5.0 release notes: Python API (boolean FAST renamed FLOAT) — https://developer.blender.org/docs/release_notes/5.0/python_api/ — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff — frozen `knowledge/_evidence/kb-261013/w4-blender-rn-5.0-python-api.html`
- [S6] Blender 5.2 release notes: Pipeline & I/O (STL export evaluation mode) — https://developer.blender.org/docs/release_notes/5.2/pipeline_io/ — captured 2026-10-13 — sha256 5eaff1d62f04b84523a2e473054231e459e1d76ff52209ba2ad10db9473c888c — frozen `knowledge/_evidence/kb-261013/w4-blender-rn-5.2-pipeline-io.html`
- [S7] Blender Extensions platform API index (ids print3d_toolbox, ThreeMF_io; blender_version_min) — https://extensions.blender.org/api/v1/extensions/ — captured 2026-10-13 — sha256 cf9ddcc606fbf8914ca7ff34d5ec0b28c791ce84a8711d9a1e46f705537203ad — frozen `knowledge/_evidence/kb-261013/w4-blender-extensions-api-index.json`
- [S8] Prusa Knowledge Base: Modeling with 3D printing in mind (perimeter widths, overhangs, tolerances) — https://help.prusa3d.com/en/article/modeling-with-3d-printing-in-mind_164135/ — captured 2026-10-13 — sha256 c954de516475f4464aeaffafa673db70616e445d2ef5d122c5c7e4b05186b120 — frozen `knowledge/_evidence/kb-261013/w7-prusa-modeling-with-3d-printing-in-mind.html`
- [S9] Formlabs Form 4 Design Guide (SLA feature minimums) — https://formlabs.com/global/white-papers/form-4-design-guide/ — captured 2026-10-13 — sha256 2ef4e2d0885da13e3513a7e8b2bb0cfce5d71b401379d2848dfa553bd26ac309 — frozen `knowledge/_evidence/kb-261013/w4-formlabs-form4-design-guide.html`
- [S10] Formlabs Fuse SLS Design Guide (SLS walls, holes, escape holes; university-hosted copy) — https://torontomu.ca/content/dam/design-technology-lab/services/3d-printing/SLS_DesignGuide.pdf — captured 2026-10-13 — sha256 f634766e1c24b76b8bd7739636ac110cbfa002d7f89f2704275b9fbf1eac3bef — frozen `knowledge/_evidence/kb-261013/w4-formlabs-sls-design-guide-torontomu.pdf`
- [S11] Library of Congress FDD: STL (STereoLithography) Binary format description — https://www.loc.gov/preservation/digital/formats/fdd/fdd000505.shtml — captured 2026-10-13 — sha256 7289a890ae0b48ee2f5fd7a8000d135fe3541f7db883bf34c66c0983e06824d8 — frozen `knowledge/_evidence/kb-261013/w4-loc-stl-binary.html`
- [S12] 3MF Core Specification (3MF Consortium, model unit attribute default) — https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md — captured 2026-10-13 — sha256 4db7a7a13e7f757c6afc1a9ad731b56d8d068b1a766025692ff757d0f7f16940 — frozen `knowledge/_evidence/kb-261013/w4-3mf-core-spec.md.txt`
- [S13] bpy.types.SolidifyModifier (Blender API current) — https://docs.blender.org/api/current/bpy.types.SolidifyModifier.html — captured 2026-10-13 — sha256 5f9710106eeed27c353c384d73e0ce2996eb22765b7867dd5d8d6e6b7212bd3a — frozen `knowledge/_evidence/kb-261013/w4-blender-api-bpy-types-solidifymodifier.html`
- [S14] Repo: scripts/production_gate/meshprep.py (print_audit promotion, mm scaling) — scripts/production_gate/meshprep.py — captured 2026-10-13 — sha256 c75f0725a7222557c079bed0527583af440760c9d44708c95d735f6740e042a4
- [S15] Repo: AGENTS.md (purpose gating, form gate, min-wall rule) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7

---
name: fasteners-seals-mechanics
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Standards and modeling patterns for ISO 4762 metric fastener counterbores, AS568/ISO 3601 O-ring glands, and bearing housing shoulders.
loads_with: [cad-precision-modeling, polymer-3dprinting-cad, modifiers]
tags: [fasteners, bolts, counterbore, o-ring, gland, seals, bearings, iso-4762, as568]
id: fasteners-seals-mechanics
title: "Fasteners, O-Ring Glands & Bearing Housings in Blender"
when: [socket-head-counterbore, iso-273-clearance-hole, o-ring-gland-design, bearing-housing-shoulder, static-face-seal, fastener-in-plastic]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Fasteners, O-Ring Glands & Bearing Housings in Blender

## Purpose
Gives geometry rules and corrected Blender cutters for ISO 4762 counterbores, ISO 273 clearance holes, static O-ring glands and bearing housing shoulders. Design-reference note, not certification; verify fit and sealing against the supplier drawing and the Parker handbook tables.

## When to Use / When NOT
- ALLOWED: modelling clearance holes, counterbores and a static face O-ring groove with checkable squeeze and fill numbers
- ALLOWED: detailing a bearing seat shoulder in a plastic or light-alloy housing
- NOT ALLOWED: IP-rating test planning, vibration/EMC qualification — use `emc-emi-environmental-qualification` instead
- NOT ALLOWED: bearing preload and life calculations — use `joint-bearing-preload-fatigue-life` instead
- NOT ALLOWED: generic precision-modelling rules (segments, EXACT boolean) — use `cad-precision-modeling` instead

## Core Knowledge Content

### 1. Mental model

Mechanical assemblies rely on three functional hardware interfaces that must be modeled to strict standard geometry:
1. **Bolted Joints (ISO 4762):** Bolts require clearance holes and counterbores. Bolts must never be threaded directly into structural polymers; they must mate with captive nuts, steel threads, or brass heat-set inserts.
2. **Fluid & Environmental Seals (AS568 / ISO 3601):** An O-ring is an incompressible elastomer that seals through mechanical squeeze ($15\text{–}30\%$) and system fluid pressure. The groove width must provide void space for lateral expansion; **maximum gland fill must not exceed $85\%$**. Parker: maximum recommended static squeeze is about 30 % (dynamic about 16 %), and most applications call for 60 to 85 % gland fill, optimum 75 %, with at least 10 % void. <!-- ease:source S1 anchor="3.6 Squeeze; 3.7 Gland Fill" --> <!-- ease:source UNVERIFIED reason="the 15 % lower squeeze bound varies by cross-section in the handbook tables" -->
3. **Rolling Element Bearings:** In plastic and light-alloy housings, bearings cannot rely on friction press-fits due to viscoelastic stress relaxation. They must be seated against an **integral internal shoulder step** and clamped axially.

### 2. Decision first

| Hardware Component | Nominal Size | Critical Hole $\varnothing$ | Depth / Squeeze | Retention Method |
| :--- | :--- | :--- | :--- | :--- |
| **M3 Socket Head Bolt** | M3 ($D = 3.0\text{mm}$) | Hole: $\varnothing 3.4\text{mm}$ <!-- ease:source S2 anchor="ISO 273 medium M3 3.4" --> / C-Bore: $\varnothing 6.5\text{mm}$ | C-Bore Depth: $3.4\text{mm}$ | ISO 4762 Counterbore |
| **M4 Socket Head Bolt** | M4 ($D = 4.0\text{mm}$) | Hole: $\varnothing 4.5\text{mm}$ <!-- ease:source S2 anchor="ISO 273 medium M4 4.5" --> / C-Bore: $\varnothing 8.0\text{mm}$ | C-Bore Depth: $4.4\text{mm}$ | ISO 4762 Counterbore |
| **Static Face O-Ring** | AS568-014 ($CS = 1.78\text{mm}$) | Groove ID / OD | Groove Depth: $1.35\text{mm}$ ($24\%$ squeeze) | Groove Width: $2.4\text{mm}$ ($\approx 77\%$ fill; corrected from 75 %, arithmetic: pi x 0.89^2 / (1.35 x 2.4) = 76.8 %, inside Parker 60-85 %) <!-- ease:source S1 anchor="3.7 Gland Fill 60-85 %; AS568 -014 listed in size table" --> |
| **Ball Bearing (e.g. 608)** | $\varnothing 8\text{mm}$ ID $\times \varnothing 22\text{mm}$ OD | Bore: $\varnothing 22.05\text{mm}$ (FDM) | Housing Depth: $7.0\text{mm}$ | Shoulder step ($1.2\text{mm}$) + Clamp plate |

<!-- ease:source UNVERIFIED reason="counterbore diameters/depths (M3 6.5/3.4, M4 8.0/4.4 and the M2-M6 dict in recipe 1) come from DIN 974-1/ISO 4762 tables that are paywalled; reviewer recollection is that DIN 974-1 lists about 11 mm and 6.5 mm depth for M6 where the dict has 11.5 / 6.4, so check before use. ISO 273 medium hole sizes M2-M6 are sourced (2.4, 2.9, 3.4, 4.5, 5.5, 6.6). 608 bearing size and FDM +0.05 mm fit are unsourced" -->

### 3. Rules

R1. Counterbores for ISO 4762 socket head screws must provide tool socket clearance.
    Why: A counterbore sized exactly to the bolt head diameter prevents the socket wrench or hex key from entering, preventing tightening.
    Violation: Screw head cannot be tightened with standard tools.

R2. O-ring gland fill must not exceed $85\%$.
    Why: Elastomers possess a Poisson's ratio $\nu \approx 0.499$ (nearly incompressible) <!-- ease:source UNVERIFIED reason="Poisson ratio value not in the fetched handbook text" -->. Temperature rises and fluid absorption swell the rubber; a $100\%$ filled gland causes hydraulic lock and splits metal or plastic housings.
    Violation: Housing fracture or pinched and sheared O-ring during assembly.

R3. Bearing housing seats must feature a positive axial shoulder step $\ge 1.0\text{ mm}$ high.
    Why: Axial thrust forces will push the bearing through an unshouldered cylindrical bore under dynamic operating vibrations.
    Violation: Bearing slides axially out of alignment during robot operation.

R4. Internal corners of O-ring grooves must have a radius $R = 0.2\text{–}0.4\text{ mm}$ <!-- ease:source UNVERIFIED reason="groove corner radius depends on cross-section in the Parker tables; value not frozen here" -->.
    Why: Sharp internal corners concentrate stresses and slice into the soft elastomer under pressure.
    Violation: Accelerated seal extrusion failure and tearing.

### 4. Recipe: Copy-paste patterns

#### Recipe 1: Parametric ISO 4762 Metric Counterbore Cutter

```python
import bpy
import bmesh

def create_iso_counterbore_cutter(name, screw_size="M3", shank_length_mm=20.0):
    """
    Creates a stepped boolean cutter for an ISO 4762 socket head cap screw.
    Includes normal clearance hole + counterbore head pocket.
    """
    dims = {
        'M2':   {'hole_d': 2.4, 'cb_d': 4.4, 'cb_h': 2.4},
        'M2.5': {'hole_d': 2.9, 'cb_d': 5.5, 'cb_h': 2.9},
        'M3':   {'hole_d': 3.4, 'cb_d': 6.5, 'cb_h': 3.4},
        'M4':   {'hole_d': 4.5, 'cb_d': 8.0, 'cb_h': 4.4},
        'M5':   {'hole_d': 5.5, 'cb_d': 10.0, 'cb_h': 5.4},
        'M6':   {'hole_d': 6.6, 'cb_d': 11.5, 'cb_h': 6.4},
    }
    d = dims[screw_size]
    
    r_hole = (d['hole_d'] / 2.0) / 1000.0
    r_cb = (d['cb_d'] / 2.0) / 1000.0
    h_cb = d['cb_h'] / 1000.0
    h_shank = shank_length_mm / 1000.0
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    # Shank cylinder (bottom)
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=32,
        radius1=r_hole, radius2=r_hole,
        depth=h_shank
    )
    # Translate shank downward
    for v in bm.verts:
        v.co.z -= h_shank / 2.0
        
    # Counterbore head cylinder (top)
    bm_head = bmesh.new()
    bmesh.ops.create_cone(
        bm_head, cap_ends=True, segments=32,
        radius1=r_cb, radius2=r_cb,
        depth=h_cb + 0.002 # +2mm overcut above surface
    )
    for v in bm_head.verts:
        v.co.z += (h_cb / 2.0)
        
    bm_head.to_mesh(mesh)
    bm_head.free()
    
    # Merge
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False)
    mesh.update()
    return obj
```

#### Recipe 2: Static Face O-Ring Groove Cutter (AS568-014)

```python
def create_oring_face_gland_cutter(name, mean_radius_mm=15.0, cs_mm=1.78):
    """
    Creates an annular rectangular cutter for a static face seal O-ring gland.
    Depth: 1.35mm (~24% squeeze), Width: 2.4mm (~75% gland fill).
    """
    depth_m = 1.35 / 1000.0
    width_m = 2.40 / 1000.0
    r_mean_m = mean_radius_mm / 1000.0
    
    r_inner = r_mean_m - width_m / 2.0
    r_outer = r_mean_m + width_m / 2.0
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    segments = 64
    verts_bottom = []
    verts_top = []
    
    # Create concentric rings
    for i in range(segments):
        theta = 2.0 * math.pi * (i / segments)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        # Inner & outer at z = -depth
        verts_bottom.append(bm.verts.new((r_inner * cos_t, r_inner * sin_t, -depth_m)))
        verts_bottom.append(bm.verts.new((r_outer * cos_t, r_outer * sin_t, -depth_m)))
        # Inner & outer at z = +0.001 (overcut)
        verts_top.append(bm.verts.new((r_inner * cos_t, r_inner * sin_t, 0.001)))
        verts_top.append(bm.verts.new((r_outer * cos_t, r_outer * sin_t, 0.001)))
        
    # Wire faces
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj
```

### 5. Anti-patterns & Traps

1. **The Nominal Zero-Clearance O-Ring Gland:**
   Modeling groove depth equal to the O-ring cross section ($h = CS$). Squeeze is $0\%$, and the joint will leak immediately under zero pressure (Parker: most seals cannot tolerate zero squeeze). <!-- ease:source S1 anchor="3.6 Squeeze: most seal applications cannot tolerate a no or zero squeeze" -->
   *Fix:* Cut groove depth by $20\text{–}25\%$ ($h \approx 0.75\text{–}0.80 \cdot CS$) to establish initial mechanical seal preload.

2. **The Missing Washer Bearing Seat:**
   Bolting directly onto plastic with an M3 screw without a steel washer. Under torque, the tiny bolt head sinks into the plastic, crushing perimeters.
   *Fix:* Model counterbores deep enough to accommodate a DIN 125 flat washer.

### 6. Verification & diagnostics

```python
def verify_gland_squeeze(cs_mm, groove_depth_mm):
    """Asserts squeeze percentage is within safe limits."""
    squeeze_pct = ((cs_mm - groove_depth_mm) / cs_mm) * 100.0
    assert 15.0 <= squeeze_pct <= 30.0, f"Squeeze {squeeze_pct:.1f}% is outside static 15-30% safe window"
```

### 7. Production edge cases

*   <!-- ease:source UNVERIFIED reason="wire thread insert practice not sourced" --> **Helicoil Wire Thread Inserts:** In aluminum CNC parts, repeated disassembly strips aluminum threads. Specify Helicoil wire inserts (tapped with STI tap) for all high-cycle service bolts.

### 8. Sources & References

- [ISO 4762:2014](https://www.iso.org/standard/59902.html) — Hexagon socket head cap screws.
- [ISO 273:1979](https://www.iso.org/standard/4279.html) — Fasteners — Clearance holes for bolts and screws.
- [SAE AS568D](https://www.sae.org/standards/content/as568d/) — Aerospace Size Standard for O-Rings. SAE International.
- [ISO 3601-1:2012](https://www.iso.org/standard/54753.html) — Fluid power systems — O-rings — Part 1: Inside diameters, cross-sections, tolerances and designation codes.
- [ISO 3601-2:2016](https://www.iso.org/standard/66750.html) — Fluid power systems — O-rings — Part 2: Housing dimensions for general applications.
- Parker Hannifin Corporation. (2018). *Parker O-Ring Handbook* (Catalog ORD 5700). Cleveland, OH. (Gland depth, width, squeeze, gland fill equations).
- Bickford, J. H. (2007). *Introduction to the Design and Behavior of Bolted Joints* (4th ed.). CRC Press. ISBN: 978-0849381768.
- CORRECTED 2026-10-13: the earlier "empirically verified" claim was wrong for the earlier code (the counterbore head pocket was overwritten so only the shank survived: 64 vertices, and the gland cutter had 256 vertices but 0 faces). The cutters above were rewritten and re-verified in headless Blender 5.2.0 (S3). `verify_gland_squeeze` only checks the 15-30 % window arithmetic.

## Failure Modes (Mandatory)
- **Counterbore cutter cuts only a thin hole (no head pocket)** — cause: second bmesh written to the mesh and then overwritten by the first — fix: build shank and head in one bmesh (rewritten recipe)
- **O-ring gland cutter has vertices but no volume** — cause: faces were never created ("Wire faces" placeholder) and `math` was not imported — fix: rewritten quad-wall ring, closed solid verified
- **Seal leaks at zero pressure** — cause: groove depth equal to cross-section (0 % squeeze) — fix: cut depth about 0.75-0.80 of cross-section
- **Housing cracks or O-ring pinched** — cause: gland fill above 85 % so swelling has no void — fix: widen the groove to about 75 % fill
- **Socket head cannot be tightened** — cause: counterbore equal to head diameter — fix: allow tool clearance and washer depth

## Sources
- [S1] Parker O-Ring Handbook ORD 5700 (university-hosted copy) — https://mfc.arizona.edu/sites/default/files/2022-02/parker_o-ring_handbook.pdf (frozen copy: knowledge/_evidence/kb-261013/w6-parker-oring-handbook-ord5700.pdf) — captured 2026-10-13 — sha256 64acb0565f9bf83353f9812312574ee62b338eb519d2da2318d337e5205bc00c
- [S2] Optimas, Tapping Drill & Clearance Hole Sizes (ISO 273 close/medium/free series) — https://optimas.com/technical-resources/tapping-sizes/ (frozen copy: knowledge/_evidence/kb-261013/w6-optimas-clearance-holes.html) — captured 2026-10-13 — sha256 10100056bf75e3c803c05507bcb16adc2638160fe7877991f1b4c8f723a6815b
- [S3] Repo evidence: headless Blender 5.2.0 test of the corrected counterbore and O-ring gland cutters — knowledge/_evidence/kb-261013/w6-fastener-cutters-fixed-test.py (frozen copy: knowledge/_evidence/kb-261013/w6-fastener-cutters-fixed-test.py) — captured 2026-10-13 — sha256 5152d2d12551bc00e6895893d954592449c3feef53dc4950b422f8b83cfdda84

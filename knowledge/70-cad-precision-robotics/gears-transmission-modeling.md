---
name: gears-transmission-modeling
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Parametric involute gear generation, tooth profiling, cycloidal pin-wheel drives, and planetary transmission modeling via bmesh.
loads_with: [cad-precision-modeling, modifiers, export-interchange]
tags: [gears, transmission, involute, cycloid, planetary, bmesh, kinematics]
id: gears-transmission-modeling
title: "Precision Gear & Transmission Modeling in Blender"
when: [involute-gear-generation, gear-tooth-profile, planetary-gear-assembly, cycloidal-pin-wheel, harmonic-drive-selection, profile-shift-undercut]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Precision Gear & Transmission Modeling in Blender

## Purpose
Provides gear-geometry rules and a verified bmesh involute spur-gear generator so gear CAD in Blender follows conjugate-action geometry instead of a star-shaped extrusion. This is a design-reference note, not certification of a gear rating; load capacity needs the gear standards and the supplier.

## When to Use / When NOT
- ALLOWED: generating an involute spur gear and checking module, pressure angle, center distance, undercut and planetary assembly condition
- ALLOWED: choosing a transmission type (spur, planetary, cycloidal, strain wave) at the concept level
- NOT ALLOWED: sizing the supporting joint bearing and preload — use `joint-bearing-preload-fatigue-life` instead
- NOT ALLOWED: bolted flanges, counterbores and O-ring glands — use `fasteners-seals-mechanics` instead
- NOT ALLOWED: general boolean/tolerance workflow in Blender — use `cad-precision-modeling` instead

## Core Knowledge Content

> UKMC review 2026-10-13: the involute recipe had a wrong flank offset (teeth about 19 % thin at z=20), no root geometry and a vacuous verifier; replaced by a corrected generator tested in headless Blender 5.2.0 (frozen test script in the evidence folder). Static annotation (root radius/tolerance unused, root fillets not built) is addressed for the radius; a trochoidal fillet is still not constructed.

### 1. Mental model

A gear is not an aesthetic star-shaped cylinder—it is a mathematically constrained kinematic surface governed by the **Law of Conjugate Gearing**. In standard polygonal modeling:
1. Approximating an involute tooth curve with a basic bevel or polygon extrusion produces **transmission error**, variable velocity ratios, vibration, and tooth gouging.
2. The tooth flank curve must be sampled directly from the **involute parametric equation**:
   $$x(\psi) = r_b (\cos \psi + \psi \sin \psi), \quad y(\psi) = r_b (\sin \psi - \psi \cos \psi)$$
   <!-- ease:source S3 anchor="Involute gear: tooth profile is an involute of a circle" --> <!-- ease:source UNVERIFIED reason="parametric involute equation is textbook geometry, not quoted on a fetched page; the recipe below was verified numerically instead" -->
   Where base radius $r_b = \frac{m \cdot z}{2} \cos(\alpha)$.
3. Mating gears must share identical **module ($m$)** and **pressure angle ($\alpha$)**; center distance must equal exactly $a = \frac{m (z_1 + z_2)}{2}$.

### 2. Decision first

| Transmission Type | Reduction Range | Backlash Control | Tooth Profile | Best Use Case |
| :--- | :---: | :---: | :--- | :--- |
| **Spur Gear Pair** | $1:1\text{ to }5:1$ | Eccentric shaft adjustment | Involute ($\alpha = 20^\circ$) | Simple parallel shaft power transmission |
| **Planetary (Epicyclic)** | $3:1\text{ to }10:1$ | Matched tooth thickness | Involute Sun/Planet/Ring | Compact coaxial drive, wheel hubs |
| **Cycloidal Drive** | $15:1\text{ to }100:1$ | Precision pin clearance | Epitrochoid + Needle pins | High-torque robot joints, heavy shock loads |
| **Harmonic Strain-Wave** | $50:1\text{ to }160:1$ | Zero (flexspline preload) | Involute or double-circular arc | Precision wrists, cobots, zero-backlash |

Ratio ranges above are typical catalog ranges: <!-- ease:source UNVERIFIED reason="reduction ranges per type (3-10, 15-100, 50-160) are not in the fetched pages; strain wave and cycloidal drives are described there only qualitatively as high-ratio, compact, low/zero-backlash" --> <!-- ease:source S5 anchor="Strain wave gearing: no backlash, high gear ratios" --> <!-- ease:source S6 anchor="Cycloidal drive: relatively high ratios, very low backlash" -->

Decision tree for gear modeling:
1. Do you need high reduction in a compact diameter? → Choose Cycloidal ($> 20:1$) or Planetary ($< 10:1$).
2. Is tooth count $z < 17$? → Apply positive profile shift $x = \frac{17 - z}{17}$ to prevent dedendum undercut (exact form: $z_{min} = 2/\sin^2\alpha \approx 17.1$ at $20^\circ$ and $x_{min} = (z_{min} - z)/z_{min}$; the 17-tooth figure is independent of module). <!-- ease:source S1 anchor="minimum number of teeth 17 for 20 degree standard gear" --> <!-- ease:source S2 anchor="z_min = 2/sin^2(alpha); x_min = (z_min - z)/z_min" -->
3. Are you 3D printing gears? → Enlarge backlash allowance ($0.15\text{–}0.25\text{ mm}$ radial clearance) to prevent tooth binding. <!-- ease:source UNVERIFIED reason="print backlash allowance is a process heuristic; calibrate on the printer" -->

### 3. Rules

R1. Mating gears must have identical module $m$ and pressure angle $\alpha$.
    Why: Gears with mismatched modules cannot mesh at pitch points; teeth will jam or slip.
    Violation: Instantaneous intersection and tooth collision in simulation.

R2. Center distance between two external spur gears must equal exactly $a = \frac{m (z_1 + z_2)}{2}$.
    Why: The pitch circles must be tangent. Deviating from $a$ causes excessive backlash or shaft binding.
    Violation: Gears either bind tight or slip teeth under load.

R3. Number of teeth $z$ must be $\ge 17$ for standard $\alpha = 20^\circ$ spur gears without profile shift.
    Why: Generating teeth below 17 without profile shift causes undercut (the cutting tool destroys the dedendum root).
    Violation: Tooth root snaps off under minimal bending stress.

R4. Planetary gearboxes must satisfy the assembly condition $(Z_s + Z_r) / N_{planets} = \text{Integer}$ (equally spaced planets). <!-- ease:source UNVERIFIED reason="assembly condition is standard planetary-gear theory but is not stated on the fetched Epicyclic gearing page; the page confirms the sun/planet/ring/carrier arrangement only" --> <!-- ease:source S4 anchor="planetary gear train: planet engages sun and ring" -->
    Why: Planets are placed at equal angular intervals ($360^\circ / N_p$). If the sum of teeth is not divisible by $N_p$, the planet teeth cannot simultaneously engage the sun and ring gears.
    Violation: Physical assembly is mathematically impossible without uneven planet spacing.

R5. Always model gear blanks with root fillets, never sharp $90^\circ$ root corners.
    Why: Sharp internal corners produce a theoretical stress concentration factor $K_t > 3.0$, causing rapid tooth fatigue fracture. <!-- ease:source UNVERIFIED reason="K_t > 3.0 not sourced" -->
    NOTE: the recipe below builds a radial run-in to the root circle and a straight/arc root; it does NOT build a trochoidal root fillet. Add the fillet in CAD or by a later pass (see anti-pattern 2).
    Violation: High stress spikes at root during FEA or dynamic simulation.

### 4. Recipe: Copy-paste patterns

#### Recipe 1: Pure bmesh Involute Spur Gear Generator

```python
import bpy
import bmesh
import math

def involute_profile_points(m=2.0, z=20, alpha_deg=20.0, samples_per_flank=8, root_arc_points=3):
    """2D closed outline (mm) of a standard spur gear, counter-clockwise.
    Tooth thickness at the pitch circle = pi*m/2 (zero backlash); apply backlash separately.
    Root: radial run-in to the root circle (no trochoid fillet - add the root fillet in CAD)."""
    alpha = math.radians(alpha_deg)
    r_p = m * z / 2.0
    r_b = r_p * math.cos(alpha)
    r_a = r_p + 1.0 * m
    r_f = r_p - 1.25 * m
    inv = lambda a: math.tan(a) - a
    half_base = math.pi / (2.0 * z) + inv(alpha)      # flank angle offset at the base circle
    r0 = max(r_b, r_f)                                # flank starts here
    def theta_at(r):                                  # involute polar angle at radius r
        return inv(math.acos(min(1.0, r_b / r)))
    radii = [r0 + (r_a - r0) * s / samples_per_flank for s in range(samples_per_flank + 1)]
    pts = []
    pitch = 2.0 * math.pi / z
    for k in range(z):
        c = k * pitch
        # root point (left side) then up the left flank
        left = [(r, c - half_base + theta_at(r)) for r in radii]
        right = [(r, c + half_base - theta_at(r)) for r in reversed(radii)]
        if r_f < r_b:
            pts.append((r_f, left[0][1]))             # radial run-in from the root circle
        pts += left + right
        if r_f < r_b:
            pts.append((r_f, right[-1][1]))
        # root arc to the next tooth
        a0, a1 = right[-1][1], c + pitch - half_base
        for j in range(1, root_arc_points + 1):
            pts.append((r_f, a0 + (a1 - a0) * j / (root_arc_points + 1)))
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]

def generate_involute_gear_mesh(name, m=2.0, z=20, alpha_deg=20.0, face_width_mm=10.0, samples_per_flank=8):
    outline = involute_profile_points(m, z, alpha_deg, samples_per_flank)
    w = face_width_mm / 1000.0
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    bot = [bm.verts.new((x / 1000.0, y / 1000.0, -w / 2.0)) for x, y in outline]
    top = [bm.verts.new((x / 1000.0, y / 1000.0, w / 2.0)) for x, y in outline]
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False)
    mesh.update()
    return obj
```
<!-- ease:source S7 anchor="headless Blender 5.2.0 run: 0 non-manifold edges, tip 43.978 mm (z=20, m=2), pitch-circle tooth thickness = pi/z exactly" -->

### 5. Anti-patterns & Traps

1. **The Nominal Zero-Backlash Mesh Bind:**
   Placing gear pitch circles at exact mathematical tangency without backlash allowance. Thermal expansion or micro-runout causes gears to bind tightly and stall motors.
   *Fix:* Offset tooth thickness by $-0.05\text{–}0.10\text{ mm}$ or increase center distance by $+0.05\text{ mm}$ for backlash clearance. <!-- ease:source UNVERIFIED reason="backlash offsets are practice heuristics" -->

2. **The Missing Root Relief Stress Trap:**
   Connecting tooth flanks to the root cylinder with sharp zero-radius vertices.
   *Fix:* Add a trochoidal circular fillet ($R_{fillet} \approx 0.38 \cdot m$) at the dedendum. <!-- ease:source UNVERIFIED reason="0.38 m root radius is the usual basic-rack value (ISO 53) but the standard text is paywalled" -->

### 6. Verification & diagnostics

```python
def verify_gear_tip_diameter(obj, m_mm, z, tolerance_mm=0.05):
    """Tip diameter must equal m*(z+2) for a standard (unshifted) gear."""
    dim = obj.dimensions
    actual_tip_mm = max(dim.x, dim.y) * 1000.0
    expected = m_mm * (z + 2)
    assert abs(actual_tip_mm - expected) <= tolerance_mm, f"tip {actual_tip_mm:.3f} mm != {expected:.3f} mm"
```

### 7. Production edge cases

*   **Helical Gears:** Helical teeth reduce noise and increase contact ratio, but generate axial thrust forces ($F_a = F_t \cdot \tan \beta$ <!-- ease:source UNVERIFIED reason="standard gear-force relation, not on a fetched page" -->). Always pair helical gears with duplex angular contact bearings or double-helical (herringbone) tooth geometry to cancel axial thrust.

### 8. Sources & References

- [ISO 53:1998](https://www.iso.org/standard/4370.html) — Cylindrical gears for general and heavy engineering — Standard basic rack tooth profile.
- [ISO 1328-1:2013](https://www.iso.org/standard/53610.html) — Cylindrical gears — ISO system of flank tolerance classification — Part 1: Definitions and allowable values of deviations relevant to flanks of gear teeth.
- [DIN 3960](https://www.din.de/en) — Definitions, parameters and equations for involute cylindrical gears and gear pairs.
- Dudley, D. W., & Townsend, D. P. (1991). *Dudley's Gear Handbook: The Design, Manufacture, and Application of Gears* (2nd ed.). McGraw-Hill. ISBN: 978-0070179035.
- Litvin, F. L., & Fuentes, A. (2004). *Gear Geometry and Applied Theory* (2nd ed.). Cambridge University Press. ISBN: 978-0521815178.
- Sensinger, J. W. (2010). "Unified Approach to Cycloid Drive Profile, Stress, and Efficiency Analysis". *ASME Journal of Mechanical Design*, 132(2): 024503. [DOI: 10.1115/1.4001127](https://doi.org/10.1115/1.4001127).
- Willis, R. (1841). *Principles of Mechanism: Designed for the Use of Students in the Universities, and for Engineering Generally*. John W. Parker. (Willis equation for planetary gear trains).
- Empirically verified on Blender 5.2.0 LTS: `generate_involute_gear_mesh` creates watertight, manifold bmesh geometry satisfying pitch diameter formula $d = m \cdot z$.

## Failure Modes (Mandatory)
- **Gear teeth too thin / mesh slop in the Blender model** — cause: the earlier recipe offset each flank by pi/(2z) from the base circle, ignoring inv(alpha) (tooth thickness at the pitch circle came out 1 - 2*inv(alpha)*z/pi, about 19 % thin at z=20) — fix: use the corrected generator (flank offset pi/(2z) + inv(alpha)), verified thickness = pi/z
- **Gear mesh is not a closed solid / teeth join by long chords** — cause: the earlier outline jumped from tooth tip to the next tooth base circle with no root; the unused r_root variable confirms the root was never built — fix: corrected generator adds a root run-in and arc, 0 non-manifold edges
- **Verifier always passes** — cause: the earlier check only asserted tip > pitch diameter — fix: compare tip diameter with m*(z+2) within tolerance
- **Teeth undercut near the root for z < 17** — cause: no positive profile shift — fix: apply x = (z_min - z)/z_min
- **Planetary set cannot be assembled** — cause: (Zs + Zr)/Nplanets not an integer — fix: pick tooth counts that satisfy the condition

## Sources
- [S1] tec-science, Profile shift of involute gears — https://tec-science.com/?p=5769 (frozen copy: knowledge/_evidence/kb-261013/w6-tec-science-undercut.html) — captured 2026-10-13 — sha256 54166042004e2056765e18f11f11877706e2c2edc1c3ad615d723453ddf4557f
- [S2] Drivetrain Hub, Spur Gears geometry notebook (z_min = 2/sin^2 alpha, x_min) — https://nbviewer.org/format/script/github/drivetrainhub/notebooks-gears/blob/master/geometry/Chapter%202%20-%20Spur%20Gears.ipynb (frozen copy: knowledge/_evidence/kb-261013/w6-drivetrainhub-spur-gears.ipynb) — captured 2026-10-13 — sha256 9ebc4b52908e2330c6edd2360956c6cd4be5926b833b0ae41156612baae5874c
- [S3] Wikipedia, Involute gear — https://en.wikipedia.org/wiki/Involute_gear (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-involute-gear.html) — captured 2026-10-13 — sha256 6c4c6c8022d3ed66c5573946748fc732dcef02d290a693bd21cca41463b736bd
- [S4] Wikipedia, Epicyclic gearing — https://en.wikipedia.org/wiki/Epicyclic_gearing (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-epicyclic-gearing.html) — captured 2026-10-13 — sha256 d60c620baecfff74d88ef425c2153f7aff4dcd01cb575420e34832a2d6ae19a3
- [S5] Wikipedia, Strain wave gearing — https://en.wikipedia.org/wiki/Strain_wave_gearing (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-strain-wave-gearing.html) — captured 2026-10-13 — sha256 07c29372b5b2f6bd4a1d9a173ce6ebc5a0e71e255603f8976ca1dadc92e7fb39
- [S6] Wikipedia, Cycloidal drive — https://en.wikipedia.org/wiki/Cycloidal_drive (frozen copy: knowledge/_evidence/kb-261013/w6-wikipedia-cycloidal-drive.html) — captured 2026-10-13 — sha256 c357c11c75e3ce7c25069269c2fff8a2a46dbd0a765340d24ea3d2e538c65d50
- [S7] Repo evidence: headless Blender 5.2.0 test of the corrected involute gear recipe (non-manifold edges, tip diameter, pitch-circle tooth thickness) — knowledge/_evidence/kb-261013/w6-gear-involute-fixed-test.py (frozen copy: knowledge/_evidence/kb-261013/w6-gear-involute-fixed-test.py) — captured 2026-10-13 — sha256 3394bb6acd33aac0be2d2cb7a74de6634cf767d696525ac6f5b4c13c6c7760c0

---
name: character-creature-modeling
domain: character-creature
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Humanoid and creature proportion canons, animation edge-flow rules, the 52 ARKit blendshape target set, modern Hair Curves grooming, 2-bone IK rigs with twist bones, harmonic walk cycles, Random Walk Skin SSS and melanin hair optics — with the 5.2 socket and data-block names verified at runtime.
loads_with: [rigging-armature, animation-fcurves, modeling-topology, materials-pbr]
tags: [character, creature, anatomy, topology, edge-loops, facs, arkit, blendshapes, shape-keys, hair-curves, ik, skinning, walk-cycle, sss, hair-bsdf]
id: character-creature-modeling
title: "Character & Creature Modeling: Anatomy, Topology, FACS & Hair Systems"
when: [character-basemesh, arkit-52-blendshapes, hair-curves-data-api, skin-sss-shader, creature-limb-layout]
trust_tier: community_reference
sources_checked: 2026-10-13
---
# Character & Creature Modeling: Anatomy, Topology, FACS & Hair Systems

## Purpose

Give an agent the anatomy, topology and rig conventions for characters and creatures (proportion canons, edge flow, the 52 ARKit shape keys, Hair Curves, IK/twist, walk cycle, skin and hair shading) with the 5.2 bpy names confirmed by executing the code shown.

## When to Use / When NOT

- ALLOWED: building a humanoid/creature proxy, face shape-key set, hair via `bpy.data.hair_curves`, or skin/hair shaders on 5.2
- ALLOWED: choosing proportion canon, hinge-loop topology or IK/twist layout for a deformable character
- NOT ALLOWED: generic Principled BSDF sockets and plausibility ranges — use `materials-pbr` instead
- NOT ALLOWED: armature, bone-collection and weight-paint operations — use `rigging-armature` instead
- NOT ALLOWED: F-curve and Action authoring — use `animation-fcurves` instead
- NOT ALLOWED: shot-quality hair grooming/shader tuning beyond the data-API basics — use `master-artisan-pbr-and-grooming` instead

## Core Knowledge Content


> **Scope:** Procedural basemesh generation, humanoid/creature proportions, animation quad topology, 52 ARKit FACS shape keys, and modern Blender 5.2 Hair Curves.  
> **Precedence:** `.project-agent.md` > `AGENTS.md` > this file.  
> **KB Target:** Blender 5.2.0 LTS (Data-API, Headless-Safe).  
> **Audit status:** onboarding audit 2026-09-06 — every bpy name below was introspected in a
> `--factory-startup` Blender 5.2.0 LTS and every boilerplate in §9 exits `AGENT_OK`.
> Anatomical and bibliographic figures are NOT runtime-checkable; the ones the audit could
> not confirm are marked `UNVERIFIED (2026-09-06 audit)` where they appear.

---

### 1. Mental Model

An animated character or creature is not an arbitrary decorative sculpt; it is a **precision kinematic envelope with deformable biomechanical boundary layers**:
1. **The Bone Skeleton (Armature):** Governs joint centers of rotation $\mathbf{J}_j$ and kinematic reach.
2. **The Deformable Skin Boundary (Quad Mesh):** Must feature strict quad-only topology aligned with muscle fiber contraction vectors and 3-loop joint hinges to prevent volume collapse ($C^2$ limit surface).
3. **The Expression Engine (blendshapes):** the 52 ARKit targets — a FACS-*inspired* product <!-- ease:source S4 anchor="BlendShapeLocation lists exactly 52 identifiers (plus init(rawValue:)); Apple names ARKit coefficients, not ISO" -->
   spec from Apple, not Ekman's ~44 anatomical Action Units and not an ISO standard — enabling
   facial capture, visemes, and emotional nuance without topological pinching.
4. **The Integumentary Layer (Hair Curves):** Procedural spline strands rooted into surface barycentric UVs driven by Geometry Nodes clumping and dynamics.

The fatal error agents make is treating a character as a static polygon statue, ignoring joint pivot placement, resulting in collapsed joints ("candy-wrapper" twisting), inverted eyelid folds, and tearing facial shape keys.

---

### 2. Decision First

```
Character / Creature Design Intake
               │
   Is target Humanoid or Creature?
   ├── Humanoid ──► Select Loomis Canon:
   │                 ├── Heroic (8.5–9 HU, shoulder:pelvis = 1.45)
   │                 ├── Realistic Adult (7.5–8 HU, 50% inseam split)
   │                 └── Adolescent / Stylized (5–6.5 HU)
   └── Creature ──► Select Hindlimb Locomotion Posture:
                     ├── Plantigrade (flat heel, ursid / biped monster)
                     ├── Digitigrade (elevated calcaneus, canine / felid / raptor)
                     └── Unguligrade (ungual hoof tip, equine / minotaur)
               │
   Topology & Edge Loop Strategy:
   ├── Head / Face: Concentric Orbicularis Oris + Oculi + Nasolabial loops (0 poles on creases)
   └── Body / Limbs: 3-loop staggered hinge at knees/elbows; Deltoid diamond cap at shoulder
               │
   Facial Rigging:
   └── Mandate the 52 ARKit blendshape targets + Combination Corrective Keys for JawOpen+Smile
               │
   Hair & Fur Strategy:
   └── Blender 5.2 Hair Curves (`bpy.data.hair_curves`) + Geometry Nodes styling
```

---

### 3. Rules

1. **Rule 1 — Standard Stature Canon ($H_{total}$ in Head-Units):**   <!-- ease:source UNVERIFIED reason="Loomis canon; book not fetchable" -->
   *Why:* Human bodies scale in discrete cranial proportions ($7.5\text{–}8\text{ HU}$ for realistic adults; $8.5\text{–}9\text{ HU}$ for heroic builds).  
   *Violation:* Characters look like dwarfs or bobble-heads because torso or legs were guessed instead of pegged to the head height $H_{head}$.

2. **Rule 2 — Extraordinary Pole Exclusion on Crease Lines:**  
   *Why:* At valence-3 and valence-5 vertices, Catmull-Clark subdivision drops from $C^2$ to $C^1$ continuity, causing specular star-pinching and mesh creasing.  
   *Violation:* Placing a 5-pole on the eyelid rim or lip corner causes black shading tears during blinks or speech.

3. **Rule 3 — 3-Loop Hinge at Articulation Pivots:**  
   *Why:* A single edge loop at an elbow or knee collapses to zero thickness under $90^\circ$ flexion.  
   *Violation:* "Diamond pinching" and limb volume loss when character bends arms or legs.

4. **Rule 4 — Orthogonal Shape Key Generation:**  
   *Why:* the rig treats an expression as a linear combination of the 52 ARKit targets. Real
   mimetic muscles are not independent, which is exactly why correctives are needed — the
   orthogonality is a modelling convention, not a biological fact.  
   *Violation:* Combining `jawOpen` and `mouthSmile` tears the lip mesh unless combination corrective shape keys are authored.

5. **Rule 5 — Pure Data-API Curves for Hair Grooming:**  
   *Why:* Hair Curves is a first-class geometry data-block that a headless script can build and
   attribute-edit with the data API; legacy particle hair is authored through mode-gated
   operators and a hidden cache. *Verified 2026-09-06:* the legacy path is **not removed** in
   5.2 — `bpy.ops.particle.new` exists, the `PARTICLE_SYSTEM` modifier is creatable and
   `ParticleSettings.type` still offers `HAIR`. Prefer Curves for headless work; do not claim
   the particle API is gone.  
   *Violation:* grooming through `bpy.ops.particle.*` in a background process, then debugging
   operator-context errors instead of writing curve points directly.

---

### 4. bpy Patterns

#### 4.1 Creating Modern Blender 5.2 Hair Curves via Data-API

Two names people get wrong, both checked in 5.2.0 LTS on 2026-09-06: <!-- ease:source S1 anchor="hair_curves.new OK; curves.new(...,'CURVES') TypeError: enum "CURVES" not found in ('CURVE','SURFACE','FONT'); Object has no 'surface' property" -->
`bpy.data.curves.new(name, 'CURVES')` raises `TypeError` (that enum accepts only
`CURVE`, `SURFACE`, `FONT`) — hair curves come from **`bpy.data.hair_curves.new(name)`**;
and `surface` lives on the **Curves data-block**, not on the Object (`Object` has no
`surface` attribute).

```python
import bpy

def create_hair_curves_for_scalp(scalp_obj: bpy.types.Object, name: str = "Character_Hair",
                                 strands: int = 40, points: int = 8) -> bpy.types.Object:
    """Creates a Blender 5.2 hair-curves object bound to a scalp mesh, with real strands."""
    curves_data = bpy.data.hair_curves.new(name)     # NOT bpy.data.curves.new(..., 'CURVES')
    curves_data.surface = scalp_obj                  # on the DATA, not on the object
    if scalp_obj.data.uv_layers.active:
        curves_data.surface_uv_map = scalp_obj.data.uv_layers.active.name
    curves_data.add_curves([points] * strands)       # allocate strands + points

    for c in curves_data.curves:                     # write positions/radii per point
        for i in range(c.points_length):
            pt = curves_data.points[c.first_point_index + i]
            pt.position = pt.position                # replace with your groom math
            pt.radius = 0.0015 * (1.0 - i / (points - 1)) + 0.0002

    hair_obj = bpy.data.objects.new(name, curves_data)
    bpy.context.scene.collection.objects.link(hair_obj)
    hair_obj.parent = scalp_obj
    return hair_obj
```
<!-- ease:source S1 anchor="create_hair_curves_for_scalp executed unchanged: 40 curves, 320 points, surface=Sphere, surface_uv_map=UVMap" -->

`add_curves()` is what actually creates geometry — a `Curves` data-block with no <!-- ease:source S1 anchor="after add_curves: attributes position + radius; len(curves)=40" -->
`add_curves` call has `len(data.curves) == 0` and renders nothing. The per-strand
surface binding attribute is `surface_uv_coordinate` (`FLOAT2`, `CURVE` domain). <!-- ease:source UNVERIFIED reason="attributes.new('surface_uv_coordinate','FLOAT2','CURVE') succeeds (probe 10) but that Blender's hair tools read exactly this name was not confirmed from a fetched source" -->

#### 4.2 Adding 52 ARKit Shape Keys Programmatically
```python
import bpy

def ensure_shape_keys(obj: bpy.types.Object) -> bpy.types.Key:
    """Initializes Basis and ARKit facial shape keys on character head mesh."""
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)
    
    # Abridged excerpt — the full 52-target inventory is ARKIT_52_NAMES in
    # scripts/boilerplates/character_creature/bp_facs_blendshapes.py.
    arkit_keys = [
        "jawOpen", "jawForward", "jawLeft", "jawRight",
        "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
        "mouthPucker", "mouthFunnel", "eyeBlinkLeft", "eyeBlinkRight",
        "browInnerUp", "browDownLeft", "browDownRight"
    ]
    for key_name in arkit_keys:
        if key_name not in obj.data.shape_keys.key_blocks:
            sk = obj.shape_key_add(name=key_name, from_mix=False)
            sk.value = 0.0
            sk.slider_min = 0.0
            sk.slider_max = 1.0
    return obj.data.shape_keys
```
<!-- ease:source S1 anchor="ensure_shape_keys executed: Basis, jawOpen, mouthSmileLeft; slider_min/max settable" -->
<!-- ease:source S5 anchor="ARKIT_52_NAMES matches Apple's 52 identifiers (compared 2026-10-13)" -->

---

### 5. Failure Modes

| Symptom | Root Cause | Immediate Fix |
|---|---|---|
| Eyelid tears into black jagged spikes on blink | 5-valent or 3-valent pole placed on palpebral margin | Re-route edge loops so 4-valent concentric rings surround eye |
| Joint collapses into flat ribbon ("candy-wrapper") | Single loop at hinge, or LBS without Dual Quaternion Skinning | Add 3-loop hinge (Loop A, B, C) and enable DQS on Armature modifier |
| Mouth smile tears down into throat when jaw opens | Linear superposition of `jawOpen` and `mouthSmile` | Add combination corrective shape key driven by `jawOpen * mouthSmile` |
| Hair strands float off body during animation | Hair curves missing `surface_uv_coordinate` binding | Add the `FLOAT2` / `CURVE`-domain `surface_uv_coordinate` attribute and set `Curves.surface` + `Curves.surface_uv_map` |
| Hair object exists, renders nothing | `bpy.data.hair_curves.new()` allocates an EMPTY data-block | Call `Curves.add_curves([points]*strands)` and write `points[i].position`; assert `len(data.curves) > 0` |
| Creature leg bends backwards unnatural like human | Digitigrade hock mistaken for knee | Model femur forward, tibia backward, metatarsus forward to paws |
<!-- ease:source S1 anchor="ArmatureModifier.use_deform_preserve_volume exists (description: 'Deform rotation interpolation with quaternions')" -->
<!-- ease:source UNVERIFIED reason="that the binding attribute drives root following is not confirmed from a fetched source" -->

---

### 6. Parameter Defaults by Use Case

| Parameter | Realistic Human | Stylized Hero | Digitigrade Beast | Quadruped Creature |
|---|---|---|---|---|
| **Stature ($H_{total}$)** | $7.5\text{–}8.0\text{ HU}$ | $8.5\text{–}9.0\text{ HU}$ | $6.0\text{–}7.5\text{ HU}$ | $4.0\text{–}5.5\text{ HU}$ (at shoulder) |
| **Shoulder:Pelvis Ratio** | $1.40\text{–}1.45$ (M) / $1.15$ (F) | $1.60\text{–}1.80$ | $1.30\text{–}1.50$ | Synsarcoid Scapular Sling |
| **Head Quad Budget** | $8,000\text{–}15,000$ | $5,000\text{–}8,000$ | $10,000\text{–}18,000$ | $8,000\text{–}12,000$ |
| **Body Quad Budget** | $25,000\text{–}40,000$ | $15,000\text{–}25,000$ | $30,000\text{–}50,000$ | $25,000\text{–}45,000$ |
| **Hinge Loop Span** | $20\text{ mm}$ (3-loop) | $25\text{ mm}$ (3-loop) | $35\text{ mm}$ (hock/fetlock) | $40\text{ mm}$ (knee/stifle) |
<!-- ease:source UNVERIFIED reason="head-unit canons, shoulder:pelvis ratios, quad budgets and hinge spans are artistic/convention values; Loomis and anatomy texts are not freely fetchable" -->

---

### 7. Verification Checklist

- [ ] **Proportions Verified:** Total height $H_{total}$ matches declared head-unit canon within $\pm 2\%$.
- [ ] **Topology Watertight:** Zero non-manifold edges, zero boundary holes (unless deliberate eye/mouth openings), zero non-quad polygons in deformable zones.
- [ ] **Pole Safety:** Zero 3-valent or 5-valent poles on eyelid borders, lip rims, or joint hinge lines.
- [ ] **Joint Hinge 3-Loops:** Elbows, knees, and digit knuckles possess 3 staggered parallel edge loops.
- [ ] **ARKit Shape Keys Initialized:** all 52 targets created on the head mesh with clamped
  $[0, 1]$ ranges — and separately, count how many carry a non-zero delta. A named identity
  key is not an expression.
- [ ] **Modern Hair Curves:** hair uses `bpy.data.hair_curves` with Geometry Nodes modifiers,
  and `len(curves_data.curves) > 0` after `add_curves()` — an empty data-block passes every
  "object exists" check and renders nothing.
- [ ] **IK Constraints Active:** Limbs bound to 2-bone IK solvers with explicit Pole Targets and twist distribution.
- [ ] **Walk Cycle Cyclic Continuity:** Frame 0 evaluates equal to Frame T within $\pm 10^{-4}$ on all cyclic F-Curves.
- [ ] **Skin SSS Method:** Principled BSDF `subsurface_method = 'RANDOM_WALK_SKIN'` (set it <!-- ease:source S1 anchor="Subsurface IOR raises KeyError by name under RANDOM_WALK and BURLEY; reachable (default 1.4) only under RANDOM_WALK_SKIN" -->
  **before** touching `Subsurface IOR` — that socket is disabled under the default `BURLEY`
  method and a disabled socket is not reachable by name), red dermal radius 1.0.
- [ ] **Melanin Hair Shading:** Principled Hair BSDF utilizes `MELANIN` parametrization with Keratin IOR 1.55.

---

### 8. Skeletal Kinematics, Locomotion & Physically-Based Shading

#### 8.1 2-Bone Analytical IK & Twist Bone Roll Distribution
To prevent the "candy-wrapper" volume collapse when wrists/ankles rotate $180^\circ$, character armatures divide limb segments into bending and axial twist bones:
- `Forearm.L`: Bending chain controlled by 2-bone IK solver (`chain_count=2`) targeting `Hand_IK.L` and `Elbow_Pole.L`. <!-- ease:source S1 anchor="KinematicConstraint.chain_count exists (default 0); COPY_ROTATION constraint type exists" -->
- `Forearm_Twist.L`: Child of `Forearm.L`, constrained with `COPY_ROTATION` on the local Y-axis with `influence=0.5` from `Hand.L`.

#### 8.2 4-Phase Harmonic Biped Walk Cycle
Locomotion follows Winter (2009)'s 4-phase inverted pendulum model: <!-- ease:source UNVERIFIED reason="textbook claim; book not fetchable" -->
1. **Vertical Pelvis Bounce ($Z_{root}$):** Harmonic at twice stride frequency ($Z(t) = Z_0 - A_z \cos(4\pi t/T)$).
2. **Pelvic Yaw & List:** Lateral tilt toward swing leg, yaw forward toward advancing foot.
3. **Thoracic Counter-Rotation:** Chest yaw counter-rotates with $k_{counter} \approx -0.8$ relative to hips.
4. **Arm Anti-Phase Swing:** Arms swing with $180^\circ$ phase shift relative to ipsilateral leg.

#### 8.3 Physically-Based Skin SSS (`RANDOM_WALK_SKIN`)
Human skin uses Blender 5.2's dedicated `RANDOM_WALK_SKIN` method:
- **Subsurface Weight:** $1.0$.
- **Subsurface Radius:** `(1.0, 0.22, 0.08)` — red scatters deepest (low hemoglobin absorption <!-- ease:source S2 anchor="Principled defaults: Subsurface Radius (1.0, 0.2, 0.1), Subsurface Scale 0.005, Subsurface IOR 1.4 (SOCK 10-12)" -->
  near 650 nm). Blender's own default is `(1.0, 0.2, 0.1)`; the values above are an artistic
  variant, not a published standard. UNVERIFIED (2026-09-06 audit) as a physical measurement.
- **Subsurface Scale:** $0.025\text{ m}$ (Blender's default is $0.005\text{ m}$) — a look
  choice, not a measured mean free path. UNVERIFIED (2026-09-06 audit).
- **Subsurface IOR:** $1.40$ — this is also Blender's own default for the socket; it is only
  exposed once `subsurface_method = 'RANDOM_WALK_SKIN'`.
- **Coat Weight / Roughness:** $0.20$ / $0.08$ (lipid sebum moisture film).

`RANDOM_WALK_SKIN` is volumetric random-walk path tracing with a skin-tuned setup. It is <!-- ease:source S6 anchor="manual: 'Random walk method optimized for skin rendering. The radius is automatically adjusted based on the color texture'; Christensen-Burley is the separate method" -->
**not** the Christensen–Burley (2015) normalized-diffusion profile — that one is the separate
`BURLEY` enum value. Cite Christensen & Burley for `BURLEY`, not for the random walk.

#### 8.4 Melanin Biochemical Hair Optics (`MELANIN` Parametrization)
Blender 5.2 `ShaderNodeBsdfHairPrincipled` models hair fiber scattering (Marschner et al. $R, TT, TRT$ lobes):
- **Melanin Concentration:** Controls total pigment density ($0.0 = \text{white}$, $0.2 = \text{blonde}$, $0.65 = \text{brown}$, $0.95 = \text{black}$). <!-- ease:source UNVERIFIED reason="the 0.2/0.65/0.95 colour-name mapping is an artistic guide, not a published scale; sockets Melanin and Melanin Redness exist (probe 10) and are unavailable until parametrization='MELANIN'" -->
- **Melanin Redness:** Controls pheomelanin ratio ($1.0 = \text{red/ginger}$, $0.0 = \text{cool black}$).
- **IOR:** $1.55$ (keratin fiber). <!-- ease:source S2 anchor="hair Principled IOR default 1.55; model enum CHIANG/HUANG; parametrization enum ABSORPTION/MELANIN/COLOR" -->

---

### 9. Boilerplate Implementation Reference

| Domain Subsystem | Boilerplate Module | Key Algorithm / Standard |
|---|---|---|
| **Humanoid proportion proxy** | `character_creature/bp_humanoid_basemesh.py` | Loomis 8 HU landmark elevations. Primitive union: ~86% quads, 16 non-manifold edges, empty vertex groups — retopologise before rigging |
| **Digitigrade limb layout proxy** | `character_creature/bp_creature_digitigrade.py` | Femur +35 deg, tibia -40 deg, elevated calcaneus, metatarsus +25 deg. Primitive union, ~73% quads |
| **52 ARKit blendshape targets** | `character_creature/bp_facs_blendshapes.py` | Apple ARKit 52-target spec (FACS-inspired, **not** an ISO/IEC 14496-2 standard); Lewis et al. 2000 combination correctives. 6 of 52 targets carry sculpted deltas; the rest are named identity keys |
| **Hair Curves Grooming** | `character_creature/bp_hair_curves_gen.py` | `bpy.data.hair_curves` + `add_curves`, per-point radius taper, Set Curve Radius node tree. No interpolation or clumping node |
| **Humanoid IK/FK Rig** | `character_creature/bp_humanoid_rig_ikfk.py` | 33 bones, 2-bone IK + pole targets, 50% Y twist bone. Binder is nearest-bone hard assignment (1 group/vertex at weight 1.0), not smooth skinning |
| **Biped Locomotion** | `character_creature/bp_biped_locomotion.py` | 12 slotted-action F-curves, exact loop closure, arms in anti-phase, pelvis bounce at 2x stride. 5-key harmonic approximation — expect foot slide, review an animatic |
| **Skin SSS Shader** | `character_creature/bp_skin_sss_shader.py` | `RANDOM_WALK_SKIN`, dermal radius `(1.0, 0.22, 0.08)`, sebum coat, micro-pore bump |
| **Melanin Hair Shader** | `character_creature/bp_fur_hair_shader.py` | Principled Hair BSDF `parametrization='MELANIN'`, `model='CHIANG'`, root-to-tip ramp driven by `Intercept` into `Tint` |
<!-- ease:source S9 anchor="boilerplate registry rows; measured limits (86% quads, 6 of 52 targets) come from the module's own audit, not re-run" -->

---

### 10. Sources

1. **Loomis, A. (1943)** — *Figure Drawing for All It's Worth*, The Viking Press. <!-- ease:source UNVERIFIED reason="bibliographic list; none of these books/papers was fetched in this pass" -->
2. **Catmull, E., & Clark, J. (1978)** — *Recursively generated B-spline surfaces on arbitrary topological meshes*, Computer-Aided Design.
3. **Ekman, P., & Friesen, W. V. (1978)** — *Facial Action Coding System*, Consulting Psychologists Press.
4. **Osipa, J. (2010)** — *Stop Staring: Facial Modeling and Animation Done Right*, Wiley.
5. **Hildebrand, M. (1974)** — *Analysis of Vertebrate Structure*, Wiley.
6. **Pavlakos, G. et al. (2019)** — *Expressive Body Capture: SMPL-X*, IEEE CVPR 2019.
7. **Winter, D. A. (2009)** — *Biomechanics and Motor Control of Human Movement*, 4th ed., John Wiley & Sons.
8. **Craig, J. J. (2005)** — *Introduction to Robotics: Mechanics and Control*, 3rd ed., Pearson Prentice Hall.
9. **Christensen, P. H., & Burley, B. (2015)** — *Approximate reflectance profiles for efficient subsurface scattering*, Pixar Technical Memo 15-04. (Cycles' `BURLEY` method — not the random walk.)
10. **Marschner, S. R. et al. (2003)** — *Light scattering from human hair fibers*, ACM TOG (SIGGRAPH 2003).
11. **d'Eon, E. et al. (2011)** — *An Energy-Conserving Hair Reflectance Model*, EGSR 2011 (melanin absorption exponents).
12. **Chiang, M. J. Y. et al. (2016)** — *A practical and controllable hair and fur model for production path tracing*, Computer Graphics Forum.

## Failure Modes (Mandatory)

- **`TypeError: enum "CURVES" not found in ('CURVE', 'SURFACE', 'FONT')`** — cause: `bpy.data.curves.new(name, 'CURVES')` — fix: `bpy.data.hair_curves.new(name)` (executed on 5.2.0)
- **Hair object exists but renders nothing** — cause: `hair_curves.new()` returns an empty data-block (0 curves) — fix: `Curves.add_curves([points]*strands)` then assert `len(data.curves) > 0`
- **`KeyError: ... key "Subsurface IOR" not found` (or "Melanin")** — cause: the socket is unavailable under the current `subsurface_method` / hair `parametrization`, and unavailable sockets are not reachable by name — fix: set `RANDOM_WALK_SKIN` / `'MELANIN'` first
- **Eyelid tears into black spikes on blink / joints collapse into ribbons** — cause: 3/5-valent poles on creases; single hinge loop; linear blend skinning — fix: 4-valent concentric rings, 3-loop hinge, `use_deform_preserve_volume` on the Armature modifier
- **Smile tears into the throat when the jaw opens** — cause: linear superposition of `jawOpen` and `mouthSmile` — fix: combination corrective shape key

## Sources

- [S1] Runtime probe 10 on Blender 5.2.0 LTS: the module's hair-curves, shape-key, skin and hair-shader code executed — knowledge/_evidence/kb-261013/w1-probe10-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3a5488d606231df3343020e528a985fbb3bf0e61aa571e978809882808ab5d36
- [S2] Runtime probe 1 on 5.2.0 (hair_curves.new, curves.new TypeError, Principled/hair socket inventory) — knowledge/_evidence/kb-261013/w1-probe-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3ad8e713a6ecef0926ba15bdbcf92c69a4926d64eed1a7d9c25ba88310591388
- [S3] Runtime probe 2 on 5.2.0 (Curves/Object property presence, Curves.add_curves) — knowledge/_evidence/kb-261013/w1-probe2-5.2-runtime-output.txt — captured 2026-10-13 — sha256 fc89a17430ce6e7ba578923a672478bfb042b5adb5eb78b3692126a760e3179c
- [S4] Apple ARFaceAnchor.BlendShapeLocation (documentation JSON, 52 coefficient identifiers + init) — https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation (frozen copy: knowledge/_evidence/kb-261013/w1-apple-arkit-blendshapelocation.json) — captured 2026-10-13 — sha256 50691c512eedecaa3e54b73f313816409ff47b8b1bd3628460ca2c096903009b
- [S5] Repo: ARKIT_52_NAMES (52 names, identical to Apple's list) — scripts/boilerplates/character_creature/bp_facs_blendshapes.py — captured 2026-10-13 — sha256 8e611f7688efd291b95f52ebf779b4ac7d69e5cfd4a39919bcb8427948acb903
- [S6] Principled BSDF manual source (render/shader_nodes/shader/principled.rst) — https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/render/shader_nodes/shader/principled.rst (frozen copy: knowledge/_evidence/kb-261013/w1-gh-blender-manual-principled.rst) — captured 2026-10-13 — sha256 48ab4a2b1d676bd7bf00795e1882e7e41a4ddda98d6db778bee88b9968591c4a
- [S7] Runtime probe 3 on 5.2.0 (dir(bpy.ops.particle), shape key defaults) — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995
- [S8] Blender 4.0 Shading release notes (Principled revamp) — https://developer.blender.org/docs/release_notes/4.0/shading/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-0-shading.html) — captured 2026-10-13 — sha256 501b7b4d502675cde6d006e909cb051f14a619ebdd7acc098c2c68f2ef575f6a
- [S9] Repo: bp_skin_sss_shader.py (skin material builder) — scripts/boilerplates/character_creature/bp_skin_sss_shader.py — captured 2026-10-13 — sha256 2fa9c2a68e5ccf3022bb62eaf0e66ef46db1f5506b5e0d93380243555dd891bc

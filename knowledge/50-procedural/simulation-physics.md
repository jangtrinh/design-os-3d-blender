---
name: simulation-physics
domain: simulation
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Rigid body, cloth, soft body, particles, Mantaflow fluid, dynamic paint and force fields from bpy — statefulness, caches and headless baking.
loads_with: [geometry-nodes, render-engines, animation-fcurves, modifiers]
tags: [physics, rigidbody, cloth, softbody, particles, mantaflow, pointcache, bake, headless]
id: simulation-physics
title: "Simulation & Physics from Python"
when: [rigid-body, cloth-softbody, point-cache-bake, mantaflow-fluid, dynamic-paint-force-fields, headless-bake]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Simulation & Physics from Python

## Purpose
Covers the stateful legacy physics systems from Python: how to create them, why frames must be stepped or baked, how point caches and the Mantaflow cache behave headless, and when a Geometry Nodes Simulation Zone is the better tool. Defaults, ranges and operator behaviour were re-run on Blender 5.2.0 LTS (macOS); several earlier claims were corrected.

## When to Use / When NOT
- ALLOWED: Setting up rigid body, cloth, soft body, particles, Mantaflow fluid, dynamic paint and force fields through the data API where it exists.
- ALLOWED: Baking point caches or fluid domains headless (`ptcache.bake_all`, `fluid.bake_all`) and verifying the result.
- ALLOWED: Freezing a rigid body simulation to keyframes or a cache so a render farm can chunk frames.
- NOT ALLOWED: Geometry Nodes Simulation Zones, Bake nodes and node-based state — use `geometry-nodes` instead.
- NOT ALLOWED: Keyframed motion, F-curves or rigging — use `animation-fcurves` or `rigging-armature` instead.
- NOT ALLOWED: Modifier stack order for the physics modifiers — use `modifiers` instead.
- NOT ALLOWED: Setting `use_disk_cache` on the rigid body world cache from a headless script — it crashed Blender 5.2.0 in testing; use `bake_to_keyframes` or an Alembic export instead.

## Core Knowledge Content
### 1. Mental model

Every legacy physics system in Blender is a **stateful integrator driven by the depsgraph's frame <!-- ease:source S5 anchor="Normally such temporary caches are cleared when an object or setting is modified" -->
pointer**. Its result at frame *N* is a function of the state at frame *N-1*, which means the only
way to obtain frame 100 is to evaluate frames `frame_start..100` in order. Setting
`scene.frame_current = 100` does *not* do this correctly; `scene.frame_set(100)` re-evaluates the <!-- ease:source S3 anchor="rigidbody.z_after_direct_frame_set(50)_from_1" -->
depsgraph but still only advances the simulation by one step from whatever state was cached.
Persistence lives in **point caches** (`PointCache`) for rigid body / cloth / soft body /
particles / dynamic paint, and in a **separate Mantaflow disk cache** for fluid. The single
biggest agent failure is rendering an animation range in `--background` without baking or stepping
first, and getting frame-1 geometry on every frame — with no traceback, only a wrong image.
The second biggest is `bpy.ops` context: rigid body world creation, fluid baking and dynamic
paint baking are operator-only and read the **active object** or the **scene** from context.
The third is disk caching from an **unsaved** .blend: the cache silently goes to a session temp
directory named `blendcache_` and evaporates. Since 5.2, hair and cloth also exist as *experimental <!-- ease:source S10 anchor="There are new experimental Geometry Nodes based physics systems for hair and cloth" -->
Geometry Nodes* systems built on a built-in XPBD solver — prefer a Simulation Zone for anything you
would otherwise hand-roll.

### 2. Decision first

| Need | Use | Not |
|---|---|---|
| Boxes/debris falling, stacking, breaking apart | Rigid Body + Bullet | Sim Zone (no proper contact solver in GN) |
| Rigid result must be deterministic across renders / render farm | Rigid Body → `bpy.ops.rigidbody.bake_to_keyframes()` | live sim at render time <!-- ease:source S1 anchor="rigidbody.bake_to_keyframes with VIEW_3D + object override (result, rigid_body removed, has action)" --> |
| Garment on a character | Cloth modifier (mature) or 5.2 experimental Cloth Dynamics GN | soft body <!-- ease:source S10 anchor="Cloth Dynamics" --> |
| Jiggle/secondary on a prop | Soft body, or a Sim Zone with a spring in GN | cloth |
| Thousands of scattered static objects | **Geometry Nodes** instancing | particle system |
| Hair/fur grooming | Curves object + GN (5.2 Hair Dynamics for motion) | legacy hair particles (maintenance mode) |
| Emitted particles with custom logic | Simulation Zone in GN | legacy particles (`NEWTON`/`BOIDS` are frozen features) |
| Smoke, fire, liquid | Mantaflow (`'FLUID'` modifier, DOMAIN/FLOW/EFFECTOR) | anything else <!-- ease:source S1 anchor="fluid domain defaults" --> |
| Wetmap / footprints / paint trails | Dynamic Paint | n/a <!-- ease:source S1 anchor="dpaint type_toggle + surface_slot_add (results, canvas, slots)" --> |
| Wind, vortex, turbulence affecting the above | Force field (`obj.field`) | keyframed transforms <!-- ease:source S1 anchor="forcefield_toggle (result, field exists, default type)" --> |
| Result feeds geometry generation, not physics accuracy | Simulation Zone | legacy system |
| Must render on a farm with independent frame chunks | Bake to disk cache / Alembic / keyframes **first** | any live sim |

Cost ladder (cheapest → most expensive to compute *and* to cache): <!-- ease:source UNVERIFIED reason="ordering is an editorial estimate; no benchmark or source" -->
force fields < rigid body < GN Sim Zone < soft body < cloth < particles(count-dependent) <
dynamic paint < smoke < liquid(FLIP).

### 3. Rules

R1. Never render or read a simulated frame without stepping from `frame_start`. <!-- ease:source S3 anchor="rigidbody.z_after_stepping_1_to_50" --> <!-- ease:source S3 anchor="rigidbody.z_after_direct_frame_set(50)_from_1" -->
    Why: integrators are order-dependent; the cache is only valid for frames actually computed.
    Violation: every frame of the render shows the rest pose; no error message.

R2. Bake (or step-and-cache) *before* `bpy.ops.render.render(animation=True)`. <!-- ease:source UNVERIFIED reason="chunked farm behaviour was not re-run; follows from R1" -->
    Why: the render loop does step frames in order, but a mid-range `frame_start` or a farm chunk does not.
    Violation: chunked farm output where each chunk restarts the sim.

R3. Create the rigid body world with `bpy.ops.rigidbody.world_add()`, then **assign its collections yourself**. <!-- ease:source S1 anchor="rbw.constraints after world_add" --> <!-- ease:source S3 anchor="scene.rigidbody_world.is_readonly" --> <!-- ease:source S3 anchor="rbw.collection_after_world_add" -->
    Why: `scene.rigidbody_world` is readonly RNA, and `world_add` leaves `collection`/`constraints` as `None`.
    Violation: `AttributeError: 'NoneType' object has no attribute 'objects'`.

R4. Add mesh objects to the sim by linking them into `scene.rigidbody_world.collection`; Blender creates `obj.rigid_body` automatically. <!-- ease:source S3 anchor="obj.rigid_body_after_collection_link" --> <!-- ease:source S1 anchor="ops.rigidbody.object_add without active object" -->
    Why: `BKE_rigidbody_main_collection_object_add` fires on collection link for `OB_MESH` objects.
    Violation with the operator path: `RuntimeError: Operator bpy.ops.rigidbody.object_add.poll() failed, context is incorrect`.

R5. Add cloth / soft body / collision / fluid / dynamic paint / particles with `obj.modifiers.new(name, TYPE)`, not `bpy.ops.object.modifier_add`. <!-- ease:source S3 anchor="collision_modifier.obj.collision_not_none" --> <!-- ease:source S1 anchor="obj.collision after COLLISION modifier" -->
    Why: `Object.modifiers.new` routes through the same editor code path, so `ob->pd` (collision/force data) and particle systems are allocated correctly, without needing UI context.
    Violation: `obj.collision is None` after adding a collision modifier via a raw BKE-style path.

R6. Set `pc.frame_start` / `pc.frame_end` on every point cache before baking. <!-- ease:source S13 anchor="frame_start" --> <!-- ease:source S1 anchor="rbw.point_cache default frame range" -->
    Why: caches default to their own range, not the scene range.
    Violation: sim stops mid-shot; frames past `frame_end` freeze.

R7. Save the .blend before enabling `use_disk_cache` or `bake_target='DISK'`. <!-- ease:source S5 anchor="The blend-file must be saved first" --> <!-- ease:source S2 anchor="rbw/saved: exit_code 139" --> <!-- ease:source S2 anchor="cloth/saved: use_disk_cache reads back True" --> <!-- ease:source S2 anchor="cloth/unsaved: use_disk_cache reads back False" -->
    Why: the manual states the file must be saved first; measured on 5.2.0: on an unsaved file `use_disk_cache = True` reads back `False` (the cache stays in memory), on a saved file cloth, soft body and particle caches wrote `blendcache_<blendname>/*.bphys` next to the .blend. *(Corrected 2026-10-13: the earlier "falls back to `<session temp>/blendcache_`" was not observed. Also measured: setting `use_disk_cache = True` on `scene.rigidbody_world.point_cache` of a saved file crashed Blender 5.2.0 with SIGSEGV, exit code 139.)*
    Violation: bake reports success, next process finds nothing, sim silently re-simulates.

R8. Call `bpy.ops.ptcache.bake_all(bake=True)` from Python (never the invoke path). <!-- ease:source S3 anchor="ptcache.bake_all.result" --> <!-- ease:source S1 anchor="bake_all covers the cloth cache (result, is_baked)" -->
    Why: Python calls `EXEC_DEFAULT`, which runs `BKE_ptcache_bake` synchronously; the invoke path spawns a `wmJob` that never runs in `--background`.
    Violation: operator returns `{'FINISHED'}` instantly, caches empty.

R9. For the fluid domain, make it the **active object** before calling `bpy.ops.fluid.bake_*`. <!-- ease:source S1 anchor="fluid.bake_all with an active object that has NO fluid modifier" --> <!-- ease:source S1 anchor="fluid.bake_all with the FLOW object active" -->
    Why: `fluid_job_init` reads `context_active_object(C)`.
    Violation: `RuntimeError: Error: No Fluid modifier found` when the active object has no Fluid modifier, `RuntimeError: Error: Invalid domain` when it has one that is not a DOMAIN (both measured on 5.2.0).

R10. Set `domain_settings.cache_directory` to an explicit, existing path. <!-- ease:source S1 anchor="fluid.bake_all after empty cache_directory (result)" --> <!-- ease:source S6 anchor="Directory to store baked simulation files in" -->
    Why: an empty path is auto-reset to a session-random name with only an `RPT_WARNING`.
    Violation: `Warning: Fluid: Empty cache path, reset to default '<session temp>/blender_XXXXXX/cache_fluid_XXXXXXXX'` (measured on an unsaved file; the path is absolute), cache lands somewhere unpredictable.

R11. Set `obj.use_simulation_cache = True` before `bpy.ops.object.simulation_nodes_cache_bake()`. <!-- ease:source S4 anchor="simulation_nodes_cache_bake without cache enabled" -->
    Why: that is the operator's poll condition.
    Violation: `RuntimeError: ... poll() failed, Cache has to be enabled`.

R12. Fix seeds explicitly (`psys.seed`, distribution `Seed` sockets, `noise_pos_scale`-style offsets) and never rely on "it looked right last time". <!-- ease:source S1 anchor="psys.seed" -->
    Why: reruns with a different seed produce a different result; Bullet is deterministic only for an identical step sequence.
    Violation: two renders of the same .blend differ.

R13. Prefer substeps/quality over collision margins when objects interpenetrate. <!-- ease:source S8 anchor="Margin Threshold of distance near the surface where collisions are still considered" -->
    Why: margins bias the contact surface outward and create visible gaps; substeps fix tunnelling at its cause.
    Violation: floating objects in the viewport screenshot, or objects passing through a floor.

R14. Free stale caches when you change topology, scale or collider geometry (`bpy.ops.ptcache.free_bake_all()`, `bpy.ops.fluid.free_all()`). <!-- ease:source S3 anchor="ptcache.free_bake_all.result" -->
    Why: caches are keyed by frame, not by input hash; a stale cache is replayed happily.
    Violation: sim visibly does not respond to the parameter you just changed.

R15. Budget memory before raising fluid resolution: cost scales ~`resolution_max³`, and Noise multiplies by `noise_scale³`. <!-- ease:source UNVERIFIED reason="the cubic scaling law is standard for grid solvers but no Blender page checked states it" -->
    Why: 32→256 is 512× the voxels.
    Violation: OOM kill or a bake that never finishes.

### 4. bpy patterns

#### 4.1 Rigid body — full headless setup (data API where possible)

```python
import bpy

def ensure_rigidbody_world(scene=None):
    scene = scene or bpy.context.scene
    if scene.rigidbody_world is None:
        with bpy.context.temp_override(scene=scene):
            bpy.ops.rigidbody.world_add()          # only way in: scene.rigidbody_world is readonly
    rbw = scene.rigidbody_world
    if rbw.collection is None:                     # world_add does NOT create these
        rbw.collection = bpy.data.collections.new("RigidBodyWorld")
    if rbw.constraints is None:
        rbw.constraints = bpy.data.collections.new("RigidBodyConstraints")
    return rbw

def add_rigid_body(obj, kind='ACTIVE', shape='CONVEX_HULL', mass=1.0, scene=None):
    """Pure data API: linking a MESH object into rbw.collection auto-creates obj.rigid_body."""
    rbw = ensure_rigidbody_world(scene)
    assert obj.type == 'MESH', "rigid body requires a mesh object"
    if obj.name not in rbw.collection.objects:
        rbw.collection.objects.link(obj)            # -> obj.rigid_body created as 'ACTIVE'
    rb = obj.rigid_body
    rb.type = kind                                  # 'ACTIVE' | 'PASSIVE'
    rb.collision_shape = shape                      # BOX|SPHERE|CAPSULE|CYLINDER|CONE|
                                                    # CONVEX_HULL|MESH|COMPOUND
    rb.mass = mass                                  # default 1.0, min 0.001
    rb.friction = 0.5                               # default 0.5
    rb.restitution = 0.0                            # default 0.0 (bounciness)
    rb.linear_damping = 0.04                        # defaults
    rb.angular_damping = 0.1
    rb.use_margin = False                           # default; margin only applies when True
    rb.collision_margin = 0.04                      # default
    rb.mesh_source = 'BASE'                         # 'BASE' | 'DEFORM' | 'FINAL'
    rb.kinematic = False                            # True = driven by keyframes, still collides
    rb.use_deactivation = True
    return rb

# World-level solver settings + cache range
rbw = ensure_rigidbody_world()
rbw.substeps_per_frame = 10        # default 10, range 1..32767  -- the tunnelling fix
rbw.solver_iterations = 10         # default 10, range 1..1000   -- the stacking-jitter fix
rbw.time_scale = 1.0
rbw.use_split_impulse = False      # True reduces bounce build-up, slightly less stable
rbw.point_cache.frame_start = bpy.context.scene.frame_start
rbw.point_cache.frame_end   = bpy.context.scene.frame_end
```

Constraints (`obj.rigid_body_constraint`) are created the same way: link an object into <!-- ease:source S1 anchor="constraint object auto-created type" -->
`rbw.constraints`, which auto-creates a `'FIXED'` constraint you then configure. Operator
equivalents exist (`bpy.ops.rigidbody.object_add`, `constraint_add`, `shape_change`,
`mass_calculate`, `objects_add`) but all require an active/selected object in context.

#### 4.2 Baking point caches in `--background`

```python
import bpy, os

def prepare_caches(scene=None, disk=False):
    """Point caches: rigid body world, cloth, soft body, particles, dynamic paint."""
    scene = scene or bpy.context.scene
    caches = []
    if scene.rigidbody_world and not disk:   # 5.2.0: use_disk_cache on the rigid body world cache crashed Blender (see R7)
        caches.append(scene.rigidbody_world.point_cache)
    for ob in scene.objects:
        for m in ob.modifiers:
            pc = getattr(m, "point_cache", None)          # Cloth/SoftBody/DynamicPaint modifiers
            if pc is not None:
                caches.append(pc)
        for psys in ob.particle_systems:
            caches.append(psys.point_cache)
    for pc in caches:
        pc.frame_start = scene.frame_start
        pc.frame_end   = scene.frame_end
        pc.frame_step  = 1
        if disk:
            assert bpy.data.filepath, "disk cache requires a saved .blend (R7)"
            pc.use_disk_cache = True                      # -> //blendcache_<blendname>/
            pc.use_library_path = True
    return caches

# Synchronous, background-safe. Python calls go through exec(), not invoke()/wmJob.
bpy.ops.ptcache.bake_all(bake=True)

# Invalidate everything (do this after changing topology/scale/colliders)
# bpy.ops.ptcache.free_bake_all()
```

Single-cache operators (`bpy.ops.ptcache.bake`, `.free_bake`, `.bake_from_cache`) poll on a <!-- ease:source S1 anchor="ptcache.bake with point_cache override (result, is_baked)" --> <!-- ease:source S1 anchor="ptcache.bake without override poll" -->
`point_cache` **context member**, so they need an override:

```python
with bpy.context.temp_override(scene=scene, object=obj, point_cache=cloth_mod.point_cache):
    bpy.ops.ptcache.bake(bake=True)
```

Disk cache location is not configurable per-cache: it is `//blendcache_<blendname>/` next to the saved .blend (manual; measured `blendcache_shot/41_000001_00.bphys`); <!-- ease:source S5 anchor="folder named blendcache_[filename] alongside the blend-file" --> <!-- ease:source S2 anchor="cloth/saved: first cache files" -->
for an unsaved file the `use_disk_cache` toggle does not take effect (measured). `pc.filepath` only applies when
`pc.use_external = True`. `PointCache.compression` was **removed in 5.0** — caches are always <!-- ease:source S9 anchor="The PointCache.compression property was removed" --> <!-- ease:source S1 anchor="PointCache has compression" -->
compressed.

#### 4.3 The manual frame-stepping fallback (always works)

When an operator refuses to run, or you only need the evaluated geometry:

```python
scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
scene.frame_set(scene.frame_start)
for f in range(scene.frame_start, target_frame + 1):
    scene.frame_set(f)                 # full depsgraph re-eval; advances every sim one step
bpy.context.view_layer.update()
me = obj.evaluated_get(dg).to_mesh()   # remember obj.evaluated_get(dg).to_mesh_clear()
```

This is the *only* portable way to advance Geometry Nodes Simulation Zones headlessly, because <!-- ease:source S4 anchor="simulation_nodes_cache_calculate_to_frame result" -->
`bpy.ops.object.simulation_nodes_cache_calculate_to_frame()` has no `exec()` (invoke/modal only).

#### 4.4 Cloth

```python
m = obj.modifiers.new("Cloth", 'CLOTH')
cs, cc = m.settings, m.collision_settings

cs.quality            = 5      # default 5  — solver steps per frame; the #1 stability knob
cs.mass               = 0.3    # default 0.3 kg per vertex
cs.tension_stiffness  = 15.0   # default 15
cs.compression_stiffness = 15.0
cs.shear_stiffness    = 5.0    # default 5
cs.bending_stiffness  = 0.5    # default 0.5
cs.tension_damping    = 5.0    # default 5
cs.bending_damping    = 0.5    # default 0.5
cs.air_damping        = 1.0    # default 1
cs.bending_model      = 'ANGULAR'   # 'ANGULAR' (accurate) | 'LINEAR' (legacy, faster)
cs.time_scale         = 1.0
cs.vertex_group_mass  = "pin"       # vertex group name = pinned verts

cc.use_collision      = True   # default True
cc.collision_quality  = 2      # default 2  — raise to 4..8 for fast motion
cc.distance_min       = 0.015  # default 0.015 m, range 0.001..1
cc.friction           = 5.0    # default 5
cc.use_self_collision = False  # default False; expensive
cc.self_distance_min  = 0.015
cc.self_friction      = 5.0

m.point_cache.frame_start, m.point_cache.frame_end = scene.frame_start, scene.frame_end
```

Colliders: `collider.modifiers.new("Collision", 'COLLISION')` then tune `collider.collision` <!-- ease:source S1 anchor="obj.collision after COLLISION modifier" -->
(`thickness_outer`, `thickness_inner`, `damping`, `cloth_friction`). `obj.collision` is only
non-`None` for mesh objects that got a Collision modifier added through this path.

#### 4.5 Soft body

```python
m = obj.modifiers.new("Softbody", 'SOFT_BODY')
sb = m.settings          # SoftBodySettings; obj.soft_body is the same struct
sb.use_goal = True
sb.goal_default = 0.7    # how strongly verts return to their animated position (0..1)
sb.goal_spring = 0.5     # 0..0.999
sb.use_edges = True
sb.pull = 0.5            # 0..0.999
sb.push = 0.5
sb.bend = 0.0            # 0..10
sb.mass = 1.0
sb.step_min, sb.step_max = 10, 300     # solver steps/frame
sb.error_threshold = 0.1               # RK solver limit, 0.001..10; lower = more precise
sb.collision_type = 'MANUAL'
```

Soft body is the least stable legacy solver. For jiggle on a modern rig, a GN Simulation Zone with <!-- ease:source UNVERIFIED reason="stability ranking is an editorial opinion" -->
an explicit spring, or the 5.2 experimental Cloth Dynamics asset, is usually better behaved.

#### 4.6 Particles — status and setup

Legacy particles are in maintenance mode: Geometry Nodes has absorbed scattering (instancing), <!-- ease:source UNVERIFIED reason="maintenance-mode statement not found on a Blender page checked in this pass" -->
hair grooming (Curves + GN), and most emission logic (Simulation Zones). Keep legacy particles only
for (a) existing files, (b) the Explode modifier, (c) boids. Everything new should be GN.

```python
m = obj.modifiers.new("ParticleSystem", 'PARTICLE_SYSTEM')  # also creates obj.particle_systems[-1]
psys = obj.particle_systems[-1]
ps = psys.settings                       # ParticleSettings (a separate ID datablock)

ps.type        = 'EMITTER'               # 'EMITTER' | 'HAIR'
ps.count       = 1000                    # default 1000
ps.frame_start = 1.0                     # default 1
ps.frame_end   = 200.0                   # default 200
ps.lifetime    = 50.0                    # default 50
ps.emit_from   = 'FACE'                  # default 'FACE'
ps.distribution = 'JIT'                  # default 'JIT'
ps.physics_type = 'NEWTON'               # default 'NEWTON'
ps.render_type  = 'HALO'                 # default 'HALO'; use 'OBJECT'/'COLLECTION' for instancing
ps.subframes    = 0                      # default 0; raise for fast emitters (dt/(subframes+1))
ps.use_modifier_stack = False

psys.seed = 0                            # determinism (R12)
psys.point_cache.frame_start = scene.frame_start
psys.point_cache.frame_end   = scene.frame_end
```

#### 4.7 Mantaflow fluid (smoke / fire / liquid)

```python
import bpy, os

def make_domain(obj, cache_dir, res=64, kind='GAS'):
    m = obj.modifiers.new("Fluid", 'FLUID')
    m.fluid_type = 'DOMAIN'                 # 'NONE' | 'DOMAIN' | 'FLOW' | 'EFFECTOR'
    d = m.domain_settings
    d.domain_type    = kind                 # 'GAS' | 'LIQUID'
    d.resolution_max = res                  # default 32; cost ~ res**3
    d.cache_type     = 'ALL'                # 'REPLAY'(viewport only) | 'MODULAR' | 'ALL'
    os.makedirs(bpy.path.abspath(cache_dir), exist_ok=True)
    d.cache_directory   = cache_dir         # R10 — never leave empty
    d.cache_frame_start = bpy.context.scene.frame_start
    d.cache_frame_end   = bpy.context.scene.frame_end
    d.cache_data_format = 'OPENVDB'
    d.use_adaptive_timesteps = True         # default True
    d.timesteps_min, d.timesteps_max = 1, 4 # defaults 1 / 4
    d.cfl_condition  = 2.0                  # default 2.0; lower = more substeps = slower/stabler
    d.gravity        = (0.0, 0.0, -9.81)
    d.use_adaptive_domain = False           # gas only; saves memory, changes bounds per frame
    if kind == 'GAS':
        d.use_noise  = False                # noise multiplies voxels by noise_scale**3
        d.noise_scale = 2                   # default 2
        d.flame_smoke = 1.0
    else:
        d.simulation_method = 'FLIP'        # 'FLIP' | 'APIC'
        d.use_mesh = True                   # surface mesh generation
        d.particle_radius = 1.0             # raise if the sim leaks volume
    return m, d

def make_flow(obj, behavior='INFLOW'):
    m = obj.modifiers.new("Fluid", 'FLUID')
    m.fluid_type = 'FLOW'
    return m, m.flow_settings               # .flow_type ('SMOKE'|'FIRE'|'BOTH'|'LIQUID'),
                                            # .flow_behavior ('INFLOW'|'OUTFLOW'|'GEOMETRY')

def make_effector(obj):
    m = obj.modifiers.new("Fluid", 'FLUID')
    m.fluid_type = 'EFFECTOR'
    return m, m.effector_settings           # .effector_type ('COLLISION'|'GUIDE'), .surface_distance

# Bake — the domain must be the ACTIVE object (R9)
vl = bpy.context.view_layer
vl.objects.active = domain_obj
domain_obj.select_set(True)
bpy.ops.fluid.bake_all()          # exec() path is synchronous -> background-safe
# Modular alternative: bake_data() -> bake_noise() -> bake_mesh() -> bake_particles()
# Invalidate: bpy.ops.fluid.free_all()
```

The fluid cache is **not** a `PointCache`; `bpy.ops.ptcache.bake_all()` does not touch it. Relative <!-- ease:source S1 anchor="fluid cache is a PointCache?" --> <!-- ease:source S1 anchor="fluid cache files written (top-level dirs)" --> <!-- ease:source S6 anchor="Fluid simulations use their own cache" --> <!-- ease:source S1 anchor="fluid domain defaults" -->
`//` cache paths resolve against the .blend. The default `cache_type` is `'REPLAY'`, the default `cache_directory` is a session temp path even before you set one (measured), and a headless `fluid.bake_all()` on a small domain wrote `config/ data/ guiding/ mesh/ noise/ particles/` under the cache directory. The bake
operators do not check `cache_type`, but set it to `'ALL'` so every enabled sub-stage (noise, mesh,
particles) is included.

Rough memory: a `GAS` domain at `resolution_max=R` allocates on the order of `R³` voxels × ~10 <!-- ease:source UNVERIFIED reason="absolute memory figures are order-of-magnitude guidance (already flagged in the original Sources)" -->
float fields. R=64 ≈ hundreds of MB with noise off; R=256 ≈ tens of GB. Start at 64, look at a
render, then scale.

#### 4.8 Dynamic paint

```python
canvas = c_obj.modifiers.new("Dynamic Paint", 'DYNAMIC_PAINT')
brush  = b_obj.modifiers.new("Dynamic Paint", 'DYNAMIC_PAINT')
# canvas_settings / brush_settings are None until the type is toggled — operator only:
with bpy.context.temp_override(object=c_obj, active_object=c_obj):
    bpy.ops.dpaint.type_toggle(type='CANVAS')
    bpy.ops.dpaint.surface_slot_add()
with bpy.context.temp_override(object=b_obj, active_object=b_obj):
    bpy.ops.dpaint.type_toggle(type='BRUSH')

surf = canvas.canvas_settings.canvas_surfaces.active
surf.surface_type = 'PAINT'          # 'PAINT'|'DISPLACE'|'WEIGHT'|'WAVE'
surf.frame_start, surf.frame_end = scene.frame_start, scene.frame_end
with bpy.context.temp_override(object=c_obj, active_object=c_obj):
    bpy.ops.dpaint.bake()
```

#### 4.9 Force fields

```python
# On an existing object: obj.field is None until ob->pd is allocated (operator-only).
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.forcefield_toggle()
f = obj.field
f.type = 'WIND'      # FORCE|WIND|VORTEX|MAGNET|HARMONIC|CHARGE|LENNARDJ|TEXTURE|
                     # GUIDE|BOID|TURBULENCE|DRAG|FLUID_FLOW (+ NONE; measured enum items on 5.2.0)
f.strength = 5.0
f.distance_max = 10.0
f.use_max_distance = True

# Or create a dedicated empty in one call:
bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, 3))

# Scene-wide
scene.use_gravity = True
scene.gravity = (0.0, 0.0, -9.81)
```

Per-system field response lives in `effector_weights` (`rbw.effector_weights`, <!-- ease:source S1 anchor="cloth effector_weights" --> <!-- ease:source S1 anchor="rbw.effector_weights exists" --> <!-- ease:source S1 anchor="ps effector_weights" -->
`cloth_mod.settings.effector_weights`, `ps.effector_weights`) — e.g. `.gravity = 0.0` to make one
system ignore gravity without changing the scene.

#### 4.10 Making a simulation reproducible / farm-safe

```python
# 1. Rigid body -> keyframes (removes objects from the sim afterwards)
# measured on 5.2.0 background: the operator needs a VIEW_3D area in the override (an object-only override fails
# inside bpy.ops.anim.keyframe_insert_by_name.poll())
win = bpy.context.window_manager.windows[0]
v3d = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in v3d.regions if r.type == 'WINDOW')
with bpy.context.temp_override(window=win, screen=win.screen, area=v3d, region=region,
                               object=obj, active_object=obj,
                               selected_objects=sim_objs, selected_editable_objects=sim_objs):
    bpy.ops.rigidbody.bake_to_keyframes(frame_start=1, frame_end=250, step=1)

# 2. Everything else -> disk point cache (requires a saved .blend)
bpy.ops.wm.save_as_mainfile(filepath="/abs/shot.blend")
prepare_caches(disk=True)
bpy.ops.ptcache.bake_all(bake=True)
bpy.ops.wm.save_mainfile()          # persist is_baked flags + cache paths

# 3. Or freeze to Alembic (fully solver-independent)
bpy.ops.wm.alembic_export(filepath="/abs/shot.abc", start=1, end=250, selected=False)
```

#### 4.11 When to use a GN Simulation Zone instead

Use a Simulation Zone when the state you need is *geometry or attributes*, not contact physics: <!-- ease:source S14 anchor="Simulation zones allow the result of one frame to influence the next one" -->
growth, trails, accumulation, decay, flocking-by-field, procedural erosion, per-point velocity
integration. It gives you a per-modifier cache (`mod.bake_target`, `mod.bake_directory`,
`obj.use_simulation_cache`) with no `PointCache` involvement, it bakes with a single synchronous
operator, and its inputs are visible in the node graph rather than spread across five RNA structs.
Use a legacy system when you need Bullet contacts (rigid body), a mature garment solver (cloth), or
Mantaflow's volumetrics. 5.2's experimental **Cloth Dynamics** / **Hair Dynamics** node groups sit <!-- ease:source S11 anchor="Physics simulation for cloth dynamics is an experimental feature" --> <!-- ease:source S12 anchor="XPBD" --> <!-- ease:source S4 anchor="idname.GeometryNodeXPBDSolver" -->
on a built-in `GeometryNodeXPBDSolver` and are the direction of travel — treat their exact socket
layout as unstable.

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Every rendered frame shows the rest state; no traceback | Never stepped/baked from `frame_start` (R1) | `bpy.ops.ptcache.bake_all(bake=True)` or a `frame_set` loop <!-- ease:source S3 anchor="rigidbody.z_after_direct_frame_set(50)_from_1" --> |
| `AttributeError: 'NoneType' object has no attribute 'objects'` | `scene.rigidbody_world.collection` is `None` after `world_add` | Assign `bpy.data.collections.new(...)` (R3) <!-- ease:source S3 anchor="rbw.collection_after_world_add" --> |
| `RuntimeError: Operator bpy.ops.rigidbody.object_add.poll() failed, context is incorrect` | No active object in `--background` | Link into `rbw.collection` instead (R4) <!-- ease:source S1 anchor="ops.rigidbody.object_add without active object" --> |
| `AttributeError: 'Scene' object attribute 'rigidbody_world' is read-only` | Tried to assign the world directly | Use `bpy.ops.rigidbody.world_add()` <!-- ease:source S3 anchor="scene.rigidbody_world.is_readonly" --> |
| `bake_all()` returns `{'FINISHED'}` instantly, `pc.is_baked` still `False` | Cache range is empty / `frame_end < frame_start` | Set `pc.frame_start/frame_end` (R6) <!-- ease:source UNVERIFIED reason="empty-range behaviour not re-run in this pass" --> |
| Bake succeeds, a later process finds no cache | Unsaved .blend: `use_disk_cache` stays `False`, the bake lives only in memory (R7) | `bpy.ops.wm.save_as_mainfile()` first, then enable `use_disk_cache` on cloth/soft body/particle caches |
| `RuntimeError: Error: No Fluid modifier found` / `Error: Invalid domain` | Fluid bake with the wrong active object: no Fluid modifier / a FLOW or EFFECTOR instead of the DOMAIN (R9) | `view_layer.objects.active = domain_obj` |
| `Fluid: Empty cache path, reset to default '...'` warning | `cache_directory` left empty (R10) | Set an explicit absolute or `//`-relative path |
| `RuntimeError: ... simulation_nodes_cache_bake.poll() failed, Cache has to be enabled` | `obj.use_simulation_cache is False` | Set it `True` (R11) <!-- ease:source S4 anchor="simulation_nodes_cache_bake without cache enabled" --> |
| `simulation_nodes_cache_calculate_to_frame` does nothing in background | Operator has invoke/modal only, no `exec()` | Step frames manually (§4.3) <!-- ease:source S4 anchor="simulation_nodes_cache_calculate_to_frame result" --> |
| `AttributeError: 'DynamicPaintModifier' object has no attribute ...` / `canvas_settings is None` | Type never toggled | `bpy.ops.dpaint.type_toggle(type='CANVAS')` with an override <!-- ease:source S1 anchor="canvas_settings before toggle" --> |
| `obj.field is None` after setting `obj.field.type` | `ob->pd` unallocated | `bpy.ops.object.forcefield_toggle()` (§4.9) <!-- ease:source S1 anchor="obj.field on a plain object" --> |
| Objects fall through the floor / tunnel at speed | Too few substeps (R13) | `rbw.substeps_per_frame` 10 → 20–60; avoid `MESH` shape on fast movers <!-- ease:source UNVERIFIED reason="tuning advice; defaults are measured (substeps 10, iterations 10)" --> |
| Stacks jitter and drift | Too few solver iterations, or `restitution > 0` | `rbw.solver_iterations` 10 → 30–60; `restitution = 0` |
| Visible gap between colliding objects | `use_margin=True` with a large `collision_margin` | `use_margin = False`, or margin ≤ 0.001 |
| Cloth explodes / self-intersects on frame 1 | `quality` too low, or initial interpenetration | `quality` 5 → 10–20; `collision_quality` 2 → 6; move cloth off the collider <!-- ease:source S1 anchor="cloth settings" --> |
| Parameter change has no visible effect | Stale cache replayed (R14) | `bpy.ops.ptcache.free_bake_all()` / `bpy.ops.fluid.free_all()` <!-- ease:source S3 anchor="ptcache.free_bake_all.result" --> |
| Process OOM-killed during fluid bake | `resolution_max` and/or noise too high (R15) | Halve `resolution_max`; `use_noise = False` <!-- ease:source UNVERIFIED reason="memory behaviour not measured" --> |
| `AttributeError: 'PointCache' object has no attribute 'compression'` | Removed in 5.0 | Delete the line; caches are always compressed <!-- ease:source S9 anchor="The PointCache.compression property was removed" --> |
| Two runs of the same script give different sims | Unfixed seeds / different frame stepping (R12) | Fix `psys.seed`, bake, or convert to keyframes |

### 6. Parameter defaults by use case

Property names in this table were checked against the 5.2.0 RNA of `RigidBodyWorld`, `RigidBodyObject`, `ClothSettings`, `ClothCollisionSettings`, `SoftBodySettings`, `ParticleSettings` and `FluidDomainSettings`; the numeric values are pipeline conventions, not Blender defaults (the real defaults are quoted in §4). <!-- ease:source S15 anchor="substeps_per_frame" --> <!-- ease:source S16 anchor="quality" --> <!-- ease:source S17 anchor="step_min" --> <!-- ease:source S18 anchor="resolution_max" --> <!-- ease:source S19 anchor="subframes" --> <!-- ease:source S1 anchor="rbw defaults (value, hard_min, hard_max)" --> <!-- ease:source S1 anchor="rigid_body defaults" --> <!-- ease:source S1 anchor="cloth settings" --> <!-- ease:source S1 anchor="cloth collision_settings" --> <!-- ease:source S1 anchor="soft body settings" --> <!-- ease:source S1 anchor="particle settings" --> <!-- ease:source S1 anchor="fluid domain defaults" --> <!-- ease:source S7 anchor="Damping Translation Amount of linear velocity that is lost over time" --> <!-- ease:source UNVERIFIED reason="pipeline convention, not a Blender-documented default; the module's own Sources note already flags it" -->

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `rbw.substeps_per_frame` | 6–10 | 10 | 10–20 | 20–60 | n/a |
| `rbw.solver_iterations` | 10 | 10 | 10–20 | 30–60 | n/a |
| `rigid_body.collision_shape` | `CONVEX_HULL` / `BOX` | `CAPSULE` (ragdoll) | `CONVEX_HULL` | `MESH` (static) + `CONVEX_HULL` (moving) | n/a |
| `rigid_body.use_margin` / `collision_margin` | True / 0.04 | True / 0.02 | False | False / 0.001 | n/a |
| `rigid_body.restitution` | 0.2–0.5 | 0.0 | 0.3–0.6 | 0.0 | n/a |
| `rigid_body.mesh_source` | `BASE` | `DEFORM` | `BASE` | `FINAL` | n/a |
| `cloth.settings.quality` | 3–5 | 10–20 | 5–10 | 15–25 | n/a |
| `cloth.collision_settings.collision_quality` | 2 | 4–8 | 2–4 | 6–12 | n/a |
| `cloth.collision_settings.use_self_collision` | False | True | False | True | n/a |
| `cloth.settings.mass` | 0.3 | 0.2–0.4 (garment) | 0.3 | 0.3 | n/a |
| `softbody.step_min` / `step_max` | 10 / 100 | 20 / 300 | 10 / 200 | 30 / 500 | n/a |
| Particle `count` | ≤ 5 000 | n/a (use GN/curves) | 10 000–100 000 | ≤ 20 000 | n/a |
| Particle `subframes` | 0 | 0 | 1–3 | 2–5 | n/a |
| Fluid `resolution_max` | n/a (bake to VDB/flipbook) | n/a | 64–128 | 128–256 | n/a |
| Fluid `use_noise` / `noise_scale` | n/a | n/a | False | True / 2 | n/a |
| Fluid `cfl_condition` | n/a | n/a | 2.0 | 1.0–1.5 | n/a |
| Point cache target | disk, committed with the asset | disk | packed or disk | disk | n/a |
| Final delivery form | keyframes / vertex anim | Alembic | baked cache | baked cache | n/a |
| GN Sim Zone vs legacy | Sim Zone | legacy cloth | Sim Zone | legacy fluid/cloth | neither (physics is n/a for print) |

### 7. Verification checklist

- [ ] `assert bpy.context.scene.rigidbody_world is not None and bpy.context.scene.rigidbody_world.collection is not None` — R3 satisfied.
- [ ] `assert obj.rigid_body is not None and obj.rigid_body.type in {'ACTIVE','PASSIVE'}` — the object really joined the sim.
- [ ] `assert all(pc.frame_end > pc.frame_start for pc in prepare_caches())` — every cache has a usable range.
- [ ] `assert all(pc.is_baked for pc in prepare_caches())` after `ptcache.bake_all` — the bake actually produced data.
- [ ] `assert not any(pc.is_outdated for pc in prepare_caches())` — no stale cache will be replayed.
- [ ] `assert bpy.data.filepath` before enabling `use_disk_cache` — R7.
- [ ] `import os; assert os.path.isdir(bpy.path.abspath("//blendcache_" + os.path.splitext(os.path.basename(bpy.data.filepath))[0]))` — disk caches landed where expected.
- [ ] Motion proof: `scene.frame_set(start); a = obj.matrix_world.copy(); scene.frame_set(start+40); assert (obj.matrix_world.translation - a.translation).length > 1e-3` — the rigid body is genuinely moving.
- [ ] Deformation proof: `dg = bpy.context.evaluated_depsgraph_get(); v0 = obj.evaluated_get(dg).data.vertices[0].co.copy()` at two frames, assert they differ — cloth/soft body is solving.
- [ ] `assert os.path.isdir(bpy.path.abspath(d.cache_directory)) and os.listdir(...)` after a fluid bake — Mantaflow wrote files.
- [ ] `assert obj.use_simulation_cache` before `simulation_nodes_cache_bake` — R11.
- [ ] `assert len(mod.node_warnings) == 0` for GN sim modifiers — surfaces red-node errors that never raise.
- [ ] Determinism: run the frame sweep twice in one session and assert identical `matrix_world` at the last frame — catches unfixed seeds.
- [ ] `get_viewport_screenshot` at start / mid / end frames — interpenetration, explosion and "nothing moved" are all visible and none of them raise.

### 8. Original reference list (pre-UKMC; the numbered Sources section at the end of this file is authoritative)

- [bpy.types.RigidBodyWorld (5.2)](https://docs.blender.org/api/current/bpy.types.RigidBodyWorld.html) — `substeps_per_frame`, `solver_iterations`, `collection`, `point_cache`
- [bpy.types.RigidBodyObject (5.2)](https://docs.blender.org/api/current/bpy.types.RigidBodyObject.html) — defaults for `mass`, `friction`, `restitution`, `collision_margin`, `mesh_source`
- [Rigidbody Object Shape Items](https://docs.blender.org/api/current/bpy_types_enum_items/rigidbody_object_shape_items.html)
- [bpy.types.PointCache (5.2)](https://docs.blender.org/api/current/bpy.types.PointCache.html) — `frame_start/end`, `use_disk_cache`, `is_baked`, `is_outdated`
- [bpy.ops.ptcache (5.2)](https://docs.blender.org/api/current/bpy.ops.ptcache.html), [bpy.ops.rigidbody](https://docs.blender.org/api/current/bpy.ops.rigidbody.html), [bpy.ops.fluid](https://docs.blender.org/api/current/bpy.ops.fluid.html), [bpy.ops.dpaint](https://docs.blender.org/api/current/bpy.ops.dpaint.html), [bpy.ops.object](https://docs.blender.org/api/current/bpy.ops.object.html)
- [bpy.types.ClothSettings](https://docs.blender.org/api/current/bpy.types.ClothSettings.html) / [ClothCollisionSettings](https://docs.blender.org/api/current/bpy.types.ClothCollisionSettings.html) / [SoftBodySettings](https://docs.blender.org/api/current/bpy.types.SoftBodySettings.html) / [CollisionSettings](https://docs.blender.org/api/current/bpy.types.CollisionSettings.html) — all quoted defaults
- [bpy.types.FluidDomainSettings](https://docs.blender.org/api/current/bpy.types.FluidDomainSettings.html) / [FluidModifier](https://docs.blender.org/api/current/bpy.types.FluidModifier.html) — `resolution_max`, `cache_type`, `cache_directory`, `timesteps_*`, `cfl_condition`, `simulation_method`
- [bpy.types.ParticleSettings](https://docs.blender.org/api/current/bpy.types.ParticleSettings.html) / [ParticleSystem](https://docs.blender.org/api/current/bpy.types.ParticleSystem.html) — `count`, `lifetime`, `subframes`, `seed`, `point_cache`
- [Manual: Fluid Domain Cache](https://docs.blender.org/manual/en/latest/physics/fluid/type/domain/cache.html) — Replay/Modular/All semantics; "Fluid simulations use their own cache"
- [Blender 5.0 release notes: Python API — PointCaches](https://developer.blender.org/docs/release_notes/5.0/python_api/) — `PointCache.compression` removed
- [Blender 5.2 LTS release notes: Physics](https://developer.blender.org/docs/release_notes/5.2/physics/) — experimental Cloth/Hair Dynamics, effectors, XPBD Solver node
- Behaviour verified against Blender source (`blenkernel/rigidbody.cc`, `blenkernel/pointcache.cc`,
  `editors/physics/physics_pointcache.cc`, `editors/physics/physics_fluid.cc`,
  `editors/object/object_bake_simulation.cc`, `editors/object/object_modifier.cc`,
  `makesrna/intern/rna_object.cc`): auto-creation of `rigid_body` on collection link,
  `blendcache_` path fallback, `exec()` vs `invoke()` paths, active-object requirement for fluid
  bakes, `ob->pd` allocation on `modifiers.new(..., 'COLLISION')`.
- `[UNVERIFIED]` exact per-voxel byte cost of a Mantaflow gas domain (the `R³` scaling law is
  documented, the absolute MB figures in §4.7 are order-of-magnitude guidance, not measured);
  socket/property layout of the 5.2 experimental Cloth Dynamics and Hair Dynamics node groups,
  which ship as bundled assets rather than stable RNA.

## Failure Modes (Mandatory)
- **Every rendered or inspected frame shows the start state** — cause: a legacy simulation only advances when frames are stepped or baked in order (measured: a falling cube read z=20.0 after jumping 1 -> 50 but 0.498 after stepping 1..50) — fix: `scene.frame_set(f)` from `frame_start`, or `bpy.ops.ptcache.bake_all(bake=True)` first. <!-- ease:source S3 anchor="rigidbody.z_after_direct_frame_set(50)_from_1" --> <!-- ease:source S3 anchor="rigidbody.z_after_stepping_1_to_50" -->
- **`use_disk_cache = True` does nothing, or Blender dies with exit code 139** — cause: on an unsaved file the toggle stays False; on a saved file the rigid body world cache crashed 5.2.0 (cloth, soft body and particle caches worked) — fix: save the .blend first, enable disk cache only on cloth/soft body/particle caches, and freeze rigid body with `bake_to_keyframes`. <!-- ease:source S2 anchor="cloth/unsaved: use_disk_cache reads back False" --> <!-- ease:source S2 anchor="rbw/saved: exit_code 139" -->
- **`bpy.ops.rigidbody.bake_to_keyframes` raises a traceback from `anim.keyframe_insert_by_name.poll()`** — cause: the override had no VIEW_3D area — fix: add `window`, `screen`, `area` (VIEW_3D) and `region` to `temp_override` (measured FINISHED, rigid body removed, action created). <!-- ease:source S1 anchor="rigidbody.bake_to_keyframes with VIEW_3D + object override (result, rigid_body removed, has action)" -->
- **`RuntimeError: Error: No Fluid modifier found` or `Error: Invalid domain` when baking fluid** — cause: the active object is not the Fluid DOMAIN (no Fluid modifier, or a FLOW/EFFECTOR) — fix: set `view_layer.objects.active = domain_obj` before `bpy.ops.fluid.bake_all()`. <!-- ease:source S1 anchor="fluid.bake_all with an active object that has NO fluid modifier" --> <!-- ease:source S1 anchor="fluid.bake_all with the FLOW object active" -->
- **`AttributeError: 'NoneType' object has no attribute 'objects'` after `rigidbody.world_add()`** — cause: `scene.rigidbody_world.collection` (and `constraints`) are `None` after `world_add` (measured) — fix: assign `bpy.data.collections.new(...)` before linking objects. <!-- ease:source S3 anchor="rbw.collection_after_world_add" --> <!-- ease:source S1 anchor="rbw.constraints after world_add" -->
- **`RuntimeError: ... simulation_nodes_cache_bake.poll() Cache has to be enabled`** — cause: `obj.use_simulation_cache` is False — fix: set it True; the bake then returns FINISHED headless, while `simulation_nodes_cache_calculate_to_frame` only passes through (invoke/modal only). <!-- ease:source S4 anchor="simulation_nodes_cache_bake without cache enabled" --> <!-- ease:source S4 anchor="simulation_nodes_cache_calculate_to_frame result" -->
- **Dynamic Paint modifier has `canvas_settings is None`** — cause: the type is only created by the operator — fix: `bpy.ops.dpaint.type_toggle(type='CANVAS')` under an object override (measured FINISHED, canvas present). <!-- ease:source S1 anchor="canvas_settings before toggle" --> <!-- ease:source S1 anchor="dpaint type_toggle + surface_slot_add (results, canvas, slots)" -->

## Sources
- [S1] Local Blender 5.2.0 LTS physics defaults/operator probe (script: knowledge/_evidence/kb-261013/w2-physics-defaults-probe.py) — knowledge/_evidence/kb-261013/w2-physics-defaults-probe.txt — captured 2026-10-13 — sha256 5fe11061119e7c56ff701562c07a249d3a069fd718635f7efbf539d71b6be333
- [S2] Local Blender 5.2.0 LTS disk-cache probe, one process per cache type (script: knowledge/_evidence/kb-261013/w2-physics-diskcache-probe.py) — knowledge/_evidence/kb-261013/w2-physics-diskcache-probe.txt — captured 2026-10-13 — sha256 2e45243ab89b1f8fec663f043de42699d78db317798af8d5a783916ae3d2d3cf
- [S3] Local Blender 5.2.0 LTS runtime probe (script: knowledge/_evidence/kb-261013/w2-bpy-52-facts.py) — knowledge/_evidence/kb-261013/w2-bpy-52-facts.txt — captured 2026-10-13 — sha256 2411832c2522b533b8523ee16511805eb0d8a75bc2f2b213663bc0f77f4667af
- [S4] Local Blender 5.2.0 LTS Geometry Nodes API probe (script: knowledge/_evidence/kb-261013/w2-gn-api-probe.py) — knowledge/_evidence/kb-261013/w2-gn-api-probe.txt — captured 2026-10-13 — sha256 c83f0e20d36cb3d773e27ac4440a9c8c6648f9a130bcf5933dc66c699648c739
- [S5] Baking Physics Simulations - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/physics/baking.html (frozen: knowledge/_evidence/kb-261013/w2-manual-physics-baking.html) — captured 2026-10-13 — sha256 2f1bc52edeb85858514e1157cc5faf73f09e93b02c0d03bf89560343face700d
- [S6] Cache - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/physics/fluid/type/domain/cache.html (frozen: knowledge/_evidence/kb-261013/w2-manual-physics-fluid-type-domain-cache.html) — captured 2026-10-13 — sha256 e26ecad6d51f173877d1c3b7ff40a19036ee2f5410f74bc8095d4325ee6ccfd0
- [S7] Dynamics - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/physics/rigid_body/properties/dynamics.html (frozen: knowledge/_evidence/kb-261013/w2-manual-physics-rigid_body-properties-dynamics.html) — captured 2026-10-13 — sha256 bff7b844a8420ca9db1c8837bfff0b54470e3b5d05a611c5eb38044cb54175f6
- [S8] Collisions - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/physics/rigid_body/properties/collisions.html (frozen: knowledge/_evidence/kb-261013/w2-manual-physics-rigid_body-properties-collisions.html) — captured 2026-10-13 — sha256 3eb7345d645aecfd9e70afa7208ad29931087b6d7a980d645463c8f93ff17927
- [S9] Python API - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-0-python_api.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S10] Physics - Blender Developer Documentation — https://developer.blender.org/docs/release_notes/5.2/physics/ (frozen: knowledge/_evidence/kb-261013/w2-relnotes-5-2-physics.html) — captured 2026-10-13 — sha256 76f263785e1c3498c9a8067c0bc90d812a923c037a7d912608d140b1e8e891da
- [S11] Cloth Dynamics - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/cloth_dynamics.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-simulation-cloth_dynamics.html) — captured 2026-10-13 — sha256 9be26cd766ed2dddbc0f73357877d2d989409e552ccf6d66d7e051c57a13b787
- [S12] XPBD Solver - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/xpbd_solver.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-simulation-xpbd_solver.html) — captured 2026-10-13 — sha256 9d8dc2758540332edd92cfe2147de96e4df591f1c0abd5c7ea60016ba55806f7
- [S13] PointCache(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.PointCache.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-PointCache.html) — captured 2026-10-13 — sha256 f5bdee3498c3f59d94dadfd4d4d30afd6f13aa8749be8d976d76c1f5c850f2be
- [S14] Simulation Zone - Blender 5.2 LTS Manual — https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/simulation_zone.html (frozen: knowledge/_evidence/kb-261013/w2-manual-modeling-geometry_nodes-simulation-simulation_zone.html) — captured 2026-10-13 — sha256 1dd410eee5592d3bd7a061e7786da27a9db2840bf82b7207cfda971e6d3c55f2
- [S15] RigidBodyWorld(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.RigidBodyWorld.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-RigidBodyWorld.html) — captured 2026-10-13 — sha256 015c376f7bbcd31910292a8872148147d97d22dd9de34c1573c9c2493bfbe730
- [S16] ClothSettings(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.ClothSettings.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-ClothSettings.html) — captured 2026-10-13 — sha256 83339a08e0eabc14e0901c71d2408b0852cbad971cc9de9ca50486d272da613b
- [S17] SoftBodySettings(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.SoftBodySettings.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-SoftBodySettings.html) — captured 2026-10-13 — sha256 a70d4d189eafdef36a38e6803bc327c29536afa2dee1a4324756b6b252efddf3
- [S18] FluidDomainSettings(bpy_struct) - Blender Python API — https://docs.blender.org/api/current/bpy.types.FluidDomainSettings.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-FluidDomainSettings.html) — captured 2026-10-13 — sha256 8268e1ef0d754a7f93982e8e39714542b6ee68fa1bcf8c6ace76a4b9b316a7d6
- [S19] ParticleSettings(ID) - Blender Python API — https://docs.blender.org/api/current/bpy.types.ParticleSettings.html (frozen: knowledge/_evidence/kb-261013/w2-api-bpy-types-ParticleSettings.html) — captured 2026-10-13 — sha256 5f854e41a54e6b040cc01f69b7d6ebf7d79435f4203e1d50ae6e0148c045a1ce

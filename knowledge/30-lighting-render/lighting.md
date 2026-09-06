---
name: lighting
domain: lighting
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Light object data properties, physical wattage reasoning against AgX/Film Exposure, HDRI worlds, light linking, and studio recipes built in bpy.
loads_with: [render-engines, materials-pbr, compositing-output]
tags: [lighting, watts, hdri, world, three-point, light-linking, agx, exposure]
---

# Lighting

## 1. Mental model

Blender lights are physical emitters measured in **radiant power (watts)**, not artistic
0-to-1 intensities. A light object is a thin wrapper: `obj.type == 'LIGHT'`, and all the
interesting properties live on `obj.data` (a `bpy.types.Light`), whose `type` is
`'POINT' | 'SUN' | 'SPOT' | 'AREA'`. Shadow softness is a function of **emitter size**,
not a shadow setting — a 0-radius point light physically cannot produce a soft shadow.

The image the agent finally looks at is `scene_linear_radiance → view transform → display`.
Since 4.0 the default view transform is **AgX** (still the default in 5.2, set from
`BKE_color_managed_view_settings_init(..., "AgX")`), which is a filmic tone map with
~16.5 stops of latitude and strong highlight desaturation. This means: **a render that
"looks fine" under AgX can be several stops off in scene-linear terms**, and a render that
looks blown out under `Standard` may be perfectly exposed. An agent evaluating its own
render must know which transform is active before drawing conclusions.

Most common agent mistake: reaching for `energy = 5` (a value that reads as "medium" in
game engines) and then concluding the scene is unlit. In Blender, 5 W at 3 m is nearly
black.

## 2. Decision first

| Goal | Light type | Key property |
|---|---|---|
| Sun / outdoor key | `SUN` | `energy` in **W/m²**, `angle` (radians) = angular diameter → shadow softness |
| Bare bulb, candle, small lamp | `POINT` | `energy` in **W**, `shadow_soft_size` = radius |
| Softbox, window, TV panel, bounce card | `AREA` | `energy` in **W**, `shape` + `size`/`size_y`, `spread` |
| Stage / practical beam, cone falloff | `SPOT` | `energy` in **W**, `spot_size` (radians), `spot_blend` |
| Whole-scene ambient / reflections / realism | World HDRI | `ShaderNodeTexEnvironment` + `ShaderNodeBackground.Strength` |
| Flat, engine-independent, no shadows | World `Background` color only | cheap, no light objects |

| Question | Answer |
|---|---|
| Hard shadows? | Small emitter: `shadow_soft_size ≈ 0`, `SUN.angle ≈ 0.5°`(=0.00873 rad) |
| Soft shadows? | Large emitter: area light 1–3× the subject's size, or `SUN.angle` 5–20° |
| Realistic reflections on a product? | HDRI world (even at low strength) + area lights, not point lights |
| Fast realtime bake? | Few lights, `SUN` + area, no volumetrics, light probes for indirect |
| Path traced hero shot? | HDRI + 2–4 area lights, `scene.cycles.use_light_tree = True` |
| Isolate a rim light to one character? | Light linking (`obj.light_linking.receiver_collection`) |
| Colour by physical temperature? | `light.use_temperature = True; light.temperature = 3200` |

## 3. Rules

R1. Set light properties on `obj.data`, never on the object.
    Why: `energy`, `color`, `shape` are on `bpy.types.Light`.
    Violation: `AttributeError: 'Object' object has no attribute 'energy'`.

R2. Think in watts and distances, not in 0–1 sliders.
    Why: irradiance falls off as 1/d²; a "reasonable" number depends entirely on distance.
    Rule of thumb (derived below): a **point** light needs ≈ `40 × d²` W and an **area**
    light ≈ `10 × d²` W to put an 18% grey subject at ~0.18 scene-linear.
    Violation: `energy = 5` at 3 m renders essentially black; agent adds more lights and
    ends up with a flat, over-bounced scene.

R3. Shadow softness comes from emitter size, and only from emitter size.
    Why: penumbra width ≈ emitter_size × (occluder→receiver distance) / (light→occluder
    distance). There is no "soften shadow" slider on the light.
    Violation: agent raises samples to fix "hard, aliased shadows" and only gets slower.

R4. Know the active view transform before judging your own render.
    Why: AgX (default), Filmic (deprecated legacy), Standard, ACES 1.3/2.0, Khronos PBR
    Neutral and False Color all map the same scene-linear data very differently.
    Violation: agent "fixes" exposure that was already correct, or ships an image that is
    3 stops hot because it was evaluated under AgX's highlight rolloff.

R5. Use `False Color` view transform to measure exposure, not your eyes.
    Why: it is a documented heat map — grey = 16–22% (correct mid-grey), red = 80–97%,
    white = clipped.
    Violation: subjective "looks a bit dark" loops that never converge.

R6. Do not set `world.use_nodes = True` expecting a tree to be created in 5.x.
    Why: deprecated in 5.0 (removal in 6.0); `bpy.data.worlds.new()` already builds the
    default tree.
    Violation: `AttributeError: 'NoneType' object has no attribute 'nodes'` when the code
    also cleared the tree first.

R7. HDRIs must be `Linear Rec.709` (or `Working Space`), never `sRGB`.
    Why: `.hdr`/`.exr` are already scene-linear; a second decode crushes the sun disc.
    Violation: HDRI looks washed out and produces almost no directional shadow.

R8. Rotate an HDRI with a `Mapping` node fed by `Texture Coordinate → Generated`.
    Why: `ShaderNodeTexEnvironment` has only a `Vector` input; there is no rotation
    property on the node or on the world.
    Violation: agent looks for `world.rotation` and finds nothing.

R9. `SUN.angle` and `SPOT.spot_size` are in **radians**.
    Why: RNA subtype is `PROP_ANGLE`.
    Violation: `sun.data.angle = 30` gives a 30-radian sun — a fully ambient, shadowless
    scene.

R10. EEVEE ignores several light features Cycles honours.
    Why: documented EEVEE limitations — light node trees (`light.use_nodes`), area
    `spread` (Beam Spread), and spot `shadow_soft_size` affecting cone softness.
    Violation: identical scene, wildly different render between engines; agent blames
    the light values.

R11. Light linking needs a real Collection, and per-member `link_state`.
    Why: `obj.light_linking.receiver_collection` points at a Collection whose
    `collection_objects[i].light_linking.link_state` is `'INCLUDE'` or `'EXCLUDE'`.
    Violation: creating the collection but not adding objects → light affects everything
    (empty include list is treated as "no restriction").

R12. Balance a three-point rig by ratio, not by absolute numbers.
    Why: key:fill:rim ≈ 1 : 0.2–0.5 : 0.5–2 is scale-invariant; absolute watts are not.
    Violation: correct-looking ratios destroyed the moment the scene is scaled.

R13. Set `scene.render.film_transparent = True` before compositing over a plate — it does
    not change lighting, only the alpha of the background.
    Why: the world still contributes light; only its *camera-ray* visibility is dropped.
    Violation: agent removes the world to get alpha and loses all ambient light.

## 4. bpy patterns

### 4.1 Verified `bpy.types.Light` properties (5.2)

```python
L = bpy.data.lights["Key"]
# Common (all types)
L.type                 # 'POINT' | 'SUN' | 'SPOT' | 'AREA'
L.color                # RGB tint, scene-linear
L.use_temperature      # bool; when True, colour comes from `temperature`
L.temperature          # Kelvin (blackbody)
L.temperature_color    # read-only resulting RGB
L.energy               # POINT/SPOT/AREA: watts | SUN: watts per square metre
L.exposure             # multiplies intensity by 2**exposure
L.normalize            # keep total power constant when size/shape changes
L.diffuse_factor; L.specular_factor; L.transmission_factor; L.volume_factor
L.use_shadow
L.use_custom_distance; L.cutoff_distance
L.use_nodes; L.node_tree          # Cycles only; EEVEE ignores light node trees

# POINT / SPOT
L.shadow_soft_size     # emitter RADIUS in metres -> shadow softness
L.use_soft_falloff     # 4.1+: non-physical falloff near intersecting geometry

# SPOT
L.spot_size            # cone angle in RADIANS (1° .. 180°)
L.spot_blend           # 0..1 inner-cone fraction; 0 = razor edge
L.show_cone

# SUN
L.angle                # angular diameter in RADIANS (real sun ≈ 0.526° ≈ 0.00918 rad)
L.shadow_cascade_max_distance; L.shadow_cascade_count
L.shadow_cascade_exponent; L.shadow_cascade_fade

# AREA
L.shape                # 'SQUARE' | 'RECTANGLE' | 'DISK' | 'ELLIPSE'
L.size; L.size_y       # metres
L.spread               # beam spread in radians (Cycles; EEVEE ignores)

# EEVEE shadow controls (4.2+)
L.shadow_filter_radius; L.shadow_maximum_resolution
L.use_shadow_jitter; L.shadow_jitter_overblur; L.use_absolute_resolution
```

### 4.2 Creating lights without operators

```python
import bpy, math

def add_light(name, ltype, energy, location, rotation=(0, 0, 0), **kw):
    data = bpy.data.lights.new(name, type=ltype)   # 'POINT'|'SUN'|'SPOT'|'AREA'
    data.energy = energy
    for k, v in kw.items():
        setattr(data, k, v)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)   # link, or it will not render
    obj.location = location
    obj.rotation_euler = rotation
    return obj

key = add_light("Key", 'AREA', 200.0, (2.5, -2.5, 2.5),
                shape='RECTANGLE', size=1.5, size_y=1.0)
sun = add_light("Sun", 'SUN', 3.0, (0, 0, 10),
                rotation=(math.radians(50), 0, math.radians(-35)),
                angle=math.radians(2.0))
spot = add_light("Practical", 'SPOT', 120.0, (0, -3, 3),
                 spot_size=math.radians(45), spot_blend=0.25,
                 shadow_soft_size=0.05)
```

Aim a light at a target without operators:

```python
from mathutils import Vector
def aim_at(obj, target):
    d = (Vector(target) - obj.location)
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
```

### 4.3 Physical intensity reasoning

For a Lambertian surface of albedo ρ, the scene-linear pixel value the renderer stores is
its outgoing radiance `L = ρ · E / π`, where `E` is irradiance.

| Emitter | Irradiance at distance d | Watts for ρ=0.18 to land at 0.18 linear |
|---|---|---|
| Point / spot | `E = P / (4πd²)` | `P ≈ 4π²·d² ≈ 39.5·d²` W |
| Area (on-axis, small vs d) | `E ≈ P / (πd²)` | `P ≈ π²·d² ≈ 9.9·d²` W |
| Sun | `E = S · cosθ` | `S ≈ π ≈ 3.14` W/m² |

Practical table (18% grey subject reading ~0.18 scene-linear, before any Film Exposure):

| Distance | Point light | Area light | Sun |
|---|---|---|---|
| 1 m | ~40 W | ~10 W | 3.1 W/m² |
| 2 m | ~160 W | ~40 W | 3.1 W/m² (distance-independent) |
| 3 m | ~355 W | ~90 W | 3.1 W/m² |
| 5 m | ~990 W | ~250 W | 3.1 W/m² |
| 10 m | ~3950 W | ~990 W | 3.1 W/m² |

Real-world power values documented in the Blender manual (verified):

| Real light | Power | Suggested type |
|---|---|---|
| Candle | 0.05 W | Point |
| 800 lm LED bulb | 2.1 W | Point |
| 1000 lm light bulb | 2.9 W | Point |
| 1500 lm PAR38 floodlight | 4 W | Area, Disk |
| 2500 lm fluorescent tube | 4.5 W | Area, Rectangle |
| 5000 lm car headlight | 22 W | Spot, size 125° |

| Sun condition | Strength |
|---|---|
| Clear sky | 1000 W/m² |
| Cloudy sky | 500 W/m² |
| Overcast sky | 200 W/m² |
| Moonlight | 0.001 W/m² |

These real values are **8–9 stops brighter** than the "neutral" numbers above, exactly as
the manual warns. Two ways to reconcile:

```python
sc = bpy.context.scene
# (a) Physically correct lights + camera-style exposure compensation:
sun.data.energy = 1000.0                 # clear sky, W/m²
sc.view_settings.exposure = -8.3         # ≈ log2(1000/3.14) stops down, both engines
# (b) Or Cycles' film exposure (Cycles only, multiplies before the view transform):
sc.cycles.film_exposure = 1.0            # leave at 1.0 and use view_settings.exposure
```

`scene.view_settings.exposure` is engine-independent colour management (stops, `2**e`).
`scene.cycles.film_exposure` is a Cycles-only linear multiplier. Prefer the former so the
same number works for EEVEE and for the compositor.

### 4.4 Colour management the agent must check before judging a render

```python
vs = bpy.context.scene.view_settings
ds = bpy.context.scene.display_settings
print(ds.display_device, vs.view_transform, vs.look, vs.exposure, vs.gamma)

vs.view_transform = 'AgX'          # DEFAULT in 4.0-5.2 (verified in 5.2 source)
# Other 5.2 views: 'Standard', 'Filmic' (deprecated legacy), 'Filmic Log',
#   'ACES 1.3', 'ACES 2.0', 'Khronos PBR Neutral', 'False Color', 'Raw'
vs.look = 'None'                   # e.g. 'AgX - Punchy', 'AgX - Medium Contrast'
vs.exposure = 0.0
vs.gamma = 1.0
vs.use_white_balance = False       # 4.5+: white_balance_temperature / _tint

# Measure, don't eyeball:
vs.view_transform = 'False Color'  # grey = 16-22% (correct mid-grey), red = 80-97%,
                                   # white = clipped, blue = deep shadow
```

Look names are config-dependent — enumerate before assigning:

```python
print(vs.bl_rna.properties['view_transform'].enum_items.keys())
print(vs.bl_rna.properties['look'].enum_items.keys())
```

### 4.5 Three-point lighting rig

```python
import math
def three_point(target=(0, 0, 1), key_w=400, fill_ratio=0.25, rim_ratio=1.5, dist=3.0):
    def place(name, angle_deg, height, energy, size):
        a = math.radians(angle_deg)
        loc = (target[0] + dist*math.cos(a), target[1] + dist*math.sin(a),
               target[2] + height)
        o = add_light(name, 'AREA', energy, loc, shape='RECTANGLE',
                      size=size, size_y=size*0.7)
        aim_at(o, target)
        return o
    key  = place("Key",  -125, 1.2, key_w,             1.2)   # 45° off-axis, above
    fill = place("Fill",   -35, 0.2, key_w*fill_ratio, 2.0)   # opposite, large & soft
    rim  = place("Rim",     60, 1.8, key_w*rim_ratio,  0.4)   # behind, small & hard
    key.data.use_temperature  = True; key.data.temperature  = 5600   # daylight
    fill.data.use_temperature = True; fill.data.temperature = 6500   # sky bounce
    rim.data.use_temperature  = True; rim.data.temperature  = 4500
    return key, fill, rim
```

Ratios, not watts, are the contract: key 1.0, fill 0.2–0.5, rim 0.5–2.0.
Because irradiance is 1/d², `energy` must scale with `dist**2` when the rig is resized.

### 4.6 HDRI / world lighting

```python
import bpy, math

def setup_hdri(filepath, strength=1.0, yaw_deg=0.0, pitch_deg=0.0, world_name="World"):
    w = bpy.data.worlds.get(world_name) or bpy.data.worlds.new(world_name)
    bpy.context.scene.world = w
    w.use_nodes = True                      # 4.x: needed | 5.x: deprecated no-op
    nt = w.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld");    out.location   = (600, 0)
    bg  = nt.nodes.new("ShaderNodeBackground");     bg.location    = (350, 0)
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.location   = (50, 0)
    mp  = nt.nodes.new("ShaderNodeMapping");        mp.location    = (-200, 0)
    tc  = nt.nodes.new("ShaderNodeTexCoord");       tc.location    = (-450, 0)

    img = bpy.data.images.load(filepath, check_existing=True)
    img.colorspace_settings.name = 'Linear Rec.709'   # HDR/EXR are already linear
    env.image = img
    env.projection = 'EQUIRECTANGULAR'       # or 'MIRROR_BALL'

    mp.vector_type = 'POINT'
    mp.inputs["Rotation"].default_value = (math.radians(pitch_deg), 0.0,
                                           math.radians(yaw_deg))
    bg.inputs["Strength"].default_value = strength

    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"],    env.inputs["Vector"])
    nt.links.new(env.outputs["Color"],    bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w
```

Verified sockets: `ShaderNodeBackground` inputs `Color, Strength` (+ internal `Weight`),
output `Background`. `ShaderNodeOutputWorld` inputs `Surface, Volume`.
`ShaderNodeTexEnvironment` input `Vector`, output `Color`.

Flat-colour world with no HDRI:

```python
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs["Strength"].default_value = 1.0
```

Hide the HDRI from the camera but keep its lighting:

```python
bpy.context.scene.render.film_transparent = True   # transparent background, light kept
w.cycles_visibility.camera = False                 # Cycles: world invisible to camera rays
w.cycles.use_shadows = True                        # 5.2: world cast-shadow toggle
```

### 4.7 Light linking (added 4.0; Cycles + EEVEE in 5.x)

```python
def link_light_to(light_obj, receivers, exclude=()):
    col = bpy.data.collections.new(f"{light_obj.name}_receivers")
    light_obj.light_linking.receiver_collection = col
    for ob in receivers:
        col.objects.link(ob)
        col.collection_objects[ob.name].light_linking.link_state = 'INCLUDE'
    for ob in exclude:
        col.objects.link(ob)
        col.collection_objects[ob.name].light_linking.link_state = 'EXCLUDE'
    return col

# Shadow linking (who BLOCKS this light):
blockers = bpy.data.collections.new("rim_blockers")
rim.light_linking.blocker_collection = blockers
```

Semantics (from the manual): only includes → light affects **only** those;
only excludes → light affects everything **except** those; both → includes minus excludes.
Emissive mesh objects support light linking in Cycles only; Grease Pencil not at all.

### 4.8 Recipes

```python
# --- Product / studio: HDRI fill + large softbox key + white bounce card -------------
setup_hdri("/hdri/studio_small.exr", strength=0.6, yaw_deg=140)
key  = add_light("SoftboxKey", 'AREA', 300.0, (1.2, -1.6, 1.8),
                 shape='RECTANGLE', size=1.6, size_y=1.0)     # big = soft
fill = add_light("Bounce", 'AREA', 60.0, (-1.6, -0.6, 0.6),
                 shape='RECTANGLE', size=2.0, size_y=1.5)
rim  = add_light("Kicker", 'AREA', 250.0, (-0.9, 1.7, 1.4),
                 shape='RECTANGLE', size=0.5, size_y=0.15)    # small = crisp edge
for o in (key, fill, rim): aim_at(o, (0, 0, 0.3))
bpy.context.scene.view_settings.view_transform = 'Khronos PBR Neutral'  # colour-faithful

# --- Outdoor daylight ---------------------------------------------------------------
sun = add_light("Sun", 'SUN', 3.5, (0, 0, 20),
                rotation=(math.radians(55), 0, math.radians(-40)),
                angle=math.radians(0.526))     # real solar angular diameter -> crisp
setup_hdri("/hdri/sky_clear.exr", strength=1.0)   # sky = fill + reflections

# --- Overcast / soft everything -----------------------------------------------------
sun.data.energy = 1.2
sun.data.angle = math.radians(20.0)               # huge angular size -> no hard shadow
```

### 4.9 Lighting for realtime bake vs path traced

```python
sc = bpy.context.scene
if sc.render.engine == 'BLENDER_EEVEE':      # 5.x id (4.2-4.5: 'BLENDER_EEVEE_NEXT')
    sc.eevee.use_raytracing = True           # screen-space GI/reflections
    sc.eevee.use_shadows = True
    sc.eevee.shadow_ray_count = 2
    sc.eevee.shadow_step_count = 6
    sc.eevee.taa_render_samples = 64
    # Indirect light that screen tracing cannot see needs baked probes:
    #   object type 'LIGHT_PROBE', data.type in {'SPHERE','PLANE','VOLUME'}
    #   then bpy.ops.object.lightprobe_cache_bake(subset='ALL') inside a temp_override.
else:                                        # 'CYCLES'
    sc.cycles.use_light_tree = True          # essential with many lights
    sc.cycles.light_sampling_threshold = 0.01
    sc.cycles.max_bounces = 12
```

Practical differences that change how you *build* the rig:
- EEVEE: many small lights are cheap; huge emissive meshes are not a light source unless
  captured by a probe. Prefer explicit light objects.
- Cycles: emissive meshes are first-class lights; a few large area lights are cheaper and
  far less noisy than dozens of tiny bright ones.
- EEVEE ignores area `spread`, light node trees, and spot radius-driven cone softness.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'Object' object has no attribute 'energy'` | wrote to the object, not `obj.data` | `obj.data.energy = ...` |
| Scene renders almost black with several lights | watts far too low for the distance (1/d²) | use `≈40·d²` W (point) / `≈10·d²` W (area) |
| Whole render blown out white | real-world watts (1000 W/m² sun) with no exposure comp | `scene.view_settings.exposure = -8.3` |
| Shadows are hard and aliased no matter the sample count | `shadow_soft_size == 0` / `SUN.angle ≈ 0` | enlarge the emitter |
| Scene has no shadows at all and looks flat | `sun.data.angle` set in degrees (e.g. `30` = 30 rad) | `math.radians(...)` |
| Spot cone fills the whole frame | `spot_size` set in degrees | `spot_size = math.radians(45)` |
| Light exists but nothing is lit | light object never linked into a collection | `scene.collection.objects.link(obj)` |
| HDRI is washed out and casts no directional shadow | `.hdr` loaded as `'sRGB'` | `img.colorspace_settings.name = 'Linear Rec.709'` |
| `AttributeError: 'NoneType' object has no attribute 'nodes'` on world | `world.use_nodes` set expecting tree creation (no-op in 5.x) | use the tree from `bpy.data.worlds.new()` or rebuild nodes explicitly |
| No way found to rotate the HDRI | looked for a property; there is none | `TexCoord.Generated → Mapping.Rotation → Environment.Vector` |
| Light linking collection created but light still hits everything | objects added to the collection without `link_state` | set `collection_objects[name].light_linking.link_state = 'INCLUDE'` |
| Same scene looks completely different in EEVEE vs Cycles | area `spread`, light node tree, or spot softness — all EEVEE-unsupported | remove reliance on those, or accept engine divergence |
| Render "looks correct" but downstream comp says it is 3 stops hot | judged under AgX's highlight rolloff | verify with `'False Color'` or `'Standard'` |
| Background transparent but scene also went dark | world deleted instead of `film_transparent` | `scene.render.film_transparent = True`, keep the world |
| Colour temperature has no effect | `use_temperature` left False | `light.use_temperature = True` before setting `temperature` |
| EEVEE indirect bounce missing in a room interior | no light probe volume baked | add a `'VOLUME'` light probe and bake the probe cache |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Engine | EEVEE | Cycles | EEVEE | Cycles | Workbench |
| Primary rig | 1 SUN + HDRI | 3-point AREA + HDRI | 2 AREA, high key | HDRI + 2–3 AREA softboxes | studio (Workbench) |
| Key light type | AREA | AREA | AREA | AREA (`RECTANGLE`) | n/a |
| Key energy @2 m | 100–200 W | 150–400 W | 200–600 W | 200–500 W | n/a |
| Key size | 0.5–1 m | 1–2 m | 1–2 m | 1.5–3 m (very soft) | n/a |
| Fill : key ratio | 0.4 | 0.25 | 0.5 | 0.3 | n/a |
| Rim : key ratio | 0.5 | 1.5 | 1.0 | 1.0 | n/a |
| SUN energy | 2–4 W/m² | 3 W/m² | — | 2 W/m² | — |
| SUN angle | 2–5° | 0.526–3° | — | 0.526° (crisp) | — |
| HDRI strength | 0.3–0.6 | 0.5–1.0 | 0–0.3 | 0.5–1.0 | 0 |
| Colour temperature | 6500 K flat | key 5600 / fill 6500 / rim 4500 | stylised RGB | 5600 K neutral | n/a |
| `view_transform` | `AgX` | `AgX` | `Standard` (flat graphics) or `AgX` | `Khronos PBR Neutral` | `Standard` |
| `look` | `None` | `AgX - Medium Contrast` | `None` | `None` | `None` |
| `view_settings.exposure` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `film_transparent` | often True | False | True | True | False |
| Light linking used | rarely | yes (rim on character) | yes (per-element) | yes (specular kickers) | no |
| Volumetrics | off | sparingly | on for beams | off | off |
| Shadow softness source | light size | light size | light size | light size | n/a |

## 7. Verification checklist

- [ ] `assert any(o.type=='LIGHT' for o in bpy.context.view_layer.objects) or bpy.context.scene.world` — there is at least one light source in the render.
- [ ] `assert all(o.data.energy > 0 for o in bpy.data.objects if o.type=='LIGHT')` — no zero-power lights.
- [ ] `assert key.data.energy > 10 * key_distance**2` (area) — key is in a plausible wattage band for its distance.
- [ ] `import math; assert 0 < sun.data.angle < math.pi` — sun angle is radians, not degrees.
- [ ] `import math; assert 0 < spot.data.spot_size <= math.pi` — spot cone is radians.
- [ ] `assert bpy.context.scene.view_settings.view_transform in ('AgX','Standard','Khronos PBR Neutral','Filmic','ACES 1.3','ACES 2.0','False Color','Raw','Filmic Log')` — a known transform is active.
- [ ] `assert env_img.colorspace_settings.name.startswith('Linear')` — HDRI not double-decoded.
- [ ] `assert bg.inputs["Strength"].default_value > 0` — world actually emits.
- [ ] `assert light_obj.name in bpy.context.view_layer.objects` — lights are linked and enabled in this view layer.
- [ ] `assert col.collection_objects[ob.name].light_linking.link_state in ('INCLUDE','EXCLUDE')` — link states set, not defaulted.
- [ ] Render once with `view_transform='False Color'`: the subject's mid-tones should read **grey/green-cyan**, not blue (underexposed) and not red/white (clipped).
- [ ] Render once with `view_transform='Standard'`: confirms the scene-linear data is sane independently of AgX's rolloff.
- [ ] Numeric exposure check without a human: `import numpy as np; px = np.array(bpy.data.images['Render Result'].pixels[:])` is unreliable for Render Result — instead render to an EXR and read it back, then `assert 0.05 < np.median(rgb) < 0.5`.

## 8. Sources

- [Light Objects (types, Power of Lights tables) — Blender Manual](https://docs.blender.org/manual/en/latest/render/lights/light_object.html)
- [Light Linking — Blender Manual](https://docs.blender.org/manual/en/latest/render/lights/light_linking.html)
- [Color Management: Displays and Views (AgX, Filmic, Standard, False Color, Look, Exposure) — Blender Manual](https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html)
- [Color Management: Color Spaces / Working Space — Blender Manual](https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html)
- [EEVEE Limitations (light node trees, area spread, spot size) — Blender Manual](https://docs.blender.org/manual/en/latest/render/eevee/limitations/limitations.html)
- [Blender 4.0 Release Notes: Python API — light falloff/attenuation properties removed](https://developer.blender.org/docs/release_notes/4.0/python_api/)
- [Blender 4.1 Release Notes: Rendering — Soft Falloff on point/spot lights](https://developer.blender.org/docs/release_notes/4.1/rendering/)
- [Blender 5.0 Release Notes: Python API — `world.use_nodes` deprecation](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.2 Release Notes: EEVEE — light camera ray visibility](https://developer.blender.org/docs/release_notes/5.2/eevee/)
- [Blender 5.2 Release Notes: Rendering — light/shadow linking copy to selection](https://developer.blender.org/docs/release_notes/5.2/rendering/)
- AgX confirmed as the 5.2 default view transform in Blender source
  `source/blender/blenkernel/intern/scene.cc` (`BKE_color_managed_view_settings_init(..., "AgX")`),
  tag `v5.2.0`. Light RNA names verified in `source/blender/makesrna/intern/rna_light.cc`.
- The watts-per-distance table in §4.3 is **derived** from standard radiometry
  (`E = P/4πd²`, `L = ρE/π`), not published by Blender. `[UNVERIFIED]` as an official
  figure — treat as a starting point and confirm with the `False Color` view.
- Whether Blender's spot `spot_size` redistributes power (narrower cone = brighter) with
  `normalize` enabled is `[UNVERIFIED]` against primary docs. Determine empirically:
  render a flat plane, halve `spot_size`, compare median pixel value.

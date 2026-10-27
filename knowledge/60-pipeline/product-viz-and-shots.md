---
name: product-viz-and-shots
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Camera as a technical instrument — framing math, DOF, constraints, studio backdrops, turntables, shadow catchers, and the render-review loop.
loads_with: [optimization-realtime, scene-organization, export-interchange]
tags: [camera, framing, dof, turntable, shadow-catcher, studio, render-loop, compositing]
id: product-viz-and-shots
title: "Product Visualisation and Shot Construction"
when: [camera-framing, depth-of-field, turntable, studio-backdrop, transparent-film, render-review-loop]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Product Visualisation and Shot Construction

## Purpose
Treat the camera as a measurable instrument: solve framing numerically, set optics and DOF deliberately, build a studio/turntable shot, and run a cheap preview-then-final render loop whose only feedback is the image and numbers.

## When to Use / When NOT
- ALLOWED: placing and framing a camera from evaluated bounds — §4.1-4.2 (math verified numerically on 5.2.0).
- ALLOWED: DOF, constraints, studio backdrop, transparent film, turntables, preview/final render loop — §4.3-4.8.
- ALLOWED: choosing view transform and alpha-capable output for product stills — §4.5.
- NOT ALLOWED: lighting design and render-engine selection in depth — use `lighting` and `render-engines` instead.
- NOT ALLOWED: media delivery evidence (aspect preflight, decoded video, revision-bound packages) — use `native-render-delivery` instead.
- NOT ALLOWED: render-time or realtime performance tuning — use `optimization-realtime` instead.
- NOT ALLOWED: compositing and output file pipelines beyond alpha PNG/EXR — use `compositing-output` instead.

## Core Knowledge Content

### 1. Mental model

A camera in Blender is two data-blocks: an Object (where it is and where it
points) and a Camera data-block (`camera.data`: how it sees). Framing is
therefore two independent problems — a transform problem and an optics problem —
and an agent that conflates them ends up "zooming" by moving the camera, which
changes perspective, or "moving closer" by changing focal length, which does not.

Focal length is a *storytelling* control, not a framing control. It sets how much
perspective distortion the subject gets. Once focal length is chosen, distance
is determined by the framing requirement, and the math is closed-form: it is a
bounding-sphere-versus-half-FOV problem (verified numerically on 5.2.0, §4.2) <!-- ease:source S12 anchor="fovcheck, fill angular" -->.

Studio product rendering is a small, well-defined recipe: a seamless backdrop so
there is no horizon line, a key/fill/rim triad or a large softbox, a three-quarter
hero angle, shallow-but-not-silly depth of field, and a transparent film so the
image can be composited. Everything else is variation.

The most common agent failure is rendering at final quality on the first attempt
and burning minutes on a badly framed shot. The correct loop is: build → cheap
preview render → look at the image → critique → fix → final. The agent's only
feedback channel is the image, so it must actually produce and inspect one.

### 2. Decision first

<!-- ease:source UNVERIFIED reason="section 2 focal-length recommendations are photographic practice, not Blender documentation" -->

| Goal | Focal length (36 mm sensor) | Why |
|---|---|---|
| Product hero, minimal distortion | 85–135 mm | near-orthographic, flattering proportions, compresses the backdrop |
| Product three-quarter, some depth | 50–85 mm | natural, mild convergence |
| Small object, "macro" feel | 100 mm + close focus, f/2.8–5.6 | tight DOF, big bokeh |
| Interior / architecture | 18–24 mm | fits the room; expect vertical convergence — correct with `shift_y`, not tilt |
| Character portrait | 85–135 mm | no nose enlargement |
| Character full body / environment | 35–50 mm | context without distortion |
| Dramatic, aggressive, "action" | 16–24 mm close | exaggerated perspective |
| Technical/exploded diagram, no perspective | `type='ORTHO'` + `ortho_scale` | parallel edges, measurable |
| Motion graphics logo reveal | 35–50 mm, or ORTHO | taste |

| Shot problem | Solution |
|---|---|
| Subject must stay centred while something moves | `TRACK_TO` constraint on the camera |
| Camera must travel a defined path | `FOLLOW_PATH` constraint + a Curve, or parent to an animated Empty |
| Turntable of a product | rotate the **object** (see §4.6) |
| Orbit of a static environment | rotate the **camera** on a parented Empty |
| Product needs to sit on "nothing" | seamless backdrop + `film_transparent` + shadow catcher |
| Composite over a photo/plate | `is_shadow_catcher` on the ground, `film_transparent=True`, save PNG/EXR with alpha |
| Cut a hole in the render for real footage | `is_holdout=True` |
| Focus must follow a moving subject | `dof.focus_object`, not `focus_distance` |

### 3. Rules

R1. Choose focal length first, then solve for distance; never "zoom" to frame.
    Why: focal length changes perspective (the relationship between near and far features); distance changes framing. They are not interchangeable.
    Violation: the product looks bulbous (too wide) or pancake-flat (too long) after the agent "framed" it by changing `lens`.

R2. Frame from the evaluated world-space bounding box, not `ob.dimensions` or `ob.bound_box` alone.
    Why: `bound_box` is object-space and pre-modifier; `dimensions` ignores rotation of the bounding box in world space <!-- ease:source S15 anchor="rna Object.bound_box: object-space coordinates; Object.dimensions: absolute bounding box dimensions" -->.
    Violation: the subject overflows the frame after a modifier or a parent rotation.

R3. Set `scene.camera` explicitly. Never assume there is one.
    Why: in `--background` with `use_empty=True` there is no camera at all (`scene.camera` is None <!-- ease:source S16 anchor="active_object after empty None scene.camera None" -->), and `bpy.ops.render.render()` raises instead of producing an image.
    Violation: `RuntimeError: Error: Cannot render, no camera` (exact text observed on 5.2.0) <!-- ease:source S16 anchor="render no camera RuntimeError: Error: Cannot render, no camera" -->. **Correction:** the previous text quoted `Error: No camera found in scene` and a silent blank result.

R4. Use `dof.focus_object` (or `focus_subtarget`) when the subject moves; `focus_distance` only for static shots.
    Why: `focus_distance` is a scalar in camera space and will not follow anything <!-- ease:source S15 anchor="rna CameraDOFSettings.focus_object / focus_distance" -->.
    Violation: the subject drifts out of focus over an animation.

R5. `aperture_fstop` is a real f-stop: lower = shallower. Keep it ≥ 2.8 for product work unless bokeh is the point.
    Why: at f/1.4 with a 100 mm lens focused at 0.4 m, the total depth of field is about 1 mm (0.97 mm computed with c = 0.029 mm <!-- ease:source S19 anchor="f=100 N=1.4 total=0.974 mm" -->); the product will be mostly blurred. `aperture_fstop` lower = more defocus <!-- ease:source S15 anchor="rna CameraDOFSettings.aperture_fstop" --><!-- ease:source S6 anchor="F-Stop: lower values give strong depth of field effect" -->.
    Violation: only one edge of the product is sharp.

R6. Compose with `shift_x` / `shift_y`, not by tilting the camera, when you need to correct verticals.
    Why: shift is a sensor offset (a view-frustum shear) and keeps vertical lines vertical; tilting introduces keystone convergence. <!-- ease:source UNVERIFIED reason="optics rationale is photographic practice; Blender RNA only says 'Camera vertical shift'" -->
    Violation: a product/building that leans backwards.

R7. Set `render.image_settings.media_type` before `file_format` (5.0 API change).
    Why: `ImageFormatSettings` gained `media_type` in 5.0 and `file_format` is validated against it <!-- ease:source S3 anchor="ImageFormatSettings media_type must be set before file_format" -->.
    Violation: `TypeError: bpy_struct: item.attr = val: enum "FFMPEG" not found in (...)` (reproduced on 5.2.0: with media_type IMAGE, `FFMPEG` and `OPEN_EXR_MULTILAYER` are rejected) <!-- ease:source S13 anchor="IMAGE->FFMPEG TypeError; IMAGE->EXR_ML TypeError" --> or a silently wrong format.

R8. Turn on `film_transparent` and save with an alpha-capable format when compositing.
    Why: `color_mode='RGB'` throws the alpha away even with a transparent film (measured: minimum alpha 1.0 with RGB, 0.0 with RGBA <!-- ease:source S13 anchor="alpha RGB min alpha 1.0; RGBA min alpha 0.0" -->).
    Violation: a black background in the "transparent" PNG.

R9. Preview at low samples and low resolution percentage, then render final; never the other way around.
    Why: the agent's only feedback is the image, and a 5-second preview answers 90% of framing/lighting questions.
    Violation: a 20-minute render of a shot with the subject half out of frame.

R10. Rotate the object for a product turntable, not the camera, unless you are exploring an environment.
    Why: <!-- ease:source UNVERIFIED reason=""rotate the object, not the camera" is a reasoned production convention; Blender documents neither approach" --> a real turntable rotates the object under fixed lights; keeping lights and camera fixed keeps the key highlight pinned in screen space and lets reflections slide across the surface, which reads as "product on a platter". Rotating the camera alone changes the light-to-subject relationship every frame.
    Violation: the subject falls into shadow on some frames, or the floor shadow swings around the frame.

R11. Restore the render settings you changed for a preview.
    Why: `resolution_percentage`, `samples` and `use_simplify` are scene state, and the next render inherits them <!-- ease:source S15 anchor="rna RenderSettings.use_simplify" -->.
    Violation: the "final" render comes out at 25% resolution.

### 4. bpy patterns

#### 4.1 Build a camera from data, not operators

```python
import bpy, math

def make_camera(name="CAM_Hero", lens=85.0, sensor=36.0, col=None):
    cam = bpy.data.cameras.new(name)
    cam.type = 'PERSP'                 # 'PERSP' | 'ORTHO' | 'PANO' | 'CUSTOM'
    cam.lens = lens                    # mm; property is `lens`, not focal_length  [ease:source S15 anchor="rna Camera.lens: focal length in millimeters, default 50"]
    cam.lens_unit = 'MILLIMETERS'      # or 'FOV' to drive cam.angle directly
    cam.sensor_fit = 'AUTO'            # 'AUTO' | 'HORIZONTAL' | 'VERTICAL'
    cam.sensor_width = sensor          # mm, default 36.0  [ease:source S12 anchor="camera defaults sensor_width 36, sensor_height 24"]
    cam.sensor_height = 24.0           # only used when sensor_fit == 'VERTICAL'
    cam.clip_start = 0.01
    cam.clip_end = 1000.0
    cam.shift_x = 0.0
    cam.shift_y = 0.0
    ob = bpy.data.objects.new(name, cam)
    (col or bpy.context.scene.collection).objects.link(ob)
    bpy.context.scene.camera = ob      # MANDATORY
    return ob
```

`cam.angle` is the field of view in radians and is *derived* from
`lens`/`sensor_*`; writing either updates the other <!-- ease:source S15 anchor="rna Camera.angle: Camera lens field of view" -->. For an orthographic camera
only `ortho_scale` matters — it is the width (or height, per `sensor_fit`) of
the view in Blender units.

#### 4.2 Framing math — solve for distance

```python
import bpy, math
from mathutils import Vector

def world_bounds(objects, depsgraph=None):
    dg = depsgraph or bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in objects:
        ev = ob.evaluated_get(dg)
        mw = ev.matrix_world
        pts.extend(mw @ Vector(c) for c in ev.bound_box)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) * 0.5
    radius = max((p - centre).length for p in pts)     # bounding SPHERE radius
    return centre, radius, lo, hi

def half_fov(cam_data, scene):
    """Returns (half_h, half_v) in radians, honouring sensor_fit and aspect."""
    r = scene.render
    aspect = (r.resolution_x * r.pixel_aspect_x) / (r.resolution_y * r.pixel_aspect_y)
    f = cam_data.lens
    sw, sh = cam_data.sensor_width, cam_data.sensor_height
    fit = cam_data.sensor_fit
    # Verified on 5.2.0: with these formulas a point at depth d offset by d*tan(half_fov)
    # projects to u/v = 1.0 exactly, for 1920x1080 / 1080x1920, AUTO / VERTICAL / HORIZONTAL  [ease:source S12 anchor="fovcheck all 0.5 (centred) results"]
    if fit == 'HORIZONTAL' or (fit == 'AUTO' and aspect >= 1.0):
        hh = math.atan((sw * 0.5) / f)                 # sensor spans the width
        hv = math.atan(math.tan(hh) / aspect)
    elif fit == 'VERTICAL':
        hv = math.atan((sh * 0.5) / f)
        hh = math.atan(math.tan(hv) * aspect)
    else:                                              # AUTO, portrait render
        hv = math.atan((sw * 0.5) / f)                 # AUTO uses sensor_width
        hh = math.atan(math.tan(hv) * aspect)
    return hh, hv

def frame_distance(cam_data, scene, radius, fill=0.85):
    """Distance from the bounding-sphere centre so the sphere occupies `fill`
    of the tighter frame axis.

        the sphere of radius R subtends 2*asin(R/d)
        we want that to equal 2 * fill * theta   =>   d = R / sin(fill*theta)

    `fill` is an ANGULAR fraction of the half-FOV; the projected sphere radius is
    R/sqrt(d^2-R^2)/tan(theta) = 0.849 of the frame half-size for fill=0.85
    (measured  # ease:source S12 anchor="fill angular 0.85 tan ratio 0.8489"), i.e. close to but not exactly `fill`.
    """
    hh, hv = half_fov(cam_data, scene)
    theta = min(hh, hv)
    fill = max(1e-3, min(fill, 0.999))
    return radius / math.sin(fill * theta)

def aim(cam_ob, target_point, from_direction):
    """Place cam_ob along `from_direction` (unit vector) and point it at target."""
    d = Vector(from_direction).normalized()
    cam_ob.location = Vector(target_point) + d * aim.distance
    fwd = (Vector(target_point) - cam_ob.location).normalized()
    # camera looks down its local -Z with local +Y up
    cam_ob.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()

def frame_objects(cam_ob, objects, fill=0.85, direction=(1.0, -1.0, 0.6)):
    scene = bpy.context.scene
    centre, radius, lo, hi = world_bounds(objects)
    d = frame_distance(cam_ob.data, scene, radius, fill)
    aim.distance = d
    aim(cam_ob, centre, direction)
    if cam_ob.data.type == 'ORTHO':
        cam_ob.data.ortho_scale = 2.0 * radius / fill
    cam_ob.data.clip_start = max(1e-4, d - radius * 2.0)
    cam_ob.data.clip_end = d + radius * 4.0
    return dict(distance=d, radius=radius, centre=tuple(centre))   # unit cube, 85 mm, 16:9: distance 8.608, radius 0.866 (executed 5.2.0)  [ease:source S20 anchor="HARNESS frame"]
```

Blender also ships the exact solver as an RNA method, which fits the actual
bounding **box** rather than a sphere (tighter, but it does not give you a
direction):

```python
dg = bpy.context.evaluated_depsgraph_get()
coords = [c for ob in objects
            for corner in ob.evaluated_get(dg).bound_box
            for c in (ob.matrix_world @ Vector(corner))]
loc, ortho_scale = cam_ob.camera_fit_coords(dg, coords)
cam_ob.location = loc
if cam_ob.data.type == 'ORTHO':
    cam_ob.data.ortho_scale = ortho_scale
```

`Object.camera_fit_coords(depsgraph, coordinates)` keeps the camera's current
*rotation* and only moves it back along its view axis until everything fits
<!-- ease:source S1 anchor="camera_fit_coords" --><!-- ease:source S15 anchor="func camera_fit_coords: Compute the coordinate (and scale for ortho cameras)" -->; it returns `(location, ortho_scale)` and ran on 5.2.0 (`(-0.001,-0.003,3.794), 1.0` for a unit cube) <!-- ease:source S13 anchor="camera_fit_coords" -->.
Use it after `aim()` to tighten the framing exactly.

Verify the framing numerically instead of guessing:

```python
from bpy_extras.object_utils import world_to_camera_view

def frame_coverage(cam_ob, objects, scene=None):
    scene = scene or bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    us, vs, zs = [], [], []
    for ob in objects:
        ev = ob.evaluated_get(dg)
        for c in ev.bound_box:
            p = world_to_camera_view(scene, cam_ob, ev.matrix_world @ Vector(c))
            us.append(p.x); vs.append(p.y); zs.append(p.z)
    return dict(u=(min(us), max(us)), v=(min(vs), max(vs)),
                behind_camera=min(zs) < 0.0,
                inside=0.0 <= min(us) and max(us) <= 1.0
                       and 0.0 <= min(vs) and max(vs) <= 1.0)
```

`world_to_camera_view` returns normalised device coords where (0,0) is the
bottom-left of the frame and z is the distance in front of the camera (negative
means behind it) <!-- ease:source S2 anchor="world_to_camera_view" --><!-- ease:source S12 anchor="fovcheck" -->. This is the agent's ground truth for "is it in frame".

#### 4.3 Depth of field

```python
import bpy

def set_dof(cam_ob, focus_object=None, distance=None, fstop=5.6, blades=0):
    d = cam_ob.data.dof
    d.use_dof = True
    if focus_object is not None:
        d.focus_object = focus_object      # tracks automatically
        # d.focus_subtarget = "head"       # if focus_object is an Armature
    else:
        d.focus_distance = distance
    d.aperture_fstop = fstop               # default 2.8; lower = more blur  [ease:source S15 anchor="rna CameraDOFSettings.aperture_fstop default 2.8"]
    d.aperture_blades = blades             # 0 = circular; 6-8 = polygonal bokeh (RNA: at least 3)  [ease:source S15 anchor="rna CameraDOFSettings.aperture_blades"]
    d.aperture_rotation = 0.0
    d.aperture_ratio = 1.0                 # >1 = anamorphic-ish oval bokeh
    return d
```

Depth of field near/far limits, for reasoning about whether the whole product
will be sharp (`f` = focal length mm, `N` = f-stop, `c` = circle of confusion,
≈ 0.029 mm for a 36 mm sensor <!-- ease:source S10 anchor="CoC d/1500 = 0.029 mm for full-frame 35 mm" -->, `s` = focus distance in mm). The hyperfocal formula
is from the cited reference <!-- ease:source S9 anchor="H = f^2/(N c) + f" -->; the near/far closed forms were checked against the harmonic-mean relation
s = 2*Dn*Df/(Dn+Df) stated for optimal focus <!-- ease:source S11 anchor="focus set to harmonic mean of near and far" --><!-- ease:source S19 anchor="harmonic_mean = s for four lens/aperture cases" -->:

```
H     = f^2 / (N * c) + f            # hyperfocal distance
near  = s * (H - f) / (H + s - 2f)
far   = s * (H - f) / (H - s)        # infinite if s >= H
```

At 100 mm, f/5.6, focused at 400 mm the total DOF is a few millimetres (3.9 mm computed <!-- ease:source S19 anchor="f=100 N=5.6 total=3.898 mm" -->). For a
product where the whole object must be sharp, either raise the f-stop to 11–22,
or disable DOF and add blur in compositing.

#### 4.4 Camera constraints from Python

```python
import bpy

def track_to(cam_ob, target, up='UP_Y'):
    c = cam_ob.constraints.new(type='TRACK_TO')
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'   # camera looks down local -Z (enum verified 5.2.0)  [ease:source S16 anchor="TrackTo up_axis UP_X UP_Y UP_Z"]  [ease:source S12 anchor="TrackTo track_axis enum"]
    c.up_axis = up                      # 'UP_X' | 'UP_Y' | 'UP_Z'
    c.use_target_z = False
    return c

def follow_path(cam_ob, curve_ob, offset_factor=0.0, follow_curve=False):
    c = cam_ob.constraints.new(type='FOLLOW_PATH')
    c.target = curve_ob
    c.use_curve_follow = follow_curve   # False when a TRACK_TO also aims it
    c.use_fixed_location = True         # then offset_factor is 0..1 along path
    c.offset_factor = offset_factor
    c.forward_axis = 'FORWARD_Y'         # FollowPath enums verified 5.2.0  [ease:source S16 anchor="FollowPath fwd/up enums"]
    c.up_axis = 'UP_Z'
    return c

def damped_track(ob, target, axis='TRACK_NEGATIVE_Z'):
    c = ob.constraints.new(type='DAMPED_TRACK')   # no up-vector roll control
    c.target = target
    c.track_axis = axis
    return c
```

With `use_fixed_location=True`, animate `offset_factor` from 0 to 1 to travel the
whole curve; without it, animate the curve's `eval_time` instead (`Curve.eval_time` exists in 5.2.0 <!-- ease:source S16 anchor="curve eval_time True" -->). Combine
`FOLLOW_PATH` (position) with `TRACK_TO` (aim) and keep `use_curve_follow=False`
so the two do not fight.

To read the final world matrix produced by constraints, evaluate the depsgraph:
`cam_ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world`.

#### 4.5 Studio: seamless backdrop, shadow catcher, transparent film

```python
import bpy, math
from mathutils import Vector

def seamless_backdrop(name="SET_Backdrop", width=6.0, depth=6.0, height=4.0,
                      fillet=1.5, segments=16, col=None):
    """Floor -> quarter-round fillet -> back wall, as one mesh (a 'cyc' wall)."""
    verts, faces = [], []
    profile = [(depth * 0.5, 0.0)]                      # (y, z): front edge of the floor
    cy, cz = -depth * 0.5 + fillet, fillet              # centre of the fillet circle
    for i in range(segments + 1):                       # quarter circle, floor -> wall
        a = -math.pi * 0.5 - (math.pi * 0.5) * (i / segments)   # -90deg -> -180deg
        profile.append((cy + fillet * math.cos(a), cz + fillet * math.sin(a)))
    profile.append((-depth * 0.5, height))              # top of the back wall
    # Corrected: the previous profile started at the wall base and its arc began at
    # (y=-depth/2, z=fillet), producing a zig-zag instead of floor -> fillet -> wall.
    # Verified 5.2.0: y non-increasing, z non-decreasing, first (3,0), last (-3,4),
    # floor normal +Z, wall normal +Y  [ease:source S18 anchor="FIXTEST profile y non-increasing True; floor face normal z 1.0"].
    profile = [(0.0, y, z) for (y, z) in profile]       # (x, y, z) template
    n = len(profile)
    for x in (-width * 0.5, width * 0.5):
        verts.extend([(x, p[1], p[2]) for p in profile])
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update(); me.validate()
    ob = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(ob)
    ob.modifiers.new("Smooth", 'SUBSURF').levels = 1
    return ob

def as_shadow_catcher(ob, cycles_only=True):
    """Cycles: renders only the shadows/reflections received, transparent
    elsewhere, so the plate shows through."""
    ob.is_shadow_catcher = True
    ob.is_holdout = False
    return ob

def transparent_film(scene=None, exr=False):
    scene = scene or bpy.context.scene
    scene.render.film_transparent = True
    ims = scene.render.image_settings
    ims.media_type = 'IMAGE'            # 5.0: set BEFORE file_format
    ims.file_format = 'OPEN_EXR' if exr else 'PNG'
    ims.color_mode = 'RGBA'             # without this, alpha is discarded
    ims.color_depth = '32' if exr else '16'
    if exr:
        ims.exr_codec = 'ZIP'
    return ims
```

`Object.is_shadow_catcher` is documented as a Cycles feature ("Only render
shadows and reflections on this object, for compositing renders into real
footage") <!-- ease:source S15 anchor="rna Object.is_shadow_catcher" --><!-- ease:source S5 anchor="Shadow catcher section" -->. `Object.is_holdout` punches a zero-alpha hole instead. Per-collection
equivalents live on `LayerCollection.holdout` and
`LayerCollection.indirect_only`.

Colour management for product work — the enum is OCIO-config-driven, so resolve
it at runtime rather than hardcoding:

```python
vs = bpy.context.scene.view_settings
print([i.identifier for i in
       vs.bl_rna.properties['view_transform'].enum_items])
vs.view_transform = 'AgX'          # the default view transform in 5.2.0  [ease:source S13 anchor="default AgX"]; 'Standard' for flat/technical
vs.look = 'None'                   # valid AgX looks: 'None', 'AgX - Base Contrast', ... (list below)
# Correction: 'AgX - Medium Contrast' does NOT exist; setting it raises TypeError on 5.2.0.
vs.exposure = 0.0
```

Views available in the bundled sRGB config (5.2): `Standard`, `ACES 1.3`,
`ACES 2.0`, `Khronos PBR Neutral`, `AgX`, `Filmic`, `Filmic Log`, `False Color`,
`Raw` <!-- ease:source S13 anchor="view_transform enum error text" --><!-- ease:source S7 anchor="active_views list" -->. With `AgX` active the valid looks are `None`, `AgX - Punchy`,
`AgX - Greyscale`, `AgX - Very High Contrast`, `AgX - High Contrast`,
`AgX - Medium High Contrast`, `AgX - Base Contrast`, `AgX - Medium Low Contrast`,
`AgX - Low Contrast`, `AgX - Very Low Contrast` <!-- ease:source S13 anchor="look enum error text" --><!-- ease:source S7 anchor="looks: AgX - Base Contrast, Medium High Contrast, Punchy" --> (the look list is filtered by the active view transform, so re-read it after changing the view). Use `Khronos PBR Neutral` (a tone mapper designed to preserve base-colour appearance for product visualisation <!-- ease:source S8 anchor="PBR Neutral Tone Mapper" -->) when the render must match a glTF web viewer <!-- ease:source UNVERIFIED reason="viewer-matching advice is practice; the Khronos README documents the mapper, not Blender equivalence" -->,
`Standard` for texture/technical output, `AgX` for photographic product shots.

#### 4.6 Turntable — rotate the object, and why

Physical reality: a product turntable is a rotating platter under fixed lights
and a fixed camera. Reproducing that means animating the **subject**:

- The key highlight stays pinned in screen space, so every frame is "hero lit".
- Reflections and specular sweeps slide across the surface — the read that makes
  glossy products look glossy.
- The backdrop, floor contact shadow and any gradient stay put.
- The camera and lights need no animation at all, so there is nothing to desync.

Rotate the **camera** (with the lights parented to the same empty) only when the
subject is an environment or an assembly whose lighting was art-directed to
specific features, and you want the viewer to feel like they are walking around
it. Rotating the camera *alone*, with static lights, is almost always wrong: the
subject swings through the key light and falls into shadow on some frames.

```python
import bpy, math

def turntable(subject, frames=120, axis='Z', pivot=None, ccw=True):
    """Animate the subject through a full revolution. Returns (start, end)."""
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, frames
    scene.render.fps = 24

    # Rotate about a stable pivot: an Empty at the object's base centre.
    if pivot is None:
        from mathutils import Vector
        dg = bpy.context.evaluated_depsgraph_get()
        ev = subject.evaluated_get(dg)
        pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        cx = sum(p.x for p in pts) / 8.0
        cy = sum(p.y for p in pts) / 8.0
        cz = min(p.z for p in pts)
        pivot = bpy.data.objects.new(subject.name + "_TT", None)
        pivot.empty_display_type = 'PLAIN_AXES'
        pivot.location = (cx, cy, cz)
        subject.users_collection[0].objects.link(pivot)
        mw = subject.matrix_world.copy()
        subject.parent = pivot
        subject.matrix_parent_inverse = pivot.matrix_world.inverted()
        subject.matrix_world = mw

    i = 'XYZ'.index(axis)
    sign = 1.0 if ccw else -1.0
    pivot.rotation_mode = 'XYZ'
    for f, a in ((1, 0.0), (frames + 1, sign * 2.0 * math.pi)):
        pivot.rotation_euler[i] = a
        pivot.keyframe_insert("rotation_euler", index=i, frame=f)
    # constant velocity: no ease in/out.
    # Correction: Action.fcurves was removed in 5.0 (AttributeError); F-curves now live
    # on the channelbag of the object's action slot  [ease:source S3 anchor="legacy Action API removed: action.fcurves, groups, id_root"]  [ease:source S13 anchor="action.fcurves attr False; channelbag fcurves"].
    act = pivot.animation_data.action
    slot = pivot.animation_data.action_slot
    channelbag = act.layers[0].strips[0].channelbag(slot) if act else None
    for fc in (channelbag.fcurves if channelbag else []):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return pivot, (1, frames)
```

Keyframing the wrap-around at `frames + 1` rather than `frames` makes frame 1
and frame `frames + 1` identical, so rendering frames 1..`frames` gives a
seamless loop with no duplicated frame. Measured on 5.2.0 (Cycles CPU, seed 0, 4 samples): frames 1 and 121 of a 120-frame cube turntable differed by max abs pixel value 0.0 <!-- ease:source S16 anchor="turntable frame1 vs frame121 max abs diff 0.0" -->; the corrected linear-key code gave 180.0 degrees at frame 61 of 120 <!-- ease:source S18 anchor="FIXTEST rot at frame 61 deg 180.0" -->.

#### 4.7 Reusable turntable render loop

```python
import bpy, os, math

def render_turntable(subject, out_dir, frames=36, samples=64, res=(1024, 1024),
                     engine='CYCLES', fill=0.85, lens=85.0,
                     direction=(0.9, -1.0, 0.45), transparent=True):
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = engine                 # 'CYCLES' | 'BLENDER_EEVEE'
    if engine == 'CYCLES':
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
    else:
        scene.eevee.taa_render_samples = samples
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    ims = scene.render.image_settings
    ims.media_type = 'IMAGE'
    ims.file_format = 'PNG'
    ims.color_mode = 'RGBA' if transparent else 'RGB'

    cam = scene.camera or make_camera(lens=lens)
    cam.data.lens = lens
    frame_objects(cam, [subject], fill=fill, direction=direction)

    pivot, (a, b) = turntable(subject, frames=frames)
    scene.frame_start, scene.frame_end = a, b
    scene.render.filepath = os.path.join(out_dir, "tt_")
    bpy.ops.render.render(animation=True)        # writes tt_0001.png ...
    return sorted(os.listdir(out_dir))
```

Blender 5.0 (not 5.1, as previously stated) added optional `frame_start` / `frame_end` arguments to
`bpy.ops.render.render()` <!-- ease:source S3 anchor="render.render() operator now supports frame_start and frame_end" --><!-- ease:source S12 anchor="render.render params" -->, so a subrange can be rendered without mutating the
scene (the 5.1 Python API notes contain no such entry <!-- ease:source S4 anchor="no render.render entry" -->; verified: scene range stayed 1-3 and only frame 2 was written <!-- ease:source S14 anchor="anim files anim_0002.png range 1 3" -->):
`bpy.ops.render.render(animation=True, frame_start=10, frame_end=20)`.

#### 4.8 The render-review loop an agent should actually run

```python
import bpy, os

def preview(path="/tmp/preview.png", samples=16, pct=40, engine='CYCLES'):
    """Cheap look-at-it render. Returns the path; then LOOK at the image."""
    scene = bpy.context.scene
    prev = dict(pct=scene.render.resolution_percentage,
                fp=scene.render.filepath,
                engine=scene.render.engine,
                samples=getattr(scene.cycles, "samples", None))
    scene.render.engine = engine
    if engine == 'CYCLES':
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
    scene.render.resolution_percentage = pct
    scene.render.filepath = os.path.splitext(path)[0]
    ims = scene.render.image_settings
    ims.media_type = 'IMAGE'; ims.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    # restore
    scene.render.resolution_percentage = prev["pct"]
    scene.render.filepath = prev["fp"]
    if prev["samples"] is not None:
        scene.cycles.samples = prev["samples"]
    # Correction: a still is written to <filepath><extension> (e.g. shot.png). The previous
    # `frame_path(...)` return value appended a frame number AND used the restored filepath,
    # so it pointed at a file that does not exist  [ease:source S17 anchor="listdir shot.png vs frame_path shot0001.png"].
    return os.path.splitext(path)[0] + scene.render.file_extension

def final(path, samples=512, pct=100):
    scene = bpy.context.scene
    scene.cycles.samples = samples
    scene.render.resolution_percentage = pct
    scene.render.filepath = os.path.splitext(path)[0]
    bpy.ops.render.render(write_still=True)
    return os.path.splitext(path)[0] + scene.render.file_extension   # see preview(): frame_path() is wrong for stills
```

The loop, in order:

1. **Assert the shot is renderable.** `scene.camera is not None`, at least one
   light or a world with non-zero strength, and `frame_coverage(...)["inside"]`.
2. **Numeric framing check** (§4.2) — catches "subject off screen" before any
   pixels are rendered. This costs milliseconds.
3. **Preview render** at 16 samples / 40% (or `get_viewport_screenshot` when a
   GUI session is available — `bpy.ops.render.opengl` needs a real window and
   fails under `--background` with `RuntimeError: Error: Cannot use OpenGL render in background mode (no opengl context)` <!-- ease:source S16 anchor="opengl RuntimeError" -->).
4. **Self-critique the image** against a fixed checklist:
   - Is the subject fully inside the frame with intentional margin?
   - Is there a clear key light, and is the key side readable?
   - Are there blown highlights (pure white regions) or crushed blacks?
   - Is the horizon/backdrop seam visible where it should be seamless?
   - Is the focus on the subject's most important feature?
   - Are there black facets (flipped normals) or magenta squares (missing textures)?
   - Does the composition put the subject on a third, not dead centre, unless
     centring is intentional?
5. **Fix one thing at a time** and re-preview. Changing three things means you
   learn nothing from the next image.
6. **Final render** only when the preview is right, then verify the output file
   exists and is non-trivial.

```python
def shot_ready(scene=None):
    scene = scene or bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    lights = [o for o in dg.objects if o.type == 'LIGHT']
    world_strength = 0.0
    if scene.world and scene.world.node_tree:
        for n in scene.world.node_tree.nodes:
            if n.type == 'BACKGROUND':
                world_strength = n.inputs['Strength'].default_value
    assert scene.camera is not None, "scene.camera is None"
    assert lights or world_strength > 0.0, "no light source"
    assert scene.render.resolution_percentage == 100, "still in preview mode"
    return dict(camera=scene.camera.name, lights=len(lights),
                world_strength=world_strength,
                engine=scene.render.engine)
```

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Error: Cannot render, no camera` <!-- ease:source S16 anchor="render no camera" --> | `scene.camera` never assigned | `bpy.context.scene.camera = cam_ob` |
| Render is pure black | no light and world strength 0, or camera inside geometry, or `clip_start` too large | `shot_ready()`; check `clip_start`/`clip_end` |
| Render is pure white / blown | light strength in the thousands, or `exposure` too high | check light `energy` against distance²; `view_settings.exposure = 0` |
| Subject not in frame despite framing code | framed from object-space `bound_box` without `matrix_world` | use `world_bounds()`; verify with `frame_coverage()` |
| Subject clipped in half | `clip_start` larger than the near face distance | `clip_start = max(1e-4, d - radius*2)` |
| "Transparent" PNG has a black background | `color_mode='RGB'` | `color_mode='RGBA'` + `film_transparent=True` |
| `TypeError: ... enum "OPEN_EXR_MULTILAYER" not found` <!-- ease:source S13 anchor="IMAGE->EXR_ML TypeError" --> | `media_type` not set first (5.0 change) | `ims.media_type='MULTI_LAYER_IMAGE'` then `file_format` |
| Whole product blurry except one edge | `aperture_fstop` far too low | raise to 8–22, or disable DOF |
| Focus drifts during animation | used `focus_distance` on a moving subject | `dof.focus_object = subject` |
| Building/product leans backwards | camera tilted up | keep the camera level, use `shift_y` |
| Turntable: subject goes dark on some frames | rotated the camera while lights stayed fixed | rotate the object (§4.6), or parent the lights to the camera pivot |
| Turntable stutters / has a duplicate frame at the loop | last keyframe at `frames` instead of `frames + 1` | key the 360° at `frames + 1`, render 1..`frames` |
| Turntable wobbles | object origin not on the rotation axis | rotate a pivot Empty at the base centre, not the object |
| Shadow catcher renders as a grey plane | `is_shadow_catcher` set but `film_transparent=False` | enable transparent film |
| `RuntimeError: Error: Cannot use OpenGL render in background mode (no opengl context)` (observed 5.2.0; the previous text quoted a `poll() failed` message) <!-- ease:source S16 anchor="opengl RuntimeError" --> | no GL context in `--background` | use `bpy.ops.render.render()` or the MCP viewport screenshot |
| Final render came out tiny/noisy | `resolution_percentage` / `samples` left at preview values | restore them (§4.8) |
| `os.path.exists(returned_path)` is False after `preview()`/`final()` | old code returned `render.frame_path(...)` (adds a frame number) for a still | return `splitext(path)[0] + render.file_extension` <!-- ease:source S17 anchor="PV listdir ['shot.png']" --> |
| `TypeError: bpy_struct: item.attr = val: enum "BLENDER_EEVEE_NEXT" not found in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES')` <!-- ease:source S16 anchor="EEVEE_NEXT TypeError" --> (the previous symptom `'Scene' has no attribute 'eevee'` is wrong: `scene.eevee` exists) | wrong engine id — 5.0 renamed `BLENDER_EEVEE_NEXT` back to `BLENDER_EEVEE` <!-- ease:source S3 anchor="EEVEE engine identifier changed from BLENDER_EEVEE_NEXT to BLENDER_EEVEE" --> | `scene.render.engine = 'BLENDER_EEVEE'` |
| Colours look washed out vs. a web viewer | `view_transform='AgX'` vs the viewer's neutral tonemap | `'Khronos PBR Neutral'` or `'Standard'` |
| `TypeError: ... enum "AgX - Medium Contrast" not found in ('None', 'AgX - Punchy', ...)` | that look does not exist in the 5.2 OCIO config (the previous snippet used it) <!-- ease:source S7 anchor="looks list" --> | use `'None'` or `'AgX - Base Contrast'` and read the valid list from the error text |
| `AttributeError: 'Action' object has no attribute 'fcurves'` in the turntable | legacy Action API removed in 5.0 <!-- ease:source S3 anchor="legacy Action API removed" --> | use `act.layers[0].strips[0].channelbag(slot).fcurves` |

### 6. Parameter defaults by use case

<!-- ease:source UNVERIFIED reason="section 6 per-use-case defaults (lens, fill, samples, resolutions) are practice-derived starting points, not documented by Blender" -->

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `camera.data.lens` | 50–60 (gameplay FOV) | 50 (full body) / 85 (close) | 35–50 | 85–135 | n/a (ORTHO for checks) |
| `camera.data.type` | `'PERSP'` | `'PERSP'` | `'PERSP'` | `'PERSP'` | `'ORTHO'` for measurable views |
| `sensor_width` | 36.0 | 36.0 | 36.0 | 36.0 | 36.0 |
| `sensor_fit` | `'AUTO'` | `'AUTO'` | `'AUTO'` | `'HORIZONTAL'` | `'AUTO'` |
| `dof.use_dof` | False | True (close-ups) | taste | True | False |
| `dof.aperture_fstop` | n/a | 2.0–4.0 | 2.8 | 5.6–16 | n/a |
| DOF focus | n/a | `focus_object` (head) | `focus_object` | `focus_object` (subject) | n/a |
| Framing `fill` fraction | 0.7 | 0.75 | 0.6–0.8 | 0.80–0.88 | 0.95 (technical) |
| Hero direction vector | n/a | (0.6,-1,0.25) eye-level | varies | (0.9,-1,0.45) three-quarter high | axis-aligned front/side/top |
| Background | engine skybox | plate/HDRI | solid/gradient | seamless backdrop + `film_transparent` | flat |
| `film_transparent` | n/a | True (comp) | True | True | False |
| `is_shadow_catcher` on ground | n/a | True (comp) | optional | True | n/a |
| `view_transform` | `'Khronos PBR Neutral'` | `'AgX'` | `'AgX'` or `'Standard'` | `'AgX'` | `'Standard'` |
| Preview samples / % | 8 / 30 | 16 / 40 | 16 / 40 | 16 / 40 | n/a |
| Final samples | 64 (bakes) | 256 | 128–256 | 512–1024 | n/a |
| Final resolution | 1024² | 1920×1080 | 1920×1080 | 2048–4096² | n/a |
| Turntable frames | 36 | n/a | 120 | 120–180 | 36 (inspection) |
| Turntable rotates | object | n/a | either | **object** | object |
| Output format | PNG RGBA | EXR multilayer | PNG/EXR | PNG RGBA 16-bit | PNG (contact sheet) |

### 7. Verification checklist

- [ ] `assert bpy.context.scene.camera is not None` — there is a camera.
- [ ] `assert shot_ready()["lights"] > 0 or shot_ready()["world_strength"] > 0` — there is light.
- [ ] `c = frame_coverage(cam, [subject]); assert c["inside"] and not c["behind_camera"]` — subject is fully in frame.
- [ ] `assert 0.55 < (c["v"][1] - c["v"][0]) < 0.95` — the subject fills a sensible fraction of the frame.
- [ ] `assert cam.data.clip_start < dist - radius and cam.data.clip_end > dist + radius` — nothing clipped.
- [ ] `assert cam.data.dof.focus_object is subject or cam.data.dof.focus_distance > 0` — focus is set deliberately.
- [ ] `assert bpy.context.scene.render.image_settings.color_mode == 'RGBA'` when `film_transparent` — alpha survives.
- [ ] `assert os.path.getsize(preview_path) > 5000` — the render actually wrote pixels.
- [ ] Load the preview and check it is not uniform: `img = bpy.data.images.load(p); px = img.pixels[:]; assert max(px) - min(px) > 0.05` — catches all-black and all-white renders numerically.
- [ ] Turntable loop: render frame 1 and frame `frames + 1` and assert the images are pixel-identical (holds for deterministic CPU Cycles with a fixed seed <!-- ease:source S16 anchor="turntable max abs diff 0.0" -->; allow a small tolerance on GPU/animated seeds <!-- ease:source UNVERIFIED reason="GPU and animated-seed behaviour not measured" -->).
- [ ] After the final render, `assert bpy.context.scene.render.resolution_percentage == 100`.
- [ ] Visually (screenshot): key light readable, no blown highlights, backdrop seamless, no black facets, subject not dead-centre unless intended.

## Failure Modes (Mandatory)
- **`RuntimeError: Error: Cannot render, no camera`** — cause: `scene.camera` is None after `read_homefile(use_empty=True)` — fix: create a camera data-block and assign `scene.camera` <!-- ease:source S16 anchor="render no camera" -->.
- **Turntable raises `AttributeError: 'Action' object has no attribute 'fcurves'`** — cause: the legacy Action API was removed in 5.0 — fix: iterate the slot's channelbag `fcurves` <!-- ease:source S3 anchor="legacy Action API removed" -->.
- **`TypeError` setting `view_settings.look = 'AgX - Medium Contrast'`** — cause: the look is not in the 5.2 OCIO config — fix: `'None'` or `'AgX - Base Contrast'` <!-- ease:source S7 anchor="looks list" -->.
- **"Transparent" PNG has an opaque background** — cause: `color_mode='RGB'` drops alpha (minimum alpha measured 1.0) — fix: `RGBA` plus `film_transparent=True` <!-- ease:source S13 anchor="alpha RGB min alpha 1.0" -->.
- **Backdrop renders as a zig-zag or has no floor-to-wall curve** — cause: the old `seamless_backdrop` profile started at the wall base — fix: use the corrected profile (floor, fillet arc, wall) <!-- ease:source S18 anchor="FIXTEST profile y non-increasing True" -->.
- **Returned preview path does not exist** — cause: `frame_path()` adds a frame number and the filepath was already restored — fix: return `splitext(path)[0] + render.file_extension` <!-- ease:source S17 anchor="PV listdir ['shot.png']" -->.

## Sources
- [S1] bpy.types.Object (Blender Python API) — https://docs.blender.org/api/current/bpy.types.Object.html → knowledge/_evidence/kb-261013/w5-bpy-Object.html — captured 2026-10-13 — sha256 aff5f361c74fa0ec3b89791f20fc2f9acf4f965f0d7b3a38de7936be3501f97d
- [S2] bpy_extras.object_utils (world_to_camera_view) — https://docs.blender.org/api/current/bpy_extras.object_utils.html → knowledge/_evidence/kb-261013/w5-bpy-extras-object-utils.html — captured 2026-10-13 — sha256 a71ab85dd4b87f74f722f7d11908d464b9e4c887be1b72adc223068a8d1c3ecb
- [S3] Blender 5.0 release notes: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ → knowledge/_evidence/kb-261013/w5-rn50-python.html — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S4] Blender 5.1 release notes: Python API (no render.render frame-range entry found) — https://developer.blender.org/docs/release_notes/5.1/python_api/ → knowledge/_evidence/kb-261013/w5-rn51-python.html — captured 2026-10-13 — sha256 31318ad73ff7341f91354696cb8e587c37de05909caf7e065ed5aef7407e14b4
- [S5] Blender 5.2 Manual: Cycles object settings (shadow catcher, holdout) — https://docs.blender.org/manual/en/latest/render/cycles/object_settings/object_data.html → knowledge/_evidence/kb-261013/w5-man-shadow-catcher.html — captured 2026-10-13 — sha256 476438655abd9c6b31a2b1091fc9ddee222cb43f0ca842a0de758e729a5a1032
- [S6] Blender 5.2 Manual: Cameras (depth of field) — https://docs.blender.org/manual/en/latest/render/cameras.html → knowledge/_evidence/kb-261013/w5-man-camera-dof.html — captured 2026-10-13 — sha256 a450246f0afbd18e8117f1caa533c58b04a3e59f85a671a8191f35096d1d2282
- [S7] Blender bundled OCIO config.ocio (views, looks) — https://projects.blender.org/blender/blender/raw/branch/main/release/datafiles/colormanagement/config.ocio → knowledge/_evidence/kb-261013/w5-ocio-config-src.ocio — captured 2026-10-13 — sha256 066a440ed1c02551fa3cacbb3af5d22d2efde7e4da5f2c14dffcca00c47751a0
- [S8] Khronos PBR Neutral tone mapper README — https://github.com/KhronosGroup/ToneMapping/blob/main/PBR_Neutral/README.md → knowledge/_evidence/kb-261013/w5-khronos-pbr-neutral.html — captured 2026-10-13 — sha256 b69714e874c449889d53149f36b5ea0152c775f67a7e354d86bae0d8b35652d3
- [S9] Wikipedia: Hyperfocal distance (community reference) — https://en.wikipedia.org/wiki/Hyperfocal_distance → knowledge/_evidence/kb-261013/w5-wiki-hyperfocal.html — captured 2026-10-13 — sha256 ceaba373f88ce0fb772172cc2cb1a7aa3853227c69e566ce510b30cf304a6ccf
- [S10] Wikipedia: Circle of confusion (community reference) — https://en.wikipedia.org/wiki/Circle_of_confusion → knowledge/_evidence/kb-261013/w5-wiki-circle-of-confusion.html — captured 2026-10-13 — sha256 c456a332505f2db6a5d35982360da21e6f85cc212684152f79b886068af2deb6
- [S11] Wikipedia: Depth of field (community reference) — https://en.wikipedia.org/wiki/Depth_of_field → knowledge/_evidence/kb-261013/w5-wiki-dof.html — captured 2026-10-13 — sha256 fdf20227545cfdeecf84d99286dd434f442f370274f4e1a15a194527c1fff87f
- [S12] Blender 5.2.0 LTS runtime probe 1 (API shape, defaults, framing math); script w5-probe-blender-52-api.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe-output.txt — captured 2026-10-13 — sha256 9fe8eb4c002bea2338899e4090d52659e26418189a9363838b9dab08fc386974
- [S13] Blender 5.2.0 LTS runtime probe 2 (hide flags, glTF filters, USD names, decimate, alpha); script w5-probe2-blender-52-behaviour.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe2-output.txt — captured 2026-10-13 — sha256 563dd275f28aedc3f35dce792110ba10e400f4467ff7263b1616da0273aa32d1
- [S14] Blender 5.2.0 LTS runtime probe 3 (F12 render alpha test per hide flag, glTF exclude); script w5-probe3-blender-52-render-visibility.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe3-output.txt — captured 2026-10-13 — sha256 7bc31c8d17a854077b7205ff9ca725fdb5aabc12bb871bdfdf37f51f2815e7b0
- [S15] Blender 5.2.0 LTS runtime probe 4 (RNA descriptions, Principled inputs, modifier defaults); script w5-probe4-blender-52-rna-descriptions.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe4-output.txt — captured 2026-10-13 — sha256 bcefc0f57b0b5accab6fe6d589b642ca522734407791b0eb4b795b0280d7c54e
- [S16] Blender 5.2.0 LTS runtime probe 5 (purge, reload, error texts, enums, turntable closure); script w5-probe5-blender-52-misc.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe5-output.txt — captured 2026-10-13 — sha256 2ed858235c4be1a8e6dc98c618b9d757f9e79a72517fb17b92c25d3eb4ca1179
- [S17] Blender 5.2.0 LTS runtime probe 8 (still-image output path vs frame_path); script w5-probe8-still-path.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe8-output.txt — captured 2026-10-13 — sha256 ee047d205680d348dd0a15f504c998b2ed449f5afe635c36041759fc5287c820
- [S18] Corrected-snippet test run (backdrop profile, linear keys, AgX look); script w5-code-fix-test.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-code-fix-test-output.txt — captured 2026-10-13 — sha256 5b03068870f3224061f2675246d8d769608f6a653c397cfd378939e6790eb681
- [S19] DOF closed-form check against the harmonic-mean relation; script w5-dof-formula-check.py — local run python3 → knowledge/_evidence/kb-261013/w5-dof-formula-check-output.txt — captured 2026-10-13 — sha256 2d66d5a7672b90c013583f56746cef3580834b026066ecce4214922589c24425
- [S20] Blender 5.2.0 LTS harness run: this module's python blocks executed after the corrections (camera, framing, DOF, constraints, backdrop, turntable, render loop) — local run /Applications/Blender.app (harness knowledge/_evidence/kb-261013/w5-harness-product-viz-output.txt) → knowledge/_evidence/kb-261013/w5-harness-product-viz-output.txt — captured 2026-10-13 — sha256 56aaf33108029ffcb5d3f8773aef9bb0713e6dda294bf1ba1e331a3bf324da4e
- Retained unverified note: `Object.is_shadow_catcher` behaviour under EEVEE in 5.2 — Blender documents it only under Cycles; assume Cycles-only and use `is_holdout` + compositing for EEVEE. <!-- ease:source UNVERIFIED reason="retained from original sources list; no primary source found" -->
- Retained unverified note: The focal-length recommendations, framing `fill` fractions and the DOF circle-of-confusion constant (0.029 mm) are photographic practice, not Blender documentation. <!-- ease:source UNVERIFIED reason="retained from original sources list; no primary source found" -->
- Retained unverified note: "Rotate the object, not the camera" for turntables is a reasoned production convention; Blender documents neither approach. <!-- ease:source UNVERIFIED reason="retained from original sources list; no primary source found" -->

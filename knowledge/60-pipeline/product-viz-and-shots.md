---
name: product-viz-and-shots
domain: pipeline
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Camera as a technical instrument — framing math, DOF, constraints, studio backdrops, turntables, shadow catchers, and the render-review loop.
loads_with: [optimization-realtime, scene-organization, export-interchange]
tags: [camera, framing, dof, turntable, shadow-catcher, studio, render-loop, compositing]
---

# Product Visualisation and Shot Construction

## 1. Mental model

A camera in Blender is two data-blocks: an Object (where it is and where it
points) and a Camera data-block (`camera.data`: how it sees). Framing is
therefore two independent problems — a transform problem and an optics problem —
and an agent that conflates them ends up "zooming" by moving the camera, which
changes perspective, or "moving closer" by changing focal length, which does not.

Focal length is a *storytelling* control, not a framing control. It sets how much
perspective distortion the subject gets. Once focal length is chosen, distance
is determined by the framing requirement, and the math is closed-form: it is a
bounding-sphere-versus-half-FOV problem.

Studio product rendering is a small, well-defined recipe: a seamless backdrop so
there is no horizon line, a key/fill/rim triad or a large softbox, a three-quarter
hero angle, shallow-but-not-silly depth of field, and a transparent film so the
image can be composited. Everything else is variation.

The most common agent failure is rendering at final quality on the first attempt
and burning minutes on a badly framed shot. The correct loop is: build → cheap
preview render → look at the image → critique → fix → final. The agent's only
feedback channel is the image, so it must actually produce and inspect one.

## 2. Decision first

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

## 3. Rules

R1. Choose focal length first, then solve for distance; never "zoom" to frame.
    Why: focal length changes perspective (the relationship between near and far features); distance changes framing. They are not interchangeable.
    Violation: the product looks bulbous (too wide) or pancake-flat (too long) after the agent "framed" it by changing `lens`.

R2. Frame from the evaluated world-space bounding box, not `ob.dimensions` or `ob.bound_box` alone.
    Why: `bound_box` is object-space and pre-modifier; `dimensions` ignores rotation of the bounding box in world space.
    Violation: the subject overflows the frame after a modifier or a parent rotation.

R3. Set `scene.camera` explicitly. Never assume there is one.
    Why: in `--background` with `use_empty=True` there is no camera at all, and `bpy.ops.render.render()` returns without producing an image.
    Violation: `RuntimeError: Error: No camera found in scene` or a blank Render Result.

R4. Use `dof.focus_object` (or `focus_subtarget`) when the subject moves; `focus_distance` only for static shots.
    Why: `focus_distance` is a scalar in camera space and will not follow anything.
    Violation: the subject drifts out of focus over an animation.

R5. `aperture_fstop` is a real f-stop: lower = shallower. Keep it ≥ 2.8 for product work unless bokeh is the point.
    Why: at f/1.4 with a 100 mm lens at 0.4 m, the depth of field is a few millimetres; the product will be mostly blurred.
    Violation: only one edge of the product is sharp.

R6. Compose with `shift_x` / `shift_y`, not by tilting the camera, when you need to correct verticals.
    Why: shift is a sensor offset (a view-frustum shear) and keeps vertical lines vertical; tilting introduces keystone convergence.
    Violation: a product/building that leans backwards.

R7. Set `render.image_settings.media_type` before `file_format` (5.0 API change).
    Why: `ImageFormatSettings` gained `media_type` in 5.0 and `file_format` is validated against it.
    Violation: `TypeError: bpy_struct: item.attr = val: enum "FFMPEG" not found in (...)` or a silently wrong format.

R8. Turn on `film_transparent` and save with an alpha-capable format when compositing.
    Why: `color_mode='RGB'` throws the alpha away even with a transparent film.
    Violation: a black background in the "transparent" PNG.

R9. Preview at low samples and low resolution percentage, then render final; never the other way around.
    Why: the agent's only feedback is the image, and a 5-second preview answers 90% of framing/lighting questions.
    Violation: a 20-minute render of a shot with the subject half out of frame.

R10. Rotate the object for a product turntable, not the camera, unless you are exploring an environment.
    Why: a real turntable rotates the object under fixed lights; keeping lights and camera fixed keeps the key highlight pinned in screen space and lets reflections slide across the surface, which reads as "product on a platter". Rotating the camera alone changes the light-to-subject relationship every frame.
    Violation: the subject falls into shadow on some frames, or the floor shadow swings around the frame.

R11. Restore the render settings you changed for a preview.
    Why: `resolution_percentage`, `samples` and `use_simplify` are scene state, and the next render inherits them.
    Violation: the "final" render comes out at 25% resolution.

## 4. bpy patterns

### 4.1 Build a camera from data, not operators

```python
import bpy, math

def make_camera(name="CAM_Hero", lens=85.0, sensor=36.0, col=None):
    cam = bpy.data.cameras.new(name)
    cam.type = 'PERSP'                 # 'PERSP' | 'ORTHO' | 'PANO' | 'CUSTOM'
    cam.lens = lens                    # mm; property is `lens`, not focal_length
    cam.lens_unit = 'MILLIMETERS'      # or 'FOV' to drive cam.angle directly
    cam.sensor_fit = 'AUTO'            # 'AUTO' | 'HORIZONTAL' | 'VERTICAL'
    cam.sensor_width = sensor          # mm, default 36.0
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
`lens`/`sensor_*`; writing either updates the other. For an orthographic camera
only `ortho_scale` matters — it is the width (or height, per `sensor_fit`) of
the view in Blender units.

### 4.2 Framing math — solve for distance

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
    return dict(distance=d, radius=radius, centre=tuple(centre))
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
*rotation* and only moves it back along its view axis until everything fits.
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
means behind it). This is the agent's ground truth for "is it in frame".

### 4.3 Depth of field

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
    d.aperture_fstop = fstop               # default 2.8; lower = more blur
    d.aperture_blades = blades             # 0 = circular; 6-8 = polygonal bokeh
    d.aperture_rotation = 0.0
    d.aperture_ratio = 1.0                 # >1 = anamorphic-ish oval bokeh
    return d
```

Depth of field near/far limits, for reasoning about whether the whole product
will be sharp (`f` = focal length mm, `N` = f-stop, `c` = circle of confusion,
≈ 0.029 mm for a 36 mm sensor, `s` = focus distance in mm):

```
H     = f^2 / (N * c) + f            # hyperfocal distance
near  = s * (H - f) / (H + s - 2f)
far   = s * (H - f) / (H - s)        # infinite if s >= H
```

At 100 mm, f/5.6, focused at 400 mm the total DOF is a few millimetres. For a
product where the whole object must be sharp, either raise the f-stop to 11–22,
or disable DOF and add blur in compositing.

### 4.4 Camera constraints from Python

```python
import bpy

def track_to(cam_ob, target, up='UP_Y'):
    c = cam_ob.constraints.new(type='TRACK_TO')
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'   # camera looks down local -Z
    c.up_axis = up                      # 'UP_X' | 'UP_Y' | 'UP_Z'
    c.use_target_z = False
    return c

def follow_path(cam_ob, curve_ob, offset_factor=0.0, follow_curve=False):
    c = cam_ob.constraints.new(type='FOLLOW_PATH')
    c.target = curve_ob
    c.use_curve_follow = follow_curve   # False when a TRACK_TO also aims it
    c.use_fixed_location = True         # then offset_factor is 0..1 along path
    c.offset_factor = offset_factor
    c.forward_axis = 'FORWARD_Y'
    c.up_axis = 'UP_Z'
    return c

def damped_track(ob, target, axis='TRACK_NEGATIVE_Z'):
    c = ob.constraints.new(type='DAMPED_TRACK')   # no up-vector roll control
    c.target = target
    c.track_axis = axis
    return c
```

With `use_fixed_location=True`, animate `offset_factor` from 0 to 1 to travel the
whole curve; without it, animate the curve's `eval_time` instead. Combine
`FOLLOW_PATH` (position) with `TRACK_TO` (aim) and keep `use_curve_follow=False`
so the two do not fight.

To read the final world matrix produced by constraints, evaluate the depsgraph:
`cam_ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world`.

### 4.5 Studio: seamless backdrop, shadow catcher, transparent film

```python
import bpy, math
from mathutils import Vector

def seamless_backdrop(name="SET_Backdrop", width=6.0, depth=6.0, height=4.0,
                      fillet=1.5, segments=16, col=None):
    """Floor -> quarter-round fillet -> back wall, as one mesh (a 'cyc' wall)."""
    verts, faces = [], []
    profile = [(-depth * 0.5, 0.0)]
    cx, cz = -depth * 0.5 + fillet, fillet
    for i in range(segments + 1):                       # quarter circle
        a = math.pi + (math.pi * 0.5) * (i / segments)  # 180deg -> 270deg
        profile.append((cx + fillet * math.cos(a), cz + fillet * math.sin(a)))
    profile.append((-depth * 0.5, height))
    profile = [(0.0, y, z) for (y, z) in profile]       # forward to +Y..
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
footage"). `Object.is_holdout` punches a zero-alpha hole instead. Per-collection
equivalents live on `LayerCollection.holdout` and
`LayerCollection.indirect_only`.

Colour management for product work — the enum is OCIO-config-driven, so resolve
it at runtime rather than hardcoding:

```python
vs = bpy.context.scene.view_settings
print([i.identifier for i in
       vs.bl_rna.properties['view_transform'].enum_items])
vs.view_transform = 'AgX'          # 4.0+ default; 'Standard' for flat/technical
vs.look = 'AgX - Medium Contrast'  # 'None' for no artistic look
vs.exposure = 0.0
```

Views available in the bundled sRGB config (5.2): `Standard`, `ACES 1.3`,
`ACES 2.0`, `Khronos PBR Neutral`, `AgX`, `Filmic`, `Filmic Log`, `False Color`,
`Raw`. Use `Khronos PBR Neutral` when the render must match a glTF web viewer,
`Standard` for texture/technical output, `AgX` for photographic product shots.

### 4.6 Turntable — rotate the object, and why

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
    # constant velocity: no ease in/out
    act = pivot.animation_data.action
    for fc in act.fcurves if act else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return pivot, (1, frames)
```

Keyframing the wrap-around at `frames + 1` rather than `frames` makes frame 1
and frame `frames + 1` identical, so rendering frames 1..`frames` gives a
seamless loop with no duplicated frame.

### 4.7 Reusable turntable render loop

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

Blender 5.1 added optional `frame_start` / `frame_end` arguments to
`bpy.ops.render.render()`, so a subrange can be rendered without mutating the
scene:
`bpy.ops.render.render(animation=True, frame_start=10, frame_end=20)`.

### 4.8 The render-review loop an agent should actually run

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
    return scene.render.frame_path(frame=scene.frame_current)

def final(path, samples=512, pct=100):
    scene = bpy.context.scene
    scene.cycles.samples = samples
    scene.render.resolution_percentage = pct
    scene.render.filepath = os.path.splitext(path)[0]
    bpy.ops.render.render(write_still=True)
    return scene.render.frame_path(frame=scene.frame_current)
```

The loop, in order:

1. **Assert the shot is renderable.** `scene.camera is not None`, at least one
   light or a world with non-zero strength, and `frame_coverage(...)["inside"]`.
2. **Numeric framing check** (§4.2) — catches "subject off screen" before any
   pixels are rendered. This costs milliseconds.
3. **Preview render** at 16 samples / 40% (or `get_viewport_screenshot` when a
   GUI session is available — `bpy.ops.render.opengl` needs a real window and
   fails under `--background`).
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

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `RuntimeError: Error: No camera found in scene` | `scene.camera` never assigned | `bpy.context.scene.camera = cam_ob` |
| Render is pure black | no light and world strength 0, or camera inside geometry, or `clip_start` too large | `shot_ready()`; check `clip_start`/`clip_end` |
| Render is pure white / blown | light strength in the thousands, or `exposure` too high | check light `energy` against distance²; `view_settings.exposure = 0` |
| Subject not in frame despite framing code | framed from object-space `bound_box` without `matrix_world` | use `world_bounds()`; verify with `frame_coverage()` |
| Subject clipped in half | `clip_start` larger than the near face distance | `clip_start = max(1e-4, d - radius*2)` |
| "Transparent" PNG has a black background | `color_mode='RGB'` | `color_mode='RGBA'` + `film_transparent=True` |
| `TypeError: ... enum "OPEN_EXR_MULTILAYER" not found` | `media_type` not set first (5.0 change) | `ims.media_type='MULTI_LAYER_IMAGE'` then `file_format` |
| Whole product blurry except one edge | `aperture_fstop` far too low | raise to 8–22, or disable DOF |
| Focus drifts during animation | used `focus_distance` on a moving subject | `dof.focus_object = subject` |
| Building/product leans backwards | camera tilted up | keep the camera level, use `shift_y` |
| Turntable: subject goes dark on some frames | rotated the camera while lights stayed fixed | rotate the object (§4.6), or parent the lights to the camera pivot |
| Turntable stutters / has a duplicate frame at the loop | last keyframe at `frames` instead of `frames + 1` | key the 360° at `frames + 1`, render 1..`frames` |
| Turntable wobbles | object origin not on the rotation axis | rotate a pivot Empty at the base centre, not the object |
| Shadow catcher renders as a grey plane | `is_shadow_catcher` set but `film_transparent=False` | enable transparent film |
| `RuntimeError: Operator bpy.ops.render.opengl.poll() failed` | no window in `--background` | use `bpy.ops.render.render()` or the MCP viewport screenshot |
| Final render came out tiny/noisy | `resolution_percentage` / `samples` left at preview values | restore them (§4.8) |
| `AttributeError: 'Scene' object has no attribute 'eevee'` after setting engine | wrong engine id — 5.0 renamed `BLENDER_EEVEE_NEXT` back to `BLENDER_EEVEE` | `scene.render.engine = 'BLENDER_EEVEE'` |
| Colours look washed out vs. a web viewer | `view_transform='AgX'` vs the viewer's neutral tonemap | `'Khronos PBR Neutral'` or `'Standard'` |

## 6. Parameter defaults by use case

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

## 7. Verification checklist

- [ ] `assert bpy.context.scene.camera is not None` — there is a camera.
- [ ] `assert shot_ready()["lights"] > 0 or shot_ready()["world_strength"] > 0` — there is light.
- [ ] `c = frame_coverage(cam, [subject]); assert c["inside"] and not c["behind_camera"]` — subject is fully in frame.
- [ ] `assert 0.55 < (c["v"][1] - c["v"][0]) < 0.95` — the subject fills a sensible fraction of the frame.
- [ ] `assert cam.data.clip_start < dist - radius and cam.data.clip_end > dist + radius` — nothing clipped.
- [ ] `assert cam.data.dof.focus_object is subject or cam.data.dof.focus_distance > 0` — focus is set deliberately.
- [ ] `assert bpy.context.scene.render.image_settings.color_mode == 'RGBA'` when `film_transparent` — alpha survives.
- [ ] `assert os.path.getsize(preview_path) > 5000` — the render actually wrote pixels.
- [ ] Load the preview and check it is not uniform: `img = bpy.data.images.load(p); px = img.pixels[:]; assert max(px) - min(px) > 0.05` — catches all-black and all-white renders numerically.
- [ ] Turntable loop: render frame 1 and frame `frames + 1` and assert the images are pixel-identical.
- [ ] After the final render, `assert bpy.context.scene.render.resolution_percentage == 100`.
- [ ] Visually (screenshot): key light readable, no blown highlights, backdrop seamless, no black facets, subject not dead-centre unless intended.

## 8. Sources

- [bpy.types.Camera — 5.2](https://docs.blender.org/api/current/bpy.types.Camera.html) (`lens`, `sensor_width`, `sensor_fit`, `angle`, `ortho_scale`, `shift_x/y`, `clip_start/end`, `type`)
- [bpy.types.CameraDOFSettings — 5.2](https://docs.blender.org/api/current/bpy.types.CameraDOFSettings.html)
- [bpy.types.Object (`camera_fit_coords`, `is_shadow_catcher`, `is_holdout`, `bound_box`, `constraints`) — 5.2](https://docs.blender.org/api/current/bpy.types.Object.html)
- [bpy.types.TrackToConstraint / FollowPathConstraint — 5.2](https://docs.blender.org/api/current/bpy.types.TrackToConstraint.html)
- [bpy_extras.object_utils.world_to_camera_view — 5.2](https://docs.blender.org/api/current/bpy_extras.object_utils.html)
- [bpy.types.RenderSettings (`film_transparent`, `resolution_*`, `frame_path`) — 5.2](https://docs.blender.org/api/current/bpy.types.RenderSettings.html)
- [bpy.types.ImageFormatSettings (`media_type`, `file_format`, `color_mode`) — 5.2](https://docs.blender.org/api/current/bpy.types.ImageFormatSettings.html)
- [bpy.ops.render (`render` with `frame_start`/`frame_end`, `opengl`) — 5.2](https://docs.blender.org/api/current/bpy.ops.render.html)
- [Cycles object settings — shadow catcher, Blender 5.2 Manual](https://docs.blender.org/manual/en/latest/render/cycles/object_settings/object_data.html)
- [Blender 5.0: Python API](https://developer.blender.org/docs/release_notes/5.0/python_api/) — `BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE`, `ImageFormatSettings.media_type`, render pass renames
- [Blender 5.1: Python API](https://developer.blender.org/docs/release_notes/5.1/python_api/) — `render.render()` frame range arguments
- [Bundled OCIO config `release/datafiles/colormanagement/config.ocio`](https://projects.blender.org/blender/blender/src/branch/main/release/datafiles/colormanagement/config.ocio) — verified view-transform and look names
- `[UNVERIFIED]` `Object.is_shadow_catcher` behaviour under EEVEE in 5.2 — Blender documents it only under Cycles; assume Cycles-only and use `is_holdout` + compositing for EEVEE.
- `[UNVERIFIED]` The focal-length recommendations, framing `fill` fractions and the DOF circle-of-confusion constant (0.029 mm) are photographic practice, not Blender documentation.
- `[UNVERIFIED]` "Rotate the object, not the camera" for turntables is a reasoned production convention; Blender documents neither approach.

---
name: mocap-retargeting
domain: animation
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Importing FBX/BVH/glTF animation, constraint-based retargeting, baking, NLA with slotted actions, root motion, loop cleanup, and shot staging.
loads_with: [rigging-armature, animation-fcurves, export-interchange]
tags: [mocap, retargeting, fbx, bvh, nla, baking, root-motion, camera, staging]
---

# Mocap, Retargeting & NLA

## 1. Mental model

Mocap data is *rotations relative to some other skeleton's rest pose*. That
sentence contains the whole problem. An FBX/BVH action stores, per frame, a
local rotation for each source bone measured against that source bone's rest
orientation. Your target rig's bones have different rest orientations (different
roll, different bone direction, different naming, often different units and
up-axis). Copying `rotation_quaternion` values across therefore produces a
scrambled pose, not a translated one — the values are correct numbers in the
wrong coordinate frame.

The reliable fix is to let Blender do the frame conversion at evaluation time:
put **Copy Rotation** constraints on the target bones pointing at the source
bones, with spaces chosen so the rest-pose difference is compensated, then
**bake** the evaluated result into a clean Action and delete the constraints.
Constraints handle the math; baking makes it editable and exportable.

Everything downstream — NLA layering, root motion, loop cleanup — operates on
that baked Action. And since 4.4, an Action is not a flat bag of F-curves: it
carries slots, and NLA strips carry an `action_slot` too. Assigning an Action to
a strip without a slot gives you a strip that plays nothing.

## 2. Decision first

| Input | Importer | Watch out for |
|---|---|---|
| `.fbx` from Mixamo / Maya / MotionBuilder | `bpy.ops.import_scene.fbx` — the **legacy Python** importer, deliberately (see note) | cm→m scale, bone axis convention, leaf bones, `use_prepost_rot` |
| `.bvh` from optical/inertial capture | `bpy.ops.import_anim.bvh` | fps mismatch, Z-up vs Y-up, huge world scale |
| `.glb` / `.gltf` from a game/web pipeline | `bpy.ops.import_scene.gltf` | `bone_heuristic`, `guess_original_bind_pose` |
| Blender-native | `bpy.ops.wm.append` / `bpy.data.libraries.load` | slot binding on append (4.4+) |

| Situation | Retarget route |
|---|---|
| Source and target are the *same* skeleton (same names, same rest) | Assign the Action directly + bind the slot. No retargeting. |
| Same proportions, different rest orientation (T-pose vs A-pose) | Copy Rotation, `owner_space='LOCAL'`, `target_space='LOCAL_OWNER_ORIENT'` |
| Different proportions, need world-space contact (feet planted) | Copy Rotation for the chain + Copy Location / IK constraints for hands & feet |
| Rest poses already identical in world space, no parent offsets | Copy Rotation, both spaces `'WORLD'` (simplest, least robust) |
| One-off, script-controlled, need full determinism | Per-frame matrix math + `pose_bone.matrix` writes + manual keying |

| Baking route | When |
|---|---|
| `bpy_extras.anim_utils.bake_action(obj, action=..., frames=..., bake_options=...)` | **Default for agents.** Pure Python, no operator context, works headless. |
| `bpy.ops.nla.bake(...)` | When you want Blender's exact UI semantics, or need `bake_types={'OBJECT'}` + parent clearing. Needs a valid context. |

## 3. Rules

R1. Never copy `rotation_quaternion`/`rotation_euler` values bone-to-bone between different rigs.
    Why: those values are relative to each bone's own rest orientation, which differs.
    Violation: the target character folds into an impossible pose on frame 1.

R2. Check and fix scale immediately after import, before anything else.
    Why: FBX/BVH from DCCs often ships in centimetres; Blender works in metres.
    Violation: a 175 cm human imports 175 m tall, IK/physics/lighting all break.

R3. Apply the import's object-level transform to the armature before retargeting.
    Why: an unapplied rotation/scale on the source object silently contaminates every world-space constraint.
    Violation: retargeted motion is rotated 90° or scaled by 100.

R4. Bind the Action slot after assigning an Action to an object *or* an NLA strip.
    Why: 4.4+ Actions hold multiple slots; the auto-assign heuristic can miss.
    Violation: strip exists with the right Action, character does not move.

R5. Bake with `do_visual_keying=True` (or `visual_keying=True` for the operator).
    Why: without it, you key the pre-constraint local values, i.e. nothing.
    Violation: baked action contains all-zero/rest keys.

R6. Remove or mute the retargeting constraints after baking.
    Why: constraints re-evaluate on top of the baked keys, doubling the motion.
    Violation: character rotates twice as far as the source.

R7. Set `scene.frame_start`/`frame_end` to the source clip's real range before baking.
    Why: `bake_action` bakes exactly the `frames` you give it; the operator defaults to 1-250.
    Violation: truncated motion, or 200 frames of held final pose.

R8. Match `scene.render.fps` to the clip's fps before baking, or bake in source frames and retime afterwards.
    Why: BVH import can rescale time (`use_fps_scale`) and produce fractional keys.
    Violation: keys land on non-integer frames; game exporters drop or round them.

R9. Run an Euler filter on baked euler rotations.
    Why: converting continuous quaternions to euler introduces ±360° discontinuities.
    Violation: limbs spin a full revolution over one frame in the render.

R10. For a loop, make the last key numerically identical to the first, then add a Cycles F-modifier.
    Why: any difference reads as a hitch every cycle.
    Violation: visible pop at the loop seam in a playblast.

R11. For locomotion loops, use `FModifierCycles.mode_after = 'REPEAT_OFFSET'` on translation channels, `'REPEAT'` on rotation.
    Why: `REPEAT` on forward translation teleports the character back to the origin each cycle.
    Violation: character moonwalks back to the start every N frames.

R12. Decide root motion policy *before* baking: extract to a root bone/object, or strip it.
    Why: game engines want root motion on a dedicated root; in-place loops want it removed.
    Violation: character slides through the floor, or animates on the spot when it should travel.

R13. Push the current Action to NLA before assigning the next one, or you lose it.
    Why: assigning `animation_data.action` replaces the previous assignment; a zero-user Action is purged on save.
    Violation: only the last imported clip survives the file round-trip.

R14. Never leave `animation_data.use_tweak_mode = True` in a headless script.
    Why: tweak mode swaps the action into `action_tweak_storage`; leaving it on corrupts the save.
    Violation: on reload the object is animated by the wrong strip, or by nothing.

## 4. bpy patterns

### 4.1 Import (5.2 signatures, all keyword-only)

> **Which FBX importer?** Blender 5.0 made `bpy.ops.wm.fbx_import` (C++) the
> default, and `export-interchange.md` recommends it for general asset import.
> For **mocap** this file deliberately keeps the legacy Python importer
> `bpy.ops.import_scene.fbx`, because the rig-specific arguments below
> (`ignore_leaf_bones`, `primary_bone_axis` / `secondary_bone_axis`,
> `automatic_bone_orientation`, `use_prepost_rot`, `bake_space_transform`) are
> what make a Mixamo/MotionBuilder skeleton usable, and the C++ importer does not
> expose the same set. Verify availability before choosing:
>
> ```python
> legacy = hasattr(bpy.ops.import_scene, "fbx")
> modern = hasattr(bpy.ops.wm, "fbx_import")
> args   = set(bpy.ops.wm.fbx_import.get_rna_type().properties.keys()) if modern else set()
> print(legacy, modern, sorted(args))
> ```
>
> If the legacy operator is ever removed, fall back to `wm.fbx_import` and fix
> scale/orientation afterwards on the armature object transform, then apply.

```python
import bpy

# --- FBX -----------------------------------------------------------------
bpy.ops.import_scene.fbx(
    filepath="/abs/path/walk.fbx",
    global_scale=1.0,              # R2: 0.01 if the file is authored in cm and
                                   #     the exporter did not write unit scale
    use_anim=True,
    anim_offset=1.0,               # first animated frame lands here
    automatic_bone_orientation=False,   # True = let Blender re-derive bone axes
    primary_bone_axis='Y',              # ignored when automatic_bone_orientation
    secondary_bone_axis='X',
    ignore_leaf_bones=True,        # drop the zero-length end-effector bones
    force_connect_children=False,
    use_prepost_rot=True,          # honour Maya/MB pre/post rotation
    use_custom_props=True,
    axis_forward='-Z', axis_up='Y',     # source axis convention
    use_manual_orientation=False,       # set True to force axis_forward/up
    bake_space_transform=False,         # True bakes the axis conversion into data
)

# --- BVH -----------------------------------------------------------------
bpy.ops.import_anim.bvh(
    filepath="/abs/path/capture.bvh",
    target='ARMATURE',             # 'ARMATURE' | 'OBJECT' (one empty per joint)
    global_scale=0.01,             # BVH is very often in cm
    frame_start=1,
    use_fps_scale=False,           # False = 1 BVH sample -> 1 Blender frame (R8)
    update_scene_fps=True,         # adopt the BVH's own frame time
    update_scene_duration=True,
    use_cyclic=False,              # add cyclic extrapolation on import
    rotate_mode='NATIVE',          # 'QUATERNION'|'NATIVE'|'XYZ'...'ZYX'
    axis_forward='-Z', axis_up='Y',
)

# --- glTF ----------------------------------------------------------------
bpy.ops.import_scene.gltf(
    filepath="/abs/path/anim.glb",
    bone_heuristic='BLENDER',      # 'BLENDER'|'TEMPERANCE'|'FORTUNE'
    guess_original_bind_pose=True,
    import_shading='NORMALS',
    disable_bone_shape=False,
)
```

Post-import hygiene (R2, R3):

```python
src = bpy.context.selected_objects[0] if bpy.context.selected_objects else None
src = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')

# Measure instead of guessing the unit scale.
h = max(b.tail_local.z for b in src.data.bones)
print("skeleton height (m):", h)          # ~1.6-1.9 for a human in metres
if h > 20:                                 # imported in cm
    src.scale = (0.01,) * 3

with bpy.context.temp_override(object=src, active_object=src,
                               selected_objects=[src],
                               selected_editable_objects=[src]):
    bpy.context.view_layer.objects.active = src
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)  # R3
```

T-pose vs A-pose: this is a **rest-pose** difference, not an animation
difference. If source and target rest poses differ (A-pose source, T-pose
target), the `'LOCAL_OWNER_ORIENT'` target space in §4.3 compensates for it
automatically. If you instead retarget in world space, you must first pose the
target into the source's rest shape and `bpy.ops.pose.armature_apply()` — a
destructive change that invalidates existing skinning, so prefer the space fix.

### 4.2 Bone name mapping

```python
# Mixamo -> your rig. Keep this data-driven; never hardcode it inline.
MAP = {
    "mixamorig:Hips":          "hips",
    "mixamorig:Spine":         "spine",
    "mixamorig:Spine1":        "chest",
    "mixamorig:Neck":          "neck",
    "mixamorig:Head":          "head",
    "mixamorig:LeftArm":       "upper_arm.L",
    "mixamorig:LeftForeArm":   "forearm.L",
    "mixamorig:LeftHand":      "hand.L",
    "mixamorig:LeftUpLeg":     "thigh.L",
    "mixamorig:LeftLeg":       "shin.L",
    "mixamorig:LeftFoot":      "foot.L",
    # ... mirror for Right
}

def validate_map(src, tgt, mapping):
    missing_s = [k for k in mapping if k not in src.pose.bones]
    missing_t = [v for v in mapping.values() if v not in tgt.pose.bones]
    assert not missing_s, f"source bones missing: {missing_s}"
    assert not missing_t, f"target bones missing: {missing_t}"
```

Some importers prefix or strip `mixamorig:`; probe rather than assume:

```python
prefix = ""
for cand in ("mixamorig:", "mixamorig1:", "mixamorig_"):
    if any(b.name.startswith(cand) for b in src.pose.bones):
        prefix = cand
        break
print("detected prefix:", repr(prefix))
```

### 4.3 Constraint-based retargeting (pure Python)

```python
def build_retarget(src, tgt, mapping, *, hips_src=None, hips_tgt=None):
    """Constrain tgt's bones to follow src's. Returns the constraints added."""
    added = []
    for s_name, t_name in mapping.items():
        pb = tgt.pose.bones[t_name]
        pb.rotation_mode = 'QUATERNION'          # avoid gimbal during retarget

        c = pb.constraints.new(type='COPY_ROTATION')
        c.name = "RETARGET_ROT"
        c.target = src
        c.subtarget = s_name
        c.owner_space = 'LOCAL'
        # 5.x: LOCAL_OWNER_ORIENT applies "a correction for the difference in
        # target and owner rest pose orientations" -- exactly the T/A-pose fix.
        c.target_space = 'LOCAL_OWNER_ORIENT'
        c.mix_mode = 'REPLACE'
        c.use_x = c.use_y = c.use_z = True
        added.append((pb, c))

    # Hips also need translation, in world space, scaled by height ratio.
    if hips_src and hips_tgt:
        pb = tgt.pose.bones[hips_tgt]
        c = pb.constraints.new(type='COPY_LOCATION')
        c.name = "RETARGET_LOC"
        c.target = src
        c.subtarget = hips_src
        c.owner_space = 'WORLD'
        c.target_space = 'WORLD'
        c.use_offset = False
        added.append((pb, c))
    return added
```

Height-ratio correction for translation, when the rigs differ in size:

```python
s_h = max(b.tail_local.z for b in src.data.bones)
t_h = max(b.tail_local.z for b in tgt.data.bones)
ratio = t_h / s_h
src.scale = (ratio,) * 3          # scale the SOURCE to the target's size,
                                  # then world-space location copying is correct
```

Foot/hand pinning: after the rotation pass, add `'COPY_LOCATION'` or `'IK'`
constraints on the target's IK controls pointing at the source's hand/foot
bones, `owner_space='WORLD'`, `target_space='WORLD'`. This removes foot sliding
caused by limb-length differences.

### 4.4 Baking

Preferred, headless-safe, no operator context:

```python
from bpy_extras import anim_utils

sc = bpy.context.scene
# R7: derive the real range from the source action instead of guessing.
src_act = src.animation_data.action
f0, f1 = (int(round(v)) for v in src_act.curve_frame_range)
sc.frame_start, sc.frame_end = f0, f1

opts = anim_utils.BakeOptions(
    only_selected=False,
    do_pose=True,
    do_object=False,
    do_visual_keying=True,      # R5 — mandatory for constraint-driven motion
    do_constraint_clear=True,   # R6 — drops constraints as it bakes
    do_parents_clear=False,
    do_clean=False,             # True removes redundant keys (lossy)
    do_location=True,
    do_rotation=True,
    do_scale=False,             # mocap should not scale bones
    do_bbone=False,
    do_custom_props=False,
)

baked = anim_utils.bake_action(
    tgt,
    action=None,                # None -> create a new Action
    frames=range(f0, f1 + 1),
    bake_options=opts,
)
baked.name = "walk_retargeted"
baked.use_fake_user = True
assert tgt.animation_data.action_slot is not None      # R4
```

Operator form (needs a valid context; equivalent semantics):

```python
with bpy.context.temp_override(object=tgt, active_object=tgt,
                               selected_objects=[tgt],
                               selected_editable_objects=[tgt],
                               selected_pose_bones=list(tgt.pose.bones)):
    bpy.context.view_layer.objects.active = tgt
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(
        frame_start=f0, frame_end=f1, step=1,
        only_selected=True,
        visual_keying=True,          # R5
        clear_constraints=True,      # R6
        clear_parents=False,
        use_current_action=False,
        clean_curves=False,
        bake_types={'POSE'},                       # or {'OBJECT'}
        channel_types={'LOCATION', 'ROTATION', 'SCALE'},   # +'BBONE', 'PROPS'
    )
    bpy.ops.object.mode_set(mode='OBJECT')
```

If you did not use `do_constraint_clear`, remove them explicitly (R6):

```python
for pb in tgt.pose.bones:
    for c in [c for c in pb.constraints if c.name.startswith("RETARGET_")]:
        pb.constraints.remove(c)
```

### 4.5 Post-bake cleanup

```python
from bpy_extras import anim_utils
cb = anim_utils.animdata_get_channelbag_for_assigned_slot(tgt.animation_data)

# Euler discontinuities (R9) — operator only, needs a Graph Editor context.
# If the rig is quaternion throughout, skip this entirely.
# bpy.ops.graph.euler_filter()   # under temp_override(area=<GRAPH_EDITOR>)

# Redundant-key removal, data-API side: drop keys that lie on the chord
# between their neighbours within `tol`.
def prune(fcu, tol=1e-4):
    kps = fcu.keyframe_points
    doomed = []
    for i in range(1, len(kps) - 1):
        a, b, c = kps[i - 1].co, kps[i].co, kps[i + 1].co
        t = (b[0] - a[0]) / (c[0] - a[0]) if c[0] != a[0] else 0.0
        if abs(a[1] + (c[1] - a[1]) * t - b[1]) <= tol:
            doomed.append(kps[i])
    for k in reversed(doomed):
        kps.remove(k, fast=True)
    fcu.update()

# Operator equivalents (graph editor context required):
#   bpy.ops.graph.clean(threshold=0.001, channels=False)
#   bpy.ops.graph.decimate(mode='ERROR', remove_error_margin=0.01)
#   bpy.ops.graph.smooth()  /  bpy.ops.graph.samples_to_keys()
```

### 4.6 Root motion

```python
from bpy_extras import anim_utils

def _flatten(fcu):                       # hold the first value for the whole curve
    v0 = fcu.keyframe_points[0].co[1]
    for k in fcu.keyframe_points:
        k.co[1] = k.handle_left[1] = k.handle_right[1] = v0
    fcu.update()

def root_motion(obj, hips="hips", root="root", *, extract=True):
    """extract=True moves hips XY travel onto `root`; False just strips it.
    Vertical bob (index 2) is always left on the hips."""
    cb = anim_utils.animdata_get_channelbag_for_assigned_slot(obj.animation_data)
    hbase, rbase = f'pose.bones["{hips}"].location', f'pose.bones["{root}"].location'
    for i in (0, 1):                     # X and Y only
        fcu = cb.fcurves.find(hbase, index=i)
        if not fcu:
            continue
        if extract:
            dst = cb.fcurves.ensure(rbase, index=i, group_name=root)
            dst.keyframe_points.clear()
            for k in fcu.keyframe_points:
                dst.keyframe_points.insert(k.co[0], k.co[1]).interpolation = k.interpolation
            dst.update()
        _flatten(fcu)
```

Which policy (R12): game engines with root-motion playback → `extract=True` to a
dedicated `root` bone at the origin. Treadmill/in-place loops, or engines that
drive locomotion from code → `extract=False`. Cinematic shots → leave hips travel intact
and do not create a root at all.

### 4.7 Loop cleanup

```python
def make_cyclic(obj, first, last, *, offset_channels=()):
    """Match last key to first, then add a Cycles modifier to every curve."""
    from bpy_extras import anim_utils
    cb = anim_utils.animdata_get_channelbag_for_assigned_slot(obj.animation_data)
    for fcu in cb.fcurves:
        kps = fcu.keyframe_points
        if len(kps) < 2:
            continue
        v_first = fcu.evaluate(first)
        # R10: force the closing key to equal the opening key.
        endk = max(kps, key=lambda k: k.co[0])
        if abs(endk.co[0] - last) < 0.5:
            key = (fcu.data_path, fcu.array_index)
            if key not in offset_channels:
                endk.co[1] = v_first
                endk.handle_left[1] = endk.handle_right[1] = v_first
        fcu.update()

        cyc = next((m for m in fcu.modifiers if m.type == 'CYCLES'), None) \
              or fcu.modifiers.new(type='CYCLES')
        # R11: travelling channels must accumulate, not reset.
        travelling = (fcu.data_path, fcu.array_index) in offset_channels
        cyc.mode_before = 'REPEAT_OFFSET' if travelling else 'REPEAT'
        cyc.mode_after  = 'REPEAT_OFFSET' if travelling else 'REPEAT'
        cyc.cycles_before = cyc.cycles_after = 0        # infinite

# Forward travel is usually hips Y (or root Y) in Blender's -Y-forward convention.
make_cyclic(tgt, 1, 32, offset_channels={('pose.bones["root"].location', 1)})

# Also mark the action's intended loop range so other tools see it.
act = tgt.animation_data.action
act.use_frame_range = True
act.frame_start, act.frame_end = 1, 32
act.use_cyclic = True          # flag only; does not itself make it loop
```

### 4.8 NLA with slotted actions

```python
ad = tgt.animation_data or tgt.animation_data_create()

# Stash the active Action into a track so it is not lost on the next assign (R13).
track = ad.nla_tracks.new()                 # NlaTracks.new(*, prev=None)
track.name = "walk"
strip = track.strips.new("walk", 1, walk_action)   # NlaStrips.new(name, start, action)

# R4: a strip needs its own slot binding. Assignment is "eager" but not certain.
if strip.action_slot is None and strip.action_suitable_slots:
    strip.action_slot = strip.action_suitable_slots[0]
assert strip.action_slot is not None, "strip has no bound slot -> plays nothing"

strip.frame_start_ui, strip.frame_end_ui = 1, 32
strip.action_frame_start, strip.action_frame_end = 1, 32
strip.blend_type = 'REPLACE'      # 'REPLACE'|'COMBINE'|'ADD'|'SUBTRACT'|'MULTIPLY'
strip.extrapolation = 'HOLD'      # 'NOTHING'|'HOLD'|'HOLD_FORWARD'
strip.blend_in, strip.blend_out = 4, 4
strip.use_auto_blend = False
strip.repeat = 4.0                # play the clip 4 times
strip.scale = 1.0                 # time scale
strip.use_sync_length = True
strip.influence = 1.0
strip.use_animated_influence = False
strip.mute = False

# Layering: additive pass on a higher track (e.g. breathing over a walk).
add_track = ad.nla_tracks.new(prev=track)
add_strip = add_track.strips.new("breathe", 1, breathe_action)
if add_strip.action_slot is None and add_strip.action_suitable_slots:
    add_strip.action_slot = add_strip.action_suitable_slots[0]
add_strip.blend_type = 'COMBINE'   # correct for rotations; ADD misbehaves on quats

# Stack-level settings
ad.use_nla = True
ad.action_blend_type = 'REPLACE'   # how the *active* Action mixes over the stack
ad.action_extrapolation = 'HOLD'
ad.action_influence = 1.0
track.is_solo = False
track.mute = False
assert ad.use_tweak_mode is False   # R14
```

How slots interact with NLA: each `NlaStrip` carries `action`, `action_slot`,
`action_slot_handle`, `action_suitable_slots` and `last_slot_identifier` — the
same quartet `AnimData` carries. One Action can therefore serve several strips
on several characters, each strip picking a different slot. Auto-assignment for
strips is *more eager* than for the main Action (any slot whose
`target_id_type` matches is chosen), but a strip whose Action has no matching
slot will bind nothing.

Pushdown / tweak-mode operators (need a NLA editor context; prefer the data API
above in headless scripts):
`bpy.ops.nla.action_pushdown(track_index=-1)`,
`bpy.ops.nla.tweakmode_enter(isolate_action=False)` / `tweakmode_exit()`,
`bpy.ops.nla.action_sync_length(active=True)`.

### 4.9 Mixamo output quirks (practical)

| Quirk | Detection | Handling |
|---|---|---|
| Bone prefix `mixamorig:` (sometimes `mixamorig1:`) | scan `pose.bones` names | probe the prefix (§4.2), do not hardcode |
| Units in centimetres | skeleton height > 20 | `global_scale=0.01` on import, or scale + apply |
| No root bone; travel lives on `Hips` | no bone named `root`/`Root` | create one and extract (§4.6) |
| Frame 1 is the bind/T-pose, motion starts at 2 | compare frame 1 to frame 2 pose | trim: bake from frame 2, then offset keys back by 1 |
| "In place" downloads still have residual hip drift | hips X/Y range > a few cm | `root_motion(..., extract=False)` (§4.6) |
| Fingers keyed even for body-only clips | many `*Hand*` fcurves | drop those channels before baking to shrink the action |
| A-pose rest, not T-pose | arms not horizontal at rest | rely on `'LOCAL_OWNER_ORIENT'` (§4.3), do not re-pose the target |
| 30 fps source into a 24 fps scene | `render.fps` != clip fps | set scene fps to 30 before baking, retime after (R8) |
| Leaf/end bones (`*_end`) | zero-length bones | `ignore_leaf_bones=True` on import |
| Every clip is a separate FBX with its own skeleton | duplicate armatures pile up | import → retarget → bake → push to NLA → delete the source armature |

### 4.10 Character camera & staging

```python
cam_data = bpy.data.cameras.new("ShotCam")
cam = bpy.data.objects.new("ShotCam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

cam_data.lens = 50.0                 # mm, on a 36 mm sensor
cam_data.sensor_width = 36.0
cam_data.dof.use_dof = True
cam_data.dof.focus_object = tgt      # or focus_distance
cam_data.dof.aperture_fstop = 2.8

# Aim at a bone and keep the aim through the shot.
c = cam.constraints.new(type='DAMPED_TRACK')
c.target = tgt
c.subtarget = "chest"
c.track_axis = 'TRACK_NEGATIVE_Z'    # cameras look down -Z
c.owner_space = 'WORLD'
c.target_space = 'WORLD'
```

Shot-size / lens table for a human figure (36 mm sensor, subject height 1.75 m):

| Shot | Focal length | Camera distance | Camera height | Reads as |
|---|---|---|---|---|
| Extreme wide / establishing | 24-28 mm | 12-25 m | 1.6 m (eye) | character in a place |
| Wide / full body | 35 mm | 5-7 m | 1.0-1.6 m | full body mechanics, best for locomotion |
| Medium (waist up) | 50 mm | 3-4 m | 1.5 m | dialogue, neutral |
| Medium close-up (chest up) | 85 mm | 2.5-3 m | 1.6 m | emotion, minimal distortion |
| Close-up (face) | 85-135 mm | 1.5-2.5 m | 1.65 m | intimacy |
| Low hero angle | 35 mm | 4 m | 0.4 m, tilt up | power/threat |
| High vulnerable angle | 50 mm | 4 m | 3.0 m, tilt down | weakness/isolation |

Staging rules an agent can encode numerically:

- **Silhouette test.** Render one frame with a white world and a pure-black
  emission override on the character. If the pose is unreadable in silhouette,
  the staging is wrong. This is a check the agent can actually run and look at.
- **Rule of thirds.** Put the head at ~0.33 from the top and on a vertical
  third: project `head` bone world position with
  `bpy_extras.object_utils.world_to_camera_view(scene, cam, v)` and assert the
  result is within ±0.06 of (0.33 or 0.67, 0.66).
- **Look room.** Leave 55-65% of the frame width on the side the character faces.
- **Screen direction.** Keep the character travelling in one horizontal
  direction across consecutive shots; crossing the 180° line without a neutral
  shot reads as a continuity error.
- **Camera easing.** Camera moves get longer eases than characters: 12-20 frames
  in, 12-20 out, `BEZIER` with `set_bezier_ease(a, b, 0.42, 0, 0.58, 1)`.
- **Never cut on the extreme.** Cut 2-4 frames after a pose settles, not on the
  frame the pose is reached.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| Character folds into a scrambled pose on frame 1 | Copied rotation values between rigs with different rest poses | Constraint-based retarget with `target_space='LOCAL_OWNER_ORIENT'` (R1, §4.3) |
| Imported skeleton is 100x too big; IK/lights/DOF all wrong | cm/m unit mismatch | `global_scale=0.01`, or scale + `transform_apply` (R2, R3) |
| Baked action contains only rest-pose keys | `do_visual_keying`/`visual_keying` left False | Enable it (R5) |
| Motion is exactly doubled | Constraints still live after baking | `do_constraint_clear=True`, or remove them manually (R6) |
| Baked action is 250 frames of a held final pose | Operator's default `frame_end=250` | Derive range from `action.curve_frame_range` (R7) |
| An arm spins 360° over one frame | Euler discontinuity from quaternion→euler | `bpy.ops.graph.euler_filter()`, or keep `rotation_mode='QUATERNION'` (R9) |
| Visible pop at the loop seam | First and last keys differ | Force last == first, then Cycles modifier (R10) |
| Character moonwalks back to the origin every cycle | `mode_after='REPEAT'` on a travelling channel | `'REPEAT_OFFSET'` on translation (R11) |
| Feet slide along the ground | Limb-length difference; rotation-only retarget | Add world-space Copy Location / IK on foot controls (§4.3) |
| NLA strip has the right Action but nothing plays | `strip.action_slot is None` | `strip.action_slot = strip.action_suitable_slots[0]` (R4) |
| Only the last imported clip exists after save/reload | Previous Actions had zero users | Push each to NLA and/or `use_fake_user = True` (R13) |
| On reload, the object is animated by the wrong strip | Script exited with `use_tweak_mode = True` | Always `ad.use_tweak_mode = False` before saving (R14) |
| `AttributeError: 'Action' object has no attribute 'fcurves'` in a mocap script | 5.0 removed the legacy Action API | Route through `anim_utils` channelbag helpers (see `animation-fcurves`) |
| `RuntimeError: Operator bpy.ops.nla.bake.poll() failed` | No active object / wrong mode in `--background` | Use `anim_utils.bake_action()` instead (§4.4) |
| Keys land on fractional frames | BVH fps rescaling | `use_fps_scale=False`, set scene fps to the source's (R8) |
| Fingers eat 60% of the action's size | Mixamo keys every finger bone | Filter `cb.fcurves` by data_path before baking (§4.9) |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Bake `step` | 1 | 1 | 2 | 2 | n/a |
| `do_clean` / `clean_curves` | True | False (keep fidelity) | True | True | n/a |
| `do_scale` in bake | False | False | True | False | n/a |
| `do_bbone` in bake | False | True (if B-bones used) | False | False | n/a |
| Rotation mode after bake | `QUATERNION` | `QUATERNION` | `XYZ` | `XYZ` | n/a |
| Root motion policy | extract to `root` | keep in hips | strip | n/a | n/a |
| Loop closure tolerance | exact (`==`) | exact | 1e-3 | n/a | n/a |
| `FModifierCycles` on export | no (bake the loop out) | yes | yes | no | n/a |
| Target fps | 30 | 24 | 60 | 25 | n/a |
| NLA usage | flatten to one action per clip | layered tracks | layered tracks | single action | n/a |
| `blend_type` for additive layers | n/a | `COMBINE` | `ADD` | n/a | n/a |
| FBX `ignore_leaf_bones` | True | True | True | True | n/a |
| FBX `automatic_bone_orientation` | False | False | False | False | n/a |
| Camera focal length | 60 (FOV-driven) | 35-85 | 24-50 | 85-135 | n/a |
| `dof.use_dof` | False | True | optional | True | n/a |

3D print is "n/a" across the board: printable output is a single static
manifold mesh; animation, NLA and cameras have no role in that pipeline.

## 7. Verification checklist

- [ ] `assert 1.4 < max(b.tail_local.z for b in src.data.bones) < 2.2` — the imported human skeleton is in metres (R2).
- [ ] `assert src.scale[:] == (1.0, 1.0, 1.0) and src.rotation_euler[:] == (0.0, 0.0, 0.0)` — import transform was applied (R3).
- [ ] `validate_map(src, tgt, MAP)` — every mapped bone exists on both rigs.
- [ ] `assert tgt.animation_data.action_slot is not None` after baking (R4).
- [ ] `assert all(len(fcu.keyframe_points) > 1 for fcu in cb.fcurves)` — the bake produced real motion, not held keys (R5).
- [ ] `assert not any(c.name.startswith("RETARGET_") for pb in tgt.pose.bones for c in pb.constraints)` — constraints cleared (R6).
- [ ] `assert tuple(int(round(v)) for v in act.curve_frame_range) == (f0, f1)` — baked range matches the source (R7).
- [ ] Loop seam: `for fcu in cb.fcurves: assert abs(fcu.evaluate(first) - fcu.evaluate(last)) < 1e-4` for non-travelling channels (R10).
- [ ] Continuity: `scene.frame_set(f)` across the clip and assert no per-frame quaternion delta exceeds ~0.5 rad — catches euler/quat pops (R9).
- [ ] Foot contact: sample `tgt.pose.bones["foot.L"].matrix` world Z over the contact frames; horizontal drift during a plant should be < 0.01 m.
- [ ] `assert tgt.animation_data.use_tweak_mode is False` before `wm.save_mainfile` (R14).
- [ ] `assert all(s.action_slot is not None for t in ad.nla_tracks for s in t.strips)` — every strip is bound (R4).
- [ ] Framing: `world_to_camera_view(scene, cam, head_world)` returns x,y in (0,1) and z > 0 — the character is actually in frame and in front of the camera.
- [ ] Render frames `[start, 25%, 50%, 75%, end]` and read the silhouettes — the only reliable staging check available to an agent.

## 8. Sources

- [bpy.ops.import_scene (5.2)](https://docs.blender.org/api/current/bpy.ops.import_scene.html) — full `fbx()` and `gltf()` signatures
- [bpy.ops.import_anim (5.2)](https://docs.blender.org/api/current/bpy.ops.import_anim.html) — full `bvh()` signature
- [bpy.ops.nla (5.2)](https://docs.blender.org/api/current/bpy.ops.nla.html) — `bake()` signature, `action_pushdown`, `tweakmode_enter/exit`, `action_sync_length`
- [bpy_extras.anim_utils](https://docs.blender.org/api/current/bpy_extras.anim_utils.html) — `bake_action`, `bake_action_objects`, `BakeOptions` field list, channelbag helpers
- [bpy.types.NlaStrip](https://docs.blender.org/api/current/bpy.types.NlaStrip.html) — `action_slot`, `action_slot_handle`, `action_suitable_slots`, `last_slot_identifier`, blending/timing properties
- [bpy.types.NlaTracks](https://docs.blender.org/api/current/bpy.types.NlaTracks.html) / [NlaStrips](https://docs.blender.org/api/current/bpy.types.NlaStrips.html) / [NlaTrack](https://docs.blender.org/api/current/bpy.types.NlaTrack.html)
- [bpy.types.AnimData](https://docs.blender.org/api/current/bpy.types.AnimData.html) — `use_nla`, `use_tweak_mode`, `action_blend_type`, `nla_tweak_strip_time_to_scene`
- [bpy.types.Constraint](https://docs.blender.org/api/current/bpy.types.Constraint.html) — `target_space` incl. the `LOCAL_OWNER_ORIENT` description used for rest-pose correction
- [bpy.types.CopyRotationConstraint](https://docs.blender.org/api/current/bpy.types.CopyRotationConstraint.html) — `mix_mode`, `euler_order`, `use_x/y/z`
- [bpy.types.FModifierCycles](https://docs.blender.org/api/current/bpy.types.FModifierCycles.html) — `mode_before/after`, `REPEAT_OFFSET`
- [bpy.ops.graph (5.2)](https://docs.blender.org/api/current/bpy.ops.graph.html) — `euler_filter`, `clean`, `decimate`, `smooth`, `samples_to_keys`
- [Slotted Actions: Upgrading to 4.4](https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/) — "NLA strips and Action Constraints have similar properties & behavior… auto-assignment is a little bit more eager"
- [Blender 5.0: Python API](https://developer.blender.org/docs/release_notes/5.0/python_api/) — legacy Action API removal that mocap scripts must account for

`[UNVERIFIED]` The Mixamo-specific quirks table in §4.9 is field knowledge, not
primary documentation — Mixamo publishes no API contract and its exporter has
changed over time. Every row is written as a *detection* plus a handling step;
run the detection rather than assuming the quirk.

`[UNVERIFIED]` The claim that `'LOCAL_OWNER_ORIENT'` is the correct
`target_space` for T-pose↔A-pose retargeting is an inference from the property's
own documented description ("followed by a correction for the difference in
target and owner rest pose orientations… produces the same global motion as the
target if the parents are still in rest pose"). It is not stated as a
retargeting recipe in the docs. Verify per rig by comparing the constrained
target pose against the source at 3-4 sampled frames before baking.

`[UNVERIFIED]` Whether `bpy.ops.graph.euler_filter()` can be driven under
`temp_override` in `--background` (there is no Graph Editor area to override
with in a headless file) was not confirmed. Prefer keeping bones in
`rotation_mode='QUATERNION'` through the bake and converting to euler only at
export, which removes the need for the filter entirely.

`[UNVERIFIED]` The lens/distance/height figures in §4.10 are standard
cinematography practice, not Blender documentation. They are starting values to
be checked against a rendered frame.

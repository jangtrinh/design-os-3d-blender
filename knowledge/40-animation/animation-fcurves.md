---
name: animation-fcurves
domain: animation
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Slotted-Action data model, F-curve/keyframe creation, interpolation & Bezier easing math, F-modifiers, drivers, and timing numbers for bpy agents.
loads_with: [rigging-armature, mocap-retargeting, scene-organization, render-engines]
tags: [animation, fcurve, keyframe, action, slot, driver, easing, timing]
---

# Animation & F-Curves (5.2 slotted Actions)

## 1. Mental model

Animation in Blender is a chain of containers, and in 4.4+ that chain got one
level longer. `ID` (Object, Material, ShapeKey...) → `id.animation_data`
(`AnimData`) → `animation_data.action` (`Action` datablock) **+**
`animation_data.action_slot` (`ActionSlot`) → `action.layers[0]` →
`layer.strips[0]` (an `ActionKeyframeStrip`) → `strip.channelbag(slot)`
(`ActionChannelbag`) → `channelbag.fcurves` → `fcurve.keyframe_points`.

Before 4.4 an Action belonged to exactly one datablock type and exposed
`action.fcurves` directly. In 4.4 that became a deprecated proxy for
`action.layers[0].strips[0].channelbag(action.slots[0])`. **In Blender 5.0 the
proxy was deleted.** `action.fcurves`, `action.groups` and `action.id_root` do
not exist in 5.x. This is the single most common way stale-training-data agents
break: they write `action.fcurves.new(...)` and get an `AttributeError`.

What you are actually deciding when you work here: (a) do you need explicit
control over curve shape, or is `keyframe_insert()` enough; (b) which *slot* of
the Action you are writing into; (c) whether motion is authored as keys or
generated procedurally by F-modifiers/drivers. Everything the agent can see is
either a traceback or a rendered frame, so prefer code that asserts its own
results (`fcurve.evaluate(f)`) over code that "looks right".

## 2. Decision first

| Goal | Route | Why |
|---|---|---|
| Key a property you can already set in Python | `obj.keyframe_insert(data_path=..., frame=...)` | Creates animdata + action + slot + layer + strip + channelbag + fcurve for you. Never touches slot plumbing. |
| Build a curve with exact handles / thousands of keys | `channelbag.fcurves.ensure(...)` + `kp.insert()` / `kp.add()` + `foreach_set("co", ...)` | 10-100x faster and fully deterministic. |
| Read an existing curve | `anim_utils.animdata_get_channelbag_for_assigned_slot(ad)` then `cb.fcurves.find(path, index=i)` | Version-safe, no slot guessing. |
| Endless / cyclic motion (spin, bob, walk loop) | `FModifierCycles` on the fcurve | No key duplication, loop length stays editable. |
| Organic jitter, camera shake, idle noise | `FModifierNoise` | Deterministic per `phase`, no keys. |
| Value derived from another value | `id.driver_add(path)` + `Driver.expression` | Rebuilds every depsgraph eval; survives retiming. |
| Same motion on many objects | One `Action` + one `ActionSlot` per object, or NLA strips | Slots are the 4.4+ mechanism for action reuse. |

Speed vs control: `keyframe_insert` is convenient but does a full RNA resolve
and dependency-graph tag per call. Above ~2000 keys, drop to the channelbag +
`foreach_set` path.

## 3. Rules

R1. Never write `action.fcurves`, `action.groups`, or `action.id_root` on a 5.x target.
    Why: the legacy Action API was removed in 5.0 (commit 1395abc502); in 4.4/4.5 it was a deprecated proxy.
    Violation: `AttributeError: 'Action' object has no attribute 'fcurves'`.

R2. Resolve the channelbag through `bpy_extras.anim_utils`, not by indexing `layers[0].strips[0]` blindly.
    Why: a freshly created Action has zero layers; `layers[0]` raises before you create one.
    Violation: `IndexError: bpy_prop_collection[index]: index 0 out of range, size 0`.

R3. After assigning `anim_data.action = act`, verify `anim_data.action_slot is not None`.
    Why: 4.4+ auto-assigns a slot by heuristic; when the heuristic fails the Action is assigned but nothing animates.
    Violation: object sits at rest pose in every rendered frame despite a populated Action.

R4. Call `fcurve.update()` (or `keyframe_points.sort()`) after direct `co`/`foreach_set` writes.
    Why: the evaluator assumes chronologically sorted points and cached handles.
    Violation: curve evaluates to garbage, keys appear out of order, viewport shows teleporting motion.

R5. Set `handle_left_type`/`handle_right_type` to `'FREE'` (or `'ALIGNED'`) *before* writing `handle_left`/`handle_right`.
    Why: `'AUTO'`/`'AUTO_CLAMPED'`/`'VECTOR'` handles are recomputed on update and your values are discarded.
    Violation: custom easing silently reverts to the default S-curve.

R6. Key rotation on the channel that matches `rotation_mode`.
    Why: keying `rotation_euler` while `rotation_mode == 'QUATERNION'` writes an fcurve that is never evaluated.
    Violation: fcurve exists, `len(keyframe_points) > 0`, object does not rotate.

R7. Use `scene.frame_set(f)` — not `scene.frame_current = f` — before reading evaluated transforms.
    Why: `frame_set()` forces a depsgraph update; the plain assignment defers it.
    Violation: `obj.matrix_world` returns the previous frame's values; baked data is off by one frame.

R8. Treat frame rate as `fps / fps_base`, never `fps` alone.
    Why: 29.97 is stored as `fps=30, fps_base=1.001`; 23.976 as `fps=24, fps_base=1.001`.
    Violation: audio/video sync drift of 1 frame per ~1000 in exported sequences.

R9. Strip the auto-created contents of a driver F-curve if you want raw pass-through.
    Why: `driver_add()` historically added a Generator F-modifier; 5.0 changed it to insert 2 keyframes instead. Either one remaps the driver result.
    Violation: driver expression is correct but the driven property clamps or scales unexpectedly.

R10. Never rely on `preferences.edit.use_keyframe_insert_available` being off.
    Why: Blender 5.2 flipped this preference to default **True** — "Only Insert Available".
    Violation: operator-driven keying (auto-key, `anim.keyframe_insert`) silently inserts nothing on properties that are not already animated.

R11. In `--background`, do not assume drivers with Python expressions will evaluate.
    Why: auto-execution of scripts is gated by `preferences.filepaths.use_scripts_auto_execute` / the `--enable-autoexec` CLI flag.
    Violation: `bpy.app.autoexec_fail == True`, driven values frozen at their last stored value, render shows an unposed rig.

R12. Give every generated Action a `use_fake_user = True` if it is not assigned to anything.
    Why: unassigned Actions are purged on save/reload.
    Violation: action disappears from `bpy.data.actions` after `bpy.ops.wm.save_mainfile()` + reload.

## 4. bpy patterns

### 4.1 Version-safe channelbag resolver (the one function to always carry)

```python
import bpy

def get_channelbag(id_block, *, create=True):
    """Return the ActionChannelbag holding id_block's F-Curves, on 4.4 -> 5.x.

    On 4.5 the legacy action.fcurves proxy still exists; on 5.x it does not.
    This routes through the slot in both cases, so it behaves identically.
    """
    ad = id_block.animation_data or (id_block.animation_data_create() if create else None)
    if ad is None:
        return None
    act = ad.action
    if act is None:
        if not create:
            return None
        act = bpy.data.actions.new(id_block.name + "Action")
        ad.action = act                       # 4.4+ tries to auto-assign a slot here

    from bpy_extras import anim_utils
    slot = ad.action_slot
    if slot is None:
        # R3: heuristic did not pick one. Prefer an existing suitable slot.
        if ad.action_suitable_slots:
            slot = ad.action_suitable_slots[0]
        elif create:
            slot = act.slots.new(id_type=id_block.id_type, name=id_block.name)
        else:
            return None
        ad.action_slot = slot

    if create:
        return anim_utils.action_ensure_channelbag_for_slot(act, slot)
    return anim_utils.action_get_channelbag_for_slot(act, slot)
```

```python
# Compat shim if you must also support 4.5 code paths that hand you a raw Action:
def fcurves_of(action, slot=None):
    if hasattr(action, "fcurves"):        # 4.4 / 4.5 legacy proxy
        return action.fcurves
    from bpy_extras import anim_utils     # 5.0+
    slot = slot or (action.slots[0] if len(action.slots) else None)
    cb = anim_utils.action_ensure_channelbag_for_slot(action, slot)
    return cb.fcurves
```

### 4.2 Route A — high level, let Blender build the plumbing

```python
obj = bpy.data.objects["Cube"]
obj.rotation_mode = 'XYZ'                  # R6: decide before keying

for frame, loc in ((1, (0, 0, 0)), (24, (0, 0, 3)), (48, (0, 0, 0))):
    obj.location = loc
    obj.keyframe_insert(data_path="location", frame=frame, group="Object Transform")

# 5.2 signature: keyframe_insert(data_path, *, index=-1, frame=None, group='',
#                                options=set(), keytype='KEYFRAME')
# 4.5: index/frame/... were already keyword-only. Positional index is NOT accepted.
assert obj.animation_data.action_slot is not None      # R3
```

Nested data paths must be keyed from the owning `ID`, not the sub-struct:

```python
arm_obj = bpy.data.objects["Rig"]
arm_obj.pose.bones["Arm_L"].keyframe_insert(data_path="rotation_quaternion", frame=1)
# equivalent, keyed from the ID:
arm_obj.keyframe_insert(data_path='pose.bones["Arm_L"].rotation_quaternion', frame=1)
```

### 4.3 Route B — low level, explicit F-curves

```python
cb = get_channelbag(obj)                                  # 4.1

# 5.x: ActionChannelbagFCurves.new(data_path, *, index=0, group_name='')
#      .ensure(...) same params, returns existing curve if present
#      NOTE 5.0 renamed the group kwarg: 4.x action_group= -> 5.x group_name=
fcu = cb.fcurves.ensure("location", index=2, group_name="Object Transform")

kp = fcu.keyframe_points.insert(frame=1.0, value=0.0)     # -> Keyframe
kp.interpolation = 'BEZIER'
kp2 = fcu.keyframe_points.insert(frame=24.0, value=3.0)
fcu.update()                                              # R4
assert abs(fcu.evaluate(24.0) - 3.0) < 1e-5
```

Bulk path for dense/baked data (fastest safe route):

```python
import math
frames = range(1, 481)
vals = [math.sin(f * 0.1) for f in frames]

fcu = cb.fcurves.ensure("location", index=0)
fcu.keyframe_points.clear()
fcu.keyframe_points.add(count=len(vals))
flat = [c for f, v in zip(frames, vals) for c in (float(f), v)]
fcu.keyframe_points.foreach_set("co", flat)               # 2 floats per key
for k in fcu.keyframe_points:
    k.interpolation = 'LINEAR'                            # enum: loop, not foreach_set
fcu.update()                                              # R4 — mandatory here
```

### 4.4 Interpolation, easing, handles

```python
# kp.interpolation: 'CONSTANT' | 'LINEAR' | 'BEZIER'
#                 | 'SINE' 'QUAD' 'CUBIC' 'QUART' 'QUINT' 'EXPO' 'CIRC'   (by strength)
#                 | 'BACK' 'BOUNCE' 'ELASTIC'                             (dynamic)
# kp.easing:        'AUTO' | 'EASE_IN' | 'EASE_OUT' | 'EASE_IN_OUT'
# kp.handle_left_type / handle_right_type:
#                   'FREE' | 'ALIGNED' | 'VECTOR' | 'AUTO' | 'AUTO_CLAMPED'
# kp.back      -> overshoot amount for 'BACK'
# kp.amplitude -> bounce boost for 'ELASTIC';  kp.period -> elastic period
# kp.type: 'KEYFRAME' 'BREAKDOWN' 'MOVING_HOLD' 'EXTREME' 'JITTER' 'GENERATED'

k0, k1 = fcu.keyframe_points[0], fcu.keyframe_points[1]
k0.interpolation = 'BACK'
k0.easing = 'EASE_OUT'
k0.back = 1.7            # classic overshoot constant
```

Explicit Bezier handles = CSS `cubic-bezier(x1,y1,x2,y2)` semantics. The segment
from key A to key B is the cubic with control points
`P0=A.co, P1=A.handle_right, P2=B.handle_left, P3=B.co`:

```python
def set_bezier_ease(a, b, x1, y1, x2, y2):
    """Shape the A->B segment like CSS cubic-bezier(x1,y1,x2,y2)."""
    a.interpolation = 'BEZIER'
    a.handle_right_type = 'FREE'          # R5: set type BEFORE the vector
    b.handle_left_type = 'FREE'
    dx = b.co[0] - a.co[0]
    dy = b.co[1] - a.co[1]
    a.handle_right = (a.co[0] + dx * x1, a.co[1] + dy * y1)
    b.handle_left  = (a.co[0] + dx * x2, a.co[1] + dy * y2)

set_bezier_ease(k0, k1, 0.25, 0.10, 0.25, 1.00)   # "ease" (slow-in, fast-out)
set_bezier_ease(k0, k1, 0.42, 0.00, 1.00, 1.00)   # "ease-in"  (slow start)
set_bezier_ease(k0, k1, 0.00, 0.00, 0.58, 1.00)   # "ease-out" (slow stop)
set_bezier_ease(k0, k1, 0.34, 1.56, 0.64, 1.00)   # overshoot / anticipation snap
fcu.update()
```

`fcu.extrapolation` is `'CONSTANT'` (default, hold endpoints) or `'LINEAR'`
(continue slope). `fcu.auto_smoothing` controls how `'AUTO'` handles are solved.

### 4.5 F-curve modifiers (procedural motion, no keys)

```python
# FModifierCycles: repeat the keyed range forever
cyc = fcu.modifiers.new(type='CYCLES')
cyc.mode_before = 'REPEAT'          # 'NONE'|'REPEAT'|'REPEAT_OFFSET'|'MIRROR'
cyc.mode_after  = 'REPEAT_OFFSET'   # REPEAT_OFFSET = walk cycles that travel forward
cyc.cycles_before = 0               # 0 = infinite
cyc.cycles_after  = 0

# FModifierNoise: shake / idle jitter
nz = fcu.modifiers.new(type='NOISE')
nz.blend_type = 'ADD'               # 'REPLACE'|'ADD'|'SUBTRACT'|'MULTIPLY'
nz.scale      = 6.0                 # frames per noise period; larger = slower
nz.strength   = 0.02                # amplitude in the curve's own units
nz.phase      = 12.0                # random seed; vary per channel to decorrelate
nz.depth      = 2                   # octaves; 0 = single octave
nz.roughness  = 0.5                 # needs depth > 0
nz.lacunarity = 2.0                 # needs depth > 0
nz.use_legacy_noise = False         # 5.x default; legacy could exceed -1..1

# Restrict a modifier to a frame window (base FModifier props):
nz.use_restricted_range = True
nz.frame_start, nz.frame_end = 1, 96
nz.blend_in, nz.blend_out = 8, 8
nz.influence = 1.0                  # nz.mute = True disables
```

Available `type` values: `GENERATOR`, `FNGENERATOR`, `ENVELOPE`, `CYCLES`,
`NOISE`, `LIMITS`, `STEPPED`, `SMOOTH` (Gaussian, added 5.1 — must be first in
the stack to work).

### 4.6 Classic principles as numbers (24 fps baseline; scale by fps/24)

| Principle | Concrete encoding |
|---|---|
| Timing — snap | 4-8 frames start→end. `BEZIER` + `EASE_OUT`. Mechanical/robotic: `LINEAR`. |
| Timing — normal | 10-14 frames. Human gesture, head turn, hand reach. |
| Timing — heavy | 20-32 frames. Large mass, camera moves, doors. |
| Spacing | Never uniform for organic motion. Put the mid-value key at ~35% of the value range at ~50% of the time for ease-out. |
| Anticipation | Counter-move of 8-20% of the main displacement, over `main_duration / 3` frames, ending 1-2 frames before the main move starts. |
| Ease in/out | `set_bezier_ease(a, b, 0.42, 0, 0.58, 1)`. Full stop = `handle_right_type='VECTOR'` on the last key to kill drift. |
| Overshoot / settle | Key past target by 5-15% at `t_end`, return to target over 4-8 frames, optional second overshoot at 2-4% over 6 frames. Or `interpolation='BACK'`, `easing='EASE_OUT'`, `back=1.7`. |
| Overlap / follow-through | Offset each child in the hierarchy by 2-4 frames from its parent. Tips of chains (hair, cloth, tails) lag 4-8 frames. |
| Arcs | Never key a limb/prop with only start+end on a straight line. Insert a mid key displaced perpendicular to the chord by 5-15% of the chord length. |
| Holds | Two identical keys with `kp.type='MOVING_HOLD'` and a tiny drift (~1-2% of range) over 8-16 frames. A dead hold (`CONSTANT`) reads as a freeze/bug. |
| Secondary action | Same curve shape, 20-40% amplitude, offset 3-6 frames. |
| Slow-in on contact | Last 3 frames before impact get `LINEAR` (no ease) so the hit reads hard. |

### 4.7 Scene time, subframes, motion blur

```python
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.frame_step = 1, 120, 1
sc.render.fps, sc.render.fps_base = 24, 1.0            # true fps = fps / fps_base
# 29.97 -> fps=30, fps_base=1.001 ; 23.976 -> fps=24, fps_base=1.001

sc.frame_set(37)                                       # R7: forces depsgraph eval
sc.frame_set(37, subframe=0.5)                         # motion-blur sub-step sampling
print(sc.frame_current, sc.frame_subframe, sc.frame_float)
sc.show_subframe = True                                # allow fractional playhead in UI

sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5                    # frames open; 0.5 = 180deg
sc.render.motion_blur_position = 'CENTER'              # 'START'|'CENTER'|'END'
```

Shutter angle → `motion_blur_shutter = angle / 360`. 180° = 0.5, 90° = 0.25,
270° = 0.75.

### 4.8 Drivers

```python
obj = bpy.data.objects["Cube"]
fcus = obj.driver_add("location", 2)      # index=-1 returns a list; here a single FCurve
fcu = fcus if not isinstance(fcus, list) else fcus[0]

# R9: neutralise whatever driver_add() pre-populated.
#   <=4.5: a Generator FModifier.  5.0+: two keyframe points.
while fcu.modifiers:
    fcu.modifiers.remove(fcu.modifiers[0])
fcu.keyframe_points.clear()               # now the driver result passes through 1:1
fcu.extrapolation = 'LINEAR'

drv = fcu.driver
drv.type = 'SCRIPTED'                     # 'AVERAGE'|'SUM'|'SCRIPTED'|'MIN'|'MAX'
drv.use_self = False

var = drv.variables.new()
var.name = "ry"
var.type = 'TRANSFORMS'                   # 'SINGLE_PROP'|'TRANSFORMS'|'ROTATION_DIFF'
                                          # |'LOC_DIFF'|'CONTEXT_PROP'
tgt = var.targets[0]
tgt.id = bpy.data.objects["Empty"]
tgt.transform_type = 'ROT_Z'              # LOC_/ROT_/SCALE_ X|Y|Z (+ROT_W, SCALE_AVG)
tgt.transform_space = 'WORLD_SPACE'       # |'TRANSFORM_SPACE'|'LOCAL_SPACE'
tgt.rotation_mode = 'AUTO'

drv.expression = "ry * 2.0"
assert drv.is_valid, drv.expression       # False after a failed evaluation
```

`SINGLE_PROP` variant (`id_type` must be set before `id`):

```python
var = drv.variables.new()
var.name = "sz"
var.type = 'SINGLE_PROP'
t = var.targets[0]
t.id_type = 'OBJECT'
t.id = bpy.data.objects["Ctrl"]
t.data_path = 'scale[2]'                  # or '["my_custom_prop"]'
t.use_fallback_value = True               # survives a broken path
t.fallback_value = 1.0
```

`drv.is_simple_expression == True` means the expression is evaluated by the
fast built-in parser (no Python interpreter, and **not** blocked by autoexec).
Only non-simple expressions need script auto-execution.

### 4.9 Headless / autoexec

```bash
blender --background scene.blend --enable-autoexec --python build_anim.py
```

```python
# Inside the script, before relying on driver results:
prefs = bpy.context.preferences
print("auto-exec allowed:", prefs.filepaths.use_scripts_auto_execute)
if bpy.app.autoexec_fail:
    raise RuntimeError("autoexec blocked: " + bpy.app.autoexec_fail_message)

# 5.2: this preference now defaults to True (R10) — check before operator keying.
print("only-insert-available:", prefs.edit.use_keyframe_insert_available)
```

Prefer `is_simple_expression`-compatible driver expressions (arithmetic,
`min`/`max`, `abs`, trig) in headless pipelines so autoexec never matters.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `AttributeError: 'Action' object has no attribute 'fcurves'` | Legacy Action API removed in 5.0 | Use `anim_utils.action_ensure_channelbag_for_slot(act, slot).fcurves` (§4.1) |
| `AttributeError: 'Action' object has no attribute 'id_root'` | Same removal; the concept moved to the slot | `action.slots[0].target_id_type` |
| `TypeError: ActionChannelbagFCurves.new(): unexpected keyword 'action_group'` | 5.0 renamed the kwarg | `group_name="..."` |
| `IndexError: bpy_prop_collection[0] ... size 0` on `action.layers[0]` | Fresh Action has no layer/strip yet | `anim_utils.action_ensure_channelbag_for_slot()`, or `layers.new("Layer")` + `strips.new(type='KEYFRAME')` |
| Action is assigned, fcurves exist, object does not move in the render | `animation_data.action_slot is None` (4.4+ heuristic missed) | `ad.action_slot = ad.action_suitable_slots[0]` (R3) |
| `TypeError: keyframe_insert(): takes 1 positional argument but 2 were given` | `index`/`frame` are keyword-only in 4.5 and 5.x | `keyframe_insert("location", frame=1)` |
| Custom `handle_left/right` values snap back to a smooth S | Handle type left at `'AUTO'`/`'AUTO_CLAMPED'` | Set `handle_*_type='FREE'` first (R5) |
| Curve evaluates to nonsense / keys visually out of order | Wrote `co` directly without re-sorting | `fcu.keyframe_points.sort()` then `fcu.update()` (R4) |
| Rotation fcurve exists with keys, object never rotates | Keyed `rotation_euler` on a `QUATERNION` bone/object (or vice versa) | Match `rotation_mode`; convert with `mathutils` before keying (R6) |
| Baked matrices are all one frame stale | Used `scene.frame_current = f` | `scene.frame_set(f)` (R7) |
| Driven property clamps at a constant instead of following the expression | 5.0 `driver_add()` leaves 2 keyframes on the driver curve; `extrapolation='CONSTANT'` clamps outside them | Clear `keyframe_points` and modifiers, set `extrapolation='LINEAR'` (R9) |
| `bpy.app.autoexec_fail == True`; drivers frozen | Headless run without `--enable-autoexec` | Add the flag, or rewrite expressions so `is_simple_expression` is True (R11) |
| Operator-based keying inserts nothing | 5.2 default `use_keyframe_insert_available = True` | Key an initial value with `keyframe_insert()` first, or flip the preference (R10) |
| Generated Action gone after save/reload | Zero users | `action.use_fake_user = True` (R12) |
| Exported video drifts out of sync | Used `render.fps` and ignored `fps_base` | true fps = `fps / fps_base` (R8) |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| `render.fps` / `fps_base` | 30 / 1.0 | 24 / 1.0 | 60 / 1.0 | 25 / 1.0 | n/a |
| Default `kp.interpolation` | `LINEAR` (baked) | `BEZIER` | `BEZIER` + `SINE`/`QUAD` easing | `BEZIER` | n/a |
| Default handle type | `VECTOR` | `AUTO_CLAMPED` | `FREE` (authored) | `AUTO_CLAMPED` | n/a |
| Key density | every frame (baked) | 1 key / 4-8 frames | 1 key / 6-12 frames | 1 key / 12-24 frames | n/a |
| Typical move duration (frames) | 6-10 | 10-16 | 12-20 | 60-180 (turntable per quarter) | n/a |
| Anticipation length | 0 (cost) | 3-6 | 2-4 | 0 | n/a |
| Overshoot amount | 0 | 5-12% | 10-20% | 0-3% | n/a |
| Follow-through offset | 0-2 frames | 2-4 frames | 1-3 frames | 0 | n/a |
| `motion_blur_shutter` | 0 (off) | 0.5 | 0.25-0.5 | 0.5 | n/a |
| `motion_blur_position` | n/a | `CENTER` | `CENTER` | `CENTER` | n/a |
| `FModifierNoise.scale` / `strength` | 8 / 0.01 | 10 / 0.015 | 4 / 0.05 | 20 / 0.003 | n/a |
| `FModifierCycles.mode_after` | `REPEAT` | `REPEAT_OFFSET` (locomotion) | `REPEAT` | `REPEAT` | n/a |
| `fcurve.extrapolation` | `CONSTANT` | `CONSTANT` | `CONSTANT` | `CONSTANT` | n/a |
| `scene.frame_step` | 1 | 1 | 1 | 1 | n/a |

## 7. Verification checklist

- [ ] `assert not hasattr(bpy.types.Action, "fcurves") or bpy.app.version < (5, 0)` — confirms which API surface you are on.
- [ ] `assert obj.animation_data.action_slot is not None` — the slot is bound, so the Action actually drives this ID (R3).
- [ ] `cb = anim_utils.animdata_get_channelbag_for_assigned_slot(obj.animation_data); assert cb and len(cb.fcurves) == expected_n` — the curves landed in the slot you think.
- [ ] `assert abs(fcu.evaluate(target_frame) - target_value) < 1e-4` — the curve really passes through the key.
- [ ] `assert list(fcu.range()) == [first_frame, last_frame]` — timing extent is what you planned.
- [ ] `fr = [k.co[0] for k in fcu.keyframe_points]; assert fr == sorted(fr)` — keys are chronologically sorted (R4).
- [ ] `assert fcu.keyframe_points[0].handle_right_type == 'FREE'` — custom easing will survive (R5).
- [ ] `assert not fcu.is_empty` — the curve contributes animation.
- [ ] `assert obj.animation_data.drivers[0].driver.is_valid` — driver expression evaluated without error.
- [ ] `assert not bpy.app.autoexec_fail, bpy.app.autoexec_fail_message` — headless drivers/scripts were permitted (R11).
- [ ] Sample the motion: `for f in range(s, e, 4): scene.frame_set(f); print(f, obj.matrix_world.translation[:])` — spacing should be non-uniform for eased motion; equal deltas mean your easing did not apply.
- [ ] Viewport screenshot at three frames (start / mid / end) — mid frame must not be the arithmetic mean of start and end for an eased channel.

## 8. Sources

- [bpy.types.Action (5.2)](https://docs.blender.org/api/current/bpy.types.Action.html) — confirms `slots`, `layers`, `fcurve_ensure_for_datablock`, `is_action_legacy`; **no** `fcurves`/`groups`/`id_root`.
- [bpy.types.ActionSlot / ActionSlots](https://docs.blender.org/api/current/bpy.types.ActionSlot.html)
- [bpy.types.ActionKeyframeStrip](https://docs.blender.org/api/current/bpy.types.ActionKeyframeStrip.html) — `channelbag(slot, *, ensure=False)`, `key_insert()`
- [bpy.types.ActionChannelbagFCurves](https://docs.blender.org/api/current/bpy.types.ActionChannelbagFCurves.html) — `new/ensure/find/remove/clear`, `group_name` kwarg
- [bpy.types.AnimData](https://docs.blender.org/api/current/bpy.types.AnimData.html) — `action_slot`, `action_slot_handle`, `action_suitable_slots`
- [bpy_extras.anim_utils](https://docs.blender.org/api/current/bpy_extras.anim_utils.html)
- [bpy.types.FCurve](https://docs.blender.org/api/current/bpy.types.FCurve.html) / [Keyframe](https://docs.blender.org/api/current/bpy.types.Keyframe.html) / [FCurveKeyframePoints](https://docs.blender.org/api/current/bpy.types.FCurveKeyframePoints.html)
- [FModifierCycles](https://docs.blender.org/api/current/bpy.types.FModifierCycles.html) / [FModifierNoise](https://docs.blender.org/api/current/bpy.types.FModifierNoise.html) / [Fmodifier Type Items](https://docs.blender.org/api/current/bpy_types_enum_items/fmodifier_type_items.html)
- [Driver](https://docs.blender.org/api/current/bpy.types.Driver.html) / [DriverVariable](https://docs.blender.org/api/current/bpy.types.DriverVariable.html) / [DriverTarget](https://docs.blender.org/api/current/bpy.types.DriverTarget.html)
- [Blender 5.0: Python API — Animation & Rigging](https://developer.blender.org/docs/release_notes/5.0/python_api/) — legacy Action API removal, `group_name` rename, `anim_utils` helpers
- [Slotted Actions: Upgrading to 4.4](https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/)
- [Blender 5.0: Animation & Rigging](https://developer.blender.org/docs/release_notes/5.0/animation_rigging/) — "driver created via Python now creates 2 keyframes"
- [Blender 5.2 LTS: Animation & Rigging](https://developer.blender.org/docs/release_notes/5.2/animation_rigging/) — "Only Insert Available" now on by default
- [PreferencesEdit](https://docs.blender.org/api/current/bpy.types.PreferencesEdit.html) — `use_keyframe_insert_available` default True in 5.2
- [bpy.app](https://docs.blender.org/api/current/bpy.app.html) — `autoexec_fail`, `autoexec_fail_message`

`[UNVERIFIED]` The exact coordinates/extrapolation of the two keyframes that
5.0+ `driver_add()` inserts are not documented; the release note only states
that 2 keyframes are created instead of an F-modifier. Introspect with
`len(fcu.keyframe_points)`, `[k.co[:] for k in fcu.keyframe_points]`,
`fcu.extrapolation` before relying on pass-through behaviour.

`[UNVERIFIED]` Whether `bpy_struct.keyframe_insert()` (the RNA function, as
opposed to the keying *operators*) consults
`preferences.edit.use_keyframe_insert_available` is not stated in the API docs.
The function takes an explicit `options` set; assume it does **not** read the
preference, but assert the resulting key count rather than trusting either way.

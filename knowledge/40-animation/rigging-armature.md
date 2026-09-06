---
name: rigging-armature
domain: rigging
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Armature data model (edit_bones vs bones vs pose_bones), headless edit-mode patterns, bone collections, constraints, IK/FK, and skinning limits for bpy agents.
loads_with: [animation-fcurves, mocap-retargeting, modeling-topology]
tags: [rigging, armature, bones, ik, constraints, skinning, vertex-groups, rigify]
---

# Armatures & Rigging

## 1. Mental model

A rig is two datablocks glued together. `bpy.data.armatures[...]` is the
*skeleton definition* (bone names, rest positions, hierarchy, collections).
`bpy.data.objects[...]` with `obj.type == 'ARMATURE'` is the *instance* — it
owns the pose (`obj.pose.bones`), the constraints and the animation data. Two
objects can share one armature datablock and hold different poses.

The same bone is exposed through three different Python types, and picking the
wrong one is by far the largest source of agent errors:

- `armature.edit_bones` → `EditBone`. **Only exists while the object is in Edit
  Mode.** This is the only place you can create bones, move `head`/`tail`, set
  `roll`, or change parenting. Outside Edit Mode the collection is empty and
  any `EditBone` reference you kept is a dangling pointer that can crash Blender.
- `armature.bones` → `Bone`. Rest-pose data in Object/Pose mode. `head`/`tail`
  are **read-only** here. Good for `matrix_local`, `use_deform`, hierarchy reads.
- `object.pose.bones` → `PoseBone`. The animatable state: `location`,
  `rotation_quaternion`, `scale`, `constraints`, IK settings, custom shapes.
  Note it hangs off the **object**, not the armature data.

Blender 5.0 moved bone *selection* and *visibility* for Object/Pose mode onto
the `PoseBone`, and removed `Bone.select`. That is a hard break for any code
carried over from 4.x.

## 2. Decision first

| Task | Where | Mode required |
|---|---|---|
| Create / delete a bone | `armature.edit_bones.new(name)` / `.remove(eb)` | EDIT |
| Set head, tail, roll, length | `EditBone.head/.tail/.roll` | EDIT |
| Parent, connect, inherit-scale | `EditBone.parent`, `.use_connect`, `.inherit_scale` | EDIT |
| Rename a bone | `EditBone.name` or `Bone.name` | any (Bone works in OBJECT) |
| `use_deform`, envelope radii | `Bone.use_deform` (also on `EditBone`) | any |
| Bone collections (membership) | `armature.collections[...].assign(bone)` | any (`bone` may be Bone/EditBone/PoseBone) |
| Read collection membership | `BoneCollection.bones` | **not** EDIT (empty in edit mode) |
| Add a constraint | `pose_bone.constraints.new(type)` | any |
| Pose a bone | `pose_bone.matrix_basis` / `.location` / `.rotation_*` | any (POSE for operators) |
| Custom widget shape | `pose_bone.custom_shape = obj` | any |
| Select bones for an operator | `pose_bone.select` (5.x) / `edit_bone.select` | POSE / EDIT |
| Automatic weights | `bpy.ops.object.parent_set(type='ARMATURE_AUTO')` | OBJECT, operator-only |
| Weight values | `mesh_obj.vertex_groups[...].add([i], w, 'REPLACE')` | OBJECT |

Rule of thumb: **do all topology in one Edit-Mode block, exit, then do all
constraints/poses in Object or Pose mode.** Never interleave.

## 3. Rules

R1. Enter Edit Mode before touching `armature.edit_bones`; exit before doing anything else.
    Why: `edit_bones` is a runtime-only mirror built on entering Edit Mode and flushed on exit.
    Violation: the collection is empty (`len(arm.edit_bones) == 0`) or `bpy.ops` reports `{'CANCELLED'}`.

R2. Never keep an `EditBone` (or a Vector taken from one) across a mode switch.
    Why: the underlying C struct is freed on exit; the Python wrapper is left dangling.
    Violation: segfault, or `ReferenceError: StructRNA of type EditBone has been removed`.

R3. Set `bpy.context.view_layer.objects.active` **and** link the object into the view layer before `mode_set`.
    Why: `object.mode_set` polls `context.object`; in `--background` there is no UI to supply one.
    Violation: `RuntimeError: Operator bpy.ops.object.mode_set.poll() failed, context is incorrect`.

R4. A bone with zero length cannot exist.
    Why: Blender deletes bones whose `head == tail` when leaving Edit Mode.
    Violation: bone silently missing from `armature.bones` after exiting Edit Mode.

R5. Set `use_connect` only after `parent`, and only when the child head equals the parent tail.
    Why: connecting snaps the child head onto the parent tail, destroying your position.
    Violation: bones visibly collapse onto their parents in a viewport screenshot.

R6. Use `pose_bone.select` / `pose_bone.hide` on 5.x, not `bone.select` / `bone.hide`.
    Why: 5.0 removed `Bone.select`/`select_head`/`select_tail`, and repurposed `Bone.hide` to mean *edit-bone* visibility.
    Violation: `AttributeError: 'Bone' object has no attribute 'select'`; or bones hide in Edit Mode instead of Pose Mode.

R7. Set `pose_bone.rotation_mode` before writing rotation, and write the matching channel.
    Why: only the channel matching `rotation_mode` is evaluated. Default is `'QUATERNION'`.
    Violation: `rotation_euler` set and keyed, bone does not move.

R8. Bone collections replaced bone layers in 4.0 — `bone.layers` / `armature.layers` do not exist.
    Why: removed in the 4.0 Animation & Rigging rewrite.
    Violation: `AttributeError: 'Bone' object has no attribute 'layers'`.

R9. Read `BoneCollection.bones` outside Edit Mode.
    Why: the docs state membership is only synchronised on exiting Edit Mode; in Edit Mode the list is always empty.
    Violation: your membership assertion returns 0 and you "fix" a non-bug.

R10. Set `owner_space` / `target_space` explicitly on every bone constraint.
    Why: the default is `'WORLD'` for both, which is almost never what you want between two bones of different rigs.
    Violation: the constrained bone flies off by the armature object's transform.

R11. Set the IK constraint's `chain_count` explicitly.
    Why: default `0` means "use all bones up the hierarchy to the root", so an arm IK will drag the spine.
    Violation: whole-body wobble when the IK target moves.

R12. Put the pole target on a bone/empty that is off the chain plane, and tune `pole_angle`.
    Why: the pole defines the chain's plane; a collinear pole is undefined.
    Violation: knee/elbow snaps or flips 180° partway through a motion.

R13. Add an `ARMATURE` modifier (or use `parent_set(type='ARMATURE*')`) — vertex groups alone deform nothing.
    Why: vertex groups are just named weight maps; the modifier is what reads them.
    Violation: rig poses, mesh stays rigid.

R14. Normalise weights after programmatic weight assignment.
    Why: per-vertex weight sums != 1.0 cause shrinking/blow-up under deformation.
    Violation: mesh visibly shrinks near joints in a render.

R15. STOP and hand off to a human for: weight-painting fine-tuning around joints, facial rigs, corrective shape keys, and any "make it look good" deformation pass.
    Why: these are judged perceptually on silhouette and volume; there is no assertion an agent can write for them.
    Violation: hours of iteration producing candy-wrapper elbows the agent cannot detect from a screenshot.

## 4. bpy patterns

### 4.1 Headless-safe Edit Mode (verified behaviour: `--background` works)

Edit Mode is fully available in background mode. `armature.edit_bones` is
populated exactly when `armature.is_editmode` is True. What background mode
lacks is a UI context for the operator poll — supply it yourself.

```python
import bpy
from contextlib import contextmanager

@contextmanager
def edit_armature(arm_obj):
    """Enter Edit Mode on arm_obj, yield its edit_bones, restore previous mode.

    Safe under `blender --background`. Uses temp_override so the caller's
    selection/active-object state is not permanently clobbered.
    """
    assert arm_obj.type == 'ARMATURE', arm_obj.type
    view_layer = bpy.context.view_layer
    # R3: the object must be reachable from the view layer for the poll to pass.
    # MEASURED 5.2.0: immediately after `scene.collection.objects.link(o)` the name is
    # still absent from `view_layer.objects` -- the view layer is stale until the
    # depsgraph updates. Linking again on that stale reading raises
    # "RuntimeError: Object 'Rig' already in collection 'Scene Collection'".
    # So: refresh first, and only link if it is genuinely not linked.
    if arm_obj.name not in view_layer.objects:
        view_layer.update()
    if arm_obj.name not in view_layer.objects:
        bpy.context.scene.collection.objects.link(arm_obj)
        view_layer.update()

    prev_active = view_layer.objects.active
    prev_mode = arm_obj.mode
    with bpy.context.temp_override(object=arm_obj, active_object=arm_obj,
                                   selected_objects=[arm_obj],
                                   selected_editable_objects=[arm_obj]):
        view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        assert arm_obj.data.is_editmode                    # verify, don't assume
        try:
            yield arm_obj.data.edit_bones
        finally:
            bpy.ops.object.mode_set(mode=prev_mode if prev_mode != 'EDIT' else 'OBJECT')
    view_layer.objects.active = prev_active
```

`temp_override` is **not** strictly required if you set
`view_layer.objects.active` yourself — `bpy.context.object` resolves from the
view layer even headless. It is included because it is the only way to leave
the caller's selection untouched, which matters when a pipeline script runs
many rig steps in sequence.

There is no data-API replacement for `mode_set`; mode is a UI/operator concept.
This is one of the legitimate `bpy.ops` cases.

Verified 2026-09-06 on 5.2.0 (`--factory-startup -b`): the §4.2 sequence below, run
top-to-bottom straight after this context manager, builds all 5 bones and returns to
Object Mode (`arm.is_editmode == False`). It works both when the caller has already
linked the armature (the §4.2 case) and when it has not.

### 4.2 Building a skeleton

```python
from mathutils import Vector

arm_data = bpy.data.armatures.new("RigArm")
arm_obj = bpy.data.objects.new("Rig", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)

CHAIN = [                      # (name, head, tail)
    ("spine",     (0, 0, 1.0), (0, 0, 1.4)),
    ("chest",     (0, 0, 1.4), (0, 0, 1.7)),
    ("upper_arm.L", (0.1, 0, 1.65), (0.45, 0, 1.62)),
    ("forearm.L",   (0.45, 0, 1.62), (0.78, 0, 1.60)),
    ("hand.L",      (0.78, 0, 1.60), (0.92, 0, 1.60)),
]

with edit_armature(arm_obj) as ebs:
    made = {}
    for name, head, tail in CHAIN:
        eb = ebs.new(name)                 # ArmatureEditBones.new(name)
        eb.head = Vector(head)
        eb.tail = Vector(tail)             # R4: must differ from head
        eb.use_deform = True
        made[name] = eb

    # R5: parent first, then decide connectivity.
    made["chest"].parent = made["spine"];        made["chest"].use_connect = True
    made["upper_arm.L"].parent = made["chest"];  made["upper_arm.L"].use_connect = False
    made["forearm.L"].parent = made["upper_arm.L"]; made["forearm.L"].use_connect = True
    made["hand.L"].parent = made["forearm.L"];      made["hand.L"].use_connect = True

    # Roll: the bone's twist about its own Y axis. Two ways.
    made["forearm.L"].roll = 0.0
    made["forearm.L"].align_roll(Vector((0, 0, 1)))   # point bone Z at world +Z
    # Whole-bone placement from a matrix (location + direction + roll, no length):
    # eb.matrix = some_4x4
    # eb.transform(matrix, scale=True, roll=True)

    made["forearm.L"].inherit_scale = 'FULL'   # 'FULL'|'FIX_SHEAR'|'ALIGNED'|
                                               # 'AVERAGE'|'NONE'|'NONE_LEGACY'
```

Operator alternative when you want Blender's own roll solver across a selection:
`bpy.ops.armature.calculate_roll(type='POS_X', axis_flip=False, axis_only=False)`
(Edit Mode; `type` also accepts `GLOBAL_POS_Z`, `ACTIVE`, `VIEW`, `CURSOR`, ...).

### 4.3 Bone collections (replaced bone layers in 4.0)

```python
arm = arm_obj.data
# BoneCollections.new(name, *, parent=None) -> hierarchical since 4.1
grp_deform = arm.collections.new("DEF")
grp_ctrl   = arm.collections.new("CTRL")
grp_ik     = arm.collections.new("IK", parent=grp_ctrl)

# assign()/unassign() accept Bone, EditBone or PoseBone.
grp_deform.assign(arm.bones["forearm.L"])
grp_ik.assign(arm_obj.pose.bones["hand_ik.L"])

grp_deform.is_visible = False       # hide the deform layer
grp_ctrl.is_solo = False            # solo overrides visibility of everything else
print(arm.collections.active_name, arm.collections.is_solo_active)

# arm.collections      -> root-level collections
# arm.collections_all  -> flat list of every collection incl. children
# R9: read membership OUTSIDE edit mode
assert arm_obj.data.is_editmode is False
print([b.name for b in grp_deform.bones])
print(grp_deform.bones_recursive)   # incl. child collections
```

### 4.4 Pose bones: shapes, locks, limits

```python
pb = arm_obj.pose.bones["hand_ik.L"]
pb.rotation_mode = 'QUATERNION'          # R7 — set before writing rotation

# Custom widget: any mesh object, usually kept out of the render collection.
pb.custom_shape = bpy.data.objects["WGT_cube"]
pb.custom_shape_scale_xyz = (1.2, 1.2, 1.2)
pb.custom_shape_translation = (0.0, 0.0, 0.0)
pb.custom_shape_rotation_euler = (0.0, 0.0, 0.0)
pb.custom_shape_wire_width = 2.0
pb.use_custom_shape_bone_size = True      # scale widget by bone length
pb.custom_shape_transform = None          # drive the widget from another bone

pb.lock_location = (False, False, False)
pb.lock_rotation = (False, False, False)
pb.lock_scale    = (True, True, True)

# 5.x: selection/visibility live on the PoseBone (R6)
pb.select = True
pb.hide = False
```

### 4.5 Constraints

```python
def add(pb, ctype, target, subtarget="", *, owner='LOCAL', tgt='LOCAL'):
    c = pb.constraints.new(type=ctype)     # PoseBoneConstraints.new(type)
    c.target = target
    if subtarget:
        c.subtarget = subtarget            # bone name on the target armature
    c.owner_space = owner                  # R10 — never leave at default 'WORLD'
    c.target_space = tgt
    return c
```

Spaces (both enums): `'WORLD'`, `'CUSTOM'`, `'POSE'`, `'LOCAL_WITH_PARENT'`,
`'LOCAL'`; `target_space` additionally has `'LOCAL_OWNER_ORIENT'` (5.x: the
correct choice for cross-rig rotation copying, see `mocap-retargeting`).
`'CUSTOM'` requires `c.space_object` and optionally `c.space_subtarget`.

Common types (`Constraint Type Items`):

| Type string | Use it for | Key properties |
|---|---|---|
| `'COPY_TRANSFORMS'` | Full slave of another bone | `mix_mode`, `head_tail` |
| `'COPY_ROTATION'` | Retargeting, twist bones | `use_x/y/z`, `invert_x/y/z`, `mix_mode` (`REPLACE`/`ADD`/`BEFORE`/`AFTER`/`OFFSET`), `euler_order` |
| `'COPY_LOCATION'` | Root motion, pinning | `use_x/y/z`, `use_offset`, `head_tail` |
| `'DAMPED_TRACK'` | Aim with shortest rotation (eyes, guns) | `track_axis` (`TRACK_X`…`TRACK_NEGATIVE_Z`), `head_tail` |
| `'TRACK_TO'` | Aim with an explicit up axis | `track_axis`, `up_axis` |
| `'CHILD_OF'` | Swappable parenting (prop pickup) | `use_location_x/y/z`, `use_rotation_*`, `use_scale_*`, `inverse_matrix` |
| `'LIMIT_ROTATION'` | Joint ranges | `use_limit_x/y/z`, `min_x`/`max_x` (radians), `euler_order` |
| `'STRETCH_TO'` | Squash-stretch / rubber limbs | `rest_length`, `bulge`, `volume`, `keep_axis` |
| `'IK'` | Inverse kinematics | see 4.6 |
| `'ACTION'` | Pose driven by another bone's transform | `action`, `action_slot` (4.4+), `transform_channel` |
| `'GEOMETRY_ATTRIBUTE'` | 5.0+: read vector/quat/matrix attributes off geometry | — |

Base props on every constraint: `name`, `influence` (0..1), `mute`, `enabled`,
`is_valid`, `error_location`, `error_rotation`, `active`.
`CHILD_OF` needs its inverse matrix set or the bone jumps; there is no data-API
setter, use `bpy.ops.constraint.childof_set_inverse(constraint=c.name,
owner='BONE')` under a `temp_override` with the right active pose bone.

### 4.6 IK vs FK

FK = you rotate each bone in the chain, children inherit. It is just
`pose_bone.rotation_*`, nothing special. Arcs are free; end-effector contact is
hard.

IK = you place a target and Blender solves the chain. Contact (feet on floor,
hand on prop) is free; arcs must be authored into the target's path.

```python
pb = arm_obj.pose.bones["forearm.L"]      # constraint goes on the LAST bone of the chain
ik = pb.constraints.new(type='IK')
ik.target = arm_obj
ik.subtarget = "hand_ik.L"
ik.chain_count = 2                        # R11: forearm + upper_arm only
ik.pole_target = arm_obj
ik.pole_subtarget = "elbow_pole.L"
ik.pole_angle = -1.5708                   # radians; -90deg is a common start (R12)
ik.use_tail = True
ik.use_stretch = False
ik.use_rotation = False                   # chain follows target rotation too
ik.use_location = True
ik.iterations = 500
ik.influence = 1.0                        # animate this for IK/FK blending

# Per-bone solver limits (on the PoseBone, not the constraint):
mid = arm_obj.pose.bones["forearm.L"]
mid.lock_ik_x, mid.lock_ik_y, mid.lock_ik_z = False, True, True   # hinge on X
mid.use_ik_limit_x = True
mid.ik_min_x, mid.ik_max_x = 0.0, 2.6     # radians (0..150deg elbow)
mid.ik_stiffness_x = 0.0                  # 0..1, resistance
mid.ik_stretch = 0.0                      # 0..1, allow scaling
assert mid.is_in_ik_chain                 # sanity check the chain actually formed
```

Chain-length cheat sheet: arm 2 (upper_arm + forearm), leg 2 (thigh + shin),
leg with foot roll 3, spine 3-4, tail/tentacle 4-8 (raise `iterations`).

### 4.7 Skinning

Automatic weights is **operator-only** — there is no `bpy.data` equivalent:

```python
mesh_obj, arm_obj = bpy.data.objects["Body"], bpy.data.objects["Rig"]
vl = bpy.context.view_layer
with bpy.context.temp_override(object=arm_obj, active_object=arm_obj,
                               selected_objects=[mesh_obj, arm_obj],
                               selected_editable_objects=[mesh_obj, arm_obj]):
    vl.objects.active = arm_obj                     # parent must be active
    mesh_obj.select_set(True); arm_obj.select_set(True)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')  # heat-map weights
# types: 'ARMATURE' (empty groups) | 'ARMATURE_NAME' (by name)
#        'ARMATURE_AUTO' (heat map) | 'ARMATURE_ENVELOPE'
assert any(m.type == 'ARMATURE' for m in mesh_obj.modifiers)   # R13
```

Explicit weights through the data API (deterministic, no operator context):

```python
vg = mesh_obj.vertex_groups.get("forearm.L") or mesh_obj.vertex_groups.new(name="forearm.L")
vg.add([12, 13, 14], 1.0, 'REPLACE')     # index list, weight 0..1, REPLACE|ADD|SUBTRACT
vg.add([15], 0.35, 'REPLACE')
print(vg.weight(12))                      # raises RuntimeError if vertex not in group
vg.remove([14])
vg.lock_weight = False

mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True
mod.use_bone_envelopes = False
mod.use_deform_preserve_volume = False    # quaternion (dual-quat) skinning
```

Weight hygiene (R14) — these are operator-only:

```python
with bpy.context.temp_override(object=mesh_obj, active_object=mesh_obj,
                               selected_objects=[mesh_obj]):
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # game budget
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.005, keep_single=True)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
```

### 4.8 Rest pose changes after skinning

```python
# Apply the current pose as the new rest pose (Pose Mode operator).
with bpy.context.temp_override(object=arm_obj, active_object=arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
# WARNING: this invalidates every existing action's rest-relative values and any
# bound mesh's bind pose. Only do this before skinning, or re-bind afterwards.
```

### 4.9 Rigify

Rigify is a bundled add-on that turns a *metarig* (a plain armature whose bones
carry `rigify_type` properties) into a full generated control rig: IK/FK
switching, pole targets, custom widgets, bone collections, a rig UI panel, and
`DEF-`/`ORG-`/`MCH-` bone layers.

When an agent should invoke it: the target is a humanoid/quadruped biped-ish
character and the user wants a *production* rig. When it should not: simple
props, mechanical rigs, or anything where you plan to hand-author constraints —
Rigify's output is machine-generated and hostile to manual editing.

**Do not half-use Rigify.** Either generate the whole rig from a metarig and
then only animate its controls, or write your own bones. Adding Rigify bones to
a hand-made armature, or editing `DEF-`/`MCH-` bones of a generated rig, breaks
regeneration and produces a rig no human can maintain.

```python
import addon_utils
# Detect rather than assume the module path — it differs between bundled add-on
# and extension packaging across 4.x/5.x.
mods = [m.__name__ for m in addon_utils.modules() if "rigify" in m.__name__.lower()]
print(mods)                       # e.g. ['rigify'] or a 'bl_ext.*.rigify' path
for name in mods:
    addon_utils.enable(name, default_set=True, persistent=True)

# Operators are only present once the add-on is enabled — probe, don't guess:
print(hasattr(bpy.ops.object, "armature_human_metarig_add"))   # add a human metarig
print(hasattr(bpy.ops.pose, "rigify_generate"))                # generate the rig
```

### 4.10 Where the agent must stop (R15)

Hand off to a human for:

- **Weight painting fine-tuning.** Shoulders, hips, wrists, and any area where
  the correct answer is "the silhouette holds up at 90° of bend". Automatic
  weights + normalize + limit-total is the agent's ceiling.
- **Facial rigs.** Shape-key driven or bone driven, they are authored against a
  performance target and an artist's eye.
- **Corrective shape keys / PSD.** Requires posing to extremes and sculpting.
- **Secondary deformation** (muscle bulges, jiggle tuning, cloth pinning).
- **Any request phrased as "make the deformation look better".**

The agent *can* still deliver: skeleton topology, naming conventions, bone
collections, constraint networks, IK setups, widget assignment, weight
normalization, and automated validation of all of the above.

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `len(arm.edit_bones) == 0` right after creating bones | Not in Edit Mode, or already exited | Wrap in `edit_armature()`; assert `arm.is_editmode` (R1) |
| `ReferenceError: StructRNA of type EditBone has been removed` | Held an `EditBone` across a mode switch | Re-fetch by name after re-entering Edit Mode (R2) |
| `RuntimeError: Operator bpy.ops.object.mode_set.poll() failed, context is incorrect` | No active object in `--background` | Link into the view layer + set `view_layer.objects.active` (R3) |
| Bone missing from `armature.bones` after exiting Edit Mode | `head == tail` | Give the bone non-zero length (R4) |
| Bones visually collapse onto their parents | `use_connect = True` with mismatched head/tail | Set `parent` first, only connect when positions match (R5) |
| `AttributeError: 'Bone' object has no attribute 'select'` | 5.0 removed it | `pose.bones[n].select` (Pose) or `edit_bones[n].select` (Edit) (R6) |
| Bones hide in Edit Mode when you meant Pose Mode | 5.0 repurposed `Bone.hide` | `object.pose.bones[n].hide` (R6) |
| `AttributeError: 'Bone' object has no attribute 'layers'` | Bone layers removed in 4.0 | `armature.collections` / `BoneCollection.assign()` (R8) |
| `len(collection.bones) == 0` for a collection you just filled | Read it while in Edit Mode | Exit Edit Mode first (R9) |
| Constrained bone flies off by the rig's world transform | `owner_space`/`target_space` left at `'WORLD'` | Set both explicitly (R10) |
| Whole spine wobbles when the hand IK target moves | `chain_count == 0` (unlimited) | Set `chain_count` to the real chain length (R11) |
| Knee/elbow flips 180° mid-motion | Pole collinear with the chain, or wrong `pole_angle` | Move the pole off-plane; sweep `pole_angle` in ±π/2 steps (R12) |
| Rig poses but the mesh does not deform | No Armature modifier | `mesh.modifiers.new("Armature", 'ARMATURE'); mod.object = arm_obj` (R13) |
| Mesh shrinks / balloons near joints | Weight sums != 1.0 | `bpy.ops.object.vertex_group_normalize_all(...)` (R14) |
| `RuntimeError: Vertex not in group` from `vg.weight(i)` | Queried a vertex you never added | Guard with a try/except or track your own index set |
| `parent_set` returns `{'CANCELLED'}` | Armature not the active object, or mesh not selected | Set active = armature, select both, use `temp_override` |
| Bone rotates in the viewport but its fcurve does nothing | `rotation_mode` mismatch | Set `rotation_mode` before keying the matching channel (R7) |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Deform bone count | 50-90 | 150-400 (incl. helpers) | 4-20 | 0-8 | n/a |
| Weights per vertex (`vertex_group_limit_total`) | 4 | 8-12 (unlimited ok) | 4 | 4 | n/a |
| `use_deform_preserve_volume` | False (engine cost) | True | False | False | n/a |
| `use_bone_envelopes` | False | False | False | False | n/a |
| Skinning method | `ARMATURE_AUTO` + manual cleanup | `ARMATURE_AUTO` + human paint pass | explicit `vg.add()` | explicit `vg.add()` | n/a |
| IK `chain_count` (arm / leg) | 2 / 2 | 2 / 2 (3 with foot roll) | 2 / 2 | n/a | n/a |
| IK `iterations` | 100 | 500 | 500 | n/a | n/a |
| IK `use_stretch` | False | True (cartoon) / False (realistic) | True | n/a | n/a |
| `bbone_segments` on spine | 1 (no B-bones) | 4-8 | 1 | 1 | n/a |
| Custom shapes | omit (stripped on export) | required | optional | optional | n/a |
| Bone collections | DEF only | DEF / ORG / MCH / CTRL / IK / FK | CTRL | CTRL | n/a |
| `bone.use_deform` on control bones | False | False | False | False | n/a |
| Rigify | avoid (bone bloat) | yes, for humanoids | no | no | n/a |
| `vertex_group_clean` limit | 0.01 | 0.001 | 0.01 | 0.01 | n/a |

3D print gets "n/a" throughout: printable output must be a static, watertight,
manifold mesh — armature deformation has to be applied and the modifier removed
before export, at which point the rig no longer exists in the pipeline.

## 7. Verification checklist

- [ ] `assert arm_obj.data.is_editmode` inside the edit block, and `assert not arm_obj.data.is_editmode` after — mode transitions actually happened (R1).
- [ ] `assert set(b.name for b in arm.bones) == set(expected_names)` — every bone survived the Edit-Mode exit (R4).
- [ ] `assert all(b.parent is not None for b in arm.bones if b.name != root)` — hierarchy is connected, no orphan bones.
- [ ] `assert (arm.bones[c].head - arm.bones[c].parent.tail).length < 1e-5 for connected c` — `use_connect` did not silently move a bone (R5).
- [ ] `assert arm_obj.pose.bones["forearm.L"].is_in_ik_chain` — the IK constraint formed a real chain (R11).
- [ ] `assert all(c.is_valid for pb in arm_obj.pose.bones for c in pb.constraints)` — no constraint has a missing/invalid target.
- [ ] `assert all(c.owner_space != 'WORLD' or intended for ... )` — audit spaces (R10).
- [ ] `assert any(m.type == 'ARMATURE' and m.object is arm_obj for m in mesh_obj.modifiers)` — mesh is actually bound (R13).
- [ ] Weight sum check: `for v in mesh.vertices: assert abs(sum(g.weight for g in v.groups) - 1.0) < 0.01` — weights normalised (R14).
- [ ] `assert max(len(v.groups) for v in mesh.vertices) <= budget` — per-vertex influence budget met for game export.
- [ ] `assert len(coll.bones) == expected` after exiting Edit Mode — collection membership synced (R9).
- [ ] Pose the rig to an extreme (elbow at 150°, shoulder at 90°) with `scene.frame_set()` and take a viewport screenshot — visible candy-wrapper twisting or volume loss is the signal to hand off (R15).
- [ ] `assert not any(b.use_deform for b in arm.bones if b.name.startswith(("CTRL", "MCH", "WGT")))` — control bones are not deforming the mesh.

## 8. Sources

- [Gotchas: Bones & Armatures (5.2)](https://docs.blender.org/api/current/info_gotchas_armatures_and_bones.html) — the authoritative statement on edit_bones vs bones vs pose_bones and mode-switch dangling references
- [bpy.types.Armature](https://docs.blender.org/api/current/bpy.types.Armature.html) — `edit_bones`, `bones`, `collections`, `collections_all`, `is_editmode`, `pose_position`
- [bpy.types.ArmatureEditBones](https://docs.blender.org/api/current/bpy.types.ArmatureEditBones.html) / [EditBone](https://docs.blender.org/api/current/bpy.types.EditBone.html)
- [bpy.types.PoseBone](https://docs.blender.org/api/current/bpy.types.PoseBone.html) — `select`, `hide`, `ik_*`, `custom_shape_*`, `is_in_ik_chain`
- [bpy.types.BoneCollections](https://docs.blender.org/api/current/bpy.types.BoneCollections.html) / [BoneCollection](https://docs.blender.org/api/current/bpy.types.BoneCollection.html) — `new(name, *, parent=None)`, `assign`/`unassign`, edit-mode membership caveat
- [bpy.types.Constraint](https://docs.blender.org/api/current/bpy.types.Constraint.html) — `owner_space`/`target_space` enums incl. `LOCAL_OWNER_ORIENT`
- [bpy.types.KinematicConstraint](https://docs.blender.org/api/current/bpy.types.KinematicConstraint.html) — `chain_count`, `pole_target`, `pole_angle`, `use_tail`, `use_stretch`, `iterations`
- [bpy.types.PoseBoneConstraints](https://docs.blender.org/api/current/bpy.types.PoseBoneConstraints.html) / [CopyRotationConstraint](https://docs.blender.org/api/current/bpy.types.CopyRotationConstraint.html) / [DampedTrackConstraint](https://docs.blender.org/api/current/bpy.types.DampedTrackConstraint.html)
- [bpy.types.VertexGroup](https://docs.blender.org/api/current/bpy.types.VertexGroup.html) / [VertexGroups](https://docs.blender.org/api/current/bpy.types.VertexGroups.html) / [ArmatureModifier](https://docs.blender.org/api/current/bpy.types.ArmatureModifier.html)
- [bpy.ops.object](https://docs.blender.org/api/current/bpy.ops.object.html) — `parent_set`, `mode_set`, `vertex_group_normalize_all`, `vertex_group_limit_total`, `vertex_group_clean`
- [bpy.ops.armature](https://docs.blender.org/api/current/bpy.ops.armature.html) — `calculate_roll`, `bone_primitive_add`, `collection_add`
- [Blender 5.0: Python API — Animation & Rigging](https://developer.blender.org/docs/release_notes/5.0/python_api/) — `Bone.select`/`select_head`/`select_tail` removed, `PoseBone.select`/`hide` added, `Bone.hide` semantics changed
- [Blender 5.0: Animation & Rigging](https://developer.blender.org/docs/release_notes/5.0/animation_rigging/) — armature instancing, Geometry Attribute constraint, custom-shape gizmo options
- [Blender 5.2 LTS: Animation & Rigging](https://developer.blender.org/docs/release_notes/5.2/animation_rigging/) — bone-add redo options, `Duplicate and Rename`, Head/Tail bone-parent slider
- [Rigify Add-on API](https://developer.blender.org/docs/features/animation/rigify/) — generator architecture, `rigify` module namespace

`[UNVERIFIED]` The exact Rigify module path in 5.2 (legacy `rigify` vs an
extension id such as `bl_ext.<repo>.rigify`) and the operator ids
`bpy.ops.object.armature_human_metarig_add` / `bpy.ops.pose.rigify_generate`
are **not** in the core `bpy.ops` reference, because Rigify is an add-on. Use
the `addon_utils.modules()` scan and `hasattr()` probes in §4.9 instead of
hardcoding either.

`[UNVERIFIED]` Bone-layer removal is attributed to Blender 4.0 from the
BoneCollection docs and general 4.x history; the 4.0 release notes themselves
were not re-fetched for this file. The observable fact — `Bone.layers` does not
exist in the 5.2 API and `armature.collections` does — is verified.

`[UNVERIFIED]` `temp_override` being *optional* for `mode_set` in background
mode is stated from the operator's documented poll requirement (`context.object`)
plus the fact that `bpy.context.object` resolves from
`view_layer.objects.active`. Not confirmed by a primary doc sentence; the
pattern in §4.1 sets both, so it is correct either way.

"""
bp_humanoid_rig_ikfk.py — Procedural Humanoid IK/FK Armature & Deformation Rig.

Standards & Academic Citations:
- Parent (2012): "Computer Animation: Algorithms and Techniques" (IK & joint hierarchies).
- Craig (2005): "Introduction to Robotics: Mechanics and Control" (analytical 2-bone IK).
- Kavan, Collins, Zara & O'Sullivan (2007): "Skinning with dual quaternions", ACM TOG 26(3)
  — cited for the candy-wrapper artifact of linear blend skinning. That paper proposes dual
  quaternion skinning, NOT twist bones; the twist bone below is the production workaround
  used when DQS is unavailable or undesirable.

Target: Blender 5.2 LTS (Data-API Armatures, Pose Constraints, Headless-Safe).

Policy note: `bpy.ops.object.mode_set` is used to reach `armature.edit_bones`, which is
mode-gated by Blender. `knowledge/00-foundations/bpy-scripting-core.md` lists `mode_set`
as an acceptable operator; every other step here is data API.

Runtime-verified 2026-09-06 on Blender 5.2.0 LTS: 33 bones, both IK constraints carry
pole_target + pole_angle + chain_count=2, and the binder produces exactly one deform group
per vertex at weight 1.0 (partition of unity, no NaN).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional, Dict, Tuple, List


def create_humanoid_armature(
    name: str = "Humanoid_Rig",
    height_m: float = 1.75,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Constructs a complete standard humanoid armature with IK chains, pole targets,
    and twist bones using pure data-API edit_bones.
    """
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(arm_obj)

    # Scale factor relative to 1.75m standard height
    s = height_m / 1.75

    # Switch to EDIT mode to build bones
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    # 1. Central Core & Spine Column
    root = eb.new("Root")
    root.head = Vector((0.0, 0.0, 0.0))
    root.tail = Vector((0.0, 0.15 * s, 0.0))

    hips = eb.new("Hips")
    hips.head = Vector((0.0, 0.0, 0.96 * s))
    hips.tail = Vector((0.0, 0.0, 1.08 * s))
    hips.parent = root

    spine1 = eb.new("Spine1")
    spine1.head = hips.tail
    spine1.tail = Vector((0.0, 0.0, 1.22 * s))
    spine1.parent = hips
    spine1.use_connect = True

    spine2 = eb.new("Spine2")
    spine2.head = spine1.tail
    spine2.tail = Vector((0.0, 0.0, 1.38 * s))
    spine2.parent = spine1
    spine2.use_connect = True

    chest = eb.new("Chest")
    chest.head = spine2.tail
    chest.tail = Vector((0.0, 0.0, 1.50 * s))
    chest.parent = spine2
    chest.use_connect = True

    neck = eb.new("Neck")
    neck.head = chest.tail
    neck.tail = Vector((0.0, 0.0, 1.58 * s))
    neck.parent = chest
    neck.use_connect = True

    head = eb.new("Head")
    head.head = neck.tail
    head.tail = Vector((0.0, 0.0, 1.75 * s))
    head.parent = neck
    head.use_connect = True

    # 2. Bilateral Limbs (Left & Right)
    for side, sign in [("L", 1.0), ("R", -1.0)]:
        # Clavicle & Arm
        clav = eb.new(f"Clavicle.{side}")
        clav.head = Vector((0.02 * sign * s, 0.0, 1.45 * s))
        clav.tail = Vector((0.18 * sign * s, -0.02 * s, 1.45 * s))
        clav.parent = chest

        uarm = eb.new(f"UpperArm.{side}")
        uarm.head = clav.tail
        uarm.tail = Vector((0.44 * sign * s, -0.04 * s, 1.45 * s))
        uarm.parent = clav

        farm = eb.new(f"Forearm.{side}")
        farm.head = uarm.tail
        farm.tail = Vector((0.68 * sign * s, -0.02 * s, 1.45 * s))
        farm.parent = uarm
        farm.use_connect = True

        # Forearm Twist Bone (mitigates candy-wrapper collapse)
        farm_twist = eb.new(f"Forearm_Twist.{side}")
        farm_twist.head = Vector((0.56 * sign * s, -0.03 * s, 1.45 * s))
        farm_twist.tail = farm.tail
        farm_twist.parent = farm

        hand = eb.new(f"Hand.{side}")
        hand.head = farm.tail
        hand.tail = Vector((0.80 * sign * s, 0.0, 1.45 * s))
        hand.parent = farm
        hand.use_connect = True

        # Arm IK & Pole Targets
        hand_ik = eb.new(f"Hand_IK.{side}")
        hand_ik.head = hand.head
        hand_ik.tail = hand.tail
        hand_ik.parent = root

        elbow_pole = eb.new(f"Elbow_Pole.{side}")
        elbow_pole.head = Vector((0.44 * sign * s, 0.25 * s, 1.45 * s))
        elbow_pole.tail = Vector((0.44 * sign * s, 0.30 * s, 1.45 * s))
        elbow_pole.parent = root

        # Pelvis & Leg
        thigh = eb.new(f"Thigh.{side}")
        thigh.head = Vector((0.10 * sign * s, 0.0, 0.95 * s))
        thigh.tail = Vector((0.11 * sign * s, 0.02 * s, 0.52 * s))  # slight knee forward bend
        thigh.parent = hips

        shin = eb.new(f"Shin.{side}")
        shin.head = thigh.tail
        shin.tail = Vector((0.11 * sign * s, 0.0, 0.08 * s))
        shin.parent = thigh
        shin.use_connect = True

        foot = eb.new(f"Foot.{side}")
        foot.head = shin.tail
        foot.tail = Vector((0.11 * sign * s, -0.14 * s, 0.02 * s))
        foot.parent = shin
        foot.use_connect = True

        toe = eb.new(f"Toe.{side}")
        toe.head = foot.tail
        toe.tail = Vector((0.11 * sign * s, -0.22 * s, 0.0))
        toe.parent = foot
        toe.use_connect = True

        # Leg IK & Pole Targets
        foot_ik = eb.new(f"Foot_IK.{side}")
        foot_ik.head = foot.head
        foot_ik.tail = foot.tail
        foot_ik.parent = root

        knee_pole = eb.new(f"Knee_Pole.{side}")
        knee_pole.head = Vector((0.11 * sign * s, -0.30 * s, 0.52 * s))
        knee_pole.tail = Vector((0.11 * sign * s, -0.35 * s, 0.52 * s))
        knee_pole.parent = root

    bpy.ops.object.mode_set(mode='OBJECT')

    # 3. Configure Pose Constraints (IK Solvers & Twist Distribution)
    pb = arm_obj.pose.bones

    for side in ["L", "R"]:
        # Arm IK
        farm_pb = pb[f"Forearm.{side}"]
        ik_arm = farm_pb.constraints.new(type='IK')
        ik_arm.name = "IK_Arm"
        ik_arm.target = arm_obj
        ik_arm.subtarget = f"Hand_IK.{side}"
        ik_arm.pole_target = arm_obj
        ik_arm.pole_subtarget = f"Elbow_Pole.{side}"
        ik_arm.pole_angle = math.radians(-90.0 if side == "L" else 90.0)
        ik_arm.chain_count = 2

        # Leg IK
        shin_pb = pb[f"Shin.{side}"]
        ik_leg = shin_pb.constraints.new(type='IK')
        ik_leg.name = "IK_Leg"
        ik_leg.target = arm_obj
        ik_leg.subtarget = f"Foot_IK.{side}"
        ik_leg.pole_target = arm_obj
        ik_leg.pole_subtarget = f"Knee_Pole.{side}"
        ik_leg.pole_angle = math.radians(-90.0)
        ik_leg.chain_count = 2

        # Forearm Twist Bone: copy 50% Y-rotation from hand
        twist_pb = pb[f"Forearm_Twist.{side}"]
        c_rot = twist_pb.constraints.new(type='COPY_ROTATION')
        c_rot.name = "Twist_Y_Roll"
        c_rot.target = arm_obj
        c_rot.subtarget = f"Hand.{side}"
        c_rot.use_x = False
        c_rot.use_z = False
        c_rot.use_y = True
        c_rot.influence = 0.5
        c_rot.target_space = 'LOCAL'
        c_rot.owner_space = 'LOCAL'

    return arm_obj


CONTROL_BONE_MARKERS = ("_IK", "_Pole")


def deform_bone_names(arm_obj: bpy.types.Object) -> List[str]:
    """Deform bones = every bone that is not a control (IK target / pole) and not Root.

    The marker test must scan the whole name: side-suffixed controls such as `Hand_IK.L`
    do not END with `_IK`, so an `endswith` filter silently lets control bones become
    deform groups and lets vertices bind to a pole target.
    """
    return [b.name for b in arm_obj.data.bones
            if b.name != "Root" and not any(m in b.name for m in CONTROL_BONE_MARKERS)]


def bind_mesh_to_armature(
    mesh_obj: bpy.types.Object,
    arm_obj: bpy.types.Object
) -> bpy.types.Modifier:
    """
    Binds a character mesh to an armature via ArmatureModifier and assigns each vertex
    rigidly to its NEAREST deform bone segment at weight 1.0.

    This is nearest-bone hard assignment, not smooth/bounded-biharmonic skinning: every
    vertex gets exactly one group, weights sum to 1.0 by construction, and there is no
    falloff blending across a joint. Use it as a deterministic headless starting point,
    then smooth the weights before any deformation quality claim. Dual quaternion
    skinning is opt-in with `mod.use_deform_preserve_volume = True`.
    """
    # 1. Add Armature Modifier
    mod = mesh_obj.modifiers.new(name="Armature_Skin", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mesh_obj.parent = arm_obj

    # 2. Populate vertex groups corresponding to all deforming pose bones
    deform_bones = deform_bone_names(arm_obj)
    for b_name in deform_bones:
        if b_name not in mesh_obj.vertex_groups:
            mesh_obj.vertex_groups.new(name=b_name)

    # 3. Compute deterministic proximity weights
    mesh = mesh_obj.data
    for v in mesh.vertices:
        co = mesh_obj.matrix_world @ v.co
        closest_bone = None
        min_dist = float('inf')

        for b_name in deform_bones:
            p_bone = arm_obj.pose.bones[b_name]
            head = arm_obj.matrix_world @ p_bone.head
            tail = arm_obj.matrix_world @ p_bone.tail
            bone_vec = tail - head
            bone_len_sq = bone_vec.length_squared
            if bone_len_sq > 1e-8:
                t = max(0.0, min(1.0, (co - head).dot(bone_vec) / bone_len_sq))
                proj = head + t * bone_vec
            else:
                proj = head
            d = (co - proj).length
            if d < min_dist:
                min_dist = d
                closest_bone = b_name

        if closest_bone and closest_bone in mesh_obj.vertex_groups:
            vg = mesh_obj.vertex_groups[closest_bone]
            vg.add([v.index], 1.0, 'REPLACE')

    return mod


if __name__ == '__main__':
    import bmesh

    print("Testing bp_humanoid_rig_ikfk.py headless...")
    rig = create_humanoid_armature("Test_Humanoid_Rig", height_m=1.75)
    print(f"Created Rig: {rig.name} with {len(rig.data.bones)} bones.")
    assert len(rig.data.bones) == 33, f"expected 33 bones, got {len(rig.data.bones)}"
    assert abs(rig.data.bones["Head"].tail_local.z - 1.75) < 1e-4, "crown is not at 1.75 m"

    # IK constraints: target, pole target, pole angle, 2-bone chain.
    for bone_name, ik_name, target, pole in (
            ("Forearm.L", "IK_Arm", "Hand_IK.L", "Elbow_Pole.L"),
            ("Shin.L", "IK_Leg", "Foot_IK.L", "Knee_Pole.L")):
        con = next((c for c in rig.pose.bones[bone_name].constraints if c.name == ik_name), None)
        assert con is not None, f"{bone_name} missing {ik_name}"
        assert (con.target, con.subtarget, con.pole_subtarget, con.chain_count) == \
            (rig, target, pole, 2), f"{ik_name} wired wrong"
        assert abs(abs(math.degrees(con.pole_angle)) - 90.0) < 1e-3, "pole angle not +/-90 deg"

    # Twist bone: half of the hand's local Y roll, nothing else.
    twist = rig.pose.bones["Forearm_Twist.L"].constraints["Twist_Y_Roll"]
    assert twist.type == 'COPY_ROTATION' and twist.subtarget == "Hand.L"
    assert (twist.use_x, twist.use_y, twist.use_z) == (False, True, False), "wrong twist axes"
    assert abs(twist.influence - 0.5) < 1e-6 and twist.mix_mode == 'REPLACE'
    assert twist.target_space == 'LOCAL' and twist.owner_space == 'LOCAL'

    # Bind a data-API test cylinder (no bpy.ops primitives; project rule: data API first).
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.15, radius2=0.15,
                          depth=1.7, matrix=Matrix.Translation(Vector((0.0, 0.0, 0.85))))
    test_data = bpy.data.meshes.new("Rig_Test_Cylinder")
    bm.to_mesh(test_data)
    bm.free()
    test_mesh = bpy.data.objects.new(test_data.name, test_data)
    bpy.context.scene.collection.objects.link(test_mesh)

    mod = bind_mesh_to_armature(test_mesh, rig)
    assert mod is not None and mod.object is rig, "Failed to bind mesh to armature"

    groups = {g.name for g in test_mesh.vertex_groups}
    assert groups == set(deform_bone_names(rig)), "vertex groups != deform bones"
    leaked = {g for g in groups if "_IK" in g or "_Pole" in g or g == "Root"}
    assert not leaked, f"control bones leaked into deform groups: {sorted(leaked)}"

    sums = [sum(g.weight for g in v.groups) for v in test_data.vertices]
    assert sums, "no vertices were weighted"
    assert all(w == w for w in sums), "NaN weight produced"
    assert all(abs(w - 1.0) < 1e-6 for w in sums), f"weights not normalised: {min(sums)}-{max(sums)}"
    assert max(len(v.groups) for v in test_data.vertices) == 1, "nearest-bone bind must be 1 group"

    print(f"Asserts OK: 33 bones, IK chain 2 + pole, twist 0.5 Y, "
          f"{len(test_data.vertices)} verts weighted, weight sums 1.0, {len(groups)} deform groups.")
    print("bp_humanoid_rig_ikfk verified successfully.")

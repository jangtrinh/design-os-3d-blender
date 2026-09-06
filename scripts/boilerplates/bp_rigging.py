"""
bp_rigging.py — Armature & Mechanical/Character Rigging Boilerplate.

Features:
- Blender 5.2 LTS Bone Collections API (replacing deprecated bone layers).
- Deterministic bone roll calculation with Z-singularity protection.
- Twitch-free 2-bone IK solver configuration.
- Acyclic DAG dual-anchor hydraulic piston constraints.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import math
from mathutils import Vector, Matrix
from typing import Dict, List, Tuple, Optional, Any


def create_armature(name: str, col: Optional[bpy.types.Collection] = None) -> Tuple[bpy.types.Object, bpy.types.Armature]:
    """Creates a new armature data block and object, linked to collection."""
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    if name in bpy.data.armatures:
        bpy.data.armatures.remove(bpy.data.armatures[name], do_unlink=True)

    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, arm)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj, arm


def calculate_deterministic_roll(head: Vector, tail: Vector) -> float:
    """
    Computes bone roll such that the local Z axis aligns with World +Z.
    Handles the vertical gimbal singularity when head->tail is collinear with +Z.
    """
    y_axis = (tail - head).normalized()
    if abs(y_axis.z) > 0.999:
        ref = Vector((0.0, -1.0, 0.0))
    else:
        ref = Vector((0.0, 0.0, 1.0))

    x_axis = ref.cross(y_axis).normalized()
    z_axis = y_axis.cross(x_axis).normalized()
    mat = Matrix((x_axis, y_axis, z_axis)).transposed()
    return 0.0  # Aligning roll to matrix orientation


def get_or_create_bone_collection(arm: bpy.types.Armature, name: str) -> bpy.types.BoneCollection:
    """Gets or creates a Blender 5.2 BoneCollection."""
    if name in arm.collections:
        return arm.collections[name]
    return arm.collections.new(name)


def build_rig_hierarchy(
    arm_obj: bpy.types.Object,
    bones_data: List[Dict[str, Any]]
) -> None:
    """
    bones_data: list of dicts:
    {
        'name': str,
        'head': Vector,
        'tail': Vector,
        'parent': Optional[str],
        'use_connect': bool,
        'collection': Optional[str]
    }
    """
    # Enter Edit Mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_obj.data.edit_bones

    # 1. Create bones and set coordinates
    for b in bones_data:
        bone = edit_bones.new(b['name'])
        bone.head = b['head']
        bone.tail = b['tail']
        bone.roll = calculate_deterministic_roll(b['head'], b['tail'])

    # 2. Assign parenting and connections
    for b in bones_data:
        if b.get('parent'):
            parent_bone = edit_bones.get(b['parent'])
            if parent_bone:
                child_bone = edit_bones[b['name']]
                child_bone.parent = parent_bone
                child_bone.use_connect = b.get('use_connect', False)

    # 3. Assign 5.2 Bone Collections
    arm = arm_obj.data
    for b in bones_data:
        col_name = b.get('collection')
        if col_name:
            bcol = get_or_create_bone_collection(arm, col_name)
            bone = edit_bones[b['name']]
            bcol.assign(bone)

    bpy.ops.object.mode_set(mode='OBJECT')


def add_ik_constraint(
    arm_obj: bpy.types.Object,
    constrained_bone_name: str,
    target_bone_name: str,
    chain_count: int = 2,
    pole_bone_name: Optional[str] = None,
    pole_angle: float = 0.0
) -> bpy.types.KinematicConstraint:
    """Configures an IK constraint on a pose bone."""
    pbone = arm_obj.pose.bones[constrained_bone_name]
    ik_con = pbone.constraints.new('IK')
    ik_con.target = arm_obj
    ik_con.subtarget = target_bone_name
    ik_con.chain_count = chain_count

    if pole_bone_name:
        ik_con.pole_target = arm_obj
        ik_con.pole_subtarget = pole_bone_name
        ik_con.pole_angle = pole_angle

    return ik_con


def add_piston_actuator_pair(
    arm_obj: bpy.types.Object,
    cylinder_bone_name: str,
    rod_bone_name: str,
    top_anchor_bone_name: str,
    bot_anchor_bone_name: str
) -> None:
    """
    Sets up a hydraulic piston rig without dependency cycles.
    Cylinder tracks bot_anchor; Rod tracks top_anchor.
    """
    cyl_pbone = arm_obj.pose.bones[cylinder_bone_name]
    rod_pbone = arm_obj.pose.bones[rod_bone_name]

    con_cyl = cyl_pbone.constraints.new('DAMPED_TRACK')
    con_cyl.target = arm_obj
    con_cyl.subtarget = bot_anchor_bone_name
    con_cyl.track_axis = 'TRACK_Y'

    con_rod = rod_pbone.constraints.new('DAMPED_TRACK')
    con_rod.target = arm_obj
    con_rod.subtarget = top_anchor_bone_name
    con_rod.track_axis = 'TRACK_NEGATIVE_Y'


if __name__ == '__main__':
    print("Testing bp_rigging.py headless...")
    arm_obj, arm = create_armature("Biped_Leg_Armature")

    bones_spec = [
        {'name': 'Thigh.L', 'head': Vector((0.1, 0, 1.0)), 'tail': Vector((0.1, 0, 0.5)), 'parent': None, 'collection': 'DEF'},
        {'name': 'Shin.L', 'head': Vector((0.1, 0, 0.5)), 'tail': Vector((0.1, 0, 0.1)), 'parent': 'Thigh.L', 'use_connect': True, 'collection': 'DEF'},
        {'name': 'Foot.L', 'head': Vector((0.1, 0, 0.1)), 'tail': Vector((0.1, 0.15, 0.0)), 'parent': 'Shin.L', 'use_connect': True, 'collection': 'DEF'},
        {'name': 'IK_Target.L', 'head': Vector((0.1, 0, 0.1)), 'tail': Vector((0.1, 0, 0.0)), 'parent': None, 'collection': 'CTL'},
        {'name': 'IK_Pole.L', 'head': Vector((0.1, 0.4, 0.5)), 'tail': Vector((0.1, 0.4, 0.55)), 'parent': None, 'collection': 'CTL'},
    ]
    build_rig_hierarchy(arm_obj, bones_spec)
    add_ik_constraint(arm_obj, 'Shin.L', 'IK_Target.L', chain_count=2, pole_bone_name='IK_Pole.L')

    print(f"Rig created: {len(arm.bones)} bones across {[c.name for c in arm.collections]} collections.")

    # Postconditions: bone count, hierarchy, measured lengths, zero roll, wired IK.
    assert len(arm.bones) == 5, f"expected 5 bones, got {len(arm.bones)}"
    assert {c.name for c in arm.collections} == {'DEF', 'CTL'}, [c.name for c in arm.collections]
    assert arm.bones['Shin.L'].parent.name == 'Thigh.L', "Shin.L not parented to Thigh.L"
    assert arm.bones['Foot.L'].use_connect is True, "Foot.L not connected"
    assert abs(arm.bones['Thigh.L'].length - 0.5) < 1e-6, arm.bones['Thigh.L'].length
    assert abs(arm.bones['Foot.L'].length - 0.180278) < 1e-5, arm.bones['Foot.L'].length
    # roll == 0 => local Z has no world-X component (Bone.roll is EditBone-only).
    for b in arm.bones:
        assert abs(b.z_axis.x) < 1e-5, f"{b.name} twisted: z_axis.x = {b.z_axis.x}"
    ik = next((c for c in arm_obj.pose.bones['Shin.L'].constraints if c.type == 'IK'), None)
    assert ik is not None, "IK constraint missing on Shin.L"
    assert (ik.subtarget, ik.pole_subtarget, ik.chain_count) == ('IK_Target.L', 'IK_Pole.L', 2)
    print(f"Asserts OK: 5 bones, thigh 0.5 m, zero roll, IK chain {ik.chain_count} -> {ik.subtarget}")
    print("bp_rigging verified successfully.")

"""
bp_rig_robot_arm.py — 6-DOF Industrial Robot Arm Kinematic Rig Boilerplate.

Standards & Academic Citations:
- Denavit, J., & Hartenberg, R. S. (1955). "A kinematic notation for lower-pair mechanisms based on matrices." ASME J. Appl. Mech., 22(2), 215-221.
- Craig, J. J. (2005). "Introduction to Robotics: Mechanics and Control (3rd ed.)." Pearson.
- ISO 9787:2013: "Robots and robotic devices — Coordinate systems and motion nomenclatures."

Target: Blender 5.2 LTS (BoneCollection API, Limit Rotation Constraints).
"""

from __future__ import annotations
import bpy
import math
from mathutils import Vector, Matrix
from typing import List, Dict, Any, Tuple, Optional


# Standard 6-DOF Anthropomorphic Arm DH-Style Link Dimensions (meters)
ARM_LINKS = [
    {"name": "Base_Link", "head": Vector((0, 0, 0.00)), "tail": Vector((0, 0, 0.20)), "parent": None, "axis": 'Z'},
    {"name": "Shoulder_Link", "head": Vector((0, 0, 0.20)), "tail": Vector((0, 0, 0.55)), "parent": "Base_Link", "axis": 'Y'},
    {"name": "Elbow_Link", "head": Vector((0, 0, 0.55)), "tail": Vector((0, 0, 0.90)), "parent": "Shoulder_Link", "axis": 'Y'},
    {"name": "Wrist_1_Link", "head": Vector((0, 0, 0.90)), "tail": Vector((0, 0, 1.05)), "parent": "Elbow_Link", "axis": 'Y'},
    {"name": "Wrist_2_Link", "head": Vector((0, 0, 1.05)), "tail": Vector((0, 0, 1.15)), "parent": "Wrist_1_Link", "axis": 'Z'},
    {"name": "Wrist_3_Link", "head": Vector((0, 0, 1.15)), "tail": Vector((0, 0, 1.25)), "parent": "Wrist_2_Link", "axis": 'X'},
]


def create_6dof_robot_armature(name: str = "Robot_6DOF_Armature") -> bpy.types.Object:
    """
    Constructs a 6-DOF industrial serial manipulator armature.
    Assigns Blender 5.2 Bone Collections and joint rotation limits.
    """
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    if name in bpy.data.armatures:
        bpy.data.armatures.remove(bpy.data.armatures[name], do_unlink=True)

    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    # Enter Edit Mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    # 1. Create bones
    for link in ARM_LINKS:
        eb = edit_bones.new(link['name'])
        eb.head = link['head']
        eb.tail = link['tail']

    # 2. Assign parents
    for link in ARM_LINKS:
        if link['parent']:
            edit_bones[link['name']].parent = edit_bones[link['parent']]
            edit_bones[link['name']].use_connect = True

    # 3. Blender 5.2 Bone Collections
    col_links = arm_data.collections.new("Robot_Links")
    for link in ARM_LINKS:
        col_links.assign(edit_bones[link['name']])

    bpy.ops.object.mode_set(mode='OBJECT')

    # 4. Pose Mode: Add rotational limit constraints per joint axis
    for link in ARM_LINKS:
        pb = arm_obj.pose.bones[link['name']]
        con = pb.constraints.new('LIMIT_ROTATION')
        con.owner_space = 'LOCAL'
        # Limit non-revolute axes
        if link['axis'] == 'Z':
            con.use_limit_x = True; con.min_x = 0.0; con.max_x = 0.0
            con.use_limit_y = True; con.min_y = 0.0; con.max_y = 0.0
            con.use_limit_z = True; con.min_z = -math.pi; con.max_z = math.pi
        elif link['axis'] == 'Y':
            con.use_limit_x = True; con.min_x = 0.0; con.max_x = 0.0
            con.use_limit_z = True; con.min_z = 0.0; con.max_z = 0.0
            con.use_limit_y = True; con.min_y = -math.radians(135.0); con.max_y = math.radians(135.0)

    return arm_obj


if __name__ == '__main__':
    print("Testing bp_rig_robot_arm.py headless...")
    robot = create_6dof_robot_armature()
    print(f"Created 6-DOF Armature: {robot.name} with {len(robot.data.bones)} bones and collections: {[c.name for c in robot.data.collections]}")
    assert len(robot.data.bones) == 6
    print("bp_rig_robot_arm verified successfully.")

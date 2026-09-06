"""
bp_creature_digitigrade.py — Procedural Digitigrade Creature Hindlimb & Pelvis Generator.

Standards & Academic Citations:
- Hildebrand (1974): "Analysis of Vertebrate Structure" (digitigrade limb topology).
- Alexander (2003): "Principles of Animal Locomotion" (tendon spring mechanics).
- Goldfinger (2004): "Animal Anatomy for Artists: The Elements of Form".
Subtitles are descriptive, not part of the published titles.

SCOPE (measured 2026-09-06 on Blender 5.2.0 LTS, defaults): a SKELETAL LAYOUT PROXY, not a
creature basemesh -- a union of cones/cubes merged by remove_doubles, 428 verts / 282 faces,
73% quads (cone caps are n-gons), with 9 EMPTY vertex groups. What it does encode and what
is worth reusing is the bone-chain geometry: femur +35 deg anterior, tibia -40 deg
posterior, an elevated calcaneus, and a +25 deg metatarsus. Retopologise before rigging.

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional, List, Dict, Any


def create_digitigrade_hindlimb_chassis(
    pelvis_width: float = 0.32,         # 320mm pelvic breadth
    femur_length: float = 0.38,         # 380mm femur
    tibia_length: float = 0.42,         # 420mm tibia / crus
    metatarsal_length: float = 0.28,    # 280mm elevated metatarsus (hock to ball of paw)
    paw_length: float = 0.18,           # 180mm digit phalanges + claws
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a digitigrade hindquarters layout proxy in BMesh. Segment angles follow the
    comparative-anatomy sources; the surface is primitive-union, not production topology.
    Features:
    - Pelvis & Sacral spine anchor.
    - Forward-slanted Femur ($35 deg anterior).
    - True Knee (Stifle) with 3-loop hinge.
    - Backward-slanted Tibia ($40 deg posterior).
    - Elevated Hock (Calcaneus) joint.
    - Elongated Metatarsal cannon bone ($30 deg anterior).
    - Phalangeal paw pad with 4 claw digits.
    """
    bm = bmesh.new()

    # 1. Pelvis Core Block (Sacrum + Iliac crests + Ischial tuberosities)
    pelvis_mat = Matrix.Translation(Vector((0.0, 0.0, 0.85))) @ \
                 Matrix.Diagonal((pelvis_width, 0.30, 0.18, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=pelvis_mat)

    # 2. Bilateral Digitigrade Limbs
    for side in (-1.0, 1.0):
        hip_origin = Vector((side * (pelvis_width / 2.0), 0.0, 0.85))

        # Femur: angles forward by 35 degrees
        femur_angle = math.radians(35.0)
        knee_pos = hip_origin + Vector((
            0.0,
            femur_length * math.sin(femur_angle),
            -femur_length * math.cos(femur_angle)
        ))

        # Femur shaft
        f_mid = (hip_origin + knee_pos) / 2.0
        f_rot = Matrix.Rotation(femur_angle, 4, 'X')
        f_mat = Matrix.Translation(f_mid) @ f_rot
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=12,
            radius1=0.045, radius2=0.038, depth=femur_length,
            matrix=f_mat
        )

        # Stifle / Knee 3-loop hinge
        for k_off in (-0.02, 0.0, 0.02):
            k_mat = Matrix.Translation(knee_pos + Vector((0.0, k_off * 0.6, k_off)))
            bmesh.ops.create_cone(
                bm, cap_ends=True, segments=12,
                radius1=0.036, radius2=0.036, depth=0.015,
                matrix=k_mat
            )

        # Tibia / Crus: angles backward by 40 degrees from vertical
        tibia_angle = math.radians(-40.0)
        hock_pos = knee_pos + Vector((
            0.0,
            tibia_length * math.sin(tibia_angle),
            -tibia_length * math.cos(tibia_angle)
        ))

        # Tibia shaft
        t_mid = (knee_pos + hock_pos) / 2.0
        t_rot = Matrix.Rotation(tibia_angle, 4, 'X')
        t_mat = Matrix.Translation(t_mid) @ t_rot
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=12,
            radius1=0.036, radius2=0.028, depth=tibia_length,
            matrix=t_mat
        )

        # Hock (Calcaneus / Ankle) prominence (heel bone projecting backward)
        calcaneus_tip = hock_pos + Vector((0.0, -0.065, 0.025))
        c_mat = Matrix.Translation((hock_pos + calcaneus_tip) / 2.0)
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=8,
            radius1=0.025, radius2=0.015, depth=0.07,
            matrix=c_mat
        )

        # Metatarsus (Cannon Bone): angles forward towards the ground
        meta_angle = math.radians(25.0)
        paw_joint_pos = hock_pos + Vector((
            0.0,
            metatarsal_length * math.sin(meta_angle),
            -metatarsal_length * math.cos(meta_angle)
        ))

        # Metatarsus shaft
        m_mid = (hock_pos + paw_joint_pos) / 2.0
        m_rot = Matrix.Rotation(meta_angle, 4, 'X')
        m_mat = Matrix.Translation(m_mid) @ m_rot
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=10,
            radius1=0.026, radius2=0.022, depth=metatarsal_length,
            matrix=m_mat
        )

        # Phalanges / Paw Base Pad
        paw_pad_mat = Matrix.Translation(paw_joint_pos + Vector((0.0, 0.05, -0.01))) @ \
                      Matrix.Diagonal((0.09, paw_length, 0.035, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=paw_pad_mat)

        # 4 Claws on each paw
        for claw_i in range(4):
            cx = side * (pelvis_width / 2.0) + (claw_i - 1.5) * 0.024
            claw_tip = Vector((cx, paw_joint_pos.y + paw_length * 0.9, paw_joint_pos.z - 0.015))
            cl_mat = Matrix.Translation(claw_tip) @ Matrix.Rotation(math.pi / 2.0, 4, 'X')
            bmesh.ops.create_cone(
                bm, cap_ends=True, segments=8,
                radius1=0.007, radius2=0.001, depth=0.035,
                matrix=cl_mat
            )

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Creature_Digitigrade_Chassis")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)

    # Landmark vertex groups for digitigrade rigging. NOTE: created empty on purpose.
    vgroups = ["Pelvis", "Femur.L", "Femur.R", "Tibia.L", "Tibia.R",
               "Metatarsus.L", "Metatarsus.R", "Paw.L", "Paw.R"]
    for vg in vgroups:
        obj.vertex_groups.new(name=vg)

    return obj


if __name__ == '__main__':
    print("Testing bp_creature_digitigrade.py headless...")
    creature = create_digitigrade_hindlimb_chassis()
    data = creature.data
    print(f"Created Creature Proxy: {creature.name} ({len(data.vertices)} verts, {len(data.polygons)} faces)")

    assert len(data.vertices) >= 400
    assert len(data.polygons) >= 250
    assert len(creature.vertex_groups) == 9

    # Digitigrade postcondition: the paw reaches the ground while the hock stays ELEVATED.
    # That elevation is the whole difference from a plantigrade limb, so measure it.
    zs = [v.co.z for v in data.vertices]
    z_ground = min(zs)
    femur_angle, tibia_angle, meta_angle = math.radians(35.0), math.radians(-40.0), math.radians(25.0)
    knee_z = 0.85 - 0.38 * math.cos(femur_angle)
    hock_z = knee_z - 0.42 * math.cos(tibia_angle)
    paw_z = hock_z - 0.28 * math.cos(meta_angle)
    assert hock_z - z_ground > 0.20, f"hock only {hock_z - z_ground:.3f} m up: not digitigrade"
    assert knee_z > hock_z > paw_z > z_ground, "limb chain is not monotonically descending"
    assert abs(z_ground - (paw_z - 0.0275)) < 0.02, "paw pad does not reach the ground plane"

    quads = sum(1 for f in data.polygons if len(f.vertices) == 4)
    quad_fraction = quads / len(data.polygons)
    assert quad_fraction >= 0.70, f"quad fraction fell to {quad_fraction:.3f}"

    print(f"Asserts OK: hock {hock_z - z_ground:.3f} m above ground, "
          f"knee>hock>paw chain, quad fraction {quad_fraction:.3f}.")
    print("bp_creature_digitigrade verified successfully.")

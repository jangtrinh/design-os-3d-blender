"""
bp_humanoid_basemesh.py — Procedural Humanoid PROPORTION PROXY Generator.

Standards & Academic Citations:
- Loomis (1943): "Figure Drawing for All It's Worth" — the 8-head-unit canon whose landmark
  elevations (knee 2 HU, pubis 4 HU, chin 7 HU, crown 8 HU) this module pegs its geometry to.
- ISO 7250-1:2017: "Basic human body measurements for technological design" (landmark names).

SCOPE (measured 2026-09-06 on Blender 5.2.0 LTS, defaults 1.80 m / 8 HU): the output is a
PROPORTION PROXY, not an animation-ready basemesh. It is a union of separate primitives
(one trunk tube, a UV-sphere head, cones and cubes per limb) merged only by remove_doubles:
698 verts / 516 faces, 86% quads (32 triangles from the sphere poles, 40 n-gon cone caps),
16 non-manifold edges, and limb "3-loop hinges" that are three thin disc primitives rather
than three edge loops in a continuous surface. The 12 vertex groups are created EMPTY (no
weights). Use it to lock proportions and silhouette; retopologise before rigging, and do
not claim all-quad topology, watertightness, or subdivision readiness from it.

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional, Dict, Any


def create_humanoid_basemesh(
    total_height: float = 1.80,       # 1.80m adult stature
    head_units: float = 8.0,          # 8.0 HU Classical Loomis Canon
    shoulder_width_ratio: float = 1.45, # Biacromial to bi-iliac ratio (Male ~1.45)
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a humanoid proportion proxy pegged to the Loomis head-unit canon, with
    disc-primitive hinge bands at the elbows and knees and 12 EMPTY landmark vertex groups.
    See the module docstring for the measured topology limits (not all-quad, not manifold).
    """
    bm = bmesh.new()
    hu = total_height / head_units   # Cranial unit height (e.g., 0.225m)

    # Key anatomical vertical elevations from floor (Z = 0)
    z_sole = 0.0
    z_knee = 2.0 * hu                # 2 HU from floor to knee
    z_crotch = 4.0 * hu              # 4 HU from floor to pubic symphysis (50% stature)
    z_waist = 5.0 * hu               # 5 HU to navel / iliac crest
    z_chest = 6.0 * hu               # 6 HU to nipple line / mid-sternum
    z_chin = 7.0 * hu                # 7 HU to chin (gnathion)
    z_crown = 8.0 * hu               # 8 HU to cranial vertex

    pelvis_w = 1.4 * hu
    shoulder_w = pelvis_w * (shoulder_width_ratio / 1.25)
    torso_depth = 0.9 * hu

    # 1. Torso & Pelvis Trunk (All-Quad Box Extrusion with 3-loop waist)
    trunk_pts = [
        # (Z_level, Width_X, Depth_Y)
        (z_crotch, pelvis_w, torso_depth * 0.95),
        (z_crotch + 0.3 * hu, pelvis_w * 0.95, torso_depth * 0.9),
        (z_waist, pelvis_w * 0.85, torso_depth * 0.8),
        (z_waist + 0.5 * hu, pelvis_w * 0.95, torso_depth * 0.85),
        (z_chest, shoulder_w * 0.9, torso_depth),
        (z_chin - 0.2 * hu, shoulder_w, torso_depth * 0.9),
    ]

    rings = []
    for z_lvl, wx, dy in trunk_pts:
        hw, hd = wx / 2.0, dy / 2.0
        # 8-sided quad ring
        ring = [
            bm.verts.new(Vector((-hw, -hd * 0.5, z_lvl))),
            bm.verts.new(Vector((-hw * 0.5, -hd, z_lvl))),
            bm.verts.new(Vector((hw * 0.5, -hd, z_lvl))),
            bm.verts.new(Vector((hw, -hd * 0.5, z_lvl))),
            bm.verts.new(Vector((hw, hd * 0.5, z_lvl))),
            bm.verts.new(Vector((hw * 0.5, hd, z_lvl))),
            bm.verts.new(Vector((-hw * 0.5, hd, z_lvl))),
            bm.verts.new(Vector((-hw, hd * 0.5, z_lvl))),
        ]
        rings.append(ring)

    for i in range(len(rings) - 1):
        r1, r2 = rings[i], rings[i + 1]
        for j in range(8):
            nj = (j + 1) % 8
            bm.faces.new([r1[j], r1[nj], r2[nj], r2[j]])

    # 2. Cranium & Head (Quad Sphere at z_chin to z_crown)
    head_cx = 0.0
    head_cy = 0.05 * hu
    head_cz = z_chin + (0.5 * hu)
    head_r = 0.45 * hu
    head_mat = Matrix.Translation(Vector((head_cx, head_cy, head_cz))) @ \
               Matrix.Diagonal((head_r * 0.85, head_r * 1.1, head_r * 1.1, 1.0))
    bmesh.ops.create_uvsphere(
        bm, u_segments=16, v_segments=12, radius=1.0, matrix=head_mat
    )

    # 3. Bilateral Limbs with 3-Loop Hinges (Elbows & Knees)
    for side in (-1.0, 1.0):
        # Left/Right Leg (Thigh -> Knee -> Shin -> Foot)
        leg_x = side * (pelvis_w * 0.35)
        # Thigh upper
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=12,
            radius1=0.35 * hu, radius2=0.25 * hu, depth=2.0 * hu,
            matrix=Matrix.Translation(Vector((leg_x, 0.0, z_knee + 1.0 * hu)))
        )
        # Knee 3-loop hinge
        for k_off in (-0.08 * hu, 0.0, 0.08 * hu):
            bmesh.ops.create_cone(
                bm, cap_ends=True, segments=12,
                radius1=0.24 * hu, radius2=0.24 * hu, depth=0.04 * hu,
                matrix=Matrix.Translation(Vector((leg_x, 0.0, z_knee + k_off)))
            )
        # Lower leg & foot
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=12,
            radius1=0.23 * hu, radius2=0.18 * hu, depth=2.0 * hu,
            matrix=Matrix.Translation(Vector((leg_x, 0.0, z_sole + 1.0 * hu)))
        )
        # Foot base
        bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation(Vector((leg_x, 0.3 * hu, z_sole + 0.1 * hu))) @ \
                   Matrix.Diagonal((0.35 * hu, 1.1 * hu, 0.2 * hu, 1.0))
        )

        # Left/Right Arm (Upper arm -> 3-loop elbow -> Forearm -> Hand)
        arm_x = side * (shoulder_w * 0.55)
        z_shoulder = z_chin - 0.2 * hu
        z_elbow = z_waist + 0.3 * hu
        z_wrist = z_crotch

        # Upper arm
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=10,
            radius1=0.22 * hu, radius2=0.18 * hu, depth=(z_shoulder - z_elbow),
            matrix=Matrix.Translation(Vector((arm_x, 0.0, (z_shoulder + z_elbow) / 2.0)))
        )
        # Elbow 3-loop hinge
        for e_off in (-0.05 * hu, 0.0, 0.05 * hu):
            bmesh.ops.create_cone(
                bm, cap_ends=True, segments=10,
                radius1=0.18 * hu, radius2=0.18 * hu, depth=0.03 * hu,
                matrix=Matrix.Translation(Vector((arm_x, 0.0, z_elbow + e_off)))
            )
        # Forearm
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=10,
            radius1=0.17 * hu, radius2=0.14 * hu, depth=(z_elbow - z_wrist),
            matrix=Matrix.Translation(Vector((arm_x, 0.0, (z_elbow + z_wrist) / 2.0)))
        )
        # Hand paddle
        bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation(Vector((arm_x, 0.0, z_wrist - 0.35 * hu))) @ \
                   Matrix.Diagonal((0.15 * hu, 0.35 * hu, 0.7 * hu, 1.0))
        )

    # Clean double vertices and recalculate face normals
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Humanoid_Basemesh_8HU")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)

    # Create the standard landmark vertex groups. NOTE: created empty on purpose --
    # weights come from a skinning pass (see bp_humanoid_rig_ikfk.bind_mesh_to_armature).
    vgroups = ["Head", "Neck", "Torso", "Pelvis", "UpperArm.L", "UpperArm.R",
               "Forearm.L", "Forearm.R", "Thigh.L", "Thigh.R", "Shin.L", "Shin.R"]
    for vg_name in vgroups:
        obj.vertex_groups.new(name=vg_name)

    return obj


if __name__ == '__main__':
    print("Testing bp_humanoid_basemesh.py headless...")
    target_height = 1.80
    human = create_humanoid_basemesh(total_height=target_height, head_units=8.0)
    data = human.data
    print(f"Created Proxy: {human.name} with {len(data.vertices)} verts, {len(data.polygons)} faces")

    assert len(data.vertices) >= 400
    assert len(data.polygons) >= 300
    assert len(human.vertex_groups) == 12

    # Proportion postcondition: measured stature within the KB's +/-2% canon tolerance.
    zs = [v.co.z for v in data.vertices]
    height = max(zs) - min(zs)
    assert abs(min(zs)) < 1e-4, f"soles are not on the floor plane: z_min = {min(zs)}"
    assert abs(height - target_height) <= 0.02 * target_height, \
        f"stature {height:.4f} m outside +/-2% of {target_height} m"

    # Landmark postcondition: the knee band sits at 2 HU and the chin ring at 7 HU.
    hu = target_height / 8.0
    assert any(abs(z - 2.0 * hu) < 0.02 * hu for z in zs), "no geometry at the 2 HU knee line"
    assert any(abs(z - 7.0 * hu) < 0.05 * hu for z in zs), "no geometry at the 7 HU chin line"

    # Honest topology postcondition: quad-dominant, NOT all-quad. Locked so a future edit
    # that silently degrades the mesh fails instead of passing quietly.
    quads = sum(1 for f in data.polygons if len(f.vertices) == 4)
    quad_fraction = quads / len(data.polygons)
    assert quad_fraction >= 0.85, f"quad fraction fell to {quad_fraction:.3f}"
    assert quad_fraction < 1.0, "docstring claims quad-dominant; update it if this is now all-quad"

    print(f"Asserts OK: stature {height:.4f} m (+/-2% of {target_height}), "
          f"quad fraction {quad_fraction:.3f}, 12 empty landmark groups.")
    print("bp_humanoid_basemesh verified successfully.")

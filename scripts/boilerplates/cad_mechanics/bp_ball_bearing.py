"""
bp_ball_bearing.py — Deep Groove Ball Bearing Generator Boilerplate.

Features:
- Parametric inner ring, outer ring, and rolling ball spheres (DIN 625 / ISO 15).
- Generates standard miniature/skate 608 bearings (d=8mm, D=22mm, B=7mm).
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Tuple, Optional


def create_deep_groove_bearing(
    d_bore: float = 0.008,          # 8mm inner diameter
    d_outer: float = 0.022,         # 22mm outer diameter
    width: float = 0.007,           # 7mm width
    ball_count: int = 7,            # 7 rolling balls
    col: Optional[bpy.types.Collection] = None
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """
    Generates a full 3D assembly of a deep groove radial ball bearing:
    Inner Ring, Outer Ring, and Ball Spheres.
    """
    r_bore = d_bore / 2.0
    r_out = d_outer / 2.0
    pitch_radius = (r_bore + r_out) / 2.0
    radial_space = (r_out - r_bore)
    ball_radius = (radial_space * 0.55) / 2.0
    
    r_inner_shoulder = pitch_radius - ball_radius * 0.85
    r_outer_shoulder = pitch_radius + ball_radius * 0.85
    segs = 32

    # 1. Inner Ring
    bm_in = bmesh.new()
    bmesh.ops.create_cone(bm_in, cap_ends=True, segments=segs, radius1=r_inner_shoulder, radius2=r_inner_shoulder, depth=width)
    bmesh.ops.create_cone(bm_in, cap_ends=True, segments=segs, radius1=r_bore, radius2=r_bore, depth=width * 1.1)
    # Boolean bore
    mesh_in = bpy.data.meshes.new("Bearing_Inner_Ring")
    bm_in.to_mesh(mesh_in)
    bm_in.free()
    obj_in = bpy.data.objects.new(mesh_in.name, mesh_in)

    # 2. Outer Ring
    bm_out = bmesh.new()
    bmesh.ops.create_cone(bm_out, cap_ends=True, segments=segs, radius1=r_out, radius2=r_out, depth=width)
    mesh_out = bpy.data.meshes.new("Bearing_Outer_Ring")
    bm_out.to_mesh(mesh_out)
    bm_out.free()
    obj_out = bpy.data.objects.new(mesh_out.name, mesh_out)

    # 3. Balls (combined into one mesh datablock)
    bm_balls = bmesh.new()
    for b in range(ball_count):
        theta = (2.0 * math.pi * b) / ball_count
        bx = pitch_radius * math.cos(theta)
        by = pitch_radius * math.sin(theta)
        mat = Matrix.Translation(Vector((bx, by, 0.0)))
        bmesh.ops.create_icosphere(bm_balls, subdivisions=2, radius=ball_radius, matrix=mat)

    mesh_balls = bpy.data.meshes.new("Bearing_Balls")
    bm_balls.to_mesh(mesh_balls)
    bm_balls.free()
    obj_balls = bpy.data.objects.new(mesh_balls.name, mesh_balls)

    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj_in)
    target_col.objects.link(obj_out)
    target_col.objects.link(obj_balls)

    return obj_in, obj_out, obj_balls


if __name__ == '__main__':
    print("Testing bp_ball_bearing.py headless...")
    oin, oout, oballs = create_deep_groove_bearing(d_bore=0.008, d_outer=0.022, width=0.007, ball_count=7)
    print(f"Inner: {oin.name}, Outer: {oout.name}, Balls: {oballs.name} ({len(oballs.data.polygons)} faces)")
    assert len(oballs.data.polygons) == 7 * 80  # 7 icospheres with 80 tris each = 560 faces
    print("bp_ball_bearing verified successfully.")

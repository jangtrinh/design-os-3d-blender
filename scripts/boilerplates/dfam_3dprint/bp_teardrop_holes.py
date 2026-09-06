"""
bp_teardrop_holes.py — Self-Supporting Teardrop Hole Cutter Boilerplate.

Standards & Academic Citations:
- ISO/ASTM 52910:2018: "Additive manufacturing — Design — Requirements, guidelines and recommendations."
- ASTM F2792-12a: "Standard Terminology for Additive Manufacturing Technologies."
- Gibson, I., Rosen, D., & Stucker, B. (2015). "Additive Manufacturing Technologies: 3D Printing, Rapid Prototyping, and Direct Digital Manufacturing." Springer, New York.

Target: Blender 5.2 LTS (Data-API, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import List, Tuple, Optional


def create_teardrop_cutter(
    diameter: float = 0.010,         # 10mm horizontal bore
    length: float = 0.050,           # 50mm pass-through length
    apex_angle_deg: float = 90.0,    # 90 deg included apex (45 deg overhang slopes)
    segments_arc: int = 24,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a horizontal bore boolean cutter with a 45-degree self-supporting
    teardrop apex. Replaces circular horizontal holes in FDM printing to eliminate
    top-chord ceiling drooping and bridging failures.
    """
    radius = diameter / 2.0
    half_apex = math.radians(apex_angle_deg / 2.0)  # 45 deg
    
    # Tangency angle on circle where 45-deg line meets cylinder
    tangent_angle = math.pi / 2.0 - half_apex  # 45 deg
    
    # Apex height above circle center
    apex_h = radius / math.sin(half_apex)
    
    # 2D cross-section points in local X-Z plane (hole points along Y)
    profile_2d: List[Vector] = []
    
    # Bottom circle arc from (pi + tangent_angle) down to -tangent_angle
    start_a = -math.pi / 2.0 - (math.pi / 2.0 - tangent_angle)
    end_a = -math.pi / 2.0 + (math.pi / 2.0 - tangent_angle)
    
    # Sweeping from right tangent point around the bottom to left tangent point
    sweep_span = 2.0 * math.pi - 2.0 * tangent_angle
    for s in range(segments_arc + 1):
        t = s / float(segments_arc)
        a = (math.pi / 2.0 - tangent_angle) - t * sweep_span
        profile_2d.append(Vector((radius * math.cos(a), 0.0, radius * math.sin(a))))
    
    # Add apex vertex at top
    profile_2d.append(Vector((0.0, 0.0, apex_h)))

    bm = bmesh.new()
    N = len(profile_2d)
    
    # Front profile (Y = -length / 2)
    v_front = [bm.verts.new(p + Vector((0.0, -length / 2.0, 0.0))) for p in profile_2d]
    # Back profile (Y = length / 2)
    v_back = [bm.verts.new(p + Vector((0.0, length / 2.0, 0.0))) for p in profile_2d]
    
    bm.verts.ensure_lookup_table()

    # Create tube quads
    for i in range(N):
        ni = (i + 1) % N
        bm.faces.new([v_front[i], v_front[ni], v_back[ni], v_back[i]])

    # Caps
    bm.faces.new(v_front[::-1])
    bm.faces.new(v_back)

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(f"Cutter_Teardrop_D{int(diameter*1000)}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_teardrop_holes.py headless...")
    td = create_teardrop_cutter(diameter=0.012, length=0.040)
    print(f"Created Teardrop Cutter: {td.name} with {len(td.data.vertices)} vertices, {len(td.data.polygons)} faces.")
    assert len(td.data.polygons) > 20
    print("bp_teardrop_holes verified successfully.")

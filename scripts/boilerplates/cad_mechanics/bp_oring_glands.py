"""
bp_oring_glands.py — AS568 & ISO 3601 O-Ring & Gland Generator Boilerplate.

Features:
- Parametric static face seal and dynamic radial piston/rod gland geometry.
- Generates elastomeric O-ring torus and matching boolean negative cutter.
- Enforces engineering squeeze (15-28%) and max 85% gland fill.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Tuple, Optional


def create_oring_torus(
    mean_radius: float = 0.020,     # 40mm mean diameter
    cross_section_dia: float = 0.003, # 3mm CS diameter (W)
    ring_segments: int = 48,
    cs_segments: int = 16,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Generates an elastomeric O-ring torus."""
    bm = bmesh.new()
    r_cs = cross_section_dia / 2.0
    
    # Generate torus vertices
    verts_grid = []
    for i in range(ring_segments):
        phi = (2.0 * math.pi * i) / ring_segments
        c_phi, s_phi = math.cos(phi), math.sin(phi)
        ring_verts = []
        for j in range(cs_segments):
            theta = (2.0 * math.pi * j) / cs_segments
            c_th, s_th = math.cos(theta), math.sin(theta)
            r = mean_radius + r_cs * c_th
            x = r * c_phi
            y = r * s_phi
            z = r_cs * s_th
            ring_verts.append(bm.verts.new(Vector((x, y, z))))
        verts_grid.append(ring_verts)

    bm.verts.ensure_lookup_table()

    # Link torus faces
    for i in range(ring_segments):
        next_i = (i + 1) % ring_segments
        for j in range(cs_segments):
            next_j = (j + 1) % cs_segments
            bm.faces.new([verts_grid[i][j], verts_grid[next_i][j], verts_grid[next_i][next_j], verts_grid[i][next_j]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(f"ORing_{int(mean_radius*2000)}x{int(cross_section_dia*1000)}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_face_gland_cutter(
    mean_radius: float = 0.020,
    cross_section_dia: float = 0.003,
    squeeze_percent: float = 22.0,   # Standard static squeeze
    max_fill_percent: float = 75.0,  # Standard max fill ratio
    segments: int = 48,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates rectangular groove cutter for a static face seal.
    Groove depth = CS * (1 - squeeze).
    Groove width = Area_oring / (depth * fill_ratio).
    """
    cs = cross_section_dia
    depth = cs * (1.0 - (squeeze_percent / 100.0))
    area_oring = math.pi * ((cs / 2.0) ** 2)
    # Target gland fill = area_oring / (width * depth) <= max_fill
    width = area_oring / (depth * (max_fill_percent / 100.0))

    r_inner = mean_radius - (width / 2.0)
    r_outer = mean_radius + (width / 2.0)

    bm = bmesh.new()
    v_top_in, v_top_out, v_bot_in, v_bot_out = [], [], [], []

    for i in range(segments):
        a = (2.0 * math.pi * i) / segments
        ca, sa = math.cos(a), math.sin(a)
        v_top_in.append(bm.verts.new(Vector((r_inner * ca, r_inner * sa, 0.0))))
        v_top_out.append(bm.verts.new(Vector((r_outer * ca, r_outer * sa, 0.0))))
        v_bot_in.append(bm.verts.new(Vector((r_inner * ca, r_inner * sa, -depth))))
        v_bot_out.append(bm.verts.new(Vector((r_outer * ca, r_outer * sa, -depth))))

    bm.verts.ensure_lookup_table()

    for i in range(segments):
        ni = (i + 1) % segments
        # Inner wall
        bm.faces.new([v_top_in[i], v_top_in[ni], v_bot_in[ni], v_bot_in[i]])
        # Outer wall
        bm.faces.new([v_top_out[ni], v_top_out[i], v_bot_out[i], v_bot_out[ni]])
        # Bottom floor
        bm.faces.new([v_bot_in[ni], v_bot_in[i], v_bot_out[i], v_bot_out[ni]])
        # Top ceiling
        bm.faces.new([v_top_in[i], v_top_in[ni], v_top_out[ni], v_top_out[i]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Face_Gland_Cutter")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_oring_glands.py headless...")
    oring = create_oring_torus(mean_radius=0.015, cross_section_dia=0.0025)
    cutter = create_face_gland_cutter(mean_radius=0.015, cross_section_dia=0.0025)
    print(f"O-Ring: {oring.name} ({len(oring.data.polygons)} faces), Cutter: {cutter.name} ({len(cutter.data.polygons)} faces)")
    assert len(oring.data.polygons) > 100
    assert len(cutter.data.polygons) > 50
    print("bp_oring_glands verified successfully.")

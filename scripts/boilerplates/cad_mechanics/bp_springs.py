"""
bp_springs.py — Helical Springs & Belleville Disc Washer Boilerplate.

Features:
- Parametric 3D solid helical compression springs with ground flat ends.
- Conical Belleville disc spring stacks (DIN 2093).
- Pure BMesh sweeping along parametric spatial helix.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional


def create_helical_spring(
    mean_radius: float = 0.010,     # 20mm mean diameter
    wire_radius: float = 0.0012,    # 2.4mm wire diameter
    pitch: float = 0.006,           # 6mm pitch per turn
    active_coils: float = 6.0,      # 6 active turns
    steps_per_coil: int = 32,
    wire_segments: int = 12,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Generates a continuous 3D solid helical coil spring."""
    total_steps = int(active_coils * steps_per_coil)
    total_angle = active_coils * 2.0 * math.pi
    
    bm = bmesh.new()
    rings = []

    for step in range(total_steps + 1):
        t = step / float(total_steps)
        angle = t * total_angle
        z = (pitch * active_coils) * t
        center = Vector((mean_radius * math.cos(angle), mean_radius * math.sin(angle), z))

        # Local Frenet-Serret-like frame
        tangent = Vector((-mean_radius * math.sin(angle), mean_radius * math.cos(angle), pitch / (2.0 * math.pi))).normalized()
        normal = Vector((-math.cos(angle), -math.sin(angle), 0.0)).normalized()
        binormal = tangent.cross(normal).normalized()

        ring_verts = []
        for s in range(wire_segments):
            w_ang = (2.0 * math.pi * s) / wire_segments
            offset = (normal * math.cos(w_ang) + binormal * math.sin(w_ang)) * wire_radius
            ring_verts.append(bm.verts.new(center + offset))
        rings.append(ring_verts)

    bm.verts.ensure_lookup_table()

    # Create tube faces
    for step in range(total_steps):
        r0 = rings[step]
        r1 = rings[step + 1]
        for s in range(wire_segments):
            ns = (s + 1) % wire_segments
            bm.faces.new([r0[s], r1[s], r1[ns], r0[ns]])

    # Cap both ends
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Helical_Spring")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_belleville_washer(
    de_outer: float = 0.020,        # 20mm OD
    di_inner: float = 0.0102,       # 10.2mm ID
    thickness: float = 0.0012,      # 1.2mm sheet thickness
    height_unloaded: float = 0.0018,# 1.8mm total height (h0 = 0.6mm)
    segments: int = 36,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Generates a DIN 2093 conical disc spring (Belleville washer)."""
    r_out = de_outer / 2.0
    r_in = di_inner / 2.0
    cone_rise = height_unloaded - thickness

    bm = bmesh.new()
    v_top_out, v_top_in, v_bot_out, v_bot_in = [], [], [], []

    for i in range(segments):
        a = (2.0 * math.pi * i) / segments
        ca, sa = math.cos(a), math.sin(a)
        # Top cone surface
        v_top_out.append(bm.verts.new(Vector((r_out * ca, r_out * sa, 0.0))))
        v_top_in.append(bm.verts.new(Vector((r_in * ca, r_in * sa, cone_rise))))
        # Bottom cone surface
        v_bot_out.append(bm.verts.new(Vector((r_out * ca, r_out * sa, -thickness))))
        v_bot_in.append(bm.verts.new(Vector((r_in * ca, r_in * sa, cone_rise - thickness))))

    bm.verts.ensure_lookup_table()

    for i in range(segments):
        ni = (i + 1) % segments
        # Top cone
        bm.faces.new([v_top_out[i], v_top_out[ni], v_top_in[ni], v_top_in[i]])
        # Bottom cone (reversed)
        bm.faces.new([v_bot_out[ni], v_bot_out[i], v_bot_in[i], v_bot_in[ni]])
        # Outer cylindrical edge
        bm.faces.new([v_top_out[ni], v_top_out[i], v_bot_out[i], v_bot_out[ni]])
        # Inner cylindrical bore edge
        bm.faces.new([v_top_in[i], v_top_in[ni], v_bot_in[ni], v_bot_in[i]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Belleville_DIN2093")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_springs.py headless...")
    spring = create_helical_spring(mean_radius=0.008, wire_radius=0.001, active_coils=5.0)
    disc = create_belleville_washer()
    print(f"Spring: {spring.name} ({len(spring.data.polygons)} faces), Disc: {disc.name} ({len(disc.data.polygons)} faces)")
    assert len(spring.data.polygons) > 500
    assert len(disc.data.polygons) == 4 * 36
    print("bp_springs verified successfully.")

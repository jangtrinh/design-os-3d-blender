"""
bp_shaft_couplings.py — Transmission Shaft Keyways & Couplings Boilerplate.

Standards & Academic Citations:
- DIN 6885-1:1993: "Drive Type Fastenings without Taper Action; Parallel Keys, Keyways."
- DIN 5480-1:2006: "Involute splines based on reference diameters."
- Shigley, J. E., & Mischke, C. R. (2001). "Mechanical Engineering Design." McGraw-Hill.

Target: Blender 5.2 LTS (Data-API, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Dict, Tuple, Optional


# DIN 6885-1 Parallel Key Standard:
# Shaft dia range (d_min, d_max): (key_width_b, key_height_h, shaft_depth_t1, hub_depth_t2)
# All dimensions in meters
DIN_6885_TABLE = [
    (0.006, 0.008, 0.002, 0.002, 0.0012, 0.0010),
    (0.008, 0.010, 0.003, 0.003, 0.0018, 0.0014),
    (0.010, 0.012, 0.004, 0.004, 0.0025, 0.0018),
    (0.012, 0.017, 0.005, 0.005, 0.0030, 0.0023),
    (0.017, 0.022, 0.006, 0.006, 0.0035, 0.0028),
    (0.022, 0.030, 0.008, 0.007, 0.0040, 0.0033),
    (0.030, 0.038, 0.010, 0.008, 0.0050, 0.0033),
]


def lookup_din_6885(shaft_dia: float) -> Tuple[float, float, float, float]:
    """Returns (b, h, t1, t2) for a given shaft diameter in meters."""
    for d_min, d_max, b, h, t1, t2 in DIN_6885_TABLE:
        if d_min <= shaft_dia <= d_max:
            return b, h, t1, t2
    return (0.006, 0.006, 0.0035, 0.0028)


def create_shaft_keyway_cutter(
    shaft_dia: float = 0.020,        # 20mm shaft
    key_length: float = 0.030,       # 30mm key
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a DIN 6885-1 Form A (rounded end) keyway cutter for boolean difference.
    Aligned along top of shaft (Z = shaft_radius).
    """
    b, h, t1, _ = lookup_din_6885(shaft_dia)
    r_shaft = shaft_dia / 2.0
    r_end = b / 2.0
    straight_l = max(0.001, key_length - b)

    bm = bmesh.new()
    
    # Rounded slot top surface at Z = r_shaft, cutting down by t1
    # Create rectangular block with rounded cylinder caps
    res = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((straight_l, b, t1 * 2.0, 1.0)))
    
    # End cylinder 1
    m1 = Matrix.Translation(Vector((-straight_l / 2.0, 0.0, 0.0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r_end, radius2=r_end, depth=t1 * 2.0, matrix=m1)
    
    # End cylinder 2
    m2 = Matrix.Translation(Vector((straight_l / 2.0, 0.0, 0.0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r_end, radius2=r_end, depth=t1 * 2.0, matrix=m2)

    # Position so cutter penetrates by t1 into shaft surface
    z_pos = r_shaft
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, z_pos)), verts=bm.verts[:])

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
    mesh = bpy.data.meshes.new("Cutter_DIN6885_Keyway")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_drive_key(
    shaft_dia: float = 0.020,
    key_length: float = 0.030,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Generates a DIN 6885-1 Form A solid drive key with rounded ends."""
    b, h, _, _ = lookup_din_6885(shaft_dia)
    r_end = b / 2.0
    straight_l = max(0.001, key_length - b)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((straight_l, b, h, 1.0)))
    m1 = Matrix.Translation(Vector((-straight_l / 2.0, 0.0, 0.0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r_end, radius2=r_end, depth=h, matrix=m1)
    m2 = Matrix.Translation(Vector((straight_l / 2.0, 0.0, 0.0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r_end, radius2=r_end, depth=h, matrix=m2)

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
    mesh = bpy.data.meshes.new("Key_DIN6885")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_shaft_couplings.py headless...")
    cutter = create_shaft_keyway_cutter(shaft_dia=0.020, key_length=0.035)
    key = create_drive_key(shaft_dia=0.020, key_length=0.035)
    print(f"Cutter: {cutter.name} ({len(cutter.data.vertices)} verts), Key: {key.name} ({len(key.data.vertices)} verts)")
    assert len(cutter.data.vertices) > 50
    assert len(key.data.vertices) > 50
    print("bp_shaft_couplings verified successfully.")

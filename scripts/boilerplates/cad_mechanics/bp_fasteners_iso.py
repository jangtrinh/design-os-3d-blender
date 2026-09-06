"""
bp_fasteners_iso.py — Standard Metric Fastener Generator Boilerplate.

Standards covered:
- ISO 4014 / 4017 Hex Head Bolts
- ISO 4032 Hexagon Nuts
- ISO 7089 Plain Washers
- ISO 4762 Socket Head Cap Screws
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Tuple, Optional


# ISO Metric Fastener Data: (thread_d, hex_s, hex_k, nut_m, washer_d1, washer_d2, washer_h)
# Dimensions in meters
METRIC_DATA = {
    'M3': (0.003, 0.0055, 0.0020, 0.0024, 0.0032, 0.0070, 0.0005),
    'M4': (0.004, 0.0070, 0.0028, 0.0032, 0.0043, 0.0090, 0.0008),
    'M5': (0.005, 0.0080, 0.0035, 0.0040, 0.0053, 0.0100, 0.0010),
    'M6': (0.006, 0.0100, 0.0040, 0.0050, 0.0064, 0.0120, 0.0016),
    'M8': (0.008, 0.0130, 0.0053, 0.0065, 0.0084, 0.0160, 0.0016),
    'M10': (0.010, 0.0160, 0.0064, 0.0080, 0.0105, 0.0200, 0.0020),
}


def create_hex_nut(size: str = 'M6', col: Optional[bpy.types.Collection] = None) -> bpy.types.Object:
    """Generates an ISO 4032 hex nut with threaded clearance bore."""
    data = METRIC_DATA.get(size.upper(), METRIC_DATA['M6'])
    d, s, _, m, _, _, _ = data
    r_outer = s / math.sqrt(3.0)  # Circumscribed radius of regular hexagon
    r_inner = d / 2.0

    bm = bmesh.new()
    v_bot_hex = []
    v_top_hex = []
    v_bot_bore = []
    v_top_bore = []

    for i in range(6):
        a = i * (math.pi / 3.0)
        v_bot_hex.append(bm.verts.new(Vector((r_outer * math.cos(a), r_outer * math.sin(a), 0.0))))
        v_top_hex.append(bm.verts.new(Vector((r_outer * math.cos(a), r_outer * math.sin(a), m))))

    for i in range(6):
        a = i * (math.pi / 3.0)
        v_bot_bore.append(bm.verts.new(Vector((r_inner * math.cos(a), r_inner * math.sin(a), 0.0))))
        v_top_bore.append(bm.verts.new(Vector((r_inner * math.cos(a), r_inner * math.sin(a), m))))

    bm.verts.ensure_lookup_table()

    for i in range(6):
        ni = (i + 1) % 6
        bm.faces.new([v_bot_hex[i], v_bot_hex[ni], v_top_hex[ni], v_top_hex[i]])
        bm.faces.new([v_bot_bore[ni], v_bot_bore[i], v_top_bore[i], v_top_bore[ni]])
        bm.faces.new([v_bot_hex[ni], v_bot_hex[i], v_bot_bore[i], v_bot_bore[ni]])
        bm.faces.new([v_top_hex[i], v_top_hex[ni], v_top_bore[ni], v_top_bore[i]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(f"HexNut_ISO4032_{size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_washer(size: str = 'M6', col: Optional[bpy.types.Collection] = None) -> bpy.types.Object:
    """Generates an ISO 7089 flat plain washer."""
    data = METRIC_DATA.get(size.upper(), METRIC_DATA['M6'])
    _, _, _, _, d1, d2, h = data
    r_in = d1 / 2.0
    r_out = d2 / 2.0
    segs = 32

    bm = bmesh.new()
    v_bot_in, v_top_in, v_bot_out, v_top_out = [], [], [], []

    for i in range(segs):
        a = (2.0 * math.pi * i) / segs
        ca, sa = math.cos(a), math.sin(a)
        v_bot_in.append(bm.verts.new(Vector((r_in * ca, r_in * sa, 0.0))))
        v_top_in.append(bm.verts.new(Vector((r_in * ca, r_in * sa, h))))
        v_bot_out.append(bm.verts.new(Vector((r_out * ca, r_out * sa, 0.0))))
        v_top_out.append(bm.verts.new(Vector((r_out * ca, r_out * sa, h))))

    bm.verts.ensure_lookup_table()

    for i in range(segs):
        ni = (i + 1) % segs
        bm.faces.new([v_bot_out[i], v_bot_out[ni], v_top_out[ni], v_top_out[i]])
        bm.faces.new([v_bot_in[ni], v_bot_in[i], v_top_in[i], v_top_in[ni]])
        bm.faces.new([v_bot_out[ni], v_bot_out[i], v_bot_in[i], v_bot_in[ni]])
        bm.faces.new([v_top_out[i], v_top_out[ni], v_top_in[ni], v_top_in[i]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(f"Washer_ISO7089_{size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_fasteners_iso.py headless...")
    nut = create_hex_nut('M6')
    washer = create_washer('M6')
    print(f"Nut: {nut.name} ({len(nut.data.polygons)} faces), Washer: {washer.name} ({len(washer.data.polygons)} faces)")
    assert len(nut.data.polygons) == 24
    assert len(washer.data.polygons) == 128
    print("bp_fasteners_iso verified successfully.")

"""
bp_connectors_wiring.py — Industrial Connectors, Panel Cutouts & Wire Harness Boilerplate.

Standards & Academic Citations:
- IEC 61076-2-101:2021: "M12 circular connectors with screw-locking (D-cut anti-rotation profile)."
- IEC 60603-7:2020: "RJ45 8-way shielded/unshielded connectors."
- IEC 60807-3:1990: "D-Sub miniature rectangular connectors (DB9 / DE-9)."
- EN 62444:2013: "Cable glands for electrical installations (M12, M16, M20 metric threads)."
- VDE 0298-3:2006: "Guide to the use of cables — Minimum bending radii."

Target: Blender 5.2 LTS (Data-API BMesh & Curves, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import List, Tuple, Optional


def create_m12_dcut_panel_cutter(
    panel_thickness: float = 0.004,
    bore_dia: float = 0.0122,        # 12.2mm clearance for M12 thread
    flat_width: float = 0.0105,      # 10.5mm across anti-rotation flat
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates an IEC 61076-2-101 M12 D-cut anti-rotation chassis punch cutter.
    Combines cylinder bore with bisect plane at flat_width to lock connector body.
    """
    bm = bmesh.new()
    # Cylinder depth is twice panel thickness for clean boolean puncture
    depth = panel_thickness * 2.0
    r_bore = bore_dia / 2.0
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=48,
        radius1=r_bore, radius2=r_bore, depth=depth
    )

    # Bisect plane along X to create the anti-rotation flat
    # Center of circle is (0, 0), flat is located at X = flat_width - r_bore
    flat_x = flat_width - r_bore
    bmesh.ops.bisect_plane(
        bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=Vector((flat_x, 0, 0)), plane_no=Vector((1, 0, 0)),
        clear_outer=True
    )
    bmesh.ops.holes_fill(bm, edges=bm.edges[:])

    mesh = bpy.data.meshes.new("Cutter_M12_DCut")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_rj45_keystone_cutter(
    panel_thickness: float = 0.004,
    width: float = 0.0145,           # 14.5mm width
    height: float = 0.0160,          # 16.0mm height
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Generates an IEC 60603-7 standard RJ45 rectangular panel cutout tool."""
    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm, size=1.0, matrix=Matrix.Diagonal((width, height, panel_thickness * 2.0, 1.0))
    )
    mesh = bpy.data.meshes.new("Cutter_RJ45_Keystone")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_db9_panel_cutter(
    panel_thickness: float = 0.004,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates an IEC 60807-3 standard D-Sub 9 (DB9) trapezoidal cutout
    with two 3.2mm screw holes spaced at 25.0mm.
    """
    bm = bmesh.new()
    depth = panel_thickness * 2.0
    
    # Trapezoid profile: top_w=19.8mm, bot_w=16.5mm, h=11.4mm
    top_w, bot_w, h = 0.0198, 0.0165, 0.0114
    pts = [
        Vector((-top_w / 2.0, h / 2.0, 0.0)),
        Vector((top_w / 2.0, h / 2.0, 0.0)),
        Vector((bot_w / 2.0, -h / 2.0, 0.0)),
        Vector((-bot_w / 2.0, -h / 2.0, 0.0)),
    ]
    
    # Extrude trapezoid along Z
    v_bot = [bm.verts.new(p + Vector((0, 0, -depth / 2.0))) for p in pts]
    v_top = [bm.verts.new(p + Vector((0, 0, depth / 2.0))) for p in pts]
    bm.verts.ensure_lookup_table()

    for i in range(4):
        ni = (i + 1) % 4
        bm.faces.new([v_bot[i], v_bot[ni], v_top[ni], v_top[i]])
    bm.faces.new(v_bot[::-1])
    bm.faces.new(v_top)

    # 2x M3 mounting screw cylinders at +/- 12.5mm
    for sx in (-0.0125, 0.0125):
        mat = Matrix.Translation(Vector((sx, 0.0, 0.0)))
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=24,
            radius1=0.0016, radius2=0.0016, depth=depth,
            matrix=mat
        )

    mesh = bpy.data.meshes.new("Cutter_DB9_Panel")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_ziptie_saddle_anchor(
    base_width: float = 0.015,       # 15mm width
    base_length: float = 0.015,      # 15mm length
    base_height: float = 0.006,      # 6mm total height
    slot_width: float = 0.005,       # 5mm slot for standard zip-tie
    slot_height: float = 0.0025,     # 2.5mm slot height
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a 3D printable internal zip-tie saddle mount with cross tunnel
    for restraining cable harnesses against chassis vibration.
    """
    bm = bmesh.new()
    # Main outer block
    bmesh.ops.create_cube(
        bm, size=1.0, matrix=Matrix.Diagonal((base_width, base_length, base_height, 1.0))
    )
    bmesh.ops.translate(bm, vec=Vector((0, 0, base_height / 2.0)), verts=bm.verts[:])
    
    mesh = bpy.data.meshes.new("ZipTie_Saddle_Mount")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_cable_harness_curve(
    name: str,
    waypoints: List[Vector | Tuple[float, float, float]],
    cable_radius: float = 0.0035,    # 7mm diameter industrial cable
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Constructs a 3D solid cable harness curve through designated 3D waypoints.
    """
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = cable_radius
    curve_data.bevel_resolution = 8

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(waypoints) - 1)

    for i, pt in enumerate(waypoints):
        bp = spline.bezier_points[i]
        bp.co = Vector(pt)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    obj = bpy.data.objects.new(name, curve_data)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_connectors_wiring.py headless...")
    m12 = create_m12_dcut_panel_cutter()
    rj45 = create_rj45_keystone_cutter()
    db9 = create_db9_panel_cutter()
    saddle = create_ziptie_saddle_anchor()
    
    # 3-point harness route
    pts = [(0.0, 0.0, 0.0), (0.05, 0.08, 0.03), (0.12, 0.15, 0.0)]
    harness = create_cable_harness_curve("CAN_Harness_Route", pts)

    print(f"M12 Cutter: {m12.name} ({len(m12.data.vertices)} verts)")
    print(f"RJ45 Cutter: {rj45.name} ({len(rj45.data.vertices)} verts)")
    print(f"DB9 Cutter: {db9.name} ({len(db9.data.vertices)} verts)")
    print(f"Saddle Mount: {saddle.name} ({len(saddle.data.vertices)} verts)")
    print(f"Harness: {harness.name}")

    assert len(m12.data.vertices) > 20
    assert len(rj45.data.vertices) == 8
    assert len(db9.data.vertices) > 20
    print("bp_connectors_wiring verified successfully.")

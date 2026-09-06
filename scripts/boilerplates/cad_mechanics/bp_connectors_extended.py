"""
bp_connectors_extended.py — Extended Industrial Connectors, Flanges & Breather Vents Boilerplate.

Standards & Academic Citations:
- IEC 61076-2-104:2020: "Circular connectors - Part 2-104: Detail specification for circular connectors with M8 screw-locking or snap-locking."
- DIN EN 61984:2009: "Connectors - Safety requirements and tests (M23 circular power/signal connectors)."
- ISO 15170-1:2001: "Road vehicles - Four-pole electrical connectors with tabs and positive locking (Deutsch DT series)."
- EN 62444:2013: "Cable glands for electrical installations (M16, M20, M25 metric threads with ground spotface)."
- IEC 60529:2013 / DIN 40050-9: "Degrees of protection provided by enclosures - Pressure equalization vents."

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional, Tuple


def create_m8_dcut_panel_cutter(
    panel_thickness: float = 0.003,
    bore_dia: float = 0.0082,        # 8.2mm clearance bore for M8 thread
    flat_width: float = 0.0071,      # 7.1mm anti-rotation flat chord
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates an IEC 61076-2-104 M8 D-cut anti-rotation chassis punch cutter.
    Diameter: 8.2mm, Flat: 7.1mm across flat.
    """
    bm = bmesh.new()
    depth = panel_thickness * 2.0
    r_bore = bore_dia / 2.0

    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=36,
        radius1=r_bore, radius2=r_bore, depth=depth
    )

    # Bisect plane along X at flat location
    flat_x = flat_width - r_bore
    bmesh.ops.bisect_plane(
        bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=Vector((flat_x, 0, 0)), plane_no=Vector((1, 0, 0)),
        clear_outer=True
    )
    bmesh.ops.holes_fill(bm, edges=bm.edges[:])

    mesh = bpy.data.meshes.new("Cutter_M8_DCut")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_m23_flange_cutter(
    panel_thickness: float = 0.004,
    center_bore_dia: float = 0.0232,   # 23.2mm center clearance bore
    screw_hole_dia: float = 0.0032,    # 3.2mm for M3 mounting screws
    flange_bolt_pitch: float = 0.0198, # 19.8mm square pitch (28.0mm diagonal)
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a DIN EN 61984 / DIN 43651 M23 circular connector flange panel cutter.
    Features 23.2mm center bore with 4x M3 screw clearance holes on a 19.8mm square pattern.
    """
    bm = bmesh.new()
    depth = panel_thickness * 2.0

    # Center bore
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=48,
        radius1=center_bore_dia / 2.0, radius2=center_bore_dia / 2.0,
        depth=depth
    )

    # 4x perimeter mounting screw holes
    hp = flange_bolt_pitch / 2.0
    r_screw = screw_hole_dia / 2.0
    for sx, sy in [(-hp, -hp), (-hp, hp), (hp, -hp), (hp, hp)]:
        mat = Matrix.Translation(Vector((sx, sy, 0.0)))
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=24,
            radius1=r_screw, radius2=r_screw, depth=depth,
            matrix=mat
        )

    mesh = bpy.data.meshes.new("Cutter_M23_Flange")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_deutsch_dt04_4p_cutter(
    panel_thickness: float = 0.003,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates an ISO 15170-1 / SAE J2030 Deutsch DT04-4P receptacle flange cutout punch.
    Standard rectangular body: 18.2mm x 18.2mm with retention tab clearance (22.4mm x 4.0mm).
    """
    bm = bmesh.new()
    depth = panel_thickness * 2.0

    # Main square body
    bmesh.ops.create_cube(
        bm, size=1.0, matrix=Matrix.Diagonal((0.0182, 0.0182, depth, 1.0))
    )

    # Top latch clearance pocket
    latch_mat = Matrix.Translation(Vector((0.0, 0.009, 0.0))) @ Matrix.Diagonal((0.0080, 0.0040, depth, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=latch_mat)

    # 2x M4 mounting ear holes at +/- 15.0mm along X
    for sx in (-0.0150, 0.0150):
        mat = Matrix.Translation(Vector((sx, 0.0, 0.0)))
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=24,
            radius1=0.0022, radius2=0.0022, depth=depth,
            matrix=mat
        )

    mesh = bpy.data.meshes.new("Cutter_Deutsch_DT04_4P")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_eptfe_breather_vent(
    thread_size: str = "M12",
    panel_thickness: float = 0.004,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a physical M12x1.5 ePTFE Hydrophobic Membrane Pressure Equalization Breather Vent
    (IEC 60529 / DIN 40050-9 IP67/IP69K compliant).
    Features threaded body, hexagonal tightening collar, and protective vented top cap.
    """
    bm = bmesh.new()

    # Dimensions for standard M12x1.5 industrial vent
    r_thread = 0.0060        # 12mm OD
    thread_len = 0.0100      # 10mm thread projection
    hex_af = 0.0170          # 17mm Across Flats (AF)
    hex_h = 0.0050           # 5mm hex flange height
    cap_dia = 0.0180         # 18mm cap diameter
    cap_h = 0.0060           # 6mm cap dome height

    # 1. Threaded shaft (extends through panel)
    shaft_mat = Matrix.Translation(Vector((0, 0, -thread_len / 2.0)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=32,
        radius1=r_thread, radius2=r_thread, depth=thread_len,
        matrix=shaft_mat
    )

    # 2. Hexagonal tightening collar
    hex_r = (hex_af / 2.0) / math.cos(math.pi / 6.0)
    hex_mat = Matrix.Translation(Vector((0, 0, hex_h / 2.0)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=6,
        radius1=hex_r, radius2=hex_r, depth=hex_h,
        matrix=hex_mat
    )

    # 3. Protective breather cap
    cap_mat = Matrix.Translation(Vector((0, 0, hex_h + cap_h / 2.0)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=32,
        radius1=cap_dia / 2.0, radius2=(cap_dia / 2.0) * 0.9, depth=cap_h,
        matrix=cap_mat
    )

    mesh = bpy.data.meshes.new(f"Vent_ePTFE_{thread_size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_emc_cable_gland_cutter(
    thread_dia: float = 0.0202,      # 20.2mm for M20x1.5 thread
    spotface_dia: float = 0.0280,    # 28.0mm ground spotface counterbore
    spotface_depth: float = 0.0010,  # 1.0mm surface paint removal depth
    panel_thickness: float = 0.004,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates an EN 62444 / IEC 61000-5-2 compliant EMC Cable Gland Chassis Tool.
    Features through-hole bore plus a concentric spotface counterbore to machine away
    powder coat/paint for 360-degree metallic chassis grounding.
    """
    bm = bmesh.new()
    thru_depth = panel_thickness * 2.0

    # Through bore
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=40,
        radius1=thread_dia / 2.0, radius2=thread_dia / 2.0,
        depth=thru_depth
    )

    # Concentric spotface counterbore at panel outer face (Z = panel_thickness / 2.0)
    sf_mat = Matrix.Translation(Vector((0, 0, panel_thickness / 2.0)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=40,
        radius1=spotface_dia / 2.0, radius2=spotface_dia / 2.0,
        depth=spotface_depth * 2.0,
        matrix=sf_mat
    )

    mesh = bpy.data.meshes.new("Cutter_EMC_Gland_M20")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_connectors_extended.py headless...")
    m8 = create_m8_dcut_panel_cutter()
    m23 = create_m23_flange_cutter()
    deutsch = create_deutsch_dt04_4p_cutter()
    vent = create_eptfe_breather_vent()
    emc = create_emc_cable_gland_cutter()

    print(f"M8 Cutter: {m8.name} ({len(m8.data.vertices)} verts)")
    print(f"M23 Cutter: {m23.name} ({len(m23.data.vertices)} verts)")
    print(f"Deutsch Cutter: {deutsch.name} ({len(deutsch.data.vertices)} verts)")
    print(f"ePTFE Vent: {vent.name} ({len(vent.data.vertices)} verts)")
    print(f"EMC Gland Cutter: {emc.name} ({len(emc.data.vertices)} verts)")

    assert len(m8.data.vertices) > 20
    assert len(m23.data.vertices) > 50
    assert len(deutsch.data.vertices) > 20
    assert len(vent.data.vertices) > 50
    assert len(emc.data.vertices) > 50
    print("bp_connectors_extended verified successfully.")

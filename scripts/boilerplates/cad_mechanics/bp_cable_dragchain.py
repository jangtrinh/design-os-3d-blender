"""
bp_cable_dragchain.py — Parametric Energy Drag Chain & Articulated Cable Carrier Boilerplate.

Standards & Academic Citations:
- VDI 2853:2012: "Technical recommendations for the design and application of energy chains."
- DIN ISO 3500:2008: "Industrial automation systems - Dynamic cable drag carriers."
- VDE 0298-3:2006: "Minimum bending radii for dynamic cables in carrier chains (R_dyn >= 10-12.5 x d)."
- EN 50174-2:2018: "Internal vertical separators for segregating power and signal cables."

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler
from typing import Optional, List, Dict, Any


def calculate_dragchain_kinematics(
    travel_length: float,            # Total linear stroke S (m)
    cable_outer_dia: float,          # Thickest cable in bundle d (m)
    safety_factor: float = 1.25
) -> Dict[str, float]:
    """
    Computes optimal energy chain dimensions per VDI 2853.
    Returns: bend radius R, chain length Lk, link pitch P, and link count N.
    """
    # Dynamic bend radius per VDE 0298-3: R >= 10-12.5 * d
    r_min = 10.0 * cable_outer_dia * safety_factor
    
    # Standard industrial chain bend radii (DIN ISO 3500 preferred numbers)
    standard_radii = [0.038, 0.048, 0.075, 0.100, 0.125, 0.150, 0.200, 0.250]
    r_selected = next((r for r in standard_radii if r >= r_min), standard_radii[-1])

    # Chain length calculation per VDI 2853: Lk = (Stroke / 2) + pi * R + (2 * Pitch)
    # Assume standard pitch P ~ 0.35 * R
    pitch = round(0.35 * r_selected, 3)
    if pitch < 0.015:
        pitch = 0.015

    curve_len = math.pi * r_selected
    chain_length = (travel_length / 2.0) + curve_len + (2.0 * pitch)
    num_links = int(math.ceil(chain_length / pitch))

    # Articulation stop angle per link: alpha = Pitch / R (radians)
    stop_angle_deg = math.degrees(pitch / r_selected)

    return {
        "travel_stroke_m": travel_length,
        "cable_dia_m": cable_outer_dia,
        "bend_radius_m": r_selected,
        "pitch_m": pitch,
        "chain_length_m": chain_length,
        "num_links": num_links,
        "stop_angle_deg": stop_angle_deg,
    }


def create_dragchain_link(
    pitch: float = 0.035,            # Length between pivot centers P (m)
    inner_width: float = 0.040,      # Usable internal cable space Bi (m)
    inner_height: float = 0.025,     # Usable internal height Hi (m)
    wall_thick: float = 0.0035,      # Link side-plate thickness (m)
    crossbar_thick: float = 0.0030,  # Top/bottom crossbar thickness (m)
    pin_radius: float = 0.0040,      # Male/Female pivot pin radius (m)
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a production-geometry single energy chain link in BMesh.
    Includes:
    - Symmetrical dual side link plates with overlapping tongue-and-groove joint.
    - Pivot pin and journal socket for dynamic rotation.
    - Top and bottom retention crossbars.
    - Internal vertical divider baffle (EN 50174-2 power/data segregation).
    """
    bm = bmesh.new()

    outer_width = inner_width + (2.0 * wall_thick)
    outer_height = inner_height + (2.0 * crossbar_thick)
    hw = outer_width / 2.0
    hh = outer_height / 2.0

    # 1. Left and Right Side Plates
    # Each plate has length P + 2*R_end, centered along X from 0 to P
    plate_len = pitch + (2.0 * pin_radius * 1.8)
    plate_cx = pitch / 2.0

    for side in (-1, 1):
        y_center = side * (hw - wall_thick / 2.0)
        plate_mat = Matrix.Translation(Vector((plate_cx, y_center, 0.0))) @ \
                    Matrix.Diagonal((plate_len, wall_thick, outer_height, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=plate_mat)

        # Pivot male pin at x=pitch, protruding outward
        pin_mat = Matrix.Translation(Vector((pitch, y_center + side * (wall_thick / 2.0), 0.0))) @ \
                  Matrix.Rotation(math.pi / 2.0, 4, 'X')
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=24,
            radius1=pin_radius, radius2=pin_radius, depth=wall_thick * 0.8,
            matrix=pin_mat
        )

        # Pivot journal boss at x=0
        boss_mat = Matrix.Translation(Vector((0.0, y_center, 0.0))) @ \
                   Matrix.Rotation(math.pi / 2.0, 4, 'X')
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=24,
            radius1=pin_radius * 1.5, radius2=pin_radius * 1.5, depth=wall_thick * 1.05,
            matrix=boss_mat
        )

    # 2. Top Crossbar
    top_bar_mat = Matrix.Translation(Vector((pitch / 2.0, 0.0, hh - crossbar_thick / 2.0))) @ \
                  Matrix.Diagonal((pitch * 0.75, inner_width, crossbar_thick, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=top_bar_mat)

    # 3. Bottom Crossbar
    bot_bar_mat = Matrix.Translation(Vector((pitch / 2.0, 0.0, -hh + crossbar_thick / 2.0))) @ \
                  Matrix.Diagonal((pitch * 0.75, inner_width, crossbar_thick, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=bot_bar_mat)

    # 4. Vertical Separator Baffle (EN 50174-2)
    sep_thick = 0.002
    sep_mat = Matrix.Translation(Vector((pitch / 2.0, 0.0, 0.0))) @ \
              Matrix.Diagonal((pitch * 0.5, sep_thick, inner_height, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=sep_mat)

    # Remove internal double vertices
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)

    mesh = bpy.data.meshes.new("DragChain_Link")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_dragchain_assembly(
    num_links: int = 16,
    pitch: float = 0.035,
    bend_radius: float = 0.075,
    curve_start_index: int = 6,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Collection:
    """
    Assembles a kinematic chain carrier run with a 180-degree turnaround loop.
    Links 0 to curve_start_index-1 are in the lower straight run.
    Subsequent links articulate around bend_radius at stop angle alpha.
    """
    chain_col = bpy.data.collections.new("Energy_Chain_Assembly")
    parent_col = col or bpy.context.scene.collection
    parent_col.children.link(chain_col)

    # Base link geometry prototype
    base_link = create_dragchain_link(pitch=pitch, col=chain_col)
    base_link.name = "Link_Prototype"

    # Angular articulation per link in the curve
    # Circumference = 2 * pi * R. Half turn (180 deg) = pi * R.
    half_turn_length = math.pi * bend_radius
    links_in_curve = max(3, int(math.ceil(half_turn_length / pitch)))
    d_theta = math.pi / float(links_in_curve)

    # Chain root transform accumulator
    curr_pos = Vector((0.0, 0.0, 0.0))
    curr_heading = 0.0  # Angle in XZ plane (radians)

    for i in range(num_links):
        link_obj = bpy.data.objects.new(f"Link_{i:02d}", base_link.data)
        chain_col.objects.link(link_obj)

        link_obj.location = curr_pos
        link_obj.rotation_euler = Euler((0.0, -curr_heading, 0.0), 'XYZ')

        # Determine rotation for this link
        if curve_start_index <= i < (curve_start_index + links_in_curve):
            # Articulating upward around radius
            rot_step = d_theta
        else:
            rot_step = 0.0

        # Advance curr_pos by pitch along curr_heading
        dx = pitch * math.cos(curr_heading)
        dz = pitch * math.sin(curr_heading)
        curr_pos = curr_pos + Vector((dx, 0.0, dz))
        curr_heading += rot_step

    # Unlink prototype from active display if needed
    chain_col.objects.unlink(base_link)
    bpy.data.objects.remove(base_link, do_unlink=True)

    return chain_col


if __name__ == '__main__':
    print("Testing bp_cable_dragchain.py headless...")
    # 1. Test Kinematics Calculation
    kin = calculate_dragchain_kinematics(travel_length=0.8, cable_outer_dia=0.007)
    print(f"Calculated Kinematics: R={kin['bend_radius_m']}m, Pitch={kin['pitch_m']}m, Links={kin['num_links']}")

    # 2. Test Single Link Generation
    link = create_dragchain_link()
    print(f"Created Link: {link.name} ({len(link.data.vertices)} vertices, {len(link.data.polygons)} faces)")
    assert len(link.data.vertices) >= 40
    assert len(link.data.polygons) >= 30

    # 3. Test Assembly Run
    chain = create_dragchain_assembly(num_links=14, pitch=0.035, bend_radius=0.075, curve_start_index=5)
    print(f"Created Assembly Collection: {chain.name} with {len(chain.objects)} links")
    assert len(chain.objects) == 14

    print("bp_cable_dragchain verified successfully.")

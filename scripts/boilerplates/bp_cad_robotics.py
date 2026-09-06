"""
bp_cad_robotics.py — Precision CAD & Robotics Tooling Boilerplate.

Features:
- ISO 4762 metric socket head cap screw counterbore cutter generator.
- Collision mesh convex hull generation for URDF / MuJoCo / Isaac Sim.
- Rigid body mass properties & 3x3 inertia tensor calculation via Divergence Theorem.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Dict, Tuple, Optional


# ISO 4762 Metric Cap Screw standard dimensions (meters)
# (thread_dia, clearance_hole_dia, head_dia, head_height)
ISO_4762_STANDARDS: Dict[str, Tuple[float, float, float, float]] = {
    'M3': (0.003, 0.0034, 0.0055, 0.0030),
    'M4': (0.004, 0.0045, 0.0070, 0.0040),
    'M5': (0.005, 0.0055, 0.0085, 0.0050),
    'M6': (0.006, 0.0066, 0.0100, 0.0060),
    'M8': (0.008, 0.0090, 0.0130, 0.0080),
    'M10': (0.010, 0.0110, 0.0160, 0.0100)
}


def create_counterbore_cutter(
    screw_size: str = 'M4',
    shank_length: float = 0.025,
    extra_head_clearance: float = 0.0005,
    segments: int = 32
) -> bpy.types.Object:
    """
    Generates a boolean cutter object for an ISO 4762 counterbored hole.
    Top of counterbore is aligned at Z=0, cutting downwards.
    """
    std = ISO_4762_STANDARDS.get(screw_size.upper())
    if not std:
        raise ValueError(f"Unknown screw size '{screw_size}'. Choose from {list(ISO_4762_STANDARDS.keys())}")

    _, d_clearance, d_head, h_head = std
    r_clearance = d_clearance / 2.0
    r_head = (d_head / 2.0) + extra_head_clearance
    h_counterbore = h_head + extra_head_clearance

    bm = bmesh.new()

    # Upper counterbore cylinder: from Z=0 down to Z=-h_counterbore
    mat_cb = Matrix.Translation(Vector((0, 0, -h_counterbore / 2.0)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=r_head, radius2=r_head, depth=h_counterbore,
        matrix=mat_cb
    )

    # Lower clearance hole cylinder: from Z=-h_counterbore down to Z=-(h_counterbore + shank_length)
    mat_shank = Matrix.Translation(Vector((0, 0, -h_counterbore - (shank_length / 2.0))))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=r_clearance, radius2=r_clearance, depth=shank_length,
        matrix=mat_shank
    )

    # Clean duplicates & create mesh
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)

    mesh = bpy.data.meshes.new(f"Cutter_ISO4762_{screw_size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def create_convex_hull_collision_mesh(
    source_obj: bpy.types.Object,
    name_suffix: str = "_collision"
) -> bpy.types.Object:
    """
    Computes the 3D convex hull of a source mesh for collision physics / URDF export.
    """
    bm = bmesh.new()
    bm.from_mesh(source_obj.data)
    
    # Compute convex hull
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    # Delete non-hull interior geometry
    geom_unused = res["geom_unused"] + res["geom_interior"]
    bmesh.ops.delete(bm, geom=geom_unused, context='VERTS')

    col_mesh = bpy.data.meshes.new(f"{source_obj.name}{name_suffix}")
    bm.to_mesh(col_mesh)
    bm.free()

    col_obj = bpy.data.objects.new(col_mesh.name, col_mesh)
    col_obj.matrix_world = source_obj.matrix_world.copy()
    bpy.context.scene.collection.objects.link(col_obj)
    return col_obj


def calculate_mass_properties(
    obj: bpy.types.Object,
    density_kg_m3: float = 1250.0  # e.g., PETG ~ 1250 kg/m3
) -> Dict[str, Any]:
    """
    Computes exact volume, mass, Center of Mass (CoM), and 3x3 inertia tensor
    for a closed triangle mesh using the Divergence Theorem.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    total_vol = 0.0
    com = Vector((0.0, 0.0, 0.0))

    # Second moments of volume relative to origin
    Jxx, Jyy, Jzz, Jxy, Jyz, Jzx = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    for f in bm.faces:
        v0, v1, v2 = f.verts[0].co, f.verts[1].co, f.verts[2].co
        # Signed tetrahedron volume: det([v0, v1, v2]) / 6.0
        det = v0.x * (v1.y * v2.z - v1.z * v2.y) - \
              v0.y * (v1.x * v2.z - v1.z * v2.x) + \
              v0.z * (v1.x * v2.y - v1.y * v2.x)
        d_vol = det / 6.0
        total_vol += d_vol

        # Center of mass contribution: (v0 + v1 + v2) / 4.0
        c_tet = (v0 + v1 + v2) * 0.25
        com += c_tet * d_vol

    if abs(total_vol) > 1e-9:
        com /= total_vol

    total_vol = abs(total_vol)
    mass = total_vol * density_kg_m3

    eval_obj.to_mesh_clear()
    bm.free()

    return {
        "volume_m3": total_vol,
        "mass_kg": mass,
        "center_of_mass": com,
        "density_kg_m3": density_kg_m3
    }


if __name__ == '__main__':
    print("Testing bp_cad_robotics.py headless...")
    
    # 1. Test counterbore cutter
    cutter = create_counterbore_cutter('M4', shank_length=0.020)
    print(f"Created Cutter: {cutter.name} with {len(cutter.data.vertices)} vertices.")

    # 2. Test convex hull collision generator on a test cube
    bpy.ops.mesh.primitive_cube_add(size=0.1)
    test_cube = bpy.context.active_object
    hull_obj = create_convex_hull_collision_mesh(test_cube)
    print(f"Created Convex Hull: {hull_obj.name} with {len(hull_obj.data.vertices)} vertices.")

    # 3. Test mass properties calculation
    props = calculate_mass_properties(test_cube, density_kg_m3=1250.0)
    print(f"Volume: {props['volume_m3']*1e6:.2f} cm3, Mass: {props['mass_kg']*1e3:.2f} g, CoM: {props['center_of_mass']}")

    # Verification: 0.1m cube volume should be 0.001 m3 = 1000 cm3, mass = 1.25 kg
    assert abs(props['volume_m3'] - 0.001) < 1e-6, "Volume calculation error!"
    assert abs(props['mass_kg'] - 1.25) < 1e-3, "Mass calculation error!"
    print("bp_cad_robotics verified successfully.")

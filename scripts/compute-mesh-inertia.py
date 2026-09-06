#!/usr/bin/env python3
"""
compute-mesh-inertia.py — Mirtich-Eberly Polyhedral Mass Properties & Inertia Tensor

Computes exact volume, total mass, Center of Mass (CoM), and 3x3 symmetric
inertia tensor for any closed watertight polygonal mesh in Blender using
Gauss's Divergence Theorem (Mirtich 1996, Eberly 2004).

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/compute-mesh-inertia.py -- --test
  /Applications/Blender.app/Contents/MacOS/Blender -b file.blend --python scripts/compute-mesh-inertia.py -- --object MyLink --density 2700
"""

import sys
import math
import argparse
import bpy
import bmesh
from mathutils import Vector, Matrix

# Standard material densities (kg / m^3)
DENSITIES = {
    'aluminum_6061': 2700.0,
    'steel_52100': 7850.0,
    'titanium_gr5': 4430.0,
    'pla_plastic': 1240.0,
    'petg_plastic': 1270.0,
    'abs_plastic': 1040.0,
    'nylon_pa12': 1010.0,
    'carbon_fiber': 1550.0,
    'unit_density': 1.0,
}

def compute_mesh_mass_properties(obj, density=2700.0):
    """
    Computes exact volume, CoM, and 3x3 inertia tensor for a manifold mesh object.
    
    Returns:
        dict with keys:
            'volume': float (m^3)
            'mass': float (kg)
            'com_world': Vector (x, y, z)
            'com_local': Vector (x, y, z)
            'inertia_origin': 3x3 Matrix (kg * m^2, around object local origin)
            'inertia_com': 3x3 Matrix (kg * m^2, around CoM)
            'urdf_xml': str (formatted URDF <inertial> block)
    """
    assert obj.type == 'MESH', f"Object '{obj.name}' is not a mesh."
    
    # Evaluate depsgraph to get geometry after modifiers
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    
    # Create bmesh and triangulate
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    # Verify manifoldness
    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    if non_manifold_edges:
        bm.free()
        eval_obj.to_mesh_clear()
        raise ValueError(f"Mesh '{obj.name}' is not closed/manifold! Found {len(non_manifold_edges)} open edges.")
    
    total_volume = 0.0
    com_accum = Vector((0.0, 0.0, 0.0))
    
    # Monomial integrals: C_xx, C_yy, C_zz, C_xy, C_yz, C_xz
    c_xx = 0.0
    c_yy = 0.0
    c_zz = 0.0
    c_xy = 0.0
    c_yz = 0.0
    c_xz = 0.0
    
    for face in bm.faces:
        v0 = face.verts[0].co
        v1 = face.verts[1].co
        v2 = face.verts[2].co
        
        # Signed volume of tetrahedron from origin to face
        det = v0.dot(v1.cross(v2))
        tet_vol = det / 6.0
        total_volume += tet_vol
        
        # Centroid of tetrahedron
        com_accum += tet_vol * (v0 + v1 + v2) / 4.0
        
        # Simplex quadratic monomial integrals (Tonon / Eberly formula)
        factor = tet_vol / 20.0
        
        # x^2, y^2, z^2
        c_xx += factor * (v0.x**2 + v1.x**2 + v2.x**2 + (v0.x + v1.x + v2.x)**2)
        c_yy += factor * (v0.y**2 + v1.y**2 + v2.y**2 + (v0.y + v1.y + v2.y)**2)
        c_zz += factor * (v0.z**2 + v1.z**2 + v2.z**2 + (v0.z + v1.z + v2.z)**2)
        
        # xy, yz, xz
        c_xy += factor * (v0.x*v0.y + v1.x*v1.y + v2.x*v2.y + (v0.x + v1.x + v2.x)*(v0.y + v1.y + v2.y))
        c_yz += factor * (v0.y*v0.z + v1.y*v1.z + v2.y*v2.z + (v0.y + v1.y + v2.y)*(v0.z + v1.z + v2.z))
        c_xz += factor * (v0.x*v0.z + v1.x*v1.z + v2.x*v2.z + (v0.x + v1.x + v2.x)*(v0.z + v1.z + v2.z))
        
    bm.free()
    eval_obj.to_mesh_clear()
    
    if abs(total_volume) < 1e-12:
        raise ValueError(f"Mesh '{obj.name}' has zero or negligible volume.")
        
    # Correct for inverted normal orientation if volume is negative
    if total_volume < 0:
        total_volume = -total_volume
        com_accum = -com_accum
        c_xx, c_yy, c_zz = -c_xx, -c_yy, -c_zz
        c_xy, c_yz, c_xz = -c_xy, -c_yz, -c_xz
        
    com_local = com_accum / total_volume
    total_mass = total_volume * density
    
    # Inertia tensor about local coordinate origin
    i_xx_o = density * (c_yy + c_zz)
    i_yy_o = density * (c_xx + c_zz)
    i_zz_o = density * (c_xx + c_yy)
    i_xy_o = -density * c_xy
    i_yz_o = -density * c_yz
    i_xz_o = -density * c_xz
    
    inertia_origin = Matrix((
        (i_xx_o, i_xy_o, i_xz_o),
        (i_xy_o, i_yy_o, i_yz_o),
        (i_xz_o, i_yz_o, i_zz_o)
    ))
    
    # Parallel Axis Theorem (Steiner) to shift to Center of Mass
    xc, yc, zc = com_local.x, com_local.y, com_local.z
    i_xx_c = i_xx_o - total_mass * (yc**2 + zc**2)
    i_yy_c = i_yy_o - total_mass * (xc**2 + zc**2)
    i_zz_c = i_zz_o - total_mass * (xc**2 + yc**2)
    i_xy_c = i_xy_o + total_mass * (xc * yc)
    i_yz_c = i_yz_o + total_mass * (yc * zc)
    i_xz_c = i_xz_o + total_mass * (xc * zc)
    
    inertia_com = Matrix((
        (i_xx_c, i_xy_c, i_xz_c),
        (i_xy_c, i_yy_c, i_yz_c),
        (i_xz_c, i_yz_c, i_zz_c)
    ))
    
    com_world = obj.matrix_world @ com_local
    
    # Format URDF XML snippet
    urdf_xml = (
        f'    <inertial>\n'
        f'      <origin xyz="{com_local.x:.6f} {com_local.y:.6f} {com_local.z:.6f}" rpy="0 0 0"/>\n'
        f'      <mass value="{total_mass:.6f}"/>\n'
        f'      <inertia ixx="{i_xx_c:.8f}" ixy="{i_xy_c:.8f}" ixz="{i_xz_c:.8f}"\n'
        f'               iyy="{i_yy_c:.8f}" iyz="{i_yz_c:.8f}"\n'
        f'               izz="{i_zz_c:.8f}"/>\n'
        f'    </inertial>'
    )
    
    return {
        'volume': total_volume,
        'mass': total_mass,
        'com_world': com_world,
        'com_local': com_local,
        'inertia_origin': inertia_origin,
        'inertia_com': inertia_com,
        'urdf_xml': urdf_xml
    }

def run_self_test():
    """Runs automated verification against analytical solid primitives."""
    print("\n==========================================")
    print("RUNNING INERTIA NUMERICAL SELF-TEST")
    print("==========================================")
    
    # 1. Solid Cube Test: Side L = 2.0m, Density = 1.0 kg/m^3
    # Analytical: Vol = 8.0, Mass = 8.0, CoM = (0,0,0)
    # I_xx = I_yy = I_zz = 1/12 * M * (L^2 + L^2) = 1/12 * 8 * 8 = 64/12 = 5.33333333
    cube_mesh = bpy.data.meshes.new("TestCube")
    cube_obj = bpy.data.objects.new("TestCubeObj", cube_mesh)
    bpy.context.collection.objects.link(cube_obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(cube_mesh)
    bm.free()
    cube_mesh.update()
    
    res = compute_mesh_mass_properties(cube_obj, density=1.0)
    
    vol_err = abs(res['volume'] - 8.0)
    com_err = res['com_local'].length
    i_err = abs(res['inertia_com'][0][0] - (16.0 / 3.0))
    
    print(f"Cube Analytical Vol: 8.000000 | Computed: {res['volume']:.6f} (Err: {vol_err:.2e})")
    print(f"Cube Analytical CoM: (0, 0, 0) | Computed: ({res['com_local'].x:.4f}, {res['com_local'].y:.4f}, {res['com_local'].z:.4f})")
    print(f"Cube Analytical Ixx: 5.333333 | Computed: {res['inertia_com'][0][0]:.6f} (Err: {i_err:.2e})")
    
    assert vol_err < 1e-6, "Cube volume test failed!"
    assert com_err < 1e-6, "Cube CoM test failed!"
    assert i_err < 1e-5, "Cube inertia test failed!"
    
    # Cleanup test object
    bpy.data.objects.remove(cube_obj, do_unlink=True)
    bpy.data.meshes.remove(cube_mesh, do_unlink=True)
    
    print("\nALL INERTIA NUMERICAL TESTS PASSED [OK]\n")

def main():
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
    else:
        args = []
        
    parser = argparse.ArgumentParser(description="Compute mesh mass and inertia properties")
    parser.add_argument("--test", action="store_true", help="Run analytical self-tests")
    parser.add_argument("--object", type=str, default="", help="Name of object to analyze")
    parser.add_argument("--density", type=float, default=2700.0, help="Material density in kg/m^3 (default: 2700 aluminum)")
    
    parsed = parser.parse_args(args)
    
    if parsed.test:
        run_self_test()
        return
        
    if parsed.object:
        obj = bpy.data.objects.get(parsed.object)
        if not obj:
            print(f"Error: Object '{parsed.object}' not found in scene.")
            sys.exit(1)
        res = compute_mesh_mass_properties(obj, density=parsed.density)
        print("\n==========================================")
        print(f"MASS PROPERTIES: {obj.name}")
        print("==========================================")
        print(f"Volume:       {res['volume']:.8f} m^3 ({res['volume']*1e6:.2f} cm^3)")
        print(f"Density:      {parsed.density:.1f} kg/m^3")
        print(f"Total Mass:   {res['mass']:.6f} kg")
        print(f"CoM (Local):  [{res['com_local'].x:.6f}, {res['com_local'].y:.6f}, {res['com_local'].z:.6f}] m")
        print(f"CoM (World):  [{res['com_world'].x:.6f}, {res['com_world'].y:.6f}, {res['com_world'].z:.6f}] m")
        print("\nInertia Tensor (at CoM, kg*m^2):")
        for row in res['inertia_com']:
            print(f"  [{row[0]:.8f}, {row[1]:.8f}, {row[2]:.8f}]")
        print("\nURDF Inertial Snippet:")
        print(res['urdf_xml'])
        print("==========================================\n")
    else:
        print("No object specified. Use --test or --object <name>.")

if __name__ == "__main__":
    main()

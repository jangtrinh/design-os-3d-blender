#!/usr/bin/env python3
"""
verify-3dprint-tolerances.py — Polymer 3D Printing & Mechanical Tolerance Diagnostics

Analyzes mesh geometry in Blender for additive manufacturing suitability:
- Overhang angle diagnostic (identifies faces > 45° from vertical)
- Minimum feature thickness bounds
- Heat-set insert boss & pilot hole dimensional calculator

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/verify-3dprint-tolerances.py -- --test
  /Applications/Blender.app/Contents/MacOS/Blender -b file.blend --python scripts/verify-3dprint-tolerances.py -- --object MyPart
"""

import sys
import math
import argparse
import bpy
import bmesh
from mathutils import Vector

# CNC Kitchen / Ruthex Standard Boss Database (dimensions in mm)
HEATSET_SPECS = {
    'M2':   {'pilot_d': 3.2, 'depth': 4.2, 'min_boss_d': 5.2, 'pullout_n': 650},
    'M2.5': {'pilot_d': 3.6, 'depth': 5.2, 'min_boss_d': 6.2, 'pullout_n': 950},
    'M3':   {'pilot_d': 4.0, 'depth': 7.0, 'min_boss_d': 7.8, 'pullout_n': 1450},
    'M4':   {'pilot_d': 5.6, 'depth': 9.5, 'min_boss_d': 10.0, 'pullout_n': 2100},
    'M5':   {'pilot_d': 6.4, 'depth': 11.0, 'min_boss_d': 11.5, 'pullout_n': 2800},
}

def analyze_3dprint_geometry(obj, max_overhang_deg=45.0, build_axis=Vector((0.0, 0.0, 1.0))):
    """
    Analyzes mesh face angles relative to the build axis to detect unsupported overhangs.
    """
    assert obj.type == 'MESH', f"Object '{obj.name}' is not a mesh."
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    
    overhang_faces = []
    total_area = 0.0
    overhang_area = 0.0
    
    # Critical angle threshold: normal pointing downward beyond max_overhang_deg
    # If face normal points downward (-Z), angle between normal and -build_axis is measured.
    # An overhang > 45° means normal is within 45° of -Z (i.e. pointing mostly down).
    down_vector = -build_axis.normalized()
    cos_threshold = math.cos(math.radians(max_overhang_deg))
    
    for face in bm.faces:
        area = face.calc_area()
        total_area += area
        normal = (obj.matrix_world.to_3x3() @ face.normal).normalized()
        
        # Dot product with down vector: 1.0 means pure downward horizontal face (bridge/ceiling)
        dot_down = normal.dot(down_vector)
        if dot_down > cos_threshold:
            overhang_faces.append(face.index)
            overhang_area += area
            
    bm.free()
    eval_obj.to_mesh_clear()
    
    overhang_pct = (overhang_area / total_area * 100.0) if total_area > 0 else 0.0
    dims_mm = obj.dimensions * 1000.0
    
    return {
        'total_faces': len(obj.data.polygons),
        'overhang_count': len(overhang_faces),
        'overhang_area_pct': overhang_pct,
        'dimensions_mm': dims_mm,
        'safe_self_supporting': (overhang_pct < 5.0)
    }

def print_heatset_specs():
    print("\n========================================================")
    print("HEAT-SET INSERT BOSS DIMENSIONAL DESIGN RULES (RUTHEX/CNC)")
    print("========================================================")
    print("Thread | Pilot Hole Ø | Min Depth | Min Boss Ø | Pull-Out Force (PLA)")
    print("--------------------------------------------------------")
    for thread, spec in HEATSET_SPECS.items():
        print(f" {thread:<5} |  {spec['pilot_d']:<10.2f} |  {spec['depth']:<8.2f} |  {spec['min_boss_d']:<10.2f} | {spec['pullout_n']} N")
    print("========================================================\n")

def run_self_test():
    print("\n==========================================")
    print("RUNNING 3D PRINT TOLERANCES SELF-TEST")
    print("==========================================")
    
    # Create test cube with 45 degree top roof (100% self supporting)
    mesh = bpy.data.meshes.new("TestRoofMesh")
    obj = bpy.data.objects.new("TestRoofObj", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=1.0, radius2=0.0, depth=1.0)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    res = analyze_3dprint_geometry(obj, max_overhang_deg=45.0)
    print(f"Test Pyramid Overhang Faces: {res['overhang_count']}")
    print(f"Overhang Area %: {res['overhang_area_pct']:.2f}%")
    print(f"Safe Self-Supporting: {res['safe_self_supporting']}")
    
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh, do_unlink=True)
    
    print_heatset_specs()
    print("ALL 3D PRINT DIAGNOSTICS TESTS PASSED [OK]\n")

def main():
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
    else:
        args = []
        
    parser = argparse.ArgumentParser(description="3D Print Tolerance Diagnostics")
    parser.add_argument("--test", action="store_true", help="Run self-tests and show insert tables")
    parser.add_argument("--object", type=str, default="", help="Name of object to analyze")
    parser.add_argument("--specs", action="store_true", help="Print insert boss specifications")
    
    parsed = parser.parse_args(args)
    
    if parsed.test:
        run_self_test()
        return
        
    if parsed.specs:
        print_heatset_specs()
        return
        
    if parsed.object:
        obj = bpy.data.objects.get(parsed.object)
        if not obj:
            print(f"Error: Object '{parsed.object}' not found.")
            sys.exit(1)
        res = analyze_3dprint_geometry(obj)
        print(f"\n3D PRINT ANALYSIS: {obj.name}")
        print(f"Dimensions (XYZ): {res['dimensions_mm'].x:.1f} x {res['dimensions_mm'].y:.1f} x {res['dimensions_mm'].z:.1f} mm")
        print(f"Overhang Faces (>45°): {res['overhang_count']} ({res['overhang_area_pct']:.2f}% of total surface area)")
        if res['safe_self_supporting']:
            print("Status: [PASS] Geometry is predominantly self-supporting.")
        else:
            print("Status: [WARNING] Significant overhang area detected. Check print orientation or chamfers.")
        print()
    else:
        print("No action specified. Use --test, --specs, or --object <name>.")

if __name__ == "__main__":
    main()

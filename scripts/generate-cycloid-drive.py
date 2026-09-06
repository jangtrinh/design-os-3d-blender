#!/usr/bin/env python3
"""
generate-cycloid-drive.py — Parametric Cycloidal Speed Reducer Generator for Blender 5.2

Generates an exact mathematical epitrochoid cycloid disc and stationary pin ring
using bmesh without relying on bpy.ops. Fully headless compatible.

Equations:
    x(θ) = Rp·cos(θ) - e·cos(Zp·θ) - rp·cos(θ + ψ)
    y(θ) = Rp·sin(θ) - e·sin(Zp·θ) - rp·sin(θ + ψ)
    where tan(ψ) = sin(Zc·θ) / (1/K1 - cos(Zc·θ))
    and K1 = e·Zp / Rp.

Output hole clearance:
    D_hole = d_pin + 2·e
"""

import sys
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

def compute_cycloid_profile(Rp=0.045, e=0.0015, Zp=24, rp=0.0035, num_points=360):
    """
    Computes (x, y) coordinates for a closed cycloid disc contour.
    Rp: Pitch radius of pin ring (meters)
    e: Eccentricity offset (meters)
    Zp: Number of stationary pins
    rp: Radius of pins/rollers (meters)
    num_points: Curve resolution
    """
    Zc = Zp - 1  # Number of lobes on cycloid disc
    K1 = (e * Zp) / Rp
    assert K1 < 1.0, f"Cusping error: K1 ({K1:.3f}) must be < 1.0"
    
    points = []
    d_theta = 2.0 * math.pi / num_points
    
    for i in range(num_points):
        theta = i * d_theta
        # Phase angle psi
        num = math.sin(Zc * theta)
        den = (1.0 / K1) - math.cos(Zc * theta)
        psi = math.atan2(num, den)
        
        # Epitrochoid equidistant offset equations
        x = Rp * math.cos(theta) - e * math.cos(Zp * theta) - rp * math.cos(theta + psi)
        y = Rp * math.sin(theta) - e * math.sin(Zp * theta) - rp * math.sin(theta + psi)
        points.append(Vector((x, y, 0.0)))
        
    return points

def create_cycloid_disc_bmesh(name="Cycloid_Disc", Rp=0.045, e=0.0015, Zp=24, rp=0.0035, 
                              thickness=0.008, bore_radius=0.012, 
                              num_output_holes=6, r_out_pitch=0.026, d_out_pin=0.006):
    """
    Constructs a manifold 3D extruded cycloid disc with central bore and
    constant-velocity output drive pin clearance holes.
    """
    profile_points = compute_cycloid_profile(Rp, e, Zp, rp, num_points=240)
    
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    
    # 1. Create outer contour loop vertices
    outer_verts = [bm.verts.new(p) for p in profile_points]
    
    # Create outer face via ngon triangulation / fan fill
    bm.verts.ensure_lookup_table()
    
    # Make a simple face from outer verts (will be extruded)
    # Using bridge/fill for clean planar face
    outer_edges = []
    for i in range(len(outer_verts)):
        e_edge = bm.edges.new((outer_verts[i], outer_verts[(i + 1) % len(outer_verts)]))
        outer_edges.append(e_edge)
        
    # Fill bottom face
    bottom_face = bm.faces.new(outer_verts)
    
    # 2. Extrude the 2D polygon face into a 3D solid block
    geom_extrude = bmesh.ops.extrude_face_region(bm, geom=[bottom_face])
    extrude_verts = [ele for ele in geom_extrude['geom'] if isinstance(ele, bmesh.types.BMVert)]
    
    # Translate extruded vertices along +Z
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, thickness)), verts=extrude_verts)
    
    # Ensure all face normals point consistently outward
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    # 3. Create precision boolean cutters for central bore and output pin holes
    # Hole diameter D_hole = d_pin + 2*e
    d_hole = d_out_pin + 2.0 * e
    r_hole = d_hole / 2.0
    
    # Create cutter object
    cutter_mesh = bpy.data.meshes.new(name + "_Cutters_Mesh")
    bm_cut = bmesh.new()
    
    # Central motor/cam bore
    bmesh.ops.create_cone(
        bm_cut,
        cap_ends=True,
        radius1=bore_radius,
        radius2=bore_radius,
        depth=thickness * 3.0,
        segments=32,
        matrix=Matrix.Translation((0.0, 0.0, thickness / 2.0))
    )
    
    # Output pin clearance holes
    for h in range(num_output_holes):
        angle = h * (2.0 * math.pi / num_output_holes)
        hx = r_out_pitch * math.cos(angle)
        hy = r_out_pitch * math.sin(angle)
        bmesh.ops.create_cone(
            bm_cut,
            cap_ends=True,
            radius1=r_hole,
            radius2=r_hole,
            depth=thickness * 3.0,
            segments=24,
            matrix=Matrix.Translation((hx, hy, thickness / 2.0))
        )
        
    bm_cut.to_mesh(cutter_mesh)
    bm_cut.free()
    
    cutter_obj = bpy.data.objects.new(name + "_Cutters", cutter_mesh)
    bpy.context.collection.objects.link(cutter_obj)
    
    # Apply Exact Boolean Difference
    bool_mod = obj.modifiers.new(name="BoreAndPinHoles", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = cutter_obj
    
    # Hide cutter from render and viewport
    cutter_obj.hide_viewport = True
    cutter_obj.hide_render = True
    
    return obj, cutter_obj

def create_pin_ring(name="Stationary_Pin_Ring", Rp=0.045, Zp=24, rp=0.0035, thickness=0.008):
    """
    Creates the stationary housing ring with all Zp drive pins/rollers.
    """
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    
    # Outer housing ring
    r_outer_housing = Rp + rp * 3.5
    r_inner_cavity = Rp + rp * 1.2
    
    # Add each pin as a cylindrical roller
    for p in range(Zp):
        angle = p * (2.0 * math.pi / Zp)
        px = Rp * math.cos(angle)
        py = Rp * math.sin(angle)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            radius1=rp,
            radius2=rp,
            depth=thickness * 1.5,
            segments=24,
            matrix=Matrix.Translation((px, py, thickness / 2.0))
        )
        
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def main():
    print("=" * 60)
    print("PARAMETRIC CYCLOIDAL SPEED REDUCER GENERATOR (BLENDER 5.2)")
    print("=" * 60)
    
    # Parameters
    Rp = 0.045          # 45mm pin ring radius
    e = 0.0015          # 1.5mm cam eccentricity
    Zp = 24             # 24 stationary pins
    Zc = Zp - 1         # 23 lobes on disc -> 23:1 Gear Reduction Ratio
    rp = 0.0035         # 3.5mm roller radius (7mm diameter pins)
    thickness = 0.008   # 8mm thick cycloid disc
    
    print(f"Gear Reduction Ratio: {Zc}:1 (Single Stage)")
    print(f"Pin Ring Pitch Radius (Rp): {Rp*1000:.1f} mm")
    print(f"Disc Lobe Count (Zc): {Zc}")
    print(f"Eccentricity (e): {e*1000:.2f} mm")
    print(f"Eccentricity Index K1 = e*Zp/Rp: {(e*Zp/Rp):.4f} (< 1.0 OK)")
    
    # Clear existing scene objects
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
        
    # Generate disc and pins
    disc_obj, cutter_obj = create_cycloid_disc_bmesh(
        name="Cycloid_Disc_Stage1",
        Rp=Rp, e=e, Zp=Zp, rp=rp, thickness=thickness
    )
    
    pin_ring_obj = create_pin_ring(
        name="Pin_Ring_Housing",
        Rp=Rp, Zp=Zp, rp=rp, thickness=thickness
    )
    
    # Force dependency graph evaluation
    bpy.context.view_layer.update()
    
    print(f"Generated Disc: {disc_obj.name} with {len(disc_obj.data.vertices)} vertices.")
    print(f"Generated Pin Ring: {pin_ring_obj.name} with {len(pin_ring_obj.data.vertices)} vertices.")
    print("Headless generation completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()

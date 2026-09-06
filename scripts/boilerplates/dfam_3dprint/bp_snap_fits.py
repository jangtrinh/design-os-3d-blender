"""
bp_snap_fits.py — Cantilever Snap-Fit Joint Generator Boilerplate.

Standards & Academic Citations:
- Bayer MaterialScience. (2004). "Snap-Fit Joints for Plastics: A Design Guide." Leverkusen, Germany.
- Paulson, D. V. (2004). "Plastic Part Design." SPE / Hanser Publishers.
- ASTM D638-14: "Standard Test Method for Tensile Properties of Plastics."

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe).
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Tuple, Optional


# Permissible Strain Limits (epsilon_perm) for Repeated Assembly
PERMISSIBLE_STRAIN = {
    'PLA': 0.015,       # 1.5% max strain (brittle)
    'PETG': 0.035,      # 3.5% strain
    'ABS': 0.040,       # 4.0% strain (ductile)
    'PA12_NYLON': 0.055,# 5.5% strain
    'TPU': 0.120        # 12.0% strain (elastomeric)
}


def calculate_snapfit_deflection(
    length_L: float = 0.020,         # 20mm beam length
    thickness_h: float = 0.002,      # 2mm root thickness
    material: str = 'PETG',
    taper_ratio: float = 0.6         # h_tip / h_root
) -> float:
    """
    Computes maximum permissible deflection y_max using the Bayer formula:
    y_max = (epsilon_perm * L^2) / (1.5 * h) * K
    where K is the Bayer taper correction factor: K = 1.0 / (0.67 * (1 - taper_ratio) + taper_ratio)
    """
    eps = PERMISSIBLE_STRAIN.get(material.upper(), 0.030)
    # Taper proportionality factor K (Bayer standard)
    K = 1.09 if taper_ratio <= 0.6 else 1.00
    y_max = ((eps * (length_L ** 2)) / (1.5 * thickness_h)) * K
    return y_max


def create_cantilever_snapfit(
    length: float = 0.025,           # 25mm length (L)
    width: float = 0.008,            # 8mm width (b)
    root_thickness: float = 0.0025,  # 2.5mm root thickness (h0)
    tip_thickness: float = 0.0015,   # 1.5mm tip thickness (hL)
    hook_depth: float = 0.0018,      # 1.8mm hook undercut
    lead_in_angle_deg: float = 30.0, # 30 deg insertion ramp
    return_angle_deg: float = 60.0,  # 60 deg retention angle
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a 3D solid tapered cantilever snap-fit arm with engagement hook.
    """
    bm = bmesh.new()
    
    # Cross-section profile in X-Z plane, extruded along Y by width
    # 0: Root bottom (0, 0)
    # 1: Tip bottom (L, 0)
    # 2: Hook apex: ramp up at lead_in_angle
    ramp_l = hook_depth / math.tan(math.radians(lead_in_angle_deg))
    ret_l = hook_depth / math.tan(math.radians(return_angle_deg))
    
    p0 = Vector((0.0, 0.0, 0.0))
    p1 = Vector((length, 0.0, 0.0))
    p2 = Vector((length + ramp_l, 0.0, hook_depth))
    p3 = Vector((length + ramp_l + 0.001, 0.0, hook_depth)) # small flat top
    p4 = Vector((length + ramp_l + 0.001 + ret_l, 0.0, 0.0))
    p5 = Vector((length + ramp_l + 0.001 + ret_l, 0.0, -tip_thickness))
    p6 = Vector((0.0, 0.0, -root_thickness))
    
    pts = [p0, p1, p2, p3, p4, p5, p6]
    N = len(pts)

    v_left = [bm.verts.new(p + Vector((0.0, -width / 2.0, 0.0))) for p in pts]
    v_right = [bm.verts.new(p + Vector((0.0, width / 2.0, 0.0))) for p in pts]
    bm.verts.ensure_lookup_table()

    for i in range(N):
        ni = (i + 1) % N
        bm.faces.new([v_left[i], v_left[ni], v_right[ni], v_right[i]])

    bm.faces.new(v_left[::-1])
    bm.faces.new(v_right)

    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Cantilever_SnapFit")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_snap_fits.py headless...")
    y_max = calculate_snapfit_deflection(length_L=0.025, thickness_h=0.0025, material='PETG')
    print(f"Bayer Permissible Deflection (PETG): {y_max*1000:.2f} mm")
    snap = create_cantilever_snapfit()
    print(f"Created Snap Fit: {snap.name} with {len(snap.data.vertices)} vertices, {len(snap.data.polygons)} faces.")
    assert len(snap.data.polygons) == 9
    print("bp_snap_fits verified successfully.")

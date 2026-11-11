"""
bp_enclosure_joints.py — Zero-Screw Clamshell & Enclosure Joint Generators for FDM/SLA.

Standards & Engineering References:
- Bayer MaterialScience. (2004). "Snap-Fit Joints for Plastics: A Design Guide."
- Trono, N. (2000). "Snap-fit joints for plastics." Fastening and Joining, Machine Design.
- DIN 16742 / ISO 20457: "Plastics moulded parts — Tolerances and acceptance conditions."
- DFAM Best Practices: Layer-orientation alignment, overhang chamfers (>= 45 deg),
  and print bed separation planes.

Target: Blender 5.2 LTS (Data-API BMesh, Headless-Safe, Host-Importable).
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, Dict, Any, List

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
except ImportError:
    bpy = None
    bmesh = None
    Vector = None
    Matrix = None


# Permissible FDM Clearances by Process & Material Class
FDM_JOINT_CLEARANCES = {
    "FDM_STANDARD": 0.25,   # 0.25 mm standard FDM sliding/snap fit
    "FDM_PRECISION": 0.20,  # 0.20 mm tuned extrusion
    "FDM_TIGHT": 0.15,      # 0.15 mm press-fit
    "SLA_RESIN": 0.10,      # 0.10 mm resin clearance
}


def calculate_hook_insertion_angle(
    lip_depth_mm: float,
    hook_height_mm: float,
    clearance_mm: float = 0.25,
) -> float:
    """
    Computes required rotational insertion swing angle (in degrees) for a top hook-hinge.
    tan(theta) = (lip_depth_mm + clearance_mm) / hook_height_mm
    """
    if hook_height_mm <= 0:
        raise ValueError("hook_height_mm must be positive")
    if lip_depth_mm <= 0:
        raise ValueError("lip_depth_mm must be positive")
    theta_rad = math.atan2(lip_depth_mm + clearance_mm, hook_height_mm)
    return math.degrees(theta_rad)


def calculate_button_beam_deflection(
    beam_length_mm: float,
    beam_thickness_mm: float,
    switch_travel_mm: float = 0.80,
    modulus_gpa: float = 2.2,  # Typical PETG ~2.1-2.4 GPa, PLA ~3.5 GPa
    beam_width_mm: float = 5.0,
) -> Dict[str, float]:
    """
    Evaluates bending force and strain on a captive U-slot cantilever button.
    Cantilever end deflection: delta = (F * L^3) / (3 * E * I)
    Moment of inertia: I = (b * h^3) / 12
    Max outer fiber strain: epsilon = (1.5 * delta * h) / (L^2)
    """
    if beam_length_mm <= 0 or beam_thickness_mm <= 0:
        raise ValueError("Beam dimensions must be positive")
    
    # In SI mm/N units: E in N/mm2 = GPa * 1000
    E_n_mm2 = modulus_gpa * 1000.0
    I_mm4 = (beam_width_mm * (beam_thickness_mm ** 3)) / 12.0
    
    # Required force for switch actuation
    F_actuation_N = (3.0 * E_n_mm2 * I_mm4 * switch_travel_mm) / (beam_length_mm ** 3)
    
    # Outer fiber strain
    strain = (1.5 * switch_travel_mm * beam_thickness_mm) / (beam_length_mm ** 2)
    
    return {
        "actuation_force_n": round(F_actuation_N, 3),
        "fiber_strain": round(strain, 4),
        "moment_of_inertia_mm4": round(I_mm4, 4),
        "is_safe_repeated_use": strain <= 0.035,  # 3.5% strain threshold for PETG/ABS
    }


def create_hook_hinge_cutter_mesh(
    width_m: float = 0.012,        # 12 mm hook width
    depth_m: float = 0.003,        # 3.0 mm engagement depth
    height_m: float = 0.008,       # 8.0 mm hook height
    lip_angle_deg: float = 45.0,   # 45 deg print-safe overhang chamfer
    col: Optional[Any] = None,
) -> Optional[Any]:
    """
    Generates a solid hook-hinge tooth (or boolean receiver cutter) with a 45-degree
    self-supporting lead-in chamfer for print-bed orientation.
    """
    if bpy is None or bmesh is None:
        return None

    bm = bmesh.new()
    
    # Extrusion in Y from -width/2 to +width/2
    y_half = width_m / 2.0
    chamfer_dx = depth_m * math.tan(math.radians(lip_angle_deg / 2.0))
    
    v0 = bm.verts.new(Vector((0.0, -y_half, 0.0)))
    v1 = bm.verts.new(Vector((depth_m, -y_half, 0.0)))
    v2 = bm.verts.new(Vector((depth_m, -y_half, height_m - chamfer_dx)))
    v3 = bm.verts.new(Vector((depth_m - chamfer_dx, -y_half, height_m)))
    v4 = bm.verts.new(Vector((0.0, -y_half, height_m)))
    
    face_front = bm.faces.new([v0, v1, v2, v3, v4])
    
    # Extrude along Y
    res = bmesh.ops.extrude_face_region(bm, geom=[face_front])
    ext_verts = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0.0, width_m, 0.0)), verts=ext_verts)
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new("HookHingeCutter")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("HookHingeCutter", mesh)
    target_col = col or bpy.context.collection
    target_col.objects.link(obj)
    return obj


def create_captive_button_mesh(
    button_w_m: float = 0.008,     # 8.0 mm outer button width
    button_l_m: float = 0.014,     # 14.0 mm length
    button_h_m: float = 0.004,     # 4.0 mm button cap height
    travel_limit_m: float = 0.0008,# 0.8 mm actuator travel
    flange_margin_m: float = 0.0012, # 1.2 mm retention flange margin
    col: Optional[Any] = None,
) -> Optional[Any]:
    """
    Generates a captive tactile push button with anti-dislodgement shoulder flange
    and actuator switch pip.
    """
    if bpy is None or bmesh is None:
        return None

    bm = bmesh.new()
    
    # 1. Main button keycap
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((button_w_m, button_l_m, button_h_m)), verts=bm.verts)
    
    # 2. Retention flange at base
    flange_verts = []
    flange_w = button_w_m + 2.0 * flange_margin_m
    flange_l = button_l_m + 2.0 * flange_margin_m
    flange_h = button_h_m * 0.3
    
    # Add box for flange offset at bottom
    res = bmesh.ops.create_cube(bm, size=1.0)
    flange_new_verts = [v for v in res["verts"]]
    bmesh.ops.scale(bm, vec=Vector((flange_w, flange_l, flange_h)), verts=flange_new_verts)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, -button_h_m / 2.0 + flange_h / 2.0)), verts=flange_new_verts)
    
    # 3. Actuator pip on bottom
    pip_r = 0.001
    pip_h = travel_limit_m + 0.0005
    res_pip = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=pip_r,
        radius2=pip_r,
        depth=pip_h,
    )
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, -button_h_m / 2.0 - pip_h / 2.0)), verts=res_pip["verts"])
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new("CaptiveButton")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("CaptiveButton", mesh)
    target_col = col or bpy.context.collection
    target_col.objects.link(obj)
    return obj

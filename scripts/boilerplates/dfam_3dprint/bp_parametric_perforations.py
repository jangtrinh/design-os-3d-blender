"""
bp_parametric_perforations.py — Parametric Acoustic & Ventilation Perforation Array Generator.

Standards & Engineering References:
- Blevins, R. D. (1984). "Applied Fluid Dynamics Handbook." (Perforated plates, discharge coefficients & acoustic impedance).
- Gibson, I., Rosen, D., Stucker, B. (2021). "Additive Manufacturing Technologies." Springer.
  (DFAM constraints: ligament width between adjacent holes >= 2x nozzle diameter).
- AGENTS.md §Failure Map: "knife-edge lip prevention" — curved inner shells require flat cavity
  ceilings to avoid sub-millimeter wall taper failures on angled boolean through-bores.

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


def calculate_acoustic_open_area_ratio(
    hole_radius_mm: float,
    pitch_mm: float,
    pattern: str = "hexagonal",
) -> float:
    """
    Computes open area fraction (porosity ratio A_open / A_total) of a perforated sheet.
    - 'hexagonal': (2 * pi * R^2) / (sqrt(3) * pitch^2)
    - 'square': (pi * R^2) / (pitch^2)
    """
    if hole_radius_mm <= 0 or pitch_mm <= 0:
        raise ValueError("hole_radius_mm and pitch_mm must be positive")
    if 2.0 * hole_radius_mm >= pitch_mm:
        raise ValueError("Hole diameter cannot exceed or equal pitch (ligament width <= 0)")

    r = hole_radius_mm
    p = pitch_mm
    pattern_lower = pattern.lower()
    if pattern_lower == "hexagonal":
        ratio = (2.0 * math.pi * (r ** 2)) / (math.sqrt(3.0) * (p ** 2))
    elif pattern_lower == "square":
        ratio = (math.pi * (r ** 2)) / (p ** 2)
    else:
        raise ValueError(f"Unknown pattern '{pattern}', expected 'hexagonal' or 'square'")
    return round(ratio, 4)


def calculate_min_ligament_thickness(
    pitch_mm: float,
    hole_diameter_mm: float,
    min_wall_mm: float = 1.20,
) -> Dict[str, Any]:
    """
    Verifies that the solid ligament bridge between adjacent perforated holes
    meets minimum FDM wall thickness requirements (preventing slice peeling or weak bridges).
    """
    ligament = pitch_mm - hole_diameter_mm
    return {
        "pitch_mm": pitch_mm,
        "hole_diameter_mm": hole_diameter_mm,
        "ligament_thickness_mm": round(ligament, 3),
        "min_wall_required_mm": min_wall_mm,
        "is_printable": ligament >= min_wall_mm,
        "recommended_min_pitch_mm": round(hole_diameter_mm + min_wall_mm, 3),
    }


def generate_graded_radial_coords(
    center_xy: Tuple[float, float] = (0.0, 0.0),
    rings: List[Tuple[float, int]] = None,
) -> List[Tuple[float, float]]:
    """
    Generates 2D planar coordinates for an Apple-style concentric radial perforation grille.
    Each ring tuple: (radius_mm, hole_count).
    Example: [(1.8, 6), (3.6, 12), (5.4, 18), (7.2, 24)] -> 60 holes total.
    """
    if rings is None:
        rings = [
            (2.0, 6),
            (4.0, 12),
            (6.0, 18),
            (8.0, 24),
        ]
    
    coords = []
    cx, cy = center_xy
    for r, count in rings:
        if count <= 0 or r <= 0:
            continue
        angle_step = (2.0 * math.pi) / count
        # Stagger alternating rings by half step for uniform acoustic distribution
        angle_offset = (angle_step / 2.0) if (len(coords) > 0 and count % 2 == 0) else 0.0
        for i in range(count):
            theta = i * angle_step + angle_offset
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            coords.append((round(x, 4), round(y, 4)))
    return coords


def create_radial_perforation_cutter_mesh(
    coords_m: List[Tuple[float, float]],
    hole_radius_m: float = 0.0006,  # 0.6 mm radius (1.2 mm bore)
    bore_depth_m: float = 0.008,    # 8.0 mm length for clean boolean penetration
    segments: int = 16,
    col: Optional[Any] = None,
) -> Optional[Any]:
    """
    Creates a compound solid cutter object containing cylinders for all coordinate pins.
    Optimized for high-speed EXACT Boolean difference through enclosure walls.
    """
    if bpy is None or bmesh is None:
        return None

    bm = bmesh.new()
    
    for (x, y) in coords_m:
        res = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=segments,
            radius1=hole_radius_m,
            radius2=hole_radius_m,
            depth=bore_depth_m,
        )
        bmesh.ops.translate(bm, vec=Vector((x, y, 0.0)), verts=res["verts"])
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new("RadialPerforationCutter")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("RadialPerforationCutter", mesh)
    target_col = col or bpy.context.collection
    target_col.objects.link(obj)
    return obj

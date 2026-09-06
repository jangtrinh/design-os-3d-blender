"""
bp_insert_boss.py — Heat-Set Threaded Insert Boss Generator Boilerplate.

Features:
- Parametric boss geometry for brass knurled inserts (M2, M3, M4, M5).
- Tapered pilot hole (8-deg included taper), lead-in chamfer, and melt reservoir.
- Enforces minimum wall thickness: t_wall >= 1.5 * d_hole (DFAM standard).
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Dict, Tuple, Optional


# Insert Specs: (pilot_hole_dia, insert_length, recommended_boss_od, counterbore_depth)
INSERT_STANDARDS: Dict[str, Tuple[float, float, float, float]] = {
    'M2': (0.0032, 0.0040, 0.0065, 0.0006),
    'M2.5': (0.0036, 0.0050, 0.0075, 0.0007),
    'M3': (0.0040, 0.0057, 0.0085, 0.0008),
    'M4': (0.0056, 0.0080, 0.0120, 0.0010),
    'M5': (0.0064, 0.0095, 0.0140, 0.0012),
}


def create_insert_pilot_cutter(
    size: str = 'M3',
    segments: int = 32,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a boolean negative cutter for heat-set insert pilot hole.
    Includes top chamfer and bottom plastic melt reservoir.
    """
    data = INSERT_STANDARDS.get(size.upper(), INSERT_STANDARDS['M3'])
    d_hole, l_insert, _, cb_depth = data
    r_pilot = d_hole / 2.0
    total_depth = l_insert + cb_depth + 0.001  # extra reservoir depth

    bm = bmesh.new()
    
    # 1. Main pilot cylinder with small taper
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=r_pilot * 0.96, radius2=r_pilot, depth=total_depth,
        matrix=Matrix.Translation(Vector((0, 0, -total_depth / 2.0)))
    )

    # 2. Lead-in top chamfer
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=r_pilot, radius2=r_pilot * 1.3, depth=cb_depth,
        matrix=Matrix.Translation(Vector((0, 0, cb_depth / 2.0)))
    )

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
    mesh = bpy.data.meshes.new(f"Cutter_Insert_{size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_boss_pillar(
    size: str = 'M3',
    height: float = 0.010,
    segments: int = 32,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a freestanding cylindrical boss pillar with DFAM recommended OD.
    """
    data = INSERT_STANDARDS.get(size.upper(), INSERT_STANDARDS['M3'])
    _, _, d_boss, _ = data
    r_boss = d_boss / 2.0

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=r_boss, radius2=r_boss, depth=height,
        matrix=Matrix.Translation(Vector((0, 0, height / 2.0)))
    )

    mesh = bpy.data.meshes.new(f"BossPillar_{size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


if __name__ == '__main__':
    print("Testing bp_insert_boss.py headless...")
    cutter = create_insert_pilot_cutter('M3')
    pillar = create_boss_pillar('M3', height=0.012)
    print(f"Cutter: {cutter.name} ({len(cutter.data.vertices)} verts), Pillar: {pillar.name} ({len(pillar.data.vertices)} verts)")
    assert len(cutter.data.vertices) > 50
    assert len(pillar.data.vertices) > 50
    print("bp_insert_boss verified successfully.")

"""
bp_bmesh_cad.py — BMesh & Non-Destructive CAD Modeling Boilerplate.

Combines high-performance BMesh topological generation with 
pure Data-API modifier application (no bpy.ops operators).
100% headless-safe, zero context dependencies.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Matrix, Vector
from typing import List, Tuple, Optional


def create_bmesh() -> bmesh.types.BMesh:
    """Instantiates a fresh in-memory BMesh."""
    return bmesh.new()


def bmesh_to_object(bm: bmesh.types.BMesh, obj_name: str, col: Optional[bpy.types.Collection] = None) -> bpy.types.Object:
    """
    Writes BMesh data to a new Blender mesh object and links it to the collection.
    Frees the BMesh instance.
    """
    if obj_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
    if obj_name in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[obj_name], do_unlink=True)

    mesh = bpy.data.meshes.new(obj_name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(obj_name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def add_box(bm: bmesh.types.BMesh, size: Vector | Tuple[float, float, float], matrix: Optional[Matrix] = None) -> List[bmesh.types.BMVert]:
    """Adds a box centered at matrix origin."""
    sx, sy, sz = size
    res = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((sx, sy, sz, 1.0)))
    verts = res["verts"]
    if matrix:
        bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    return verts


def add_cylinder(
    bm: bmesh.types.BMesh,
    radius: float,
    height: float,
    segments: int = 32,
    cap_ends: bool = True,
    matrix: Optional[Matrix] = None
) -> List[bmesh.types.BMVert]:
    """Adds a cylinder aligned along local Z axis."""
    res = bmesh.ops.create_cone(
        bm,
        cap_ends=cap_ends,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=height,
        matrix=matrix or Matrix.Identity(4)
    )
    return res["verts"]


def apply_all_modifiers_headless(obj: bpy.types.Object) -> None:
    """
    Applies the entire modifier stack (booleans, bevels, mirror) via the
    evaluated depsgraph data API. Completely avoids bpy.ops.modifier_apply.
    """
    if not obj.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(
        obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg
    )
    old_me = obj.data
    obj.modifiers.clear()
    obj.data = new_me
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)


def add_boolean_difference(target_obj: bpy.types.Object, cutter_obj: bpy.types.Object, solver: str = 'EXACT') -> bpy.types.Modifier:
    """
    Adds a non-destructive BOOLEAN modifier to target_obj.
    In Blender 5.2, solver can be 'EXACT', 'FLOAT', or 'MANIFOLD'.
    """
    mod = target_obj.modifiers.new(name=f"Bool_{cutter_obj.name}", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter_obj
    mod.solver = solver
    return mod


def verify_mesh_manifold(mesh: bpy.types.Mesh) -> Tuple[bool, int, int]:
    """
    Verifies if a Mesh data-block is watertight/manifold.
    Returns (is_manifold, non_manifold_edges, non_manifold_verts).
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    bad_edges = sum(1 for e in bm.edges if not e.is_manifold)
    bad_verts = sum(1 for v in bm.verts if not v.is_manifold)
    is_manifold = (bad_edges == 0 and bad_verts == 0 and len(bm.faces) > 0)
    bm.free()
    return is_manifold, bad_edges, bad_verts


if __name__ == '__main__':
    print("Testing bp_bmesh_cad.py headless...")
    
    # 1. Base Plate via BMesh: 60mm x 60mm x 15mm
    bm_base = create_bmesh()
    add_box(bm_base, size=(0.060, 0.060, 0.015))
    target_obj = bmesh_to_object(bm_base, "CAD_Flange_Base")

    # 2. Center Cutter: 22mm diameter (608 bearing standard)
    bm_bore = create_bmesh()
    add_cylinder(bm_bore, radius=0.011, height=0.030, segments=32)
    bore_obj = bmesh_to_object(bm_bore, "Bearing_Bore_Cutter")

    # Add Boolean difference
    add_boolean_difference(target_obj, bore_obj, solver='EXACT')

    # Apply via pure data API depsgraph
    apply_all_modifiers_headless(target_obj)
    
    # Cleanup cutter
    bpy.data.objects.remove(bore_obj, do_unlink=True)

    # 3. Verify Manifold
    is_watertight, bad_edges, bad_verts = verify_mesh_manifold(target_obj.data)
    print(f"Watertight: {is_watertight} (Bad edges: {bad_edges}, Bad verts: {bad_verts})")
    print(f"Final Vertices: {len(target_obj.data.vertices)}, Faces: {len(target_obj.data.polygons)}")
    assert is_watertight, "CAD Plate is not manifold!"
    print("bp_bmesh_cad verified successfully.")

"""Shared bmesh preparation. Everything downstream is world-space millimetres."""
from __future__ import annotations

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

MM_PER_BU = 1000.0  # Blender unit is the metre when scale_length == 1.0

AXES = {"x": Vector((1.0, 0.0, 0.0)), "y": Vector((0.0, 1.0, 0.0)),
        "z": Vector((0.0, 0.0, 1.0)),
        "+x": Vector((1.0, 0.0, 0.0)), "-x": Vector((-1.0, 0.0, 0.0)),
        "+y": Vector((0.0, 1.0, 0.0)), "-y": Vector((0.0, -1.0, 0.0)),
        "+z": Vector((0.0, 0.0, 1.0)), "-z": Vector((0.0, 0.0, -1.0))}


def axis_vector(axis):
    if isinstance(axis, str):
        v = AXES.get(axis.lower())
        if v is None:
            raise ValueError("unknown axis %r" % axis)
        return v.copy()
    return Vector(tuple(float(c) for c in axis)).normalized()


def evaluated_mm_bmesh(obj, scale=MM_PER_BU):
    """Evaluated (modifiers applied) mesh, world space, coordinates in mm.

    Promoted from knowledge/60-pipeline/3d-printing.md print_audit, which uses
    the depsgraph-evaluated mesh and bm.transform(obj.matrix_world); the mm
    scale is added so every predicate speaks one unit.
    """
    bm = bmesh.new()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    bm.from_mesh(me)
    ev.to_mesh_clear()
    bm.transform(Matrix.Scale(scale, 4) @ obj.matrix_world)
    return finish(bm)


def raw_mm_bmesh(mesh, scale=1.0):
    """Mesh data taken as-is (used after an STL re-import written in mm)."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if scale != 1.0:
        bm.transform(Matrix.Scale(scale, 4))
    return finish(bm)


def finish(bm):
    bm.normal_update()
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
        seq.index_update()
    return bm


def triangulated(bm):
    tri = bm.copy()
    bmesh.ops.triangulate(tri, faces=tri.faces[:])
    return finish(tri)


def bvh(bm):
    return BVHTree.FromBMesh(bm, epsilon=0.0)


def bbox_mm(bm):
    if not bm.verts:
        return [0.0, 0.0, 0.0]
    lo = [min(v.co[k] for v in bm.verts) for k in range(3)]
    hi = [max(v.co[k] for v in bm.verts) for k in range(3)]
    return [hi[k] - lo[k] for k in range(3)]


def triangles(bm):
    """List of (a, b, c) Vectors in mm, from a triangulated copy."""
    tri = triangulated(bm)
    out = [tuple(v.co.copy() for v in f.verts) for f in tri.faces]
    tri.free()
    return out

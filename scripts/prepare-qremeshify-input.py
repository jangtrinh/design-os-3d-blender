"""Prepare a bounded, manifold scaffold for the local QRemeshify stage."""
import json
import os
from pathlib import Path

import bmesh
import bpy


def triangle_count(mesh):
    return sum(len(face.vertices) - 2 for face in mesh.polygons)


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def topology(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    seen = set()
    component_sizes = []
    for vert in bm.verts:
        if vert in seen:
            continue
        stack = [vert]
        seen.add(vert)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for edge in current.link_edges:
                neighbor = edge.other_vert(current)
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        component_sizes.append(size)
    stats = {
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "components": len(component_sizes),
        "faces": len(bm.faces),
        "largest_component_verts": max(component_sizes, default=0),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "tris": sum(len(face.verts) - 2 for face in bm.faces),
        "verts": len(bm.verts),
        "zero_area_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    bm.free()
    return stats


def repair_after_decimate(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-8)
    collapsed_flaps = [face for face in bm.faces
                       if sum(edge.is_boundary for edge in face.edges) >= 2
                       and any(len(edge.link_faces) > 2 for edge in face.edges)]
    if collapsed_flaps:
        bmesh.ops.delete(bm, geom=collapsed_flaps, context="FACES")
    boundary = [edge for edge in bm.edges if edge.is_boundary]
    if boundary:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def non_manifold_samples(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    samples = [{"faces": len(edge.link_faces),
                "vertices": [tuple(round(value, 6) for value in vert.co)
                             for vert in edge.verts]}
               for edge in bm.edges if not edge.is_manifold]
    bm.free()
    return samples[:12]


def main():
    name = os.environ.get("QREMESHIFY_OBJECT", "drone-silhouette-repaired")
    target = int(os.environ.get("QREMESHIFY_PREP_TARGET_TRIS", "80000"))
    output = Path(os.environ.get("QREMESHIFY_PREP_OUTPUT", str(
        Path(bpy.data.filepath).with_name("qremeshify-input.blend"))))
    obj = bpy.data.objects[name]
    activate(obj)
    source_tris = triangle_count(obj.data)
    for modifier in list(obj.modifiers):
        assert bpy.ops.object.modifier_apply(modifier=modifier.name) == {"FINISHED"}
    current_tris = triangle_count(obj.data)
    if current_tris > target:
        modifier = obj.modifiers.new("qremeshify-triangle-budget", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = target / current_tris
        modifier.use_collapse_triangulate = True
        assert bpy.ops.object.modifier_apply(modifier=modifier.name) == {"FINISHED"}
    repair_after_decimate(obj.data)
    stats = topology(obj.data)
    if stats["non_manifold_edges"]:
        print("QREMESHIFY_INPUT_NON_MANIFOLD " + json.dumps(
            non_manifold_samples(obj.data), sort_keys=True), flush=True)
    assert stats["tris"] <= round(target * 1.02), stats
    assert stats["boundary_edges"] == 0, stats
    assert stats["non_manifold_edges"] == 0, stats
    assert stats["zero_area_faces"] == 0, stats
    obj["qremeshify-preflight-source-tris"] = source_tris
    obj["qremeshify-preflight-target-tris"] = target
    obj["qremeshify-preflight-stats"] = json.dumps(stats, sort_keys=True)
    bpy.context.scene["qremeshify-input-prepared"] = True
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print("QREMESHIFY_INPUT_OK " + json.dumps(
        {"blend": str(output), "source_tris": source_tris, **stats},
        sort_keys=True))


if __name__ == "__main__":
    main()

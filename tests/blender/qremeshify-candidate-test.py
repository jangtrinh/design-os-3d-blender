"""Read-only topology and silhouette gate for a QRemeshify candidate blend."""
import json

import bmesh
import bpy


def mesh_world_extents(obj, mesh):
    points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    return [max(point[index] for point in points) -
            min(point[index] for point in points) for index in range(3)]


def source_extents(obj):
    points = [obj.matrix_world @ type(obj.location)(corner)
              for corner in obj.bound_box]
    return [max(point[index] for point in points) -
            min(point[index] for point in points) for index in range(3)]


def main():
    source = (bpy.data.objects.get("drone-silhouette-repaired") or
              bpy.data.objects["fpv_drone_rodin"])
    candidate = bpy.data.objects["drone-silhouette-qremesh"]
    failures = []
    if bpy.context.scene.get("external-service-calls") != 0:
        failures.append("external-service-calls must be 0")
    if candidate.get("qremeshify-version") != "1.1.0":
        failures.append("missing pinned QRemeshify version")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = candidate.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    stats = {
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "faces": len(bm.faces),
        "loose_verts": sum(not vert.link_edges for vert in bm.verts),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "zero_area_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
    }
    quad_ratio = sum(len(face.verts) == 4 for face in bm.faces) / max(len(bm.faces), 1)
    source_size = source_extents(source)
    candidate_size = mesh_world_extents(candidate, mesh)
    dimension_delta = [abs(after / before - 1.0) for before, after in
                       zip(source_size, candidate_size)]
    if stats["faces"] < 1000 or stats["faces"] > 120000:
        failures.append(f"face budget failed: {stats['faces']}")
    if quad_ratio < 0.8:
        failures.append(f"quad ratio below 0.8: {quad_ratio:.4f}")
    if stats["loose_verts"] or stats["zero_area_faces"]:
        failures.append(f"degenerate topology: {stats}")
    if stats["boundary_edges"] or stats["non_manifold_edges"]:
        failures.append(f"open or non-manifold topology: {stats}")
    if max(dimension_delta) > 0.05:
        failures.append(f"dimension delta above 5%: {dimension_delta}")
    bm.free()
    evaluated.to_mesh_clear()
    result = {"dimension_delta": dimension_delta, "failures": failures,
              "quad_ratio": quad_ratio, "stats": stats}
    assert not failures, json.dumps(result, sort_keys=True)
    print("TEST_PASS " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

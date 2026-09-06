"""
bp_hair_curves_gen.py — Modern Blender 5.2 Hair Curves Generator & Geometry Nodes Grooming.

Standards & Academic Citations:
- Bergou, M., Wardetzky, M., Robinson, S., Audoly, B., & Grinspun, E. (2008): "Discrete
  Elastic Rods", ACM TOG 27(3) — the discrete-rod model hair strands are usually built on.
- Selle, A., Lentine, M., & Fedkiw, R. (2008): "A Mass Spring Model for Hair Simulation",
  ACM TOG 27(3), Article 64.
- Blender 5.2 LTS Python API: `bpy.types.Curves` (hair curves data-block).

Target: Blender 5.2 LTS (Data-API Curves & NodeTreeInterface, Headless-Safe).

Runtime-verified 2026-09-06 against Blender 5.2.0 LTS: `bpy.data.hair_curves.new()`,
`Curves.add_curves()`, `Curves.points[i].position/.radius`, `Curves.surface`,
`Curves.surface_uv_map`, and the CURVE-domain `surface_uv_coordinate` attribute all exist.
`bpy.data.curves.new(name, 'CURVES')` does NOT — that enum accepts only CURVE/SURFACE/FONT.
"""

from __future__ import annotations
import bpy
import math
from mathutils import Vector, Matrix
from typing import Optional, List, Dict, Any


def create_scalp_mesh(
    radius: float = 0.10,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Creates a hemisphere scalp emitter mesh in BMesh."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm, u_segments=16, v_segments=12, radius=radius,
        matrix=Matrix.Translation(Vector((0.0, 0.0, 1.65)))
    )
    # Remove lower hemisphere (below center) to keep only upper scalp
    del_verts = [v for v in bm.verts if v.co.z < 1.65]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Scalp_Emitter")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def create_hair_curves_groom(
    scalp_obj: bpy.types.Object,
    num_strands: int = 40,
    points_per_strand: int = 8,
    strand_length: float = 0.15,
    root_radius: float = 0.0015,
    tip_radius: float = 0.0002,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """
    Generates a native Blender 5.2 Curves ('hair curves') object rooted on the scalp
    emitter mesh. Roots are sampled from scalp vertices; each strand leaves the scalp
    along the local vertex normal and bends sideways toward the gravity direction, so the
    polyline arc length stays >= strand_length for every root orientation.

    Returns an object whose data holds exactly num_strands curves of points_per_strand
    points each, with a per-point radius taper and a CURVE-domain
    `surface_uv_coordinate` attribute so Geometry Nodes can bind strands to the surface.
    """
    verts = scalp_obj.data.vertices
    if not len(verts):
        raise ValueError("scalp emitter mesh has no vertices to root hair on")
    step = max(1, len(verts) // num_strands)
    roots = [verts[i] for i in range(0, len(verts), step)][:num_strands]

    curves_data = bpy.data.hair_curves.new("Hair_Curves_Groom")
    curves_data.surface = scalp_obj
    if scalp_obj.data.uv_layers.active is not None:
        curves_data.surface_uv_map = scalp_obj.data.uv_layers.active.name
    curves_data.add_curves([points_per_strand] * len(roots))

    gravity = Vector((0.0, 0.0, -1.0))
    for c_index, root in enumerate(roots):
        slice_ = curves_data.curves[c_index]
        base = Vector(root.co)
        normal = Vector(root.normal)
        if normal.length_squared < 1e-12:
            normal = Vector((0.0, 0.0, 1.0))
        normal.normalize()
        # Bend direction = gravity component perpendicular to the normal (never parallel,
        # so the quadratic bend adds arc length instead of cancelling the root direction).
        bend = gravity - normal * gravity.dot(normal)
        if bend.length_squared < 1e-8:
            bend = Vector((1.0, 0.0, 0.0)) - normal * normal.x
        bend.normalize()
        for p_index in range(points_per_strand):
            t = p_index / (points_per_strand - 1)          # 0.0 root -> 1.0 tip
            # Straight along the normal, bending sideways quadratically with arc length.
            offset = normal * (strand_length * t) + bend * (strand_length * 0.45 * t * t)
            point = curves_data.points[slice_.first_point_index + p_index]
            point.position = base + offset
            point.radius = root_radius + (tip_radius - root_radius) * t

    uv_attr = curves_data.attributes.get("surface_uv_coordinate")
    if uv_attr is None:
        uv_attr = curves_data.attributes.new("surface_uv_coordinate", 'FLOAT2', 'CURVE')
    for c_index, root in enumerate(roots):
        # Deterministic placeholder binding: real grooms bake this from the scalp UV map.
        uv_attr.data[c_index].vector = (
            (c_index % 8) / 8.0, math.floor(c_index / 8.0) / max(1.0, num_strands / 8.0))

    hair_obj = bpy.data.objects.new("Hair_Curves_Groom", curves_data)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(hair_obj)
    hair_obj.parent = scalp_obj
    return hair_obj


def build_hair_procedural_geonodes(
    hair_obj: bpy.types.Object,
    root_radius: float = 0.0015,     # 1.5mm root radius (stylized/braid) or 0.00004m (realistic)
    tip_radius: float = 0.0002       # 0.2mm tip taper radius
) -> bpy.types.Modifier:
    """
    Builds a Blender 5.2 NodeTreeInterface Geometry Nodes modifier for the hair curves
    controlling root-to-tip taper radius. Note: this tree only re-tapers the radius; it
    does not generate, interpolate, or clump strands.
    """
    mod = hair_obj.modifiers.new("Hair_Styling_Engine", 'NODES')
    group = bpy.data.node_groups.new("Hair_Styling_Group", 'GeometryNodeTree')
    mod.node_group = group

    # Blender 5.2 NodeTreeInterface socket creation
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = group.nodes
    links = group.links

    in_node = nodes.new('NodeGroupInput')
    in_node.location = (-300, 0)
    out_node = nodes.new('NodeGroupOutput')
    out_node.location = (400, 0)

    set_radius = nodes.new('GeometryNodeSetCurveRadius')
    set_radius.location = (0, 0)

    spline_param = nodes.new('GeometryNodeSplineParameter')  # Factor: 0.0 root -> 1.0 tip
    spline_param.location = (-300, -150)

    map_range = nodes.new('ShaderNodeMapRange')
    map_range.location = (-150, -150)
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = root_radius
    map_range.inputs['To Max'].default_value = tip_radius

    links.new(in_node.outputs['Geometry'], set_radius.inputs['Curve'])
    links.new(spline_param.outputs['Factor'], map_range.inputs['Value'])
    links.new(map_range.outputs['Result'], set_radius.inputs['Radius'])
    links.new(set_radius.outputs['Curve'], out_node.inputs['Geometry'])

    return mod


if __name__ == '__main__':
    print("Testing bp_hair_curves_gen.py headless...")
    scalp = create_scalp_mesh()
    hair = create_hair_curves_groom(scalp, num_strands=40, points_per_strand=8,
                                    strand_length=0.15)
    mod = build_hair_procedural_geonodes(hair)
    data = hair.data

    print(f"Created Scalp Emitter: {scalp.name} ({len(scalp.data.vertices)} verts)")
    print(f"Created Hair Object: {hair.name} ({len(data.curves)} strands, {len(data.points)} points)")
    print(f"Built Geometry Nodes Modifier: {mod.name} with {len(mod.node_group.nodes)} nodes")

    # Postconditions: real strand geometry, taper, surface binding, wired node tree.
    assert hair.type == 'CURVES', hair.type
    assert hair.parent == scalp
    assert len(data.curves) == 40, f"expected 40 strands, got {len(data.curves)}"
    assert len(data.points) == 320, f"expected 320 points, got {len(data.points)}"
    assert all(c.points_length == 8 for c in data.curves), "ragged strand point counts"
    assert data.surface == scalp, "hair curves not bound to the scalp surface"
    assert "surface_uv_coordinate" in data.attributes, "missing surface_uv_coordinate"
    def arc_length(curve_slice):
        pts = [data.points[curve_slice.first_point_index + i].position
               for i in range(curve_slice.points_length)]
        return sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))

    lengths = [arc_length(c) for c in data.curves]
    assert min(lengths) >= 0.15 - 1e-4, f"shortest strand {min(lengths):.4f} m < 0.15 m"
    assert max(lengths) <= 0.18, f"longest strand {max(lengths):.4f} m > 0.18 m"
    first = data.curves[0]
    assert data.points[first.first_point_index].radius > \
        data.points[first.first_point_index + 7].radius, "radius does not taper root->tip"
    assert len(mod.node_group.nodes) >= 5
    assert all(n.outputs[0].is_linked for n in mod.node_group.nodes
               if n.bl_idname != 'NodeGroupOutput'), "dangling node in hair node tree"
    print(f"Asserts OK: 40 strands x 8 points, arc {min(lengths):.4f}-{max(lengths):.4f} m, "
          "tapered, surface bound.")
    print("bp_hair_curves_gen verified successfully.")

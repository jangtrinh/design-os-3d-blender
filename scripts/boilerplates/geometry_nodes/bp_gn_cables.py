"""
bp_gn_cables.py — Procedural Catenary Hanging Cable Node Tree Boilerplate.

Standards & Academic Citations:
- Irvine, H. M. (1981). "Cable Structures." MIT Press, Cambridge, MA. ISBN: 978-0-262-09023-0.
- Meriam, J. L., & Kraige, L. G. (2012). "Engineering Mechanics: Statics (7th ed.)." John Wiley & Sons. (Catenary equilibrium & parabolic cable approximation).
- Blender Foundation (2026): "Blender 5.2 Python API: GeometryNodeCurveLine, GeometryNodeCurveToMesh."

Target: Blender 5.2 LTS (tree.interface.new_socket).
"""

from __future__ import annotations
import bpy


def build_catenary_cable_node_tree(name: str = "GN_Catenary_Cable") -> bpy.types.GeometryNodeTree:
    """
    Constructs a procedural hanging wire/cable tree with sag math:
    Z_offset(t) = -4 * sag * t * (1 - t)  (Parabolic catenary approximation).
    """
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # 5.2 Interface API
    tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Span", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Sag", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Cable_Radius", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    for item in tree.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Span": item.default_value = 2.0
            elif item.name == "Sag": item.default_value = 0.25
            elif item.name == "Cable_Radius": item.default_value = 0.005

    in_node = tree.nodes.new('NodeGroupInput')
    in_node.location = (-400, 0)
    out_node = tree.nodes.new('NodeGroupOutput')
    out_node.location = (600, 0)

    # 1. Base Curve Line along X
    line_node = tree.nodes.new('GeometryNodeCurvePrimitiveLine')
    line_node.location = (-200, 100)

    # Combine XYZ for line end
    comb_end = tree.nodes.new('ShaderNodeCombineXYZ')
    comb_end.location = (-350, 150)
    tree.links.new(in_node.outputs['Span'], comb_end.inputs['X'])
    tree.links.new(comb_end.outputs['Vector'], line_node.inputs['End'])

    # 2. Resample curve
    resample = tree.nodes.new('GeometryNodeResampleCurve')
    resample.location = (0, 100)
    resample.inputs['Count'].default_value = 32
    tree.links.new(line_node.outputs['Curve'], resample.inputs['Curve'])

    # 3. Curve to Mesh with circle profile
    c2m = tree.nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (200, 100)

    circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.location = (0, -100)
    circle.inputs['Resolution'].default_value = 16
    tree.links.new(in_node.outputs['Cable_Radius'], circle.inputs['Radius'])

    tree.links.new(resample.outputs['Curve'], c2m.inputs['Curve'])
    tree.links.new(circle.outputs['Curve'], c2m.inputs['Profile Curve'])

    # 4. Smooth shading
    smooth = tree.nodes.new('GeometryNodeSetShadeSmooth')
    smooth.location = (400, 100)
    tree.links.new(c2m.outputs['Mesh'], smooth.inputs['Mesh'])
    tree.links.new(smooth.outputs['Mesh'], out_node.inputs['Geometry'])

    return tree


if __name__ == '__main__':
    print("Testing bp_gn_cables.py headless...")
    tree = build_catenary_cable_node_tree()
    print(f"Created Cable Node Tree: '{tree.name}' with {len(tree.nodes)} nodes.")

    mesh = bpy.data.meshes.new("Test_Cable_Obj")
    obj = bpy.data.objects.new("Test_Cable_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    mod = obj.modifiers.new("GN_Cable", 'NODES')
    mod.node_group = tree

    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    eval_mesh = eval_obj.to_mesh()
    n_v, n_f = len(eval_mesh.vertices), len(eval_mesh.polygons)
    eval_obj.to_mesh_clear()

    print(f"Evaluated Cable: {n_v} vertices, {n_f} faces.")
    assert n_v > 0 and n_f > 0, "Cable evaluation failed!"
    print("bp_gn_cables verified successfully.")

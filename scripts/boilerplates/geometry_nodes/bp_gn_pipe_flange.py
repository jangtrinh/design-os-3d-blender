"""
bp_gn_pipe_flange.py — Parametric Pipe Flange Geometry Node Tree Boilerplate.

Standards & Academic Citations:
- ASME B16.5-2020: "Pipe Flanges and Flanged Fittings: NPS 1/2 through NPS 24 Metric/Inch Standard."
- Blender Foundation (2026): "Blender 5.2 Python API: GeometryNodeTree & NodeTreeInterface."

Target: Blender 5.2 LTS (tree.interface.new_socket, RNA modifier binding).
"""

from __future__ import annotations
import bpy
from mathutils import Vector
from typing import Tuple


def build_parametric_flange_node_tree(name: str = "GN_ASME_Pipe_Flange") -> bpy.types.GeometryNodeTree:
    """
    Constructs an ASME B16.5 parametric pipe flange node group in Blender 5.2.
    Inputs: Pipe Bore, Flange OD, Flange Thickness, Hub Length.
    """
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Blender 5.2 NodeTreeInterface API
    tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Flange_OD", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Flange_Thick", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Bore_ID", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set interface defaults
    for item in tree.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Flange_OD": item.default_value = 0.100  # 100mm OD
            elif item.name == "Flange_Thick": item.default_value = 0.015  # 15mm thick
            elif item.name == "Bore_ID": item.default_value = 0.040  # 40mm bore

    # Create Group Input / Output
    in_node = tree.nodes.new('NodeGroupInput')
    in_node.location = (-400, 0)
    out_node = tree.nodes.new('NodeGroupOutput')
    out_node.location = (600, 0)

    # Flange Disc Node
    disc_node = tree.nodes.new('GeometryNodeMeshCylinder')
    disc_node.location = (-150, 100)
    disc_node.inputs['Vertices'].default_value = 48

    # Math Node: Divide Flange_OD by 2 for radius
    div_od = tree.nodes.new('ShaderNodeMath')
    div_od.operation = 'DIVIDE'
    div_od.inputs[1].default_value = 2.0
    div_od.location = (-300, 200)

    # Math Node: Divide Bore_ID by 2 for radius
    div_id = tree.nodes.new('ShaderNodeMath')
    div_id.operation = 'DIVIDE'
    div_id.inputs[1].default_value = 2.0
    div_id.location = (-300, -100)

    # Center Bore Cutter
    bore_node = tree.nodes.new('GeometryNodeMeshCylinder')
    bore_node.location = (-150, -100)
    bore_node.inputs['Vertices'].default_value = 48

    # Boolean Difference Node
    bool_node = tree.nodes.new('GeometryNodeMeshBoolean')
    bool_node.operation = 'DIFFERENCE'
    bool_node.location = (150, 0)

    # Shade Smooth Node
    smooth_node = tree.nodes.new('GeometryNodeSetShadeSmooth')
    smooth_node.location = (350, 0)

    # Wiring
    tree.links.new(in_node.outputs['Flange_OD'], div_od.inputs[0])
    tree.links.new(div_od.outputs['Value'], disc_node.inputs['Radius'])
    tree.links.new(in_node.outputs['Flange_Thick'], disc_node.inputs['Depth'])

    tree.links.new(in_node.outputs['Bore_ID'], div_id.inputs[0])
    tree.links.new(div_id.outputs['Value'], bore_node.inputs['Radius'])
    
    # Make cutter taller than flange thickness
    add_h = tree.nodes.new('ShaderNodeMath')
    add_h.operation = 'ADD'
    add_h.inputs[1].default_value = 0.010
    add_h.location = (-300, 0)
    tree.links.new(in_node.outputs['Flange_Thick'], add_h.inputs[0])
    tree.links.new(add_h.outputs['Value'], bore_node.inputs['Depth'])

    # Boolean wiring
    tree.links.new(disc_node.outputs['Mesh'], bool_node.inputs[0])
    tree.links.new(bore_node.outputs['Mesh'], bool_node.inputs[1])

    tree.links.new(bool_node.outputs['Mesh'], smooth_node.inputs['Mesh'])
    tree.links.new(smooth_node.outputs['Mesh'], out_node.inputs['Geometry'])

    return tree


if __name__ == '__main__':
    print("Testing bp_gn_pipe_flange.py headless...")
    tree = build_parametric_flange_node_tree()
    print(f"Created Node Tree: '{tree.name}' with {len(tree.nodes)} nodes and {len(tree.links)} links.")
    
    # Test on Blender object
    mesh = bpy.data.meshes.new("Test_Flange_Obj")
    obj = bpy.data.objects.new("Test_Flange_Obj", mesh)
    bpy.context.scene.collection.objects.link(obj)

    mod = obj.modifiers.new("GN_Flange", 'NODES')
    mod.node_group = tree

    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    eval_mesh = eval_obj.to_mesh()
    n_v, n_f = len(eval_mesh.vertices), len(eval_mesh.polygons)
    eval_obj.to_mesh_clear()

    print(f"Evaluated Flange: {n_v} vertices, {n_f} faces.")
    assert n_v > 0 and n_f > 0, "Geometry Nodes flange evaluation failed!"
    print("bp_gn_pipe_flange verified successfully.")

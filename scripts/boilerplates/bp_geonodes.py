"""
bp_geonodes.py — Procedural Geometry Nodes Boilerplate for Blender 5.2+.

Compliant with Blender 4.0+ / 5.2 LTS interface API (tree.interface.new_socket)
and Blender 5.2 RNA modifier property bindings.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
from typing import Optional, Any, Tuple


def create_geometry_node_tree(name: str) -> Tuple[bpy.types.GeometryNodeTree, bpy.types.Node, bpy.types.Node]:
    """
    Creates a new GeometryNodeTree with standard Geometry Input and Output sockets.
    Returns: (tree, input_node, output_node).
    """
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    
    # 4.0+ / 5.2 Interface API
    tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    input_node = tree.nodes.new('NodeGroupInput')
    input_node.location = (-300, 0)
    
    output_node = tree.nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)

    return tree, input_node, output_node


def add_interface_socket(
    tree: bpy.types.GeometryNodeTree,
    name: str,
    in_out: str,
    socket_type: str,
    default_value: Any = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> bpy.types.NodeTreeInterfaceSocket:
    """
    Adds a custom typed input/output socket to the GeometryNodeTree interface.
    socket_type examples: 'NodeSocketFloat', 'NodeSocketInt', 'NodeSocketVector', 'NodeSocketBool'.
    """
    item = tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    if default_value is not None and hasattr(item, 'default_value'):
        item.default_value = default_value
    if min_value is not None and hasattr(item, 'min_value'):
        item.min_value = min_value
    if max_value is not None and hasattr(item, 'max_value'):
        item.max_value = max_value
    return item


def add_node(
    tree: bpy.types.GeometryNodeTree,
    bl_idname: str,
    location: Tuple[float, float] = (0, 0),
    label: Optional[str] = None
) -> bpy.types.Node:
    """Spawns a node in the tree with explicit coordinates to avoid overlapping."""
    node = tree.nodes.new(bl_idname)
    node.location = location
    if label:
        node.label = label
    return node


def connect(
    tree: bpy.types.GeometryNodeTree,
    from_node: bpy.types.Node,
    from_socket: str | int,
    to_node: bpy.types.Node,
    to_socket: str | int
) -> bpy.types.NodeLink:
    """
    Connects two node sockets safely, resolving by name or index.
    Raises KeyError with introspection diagnostic if socket cannot be resolved.
    """
    def resolve(node: bpy.types.Node, ident: str | int, is_out: bool):
        sockets = node.outputs if is_out else node.inputs
        if isinstance(ident, int):
            return sockets[ident]
        if ident in sockets:
            return sockets[ident]
        ident_lower = ident.lower()
        for s in sockets:
            if s.name.lower() == ident_lower or s.identifier == ident:
                return s
        avail = [f"'{s.name}'" for s in sockets]
        dir_str = "output" if is_out else "input"
        raise KeyError(f"Socket '{ident}' not found on {dir_str} of '{node.name}' ({node.bl_idname}). Available: {avail}")

    sock_from = resolve(from_node, from_socket, is_out=True)
    sock_to = resolve(to_node, to_socket, is_out=False)
    return tree.links.new(sock_from, sock_to)


def assign_geonodes_modifier(
    obj: bpy.types.Object,
    tree: bpy.types.GeometryNodeTree,
    mod_name: str = "GeometryNodes"
) -> bpy.types.NodesModifier:
    """
    Assigns a GeometryNodeTree to an object's modifier stack.
    """
    mod = obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = tree
    return mod


def set_modifier_input(mod: bpy.types.NodesModifier, socket_name: str, value: Any) -> None:
    """
    Sets a modifier input parameter cleanly across Blender versions.
    Blender 5.2 uses mod.properties.inputs.<identifier>.value.
    Blender 4.0-5.1 fallback uses mod[identifier].
    """
    tree = mod.node_group
    if not tree:
        return

    # Find the socket identifier from the interface
    identifier = None
    for item in tree.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == socket_name:
            identifier = item.identifier
            break

    if identifier is None:
        raise KeyError(f"Input socket '{socket_name}' not found on interface of '{tree.name}'")

    # Version-safe assignment
    if hasattr(mod, "properties") and hasattr(mod.properties, "inputs"):
        prop_input = getattr(mod.properties.inputs, identifier, None)
        if prop_input is not None:
            prop_input.value = value
            return

    # Fallback to ID-property lookup
    mod[identifier] = value


if __name__ == '__main__':
    print("Testing bp_geonodes.py headless...")
    
    # Create test object
    mesh = bpy.data.meshes.new("GN_Parametric_Object")
    obj = bpy.data.objects.new("GN_Parametric_Object", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Build Parametric Node Tree: Mesh Cylinder with customizable radius & depth
    tree, in_node, out_node = create_geometry_node_tree("Parametric_Cylinder_Tree")
    
    # Interface Inputs
    add_interface_socket(tree, "Radius", 'INPUT', 'NodeSocketFloat', default_value=0.025, min_value=0.001)
    add_interface_socket(tree, "Depth", 'INPUT', 'NodeSocketFloat', default_value=0.080, min_value=0.001)
    
    # Nodes
    cyl_node = add_node(tree, 'GeometryNodeMeshCylinder', location=(0, 0))
    shade_node = add_node(tree, 'GeometryNodeSetShadeSmooth', location=(300, 0))

    # Wiring
    connect(tree, in_node, "Radius", cyl_node, "Radius")
    connect(tree, in_node, "Depth", cyl_node, "Depth")
    connect(tree, cyl_node, "Mesh", shade_node, "Mesh")
    connect(tree, shade_node, "Mesh", out_node, "Geometry")

    # Modifier setup & driving
    mod = assign_geonodes_modifier(obj, tree)
    set_modifier_input(mod, "Radius", 0.050)
    set_modifier_input(mod, "Depth", 0.120)

    # Evaluation test
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    eval_mesh = eval_obj.to_mesh()
    print(f"Evaluated GN Mesh: {len(eval_mesh.vertices)} verts, {len(eval_mesh.polygons)} faces.")
    n_verts = len(eval_mesh.vertices)
    eval_obj.to_mesh_clear()
    assert n_verts > 0, "Geometry Nodes produced empty mesh!"

    print("bp_geonodes verified successfully.")

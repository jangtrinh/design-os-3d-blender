"""
bp_geonodes.py — Procedural Geometry Nodes Boilerplate for Blender 5.2+.

Compliant with Blender 4.0+ / 5.2 LTS interface API (tree.interface.new_socket)
and Blender 5.2 RNA modifier property bindings.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import math
from numbers import Integral, Real
import bpy
from typing import Optional, Any, Tuple


def create_geometry_node_tree(name: str) -> Tuple[bpy.types.GeometryNodeTree, bpy.types.Node, bpy.types.Node]:
    """
    Creates a new GeometryNodeTree with standard Geometry Input and Output sockets.
    Returns: (tree, input_node, output_node).
    """
    if name in bpy.data.node_groups:
        existing = bpy.data.node_groups[name]
        if existing.users:
            raise RuntimeError(
                f"Node group '{name}' is in use by {existing.users} datablock(s); "
                "refusing to delete or replace it"
            )
        raise RuntimeError(
            f"Node group '{name}' already exists; zero users does not establish ownership, "
            "refusing to delete or replace it"
        )

    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    tree.is_modifier = True
    
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
    Assigns a GeometryNodeTree without silently creating duplicate-name modifiers.

    Re-running the same object/name/tree binding is idempotent. Any existing modifier
    with the requested name but a different type or tree is treated as owned state and
    left unchanged.
    """
    existing = obj.modifiers.get(mod_name)
    if existing is not None:
        if existing.type != 'NODES':
            raise RuntimeError(
                f"Modifier '{mod_name}' already exists on '{obj.name}' with type "
                f"'{existing.type}'; refusing to replace it"
            )
        if existing.node_group is tree:
            return existing
        bound_name = existing.node_group.name if existing.node_group is not None else '<none>'
        raise RuntimeError(
            f"Geometry Nodes modifier '{mod_name}' already exists on '{obj.name}' with "
            f"node group '{bound_name}'; refusing to replace it with '{tree.name}'"
        )

    mod = obj.modifiers.new(name=mod_name, type='NODES')
    mod.node_group = tree
    return mod


def _resolve_interface_input(
    tree: bpy.types.GeometryNodeTree,
    socket_name: str,
) -> bpy.types.NodeTreeInterfaceSocket:
    """Resolve an input by stable identifier first, then by unique display name."""
    if not isinstance(socket_name, str) or not socket_name:
        raise TypeError("socket_name must be a non-empty string identifier or interface name")

    inputs = [
        item for item in tree.interface.items_tree
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
    ]

    identifier_matches = [item for item in inputs if item.identifier == socket_name]
    if len(identifier_matches) == 1:
        return identifier_matches[0]
    if len(identifier_matches) > 1:
        raise RuntimeError(
            f"Interface of '{tree.name}' contains duplicate identifier '{socket_name}'"
        )

    name_matches = [item for item in inputs if item.name == socket_name]
    if len(name_matches) == 1:
        return name_matches[0]
    if len(name_matches) > 1:
        ids = ", ".join(item.identifier for item in name_matches)
        raise ValueError(
            f"Input socket name '{socket_name}' is ambiguous on '{tree.name}'; "
            f"use one of these stable identifiers instead: {ids}"
        )

    available = ", ".join(f"{item.name!r} ({item.identifier})" for item in inputs)
    raise KeyError(
        f"Input socket '{socket_name}' not found on interface of '{tree.name}'. "
        f"Available inputs: {available or '<none>'}"
    )


def _validate_range(item: bpy.types.NodeTreeInterfaceSocket, value: Real, label: str) -> None:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"Input '{label}' must be finite, got {value!r}")

    min_value = getattr(item, "min_value", None)
    max_value = getattr(item, "max_value", None)
    if min_value is not None and numeric < float(min_value):
        raise ValueError(
            f"Input '{label}' value {value!r} is below interface minimum {min_value!r}"
        )
    if max_value is not None and numeric > float(max_value):
        raise ValueError(
            f"Input '{label}' value {value!r} is above interface maximum {max_value!r}"
        )


def _validated_modifier_value(
    item: bpy.types.NodeTreeInterfaceSocket,
    entry: Any,
    value: Any,
) -> Any:
    """Validate against the runtime-generated Blender 5.2 RNA value property."""
    value_prop = entry.bl_rna.properties.get("value")
    if value_prop is None:
        raise TypeError(
            f"Input '{item.name}' ({item.identifier}, {item.socket_type}) "
            "does not expose a direct modifier value in Blender 5.2"
        )

    prop_type = value_prop.type
    array_length = int(getattr(value_prop, "array_length", 0) or 0)
    label = f"{item.name} ({item.identifier})"

    if prop_type == 'FLOAT':
        if array_length:
            if isinstance(value, (str, bytes)):
                raise TypeError(
                    f"Input '{label}' expects {array_length} numeric components, got {type(value).__name__}"
                )
            try:
                components = tuple(value)
            except TypeError as exc:
                raise TypeError(
                    f"Input '{label}' expects {array_length} numeric components"
                ) from exc
            if len(components) != array_length:
                raise TypeError(
                    f"Input '{label}' expects {array_length} numeric components, got {len(components)}"
                )
            normalized = []
            for index, component in enumerate(components):
                if isinstance(component, bool) or not isinstance(component, Real):
                    raise TypeError(
                        f"Input '{label}' component {index} must be numeric, got {type(component).__name__}"
                    )
                _validate_range(item, component, f"{item.name}[{index}] ({item.identifier})")
                normalized.append(float(component))
            return tuple(normalized)

        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(
                f"Input '{label}' expects a numeric value, got {type(value).__name__}"
            )
        _validate_range(item, value, label)
        return float(value)

    if prop_type == 'INT':
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(
                f"Input '{label}' expects an integer value, got {type(value).__name__}"
            )
        _validate_range(item, value, label)
        return int(value)

    if prop_type == 'BOOLEAN':
        if type(value) is not bool:
            raise TypeError(
                f"Input '{label}' expects bool, got {type(value).__name__}"
            )
        return value

    if prop_type == 'STRING':
        if not isinstance(value, str):
            raise TypeError(
                f"Input '{label}' expects str, got {type(value).__name__}"
            )
        return value

    if prop_type == 'POINTER':
        if value is None:
            return None
        fixed_type = getattr(value_prop, "fixed_type", None)
        expected = getattr(bpy.types, getattr(fixed_type, "identifier", ""), None)
        if expected is None or not isinstance(value, expected):
            expected_name = getattr(fixed_type, "identifier", "Blender datablock")
            raise TypeError(
                f"Input '{label}' expects {expected_name}, got {type(value).__name__}"
            )
        return value

    raise TypeError(
        f"Input '{label}' uses unsupported RNA value type '{prop_type}'"
    )


def set_modifier_input(mod: bpy.types.NodesModifier, socket_name: str, value: Any) -> None:
    """
    Set a Blender 5.2 Geometry Nodes modifier input by identifier or unique name.

    Stable interface identifiers are preferred. Display names remain supported for
    existing callers only when exactly one INPUT socket has that name. Type/range
    validation completes before the modifier is mutated.
    """
    if bpy.app.version < (5, 2, 0):
        raise RuntimeError(
            f"set_modifier_input requires Blender 5.2+ RNA modifier inputs, got {bpy.app.version_string}"
        )

    tree = mod.node_group
    if not tree:
        raise ValueError(f"Geometry Nodes modifier '{mod.name}' has no node group")
    if tree.bl_idname != 'GeometryNodeTree':
        raise TypeError(
            f"Modifier '{mod.name}' node group must be GeometryNodeTree, got {tree.bl_idname}"
        )

    item = _resolve_interface_input(tree, socket_name)
    entry = getattr(mod.properties.inputs, item.identifier, None)
    if entry is None:
        raise RuntimeError(
            f"Blender 5.2 modifier '{mod.name}' has no RNA input property for "
            f"'{item.name}' ({item.identifier})"
        )

    type_prop = entry.bl_rna.properties.get("type")
    modes = {enum_item.identifier for enum_item in type_prop.enum_items} if type_prop else set()
    if 'VALUE' not in modes:
        raise TypeError(
            f"Input '{item.name}' ({item.identifier}) does not support direct VALUE binding"
        )

    normalized = _validated_modifier_value(item, entry, value)
    previous_type = entry.type
    previous_value = tuple(entry.value) if hasattr(entry.value, "__len__") and not isinstance(entry.value, str) else entry.value
    try:
        entry.type = 'VALUE'
        entry.value = normalized
    except Exception:
        try:
            entry.type = previous_type
            entry.value = previous_value
        except Exception:
            pass
        raise
    mod.id_data.update_tag()


if __name__ == '__main__':
    print("Testing bp_geonodes.py headless...")
    
    # Create test object
    mesh = bpy.data.meshes.new("GN_Parametric_Object")
    obj = bpy.data.objects.new("GN_Parametric_Object", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Build Parametric Node Tree: Mesh Cylinder with customizable radius & depth
    tree, in_node, out_node = create_geometry_node_tree("Parametric_Cylinder_Tree")
    
    # Interface Inputs
    radius = add_interface_socket(tree, "Radius", 'INPUT', 'NodeSocketFloat', default_value=0.025, min_value=0.001)
    depth = add_interface_socket(tree, "Depth", 'INPUT', 'NodeSocketFloat', default_value=0.080, min_value=0.001)
    
    # Nodes
    cyl_node = add_node(tree, 'GeometryNodeMeshCylinder', location=(0, 0))
    shade_node = add_node(tree, 'GeometryNodeSetShadeSmooth', location=(300, 0))

    # Wiring
    connect(tree, in_node, radius.identifier, cyl_node, "Radius")
    connect(tree, in_node, depth.identifier, cyl_node, "Depth")
    connect(tree, cyl_node, "Mesh", shade_node, "Mesh")
    connect(tree, shade_node, "Mesh", out_node, "Geometry")

    # Modifier setup & driving
    mod = assign_geonodes_modifier(obj, tree)
    set_modifier_input(mod, radius.identifier, 0.050)
    set_modifier_input(mod, "Depth", 0.120)

    # Evaluation test
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    eval_mesh = eval_obj.to_mesh()
    xs = [vert.co.x for vert in eval_mesh.vertices]
    ys = [vert.co.y for vert in eval_mesh.vertices]
    zs = [vert.co.z for vert in eval_mesh.vertices]
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    print(f"Evaluated GN Mesh: {len(eval_mesh.vertices)} verts, {len(eval_mesh.polygons)} faces, dims={dims}.")
    n_verts = len(eval_mesh.vertices)
    eval_obj.to_mesh_clear()
    assert n_verts > 0, "Geometry Nodes produced empty mesh!"
    assert all(abs(value - expected) < 1e-5 for value, expected in zip(dims, (0.100, 0.100, 0.120))), dims

    print("bp_geonodes verified successfully.")

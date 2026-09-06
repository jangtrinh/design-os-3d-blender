"""
bp_core.py — Core Foundation Boilerplate for Blender 5.2+ bpy Scripts.

Designed for AI agent reuse, headless execution, and zero-context-dependence.
Target: Blender 5.2 LTS (macOS / Linux / Windows).
"""

from __future__ import annotations
import bpy
from typing import Optional, Any, List, Tuple


def clean_scene(keep_camera_and_lights: bool = False) -> None:
    """
    Idempotently clears the active scene without invoking fragile operators.
    Purges unlinked meshes, materials, collections, and node groups.
    """
    # Ensure Object Mode
    if bpy.context.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

    # Remove objects
    for obj in list(bpy.data.objects):
        if keep_camera_and_lights and obj.type in {'CAMERA', 'LIGHT'}:
            continue
        bpy.data.objects.remove(obj, do_unlink=True)

    # Purge orphaned data blocks
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    for arm in list(bpy.data.armatures):
        if arm.users == 0:
            bpy.data.armatures.remove(arm)
    for ng in list(bpy.data.node_groups):
        if ng.users == 0:
            bpy.data.node_groups.remove(ng)
    for cam in list(bpy.data.cameras):
        if not keep_camera_and_lights and cam.users == 0:
            bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        if not keep_camera_and_lights and light.users == 0:
            bpy.data.lights.remove(light)


def get_or_create_collection(name: str, parent: Optional[bpy.types.Collection] = None) -> bpy.types.Collection:
    """
    Idempotent collection getter/creator. Links to scene collection if parent is None.
    """
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        target_parent = parent or bpy.context.scene.collection
        target_parent.children.link(col)
    return col


def create_mesh_object(name: str, collection: Optional[bpy.types.Collection] = None) -> Tuple[bpy.types.Object, bpy.types.Mesh]:
    """
    Creates an empty mesh and object data-block, linked to the given collection.
    Avoids duplicate name accumulation.
    """
    # Remove existing object with the same name if present
    if name in bpy.data.objects:
        old_obj = bpy.data.objects[name]
        bpy.data.objects.remove(old_obj, do_unlink=True)
    if name in bpy.data.meshes:
        old_mesh = bpy.data.meshes[name]
        bpy.data.meshes.remove(old_mesh, do_unlink=True)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    target_col = collection or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj, mesh


def get_evaluated_mesh(obj: bpy.types.Object, depsgraph: Optional[bpy.types.Depsgraph] = None) -> bpy.types.Mesh:
    """
    Extracts the evaluated mesh (post-modifiers/geometry nodes) via depsgraph
    without destructive operator application. Must be freed with obj.to_mesh_clear().
    """
    if depsgraph is None:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    return eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)


def safe_get_socket(node: bpy.types.Node, identifier_or_name: str | int, is_output: bool = False) -> Optional[bpy.types.NodeSocket]:
    """
    Robust runtime socket retriever for Shader and Geometry nodes.
    Prevents KeyError when socket names change across Blender versions.
    Checks:
      1. Exact match by name
      2. Exact match by identifier
      3. Index lookup if int
      4. Case-insensitive substring match
    """
    sockets = node.outputs if is_output else node.inputs
    if isinstance(identifier_or_name, int):
        if 0 <= identifier_or_name < len(sockets):
            return sockets[identifier_or_name]
        return None

    # Check direct dictionary lookup (name or identifier)
    if identifier_or_name in sockets:
        return sockets[identifier_or_name]

    # Search by identifier or case-insensitive name
    query_lower = identifier_or_name.lower()
    for s in sockets:
        if s.identifier == identifier_or_name:
            return s
        if s.name.lower() == query_lower:
            return s
        if query_lower in s.name.lower():
            return s

    return None


def dump_node_sockets(node: bpy.types.Node) -> str:
    """
    Introspection utility: returns formatted string of all input/output socket names and identifiers.
    Use for debugging when node connection fails.
    """
    in_str = ", ".join(f"'{s.name}' (id: '{s.identifier}', type: {s.type})" for s in node.inputs)
    out_str = ", ".join(f"'{s.name}' (id: '{s.identifier}', type: {s.type})" for s in node.outputs)
    return f"Node '{node.name}' ({node.bl_idname}):\n  Inputs: [{in_str}]\n  Outputs: [{out_str}]"


def ensure_mode(mode: str = 'OBJECT') -> None:
    """
    Safely transitions to the requested interaction mode.
    """
    if bpy.context.mode != mode:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode=mode)


if __name__ == '__main__':
    print("Testing bp_core.py headless...")
    clean_scene()
    col = get_or_create_collection("Test_Collection")
    obj, mesh = create_mesh_object("Test_Box", col)
    print(f"Created: {obj.name} in {col.name}")

    # Postconditions: the collection exists and is linked to the scene, the object is
    # linked to it, and the depsgraph round-trip returns the same (empty) mesh.
    scene_children = {c.name for c in bpy.context.scene.collection.children}
    assert col.name in bpy.data.collections, "collection datablock missing"
    assert col.name in scene_children, f"{col.name} not linked to the scene collection"
    assert obj.name in col.objects, f"{obj.name} not linked to {col.name}"
    assert obj.data is mesh, "object is not using the mesh it was created with"
    evaluated = get_evaluated_mesh(obj)
    n_verts = len(evaluated.vertices)
    obj.to_mesh_clear()
    assert n_verts == len(mesh.vertices) == 0, f"evaluated verts {n_verts}, source {len(mesh.vertices)}"
    assert safe_get_socket(bpy.data.materials.new("probe").node_tree.nodes.new(
        'ShaderNodeBsdfPrincipled'), "Base Color") is not None, "socket lookup failed"
    print(f"Asserts OK: 1 collection, 1 object, evaluated verts = {n_verts}")
    print("bp_core verified successfully.")

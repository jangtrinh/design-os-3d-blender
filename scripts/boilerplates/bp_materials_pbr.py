"""
bp_materials_pbr.py — Physically Based Shading & Node Boilerplate.

Target: Blender 5.2 LTS (OpenPBR / Principled BSDF).
Safe socket resolution against 4.x / 5.x naming shifts.
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple


def create_pbr_material(
    name: str,
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.4,
    ior: float = 1.5,
    transmission: float = 0.0
) -> bpy.types.Material:
    """
    Creates a node-based PBR material with Blender 5.2 Principled BSDF.
    """
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])

    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    tree.nodes.clear()

    # Create Core Nodes
    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (400, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Robust socket setter
    def set_bsdf_input(socket_name: str, val):
        if socket_name in bsdf.inputs:
            bsdf.inputs[socket_name].default_value = val
        else:
            # Fallback search
            q = socket_name.lower().replace(" ", "")
            for inp in bsdf.inputs:
                if inp.name.lower().replace(" ", "") == q:
                    inp.default_value = val
                    return

    set_bsdf_input("Base Color", base_color)
    set_bsdf_input("Metallic", metallic)
    set_bsdf_input("Roughness", roughness)
    set_bsdf_input("IOR", ior)
    set_bsdf_input("Transmission Weight", transmission)

    # Link BSDF to Output
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat


def add_procedural_micro_roughness(
    mat: bpy.types.Material,
    scale: float = 50.0,
    detail: float = 6.0,
    roughness_min: float = 0.3,
    roughness_max: float = 0.6
) -> None:
    """
    Adds procedural fractal noise to vary surface micro-roughness.
    Prevents unrealistic CG plastic/mirror uniformity.
    """
    tree = mat.node_tree
    bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return

    tex_coord = tree.nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 100)

    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, 100)
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = detail

    map_range = tree.nodes.new('ShaderNodeMapRange')
    map_range.location = (-200, 100)
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = roughness_min
    map_range.inputs['To Max'].default_value = roughness_max

    # Wiring
    tree.links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    tree.links.new(noise.outputs['Fac'], map_range.inputs['Value'])
    tree.links.new(map_range.outputs['Result'], bsdf.inputs['Roughness'])


def assign_material_to_object(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    """Assigns material to object, replacing slot 0 or adding if empty."""
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


if __name__ == '__main__':
    print("Testing bp_materials_pbr.py headless...")
    mat = create_pbr_material("Anodized_Titanium", base_color=(0.15, 0.16, 0.18, 1.0), metallic=0.95, roughness=0.35)
    add_procedural_micro_roughness(mat, scale=80.0, detail=5.0, roughness_min=0.25, roughness_max=0.45)
    print(f"Created Material: '{mat.name}' with {len(mat.node_tree.nodes)} shader nodes.")

    # Postconditions: a Principled BSDF exists, the values passed in were actually written
    # to its sockets, and the micro-roughness chain is fully wired (4 links).
    tree = mat.node_tree
    bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    assert bsdf is not None, "no Principled BSDF in the material"
    assert abs(bsdf.inputs["Metallic"].default_value - 0.95) < 1e-6, bsdf.inputs["Metallic"].default_value
    assert abs(bsdf.inputs["IOR"].default_value - 1.5) < 1e-6, bsdf.inputs["IOR"].default_value
    base = tuple(round(v, 4) for v in bsdf.inputs["Base Color"].default_value)
    assert base == (0.15, 0.16, 0.18, 1.0), base
    assert len(tree.links) == 4, f"expected 4 links, got {len(tree.links)}"
    rough_link = next((l for l in tree.links
                       if l.to_node == bsdf and l.to_socket.name == "Roughness"), None)
    assert rough_link is not None and rough_link.from_node.type == 'MAP_RANGE', "roughness not driven by Map Range"
    print(f"Asserts OK: metallic 0.95, base {base}, {len(tree.links)} links, roughness driven by Map Range")
    print("bp_materials_pbr verified successfully.")

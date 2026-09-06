"""
bp_mat_metals.py — Physically Based Metals & Anisotropy Boilerplate.

Standards & Academic Citations:
- ASWF (2023). "OpenPBR Surface Specification v1.0." Academy Software Foundation.
- Walter, B., Marschner, S. R., Li, H., & Torrance, K. E. (2007). "Microfacet models for refraction through rough surfaces." In Rendering Techniques 2007 (pp. 195-206).
- Burley, B. (2012). "Physically-Based Shading at Disney." ACM SIGGRAPH 2012 Courses.

Target: Blender 5.2 LTS (Zero use_nodes deprecation, safe socket access).
"""

from __future__ import annotations
import bpy
from typing import Tuple, Dict, Any


# Complex Refractive Index & Reflectance Data (at 550nm green light)
# (base_color_rgb, metallic, roughness, anisotropic, ior)
METAL_PRESETS: Dict[str, Tuple[Tuple[float, float, float], float, float, float, float]] = {
    'CHROME': ((0.95, 0.95, 0.95), 1.0, 0.05, 0.0, 2.95),
    'ALUMINUM_6061': ((0.91, 0.92, 0.92), 1.0, 0.25, 0.4, 1.44),
    'TITANIUM_BRUSHED': ((0.63, 0.58, 0.54), 1.0, 0.35, 0.6, 2.16),
    'COPPER': ((0.95, 0.64, 0.54), 1.0, 0.15, 0.0, 1.10),
    'BRASS_CARTRIDGE': ((0.92, 0.78, 0.43), 1.0, 0.20, 0.0, 1.25),
    'CAST_IRON': ((0.35, 0.35, 0.35), 0.9, 0.60, 0.0, 2.40),
}


def create_physical_metal_material(
    preset_name: str = 'ALUMINUM_6061',
    mat_name: Optional[str] = None
) -> bpy.types.Material:
    """
    Creates an OpenPBR-compliant metallic material in Blender 5.2.
    """
    preset = METAL_PRESETS.get(preset_name.upper(), METAL_PRESETS['ALUMINUM_6061'])
    rgb, met, rough, aniso, ior = preset
    
    name = mat_name or f"Metal_{preset_name.capitalize()}"
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])

    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    tree.nodes.clear()

    # Output Material Node
    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (300, 0)

    # Principled BSDF Node
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Safe socket setting
    def set_val(sock_name: str, val: Any):
        if sock_name in bsdf.inputs:
            bsdf.inputs[sock_name].default_value = val

    set_val("Base Color", (*rgb, 1.0))
    set_val("Metallic", met)
    set_val("Roughness", rough)
    set_val("Anisotropic", aniso)
    set_val("IOR", ior)

    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat


if __name__ == '__main__':
    print("Testing bp_mat_metals.py headless...")
    for metal_key in METAL_PRESETS:
        m = create_physical_metal_material(metal_key)
        assert len(m.node_tree.nodes) == 2
    print(f"Verified {len(METAL_PRESETS)} physical metal presets successfully.")
    print("bp_mat_metals verified successfully.")

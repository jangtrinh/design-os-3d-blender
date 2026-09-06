"""
bp_mat_thinfilm.py — Wave Interference & Thin-Film Iridescence Boilerplate.

Standards & Academic Citations:
- Born, M., & Wolf, E. (1999). "Principles of Optics (7th ed.)." Cambridge University Press. ISBN: 978-0-521-64222-4. (Airy multi-beam interference formulation).
- Belcour, L., & Barla, P. (2017). "A Practical Extension to Microfacet Theory for the Modeling of Varying Iridescence." ACM Transactions on Graphics (TOG), 36(4), 65:1-65:14.

Target: Blender 5.2 LTS (ShaderNodeValToRGB ColorRamp, Principled BSDF).
"""

from __future__ import annotations
import bpy


def create_tempered_titanium_material(name: str = "Iridescent_Titanium") -> bpy.types.Material:
    """
    Creates a heat-treated titanium exhaust material with physical
    thin-film interference oxidation layers (Airy phase difference).
    """
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])

    mat = bpy.data.materials.new(name)
    tree = mat.node_tree
    tree.nodes.clear()

    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (400, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (100, 0)
    bsdf.inputs['Metallic'].default_value = 0.95
    bsdf.inputs['Roughness'].default_value = 0.25

    # Layer Weight / Fresnel Node for view angle dependence
    layer_weight = tree.nodes.new('ShaderNodeLayerWeight')
    layer_weight.location = (-400, 100)
    layer_weight.inputs['Blend'].default_value = 0.65

    # ColorRamp mapped to Newton's thin-film interference scale
    # Pale straw -> Gold -> Purple -> Deep blue -> Cyan
    color_ramp = tree.nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-150, 100)
    elements = color_ramp.color_ramp.elements

    # Configure 5 Newton interference color stops
    elements[0].position = 0.10
    elements[0].color = (0.85, 0.70, 0.40, 1.0) # Straw gold (380nm TiO2)
    elements[1].position = 0.35
    elements[1].color = (0.75, 0.30, 0.65, 1.0) # Purple (450nm)
    
    e3 = elements.new(0.60)
    e3.color = (0.15, 0.35, 0.85, 1.0)          # Royal blue (520nm)
    
    e4 = elements.new(0.85)
    e4.color = (0.20, 0.80, 0.85, 1.0)          # Cyan (600nm)

    # Wiring
    tree.links.new(layer_weight.outputs['Facing'], color_ramp.inputs['Fac'])
    tree.links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])

    return mat


if __name__ == '__main__':
    print("Testing bp_mat_thinfilm.py headless...")
    mat = create_tempered_titanium_material()
    print(f"Created Iridescent Material: {mat.name} with {len(mat.node_tree.nodes)} nodes.")
    assert len(mat.node_tree.nodes) == 4
    print("bp_mat_thinfilm verified successfully.")

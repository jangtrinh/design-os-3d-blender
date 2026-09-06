"""
bp_fur_hair_shader.py — Melanin-Based Biochemical Hair & Fur Shader for Curves.

Standards & Academic Citations:
- Marschner et al. (2003): "Light Scattering from Human Hair Fibers" (R, TT, TRT Specular Lobes).
- Chiang et al. (2016): "A Practical and Controllable Hair and Fur Model for Production Path
  Tracing" — the model Blender exposes as ShaderNodeBsdfHairPrincipled.model = 'CHIANG'.
- d'Eon et al. (2011): "An Energy-Conserving Hair Reflectance Model" (melanin absorption).

Target: Blender 5.2 LTS (Data-API Node Trees, Principled Hair BSDF, Hair Curves, Headless-Safe).

Runtime-verified 2026-09-06 against Blender 5.2.0 LTS: parametrization enum is
{ABSORPTION, MELANIN, COLOR}; `model` enum is {CHIANG, HUANG} (default CHIANG); the sockets
enabled under MELANIN are Melanin, Melanin Redness, Tint, Roughness, Radial Roughness, Coat,
IOR, Offset, Random Color, Random Roughness, Random. The strand-info node is created with
`ShaderNodeHairInfo` but is *named* "Curves Info" in 5.2; its outputs are Is Strand,
Intercept, Length, Thickness, Tangent Normal, Random. Root-to-tip gradients must be driven
by `Intercept` (0 at root, 1 at tip) — `Is Strand` is constant on a strand.
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple


def create_melanin_hair_material(
    name: str = "M_Melanin_Hair",
    melanin_conc: float = 0.65,      # 0.0=Albino/White, 0.2=Blonde, 0.65=Brown, 0.95=Black
    melanin_redness: float = 0.35,   # Ratio of Pheomelanin to Eumelanin
    roughness: float = 0.28,         # Longitudinal roughness along keratin cuticle
    radial_roughness: float = 0.32,  # Azimuthal cross-section roughness
    coat: float = 0.25,              # Cuticle oil / conditioner shine
    random_color_variation: float = 0.15
) -> bpy.types.Material:
    """
    Creates a production-quality biochemical hair and fur material for Blender 5.2 Curves
    using the Principled Hair BSDF in MELANIN parametrization mode.
    """
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # 1. Output Node
    out_node = nodes.new(type='ShaderNodeOutputMaterial')
    out_node.location = (500, 0)

    # 2. Principled Hair BSDF
    hair_bsdf = nodes.new(type='ShaderNodeBsdfHairPrincipled')
    hair_bsdf.location = (150, 0)

    hair_bsdf.parametrization = 'MELANIN'
    hair_bsdf.model = 'CHIANG'   # Chiang et al. 2016; the alternative in 5.2 is 'HUANG'

    # Set Biochemical Pigmentation
    hair_bsdf.inputs['Melanin'].default_value = melanin_conc
    hair_bsdf.inputs['Melanin Redness'].default_value = melanin_redness
    hair_bsdf.inputs['Roughness'].default_value = roughness
    hair_bsdf.inputs['Radial Roughness'].default_value = radial_roughness
    hair_bsdf.inputs['Coat'].default_value = coat
    hair_bsdf.inputs['IOR'].default_value = 1.55  # Keratin fiber refractive index
    hair_bsdf.inputs['Random Color'].default_value = random_color_variation

    # 3. Strand-info node ("Curves Info" in 5.2) for root-to-tip variation.
    hair_info = nodes.new(type='ShaderNodeHairInfo')
    hair_info.location = (-350, 0)

    # Subtle root-to-tip lightening (tips bleached by solar UV), driven by Intercept.
    ramp = nodes.new(type='ShaderNodeValToRGB')
    ramp.location = (-100, 100)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)  # Root: untinted
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.85, 0.82, 0.78, 1.0)  # Tip: subtle UV bleaching

    links.new(hair_info.outputs['Intercept'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], hair_bsdf.inputs['Tint'])
    links.new(hair_bsdf.outputs['BSDF'], out_node.inputs['Surface'])

    return mat


def apply_hair_material(hair_obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    """Assigns hair material to Curves or Mesh object."""
    if hair_obj.data.materials:
        hair_obj.data.materials[0] = mat
    else:
        hair_obj.data.materials.append(mat)


if __name__ == '__main__':
    print("Testing bp_fur_hair_shader.py headless...")
    mat = create_melanin_hair_material("Test_Melanin_Groom", melanin_conc=0.7, melanin_redness=0.3)
    assert mat is not None, "Failed to create hair material"
    assert "Principled Hair BSDF" in mat.node_tree.nodes, "Missing Principled Hair BSDF node"

    hbsdf = mat.node_tree.nodes["Principled Hair BSDF"]
    assert hbsdf.parametrization == 'MELANIN', f"Expected MELANIN, got {hbsdf.parametrization}"
    assert hbsdf.model == 'CHIANG', f"Expected CHIANG model, got {hbsdf.model}"
    assert abs(hbsdf.inputs["Melanin"].default_value - 0.7) < 1e-4, "Melanin concentration mismatch"
    assert abs(hbsdf.inputs["IOR"].default_value - 1.55) < 1e-4, "Keratin IOR mismatch"
    assert hbsdf.inputs["Tint"].is_linked, "root-to-tip ramp is not wired into the BSDF"

    # Every non-output node must feed something: a dangling ramp renders nothing.
    for node in mat.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            continue
        assert any(o.is_linked for o in node.outputs), f"dangling node: {node.name}"

    # End-to-end on a real Curves object with geometry (no bpy.ops anywhere).
    curves_data = bpy.data.hair_curves.new("Test_Hair_Curves")
    curves_data.add_curves([4, 4])
    for i, point in enumerate(curves_data.points):
        point.position = (0.0, 0.0, i * 0.01)
    hair_obj = bpy.data.objects.new("Test_Hair_Curves", curves_data)
    bpy.context.scene.collection.objects.link(hair_obj)

    apply_hair_material(hair_obj, mat)
    assert hair_obj.type == 'CURVES', hair_obj.type
    assert len(curves_data.curves) == 2 and len(curves_data.points) == 8
    assert hair_obj.data.materials[0] == mat, "Failed to assign material to hair curves"

    print(f"Asserts OK: MELANIN/{hbsdf.model}, IOR 1.55, Tint wired, "
          f"{len(curves_data.curves)} strands materialised.")
    print("bp_fur_hair_shader verified successfully.")

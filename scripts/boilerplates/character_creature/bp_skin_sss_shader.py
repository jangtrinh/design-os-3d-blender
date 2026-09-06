"""
bp_skin_sss_shader.py — Production Physically-Based Human Skin Shader (Random Walk Skin SSS).

Standards & Academic Citations:
- Christensen & Burley (2015): "Approximate Reflectance Profiles for Efficient Subsurface
  Scattering" — this is the normalized-diffusion profile Cycles exposes as subsurface_method
  'BURLEY'. It is NOT the method set below: 'RANDOM_WALK_SKIN' is a volumetric random-walk
  path-tracing method with a skin-tuned phase/IOR setup. Do not conflate the two.
- Igarashi, Nishino & Nayar (2007): "The Appearance of Human Skin: A Survey" (epidermal /
  dermal optics; source of the red-deep / blue-shallow scattering asymmetry).

Target: Blender 5.2 LTS (Data-API Node Trees, Principled BSDF v2 RANDOM_WALK_SKIN, Headless-Safe).

Runtime-verified 2026-09-06 against Blender 5.2.0 LTS: subsurface_method enum is
{BURLEY, RANDOM_WALK, RANDOM_WALK_SKIN, RANDOM_WALK_LEGACY}. The sockets 'Subsurface Weight',
'Subsurface Radius', 'Subsurface Scale', 'Subsurface IOR' and 'Subsurface Anisotropy' all
exist, but 'Subsurface IOR' is DISABLED under the default BURLEY method and a disabled socket
is not reachable by name (`inputs['Subsurface IOR']` raises KeyError) — set
subsurface_method first, as this module does. Blender's own default Subsurface Radius is
(1.0, 0.2, 0.1); the (1.0, 0.22, 0.08) used here is an artistic variant, not a published
standard value.
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple


def create_procedural_skin_material(
    name: str = "M_Human_Skin_SSS",
    base_tone_rgb: Tuple[float, float, float] = (0.78, 0.56, 0.44),
    subsurface_scale_m: float = 0.025,
    blood_radius_rgb: Tuple[float, float, float] = (1.0, 0.22, 0.08),
    sebum_coat_weight: float = 0.20
) -> bpy.types.Material:
    """
    Creates a production-ready, physically grounded human skin material using
    Random Walk Skin Subsurface Scattering, dual-lobe specular coat, and micro-pore bump.
    """
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # 1. Output Node
    out_node = nodes.new(type='ShaderNodeOutputMaterial')
    out_node.location = (600, 0)

    # 2. Principled BSDF (Blender 5.2 v2)
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    # Must be set BEFORE touching Subsurface IOR: that socket is disabled (and therefore
    # not addressable by name) while the default BURLEY method is active.
    bsdf.subsurface_method = 'RANDOM_WALK_SKIN'

    # Set Optical Properties
    bsdf.inputs['Base Color'].default_value = (*base_tone_rgb, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.42
    bsdf.inputs['IOR'].default_value = 1.40  # Keratin / Epidermal refractive index

    # Subsurface Scattering Parameters
    bsdf.inputs['Subsurface Weight'].default_value = 1.0
    bsdf.inputs['Subsurface Radius'].default_value = blood_radius_rgb
    bsdf.inputs['Subsurface Scale'].default_value = subsurface_scale_m
    bsdf.inputs['Subsurface IOR'].default_value = 1.40
    bsdf.inputs['Subsurface Anisotropy'].default_value = 0.75  # Forward tissue scattering

    # Dual-lobe sebum / lipid coat layer
    bsdf.inputs['Coat Weight'].default_value = sebum_coat_weight
    bsdf.inputs['Coat Roughness'].default_value = 0.08
    bsdf.inputs['Coat IOR'].default_value = 1.46

    # 3. Procedural Micro-Pore Normal Bump
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, -200)

    noise_pores = nodes.new(type='ShaderNodeTexNoise')
    noise_pores.location = (-400, -200)
    noise_pores.inputs['Scale'].default_value = 250.0  # High-frequency micro-pores
    noise_pores.inputs['Detail'].default_value = 4.0
    noise_pores.inputs['Roughness'].default_value = 0.65

    bump = nodes.new(type='ShaderNodeBump')
    bump.location = (-100, -200)
    bump.inputs['Strength'].default_value = 0.08  # Subtle epidermal displacement
    bump.inputs['Distance'].default_value = 0.001

    # Wire nodes
    links.new(tex_coord.outputs['Object'], noise_pores.inputs['Vector'])
    links.new(noise_pores.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])

    return mat


def apply_skin_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    """Assigns or replaces material on mesh object."""
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


if __name__ == '__main__':
    import bmesh
    from mathutils import Matrix

    print("Testing bp_skin_sss_shader.py headless...")
    mat = create_procedural_skin_material()
    assert mat is not None, "Failed to create skin material"
    assert "Principled BSDF" in mat.node_tree.nodes, "Missing Principled BSDF node"

    bsdf = mat.node_tree.nodes["Principled BSDF"]
    assert bsdf.subsurface_method == 'RANDOM_WALK_SKIN', bsdf.subsurface_method
    assert bsdf.inputs["Subsurface Weight"].default_value == 1.0, "SSS weight should be 1.0"
    radius = list(bsdf.inputs["Subsurface Radius"].default_value)
    assert abs(radius[0] - 1.0) < 1e-3, "Red scattering radius should be 1.0"
    assert abs(radius[1] - 0.22) < 1e-3, "Green scattering radius should be 0.22"
    assert abs(radius[2] - 0.08) < 1e-3, "Blue scattering radius should be 0.08"
    assert radius[0] > radius[1] > radius[2], "red must scatter deepest in skin"
    assert abs(bsdf.inputs["Subsurface IOR"].default_value - 1.40) < 1e-4, "Subsurface IOR"
    assert abs(bsdf.inputs["Coat Weight"].default_value - 0.20) < 1e-4, "sebum coat weight"
    assert bsdf.inputs["Normal"].is_linked, "micro-pore bump chain is not wired"
    for node in mat.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            continue
        assert any(o.is_linked for o in node.outputs), f"dangling node: {node.name}"

    # Assignment on a data-API sphere (no bpy.ops; project rule: data API first).
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.1, matrix=Matrix())
    sphere_mesh = bpy.data.meshes.new("Skin_Test_Sphere")
    bm.to_mesh(sphere_mesh)
    bm.free()
    sphere = bpy.data.objects.new(sphere_mesh.name, sphere_mesh)
    bpy.context.scene.collection.objects.link(sphere)
    apply_skin_material(sphere, mat)
    assert sphere.data.materials[0] == mat, "Material assignment failed"

    print(f"Asserts OK: RANDOM_WALK_SKIN, radius {tuple(round(r, 3) for r in radius)}, "
          "SS IOR 1.40, coat 0.20, bump wired.")
    print("bp_skin_sss_shader verified successfully.")

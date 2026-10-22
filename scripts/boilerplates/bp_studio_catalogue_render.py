"""
bp_studio_catalogue_render.py — Commercial Studio Catalogue 6-Shot Pipeline & Decoupled PBR Shaders.

Target: Blender 5.2.0 LTS (Cycles Metal/GPU on macOS, CPU fallback, AgX OCIO).
Enforces:
1. CAD Geometry Lockdown (100% vertex coordinate preservation).
2. Decoupled PBR shader architecture (grain/bump/roughness vs color tint).
3. Automated Face vs CutEdge normal-based material slotting for multiplex plywood.
4. Standardized 6-shot studio camera rig (front, side, top, 3/4 beauty, overview, details macro).
5. 3-point grazing chiaroscuro area light triad + shadow-catcher ground plane + AgX.
6. Structured AI Refine Kit manifest export with explicit media authority provenance.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bpy
from mathutils import Vector

# Import agent_runtime for sentinel contract
try:
    _this_file = Path(__file__).resolve()
    repo_scripts = _this_file.parent.parent
except Exception:
    repo_scripts = Path("/Users/jangtrinh/Products/design-os-3d-blender/scripts")
if str(repo_scripts) not in sys.path:
    sys.path.insert(0, str(repo_scripts))

import agent_runtime as rt


def compute_mesh_vertex_sha256(obj: bpy.types.Object) -> str:
    """Computes a deterministic SHA-256 hash of all mesh vertex coordinates.
    Used to mathematically verify CAD Geometry Lockdown (zero coordinate drift).
    """
    if obj.type != 'MESH' or not obj.data:
        raise ValueError(f"Object {obj.name} is not a valid mesh.")
    hasher = hashlib.sha256()
    for v in obj.data.vertices:
        hasher.update(f"{v.co.x:.7f},{v.co.y:.7f},{v.co.z:.7f};".encode("utf-8"))
    return hasher.hexdigest()


def find_socket(node: bpy.types.Node, *candidates: str, inputs: bool = True) -> Optional[bpy.types.NodeSocket]:
    """Finds the first active socket matching any candidate name (case-insensitive).
    Version-proof across Blender 4.x and 5.x.
    """
    coll = node.inputs if inputs else node.outputs
    names = {s.name.lower(): s for s in coll if not getattr(s, "is_unavailable", False)}
    for c in candidates:
        s = names.get(c.lower())
        if s is not None:
            return s
    # Prefix fallback
    for c in candidates:
        for s in coll:
            if not getattr(s, "is_unavailable", False) and s.name.lower().startswith(c.lower()):
                return s
    return None


def slot_plywood_face_vs_cutedge(
    obj: bpy.types.Object,
    dominant_axis: str = 'Z',
    dot_threshold: float = 0.85
) -> dict:
    """Assigns slot 0 ('Plywood_Face') to faces whose normal aligns with dominant_axis
    (|n . a| >= dot_threshold) and slot 1 ('Plywood_CutEdge_Multiplex') to peripheral
    cut-edge faces.

    CRITICAL CAD GEOMETRY LOCKDOWN:
    This operation only mutates polygon material indices; it strictly never modifies
    vertex coordinates, edge topology, or dimensions.
    """
    if obj.type != 'MESH':
        raise ValueError(f"Target object '{obj.name}' is not a mesh.")

    axis_map = {
        'X': Vector((1.0, 0.0, 0.0)),
        'Y': Vector((0.0, 1.0, 0.0)),
        'Z': Vector((0.0, 0.0, 1.0)),
    }
    axis_vec = axis_map.get(dominant_axis.upper(), Vector((0.0, 0.0, 1.0)))

    mesh = obj.data

    # Ensure material slots exist
    while len(mesh.materials) < 2:
        if len(mesh.materials) == 0:
            mat_face = bpy.data.materials.get("Plywood_Face") or bpy.data.materials.new("Plywood_Face")
            mesh.materials.append(mat_face)
        elif len(mesh.materials) == 1:
            mat_edge = bpy.data.materials.get("Plywood_CutEdge_Multiplex") or bpy.data.materials.new("Plywood_CutEdge_Multiplex")
            mesh.materials.append(mat_edge)

    face_count = 0
    cutedge_count = 0

    for poly in mesh.polygons:
        # Measure alignment with dominant axis
        alignment = abs(poly.normal.dot(axis_vec))
        if alignment >= dot_threshold:
            poly.material_index = 0
            face_count += 1
        else:
            poly.material_index = 1
            cutedge_count += 1

    mesh.update()

    return {
        "face_count": face_count,
        "cutedge_count": cutedge_count,
        "total_polygons": len(mesh.polygons),
        "dominant_axis": dominant_axis,
        "dot_threshold": dot_threshold,
        "geometry_locked": True,
    }


def build_decoupled_stain_pbr_material(
    name: str,
    tint_rgba: Tuple[float, float, float, float] = (0.12, 0.24, 0.52, 1.0),
    bevel_radius_m: float = 0.0006
) -> bpy.types.Material:
    """Creates a Blender 5.2 OpenPBR ShaderNodeBsdfPrincipled material with decoupled
    grain/roughness vs color-stain control, plus a non-destructive ShaderNodeBevel micro-bevel.

    Architecture:
    1. Texture Coordinate (Object) -> Mapping -> TexNoise drives:
       - Grain & Surface Micro-Relief Branch: Bump (Normal) + Roughness ColorRamp (0.25 - 0.45)
       - Coat Weight (0.25) for lacquer protection sheen
    2. Color Tint / Stain Branch:
       - ShaderNodeMix (RGBA, MULTIPLY) combining wood grain variation with independent tint_rgba.
       - Changing stain color preserves 100% of grain contrast and roughness.
    3. Micro-Bevel Normal Node:
       - ShaderNodeBevel (radius=bevel_radius_m, samples=4) feeds into Bump.inputs['Normal']
       - Composites 90-degree edge specular highlights without destructive mesh beveling.
    """
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
    else:
        mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.clear()

    # Base nodes
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (800, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (450, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Physical baseline values
    s_ior = find_socket(bsdf, "IOR")
    if s_ior:
        s_ior.default_value = 1.50
    s_coat = find_socket(bsdf, "Coat Weight", "Coat", "Clearcoat")
    if s_coat:
        s_coat.default_value = 0.25
    s_coat_rough = find_socket(bsdf, "Coat Roughness")
    if s_coat_rough:
        s_coat_rough.default_value = 0.03
    s_metal = find_socket(bsdf, "Metallic")
    if s_metal:
        s_metal.default_value = 0.0

    # 1. Micro-Bevel Node (Non-destructive edge highlight)
    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.location = (-100, -250)
    bevel.samples = 4
    bevel.inputs["Radius"].default_value = bevel_radius_m

    # 2. Bump Node (Micro-relief grain)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (150, -150)
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.001
    # Feed Bevel into Bump Normal input
    nt.links.new(bevel.outputs["Normal"], bump.inputs["Normal"])
    # Feed Bump output into Principled BSDF Normal input
    s_normal = find_socket(bsdf, "Normal")
    if s_normal:
        nt.links.new(bump.outputs["Normal"], s_normal)

    # 3. Procedural Wood Grain Coordinates & Texture
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-850, 100)

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.location = (-650, 100)
    # Elongate coordinates along one axis to create directional wood grain
    mapping.inputs["Scale"].default_value = (1.0, 14.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-450, 100)
    noise.inputs["Scale"].default_value = 35.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    noise_fac = find_socket(noise, "Factor", "Fac", inputs=False)
    # Feed noise height to bump
    nt.links.new(noise_fac, bump.inputs["Height"])

    # 4. Roughness Ramp (Satin range 0.25 - 0.45)
    rough_ramp = nt.nodes.new("ShaderNodeValToRGB")
    rough_ramp.location = (-150, 250)
    rough_ramp.color_ramp.elements[0].position = 0.0
    rough_ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1.0)
    rough_ramp.color_ramp.elements[1].position = 1.0
    rough_ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1.0)
    nt.links.new(noise_fac, find_socket(rough_ramp, "Fac", "Factor"))
    s_rough = find_socket(bsdf, "Roughness")
    if s_rough:
        nt.links.new(rough_ramp.outputs["Color"], s_rough)

    # 5. Decoupled Color Tint / Stain Branch
    # Wood grain underlying variation ramp
    wood_albedo_ramp = nt.nodes.new("ShaderNodeValToRGB")
    wood_albedo_ramp.location = (-150, 50)
    wood_albedo_ramp.color_ramp.elements[0].position = 0.0
    wood_albedo_ramp.color_ramp.elements[0].color = (0.75, 0.72, 0.65, 1.0)
    wood_albedo_ramp.color_ramp.elements[1].position = 1.0
    wood_albedo_ramp.color_ramp.elements[1].color = (0.95, 0.92, 0.86, 1.0)
    nt.links.new(noise_fac, find_socket(wood_albedo_ramp, "Fac", "Factor"))

    # Independent Stain Color Node
    tint_node = nt.nodes.new("ShaderNodeRGB")
    tint_node.location = (-150, -100)
    tint_node.outputs["Color"].default_value = tint_rgba

    # Mix ShaderNode (Multiply stain over grain)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.location = (150, 100)
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'

    mix_fac = [s for s in mix.inputs if s.name == "Factor" and not getattr(s, "is_unavailable", False)][0]
    mix_fac.default_value = 1.0
    mix_a = [s for s in mix.inputs if s.name == "A" and s.type == "RGBA" and not getattr(s, "is_unavailable", False)][0]
    mix_b = [s for s in mix.inputs if s.name == "B" and s.type == "RGBA" and not getattr(s, "is_unavailable", False)][0]
    mix_res = [s for s in mix.outputs if s.name == "Result" and s.type == "RGBA" and not getattr(s, "is_unavailable", False)][0]

    nt.links.new(wood_albedo_ramp.outputs["Color"], mix_a)
    nt.links.new(tint_node.outputs["Color"], mix_b)

    s_base_col = find_socket(bsdf, "Base Color")
    if s_base_col:
        nt.links.new(mix_res, s_base_col)

    return mat


def calculate_world_bounding_box(objects: List[bpy.types.Object]) -> Tuple[Vector, float, Vector, Vector]:
    """Computes evaluated world-space bounding box across multiple objects."""
    dg = bpy.context.evaluated_depsgraph_get()
    all_corners = []
    for ob in objects:
        ev = ob.evaluated_get(dg)
        mw = ev.matrix_world
        all_corners.extend(mw @ Vector(c) for c in ev.bound_box)

    if not all_corners:
        return Vector((0.0, 0.0, 0.0)), 1.0, Vector((-0.5, -0.5, -0.5)), Vector((0.5, 0.5, 0.5))

    lo = Vector((min(p.x for p in all_corners), min(p.y for p in all_corners), min(p.z for p in all_corners)))
    hi = Vector((max(p.x for p in all_corners), max(p.y for p in all_corners), max(p.z for p in all_corners)))
    center = (lo + hi) * 0.5
    radius = max((p - center).length for p in all_corners)
    return center, radius, lo, hi


def create_or_update_camera(
    name: str,
    cam_type: str = 'PERSP',
    lens: float = 50.0,
    ortho_scale: float = 2.0,
    location: Vector = Vector((0.0, -2.0, 1.0)),
    target_point: Vector = Vector((0.0, 0.0, 0.0)),
    dof_focus_dist: Optional[float] = None,
    dof_fstop: float = 4.0
) -> bpy.types.Object:
    """Spawns or updates a named studio camera pointing at target_point."""
    cam_data = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam_data.type = cam_type
    cam_data.sensor_fit = 'HORIZONTAL'
    cam_data.sensor_width = 36.0

    if cam_type == 'PERSP':
        cam_data.lens = lens
    elif cam_type == 'ORTHO':
        cam_data.ortho_scale = ortho_scale

    cam_data.clip_start = 0.01
    cam_data.clip_end = 200.0

    if dof_focus_dist is not None:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = dof_focus_dist
        cam_data.dof.aperture_fstop = dof_fstop
    else:
        cam_data.dof.use_dof = False

    cam_obj = bpy.data.objects.get(name)
    if cam_obj is None:
        cam_obj = bpy.data.objects.new(name, cam_data)
        bpy.context.scene.collection.objects.link(cam_obj)
    else:
        cam_obj.data = cam_data

    cam_obj.location = location

    # Orient camera towards target
    fwd = (target_point - cam_obj.location).normalized()
    # Camera forward is -Z, up is Y
    cam_obj.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()

    return cam_obj


def setup_six_shot_studio_rig(target_objects: List[bpy.types.Object]) -> dict:
    """Computes combined world-space bounding box of target_objects and creates:
    1. 6 standardized studio catalogue cameras:
       - 01_front_view (ORTHO)
       - 02_side_view (ORTHO)
       - 03_top_view (ORTHO)
       - 04_3_4_beauty (PERSP 85mm)
       - 05_overview_studio (PERSP 50mm)
       - 06_details_macro (PERSP 100mm f/4.0 DOF)
    2. 3-point Grazing Chiaroscuro Area Light triad:
       - Key_Grazing_Softbox
       - Fill_Softbox
       - Rim_Backlight
    3. Shadow-catcher ground plane (obj.is_shadow_catcher = True)
    4. AgX color management & transparent film setup.
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'None'
    scene.render.film_transparent = True

    center, radius, lo, hi = calculate_world_bounding_box(target_objects)
    extents = hi - lo
    d = max(radius * 2.5, 0.8)

    # 1. Standardized 6 Studio Cameras
    fill_margin = 0.85
    ortho_span = (radius * 2.0) / fill_margin

    # 01_front_view: Orthographic Front Elevation (-Y looking +Y)
    cam_front = create_or_update_camera(
        "01_front_view",
        cam_type='ORTHO',
        ortho_scale=ortho_span,
        location=Vector((center.x, center.y - d, center.z)),
        target_point=center
    )

    # 02_side_view: Orthographic Right Elevation (+X looking -X)
    cam_side = create_or_update_camera(
        "02_side_view",
        cam_type='ORTHO',
        ortho_scale=ortho_span,
        location=Vector((center.x + d, center.y, center.z)),
        target_point=center
    )

    # 03_top_view: Orthographic Plan Elevation (+Z looking -Z)
    cam_top = create_or_update_camera(
        "03_top_view",
        cam_type='ORTHO',
        ortho_scale=ortho_span,
        location=Vector((center.x, center.y, center.z + d)),
        target_point=center
    )
    # Manual roll alignment for top view (up along +Y)
    cam_top.rotation_euler = (0.0, 0.0, 0.0)

    # 04_3_4_beauty: Perspective Hero shot (85mm, flattering proportions)
    beauty_pos = center + Vector((d * 0.75, -d * 0.85, d * 0.55))
    cam_beauty = create_or_update_camera(
        "04_3_4_beauty",
        cam_type='PERSP',
        lens=85.0,
        location=beauty_pos,
        target_point=center
    )

    # 05_overview_studio: Perspective Studio Context (50mm, natural field of view)
    overview_pos = center + Vector((d * 0.6, -d * 1.1, d * 0.4))
    cam_overview = create_or_update_camera(
        "05_overview_studio",
        cam_type='PERSP',
        lens=50.0,
        location=overview_pos,
        target_point=center
    )

    # 06_details_macro: Perspective Close-Up Macro (100mm, shallow f/4.0 DOF)
    # Focus on top front-right corner / joint
    macro_target = center + Vector((extents.x * 0.35, -extents.y * 0.35, extents.z * 0.35))
    macro_pos = macro_target + Vector((0.28, -0.32, 0.22))
    macro_dist = (macro_target - macro_pos).length
    cam_macro = create_or_update_camera(
        "06_details_macro",
        cam_type='PERSP',
        lens=100.0,
        location=macro_pos,
        target_point=macro_target,
        dof_focus_dist=macro_dist,
        dof_fstop=4.0
    )

    # Set default scene camera to Hero shot
    scene.camera = cam_beauty

    # 2. 3-point Grazing Chiaroscuro Area Light Triad
    def make_area_light(name: str, loc: Vector, energy: float, size_x: float, size_y: float, aim_target: Vector) -> bpy.types.Object:
        l_data = bpy.data.lights.get(name) or bpy.data.lights.new(name, 'AREA')
        l_data.shape = 'RECTANGLE'
        l_data.size = size_x
        l_data.size_y = size_y
        l_data.energy = energy
        l_obj = bpy.data.objects.get(name)
        if l_obj is None:
            l_obj = bpy.data.objects.new(name, l_data)
            scene.collection.objects.link(l_obj)
        else:
            l_obj.data = l_data
        l_obj.location = loc
        fwd = (aim_target - loc).normalized()
        l_obj.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
        return l_obj

    # Key light: Grazing softbox at low elevation to rake across surface grain
    key_loc = center + Vector((d * 0.9, -d * 0.6, d * 0.35))
    key_light = make_area_light("Key_Grazing_Softbox", key_loc, energy=380.0, size_x=1.2, size_y=0.8, aim_target=center)

    # Fill light: Diffuse softbox on opposite side to soften shadows
    fill_loc = center + Vector((-d * 1.0, -d * 0.5, d * 0.4))
    fill_light = make_area_light("Fill_Softbox", fill_loc, energy=120.0, size_x=1.0, size_y=1.0, aim_target=center)

    # Rim light: Elevated backlight behind subject to separate silhouette
    rim_loc = center + Vector((-d * 0.3, d * 1.0, d * 0.8))
    rim_light = make_area_light("Rim_Backlight", rim_loc, energy=240.0, size_x=0.6, size_y=0.6, aim_target=center)

    # 3. Ground Shadow-Catcher Plane
    ground_name = "Studio_Ground_ShadowCatcher"
    ground_mesh = bpy.data.meshes.get(ground_name) or bpy.data.meshes.new(ground_name)
    ground_obj = bpy.data.objects.get(ground_name)
    if ground_obj is None:
        ground_obj = bpy.data.objects.new(ground_name, ground_mesh)
        scene.collection.objects.link(ground_obj)

    ground_size = max(radius * 8.0, 4.0)
    # Define quad plane vertices
    half_s = ground_size * 0.5
    verts = [
        (-half_s, -half_s, 0.0),
        (half_s, -half_s, 0.0),
        (half_s, half_s, 0.0),
        (-half_s, half_s, 0.0),
    ]
    faces = [(0, 1, 2, 3)]
    ground_mesh.clear_geometry()
    ground_mesh.from_pydata(verts, [], faces)
    ground_mesh.update()

    ground_obj.location = Vector((center.x, center.y, lo.z - 0.0005))
    ground_obj.is_shadow_catcher = True

    return {
        "cameras": [
            cam_front.name,
            cam_side.name,
            cam_top.name,
            cam_beauty.name,
            cam_overview.name,
            cam_macro.name,
        ],
        "lights": [
            key_light.name,
            fill_light.name,
            rim_light.name,
        ],
        "ground_shadow_catcher": ground_obj.name,
        "world_bounds": {
            "center": tuple(center),
            "radius": radius,
            "lo": tuple(lo),
            "hi": tuple(hi),
        },
        "color_management": "AgX",
        "film_transparent": True,
    }


def build_ai_refine_kit_manifest(
    base_renders: dict,
    style_ref_path: Optional[str] = None,
    product_name: str = "Plywood and Aluminum CAD Assembly"
) -> dict:
    """Generates the structured JSON manifest for Tier-2 (image-generator / Nano Banana Pro)
    and Tier-3 (Gemini / ChatGPT multimodal handoff prompts).

    Enforces repository provenance policy:
    - media_authority is explicitly tagged POST_RENDER_CONCEPT_MEDIA.
    - geometry_authority is strictly NATIVE_BLENDER_RENDER_LOCKED.
    """
    manifest = {
        "manifest_version": "1.0.0",
        "provenance": {
            "media_authority": "POST_RENDER_CONCEPT_MEDIA",
            "geometry_authority": "NATIVE_BLENDER_RENDER_LOCKED",
            "render_engine": "Blender 5.2.0 LTS Cycles OptiX/Metal",
            "color_transform": "AgX",
            "notes": "Refined imagery is concept presentation media; native Blender renders remain the single source of truth for CAD geometry.",
        },
        "product_name": product_name,
        "base_renders": base_renders,
        "style_reference": style_ref_path,
        "tier_2_direct_generation": {
            "target_subagent": "image-generator",
            "target_model": "nano-banana-pro",
            "prompt_template": (
                f"Commercial product design studio photograph of {product_name}, 100% preserving CAD geometry "
                "and proportions from base render. Royal blue stained birch multiplex plywood with natural 24-ply "
                "exposed cut edges, matte anodized aluminum extrusions, stainless steel fasteners. Studio grazing "
                "softbox lighting, crisp contact shadows on neutral cyclorama, AgX tone mapping, subtle photographic "
                "sensor grain, ultra-sharp material micro-details."
            ),
        },
        "tier_3_multimodal_handoff": {
            "gemini_imagen3_prompt": (
                "Image-to-Image Conditioning: Preserve exact CAD geometry, object dimensions, and camera perspective "
                "from Image 1 (Base Render). Apply the exact material styling from Image 2 (Style Reference): deep "
                "royal blue stained birch plywood with visible wood grain relief, satin lacquer coat (0.25), exposed "
                "24-ply multiplex cut edges with micro-chamfer highlights. Commercial product studio catalogue lighting, "
                "chiaroscuro grazing light, clean contact shadow, 8k resolution, crisp photorealism."
            ),
            "chatgpt_dalle3_prompt": (
                "Strict physical studio product visualization based on Image 1 geometry and Image 2 material reference. "
                f"Product: Precision CAD assembly of {product_name}. Materials: Satin stained royal blue birch plywood "
                "with distinct longitudinal grain, alternating veneer cut edges, sandblasted dark grey aluminum frame. "
                "Lighting: Dual softbox studio setup with subtle rim backlight. Maintain strict 1:1 fidelity with input structure, "
                "no shape morphing."
            ),
        },
    }
    return manifest


def main():
    print("Executing bp_studio_catalogue_render self-test in Blender 5.2 LTS...")

    # 1. Clean workspace scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Build sample CAD test objects: Plywood Panel + Aluminum Frame
    # CAD Plywood panel: 300mm x 200mm x 18mm (0.3m x 0.2m x 0.018m)
    me_panel = bpy.data.meshes.new("CAD_Plywood_Panel")
    dx, dy, dz = 0.15, 0.10, 0.009
    p_verts = [
        (-dx, -dy, -dz), (dx, -dy, -dz), (dx, dy, -dz), (-dx, dy, -dz),
        (-dx, -dy,  dz), (dx, -dy,  dz), (dx, dy,  dz), (-dx, dy,  dz),
    ]
    p_faces = [
        (0, 1, 2, 3), # Bottom (-Z)
        (4, 7, 6, 5), # Top (+Z)
        (0, 4, 5, 1), # Front (-Y)
        (1, 5, 6, 2), # Right (+X)
        (2, 6, 7, 3), # Back (+Y)
        (3, 7, 4, 0), # Left (-X)
    ]
    me_panel.from_pydata(p_verts, [], p_faces)
    me_panel.update()
    ob_panel = bpy.data.objects.new("CAD_Plywood_Panel", me_panel)
    bpy.context.scene.collection.objects.link(ob_panel)

    # Aluminum Extrusion Frame (surrounding the panel)
    me_frame = bpy.data.meshes.new("CAD_Aluminum_Frame")
    fx, fy, fz = 0.165, 0.115, 0.012
    f_verts = [
        (-fx, -fy, -fz), (fx, -fy, -fz), (fx, fy, -fz), (-fx, fy, -fz),
        (-fx, -fy,  fz), (fx, -fy,  fz), (fx, fy,  fz), (-fx, fy,  fz),
    ]
    f_faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    me_frame.from_pydata(f_verts, [], f_faces)
    me_frame.update()
    ob_frame = bpy.data.objects.new("CAD_Aluminum_Frame", me_frame)
    bpy.context.scene.collection.objects.link(ob_frame)

    # 3. VERIFY CAD GEOMETRY LOCKDOWN: Record initial vertex SHA256 hashes
    panel_v_sha_before = compute_mesh_vertex_sha256(ob_panel)
    frame_v_sha_before = compute_mesh_vertex_sha256(ob_frame)
    print(f"Vertex SHA256 Before: Panel={panel_v_sha_before[:12]} Frame={frame_v_sha_before[:12]}")

    # 4. Slot plywood Face vs CutEdge based on normal vector
    slot_stats = slot_plywood_face_vs_cutedge(ob_panel, dominant_axis='Z', dot_threshold=0.85)
    print(f"Slotting stats: {slot_stats}")
    assert slot_stats["face_count"] == 2, f"Expected 2 face polygons (+Z, -Z), got {slot_stats['face_count']}"
    assert slot_stats["cutedge_count"] == 4, f"Expected 4 cut-edge polygons, got {slot_stats['cutedge_count']}"

    # 5. Build decoupled PBR materials
    mat_face = build_decoupled_stain_pbr_material(
        "Plywood_Face",
        tint_rgba=(0.12, 0.24, 0.52, 1.0), # Royal blue stain
        bevel_radius_m=0.0006
    )
    mat_cutedge = build_decoupled_stain_pbr_material(
        "Plywood_CutEdge_Multiplex",
        tint_rgba=(0.18, 0.16, 0.12, 1.0), # Natural 24-ply cut-edge tone
        bevel_radius_m=0.0006
    )
    ob_panel.data.materials[0] = mat_face
    ob_panel.data.materials[1] = mat_cutedge

    # Frame material (anodized aluminum)
    mat_frame = bpy.data.materials.new("Aluminum_Anodized_Matte")
    bsdf_frame = mat_frame.node_tree.nodes.get("Principled BSDF")
    if bsdf_frame:
        find_socket(bsdf_frame, "Metallic").default_value = 1.0
        find_socket(bsdf_frame, "Roughness").default_value = 0.28
        find_socket(bsdf_frame, "Base Color").default_value = (0.22, 0.23, 0.25, 1.0)
    ob_frame.data.materials.append(mat_frame)

    # 6. Setup 6-shot studio catalogue rig
    rig_info = setup_six_shot_studio_rig([ob_panel, ob_frame])
    print(f"Rig cameras: {rig_info['cameras']}")
    print(f"Rig lights: {rig_info['lights']}")

    # 7. Postcondition asserts: Geometry lockdown verified
    panel_v_sha_after = compute_mesh_vertex_sha256(ob_panel)
    frame_v_sha_after = compute_mesh_vertex_sha256(ob_frame)
    assert panel_v_sha_before == panel_v_sha_after, "FATAL: Panel CAD geometry altered during shading/slotting!"
    assert frame_v_sha_before == frame_v_sha_after, "FATAL: Frame CAD geometry altered during shading/rigging!"

    # Camera asserts
    assert len(rig_info["cameras"]) == 6, f"Expected 6 cameras, got {len(rig_info['cameras'])}"
    for cam_name in ["01_front_view", "02_side_view", "03_top_view", "04_3_4_beauty", "05_overview_studio", "06_details_macro"]:
        assert cam_name in bpy.data.objects, f"Missing camera {cam_name}"

    # Shading asserts: verify bevel and mix nodes
    nt_face = mat_face.node_tree
    bevel_nodes = [n for n in nt_face.nodes if n.bl_idname == "ShaderNodeBevel"]
    mix_nodes = [n for n in nt_face.nodes if n.bl_idname == "ShaderNodeMix"]
    bump_nodes = [n for n in nt_face.nodes if n.bl_idname == "ShaderNodeBump"]
    assert len(bevel_nodes) == 1, "ShaderNodeBevel missing from Plywood_Face material"
    assert len(mix_nodes) == 1, "ShaderNodeMix missing from Plywood_Face material"
    assert len(bump_nodes) == 1, "ShaderNodeBump missing from Plywood_Face material"

    # Verify AI Refine Kit manifest generation
    sample_renders = {cam: f"renders/studio/{cam}.png" for cam in rig_info["cameras"]}
    manifest = build_ai_refine_kit_manifest(sample_renders, style_ref_path="refs/royal_blue_multiplex.png")
    assert manifest["provenance"]["media_authority"] == "POST_RENDER_CONCEPT_MEDIA"
    assert manifest["provenance"]["geometry_authority"] == "NATIVE_BLENDER_RENDER_LOCKED"
    print("AI Refine Kit Manifest verified successfully.")

    # 8. Authoritative emit_ok
    rt.emit_ok(
        "bp_studio_catalogue_render",
        geometry_locked=True,
        face_slots=2,
        cameras_created=len(rig_info["cameras"]),
        bevel_radius_m=0.0006,
        agx_configured=True,
        shadow_catcher=True,
        panel_vertex_sha=panel_v_sha_after,
    )
    print("bp_studio_catalogue_render execution finished successfully.")


if __name__ == '__main__':
    main()

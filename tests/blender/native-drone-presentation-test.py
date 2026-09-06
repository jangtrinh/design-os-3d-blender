"""Read-only presentation QA for native FPV drone Blender deliverables.

Run: blender -b asset.blend --python tests/blender/native-drone-presentation-test.py
"""
import json
import re
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


STUDIO_WORDS = ("studio", "backdrop", "cyclorama", "ground", "floor", "shadow", "sweep")
HERO_FILL = (0.45, 0.95)
TOP_FILL = (0.45, 0.98)


def named_camera(kind):
    matches = [o for o in bpy.data.objects if o.type == "CAMERA" and kind in o.name.lower()]
    return matches[0] if len(matches) == 1 else None


def drone_meshes():
    meshes = []
    for ob in bpy.context.scene.objects:
        label = "%s %s" % (ob.name, " ".join(c.name for c in ob.users_collection))
        if ob.type == "MESH" and not any(word in label.lower() for word in STUDIO_WORDS):
            meshes.append(ob)
    return meshes


def frame(ob, camera, scene):
    points = [world_to_camera_view(scene, camera, ob.matrix_world @ Vector(c)) for c in ob.bound_box]
    xs, ys, zs = [p.x for p in points], [p.y for p in points], [p.z for p in points]
    return {"in_frame": min(xs) >= 0 and max(xs) <= 1 and min(ys) >= 0 and max(ys) <= 1,
            "in_front": min(zs) > 0, "fill_u": round(max(xs) - min(xs), 5),
            "fill_v": round(max(ys) - min(ys), 5)}


def combined_frame(objects, camera, scene):
    points = [world_to_camera_view(scene, camera, ob.matrix_world @ Vector(c))
              for ob in objects for c in ob.bound_box]
    xs, ys = [p.x for p in points], [p.y for p in points]
    return {"fill_u": round(max(xs) - min(xs), 5), "fill_v": round(max(ys) - min(ys), 5)}


def material_color(material):
    if material.use_nodes and material.node_tree:
        node = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if node and "Base Color" in node.inputs:
            return tuple(round(v, 4) for v in node.inputs["Base Color"].default_value[:3])
    return tuple(round(v, 4) for v in material.diffuse_color[:3])


def output_is_16bit(scene):
    image = scene.render.image_settings
    return ((image.file_format == "PNG" and image.color_depth == "16") or
            (image.file_format == "OPEN_EXR" and image.color_depth in {"16", "32"}))


def main():
    scene = bpy.context.scene
    failures = []
    hero, top = named_camera("hero"), named_camera("top")
    meshes = drone_meshes()
    materials = sorted({mat for ob in meshes for mat in ob.data.materials if mat}, key=lambda m: m.name)
    lights = [ob for ob in scene.objects if ob.type == "LIGHT" and ob.data.energy > 0]
    world_strength = 0.0
    if scene.world and scene.world.use_nodes:
        background = next((n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if background:
            world_strength = float(background.inputs["Strength"].default_value)

    if not hero:
        failures.append("missing_or_ambiguous_hero_camera")
    if not top:
        failures.append("missing_or_ambiguous_top_camera")
    if hero and scene.camera != hero:
        failures.append("hero_camera_not_active")
    if not meshes:
        failures.append("no_visible_drone_meshes")

    fills = {}
    for label, camera, limits in (("hero", hero, HERO_FILL), ("top", top, TOP_FILL)):
        if not camera or not meshes:
            continue
        fills[label] = {ob.name: frame(ob, camera, scene) for ob in meshes}
        invalid = [name for name, value in fills[label].items()
                   if not value["in_frame"] or not value["in_front"]]
        if invalid:
            failures.append("%s_component_framing:%s" % (label, ",".join(invalid)))
        total = combined_frame(meshes, camera, scene)
        fills[label]["__combined__"] = total
        if not (limits[0] <= max(total["fill_u"], total["fill_v"]) <= limits[1]):
            failures.append("%s_fill_out_of_bounds" % label)

    if scene.render.engine != "CYCLES":
        failures.append("render_engine_not_cycles")
    if max(scene.render.resolution_x, scene.render.resolution_y) < 4096:
        failures.append("long_edge_below_4096")
    if scene.render.resolution_percentage != 100:
        failures.append("resolution_percentage_not_100")
    if not output_is_16bit(scene):
        failures.append("output_not_16bit_png_or_exr")
    intended = scene.get("intended_view_transform")
    if scene.view_settings.view_transform != "AgX" and intended != scene.view_settings.view_transform:
        failures.append("view_transform_not_agx_or_verified")
    if not lights and world_strength <= 0:
        failures.append("no_nonzero_lights_or_world")
    if any(camera and camera.data.dof.use_dof for camera in (hero, top)):
        failures.append("dof_enabled_for_fidelity_review")
    if len(materials) < 3:
        failures.append("insufficient_material_separation")
    dark_lenses = [m.name for m in materials if re.search(r"lens|glass", m.name, re.I)
                   and sum(material_color(m)) / 3 <= 0.15]
    if not dark_lenses:
        failures.append("missing_dark_lens_material")

    metrics = {"cameras": {"hero": hero.name if hero else None, "top": top.name if top else None,
                            "active": scene.camera.name if scene.camera else None},
               "fills": fills, "resolution": [scene.render.resolution_x, scene.render.resolution_y,
                                                 scene.render.resolution_percentage],
               "engine": scene.render.engine, "lights": [ob.name for ob in lights],
               "world_strength": world_strength, "materials": {m.name: material_color(m) for m in materials}}
    print("TEST_%s %s" % ("PASS" if not failures else "FAIL",
                            json.dumps({"failures": failures, "metrics": metrics}, sort_keys=True)))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

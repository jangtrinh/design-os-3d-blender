"""Read-only presentation QA for the Rodin-optimized FPV candidate.

Run: blender -b asset.blend --python tests/blender/rodin-optimized-presentation-test.py
"""
import json
import re

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


CAMERAS = ("CAM-Drone-Hero", "CAM-Drone-Top", "CAM-Drone-Opposite", "CAM-Drone-Underside")
STUDIO = ("studio", "backdrop", "cyclorama", "ground", "floor", "shadow", "sweep")
OVERLAY = ("camera-", "side-vent")


def drone_meshes(scene):
    return [o for o in scene.objects if o.type == "MESH" and
            not any(x in (o.name + " " + " ".join(c.name for c in o.users_collection)).lower() for x in STUDIO)]


def projection(scene, camera, objects):
    values = {o.name: [world_to_camera_view(scene, camera, o.matrix_world @ Vector(c)) for c in o.bound_box]
              for o in objects}
    points = [p for ps in values.values() for p in ps]
    bad = sorted(name for name, ps in values.items() if any(p.x < 0 or p.x > 1 or p.y < 0 or p.y > 1 or p.z <= 0 for p in ps))
    xs, ys, zs = [p.x for p in points], [p.y for p in points], [p.z for p in points]
    return {"fill_u": round(max(xs) - min(xs), 5), "fill_v": round(max(ys) - min(ys), 5),
            "min_depth": round(min(zs), 5), "clipped": bad}


def color(mat):
    if mat.node_tree:
        node = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if node:
            return tuple(round(x, 4) for x in node.inputs["Base Color"].default_value[:3])
    return tuple(round(x, 4) for x in mat.diffuse_color[:3])


def image_is_16bit(scene):
    im = scene.render.image_settings
    return (im.file_format == "PNG" and im.color_depth == "16") or (im.file_format == "OPEN_EXR" and im.color_depth in {"16", "32"})


def main():
    scene = bpy.context.scene
    failures = []
    cameras = {name: bpy.data.objects.get(name) for name in CAMERAS}
    objects = drone_meshes(scene)
    materials = sorted({m for o in objects for m in o.data.materials if m}, key=lambda m: m.name)
    lights = [o for o in scene.objects if o.type == "LIGHT" and o.data.energy > 0]
    if not objects:
        failures.append("no_drone_meshes")
    for name, camera in cameras.items():
        if not camera or camera.type != "CAMERA":
            failures.append("missing_camera:" + name)
    if cameras["CAM-Drone-Hero"] and scene.camera != cameras["CAM-Drone-Hero"]:
        failures.append("hero_camera_not_active")

    framing = {}
    for name, camera in cameras.items():
        if camera and objects:
            framing[name] = projection(scene, camera, objects)
            if framing[name]["clipped"]:
                failures.append("camera_clipping:%s:%s" % (name, ",".join(framing[name]["clipped"])))

    base = max((o for o in objects if not o.name.startswith(OVERLAY)), key=lambda o: o.dimensions.length, default=None)
    detached = []
    if base:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = base.evaluated_get(depsgraph)
        for overlay in (o for o in objects if o.name.startswith(OVERLAY)):
            local = base.matrix_world.inverted() @ overlay.matrix_world.translation
            hit, point, _normal, _index = evaluated.closest_point_on_mesh(local)
            if not hit or (local - point).length > 0.16:
                detached.append(overlay.name)
    if detached:
        failures.append("detached_overlays:" + ",".join(detached))

    if scene.render.engine != "CYCLES": failures.append("render_engine_not_cycles")
    if (scene.render.resolution_x, scene.render.resolution_y) != (4096, 2304): failures.append("resolution_not_4096x2304")
    if scene.render.resolution_percentage != 100: failures.append("resolution_percentage_not_100")
    if not image_is_16bit(scene): failures.append("output_not_16bit_png_or_exr")
    if scene.view_settings.view_transform != "AgX": failures.append("view_transform_not_agx")
    if not lights: failures.append("no_nonzero_lights")
    if any(c and c.data.dof.use_dof for c in cameras.values()): failures.append("dof_enabled")
    if len(materials) < 3: failures.append("insufficient_material_separation")
    if not any(re.search(r"lens|glass", m.name, re.I) and sum(color(m)) / 3 <= .15 for m in materials):
        failures.append("missing_dark_lens_material")

    metrics = {"active_camera": scene.camera.name if scene.camera else None, "framing": framing,
               "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
               "engine": scene.render.engine, "lights": [o.name for o in lights],
               "materials": {m.name: color(m) for m in materials}, "detached_overlays": detached}
    print("TEST_%s %s" % ("PASS" if not failures else "FAIL", json.dumps({"failures": failures, "metrics": metrics}, sort_keys=True)))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Read-only acceptance test for the native FPV drone Blender asset."""
import json
import re
import sys

import bmesh
import bpy


EPSILON = 1e-9
VENDORS = re.compile(r"(?:rodin|hyper3d|hunyuan|meshy|tripo|sketchfab)", re.I)
COMPONENTS = {
    "central_shell_body": (r"(?:shell|body|chassis|frame)", 1),
    "duct": (r"duct", 4),
    "motor_hub": (r"(?:motor|hub)", 4),
    "prop_blade": (r"(?:prop(?:eller)?|blade)", 12),
    "camera": (r"(?:camera|gimbal)", 1),
    "lens": (r"lens", 1),
    "top_plate": (r"(?:top[_ -]?plate|plate[_ -]?top)", 1),
}
MATERIALS = {
    "body": r"(?:body|shell|carbon|chassis|frame)",
    "prop": r"(?:prop|blade)",
    "lens": r"(?:lens|glass|optic)",
}


def visible_meshes():
    return [obj for obj in bpy.context.scene.objects
            if obj.type == 'MESH' and obj.visible_get() and not obj.hide_render]


def text(obj):
    return " ".join((obj.name, getattr(obj.data, "name", ""))).lower()


def matches(objects, pattern):
    return [obj for obj in objects if re.search(pattern, text(obj), re.I)]


def assigned_materials(obj):
    slots = obj.data.materials
    return {slots[face.material_index] for face in obj.data.polygons
            if face.material_index < len(slots) and slots[face.material_index]}


def mesh_report(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        return {
            "verts": len(bm.verts), "faces": len(bm.faces),
            "tris": sum(len(face.verts) - 2 for face in bm.faces),
            "loose_verts": sum(not vert.link_edges for vert in bm.verts),
            "zero_area_faces": sum(face.calc_area() < EPSILON for face in bm.faces),
            "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
            "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "flipped_edges": sum(edge.is_manifold and not edge.is_contiguous
                                for edge in bm.edges),
        }
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def production_cameras():
    return [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA'
            and re.search(r"(?:fpv|drone).*(?:hero|beauty|top|three|turntable)|"
                          r"(?:hero|beauty|top|three|turntable).*(?:fpv|drone)",
                          obj.name, re.I)]


def main():
    failures = []
    if bpy.app.version < (5, 2, 0):
        failures.append("Blender 5.2+ required; found %s" % (bpy.app.version_string,))
    all_names = [("object", obj.name) for obj in bpy.data.objects]
    all_names += [("material", mat.name) for mat in bpy.data.materials]
    for kind, name in all_names:
        if VENDORS.search(name):
            failures.append("vendor name forbidden in %s: %s" % (kind, name))

    meshes = visible_meshes()
    reports = {obj.name: mesh_report(obj) for obj in meshes}
    aggregate = {key: sum(report[key] for report in reports.values())
                 for key in ("verts", "faces", "tris")}
    groups = {name: matches(meshes, pattern) for name, (pattern, _count)
              in COMPONENTS.items()}
    for name, (_pattern, minimum) in COMPONENTS.items():
        if len(groups[name]) < minimum:
            failures.append("missing %s: need %d, found %d" %
                            (name, minimum, len(groups[name])))
    for obj in meshes:
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            failures.append("visible mesh scale is not 1,1,1: %s" % obj.name)
        report = reports[obj.name]
        for key in ("loose_verts", "zero_area_faces"):
            if report[key]:
                failures.append("%s has %d %s" % (obj.name, report[key], key))
    hero_objects = {obj for group in groups.values() for obj in group}
    for obj in hero_objects:
        report = reports[obj.name]
        for key in ("boundary_edges", "non_manifold_edges", "flipped_edges"):
            if report[key]:
                failures.append("closed hero %s has %d %s" %
                                (obj.name, report[key], key))
        if not assigned_materials(obj):
            failures.append("required material missing from %s" % obj.name)
    used_material_names = {mat.name for obj in hero_objects for mat in assigned_materials(obj)}
    for category, pattern in MATERIALS.items():
        if not any(re.search(pattern, name, re.I) for name in used_material_names):
            failures.append("required %s material is not assigned" % category)
    cameras = production_cameras()
    if len(cameras) < 2:
        failures.append("named production cameras: need hero/3-4 and top, found %d" % len(cameras))
    else:
        camera_names = " ".join(camera.name.lower() for camera in cameras)
        for viewpoint, pattern in (("hero/3-4", r"(?:hero|beauty|three)"), ("top", r"top")):
            if not re.search(pattern, camera_names):
                failures.append("named production %s camera missing" % viewpoint)

    result = {"aggregate": aggregate, "mesh_objects": len(meshes),
              "failures": sorted(set(failures))}
    print(("TEST_FAIL " if failures else "TEST_PASS ") + json.dumps(result, sort_keys=True))
    return 1 if failures else 0


sys.exit(main())

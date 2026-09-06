"""Read-only QA for the locally repaired Rodin scaffold candidate."""
import hashlib
import json
import os
import re
import sys

import bmesh
import bpy


MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TRIANGLES = 1_500_000
EPSILON = 1e-9
DETAILS = {
    "lens": (r"camera.*lens", 1),
    "camera_inset": (r"camera.*inset", 1),
    "camera_ribs": (r"camera.*rib", 10),
    "side_vents": (r"side.*vent", 2),
}
SERVICE_URL = re.compile(r"https?://|(?:api|service)[-_ ]?(?:url|endpoint)", re.I)


def mesh_report(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {
            "verts": len(bm.verts), "faces": len(bm.faces),
            "tris": sum(len(face.verts) - 2 for face in bm.faces),
            "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
            "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "flipped_edges": sum(edge.is_manifold and not edge.is_contiguous
                                for edge in bm.edges),
            "loose_verts": sum(not vert.link_edges for vert in bm.verts),
            "zero_area_faces": sum(face.calc_area() < EPSILON for face in bm.faces),
        }
    finally:
        bm.free()


def linked_ids():
    pools = (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
             bpy.data.cameras, bpy.data.lights, bpy.data.collections)
    return [item.name for pool in pools for item in pool if item.library]


def custom_strings():
    ids = [bpy.context.scene] + list(bpy.data.objects) + list(bpy.data.materials)
    return ["%s:%s=%s" % (item.name, key, value)
            for item in ids for key, value in item.items() if isinstance(value, str)]


def main():
    failures = []
    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == 'MESH' and obj.visible_get()
              and not obj.hide_render]
    scaffold = bpy.data.objects.get("drone-silhouette-repaired")
    if bpy.app.version < (5, 2, 0):
        failures.append("Blender 5.2+ required")
    if not str(scene.get("asset-source", "")).startswith("local-rodin-scaffold"):
        failures.append("local scaffold provenance missing")
    if scene.get("external-service-calls") != 0:
        failures.append("external-service-calls must equal 0")
    links = [library.filepath for library in bpy.data.libraries] + linked_ids()
    if links:
        failures.append("linked external data present: %s" % ", ".join(links))
    services = [value for value in custom_strings() if SERVICE_URL.search(value)]
    if services:
        failures.append("service URL/endpoint metadata present")
    if not scaffold or scaffold.type != 'MESH':
        failures.append("repaired scaffold missing")
        report = {}
    else:
        report = mesh_report(scaffold)
        if not str(scaffold.get("source-provenance", "")).startswith("local-rodin-scaffold"):
            failures.append("scaffold source provenance missing")
        for key in ("boundary_edges", "non_manifold_edges", "flipped_edges",
                    "loose_verts", "zero_area_faces"):
            if report[key]:
                failures.append("scaffold has %d %s" % (report[key], key))
    for obj in meshes:
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            failures.append("visible mesh scale is not 1,1,1: %s" % obj.name)
    for label, (pattern, minimum) in DETAILS.items():
        found = [obj.name for obj in meshes if re.search(pattern, obj.name, re.I)]
        if len(found) < minimum:
            failures.append("missing %s: need %d, found %d" % (label, minimum, len(found)))
    cameras = [obj.name for obj in scene.objects if obj.type == 'CAMERA'
               and re.search(r"CAM-Drone-(?:Hero|Top|Opposite|Underside)", obj.name)]
    if len(cameras) < 4:
        failures.append("required production cameras missing")
    file_size = os.path.getsize(bpy.data.filepath) if bpy.data.filepath else 0
    triangles = sum(mesh_report(obj)["tris"] for obj in meshes)
    if file_size > MAX_FILE_BYTES:
        failures.append("blend exceeds %d MB" % (MAX_FILE_BYTES // 1024 // 1024))
    if triangles > MAX_TRIANGLES:
        failures.append("triangle budget exceeds %d" % MAX_TRIANGLES)
    saved = scene.get("topology-stats", "{}")
    try:
        saved = json.loads(saved)
    except (TypeError, ValueError):
        saved = {}
    stat_keys = {"verts": "verts", "faces": "faces",
                 "boundary_edges": "boundary_edges",
                 "nonmanifold_edges": "non_manifold_edges"}
    if report and any(saved.get(saved_key) != report[report_key]
                      for saved_key, report_key in stat_keys.items()):
        failures.append("stored topology-stats do not match scaffold")
    fingerprint = [(obj.name, len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]
    digest = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    result = {"file_bytes": file_size, "mesh_objects": len(meshes),
              "scaffold": report, "triangles": triangles, "fingerprint": digest,
              "failures": sorted(set(failures))}
    print(("TEST_FAIL " if failures else "TEST_PASS ") + json.dumps(result, sort_keys=True))
    return 1 if failures else 0


sys.exit(main())

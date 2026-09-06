"""Read-only sense organs. None of these mutate the scene."""
import statistics

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def assert_exists(name):
    assert name in bpy.data.objects, f"missing object: {name}"
    return bpy.data.objects[name]


def tri_count(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(deps).to_mesh()
    try:
        me.calc_loop_triangles()
        return len(me.loop_triangles)
    finally:
        obj.evaluated_get(deps).to_mesh_clear()


def world_bbox(obj):
    cs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (Vector((min(c.x for c in cs), min(c.y for c in cs),
                    min(c.z for c in cs))),
            Vector((max(c.x for c in cs), max(c.y for c in cs),
                    max(c.z for c in cs))))


def has_material(obj, must_have_nodes=True):
    if not obj.data.materials or obj.data.materials[0] is None:
        return False
    mat = obj.data.materials[0]
    return (not must_have_nodes) or (mat.node_tree and
                                     len(mat.node_tree.links) > 0)


def framing(obj, cam=None, scene=None):
    """Is the object in frame? Target fill 0.7-0.85 for hero shots."""
    scene = scene or bpy.context.scene
    cam = cam or scene.camera
    us, vs, zs = [], [], []
    for c in obj.bound_box:
        co = world_to_camera_view(scene, cam, obj.matrix_world @ Vector(c))
        us.append(co.x)
        vs.append(co.y)
        zs.append(co.z)
    return {
        "in_frame": all(0.0 <= u <= 1.0 for u in us)
                    and all(0.0 <= v <= 1.0 for v in vs),
        "in_front": min(zs) > 0.0,
        "fill_u": max(us) - min(us),
        "fill_v": max(vs) - min(vs),
    }


def frame_stats(path):
    """stdev < 0.01 => flat frame: nothing in view or lighting failure."""
    img = bpy.data.images.load(path, check_existing=False)
    try:
        px = list(img.pixels)
        lum = [0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]
               for i in range(0, len(px), 4)]
        return {"mean": statistics.fmean(lum),
                "stdev": statistics.pstdev(lum),
                "black": statistics.fmean(lum) < 0.005,
                "blown": statistics.fmean(lum) > 0.98}
    finally:
        bpy.data.images.remove(img)

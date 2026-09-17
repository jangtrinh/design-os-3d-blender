"""Read-only sense organs. None of these mutate the scene."""
import math
import statistics

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

from boilerplates.bp_core import evaluated_mesh


def assert_exists(name):
    assert name in bpy.data.objects, f"missing object: {name}"
    return bpy.data.objects[name]


def tri_count(obj):
    with evaluated_mesh(obj) as (_, me):
        me.calc_loop_triangles()
        return len(me.loop_triangles)


def _extents(points):
    """Finite component bounds; empty geometry cannot pass a measurement."""
    low, high = [math.inf] * 3, [-math.inf] * 3
    count = 0
    for point in points:
        if not all(math.isfinite(v) for v in point):
            raise ValueError("non-finite evaluated coordinates")
        for axis in range(3):
            low[axis] = min(low[axis], point[axis])
            high[axis] = max(high[axis], point[axis])
        count += 1
    if not count:
        raise ValueError("no evaluated mesh vertices to measure")
    return Vector(low), Vector(high)


def world_bbox(obj):
    """Tight world bounds of evaluated mesh vertices in Blender units.

    Uses the active view layer's graph, including evaluated transforms. Does not
    aggregate children/instances or prove local wall thickness or visibility.
    """
    with evaluated_mesh(obj) as (owner, mesh):
        matrix = owner.matrix_world.copy()
        return _extents(matrix @ vertex.co for vertex in mesh.vertices)


def has_material(obj, must_have_nodes=True):
    if not obj.data.materials or obj.data.materials[0] is None:
        return False
    mat = obj.data.materials[0]
    return (not must_have_nodes) or (mat.node_tree and
                                     len(mat.node_tree.links) > 0)


def framing(obj, cam=None, scene=None):
    """Screen evaluated mesh vertices against a perspective/orthographic camera.

    in_frame now includes front/near/far clipping; in_image is the previous XY
    predicate. Uses full-frame projection, not render borders, occlusion, children
    or instances. This is a numeric screen, not a rendered-visibility verdict.
    """
    scene = scene or bpy.context.scene
    cam = cam or scene.camera
    if cam is None or cam.type != 'CAMERA':
        raise ValueError("framing requires a camera object")
    if scene != bpy.context.scene:
        raise ValueError("framing requires the active scene's evaluated graph")
    graph = bpy.context.evaluated_depsgraph_get()
    camera = cam.evaluated_get(graph)
    if camera.data.type not in {'PERSP', 'ORTHO'}:
        raise ValueError("framing supports perspective and orthographic cameras")
    with evaluated_mesh(obj, graph) as (owner, mesh):
        matrix = owner.matrix_world.copy()
        low, high = _extents(
            world_to_camera_view(scene, camera, matrix @ vertex.co)
            for vertex in mesh.vertices)
    in_image = 0.0 <= low.x <= high.x <= 1.0 and 0.0 <= low.y <= high.y <= 1.0
    in_front = low.z > 0.0
    within_clip = camera.data.clip_start <= low.z <= high.z <= camera.data.clip_end
    return {
        "in_frame": bool(in_image and in_front and within_clip),
        "in_image": bool(in_image),
        "in_front": bool(in_front),
        "within_clip": bool(within_clip),
        "fill_u": high.x - low.x,
        "fill_v": high.y - low.y,
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

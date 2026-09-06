"""Scene ownership, frames and idempotent object helpers for the watch-winder capsule.

Load through agent_runtime.load_lib (sha-keyed cache). Everything here targets the
owned scene WW_capsule only; nothing touches other scenes. Units: params in mm,
converted once by mm(); 1 BU = 1 m.
"""
import hashlib
import json
import math
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(BUILD, "..", ".."))
SCENE_NAME = "WW_capsule"
PARAM_PATH = os.path.join(BUILD, "design-parameters.json")

P = {}


def reload_params():
    """Refresh P in place (same dict object) so passes always see the file on disk."""
    with open(PARAM_PATH, "r", encoding="utf-8") as fh:
        fresh = json.load(fh)
    P.clear()
    P.update(fresh)
    return P


reload_params()


def mm(x):
    """Millimetres -> metres. Convert exactly once, at mesh construction."""
    return float(x) * 0.001


def vmm(v):
    return Vector((mm(v[0]), mm(v[1]), mm(v[2])))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# ---------------------------------------------------------------- scene ownership
FACTORY_OBJECTS = {"Cube", "Light", "Camera"}


def adopt_factory_scene():
    """A fresh file's default 'Scene' (only Cube/Light/Camera) becomes the owned scene.
    Refuses when the file carries anything else, so no unrelated work is ever touched."""
    if bpy.data.scenes.get(SCENE_NAME) is not None:
        return False
    default = bpy.data.scenes.get("Scene")
    if default is None or len(bpy.data.scenes) != 1:
        return False
    names = {o.name for o in default.objects}
    if not names.issubset(FACTORY_OBJECTS):
        return False
    for ob in list(default.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    default.name = SCENE_NAME
    return True


def scene():
    """Get or create the owned scene; never resets anything that already exists."""
    reload_params()
    adopt_factory_scene()
    sc = bpy.data.scenes.get(SCENE_NAME)
    if sc is None:
        sc = bpy.data.scenes.new(SCENE_NAME)
        sc.unit_settings.system = "METRIC"
        sc.unit_settings.scale_length = 1.0
        sc.render.engine = "CYCLES"
        sc.render.use_persistent_data = False
        world = bpy.data.worlds.get("WW_world") or bpy.data.worlds.new("WW_world")
        sc.world = world
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.render.engine = "CYCLES"
    sc.render.use_persistent_data = False
    if sc.world is None:
        sc.world = bpy.data.worlds.get("WW_world") or bpy.data.worlds.new("WW_world")
    return sc


def activate():
    """Make the owned scene the window scene (GUI + headless) and return it."""
    sc = scene()
    wm = bpy.context.window_manager
    for win in (wm.windows if wm else []):
        if win.scene != sc:
            win.scene = sc
    return sc


def coll(name, parent=None):
    sc = scene()
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    holder = parent if parent is not None else sc.collection
    if c.name not in holder.children:
        holder.children.link(c)
    return c


def empty(name, collection, parent=None, matrix_local=None, size=0.02):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, None)
        ob.empty_display_type = "PLAIN_AXES"
        ob.empty_display_size = size
    if ob.name not in collection.objects:
        collection.objects.link(ob)
    ob.parent = parent
    ob.matrix_local = matrix_local if matrix_local is not None else Matrix.Identity(4)
    return ob


def mesh_obj(name, verts, faces, collection, parent=None, matrix_local=None,
             smooth=True, role="", material=None):
    """Idempotent: replaces the mesh data of an existing object of that name."""
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces], shade_flat=not smooth)
    bad = me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.get(name)
    old = None
    if ob is None:
        ob = bpy.data.objects.new(name, me)
    else:
        old = ob.data
        ob.data = me
        ob.modifiers.clear()  # each pass re-adds its own modifiers; stale booleans must not linger
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)
    if ob.name not in collection.objects:
        collection.objects.link(ob)
    ob.parent = parent
    ob.matrix_local = matrix_local if matrix_local is not None else Matrix.Identity(4)
    ob["ww_role"] = role
    ob["ww_validate_fixed"] = bool(bad)
    if material is not None:
        me.materials.clear()
        me.materials.append(material)
    return ob


def clay_material(name="WW_clay", rgb=(0.55, 0.55, 0.55, 1.0)):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgb
            bsdf.inputs["Roughness"].default_value = 0.6
    return mat


# ---------------------------------------------------------------- frames
def frame_P():
    """Product frame: origin at shell centre C, rotated +tilt about world X."""
    c = vmm(P["shell"]["center_world"])
    rot = Matrix.Rotation(math.radians(P["axis"]["tilt_about_world_x_deg"]), 4, "X")
    return Matrix.Translation(c) @ rot


def world_dir(polar_deg, azimuth_deg):
    """Unit vector from world polar angle (from +Z) and azimuth (from +Y toward +X)."""
    p, a = math.radians(polar_deg), math.radians(azimuth_deg)
    return Vector((math.sin(p) * math.sin(a), math.sin(p) * math.cos(a), math.cos(p)))


def surface_matrix_local(parent_world, world_direction, lift_mm=0.0):
    """Local matrix (under parent_world) with origin on the shell surface along
    world_direction and local +Z aligned with the outward surface normal."""
    r = mm(P["shell"]["outer_radius"] + lift_mm)
    c = vmm(P["shell"]["center_world"])
    d = world_direction.normalized()
    pos = c + d * r
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    return parent_world.inverted() @ (Matrix.Translation(pos) @ rot)


def world_axis(ob, local_axis=(0, 0, 1)):
    bpy.context.view_layer.update()
    return (ob.matrix_world.to_3x3() @ Vector(local_axis)).normalized()


def elevation_deg(v):
    v = Vector(v).normalized()
    return math.degrees(math.asin(max(-1.0, min(1.0, v.z))))


# ---------------------------------------------------------------- measurement
def evaluated_bbox(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    try:
        if not me.vertices:
            return None
        pts = [ev.matrix_world @ v.co for v in me.vertices]
    finally:
        ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def evaluated_verts_world(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    try:
        return [ev.matrix_world @ v.co for v in me.vertices]
    finally:
        ev.to_mesh_clear()


def other_scene_signature():
    """Digest of every non-owned scene: object names + rounded world matrices."""
    h = hashlib.sha256()
    for sc in bpy.data.scenes:
        if sc.name == SCENE_NAME:
            continue
        h.update(sc.name.encode())
        for ob in sc.objects:
            h.update(ob.name.encode())
            h.update(str([round(x, 6) for row in ob.matrix_world for x in row]).encode())
            h.update(str((ob.hide_render, ob.hide_viewport)).encode())
    return h.hexdigest()


NON_PRODUCT_ROLES = ("cutter", "internal_envelope", "studio_ground")


def ww_objects(product_only=True):
    """Owned objects. Default = product audit set: scenery, cutters and the
    internal envelope are excluded (they are not part of the delivered object).
    Any role named studio_* is scenery by construction, so a future
    studio_backdrop/studio_reflector is excluded without editing this list.
    Pass product_only=False for an inventory or a census of everything owned."""
    objs = [o for o in bpy.data.objects if o.name.startswith("WW_")]
    if not product_only:
        return objs
    return [o for o in objs
            if (o.get("ww_role") or "") not in NON_PRODUCT_ROLES
            and not (o.get("ww_role") or "").startswith("studio_")]


def ww_object_names():
    return sorted(o.name for o in ww_objects(product_only=False))


def state_path(*parts):
    p = os.path.join(BUILD, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True, default=str)
    return path

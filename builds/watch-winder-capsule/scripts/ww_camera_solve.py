"""Camera solver: place an 85 mm camera at (azimuth, elevation) so the chosen target's
evaluated extents fill `fill_target` of the frame, then re-centre in the image plane."""
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector


# target -> (role set, optional object-name filter)
TARGETS = {
    "watch": (("watch", "watch_part", "cushion"), None),
    "knob": (("knob", "knurl", "knob_boss"), lambda n: n.endswith("_L")),
    "hinge": (("hinge_fixed", "hinge_moving"), None),
    "guilloche": (("faceplate", "led_diffuser"), None),
    "rear-detail": (("usb_receptacle", "usb_recess", "control", "control_bezel"), None),
    "controls": (("control", "control_bezel"), None),
    "usb": (("usb_receptacle", "usb_recess"), None),
    "tab": (("finger_tab",), None),
}


def target_points(ww, target="product"):
    """World-space bbox corners of the evaluated meshes for a target group."""
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in ww.ww_objects():
        if ob.type != "MESH" or ob.hide_render or ob.get("ww_role") in ("cutter", "internal_envelope", "studio_ground"):
            continue
        role = ob.get("ww_role", "")
        if target != "product":
            roles, name_filter = TARGETS[target]
            if role not in roles or (name_filter and not name_filter(ob.name)):
                continue
        ev = ob.evaluated_get(deps)
        pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    return pts


def solve(ww, st, scene, name, collection, az, el, fill_target, target="product", lens=85.0, sensor=36.0, aim=None, zoom=1.0):
    pts = target_points(ww, target)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2.0
    a, e = math.radians(az), math.radians(el)
    d = 1.0
    cam = None
    for _ in range(4):
        loc = center + Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))
        cam = st.camera(name, collection, loc, center, lens=lens, sensor=sensor)
        bpy.context.view_layer.update()
        us, vs = zip(*[(world_to_camera_view(scene, cam, p).x, world_to_camera_view(scene, cam, p).y) for p in pts])
        fill = max(max(us) - min(us), max(vs) - min(vs))
        d *= fill / fill_target
    for _ in range(2):
        us, vs = zip(*[(world_to_camera_view(scene, cam, p).x, world_to_camera_view(scene, cam, p).y) for p in pts])
        du, dv = 0.5 - (min(us) + max(us)) / 2, 0.5 - (min(vs) + max(vs)) / 2
        W = d * sensor / lens
        H = W * scene.render.resolution_y / scene.render.resolution_x
        shift = cam.matrix_world.to_3x3() @ Vector((-du * W, -dv * H, 0.0))
        cam.matrix_world = Matrix.Translation(shift) @ cam.matrix_world
        bpy.context.view_layer.update()
    if aim is not None or zoom != 1.0:  # macro: re-aim at a surface point and dolly in along the same direction
        tgt = Vector(aim) if aim is not None else center
        d *= zoom
        loc = tgt + Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))
        cam = st.camera(name, collection, loc, tgt, lens=lens, sensor=sensor)
        bpy.context.view_layer.update()
    us, vs = zip(*[(world_to_camera_view(scene, cam, p).x, world_to_camera_view(scene, cam, p).y) for p in pts])
    return cam, {"distance_m": round(d, 4), "fill_u": round(max(us) - min(us), 3), "fill_v": round(max(vs) - min(vs), 3),
                 "margins": [round(min(us), 3), round(1 - max(us), 3), round(min(vs), 3), round(1 - max(vs), 3)],
                 "center": [round(c, 4) for c in center]}

"""Pass 28 — detail reel: five slow macro dolly shots (60 f each @24 fps), one camera per shot
bound to timeline markers; lid state per shot (constant), rotor turning slowly in the ring/dial
shots. Camera start/end matrices come from two solves (fill/angle A -> B), focus distance keyed
to the target centre. Saved to watch-winder-capsule-detail-anim.blend.
Postconditions: marker->camera map, per-shot start/end frame margins, lid/rotor samples.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
cs = rt.load_lib(os.path.join(HERE, "ww_camera_solve.py"))
P = ww.P
sc = ww.activate()
LEN = 60
lid_open = math.radians(-float(P["studio"]["open"]["lid_deg"]))
#            name,        target,        lid,   (az0, el0, fill0), (az1, el1, fill1), rotor_deg_end
#            name,      target,      lid,  (az0, el0, fill0), (az1, el1, fill1), rotor_end, zoom(a,b), aim
SHOTS = [("knob", "knob", 0.0, (-62, 8, 0.60), (-42, 14, 0.78), 0.0, (1.0, 1.0), None),
         ("guilloche", "guilloche", lid_open, (-22, 44, 0.5), (8, 50, 0.5), 40.0, (0.45, 0.30), "ring6"),
         ("dial", "watch", 0.0, (-26, 30, 0.50), (-14, 36, 0.72), 25.0, (1.0, 1.0), None),
         ("hinge", "hinge", 0.0, (-32, 36, 0.48), (-10, 30, 0.66), 0.0, (1.0, 1.0), None),
         ("controls", "controls", 0.0, (160, 48, 0.45), (176, 36, 0.72), 0.0, (1.0, 1.0), None),
         ("usb", "usb", 0.0, (176, 10, 0.40), (168, 4, 0.62), 0.0, (1.0, 1.0), None)]  # keep azimuths on one side of 180 (Euler wrap)
lid, rotor, unit = (bpy.data.objects[n] for n in ("WW_LID_PIVOT", "WW_ROTOR_PIVOT", "WW_CUSHION_UNIT"))
for ob in (lid, rotor, unit):
    ob.animation_data_clear()
    ob.rotation_mode = "XYZ"
for n in ("WW_ORBIT_PIVOT", "WW_CAM_VIDEO"):
    if n in bpy.data.objects:
        bpy.data.objects[n].animation_data_clear()
pz.apply(sc, "hero", P)
unit.matrix_local = unit.matrix_local  # seated
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.timeline_markers.clear()
col = ww.coll("WW_studio")


def fcurves(ob):
    act = ob.animation_data.action
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        return list(action_get_channelbag_for_slot(act, ob.animation_data.action_slot).fcurves)
    except Exception:  # noqa: BLE001
        return list(act.fcurves)


def set_interp(ob, mode, easing="EASE_IN_OUT"):
    for fc in fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = mode
            if mode == "BEZIER":
                kp.easing = easing


report = {}
frame = 1
for i, (name, target, lid_rot, a, b, rot_end, zooms, aim_key) in enumerate(SHOTS, start=1):
    f0, f1 = frame, frame + LEN - 1
    lid.rotation_euler.x = lid_rot
    rotor.rotation_euler.z = 0.0
    bpy.context.view_layer.update()
    cam_name = f"WW_CAM_DETAIL_{i:02d}_{name}"
    mats = []
    aim = pz.aim_point(aim_key) if aim_key else None
    for (az, el, fill), zoom in zip((a, b), zooms):
        cam, fr = cs.solve(ww, st, sc, cam_name, col, az, el, fill, target=target, aim=aim, zoom=zoom)
        pts = cs.target_points(ww, target)
        tc = aim if aim is not None else Vector([sum(p[k] for p in pts) / len(pts) for k in range(3)])
        mats.append((cam.matrix_world.copy(), (tc - cam.matrix_world.translation).length, fr))
    cam.animation_data_clear()
    cam.rotation_mode = "XYZ"
    cam.data.dof.use_dof, cam.data.dof.aperture_fstop, cam.data.dof.focus_object = True, 11.0, None
    prev = None
    for f, (m, fd, _) in zip((f0, f1), mats):
        # keep Euler keys continuous (shortest path) so the camera never swings the long way round
        eul = m.to_euler("XYZ", prev) if prev is not None else m.to_euler("XYZ")
        cam.location, cam.rotation_euler = m.translation, eul
        prev = eul
        cam.data.dof.focus_distance = fd
        assert cam.keyframe_insert("location", frame=f) and cam.keyframe_insert("rotation_euler", frame=f)
        assert cam.data.dof.keyframe_insert("focus_distance", frame=f)
    set_interp(cam, "BEZIER")
    mk = sc.timeline_markers.new(f"shot{i:02d}-{name}", frame=f0)
    mk.camera = cam
    # lid constant per shot; rotor linear within the shot
    lid.rotation_euler.x = lid_rot
    assert lid.keyframe_insert("rotation_euler", index=0, frame=f0)
    rotor.rotation_euler.z = 0.0
    assert rotor.keyframe_insert("rotation_euler", index=2, frame=f0)
    rotor.rotation_euler.z = math.radians(rot_end)
    assert rotor.keyframe_insert("rotation_euler", index=2, frame=f1)
    report[name] = {"frames": [f0, f1], "camera": cam_name, "start": mats[0][2], "end": mats[1][2],
                    "focus_m": [round(mats[0][1], 4), round(mats[1][1], 4)], "lid_deg": round(math.degrees(lid_rot), 1), "rotor_end_deg": rot_end}
    frame = f1 + 1
set_interp(lid, "CONSTANT")
set_interp(rotor, "LINEAR")
sc.frame_start, sc.frame_end, sc.render.fps = 1, frame - 1, 24

# --- sampled verification: marker camera + target margins at both ends of every shot ---
def marker_cam(f):
    ms = [m for m in sc.timeline_markers if m.frame <= f and m.camera]
    return max(ms, key=lambda m: m.frame).camera


for name, (_, target, lid_rot, _a, _b, rot_end, _z, _k) in zip(report, SHOTS):
    r = report[name]
    for f in (r["frames"][0], (r["frames"][0] + r["frames"][1]) // 2, r["frames"][1]):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        cam = marker_cam(f)
        assert cam.name == r["camera"], (f, cam.name)
        pts = cs.target_points(ww, target)
        us, vs = zip(*[(world_to_camera_view(sc, cam, p).x, world_to_camera_view(sc, cam, p).y) for p in pts])
        margins = [round(min(us), 3), round(1 - max(us), 3), round(min(vs), 3), round(1 - max(vs), 3)]
        if min(_z) >= 1.0:
            assert min(margins) > 0.02, (name, f, margins)
        assert abs(lid.rotation_euler.x - lid_rot) < 1e-4, (name, f, lid.rotation_euler.x)
        r.setdefault("margins", []).append(margins)
    sc.frame_set(r["frames"][1])
    assert abs(math.degrees(rotor.rotation_euler.z) - rot_end) < 0.01
sc.frame_set(1)
out = os.path.join(ww.BUILD, "watch-winder-capsule-detail-anim.blend")
if not bpy.app.background:
    assert bpy.ops.wm.save_as_mainfile(filepath=out, copy=True) == {"FINISHED"}
ww.write_json(ww.state_path("reports", "detail-reel-keys.json"), {"shots": report, "frame_end": sc.frame_end, "fps": 24, "blend": out})
rt.emit_ok("pass-28-detail-reel-keys", shots={k: v["frames"] for k, v in report.items()}, frame_end=sc.frame_end,
           margins={k: v["margins"] for k, v in report.items()}, focus_m={k: v["focus_m"] for k, v in report.items()})

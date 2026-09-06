"""Pass 24 — product film keys (24 fps): A insert cushion+watch (lid open) → B lid closes →
C rotor turns 360° inside → D camera orbits 360° (rotor keeps turning slowly).
Camera rig: WW_ORBIT_PIVOT at the closed-pose product centre, WW_CAM_VIDEO as its child.
Saved to watch-winder-capsule-anim.blend (the stills file is never touched by animation).
Postconditions: key values read back from fcurves; sampled frames prove unit seated/lifted,
lid angles, rotor turn, orbit closure; frame range set.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
cs = rt.load_lib(os.path.join(HERE, "ww_camera_solve.py"))
P = ww.P
sc = ww.activate()
FPS = 24
F = {"insert0": 1, "insert1": 73, "close0": 85, "close1": 121, "spin0": 133, "spin1": 229, "orbit0": 241, "orbit1": 385}
lid, rotor, unit = (bpy.data.objects[n] for n in ("WW_LID_PIVOT", "WW_ROTOR_PIVOT", "WW_CUSHION_UNIT"))
lid_open = math.radians(-float(P["studio"]["open"]["lid_deg"]))
for ob in (lid, rotor, unit):
    ob.animation_data_clear()
    ob.rotation_mode = "XYZ"

# camera rig solved in the CLOSED hero pose so the orbit stays centred; frame must also hold the open lid
pz.apply(sc, "hero", P)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100  # film is 16:9; solve in that aspect
col = ww.coll("WW_studio")
# two solves: open-lid framing for the insert, closed framing (push-in) from the lid close onward
lid.rotation_euler = (lid_open, 0.0, 0.0)
unit.location.z = 0.070
bpy.context.view_layer.update()
cam, fr_open = cs.solve(ww, st, sc, "WW_CAM_VIDEO", col, -30, 14, 0.84, target="product")
m_open = cam.matrix_world.copy()
lid.rotation_euler = (0.0, 0.0, 0.0)
unit.location.z = 0.0
bpy.context.view_layer.update()
cam, fr = cs.solve(ww, st, sc, "WW_CAM_VIDEO", col, -30, 14, 0.80, target="product")
m_closed = cam.matrix_world.copy()
cam.animation_data_clear()
cam.rotation_mode = "XYZ"
pivot = ww.empty("WW_ORBIT_PIVOT", col, matrix_local=Matrix.Translation(Vector(fr["center"])), size=0.03)
pivot.animation_data_clear()
pivot.rotation_mode = "XYZ"
cam.parent = None
bpy.context.view_layer.update()  # matrix_world of the new pivot must be current before parenting
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()  # basis == world while the pivot is unrotated
bpy.context.view_layer.update()
for frame, m in ((F["insert0"], m_open), (F["close0"], m_open), (F["close1"], m_closed)):
    cam.matrix_world = m
    assert cam.keyframe_insert(data_path="location", frame=frame) and cam.keyframe_insert(data_path="rotation_euler", frame=frame)
cam.matrix_world = m_closed
bpy.context.view_layer.update()
sc.frame_set(F["insert0"])
bpy.context.view_layer.update()
assert (cam.matrix_world.translation - m_open.translation).length < 1e-5, "camera key does not reproduce the open solve"
cam.data.dof.use_dof, cam.data.dof.aperture_fstop, cam.data.dof.focus_object = True, 4.0, bpy.data.objects["WW_WATCH_DIAL"]


def key(ob, path, frame, value, interp="BEZIER"):
    if path == "location.z":
        ob.location.z = value
    elif path == "rotation_euler.x":
        ob.rotation_euler.x = value
    elif path == "rotation_euler.z":
        ob.rotation_euler.z = value
    ok = ob.keyframe_insert(data_path=path.split(".")[0], index={"x": 0, "y": 1, "z": 2}[path[-1]], frame=frame)
    assert ok, (ob.name, path, frame)


# A: unit descends 70 mm along the rotor axis into the cup (eased)
key(unit, "location.z", F["insert0"], 0.070)
key(unit, "location.z", F["insert1"], 0.0)
# lid: open through A, closes in B, stays closed
key(lid, "rotation_euler.x", F["insert0"], lid_open)
key(lid, "rotation_euler.x", F["close0"], lid_open)
key(lid, "rotation_euler.x", F["close1"], 0.0)
# C: rotor one full turn (linear), then keeps turning slowly through the orbit
key(rotor, "rotation_euler.z", F["spin0"], 0.0)
key(rotor, "rotation_euler.z", F["spin1"], 2 * math.pi)
key(rotor, "rotation_euler.z", F["orbit1"], 2 * math.pi + math.pi / 2)
# D: orbit 360° (linear)
key(pivot, "rotation_euler.z", F["orbit0"], 0.0)
key(pivot, "rotation_euler.z", F["orbit1"], 2 * math.pi)


def fcurves(ob):
    act = ob.animation_data.action
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        cb = action_get_channelbag_for_slot(act, ob.animation_data.action_slot)
        return list(cb.fcurves)
    except Exception:  # noqa: BLE001 - pre-5.0 layout
        return list(act.fcurves)


for ob, linear in ((rotor, True), (pivot, True), (unit, False), (lid, False), (cam, False)):
    for fc in fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR" if linear else "BEZIER"
            if not linear:
                kp.easing = "EASE_IN_OUT"
sc.frame_start, sc.frame_end, sc.render.fps = F["insert0"], F["orbit1"], FPS
sc.camera = cam

# --- sampled verification (evaluated at frames) ---
def at(frame):
    sc.frame_set(frame)
    bpy.context.view_layer.update()

inv_body = bpy.data.objects["WW_BODY_FRAME"].matrix_world.inverted()
samples = {}
for f in (F["insert0"], (F["insert0"] + F["insert1"]) // 2, F["insert1"], F["close1"], F["spin1"], F["orbit0"], F["orbit0"] + 72, F["orbit1"]):
    at(f)
    uz = (inv_body @ unit.matrix_world.translation).z * 1000
    samples[f] = {"unit_z_mm": round(uz, 3), "lid_deg": round(math.degrees(lid.rotation_euler.x), 2),
                  "rotor_deg": round(math.degrees(rotor.rotation_euler.z), 2), "orbit_deg": round(math.degrees(pivot.rotation_euler.z), 2),
                  "cam_world": [round(c, 4) for c in cam.matrix_world.translation]}
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
margins = {}
for f in (F["insert0"], F["close1"], F["orbit0"] + 72):
    at(f)
    pts = cs.target_points(ww, "product")
    us, vs = zip(*[(world_to_camera_view(sc, cam, p).x, world_to_camera_view(sc, cam, p).y) for p in pts])
    margins[f] = [round(min(us), 3), round(1 - max(us), 3), round(min(vs), 3), round(1 - max(vs), 3)]
    assert min(margins[f]) > 0.02, (f, margins[f])
at(F["insert0"])
keys = {ob.name: sorted((fc.data_path, fc.array_index, len(fc.keyframe_points)) for fc in fcurves(ob)) for ob in (unit, lid, rotor, pivot, cam)}
assert abs(samples[F["insert0"]]["unit_z_mm"] - 70.0) < 0.01 and abs(samples[F["insert1"]]["unit_z_mm"]) < 0.01
assert abs(samples[F["insert1"]]["lid_deg"] + P["studio"]["open"]["lid_deg"]) < 0.01 and abs(samples[F["close1"]]["lid_deg"]) < 0.01
assert abs(samples[F["spin1"]]["rotor_deg"] - 360.0) < 0.01 or abs(samples[F["spin1"]]["rotor_deg"]) < 0.01
assert abs(samples[F["orbit1"]]["orbit_deg"] - 360.0) < 0.01 or abs(samples[F["orbit1"]]["orbit_deg"]) < 0.01
assert (Vector(samples[F["orbit1"]]["cam_world"]) - Vector(samples[F["orbit0"]]["cam_world"])).length < 1e-3, "orbit does not close"

anim = os.path.join(ww.BUILD, "watch-winder-capsule-anim.blend")
if not bpy.app.background:
    assert bpy.ops.wm.save_as_mainfile(filepath=anim, copy=True) == {"FINISHED"}
ww.write_json(ww.state_path("reports", "animation-keys.json"), {"frames": F, "fps": FPS, "keys": keys, "samples": samples, "camera_closed": fr, "camera_open": fr_open, "margins": margins,
                                                                 "blend": anim, "blend_sha256": ww.sha256_file(anim) if os.path.exists(anim) else None})
rt.emit_ok("pass-24-animation-keys", frames=F, fps=FPS, keys=keys, samples=samples, camera_fill_closed=(fr["fill_u"], fr["fill_v"]), camera_fill_open=(fr_open["fill_u"], fr_open["fill_v"]), margins=margins)

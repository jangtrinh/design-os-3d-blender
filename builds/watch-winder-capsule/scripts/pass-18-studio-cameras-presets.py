"""Pass 18 — studio (cyclorama ground, key/strip/fill area lights, grey world), three cameras
solved from evaluated product extents (85 mm, 36 mm sensor, 3:2, 5-8 % margins), DOF f/2.8 on
the dial, state presets hero/rear/open, Cycles device timing probe.
Postconditions: framing fill per camera, focus distances, device choice with measured times.
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
wd = rt.load_lib(os.path.join(HERE, "ww_mesh_detail.py"))
mt = rt.load_lib(os.path.join(HERE, "ww_materials.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
S = P["studio"]
col = ww.coll("WW_studio")
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 3072, 2048, 100

# Cyclorama: floor -> 0.5 m radius sweep -> back wall (thick slab), matte grey
path = [(-1.8, 0.0), (1.0, 0.0)] + [(1.0 + 0.5 * math.sin(a), 0.5 - 0.5 * math.cos(a)) for a in
                                     [math.radians(t) for t in range(10, 91, 10)]] + [(1.5, 2.5)]
v, f = wd.ribbon([(y, z - 0.005) for y, z in path], 5.0, 0.01)
ground = ww.mesh_obj("WW_GROUND", v, f, col, role="studio_ground", material=mt.mat_simple("WW_MAT_STUDIO_GREY", S["ground_hex"], 0.85, 0.2))
ground.parent = bpy.data.objects["WW_STUDIO"]
wr.world_grey(sc, S["world_strength"], 0.5)
C = ww.vmm(P["shell"]["center_world"])
kd = S["key_distance_m"]
wr.area_light("WW_LIGHT_KEY", col, C + Vector((-kd * 0.5, -kd * 0.4, kd * 0.9)), C, S["key_size_m"][0], S["key_size_m"][1], S["key_energy_w"], (1.0, 0.96, 0.9))
wr.area_light("WW_LIGHT_STRIP", col, C + Vector((0.45, 0.75, 0.5)), C, S["strip_size_m"][0], S["strip_size_m"][1], S["strip_energy_w"])
wr.area_light("WW_LIGHT_FILL", col, C + Vector((0.8, -0.6, 0.1)), C + Vector((0, 0, 0.02)), 1.0, 1.0, S["fill_energy_w"])
for n in ("WW_TEST_STRIP",):
    if n in bpy.data.objects:
        bpy.data.objects[n].hide_render = True

pz.define(sc, P)


def visible_points():
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in ww.ww_objects():
        if ob.type != "MESH" or ob.hide_render or ob.get("ww_role") in ("cutter", "internal_envelope", "studio_ground"):
            continue
        ev = ob.evaluated_get(deps)
        pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    return pts


def solve_camera(name, az, el, fill_target):
    pts = visible_points()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2.0  # bbox centre, not the object-count-weighted centroid
    a, e = math.radians(az), math.radians(el)
    d = 1.0
    cam = None
    for _ in range(4):
        loc = center + Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))
        cam = st.camera(name, col, loc, center, lens=S["lens_mm"], sensor=S["sensor_mm"])
        bpy.context.view_layer.update()
        us, vs = zip(*[(world_to_camera_view(sc, cam, p).x, world_to_camera_view(sc, cam, p).y) for p in pts])
        fill = max(max(us) - min(us), max(vs) - min(vs))
        d *= fill / fill_target
    # re-centre twice: translate the camera in its own image plane by the frame-centre offset
    for _ in range(2):
        us, vs = zip(*[(world_to_camera_view(sc, cam, p).x, world_to_camera_view(sc, cam, p).y) for p in pts])
        du, dv = 0.5 - (min(us) + max(us)) / 2, 0.5 - (min(vs) + max(vs)) / 2
        W = d * S["sensor_mm"] / S["lens_mm"]
        H = W * sc.render.resolution_y / sc.render.resolution_x
        shift = cam.matrix_world.to_3x3() @ Vector((-du * W, -dv * H, 0.0))
        cam.matrix_world = Matrix.Translation(shift) @ cam.matrix_world
        bpy.context.view_layer.update()
    us, vs = zip(*[(world_to_camera_view(sc, cam, p).x, world_to_camera_view(sc, cam, p).y) for p in pts])
    return cam, {"distance_m": round(d, 4), "fill_u": round(max(us) - min(us), 3), "fill_v": round(max(vs) - min(vs), 3),
                 "margins": [round(min(us), 3), round(1 - max(us), 3), round(min(vs), 3), round(1 - max(vs), 3)]}


report = {}
for preset, key in (("hero", "hero"), ("rear", "rear"), ("open", "open")):
    pz.apply(sc, preset, P)
    cfg = S[key]
    cam, fr = solve_camera({"hero": "WW_CAM_HERO", "rear": "WW_CAM_REAR", "open": "WW_CAM_OPEN"}[preset],
                           cfg["azimuth_deg"], cfg["elevation_deg"], S["hero"]["fill_target"])
    dial = bpy.data.objects["WW_WATCH_DIAL"]
    cam.data.dof.use_dof, cam.data.dof.focus_object, cam.data.dof.aperture_fstop = True, dial, S["fstop"]
    knob = min((bpy.data.objects["WW_KNOB_L"], bpy.data.objects["WW_KNOB_R"]), key=lambda o: (o.matrix_world.translation - cam.matrix_world.translation).length)
    fr["focus_dial_m"] = round((dial.matrix_world.translation - cam.matrix_world.translation).length, 4)
    fr["nearest_knob_m"] = round((knob.matrix_world.translation - cam.matrix_world.translation).length, 4)
    fr["knob_dial_depth_delta_mm"] = round((fr["focus_dial_m"] - fr["nearest_knob_m"]) * 1000, 1)
    assert fr["fill_u"] < 0.92 and fr["fill_v"] < 0.92 and min(fr["margins"]) > 0.04, fr
    report[preset] = fr
pz.apply(sc, "hero", P)

# device probe: time a small render on CPU and (if present) Metal GPU
dev = wr.probe_devices()
timing = {}
prefs = bpy.context.preferences.addons["cycles"].preferences
for device in ("CPU", "GPU"):
    if device == "GPU" and not any(d[1] == "METAL" for d in dev["devices"]):
        continue
    sc.cycles.device = device
    if device == "GPU":
        prefs.compute_device_type = "METAL"
        for d in prefs.devices:
            d.use = d.type == "METAL"
    runs = []
    for _ in range(2):  # second run excludes kernel warm-up
        _, secs, _ = wr.cycles_still(sc, bpy.data.objects["WW_CAM_HERO"], os.path.join(wr.RENDERS, f"probe-device-{device}.png"), 384, 256, 32, True)
        runs.append(secs)
    timing[device] = min(runs)
best = min(timing, key=timing.get)
sc.cycles.device = best
report["device"] = {"timings_s": timing, "chosen": best, "devices": dev["devices"]}
sc.render.use_persistent_data = False

ww.write_json(ww.state_path("reports", "studio-cameras.json"), report)
rt.emit_ok("pass-18-studio-cameras-presets", **{k: v for k, v in report.items()},
           output_res=[sc.render.resolution_x, sc.render.resolution_y], hdri="none local; procedural grey world + area lights (substitution reported)")

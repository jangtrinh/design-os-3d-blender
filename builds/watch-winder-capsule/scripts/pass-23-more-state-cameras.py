"""Pass 23 — extra still states: (re)define presets, solve each new camera from evaluated
extents in its own pose (same 85 mm / 36 mm / 3:2 studio as the hero), DOF on the dial,
512 px Cycles previews + one contact sheet source set. Saves the working file + checkpoint.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
cs = rt.load_lib(os.path.join(HERE, "ww_camera_solve.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
P = ww.P
sc = ww.activate()
col = ww.coll("WW_studio")
presets = pz.define(sc, P)
dial = bpy.data.objects["WW_WATCH_DIAL"]
knob = bpy.data.objects["WW_KNOB_L"]
report = {}
for name, pr in presets.items():
    if name.startswith("_") or "solve" not in pr:
        continue
    pz.apply(sc, name, P)  # pose first (lid / unit), then solve the camera in that pose
    az, el, fill, target, fstop = pr["solve"][:5]
    zoom = pr["solve"][5] if len(pr["solve"]) > 5 else 1.0
    aim = pz.aim_point(pr["solve"][6]) if len(pr["solve"]) > 6 else None
    cam, fr = cs.solve(ww, st, sc, pr["camera"], col, az, el, fill, target=target, aim=aim, zoom=zoom)
    cam.data.dof.use_dof, cam.data.dof.aperture_fstop = True, fstop
    if target in ("product", "watch"):
        cam.data.dof.focus_object = dial
    else:  # macro targets: part origins sit at the frame origin, so focus by distance to the target bbox centre
        from mathutils import Vector
        pts = cs.target_points(ww, target)
        tc = aim if aim is not None else Vector([sum(p[i] for p in pts) / len(pts) for i in range(3)])
        cam.data.dof.focus_object = None
        cam.data.dof.focus_distance = (tc - cam.matrix_world.translation).length
    if zoom >= 1.0:  # a zoomed macro deliberately frames only part of its target bbox
        assert fr["fill_u"] < 0.95 and fr["fill_v"] < 0.95 and min(fr["margins"]) > 0.02, (name, fr)
    sc.camera = cam
    path, secs, _ = wr.cycles_still(sc, cam, os.path.join(wr.RENDERS, "states", f"preview-{name}.png"), 512, 341, 32, True)
    stats = lib.frame_stats(path)
    assert stats["stdev"] > 0.01 and not stats["black"], (name, stats)
    fr.update({"preview": path, "seconds": secs, "fstop": fstop, "lid_deg": pr["lid_deg"], "unit": pr["unit"]})
    report[name] = fr
pz.apply(sc, "hero", P)
main = os.path.join(ww.BUILD, "watch-winder-capsule.blend")
if not bpy.app.background:
    assert bpy.ops.wm.save_as_mainfile(filepath=main) == {"FINISHED"}
    assert bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ww.BUILD, "checkpoints", "phase5-stills-states.blend"), copy=True) == {"FINISHED"}
ww.write_json(ww.state_path("reports", "state-cameras.json"), {"states": report, "blend_sha256": ww.sha256_file(main)})
rt.emit_ok("pass-23-more-state-cameras", states=sorted(report), fills={k: (v["fill_u"], v["fill_v"]) for k, v in report.items()},
           seconds={k: v["seconds"] for k, v in report.items()}, blend_sha256=ww.sha256_file(main)[:16])

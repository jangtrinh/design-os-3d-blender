"""Pass 17 — Phase-3 gate: neutral Cycles light, close crops (guilloche, knurl, leather/watch,
LED halo) denoised + raw, graphite vs walnut concept previews on identical geometry/camera.
Saves + checkpoint. Visual judgement happens outside (the images are the evidence).
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
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
mt = rt.load_lib(os.path.join(HERE, "ww_materials.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_studio")
body, lid = bpy.data.objects["WW_BODY_FRAME"], bpy.data.objects["WW_LID_PIVOT"]
C = ww.vmm(P["shell"]["center_world"])
axis = ww.world_axis(body)

# neutral studio (start values; tuned in phase 4)
wr.world_grey(sc, 0.4, 0.5)
wr.area_light("WW_LIGHT_KEY", col, C + Vector((-0.6, -0.55, 0.75)), C, 1.2, 0.8, 250.0, (1.0, 0.96, 0.9))
wr.area_light("WW_LIGHT_FILL", col, C + Vector((0.7, -0.5, 0.05)), C, 1.0, 1.0, 60.0)
wr.area_light("WW_LIGHT_STRIP", col, C + Vector((0.35, 0.8, 0.55)), C, 0.15, 1.6, 120.0)
strip_test = bpy.data.objects.get("WW_TEST_STRIP")
if strip_test:
    strip_test.hide_render = True

lid0 = lid.matrix_local.copy()
out = {}
den, den_items = wr.denoiser_choice(sc)
try:
    lid.matrix_local = lid0 @ Matrix.Rotation(math.radians(-95), 4, "X")
    bpy.context.view_layer.update()
    ring_pt = body.matrix_world @ Vector((0, -0.0425, 0.030))
    knob = body.matrix_world @ Vector((0.080, 0, 0))
    xw = ww.world_axis(body, (1, 0, 0))
    watch_pt = body.matrix_world @ Vector((0, 0, 0.034))
    crops = {
        "guilloche": st.camera("WW_CAM_CROP", col, ring_pt + axis * 0.07 + Vector((0, 0, 0.012)), ring_pt, lens=100),
    }
    for name, cam_fn in (
        ("guilloche", lambda: st.camera("WW_CAM_CROP", col, ring_pt + axis * 0.07 + Vector((0, 0, 0.012)), ring_pt, lens=100)),
        ("knurl", lambda: st.camera("WW_CAM_CROP", col, knob + xw * 0.05 + Vector((0, -0.03, 0.02)), knob - xw * 0.004, lens=100)),
        ("leather-watch", lambda: st.camera("WW_CAM_CROP", col, watch_pt + axis * 0.13 + Vector((0.03, -0.01, 0.03)), watch_pt, lens=100)),
    ):
        cam = cam_fn()
        for dn in (True, False):
            tag = "denoised" if dn else "raw"
            path, secs, settings = wr.cycles_still(sc, cam, os.path.join(wr.RENDERS, f"phase3-crop-{name}-{tag}.png"), 640, 640, 64, dn)
            stats = lib.frame_stats(path)
            assert stats["stdev"] > 0.01, (name, stats)
            out[f"{name}-{tag}"] = {"path": path, "seconds": secs, "stats": {k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}}
    lid.matrix_local = lid0
    bpy.context.view_layer.update()
    hero = bpy.data.objects["WW_CAM_CONCEPT"]
    mats = {m.name: m for m in bpy.data.materials if m.get("ww_material")}
    keyed = {"graphite": mats["WW_MAT_GRAPHITE"], "walnut": mats["WW_MAT_WALNUT"], "acrylic": mats["WW_MAT_ACRYLIC"]}
    for variant in ("graphite", "walnut"):
        for ob in (bpy.data.objects["WW_SHELL"], bpy.data.objects["WW_REAR_SERVICE_COVER"]):
            ob.data.materials.clear()
            ob.data.materials.append(keyed[variant])
        path, secs, settings = wr.cycles_still(sc, hero, os.path.join(wr.RENDERS, f"phase3-preview-{variant}.png"), 768, 512, 64, True)
        out[f"preview-{variant}"] = {"path": path, "seconds": secs, "settings": settings, "camera_matrix": [list(r) for r in hero.matrix_world]}
    for ob in (bpy.data.objects["WW_SHELL"], bpy.data.objects["WW_REAR_SERVICE_COVER"]):
        ob.data.materials.clear()
        ob.data.materials.append(keyed["graphite"])
    sc["ww_shell_variant"] = "graphite"
finally:
    lid.matrix_local = lid0
    bpy.context.view_layer.update()
    crop_cam = bpy.data.objects.get("WW_CAM_CROP")
    if crop_cam:
        bpy.data.objects.remove(crop_cam, do_unlink=True)

assert out["preview-graphite"]["camera_matrix"] == out["preview-walnut"]["camera_matrix"]
main = os.path.join(ww.BUILD, "watch-winder-capsule.blend")
ck = os.path.join(ww.BUILD, "checkpoints", "phase3-detail-materials.blend")
if not bpy.app.background:  # only the GUI session writes the working file (isolated rebuilds must not)
    assert bpy.ops.wm.save_as_mainfile(filepath=main) == {"FINISHED"}
    assert bpy.ops.wm.save_as_mainfile(filepath=ck, copy=True) == {"FINISHED"}
ww.write_json(ww.state_path("reports", "phase3-gate.json"),
              {"renders": out, "denoiser": den, "denoiser_items": den_items, "blend_sha256": ww.sha256_file(main),
               "parameters_sha256": ww.sha256_file(ww.PARAM_PATH), "devices": wr.probe_devices()})
rt.emit_ok("pass-17-phase3-gate-material-crops", renders=sorted(out), denoiser=den,
           seconds={k: v["seconds"] for k, v in out.items()}, blend_sha256=ww.sha256_file(main)[:16])

"""Pass 20 — final stills: hero / rear / open at 3072x2048, Cycles <= 2048 samples adaptive
(threshold recorded) + OpenImageDenoise; plus an f/8 inspection hero at 1536x1024.
argv: [samples] [adaptive_threshold] [device]. Records per-image settings, seconds, sha256.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
P = ww.P
sc = ww.activate()
samples = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
if len(sys.argv) > 3:
    sc.cycles.device = sys.argv[3]
    if sys.argv[3] == "GPU":  # a headless process starts with fresh prefs: enable Metal explicitly and verify
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        assert any(d.use and d.type == "METAL" for d in prefs.devices), "no Metal device enabled"
FINAL = os.path.join(ww.BUILD, "renders", "final")
os.makedirs(FINAL, exist_ok=True)
pz.set_variant(sc, "graphite")
den, den_items = wr.denoiser_choice(sc)
assert den == "OPENIMAGEDENOISE", den_items

out = {}
import json  # noqa: E402
preset_names = [k for k in json.loads(sc["ww_presets_json"]) if not k.startswith("_")]
jobs = [(p, f"{p}-graphite.png", 3072, 2048, None) for p in preset_names] + [("hero", "hero-graphite-f8-inspection.png", 1536, 1024, 8.0)]
only = sys.argv[4].split(",") if len(sys.argv) > 4 else None  # one image per headless job keeps each run short
if only:
    jobs = [j for j in jobs if j[1] in only]
# merge with an earlier partial report so per-image jobs accumulate into one record
rep_path = ww.state_path("reports", "final-renders.json")
if os.path.exists(rep_path):
    with open(rep_path, "r", encoding="utf-8") as fh:
        out = json.load(fh).get("renders", {})
for preset, fname, w, h, fstop in jobs:
    pz.apply(sc, preset, P)
    cam = sc.camera
    saved_f = cam.data.dof.aperture_fstop
    if fstop:
        cam.data.dof.aperture_fstop = fstop
    try:
        path, secs, settings = wr.cycles_still(sc, cam, os.path.join(FINAL, fname), w, h, samples if not fstop else min(samples, 512), True, adaptive_threshold=threshold)
    finally:
        cam.data.dof.aperture_fstop = saved_f
    stats = lib.frame_stats(path)
    assert stats["stdev"] > 0.01 and not stats["black"] and not stats["blown"], (fname, stats)
    img = bpy.data.images.load(path, check_existing=False)
    size = tuple(img.size)
    bpy.data.images.remove(img)
    assert size == (w, h), (fname, size)
    settings["fstop"] = fstop or saved_f
    out[fname] = {"path": path, "seconds": secs, "settings": settings, "size": size, "camera": cam.name,
                  "camera_matrix": list(map(list, cam.matrix_world)), "sha256": ww.sha256_file(path),
                  "stats": {k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}}
pz.apply(sc, "hero", P)
main = os.path.join(ww.BUILD, "watch-winder-capsule.blend")
if not bpy.app.background:  # the GUI session owns the working file; a headless render run never writes it
    assert bpy.ops.wm.save_as_mainfile(filepath=main) == {"FINISHED"}
    assert bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ww.BUILD, "checkpoints", "phase5-final.blend"), copy=True) == {"FINISHED"}
ww.write_json(rep_path,
              {"renders": out, "denoiser": den, "blend_sha256": ww.sha256_file(main), "parameters_sha256": ww.sha256_file(ww.PARAM_PATH),
               "blender": bpy.app.version_string, "device": sc.cycles.device,
               "lights": {o.name: (list(map(list, o.matrix_world)), o.data.energy) for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("WW_LIGHT") and not o.hide_render}})
rt.emit_ok("pass-20-final-renders", images=sorted(out), seconds={k: v["seconds"] for k, v in out.items()},
           samples=samples, adaptive_threshold=threshold, denoiser=den, device=sc.cycles.device,
           blend_sha256=ww.sha256_file(main)[:16])

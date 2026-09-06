"""Pass 26 — film frames (headless, Metal GPU): Cycles 1920x1080, argv samples (default 128)
adaptive 0.02 + OpenImageDenoise, frames [start..end] to renders/film/frames/frame_####.png.
Skips frames already present and complete (resumable per frame). Records per-frame seconds.
argv: [samples] [start] [end]
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
sc = bpy.data.scenes["WW_capsule"]
bpy.context.window.scene = sc
samples = int(sys.argv[1]) if len(sys.argv) > 1 else 128
start = int(sys.argv[2]) if len(sys.argv) > 2 else sc.frame_start
end = int(sys.argv[3]) if len(sys.argv) > 3 else sc.frame_end
cam_arg = sys.argv[4] if len(sys.argv) > 4 else "WW_CAM_VIDEO"
markers = sorted((m for m in sc.timeline_markers if m.camera), key=lambda m: m.frame)


def camera_for(f):
    if cam_arg != "markers":
        return bpy.data.objects[cam_arg]
    return max((m for m in markers if m.frame <= f), key=lambda m: m.frame).camera


cam = camera_for(start)
assert cam.animation_data and cam.animation_data.action, "film camera has no keys: wrong file?"
OUT = os.path.join(ww.BUILD, "renders", "film", "frames" if cam_arg != "markers" else "detail-frames")
os.makedirs(OUT, exist_ok=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "METAL"
sc.cycles.device = "GPU"
sc.render.use_persistent_data = True  # same scene every frame: persistent data is safe and faster here
log = {}
den, _ = wr.denoiser_choice(sc)
for f in range(start, end + 1):
    path = os.path.join(OUT, f"frame_{f:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 50000:
        continue
    sc.frame_set(f)
    cam = camera_for(f)
    _, secs, settings = wr.cycles_still(sc, cam, path, 1920, 1080, samples, True, adaptive_threshold=0.02)
    log[f] = secs
stats = lib.frame_stats(os.path.join(OUT, f"frame_{end:04d}.png"))
assert stats["stdev"] > 0.01 and not stats["black"]
done = sorted(int(n[6:10]) for n in os.listdir(OUT) if n.startswith("frame_") and n.endswith(".png"))
with open(os.path.join(ww.BUILD, "renders", "film", f"{os.path.basename(OUT)}-log-{start:04d}-{end:04d}.json"), "w", encoding="utf-8") as fh:
    json.dump({"seconds": log, "samples": samples, "adaptive_threshold": 0.02, "denoiser": den, "device": sc.cycles.device,
               "blend": bpy.data.filepath, "blend_sha256": ww.sha256_file(bpy.data.filepath)}, fh, indent=1)
rt.emit_ok("pass-26-film-render-frames", rendered=len(log), start=start, end=end, frames_present=len(done),
           seconds_total=round(sum(log.values()), 1), seconds_per_frame=round(sum(log.values()) / max(1, len(log)), 2),
           samples=samples, denoiser=den, device=sc.cycles.device)

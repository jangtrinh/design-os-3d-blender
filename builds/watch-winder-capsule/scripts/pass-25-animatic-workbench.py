"""Pass 25 — animatic (<= 120 frames): every 3rd frame of the film at 480x270 with Workbench
(motion/timing/framing check only; not shading). Writes renders/animatic/frame_####.png and a
frame list; encoding + inspection happen on the host. Restores render settings.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
sc = ww.activate()
use_markers = len(sys.argv) > 1 and sys.argv[1] == "markers"
markers = sorted((m for m in sc.timeline_markers if m.camera), key=lambda m: m.frame)
cam = bpy.data.objects["WW_CAM_VIDEO"] if not use_markers else markers[0].camera
tag = "detail" if use_markers else "film"
OUT = os.path.join(ww.BUILD, "renders", "animatic" if not use_markers else "animatic-detail")
os.makedirs(OUT, exist_ok=True)
step = 3
frames = list(range(sc.frame_start, sc.frame_end + 1, step))
assert len(frames) <= 130, len(frames)
r = sc.render
saved = (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath, sc.camera, r.image_settings.file_format,
         r.image_settings.color_mode, sc.display.shading.light, sc.display.shading.color_type, sc.frame_current)
try:
    r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage = "BLENDER_WORKBENCH", 480, 270, 100
    r.image_settings.file_format, r.image_settings.color_mode = "PNG", "RGB"
    sc.display.shading.light, sc.display.shading.color_type = "STUDIO", "MATERIAL"
    sc.camera = cam
    written = []
    for f in frames:
        sc.frame_set(f)
        if use_markers:
            sc.camera = max((m for m in markers if m.frame <= f), key=lambda m: m.frame).camera
        r.filepath = os.path.join(OUT, f"frame_{f:04d}.png")
        with bpy.context.temp_override(scene=sc):
            assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
        written.append(r.filepath)
finally:
    (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath, sc.camera, r.image_settings.file_format,
     r.image_settings.color_mode, sc.display.shading.light, sc.display.shading.color_type, fc) = saved
    sc.frame_set(fc)
stats = {f: lib.frame_stats(p)["stdev"] for f, p in zip(frames[::20], written[::20])}
assert all(v > 0.01 for v in stats.values()), stats
assert all(os.path.getsize(p) > 2000 for p in written)
ww.write_json(os.path.join(OUT, "frames.json"), {"frames": frames, "step": step, "files": written})
rt.emit_ok("pass-25-animatic-workbench", frames_rendered=len(written), first=frames[0], last=frames[-1], frame_step=step,
           sample_stdev={str(k): round(v, 4) for k, v in stats.items()})

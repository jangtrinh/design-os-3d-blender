"""Pass 31 — Cycles stills of the print plates (headless): one 3/4 shot per plate + one wide
overview, on a light studio ground with two area lights, same colour management as the finals.
Opens watch-winder-capsule-plates.blend (scene WW_plates from pass-30). Resumable: existing images
are skipped. argv: [samples] [adaptive_threshold] [device] [only: comma list of plate ids|overview]
Postconditions: every image non-black/non-blown, every plate corner inside the frame (margin >= 0.03).
"""
import json
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
wr = rt.load_lib(os.path.join(HERE, "ww_render.py"))
mt = rt.load_lib(os.path.join(HERE, "ww_materials.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
device = sys.argv[3] if len(sys.argv) > 3 else "GPU"
only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
sc = bpy.data.scenes["WW_plates"]
bpy.context.window.scene = sc
if device == "GPU":
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
sc.cycles.device = device
sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Medium High Contrast"
with open(os.path.join(ww.BUILD, "plates", "manifest.json"), "r", encoding="utf-8") as fh:
    plates = json.load(fh)["plates"]
col = bpy.data.collections.get("WW_plates_studio") or bpy.data.collections.new("WW_plates_studio")
if col.name not in sc.collection.children:
    sc.collection.children.link(col)

# --- studio: ground under the plate slabs, grey world, key + fill ---
xs = [p["origin_mm"][0] for p in plates] + [p["origin_mm"][0] + p["size_mm"][0] for p in plates]
ys = [p["origin_mm"][1] for p in plates] + [p["origin_mm"][1] + p["size_mm"][1] for p in plates]
cx, cy = (min(xs) + max(xs)) / 2 * 0.001, (min(ys) + max(ys)) / 2 * 0.001
gm = mt.mat_simple("PL_MAT_GROUND", "#7A7A7A", 0.9)
ww.mesh_obj("PL_GROUND", [(cx - 4, cy - 4, -0.0031), (cx + 4, cy - 4, -0.0031), (cx + 4, cy + 4, -0.0031), (cx - 4, cy + 4, -0.0031)],
            [(0, 1, 2, 3)], col, material=gm, role="studio_ground")
if sc.world is None:
    sc.world = bpy.data.worlds.new("WW_plates_world")
    sc.world.use_nodes = True
wr.world_grey(sc, 0.25)
wr.area_light("PL_LIGHT_KEY", col, Vector((cx - 0.6, cy - 0.9, 1.2)), Vector((cx, cy, 0)), 1.6, 1.6, 140.0)
wr.area_light("PL_LIGHT_FILL", col, Vector((cx + 1.2, cy + 0.6, 0.9)), Vector((cx, cy, 0)), 2.0, 2.0, 50.0)


def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def fit(name, lo, hi, az, el, fill, lens):
    """Perspective camera at (az, el) whose frame the bbox corners fill by `fill` (iterative)."""
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    c, d = (lo + hi) / 2, 1.0
    a, e = math.radians(az), math.radians(el)
    for _ in range(5):
        loc = c + Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))
        cam = st.camera(name, col, loc, c, lens=lens)
        bpy.context.view_layer.update()
        uv = [world_to_camera_view(sc, cam, p) for p in corners]
        span = max(max(q.x for q in uv) - min(q.x for q in uv), max(q.y for q in uv) - min(q.y for q in uv))
        d *= span / fill
        # re-centre in the image plane (a perspective view of a flat row projects off-centre)
        for _ in range(2):
            uv = [world_to_camera_view(sc, cam, p) for p in corners]
            du, dv = 0.5 - (min(q.x for q in uv) + max(q.x for q in uv)) / 2, 0.5 - (min(q.y for q in uv) + max(q.y for q in uv)) / 2
            W = d * 36.0 / lens
            cam.matrix_world.translation += cam.matrix_world.to_3x3() @ Vector((-du * W, -dv * W * sc.render.resolution_y / sc.render.resolution_x, 0.0))
            c = c + (cam.matrix_world.to_3x3() @ Vector((-du * W, -dv * W * sc.render.resolution_y / sc.render.resolution_x, 0.0)))
            bpy.context.view_layer.update()
    uv = [world_to_camera_view(sc, cam, p) for p in corners]
    margins = [min(q.x for q in uv), 1 - max(q.x for q in uv), min(q.y for q in uv), 1 - max(q.y for q in uv)]
    return cam, [round(m, 3) for m in margins]


OUT = os.path.join(ww.BUILD, "renders", "plates")
os.makedirs(OUT, exist_ok=True)
jobs = [(p["id"], [o for o in sc.objects if o.name.startswith("PL_PLATE_" + p["id"]) or o.get("pl_plate") == p["id"]], -35, 48, 0.82, 50.0, (3072, 2048)) for p in plates]
jobs.append(("overview", [o for o in sc.objects if o.name.startswith("PL_PLATE_") or o.get("pl_plate")], -24, 42, 0.9, 45.0, (3072, 2048)))
# print-material looks: the PETG shell/cover use the delivered matte graphite tree, the clear
# resin visor the delivered acrylic tree; lathe/knurl parts are shaded smooth for the render only
petg, clear = mt.mat_graphite(), mt.mat_acrylic()
for ob in sc.objects:
    if ob.get("pl_bucket") == "fdm-petg":
        ob.data.materials.clear(); ob.data.materials.append(petg)
    elif ob.get("pl_bucket") == "sla-clear":
        ob.data.materials.clear(); ob.data.materials.append(clear)
    if ob.get("pl_part") and len(ob.data.polygons) > 200:
        ob.data.shade_smooth()
report, den = {}, wr.denoiser_choice(sc)[0]
for pid, objs, az, el, fill, lens, (w, h) in jobs:
    if only and pid not in only:
        continue
    assert objs, pid
    sc.render.resolution_x, sc.render.resolution_y = w, h
    cam, margins = fit("PL_CAMR_" + pid, *bbox(objs), az, el, fill, lens)
    assert min(margins) >= 0.03, (pid, margins)
    path = os.path.join(OUT, f"plate-{pid}.png")
    secs = 0.0
    if not (os.path.exists(path) and os.path.getsize(path) > 100000):
        _, secs, _ = wr.cycles_still(sc, cam, path, w, h, samples, True, adaptive_threshold=threshold)
    stats = lib.frame_stats(path)
    assert stats["stdev"] > 0.01 and not stats["black"] and not stats["blown"], (pid, stats)
    report[pid] = {"path": path, "seconds": round(secs, 1), "margins": margins, "size": [w, h], "sha256": ww.sha256_file(path),
                   "stats": {k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}}
if not only:
    assert bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ww.BUILD, "watch-winder-capsule-plates.blend"), copy=True) == {"FINISHED"}
ww.write_json(ww.state_path("reports", "print-plates-renders.json"),
              {"renders": report, "samples": samples, "adaptive_threshold": threshold, "device": sc.cycles.device, "denoiser": den,
               "blend_sha256": ww.sha256_file(bpy.data.filepath)})
rt.emit_ok("pass-31-print-plates-render", images=list(report), seconds={k: v["seconds"] for k, v in report.items()},
           margins={k: v["margins"] for k, v in report.items()}, device=sc.cycles.device, denoiser=den, samples=samples)

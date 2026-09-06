"""Pass 19 — render the three presets (hero, rear, open) at a given size/samples.
argv: <tag> <width> <samples> [device]   e.g. preview 512 32  |  review 1024 96 GPU
Restores the hero preset afterwards. Postconditions: non-flat frames, identical camera/lights
across variants (recorded), seconds per frame.
"""
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
tag = sys.argv[1] if len(sys.argv) > 1 else "preview"
width = int(sys.argv[2]) if len(sys.argv) > 2 else 512
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 32
if len(sys.argv) > 4:
    sc.cycles.device = sys.argv[4]
height = width * 2 // 3
pz.set_variant(sc, "graphite")

out = {}
lights = {o.name: (list(map(list, o.matrix_world)), o.data.energy) for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("WW_LIGHT")}
for preset in ("hero", "rear", "open"):
    pz.apply(sc, preset, P)
    cam = sc.camera
    path, secs, settings = wr.cycles_still(sc, cam, os.path.join(wr.RENDERS, f"{tag}-{preset}.png"), width, height, samples, True)
    stats = lib.frame_stats(path)
    assert stats["stdev"] > 0.01 and not stats["black"] and not stats["blown"], (preset, stats)
    out[preset] = {"path": path, "seconds": secs, "settings": settings, "camera": cam.name,
                   "camera_matrix": list(map(list, cam.matrix_world)), "stats": {k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()}}
pz.apply(sc, "hero", P)
ww.write_json(ww.state_path("reports", f"renders-{tag}.json"), {"renders": out, "lights": lights, "device": sc.cycles.device})
rt.emit_ok(f"pass-19-{tag}-renders", width=width, height=height, samples=samples, device=sc.cycles.device,
           seconds={k: v["seconds"] for k, v in out.items()}, stats={k: v["stats"]["mean"] for k, v in out.items()})

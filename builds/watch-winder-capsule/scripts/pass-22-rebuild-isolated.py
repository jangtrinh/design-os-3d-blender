"""Pass 22 — rebuild the whole asset from the pass scripts in a FRESH factory-startup process
(no checkpoint input), then write an inventory (object names, types, parents, base vertex
counts, materials) to reports/rebuild-isolated.json for comparison with the GUI build.
Run: bash scripts/headless-run.sh builds/watch-winder-capsule/scripts/pass-22-rebuild-isolated.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

assert bpy.app.background and not bpy.data.filepath, "must start from factory startup with no file"
PASSES = [f for f in sorted(os.listdir(HERE)) if f.startswith("pass-") and f[5:7].isdigit() and 1 <= int(f[5:7]) <= 18]
verdicts = {}
for name in PASSES:
    path = os.path.join(HERE, name)
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    ns = {"__name__": "__main__", "__file__": path, "__builtins__": __builtins__}
    seq = rt._STATE["seq"]
    exec(compile(src, path, "exec"), ns)  # a failing pass raises here and ends the run as AGENT_FAIL
    tag, verdict = rt._STATE["last"]
    assert rt._STATE["seq"] > seq and tag == rt.SENTINEL_OK, (name, tag)
    verdicts[name] = verdict["step"]


def inventory():
    inv = {}
    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        if not o.name.startswith("WW_"):
            continue
        inv[o.name] = {"type": o.type, "parent": o.parent.name if o.parent else None, "role": o.get("ww_role", ""),
                       "verts": len(o.data.vertices) if o.type == "MESH" else None,
                       "material": (o.data.materials[0].name if o.type == "MESH" and o.data.materials and o.data.materials[0] else None),
                       "modifiers": [m.type for m in o.modifiers] if o.type == "MESH" else []}
    return inv


inv = inventory()
ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
out = os.path.join(ww.BUILD, "reports", "rebuild-isolated.json")
ww.write_json(out, {"passes": verdicts, "inventory": inv, "object_count_WW": len(inv), "blender": bpy.app.version_string,
                    "scenes": [s.name for s in bpy.data.scenes]})
rt.emit_ok("pass-22-rebuild-isolated", passes=len(verdicts), object_count_WW=len(inv),
           scenes=[s.name for s in bpy.data.scenes], inventory_path=out)

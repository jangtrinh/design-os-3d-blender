"""Export verification that never touches the live scene.

The re-import runs in a separate `--factory-startup -b` Blender process, so a
missing file, a broken export, or a wrong format cannot wipe unsaved work.
"""
import json
import os
import subprocess
import tempfile

import bpy

IMPORT_OPS = {".glb": ("import_scene", "gltf"), ".gltf": ("import_scene", "gltf"),
              ".fbx": ("wm", "fbx_import"), ".obj": ("wm", "obj_import")}

CHECKER = '''import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
out = {"objects": [], "tris": 0, "error": None}
try:
    bpy.ops.wm.read_homefile(use_empty=True)
    getattr(getattr(bpy.ops, a[1]), a[2])(filepath=a[0])
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            out["tris"] += len(o.data.loop_triangles)
    out["objects"] = sorted(o.name for o in bpy.data.objects)
except Exception as exc:
    out["error"] = repr(exc)
print("EXPORT_CHECK " + json.dumps(out))
'''


def import_op(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMPORT_OPS:
        raise ValueError(f"unsupported format: {path}")
    mod, op = IMPORT_OPS[ext]
    if (mod, op) == ("wm", "fbx_import") and bpy.app.version < (5, 0):
        mod, op = "import_scene", "fbx"
    return mod, op


def import_any(path):
    """Version-branched import INTO THE CURRENT SCENE (mutating by design)."""
    mod, op = import_op(path)
    return getattr(getattr(bpy.ops, mod), op)(filepath=path)


def verify_export(path, expect_objects, expect_min_tris, timeout=300):
    """An export is not verified until re-imported — in another process."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise AssertionError(f"export file does not exist: {path}")
    mod, op = import_op(path)
    exe = os.environ.get("BLENDER_BIN") or bpy.app.binary_path
    fd, checker = tempfile.mkstemp(suffix="-export-check.py")
    with os.fdopen(fd, "w") as fh:
        fh.write(CHECKER)
    try:
        proc = subprocess.run(
            [exe, "--factory-startup", "-b", "--python-exit-code", "3",
             "--python", checker, "--", path, mod, op],
            capture_output=True, text=True, timeout=timeout)
    finally:
        os.unlink(checker)
    hits = [ln for ln in proc.stdout.splitlines()
            if ln.startswith("EXPORT_CHECK ")]
    if not hits:
        raise AssertionError(
            f"re-import subprocess gave no result (rc={proc.returncode})\n"
            f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    res = json.loads(hits[-1][len("EXPORT_CHECK "):])
    if res["error"]:
        raise AssertionError(f"re-import failed: {res['error']}")
    assert len(res["objects"]) >= expect_objects, (expect_objects, res["objects"])
    assert res["tris"] >= expect_min_tris, res["tris"]
    return res

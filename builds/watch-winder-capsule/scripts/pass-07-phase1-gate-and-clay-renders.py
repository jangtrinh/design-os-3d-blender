"""Pass 07 — Phase-1 gate: re-measure everything from evaluated geometry, clay renders
(front/side/top ortho + concept angle), save the working file + checkpoint, gate report.
"""
import hashlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
C = ww.vmm(P["shell"]["center_world"])
body, rotor, visor = (bpy.data.objects[n] for n in ("WW_BODY_FRAME", "WW_ROTOR_PIVOT", "WW_VISOR"))
meshes = [o for o in ww.ww_objects() if o.type == "MESH"]                        # product audit set
all_meshes = [o for o in ww.ww_objects(product_only=False) if o.type == "MESH"]  # incl. cutters/envelope/ground
roles = {}
for o in meshes:
    roles[o.get("ww_role", "")] = roles.get(o.get("ww_role", ""), 0) + 1

axis = ww.world_axis(body)
g = {
    "axis_elevation_deg": round(ww.elevation_deg(axis), 4),
    "unit_scale_length": sc.unit_settings.scale_length,
    "unit_system": sc.unit_settings.system,
    "all_mesh_scale_unity": all(max(abs(s - 1.0) for s in o.matrix_world.to_scale()) < 1e-6 for o in all_meshes),
    "visor_axis_vs_body_deg": round(math.degrees(ww.world_axis(visor).angle(axis)), 5),
    "rotor_axis_vs_body_deg": round(math.degrees(ww.world_axis(rotor).angle(axis)), 5),
    "role_counts": roles,
    "feet_bottom_z_mm": [round(ww.evaluated_bbox(o)[0].z * 1000, 4) for o in meshes if o.get("ww_role") == "foot"],
    "validate_fixed_any": any(o.get("ww_validate_fixed") for o in all_meshes),
    "object_count_WW": len(ww.ww_objects(product_only=False)),
}
boxes = {o.name: ww.evaluated_bbox(o) for o in meshes if not o.hide_render}
empty = [n for n, b in boxes.items() if b is None]
assert not empty, f"objects with empty evaluated geometry: {empty}"
lo = Vector((min(b[0][i] for b in boxes.values()) for i in range(3)))
hi = Vector((max(b[1][i] for b in boxes.values()) for i in range(3)))
g["product_bbox_mm"] = {"min": [round(v * 1000, 2) for v in lo], "max": [round(v * 1000, 2) for v in hi]}
vis_r = max((p - C).length for p in ww.evaluated_verts_world(visor)) * 1000
g["visor_max_radius_from_C_mm"] = round(vis_r, 3)
g["visor_rim_clearance_mm"] = P["front_rim"]["r_in"] - P["visor"]["outer_radius"]

assert abs(g["axis_elevation_deg"] - 50.0) <= 0.1
assert g["unit_scale_length"] == 1.0 and g["all_mesh_scale_unity"]
assert g["visor_axis_vs_body_deg"] < 0.01 and g["rotor_axis_vs_body_deg"] < 0.01
assert roles.get("knob") == 2 and roles.get("foot") == 3 and roles.get("leg") == 3
assert roles.get("control") == 2 and roles.get("watch") == 1 and roles.get("usb_receptacle") == 1
assert all(abs(z) < 0.1 for z in g["feet_bottom_z_mm"])
assert not g["validate_fixed_any"], "mesh.validate had to repair something"

# Clay renders: ortho front/side/top + concept angle
center = (lo + hi) / 2.0
radius = (hi - lo).length / 2.0
col = ww.coll("WW_studio")
cams = st.ortho_views(col, center, radius)
cams["concept"] = bpy.data.objects["WW_CAM_CONCEPT"]
renders = {}
for key, cam in cams.items():
    path = os.path.join(st.RENDERS, f"phase1-clay-{key}.png")
    st.clay_render(sc, cam, path, 1024, 1024)
    renders[key] = path
    assert os.path.getsize(path) > 10000, path

# Save working file + checkpoint copy
main = os.path.join(ww.BUILD, "watch-winder-capsule.blend")
ck = os.path.join(ww.BUILD, "checkpoints", "phase1-blockout.blend")
os.makedirs(os.path.dirname(ck), exist_ok=True)
if not bpy.app.background:  # only the GUI session writes the working file (isolated rebuilds must not)
    assert bpy.ops.wm.save_as_mainfile(filepath=main) == {"FINISHED"}
    assert bpy.ops.wm.save_as_mainfile(filepath=ck, copy=True) == {"FINISHED"}
script_hashes = {f: ww.sha256_file(os.path.join(HERE, f))[:16] for f in sorted(os.listdir(HERE)) if f.endswith(".py")}
g.update({"renders": renders, "blend": main, "blend_sha256": ww.sha256_file(main), "checkpoint": ck,
          "parameters_sha256": ww.sha256_file(ww.PARAM_PATH), "script_sha256_16": script_hashes,
          "blender": bpy.app.version_string})
ww.write_json(ww.state_path("reports", "phase1-gate.json"), g)
rt.emit_ok("pass-07-phase1-gate-and-clay-renders", **{k: v for k, v in g.items() if k not in ("script_sha256_16",)})

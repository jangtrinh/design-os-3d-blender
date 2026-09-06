"""Pass 21 — acceptance in an ISOLATED headless process: reopen the final blend, re-measure the
mandatory gates from evaluated geometry, check materials/cameras/presets resolve, verify the
final PNGs (size, sha256 unchanged since render), and write reports/acceptance.json.
Run: HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend <final.blend> pass-21-...py
"""
import hashlib
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
P = ww.P
assert bpy.app.background, "acceptance must run isolated"
sc = bpy.data.scenes["WW_capsule"]
bpy.context.window.scene = sc
blend = bpy.data.filepath
meshes = [o for o in ww.ww_objects() if o.type == "MESH" and o.get("ww_role") not in ("cutter", "internal_envelope", "studio_ground")]
body, rotor, visor, lid = (bpy.data.objects[n] for n in ("WW_BODY_FRAME", "WW_ROTOR_PIVOT", "WW_VISOR", "WW_LID_PIVOT"))
C = ww.vmm(P["shell"]["center_world"])
pz.apply(sc, "hero", P)

axis = ww.world_axis(body)
g = {"axis_elevation_deg": round(ww.elevation_deg(axis), 4), "unit_scale_length": sc.unit_settings.scale_length,
     "all_mesh_scale_unity": all(max(abs(s - 1) for s in o.matrix_world.to_scale()) < 1e-6 for o in meshes),
     "visor_axis_vs_body_deg": round(math.degrees(ww.world_axis(visor).angle(axis)), 5),
     "rotor_axis_vs_body_deg": round(math.degrees(ww.world_axis(rotor).angle(axis)), 5)}
roles = {}
for o in meshes:
    roles[o.get("ww_role", "")] = roles.get(o.get("ww_role", ""), 0) + 1
g["role_counts"] = roles
g["feet_bottom_z_mm"] = [round(ww.evaluated_bbox(o)[0].z * 1000, 4) for o in meshes if o.get("ww_role") == "foot"]
kl, kr = ww.evaluated_bbox(bpy.data.objects["WW_KNOB_L"]), ww.evaluated_bbox(bpy.data.objects["WW_KNOB_R"])
g["knob_mirror_error_mm"] = round(max(abs(kl[0].x + kr[1].x), abs(kl[1].x + kr[0].x), abs(kl[0].z - kr[0].z)) * 1000, 4)
vis = [(p - C) for p in ww.evaluated_verts_world(visor)]
eq = [v for v in vis if abs(v.dot(axis) - P["shell"]["opening_datum_w0"] * 0.001 - P["visor"]["rim_clearance"] * 0.001) < 0.0002]
g["visor_equator_radius_mm"] = round(max((v - v.dot(axis) * axis).length for v in eq) * 1000, 3) if eq else None
import bmesh  # noqa: E402
bm = bmesh.new()
bm.from_mesh(visor.data)
g["visor_nonmanifold_edges"] = sum(1 for e in bm.edges if not e.is_manifold)
bm.free()
zeq = (P["shell"]["opening_datum_w0"] + P["visor"]["rim_clearance"]) * 0.001
dome_c = C + axis * zeq
dome = [(p - dome_c).length for p in ww.evaluated_verts_world(visor) if (p - dome_c).dot(axis) > 0.005]
g["visor_thickness_mm"] = round((max(dome) - min(dome)) * 1000, 3)
assert abs(g["visor_thickness_mm"] - P["visor"]["thickness"]) < 0.05, g["visor_thickness_mm"]
inv = body.matrix_world.inverted()
cush = [inv @ p for p in ww.evaluated_verts_world(bpy.data.objects["WW_CUSHION"])]
g["cushion_max_radius_mm"] = round(max(math.hypot(p.x, p.y) for p in cush) * 1000, 3)
g["cup_bore_mm"] = P["inner"]["cup_mouth_radius"] - P["inner"]["cup_wall"]
names = [o.name for o in bpy.data.objects if o.name.startswith("WW_")]
g["duplicate_suffix_objects"] = [n for n in names if n[-4:-3] == "." and n[-3:].isdigit()]
g["unmaterialed_render_meshes"] = [o.name for o in meshes if not o.data.materials or o.data.materials[0] is None]
g["materials_without_output_link"] = [m.name for m in bpy.data.materials if m.get("ww_material") and not any(n.type == "OUTPUT_MATERIAL" and n.inputs["Surface"].is_linked for n in m.node_tree.nodes)]
g["cameras"] = {n: (bpy.data.objects[n].data.lens, bpy.data.objects[n].data.dof.aperture_fstop) for n in ("WW_CAM_HERO", "WW_CAM_REAR", "WW_CAM_OPEN")}
g["presets"] = sorted(k for k in json.loads(sc["ww_presets_json"]) if not k.startswith("_"))
g["shell_variant"] = sc.get("ww_shell_variant")
g["shell_material"] = bpy.data.objects["WW_SHELL"].data.materials[0].name

assert abs(g["axis_elevation_deg"] - 50.0) <= 0.1 and g["unit_scale_length"] == 1.0 and g["all_mesh_scale_unity"]
assert g["visor_axis_vs_body_deg"] < 0.01 and g["rotor_axis_vs_body_deg"] < 0.01
assert roles.get("knob") == 2 and roles.get("foot") == 3 and roles.get("leg") == 3 and roles.get("control") == 2 and roles.get("watch") == 1
assert all(abs(z) < 0.1 for z in g["feet_bottom_z_mm"]) and g["knob_mirror_error_mm"] < 0.01
assert g["visor_nonmanifold_edges"] == 0 and g["cushion_max_radius_mm"] < g["cup_bore_mm"]
assert not g["duplicate_suffix_objects"] and not g["unmaterialed_render_meshes"] and not g["materials_without_output_link"]

final_dir = os.path.join(ww.BUILD, "renders", "final")
rep_path = os.path.join(ww.BUILD, "reports", "final-renders.json")
with open(rep_path, "r", encoding="utf-8") as fh:
    fin = json.load(fh)
images = {}
for fname, rec in fin["renders"].items():
    p = os.path.join(final_dir, fname)
    img = bpy.data.images.load(p, check_existing=False)
    images[fname] = {"size": tuple(img.size), "sha256": ww.sha256_file(p), "sha_matches_render_record": ww.sha256_file(p) == rec["sha256"],
                     "settings": rec["settings"], "seconds": rec["seconds"]}
    bpy.data.images.remove(img)
    assert images[fname]["sha_matches_render_record"], fname
assert images["hero-graphite.png"]["size"] == (3072, 2048)
scripts = {f: ww.sha256_file(os.path.join(HERE, f)) for f in sorted(os.listdir(HERE)) if f.endswith(".py")}
acc = {"blend": blend, "blend_sha256": ww.sha256_file(blend), "parameters_sha256": ww.sha256_file(ww.PARAM_PATH),
       "reference_sha256": ww.sha256_file(os.path.join(ww.BUILD, "reference", "approved-concept.png")),
       "script_sha256": scripts, "blender": bpy.app.version_string, "geometry": g, "images": images,
       "status": {"geometry": "PASS", "visual_appearance": "PASS_with_noted_deviations (see README)",
                  "motion_samples": "PASS (sampled lid 0-100 deg / rotor 0-270 deg; digital geometry only)",
                  "manufacture": "NOT_REQUESTED_NOT_VERIFIED"},
       "exclusions": ["no continuous collision proof", "no cable routing / retention / motor duty",
                      "walnut variant not rendered (owner: matte plastic only)", "dispersion omitted (no Principled input)",
                      "support polygon is geometric only, not centre-of-mass"]}
ww.write_json(os.path.join(ww.BUILD, "reports", "acceptance.json"), acc)
rt.emit_ok("pass-21-acceptance-isolated-check", **{k: v for k, v in g.items() if k not in ("cameras",)},
           images={k: v["size"] for k, v in images.items()}, blend_sha256=acc["blend_sha256"][:16])

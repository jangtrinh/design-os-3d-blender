"""Pass 16 — build all named node materials, assign by role (graphite variant), read back the
wired values, record the socket mappings/omissions. Colour management: AgX if available.
Postconditions: every render mesh has a WW material with a linked output; key values match the brief.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
mt = rt.load_lib(os.path.join(HERE, "ww_materials.py"))
sc = ww.activate()
mats = mt.build_all()
assigned, unmapped = mt.assign(mats, "graphite")
sc["ww_shell_variant"] = "graphite"

reports = {m.name: mt.verify(m) for m in mats.values()}
assert all(r["output_linked"] for r in reports.values()), [n for n, r in reports.items() if not r["output_linked"]]
assert not unmapped, f"unmapped render meshes: {unmapped}"
g, w, a, m, l = (reports[k] for k in ("WW_MAT_GRAPHITE", "WW_MAT_WALNUT", "WW_MAT_ACRYLIC", "WW_MAT_METAL_TURNED", "WW_MAT_LEATHER_CUSHION"))
assert g["Metallic"] == 0.0 and abs(g["Roughness"] - 0.58) < 1e-6 and g["normal_linked"]  # matte plastic (owner 2026-09-06)
assert g["Base Color"] == [round(c, 4) for c in mt.hex_rgba("#1A1D24")[:3]]
assert w["Metallic"] == 0.0 and abs(w["Coat Weight"] - 0.8) < 1e-6 and abs(w["Coat Roughness"] - 0.25) < 1e-6 and w["base_color_linked"]
assert a["Transmission Weight"] == 1.0 and abs(a["Roughness"] - 0.02) < 1e-6 and abs(a["IOR"] - 1.491) < 1e-6
assert m["Metallic"] == 1.0 and abs(m["Roughness"] - 0.15) < 1e-6 and abs(m["Anisotropic"] - 0.6) < 1e-6 and m["tangent_linked"]
assert abs(l["Roughness"] - 0.65) < 1e-6 and abs(l["Specular IOR Level"] - 0.4) < 1e-6 and l["normal_linked"]
assert reports["WW_MAT_LED_EMITTER"]["emission_strength"] == 6.0
assert not any(r["image_textures"] for r in reports.values())  # fully procedural: no colour-space risk
shell_mat = bpy.data.objects["WW_SHELL"].data.materials[0].name
assert shell_mat == "WW_MAT_GRAPHITE" and bpy.data.objects["WW_REAR_SERVICE_COVER"].data.materials[0].name == shell_mat

# colour management (introspect the enum instead of guessing)
vt_items = [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items_static]
try:
    sc.view_settings.view_transform = "AgX"
    look_ok = None
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "AgX - Medium Contrast"):
        try:
            sc.view_settings.look = look
            look_ok = look
            break
        except TypeError:
            continue
    cm = {"view_transform": sc.view_settings.view_transform, "look": sc.view_settings.look, "look_requested_ok": look_ok}
except TypeError:
    sc.view_settings.view_transform = "Filmic"
    cm = {"view_transform": "Filmic (AgX unavailable, substitute logged)", "look": sc.view_settings.look}
sc.view_settings.exposure = 0.0

ww.write_json(ww.state_path("reports", "materials.json"),
              {"materials": reports, "assigned": assigned, "colour_management": cm, "static_view_transforms": vt_items,
               "notes": {"acrylic_dispersion": mats["acrylic"].get("ww_dispersion"),
                         "leather_specular": mats["leather"].get("ww_specular_mapping"),
                         "led_temperature": mats["led"].get("ww_temperature"),
                         "perforation": mats["leather"].get("ww_perforation")}})
rt.emit_ok("pass-16-materials-assign-verify", materials=len(mats), assigned=len(assigned), unmapped=unmapped,
           shell_material=shell_mat, colour_management=cm, graphite=g, acrylic={k: a[k] for k in ("Transmission Weight", "Roughness", "IOR")},
           metal_turned={k: m[k] for k in ("Roughness", "Anisotropic", "tangent_linked")}, leather={k: l[k] for k in ("Roughness", "Specular IOR Level")})

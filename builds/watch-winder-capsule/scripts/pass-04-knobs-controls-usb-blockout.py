"""Pass 04 — two side bosses + knobs (axis +-localX), two rear pill controls, USB-C recess
placeholder. Controls/USB are placed on the world-upper-rear surface and oriented to the
local surface normal (matrix expressed under WW_BODY_FRAME).
Postconditions: exactly 2 knobs, mirror symmetry, 2 controls, 1 USB, all on the shell.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_product")
body = bpy.data.objects["WW_BODY_FRAME"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))
K = P["knobs"]
ly, lz = mm(K["local_y"]), mm(K["local_z"])

made = {}
for side, sgn in (("L", -1.0), ("R", 1.0)):
    p_in = Vector((sgn * mm(K["boss_inner_x"]), ly, lz))
    p_out = Vector((sgn * mm(K["boss_outer_x"]), ly, lz))
    p_tip = Vector((sgn * mm(K["boss_outer_x"] + K["body_depth"]), ly, lz))
    v, f = wm.tapered_tube(p_in, p_out, mm(K["boss_diameter"] / 2), mm(K["boss_diameter"] / 2), 48)
    made["boss" + side] = ww.mesh_obj(f"WW_KNOB_BOSS_{side}", v, f, col, parent=body, role="knob_boss", material=metal)
    v, f = wm.tapered_tube(p_out, p_tip, mm(K["body_diameter"] / 2), mm(K["body_diameter"] / 2), 64)
    made["knob" + side] = ww.mesh_obj(f"WW_KNOB_{side}", v, f, col, parent=body, role="knob", material=metal)

C = P["controls"]
ctrl = []
for i, az in enumerate(C["world_azimuth_deg"], start=1):
    m = ww.surface_matrix_local(body.matrix_world, ww.world_dir(C["world_polar_from_z_deg"], az), lift_mm=-0.6)
    v, f = wm.pill(mm(C["size"][0]), mm(C["size"][1]), mm(C["height"] + 0.6))
    ctrl.append(ww.mesh_obj(f"WW_CONTROL_{i:02d}", v, f, col, parent=body, matrix_local=m,
                            role="control", material=metal))

U = P["usb"]
m = ww.surface_matrix_local(body.matrix_world, ww.world_dir(U["world_polar_from_z_deg"], U["world_azimuth_deg"]), lift_mm=0.3)
v, f = wm.rounded_box(mm(U["recess"][0]), mm(U["recess"][1]), mm(U["recess_depth"]), mm(2.0),
                      corner_segs=4, z_center=-mm(U["recess_depth"] / 2))
usb_recess = ww.mesh_obj("WW_USB_RECESS", v, f, col, parent=body, matrix_local=m, role="usb_recess", material=dark)
v, f = wm.rounded_box(mm(U["envelope"][0]), mm(U["envelope"][1]), mm(U["recess_depth"] - 1.5), mm(U["envelope"][1] / 2),
                      corner_segs=4, z_center=-mm(U["recess_depth"] / 2 + 0.75))
usb_rec = ww.mesh_obj("WW_USB_RECEPTACLE", v, f, col, parent=body, matrix_local=m, role="usb_receptacle", material=metal)

# --- measurements ---
bpy.context.view_layer.update()
Cw = ww.vmm(P["shell"]["center_world"])
R = P["shell"]["outer_radius"]
bl, bh = ww.evaluated_bbox(made["knobL"])
rl, rh = ww.evaluated_bbox(made["knobR"])
sym = max(abs(bl.x + rh.x), abs(bh.x + rl.x), abs(bl.y - rl.y), abs(bh.y - rh.y), abs(bl.z - rl.z), abs(bh.z - rh.z)) * 1000
knobs = [o for o in ww.ww_objects() if o.get("ww_role") == "knob"]
controls = [o for o in ww.ww_objects() if o.get("ww_role") == "control"]
usbs = [o for o in ww.ww_objects() if o.get("ww_role") == "usb_receptacle"]
ctrl_rad = [round(((o.matrix_world.translation - Cw).length) * 1000, 3) for o in controls]
usb_rad = round((usb_rec.matrix_world.translation - Cw).length * 1000, 3)
ctrl_z = [round(o.matrix_world.translation.z * 1000, 2) for o in controls]
assert len(knobs) == 2 and len(controls) == 2 and len(usbs) == 1
assert sym < 0.01, f"knob asymmetry {sym} mm"
assert all(abs(r - (R - 0.6)) < 0.01 for r in ctrl_rad), ctrl_rad
assert abs(usb_rad - (R + 0.3)) < 0.01, usb_rad
assert all(z > Cw.z * 1000 for z in ctrl_z), "controls not on the upper shell"
assert usb_rec.matrix_world.translation.z < Cw.z, "usb not on the lower shell"
assert all(o.matrix_world.translation.y > Cw.y for o in controls + [usb_rec]), "rear parts not at the rear"

rt.emit_ok("pass-04-knobs-controls-usb-blockout",
           knob_count=len(knobs), knob_mirror_error_mm=round(sym, 4),
           knob_x_extent_mm=[round(bl.x * 1000, 2), round(rh.x * 1000, 2)],
           control_count=len(controls), control_radius_from_C_mm=ctrl_rad, control_world_z_mm=ctrl_z,
           usb_count=len(usbs), usb_radius_from_C_mm=usb_rad,
           usb_world_mm=[round(x * 1000, 2) for x in usb_rec.matrix_world.translation])

"""Pass 09 — hinge (fixed lugs on the rim, moving knuckle+bridge on the lid), finger tab at
6 o'clock, knobs with rounded caps + boss collars, control bezels with a seam, LED emitter.
Postconditions: knuckle axis == lid pivot X axis, lug/knuckle gap, tab at 6 o'clock, counts.
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
body, lid = bpy.data.objects["WW_BODY_FRAME"], bpy.data.objects["WW_LID_PIVOT"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
H, T, K = P["hinge"], P["finger_tab"], P["knobs"]
ro, w0 = P["shell"]["opening_radius"], P["shell"]["opening_datum_w0"]
piv = lid.matrix_local.translation  # (0, ro+setback, w0) in P
ROT_ZX = Matrix.Rotation(math.radians(90), 4, "Y")  # local Z -> +X


def box_at(name, sx, sy, sz, center_P, parent, radius=1.0, offset=Vector((0, 0, 0))):
    v, f = wm.rounded_box(mm(sx), mm(sy), mm(sz), mm(radius), 3)
    c = ww.vmm(center_P) - offset  # centre given in mm
    v = [(x + c.x, y + c.y, z + c.z) for x, y, z in v]
    return v, f


# Fixed lugs flank the knuckle; they sit on the rim/shell top (fitted contact, mounted part)
x_in = H["knuckle_radius"] * 0 + 7.8
lugs_v, lugs_f = [], []
for sgn in (-1, 1):
    v, f = box_at("", H["lug_thickness"], 9.0, 9.0, (sgn * (x_in + H["lug_thickness"] / 2), piv.y * 1000 - 1.0, piv.z * 1000 - 0.5), body)
    base = len(lugs_v)
    lugs_v += v
    lugs_f += [tuple(i + base for i in face) for face in f]
hinge_fixed = ww.mesh_obj("WW_HINGE_FIXED", lugs_v, lugs_f, col, parent=body, role="hinge_fixed", material=metal)

# Moving knuckle (axis = lid local X through the pivot) + bridge to the visor rim
v, f = wm.tapered_tube(Vector((-mm(x_in - 0.3), 0, 0)), Vector((mm(x_in - 0.3), 0, 0)), mm(H["knuckle_radius"]), mm(H["knuckle_radius"]), 32)
vb, fb = wm.rounded_box(mm(12.0), mm(H["hinge_setback"] if "hinge_setback" in H else 5.0), mm(3.0), mm(1.0), 3)
off = Vector((0, -mm(2.0), mm(0.6)))
vb = [(x + off.x, y + off.y, z + off.z) for x, y, z in vb]
base = len(v)
knuckle = ww.mesh_obj("WW_HINGE_MOVING", v + vb, f + [tuple(i + base for i in face) for face in fb], col,
                      parent=lid, role="hinge_moving", material=metal)

# Finger tab at 6 o'clock on the visor rim, in lid space
tab_center_P = Vector((0.0, -(ro + 1.5), w0 + P["visor"]["rim_clearance"] + T["height"] / 2))
v, f = wm.pill(mm(T["size"][0]), mm(T["size"][1]), mm(T["height"]))
v = [(x + tab_center_P.x * 0 , y + mm(tab_center_P.y) - piv.y, z + mm(tab_center_P.z - T["height"] / 2) - piv.z) for x, y, z in v]
v = [(x, y, z) for x, y, z in v]
tab = ww.mesh_obj("WW_FINGER_TAB", v, f, col, parent=lid, role="finger_tab", material=metal)

# Knobs: rounded cap lathe about X; boss with a collar
for side, sgn in (("L", -1.0), ("R", 1.0)):
    r, x0, x1, e = K["body_diameter"] / 2, K["boss_outer_x"], K["boss_outer_x"] + K["body_depth"], K["cap_edge_radius"]
    prof = [(0, x0), (r, x0), (r, x1 - e), (r - e, x1), (0, x1)]
    v, f = wm.lathe([(mm(a), mm(b) * sgn) for a, b in prof], 64, closed=True)
    v = wm.rotate_verts(v, ROT_ZX)
    v = [(x, y + mm(K["local_y"]), z + mm(K["local_z"])) for x, y, z in v]
    ww.mesh_obj(f"WW_KNOB_{side}", v, f, col, parent=body, role="knob", material=metal)
    rb = K["boss_diameter"] / 2
    prof = [(0, K["boss_inner_x"]), (rb, K["boss_inner_x"]), (rb, x0 - 1.5), (rb + 1.0, x0 - 1.5), (rb + 1.0, x0), (0, x0)]
    v, f = wm.lathe([(mm(a), mm(b) * sgn) for a, b in prof], 48, closed=True)
    v = wm.rotate_verts(v, ROT_ZX)
    v = [(x, y + mm(K["local_y"]), z + mm(K["local_z"])) for x, y, z in v]
    ww.mesh_obj(f"WW_KNOB_BOSS_{side}", v, f, col, parent=body, role="knob_boss", material=metal)

# Control bezels with a 0.3 mm seam (bezel minus button envelope)
Cc = P["controls"]
for i, az in enumerate(Cc["world_azimuth_deg"], start=1):
    m = ww.surface_matrix_local(body.matrix_world, ww.world_dir(Cc["world_polar_from_z_deg"], az), lift_mm=-0.9)
    v, f = wm.pill(mm(Cc["size"][0] + 2.5), mm(Cc["size"][1] + 2.5), mm(1.2))
    bez = ww.mesh_obj(f"WW_CONTROL_BEZEL_{i:02d}", v, f, col, parent=body, matrix_local=m, role="control_bezel", material=metal)
    v, f = wm.pill(mm(Cc["size"][0] + 0.6), mm(Cc["size"][1] + 0.6), mm(4.0))
    v = [(x, y, z - mm(1.0)) for x, y, z in v]
    cut = ww.mesh_obj(f"WW_CUT_BEZEL_{i:02d}", v, f, ww.coll("WW_helpers"), parent=body, matrix_local=m, role="cutter")
    cut.display_type, cut.hide_render = "WIRE", True
    mod = bez.modifiers.get("WW_bool_seam") or bez.modifiers.new("WW_bool_seam", "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cut

# LED emitter strip behind the diffuser, clear of the liner inner wall (r >= 50.5)
L = P["led"]
v, f = wm.annulus(mm(49.2), mm(50.4), mm(L["z0"] - 0.4), mm(L["z0"]), 96)
ww.mesh_obj("WW_LED_EMITTER", v, f, col, parent=body, role="led_emitter", material=ww.clay_material("WW_clay_led", (0.85, 0.93, 1.0, 1.0)))

# --- measurements ---
bpy.context.view_layer.update()
kn_axis = ww.world_axis(knuckle, (1, 0, 0))
lid_axis = ww.world_axis(lid, (1, 0, 0))
lug_pts = [body.matrix_world.inverted() @ p for p in ww.evaluated_verts_world(hinge_fixed)]
lug_inner_gap = (min(abs(p.x) for p in lug_pts) - (x_in - 0.3) / 1000) * 1000
tab_P = body.matrix_world.inverted() @ tab.matrix_world @ Vector((0, 0, 0))
tab_c = body.matrix_world.inverted() @ (tab.matrix_world @ (sum((vv.co for vv in tab.data.vertices), Vector()) / len(tab.data.vertices)))
roles = {}
for o in ww.ww_objects(product_only=False):
    roles[o.get("ww_role", "")] = roles.get(o.get("ww_role", ""), 0) + 1
assert math.degrees(kn_axis.angle(lid_axis)) < 0.01
assert lug_inner_gap > 0.2, f"lug/knuckle gap {lug_inner_gap}"
assert tab_c.y < -mm(ro - 2) and abs(tab_c.x) < 1e-6, f"tab not at 6 o'clock: {tab_c}"
assert roles["knob"] == 2 and roles["knob_boss"] == 2 and roles["control_bezel"] == 2

rt.emit_ok("pass-09-hinge-tab-knobs-controls-led", knuckle_axis_vs_lid_deg=round(math.degrees(kn_axis.angle(lid_axis)), 5),
           lug_knuckle_gap_mm=round(lug_inner_gap, 3), tab_center_P_mm=[round(c * 1000, 2) for c in tab_c],
           knob_faces=len(bpy.data.objects["WW_KNOB_L"].data.polygons), roles={k: v for k, v in roles.items() if k})

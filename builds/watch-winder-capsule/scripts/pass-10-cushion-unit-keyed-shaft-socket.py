"""Pass 10 — rigid cushion+watch unit under the rotor, keyed D-shaft, matching keyed socket
cut into the cushion (boolean), removal test (unit lifted out along the axis, then restored).
Postconditions: flat present on shaft, socket clearance, 10 mm engagement, clean extraction.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector, kdtree  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col, helpers = ww.coll("WW_product"), ww.coll("WW_helpers")
rotor, body = bpy.data.objects["WW_ROTOR_PIVOT"], bpy.data.objects["WW_BODY_FRAME"]
Cu, S, I = P["cushion"], P["shaft"], P["inner"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))

unit = ww.empty("WW_CUSHION_UNIT", helpers, parent=rotor, matrix_local=Matrix.Identity(4), size=0.015)
z_floor = I["cup_floor_localz"]
z_bottom = Cu["center_localz"] - Cu["depth"] / 2  # cushion underside
z_top_shaft = z_bottom + Cu["socket_depth"]

# Keyed D-shaft from the cup floor up into the socket
r = S["diameter"] / 2
flat_x = r - S["keyed_flat_depth"]
v, f = wm.prism([(mm(x), mm(y)) for x, y in wm.d_profile(mm(r) * 1000, flat_x, 32)], mm(z_floor), mm(z_top_shaft))
shaft = ww.mesh_obj("WW_SHAFT", v, f, col, parent=rotor, role="shaft", material=metal)

# Cushion (placeholder form for now) as part of the unit, with the keyed socket cut in
v, f = wm.rounded_box(mm(Cu["size_x"]), mm(Cu["size_y"]), mm(Cu["depth"]), mm(Cu["corner_radius"]), 6, z_center=mm(Cu["center_localz"]))
cushion = ww.mesh_obj("WW_CUSHION", v, f, col, parent=unit, role="cushion", material=dark)
clr = 0.2
v, f = wm.prism([(mm(x), mm(y)) for x, y in wm.d_profile(r + clr, flat_x + clr, 32)], mm(z_bottom - 1.0), mm(z_bottom + Cu["socket_depth"]))
cut = ww.mesh_obj("WW_CUT_SOCKET", v, f, helpers, parent=unit, role="cutter")
cut.display_type, cut.hide_render = "WIRE", True
mod = cushion.modifiers.get("WW_bool_socket") or cushion.modifiers.new("WW_bool_socket", "BOOLEAN")
mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cut

watch = bpy.data.objects["WW_WATCH"]
watch.parent = unit
watch.matrix_local = Matrix.Identity(4)

# --- measurements ---
bpy.context.view_layer.update()
inv = body.matrix_world.inverted()
sh = [inv @ p for p in ww.evaluated_verts_world(shaft)]
shaft_max_x = max(p.x for p in sh) * 1000
shaft_top = max(p.z for p in sh) * 1000
cu = [inv @ p for p in ww.evaluated_verts_world(cushion)]
socket_pts = [p for p in cu if math.hypot(p.x, p.y) < mm(r + clr + 0.05) and p.z > mm(z_bottom) + 1e-6]
socket_depth = (max(p.z for p in socket_pts) - mm(z_bottom)) * 1000 if socket_pts else 0.0
engagement = shaft_top - z_bottom

# Removal test: lift the unit 70 mm along the axis; nearest housing point must stay clear
obst = [p for n in ("WW_ROTOR_CUP", "WW_GUILLOCHE", "WW_INNER_LINER", "WW_LED_DIFFUSER", "WW_FRONT_RIM", "WW_SHAFT")
        for p in ww.evaluated_verts_world(bpy.data.objects[n])]
kd = kdtree.KDTree(len(obst))
for i, p in enumerate(obst):
    kd.insert(p, i)
kd.balance()
unit.matrix_local = Matrix.Translation(Vector((0, 0, mm(70.0))))
bpy.context.view_layer.update()
lifted = ww.evaluated_verts_world(cushion) + ww.evaluated_verts_world(watch)
clear_lifted = min(kd.find(p)[2] for p in lifted[::2]) * 1000
unit.matrix_local = Matrix.Identity(4)
bpy.context.view_layer.update()
seated = ww.evaluated_verts_world(cushion)
seated_gap = min(kd.find(p)[2] for p in seated[::2] if (inv @ p).z > mm(z_bottom + 0.5)) * 1000

assert abs(shaft_max_x - flat_x) < 0.01, f"flat missing: {shaft_max_x}"
assert abs(socket_depth - Cu["socket_depth"]) < 0.05, f"socket depth {socket_depth}"
assert abs(engagement - Cu["socket_depth"]) < 0.05, f"engagement {engagement}"
assert clear_lifted > 1.0, f"lifted unit within {clear_lifted} mm of housing"
assert max(abs(a - b) for ra, rb in zip(unit.matrix_local, Matrix.Identity(4)) for a, b in zip(ra, rb)) < 1e-6, 'pose not restored'

rt.emit_ok("pass-10-cushion-unit-keyed-shaft-socket", shaft_flat_x_mm=round(shaft_max_x, 3), shaft_round_r_mm=r,
           socket_depth_mm=round(socket_depth, 3), socket_clearance_mm=clr, engagement_mm=round(engagement, 3),
           lifted_unit_min_clearance_mm=round(clear_lifted, 3), seated_cushion_gap_to_housing_mm=round(seated_gap, 3),
           unit_children=[o.name for o in unit.children])

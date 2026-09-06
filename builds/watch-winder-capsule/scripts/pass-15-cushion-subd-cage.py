"""Pass 15 — cushion as a SubD cage: box cage -> Bevel (rounded shoulders) -> Subsurf ->
keyed socket boolean (re-attached). Seam and micro-perforation are shader work (pass-16).
Postconditions: evaluated envelope within the provisional 45x60x38 box, inside the cup bore,
socket still cut (engagement preserved), subdivision present.
"""
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
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_product")
unit = bpy.data.objects["WW_CUSHION_UNIT"]
Cu = P["cushion"]
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))

# cage: plain box (8 verts, 6 quads); rounding comes from the modifier stack so it stays editable
hx, hy, hz = mm(Cu["size_x"] / 2), mm(Cu["size_y"] / 2), mm(Cu["depth"] / 2)
zc = mm(Cu["center_localz"])
v = [(sx * hx, sy * hy, zc + sz * hz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
v, f = wm.orient_outward(v, f)
cushion = ww.mesh_obj("WW_CUSHION", v, f, col, parent=unit, role="cushion", material=dark)
bev = cushion.modifiers.new("WW_bevel", "BEVEL")
bev.width, bev.segments, bev.limit_method = mm(Cu.get("shoulder_radius", 9.0)), 6, "NONE"
bev.use_clamp_overlap = True
sub = cushion.modifiers.new("WW_subsurf", "SUBSURF")
sub.levels, sub.render_levels = 2, 3
mod = cushion.modifiers.new("WW_bool_socket", "BOOLEAN")
mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", bpy.data.objects["WW_CUT_SOCKET"]

# --- measurements on the evaluated cushion (unit-local == product frame at the seated pose) ---
bpy.context.view_layer.update()
inv = bpy.data.objects["WW_ROTOR_PIVOT"].matrix_world.inverted()
pts = [inv @ p for p in ww.evaluated_verts_world(cushion)]
ext = {"x": (min(p.x for p in pts), max(p.x for p in pts)), "y": (min(p.y for p in pts), max(p.y for p in pts)),
       "z": (min(p.z for p in pts), max(p.z for p in pts))}
max_r = max(math.hypot(p.x, p.y) for p in pts) * 1000
z_bottom = Cu["center_localz"] - Cu["depth"] / 2
r_sock = P["shaft"]["diameter"] / 2 + 0.2 + 0.05
socket_pts = [p for p in pts if math.hypot(p.x, p.y) < mm(r_sock) and mm(z_bottom) + 1e-6 < p.z < mm(z_bottom + Cu["socket_depth"] + 2.0)]
socket_depth = (max(p.z for p in socket_pts) - mm(z_bottom)) * 1000 if socket_pts else 0.0
top_flat = max(p.z for p in pts) * 1000
assert ext["x"][1] * 1000 <= Cu["size_x"] / 2 + 0.05 and ext["y"][1] * 1000 <= Cu["size_y"] / 2 + 0.05
assert max_r < P["inner"]["cup_mouth_radius"] - P["inner"]["cup_wall"] - 1.0, max_r
assert abs(socket_depth - Cu["socket_depth"]) < 0.3, socket_depth
assert abs(top_flat - (Cu["center_localz"] + Cu["depth"] / 2)) < 0.05, top_flat

rt.emit_ok("pass-15-cushion-subd-cage", eval_verts=len(pts), max_radius_mm=round(max_r, 3),
           extents_mm={k: [round(a * 1000, 2), round(b * 1000, 2)] for k, (a, b) in ext.items()},
           socket_depth_mm=round(socket_depth, 3), top_localz_mm=round(top_flat, 3),
           modifiers=[m.name for m in cushion.modifiers], subsurf_levels=[sub.levels, sub.render_levels])

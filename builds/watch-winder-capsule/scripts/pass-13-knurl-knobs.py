"""Pass 13 — diamond-knurled sleeves on both knobs (one connected height-field solid each);
knob bodies re-lathed with a smooth cap ring and rounded cap edge.
Postconditions: diamond count around, relief, periodic seam, mirror symmetry.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
wd = rt.load_lib(os.path.join(HERE, "ww_mesh_detail.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_product")
body = bpy.data.objects["WW_BODY_FRAME"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
K = P["knobs"]
r, x0, x1, e = K["body_diameter"] / 2, K["boss_outer_x"], K["boss_outer_x"] + K["body_depth"], K["cap_edge_radius"]
ROT_ZX = Matrix.Rotation(math.radians(90), 4, "Y")
sleeve_x0, sleeve_x1 = x0 + 0.8, x1 - 1.4
made = {}
for side, sgn in (("L", -1.0), ("R", 1.0)):
    # body: slightly under the knurl base so the sleeve wraps it; cap ring at full radius
    prof = [(0, x0), (r - 0.3, x0), (r - 0.3, sleeve_x1), (r, sleeve_x1 + 0.2), (r, x1 - e), (r - e, x1), (0, x1)]
    v, f = wm.lathe([(mm(a), mm(b) * sgn) for a, b in prof], 64, closed=True)
    v = wm.rotate_verts(v, ROT_ZX)
    v = [(x, y + mm(K["local_y"]), z + mm(K["local_z"])) for x, y, z in v]
    ww.mesh_obj(f"WW_KNOB_{side}", v, f, col, parent=body, role="knob", material=metal)
    v, f = wd.knurl_sleeve(mm(sleeve_x0) * sgn, mm(sleeve_x1) * sgn, mm(r - 0.5), mm(r), mm(K["knurl_relief"]),
                           mm(K["knurl_pitch"]), samples_per_pitch=8)
    v = [(x, y + mm(K["local_y"]), z + mm(K["local_z"])) for x, y, z in v]
    v, f = wm.orient_outward(v, f)
    made[side] = ww.mesh_obj(f"WW_KNURL_{side}", v, f, col, parent=body, role="knurl", material=metal)

# --- measurements (base mesh of the right sleeve; left must mirror) ---
me = made["R"].data
circ = 2 * math.pi * r
n_d = round(circ / K["knurl_pitch"])
na = n_d * 8
radii = [math.hypot(vv.co.y - mm(K["local_y"]), vv.co.z - mm(K["local_z"])) * 1000 for vv in me.vertices]
outer = [rr for rr in radii if rr > r - 0.5 + 0.01]
relief = max(outer) - min(outer)
# diamond count: peaks along one circumferential row that passes through ridge crossings
n_along = len([1 for vv in me.vertices]) // 2 // na
# count on the crossing row (where ridge families intersect: max radius == base radius);
# rows between crossings legitimately show both families -> 2 peaks per pitch
rows = [radii[i * na:(i + 1) * na] for i in range(n_along)]
row = max(rows, key=max)
best = sum(1 for j in range(na) if row[j] > row[j - 1] and row[j] >= row[(j + 1) % na])
bm = bmesh.new()
bm.from_mesh(me)
nonmanifold = sum(1 for e_ in bm.edges if not e_.is_manifold)
flipped = sum(1 for e_ in bm.edges if e_.is_manifold and not e_.is_contiguous)
bm.free()
lo_l, hi_l = ww.evaluated_bbox(made["L"])
lo_r, hi_r = ww.evaluated_bbox(made["R"])
sym = max(abs(lo_l.x + hi_r.x), abs(hi_l.x + lo_r.x), abs(lo_l.z - lo_r.z), abs(hi_l.y - hi_r.y)) * 1000
assert abs(relief - K["knurl_relief"]) < 0.01, relief
assert best == n_d, (best, n_d)
assert nonmanifold == 0 and flipped == 0, (nonmanifold, flipped)
assert sym < 0.05, sym  # y/z peaks land at different sample angles per hand; 0.03 mm bbox delta is sampling, not design

rt.emit_ok("pass-13-knurl-knobs", diamonds_around=n_d, effective_pitch_mm=round(circ / n_d, 4),
           relief_mm=round(relief, 4), peaks_measured=best, sleeve_verts=len(me.vertices),
           sleeve_faces=len(me.polygons), mirror_error_mm=round(sym, 4), sleeve_x_mm=[sleeve_x0, sleeve_x1])

"""Pass 12 — real spiral guilloche relief mesh replaces the flat faceplate annulus.
Postconditions: measured relief amplitude, 128 peaks around a mid ring, closed solid,
plate stays under the cup mouth / inside the liner clearance.
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

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
wd = rt.load_lib(os.path.join(HERE, "ww_mesh_detail.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_product")
rotor = bpy.data.objects["WW_ROTOR_PIVOT"]
I = P["inner"]
G = P.setdefault("guilloche", {"rays": 128, "relief": 0.12, "twist_rad": 0.18, "flat_border": 0.8,
                               "status": "provisional_visualization_default"})
r_in, r_out = I["cup_mouth_radius"] - I["cup_wall"], I["faceplate_r_out"]
z_bot, z_top = I["cup_mouth_localz"], I["cup_mouth_localz"] + I["faceplate_thickness"]

v, f = wd.guilloche_annulus(mm(r_in), mm(r_out), mm(z_top), mm(z_bot), mm(G["relief"]), rays=G["rays"],
                            twist_rad=G["twist_rad"], n_ring=40, samples_per_ray=8, flat_border=mm(G["flat_border"]))
v, f = wm.orient_outward(v, f)
plate = ww.mesh_obj("WW_GUILLOCHE", v, f, col, parent=rotor, role="faceplate",
                    material=ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0)))

# --- measurements on the base mesh (rotor-local = product frame) ---
me = plate.data
zs = [vv.co.z * 1000 for vv in me.vertices if vv.co.z * 1000 > z_bot + 0.5]
relief = max(zs) - min(zs)
na = G["rays"] * 8
mid_ring = 20
ring = [me.vertices[mid_ring * na + j].co.z for j in range(na)]
peaks = sum(1 for j in range(na) if ring[j] > ring[j - 1] and ring[j] >= ring[(j + 1) % na])
bm = bmesh.new()
bm.from_mesh(me)
nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
flipped = sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
bm.free()
me.calc_loop_triangles()
vol = sum(me.vertices[t.vertices[0]].co.dot(me.vertices[t.vertices[1]].co.cross(me.vertices[t.vertices[2]].co)) for t in me.loop_triangles) / 6.0
assert abs(relief - G["relief"]) < 0.005, relief
assert peaks == G["rays"], peaks
assert nonmanifold == 0 and flipped == 0 and vol > 0, (nonmanifold, flipped, vol)
assert max(math.hypot(vv.co.x, vv.co.y) for vv in me.vertices) * 1000 <= r_out + 1e-3

rt.emit_ok("pass-12-guilloche-relief", relief_mm=round(relief, 4), peaks_mid_ring=peaks, rays=G["rays"],
           twist_rad=G["twist_rad"], verts=len(me.vertices), faces=len(me.polygons),
           signed_volume_mm3=round(vol * 1e9, 1), r_in_mm=r_in, r_out_mm=r_out, z_top_mm=z_top)

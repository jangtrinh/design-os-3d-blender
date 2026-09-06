"""Pass 14 — unbranded dress watch on the cushion: case, caseback, dial, 12 markers, bezel,
domed crystal, separate hour/minute/second hands (10:10), crown, lugs, leather strap wrapped
around the cushion. WW_WATCH becomes an empty group under WW_CUSHION_UNIT.
Postconditions: hand angles, strap inside the cup bore, strap-to-cushion contact gap, counts.
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
wd = rt.load_lib(os.path.join(HERE, "ww_mesh_detail.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col, helpers = ww.coll("WW_product"), ww.coll("WW_helpers")
unit = bpy.data.objects["WW_CUSHION_UNIT"]
Cu, W = P["cushion"], P["watch"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))
glass = ww.clay_material("WW_clay_glass", (0.7, 0.85, 1.0, 1.0))
z_top = Cu["center_localz"] + Cu["depth"] / 2

old = bpy.data.objects.get("WW_WATCH")
if old is not None and old.type == "MESH":
    bpy.data.objects.remove(old, do_unlink=True)
watch = ww.empty("WW_WATCH", helpers, parent=unit, matrix_local=Matrix.Translation(Vector((0, 0, mm(z_top)))), size=0.01)
R = W["case_diameter"] / 2  # 20


def part(name, v, f, mat, role="watch_part"):
    v, f = wm.orient_outward(v, f)
    return ww.mesh_obj(name, v, f, col, parent=watch, role=role, material=mat)


def merge(parts):
    v_all, f_all = [], []
    for v, f in parts:
        base = len(v_all)
        v_all += v
        f_all += [tuple(i + base for i in face) for face in f]
    return v_all, f_all


def rz(deg):
    return Matrix.Rotation(math.radians(-deg), 4, "Z")  # clockwise from 12 o'clock (+Y)


L = lambda pts: [(mm(a), mm(b)) for a, b in pts]  # noqa: E731
case = part("WW_WATCH_CASE", *wm.lathe(L([(R - 2.4, 1.0), (R - 0.6, 1.0), (R, 1.6), (R, 7.6), (R - 0.6, 8.2), (R - 2.4, 8.2)]), 96), metal, role="watch")
part("WW_WATCH_CASEBACK", *wm.cylinder(mm(R - 2.3), mm(0.0), mm(1.2), 64), metal)
part("WW_WATCH_DIAL", *wm.cylinder(mm(R - 2.5), mm(5.4), mm(5.8), 96), ww.clay_material("WW_clay_dial", (0.75, 0.75, 0.75, 1.0)))
part("WW_WATCH_BEZEL", *wm.lathe(L([(R - 2.8, 8.2), (R, 8.2), (R, 9.0), (R - 0.8, 9.6), (R - 2.8, 9.6)]), 96), metal)
sag, rc = 1.6, R - 2.8
Rs = (rc * rc + sag * sag) / (2 * sag)
v, f = wm.spherical_cap(mm(Rs), mm(Rs - 1.0), math.asin(rc / Rs), 96, 8)
v = [(x, y, z - mm(Rs - (9.4 + sag))) for x, y, z in v]
part("WW_WATCH_CRYSTAL", v, f, glass)
markers = []
for h in range(12):
    v, f = wm.rounded_box(mm(0.9), mm(2.4), mm(0.35), mm(0.3), 2, z_center=mm(5.975))
    m = rz(h * 30) @ Matrix.Translation(Vector((0, mm(R - 5.4), 0)))
    markers.append(([tuple(m @ Vector(p)) for p in v], f))
part("WW_WATCH_MARKERS", *merge(markers), metal)
hands = {"HOUR": (305.0, 9.5, 1.4, 6.2, 6.5), "MINUTE": (60.0, 13.5, 1.0, 6.55, 6.85), "SECOND": (210.0, 15.0, 0.35, 6.9, 7.1)}
for name, (ang, length, width, z0, z1) in hands.items():
    v, f = wm.rounded_box(mm(width), mm(length + 1.0), mm(z1 - z0), mm(width / 2 * 0.6), 2, z_center=mm((z0 + z1) / 2))
    m = rz(ang) @ Matrix.Translation(Vector((0, mm(length / 2 - 0.5), 0)))
    part(f"WW_WATCH_HAND_{name}", [tuple(m @ Vector(p)) for p in v], f, metal)
part("WW_WATCH_HAND_CAP", *wm.cylinder(mm(1.2), mm(6.2), mm(7.3), 32), metal)
v, f = wm.lathe(L([(0, R - 1.0), (1.2, R - 1.0), (1.2, R + 0.4), (1.9, R + 0.4), (1.9, R + 2.6), (0, R + 2.6)]), 48)
part("WW_WATCH_CROWN", [tuple(Matrix.Rotation(math.radians(90), 4, "Y") @ Vector(p) + Vector((0, 0, mm(4.6)))) for p in v], f, metal)
lugs = []
for sx in (-1, 1):
    for sy in (-1, 1):
        v, f = wm.rounded_box(mm(2.2), mm(4.5), mm(3.5), mm(0.8), 2, z_center=mm(4.35))
        lugs.append(([(x + sx * mm(9.2), y + sy * mm(22.5), z) for x, y, z in v], f))
part("WW_WATCH_LUGS", *merge(lugs), metal)
half = Cu["size_y"] / 2  # 30
path = [(21.5, 1.35), (28.4, 1.35), (half + 1.35, -1.6), (half + 1.35, -Cu["depth"] + 1.5)]
straps = []
for sgn, name in ((1, "12"), (-1, "6")):
    v, f = wd.ribbon([(mm(y * sgn), mm(z)) for y, z in path], mm(18.0), mm(2.5))
    straps.append(part(f"WW_WATCH_STRAP_{name}", v, f, dark))

# --- measurements ---
bpy.context.view_layer.update()
inv_rotor = bpy.data.objects["WW_ROTOR_PIVOT"].matrix_world.inverted()
strap_pts = [inv_rotor @ p for s in straps for p in ww.evaluated_verts_world(s)]
strap_r = max(math.hypot(p.x, p.y) for p in strap_pts) * 1000
cushion = bpy.data.objects["WW_CUSHION"]
from mathutils.bvhtree import BVHTree  # noqa: E402
bvh = BVHTree.FromObject(cushion, bpy.context.evaluated_depsgraph_get())  # true surface distance, not vertex distance
side_pts = [p for s in straps for p in ww.evaluated_verts_world(s) if abs((inv_rotor @ p).y) > mm(half) and (inv_rotor @ p).z < mm(z_top - 5)]
gap = min(bvh.find_nearest(cushion.matrix_world.inverted() @ p)[3] for p in side_pts) * 1000
angles = {}
inv_w = watch.matrix_world.inverted()
for name, (ang, *_rest) in hands.items():
    ob = bpy.data.objects[f"WW_WATCH_HAND_{name}"]
    tip = max((inv_w @ p for p in ww.evaluated_verts_world(ob)), key=lambda q: q.xy.length)
    angles[name] = round(math.degrees(math.atan2(tip.x, tip.y)) % 360, 2)
    assert abs(((angles[name] - ang + 180) % 360) - 180) < 3.0, (name, angles[name], ang)
n_parts = len([o for o in watch.children])
assert strap_r < P["inner"]["cup_mouth_radius"] - P["inner"]["cup_wall"] - 0.5, strap_r
assert 0.0 < gap < 1.0, f"strap not in contact with the cushion end faces: {gap} mm"
assert n_parts == 14, n_parts

rt.emit_ok("pass-14-watch-dress-unbranded", parts=n_parts, hand_angles_deg=angles, strap_max_radius_mm=round(strap_r, 3),
           cup_bore_mm=P["inner"]["cup_mouth_radius"] - P["inner"]["cup_wall"], strap_cushion_gap_mm=round(gap, 3),
           crystal_apex_localz_mm=round(z_top + 9.4 + sag, 2), case_diameter_mm=W["case_diameter"])

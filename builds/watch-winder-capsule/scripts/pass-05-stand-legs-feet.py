"""Pass 05 — three tapered legs + rubber feet in WORLD coordinates under WW_STAND.
Postconditions: exactly 3 feet with bottoms at Z=0 (+-0.1 mm), legs attach inside the
shell wall, no leg-leg intersection (axis distance), support polygon contains C's projection.
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
col = ww.coll("WW_stand")
stand = bpy.data.objects["WW_STAND"]
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
rubber = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))
S = P["stand"]
C = ww.vmm(P["shell"]["center_world"])

legs, feet, attach_pts = [], [], []
for i, foot in enumerate(S["feet_contact_world"], start=1):
    fpt = ww.vmm(foot)
    d = (fpt - C).normalized()
    attach = C + d * mm(S["attach_radius"])
    attach_pts.append(attach)
    top_of_foot = Vector((fpt.x, fpt.y, mm(S["foot_height"])))
    # leg mesh in its OWN local frame (local Z = leg axis) so a radial tangent gives the brushed grain
    axis_v = top_of_foot - attach
    rot = axis_v.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    m_leg = Matrix.Translation(attach) @ rot
    v, f = wm.lathe([(0.0, 0.0), (mm(S["leg_radius_at_shell"]), 0.0), (mm(S["leg_radius_at_foot"]), axis_v.length), (0.0, axis_v.length)], 32)
    legs.append(ww.mesh_obj(f"WW_LEG_{i:02d}", v, f, col, parent=stand, matrix_local=m_leg, role="leg", material=metal))
    v, f = wm.lathe([(0.0, 0.0), (mm(S["foot_radius"]), 0.0), (mm(S["foot_radius"] - 0.5), mm(S["foot_height"])), (0.0, mm(S["foot_height"]))], 32)
    feet.append(ww.mesh_obj(f"WW_FOOT_{i:02d}", v, f, col, parent=stand, matrix_local=Matrix.Translation(Vector((fpt.x, fpt.y, 0.0))), role="foot", material=rubber))

bpy.context.view_layer.update()
foot_z = [ww.evaluated_bbox(o)[0].z * 1000 for o in feet]
assert len(feet) == 3 and len(legs) == 3
assert all(abs(z) < 0.1 for z in foot_z), foot_z

# leg-leg separation: closest distance between leg axis segments must exceed radii sum
def seg_dist(p1, q1, p2, q2):
    best = 1e9
    for a in range(0, 21):
        for b in range(0, 21):
            best = min(best, ((p1 + (q1 - p1) * a / 20) - (p2 + (q2 - p2) * b / 20)).length)
    return best

segs = [(attach_pts[i], ww.vmm(S["feet_contact_world"][i])) for i in range(3)]
min_sep = min(seg_dist(*segs[i], *segs[j]) for i in range(3) for j in range(i + 1, 3)) * 1000
assert min_sep > 2 * S["leg_radius_at_shell"], f"legs too close: {min_sep} mm"

# support polygon (feet contact triangle) contains the projection of C — geometric screen only
def sign(a, b, c):
    return (a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1])
tri = [(f[0], f[1]) for f in S["feet_contact_world"]]
pc = (P["shell"]["center_world"][0], P["shell"]["center_world"][1])
s1, s2, s3 = sign(pc, tri[0], tri[1]), sign(pc, tri[1], tri[2]), sign(pc, tri[2], tri[0])
inside = not ((s1 < 0 or s2 < 0 or s3 < 0) and (s1 > 0 or s2 > 0 or s3 > 0))
assert inside, "shell centre projection outside support triangle"
attach_r = [round((a - C).length * 1000, 3) for a in attach_pts]

rt.emit_ok("pass-05-stand-legs-feet", leg_count=len(legs), foot_count=len(feet),
           foot_bottom_z_mm=[round(z, 4) for z in foot_z], min_leg_axis_separation_mm=round(min_sep, 2),
           attach_radius_mm=attach_r, support_polygon_contains_C=inside,
           note="support polygon is a geometric screen, not a centre-of-mass or tipping proof")

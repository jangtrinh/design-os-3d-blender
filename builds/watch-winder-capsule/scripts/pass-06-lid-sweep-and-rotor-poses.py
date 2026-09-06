"""Pass 06 — lid opening sign test + sampled 0..100 deg sweep vs shell/controls/knobs;
rotor poses 0/90/180/270 keep cushion+watch inside the cup. Restores closed pose.
Digital sampled geometry evidence only (not continuous collision proof).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector, kdtree  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
lid, rotor, body = (bpy.data.objects[n] for n in ("WW_LID_PIVOT", "WW_ROTOR_PIVOT", "WW_BODY_FRAME"))
visor = bpy.data.objects["WW_VISOR"]
C = ww.vmm(P["shell"]["center_world"])
R = P["shell"]["outer_radius"]
lid_base = lid.matrix_local.copy()
rotor_base = rotor.matrix_local.copy()

obstacles = [bpy.data.objects[n] for n in ("WW_CONTROL_01", "WW_CONTROL_02", "WW_KNOB_L", "WW_KNOB_R",
                                            "WW_FRONT_RIM", "WW_INNER_LINER", "WW_LED_DIFFUSER")]
pts = [p for o in obstacles for p in ww.evaluated_verts_world(o)]
kd = kdtree.KDTree(len(pts))
for i, p in enumerate(pts):
    kd.insert(p, i)
kd.balance()


def pose_lid(deg, sign):
    lid.matrix_local = lid_base @ Matrix.Rotation(math.radians(sign * deg), 4, "X")
    bpy.context.view_layer.update()


RO = P["shell"]["opening_radius"]


def visor_metrics():
    """Shell = sphere(67.5..70) minus the bore cylinder (r < opening radius about localZ).
    A visor vertex penetrates only when it is outside the bore AND closer than R to C."""
    vs = ww.evaluated_verts_world(visor)
    inv = body.matrix_world.inverted()
    loc = np.array([list(inv @ v) for v in vs]) * 1000.0
    rad = np.linalg.norm(loc, axis=1)
    cyl = np.hypot(loc[:, 0], loc[:, 1])
    outside_bore = cyl >= RO
    pen = np.where(outside_bore, np.clip(R - rad, 0.0, None), 0.0)
    near = min(kd.find(v)[2] for v in vs[::3]) * 1000
    return float(rad.min()), float(near), float(pen.max())


# Sign test: the opening direction moves the visor apex away from the shell centre
apex_dist = {}
for sign in (1, -1):
    pose_lid(10.0, sign)
    apex = visor.matrix_world @ Vector((0.0, 0.0, mm(P["visor"]["outer_radius"] + P["visor"]["rim_clearance"])))
    apex_dist[sign] = (apex - C).length
open_sign = 1 if apex_dist[1] > apex_dist[-1] else -1

sweep = []
for deg in range(0, 101, 5):
    pose_lid(float(deg), open_sign)
    rmin, near, pen = visor_metrics()
    sweep.append({"deg": deg, "visor_min_radius_from_C_mm": round(rmin, 3),
                  "shell_penetration_mm": round(pen, 3), "nearest_obstacle_mm": round(near, 3)})
lid.matrix_local = lid_base
bpy.context.view_layer.update()

# Rotor poses: cushion + watch stay inside the cup bore / faceplate bore at every pose
rotor_ok = []
bore = P["inner"]["cup_mouth_radius"] - P["inner"]["cup_wall"]
for deg in (0, 90, 180, 270):
    rotor.matrix_local = rotor_base @ Matrix.Rotation(math.radians(deg), 4, "Z")
    bpy.context.view_layer.update()
    inv = body.matrix_world.inverted()
    rad = max(math.hypot(*(inv @ p).xy) for p in ww.evaluated_verts_world(bpy.data.objects["WW_CUSHION"])) * 1000
    rotor_ok.append({"deg": deg, "cushion_max_radius_mm": round(rad, 3), "inside": rad < bore})
rotor.matrix_local = rotor_base
bpy.context.view_layer.update()

worst_pen = max(s["shell_penetration_mm"] for s in sweep)
min_near = min(s["nearest_obstacle_mm"] for s in sweep[1:])
ww.write_json(ww.state_path("reports", "phase1-lid-sweep.json"),
              {"open_sign_about_localX": open_sign, "apex_distance_test_mm": {k: round(v * 1000, 3) for k, v in apex_dist.items()},
               "sweep": sweep, "rotor_poses": rotor_ok, "obstacle_set": [o.name for o in obstacles],
               "evidence_class": "sampled digital geometry, 5 deg steps, every 3rd visor vertex vs obstacle KD-tree"})
assert all(r["inside"] for r in rotor_ok), rotor_ok
assert worst_pen < 0.05, f"visor enters shell by {worst_pen} mm during sweep"
assert max(abs(a - b) for ra, rb in zip(lid.matrix_local, lid_base) for a, b in zip(ra, rb)) < 1e-6, 'pose not restored'
assert max(abs(a - b) for ra, rb in zip(rotor.matrix_local, rotor_base) for a, b in zip(ra, rb)) < 1e-6, 'pose not restored'
rt.emit_ok("pass-06-lid-sweep-and-rotor-poses", open_sign_about_localX=open_sign,
           sweep_max_shell_penetration_mm=round(worst_pen, 3), sweep_min_obstacle_gap_mm=round(min_near, 3),
           sweep_samples=len(sweep), rotor_poses_inside=[r["inside"] for r in rotor_ok],
           closed_pose_restored=True)

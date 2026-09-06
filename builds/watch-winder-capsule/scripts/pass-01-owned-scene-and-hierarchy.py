"""Pass 01 — owned scene WW_capsule + empty hierarchy (no meshes yet).

Postconditions: scene exists with metre units, body frame localZ at 50 deg
elevation, pivots placed, other scenes untouched (signature stored).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
from mathutils import Matrix, Vector  # noqa: E402

sc = ww.activate()  # adopts a factory-fresh default scene first
sig_before = ww.other_scene_signature()
P = ww.P

col_product = ww.coll("WW_product")
col_stand = ww.coll("WW_stand")
col_studio = ww.coll("WW_studio")
col_helpers = ww.coll("WW_helpers")

root = ww.empty("WW_ROOT", col_helpers, size=0.05)
body = ww.empty("WW_BODY_FRAME", col_helpers, parent=root, matrix_local=ww.frame_P(), size=0.04)
w0 = ww.mm(P["shell"]["opening_datum_w0"])
lid_y = ww.mm(P["shell"]["opening_radius"] + P["visor"]["hinge_setback"])
lid = ww.empty("WW_LID_PIVOT", col_helpers, parent=body,
               matrix_local=Matrix.Translation(Vector((0.0, lid_y, w0))), size=0.02)
rotor = ww.empty("WW_ROTOR_PIVOT", col_helpers, parent=body, matrix_local=Matrix.Identity(4), size=0.02)
stand = ww.empty("WW_STAND", col_helpers, parent=root, matrix_local=Matrix.Identity(4), size=0.03)
studio = ww.empty("WW_STUDIO", col_helpers, parent=None, matrix_local=Matrix.Identity(4), size=0.03)

st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
cam = st.concept_view(col_studio, c_world_center := ww.vmm(P["shell"]["center_world"]) - Vector((0, 0, 0.02)),
                      ww.mm(P["shell"]["outer_radius"]) + 0.03)
cam.parent = studio
sc.camera = cam
st.viewport_to_camera(cam)

axis = ww.world_axis(body)
elev = ww.elevation_deg(axis)
rot_axis = ww.world_axis(rotor)
lid_world = lid.matrix_world.translation
c_world = ww.vmm(P["shell"]["center_world"])

assert abs(elev - P["axis"]["rotor_axis_elevation_deg"]) < 0.1, f"axis elevation {elev}"
assert (rot_axis - axis).length < 1e-6, "rotor pivot axis differs from body axis"
assert abs(sc.unit_settings.scale_length - 1.0) < 1e-9
assert ww.other_scene_signature() == sig_before, "unrelated scene changed"

ww.write_json(ww.state_path("reports", "ownership-signature.json"),
              {"other_scene_signature": sig_before, "owned_scene": ww.SCENE_NAME})

rt.emit_ok("pass-01-owned-scene-and-hierarchy",
           scene=sc.name, scale_length=sc.unit_settings.scale_length,
           body_axis_world=[round(x, 6) for x in axis], axis_elevation_deg=round(elev, 4),
           lid_pivot_world_mm=[round(x * 1000, 3) for x in lid_world],
           lid_pivot_dist_from_C_mm=round((lid_world - c_world).length * 1000, 3),
           other_scene_signature=sig_before[:16], ww_objects=ww.ww_object_names())

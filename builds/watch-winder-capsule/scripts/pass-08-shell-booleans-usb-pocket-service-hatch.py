"""Pass 08 — real recessed USB pocket (housing behind the wall + shared cutter) and an
underside service hatch (hole in the shell + separate spherical-cap cover with a seam).
Booleans stay as modifiers (EXACT); cutters are render-hidden wire helpers.
Postconditions: no evaluated shell vertex remains inside either opening; evaluated
shell stays manifold; cover thickness and seam measured.
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
from mathutils import Matrix, Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()
col, helpers = ww.coll("WW_product"), ww.coll("WW_helpers")
body, shell = bpy.data.objects["WW_BODY_FRAME"], bpy.data.objects["WW_SHELL"]
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))
clay = ww.clay_material()
U, SC = P["usb"], P["service_cover"]
R, wall = P["shell"]["outer_radius"], P["shell"]["wall"]


def cutter(name, verts, faces, matrix_local):
    ob = ww.mesh_obj(name, verts, faces, helpers, parent=body, matrix_local=matrix_local, role="cutter")
    ob.display_type = "WIRE"
    ob.hide_render = True
    return ob


def boolean(target, cut, name):
    mod = target.modifiers.get(name) or target.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cut
    return mod


# USB: housing sunk 1 mm under the surface, pocket + shell hole from one cutter
m_usb = ww.surface_matrix_local(body.matrix_world, ww.world_dir(U["world_polar_from_z_deg"], U["world_azimuth_deg"]), lift_mm=-1.0)
rw, rh, rd = U["recess"][0], U["recess"][1], U["recess_depth"]
v, f = wm.rounded_box(mm(rw + 2.0), mm(rh + 2.0), mm(rd + 1.0), mm(3.0), 4, z_center=-mm((rd + 1.0) / 2))
housing = ww.mesh_obj("WW_USB_RECESS", v, f, col, parent=body, matrix_local=m_usb, role="usb_recess", material=dark)
v, f = wm.rounded_box(mm(rw), mm(rh), mm(rd + 3.0), mm(2.0), 4, z_center=mm((3.0 - rd) / 2))  # z -rd .. +3 (through the wall)
cut_usb = cutter("WW_CUT_USB_POCKET", v, f, m_usb)
boolean(shell, cut_usb, "WW_bool_usb")
boolean(housing, cut_usb, "WW_bool_pocket")
# receptacle envelope sits on the pocket floor (re-placed relative to the housing frame)
v, f = wm.rounded_box(mm(U["envelope"][0]), mm(U["envelope"][1]), mm(rd - 2.0), mm(U["envelope"][1] / 2), 4,
                      z_center=-mm(rd - (rd - 2.0) / 2))
ww.mesh_obj("WW_USB_RECEPTACLE", v, f, col, parent=body, matrix_local=m_usb, role="usb_receptacle",
            material=ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0)))

# Service hatch: hole through the shell + separate cap cover with a seam gap
d_hatch = ww.world_dir(SC["world_polar_from_z_deg"], SC["world_azimuth_deg"])
m_hatch = ww.surface_matrix_local(body.matrix_world, d_hatch, lift_mm=0.0)
v, f = wm.cylinder(mm(SC["cap_radius"]), -mm(wall + 4.0), mm(4.0), 96)
cut_hatch = cutter("WW_CUT_SERVICE_HATCH", v, f, m_hatch)
boolean(shell, cut_hatch, "WW_bool_hatch")
ang = math.asin((SC["cap_radius"] - SC["seam_gap"]) / R)
v, f = wm.spherical_cap(mm(R - 0.05), mm(R - SC["thickness"] - 0.05), ang, 96, 10)
m_cap = body.matrix_world.inverted() @ (Matrix.Translation(ww.vmm(P["shell"]["center_world"])) @ d_hatch.to_track_quat("Z", "Y").to_matrix().to_4x4())
cover = ww.mesh_obj("WW_REAR_SERVICE_COVER", v, f, col, parent=body, matrix_local=m_cap, role="service_cover", material=clay)

# --- measurements on the EVALUATED shell ---
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = shell.evaluated_get(deps)
me = ev.to_mesh()
bm = bmesh.new()
bm.from_mesh(me)
nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
tris = len(me.polygons)
verts_w = [ev.matrix_world @ v.co for v in me.vertices]
bm.free()
ev.to_mesh_clear()
inv_usb = (body.matrix_world @ m_usb).inverted()
inv_hatch = (body.matrix_world @ m_hatch).inverted()
def in_rounded_rect(p, hx, hy, rr, inset):
    dx, dy = max(abs(p.x) - (hx - rr), 0.0), max(abs(p.y) - (hy - rr), 0.0)
    return math.hypot(dx, dy) < rr - inset


inside_usb = [p for p in (inv_usb @ w for w in verts_w)
              if in_rounded_rect(p, mm(rw / 2), mm(rh / 2), mm(2.0), mm(0.05)) and p.z > -mm(rd)]
inside_hatch = [p for p in (inv_hatch @ w for w in verts_w) if math.hypot(p.x, p.y) < mm(SC["cap_radius"] - 0.05) and p.z > -mm(wall + 3.0)]
cover_r = [(ww.vmm(P["shell"]["center_world"]) - p).length * 1000 for p in ww.evaluated_verts_world(cover)]
cover_ang = max(math.asin(min(1.0, (p - ww.vmm(P["shell"]["center_world"])).normalized().cross(d_hatch).length)) for p in ww.evaluated_verts_world(cover))
seam = (SC["cap_radius"] - R * math.sin(cover_ang))
assert nonmanifold == 0, f"evaluated shell non-manifold edges: {nonmanifold}"
assert not inside_usb, f"{len(inside_usb)} shell verts still inside the USB opening"
assert not inside_hatch, f"{len(inside_hatch)} shell verts still inside the hatch opening"
assert abs((max(cover_r) - min(cover_r)) - SC["thickness"]) < 0.05

rt.emit_ok("pass-08-shell-booleans-usb-pocket-service-hatch", shell_eval_faces=tris,
           shell_eval_nonmanifold_edges=nonmanifold, usb_opening_clear=True, hatch_opening_clear=True,
           cover_thickness_mm=round(max(cover_r) - min(cover_r), 3), cover_seam_gap_mm=round(seam, 3),
           cover_angular_radius_deg=round(math.degrees(cover_ang), 3), modifiers=[m.name for m in shell.modifiers])

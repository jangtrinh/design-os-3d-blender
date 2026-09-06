"""Pass 03 — rotor cup, faceplate, shaft, inner liner, LED ring, cushion + watch placeholders,
internal envelope. Rotating parts under WW_ROTOR_PIVOT; static under WW_BODY_FRAME.
Postconditions: cushion inside cup bore, watch inside faceplate bore, envelope inside shell.
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
col, helpers = ww.coll("WW_product"), ww.coll("WW_helpers")
body = bpy.data.objects["WW_BODY_FRAME"]
rotor = bpy.data.objects["WW_ROTOR_PIVOT"]
clay, metal = ww.clay_material(), ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
dark = ww.clay_material("WW_clay_dark", (0.12, 0.12, 0.12, 1.0))
SEG = 96
I = P["inner"]
rm, zm, zf, t = I["cup_mouth_radius"], I["cup_mouth_localz"], I["cup_floor_localz"], I["cup_wall"]

# Rotor cup: thick open bowl, two pole fans on the floor (hidden)
prof = [(rm, zm), (rm, zf - t), (0.0, zf - t), (0.0, zf), (rm - t, zf), (rm - t, zm)]
v, f = wm.lathe([(mm(r), mm(z)) for r, z in prof], SEG, closed=True)
cup = ww.mesh_obj("WW_ROTOR_CUP", v, f, col, parent=rotor, role="rotor_cup", material=dark)

# Faceplate (guilloche annulus placeholder) caps the cup wall: r 37..48, z 28..30
fp_in, fp_out, fp_z = rm - t, I["faceplate_r_out"], zm
v, f = wm.annulus(mm(fp_in), mm(fp_out), mm(fp_z), mm(fp_z + I["faceplate_thickness"]), SEG)
plate = ww.mesh_obj("WW_GUILLOCHE", v, f, col, parent=rotor, role="faceplate", material=metal)

# Shaft: keyed later; plain cylinder from the cup floor up
S = P["shaft"]
v, f = wm.cylinder(mm(S["diameter"] / 2), mm(zf), mm(zf + S["length"]), 32)
shaft = ww.mesh_obj("WW_SHAFT", v, f, col, parent=rotor, role="shaft", material=metal)

# Static inner liner from the shell bore lip down to just outside the faceplate edge
R, ro = P["shell"]["outer_radius"], P["shell"]["opening_radius"]
wi = math.sqrt((R - P["shell"]["wall"]) ** 2 - ro * ro)
lp = [(ro, wi), (fp_out + 0.5, fp_z + 3.0), (fp_out + 0.5, fp_z - 1.0), (fp_out - 1.0, fp_z - 1.0),
      (fp_out - 1.0, fp_z + 2.0), (ro - 1.5, wi - 1.0), (ro - 1.5, wi)]
v, f = wm.lathe([(mm(r), mm(z)) for r, z in lp], SEG, closed=True)
liner = ww.mesh_obj("WW_INNER_LINER", v, f, col, parent=body, role="inner_liner", material=dark)

# LED diffuser ring seated on the liner top, behind the front lip
L = P["led"]
v, f = wm.annulus(mm(L["r_in"]), mm(L["r_out"]), mm(L["z0"]), mm(L["z1"]), SEG)
led = ww.mesh_obj("WW_LED_DIFFUSER", v, f, col, parent=body, role="led_diffuser",
                  material=ww.clay_material("WW_clay_led", (0.85, 0.93, 1.0, 1.0)))

# Cushion placeholder + watch placeholder (rigid unit under rotor for now)
Cu = P["cushion"]
v, f = wm.rounded_box(mm(Cu["size_x"]), mm(Cu["size_y"]), mm(Cu["depth"]), mm(Cu["corner_radius"]),
                      corner_segs=6, z_center=mm(Cu["center_localz"]))
cushion = ww.mesh_obj("WW_CUSHION", v, f, col, parent=rotor, role="cushion", material=dark)
W = P["watch"]
ztop = Cu["center_localz"] + Cu["depth"] / 2
_old_watch = bpy.data.objects.get("WW_WATCH")
if _old_watch is not None and _old_watch.type != "MESH":  # detailed watch group from pass-14: rebuild placeholder
    for _child in list(_old_watch.children_recursive):
        bpy.data.objects.remove(_child, do_unlink=True)
    bpy.data.objects.remove(_old_watch, do_unlink=True)
v, f = wm.cylinder(mm(W["case_diameter"] / 2), mm(ztop), mm(ztop + W["case_height"]), 64)
watch = ww.mesh_obj("WW_WATCH", v, f, col, parent=rotor, role="watch", material=metal)

# Internal envelope: wire placeholder behind the cup, never rendered
v, f = wm.cylinder(mm(28.0), mm(-58.0), mm(zf - t - 2.0), 32)
env = ww.mesh_obj("WW_INTERNAL_ENVELOPE", v, f, helpers, parent=body, role="internal_envelope")
env.display_type = "WIRE"
env.hide_render = True

# --- clearance measurements in the product frame (local coords of rotor/body) ---
def local_radii(ob):
    return [math.hypot(x, y) * 1000 for x, y, z in (v.co for v in ob.data.vertices)]

cush_r = max(local_radii(cushion))
watch_r = max(local_radii(watch))
env_pts = [v.co for v in env.data.vertices]
env_r = max(p.length for p in env_pts) * 1000
assert cush_r < rm - t - 1.0, f"cushion corner {cush_r} mm hits cup bore {rm - t}"
assert watch_r < fp_in - 1.0, f"watch {watch_r} hits faceplate bore {fp_in}"
assert env_r < R - P["shell"]["wall"] - 1.0, f"envelope {env_r} outside inner sphere"
assert ztop <= zm + 1e-6, "cushion proud of cup mouth"

rt.emit_ok("pass-03-rotor-cup-cushion-watch-blockout",
           cushion_max_radius_mm=round(cush_r, 3), cup_bore_mm=rm - t,
           cushion_gap_to_bore_mm=round(rm - t - cush_r, 3), watch_max_radius_mm=round(watch_r, 3),
           faceplate_bore_mm=fp_in, envelope_max_radius_mm=round(env_r, 3),
           inner_sphere_mm=R - P["shell"]["wall"], cushion_top_lz_mm=ztop, watch_top_lz_mm=ztop + W["case_height"],
           objects=[o.name for o in (cup, plate, shaft, liner, led, cushion, watch, env)])

"""Pass 02 — shell (lathe, thick, real opening), acrylic visor (thick hemisphere), front rim.

Shell = surface of revolution about localZ: outer sphere arc from the opening to the
rear pole, cylindrical bore at the opening, inner sphere arc back. Rear poles are
triangle fans (documented; hidden at the lower rear).
Postconditions: thickness, bore radius, visor thickness, coaxiality, bboxes.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
wm = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
from mathutils import Matrix, Vector  # noqa: E402

P, mm = ww.P, ww.mm
sc = ww.activate()
col = ww.coll("WW_product")
body = ww.assert_parent = ww.empty("WW_BODY_FRAME", ww.coll("WW_helpers"),
                                   parent=ww.empty("WW_ROOT", ww.coll("WW_helpers")),
                                   matrix_local=ww.frame_P())
clay = ww.clay_material()
SEG = 96

R, wall, ro = P["shell"]["outer_radius"], P["shell"]["wall"], P["shell"]["opening_radius"]
Ri = R - wall
w0 = math.sqrt(R * R - ro * ro)
wi = math.sqrt(Ri * Ri - ro * ro)
rf = P["shell"].get("rim_flat_r_out", ro)  # flat rim r ro..rf so the opening edge is not a knife edge
z_flat = math.sqrt(R * R - rf * rf)
# the inner sphere reaches the bore radius only 0.9 mm under the flat rim (knife edge), so the
# cavity is truncated by a flat ceiling one wall below the rim; the bore runs rim -> ceiling
z_ceil = z_flat - wall
r_ceil = math.sqrt(Ri * Ri - z_ceil * z_ceil)
th_o, th_c = math.asin(rf / R), math.acos(z_ceil / Ri)
prof = wm.arc(mm(R), th_o, math.pi, 30) + wm.arc(mm(Ri), math.pi, th_c, 30) + [(mm(ro), mm(z_ceil)), (mm(ro), mm(z_flat))]
prof = wm.dedupe_profile(prof)
v, f = wm.lathe(prof, SEG, closed=True)
shell = ww.mesh_obj("WW_SHELL", v, f, col, parent=body, role="shell", material=clay)

# Visor: thick hemisphere, equator lifted by the seal clearance; mesh in lid-pivot space
Rv, tv = P["visor"]["outer_radius"], P["visor"]["thickness"]
zeq = w0 + P["visor"]["rim_clearance"]
lid = ww.empty("WW_LID_PIVOT", ww.coll("WW_helpers"), parent=body,
               matrix_local=Matrix.Translation(Vector((0.0, mm(ro + P["visor"]["hinge_setback"]), mm(w0)))))
prof_v = wm.arc(mm(Rv), math.pi / 2, 0.0, 24, z_offset=mm(zeq)) + \
    wm.arc(mm(Rv - tv), 0.0, math.pi / 2, 24, z_offset=mm(zeq))
prof_v = wm.dedupe_profile(prof_v)
v, f = wm.lathe(prof_v, SEG, closed=True)
off = lid.matrix_local.translation
v = [(x - off.x, y - off.y, z - off.z) for x, y, z in v]
glass = bpy.data.materials.get("WW_clay_glass") if "bpy" in dir() else None
import bpy  # noqa: E402
glass = ww.clay_material("WW_clay_glass", (0.7, 0.85, 1.0, 1.0))
visor = ww.mesh_obj("WW_VISOR", v, f, col, parent=lid, role="visor", material=glass)

# Front rim bezel: annulus seated on the sphere around the opening
fr = P["front_rim"]
v, f = wm.lathe([(mm(fr["r_in"]), mm(fr["z0"])), (mm(fr["r_out"]), mm(math.sqrt(R * R - fr["r_out"] ** 2) - 0.5)),
                 (mm(fr["r_out"]), mm(fr["z1"] - 1.0)), (mm(fr["r_in"] + 1.0), mm(fr["z1"])),
                 (mm(fr["r_in"]), mm(fr["z1"]))], SEG, closed=True)
metal = ww.clay_material("WW_clay_metal", (0.8, 0.8, 0.8, 1.0))
rim = ww.mesh_obj("WW_FRONT_RIM", v, f, col, parent=body, role="front_rim", material=metal)

# --- measurements (evaluated, world) ---
bpy.context.view_layer.update()
axis = ww.world_axis(body)
vis_axis = ww.world_axis(visor)
C = ww.vmm(P["shell"]["center_world"])
# visor equator centre must lie on the body axis
eq_center_world = visor.matrix_world @ Vector((0.0, 0.0, 0.0)) + vis_axis * 0.0
lid_world = lid.matrix_world.translation
eq_c = lid_world - ww.world_axis(lid, (0, 1, 0)) * mm(ro + P["visor"]["hinge_setback"])
off_axis = ((eq_c - C) - (eq_c - C).dot(axis) * axis).length
shell_pts = [shell.matrix_world @ v.co for v in shell.data.vertices]  # base lathe, not later booleans
rad = [(p - C).length * 1000 for p in shell_pts]
rad_sph = [v.co.length * 1000 for v in shell.data.vertices if v.co.z * 1000 < z_ceil - 0.01]  # below the ceiling: pure spheres
lo, hi = ww.evaluated_bbox(shell)
assert abs(math.degrees(vis_axis.angle(axis))) < 0.01, "visor not coaxial"
assert off_axis * 1000 < 0.05, f"visor centre off axis {off_axis*1000} mm"
assert abs(max(rad) - R) < 0.05 and abs(min(rad_sph) - Ri) < 0.05, (max(rad), min(rad_sph))
assert min(rad) > Ri - wall - 0.05, min(rad)  # ceiling corner (ro, z_ceil) is the innermost vertex
assert lo.z > 0, "shell below table"

rt.emit_ok("pass-02-shell-visor-rim-blockout",
           shell_faces=len(shell.data.polygons), shell_r_max_mm=round(max(rad), 3),
           shell_r_min_mm=round(min(rad_sph), 3), wall_mm=round(max(rad) - min(rad_sph), 3), ceiling_corner_r_mm=round(min(rad), 3),
           opening_r_mm=ro, w0_mm=round(w0, 3), rim_flat_z_mm=round(z_flat, 3), rim_flat_r_out_mm=rf, bore_height_mm=round(z_flat - z_ceil, 3),
           ceiling_z_mm=round(z_ceil, 3), ceiling_undercut_mm=round(r_ceil - ro, 3), lip_wall_mm=round(math.hypot(r_ceil - ro, wall), 3),
           visor_axis_vs_body_deg=round(math.degrees(vis_axis.angle(axis)), 5),
           visor_center_off_axis_mm=round(off_axis * 1000, 4), visor_thickness_mm=tv,
           visor_equator_lz_mm=round(zeq, 3), shell_bbox_z_mm=[round(lo.z * 1000, 2), round(hi.z * 1000, 2)],
           rim_faces=len(rim.data.polygons))

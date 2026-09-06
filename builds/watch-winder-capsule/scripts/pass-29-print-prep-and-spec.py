"""Pass 29 — production-gate audit prep (headless, loads the stills blend):
1. bake every candidate part to a standalone object at identity, mesh = evaluated
   (modifiers applied) geometry in the PART'S OWN frame (axis-aligned for printing);
2. drop everything else and save watch-winder-capsule-print.blend;
3. write spec.json with NOMINAL target dims derived from design-parameters.json
   (not from measuring the mesh), holes as features, physical evidence still owed.
The gate (scripts/production-gate.py) is run separately on that blend.
"""
import json
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
pz = rt.load_lib(os.path.join(HERE, "ww_presets.py"))
P = ww.P
assert bpy.app.background
sc = bpy.data.scenes["WW_capsule"]
bpy.context.window.scene = sc
for n in ("WW_LID_PIVOT", "WW_ROTOR_PIVOT", "WW_CUSHION_UNIT", "WW_ORBIT_PIVOT"):
    if n in bpy.data.objects:
        bpy.data.objects[n].animation_data_clear()
pz.apply(sc, "hero", P)

S, K, Cu, I, R, wall = P["stand"], P["knobs"], P["cushion"], P["inner"], P["shell"]["outer_radius"], P["shell"]["wall"]
ro, w0 = P["shell"]["opening_radius"], P["shell"]["opening_datum_w0"]
wi = math.sqrt((R - wall) ** 2 - ro * ro)
SC, fr, V, H, T = P["service_cover"], P["front_rim"], P["visor"], P["hinge"], P["finger_tab"]
ang = math.asin((SC["cap_radius"] - SC["seam_gap"]) / R)
C = ww.vmm(P["shell"]["center_world"])
foot0 = ww.vmm(S["feet_contact_world"][0])
d0 = (foot0 - C).normalized()
leg_len = (Vector((foot0.x, foot0.y, ww.mm(S["foot_height"]))) - (C + d0 * ww.mm(S["attach_radius"]))).length * 1000
body = bpy.data.objects["WW_BODY_FRAME"]
hatch_m = bpy.data.objects["WW_CUT_SERVICE_HATCH"].matrix_local  # in the body (P) frame
hatch_axis_v = (hatch_m.to_3x3() @ Vector((0, 0, 1))).normalized()
hatch_c = [round(v * 1000, 3) for v in (hatch_m.translation - hatch_axis_v * 0.0013)]  # ring probe 1.3 mm inside the wall
hatch_axis = [round(v, 6) for v in (hatch_m.to_3x3() @ Vector((0, 0, 1))).normalized()]
usb_m = bpy.data.objects["WW_USB_RECESS"].matrix_local
sock_z = Cu["center_localz"] - Cu["depth"] / 2

# (object, nominal dims mm, tol, material/process, min_wall, features)
PARTS = [
    ("WW_SHELL", [2 * R, 2 * R, R + math.sqrt(R * R - P["shell"]["rim_flat_r_out"] ** 2)], 0.3, "PETG (matte)", "FDM 0.4 mm / 0.2 mm layers", 2.0, [
        {"id": "service_hatch", "type": "hole", "axis": hatch_axis, "center_mm": hatch_c, "diameter_mm": 2 * SC["cap_radius"], "tol_mm": 0.3},
        {"id": "usb_pocket", "type": "slot", "axis": [round(v, 6) for v in (usb_m.to_3x3() @ Vector((0, 0, 1))).normalized()],
         "center_mm": [round(v * 1000, 3) for v in usb_m.translation], "diameter_mm": P["usb"]["recess"][1], "tol_mm": 0.3}]),
    ("WW_REAR_SERVICE_COVER", [2 * (R - 0.05) * math.sin(ang), 2 * (R - 0.05) * math.sin(ang), (R - 0.05) - (R - SC["thickness"] - 0.05) * math.cos(ang)], 0.3, "PETG", "FDM", 2.0, []),
    ("WW_ROTOR_CUP", [2 * I["cup_mouth_radius"], 2 * I["cup_mouth_radius"], I["cup_mouth_localz"] - (I["cup_floor_localz"] - I["cup_wall"])], 0.3, "ABS (satin black)", "FDM", 1.5, []),
    ("WW_INNER_LINER", [2 * ro, 2 * ro, wi - (I["cup_mouth_localz"] - 1.0)], 0.3, "ABS", "FDM", 1.0, []),
    ("WW_FRONT_RIM", [2 * fr["r_out"], 2 * fr["r_out"], fr["z1"] - (math.sqrt(R * R - fr["r_out"] ** 2) - 0.5)], 0.3, "aluminium (turned) / resin proxy", "SLA proxy", 1.0, []),
    ("WW_GUILLOCHE", [2 * I["faceplate_r_out"], 2 * I["faceplate_r_out"], I["faceplate_thickness"] + P["guilloche"]["relief"]], 0.3, "brass (machined) / resin proxy", "SLA proxy", None, []),
    ("WW_KNOB_L", [K["body_depth"], K["body_diameter"], K["body_diameter"]], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, []),
    ("WW_KNURL_L", [K["body_depth"] - 2.2, K["body_diameter"], K["body_diameter"]], 0.3, "stainless / resin proxy", "SLA proxy", None, []),
    ("WW_KNOB_BOSS_L", [K["boss_outer_x"] - K["boss_inner_x"], K["boss_diameter"] + 2.0, K["boss_diameter"] + 2.0], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, []),
    ("WW_CUSHION", [Cu["size_x"], Cu["size_y"], Cu["depth"]], 0.5, "TPU 85A / leather-wrapped foam", "FDM TPU", 1.0, [
        {"id": "keyed_socket", "type": "hole", "axis": "z", "center_mm": [0.0, 0.0, sock_z + 1.5], "diameter_mm": P["shaft"]["diameter"] + 0.4, "depth_mm": Cu["socket_depth"], "tol_mm": 0.3,
         "keyed_flat_mm": P["shaft"]["diameter"] / 2 - P["shaft"]["keyed_flat_depth"] + 0.2, "keyed_flat_dir": "x"}]),
    ("WW_SHAFT", [P["shaft"]["diameter"] - P["shaft"]["keyed_flat_depth"], P["shaft"]["diameter"], sock_z + Cu["socket_depth"] - I["cup_floor_localz"]], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, []),
    ("WW_LEG_01", [2 * S["leg_radius_at_shell"], 2 * S["leg_radius_at_shell"], leg_len], 0.3, "stainless (turned) / resin proxy", "SLA proxy", 1.0, []),
    ("WW_FOOT_01", [2 * S["foot_radius"], 2 * S["foot_radius"], S["foot_height"]], 0.3, "rubber / TPU", "FDM TPU", 1.0, []),
    ("WW_VISOR", [2 * V["outer_radius"], 2 * V["outer_radius"], V["outer_radius"]], 0.3, "PMMA (formed) / clear resin proxy", "SLA clear", 1.5, []),
    ("WW_HINGE_FIXED", [2 * (7.8 + H["lug_thickness"]), 9.0, 9.0], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, [], 2),
    ("WW_HINGE_MOVING", [2 * 7.5, 7.0, 5.0], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, []),
    ("WW_FINGER_TAB", [T["size"][0], T["size"][1], T["height"]], 0.3, "stainless / resin proxy", "SLA proxy", 1.0, []),
]

# --- bake to standalone objects (local evaluated mesh, identity transform) ---
deps = bpy.context.evaluated_depsgraph_get()
keep = set()
baked = {}
for name, *_rest in PARTS:
    src = bpy.data.objects[name]
    ev = src.evaluated_get(deps)
    me = ev.to_mesh()
    new = bpy.data.meshes.new(name + "_print")
    new.from_pydata([v.co.copy() for v in me.vertices], [], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    new.validate(verbose=False)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(new)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(new)
    bm.free()
    new.update()
    baked[name] = new
    keep.add(name)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for name, me in baked.items():
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.matrix_world = Matrix.Identity(4)
# hinge moving = knuckle + bridge modelled as two overlapping solids: union them into one printable shell
hm = bpy.data.objects["WW_HINGE_MOVING"]
import bmesh
bm = bmesh.new()
bm.from_mesh(hm.data)
parts_ = []
seen = set()
for f in bm.faces:
    if f.index in seen:
        continue
    stack, comp = [f], set()
    while stack:
        g = stack.pop()
        if g.index in comp:
            continue
        comp.add(g.index)
        for e in g.edges:
            stack.extend(x for x in e.link_faces if x.index not in comp)
    seen |= comp
    parts_.append(comp)
bm.free()
if len(parts_) > 1:
    import bpy as _b
    tmp_meshes = []
    for i, comp in enumerate(parts_):
        bmp = bmesh.new()
        bmp.from_mesh(hm.data)
        bmp.faces.ensure_lookup_table()
        bmesh.ops.delete(bmp, geom=[fc for fc in bmp.faces if fc.index not in comp], context="FACES")
        m = _b.data.meshes.new(f"hm_part{i}")
        bmp.to_mesh(m)
        bmp.free()
        tmp_meshes.append(m)
    base = _b.data.objects.new("hm_base", tmp_meshes[0])
    sc.collection.objects.link(base)
    for m in tmp_meshes[1:]:
        cut = _b.data.objects.new("hm_cut", m)
        sc.collection.objects.link(cut)
        mod = base.modifiers.new("union", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "UNION", "EXACT", cut
        deps2 = _b.context.evaluated_depsgraph_get()
        ev2 = base.evaluated_get(deps2)
        me2 = ev2.to_mesh()
        merged = _b.data.meshes.new("hm_union")
        merged.from_pydata([v.co.copy() for v in me2.vertices], [], [tuple(p.vertices) for p in me2.polygons])
        ev2.to_mesh_clear()
        base.modifiers.clear()
        base.data = merged
        _b.data.objects.remove(cut, do_unlink=True)
    hm.data = base.data
    _b.data.objects.remove(base, do_unlink=True)
sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 1.0
out = os.path.join(ww.BUILD, "watch-winder-capsule-print.blend")
assert bpy.ops.wm.save_as_mainfile(filepath=out, copy=True) == {"FINISHED"}

spec = {
    "schema_version": 1, "units": "mm",
    "project": "watch-winder-capsule — production-gate AUDIT (spec derived from provisional design-parameters.json, owner 2026-09-06 13:15)",
    "parts": [dict({"id": row[0].lower().replace("ww_", ""), "object": row[0], "target_dims_mm": [round(d, 3) for d in row[1]],
                    "tol_mm": row[2], "material": row[3], "process": row[4], "orientation_up": "+z", "max_overhang_deg": 45.0,
                    "expected_shells": row[7] if len(row) > 7 else 1, "features": row[6]},
                   **({"min_wall_mm": row[5]} if row[5] is not None else {})) for row in PARTS],
    "fasteners": [],
    "load_cases": [{"id": "none-declared", "description": "tabletop product; no load case has been specified by the owner", "status": "declared only"}],
    "required_checks": ["non_manifold_edges", "bbox_dims_mm", "scale_applied", "signed_volume_positive"],
    "physical_evidence": ["no part has been printed", "visor-in-rim fit trial (0.5 mm designed seal gap)",
                          "cushion-in-cup fit trial (2.7 mm designed gap)", "keyed shaft/socket engagement trial (0.2 mm clearance)",
                          "metal parts (legs, knobs, rim, hinge) are modelled as machined metal; a resin proxy print proves shape only"],
}
spec_path = os.path.join(ww.BUILD, "spec.json")
with open(spec_path, "w", encoding="utf-8") as fh:
    json.dump(spec, fh, indent=1)
rt.emit_ok("pass-29-print-prep-and-spec", parts=len(PARTS), print_blend=out, spec=spec_path,
           objects_in_print_blend=sorted(o.name for o in bpy.data.objects), leg_len_mm=round(leg_len, 3), hatch_center_mm=hatch_c)

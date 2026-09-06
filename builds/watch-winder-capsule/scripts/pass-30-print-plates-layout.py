"""Pass 30 — parts on print plates (headless; load watch-winder-capsule-print.blend).

Builds a NEW scene WW_plates (the source scene WW_capsule is never touched): the 24
printable instances (17 baked parts + knob/knurl/boss mirrors + 2 leg + 2 foot copies),
each rotated into its print orientation, dropped to min z = 0 and shelf-packed onto
per-material build plates. Verifies numerically, exports one STL per plate in mm,
re-imports one to prove the scale, renders a workbench preview per plate, saves
watch-winder-capsule-plates.blend and writes plates/manifest.json + reports/print-plates.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
mt = rt.load_lib(os.path.join(HERE, "ww_materials.py"))
mh = rt.load_lib(os.path.join(HERE, "ww_mesh.py"))
pl = rt.load_lib(os.path.join(HERE, "ww_plates.py"))
assert bpy.app.background, "pass 30 is headless-only; it must never write to the GUI session"
RES = (1024, 683)

# ---------------------------------------------------------------- 1. orient every instance
built, measured = {}, {}
for it in pl.instances():
    src = bpy.data.objects[it["source"]]
    verts = [Vector(v.co) * 1000.0 for v in src.data.vertices]          # mm, part frame
    faces = [tuple(p.vertices) for p in src.data.polygons]
    if it["mirror"]:
        verts, faces = pl.mirror_mesh(verts, faces)
        assert mh.signed_volume(verts, faces) > 0, f"{it['instance']}: mirror left it inside-out"
    verts, w, h, z = pl.drop_to_plate(pl.orient_mesh(verts, it["rotation"]))
    exp = pl.EXPECTED_HEIGHT_MM.get(it["instance"])
    assert exp is None or abs(z - exp) <= 0.2, (it["instance"], round(z, 3), exp)
    it.update(verts=verts, faces=faces, bbox_mm=[round(w, 3), round(h, 3), round(z, 3)])
    built[it["instance"]] = it
    sco = [v.co for v in src.data.vertices]
    measured[it["instance"]] = {"source_bbox_mm": [round((max(c[i] for c in sco) - min(c[i] for c in sco)) * 1000, 3) for i in range(3)],
                                "oriented_bbox_mm": it["bbox_mm"], "expected_height_mm": exp}

plates = []
for bucket in pl.PLATE_SIZES:
    items = [(i["instance"], i["bbox_mm"][0], i["bbox_mm"][1]) for i in built.values() if i["bucket"] == bucket]
    plates += pl.pack_bucket(bucket, items)

# ---------------------------------------------------------------- 2. scene + objects
for old in [s for s in bpy.data.scenes if s.name == "WW_plates"]:
    bpy.data.scenes.remove(old)
sc = bpy.data.scenes.new("WW_plates")
sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 1.0
sc.render.engine, sc.render.use_persistent_data = "BLENDER_WORKBENCH", False
bpy.context.window.scene = sc
col = bpy.data.collections.new("WW_plates_layout")
sc.collection.children.link(col)
slab_mat = mt.mat_simple("PL_MAT_PLATE", "#2B2B2B", 0.8)
mats = {}
for b, (_proc, _mat, hexc, rough) in pl.BUCKETS.items():
    name = "PL_MAT_" + b.upper().replace("-", "_")
    if hexc:
        mats[b] = mt.mat_simple(name, hexc, rough)
    else:
        m, nt, out = mt._new(name)
        mt._principled(nt, out, **{"Base Color": (1.0, 1.0, 1.0, 1.0), "Transmission Weight": 1.0,
                                   "IOR": 1.5, "Roughness": rough, "Metallic": 0.0})
        mats[b] = m

ox, oy, objs = 0.0, 0.0, {}  # 3 plates per row: FDM row in front, resin row behind
for i, p in enumerate(plates):
    if i and i % 3 == 0:
        ox, oy = 0.0, oy + 256.0 + pl.PLATE_GAP_MM
    pw, ph = p["size_mm"]
    p["origin_mm"] = [round(ox, 3), round(oy, 3)]
    sv, sf = mh.rounded_box(pw, ph, pl.SLAB_THICKNESS_MM, 2.0, 4, -pl.SLAB_THICKNESS_MM / 2.0)
    shift = Vector((ox + pw / 2.0, oy + ph / 2.0, 0.0))
    ww.mesh_obj("PL_PLATE_" + p["id"], [(Vector(v) + shift) * 0.001 for v in sv], sf, col,
                smooth=False, role="print_plate", material=slab_mat)
    p["parts"] = []
    for pid, x, y, w, h, rot in p["placements"]:
        it = built[pid]
        vs = it["verts"]
        if rot:
            vs = pl.drop_to_plate(pl.orient_mesh(vs, ("Z", 90.0)))[0]
        ob = ww.mesh_obj(f"PL_{p['id']}_{pid}", [(v + Vector((x + ox, y + oy, 0.0))) * 0.001 for v in vs],
                         it["faces"], col, smooth=False, role="print_part", material=mats[p["bucket"]])
        ob["pl_plate"], ob["pl_part"], ob["pl_bucket"] = p["id"], pid, p["bucket"]
        objs.setdefault(p["id"], []).append(ob)
        p["parts"].append({"instance": pid, "source_object": it["source"], "mirrored": it["mirror"],
                           "rotation_applied_deg": ([list(it["rotation"])] if it["rotation"] else [])
                           + ([["Z", 90.0]] if rot else []),
                           "position_mm": [round(x, 3), round(y, 3), 0.0],
                           "bbox_mm": [round(w, 3), round(h, 3), it["bbox_mm"][2]],
                           "recommended_tilt_deg": it["recommended_tilt_deg"], "supports_note": it["supports_note"]})
    ox += pw + pl.PLATE_GAP_MM

# ---------------------------------------------------------------- 3. numeric verification
checks = {"instances": sum(len(v) for v in objs.values()), "plates": len(plates), "min_gap_mm": 1e9,
          "max_abs_min_z_mm": 0.0, "nonmanifold_edges": 0, "min_signed_volume_mm3": 1e9, "overlaps": []}
assert checks["instances"] == 24, checks["instances"]
for p in plates:
    gap, bad = pl.check_placements(p)
    checks["min_gap_mm"] = min(checks["min_gap_mm"], gap)
    checks["overlaps"] += bad
    for ob in objs[p["id"]]:
        co = [v.co for v in ob.data.vertices]
        checks["max_abs_min_z_mm"] = max(checks["max_abs_min_z_mm"], abs(min(c.z for c in co) * 1000.0))
        checks["min_signed_volume_mm3"] = min(checks["min_signed_volume_mm3"],
                                              mh.signed_volume(co, [tuple(f.vertices) for f in ob.data.polygons]) * 1e9)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        checks["nonmanifold_edges"] += sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
assert not checks["overlaps"], checks["overlaps"]
assert checks["max_abs_min_z_mm"] <= 0.001, checks["max_abs_min_z_mm"]
assert checks["nonmanifold_edges"] == 0 and checks["min_signed_volume_mm3"] > 0, checks

# ---------------------------------------------------------------- 4. STL export + round trip
pdir = os.path.dirname(ww.state_path("plates", "manifest.json"))
for p in plates:
    for ob in sc.objects:
        ob.select_set(False)
    for ob in objs[p["id"]]:  # slide the plate back to its own origin: a slicer needs plate-local mm
        ob.select_set(True)
        ob.location.x, ob.location.y = -p["origin_mm"][0] * 0.001, -p["origin_mm"][1] * 0.001
    p["stl"] = os.path.join(pdir, p["id"] + ".stl")
    assert bpy.ops.wm.stl_export(filepath=p["stl"], check_existing=False, export_selected_objects=True,
                                 global_scale=1000.0, use_scene_unit=False, apply_modifiers=False,
                                 ascii_format=False, forward_axis="Y", up_axis="Z") == {"FINISHED"}
    p["stl_sha256"] = ww.sha256_file(p["stl"])
    for ob in objs[p["id"]]:
        ob.location.x, ob.location.y = 0.0, 0.0
tmp = bpy.data.scenes.new("WW_plates_stlcheck")
bpy.context.window.scene = tmp
probe = max(plates, key=lambda q: len(q["parts"]))
assert bpy.ops.wm.stl_import(filepath=probe["stl"], global_scale=1.0, use_scene_unit=False,
                             forward_axis="Y", up_axis="Z") == {"FINISHED"}
pts = [ob.matrix_world @ v.co for ob in tmp.objects for v in ob.data.vertices]
got = [round(min(p_[i] for p_ in pts), 3) for i in range(3)] + [round(max(p_[i] for p_ in pts), 3) for i in range(3)]
want = [min(a["position_mm"][0] for a in probe["parts"]), min(a["position_mm"][1] for a in probe["parts"]), 0.0,
        max(a["position_mm"][0] + a["bbox_mm"][0] for a in probe["parts"]),
        max(a["position_mm"][1] + a["bbox_mm"][1] for a in probe["parts"]),
        max(a["bbox_mm"][2] for a in probe["parts"])]
checks["stl_roundtrip"] = {"plate": probe["id"], "imported_bbox_mm": got, "expected_bbox_mm": [round(v, 3) for v in want]}
assert max(abs(g - w) for g, w in zip(got, want)) < 0.01, checks["stl_roundtrip"]
for ob in list(tmp.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.context.window.scene = sc
bpy.data.scenes.remove(tmp)

# ---------------------------------------------------------------- 5. workbench previews
def preview(name, lo, hi, path):
    """3/4 overhead workbench still (az -35, el 55) with the ortho scale solved from the bbox."""
    import math
    c = (lo + hi) * 0.5
    a, e = math.radians(-35.0), math.radians(55.0)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam = st.camera(name, col, c + d * 2.5, c, ortho_scale=1.0)
    R = cam.matrix_world.to_3x3()
    right, up = R.col[0], R.col[1]
    corners = [Vector((x, y, z)) - c for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    ex = 2 * max(abs(v.dot(right)) for v in corners)
    ey = 2 * max(abs(v.dot(up)) for v in corners)
    cam.data.ortho_scale = 1.08 * max(ex, ey * RES[0] / RES[1])
    return st.clay_render(sc, cam, path, RES[0], RES[1])

rdir = os.path.join(st.RENDERS, "plates")
allpts = []
for p in plates:
    pts = [ob.matrix_world @ v.co for ob in objs[p["id"]] for v in ob.data.vertices]
    pts += [Vector((p["origin_mm"][0] * 0.001, p["origin_mm"][1] * 0.001, -0.003)), Vector(((p["origin_mm"][0] + p["size_mm"][0]) * 0.001, (p["origin_mm"][1] + p["size_mm"][1]) * 0.001, 0))]
    allpts += pts
    lo = Vector([min(q[i] for q in pts) for i in range(3)])
    hi = Vector([max(q[i] for q in pts) for i in range(3)])
    p["preview"] = preview("PL_CAM_" + p["id"], lo, hi, os.path.join(rdir, f"preview-{p['id']}.png"))
overview = preview("PL_CAM_overview", Vector([min(q[i] for q in allpts) for i in range(3)]),
                   Vector([max(q[i] for q in allpts) for i in range(3)]), os.path.join(rdir, "preview-all-plates.png"))

# ---------------------------------------------------------------- 6. save + manifests
blend = os.path.join(ww.BUILD, "watch-winder-capsule-plates.blend")
assert bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True) == {"FINISHED"}
manifest = {"units": "mm", "spacing_mm": pl.SPACING_MM, "plate_gap_mm": pl.PLATE_GAP_MM,
            "stl_frame": "plate-local mm (origin at the plate corner); origin_mm is the plate's place in the WW_plates row",
            "plates": [
    {k: p[k] for k in ("id", "bucket", "size_mm", "margin_mm", "margin_requested_mm", "margin_reduced",
                       "origin_mm", "utilisation_pct", "parts", "stl", "stl_sha256")}
    | {"process": pl.BUCKETS[p["bucket"]][0], "material": pl.BUCKETS[p["bucket"]][1], "preview": p["preview"]}
    for p in plates]}
ww.write_json(os.path.join(pdir, "manifest.json"), manifest)
checks["min_gap_mm"] = round(checks["min_gap_mm"], 4)
ww.write_json(ww.state_path("reports", "print-plates.json"),
              dict(manifest, checks=checks, measured=measured, blend=blend, blend_sha256=ww.sha256_file(blend),
                   source_blend_sha256=ww.sha256_file(os.path.join(ww.BUILD, "watch-winder-capsule-print.blend")),
                   overview_preview=overview))
rt.emit_ok("pass-30-print-plates-layout", instances=checks["instances"], plates=[p["id"] for p in plates],
           utilisation_pct={p["id"]: p["utilisation_pct"] for p in plates}, min_gap_mm=checks["min_gap_mm"],
           max_abs_min_z_mm=round(checks["max_abs_min_z_mm"], 6), nonmanifold_edges=checks["nonmanifold_edges"],
           min_signed_volume_mm3=round(checks["min_signed_volume_mm3"], 3),
           margin_reduced=[p["id"] for p in plates if p["margin_reduced"]],
           stl_roundtrip_max_err_mm=round(max(abs(g - w) for g, w in zip(got, want)), 5),
           blend=blend, manifest=os.path.join(pdir, "manifest.json"), overview=overview)

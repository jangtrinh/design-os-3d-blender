"""Pass 11 — Phase-2 gate: per-object topology audit (evaluated), signed volume of shell/visor,
Cycles strip-reflection test (material override, restored), lid/rotor/removal pose clay renders,
save + checkpoint + gate report.
"""
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import agent_runtime as rt  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ww = rt.load_lib(os.path.join(HERE, "ww_lib.py"))
st = rt.load_lib(os.path.join(HERE, "ww_studio.py"))
lib = rt.load_lib(os.path.join(ROOT, "scripts", "agent-verify-lib.py"))
P, mm = ww.P, ww.mm
sc = ww.activate()


def audit(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    val = Counter(len(v.link_edges) for v in bm.verts)
    r = {"faces": len(bm.faces), "tris": sum(1 for f in bm.faces if len(f.verts) == 3),
         "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
         "nonmanifold": sum(1 for e in bm.edges if not e.is_manifold),
         "flipped": sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous),
         "zero_area": sum(1 for f in bm.faces if f.calc_area() < 1e-12),
         "doubles": len(bmesh.ops.find_doubles(bm, verts=bm.verts, dist=1e-6)["targetmap"]),
         "poles5plus": sum(n for k, n in val.items() if k >= 5)}
    me.calc_loop_triangles()
    r["signed_volume_mm3"] = round(sum(me.vertices[t.vertices[0]].co.dot(me.vertices[t.vertices[1]].co.cross(me.vertices[t.vertices[2]].co)) for t in me.loop_triangles) / 6.0 * 1e9, 1)
    bm.free()
    ev.to_mesh_clear()
    return r


meshes = [o for o in ww.ww_objects() if o.type == "MESH"]
topo = {o.name: audit(o) for o in meshes}
has_bool = {o.name: any(m.type == "BOOLEAN" for m in o.modifiers) for o in meshes}
# doubles/n-gons are tolerated only as EXACT-boolean by-products on render meshes; reported, not hidden
bad = {n: t for n, t in topo.items() if t["nonmanifold"] or t["flipped"] or t["zero_area"] or (t["doubles"] and not has_bool[n])}
assert not bad, f"topology defects: {bad}"
assert topo["WW_SHELL"]["signed_volume_mm3"] > 0 and topo["WW_VISOR"]["signed_volume_mm3"] > 0

# Cycles strip reflection: glossy override + one long thin area light, then restore everything
col = ww.coll("WW_studio")
strip = bpy.data.objects.get("WW_TEST_STRIP")
if strip is None:
    ld = bpy.data.lights.new("WW_TEST_STRIP", "AREA")
    strip = bpy.data.objects.new("WW_TEST_STRIP", ld)
    col.objects.link(strip)
strip.data.shape, strip.data.size, strip.data.size_y, strip.data.energy = "RECTANGLE", 2.0, 0.08, 400.0
strip.matrix_world = Matrix.Translation(Vector((0.0, -0.6, 0.55))) @ Vector((0, 0.6, -0.45)).to_track_quat("-Z", "Y").to_matrix().to_4x4()
gl = bpy.data.materials.get("WW_test_gloss") or bpy.data.materials.new("WW_test_gloss")
b = gl.node_tree.nodes.get("Principled BSDF")
b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 1.0, 0.08
b.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
vl = sc.view_layers[0]
saved_override, saved_world = vl.material_override, sc.world.node_tree.nodes.get("Background").inputs[0].default_value[:] if sc.world.node_tree.nodes.get("Background") else None
saved_cam, saved_strip_hide = sc.camera, strip.hide_render
try:
    vl.material_override = gl
    sc.camera = bpy.data.objects["WW_CAM_CONCEPT"]
    strip.hide_render = False
    with bpy.context.temp_override(scene=sc):
        refl = lib.preview_render(os.path.join(st.RENDERS, "phase2-strip-reflection.png"), res=768, samples=48, engine="CYCLES")
    stats = lib.frame_stats(refl)
finally:
    vl.material_override = saved_override
    sc.camera = saved_cam
    strip.hide_render = True
assert stats["stdev"] > 0.01, stats

# Pose renders (workbench clay) — lid 0/50/100, rotor 0/90/180/270, cushion lifted
cam = bpy.data.objects["WW_CAM_CONCEPT"]
lid, rotor, unit = (bpy.data.objects[n] for n in ("WW_LID_PIVOT", "WW_ROTOR_PIVOT", "WW_CUSHION_UNIT"))
lid0, rot0, unit0 = lid.matrix_local.copy(), rotor.matrix_local.copy(), unit.matrix_local.copy()
poses = {}
try:
    for d in (0, 50, 100):
        lid.matrix_local = lid0 @ Matrix.Rotation(math.radians(-d), 4, "X")
        poses[f"lid{d:03d}"] = st.clay_render(sc, cam, os.path.join(st.RENDERS, f"phase2-pose-lid{d:03d}.png"), 640, 640)
    lid.matrix_local = lid0 @ Matrix.Rotation(math.radians(-100), 4, "X")
    for d in (0, 90, 180, 270):
        rotor.matrix_local = rot0 @ Matrix.Rotation(math.radians(d), 4, "Z")
        poses[f"rotor{d:03d}"] = st.clay_render(sc, cam, os.path.join(st.RENDERS, f"phase2-pose-rotor{d:03d}.png"), 640, 640)
    rotor.matrix_local = rot0
    unit.matrix_local = Matrix.Translation(Vector((0, 0, mm(70))))
    poses["lifted"] = st.clay_render(sc, cam, os.path.join(st.RENDERS, "phase2-pose-cushion-lifted.png"), 640, 640)
finally:
    lid.matrix_local, rotor.matrix_local, unit.matrix_local = lid0, rot0, unit0
    bpy.context.view_layer.update()

main = os.path.join(ww.BUILD, "watch-winder-capsule.blend")
ck = os.path.join(ww.BUILD, "checkpoints", "phase2-form.blend")
if not bpy.app.background:  # only the GUI session writes the working file (isolated rebuilds must not)
    assert bpy.ops.wm.save_as_mainfile(filepath=main) == {"FINISHED"}
    assert bpy.ops.wm.save_as_mainfile(filepath=ck, copy=True) == {"FINISHED"}
report = {"topology": topo, "strip_reflection": {"path": refl, "stats": stats}, "poses": poses,
          "blend_sha256": ww.sha256_file(main), "parameters_sha256": ww.sha256_file(ww.PARAM_PATH),
          "axis_elevation_deg": round(ww.elevation_deg(ww.world_axis(bpy.data.objects["WW_BODY_FRAME"])), 4)}
ww.write_json(ww.state_path("reports", "phase2-gate.json"), report)
rt.emit_ok("pass-11-phase2-gate-topology-poses-reflection", objects_audited=len(topo), defects=0,
           shell_eval_faces=topo["WW_SHELL"]["faces"], visor_signed_volume_mm3=topo["WW_VISOR"]["signed_volume_mm3"],
           strip_stats={k: round(v, 4) if isinstance(v, float) else v for k, v in stats.items()},
           poses=sorted(poses), blend_sha256=report["blend_sha256"][:16], axis_elevation_deg=report["axis_elevation_deg"])

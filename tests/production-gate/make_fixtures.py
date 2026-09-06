"""Generate every production-gate test fixture .blend into a target directory.

Run headless:
    Blender --factory-startup -b --python-exit-code 3 \
        --python tests/production-gate/make_fixtures.py -- --out <dir>

Nothing here reads builds/ or any existing .blend: every fixture is generated
from primitives so the gate is tested against geometry whose truth is known.
"""
import argparse
import os
import sys

import bmesh
import bpy
from mathutils import Matrix

MM = 0.001
BRACKET = "bracket-m3"
HOLES = [(13.0, 0.0, 3.4), (-13.0, 0.0, 3.4), (0.0, 0.0, 3.6)]  # M3 clearance x2, M2.5 heat-set pilot


def reset():
    bpy.ops.wm.read_homefile(use_empty=True)


def link(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box(name, sx, sy, sz, at=(0.0, 0.0, 0.0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.verts.ensure_lookup_table()
    bmesh.ops.scale(bm, vec=(sx * MM, sy * MM, sz * MM), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=tuple(v * MM for v in at), verts=bm.verts[:])
    return link(name, bm)


def cylinder(name, x, y, dia, depth, z=0.0, segments=64):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=dia * MM / 2.0, radius2=dia * MM / 2.0,
                          depth=depth * MM,
                          matrix=Matrix.Translation((x * MM, y * MM, z * MM)))
    return link(name, bm)


def cut(target, cutter):
    m = target.modifiers.new("b_" + cutter.name, "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = "EXACT"
    m.use_hole_tolerant = True
    with bpy.context.temp_override(object=target, active_object=target,
                                   selected_objects=[target]):
        res = bpy.ops.object.modifier_apply(modifier=m.name)
    assert res == {"FINISHED"}, res
    bpy.data.objects.remove(cutter, do_unlink=True)


def plate(length=40.0, width=20.0, thick=6.0, holes=None, scale_mm=1.0,
          name=BRACKET):
    """scale_mm 0.5 builds the mesh at half size (for the unapplied-scale case)."""
    s = scale_mm
    ob = box(name, length * s, width * s, thick * s)
    for i, (x, y, dia) in enumerate(HOLES if holes is None else holes):
        cut(ob, cylinder("cut%d" % i, x * s, y * s, dia * s, thick * s * 4.0))
    return ob


def save(out, name):
    path = os.path.join(out, name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=False)
    return path


def fx_positive(out):
    reset()
    plate()
    return save(out, "positive")


def fx_nonmanifold(out):
    reset()
    ob = plate()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    victim = max(bm.faces, key=lambda f: f.calc_area())
    bmesh.ops.delete(bm, geom=[victim], context="FACES_ONLY")
    bm.to_mesh(ob.data)
    bm.free()
    return save(out, "nonmanifold")


def fx_wrongdim(out):
    reset()
    plate(length=44.0)
    return save(out, "wrongdim")


def fx_thinwall(out):
    reset()
    ob = plate()
    # 5 mm deep pocket in a hole-free strip: leaves a 1 mm floor.
    cut(ob, box("pocket", 36.0, 5.0, 5.0, at=(0.0, -6.5, 0.5)))
    return save(out, "thinwall")


def fx_missinghole(out):
    reset()
    plate(holes=[HOLES[0], HOLES[2]])
    return save(out, "missinghole")


def fx_unappliedscale(out):
    reset()
    ob = plate(scale_mm=0.5)
    ob.scale = (2.0, 2.0, 2.0)
    bpy.context.view_layer.update()
    return save(out, "unappliedscale")


def fx_calibration(out):
    """Known-diameter bores for the measurement falsification test."""
    reset()
    plate(length=60.0, width=24.0, thick=6.0,
          holes=[(-15.0, 0.0, 3.4), (15.0, 0.0, 5.0)], name=BRACKET)
    return save(out, "calibration")


def fx_selfintersect(out):
    """Two overlapping boxes welded into ONE mesh: must be flagged."""
    reset()
    ob = box(BRACKET, 40.0, 20.0, 6.0)
    other = box("other", 20.0, 20.0, 6.0, at=(10.0, 0.0, 2.0))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.from_mesh(other.data)
    bm.to_mesh(ob.data)
    bm.free()
    bpy.data.objects.remove(other, do_unlink=True)
    return save(out, "selfintersect")


def fx_torus(out):
    """Clean closed surface that must NOT be flagged as self-intersecting."""
    reset()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.020, minor_radius=0.005,
                                     major_segments=64, minor_segments=24)
    bpy.context.active_object.name = BRACKET
    bpy.context.active_object.data.name = BRACKET
    return save(out, "torus")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    made = [fn(args.out) for fn in (
        fx_positive, fx_nonmanifold, fx_wrongdim, fx_thinwall, fx_missinghole,
        fx_unappliedscale, fx_calibration, fx_selfintersect, fx_torus)]
    print("FIXTURES_OK " + ";".join(os.path.basename(p) for p in made))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

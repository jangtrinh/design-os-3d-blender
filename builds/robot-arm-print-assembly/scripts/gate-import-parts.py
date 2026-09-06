"""Import the 38 exported STL parts (mm) into one metre-scaled scene for gating."""
import bpy, csv, os, agent_runtime as rt
root = os.environ["ARM_ROOT"]; out = os.environ["PARTS_BLEND"]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
rows = list(csv.DictReader(open(os.path.join(root, "parts-list.csv"))))
for r in rows:
    before = set(bpy.data.objects)
    assert bpy.ops.wm.stl_import(filepath=os.path.join(root, r["STL"]), global_scale=0.001) == {'FINISHED'}
    ob = next(iter(set(bpy.data.objects) - before)); ob.name = r["ID"]
    ob.data.transform(ob.matrix_world); ob.matrix_world.identity()   # bake mm->m into mesh data
bpy.ops.wm.save_as_mainfile(filepath=out)
rt.emit_ok("import-parts", parts=len(rows), objects=len(bpy.data.objects))

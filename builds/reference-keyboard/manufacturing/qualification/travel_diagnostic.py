"""Identify actual full-stroke cap/cover interference before choosing a cap revision."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BUILD=HERE.parents[1]
sys.path[:0]=[str(BUILD/'scripts'),str(BUILD.parents[1]/'scripts')]
import bpy,bmesh
import controls
import inspect_fit as fit
from agent_runtime import emit_ok
from project import sha

assert bpy.app.background
source=Path(bpy.data.filepath);before=sha(source)
out=BUILD/'manufacturing/runs/travel-diagnostic-C01'
out.mkdir(parents=True,exist_ok=False)
cover=bpy.data.objects['RK_SWITCH_TOP_00']
key=bpy.data.objects['RK_KEY_00']


def overlap(obj,target):
    mod=obj.modifiers.new('DIAGNOSTIC_INTERSECT','BOOLEAN')
    mod.operation,mod.solver,mod.object='INTERSECT','EXACT',target
    graph=bpy.context.evaluated_depsgraph_get()
    me=bpy.data.meshes.new_from_object(obj.evaluated_get(graph),depsgraph=graph)
    bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
    volume=abs(bm.calc_volume(signed=True))*1e9 if bm.faces else 0
    zrange=None
    if bm.verts:
        zs=[(obj.matrix_world@v.co).z*1000 for v in bm.verts]
        zrange=[min(zs),max(zs)]
    result={'intersection_mm3':volume,'intersection_z_mm':zrange,'faces':len(bm.faces)}
    bm.free();bpy.data.meshes.remove(me);obj.modifiers.remove(mod)
    return result


rows=[]
for start_mm in (4.5,4.8,5.0,5.2):
    obj=controls.keycap('DIAGNOSTIC_'+str(start_mm),visible_skirt_bottom_m=start_mm/1000)
    obj.location=key.location.copy();obj.location.z-=.0032
    bpy.context.view_layer.update()
    detected,method=fit._intersects(fit._tri_mesh(obj),fit._tri_mesh(cover))
    row={'visible_skirt_start_mm':start_mm,'contact_detected':detected,'method':method}
    row.update(overlap(obj,cover));rows.append(row)
    mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
assert sha(source)==before
with (out/'diagnostic.json').open('x') as handle:
    json.dump({'scene_sha256':before,'travel_mm':3.2,'candidates':rows,
               'scope':'Temporary candidate probes only. No delivered geometry changed.'},handle,indent=2)
assert rows[0]['intersection_mm3']>0,'baseline did not reproduce a physical geometry intersection'
emit_ok('full-stroke-cap-diagnosis',candidates=len(rows),baseline_intersection_mm3=rows[0]['intersection_mm3'],
        collision_free_candidates=[r['visible_skirt_start_mm'] for r in rows if not r['contact_detected']])

"""Measure the reported staging fault against final-pose contact baselines."""
from pathlib import Path
import bpy,json,itertools
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
units=json.loads((ROOT/'reports/units.json').read_text())
selected=[u for u in units if u['group']=='shoulder' and u['kind']!='hardware' and u['installed_at']<=588]

def geometry(frame):
    sc.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    data={}
    for u in selected:
        vs=[];faces=[]
        for name in u['names']:
            ob=sc.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh();off=len(vs)
            vs.extend(ev.matrix_world@v.co for v in me.vertices)
            faces.extend(tuple(off+i for i in f.vertices) for f in me.polygons);ev.to_mesh_clear()
        data[u['id']]=(BVHTree.FromPolygons(vs,faces),vs)
    pairs={}
    for a,b in itertools.combinations(selected,2):
        if a['subassembly']==b['subassembly']:continue
        hits=data[a['id']][0].overlap(data[b['id']][0])
        if hits:pairs[a['id']+'|'+b['id']]={'a':a['names'],'b':b['names'],'hits':len(hits)}
    boxes={}
    for sub in {u['subassembly'] for u in selected}:
        pts=[world_to_camera_view(sc,sc.camera,p) for u in selected if u['subassembly']==sub for p in data[u['id']][1]]
        boxes[sub]=[min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)]
    return pairs,boxes

baseline,_=geometry(sc.frame_end);current,boxes=geometry(588)
new={k:v for k,v in current.items() if k not in baseline}
report={'frame':588,'baseline_pair_count':len(baseline),'current_cross_subassembly_pairs':current,
        'new_intersection_pairs':new,'projected_subassembly_boxes':boxes,
        'limits':'Surface intersections and projected boxes are diagnostic, not a complete solid/collision test.'}
(ROOT/'reports/overlap-before.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
fork_ids={u['id'] for u in selected if u['subassembly']=='fork'}
main_ids={u['id'] for u in selected if u['subassembly']=='main'}
waiting_clashes={k:v for k,v in current.items() if any(a in k and b in k for a in fork_ids for b in main_ids)}
assert not waiting_clashes,'REPRODUCED waiting fork intersects assembled servo before its seating event'

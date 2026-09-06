from pathlib import Path
import bpy,bmesh,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
source=bpy.data.scenes['A3-Frozen-source'];rows=[]
for i,o in enumerate(sorted((o for o in source.objects if o.get('part_type')=='print'),key=lambda o:o.name),1):
 bm=bmesh.new();bm.from_mesh(o.data)
 before={'verts':len(bm.verts),'faces':len(bm.faces),'bad_edges':sum(not e.is_manifold for e in bm.edges)}
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();bm.verts.index_update();bm.faces.index_update()
 seen=set();components=[]
 for v in bm.verts:
  if v.index in seen:continue
  stack=[v];seen.add(v.index);n=0
  while stack:
   at=stack.pop();n+=1
   for e in at.link_edges:
    nxt=e.other_vert(at)
    if nxt.index not in seen:seen.add(nxt.index);stack.append(nxt)
  components.append(n)
 bad=sum(not e.is_manifold for e in bm.edges);flip=sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
 volume=bm.calc_volume(signed=True)*1e9
 tree=BVHTree.FromBMesh(bm,epsilon=0.0);walls=[]
 for f in bm.faces:
  if f.calc_area()<.0000003:continue
  pt=f.calc_center_median();n=f.normal
  hit,hn,idx,d=tree.ray_cast(pt-n*1e-7,-n,.05)
  if hit is not None and hn.dot(n)<-.5:walls.append((d+1e-7)*1000)
 walls.sort();ext=[(max(v.co[k] for v in bm.verts)-min(v.co[k] for v in bm.verts))*1000 for k in range(3)]
 row={'id':f'P{i:02d}','object':o.name,'source':o['source_object'],'kind':'TPU' if 'TPU' in o.name else 'PETG','tool_library':bool(o.get('tool_library')),'before':before,'bad_edges':bad,'flipped_edges':flip,'components':components,'volume_mm3':volume,'dimensions_mm':ext,'wall_ray_samples':len(walls),'wall_min_mm':walls[0] if walls else None,'wall_p01_mm':walls[int(len(walls)*.01)] if walls else None,'status':'TOPOLOGY_PASS' if not bad and not flip and volume>0 else 'FAIL'}
 rows.append(row);bm.free()
report={'parts':rows,'units':'mm','limitations':'Wall ray screen uses face centroids area >=0.3mm2 and opposing normals; not an exhaustive thickness or strength proof. Source untouched.','failed':[r['id'] for r in rows if r['status']=='FAIL']}
(ROOT/'reports/mesh-audit.json').write_text(json.dumps(report,indent=2))
print('AGENT_OK',json.dumps({'count':len(rows),'failed':report['failed'],'multicomponent':[(r['id'],r['object'],r['components']) for r in rows if len(r['components'])>1],'walls':[(r['id'],round(r['wall_p01_mm'] or 0,3)) for r in rows]}))

"""Export native meshes in millimetres, explicitly as unreleased fit prototypes."""
from pathlib import Path
import bpy,bmesh,json,struct,hashlib
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent
folder=ROOT/'parts'/'UNRELEASED-fit-prototypes';folder.mkdir(parents=True,exist_ok=True)
rows=[]
for colname in ['A2-Printed','A2-Tools']:
 for ob in bpy.data.collections[colname].objects:
  if ob.type!='MESH' or ob.get('part_type')!='print':continue
  bm=bmesh.new();bm.from_mesh(ob.data)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  assert not any(not e.is_manifold for e in bm.edges),ob.name
  bm.to_mesh(ob.data);bm.free();ob.data.calc_loop_triangles()
  vs=[v.co.copy()*1000 for v in ob.data.vertices]
  ext=[max(v[k] for v in vs)-min(v[k] for v in vs) for k in range(3)]
  # Minimum dimension placed vertically, broadest support face is a slicing candidate.
  axis=min(range(3),key=lambda k:ext[k]);rot=Vector(tuple(int(k==axis) for k in range(3))).rotation_difference(Vector((0,0,1))).to_matrix()
  vs=[rot@v for v in vs];lo=Vector(tuple(min(v[k] for v in vs) for k in range(3)))
  vs=[v-lo for v in vs]
  out=bmesh.new();out.from_mesh(ob.data)
  out.verts.ensure_lookup_table()
  for i,v in enumerate(out.verts):v.co=vs[i]
  bmesh.ops.remove_doubles(out,verts=list(out.verts),dist=.00002)
  bmesh.ops.triangulate(out,faces=list(out.faces))
  bmesh.ops.dissolve_degenerate(out,edges=list(out.edges),dist=.00002)
  bmesh.ops.triangulate(out,faces=list(out.faces))
  bmesh.ops.recalc_face_normals(out,faces=list(out.faces))
  assert not any(not e.is_manifold for e in out.edges),ob.name
  tris=[tuple(v.co.copy() for v in f.verts) for f in out.faces]
  out.free()
  path=folder/(ob.name.removeprefix('A2-')+'.stl')
  with path.open('wb') as f:
   f.write(b'UNRELEASED FIT PROTOTYPE - millimetres'.ljust(80,b' '));f.write(struct.pack('<I',len(tris)))
   for tri in tris:
    a,b,c=tri;n=(b-a).cross(c-a).normalized()
    f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
  rows.append({'name':ob.name,'file':str(path.relative_to(ROOT)),'triangles':len(tris),
   'dimensions_mm':[max(v[k] for v in vs) for k in range(3)],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
   'material':ob.get('material','PETG'),'status':'UNRELEASED_FIT_PROTOTYPE'})
manifest={'status':'NOT_MANUFACTURING_APPROVED','units':'mm','parts':rows,
 'print_assumptions':'FDM 0.4mm nozzle, 0.2mm layers, PETG structural parts, TPU pads. Minimum6walls proposed; supports/orientation must be checked per part in slicer.',
 'prohibited_claim':'Watertight STL does not establish load capability, assembly fit or heat endurance.'}
(ROOT/'reports/print-prototype-manifest.json').write_text(json.dumps(manifest,indent=2))
print('AGENT_OK STL prototype export',len(rows),max(max(r['dimensions_mm']) for r in rows))

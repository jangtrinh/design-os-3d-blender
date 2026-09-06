"""Export core 3MF in mm from checked STL bytes; no slicer process or G-code."""
from pathlib import Path
import json,struct,zipfile,xml.etree.ElementTree as ET,hashlib,collections,math
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'reports/plates-manifest.json').read_text())
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS)
def node(parent,tag,**kw):return ET.SubElement(parent,'{'+NS+'}'+tag,kw)
def read_mesh(p):
 data=p.read_bytes();n=struct.unpack_from('<I',data,80)[0];assert len(data)==84+n*50
 verts=[];faces=[];seen={};edges=collections.Counter();volume=0
 for i in range(n):
  values=struct.unpack_from('<12fH',data,84+50*i);face=[]
  for j in [3,6,9]:
   xyz=tuple(values[j:j+3]);assert all(math.isfinite(v) for v in xyz)
   if xyz not in seen:seen[xyz]=len(verts);verts.append(xyz)
   face.append(seen[xyz])
  assert len(set(face))==3,(p,i)
  for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))]+=1
  a,b,c=[verts[k] for k in face];volume+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
  faces.append(face)
 assert all(v==2 for v in edges.values()),p
 assert volume>0,(p,'inverted volume')
 return verts,faces
meshes={}
for p in m['parts']:
 path=ROOT/p['stl'];assert hashlib.sha256(path.read_bytes()).hexdigest()==p['stl_sha256'];meshes[p['id']]=read_mesh(path)
results=[]
for i,pl in enumerate(m['plates'],1):
 model=ET.Element('{'+NS+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
 node(model,'metadata',name='Title').text=f'Arm plate {i:02d} - {pl["material"]} - FIT PROTOTYPE'
 res=node(model,'resources');build=node(model,'build');selected=[p for p in m['parts'] if p['plate']==i];alltris=[]
 for index,p in enumerate(selected,1):
  ob=node(res,'object',id=str(index),type='model',name=p['id']+' '+p['name']);mesh=node(ob,'mesh');vv=node(mesh,'vertices');tt=node(mesh,'triangles')
  verts,faces=meshes[p['id']];placed=[]
  for x,y,z in verts:
   if p['turn']:x,y=p['dims'][1]-y,x
   x+=p['xy'][0];y+=p['xy'][1];assert 6.99<=x<=213.01 and 6.99<=y<=213.01 and z>=-.001
   placed.append((x,y,z));node(vv,'vertex',x=repr(x),y=repr(y),z=repr(z))
  for a,b,c in faces:node(tt,'triangle',v1=str(a),v2=str(b),v3=str(c));alltris.append([placed[k] for k in [a,b,c]])
  node(build,'item',objectid=str(index))
 for a,p in enumerate(selected):
  x,y,xx,yy=p['placed_bounds_mm']
  for q in selected[a+1:]:
   X,Y,XX,YY=q['placed_bounds_mm'];assert xx+7.99<=X or XX+7.99<=x or yy+7.99<=Y or YY+7.99<=y,(p['id'],q['id'])
 path=ROOT/'plates'/f'plate-{i:02d}-{pl["material"]}.3mf'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
 with path.with_suffix('.stl').open('wb') as f:
  f.write(b'ARM PLATE | mm | fit prototype; not load approved'.ljust(80,b' '));f.write(struct.pack('<I',len(alltris)))
  for tri in alltris:
   a,b,c=tri;u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
   n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(q*q for q in n));assert length>0
   f.write(struct.pack('<12fH',*[q/length for q in n],*sum((list(v) for v in tri),[]),0))
 results.append({'plate':i,'material':pl['material'],'parts':[p['id'] for p in selected],'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':len(alltris)})
(ROOT/'reports/export-check.json').write_text(json.dumps({'status':'PASS_STL_CLOSED_EDGES_POSITIVE_VOLUME_AND_PLATE_BOUNDS','parts':len(meshes),'plates':results,'reference':'https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md','limits':'Core geometry package, no printer profile, supports, extrusion paths or G-code; not a physical-fit or load release.'},indent=2))
print('EXPORT_PASS',len(meshes),'pieces',len(results),'plates')

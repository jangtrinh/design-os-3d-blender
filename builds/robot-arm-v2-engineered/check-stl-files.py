"""Validate actual binary STL topology and hashes, without trusting source meshes."""
from pathlib import Path
import struct,collections,json,hashlib
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'reports/print-prototype-manifest.json').read_text());rows=[]
for row in manifest['parts']:
    p=ROOT/row['file'];data=p.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+n*50
    edges=collections.Counter()
    for i in range(n):
        vs=struct.unpack_from('<12fH',data,84+50*i)[3:12]
        pts=[tuple(vs[j:j+3]) for j in [0,3,6]]
        assert len(set(pts))==3,(p,'collapsed triangle')
        for a,b in [(pts[0],pts[1]),(pts[1],pts[2]),(pts[2],pts[0])]:edges[tuple(sorted([a,b]))]+=1
    bad=sum(v!=2 for v in edges.values());assert bad==0,(p,bad)
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    rows.append({'file':row['file'],'triangles':n,'nonmanifold_edges':bad})
(ROOT/'reports/stl-file-roundtrip.json').write_text(json.dumps({'count':len(rows),'status':'PASS_CLOSED_TRIANGLE_EDGE_COUNTS','files':rows},indent=2))
print('STL_BINARY_CLOSED',len(rows))

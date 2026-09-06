import bpy,bmesh,math,struct,hashlib
from mathutils import Vector,Matrix

def clean_mesh(ob):
 bm=bmesh.new();bm.from_mesh(ob.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 assert not any(not e.is_manifold for e in bm.edges),ob.name
 return bm

def orient(bm,ob):
 best=None
 for axis in range(3):
  for sign in [-1,1]:
   up=Vector(tuple(sign if k==axis else 0 for k in range(3)))
   rot=up.rotation_difference(Vector((0,0,1))).to_matrix()
   vv=[rot@v.co*1000 for v in bm.verts];lo=Vector(tuple(min(v[k] for v in vv) for k in range(3)));hi=Vector(tuple(max(v[k] for v in vv) for k in range(3)))
   bottom=overhang=0
   for f in bm.faces:
    n=rot@f.normal;z=(rot@f.calc_center_median()).z*1000-lo.z;area=f.calc_area()*1e6
    if z<.35 and n.z<-.7:bottom+=area
    elif z>.6 and n.z<-.707:overhang+=area
   ext=hi-lo
   score=ext.z*.6+overhang*.04-bottom*.08
   if 'U-body' in ob.name and axis!=0:score+=1000
   if best is None or score<best[0]:best=(score,rot,lo,ext,bottom,overhang,axis,sign)
 _,rot,lo,ext,bottom,overhang,axis,sign=best
 return rot,lo,ext,{'local_up_axis':axis,'local_up_sign':sign,'estimated_bed_contact_mm2':bottom,'downward_overhang_area_mm2':overhang,'support_review':overhang>10,'orientation_basis':'Six axis candidates: bed contact, low height, downward area. Fork broad bridge on bed; slicer support/strength review required.'}

def output_mesh(bm,rot,lo,name):
 for v in bm.verts:v.co=rot@v.co*1000-lo
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002)
 bmesh.ops.triangulate(bm,faces=list(bm.faces))
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00002)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 assert not any(not e.is_manifold for e in bm.edges),name
 me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.update();return me

def write_stl(path,me,offset=(0,0,0)):
 me.calc_loop_triangles();off=Vector(offset)
 with path.open('wb') as f:
  f.write(b'ARM FIT PROTOTYPE | millimetres | not load released'.ljust(80,b' '));f.write(struct.pack('<I',len(me.loop_triangles)))
  for t in me.loop_triangles:
   a,b,c=[me.vertices[i].co+off for i in t.vertices];n=(b-a).cross(c-a).normalized()
   f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
 return hashlib.sha256(path.read_bytes()).hexdigest()

def pack(parts,size=220,margin=7,gap=8):
 plates=[]
 for material in ['PETG','TPU']:
  for p in sorted([p for p in parts if p['material']==material],key=lambda p:-(p['dims'][0]*p['dims'][1])):
   choice=None
   for pi,pl in enumerate(plates):
    if pl['material']!=material:continue
    for x,y,w,h in pl['free']:
     for turn in [False,True]:
      dx,dy=p['dims'][int(turn)],p['dims'][int(not turn)]
      if dx+gap<=w+1e-5 and dy+gap<=h+1e-5:
       val=(min(w-dx-gap,h-dy-gap),w*h-dx*dy,pi,x,y,turn,dx,dy)
       if choice is None or val<choice:choice=val
   if choice is None:
    plates.append({'material':material,'free':[(margin,margin,size-2*margin+gap,size-2*margin+gap)],'parts':[]})
    pi=len(plates)-1;x=y=margin;turn=False;dx,dy=p['dims'][:2];assert max(dx,dy)<=size-2*margin
   else:_,_,pi,x,y,turn,dx,dy=choice
   pl=plates[pi];rx=x+dx+gap;ry=y+dy+gap;free=[]
   for fx,fy,fw,fh in pl['free']:
    fr,ft=fx+fw,fy+fh
    if rx<=fx or x>=fr or ry<=fy or y>=ft:free.append((fx,fy,fw,fh));continue
    if x>fx:free.append((fx,fy,x-fx,fh))
    if rx<fr:free.append((rx,fy,fr-rx,fh))
    if y>fy:free.append((fx,fy,fw,y-fy))
    if ry<ft:free.append((fx,ry,fw,ft-ry))
   free=list(dict.fromkeys(free));pl['free']=[a for a in free if not any(a!=b and a[0]>=b[0] and a[1]>=b[1] and a[0]+a[2]<=b[0]+b[2]+1e-6 and a[1]+a[3]<=b[1]+b[3]+1e-6 for b in free)]
   p.update(plate=pi+1,xy=[x,y],turn=turn,footprint=[dx,dy]);pl['parts'].append(p['id'])
 return plates

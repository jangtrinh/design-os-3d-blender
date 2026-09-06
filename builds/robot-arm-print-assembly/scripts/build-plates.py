from pathlib import Path
import bpy,json,runpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
g=runpy.run_path(str(ROOT/'scripts/plate-geometry.py'))
source=bpy.data.scenes['A3-Frozen-source'];audit=json.loads((ROOT/'reports/mesh-audit.json').read_text());parts=[]
assert not bpy.data.scenes.get('A3-Print-plates')
sc=bpy.data.scenes.new('A3-Print-plates');sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.world=source.world.copy();bpy.context.window.scene=sc
for row in audit['parts']:
 ob=source.objects[row['object']];bm=g['clean_mesh'](ob);rot,lo,ext,orientation=g['orient'](bm,ob)
 me=g['output_mesh'](bm,rot,lo,row['id']+'-mm');me.materials.clear()
 for m in ob.data.materials:me.materials.append(m)
 name=ob.name.removeprefix('A3-src-');path=ROOT/'parts'/f"{row['id']}-{name}.stl"
 sha=g['write_stl'](path,me)
 cp=bpy.data.objects.new('A3-'+row['id']+'-'+name,me);cp.scale=(.001,)*3
 cp['part_id']=row['id'];cp['source_object']=ob['source_object'];cp['part_type']='print';cp['release']='UNRELEASED FIT PROTOTYPE'
 sc.collection.objects.link(cp)
 parts.append({'id':row['id'],'name':name,'object':cp.name,'source':ob['source_object'],'material':row['kind'],'dims':list(ext),'stl':str(path.relative_to(ROOT)),'stl_sha256':sha,'orientation':orientation,'tool_library':row['tool_library'],'local_to_print':{'rotation':[list(r) for r in rot],'translation':list(-lo)}})
plates=g['pack'](parts)
for i,plate in enumerate(plates,1):
 col=bpy.data.collections.new(f'A3-Plate-{i:02d}-{plate["material"]}');sc.collection.children.link(col)
 origin=Vector(((i-1)%3*.25,(i-1)//3*.25,0));plate['display_origin_m']=list(origin)
 for p in [p for p in parts if p['plate']==i]:
  cp=sc.objects[p['object']];sc.collection.objects.unlink(cp);col.objects.link(cp)
  if p['turn']:
   for v in cp.data.vertices:x,y,z=v.co;v.co=(p['dims'][1]-y,x,z)
  cp.location=origin+Vector((*p['xy'],0))*.001
  p['placed_bounds_mm']=[*p['xy'],p['xy'][0]+p['footprint'][0],p['xy'][1]+p['footprint'][1]]
  assert p['placed_bounds_mm'][2]<=213.0001 and p['placed_bounds_mm'][3]<=213.0001
 plate.pop('free')
sc['release']='FIT PROTOTYPES; not load-approved';sc['bed_mm']=220
manifest={'source':json.loads((ROOT/'reports/source-freeze.json').read_text()),'bed_mm':[220,220],'gap_mm':8,'edge_margin_mm':7,'units':'mm','status':'UNRELEASED_FIT_PROTOTYPES','parts':parts,'plates':plates,'limits':['Supports and process require slicer review; geometric packing has no printer profile or G-code.','Topology/wall screen is not physical load/thermal/fit release.']}
(ROOT/'reports/plates-manifest.json').write_text(json.dumps(manifest,indent=2))
assert len(parts)==38 and len({p['id'] for p in parts})==38
bpy.data.libraries.write(str(ROOT/'arm-print-plates.blend'),{sc},fake_user=True,compress=True)
print('AGENT_OK',json.dumps({'parts':len(parts),'plates':[(i+1,p['material'],len(p['parts'])) for i,p in enumerate(plates)]}))

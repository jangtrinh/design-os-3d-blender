from pathlib import Path
import bpy,json,runpy
ROOT=Path(__file__).resolve().parents[1];h=runpy.run_path(str(ROOT/'scripts/studio-helpers.py'))
sc=bpy.data.scenes['A3-Print-plates'];bpy.context.window.scene=sc
assert not sc.camera,'Presentation already created'
m=json.loads((ROOT/'reports/plates-manifest.json').read_text())
plate=h['material']('A3-graphite-plate',(.032,.043,.055));ink=h['material']('A3-plate-ink',(.62,.72,.78));accent=h['material']('A3-plate-accent',(.05,.34,.42))
for i,pl in enumerate(m['plates'],1):
 x,y,_=pl['display_origin_m'];h['box'](sc,f'A3-build-plate-{i}',(.22,.22,.002),(x+.11,y+.11,-.0012),plate)
 h['text'](sc,f'A3-plate-label-{i}',f'{i:02d}  /  {pl["material"]}   /   220 mm',(x,y-.014,.001),.009,ink)
 for p in [p for p in m['parts'] if p['plate']==i]:
  px,py=p['xy'];h['text'](sc,'A3-ID-'+p['id'],p['id'],(x+px*.001,y+py*.001-.004,.0002),.0035,ink)
 for k in range(1,22):
  q=k*.01
  h['box'](sc,f'A3-grid-{i}-x{k}',(.00012,.22,.00005),(x+q,y+.11,-.00015),accent)
  h['box'](sc,f'A3-grid-{i}-y{k}',(.22,.00012,.00005),(x+.11,y+q,-.00015),accent)
h['camera'](sc,(.36,.225,1.5),(.36,.225,0),.80);h['lighting'](sc)
sc.render.resolution_x=1440;sc.render.resolution_y=1000
sc.render.filepath=str(ROOT/'renders/plates-overview.png')
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.data.libraries.write(str(ROOT/'arm-print-plates.blend'),{sc},fake_user=True,compress=True)
print('AGENT_OK plate presentation',len(sc.objects))

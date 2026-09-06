from pathlib import Path
import bpy,json,hashlib
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
assert bpy.context.mode=='OBJECT'
assert not bpy.data.scenes.get('A3-Frozen-source'), 'Source already frozen; inspect existing state'
assert bpy.data.filepath.endswith('arm-v2-task-demo.blend')
checkpoint=ROOT/'source-session-checkpoint.blend'
assert not checkpoint.exists(), 'Preserve existing checkpoint'
assert bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint),copy=True,compress=True)=={'FINISHED'}
source=bpy.data.scenes['ARM2-Task-demo'];old=bpy.context.window.scene;frame=source.frame_current
sc=bpy.data.scenes.new('A3-Frozen-source');sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.world=source.world.copy();mapping=[]
try:
 bpy.context.window.scene=source;source.frame_set(1);bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get()
 selected=[o for o in source.objects if o.type=='MESH' and o.get('part_type')]
 for o in selected:
  ev=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev,depsgraph=dg)
  cp=bpy.data.objects.new(o.name.removesuffix('-task').replace('A2-','A3-src-',1),me)
  cp.matrix_world=o.matrix_world.copy();sc.collection.objects.link(cp)
  for k,v in o.items():cp[k]=v
  cp['source_object']=o.name;cp['source_parent']=o.parent.name if o.parent else '';cp['tool_library']=False
  mapping.append({'source':o.name,'frozen':cp.name,'kind':o.get('part_type')})
 lib=bpy.data.scenes['ARM2-Tool-library'];bpy.context.window.scene=lib;dg=bpy.context.evaluated_depsgraph_get()
 for o in lib.objects:
  if o.type!='MESH' or o.get('part_type')!='print':continue
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
  cp=bpy.data.objects.new(o.name.replace('A2-','A3-src-',1),me);cp.matrix_world=o.matrix_world.copy();sc.collection.objects.link(cp)
  for k,v in o.items():cp[k]=v
  cp['source_object']=o.name;cp['source_parent']=o.parent.name if o.parent else '';cp['tool_library']=True
  mapping.append({'source':o.name,'frozen':cp.name,'kind':'print','tool_library':True})
finally:
 source.frame_set(frame);bpy.context.window.scene=old
assert Counter(x['kind'] for x in mapping)['print']==38
sc['source_file']=str(checkpoint);sc['source_frame']=1;sc['release']='UNRELEASED FIT PROTOTYPE'
bpy.data.libraries.write(str(ROOT/'frozen-source.blend'),{sc},fake_user=True,compress=True)
report={'version':bpy.app.version_string,'controller':'root','source_file':str(checkpoint),'source_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),'frozen_sha256':hashlib.sha256((ROOT/'frozen-source.blend').read_bytes()).hexdigest(),'counts':dict(Counter(x['kind'] for x in mapping)),'objects':mapping}
(ROOT/'reports/source-freeze.json').write_text(json.dumps(report,indent=2));print('AGENT_OK',report['counts'])

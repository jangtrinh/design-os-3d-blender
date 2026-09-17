"""Export an explicitly selected product, with one scene animation and embedded RGB."""
from pathlib import Path
import sys
import json
import struct
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import BUILD,ROOT,output_context,write,sha,spec_path,contract_path
import bpy
from agent_runtime import emit_ok
from export_compare import capture_source
from boilerplates.bp_parametric_contract import bind_export_evidence

assert bpy.app.background
out,inputs=output_context()
sources=[p for k,p in inputs['project'].items() if k.endswith('/keyboard.blend')]
assert len(sources)==1,'declare exactly one saved keyboard scene'
source=sources[0]
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
bpy.context.scene.frame_set(1)
names=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('RK_'))
surface=capture_source(names,(1,7,60))
surface['blend_sha256']=sha(source)
write(out/'source-surfaces.json',surface)
for obj in bpy.context.scene.objects:
    obj.select_set(obj.name in names or obj.name.startswith('ASSEMBLY_'))
bpy.context.view_layer.objects.active=bpy.data.objects['RK_BASE']
rna=bpy.ops.export_scene.gltf.get_rna_type().properties
assert 'export_animation_mode' in rna
modes={i.identifier for i in rna['export_animation_mode'].enum_items}
assert 'SCENE' in modes,sorted(modes)
settings={'filepath':str(out/'keyboard.glb'),'export_format':'GLB','use_selection':True,
          'use_active_scene':True,
          'export_apply':True,'export_animations':True,'export_frame_range':True,
          'export_animation_mode':'SCENE','export_force_sampling':True,'export_frame_step':1,
          'export_extras':True,'export_yup':True}
for name,value in [('export_anim_slide_to_zero',False),('export_anim_scene_split_object',False),('export_bake_animation',True)]:
    if name in rna: settings[name]=value
assert all(k in rna for k in settings),sorted(set(settings)-set(rna.keys()))
assert bpy.ops.export_scene.gltf(**settings)=={'FINISHED'}
raw=(out/'keyboard.glb').read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
n,kind=struct.unpack_from('<I4s',raw,12)
assert kind==b'JSON'
doc=json.loads(raw[20:20+n])
assert len(doc.get('animations',[]))==1,'expected one merged scene animation'
assert doc.get('images') and all('bufferView' in image for image in doc['images']),'RGB texture must be embedded'
assert sum('mesh' in node for node in doc['nodes'])==len(names)
write(out/'export-settings.json',{'settings':settings,'blend_sha256':sha(source),'glb_sha256':sha(out/'keyboard.glb'),
                                 'meshes':len(names),'animations':len(doc['animations']),
                                 'embedded_images':len(doc['images']),'extensions':doc.get('extensionsUsed',[])})
contract=json.loads(contract_path().read_text())
write(out/'export-evidence.json',bind_export_evidence(contract,[out/'keyboard.glb'],ROOT,
                                                     scene_sha256=sha(source),spec_sha256=sha(spec_path())))
emit_ok('reference-keyboard-export',meshes=len(names),source_frames=3,animations=len(doc['animations']),
        glb_bytes=len(raw),embedded_images=len(doc['images']))

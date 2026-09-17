"""Full HD inspection sheet of the actual gated specimen meshes."""
import json
from pathlib import Path
import struct
import sys
HERE=Path(__file__).resolve().parent
BUILD=HERE.parents[1]
sys.path[:0]=[str(BUILD/'scripts'),str(BUILD.parents[1]/'scripts')]
from project import output_context,write,sha
from agent_verify import framing
from agent_runtime import emit_ok
import bpy
import studio,fullhd

assert bpy.app.background
out,inputs=output_context()
source=inputs['artifacts']['build:specimens.blend']
gate=json.loads(Path(inputs['artifacts']['gate:gate-report.json']).read_text())
assert gate['inputs']['scene_sha256']==sha(source) and not gate['failed'] and not gate['required_checks_missing']
assert bpy.ops.wm.open_mainfile(filepath=source)=={'FINISHED'}
studio.setup()
settings=fullhd.renderer()
bpy.context.scene.cycles.samples=32
mat=studio.material('Process specimens',(.055,.22,.27),0,.45)
ink=studio.material('Specimen labels',(.015,.015,.015),0,.7)
proof=[o for o in bpy.context.scene.objects if o.name.startswith('PROOF_')]
for obj in proof:
    obj.data.materials.clear(); obj.data.materials.append(mat)
    text=bpy.data.curves.new('Label_'+obj.name,'FONT')
    text.body=obj.name.removeprefix('PROOF_');text.size=.003;text.align_x='CENTER'
    label=bpy.data.objects.new(text.name,text)
    bpy.context.scene.collection.objects.link(label)
    label.location=(obj.location.x,obj.location.y-.011,.0001)
    text.materials.append(ink)
context=studio.aim(location=(.115,-.14,.20),target=(.036,.033,.004),scale=.215)
assert all(framing(o)['in_frame'] for o in proof)
path=out/'specimen-set-FullHD.png'
bpy.context.scene.render.filepath=str(path)
assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
assert struct.unpack('>II',path.read_bytes()[16:24])==(1920,1080)
write(out/'view.json',{'source_sha256':sha(source),'image_sha256':sha(path),
                     'settings':settings,'camera':context,'purpose':'Process specimen identification, not physical test evidence'})
emit_ok('manufacturing-specimen-sheet',specimens=len(proof),width=1920,height=1080)

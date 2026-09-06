"""Screen actual keyed arm and payload poses, including pickup/stack supports."""
from pathlib import Path
import os,time,json,bpy
ROOT=Path(__file__).resolve().parent
os.environ['ARM_CONTACT_SCENE']='ARM2-Task-demo';os.environ['ARM_CONTACT_SUFFIX']='-task'
exec(compile((ROOT/'flexibility-contact-lib.py').read_text(),str(ROOT/'flexibility-contact-lib.py'),'exec'))
step=int(os.environ.get('ARM_FRAME_STEP','1'));failures=[];permitted=[];checked=0;t=time.time()
for frame in range(1,721):
    if (frame-1)%step and frame!=720:continue
    sc.frame_set(frame);bpy.context.view_layer.update();hits=contacts();bad=[]
    for pair in hits:
        # TPU is intentionally compliant at the20mm workpiece faces; rigid parts are never excused.
        if any(n.startswith('Task-payload-') for n in [pair['a'],pair['b']]) and any('TPU-pad-72' in n for n in [pair['a'],pair['b']]):
            permitted.append({'frame':frame,**pair})
        else:bad.append(pair)
    minz=min((o.matrix_world@Vector(v)).z for o in meshes for v in o.bound_box)*1000
    if bad or minz<-.05:
        failures.append({'frame':frame,'hits':bad,'min_z_mm':minz});print('TASK_CONTACT',frame,bad,flush=True)
    checked+=1
    if checked%40==0:print('TASK_CHECKED',checked,round(time.time()-t,1),flush=True)
report={'status':'PASS_SCREEN' if not failures else 'REQUIRES_REFINEMENT','frames_checked':checked,'frame_step':step,
    'cross_group_pairs':len(pairs),'failures':failures,'permitted_pad_contacts':permitted,
    'scope':'Sampled triangle surface screen including keyed payload and stands; excludes same-rigid-group/internal servo proxies and permits payload/TPU72 contact. Not force, friction, solid-containment or continuous swept-volume proof.'}
(ROOT/'reports'/('task-path-check.json' if step==1 else 'task-path-coarse.json')).write_text(json.dumps(report,indent=2))
print('AGENT_OK task screen',report['status'],checked,len(failures),flush=True)

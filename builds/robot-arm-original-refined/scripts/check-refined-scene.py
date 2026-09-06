"""Numeric preflight before visual rendering; placement does not prove hardware fit."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.data.scenes['A5-Original-refined'];bpy.context.window.scene=sc
rows=json.loads((ROOT/'reports/source-map.json').read_text())['objects']
units={u['id']:u for u in json.loads((ROOT/'reports/units.json').read_text())}
timing=json.loads((ROOT/'reports/timing.json').read_text())
sc.frame_set(sc.frame_end);bpy.context.view_layer.update()
error=max(abs(sc.objects[r['candidate']].matrix_world[i][j]-r['final_matrix'][i][j]) for r in rows for i in range(4) for j in range(4))
assert len(rows)==402 and error<1e-6,error
bad=[];held=[]
for e in timing['events']:
    if e['type']=='camera-transition':continue
    poses=[]
    for frame in (e['start'],(e['start']+e['end'])//2,e['end']):
        sc.frame_set(frame);bpy.context.view_layer.update()
        poses.append(tuple(sc.camera.location)+(sc.camera.data.ortho_scale,)+tuple(sc.camera.rotation_quaternion))
    assert poses[0]==poses[1]==poses[2],e
    held.append(e['group_index'])
    if 'units' in e:
        for unit in e['units']:
            for name in units[unit]['names']:
                ob=sc.objects[name]
                for vertex in ob.bound_box:
                    p=world_to_camera_view(sc,sc.camera,ob.matrix_world@Vector(vertex))
                    if not (0<=p.x<=1 and 0<=p.y<=1 and p.z>0):
                        bad.append({'event':e['group_index'],'frame':e['end'],'object':name,'xy':list(p)});break
assert not bad,bad[:5]
assert len([o for o in sc.objects if o.name.startswith('A5-wire-')])==6
assert not sc.objects.get('A5-external-supply')
report={'status':'PASS','source_meshes':len(rows),'final_matrix_error':error,'held_event_count':len(held),
        'camera_transitions':sum(e['type']=='camera-transition' for e in timing['events']),
        'bad_arrival_endpoints':bad,'frames':timing['frames'],'fps':24,'six_servo_wires':True,'external_black_box':False,
        'limits':'Camera samples at start/mid/end; insertion, retention and physical performance unverified.',
        'scene_sha256':hashlib.sha256((ROOT/'arm-original-refined.blend').read_bytes()).hexdigest()}
(ROOT/'reports/scene-check.json').write_text(json.dumps(report,indent=2))
sc.frame_set(sc.frame_end)
print('REFINED_SCENE_PASS',json.dumps(report))

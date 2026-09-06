"""Original viewing direction; camera only moves in named transition windows."""
from pathlib import Path
import bpy, json, runpy
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
L = runpy.run_path(str(ROOT/'scripts/motion-lib.py'))
sc = bpy.context.scene
assert sc.name == 'A5-Original-refined'
timing = json.loads((ROOT/'reports/timing.json').read_text())
units = json.loads((ROOT/'reports/units.json').read_text())
cam = sc.camera
cam.animation_data_clear(); cam.data.animation_data_clear()
direction = Vector((.55,-1,.60)).normalized()
q = (-direction).to_track_quat('-Z','Y')
inv = q.inverted()

def points(rows, station=False):
    result = []
    for u in rows:
        at = Vector(u['center'])
        if station:
            at += Vector(u['offset'])+Vector(u['sub_offset'])
        extent = Vector(u['extent'])
        result.extend(inv@(at+Vector((x*extent.x,y*extent.y,z*extent.z)))
                      for x in (-.5,.5) for y in (-.5,.5) for z in (-.5,.5))
    return result

def fit(pts,minimum=.25):
    low = Vector(tuple(min(p[k] for p in pts) for k in range(3)))
    high = Vector(tuple(max(p[k] for p in pts) for k in range(3)))
    return {'focus':list(q@((low+high)/2)), 'scale':max(minimum,(high.x-low.x)*1.28,(high.y-low.y)*4/3*1.28)}

station = points([u for u in units if u['group'] in ('shoulder','elbow','wrist','hand')],True)
# Include the swept fork clearance envelope in the stationary camera fit.
for u in units:
    if u['group'] in ('shoulder','elbow') and u['subassembly']=='fork':
        for remote in (True,False):
            v=dict(u);v['center']=list(Vector(u['center'])+Vector((0,0,.120)))
            if not remote:v['sub_offset']=[0,0,0]
            station.extend(points([v],True))
final = points(units)
cpu = [u for u in units if any(s in n for n in u['original_names'] for s in ('electronics','controller','service-connector'))]
base = [u for u in units if u['group']=='base']+[u for u in cpu if 'shell' in u['original_names'][0]]
presets = {'base':fit(points(base),.29),'station':fit(station,.34),'wide':fit(final+station),
           'cpu':fit(points(cpu),.19),'hero':fit(final,.545754611492157)}
presets['station']['scale'] *= 1.13/1.28
original = json.loads((ROOT.parent/'robot-arm-print-assembly/reports/assembly-timeline.json').read_text())
presets['hero'] = {'focus':original['full_center'], 'scale':max(original['full_size'])*1.68*1.08}
cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
transitions = [e for e in timing['events'] if e['type']=='camera-transition']
shot = 'base'
for frame in range(1,timing['frames']+1):
    active = next((e for e in transitions if e['start']<=frame<=e['end']),None)
    if active:
        a,b = presets[active['from']],presets[active['to']]
        t = L['smooth']((frame-active['start'])/(active['end']-active['start']))
        focus = Vector(a['focus']).lerp(Vector(b['focus']),t)
        scale = a['scale']*(1-t)+b['scale']*t
        shot = active['to']
    else:
        focus = Vector(presets[shot]['focus']);scale = presets[shot]['scale']
    cam.location = focus+direction*1.6;cam.data.ortho_scale = scale
    cam.keyframe_insert('location',frame=frame);cam.data.keyframe_insert('ortho_scale',frame=frame)
L['linear_keys'](cam);L['linear_keys'](cam.data)
sc.frame_start=1;sc.frame_end=timing['frames'];sc.render.fps=24
(ROOT/'reports/camera-presets.json').write_text(json.dumps({'presets':presets,'direction':list(direction),'rotation':list(q)},indent=2))
print('HELD_CAMERA_PASS',len(transitions),'explicit transitions',presets)

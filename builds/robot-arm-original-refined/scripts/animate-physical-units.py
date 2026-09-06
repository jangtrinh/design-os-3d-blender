"""Assemble reviewed units while leaving the camera fixed at its receiver."""
from pathlib import Path
import bpy, json, runpy
from mathutils import Vector, Quaternion
ROOT = Path(__file__).resolve().parents[1]
L = runpy.run_path(str(ROOT/'scripts/motion-lib.py'))
sc = bpy.context.scene
assert sc.name == 'A5-Original-refined'
units = json.loads((ROOT/'reports/units.json').read_text())
timing = json.loads((ROOT/'reports/timing.json').read_text())
cam = json.loads((ROOT/'reports/camera-presets.json').read_text())
right = Quaternion(cam['rotation']) @ Vector((1,0,0))
lookup = {u['id']:u for u in units}
placed = {};group_offsets = {u['group']:Vector(u['offset']) for u in units}
sub_offsets = {(u['group'],u['subassembly']):Vector(u['sub_offset']) for u in units}
for u in units:
    sc.objects[u['id']].animation_data_clear()
    for name in u['names']:
        ob=sc.objects[name];ob.animation_data_clear();ob.hide_render=ob.hide_viewport=True
        ob.keyframe_insert('hide_render',frame=1);ob.keyframe_insert('hide_viewport',frame=1)
for e in timing['events']:
    if e['type'] == 'install':
        scale = cam['presets'][e['shot']]['scale']
        for index,key in enumerate(e['units']):
            u = lookup[key];root = sc.objects[key]
            end = Vector(u['center'])+group_offsets[u['group']]+sub_offsets[(u['group'],u['subassembly'])]
            start = end+right*((-1 if index%2 else 1)*(scale+max(u['extent'])))
            if u['group'] in ('shoulder','elbow'):
                sub=u['subassembly']
                if sub=='fork':start=end+right*(scale+max(u['extent']))
                elif sub.startswith('carrier-'):
                    start=end+Vector((0,(-1 if sub.endswith('left') else 1)*scale,0))
            root.location = start;root.keyframe_insert('location',frame=1)
            for name in u['names']:
                ob = sc.objects[name]
                for frame,hidden in ((e['start']-1,True),(e['start'],False)):
                    if frame < 1:continue
                    ob.hide_render=ob.hide_viewport=hidden
                    ob.keyframe_insert('hide_render',frame=frame);ob.keyframe_insert('hide_viewport',frame=frame)
            L['move'](root,start,end,e['start'],e['end']-e['start'])
            placed[key]=end;u['arrival_start']=list(start);u['arrival_end']=list(end)
    elif e['type'].startswith('seat-'):
        whole = e['type']=='seat-module'
        for key in e['units']:
            u=lookup[key];tag=(u['group'],u['subassembly'])
            delta = -group_offsets[u['group']] if whole else -sub_offsets[tag]
            end=placed[key]+delta
            if not whole and u['subassembly']=='fork':
                lift=Vector((0,0,.120));span=(e['end']-e['start'])//3
                L['move'](sc.objects[key],placed[key],placed[key]+lift,e['start'],span)
                L['move'](sc.objects[key],placed[key]+lift,end+lift,e['start']+span,span)
                L['move'](sc.objects[key],end+lift,end,e['start']+2*span,span)
            else:
                L['move'](sc.objects[key],placed[key],end,e['start'],e['end']-e['start'])
            placed[key]=end
        if whole:group_offsets[e['module']]=Vector()
        else:
            for key in e['units']:
                u=lookup[key];sub_offsets[(u['group'],u['subassembly'])]=Vector()
for u in units:
    L['linear_keys'](sc.objects[u['id']])
    for name in u['names']:L['linear_keys'](sc.objects[name])
sc.frame_set(sc.frame_end);bpy.context.view_layer.update()
assert len(placed)==252
assert max((placed[u['id']]-Vector(u['center'])).length for u in units)<1e-6
(ROOT/'reports/units.json').write_text(json.dumps(units,indent=2))
print('UNIT_MOTION_PASS',len(placed),sc.frame_end)

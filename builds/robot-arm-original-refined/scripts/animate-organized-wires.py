"""Route six servo leads from the enclosed rear controller before cover closure."""
from pathlib import Path
import bpy, json, runpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
L=runpy.run_path(str(ROOT/'scripts/motion-lib.py'))
sc=bpy.context.scene
assert sc.name=='A5-Original-refined'
timing=json.loads((ROOT/'reports/timing.json').read_text())
wires={w['object']:w for w in json.loads((ROOT/'reports/native-wires.json').read_text())}
for e in timing['events']:
    if e['type']!='wire':continue
    ob=sc.objects[e['object']];ob.data.animation_data_clear();ob.animation_data_clear()
    points=ob.data.splines[0].points;path=[Vector(p) for p in wires[ob.name]['points']]
    for p in points:p.co=(*path[0],1);p.keyframe_insert('co',frame=1)
    ob.hide_render=ob.hide_viewport=False
    for f in range(e['start'],e['end']+1):
        position=L['smooth']((f-e['start'])/(e['end']-e['start']))*(len(path)-1)
        j=min(int(position),len(path)-2);tip=path[j].lerp(path[j+1],position-j)
        for i,p in enumerate(points):
            co=path[i] if i<=position else tip;p.co=(*co,1);p.keyframe_insert('co',frame=f)
    L['linear_keys'](ob.data)
sc.frame_set(sc.frame_end);bpy.context.view_layer.update()
assert not sc.objects.get('A5-external-supply') and not sc.objects.get('A5-wire-power-in')
sc['camera_review_status']='Candidate based on owner-selected original film'
bpy.data.libraries.write(str(ROOT/'arm-original-refined.blend'),{sc},fake_user=True,compress=True)
print('WIRE_AND_SCENE_PASS',len(wires),sc.frame_end)

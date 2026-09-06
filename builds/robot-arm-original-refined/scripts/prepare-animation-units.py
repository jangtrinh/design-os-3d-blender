"""Keep physical purchased assemblies and screw pairs rigid through installation."""
from pathlib import Path
import bpy, json, runpy
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[1]
L = runpy.run_path(str(ROOT/'scripts/motion-lib.py'))
sc = bpy.context.scene
assert sc.name == 'A5-Original-refined'
rows = json.loads((ROOT/'reports/source-map.json').read_text())['objects']
by_source = {r['source']: sc.objects[r['candidate']] for r in rows}
prior = json.loads((ROOT.parent/'robot-arm-assembly-guide/reports/mechanical-review/suggested-sequence.json').read_text())
old = json.loads((ROOT.parent/'robot-arm-print-assembly/reports/assembly-timeline.json').read_text())
offsets = {c['group']: Vector(c['offset']) for c in old['chapters']}
offsets['electronics'] = Vector()
sub_offsets = {'main': Vector(), 'mount-left': Vector((0,-.020,0)),
 'mount-right': Vector((0,.020,0)), 'carrier-left': Vector((0,-.025,0)),
 'carrier-right': Vector((0,.025,0)), 'fork': Vector((0,0,.025))}
units = []
for op in prior['operations']:
    if op['type'] != 'install':
        continue
    obs = [by_source[n] for n in op['names']]
    lo, hi = L['bounds'](obs)
    center = (lo+hi)/2
    root = L['empty'](sc, f'A5-unit-{len(units)+1:03d}')
    root.location = center
    for ob in obs:
        final = ob.matrix_world.copy()
        ob.animation_data_clear()
        ob.parent = root
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = Matrix.Translation(-center) @ final
        ob.hide_render = ob.hide_viewport = True
        ob.keyframe_insert('hide_render',frame=1)
        ob.keyframe_insert('hide_viewport',frame=1)
    group = op['group']
    sub = op.get('subassembly','main')
    units.append({'id':root.name,'names':[o.name for o in obs],
      'original_names':[o['original_build_name'] for o in obs],
      'group':group,'subassembly':sub,'center':list(center),'extent':list(hi-lo),
      'offset':list(offsets[group]),'sub_offset':list(sub_offsets[sub]),
      'kind':obs[0].get('part_type'),'installed':False})
assert len(units)==252 and sum(len(u['names']) for u in units)==402
(ROOT/'reports/units.json').write_text(json.dumps(units,indent=2))
runpy.run_path(str(ROOT/'scripts/repair-staging-layout.py'))
print('PHYSICAL_UNITS_PASS',len(units))

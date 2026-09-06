"""Compile reviewed physical groups into held shots and explicit transitions."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
groups = json.loads((ROOT/'reports/independent-review/grouped-sequence.json').read_text())['groups']
# Seat the preloaded fork before either closed carrier can obstruct its path.
for seat, before in ((25,22),(47,44)):
    item = next(g for g in groups if g['index']==seat)
    groups.remove(item)
    groups.insert(next(i for i,g in enumerate(groups) if g['index']==before),item)
units = json.loads((ROOT/'reports/units.json').read_text())
clock = 1
events = []
shot = 'base'
seated = set()
installed = set()
introduced = set()
sub_seats = {14:['mount-left','mount-right'],23:['carrier-left'],25:['fork'],27:['carrier-right'],
             36:['mount-left','mount-right'],45:['carrier-left'],47:['fork'],49:['carrier-right']}


def change_shot(target):
    global clock, shot
    if target == shot:
        return
    events.append({'type':'camera-transition','start':clock,'end':clock+36,'from':shot,'to':target})
    clock += 40
    shot = target


def event(kind, duration, **fields):
    global clock
    item = {'type':kind,'start':clock,'end':clock+duration,'shot':shot,**fields}
    events.append(item)
    clock += duration+4
    return item


for group in groups:
    module = group['module']
    number = group['index']
    operation = group['operation']
    desired = 'wide' if module in seated or module=='finish' else 'base' if module=='base' else 'cpu' if module=='electronics' else 'station'
    if module in {'shoulder','elbow','wrist','hand'} and module not in introduced and operation=='install':
        desired='wide'
        introduced.add(module)
    if operation == 'unmodeled-gate':
        change_shot('wide')
        wires = json.loads((ROOT/'reports/native-wires.json').read_text())
        for wire in wires:
            event('wire',24,object=wire['object'],group_index=number,module=module)
        continue
    if operation == 'seat-module':
        change_shot('wide')
        chosen = [u for u in units if u['id'] in installed and u['group']==module]
        event('seat-module',36,units=[u['id'] for u in chosen],module=module,group_index=number)
        seated.add(module)
        continue
    change_shot(desired)
    if operation.startswith('seat-subassembl'):
        chosen = [u for u in units if u['id'] in installed and u['group']==module and u['subassembly'] in sub_seats[number]]
        assert chosen, number
        event('seat-subassembly',72 if 'fork' in sub_seats[number] else 24,units=[u['id'] for u in chosen],module=module,group_index=number)
        continue
    names = set(group['names'])
    selected = [u for u in units if set(u['original_names']) <= names]
    assert set(n for u in selected for n in u['original_names']) == names, number
    kinds = list(dict.fromkeys(u['kind'] for u in selected))
    for kind in kinds:
        chosen = [u for u in selected if u['kind']==kind]
        duration = 14 if kind=='hardware' else 18
        step = event('install',duration,units=[u['id'] for u in chosen],module=module,
                     group_index=number,title=group['title'],flags=group['flags'])
        for u in chosen:
            assert u['id'] not in installed
            installed.add(u['id'])
            u['installed_at'] = step['end']
            u['group_index'] = number
assert len(installed)==252
change_shot('hero')
end = clock+48
(ROOT/'reports/timing.json').write_text(json.dumps({'events':events,'frames':end,'fps':24,
    'reviewed_groups':len(groups),'source_units':252,'camera_transition_frames':36,
    'camera_policy':'Fixed camera throughout each install, subassembly seat, module transfer and wiring; explicit transitions only.'},indent=2))
(ROOT/'reports/units.json').write_text(json.dumps(units,indent=2))
print('TIMING_PASS',len(events),end,round(end/24,2),'seconds')

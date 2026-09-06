"""Gate the measured assembly path without approving simplified mating geometry."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
measured=json.loads((ROOT/'reports/independent-review/overlap-repair-check.json').read_text())
scene_hash=hashlib.sha256((ROOT/'arm-original-refined.blend').read_bytes()).hexdigest()
assert measured['artifact_sha256']==scene_hash,'Sweep report is stale'
assert all(not state['pairs'] for state in measured['waiting'])
for sweep in measured['sweeps']:
    for pair in sweep['pairs']:
        assert pair['classification']!='actuator-case',pair
        if sweep['subassembly']=='fork':
            assert 'drive-flange' in pair['moving'] and '-output-' in pair['fixed'],pair
        else:
            assert 'bearing-carrier' in pair['moving'] and 'cradle-floor' in pair['fixed'],pair
            assert pair['last']==sweep['frames'][1] and pair['first']>=sweep['frames'][1]-5,pair
result={'status':'PASS_VISUAL_ASSEMBLY_PATH','scene_sha256':scene_hash,
        'real_servo_case_collisions':0,'waiting_cross_pairs':0,
        'limits':'Output visual mates and final carrier-floor contacts remain; hardware, fit and manufacturability not approved.'}
(ROOT/'reports/clearance-acceptance.json').write_text(json.dumps(result,indent=2))
print('CLEARANCE_ACCEPTANCE_PASS',scene_hash)

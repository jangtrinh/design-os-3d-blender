"""Keep preassembled servo visual components rigid during their arrival."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
scene = bpy.data.scenes['A3-Step-assembly']
bpy.context.window.scene = scene
timeline = json.loads((ROOT/'reports/assembly-timeline.json').read_text())
rows = {r['object']: r for r in timeline['objects']}
groups = {'yaw': ['--1'], 'shoulder': ['--1', '-1'],
          'elbow': ['--1', '-1'], 'roll': ['--1', '-1'],
          'gripper': ['--1', '-1']}
members = [f'A3-build-{joint}-output{side}' for joint, sides in groups.items() for side in sides]
before = {}
for frame in range(scene.frame_start, scene.frame_end+1):
    scene.frame_set(frame)
    before[frame] = {n: scene.objects[n].location.copy() for n in members}
changed = set()
for joint, sides in groups.items():
    owner = scene.objects[f'A3-build-{joint}-servo']
    row = rows[owner.name]
    scene.frame_set(row['start'])
    delta = owner.location - Vector([row['final_matrix'][i][3] for i in range(3)])
    for side in sides:
        ob = scene.objects[f'A3-build-{joint}-output{side}']
        other = rows[ob.name]
        assert (row['start'], row['end']) == (other['start'], other['end'])
        final = Vector([other['final_matrix'][i][3] for i in range(3)])
        ob.location = final + delta
        ob.keyframe_insert('location', frame=row['start'])
        ob.location = final
        ob.keyframe_insert('location', frame=row['end'])
for frame in range(scene.frame_start, scene.frame_end+1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for n in members:
        if not scene.objects[n].hide_render and (scene.objects[n].location-before[frame][n]).length > 1e-8:
            changed.add(frame)
            assert rows[n]['start'] <= frame <= rows[n]['end'], (n, frame)
    for joint, sides in groups.items():
        owner = scene.objects[f'A3-build-{joint}-servo']
        row = rows[owner.name]
        if row['start'] <= frame <= row['end']:
            delta = owner.location-Vector([row['final_matrix'][i][3] for i in range(3)])
            for side in sides:
                ob = scene.objects[f'A3-build-{joint}-output{side}']; r = rows[ob.name]
                assert (ob.location-Vector([r['final_matrix'][i][3] for i in range(3)])-delta).length < 1e-7
scene.frame_set(scene.frame_end)
candidate = ROOT/'arm-step-assembly-corrected.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate), compress=True)
report = {'status':'PASS_RIGID_SERVO_ARRIVAL', 'units':groups, 'changed_frames':sorted(changed),
          'base_sha256':hashlib.sha256((ROOT/'arm-step-assembly.blend').read_bytes()).hexdigest(),
          'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
          'scope':'Location curves only; visible state unchanged outside reported arrival frames. Hidden pre-arrival extrapolation changes too; no geometry or camera changes.'}
(ROOT/'reports/servo-motion-repair.json').write_text(json.dumps(report,indent=2)+'\n')
print('SERVO_REPAIR_PASS', len(changed), 'frames')

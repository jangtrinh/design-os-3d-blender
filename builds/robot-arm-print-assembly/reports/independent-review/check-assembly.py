from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
timeline = json.loads((REPORTS / "assembly-timeline.json").read_text())
scene = bpy.data.scenes["A3-Step-assembly"]
assert scene.frame_end == timeline["frames"] == 1429
assert scene.render.fps == timeline["fps"] == 24
assert len(timeline["events"]) == 67
assert len(timeline["objects"]) == 402

scene.frame_set(scene.frame_end)
bpy.context.view_layer.update()
build_rows = {r["object"]: r for r in timeline["objects"]}
build_objects = {o.name: o for o in scene.objects if o.name.startswith("A3-build-")}
assert set(build_objects) == set(build_rows)
assert all(not o.hide_render and not o.hide_viewport for o in build_objects.values())

covered = [name for event in timeline["events"] for name in event["objects"]]
assert len(covered) == len(set(covered)) == 402
assert set(covered) == set(build_objects)

max_final_error = 0.0
for name, row in build_rows.items():
    ob = build_objects[name]
    expected = row["final_matrix"]
    error = max(abs(ob.matrix_world[a][b] - expected[a][b]) for a in range(4) for b in range(4))
    max_final_error = max(max_final_error, error)
    assert error < 1e-6, (name, error)

# Head and cylindrical shaft are a single fastener presentation: same event and displacement.
pair_errors = []
pair_count = 0
for name, row in build_rows.items():
    if not name.endswith("-head"):
        continue
    shaft_name = name.removesuffix("-head") + "-thread-envelope"
    if shaft_name not in build_rows:
        continue
    pair_count += 1
    shaft_row = build_rows[shaft_name]
    assert (row["group"], row["step"], row["start"], row["end"]) == (
        shaft_row["group"], shaft_row["step"], shaft_row["start"], shaft_row["end"]
    ), (name, shaft_name)
    for frame in range(row["start"], row["end"] + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        h = build_objects[name].matrix_world.translation
        s = build_objects[shaft_name].matrix_world.translation
        scene.frame_set(row["end"])
        bpy.context.view_layer.update()
        hend = build_objects[name].matrix_world.translation.copy()
        send = build_objects[shaft_name].matrix_world.translation.copy()
        pair_errors.append(((hend - h) - (send - s)).length)
assert max(pair_errors, default=0.0) < 1e-7, max(pair_errors, default=0.0)

# Bought-unit presentation contracts intentionally encoded by assembly-order.py.
expected_units = [
    {"A3-build-yaw-servo", "A3-build-yaw-output--1"},
    {"A3-build-shoulder-servo", "A3-build-shoulder-output--1", "A3-build-shoulder-output-1"},
    {"A3-build-elbow-servo", "A3-build-elbow-output--1", "A3-build-elbow-output-1"},
    {"A3-build-roll-servo", "A3-build-roll-output--1", "A3-build-roll-output-1"},
    {"A3-build-gripper-servo", "A3-build-gripper-output--1", "A3-build-gripper-output-1"},
]
events_by_object = {name: event for event in timeline["events"] for name in event["objects"]}
unit_motion_violations = []
for unit in expected_units:
    signatures = {(events_by_object[n]["group"], events_by_object[n]["step"], events_by_object[n]["start"], events_by_object[n]["end"]) for n in unit}
    assert len(signatures) == 1, (unit, signatures)
    event = events_by_object[next(iter(unit))]
    for frame in range(event["start"], event["end"] + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        displacements = []
        for name in sorted(unit):
            current = build_objects[name].matrix_world.translation.copy()
            scene.frame_set(event["end"])
            bpy.context.view_layer.update()
            final = build_objects[name].matrix_world.translation.copy()
            displacements.append(final - current)
            scene.frame_set(frame)
            bpy.context.view_layer.update()
        error = max((d - displacements[0]).length for d in displacements)
        if error >= 1e-7:
            unit_motion_violations.append({"objects": sorted(unit), "frame": frame, "max_relative_displacement_error_m": error, "displacements_m": [list(d) for d in displacements]})

# Captive receivers must appear before their matching screws or before the retained module transfer.
order_checks = []
def before(first, second):
    a = events_by_object[first]
    b = events_by_object[second]
    assert a["end"] < b["start"], (first, a, second, b)
    order_checks.append((first, second, a["end"], b["start"]))

for joint in ("shoulder", "elbow"):
    for side in ("-1", "1"):
        for y in ("-11", "11"):
            before(f"A3-build-{joint}-mount-foot-nut-({side}, {y})", f"A3-build-{joint}-mount-foot-({side}, {y})-head")
for y in ("-16", "16"):
    for z in ("-48", "-34"):
        before(f"A3-build-lower-cassette-nut-({y}, {int(z)+111})", f"A3-build-elbow-cassette-({y}, {z})-head")
        before(f"A3-build-upper-cassette-nut-({y}, {int(z)+137})", f"A3-build-wrist-cassette-({y}, {z})-head")
for x in ("-15.8", "15.8"):
    for y in ("-12", "12"):
        before(f"A3-build-wrist-cage-nut-({x}, {y})", f"A3-build-wrist-cage-({x}, {y})-head")
for x in ("-17", "17"):
    for y in ("-18", "18"):
        before(f"A3-build-tool-lock-nut-({x}, {y})", f"A3-build-tool-retention-({x}, {y})-head")
for y in ("8", "20"):
    before(f"A3-build-hand-adapter-nut-{y}", f"A3-build-hand-adapter-bolt-{y}-head")
for x, ys in (("-15.25", ("-9", "-16")), ("15.25", ("-12", "12"))):
    for y in ys:
        before(f"A3-build-hand-clamp-nut-({x}, {y})", f"A3-build-hand-case-clamp-({x}, {y})-head")
for nut_xy, bolt_xz in (("(21, 0)", "(-7, 0)"), ("(35, 0)", "(7, 0)"), ("(28, 7)", "(0, 7)"), ("(28, -7)", "(0, -7)")):
    before(f"A3-build-fixed-jaw-nut-{nut_xy}", f"A3-build-fixed-jaw-bolt-{bolt_xz}-head")

# Load the frozen source into this process only and compare geometry plus final transforms.
before_scenes = {s.name for s in bpy.data.scenes}
with bpy.data.libraries.load(str(ROOT / "frozen-source.blend"), link=False) as (src, dst):
    dst.scenes = ["A3-Frozen-source"]
loaded = {s.name for s in bpy.data.scenes} - before_scenes
assert len(loaded) == 1
frozen = bpy.data.scenes[next(iter(loaded))]

def mesh_digest(ob):
    h = hashlib.sha256()
    if ob.type != "MESH":
        return None
    for v in ob.data.vertices:
        h.update(("%.12g,%.12g,%.12g;" % tuple(v.co)).encode())
    for p in ob.data.polygons:
        h.update((",".join(map(str, p.vertices)) + ";").encode())
    return h.hexdigest()

mesh_count = 0
max_source_error = 0.0
source_errors = []
bpy.context.window.scene = frozen
frozen.frame_set(1)
bpy.context.view_layer.update()
for name, row in build_rows.items():
    src = frozen.objects[row["source"]]
    ob = build_objects[name]
    expected = row["final_matrix"]
    source_error = max(abs(expected[a][b] - src.matrix_world[a][b]) for a in range(4) for b in range(4))
    source_errors.append((source_error, name, row["source"]))
    max_source_error = max(max_source_error, source_error)
    if ob.type == "MESH":
        mesh_count += 1
        assert mesh_digest(ob) == mesh_digest(src), (name, row["source"])
if max_source_error >= 1e-6:
    print("SOURCE_MATRIX_WORST", sorted(source_errors, reverse=True)[:12])
    for probe in ("A3-build-roll-servo", "A3-build-moving-jaw"):
        probe_row = build_rows[probe]
        print("SOURCE_MATRIX_PROBE", probe, "BUILD", [list(r) for r in build_objects[probe].matrix_world], "FROZEN", [list(r) for r in frozen.objects[probe_row["source"]].matrix_world], "TIMELINE", probe_row["final_matrix"])
assert max_source_error < 1e-6, max_source_error

bpy.context.window.scene = scene
scene.frame_set(1)
bpy.context.view_layer.update()
assert all(o.hide_render and o.hide_viewport for o in build_objects.values())

result = {
    "status": "PASS" if not unit_motion_violations else "FAIL_PURCHASED_UNIT_MOTION",
    "scene": scene.name,
    "artifact_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
    "frames": scene.frame_end,
    "events": len(timeline["events"]),
    "objects": len(build_objects),
    "mesh_objects": mesh_count,
    "final_timeline_matrix_error": max_final_error,
    "final_source_matrix_error": max_source_error,
    "fastener_pairs": pair_count,
    "max_fastener_pair_motion_error_m": max(pair_errors, default=0.0),
    "capture_order_checks": len(order_checks),
    "purchased_unit_motion_violations": unit_motion_violations,
}
out = Path(__file__).with_name("assembly-check.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print("INDEPENDENT_ASSEMBLY_CHECK", json.dumps(result, sort_keys=True))

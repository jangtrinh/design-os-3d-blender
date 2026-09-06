#!/usr/bin/env python3
"""Independent read-only audit for arm-original-refined.blend."""

from __future__ import annotations

from array import array
import hashlib
import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILDS = HERE.parents[2]
ARTIFACT = ROOT / "arm-original-refined.blend"
SOURCE_BLEND = BUILDS / "robot-arm-print-assembly/arm-step-assembly.blend"
OUTPUT = HERE / "saved-candidate-check.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def max_matrix_error(a: Matrix, b: Matrix) -> float:
    return max(abs(a[row][column] - b[row][column]) for row in range(4) for column in range(4))


def mesh_digest(mesh) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps({
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "loops": len(mesh.loops),
        "polygons": len(mesh.polygons),
    }, sort_keys=True).encode())
    fields = [
        (mesh.vertices, "co", "f", len(mesh.vertices) * 3),
        (mesh.edges, "vertices", "i", len(mesh.edges) * 2),
        (mesh.loops, "vertex_index", "i", len(mesh.loops)),
        (mesh.loops, "edge_index", "i", len(mesh.loops)),
        (mesh.polygons, "loop_start", "i", len(mesh.polygons)),
        (mesh.polygons, "loop_total", "i", len(mesh.polygons)),
        (mesh.polygons, "material_index", "i", len(mesh.polygons)),
        (mesh.polygons, "use_smooth", "b", len(mesh.polygons)),
    ]
    for collection, field, kind, count in fields:
        values = array(kind, [0]) * count
        collection.foreach_get(field, values)
        digest.update(field.encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def object_corners(scene, obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    if evaluated.type == "CURVE":
        points = []
        for spline in evaluated.data.splines:
            if spline.type == "BEZIER":
                points.extend(evaluated.matrix_world @ point.co for point in spline.bezier_points)
            else:
                points.extend(evaluated.matrix_world @ Vector(point.co[:3]) for point in spline.points)
        assert points, evaluated.name
        return points
    return [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]


def frame_objects(scene, objects, frame, label, failures):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.hide_render or obj.hide_viewport:
            failures.append({"label": label, "frame": frame, "object": obj.name, "reason": "hidden"})
            continue
        for point in object_corners(scene, obj):
            projected = world_to_camera_view(scene, scene.camera, point)
            if not (0.0 <= projected.x <= 1.0 and 0.0 <= projected.y <= 1.0 and projected.z > 0.0):
                failures.append({
                    "label": label,
                    "frame": frame,
                    "object": obj.name,
                    "reason": "outside-frustum",
                    "xyz": [projected.x, projected.y, projected.z],
                })
                break


def main() -> None:
    source_map = json.loads((ROOT / "reports/source-map.json").read_text())
    units = json.loads((ROOT / "reports/units.json").read_text())
    timing = json.loads((ROOT / "reports/timing.json").read_text())
    grouped = json.loads((HERE / "grouped-sequence.json").read_text())
    presets = json.loads((ROOT / "reports/camera-presets.json").read_text())

    assert sha256(SOURCE_BLEND) == source_map["source_sha256"]
    scene = bpy.data.scenes["A5-Original-refined"]
    bpy.context.window.scene = scene
    assert scene.frame_end == timing["frames"]
    assert scene.render.fps == timing["fps"] == 24

    rows = source_map["objects"]
    assert len(rows) == 402
    candidate_names = {row["candidate"] for row in rows}
    assert len(candidate_names) == 402
    assert all(name in scene.objects for name in candidate_names)

    # Load the immutable A3 scene into this isolated process only.
    with bpy.data.libraries.load(str(SOURCE_BLEND), link=False) as (available, requested):
        assert "A3-Step-assembly" in available.scenes
        requested.scenes = ["A3-Step-assembly"]
    source_scene = bpy.data.scenes["A3-Step-assembly"]
    mesh_mismatches = []
    modifier_mismatches = []
    for row in rows:
        candidate = scene.objects[row["candidate"]]
        source = source_scene.objects[row["object"]]
        assert candidate.type == source.type == "MESH", (candidate.name, candidate.type, source.type)
        if mesh_digest(candidate.data) != mesh_digest(source.data):
            mesh_mismatches.append(row["candidate"])
        candidate_modifiers = [(item.type, item.name) for item in candidate.modifiers]
        source_modifiers = [(item.type, item.name) for item in source.modifiers]
        if candidate_modifiers != source_modifiers:
            modifier_mismatches.append({"object": row["candidate"], "candidate": candidate_modifiers, "source": source_modifiers})
    assert not mesh_mismatches, mesh_mismatches[:5]
    assert not modifier_mismatches, modifier_mismatches[:5]

    # Final transforms reproduce the source delivery matrices.
    scene.frame_set(scene.frame_end)
    bpy.context.view_layer.update()
    final_errors = []
    for row in rows:
        expected = Matrix(row["final_matrix"])
        error = max_matrix_error(scene.objects[row["candidate"]].matrix_world, expected)
        final_errors.append((error, row["candidate"]))
    final_error, final_error_object = max(final_errors)
    assert final_error < 1e-6, (final_error, final_error_object)

    # 252 physical units cover all 402 meshes. Every install unit occurs exactly once.
    assert len(units) == 252
    unit_by_id = {unit["id"]: unit for unit in units}
    assert len(unit_by_id) == 252
    unit_names = [name for unit in units for name in unit["names"]]
    assert len(unit_names) == len(set(unit_names)) == 402
    assert set(unit_names) == candidate_names
    install_events = [event for event in timing["events"] if event["type"] == "install"]
    scheduled_units = [unit for event in install_events for unit in event["units"]]
    assert len(scheduled_units) == len(set(scheduled_units)) == 252
    assert set(scheduled_units) == set(unit_by_id)

    # Event/group expansion matches all 93 reviewed groups without source omissions.
    expected_group_names = {group["index"]: set(group["names"]) for group in grouped["groups"]}
    actual_group_names = {index: set() for index in range(1, 94)}
    for event in install_events:
        for unit_id in event["units"]:
            actual_group_names[event["group_index"]].update(unit_by_id[unit_id]["original_names"])
    assert set(event["group_index"] for event in timing["events"] if "group_index" in event) == set(range(1, 94))
    assert actual_group_names == expected_group_names
    for previous, current in zip(timing["events"], timing["events"][1:]):
        assert current["start"] > previous["end"], (previous, current)

    # Screw pairs and large servos remain within one physical unit.
    candidate_to_unit = {name: unit["id"] for unit in units for name in unit["names"]}
    paired_fasteners = 0
    for name in candidate_names:
        if name.endswith("-head"):
            mate = name[:-5] + "-thread-envelope"
            assert mate in candidate_to_unit
            assert candidate_to_unit[name] == candidate_to_unit[mate]
            paired_fasteners += 1
    assert paired_fasteners == 146
    for joint in ("shoulder", "elbow"):
        names = {
            f"A5-part-{joint}-servo",
            f"A5-part-{joint}-output--1",
            f"A5-part-{joint}-output-1",
        }
        assert len({candidate_to_unit[name] for name in names}) == 1

    # Relative transforms stay fixed throughout every multi-mesh unit arrival.
    event_for_unit = {unit_id: event for event in install_events for unit_id in event["units"]}
    rigid_max_error = 0.0
    rigid_where = None
    for unit in units:
        if len(unit["names"]) < 2:
            continue
        event = event_for_unit[unit["id"]]
        frames = range(event["start"], event["end"] + 1)
        reference = None
        for frame in frames:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            objects = [scene.objects[name] for name in unit["names"]]
            relatives = [objects[0].matrix_world.inverted_safe() @ obj.matrix_world for obj in objects[1:]]
            if reference is None:
                reference = [matrix.copy() for matrix in relatives]
            for obj, actual, expected in zip(objects[1:], relatives, reference):
                error = max_matrix_error(actual, expected)
                if error > rigid_max_error:
                    rigid_max_error = error
                    rigid_where = [unit["id"], obj.name, frame]
    assert rigid_max_error < 1e-5, (rigid_max_error, rigid_where)

    # Actual frame ordering retains nut, seat, late-interface, electronics, wire, and cover gates.
    events_by_group = {}
    for event in timing["events"]:
        if "group_index" in event:
            events_by_group.setdefault(event["group_index"], []).append(event)
    group_start = {index: min(event["start"] for event in events) for index, events in events_by_group.items()}
    group_end = {index: max(event["end"] for event in events) for index, events in events_by_group.items()}
    for nuts, seat in ((13, 14), (21, 25), (35, 36), (43, 47), (56, 58), (75, 76), (77, 80)):
        assert group_end[nuts] < group_start[seat], (nuts, seat)
    for seat, late in ((31, 32), (53, 54), (72, 73), (88, 89)):
        assert group_end[seat] < group_start[late], (seat, late)
    assert group_end[3] < group_start[90] < group_start[91] < group_start[92] < group_start[93]
    assert group_end[91] < group_start[92] and group_end[92] < group_start[93]

    # Each station-built module introduces its receiving floor/interface in wide view
    # immediately before the camera closes into the fixed station view.
    receiver_groups = {"shoulder": 11, "elbow": 33, "wrist": 55, "hand": 74}
    receiver_first = []
    for module, group_index in receiver_groups.items():
        event_index = next(
            index for index, event in enumerate(timing["events"])
            if event.get("group_index") == group_index and event["type"] == "install"
        )
        receiver = timing["events"][event_index]
        transition = timing["events"][event_index + 1]
        following = timing["events"][event_index + 2]
        assert receiver["module"] == module and receiver["shot"] == "wide"
        assert transition["type"] == "camera-transition" and transition["from"] == "wide" and transition["to"] == "station"
        assert following.get("module") == module and following["shot"] == "station"
        assert receiver["end"] < transition["start"] < transition["end"] < following["start"]
        receiver_first.append({
            "module": module,
            "receiver_group": group_index,
            "receiver_end": receiver["end"],
            "transition": [transition["start"], transition["end"]],
            "next_install_start": following["start"],
        })

    # Six rear-CPU servo routes only; no separate supply box or loose power cord.
    wire_names = {obj.name for obj in scene.objects if obj.name.startswith("A5-wire-")}
    expected_wires = {f"A5-wire-{name}" for name in ("yaw", "shoulder", "elbow", "wrist", "roll", "gripper")}
    assert wire_names == expected_wires
    prohibited = [name for name in scene.objects if name in {"A5-external-supply", "A5-extra-servo-supply", "A5-wire-power-in"}]
    assert not prohibited
    wire_events = [event for event in timing["events"] if event["type"] == "wire"]
    assert len(wire_events) == 6 and {event["object"] for event in wire_events} == expected_wires

    # Camera rotation is fixed globally. Location/scale are exactly held during every non-camera event,
    # and any inter-frame camera motion occurs only within an explicit transition interval.
    camera = scene.camera
    assert camera is not None and camera.type == "CAMERA" and camera.data.type == "ORTHO"
    transitions = [event for event in timing["events"] if event["type"] == "camera-transition"]
    transition_frames = {frame for event in transitions for frame in range(event["start"], event["end"] + 1)}
    camera_samples = {}
    reference_rotation = None
    rotation_max = 0.0
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rotation = camera.matrix_world.to_quaternion()
        if reference_rotation is None:
            reference_rotation = rotation.copy()
        rotation_max = max(rotation_max, reference_rotation.rotation_difference(rotation).angle)
        camera_samples[frame] = (camera.location.copy(), float(camera.data.ortho_scale), rotation.copy())
    assert rotation_max < 1e-10, rotation_max
    static_translation_max = 0.0
    static_scale_max = 0.0
    for event in timing["events"]:
        if event["type"] == "camera-transition":
            continue
        first = camera_samples[event["start"]]
        for frame in range(event["start"] + 1, event["end"] + 1):
            current = camera_samples[frame]
            static_translation_max = max(static_translation_max, (current[0] - first[0]).length)
            static_scale_max = max(static_scale_max, abs(current[1] - first[1]))
    assert static_translation_max < 1e-10, static_translation_max
    assert static_scale_max < 1e-10, static_scale_max
    illegal_camera_moves = []
    camera_move_max = 0.0
    camera_scale_max = 0.0
    for frame in range(scene.frame_start + 1, scene.frame_end + 1):
        previous, current = camera_samples[frame - 1], camera_samples[frame]
        translation = (current[0] - previous[0]).length
        scale = abs(current[1] - previous[1])
        camera_move_max = max(camera_move_max, translation)
        camera_scale_max = max(camera_scale_max, scale)
        if (translation > 1e-10 or scale > 1e-10) and frame not in transition_frames and frame - 1 not in transition_frames:
            illegal_camera_moves.append({"frame": frame, "translation": translation, "scale": scale})
    assert not illegal_camera_moves, illegal_camera_moves[:5]
    preset_rotation = presets["rotation"]
    assert max(abs(reference_rotation[index] - preset_rotation[index]) for index in range(4)) < 1e-7

    # Arrivals end fully framed; complete seated submodules remain framed through transfer samples.
    arrival_failures = []
    seat_failures = []
    for event in timing["events"]:
        if event["type"] == "install":
            objects = [scene.objects[name] for unit_id in event["units"] for name in unit_by_id[unit_id]["names"]]
            frame_objects(scene, objects, event["end"], f"install-{event['group_index']}", arrival_failures)
        elif event["type"] == "wire":
            frame_objects(scene, [scene.objects[event["object"]]], event["end"], f"wire-{event['object']}", arrival_failures)
        elif event["type"] in {"seat-subassembly", "seat-module"}:
            objects = [scene.objects[name] for unit_id in event["units"] for name in unit_by_id[unit_id]["names"]]
            for frame in (event["start"], (event["start"] + event["end"]) // 2, event["end"]):
                frame_objects(scene, objects, frame, f"{event['type']}-{event['group_index']}", seat_failures)
    assert not arrival_failures, arrival_failures[:5]
    assert not seat_failures, seat_failures[:5]

    result = {
        "status": "PASS",
        "artifact_sha256": sha256(ARTIFACT),
        "source_blend_sha256": sha256(SOURCE_BLEND),
        "source_meshes": len(rows),
        "mesh_digest_mismatches": mesh_mismatches,
        "modifier_mismatches": modifier_mismatches,
        "final_world_matrix_max_error": final_error,
        "final_world_matrix_max_error_object": final_error_object,
        "physical_units": len(units),
        "scheduled_units_once": len(scheduled_units),
        "grouped_operations": len(grouped["groups"]),
        "timed_events": len(timing["events"]),
        "physical_fasteners_paired": paired_fasteners,
        "rigid_unit_max_matrix_error": rigid_max_error,
        "rigid_unit_max_where": rigid_where,
        "nut_order": "PASS",
        "late_interfaces": "PASS",
        "electronics_wiring_covers": "PASS",
        "receiver_first_wide_introductions": receiver_first,
        "servo_wires": sorted(wire_names),
        "external_supply_or_power_cord": False,
        "camera_rotation_max_change_rad": rotation_max,
        "camera_static_event_translation_max_m": static_translation_max,
        "camera_static_event_scale_max": static_scale_max,
        "camera_max_translation_per_frame_m": camera_move_max,
        "camera_max_scale_change_per_frame": camera_scale_max,
        "camera_transitions": len(transitions),
        "arrival_endpoint_failures": arrival_failures,
        "seat_transfer_failures": seat_failures,
        "limits": [
            "Bounding-box framing is a numeric screen, not a rendered visual-quality review.",
            "Motion does not prove physical insertion, tool access, fit, retention, wiring, strength, thermal behavior, or 250 g multi-minute operation.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("INDEPENDENT_SAVED_CANDIDATE_PASS")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

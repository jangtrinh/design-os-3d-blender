#!/usr/bin/env python3
"""Check grouped-sequence coverage and dependency invariants."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDS = HERE.parents[2]
TIMELINE = BUILDS / "robot-arm-print-assembly/reports/assembly-timeline.json"
SEQUENCE = HERE / "grouped-sequence.json"


def group_index(groups, name):
    return next(group["index"] for group in groups if name in group["names"])


def main() -> None:
    timeline = json.loads(TIMELINE.read_text())
    sequence = json.loads(SEQUENCE.read_text())
    groups = sequence["groups"]
    names = [name for group in groups for name in group["names"]]
    expected = {item["object"] for item in timeline["objects"]}
    assert 70 <= len(groups) <= 95, len(groups)
    assert len(names) == len(set(names)) == len(expected) == 402
    assert set(names) == expected
    assert [group["index"] for group in groups] == list(range(1, len(groups) + 1))

    # Every modeled screw head and shaft remains paired in one grouped operation.
    by_name = {name: group["index"] for group in groups for name in group["names"]}
    paired = 0
    for name in names:
        if name.endswith("-head"):
            mate = name[:-5] + "-thread-envelope"
            assert mate in by_name and by_name[mate] == by_name[name], (name, mate)
            paired += 1
    assert paired == 146, paired

    # Integral large servo visuals move with their purchased case.
    for joint in ("shoulder", "elbow"):
        unit = {
            f"A3-build-{joint}-servo",
            f"A3-build-{joint}-output--1",
            f"A3-build-{joint}-output-1",
        }
        assert len({by_name[name] for name in unit}) == 1

    # Captive nuts are separated from the prints that own/obscure them.
    for joint in ("shoulder", "elbow"):
        mounts = [f"A3-build-{joint}-motor-mount--1", f"A3-build-{joint}-motor-mount-1"]
        nuts = [name for name in names if name.startswith(f"A3-build-{joint}-mount-foot-nut-")]
        assert max(group_index(groups, name) for name in mounts) < min(group_index(groups, name) for name in nuts)
        assert len(nuts) == 4
    assert group_index(groups, "A3-build-wrist-pitch-cassette") < group_index(groups, "A3-build-wrist-cage-nut-(-15.8, -12)")
    assert group_index(groups, "A3-build-gripper-tool-plate") < group_index(groups, "A3-build-hand-adapter-nut-8") < group_index(groups, "A3-build-hand-servo-cradle")
    assert group_index(groups, "A3-build-hand-servo-cradle") < group_index(groups, "A3-build-fixed-jaw-nut-(21, 0)") < group_index(groups, "A3-build-gripper-servo")

    # Interface bolts are after an explicit seat marker.
    for module in ("shoulder", "elbow", "wrist", "hand"):
        seat = next(group["index"] for group in groups if group["module"] == module and group["operation"] == "seat-module")
        late = [group["index"] for group in groups if group["module"] == module and "late-interface" in group["flags"]]
        assert late and min(late) > seat, (module, seat, late)

    # Open shell, internals, wiring gate, covers, then service lid last.
    shell = group_index(groups, "A3-build-base-electronics-shell")
    controller = group_index(groups, "A3-build-TTL-RS485-controller-envelope")
    connector = group_index(groups, "A3-build-service-connector")
    wiring = next(group["index"] for group in groups if "wiring-before-covers" in group["flags"])
    cover_groups = [group["index"] for group in groups if "final-covers" in group["flags"] or "final-cover" in group["flags"]]
    lid = group_index(groups, "A3-build-electronics-service-lid")
    assert shell < controller == connector < wiring < min(cover_groups) <= max(cover_groups) == lid
    assert lid == len(groups)

    result = {
        "status": "PASS",
        "grouped_operations": len(groups),
        "source_meshes_once": len(names),
        "physical_fasteners_paired": paired,
        "large_servo_units_integral": 2,
        "captive_nut_dependencies": "PASS",
        "late_interfaces_after_seat": "PASS",
        "electronics_wiring_closure_order": "PASS",
        "final_operation": groups[-1]["title"],
    }
    (HERE / "grouped-sequence-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Derive a compact A3-build assembly order from the source-exact dependency plan."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDS = HERE.parents[2]
TIMELINE = BUILDS / "robot-arm-print-assembly/reports/assembly-timeline.json"
DETAILED = BUILDS / "robot-arm-assembly-guide/reports/mechanical-review/suggested-sequence.json"
OUTPUT = HERE / "grouped-sequence.json"


def main() -> None:
    timeline = json.loads(TIMELINE.read_text())
    detailed = json.loads(DETAILED.read_text())
    source_to_build = {item["source"]: item["object"] for item in timeline["objects"]}
    source_ops = detailed["operations"]
    specs: list[dict] = []

    def add(module, title, indices=(), *, operation="install", flags=(), note=""):
        specs.append({
            "module": module,
            "title": title,
            "source_operation_indices": list(indices),
            "operation": operation,
            "flags": list(flags),
            "note": note,
        })

    # Base and open electronics bay.
    add("base", "Place table anchor plate", [0], flags=["anchor-unmodeled"])
    add("base", "Place base cover", [1])
    add("base", "Place open rear electronics shell", [2], flags=["shell-open", "retention-unvalidated"])
    add("base", "Place stationary yaw adapter", [3], flags=["adapter-interface-unvalidated"])
    add("base", "Place yaw servo", [4], flags=["purchased-unit"])
    add("base", "Place yaw bearing pedestal", [5])
    add("base", "Fasten yaw pedestal symmetrically", range(6, 10), flags=["grouped-symmetric-fasteners"])
    add("base", "Seat yaw bearing", [10])
    add("base", "Place moving yaw adapter and turntable", [11, 12], flags=["adapter-interface-unvalidated"])
    add("base", "Fasten yaw horn symmetrically", range(13, 17), flags=["grouped-symmetric-fasteners"])

    def add_large_joint(module, start, nouns):
        fork, side_prefix, interface_prefix = nouns
        add(module, f"Place {module} cassette floor", [start])
        add(module, f"Place both {module} motor-mount cheeks", [start + 1, start + 5], flags=["grouped-symmetric-parts"])
        add(module, f"Capture four {module} mount-foot nuts", [start + 2, start + 3, start + 6, start + 7], flags=["capture-nuts"])
        add(module, f"Seat both prepared {module} motor mounts", [start + 4, start + 8], operation="seat-subassemblies", flags=["seat-before-fasteners"])
        add(module, f"Place integral {module} servo unit", [start + 9], flags=["purchased-unit", "integral-actuator-visuals"])
        add(module, f"Fasten {module} servo case", [start + 10, start + 11, start + 12, start + 15, start + 16, start + 17], flags=["grouped-symmetric-fasteners"])
        add(module, f"Fasten {module} mounts to floor", [start + 13, start + 14, start + 18, start + 19], flags=["grouped-symmetric-fasteners"])
        add(module, f"Place {fork} U-body", [start + 20])
        add(module, f"Place both {module} drive flanges", [start + 21, start + 26], flags=["grouped-symmetric-parts"])
        add(module, f"Fasten both {module} drive flanges", [*range(start + 22, start + 26), *range(start + 27, start + 31)], flags=["grouped-symmetric-fasteners"])
        add(module, f"Capture four {fork} cassette nuts", range(start + 31, start + 35), flags=["capture-nuts", "before-enclosing-module"])
        add(module, f"Prepare left {module} carrier and bearing", [start + 35, start + 36], flags=["preassembled-carrier", "fit-unvalidated"])
        add(module, f"Seat left {module} carrier", [start + 37], operation="seat-subassembly", flags=["seat-before-fasteners"])
        add(module, f"Fasten left {module} carrier", [start + 38, start + 39], flags=["grouped-symmetric-fasteners"])
        add(module, f"Seat prepared {fork} fork", [start + 40], operation="seat-subassembly", flags=["dual-bearing-load-path"])
        add(module, f"Prepare right {module} carrier and bearing", [start + 41, start + 42], flags=["preassembled-carrier", "fit-unvalidated"])
        add(module, f"Seat right {module} carrier", [start + 43], operation="seat-subassembly", flags=["seat-before-fasteners"])
        add(module, f"Fasten right {module} carrier", [start + 44, start + 45], flags=["grouped-symmetric-fasteners"])
        add(module, f"Fasten both {module} output circles", range(start + 46, start + 62), flags=["grouped-symmetric-fasteners", "after-dual-bearing-support"])
        add(module, f"Install both {module} bearing caps and cap screws", range(start + 62, start + 72), flags=["structural-retainers", "grouped-symmetric-fasteners"])
        add(module, f"Seat complete {module} module", [start + 72], operation="seat-module", flags=["seat-before-interface"])
        add(module, f"Install {interface_prefix} interface bolts", range(start + 73, start + 77), flags=["late-interface", "after-module-seat", "grouped-symmetric-fasteners"])

    add_large_joint("shoulder", 17, ("lower", "lower", "floor"))
    add_large_joint("elbow", 94, ("upper", "upper", "cassette"))

    # Wrist.
    add("wrist", "Place wrist pitch cassette", [171])
    add("wrist", "Capture four wrist cage nuts", range(172, 176), flags=["capture-nuts", "before-case-retainer"])
    add("wrist", "Place wrist servo", [176], flags=["purchased-unit"])
    add("wrist", "Install wrist case retainer", [177], flags=["structural-retainer"])
    add("wrist", "Fasten wrist servo cage", range(178, 182), flags=["grouped-symmetric-fasteners"])
    add("wrist", "Place left wrist adapter, hub, and cheek", [182, 183, 184], flags=["adapter-interface-unvalidated"])
    add("wrist", "Fasten left wrist pivot circle", range(185, 189), flags=["grouped-symmetric-fasteners"])
    add("wrist", "Place right wrist adapter, hub, and cheek", [189, 190, 191], flags=["adapter-interface-unvalidated"])
    add("wrist", "Fasten right wrist pivot circle", range(192, 196), flags=["grouped-symmetric-fasteners"])
    add("wrist", "Place wrist cross bridge", [196], flags=["retention-unvalidated"])
    add("wrist", "Place roll motor cradle", [197], flags=["retention-unvalidated"])
    add("wrist", "Place both roll adapter envelopes", [198, 199], flags=["adapter-interface-unvalidated"])
    add("wrist", "Place roll servo", [200], flags=["purchased-unit"])
    add("wrist", "Place tool dock", [201])
    add("wrist", "Capture four tool-lock nuts", range(202, 206), flags=["capture-nuts", "before-tool-interface"])
    add("wrist", "Seat two tool dowels", [206, 207], flags=["fit-unvalidated"])
    add("wrist", "Fasten roll dock", range(208, 212), flags=["grouped-symmetric-fasteners"])
    add("wrist", "Seat complete wrist module", [212], operation="seat-module", flags=["seat-before-interface"])
    add("wrist", "Install wrist cassette interface bolts", range(213, 217), flags=["late-interface", "after-module-seat", "grouped-symmetric-fasteners"])

    # Hand.
    add("hand", "Place gripper tool plate", [217])
    add("hand", "Capture two tool-plate adapter nuts", [218, 219], flags=["capture-nuts", "before-cradle"])
    add("hand", "Place hand servo cradle", [220])
    add("hand", "Capture jaw and case-clamp receiver nuts", range(221, 229), flags=["capture-nuts", "before-servo-and-retainer"])
    add("hand", "Fasten cradle to tool plate", [229, 230], flags=["grouped-symmetric-fasteners"])
    add("hand", "Place both gripper adapter envelopes", [231, 232], flags=["adapter-interface-unvalidated"])
    add("hand", "Place gripper servo", [233], flags=["purchased-unit"])
    add("hand", "Install hand case retainer", [234], flags=["structural-retainer"])
    add("hand", "Fasten hand case clamp", range(235, 239), flags=["grouped-symmetric-fasteners"])
    add("hand", "Place fixed jaw", [239])
    add("hand", "Fasten fixed jaw", range(240, 244), flags=["grouped-symmetric-fasteners"])
    add("hand", "Place moving jaw", [244])
    add("hand", "Fasten moving jaw", range(245, 249), flags=["grouped-symmetric-fasteners"])
    add("hand", "Install all six TPU grip pads", range(249, 255), flags=["grouped-print-variants"])
    add("hand", "Seat complete hand module", [255], operation="seat-module", flags=["seat-before-interface"])
    add("hand", "Install four tool-retention bolts", range(256, 260), flags=["late-interface", "after-module-seat", "grouped-symmetric-fasteners"])

    # Electronics and closure. Wiring is an explicit dependency gate because no wire mesh exists.
    add("electronics", "Install controller envelope and service connector", [260, 261], flags=["inside-open-shell", "electronics-placeholder"])
    add("electronics", "Route and verify all wiring before closure", [], operation="unmodeled-gate", flags=["wiring-before-covers"], note="No wire mesh or verified harness/BOM exists in the 402-source set.")
    add("finish", "Install exterior skirt, fascia, and wrist cover", [262, 263, 264], flags=["final-covers", "retention-unvalidated"])
    add("finish", "Install electronics service lid last", [265], flags=["final-cover", "after-electronics-and-wiring", "retention-unvalidated"])

    consumed = [index for spec in specs for index in spec["source_operation_indices"]]
    assert len(consumed) == len(set(consumed)) == len(source_ops)
    assert set(consumed) == set(range(len(source_ops)))

    groups = []
    covered = []
    for number, spec in enumerate(specs, 1):
        names = []
        source_types = []
        for index in spec.pop("source_operation_indices"):
            operation = source_ops[index]
            source_types.append(operation["type"])
            names.extend(source_to_build[name] for name in operation.get("names", []))
        covered.extend(names)
        groups.append({
            "index": number,
            **spec,
            "names": names,
            "source_operation_types": sorted(set(source_types)),
        })

    expected = {item["object"] for item in timeline["objects"]}
    assert len(covered) == len(set(covered)) == 402
    assert set(covered) == expected
    assert 70 <= len(groups) <= 95

    result = {
        "status": "PASS",
        "authority": {
            "timeline": str(TIMELINE),
            "detailed_dependency_order": str(DETAILED),
            "scope": "Grouped presentation order only; no insertion, access, fit, retention, wiring, or manufacturing approval.",
        },
        "counts": {
            "grouped_operations": len(groups),
            "source_meshes_covered_once": len(covered),
            "original_grouped_events": len(timeline["events"]),
            "detailed_physical_install_operations": detailed["counts"]["install_operations"],
        },
        "identity_rules": {
            "physical_fastener": "A matching A3-build *-head and *-thread-envelope pair is one screw and always moves in the same grouped operation.",
            "large_servo_unit": "Shoulder/elbow actuator plus two actuator-visual outputs remain one purchased servo unit.",
            "shaft_articulation": "Operational parenting does not establish detachable assembly ownership; yaw/wrist/roll/gripper adapter envelopes remain explicit interface placeholders.",
            "wiring": "The 402-source set contains no wire geometry; the wiring operation is a dependency gate before covers, not a modeled installed item.",
        },
        "groups": groups,
        "optional_appendix": detailed["optional_appendix"],
        "unresolved": [
            "Actual adapter spline and retention hardware",
            "Continuous physical insertion and tool access",
            "Bearing fits and carrier retention",
            "Cross-bridge, roll-cradle, electronics-shell, cover, and yaw-case retention",
            "Harness, controller, supply, connector, strain-relief, electrical, and thermal design",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["counts"], indent=2))


if __name__ == "__main__":
    main()

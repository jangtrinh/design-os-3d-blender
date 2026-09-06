# Independent grouped assembly-order review

## Implementable contract

Use `grouped-sequence.json`. It contains 93 ordered operations using exact `A3-build-*` names:

- base 10; shoulder 22; elbow 22; wrist 19; hand 16; electronics 2; finish 2;
- all 402 source meshes appear exactly once;
- all 146 physical screws keep their matching `-head` and `-thread-envelope` meshes in one operation;
- each shoulder/elbow servo stays one purchased unit with both actuator-visual output meshes;
- symmetric fasteners arrive together, preserving the original grouped presentation style.

The compact timing target can stay near the original 58 seconds: about 10 arrival frames plus 3 hold frames per operation, with 36-frame eased camera transitions only between chapter or module-seat windows. The camera should remain static throughout each install group and use the original direction, studio, and assembly station selected by the controller.

## Dependency corrections carried forward

1. Install each motor-mount cheek, then insert its captive nuts, then seat the prepared mount. The nut and its receiver/enclosing placement never share an operation.
2. Prepare each dual-output fork with both flanges, flange screws, and cassette nuts. Seat the left carrier/bearing, seat the fork, add the right carrier/bearing, then install output-circle screws and bearing-cap retainers.
3. Seat shoulder, elbow, wrist, and hand modules before their flagged `late-interface` bolts. These are operations 32, 54, 73, and 89.
4. Keep the rear electronics shell open from operation 3. Install the controller envelope and service connector at operation 90, route wiring at gate 91, add exterior covers at 92, and close the electronics service lid last at 93.
5. Preserve adapter identity: yaw, wrist, roll, and gripper output meshes are interface placeholders. Operational shaft parenting does not prove that they are integral servo parts. Only the shoulder/elbow actuator-visual outputs are absorbed into their purchased servo units.

## Verification

Run from this report directory:

```bash
python3 your_report_checker.py
```

Result: `PASS`; 93 grouped operations, 402 unique source meshes, 146 paired physical fasteners, two integral large-servo units, captive-nut dependencies pass, every late interface follows its module seat, and electronics/wiring/closure order passes.

The seven A4 cable paths may be copied into operation 91 as presentation-only wire geometry. They remain outside the 402-source identity count and must not be described as a verified harness, connector, pinout, bend-radius, strain-relief, or electrical design.

## Unresolved physical limits

The refined video can show this dependency order, but it cannot establish collision-free insertion, tool access, bearing fit, adapter retention, structural retention for placement-only pieces, cable feasibility, strength, thermal performance, or the 250 g multi-minute requirement. Those uncertainties are unchanged from the source model.

Status: DONE_WITH_CONCERNS

Summary: Delivered and independently checked a 93-operation grouped sequence that preserves the original presentation cadence while covering every one of the 402 A3-build meshes exactly once and enforcing nut, seating, interface, electronics, wiring, and cover dependencies.

Concerns/Blockers: Unknown physical access and retention remain; the video must present the sequence as an assembly proposal, not proof of manufacture or loaded operation.

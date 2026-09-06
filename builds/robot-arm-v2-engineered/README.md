# Arm V2 — full rebuild, preproduction

**Status: NOT APPROVED FOR MANUFACTURE OR A 250 g LOADED RUN.**

The whole arm has been rebuilt in a separate scene and file. This is more than the earlier joint-interface study. The intended useful payload remains250g held for many minutes; it has not been reduced to make this revision pass. The wrist-pitch torque screen currently fails the chosen1.5factor after a50g reserve. The exact small-servo adapters and several thread depths also remain unresolved. STL closure and an animation are not proof of an operational assembly.

## Open and inspect

**New natural task demonstration:** [TASK-DEMO.md](TASK-DEMO.md), `arm-v2-task-demo.blend`, and `videos/arm-v2-natural-tasks.mp4`: pick, lift/inspect, transfer to the rear station, stack and park. The secondary [FLEXIBILITY.md](FLEXIBILITY.md) / `arm-v2-flexibility.blend` retains the40second joint-range study. Its changed parts are not included in the baseline STL package below; physical release remains blocked.

- `arm-v2-engineered.blend`: `ARM2-Assembled`, `ARM2-Motion-and-assembly`, `ARM2-Tool-library`.
- `videos/arm-v2-joint-demo.mp4`:6seconds, six joint controls including gripper.
- `videos/arm-v2-explode-reassemble.mp4`:10seconds, fasteners → modules → covers → reassembly. This is an assembly overview, not a validated installation trajectory.
- `renders/arm-v2-hero.png`, `arm-v2-reverse.png`, `arm-v2-underside.png`, `reference-comparison.png`, `tool-library.png`.
- `parts/UNRELEASED-fit-prototypes/`:38 separated, closed STL meshes in millimetres. Inspect them as fit studies only. None is a load-approved release.

## Mechanical design represented

Nominal shoulder height119mm; shoulder–elbow111mm; elbow–wrist137mm. The original drawing's119+111+137+166 sums to533mm while its overall label says532mm. New offset tooling changes the exact end-point envelope; the segment sum is not a verified maximum reach.

Two SM105-class large servos have dual bearing-supported interfaces, detachable forks and removable cassettes. Four smaller C018-class actuator envelopes represent yaw, wrist pitch, roll and gripper. The visible body is matte white PETG with metal internal carriers and journals. This design therefore requires machined/bought metal parts as well as printed polymer. A Blender mesh is not a toleranced machining drawing.

The case-growth approval is reflected in visibly larger shoulder/elbow cartridges and an anchored base. The revised silhouette, wrist packaging, fork ends and hidden surfaces differ from the reference; no100% shape-fidelity claim is made. The reference comparison exposes these differences.

### Hand and interchangeable heads

T48 dock:48×52×6mm plates, four M3 positions on a34×36mm rectangle, two3mm alignment pins24mm apart. The gripper head, universal blank and12mm pen-clamp adapter share this interface. The pen collet is a separate bolted part.

The gripper's case has a removable cap, four clamp screws and captive nuts. Its four moving-jaw screw axes follow the output horn through the tested−16°,0°,12° positions. Maximum numerical axis offset is0.000026mm; this is CAD arithmetic, not manufacturing tolerance. Modeled moving-jaw thread overlap is only1.4mm and needs real hardware validation. The cap requires a0.5mm shim at the actual servo case. M3×52 clamp screws are a finished/cut length, not an instruction to buy an assumed standard part.

At a72mm pad station, approximate projected clearance ranges41mm to6mm over the demonstrated angles. Do not command18° closure: the current geometric projection gives negative clearance. With assumed frictionμ=0.30 and two opposed contacts,250g requires4.09N normal force per jaw; gripper torque is0.294N·m static,0.588N·m with factor2. Friction, eccentric objects, TPU retention, jaw bending and continuous-hold temperature still require testing.

### Rear electronics compartment

The rear block is a provisional controller/power-connection enclosure. Outer envelope63×66×39mm; cavity cutter55×58×38mm. It is **not fitted to a specific Raspberry Pi**, and no Pi mounting bosses or port clearances are modeled. The43×49mm board inside is explicitly an envelope. Exact controller, supply, wiring, switches and cooling are still open BOM items.

## Digital evidence

| Axis | Sampled gravity bound incl.50g reserve | ×1.5 demand | Published rated | Rated / demand |
|---|---:|---:|---:|---:|
| Shoulder |3.176N·m|4.764N·m|4.903N·m|1.029|
| Elbow |1.706N·m|2.558N·m|4.903N·m|1.917|
| Wrist pitch |0.671N·m|1.006N·m|0.981N·m|0.975 — FAIL|
| Wrist roll |0.284N·m|0.427N·m|0.981N·m|2.298|

`reports/operating-envelope.json` explains the75 downstream configurations and gravity-direction bound. It uses full-solid CAD masses, purchased component overrides and50g reserve. This is not a dynamic or collision-certified workspace. Even the shoulder retains only2.9% numerical headroom above the selected demand.

`reports/final-delivery-audit.json` records closed-mesh checks, hand-axis alignment, four tool-lock nuts,38 STL bounds below220mm, and exact animation return to the assembled transforms. `reports/component-register.csv` is a component census, not a purchase-ready BOM.

Independent checks are in `reports/independent-final-check.md`, with the reviewed file hash. They reproduce removal of both fork/cassette clashes and the roll-output pocket clash. Fourteen surface-contact pairs remain in the assembled screen; the independent narrow checks classify these as intended seats or numerical residues. No complete fastener-inclusive motion sweep is claimed.

## Release gates

1. Restore wrist-pitch rated margin through a verified actuator/reduction redesign; retain the user's250g duty requirement. Recheck shoulder mass and dynamics after that change.
2. Verify exact C01825T/idler adapter parts and actual SM105 output M3 usable thread depth. The modeled vendor M3×6 output screws are provisional.
3. Finish matched fastener-stack drawings, nut insertion/tool-access paths, case shims, bearing fits, cable loops, limits and full-motion collisions. Cosmetic covers also need their final retention details.
4. Validate printed coupon fits, weakest sections, jaw stiffness, printed creep/fatigue and metal carrier tolerances. Suggested starting process: PETG,0.4mm nozzle,0.2mm layers,6walls; TPU pads. Orientation/support choices require slicer inspection and coupons.
5. Specify actual base anchors/table clamp and instrument a250g horizontal multi-minute hold. Log current, case temperature, positional drift and protection events against the purchased actuator's limits. No hold-on-power-loss behavior is provided.

## Reproduce

Run `build-arm.py` in Blender's connected scene or a separate headless process; it replaces onlyA2-prefixed rebuild objects. Run `check-operating-envelope.py`, `export-prototype-parts.py`, then `create-animation.py` and `final-delivery-audit.py`. Run `render-animation.py` only after saving the new animation scene. Scripts use the project path recorded in their sources.

Original V1 SHA256 remains`9ed05eb62e88f8025c1058e79c974cc592efdb48df404196bea3caeac493fac4`; original reference V2 remains`7ec71fb5d1c2f5d850fdcac8d8ee435eccde79862edd532d06a9538cdc8dcf8d`.

Primary dimensional/rating sources: [FEETECH SM105 page](https://www.feetechrc.com/861651.html), local official SM105PDF in the reference build, and [FEETECH ST-3215-C018 drawing/specification](https://www.feetechrc.com/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf). A rated torque is not a thermal certificate for this enclosure.

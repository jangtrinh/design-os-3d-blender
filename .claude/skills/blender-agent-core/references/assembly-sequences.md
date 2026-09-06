# Removable assembly films: staging, order and swept paths

Use for assembly/exploded views of separate printed and purchased parts. This is a project recipe, not a physical assembly certification. [Evidence and journal](../../../../plans/260905-2337-arm-session-retro/plan.md) identify the Arm session that motivated it.

## Contract before motion

Identify every physical unit, assembly receiver, final datum, fastener pairing and dependency. Keep the approved source scene immutable. Record separately: presentation intent, assembly order, geometric fit and loaded operation. Changing the film cannot erase payload/duty requirements.

Preserve the owner's selected film direction. If asked to repair transition/order, adjust that film's timing and paths; do not silently replace its camera language with a workshop/orbit concept. Keep receivers visible before moving the camera toward them. Hold the camera while parts install, unless the brief explicitly requests motion.

## Eight outputs, in order

1. **Contract:** source revision, intended sequence, camera language and physical blockers.
2. **Unit manifest:** each printed/purchased part once; rigid screw head/thread pairs; reversible final transforms.
3. **Dependency graph:** receiver → internal hardware → mating unit → retention → wiring → covers; insertion/access may change the order.
4. **Staging layout:** waiting subassemblies separated in world space and camera projection; gap derived from actual envelopes.
5. **Swept-path report:** arrivals and seats tested through time against already installed parts; distinguish waiting, transit and terminal mating.
6. **Short animatic:** inspect the failing interval and analogous mechanisms, plus framing at first/last poses; reject before full batch.
7. **Frozen render manifest:** exact inputs/settings/range; new revision invalidates affected evidence and frames.
8. **Decoded delivery:** count/rate/size/full decode plus viewed output; media/motion/fit/manufacture statuses remain separate.

## Staging is not seating

A correct final pose does not validate the waiting pose or approach. A pair that touches in the final assembly must not be exempted throughout the sequence. Same-link filtering is valid only while parts actually form one rigid installed body; it can hide an uninstalled part intersecting its future link.

First broad-phase evaluated world bounds, then an appropriate surface/solid predicate. AABB overlap is a candidate pair, not penetration volume. Surface BVH misses full containment and cannot establish exact clearance or physical insertion. Record scene units, object transforms, evaluated geometry, exclusions and frame coverage.

For each exception specify **exact pair, phase/frame window, interface, rationale and residual uncertainty**. An `actuator-visual` tag alone is not permission to ignore every collision. Separate actual servo cases from illustrative output shapes. Contact with a simplified output does not validate real horn/spline mating or retention.

Zero overlap while waiting still does not validate transit. Test the swept route, including any waypoints. Lift/traverse/lower is one candidate when a direct segment crosses the receiver; derive lift and approach axes from geometry, not a universal 120mm constant. Closed bearing carriers can obstruct a fork's passage even when all final poses fit. Validate alternate order before changing geometry or hiding parts.

Do not infer driver obstruction from nearby envelopes without measuring head-to-thread direction and tool approach. Component fit, access and torque require the actual hardware geometry/evidence.

## Timing, camera and wires

Quintic easing values have zero first/second derivative at their endpoints. This does not mean zero jerk, and frame-sampled LINEAR F-curves do not constitute a continuous C2 trajectory. Inspect the interpolation actually evaluated by Blender; distinguish visual smoothness from a controller motion profile.

Fit the camera to the intended visible interval, including moving envelopes and final fingertips. Preview the initial receiving part, complete remote subassembly, midpoint transit, seat, analogous joint, tool and hero endpoints before long render. Pose screenshots do not by themselves prove temporal smoothness.

A curve reveal or collapsed-tip animation is visual assembly order. It is not length-preserving wire threading, bend-radius compliance or strain relief. Declare connector pinout, cable diameter, slack, bend limits and moving-joint sweep from selected hardware when claiming a functional harness. Leave those claims open until checked.

## Evidence in this Arm

The [layout](../../../../builds/robot-arm-original-refined/scripts/repair-staging-layout.py), [motion](../../../../builds/robot-arm-original-refined/scripts/animate-physical-units.py), [independent sweep](../../../../builds/robot-arm-original-refined/reports/independent-review/check-overlap-repair.py) and [acceptance guard](../../../../builds/robot-arm-original-refined/scripts/check-clearance-acceptance.py) are artifact-specific inspect/adapt examples. The waiting and seat checks exclude hardware; do not generalize their result to the complete assembly, subframe continuity or manufacture. The Arm used 35mm projected staging target, 120mm lift and axial carriers; these are case values, not design standards.

**Enforcement:** sequence/gap/phase choice and visual review are MANUAL. Named Arm scripts executed particular predicates on one revision. A reusable general gate is still [E6](../../../../docs/blender-workflow-improvement-backlog.md#e6--validate-assembly-states-before-full-render).

# Independent saved-candidate review

Reviewed artifact SHA-256: `522afd6712129a2cf751de5a2dd9d517847619dc9783fd4732da79683487f361`

## Direct saved-file evidence

- Exact source identity passes for all 402 production meshes against `arm-step-assembly.blend` SHA-256 `20e27bc6022251d1a07ff6cad86098f11aade295178e9e2af2adfc83b69495ba`: zero raw mesh-digest mismatches, zero modifier-list mismatches, and final world-matrix maximum element error `1.1920928955078125e-7`.
- All 252 physical units are scheduled exactly once and cover the 402 meshes once. All 146 screw head/thread-envelope pairs share one physical unit. Shoulder and elbow servos each retain their two actuator-visual outputs as one rigid purchased unit. Maximum relative-matrix drift across every frame of every multi-mesh arrival is `1.1920928955078125e-7`.
- All 93 reviewed groups are present in 121 timed events: 109 install/seat/wire events plus 12 camera transitions. They contain no overlap or source omission. Captive-nut gates, four module seats followed by late interfaces, open-shell electronics, wiring, exterior covers, and last service-lid order pass on actual frame ranges.
- The saved scene contains exactly six servo cable curves: yaw, shoulder, elbow, wrist, roll, and gripper. It contains no `A5-external-supply`, `A5-extra-servo-supply`, or `A5-wire-power-in` object.

## Camera and framing

- Camera world rotation is globally fixed: maximum change `0.0 rad` across all 2,887 frames.
- Camera translation and orthographic scale are exactly static during every install, wire, seat-subassembly, and seat-module event: both maximum deltas are `0.0`.
- All camera movement occurs within the 12 explicit transition windows. Maximum evaluated changes are `0.0140534314 m/frame` translation and `0.0271746516/frame` orthographic scale.
- Every installed unit and completed wire endpoint is inside the camera frame. Every visible member of every seated subassembly/module remains inside the frame at transfer start, midpoint, and endpoint. Both failure lists are empty.
- Receiver-first introduction passes for all four station modules. The shoulder, elbow, wrist, and hand floor/receiver installs finish in wide view at frames 293, 901, 1509, and 2081; each is followed by a 36-frame wide-to-station transition, then the next same-module install. The camera therefore never closes into an empty module station.
- Blender reports animated curve `bound_box` values padded by approximately ±1 m, unrelated to the actual spline. The independent wire gate therefore projects evaluated spline points; those rendered path coordinates pass. Mesh framing uses evaluated object bounding boxes.

## Delivery concerns

- The scene is 2,887 frames at 24 fps. The stated encoded range, frames 12–2887 inclusive, is 2,876 frames or `119.833 s`. This is materially longer than the approximately 58-second baseline the user said was close to desired. Numeric structure passes, but the animatic/owner review must decide whether the doubled runtime still preserves the requested cadence.
- Standalone normalization is resolved. The exact headless command opens the file directly without the prior `Library file, loading empty scene` warning, and `A5-Original-refined` is active.
- No completed preview/video was assessed in this review. Numeric framing cannot establish the original studio look, perceived smoothness, or visual timing.

## Reproduction command

```bash
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --disable-autoexec \
  -b /Users/jang/Products/Blender/builds/robot-arm-original-refined/arm-original-refined.blend \
  --python-exit-code 23 \
  -P /Users/jang/Products/Blender/builds/robot-arm-original-refined/reports/independent-review/check-saved-candidate.py
```

Result: exit `0`, `INDEPENDENT_SAVED_CANDIDATE_PASS`. Full evidence is in `saved-candidate-check.json`.

Status: DONE_WITH_CONCERNS

Summary: The final normalized candidate passes independent source, transform, unit rigidity, exact group coverage, dependency order, six-wire scope, fixed-camera, receiver-first introduction, endpoint-framing, and seated-module framing checks.

Concerns/Blockers: Review the 119.833-second encoded animatic against the requested approximately 58-second cadence. Physical insertion, access, fit, retention, wiring, strength, thermal performance, and 250 g multi-minute operation remain unverified.

# Independent staging-overlap diagnosis and repair review

Current reviewed artifact: `arm-original-refined.blend`, SHA-256 `11d88f93996dcb1eb54a21fe8dbf4bd769b0abd7284b9472e9b77cb12510bd6e`.

Superseded defect snapshot: SHA-256 `522afd6712129a2cf751de5a2dd9d517847619dc9783fd4732da79683487f361`.

## Original cause

The superseded animation staged the complete fork only `+25 mm Z` and placed a closed carrier before seating the fork. Shoulder frame 588 put the waiting fork directly through the cassette: exact BVH intersections occurred between both drive flanges and actuator output visuals. Elbow frame 1198 reproduced the defect. The carrier-first order also forced the fork through a closed bearing journal.

The first remote-stage repair (`e9323de9...`) removed waiting overlap but sent the fork straight from camera-right to its receiver. That diagonal swept through real parts: shoulder `lower-U-body` / `shoulder-drive-flange--1` crossed the servo case and right motor mount during frames `563–572`; elbow repeated the case/body conflict during frames `1211–1217`. It was correctly rejected before final rendering.

## Current repair verification

The current artifact uses remote camera-right staging, seats the fork before both carriers, and moves each fork through three 24-frame segments: lift `120 mm Z`, traverse above the receiver, then lower vertically.

- All six waiting states have zero cross-subassembly triangle-BVH pairs: shoulder/elbow fork, left carrier, and right carrier.
- The measured fork-to-cassette projected gap is `41.31 mm` at the shoulder and `65.29 mm` at the elbow along the staging axis `(1, 0.55, 0).normalized`. Both exceed the specified `35 mm` construction gap because these measurements use evaluated mesh bounds rather than the unit-envelope approximation.
- Shoulder fork seats during frames `543–615`, before left carrier `663–687` and right carrier `753–777`. Elbow fork seats during `1223–1295`, before left carrier `1343–1367` and right carrier `1433–1457`.
- Complete fork sweeps contain no servo-case, motor-mount, cradle, carrier, or printed-body intersection. Their sole exact pair is drive flange versus the corresponding `actuator-visual` output near the endpoint: shoulder frames `606–615`, elbow `1286–1295`.
- Each axial carrier sweep has one terminal carrier-to-cradle-floor BVH pair during its final six frames: shoulder `682–687` and `772–777`; elbow `1362–1367` and `1452–1457`. Source geometry places the carrier stem bottom and cradle top at the same nominal `Z=-52.5 mm`, so this is consistent with the intended terminal face contact. The BVH method does not establish positive penetration volume.

The independent saved-scene audit also passes: all `402` source meshes retain their mesh digests, final world matrices match within `1.1921e-7`, all `252` physical units are scheduled once, all `146` head/thread pairs remain rigid, the `93` reviewed groups remain covered, and nut/interface/cover ordering is unchanged.

## Flange capture and output-mating limit

Direct measurement corrects the earlier access inference: both flange-screw heads face outward. The left head is centered at `Y=-33.0 mm` with its thread toward `Y=-28.5 mm`; the right head is centered at `Y=+33.0 mm` with its thread toward `Y=+28.5 mm`. Driver approach is outward (`-Y` left, `+Y` right). The saved geometry does not show a driver-access obstruction.

The flange/journal geometry still constrains assembly. Each united metal part has a `Ø44 mm` flange and `Ø29.98 mm` journal; the monolithic fork cheek opening is `Ø30.3 mm`. The flange cannot pass through that opening from outside. The presentation therefore preloads each flange from the fork interior, with its journal through the cheek, before seating the fork. The output-circle screws are added only after dual bearing support.

Physical output mating remains `UNKNOWN`. The saved outputs are tagged `actuator-visual`, and synthetic straight approaches intersect those simplified meshes `30–35 mm` before the final pose. No tested approach intersects the actual servo case after the repair, but neither the collision exception nor the animation proves a real actuator/horn insertion path. Exact output/horn geometry and retention must define that path.

## Reproduction

```bash
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --disable-autoexec \
  -b /Users/jang/Products/Blender/builds/robot-arm-original-refined/arm-original-refined.blend \
  --python-exit-code 23 \
  -P /Users/jang/Products/Blender/builds/robot-arm-original-refined/reports/independent-review/check-overlap-repair.py
```

The command exits `0` and writes `overlap-repair-check.json`. It samples every fork/carrier seat frame, checks waiting-state BVHs and projected gaps, verifies order, classifies output visuals separately from actuator cases, and checks final source matrices.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --disable-autoexec \
  -b /Users/jang/Products/Blender/builds/robot-arm-original-refined/arm-original-refined.blend \
  --python-exit-code 23 \
  -P /Users/jang/Products/Blender/builds/robot-arm-original-refined/reports/independent-review/check-saved-candidate.py
```

This command also exits `0` and writes `saved-candidate-check.json` with source identity, unit rigidity, sequence, camera, and endpoint gates.

Status: DONE_WITH_CONCERNS

Summary: The current three-segment repair removes the demonstrated waiting overlap and every real case/body clash from both fork sweeps. Fork-before-carriers order, axial carrier paths, exact source preservation, and grouped sequence gates pass.

Concerns/Blockers: Output/flange contact is still a schematic `actuator-visual` exception, not a validated insertion. Flange retention, exact output/horn geometry, fits, tool access, and loaded operation remain physically unverified.

# Arm V2 — large-range motion study

Separate artifact: `arm-v2-flexibility.blend`, scene `ARM2-Flexibility`. The engineering baseline `arm-v2-engineered.blend`, its old assembly animation and its prototype STL package are preserved. This revision is a CAD motion study, **not a manufacturing release or evidence of a 250 g continuous hold**.

## Watch

The Blender scene contains40seconds at24fps with six real joint transforms. Its full video render was stopped after the user requested natural tasks instead; the encoded preview is `videos/flexibility-first-10-seconds.mp4`. The main new film is described in [TASK-DEMO.md](TASK-DEMO.md). A fixed camera and fixed floor directions make base rotation distinguishable from camera orbit. The diagnostic side panel displays actual keyed angles and a tracked point at the fixed jaw tip; that point is not a calibrated tool center. Each major endpoint briefly holds.

| Demonstrated movement | Selected angles |
|---|---|
| Base yaw | −180° to +180°, then unwind |
| Shoulder | −100° rearward through vertical to +90° forward |
| Elbow | −130° to +85° |
| Wrist pitch | −15° to +30° |
| Wrist roll | −180° to +180°, then unwind |
| Gripper joint | −16° open to +12° closing |

These are selected ranges for this path. They are not verified servo hard stops, a maximal collision-free workspace, or permission to combine all extremes. Cabling, physical stops, servo control, inertia and speed limits are not simulated. Wider wrist-pitch endpoints found in isolated probes cannot be used when intervening poses collide.

## Geometry differences from the engineering baseline

1. Corrected the front yaw-output horn parent so the horn follows its bolts and the yaw joint.
2. Shoulder cosmetic fascia: 70 to 56 mm wide, 5 to 2.5 mm thick, shifted 2.5 mm inward to clear the horizontal fork.
3. Fixed yaw pedestal corners trimmed to a 43 mm radius, retaining its four mounting positions. Nominal radial clearance to the rotating skirt is 0.5 mm.
4. Rear controller shell and lid lowered 11 mm. Shell exterior is 63 × 66 × 28 mm; it remains a generic controller envelope, **not a Raspberry Pi installation**. The represented board and connector retain their positions.
5. Hand-servo cradle receives a circular roll-motor clearance; wrist cross-bridge receives a swept cap-clearance cut. Both remain one closed component. Cradle volume changes from 42,607 to 42,296 mm³; bridge volume from 5,442 to 4,666 mm³. Residual wall strength and physical fits require renewed review before printing for service.

The old `parts/UNRELEASED-fit-prototypes/` STLs match the baseline, **not these revised parts**. No replacement print kit is released with this animation. The previous mass/torque report is also a baseline calculation, not a recalculation for this revision. Its wrist overload, small shoulder margin, adapter/thread uncertainties and thermal blockers remain unresolved.

## Verification scope

- `reports/flexibility-path-check.json`: every rendered pose screened for cross-joint triangle intersections, including modeled fasteners; only own-servo/output proxy pairs excluded. Uses a 50 μm broad-phase overlap threshold and object bounding boxes for the ground-plane screen. Does not test solid containment, continuous swept volume, minimum clearances or printed deflection.
- `reports/flexibility-framing-check.json`: all 960 poses compared to authored angles; every arm bounding-box corner stays at least 5% inside the render. Fixed camera throughout.
- `reports/flexibility-wrist-clearance.json`: before/after closure, component count and volumes for the two wrist/hand changes.
- `reports/independent-flexibility-review.md`: separate read-only assessment and remaining concerns.

## Reproduce

Run `build-flexibility.py` with Blender. It first reloads the preserved baseline, then applies each clearance revision exactly once and saves the separate file. **Do not run the individual scaling refinements repeatedly on an already revised model.** `ARM_FLEX_OUTPUT` can target a separate candidate file.

Then run `check-flexibility-path.py`, `verify-flexibility-framing.py`, `render-flexibility.py`; run `caption-flexibility.py` with system Python/Pillow. Encode `videos/flexibility-captioned/frame-%04d.png` at 24 fps with H.264/yuv420p. Cycles CPU is used for the delivered render; the local Metal preview was slower at this resolution.

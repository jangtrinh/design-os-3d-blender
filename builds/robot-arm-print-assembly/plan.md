# Arm print breakdown and sequential assembly

Outcome: extract the latest Arm geometry into individually identified print parts, orient/pack them on 220 x 220 mm plates, deliver mm STL/3MF geometry and an editable Blender assembly plus clean step-by-step video. Include interchangeable tools separately; purchased servos/fasteners/bearings and machined metal are inventory, not polymer print parts.

Controller/sole writer: root. Independent reviewer: read-only artifact reviewer; reports only. Source boundary: preserve all existing Arm files and dirty GUI via copy checkpoint. New files only under this build folder. No scene resets of source objects. Native local geometry only; no device/printer actuation or hardware ordering.

Accepted assumptions: 220 x 220 mm plates, 0.4 mm nozzle, 0.2 mm layers, PETG body and TPU pads. Confirm in actual printer/slicer before machine-specific G-code. Physical release remains blocked for 250 g multi-minute duty; current task must not relabel a fit prototype as load-qualified.

Scene graph: frozen source snapshot -> independent extracted meshes with source IDs -> A3-Print-plates scene (one collection/plate, planar build plates, oriented separated meshes, part IDs in reference renders only) and A3-Step-assembly scene (unaltered final-part transforms, explicit stages for base, shoulder, lower arm, elbow, upper arm, wrist, tool dock, gripper, covers/hardware). Matte original materials, orthographic 3/4 studio camera, soft area lights. Video has no subtitles/text overlays.

Passes: (1) freeze/inventory and mesh audit; (2) orient/export/pack, numeric plate and round-trip checks, show sheet; (3) stage animation from real components, verify final transforms and event coverage, preview; (4) final video encode/decode checks and independent review. Initial estimate 15–25 minutes plus render time, adjusted after preview timing.

Acceptance: all source print pieces accounted for exactly once, no purchase/metal parts included as printed; correct mm dimensions, geometry checks, plate bounds/no overlap, material segregation, individual source/export hashes and manifest; actual exported files checked; sequential visible assembly endpoints return to frozen geometry; clean video and editable .blend; visual verification. Installation trajectories, tool access and physical fit must be disclosed if not validated, never inferred from animation.

Final state: extraction, plate packages and reviewed assembly video delivered. Independent rigid-servo-arrival defect corrected; canonical file promoted byte-for-byte and37 affected visible frames replaced. Full MP4 decode passes; plate and decoded-video sheets visually inspected. Physical manufacturing/load gate remains blocked as recorded in README and delivery-check.json.

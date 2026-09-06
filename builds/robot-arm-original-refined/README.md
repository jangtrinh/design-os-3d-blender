# Arm — refinement of the original assembly film

Based on the user-selected `../robot-arm-print-assembly/video/arm-step-by-step.mp4`. Original production files remain untouched. This candidate preserves the original studio, materials, camera direction, assembly station and final hero direction; the last shot is widened8% to retain fingertip clearance.

Camera remains stationary during every installation, subassembly seating, module transfer and wiring operation. Twelve explicit 1.5-second eased transitions connect the held shots. A new module's receiving floor arrives in the wide shot before the camera approaches it. The reviewer's 93 groups become 109 timed assembly/wiring events where mixed carrier/bearing, adapter/cheek and cover/fastener steps need separate arrival. No captions, subtitles or audio.

402 original meshes / 252 physical units are retained. Symmetric fasteners can arrive together; screw heads and shafts stay paired. Captive nuts precede enclosing parts. Interface screws arrive after module seating. Six servo leads route from the lower rear controller enclosure, before outer covers and the final service lid. No separate black power/computer box or loose external supply cable appears.

`arm-original-refined.blend` is the editable scene. `reports/timing.json` and `reports/independent-review/grouped-sequence.json` record unit membership and timed execution order; `plan-grouped-timing.py` moves fork seating ahead of both carrier groups. Delivered `video/arm-step-by-step-refined.mp4`:3020frames,24fps,960×720,125.833s. Full decode passes; decoded shoulder/elbow frames and final hero visually reviewed. Evidence: `reports/media-check.json`, `reports/clearance-acceptance.json` and `reports/hero-prefix-reuse.json`.

This changes assembly presentation only. Retention, adapters, insertion/tool clearance, wire bend/clearance/strain relief, actual electronics, and 250 g multi-minute strength/thermal qualification remain unresolved. A visually seated part is not evidence of physical retention or a manufacturable assembly procedure.

Fork staging uses projected-envelope clearance (`repair-staging-layout.py`, automatically applied by unit preparation). Fork transfers lift120mm, traverse above the servo, then lower; carriers approach axially. Rebuild after staging/timing changes: plan-grouped-timing → build-held-camera → animate-physical-units → animate-organized-wires; normalize the saved library to standalone, then rerun scene and independent overlap checks. Old522afd/e9323 preview revisions are rejected.

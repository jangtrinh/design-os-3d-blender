# Original Arm film refinement

User-selected baseline: ../robot-arm-print-assembly/video/arm-step-by-step.mp4. Preserve studio, lighting, materials, fixed three-quarter direction, subassembly closeups, final assembled pose, and brief grouped-step format. No reuse of the rejected A4 wandering camera. Immutable original source retained.

Scene graph: cloned A3-Step-assembly -> A5-Original-refined. Same 402 production meshes; six original major group parents and added independent physical unit/subassembly parents only where assembly ordering requires. Existing stage/camera/lights retained. Receiving modules built at the original nearby assembly station. Keep camera fixed during install steps; move only in explicit inter-module/seat transition windows. No camera orbit. No rapid return-to-overview between individual steps. Components approach receiving seats; intact servo and screw pairs move rigidly.

Root owns scripts and GUI writes. Independent reviewer writes reports/independent-review only. Correct original order using reviewed mechanical dependencies; group equivalent hardware to preserve brevity, never group concealed nuts with their enclosing parts. Attach interface fasteners after module seating; open rear CPU shell before controller and lid, retain neat wire-before-cover story if existing native cable geometry transfers cleanly. Do not alter mechanical geometry or imply solved manufacturing gates.

Passes: 1) original visual/numeric diagnosis and grouped sequence; 2) candidate native motion + fixed chapter camera; 3) cheap complete animatic and independent saved-file review; 4) final render only after internal visual review (user can steer at any point). Expected preview work 10-15 minutes, final rendering depends on final frame count. No approval gate is invented.

Acceptance: 402 source meshes unchanged and final transforms preserved, exact-once source coverage, paired screws and servo visuals rigid, captive nuts before enclosure, late interface fasteners, camera exactly unchanged during installation, C2 smooth transition windows with zero endpoint velocity, all receiver endpoints framed, no subtitles. Compare representative frames against original decoded video and review temporal preview. Numeric camera gates are evidence only; owner rejection overrides any PASS.

Physical release remains unresolved: 250g multi-minute load, retention, adapters, tool access, collision-free insertion, wiring clearances, power/thermal tests. This revision repairs media, not mechanical qualification.

User correction: remove separate black supply box. Only six organized servo harness routes from enclosed rear CPU; no floating external power cable or external computer/power block in this film.

Visual refinement: initial temporal preview revealed an empty destination during the base-to-station camera move. Corrected by introducing each new module receiver under the held wide camera before closing in. Twelve explicit transitions, 109 assembly/wire events, 2887 scene frames. Final video trims the first 11 offscreen-arrival frames, keeping source frames 12-2887 (2876 frames / 24 fps). Final hero pose matches the original camera exactly. Standalone file normalized so A5 is active on open.

Knowledge catalog was stale during this pass; existing named core/animation/render owner files were read directly. No claim of refreshed catalog or new mechanical evidence.

## Repair user-reported overlap at preview 00:24

Frozen failed scene: `snapshots/before-overlap-repair.blend` (522afd). Full render stopped; its partial frames are not deliverable. Reproduced waiting fork/main surface intersection at source588, failing check exit23. Camera and final transforms alone did not establish correct assembly staging.

Scene graph preserved:402 source meshes,252 rigid units, six wires, original fixed viewing direction. Separate shoulder/elbow fork staging from the main cassette using projected-envelope gap35mm; stage carriers75mm axially. Seat each preloaded fork before either closed bearing/carrier. Keep cameras held during installs. Revised sequence2959frames.

The simplified actuator output visuals overlap flange interfaces during insertion; physical insertion remains unresolved. Independent examination retracts the earlier driver-gap inference: screw heads face outward. Rendering is an assembly visualization, not evidence of manufacturability. No geometry is hidden to conceal these limitations.

Acceptance: waiting fork separated in world and camera projection; no carrier exists during fork transfer; carriers approach axially; final source transforms preserved; visually inspect repaired shoulder and elbow clips before full render. Actual mating fit/retention/load gates remain open.

Second repair: e9323 waiting clearance passed but straight transfer collided with actual servo cases. Replaced with120mmZ lift, horizontal clearance traverse, vertical lowering; each24frames, total72. Camera fit includes swept envelopes and remains held. Candidate11d88f,3031frames. Narrow sweep verification and short visual previews required before full render.

Delivery: final candidate06e248dc,3020video frames,125.833s. Widened hero8% after decoded endpoint exposed fingertip clipping. Reused2931prefix frames only after exact per-frame evaluated-state hashes matched old/new scenes; rendered89suffix frames. Reran scene, independent saved-candidate, narrow sweep, acceptance, full MP4decode; visual inspection of decoded22frame sheet and keyframes passed for reported issue. Manufacturing limits remain unchanged.

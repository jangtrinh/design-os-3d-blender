# Reference keyboard CK-001

## Current revision B handoff, 2026-09-17

Status: REVIEWED_DIGITAL_PROTOTYPE. Current delivery is `delivery/r02`, with archive
`CK-001-revision-B-FullHD.zip`. Geometry-B03, presentation-B03 and verification-B03
are complete; FullHD-B02 contains eleven actual 1920 x 1080 stills and a native
96-frame, 24 fps, 1920 x 1080 MP4 with full decode passed. The source geometry and
final presentation have distinct recorded hashes; the presentation adds reviewed
normal/shading changes while asserting coordinates and face loops unchanged.

Actual cross receivers/stems, two spacebar guides, five D shaft/receiver pairs and
PCB/USB/encoder supports are now modeled. 58 keys were checked at seven nominal
travel positions over 0..3 mm. Form/final gates pass eight representative families;
781 exported meshes pass GLB comparison at frames 1, 7 and 60.

Four available local reference copies are pinned in `runs/reference-review-B01`.
The independent seven-feature visual assessment is accepted; decoded-video review
is separately recorded. Local-copy hashes do not authenticate a vendor drawing or
the original upload transport. Secondary sheets remain derivative design guides.
Physical manufacture remains BLOCKED for retention, tolerance extremes, adhesive/
thread/preload, electrical design, process and bench/load/thermal qualification.

Owner authorization carried forward: "Tất cả assets phải full HD. Chạy render lại
giúp tôi xong báo lại." and "Hãy tiếp tục IMPROVE cho sản phẩm 3D Keyboard ...".
All new media were rendered from the actual scene. Earlier generated lookalike
images are excluded from product source and delivery evidence.

## Historical r01 record below

The following text describes the former r01 state and its then-missing interfaces
and local references. It is preserved for chronology, not current acceptance.

Owner-selected sample: black compact creative keyboard with five silver rotary
knobs, rounded low-profile dark keys, printed white legends, modular black upper
boards, transparent RGB middle layer and aluminum lower plate.

User supplied a perspective photo, blueprint, 360-degree sheet and parts catalog. The photo
is the visual authority; explicit dimensions on the blueprint are dimensional
input. These are design references, not verified vendor manufacturing drawings. The image
files are visible in tool-delivered conversation instructions but have not yet
been exposed as local files; their bytes/hash cannot yet be pinned. Requested
their native paths for an actual independent image-review packet.

purpose: assumed both (owner requested a production-grade workflow demonstration)

Known authored dimensions: 284 x 92 mm footprint; knobs diameter 16 x 18 mm;
keycap upper face 14 x 14 mm and height 9.5 mm; drawn switch width 15.6 mm and
height 11 mm. Blueprint maximum height is inconsistent (32 mm front/table,
41 mm side). The later parts catalog repeats 32 mm, which is the current design
envelope. The older 41 mm dimension remains recorded as a reference conflict.
The implemented stack uses an explicit local knob neck and PCB rebate; those are
engineering adaptations rather than hidden dimensions measured from the photo.

The proof must cover actual visual reconstruction and editable scene/export
quality. Physical keyboard compatibility, switch retention, PCB/electronics,
knob shaft fit, electrical function, polymer process and machining remain
unqualified unless separately specified and tested. A rendered certification
logo or product weight will not be reproduced as a certification claim.

Scope: keycap/switch instances, five knobs with actual slots, black module plates,
PCB/LED/fastener forms, acrylic diffusion, lower chassis, layer-separated assembly,
key travel and knob motion, native editable .blend and reimported GLB. Actual
manufacturing outputs depend on a complete mechanical interface contract.

Prior example builds/desk-node-120 is preserved with its first failed form gate;
the owner changed the sample and no longer requested work on that enclosure.

2026-09-17 progress: geometry-r02 contains 374 native meshes, 58 keys and 5 knobs.
The first completed gate failed: long-plate axial probes exceeded the checker's
fixed 200 mm ray reach, and the knob carried 12 unreferenced vertices. Those
failures are preserved. Independent inspection of this scene found 58 switch
components and no keycap/cover/flange/plate contact at sampled 0/0.5/1/1.5 mm
press travel. That does not establish switch-stem engagement or hardware fit.

2026-09-17 digital review handoff: geometry-r03 form gate and presentation-r02 final
gate passed seven representative families with STL re-import. The saved final scene
has 496 product meshes and 96-frame animation; the corrected independent GLB check
passed 496 meshes at frames 1/7/60 without changing the export. Final media was viewed
and the encoded 96-frame video fully decoded. delivery/r01 and CK-001-review-r01.zip
were created and hash-checked; review.html and CK-001.blend were sent to the host's
open command. Physical manufacture and formal original-reference hash review retain
their BLOCKED statuses, documented in README and the completion report.

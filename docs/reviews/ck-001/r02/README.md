# CK-001 revision B | native Blender delivery

Open `review.html` for the eleven native Full HD views and `CK-001-animation-FullHD.mp4`. The editable
scene is `CK-001.blend`; `CK-001.glb` is the verified exchange export. Both are bound to
scene SHA-256 `de2251261c7d1c17c4150dd3cccc6e42f5a146036916d223801882c4f61c8e16` through the gate, inspection, export, Full HD
manifest and native review evidence.

## Declared digital result

The validated design envelope is 284 × 92 × 32 mm with
58 keys and 5 knobs. Key travel is 3.0 mm; actual fit evidence reports
3.0 mm stem insertion, 0.2 mm receiver ceiling reserve,
2 parallel spacebar guides and 5.0 mm D-shaft engagement.

The GLB contains 781 exported product meshes. All names, triangle counts,
bounds and sampled surfaces pass after reopening at frames 1, 7 and 60. This mesh count is
an exchange/assembly count, not a claim that every mesh is an independently printable part.
The production gate covers 8 declared representative families, listed in
`status.json` and `BOM.json`.

All eleven new delivery PNGs have actual 1920×1080 PNG headers and hashes matching the
Full HD manifest. The MP4 is recorded as 1920×1080, 96 fully decoded frames at 24 fps;
its 96 source frames were hash-checked during package preflight but are intentionally
excluded from this archive. The four files in `reference/` are byte-for-byte source
reference inputs used by the locked review. Their original lower resolutions are preserved;
the Full HD requirement applies only to newly rendered delivery media.

The native eleven-still reference review and final decoded-media review have passed their declared criteria. This is a **REVIEWED_DIGITAL_PROTOTYPE**, not a manufacturing release. Camera framing, simplified markings and restrained RGB remain documented visual differences.

## Manufacture status: BLOCKED

- Keycap/switch insertion, retention force, tolerance stack, wear and process shrinkage need physical coupons.
- Knob D-flat fit and axial retention need physical shaft/knob testing.
- Encoder carrier threads, tightening torque and bonded-riser adhesive shear/peel/creep need physical qualification.
- PCB, encoder and USB footprints/netlist/ESD/power/firmware are not electrically qualified.
- Spacebar guide friction/rattle/wear and assembly bench testing remain open.
- Material/process, slicer/support, dimensional post-process and load/thermal evidence remain open.

The 8-family representative STL set remains marked `UNRELEASED_DIGITAL_CHECK_ONLY` /
`NOT_MANUFACTURING_APPROVED` by its source manifest. No review result upgrades physical,
electrical, material or manufacturing evidence.

## Evidence layout

`reports/` contains the final gate, full-layout fit/layout inventory, export settings and
evidence, the complete source-surface proof used for GLB reopening, frames 1/7/60 reopen
comparison, presentation motion/provenance, Full HD manifests and the locked native-review
target/packet/critique/assessment. Those JSON files intentionally retain their historical
project source paths and hashes. `manifest.json` hashes every copied/generated package file
except itself, and the ZIP is fully CRC-read after creation.

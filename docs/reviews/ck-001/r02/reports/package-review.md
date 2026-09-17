# CK-001 revision-B package code review

Date: 2026-09-17

Scope: code-only handoff for `builds/reference-keyboard/scripts/package_delivery.py`.
No delivery directory or ZIP was created. The eleven-still native review assessment is
now accepted; the Full HD movie/media manifest was still rendering at handoff.

## CLI

```sh
python3 builds/reference-keyboard/scripts/package_delivery.py \
  --presentation <presentation-attempt-dir> \
  --verification <verification-steps-dir> \
  --media <fullhd-media-attempt-dir> \
  --review <native-review-dir> \
  --destination <new-delivery-dir> \
  --archive <new-archive.zip>
```

`--verification` may also point to the verification run directory when it directly
contains `steps/`. `--preflight-only` performs the complete read/hash validation and
does not create the destination or archive.

All six user paths resolve inside the project root. Packaging refuses an existing
destination or archive and performs every required input/hash check before copying.

## Input/schema assumptions

- Presentation attempt: `keyboard.blend`, `motion-contract.json`,
  `motion-report.json`, `provenance.json`, `views.json`.
- Verification steps: latest artifact-bearing `inspect`, `final-gate`, `export` and
  `reopen` attempt directories. Required evidence includes layout/fit/inventory,
  final gate + STL manifest, GLB + export receipts + complete `source-surfaces.json`,
  and `glb-roundtrip.json`.
- Full HD media attempt: `stills.json`, `media-manifest.json`, eleven
  `CK-001-<view>.png` files derived from the manifest view keys, MP4 and its 96 source
  frames. The frame PNGs are verified but deliberately excluded from the package.
- Native review directory: `target.json`, `packet.json`, `critique.json`,
  `assessment.json`, `references.json`, `numeric.json`. All packet/review pins are
  re-hashed against their historical project paths.
- Revision-B design inputs: `layout.json`, `interfaces.json`, `spec-B.json`,
  `dimensions-contract-B.json`, plus the final engineering/visual/package reports.

## Binding and acceptance checks

The packager requires one presentation scene SHA across final gate, layout/fit/
inventory, export settings/evidence, Full HD media and native-review candidate pins.
The final-gate spec SHA must equal the current `spec-B.json` bytes. Export evidence
uses the repository's canonical JSON contract digest for `dimensions-contract-B.json`.

GLB acceptance is derived from actual evidence, with no hard-coded native mesh count:
export-settings count == expected roundtrip names == imported names == scene inventory
set. Reopen evidence must contain exactly frames 1, 7 and 60; every mesh on every frame
must pass triangle-count, bounds and sampled-surface criteria. The actual GLB SHA must
match export settings and the roundtrip receipt. `source-surfaces.json` is hash-bound
and included in the package because it is the geometric source proof for reopen.

The representative production-family count is derived from the revision-B spec/gate,
and the STL manifest must contain exactly that same set. The current verified evidence
derives 8 families and 8 STL files; the code does not hard-code 8 or 781.

Numeric revision-B checks compare the declared contract and actual fit evidence. The
current B02 receipts resolve to 284 x 92 x 32 mm, 58 keys, 5 knobs, 3.0 mm key travel,
3.0 mm stem insertion, 0.2 mm receiver ceiling reserve, 2 spacebar guides and 5.0 mm
D-shaft engagement. Collision checks, D-shaft negative controls and guide travel must
also pass.

Every new delivery PNG is reopened at the PNG header and must be exactly 1920 x 1080,
with a SHA matching both still/media evidence. The video manifest must report a full
decode pass, 1920 x 1080, 96 frames and 24/1 fps; all 96 source-frame PNG hashes and
headers are checked during preflight. Source reference images are copied byte-for-byte
to `reference/` and explicitly remain ORIGINAL INPUTS at their source resolution.

Native review acceptance is preserved exactly in the nested review status. Package-level
status remains `REVIEW_CANDIDATE` even when the eleven-still assessment is accepted,
because the final share-quality decision also includes the completed movie and belongs
to the prime workflow. `README.md` and `review.html` show the actual assessment verdict
without presenting the candidate package as final share acceptance.

## Package contents

- Root: `CK-001.blend`, `CK-001.glb`, 11 Full HD PNGs, Full HD MP4, `README.md`,
  `BOM.json`, `status.json`, `review.html`, `manifest.json`.
- `stl/`: gated representative STL set plus original STL manifest.
- `design/`: layout, interfaces, spec-B, dimensions-contract-B and current engineering
  design notes.
- `reports/`: fit/layout/inventory/gate/export/source-surface/reopen/motion/FullHD
  receipts, engineering/visual/package reports and the six locked native-review JSONs.
- `reference/`: the four source reference images plus an ORIGINAL INPUTS note.

`review.html` uses only local package files and inline CSS. It displays all eleven
views, the Full HD video and direct Blender/GLB links without a CDN.

`manifest.json` records SHA-256 and byte count for every copied/generated package file
except itself. Copied bytes are immediately re-hashed. The ZIP member set must equal
the delivery tree exactly and `ZipFile.testzip()` reads every member for CRC validation.

## Manufacturing boundary

Status always remains `manufacture: BLOCKED`. The export mesh count is not described
as a printable-part count. Remaining physical evidence is stated specifically:
keycap/switch retention and tolerance/wear, D-flat retention, carrier threads/torque,
bonded-riser adhesive shear/peel/creep, real PCB/USB/electrical/ESD/power/firmware,
spacebar friction/rattle/wear, material/process/slicer evidence and assembly bench/load/
thermal tests.

## Validation performed on the code

- Python AST parse: PASS.
- CLI `--help`: PASS.
- Canonical dimensional-contract/export-evidence binding against completed
  Verification-B02: PASS.
- Revision-B numeric/fit extraction against Verification-B02: PASS.
- Final-gate/STL validation against Verification-B02: 8 families / 8 STL, PASS.
- GLB reopen validator against Verification-B02: 781 derived meshes, frames 1/7/60,
  maximum sampled surface error 0.0 mm, PASS.
- Revision-B fail-closed `--preflight-only`: correctly stopped on the still-in-progress
  missing FullHD-B02 `media-manifest.json`; confirmed `delivery/r02` and the target ZIP
  were not created.

The actual revision-B delivery/package command remains intentionally unexecuted until
prime supplies the completed FullHD-B02 media manifest/movie. Presentation-B03,
Verification-B03 and Reference-review-B01 are already the confirmed final input dirs.

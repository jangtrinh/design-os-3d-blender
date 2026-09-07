# Bring your own 3MF

This repo does not ship a licensed real Bambu Studio export (see the Native
Asset Policy) — it ships a validator and a format-faithful fixture generator.
To validate a real file, export your own project 3MF from Bambu Studio and
point the tools at it.

## Why Bambu Studio, not OrcaSlicer

MakerWorld rejects print profiles that originate from OrcaSlicer-produced
project files for MakerWorld-target publishing; the upstream issue asking for
support was closed "not planned" with no root cause published
(https://github.com/OrcaSlicer/OrcaSlicer/issues/2494). Bambu Studio is the
only tool this repo recommends for producing a MakerWorld-target 3MF.

## Exporting a project 3MF

1. Open your sliced project in Bambu Studio (GUI — CLI slicing needs a GPU and
   a display server and is not something this repo automates).
2. Arrange and slice the plate(s) you want to validate.
3. `File -> Export -> Export plate sliced file` (project 3MF), save it
   anywhere on disk.

Bambu Studio also exposes a CLI (`--load-settings`, `--load-filaments`,
`--slice`, `--export-3mf`; canonical usage:
https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage). The CLI
shares the same export code path as the GUI, but several open upstream issues
document CLI-specific breakage (multi-color/segfault and CLI-vs-GUI slicing
differences) that are not proven fixed — when in doubt, export from the GUI.

## Running the validator

```
python3 makerworld-pipeline/scripts/validate_bambu_3mf.py your-export.3mf --json
```

To also run this repo's differential tests against your real file:

```
BAMBU_REAL_3MF=/absolute/path/to/your-export.3mf python3 -m unittest discover -s makerworld-pipeline/tests
```

## What SKIP means

Without `BAMBU_REAL_3MF` set, every test that needs a real Bambu Studio
export **SKIPs** — it does not run, and a SKIP is not a PASS. Only set
`BAMBU_REAL_3MF` when you have a real export on disk; never commit that file
to this repo (Native Asset Policy — it is a local oracle only).

## What fixture-green does not prove

`makerworld-pipeline/tools/make_bambu_like_fixture.py` writes a structurally
plausible Bambu-style 3MF into `makerworld-pipeline/tests/fixtures/` for
CI, where a real Bambu Studio export cannot run (no GPU/display in CI). The
validator passing against that generated fixture only proves the parser
agrees with its own generator's assumptions about the format — it does not
prove the parser handles a real Bambu Studio export correctly. Structural
truth about the real format comes only from the differential checks against a
`BAMBU_REAL_3MF`-supplied file.

The validator's checks are structural/geometric (bounding box, plate
membership, config-key presence, per-check PASS/FAIL/SKIP). It never rates a
model, checks manufacturability, or predicts MakerWorld's acceptance
decision — none of the checklist's MANUAL policy steps in
`docs/publish-checklist.md` are replaced by a green validator run.

Reference for the underlying format: `bbs_3mf.cpp` is the closest thing Bambu
publishes to a schema for its own `Metadata/*.config` files (no separate
schema doc exists) —
https://raw.githubusercontent.com/bambulab/BambuStudio/master/src/libslic3r/Format/bbs_3mf.cpp.
Re-diff this reference whenever you bump your local Bambu Studio version;
these are internal constants with no compatibility guarantee.

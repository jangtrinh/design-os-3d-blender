# makerworld-pipeline

Tooling to prepare a Blender build for MakerWorld: a format-faithful Bambu-3MF
fixture generator plus a real-file validator. It does NOT slice, does NOT
upload, and does NOT automate MakerWorld publishing — those steps are
policy-gated human actions, not a tooling gap (`docs/makerworld-constraints.md`).

If you own a Bambu printer, install **Bambu Studio** (free, official) and use
its GUI to slice and to `File -> Publish to MakerWorld`. This repo never
drives Bambu Studio or MakerWorld on your behalf.

## Entry points

- Validate a real project 3MF:
  `python3 makerworld-pipeline/scripts/validate_bambu_3mf.py <file>.3mf --json`
  (set `BAMBU_REAL_3MF=<path>` to run the differential checks against a real
  Bambu Studio export)
- Generate a format-faithful CI fixture:
  `python3 makerworld-pipeline/tools/make_bambu_like_fixture.py --out <fixture>.3mf --stl <part>.stl [--stl <part2>.stl] [--plates N]`
  (the committed fixtures under `makerworld-pipeline/tests/fixtures/` were made this way from `builds/watch-winder-capsule/parts/`)

## Docs

- `docs/makerworld-constraints.md` — sourced publishing constraints; every
  numeric claim cites a URL
- `docs/publish-checklist.md` — the ordered human publish workflow,
  AUTOMATED vs MANUAL, with the policy reason for each MANUAL step
- `docs/bring-your-own-3mf.md` — exporting a real 3MF from Bambu Studio and
  validating it, including what SKIP means and what a green fixture run does
  not prove

## Delivery status

| Row | Status | Note |
|---|---|---|
| media | NOT_REQUESTED | no reference renders commissioned for this folder |
| motion | NOT_REQUESTED | no animation scope for this folder |
| fit | NOT_REQUESTED | run `production-gate.py` against a specific build's own `spec.json`; this folder ships no printable part of its own |
| manufacture | BLOCKED | no physical print evidence — maintainer has no Bambu printer |
| publish | NOT_REQUESTED | MANUAL: requires a printed-sample photo and a human MakerWorld session — no API exists and the ToS forbids bots |

Silence is never a waiver — every row above is stated explicitly.

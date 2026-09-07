# Publish checklist (MakerWorld)

Ordered steps from a finished Blender build to a live MakerWorld listing. Every
MANUAL step is MANUAL because of a specific platform policy, not because this
repo lacks a script for it — see `docs/makerworld-constraints.md` for the
sourced claim behind each reason below.

| # | Step | AUTOMATED / MANUAL | Reason |
|---|---|---|---|
| 1 | Export a mesh (STL) from the finished `builds/<slug>/*.blend` | AUTOMATED | Repo tooling (`bpy.ops.wm.stl_export`); part of the normal Blender build loop, not MakerWorld-specific |
| 2 | Open the STL in **Bambu Studio** and slice it | MANUAL | MakerWorld-target project files must come from Bambu Studio — MakerWorld rejects OrcaSlicer-produced profiles for this use (see constraints doc); slicing needs a GPU + a display, so it cannot run in this repo's headless/CI path |
| 3 | Export the project 3MF from Bambu Studio (`File -> Export -> Export plate sliced file`) | MANUAL | Same Bambu Studio GUI session as step 2 |
| 4 | Validate the exported 3MF | AUTOMATED | `python3 makerworld-pipeline/scripts/validate_bambu_3mf.py <your-file>.3mf --json` — see `docs/bring-your-own-3mf.md` for what a PASS/SKIP/FAIL each mean |
| 5 | Draft the listing title/description/tags | AUTOMATED (draft) + MANUAL (finalize) | A draft can be templated from the build's own spec/metadata; the AIGC tag on AI-assisted work and the final listing text are a policy-required human call, not something this repo can certify for you |
| 6 | Print the model physically and photograph the real result — once for the model listing image, once per print profile | MANUAL | MakerWorld requires an original real print photo for both the model and each profile (mandatory since 2026-02-05, grace to 2026-05-05 — see constraints doc); there is no tooling path around a physical printer |
| 7 | Publish via the MakerWorld web UI or Bambu Studio's `File -> Publish to MakerWorld` | MANUAL | No official bulk-upload API exists; the user agreement forbids bot/automated access (see constraints doc) — every publish is one human session, one item at a time |

## Policy notes that apply across steps 5-7

- **AIGC tag**: AI-assisted models must be tagged as such; MakerWorld's own
  classifier also applies this tag automatically in some cases. This repo
  cannot decide the tag for you.
- **Anti-bulk throttle**: MakerWorld restricts rapid/bulk uploads and
  near-duplicate variants (same model differing only by pattern, text, or
  scale). Publishing multiple builds from this repo must go through separate,
  human-paced sessions — never scripted in a loop.
- **License and remix attribution**: chosen per listing by the human
  publisher; this repo does not select a license or auto-fill remix credit.

None of steps 5-7 becomes AUTOMATED by a future script — they are platform
policy, permanent, not a backlog item.

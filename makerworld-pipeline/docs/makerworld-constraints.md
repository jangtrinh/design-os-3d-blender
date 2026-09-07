# MakerWorld publishing constraints

Rule for every future edit to this file: a claim with a digit gets a Source
URL in the same table row, or the digit is deleted. No table row states a
number "from memory" or from an unlinked forum paraphrase.

## Sourced constraints

| Claim | Value | Source URL | Verified |
|---|---|---|---|
| Real print photo required for BOTH the model listing image AND each print profile image | Mandatory from 2026-02-05; grace period to 2026-05-05 (renders may only be a secondary/cover image if they match a real photo already on file; a render never replaces the real photo) | https://makerworld.com/en/community/post/1447793 | VERIFIED |
| No official bulk-upload API; the only publish paths are the MakerWorld web UI and Bambu Studio's own `File -> Publish to MakerWorld` | Policy | https://makerworld.com/en/user-agreement | VERIFIED |
| Automated/bot access — "robot, spider, automatic device... AI service" traffic against the site | Prohibited by the user agreement | https://makerworld.com/en/user-agreement | VERIFIED |
| OrcaSlicer-produced project files targeting MakerWorld print profiles | Rejected by MakerWorld; upstream issue closed "not planned", root cause not published by Bambu | https://github.com/OrcaSlicer/OrcaSlicer/issues/2494 | VERIFIED |
| Bambu Studio config key for scarf-joint seams | `filament_scarf_seam_type` (enum none/external/all) plus `filament_scarf_height`, `filament_scarf_gap`, `filament_scarf_length`; the key `enable_scarf_joint_seam` does not exist | https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp | VERIFIED (source grep) |
| `printer_model` string in `project_settings.config` for the A1 mini preset | `Bambu Lab A1 mini` | https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/machine/Bambu%20Lab%20A1%20mini%200.4%20nozzle.json | VERIFIED |
| Boost token validity | 30 days (raised from the original 14 days) | https://forum.bambulab.com/t/boost-token-update-30-days-validity/82009 | VERIFIED (official forum announcement) |
| Print-by-object profiles across printers in cloud slicing | Blocked specifically between A1 mini and P1S because of clearance differences; not a blanket rule | https://forum.bambulab.com/t/automatic-slicing-for-a1-mini-printer-fails-with-print-by-object/99751 | PARTIAL (official reply in thread) |
| Exclusive Model Program eligibility | Requires at least 100 accumulated prints on MakerWorld | https://blog.bambulab.com/rethinking-rewards-makerworld-boost-system/ | VERIFIED |
| Cloud slicing behaviour | One Bambu Studio print profile can serve multiple printers and plate types; the cloud re-slices keeping support/strength settings and adapting printer, filament and plate; compatibility is re-verified at publish | https://blog.bambulab.com/makerworld-one-step-printing | VERIFIED |
| Upload size caps | Raw model files 250 MB combined; print profile 150 MB each | https://forum.bambulab.com/t/max-raw-model-and-print-profile-file-size-limit-too-low/64114 | PARTIAL (forum-sourced, not a guideline page) |
| Hot-score / trending formula | Not published; Bambu Lab stopped publishing the weighting in June 2025, so no "prints weighted N x downloads" figure is citable | https://forum.bambulab.com/t/strange-trending-algorithm | UNVERIFIABLE (formula intentionally opaque) |

## Not verified — do not rely on

These were reported by community/forum sources only, or the primary Bambu/MakerWorld
page returned an access error (402/403) when we tried to fetch it directly. No
number from this list belongs in code, a spec, or a listing without re-checking
the current official page first.

- Exact print-bed dimensions per printer model (they do differ across the
  printer lineup — do not hard-code a millimeter figure from this repo; read
  it from the printer's own profile).
- MakerWorld's post-2025 model-discovery / ranking algorithm. Bambu stopped
  publishing this formula in mid-2025 — treat any specific weighting,
  multiplier, or "score" you see elsewhere (including in this repo's own
  archived drafts) as invented and ignore it.
- Raw-model and print-profile upload size caps, listing video length/size
  limits, and the full license list depth — forum-sourced only.
- The full cross-machine profile-compatibility matrix (which printer pairs
  MakerWorld auto-converts vs. blocks) beyond the general rule that a
  mismatched nozzle produces a slicing error.

## Why this matters for automation

Every row above with `MANUAL`-flavored language in `docs/publish-checklist.md`
traces back to one of the sourced rows in this file (no bulk API, ToS bans
bots, real-photo mandate) — those are platform policy, not a gap in this
repo's tooling. See `docs/publish-checklist.md` for the ordered human
workflow and `docs/bring-your-own-3mf.md` for exporting and validating a real
3MF.

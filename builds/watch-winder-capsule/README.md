# watch-winder-capsule — precision single-slot watch winder (render asset)

Owner-approved concept: `reference/approved-concept.png` (sha256 `605db7906a14a835eebd7aadfd78cb1340f4c28272eea89c1bafcf9c71d6aef4`, copied from `plans/watch-winder-light-model-prompt/reference/`). Built 2026-09-06 in Blender 5.2.0 LTS from native geometry only (no imports, no downloads, no generated meshes).

## Status (separate, per AGENTS.md delivery rule)
| Track | Status | Evidence |
|---|---|---|
| Media (stills) | **DELIVERED** — 16 states in `renders/final/<state>-graphite.png` (hero, hero-right, front, profile, top, rear-quarter, lid-half, open-seated, open, rear, macro-dial, macro-knob, macro-hinge, macro-guilloche, macro-controls, macro-usb; 3072×2048, Cycles ≤2048 spp adaptive 0.01, OpenImageDenoise, identical studio) + `hero-graphite-f8-inspection.png`; sheet `renders/final-states-contact-sheet.png` | `reports/final-renders.json`, `reports/state-cameras.json`, `reports/acceptance.json` |
| Media (film) | `renders/film/watch-winder-capsule-film-1080p.mp4` (385 f) + `watch-winder-capsule-detail-reel-1080p.mp4` (360 f, 6 macro dolly shots) + merged `watch-winder-capsule-full-1080p.mp4` (733 f, 30.5 s, overview → 0.5 s crossfade → detail reel, sha `2015af19…`) — 24 fps 1920×1080: insert cushion+watch → lid closes (dolly push-in) → rotor 360° → orbit 360°; keys/margins `reports/animation-keys.json`, animatic `renders/animatic/animatic-8fps.mp4` | `renders/film/frames-log-*.json`, `encode-and-verify-film.sh` output |
| Motion samples | **PASS (sampled)** — lid 0–100° in 5° steps: 0.0 mm shell penetration, nearest obstacle 0.53 mm (closed seal gap) → 3.5 mm at 100°; rotor 0/90/180/270°: cushion 34.3 mm < 37 mm bore; cushion lift-out clear by 21 mm | `reports/phase1-lid-sweep.json`, `reports/phase2-gate.json`, `renders/phase2-pose-contact-sheet.png` |
| Fit | **VISUALIZATION ONLY** — clearances are declared render tolerances (visor/rim 0.5 mm, shaft/socket 0.2 mm, cushion/bore 2.7 mm), not a tolerance study | `design-parameters.json` (every dimension `provisional_visualization_default`) |
| Manufacture (digital) | **GATE PASS (digital checks only)** — `spec.json` (17 parts, derived from `design-parameters.json` after modelling, not a pre-detail contract) + `scripts/production-gate.py` exit 0 on `watch-winder-capsule-print.blend` (sha `c8d660c8…`): 0 failing checks, 35 unchecked items, 12 standing exclusions; STL round trip of all 17 parts in `parts/` | `reports/gate-report.json`, `parts/manifest.json` |
| Print plates | **LAYOUT DONE (digital)** — 24 printable instances (17 parts + mirrored knob set, 3 legs, 3 feet) oriented for printing and packed on 6 plates: `fdm-petg-01`, `fdm-abs-01`, `fdm-tpu-01` (256×256, Bambu X1C class), `sla-proxy-01/02`, `sla-clear-01` (218×123, Elegoo Saturn class); spacing 6 mm, margin 8 mm (5.5 mm on resin: front_rim is 112 mm on the 123 mm axis); one STL per plate in `plates/` (plate-local mm) + `plates/manifest.json` (orientation, recommended tilt, supports note per part); Cycles stills `renders/plates/plate-*.png` | `reports/print-plates.json`, `reports/print-plates-renders.json`, research `plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md` |
| Manufacture (physical) | **BLOCKED — no physical evidence.** No part printed; visor/rim, cushion/cup and keyed shaft/socket fit trials owed; no load case declared; metal parts modelled as machined, a resin proxy proves shape only | `reports/gate-report.json → exclusions` |

## Production gate 2026-09-06 (owner request: "run the print and production gate audit")
Three gate runs. Run 1 failed 7 parts, run 2 failed 2, run 3 passed 17/17. Geometry changes forced by the gate (all in `design-parameters.json` + pass-02, provisional):
- **Shell opening lip** was a knife edge (wall screen min 1.06 mm): added a flat rim r 52..54.5 at z 43.93 and truncated the inner cavity with a flat ceiling one wall (2.5 mm) below it (z 41.43, 1.29 mm undercut ring). Shell wall screen now min 2.47 mm (p01 2.47), lip 2.81 mm. Bezel sits on the flat; visually the change is 0.6 mm under the bezel.
- **Hinge moving** overlapping solids → unioned in the print bake; shaft nominal length 24 mm (cup floor to socket top); probes for hatch/socket moved 1.3/1.5 mm inside the surface; guilloché/knurl sleeves have faces < 0.3 mm² so the wall screen cannot sample them (declared without `min_wall_mm`, reported unchecked).
- **Keyed socket** is a D-hole: the gate gained `keyed_flat_mm`/`keyed_flat_dir` (schema + `production_gate/features_fasteners.py`); measured Ø6.388 (target 6.4) and flat 2.200 mm (target 2.2).
What "unchecked" means: 15 parts declare no bores (nothing to probe), overhang % is informational for every part (no `max_overhang_area_pct` declared), USB pocket is a `slot` (not measured in v1), guilloché/knurl wall not sampled. Print is FDM PETG for the shell/cover/cup/cushion, SLA resin proxies for the metal parts (materials in `spec.json` are proxies, not the intended production materials).

**Evidence status:** the 16 stills (+ f/8 inspection) were re-rendered 2026-09-06 14:29 from the gate-passed blend `6494186a…` (`reports/final-renders.json`, 53 min GPU; the pre-gate set is kept in `renders/final-pre-gate/`). Both films and the merged film are still from the pre-gate geometry (film blends `bd23c8dc…`); only the 0.6 mm rim lip differs. `reports/acceptance.json` passes on the current blend.

## Owner decisions applied
- 08:20 — build in a fresh Blender file; capture every step (viewport + terminal) → `marketing/step-NN-*-{viewport,screen}.png`.
- 08:45 — owner: "a matte plastic material is enough": shell is **matte dark plastic** (#1A1D24, metallic 0, roughness 0.58); the brief's metallic-titanium values were retired and the walnut variant is kept only as a material preset (`WW_MAT_WALNUT`), not rendered.

## What was measured (evaluated geometry, after depsgraph update)
Rotor/opening axis elevation 50.0° (±0.1 gate) · unit scale 1.0, all mesh scales unity · visor/rotor coaxial 0.00° · 2 knobs mirror error 0.000 mm · 3 feet at Z = 0.000 mm · visor thickness 2.0 mm, closed manifold rim · 31 render meshes: 0 non-manifold / flipped / zero-area · guilloché relief 0.120 mm, 240 spiral rays, twist 0.18 rad · knurl 69 diamonds, 0.150 mm relief, pitch 1.0017 mm · watch hands 306.7° / 59.2° / 210.3° (10:10) · strap max radius 33.8 mm < 37 mm bore, 0.1 mm contact gap. Full numbers: `reports/*.json`.

## Visual inspection (final pixels read, not previews)
Sphere reads round and reclined; dome transparent and bulging with continuous strip reflection; hinge at 12 o'clock, tab at 6 o'clock; watch supported on the cushion, dial legible through the dome; guilloché reads as fine spiral relief; knurls read as diamonds; LED halo restrained (emission 6); rear shows two pill controls + recessed USB-C; feet grounded with soft contact shadows; nothing cropped.
**Deviations kept on purpose:** stance lowered (C.z 95 → 86 mm) and legs thickened (6/3.5 mm radii) to match the concept's low stance; cushion corner radius 8 mm (sharp 45×60 corners would hit the 37 mm bore); service cover moved to the underside so the rear stays clean like the concept; key-light reflection on the dome is larger than in the concept; guilloché rays are only resolved at ≥1024 px.

## Provisional layout (mm, editable — `design-parameters.json`)
Shell R70 wall 2.5, opening r52 (w0 46.86) with flat rim to r54.5 @ z43.93 and cavity ceiling @ z41.43, visor R52 t2, cup r39 floor −24, faceplate 37..48 @ z 28..30, cushion 45×60×38, watch Ø40, knobs Ø22×8 on Ø17 bosses (±X), feet (−48,−42) (48,−42) (0,55).

## Rebuild / re-render
```
# live GUI (MCP): run passes 01..19 in order through agent_runtime.run_file
# finals (headless, Metal): HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend builds/watch-winder-capsule/watch-winder-capsule.blend builds/watch-winder-capsule/scripts/pass-20-final-renders.py -- 2048 0.01 GPU
# acceptance (isolated): HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend builds/watch-winder-capsule/watch-winder-capsule.blend builds/watch-winder-capsule/scripts/pass-21-acceptance-isolated-check.py
# sheets: bash builds/watch-winder-capsule/scripts/make-delivery-sheets.sh
# print bake + spec (headless): HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend builds/watch-winder-capsule/watch-winder-capsule.blend builds/watch-winder-capsule/scripts/pass-29-print-prep-and-spec.py
# plates (headless): HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend builds/watch-winder-capsule/watch-winder-capsule-print.blend builds/watch-winder-capsule/scripts/pass-30-print-plates-layout.py ; then pass-31-print-plates-render.py on watch-winder-capsule-plates.blend -- 1024 0.01 GPU
# gate: python3 scripts/production-gate.py --scene builds/watch-winder-capsule/watch-winder-capsule-print.blend --spec builds/watch-winder-capsule/spec.json --report builds/watch-winder-capsule/reports/gate-report.json --export-dir builds/watch-winder-capsule/parts
```
Scene graph: `WW_ROOT → WW_BODY_FRAME (+40° X) → shell/rim/LED/knobs/controls/USB/hinge-fixed, WW_LID_PIVOT → hinge-moving/visor/tab, WW_ROTOR_PIVOT → cup/guilloché/shaft, WW_CUSHION_UNIT → cushion, WW_WATCH group`; `WW_STAND` (world) → legs/feet; `WW_STUDIO` → cyclorama, lights, cameras. Presets `hero / rear / open` stored in the scene (`ww_presets_json`).

## Public repo note
The public export (`design-os-3d-blender`) carries only what reproduces the build — parameters, spec, scripts, blends, reports, STL parts/plates — plus three JPEG contact sheets as proof of output. Full-resolution stills, films, GIFs, step captures and the concept image are kept privately.

## Exclusions
No HDRI (none local → procedural grey world + area lights); no dispersion (Principled 5.2 has no such input); sampled sweeps are not continuous-collision proof; support polygon is a geometric screen only; STL exists only as the gate round-trip export (`parts/`), not a slicer-validated print job; the film is a keyed visualization (rotor speed, lid motion and insertion path are artistic, not mechanism evidence).

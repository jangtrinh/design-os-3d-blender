# builds/ — robot-arm demo (curated)

Three folders from the 2026-09-05 robot-arm session, trimmed for a public repository.

| Folder | What is included | What is not |
|---|---|---|
| `robot-arm-original-refined/` | Source `.blend`, accepted film `video/arm-step-by-step-refined.mp4`, check renders, `reports/` (overlap diagnosis, clearance acceptance, decoded-frame review, hero-prefix reuse), pass scripts, README/plan | 3,020 raw frames, rejected/draft frame sets, GUI session snapshots |
| `robot-arm-print-assembly/` | 38 STL parts (`parts/`), 5 plate packages STL+3MF (`plates/`), `parts-list.csv`, `assembly-steps.csv`, plate + assembly `.blend`, films (`video/`), key renders, `reports/` (mesh audit, export check, plates manifest, source freeze) | 1,400 animatic/render frames, full render set, zip kit |
| `robot-arm-v2-engineered/` | The 16 scripts/docs the knowledge catalog cites as execution examples (task motion plan, path check, STL export with manifest, video verifier, delivery audit) | The `.blend`, renders and remaining reports |
| `fpv-drone-native/` | Two catalog example scripts (native drone builder + mesh library) | The drone builds themselves |

Each build README states status per domain (media / motion / fit prototype / manufacture). The arm remains **not released for manufacture**: wrist torque margin, output/retention hardware, thermal duty and loaded trials are open. Closed meshes and a good-looking film do not establish those properties.

Gate evidence for the print kit (2026-09-06): `robot-arm-print-assembly/reports/gate-report-260906.json` — 38/38 parts pass topology, dimension and STL round-trip checks (`gate-spec-260906.json`, reproduction: `scripts/gate-import-parts.py`).

To gate any of these parts with the current tooling, write a `spec.json` (see `specs/README.md`) and run `scripts/production-gate.py`; the shipped reports predate the gate and were produced by the per-build scripts in `scripts/` of each folder.

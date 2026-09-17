# builds/ — curated worked builds

Worked examples trimmed for a public repository. Each build README states status per domain (media / motion / fit prototype / manufacture). None is released for manufacture: closed meshes, passing digital gates and good-looking media do not establish physical fit, retention, load, thermal or process properties.

| Folder | What is included | What stays local |
|---|---|---|
| `robot-arm-original-refined/` | Source `.blend`, accepted film `video/arm-step-by-step-refined.mp4`, check renders, `reports/` (overlap diagnosis, clearance acceptance, decoded-frame review, hero-prefix reuse), pass scripts, README/plan | 3,020 raw frames, rejected/draft frame sets, GUI session snapshots |
| `robot-arm-print-assembly/` | 38 STL parts (`parts/`), 5 plate packages STL+3MF (`plates/`), `parts-list.csv`, `assembly-steps.csv`, plate + assembly `.blend`, films (`video/`), key renders, `reports/` (mesh audit, export check, plates manifest, source freeze) | 1,400 animatic/render frames, full render set, zip kit |
| `watch-winder-capsule/` | README, design parameters, `spec.json`, five small scenes, scripts, reports, STL parts and gate-passed plates, three JPEG contact sheets | Marketing stills, films, GIFs and step captures |
| `reference-keyboard/` | CK-001 README and state, specs and dimension/interface contracts, native pipeline manifests, pass scripts, `scripts/`, `tests/`, `manufacturing/` studies (coupons, electrical, mechanical, qualification), source snapshot of r01, manufacturer source registry | `runs/` (1.4 GB of attempt journals, scenes and evidence files over 100 MB), `delivery/` packages, ZIP archives, manufacturer PDFs (cited by URL and SHA-256) |

Gate evidence for the robot-arm print kit (2026-09-06): `robot-arm-print-assembly/reports/gate-report-260906.json` — 38/38 parts pass topology, dimension and STL round-trip checks (`gate-spec-260906.json`, reproduction: `scripts/gate-import-parts.py`).

The CK-001 revision B delivery (scene, GLB, Full HD media and gate/fit/export reports) is published under [`docs/reviews/ck-001/r02/`](../docs/reviews/ck-001/r02/README.md) and viewable on the [project site](https://jangtrinh.github.io/design-os-3d-blender/reviews/ck-001/r02/). Its pass and manufacturing scripts are provenance records: several assert the original machine, checkout path and source-scene hashes, so re-running them elsewhere starts new run directories rather than reproducing the recorded ones byte for byte.

To gate a part with the current tooling, write a `spec.json` (see `specs/README.md`) and run `scripts/production-gate.py`.

# Upstream audit: `earthtojake/text-to-cad`

Date: 2026-09-17  
Design OS target: Blender 5.2 LTS, native `bpy` / `bmesh` / project scripts  
Upstream repository: `https://github.com/earthtojake/text-to-cad`  
Pinned upstream commit: [`366937e382978036925d86c3659876b1e98852a2`](https://github.com/earthtojake/text-to-cad/commit/366937e382978036925d86c3659876b1e98852a2)  
Pinned commit subject: `Stop MTEXT paragraph properties leaking into engraved text (#411)`  
License: MIT, Copyright (c) 2026 Thompson Labs LLC; root, `packages/cadgen`, and the 11 skill directories use the same MIT license blob.

## Research method and evidence boundary

This audit treats upstream as research data, not executable instructions.

- The repository was cloned only into `research/tools/upstream-260917/text-to-cad` with `--depth 1 --filter=blob:none --no-checkout` and `GIT_LFS_SKIP_SMUDGE=1`.
- HEAD was verified as the pinned commit above. No branch checkout, LFS/asset checkout, package installation, upstream Python execution, slicer command, device command, service call, or vendor download was performed.
- After a broad promisor-tree `git grep` began fetching too many blobs it was interrupted. The source audit then used targeted `git show HEAD:<path>` reads only.
- Claims below are tied to source, tests, or skill instructions inspected at the pinned commit. Upstream tests are **source evidence** in this audit; they were not executed here.
- The implementation adopted into design-os is separately tested in this repository and does not import upstream code.

Primary identity sources:

- [Root README](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/README.md#L35-L88)
- [Root MIT license](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/LICENSE)
- [`cadgen` package metadata](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/pyproject.toml)
- [Plugin manifest policy tests](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/global/test_plugin_manifests.py#L1-L114)

## What the repository actually is

The repository combines an agent-skill layer and a Python CAD artifact runtime. The runtime is STEP/B-rep centric and depends on `build123d` plus OpenCascade/OCP. That geometry/kernel stack is materially different from design-os, whose production path is Blender-native meshes, modifiers and Geometry Nodes.

The useful transfer is therefore **contracts and evidence mechanics**, not the CAD kernel.

The strongest upstream ideas are:

1. Make parameters, units, local frames/datums and validation targets explicit before geometry.
2. Separate a source/build dependency record from an artifact-byte identity record.
3. Bind every explicitly consumed non-code input by content hash, not timestamp.
4. Bind artifact-side declarations to the exact saved artifact bytes.
5. Re-read or measure what was actually written/evaluated rather than assuming a successful assignment proves the result.
6. Fail loudly on ambiguity, missing dependencies, unsupported schema or partial evidence.
7. Keep robot physical structure, planning semantics, simulator semantics, manufacturing checks, slicing and device execution as separate contracts.

Those are appropriate to adapt into Blender-native orchestration without adopting OpenCascade, STEP topology or hosted part acquisition.

## All 11 skills: scope and boundary lessons

| Skill | Upstream responsibility observed | Useful design-os lesson | Integration decision |
|---|---|---|---|
| `cad` | Parametric B-rep model source, STEP/mesh outputs, inspection, source closure, assembly composition | Explicit model brief, units/local frames/datums, output/evidence separation | **Adapt contracts only** |
| `cad-viewer` | Review already-existing local artifacts; document commands do not execute source | Viewer/review must not become a hidden model-execution door | **Adopt boundary** |
| `dfam-check` | Mesh printability measurements by process, partial/error reporting | Unmeasured is not pass; units and process assumptions travel with numbers | **Adapt evidence semantics**; keep production gate |
| `dxf` | 2D artifact generation/validation with unit/plane constraints | Explicit units and reject lossy/silent projection | **Adapt validation posture** |
| `gcode` | Slice meshes using explicit printer profile; dry-run then execute; validate output | Separate geometry from process plan and device action | **Concept only**; no slicer execution in this scope |
| `bambu-labs` | Printer-specific upload/start/control, status and confirmation | Dry-run, explicit live action, verify actual device state after request | **Concept only**; no device code |
| `sendcutsend` | Vendor-specific fabrication preflight | Missing/conflicting vendor rule => unknown/request input, not invented pass | **Concept only**; no vendor workflow adoption |
| `step-parts` | Search/download off-the-shelf STEP parts | Provenance/checksum idea is useful | **Exclude downloader/vendor STEP acquisition** |
| `urdf` | Physical robot structure: links, joints, visual/collision/inertial data | Separate frame/unit/geometry roles; physical structure is its own contract | **Adapt semantic separation** |
| `srdf` | MoveIt planning groups/states/end-effectors/collision-disable semantics paired to URDF | Planning semantics must cross-validate against physical model; do not merge them | **Adapt boundary only** |
| `sdf` | Simulator/world frames, physics, sensors, plugins, lights | Simulator semantics and consumer-specific validation stay separate | **Adapt boundary only** |

Skill source examples:

- [`cad` source-vs-document boundary and model contract](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/SKILL.md#L78-L176)
- [`bambu-labs` dry-run/live-device boundary](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/bambu-labs/SKILL.md#L12-L30)
- [`gcode` mesh/slicer/device boundary](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/gcode/SKILL.md#L12-L59)
- [`gcode` rejects STEP/URDF/SDF as slice inputs](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/gcode/SKILL.md#L115-L137)
- [`urdf` physical roles and frame/unit rules](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/urdf/SKILL.md#L29-L38)
- [`srdf` separates URDF/SRDF/SDF responsibilities](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/srdf/SKILL.md#L31-L55)
- [`sdf` explicit frames and SI units](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/sdf/SKILL.md#L33-L50)

## Model contract: parameters are explicit, execution entry is deliberately narrow

The CAD skill makes a useful distinction between a model entry point and its parameterized factory. A model entry is parameterless; dimensions live as named source values/factory arguments, and a configuration is treated as an explicit model identity rather than hidden runtime state. The same skill says environment, current directory, current time and random state must not drive geometry because they are not freshness inputs.

Sources:

- [Model entry/factory rules](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/SKILL.md#L94-L176)
- [CAD brief fields: units, coordinate convention, dimensions, mating, paths, validation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/cad-brief.md#L29-L58)
- [Drawing dimensions become named parameters and validation targets](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/cad-brief.md#L29-L38)
- [Part-local coordinate and datum conventions](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/positioning.md#L20-L77)

### Design-os adaptation

Do not copy the parameterless-decorator runtime or executable Python configuration system. Instead use a small data contract whose numeric intent can be validated before Blender mutation:

- named length parameters with explicit source units and min/value/max,
- named local frames with parent, origin and right-handed orthonormal axes,
- named datums anchored to frames,
- semantic ports anchored to frames,
- separate visual/collision/physical role labels.

`ports` are a **design-os adaptation**. Upstream has datums, mating frames, joints and named assembly relationships, but this audit did not find a generic upstream port schema. A port in design-os is therefore a semantic interface marker, not evidence of fit or a standards-qualified connection.

## Units, frames and placed geometry

The positioning references are unusually strict about local frames: define origin, base plane, up axis, offsets and mating datums before child placement, then validate the resulting artifact. This is directly useful to Blender because a large class of AI 3D failures are frame/unit errors rather than shape-construction errors.

The upstream regression test `test_placed_frames_and_group_labels.py` is also instructive: it records a real failure where a placed circle's displayed center and its analytic `params.center` lived in different frames, yielding a plausible but wrong measurement. The tests require placed analytic centers to agree with their reported world-space row and keep axis directions unit length.

Sources:

- [Positioning core rule](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/positioning.md#L1-L35)
- [Part-local convention](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/positioning.md#L39-L77)
- [Placed-frame regression tests](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_placed_frames_and_group_labels.py#L1-L18)
- [World-placement invariants](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_placed_frames_and_group_labels.py#L134-L188)

### Design-os adaptation

The new native contract normalizes authored `mm`/`m` lengths to metres because this repository uses Blender's `1 BU = 1 m` convention. It accepts rigid right-handed frames only. It does not yet solve a frame hierarchy into world transforms; it validates references, cycles, local origins and bases. Actual Blender transforms remain a separate build/verification concern.

## Source identity: explicit inputs, content hashes, no timestamp trust

`declare_input()` is one of the most transferable pieces of upstream design. A non-CAD file read by a model is explicitly declared as a dependency; the next run compares content hash, so replacing a file with identical bytes remains current and changing bytes at the same path becomes stale. The function also refuses a model's own output as an input.

Sources:

- [`declare_input` rationale and implementation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/inputs.py#L1-L81)
- [Changed bytes / identical bytes / missing file regression cases](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_discovered_file_inputs.py#L1-L18)
- [Own-output-as-input controls](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_discovered_file_inputs.py#L228-L351)

### Design-os adaptation

`bind_source_evidence()` records only explicitly supplied, root-bounded files. It does **not** discover Python import closure, infer project roots, inspect Blender dependencies, or hash environment state. `source_evidence_current()` re-hashes those exact declared files and can additionally compare the normalized contract digest.

This narrower mechanism is intentional. It gives a reusable source-evidence primitive without adding a daemon/module-eviction/import-audit subsystem to Blender.

## Import isolation and stale-cache defense: useful lesson, excluded implementation

Upstream's warm-worker system addresses several real Python hazards:

- Import roots are the script directory plus caller `PYTHONPATH`; no directory-name heuristic invents a project root.
- The generator loader compiles current source bytes instead of trusting `.pyc`.
- First-party project modules are evicted between builds while runtime/site-packages/C extensions are protected.
- Bytecode writes are disabled in the model window to avoid same-second, same-size stale `.pyc` acceptance.
- Executed first-party files plus declared data inputs form the source closure.

Sources:

- [Explicit import roots](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/_internal/import_roots.py#L1-L41)
- [Runtime root tests](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_import_roots.py#L76-L121)
- [Current-source compilation and module isolation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/_internal/generation_runner.py#L59-L136)
- [No-stale-bytecode contract](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_no_stale_bytecode.py#L1-L96)
- [First-party closure and eviction rationale](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/_internal/source_hash.py#L307-L392)

### Design-os decision

Do **not** port this module eviction/cache machinery into Blender as part of this task. Blender is a long-lived embedded Python application with its own loaded extensions and state ownership. The existing design-os `agent_runtime.load_lib` dependency mechanism is the appropriate bounded reload surface. The transferable lesson is explicit ownership and explicit dependency identity, not upstream's process implementation.

## Artifact identity is independent from source identity

This is the most valuable architectural pattern in the upstream store.

`records.py` documents two indexes:

- `document/<sha256(document bytes)> -> tree`: artifact-to-artifact identity for viewers/readers.
- `output/<sha256(output path)> -> model`: code-side memory for provenance/staleness.

The generated document itself is intentionally independent from its source script. A model record separately stores source closure, child pins and output SHA values.

Sources:

- [Record structure and source/artifact split](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/store/records.py#L1-L35)
- [Document-byte tree index](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/store/records.py#L128-L173)
- [Code-side output provenance](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/store/records.py#L204-L241)

### Exact saved bytes beat in-memory assumptions

`test_tree_reflects_written_step.py` documents a particularly strong falsifier: OpenCascade STEP translation can be lossy enough that an in-memory shape and the re-imported STEP differ. The upstream build therefore re-reads the written STEP and makes document-side reads describe the written bytes, not a pre-export object.

Source: [written-document tree regression suite](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_tree_reflects_written_step.py#L1-L18)

For design-os this maps cleanly to export evidence: hash the exact exported bytes and, when the export semantics matter, verify by re-import through the existing isolated export verifier. A receipt containing a `.glb` suffix and SHA is not itself proof that the GLB is valid.

## Sidecars: declaration binding is separate from provenance

Upstream source sidecars contain artifact-adjacent declarations such as kinematics/appearance/animation and carry `documentHash` to bind those declarations to exact STEP bytes. The tests explicitly reject a sidecar at another schema or one whose `documentHash` no longer matches the document. They also explicitly forbid using the sidecar as a provenance fallback.

Sources:

- [Sidecar schema and artifact binding implementation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/_internal/source_sidecar.py)
- [Schema/binding/provenance tests](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_source_sidecar_schema_gate.py#L1-L158)

### Design-os decision

Adopt the **separation**, not the exact sidecar schema. The new contract receipt binds contract/source/export evidence but does not embed provenance into model geometry or claim that a sidecar proves geometry. Executable JavaScript animation expressions and other upstream runtime declarations are excluded.

## Result tree is not a parametric feature tree

The upstream `geometry-tree` is a content-addressed result graph. It stores native B-rep component objects, world-placed occurrences, child-tree links, an assembly hierarchy, bbox and stats. It deduplicates/links child results. This is useful architecture for result identity and assemblies, but it is **not** a CAD feature-history tree such as sketch → extrude → fillet → hole.

Source: [`cadgen.store.trees` structure](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/store/trees.py#L1-L28)

The positioning reference further warns that labels on boolean-subtracted or fused feature history are not reliable STEP feature history.

Source: [feature-label limitation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/cad/references/positioning.md#L116-L127)

### Design-os decision

Do not describe or implement the upstream result tree as Blender feature history. If design-os later needs a reusable component/occurrence graph, borrow the content-addressed link/occurrence idea separately from modeling operations.

## Publish race: useful evidence principle, no concurrency subsystem adopted

Upstream re-hashes the source closure before publishing a build, refusing to replace a current record with a result already known stale. The implementation explicitly states that check-then-rename is not a perfect concurrency exclusion and the ordinary freshness gate catches the remaining race later.

Source: [publish decision](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/store/publish.py#L1-L43)

Design-os should adopt the principle that source/export evidence must be revision-bound. The new helper does not add a concurrent build store or publication arbitration.

## DfAM: keep manufacturing predicates separate and honest

The DfAM source/tests make two lessons concrete:

1. Known-geometry fixtures are more informative than snapshotting whatever the checker previously emitted.
2. One failed measurement family must produce an explicit partial report; missing wall/support data cannot be read as a clean result.

The test suite also checks unit-scale suspicion and measures multi-body wall thickness per body so fit gaps are not misclassified as walls.

Source: [DfAM tests](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/skills/dfam-check/test_dfam_tool.py#L1-L9), [partial-result controls](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/skills/dfam-check/test_dfam_tool.py#L295-L345)

### Design-os decision

This reinforces the existing `production-gate.py`; it does not replace it. The new parametric contract declares intent and evidence identity. Production gate remains the digital topology/dimension/manufacture screen for printable parts, and physical fit/load/thermal evidence remains separate.

## URDF, SRDF and SDF: separation worth preserving

The repository treats robot-description formats as distinct sources of truth:

- **URDF**: physical link/joint structure, frames, joint limits, inertials, visual geometry and collision geometry.
- **SRDF**: MoveIt planning groups/states, end effectors, passive/virtual joints and disabled collision pairs, cross-validated against a paired URDF.
- **SDF**: simulator/world semantics, explicit `relative_to` / `expressed_in` frames, physics, sensors, plugins and lights.

The URDF validator's own data model keeps visual and collision mesh path lists separate, and joint values use native radians/metres. It validates the link/joint graph as a rooted tree. The SRDF validator rejects unknown joints, invalid chain direction, out-of-limit group states and unknown disabled-collision links. SDF validation distinguishes internal checks from optional/required consumer-side `gz` checks.

Sources:

- [URDF source model and units](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/urdf_source.py#L15-L110)
- [URDF graph validation](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/packages/cadgen/src/cadgen/urdf_source.py#L202-L378)
- [URDF CLI negative controls](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_urdf_validate_cli.py#L88-L205)
- [SRDF/URDF boundary](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/srdf/SKILL.md#L31-L55)
- [SRDF cross-file negative controls](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_srdf_validate_cli.py#L110-L179)
- [SDF source/boundary rules](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/sdf/SKILL.md#L33-L50)
- [SDF optional vs required consumer check](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/tests/python/packages/cadgen/test_sdf_validate_cli.py#L123-L183)

### Design-os adaptation

The new contract's `roles` vocabulary (`visual`, `collision`, `physical`) is only a semantic separation mechanism inspired by this boundary. It does not validate URDF, collision geometry, inertial correctness or simulation behavior.

## Device handoff: request is not result

The Bambu skill is explicitly staged:

1. validated G-code exists,
2. read printer status,
3. dry-run exact handoff,
4. upload-only,
5. live start only with explicit execution/start intent,
6. confirm actual printer state after the request.

It says MQTT publish is only a start request, not proof the print started.

Source: [Bambu safety rules](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/bambu-labs/SKILL.md#L12-L30), [handoff sequencing](https://github.com/earthtojake/text-to-cad/blob/366937e382978036925d86c3659876b1e98852a2/skills/bambu-labs/SKILL.md#L73-L87)

### Design-os decision

Adopt the generic orchestration lesson only: command/request success is not state-change evidence. No printer, slicer, FTPS, MQTT or hardware code is introduced by this work.

## Native implementation added to design-os

Files:

- `scripts/boilerplates/bp_parametric_contract.py`
- `tests/boilerplates/test_parametric_contract.py`

The helper is standard-library only and independent of Blender/OpenCascade. Its public surface is deliberately small:

```python
normalize_contract(raw)
bind_source_evidence(contract, paths, root)
source_evidence_current(receipt, root, contract=None)
bind_export_evidence(contract, paths, root, scene_sha256=None, spec_sha256=None)
```

### Normalized contract shape

For a length parameter:

```python
normalized["parameters"]["height"] == {
    "unit": "mm",
    "values_si": {"value": 0.03, "min": 0.01, "max": 0.08},
}
```

Frames expose local `origin_m` and normalized right-handed `axes`; datums expose `position_m`. Frame parents are reference-checked and cycle-checked. Port frame/role references are checked. Named keys are stripped only after collision detection, so `"height"` and `" height "` are an error rather than an overwrite.

Evidence paths are root-relative in receipts, may not escape the root, and reject symlink/parent-alias spelling. This prevents two spellings from silently naming one evidence file. Exact bytes are SHA-256 hashed. Export `format` is only the filename suffix label; it is not a format-validation result.

Current local source hashes after the final host contract run:

```text
bp_parametric_contract.py       a6b914351332bcd8a3e494e924bbcf76a3df8022b47062851e4017b776863898
test_parametric_contract.py     7d983d0c3cd1363bdfa9b6ec9dd6a9599dbeb489638f4f6c0500b3cfd4a0e1c4
```

These are the final helper/test filesystem hashes observed after the 8-test host contract passed. The prime integration workflow still owns shared catalog/publication binding.

### Local validation

Executed in the design-os host Python, not upstream:

```bash
python3 -m unittest tests.boilerplates.test_parametric_contract -v
python3 -m py_compile scripts/boilerplates/bp_parametric_contract.py tests/boilerplates/test_parametric_contract.py
git diff --check -- scripts/boilerplates/bp_parametric_contract.py tests/boilerplates/test_parametric_contract.py
```

Final result after validation refinements: **8 tests passed**. Controls include:

- mm and m normalize to equal SI lengths,
- no mutation of input dictionaries,
- non-finite/type/out-of-range/unknown-unit rejection,
- unknown frame parent, parent cycle, non-orthogonal and left-handed frame rejection,
- datum/port/role reference checks,
- canonical-name collision rejection,
- port-role shape/duplicate/reference checks,
- source content current/stale behavior independent of replacement mtime,
- contract digest changes invalidate an optionally contract-bound source receipt,
- missing/duplicate/outside-root/symlink source paths rejected,
- export receipt hashes exact output bytes and validates optional SHA syntax without claiming format validity.

## Adopt / adapt / exclude

### Adopt as design principles

- Explicit source units, local frame/origin, datums and named parameters before geometry.
- Numeric falsifiers plus visual review; successful execution alone is insufficient.
- Exact-byte artifact identity separate from code/source provenance.
- Declared external inputs bound by content hash rather than timestamp.
- Closed vocabularies, ambiguity rejection and schema/version gates.
- Explicit partial/unknown states instead of interpreting missing evidence as pass.
- Distinct physical/planning/simulation/manufacturing/process/device contracts.
- State change verification after a command/request.

### Adapt to Blender-native implementation

- Length parameters normalize to Blender metres rather than build123d's mm conventions.
- Upstream frames/datums/joints/mating intent become simple frame/datum/port metadata; Blender transforms remain authored by native scene code.
- Upstream source closure becomes declared-file receipts only; design-os does not adopt import auditing/eviction here.
- Upstream document/record split becomes source-evidence and export-evidence receipts bound to the design contract.
- URDF visual/collision/physical separation becomes a generic role-label vocabulary only.

### Explicitly exclude from this integration

- `build123d`, OpenCascade/OCP, CadQuery or any other B-rep kernel dependency.
- STEP-native topology selectors, B-rep component serialization or OpenCascade tolerances as Blender proof.
- Hosted vendor part search/download and vendor STEP acquisition.
- Upstream LFS model assets.
- Slicer installation/execution, G-code generation, printer upload/start/control or network service calls.
- SendCutSend/vendor process automation.
- Warm-worker daemon, global first-party `sys.modules` eviction and upstream bytecode/cache subsystem.
- Executable formula strings, JavaScript animation expressions, arbitrary environment/time/random inputs.
- Treating the upstream result tree as a parametric feature-history model.

## Relationship to the existing production gate

The new contract **does not replace or weaken** `scripts/production-gate.py`.

| Evidence layer | Question answered |
|---|---|
| Parametric contract | What values/units/frames/datums/ports/semantic roles were declared? |
| Source receipt | Which explicitly declared source/input bytes was this contract bound to? |
| Blender numeric verification | Did native evaluated geometry respond as intended? |
| Export receipt | Which exact output bytes were produced, and optionally which scene/spec hashes were associated? |
| Existing production gate | Does the delivered print candidate satisfy its digital topology/dimension/manufacturing-screen predicates? |
| Physical validation | Did real fit/load/thermal/printing/manufacturing succeed? Separate evidence. |

This layering is the main integration result from the text-to-cad audit.

## Remaining limitations and next useful tests

The current native contract is deliberately narrower than the upstream system:

- Parameters support length scalars in `mm` or `m` only. Angles, counts, tolerances, material/process enums and dimensionless values need separate typed contracts if a real consumer requires them.
- Frames validate local rigid bases and parent graphs but do not compose them into world matrices.
- Datums are points only; axes/planes/cylinders are not yet first-class datum types.
- Ports are semantic markers and carry no fit, clearance, hardware or standards evidence.
- Role labels do not prove that named Blender objects actually satisfy visual/collision/physical requirements.
- Source evidence covers explicitly declared files only. It does not infer transitive imports, Blender text blocks, add-ons, environment variables or connected data.
- Export evidence is a byte receipt. Format validity still requires the repository's real export/re-import verifier where relevant.
- No upstream test suite was run, so upstream behavior claims remain source/test-intent observations at the pinned commit rather than independent runtime certification.
- No manufacturing qualification follows from the contract. Existing production and physical gates remain authoritative for their own predicates.

If expanded later, the most useful next native tests are: typed angle/count parameters; frame-hierarchy world composition against Blender matrices; explicit port mate/clearance predicates; object-to-role binding; and contract/source/export receipts integrated into a real build receipt without duplicating production-gate evidence.

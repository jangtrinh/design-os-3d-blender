# Visual component brief template

Use this template for one component and one declared primary view, supported by a bounded view set. Keep prior prompt history separate. This is a manual build input and visual-review checklist. Export the frozen coverage receipts to the [HQ coverage gate](hq-coverage-gate.md) for executable file/binding/dimension checks. Apply the [ORC component workflow](orc-component-workflow.md).

## 1. Outcome and non-claims

- Component / purpose:
- Visual target:
- Fixed owner decisions:
- Not claimed: hidden construction, function, loads, manufacture, standards, or dimensions absent from evidence.

## 2. Evidence and authority

| Source | Pixel size | Verified hash | Role | Conflicts |
|---|---:|---|---|---|
| Primary view |  |  | count, silhouette, attachments |  |
| Corroborating view |  |  | envelope/camera only |  |
| Detail tile |  |  | local shape/material only |  |

- Image inspection tool used:
- Authority rule: primary view governs appearance; applicable technical documentation governs mechanical function, routing and installation. Never merge visual counts across views or treat visual count as the required instrument count.

### CAD or drawing evidence

| Source URL or local file | Verified hash / units | Exact model or analogue | Supported dimension/profile | Unsupported inference |
|---|---|---|---|---|
|  |  |  |  |  |

CAD is reference-only; no retrieved mesh enters a native build. If no useful CAD is found, record the search boundary and the missing fact that actually blocks work.

### Mechanical specification and installation evidence

| Mechanical question | Official document / actual revision / page or section | Applicable service / conditions | Documented rule | Modeling decision / unresolved selection |
|---|---|---|---|---|
|  |  |  |  |  |

Read these documents before reasoning from the image about function. Distinguish a requirement from an optional manufacturer example. Project-specific P&ID/GA and selected-equipment documents govern when supplied; otherwise label the proposed layout illustrative and retain unknown operating conditions. Record any visual conflict and a concrete resolution before changing accepted topology.

## 3. Frames and camera separation

- Model axes:
- Primary camera side/elevation:
- Screen frame: `(u,v)=(x/W,y/H)`, origin top-left.
- Foreshortened axes:
- Rule preventing camera perspective from becoming mesh proportions:
- Camera-first flip test before physical-ratio changes:

## 4. Fixed envelope

| Quantity | Value | Fixed / provisional / unknown | Flip evidence |
|---|---:|---|---|
| X |  |  |  |
| Y |  |  |  |
| Z |  |  |  |

### Site scale and integration contract

- Declared site scale and shared model units:
- Shared site axes/origin and camera convention:
- Physical envelope source, units, and exact match / analogue / proxy status:
- Tabletop/display envelope and visible protrusions or service allowance:
- No independent or anisotropic component scaling:

| External port | Elevation / position | Axis and orientation | Interface role | Counterpart / whole-site check |
|---|---|---|---|---|
|  |  |  |  |  |

An illustrative site envelope supports composition and interface review only. It does not select equipment, capacity, rating, duty, or manufacturer identity. Recheck all modules together after placement: footprint, port alignment, route continuity, protrusion/access separation, and camera visibility.

## 5. Primary-view inventory

Count only what is visible in the authority view. Use `at least N visible` when occlusion blocks an exact count.

| System/part | Count | Screen region | Attached to | Confidence | Named object/subassembly |
|---|---:|---|---|---|---|
|  |  |  |  |  |  |

## 6. Normalized landmarks

Record observed pixels first; normalized values are screen targets, not physical measurements.

| Landmark | Pixels `(x,y)` or extent | Normalized `(u,v)` or ratio | Uncertainty | Use |
|---|---|---|---|---|
|  |  |  |  |  |

## 7. Silhouette and shape hierarchy

Inspect every supplied detail before choosing primitives. Record section, taper, shoulder/edge treatment, transition into the adjacent part, candidate construction, and a comparison falsifier. A name such as wheel, pipe, or flange is not a shape specification.

| Region / reference crop | Visible contour or transition | Candidate construction | Comparison falsifier |
|---|---|---|---|
|  |  |  |  |

Separate material highlights from confirmed grooves or steps. Unseen cross-sections remain unknown.

### Critical

1.

### Important

-

### Optional

-

## 8. Attachment graph and axes

- `parent` → connector/interface → `child`.
- State flow/body axis separately from bonnet, wheel, gauge-face, or control axis.
- Every visible child touches its parent or has a named connector; proximity is not attachment.
- Explicit UNKNOWN attachment/depth:

| Interface / adjacent objects | Local axis / units | Surface or interval owned by each part | Allowed contact, gap, or overlap | Exact numeric/visual check |
|---|---|---|---|---|
|  |  |  |  |  |

Declare intentional overlaps. For hollow pipe–flange joints, assign each inner-wall interval to one part. A clear centreline ray does not prove the surrounding walls are free of overlap. Record both endpoints.

### Instrument station map

| Station ID / measurement purpose | Technical source / section | Circuit and inlet/outlet role / host | Verified host port and adapter | Family and local mount port | Reading orientation / access | Fact / design choice / unknown |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Do not inherit proxy coordinates as a station. Separate head geometry from its process adapter; a geometric mount port proves no process rating. Align each instance to the documented connection scheme; use one mounting rule per repeated station type. Trace both process circuits before placement. Unknown as-built ownership remains UNKNOWN; a document-based proposed circuit must be labeled a design choice. Record conditional thermal protection, probe immersion and service clearance without inventing operating values.

## 9. Material intent

| Part group | Colour/value family | Finish | Shape cue it must reveal |
|---|---|---|---|
|  |  |  |  |

Materials cannot substitute for missing geometry.

## 10. Reusable subassembly proposals

| Constructor | Parameters supported by evidence | Returned parts/invariant | Keep local until |
|---|---|---|---|
|  |  |  | visual qualification |

## 11. Incremental recipe and reuse contract

Choose the highest-risk identity subcomponent first. The controller builds a new family prototype; qualified modules may use their supported parameters. Pass count follows complexity.

- Frozen source path/hash and acceptance scope:
- Local axes, pivot, dimensions, and port/interface transforms:
- Supported parameters and invariant geometry/materials:
- Nominal and second intended-scale checks plus attachment check:
- Local or shared constructor; concrete second consumer or explicit owner library request, with qualification status:
- Regression proof: observed failure, supported range, command or evidence, expected result. Re-run after instancing or changing supported parameters.

| Pass | Scope | Comparison target | Exact pass/fail observation |
|---|---|---|---|
| 1 — camera/blockout |  |  |  |
| 2 — primary form |  |  |  |
| 3 — attachments |  |  |  |
| 4 — supports/interfaces |  |  |  |
| 5 — detail/material |  |  |  |

Visual iteration precedes numeric audit when the owner selected visual-first. Do not advance past a failed critical feature. Cheap assertions still run in every pass; full audit follows visual repair on the final saved source.

## 12. Exact falsifiers

1. Wrong primary-view count or side.
2. Wrong silhouette/profile at a named landmark.
3. Detached child, missing connector, intersecting controls, or conflated axes.
4. Camera mismatch "fixed" by distorting physical geometry.
5. An UNKNOWN silently promoted to FACT.

## 13. Uncertainty ledger

| Tier | Statement | Confidence | Cheapest flip evidence | Current treatment |
|---|---|---:|---|---|
| FACT |  |  |  |  |
| INFERENCE |  |  |  |  |
| ASSUMPTION |  |  |  |  |
| UNKNOWN |  |  |  |  |

## 14. Acceptance handoff

- Critical systems checked:
- Primary comparison artifact:
- Corroborating views:
- Numeric audit deferred/run:
- Remaining visible deltas:
- Local comparisons at similar apparent scale with lighting that exposes section and transitions:
- Independent review of proportions, sections, junctions, steps, and hardware:
- Every known visible discrepancy repaired or explicitly named; mesh counts/topology are not visual acceptance.
- Verdict: `continue` / `refine-spec` / `refine-code` / `request-input` / `stop`.

## 15. Complete close-up and output coverage

The reviewer inventories reference features before viewing the candidate. Include every supplied tile and junction, not only an isolated module.

| Reference tile | Object + interface | Shot / required framing | Native-density proof and target resolution | Falsifier / exact check | Reviewer / verdict / issue |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Before HQ, every critical row requires inspected proof, not a planned filename. Cover visible terminal bores, hardware rims, both gauge endpoints, and small branch joins. Mark hidden or non-applicable features with a reason. Source, camera, or output-resolution changes renew affected proofs.

### Frozen review input — manual decisions and executable receipt checks

- Immutable candidate path + source SHA; shot/settings manifest hash:
- Assigned reviewer coverage and evidence paths:
- Controller hash comparison at dispatch and report receipt; repairs use a new revision:
- Changed objects/interfaces/shots and invalidated evidence after repair:
- Required overview/close-up shots and authorized output scope:
- Output-density regions: transitions, contact/coplanar risk, dial/text, metal highlight:
- Per-family hardware pixel ratio and matched-camera comparison:
- Near-clip check and proof region within the target frame:
- Coverage JSON, pinned requirements/shot plan, gate report, guarded launch command:
- Final source SHA; image/settings manifest; every delivered shot inspected:
- Remaining defects and coverage not performed:
- Separate acceptance scopes: prototype / whole form / final detail:
- Media revision plan; preserve old images and decisions:
- Next-component measures: owner-discovered misses, repair rounds, HQ-only defects, discarded render seconds, qualified reuse; model cost only when available:

Mechanical assertions and visual proof remain separate. Missing proof or a stale hash does not pass this manual checklist, and the checklist creates no owner approval gate.

# ORC component reconstruction workflow

Use this manual workflow to reconstruct an ORC model component from reference imagery. It combines manual visual decisions with the explicit [HQ coverage gate](hq-coverage-gate.md); source files, manifests, audits, and original images remain the authority for the current state. Use the [component brief template](orc-component-brief-template.md) for a build contract and the [worked Separator example](orc-separator-worked-example.md) for the evidence sequence.

## Durable decisions

- Record the deliverable purpose first. `render-only` does not establish print, fit, load, pressure, or standards evidence. A future print/both build must follow the project spec and production-gate requirements.
- The declared primary 3/4 view controls visible count, placement, facing, and silhouette. Read every close-up for local form, but do not merge features from conflicting views.
- CAD and drawings may support a named profile or architecture. State whether each is an exact match or an analogue. Do not import retrieved geometry or use an analogue as a dimension, identity, or compliance claim.
- Keep accepted footprint and owner decisions. Separate physical measurements, display choices, body envelope, and protrusions. Mark unsupported depth or section detail as `UNKNOWN`.
- The controller creates the first native prototype for a new geometry family. A qualified constructor may then be implemented or reused within its explicit parameter range.

## Five stages

| Stage | Work | Required exit evidence |
|---|---|---|
| 1. Reconcile sources | Inspect the sheet, close-ups, and bounded CAD research. Record FACT, INFERENCE, and UNKNOWN. | An active brief maps each critical feature to a source, object/interface, and proof shot. |
| 2. Prototype the identity risk | Build the highest-risk local profile or subassembly at comparable display scale. | Matched silhouette/section evidence, independent review, and any required owner prototype decision. |
| 3. Assemble the form | Place accepted prototypes, body, branches, frame, and ports camera-first. | Primary-view and useful corroborating views show proportions, continuous routes, and interfaces. |
| 4. Detail and verify | Add hardware, fittings, instruments, and materials. Review every tile and inter-module junction. | Current saved source is audited; visual coverage names repaired and remaining discrepancies. |
| 5. Freeze and review output | Freeze source/camera/settings and make output-density proofs before authorized HQ work. | Source/hash-bound manifest, original-image review coverage, and separate technical, visual, and owner-acceptance status. |

Owner checkpoints apply to a new prototype and whole form. They are not a request loop for every fastener. If a material decision is missing, request the narrow decision while continuing independent work.

## Build a falsifiable brief

Use the [canonical template](orc-component-brief-template.md). A named wheel, pipe, or flange is not a geometry specification. For every critical region, record section/profile, thickness, taper, shoulder, edge treatment, transition to its neighbor, candidate construction, and the observation that would reject it.

Record pixels before ratios. Pixel ratios are screen targets, not millimetres. Match camera side, projection, and foreshortening before changing mesh proportions. Time-box CAD research and record its boundary; further research is only useful when its result would change a visual form or interface decision.

## Reuse contract and interface ownership

Keep a constructor local until it has a second real consumer. Its contract names frozen source/hash, acceptance scope, local axes/pivot, dimensions, ports, supported parameters, invariants, and the nominal plus second intended-scale checks. A previous instance passing does not qualify an arbitrary variant.

Every repaired defect has a regression proof beside its constructor: scope, supported parameter range, command or visual proof, and expected result. Re-run it after instancing or supported-parameter changes.

For every attachment, declare both objects, axes/units, the surface or axial interval each owns, allowed contact/gap/overlap, and its specific check. Intentional overlap may be valid. Hollow pipe-to-flange joints require exactly one owner for every inner-wall interval; a clear centreline ray cannot detect competing surrounding walls.

## Verify the right claim

Run cheap execution assertions in every pass. Audit the final saved source for object existence, envelope, transforms, interfaces/contacts, and evaluated topology. Numeric success does not prove visual likeness.

The reviewer writes expected source features before opening the candidate. Coverage includes every supplied detail tile and every junction; a feature clipped from one shot needs another shot. Check silhouette, profile, wheel/spoke fullness, gauges and mounts, hardware containment, support contacts, and complete pipe routes in the primary plus corroborating views.

When the same defect survives two repairs, change the construction hypothesis. After three unresolved attempts, use `request-input` rather than hiding the uncertainty with more primitives, samples, or materials.

## Freeze, output-density proof, and revision

Before review, keep the candidate at a unique path and record its source hash plus shot/settings manifest hash. The dispatch receipt identifies both path and hash. The reviewer examines only that revision; the controller compares the same hashes when receiving the result. Repairs create a new revision and name the objects, interfaces, shots, and evidence invalidated by the change. The [HQ coverage command](hq-coverage-gate.md) checks the declared file and receipt bindings. Choosing sufficient coverage and judging visual likeness remain manual; this adds no new owner checkpoint.

Use the template coverage table: `reference → object/interface → shot → native-density proof → falsifier → reviewer/verdict`. Before HQ, each critical row must have inspected proof at final output density. Export those rows to the coverage JSON and use `hq-coverage-gate.py --launch` for the guarded render-only route. Changing source, camera, or resolution invalidates the affected proof.

Check camera near clipping and record the proof region within the target frame. Compare hardware proportions by family as well as contact and containment. Preview every risky region at output density before the full batch: contacts, metal highlights, lettering, dial marks, and terminal bores. Enlarging a small preview creates no new evidence. If an image shows striping or a shutter-like surface, use camera-ray diagnostics and an A/B crop to distinguish geometry from material before changing samples or shading.

The manifest records source/script hashes, camera/settings, and each image. Verify format, dimensions, bit depth, and hash, then inspect every original final image. Package integrity is not a visual review. Preserve pre-change media and record whether it belongs to an older source revision.

Report these separately: built; numeric checked; visual reviewed with coverage; owner accepted with scope; media current; fit/manufacture.

## Role routing

| Role | Owns | Does not decide |
|---|---|---|
| Controller | source reconciliation, new-family prototype, integration, source freeze, final decision | owner acceptance or unsupported engineering facts |
| Mechanical tier | inventory, hashes, bounded CAD research, existing checks | hidden count/profile or manufacturer match |
| Workhorse | qualified reuse and contracted detail | new source authority or shared-source changes outside ownership |
| Independent reviewer | source-first coverage and falsifiers | edits to the artifact being reviewed |

Each dispatch states read/write paths, acceptance criteria, verification command, report path, and isolation boundary. Parallel work requires independent ownership.

## Start the next component

1. Inspect the source sheet and every close-up; reconcile site/footprint decisions.
2. Check whether a qualified family is actually reusable; list what remains new.
3. Complete the brief's evidence, conflicts, interfaces, and coverage tables.
4. Prototype the highest-risk visual family and define its falsifiers before building the rest.
5. Keep unresolved visual and evidence gaps visible; do not transfer them to a shared library.

Only record efficiency measures when the runtime provides them. This workflow does not claim a model-cost, quality, or time benchmark.

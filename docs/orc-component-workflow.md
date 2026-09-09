# ORC component reconstruction workflow

Use this manual workflow to reconstruct an ORC model component from reference imagery. It combines manual visual decisions with the explicit [HQ coverage gate](hq-coverage-gate.md); source files, manifests, audits, and original images remain the authority for the current state. Use the [component brief template](orc-component-brief-template.md) for a build contract and the [worked Separator example](orc-separator-worked-example.md) for the evidence sequence.

## Durable decisions

- Record the deliverable purpose first. `render-only` does not establish print, fit, load, pressure, or standards evidence. A future print/both build must follow the project spec and production-gate requirements.
- The declared primary 3/4 view controls visual silhouette and appearance; close-ups refine local form. Mechanical function, flow routing, instrument locations, connections and installation constraints follow applicable technical documents. Record conflicts explicitly; an image does not override a documented mechanical requirement.
- CAD and drawings may support a named profile or architecture. State whether each is an exact match or an analogue. Do not import retrieved geometry or use an analogue as a dimension, identity, or compliance claim.
- Keep accepted footprint and owner decisions. Separate physical measurements, display choices, body envelope, and protrusions. Mark unsupported depth or section detail as `UNKNOWN`.
- The controller creates the first native prototype for a new geometry family. A qualified constructor may then be implemented or reused within its explicit parameter range.

## Five stages

| Stage | Work | Required exit evidence |
|---|---|---|
| 1. Reconcile sources | Inspect the sheet and close-ups; immediately read applicable manufacturer specifications, installation manuals and drawings for mechanical questions. Record FACT, design choice, and UNKNOWN. | An active brief maps each critical feature to a source, object/interface, and proof shot; technical rules cite document revision, page/section and applicability. |
| 2. Prototype the identity risk | Build the highest-risk local profile or subassembly at comparable display scale. | Matched silhouette/section evidence, independent review, and any required owner prototype decision. |
| 3. Assemble the form | Place accepted prototypes, body, branches, frame, and ports from source anchors and declared interfaces; use the camera to verify visibility. | Primary-view and useful corroborating views show proportions, continuous routes, and interfaces. |
| 4. Detail and verify | Add hardware, fittings, instruments, and materials. Review every tile and inter-module junction. | Current saved source is audited; visual coverage names repaired and remaining discrepancies. |
| 5. Freeze and review output | Freeze source/camera/settings and make output-density proofs before authorized HQ work. | Source/hash-bound manifest, original-image review coverage, and separate technical, visual, and owner-acceptance status. |

Owner checkpoints apply to a new prototype and whole form. They are not a request loop for every fastener. If a material decision is missing, request the narrow decision while continuing independent work.

## Build a falsifiable brief

Use the [canonical template](orc-component-brief-template.md). A named wheel, pipe, or flange is not a geometry specification. For every critical region, record section/profile, thickness, taper, shoulder, edge treatment, transition to its neighbor, candidate construction, and the observation that would reject it.

Record pixels before ratios. Pixel ratios are screen targets, not millimetres. Match camera side, projection, and foreshortening before changing mesh proportions. Research must answer a named geometry, interface or mechanical-function question; read the relevant specification immediately rather than speculate from an image. Verify the document's actual edition and printed page, not just its URL filename.

## Technical evidence before mechanical choices

Use project-specific P&IDs, general arrangements and selected-equipment drawings when available. Otherwise find official manufacturer installation manuals and technical specifications, check their service/applicability, and derive an explicitly illustrative layout. A generic manual supplies constraints and assembly relationships; it does not identify the equipment or establish this plant's operating conditions.

For every technical decision, record the source and section, what it actually requires, conditions under which it applies, and the resulting modeling rule. Distinguish manufacturer requirements from optional choices. For example, remote gauge support, siphons, diaphragm seals and thermowell lengths are not universal defaults. Keep unresolved ratings, material selection and process values separate from model geometry.

Missing project documents do not block source research or reusable head construction. Ask the owner only for a material choice that remains after research, with a concrete proposed layout or alternatives. Do not silently rearrange an accepted form when the technical correction changes its topology. Preserve prior evidence and identify the scope to replace.

## Site scale and inter-component integration

Choose one declared site scale before replacing components; never independently stretch a component to make it fit. For each module, record the source and units for its physical envelope, the corresponding tabletop/display envelope, and visible protrusions or service allowance. A matched vendor GA, CAD file, or catalogue may support an envelope only when its match and units are recorded; proxy and analogue envelopes remain explicitly provisional.

Keep shared units and axes across the assembly. Declare each cross-component port by name, elevation, axis/orientation, and interface role. Test all modules together after placement: footprint, body/protrusion separation, port alignment, routes, access envelope, and the camera view. An illustrative scale or envelope does not select equipment, capacity, rating, duty, or manufacturer identity.

## Reuse contract and interface ownership

Keep a constructor local until it has a second real consumer, unless the owner explicitly requests a reusable library. An early library remains a candidate until its visual and interface proofs pass. Its contract names frozen source/hash, acceptance scope, local axes/pivot, dimensions, ports, supported parameters, invariants, and the nominal plus second intended-scale checks. A previous instance passing does not qualify an arbitrary variant.

Every repaired defect has a regression proof beside its constructor: scope, supported parameter range, command or visual proof, and expected result. Re-run it after instancing or supported-parameter changes.

For every attachment, declare both objects, axes/units, the surface or axial interval each owns, allowed contact/gap/overlap, and its specific check. Intentional overlap may be valid. Hollow pipe-to-flange joints require exactly one owner for every inner-wall interval; a clear centreline ray cannot detect competing surrounding walls.

At pipe/reducer interfaces, verify endpoint position, tangent direction and bore radius together. Coincident centers can hide a perpendicular opening. After loading an existing scene, reuse its camera/light setup or replace it deliberately; assert the intended environment counts before rendering.

## Instrument stations precede instances

A detailed gauge must not inherit an arbitrary proxy coordinate. Before placing it, record the measurement purpose, process circuit, inlet/outlet or other station role, applicable installation source, owning pipe/nozzle, verified host port, instrument family, face orientation and access clearance. Each family declares a local mount port; placement aligns that port to the specified adapter. A geometric port is not proof of a pressure-rated process connection. Repeated station types share the same mounting rule.

When only the image exists, trace visible connections as visual evidence and research the mechanical architecture independently. Preserve unknown as-built ownership; a proposed document-based route is a design choice, not a discovered P&ID. Separate pressure indicators, temperature sensors/transmitters and valve actuators by function. Do not assign every similar blue head to the same family or move a tap merely to expose it in a camera.

Qualify the housing and process adapter separately. Pressure assemblies need a documented tap/isolation/connection scheme; thermal or media protection is conditional. Temperature assemblies need a distinct process connection, sensor/thermowell choice, immersion target and extension/head relationship. Check circuit continuity and separation before mounting, then verify contact, insertion (where specified), display access and service clearance.

Build one detailed analog/digital family before mass instances. Macro proof must show minor/major dial ticks, needle taper and hub, bezel/window layers, display recess and housing grip relief as applicable. For identical instances, share mesh/font datablocks under independent transform roots; a separately built variant requires its own qualification. Recheck port contact and reading access after instancing.

Reopen the installed assembly and verify actual host bore openings, specified probe-tip positions, shared head data and inter-assembly clearances. A prototype pass does not qualify the assembled station. Record exactly which collision pairs and views were checked; distinguish a visible display from verified maintenance/removal access.

## Verify the right claim

Run cheap execution assertions in every pass. Audit the final saved source for object existence, envelope, transforms, interfaces/contacts, and evaluated topology. Numeric success does not prove visual likeness.

The reviewer writes expected source features before opening the candidate. Coverage includes every supplied detail tile and every junction; a feature clipped from one shot needs another shot. Check silhouette, profile, wheel/spoke fullness, gauges and mounts, hardware containment, support contacts, and complete pipe routes in the primary plus corroborating views.

For detailed hardware, presence is only the first check. Name the visible assembly layers and what distinguishes this family from a generic primitive: for a cabinet, door return/seal, hinge leaves/pin/knuckles, opposed lock, HMI bezel/recess, operator head/collar/stem, and framed louver/filter construction. Tie each expected feature to a reference or applicable technical source and inspect its close-up. Clean topology, readable labels, and an unclipped object cannot substitute for this construction review. These are manual review criteria, not an automated fidelity score.

Validate a surprising measurement before changing the model. Signed-volume checks on tiny meshes far from the origin use evaluated coordinates shifted to a local centroid and float64 scalar arithmetic; world-origin float32 triple products can reverse the reported sign through cancellation. Inspect topology and the measurement implementation separately. A corrected measurement must be rerun on the unchanged candidate before it justifies any geometry repair.

When the same defect survives two repairs, change the construction hypothesis. After three unresolved attempts, use `request-input` rather than hiding the uncertainty with more primitives, samples, or materials.

## Freeze, output-density proof, and revision

Before review, keep the candidate at a unique path and record its source hash plus shot/settings manifest hash. The dispatch receipt identifies both path and hash. The reviewer examines only that revision; the controller compares the same hashes when receiving the result. Review transformations and comparison sheets write only to a separate review directory, never source or delivery paths; the controller rechecks delivery-asset hashes after review finishes. Repairs create a new revision and name the objects, interfaces, shots, and evidence invalidated by the change. The [HQ coverage command](hq-coverage-gate.md) checks the declared file and receipt bindings. Choosing sufficient coverage and judging visual likeness remain manual; this adds no new owner checkpoint.

Use the template coverage table: `reference → object/interface → shot → native-density proof → falsifier → reviewer/verdict`. Before HQ, each critical row must have inspected proof at final output density. Export those rows to the coverage JSON and use `hq-coverage-gate.py --launch` for the guarded render-only route. Direct Blender, MCP, and direct headless rendering bypass this opt-in guard; name the route actually used. Changing source, camera, or resolution invalidates the affected proof.

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

1. Declare the site scale, shared units/axes, source-backed or provisional envelope, and named external ports before placing the component.
2. Inspect the source sheet and every close-up; read technical documentation for mechanical logic and reconcile site/footprint decisions.
3. Check whether a qualified family is actually reusable; list what remains new.
4. Complete the brief's evidence, conflicts, interfaces, and coverage tables.
5. Prototype the highest-risk visual family and define its falsifiers before building the rest.
6. Keep unresolved visual and evidence gaps visible; do not transfer them to a shared library.

Only record efficiency measures when the runtime provides them. This workflow does not claim a model-cost, quality, or time benchmark.

# Worked example: ORC Separator evidence flow

This is a completed render-only reconstruction example. It demonstrates how to use the [ORC workflow](orc-component-workflow.md) and [component brief template](orc-component-brief-template.md). It does not make the Separator's dimensions, render settings, durations, or output count defaults for another component.

## Evidence boundary

- **FACT:** the delivered candidate was independently audited as closed, consistently oriented, and positive-volume; original-image review was split between controller and independent reviewer.
- **FACT:** a terminal artifact passed topology, centreline-bore rays, and previews before appearing in final output.
- **INFERENCE:** competing hollow-shell intervals caused the artifact after camera-ray and source-constructor inspection ruled out a material-only cause.
- **UNKNOWN:** manufacturer identity, hidden construction, pressure rating, printability, physical fit, and owner appearance acceptance.

The private project retains its source, audit, manifests, original images, and chronological journal. They are historical provenance, not public runnable dependencies.

## 1. Reconcile the reference before modelling

1. Declare a primary 3/4 image and bounded supporting views. The primary controls visible inventory, orientation, and silhouette.
2. Inspect every close-up before selecting primitives. Record local section, taper, shoulders, edge treatment, and neighbor transitions.
3. Fill the brief's evidence, uncertainty, attachment, and coverage tables. Keep unobserved cross-sections and hidden attachments as `UNKNOWN`.
4. Time-box CAD research. An analogue can justify a construction vocabulary; it cannot establish the depicted unit's dimensions or identity.

The wellhead pilot supplied two reusable lessons: the primary view corrected an over-read inventory from a generative analysis, and the small wheel close-up established a five-spoke crowned wheel rather than a generic flat primitive. Those are source-reconciliation lessons, not a general model comparison.

## 2. Assign ownership before dispatch

| Role | Separator example responsibility | Boundary |
|---|---|---|
| Controller | reconciled source, integrated detail, froze the candidate and output settings | did not treat technical review as owner acceptance |
| Mechanical support | bounded inventory and repeatable checks | did not infer hidden count or manufacturer identity |
| Workhorse | implemented contracted local detail | did not alter unowned shared geometry |
| Independent reviewer | reviewed source-first, source-bound shot coverage | did not mutate the candidate |

For a new family, the controller builds the first native prototype. A reusable constructor is promoted only after a second real consumer and its regression proof have passed at supported scales.

## 3. Build against named falsifiers

The Separator brief mapped every reference tile to a detail group, interface, and planned output shot. Typical falsifiers were a floating instrument, a buried washer, an unreadable gauge endpoint, a disconnected pipe, or a clipped terminal bore.

The render-only implementation still used saved-source audits for mesh integrity, interfaces, transforms, bores, and clearances. These checks establish the narrow technical result they actually test; they do not establish likeness, manufacture, or owner approval.

### Filled interface and coverage examples

The following are executable brief rows, not generic reminders. Replace symbolic intervals with the component's measured coordinates before building.

| Reference feature | Object and owned interval | Required shot/proof | Falsifier |
|---|---|---|---|
| Open vapor terminal | Sweep owns axial `x=[a,b)`; flange neck owns `x=[b,c]`; one inner wall per interval | Terminal close-up plus output-density bore crop | A camera ray hits both walls in the same interval, or the crop shows a stripe/seam inside the bore |
| Layered terminal profile | Neck, flange face, seal, and hardware each own named surfaces | Oblique profile crop at final output density | The flange reads as one featureless disc, hardware crosses the rim, or the bore is capped |
| Mounted gauge | Parent port, riser, body, face, and both endpoint connectors | One shot contains both endpoints and a readable face | A pipe ends in air, a mount floats, or the frame clips either endpoint |

The coverage receipt for those rows records: candidate path/hash, shot/settings manifest hash, crop file and bounds, reviewer, result, and which source/camera/resolution change would invalidate it.

For a generic project, run its own declared audit after the final mutation:

```sh
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/headless-run.sh --blend builds/<component>/<candidate>.blend \
  builds/<component>/audit.py
```

The exact `<component>` paths and audit script must come from that component's brief. Do not run a private historical example command in a public checkout that does not contain its artifacts.

### Owner checkpoint versus routine continuation

Ask a fresh owner question when the reference conflict would change an accepted footprint, whole-form composition, or the deliverable scope; when the source cannot resolve a material visual decision; when proposed output costs exceed existing authorization; or when requesting owner appearance acceptance. Continue without a new question when applying a repair inside the accepted source/hash-bound scope, running declared regression checks, or reusing a qualified constructor within its documented parameters. A prior prototype approval does not approve the whole component or a later high-quality batch.

### Bounded native worker prompt

After the controller has made the first prototype of a new geometry family, a native worker may receive a prompt of this shape:

```text
Task: Implement the declared pipe-to-flange interface in the existing candidate.
Read: builds/<component>/active-brief.md, builds/<component>/interfaces.md,
      builds/<component>/constructors/<family>.py.
May modify: builds/<component>/constructors/<family>.py and its local regression check.
Must not modify: accepted source snapshots, shared libraries, cameras, materials, or other components.
Acceptance: each axial interval has one inner-wall owner; declared bore and clearance checks pass;
            output-density terminal crop has no stripe or seam; emit AGENT_OK with the candidate hash.
Report: builds/<component>/reports/<family>-interface.md.
Run: bash scripts/headless-run.sh --blend builds/<component>/<candidate>.blend \
       builds/<component>/checks/check-interface.py
```

The controller reviews the worker's diff, reruns the acceptance check on the final saved source, and sends the frozen revision to an independent reviewer. A worker report is not acceptance evidence by itself.

## 4. Diagnose an output-only failure at the shared boundary

The first final-output batch showed a stripe at the vapor terminal. It had survived earlier topology, centreline-ray, and preview checks. The controller did not increase samples or mask it with material changes.

Instead, the team traced camera rays across the bore and inspected the constructors. The diagnostic found the pipe sweep and flange neck occupying the same hollow-wall interval. The repair gave the flange neck that interval, ended the sweep at its entrance, re-audited the candidate, and made a native-density A/B crop before another output batch.

Use this pattern for any visible pipe terminal:

1. Declare the axial or surface interval owned by each adjoining object in the brief.
2. Check the clear bore and the surrounding wall; a centreline ray alone is insufficient.
3. If output shows striping, use camera-ray hits and an output-density crop to falsify geometry, normal, and material hypotheses.
4. Repair the shared boundary once, rerun the component audit, and regenerate only evidence invalidated by the repair.

## 5. Spend render budget in the evidence order

Start with inexpensive primary-view blockouts and close-up previews. Before an expensive batch, render only each critical crop at its intended output pixel density: terminal bores, profile transitions, gauge endpoints, hardware rims, and specular contacts. A full HQ schedule follows the coverage table; eight shots were a bounded Separator delivery choice, not a default count. Do not use a larger sample count to compensate for unresolved geometry or framing.

## 6. Freeze a reviewable revision

Before dispatching high-quality output:

1. Save the candidate at a unique revision path.
2. Record the candidate hash and shot/settings manifest hash in the dispatch receipt.
3. Make critical-interface proofs at final pixel density.
4. Assign every final image to a reviewer and record the shot coverage.

The recipient verifies both hashes before reviewing. A source, camera, or resolution change invalidates affected proof. Repairs use a new revision; original media is retained and never presented as evidence for the repaired source. These are manual review controls, not automatically enforced gates.

## 7. Package and inspect independently

An output package may verify file names, source binding, image hashes, dimensions, bit depth, and archive integrity. It cannot determine whether an image has correct silhouette, readable hardware, continuous contacts, or sufficient framing. Inspect every original final image and each critical native-density crop.

Use the repository's current packaging script only if the component brief names one. The generic validation order is:

```sh
python3 scripts/blender-knowledge.py check
python3 -m unittest discover -s tests/knowledge
```

Those public checks validate the public repository's knowledge and tests. They do not recreate or visually certify private project media.

## 8. Close with narrow claims

The example can support these outcomes: a source-bound technical audit, a scoped visual review with named coverage, and output package integrity. It cannot support claims about physical manufacture, engineering operation, exact vendor identity, or owner acceptance.

For the next component, begin again with the template: reconcile the primary view and close-ups, declare interfaces, prototype the highest-risk family, and let the actual component evidence determine its audit and proof set.

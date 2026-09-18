# New product workflow contract

Copy this outline into the new build's task record and replace placeholders before
execution. Empty fields mean unresolved evidence, never implicit acceptance. This
is a controller template; no generic validator interprets this Markdown.

## Identity and authority

| Field | Record |
|---|---|
| Build and current revision | `<slug>` / `<revision>` |
| Purpose and owner instruction | `render-only`, `print` or `both`; quote authorization |
| Workspace / runtime | Actual root, host, Blender/Python version/build |
| Source input | Path, SHA-256, scene/view layer, units and initial frame |
| Primary visual reference | Local bytes, hash, origin, intended authority |
| Secondary references | Per-image role, conflicts, inferred or generated content |
| Engineering source | Exact part/revision/page; read vs search-only vs unavailable |
| Authored dimensions | Separate targets, tolerances and worst-case conditions |
| Unresolved requirements | Which work needs input; which independent work can proceed |
| Motion contract (any animation) | Frame rate, distinct rendered states, what the owner accepts as smooth |
| Pass inventory | Every intended pass has a manifest step; `scripts/check-pass-coverage.py` clean or excused with a reason |

## Pass contract

For each pass, specify one writer, the reviewed source/dependencies, consumed
artifacts, exclusive output directory, timeout, numerical postconditions and the
evidence consumer. Use the real manifest schema, not a shell task list:

```json
{
  "version": 1,
  "pipeline_id": "replace-with-build-id",
  "steps": [
    {
      "id": "build",
      "script": "builds/<slug>/pass-01-build.py",
      "inputs": ["builds/<slug>/spec.json"],
      "depends_on": [],
      "artifact_inputs": [],
      "outputs": ["model.blend", "measurements.json"],
      "required_postconditions": ["parts_measured"],
      "timeout_seconds": 180
    },
    {
      "id": "inspect",
      "script": "builds/<slug>/pass-02-inspect.py",
      "inputs": ["builds/<slug>/spec.json"],
      "depends_on": ["build"],
      "artifact_inputs": ["build:model.blend"],
      "outputs": ["inspection.json"],
      "required_postconditions": ["parts_checked", "failed_checks"],
      "timeout_seconds": 180
    }
  ]
}
```

The example paths are placeholders and deliberately do not execute as shipped.
Choose timeouts from the actual workload. Declare all imported helper files, not
just the pass file. Required postconditions must be finite numbers, not booleans
or hash strings. Keep hashes in receipts or extra metadata. The inspection payload
must assert its failure conditions; naming `failed_checks` alone does not require
that its value be zero. A downstream artifact producer must also be in depends_on.

## Stage exits

| Stage | Exit evidence | Reject / pause when |
|---|---|---|
| Contract and blockout | Authored dimensions, source roles, scene graph, viewed blockout | Critical geometry/function is still guessed |
| Form and interfaces | Saved geometry, gate on declared families, actual mating surfaces | Shape, topology, stroke extremes or contacts fail |
| Presentation | Same geometry identity, view plan, materials, actual driver behavior | Unexplained geometry changes or hidden expected details |
| Export | Explicit product selection, export bytes, separate-process reimport | Extra scene objects, units, names, triangles or sampled poses disagree |
| Final media | Actual pixel headers, complete source frames, full decode, inspected originals | Wrong aspect, crop, faceting, missing frames or revision mismatch |
| Visual review | Locked target/candidate/proofs and attributed feature findings | Missing view, unknown critical feature or changed source |
| Engineering candidate | Exact component/process choices, changed-interface checks, specimens | Unselected hardware, electrical mismatch or unverified joint construction |
| Physical pilot | Real specimens, calibrated records, paired history and design bindings | Missing/raw-stale/synthetic records, unsafe fit or failed interval |

Family reuse must state the qualified parameter range, second real consumer and
shared-geometry proof. Declare separate instance checks for placement and contact.
Do not count scene meshes as independently manufacturing-qualified parts.

## Failure and recovery record

Record expected behavior, actual saved evidence, root cause (`spec`, `code`,
`checker`, `environment` or `missing evidence`), a discriminating control, the
minimum owned correction and affected downstream proofs. Preserve the failed
journal. Inspect an already-saved artifact after a wrapper failure before deciding
whether anything needs rebuilding. New directory names do not reset failure budgets.

## Media brief

Set output width/height, aspect, views, detail subjects, camera poses, lighting,
samples/denoiser/device, fps and duration. Lock a short animatic before a long film.
At final aspect and apparent scale, preflight every view, including isolated
undersides and first/last motion frames. Review the highest-risk metal edge,
legend and translucent surface before batching. Deliver native render output for
a request to render the actual model; generated concept images are separate assets.

When geometry changes, identify old media as historical. Reuse existing owner
authorization when it covers the new render; otherwise obtain one scoped decision
with a measured estimate. Preserve source references at original resolution.

## Closure ledger

| Claim / domain | Current artifact and checker pins | Coverage / uncertainty | Result | Missing evidence / next action |
|---|---|---|---|---|
| Geometry | `<scene/spec/checker>` | `<families, features, wall sampling>` | `unassessed` | `<action>` |
| Motion and interfaces | `<scene/config/report>` | `<instances, samples, exclusions>` | `unassessed` | `<action>` |
| Export | `<source/export/reimport-report>` | `<frames, surface predicate>` | `unassessed` | `<action>` |
| Media and visual review | `<scene/settings/images/video/review>` | `<views actually inspected>` | `unassessed` | `<action>` |
| Electrical and firmware | `<parts/netlist/ECAD/build>` | `<logic vs ERC/DRC vs target/bench>` | `unassessed` | `<action>` |
| Physical qualification | `<snapshot/specimen/raw/calibration/process>` | `<pilot counts, uncertainty, cohort>` | `no measurements` | `<action>` |

There is intentionally no fabricated sample result. Keep a failed/unknown domain
visible while completing independent work. A whole-project release requires every
criterion applicable to the owner's purpose, not a majority of passing rows.

## Handoff and retrospective

Preflight package bindings before copying; rehash copied files and check archive
membership/CRC. Keep source, local run evidence and curated public media distinct.
For each new lesson, record incident → cause → reusable action → falsifier →
implementation/test → exact scope → skill/topic route. Reuse a current skill and
one bounded topic. Publish only after source reviews settle, test actual routes,
and verify the committed tree works without local-only ignored files.

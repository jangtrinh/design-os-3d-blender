# Check reference coverage before HQ rendering

The coverage gate checks whether every declared critical reference feature has a current, inspected proof receipt. It verifies frozen files, review bindings, PNG dimensions and required review fields. It does not measure visual similarity, authenticate reviewers, establish owner approval or qualify manufacture.

Use it after form/camera acceptance and native-density proof review, before the full HQ batch. Keep proof renders cheap: use native-resolution render regions, rather than enlarging small full-frame previews. The controller chooses the feature inventory; an omitted feature cannot be discovered by this checker.

## One guarded entry point

```bash
python3 scripts/hq-coverage-gate.py \
  --coverage path/to/coverage.json \
  --report path/to/coverage-report.json
```

Choose a new report path for every invocation; existing reports are preserved. Exit 0 means the declared critical coverage receipts pass. Exit 1 means incomplete or failed coverage. Exit 2 means invalid input. Read the structured report and final `AGENT_OK` / `AGENT_FAIL` line for the next action.

After the required owner authorization and any separate production gates, add `--launch`:

```bash
python3 scripts/hq-coverage-gate.py \
  --coverage path/to/coverage.json \
  --report path/to/coverage-launch-report.json \
  --launch
```

This invokes the existing headless runner with the pinned scene and render pass only after the check passes. Version 1 launch supports `purpose: render-only` and `mode: preflight`. A `retrospective` record validates existing evidence but cannot launch a render. Direct Blender, MCP and direct headless calls remain available: this is an explicit guarded route, not a global interception hook.

A launch failure must remain a failure. Coverage success alone does not establish that a render completed; retain the renderer's own manifest and inspect its final images.

Start from the [deliberately incomplete starter](../specs/hq-coverage-starter/README.md). It includes all three JSON files and must fail until real inputs and reviews replace the placeholders.

## Prepare the evidence

1. Freeze the source, render pass, shot plan and feature requirements at stable paths. Each pin has `path` and `sha256`. Paths, including nested reference/report/proof paths, resolve relative to the coverage JSON's directory.
2. Define every critical feature in the requirements file: source reference pin, object/interface names, shot ID and the visible condition that would reject it. Keep supplied but unreviewed corroborating views visible as uncovered; do not silently remove inconvenient rows.
3. Freeze each shot's dimensions, camera and inspection visibility state. Record settings in the shot plan. For a macro proof, render a region of that target frame at native density. Verify the near clipping plane and the entire target region visually.
4. Have the reviewer inspect the actual reference and proof. Record feature ID, verdict, reviewer, a concrete comparison note, pinned report, proof pin, matching shot snapshot, framing/near-clip checks and all four current input hashes.
5. Run the command. Fix missing/stale/failed evidence before launch. A source, script, shot-plan or requirements change invalidates bindings; refresh them only after reviewing the affected evidence.

The review's proof `region` is `[x, y, width, height]` inside the target shot frame. The actual PNG must have exactly that width and height. A full-frame proof uses `[0, 0, target_width, target_height]`. The checker validates image structure and dimensions, but cannot determine whether an image was secretly upscaled or rendered from the declared camera. Those remain explicit reviewer responsibilities.

The initial implementation uses whole-file hashes. Even an unrelated scene edit makes the source binding stale. Do not silently reuse old receipts; per-object invalidation needs its own proven dependency mechanism before it can replace this conservative rule.

## Coverage JSON shape

The root contains `version: 1`, `mode`, `purpose`, pins named `candidate`, `render_script`, `shot_plan`, `requirements`, and a `reviews` list. The shot plan has nonempty `settings` and uniquely named `shots`; each shot supplies `id`, `size`, `camera` and `visibility`. Requirements have a nonempty `features` list with at least one critical feature.

Each review records:

```json
{
  "feature": "inlet-bore",
  "reviewer": "reviewer-name",
  "verdict": "pending",
  "note": "Inspect clean concentric lip, open bore and seated hardware.",
  "report": {"path": "review.md", "sha256": "UNSET"},
  "binding": {
    "candidate_sha256": "UNSET",
    "render_script_sha256": "UNSET",
    "shot_plan_sha256": "UNSET",
    "requirements_sha256": "UNSET"
  },
  "proof": {
    "path": "proof/inlet.png",
    "sha256": "UNSET",
    "shot_snapshot": {},
    "region": [0, 0, 512, 512]
  },
  "checks": {"framing": "fail", "near_clip": "fail"}
}
```

This fragment is deliberately incomplete and must fail; it is not a passing receipt. Never create placeholder PASS values to make the gate green. Use a named reviewer and the actual comparison result. Independent review is a workflow responsibility, not something a reviewer-name string proves.

## What to review first

The first proof set covers the primary-view silhouette/count and the riskiest close-up regions: hollow terminals, reflective coplanar joins, hardware scale, lettering, dial marks and small branch connections. Only then start the full authorized batch. If a final image exposes a new defect, stop the remaining batch, preserve outputs and repair a new source revision.

For each fastener family, compare source pixels and apparent diameter against the owning flange or plate at a matched camera. Check both scale and containment. A seated, manifold fastener can still look too small; a visually enlarged washer may leave inadequate physical clearance. Reusable constructors must specify contact origin, axes, supported scales and interval ownership.

## Evidence and efficiency

Keep one controller-owned coverage record. Builders supply artifacts; reviewers supply scoped findings; mechanical workers verify file integrity and package outputs. A worker should receive one complete review scope per revision rather than repeated single-shot handoffs when the evidence can be delivered together.

Track owner-discovered misses, HQ-only defects, repair rounds, render time by retained/invalidated set, and reuse consumers. Record model cost only when the runtime actually exposes it. This command establishes no cost-saving percentage or model-quality benchmark. Automatic batch resume and per-shot dependency caching are not implemented by this gate.

A useful real-data qualification is to validate a completed package in retrospective mode, substitute its old low-resolution preview while preserving the target frame, and confirm rejection. Then change a pinned source or review verdict and confirm another rejection. Such a retrospective experiment does not mean the gate ran before the original render.

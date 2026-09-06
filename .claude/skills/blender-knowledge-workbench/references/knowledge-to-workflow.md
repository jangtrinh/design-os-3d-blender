# Knowledge → workflow → skill pipeline

Use when the user adds/changes local knowledge, asks to refresh routes, or asks to turn source knowledge into reusable Blender practice. Existing core owns scene execution; this procedure produces routing and instructions. It never executes source snippets.

## 1. Detect and frame

Run `python3 scripts/knowledge-pipeline.py scan`. It works with a stale catalog and reports added/changed/removed files, unrouted knowledge, hash-bound deferrals and validation errors. After first publication it compares against the last publication receipt; rebuilding the search catalog alone cannot erase pending changes.

State the intended artifact, affected workflows, exclusions and acceptance before edits. Preserve the source corpus. Read each changed source relevant to the request; headings or a bibliography alone are insufficient to promote a procedure. For broad independent clusters, read-only scouts may propose mappings and cautions; one controller edits shared configuration. Their reports remain evidence, not runtime certification.

## 2. Curate before compiling

Edit `knowledge/catalog-config.json`:

- Reuse a primary workflow when its output/gates fit. Add a conditional topic when the extra reading is needed only for a particular technique. Keep base required reading unchanged unless it is actually mandatory.
- A topic has `when`, 1–5 `sources`, 1–5 `steps`, `gates` and `limitations`, plus `review.kind: static-routing-review`, `review.by`, and exact `review.source_hashes` for every selected source.
- Convert observations into a decision, an action and a falsifiable check. Distinguish numeric, visual, runtime and physical evidence. Do not inherit absolute quality claims or presets as acceptance thresholds.
- Add source-specific `annotations` with SHA256, runtime/effects and concrete cautions. Destructive examples stay inspect/adapt. Archive sources cannot enter topic packs.
- If a source is intentionally outside current workflows, use `routing_exclusions[path]` with `reason` and `reviewed_sha256`. It stays searchable. A changed source invalidates that deferral.

A new topic is usually enough. Create a new skill only for a distinct reusable intent not served by the existing entrypoints; use the installed skill-creator and a realistic forward test. Do not mass-generate SKILL.md files from source headings. Current workbench consumes the generated shared playbook; its two runtime mirrors reference the same artifact.

## 3. Prepare and review

```bash
python3 scripts/knowledge-pipeline.py prepare --bundle plans/knowledge-updates/candidate.json
python3 -m unittest discover -s tests/knowledge -v
```

Prepare refuses unrouted active knowledge and stale topic reviews. It produces a candidate containing the exact project root, source/config hashes, prior output hash and generated playbook content. Inspect its `content`, source mapping and gates; independent review is useful for substantial changes. The returned `review_sha256` binds the reviewed candidate, not external technical truth. No routine user reconfirmation is needed for an already authorized update.

## 4. Publish the inspected candidate

```bash
python3 scripts/knowledge-pipeline.py publish \
  --bundle plans/knowledge-updates/candidate.json \
  --reviewed-sha256 <exact-review_sha256-returned-by-prepare>
python3 scripts/blender-knowledge.py check
python3 scripts/blender-knowledge.py route native-animation-rigging --topic rig-spaces-ik-mechanisms
```

Use the exact returned digest after inspecting the candidate. Publication recomputes the source set and compiler result, rejects changed inputs or conflicting output edits, atomically replaces `knowledge/generated-workflows.md`, rebuilds/checks the catalog and records `plans/knowledge-updates/last-publication.json`. A local advisory lock serializes publishers; it is not an OS sandbox or a lock on unrelated source writers.

Playbook and catalog are separate writes. If interrupted after the playbook write, rerun the same candidate if sources and output still match; otherwise prepare/review again. Consumers reject a stale catalog until rebuild completes, and compare the generated playbook with current compiler output. A catalog rebuild cannot bless an outdated or missing published playbook. Never overwrite an externally edited generated output to force a retry. Receipts are written only after final source/freshness checks.

## 5. Verify and hand off

Check the intended topics through `route --topic`, not just the generator's exit code. Unknown topics and stale topic review hashes must fail. Inspect source cautions and required reading size. Record snapshot identity, test results, unresolved source claims and next execution gates. Use the generated playbook as selective reading; do not dump the entire document into model context.

No daemon/watch/scheduler is installed. This pipeline runs on request. Promotion means curated task routing; actual Blender builds still need core numeric/visual verification and engineering work still needs physical evidence where relevant.

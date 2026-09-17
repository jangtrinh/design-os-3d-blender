# Research: turn Blender API findings into reusable contracts

Date: 2026-09-17. Scope: AI-authored native Python, evaluated geometry,
Action slots, Geometry Nodes input binding, and knowledge freshness.
Runtime under test: Blender 5.2.0 LTS, build `fbe6228777e7`, macOS.

## Evidence and source access

Research begins with the checked repository and actual callers. The reviewed
baseline exposed concrete ownership and silent-success risks; these are better
test targets than accumulating another unexecuted snippet collection.

Official documentation locators used for this investigation:

| Subject | Primary locator | Access and evidence boundary |
|---|---|---|
| Evaluated object and temporary mesh | https://docs.blender.org/api/5.2/bpy.types.Depsgraph.html ; https://docs.blender.org/api/5.2/bpy.types.Object.html | Direct web fetch returned HTTP 402; a native urllib Depsgraph fetch returned HTTP 403. The implementation and tests establish the local behavior; these pages are not represented as successfully fetched snapshots. |
| Camera projection | https://docs.blender.org/api/5.2/bpy_extras.object_utils.html | Direct web fetch returned HTTP 402. Perspective/orthographic projection, modifier response, camera shift and depth rejection are independently tested locally. |
| Assigned Action channelbag | https://docs.blender.org/api/5.2/bpy_extras.anim_utils.html ; https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/ | The animation worker obtained official search excerpts; full-page fetch was unavailable for some pages. Shared-slot behavior was tested on the installed runtime. See its report for exact scope. |
| Legacy Action and driver changes | https://developer.blender.org/docs/release_notes/5.0/python_api/ ; https://developer.blender.org/docs/release_notes/5.0/animation_rigging/ | Use versioned locators as provenance, not proof of the current binary. The original modifier-collection clear call failed in a real 5.2 test before repair. |
| Geometry Nodes modifier inputs | https://docs.blender.org/api/5.2/bpy.types.NodesModifier.html ; https://developer.blender.org/docs/release_notes/5.2/python_api/ | Full-page web access is unverified in the prime run. The GN worker's report and changing-output tests supply the observed runtime binding evidence. |

An additional command to inspect installed API source via `--python-expr` was
blocked by the tool because it could not determine the request's safety status.
It was not executed and is not a source-evidence claim. Existing authorized
repository payloads and tests continued to work. No documentation text was
silently substituted from a third-party tutorial.

## Findings, actions and falsifiers

| Finding | Applied technique | A result that must fail |
|---|---|---|
| A bare temporary mesh return loses the allocation's owner. | Borrow evaluated owner + mesh using a context manager; clear in `finally`; copy only independent data outward. | Wrong owner is cleared; consumer exceptions bypass cleanup; original data is changed. |
| Raw data and transforms can miss evaluated behavior. | Measure evaluated mesh vertices using the evaluated matrix. | Array width or a Copy Location constraint is absent from measured bounds. |
| XY projection alone does not establish camera depth validity. | Include positive depth and near/far clip tests; expose individual predicates. | A centered object outside the clip range is marked in frame. |
| One Action may contain unrelated slots. | Resolve the assigned slot; edit only requested channels and frames. | A neighboring slot's values/interpolation change or a rerun duplicates keys. |
| A stored GN custom property can be unrelated to actual geometry. | Resolve the live interface identifier, validate the binding, then measure output after parameter changes. | A missing input succeeds, duplicate names pick an arbitrary socket, or height remains unchanged. |
| Top-level-only source scans miss implementation edits. | Include nested Python/shell modules while retaining generated/environment exclusions. | Editing/deleting a nested module leaves `checked_catalog()` current. |
| A file-only loader cache misses imported helper changes. | Explicit dependency manifests invalidate cached helpers; the verification facade reloads its owned modules and clears their stale bytecode. | An unchanged facade keeps old behavior after a same-size dependency edit, or a missing dependency returns cached success. |

Detailed reusable instructions and the executable sample are in
`knowledge/00-foundations/native-api-contracts.md` and
`scripts/samples/native-api-contract.py`.

## Reusable research loop

1. State one behavior and a falsifier before editing. Identify the actual helper,
   callers, target version and owned data. Preserve the active scene and unrelated
   work. Use disposable background fixtures for API research.
2. Read official versioned documentation when accessible. Record failed access
   and distinguish a search excerpt, source read, runtime observation and formal
   specification. A `/current/` URL is a moving locator, not a version pin.
3. Build the smallest native fixture that can expose a wrong result. Include an
   independent negative control: a neighbor slot, invalid parameter, changed
   geometry, clipping plane or intentional consumer exception.
4. Fix the existing reusable helper and its real callers. Avoid globally removing
   shared objects/data merely to make a rerun succeed. Record migration when a
   former API cannot be preserved safely.
5. Run numeric tests in the actual Blender interpreter. Record binary identity,
   meaningful postconditions and failures. Compare outputs, not only successful
   assignments. A passing fixture does not prove topology, physics, render quality
   or other runtime versions.
6. Route the recipe, helper and tests through an existing workflow topic. Review
   changed hashes and cautions. Use `knowledge-pipeline.py prepare`, inspect the
   candidate, then `publish` with the exact reviewed digest; finish with `check`
   and a real `route --topic` call.

## Boundaries and follow-on research

These patches do not implement a background research daemon or automatically
approve incoming documentation changes. The user requested autonomous work in
this session. Publication remains a concrete reviewed operation.

The reusable next investigations are evaluated instances and render-depsgraph
parity; NLA and layered animation; broader typed GN sockets and simulation zones;
and dependency discovery for helpers beyond the explicit verifier manifest.
None is claimed complete by this batch.
Existing global scene reset, substring socket matching and unrelated engineering
boilerplates retain their cautions. Manufacture remains separate from geometry
and API qualification.

Executed results, review observations and source hashes for this batch belong in
`plans/260917-blender-auto-research/reports/`, outside the generated knowledge
inputs so appending final verification evidence does not invalidate publication.

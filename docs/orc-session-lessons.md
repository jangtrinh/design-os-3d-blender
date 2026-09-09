# ORC component reconstruction lessons

This is portable guidance distilled from reference-led ORC component work. It documents method and evidence boundaries, not hidden source models, vendor selection, operating conditions, or manufacture. Use it with the [component workflow](orc-component-workflow.md), [brief template](orc-component-brief-template.md), [HQ coverage guide](hq-coverage-gate.md), and [Separator worked example](orc-separator-worked-example.md).

## What the records support

| Source record | Observed result | Durable rule |
|---|---|---|
| Wellhead retrospective | A generative inventory over-read visible counts; close review also exposed a generic wheel profile and an output-only grating defect. | Reconcile count/side/landmarks in one active brief, prototype the identity profile first, and inspect every final image plus critical output-density proof. |
| Separator evidence workflow | A terminal artifact survived topology, bore-ray, and preview checks before appearing in output. | Assign each hollow-wall interval to one object, then inspect an output-density crop and camera rays around the bore. |
| HQ coverage gate record | Receipt checks reject stale, incomplete, or low-density declared proof; the guarded launch route is deliberately narrow. | Treat `--launch` as an opt-in route. Direct Blender, MCP, and direct headless launches bypass it and must be reported accurately. |
| Component04 prototype record | A float-derived generated identifier aborted Blender before a candidate or sentinel existed. | Use integer indices for generated names; reproduce process failures in a disposable headless probe before sending them to a live GUI. |
| Reusable-instruments record | Plausible heads at proxy coordinates did not establish valid station placement. | Define the station and its host/adapter contract before mass instances; recheck it in the installed assembly. |
| C05 cabinet review | A cabinet could be visible and mesh-valid while still reading as a generic box. | Review named construction layers in a close-up, not only object presence, topology, or count. |

## The working method

1. **Read evidence in the right order.** The designated primary 3/4 view governs visible count, facing, placement, and silhouette. Close-ups establish local profile, transitions, and construction. For mechanical routing, taps, instrument stations, and connection anatomy, read applicable project drawings or official installation documents before reasoning from the image. A CAD analogue can supply vocabulary; it cannot select a product or establish dimensions, ratings, or compliance.
2. **Prototype identity before scale-out.** The controller makes the first native prototype for a new geometry family. Promote it only after its axes, pivot, ports, supported range, regression proof, and second real consumer are documented. A family-level pass does not qualify clearances or contacts after installation.
3. **Scale the site as one system.** Declare shared units, axes, origin, and one site scale. For every component, distinguish source-backed physical envelope from tabletop/display envelope, visible protrusions, and service allowance; proxies and analogues remain provisional. Name each external port with elevation and orientation, then test all modules together. An illustrative envelope never selects equipment, capacity, rating, duty, or manufacturer identity.
4. **Own each boundary.** For every attachment, name the two objects, axes, owned surface or axial interval, permitted contact/gap/overlap, and a falsifier. Endpoint coincidence alone can hide an incorrect tangent or a competing bore wall.
5. **Review construction, not just presence.** Write the expected critical features before opening the candidate. Review every supplied close-up and an opposing or 3/4 view that can falsify the construction. Hardware needs family-scale comparison in the matched camera. A cabinet close-up may need door return, seal, hinge leaves/pin/knuckles, lock, HMI recess, operator layers, and framed louver construction.
6. **Freeze evidence before expensive output.** Bind candidate, render settings, proof regions, and final images by hash. Review risky regions at final output density: bores, coplanar joins, fasteners, text, dial marks, and specular contacts. A changed source, camera, or resolution invalidates affected proof; retain previous media as earlier-revision evidence.

## Checks that answer different questions

| Check | Can support | Cannot support |
|---|---|---|
| Saved-source audit | Existence, topology, transform, declared contact, bore, or bounds predicate | Visual fidelity, chosen vendor, load, fit, or manufacture |
| Manual source-first review | Named visible features, construction layers, and declared shot coverage | Hidden construction or an engineering qualification |
| Coverage receipt | Declared file/hash/review/proof bindings for its supplied inputs | Camera provenance, omitted inventory features, reviewer authenticity, or automatic coverage of direct rendering |
| Package integrity | File names, hashes, image dimensions, bit depth, and decode status | Whether the image actually looks correct |

## Worked C05 cabinet case

The C05 cabinet is a documented review case. The first enclosure was visible and numerically healthy, but it lacked readable construction. The correction reviewed layered HMI and operator controls, hinge and lock anatomy, framed ventilation, and service-zone detail against close views. A separate signed-volume audit initially reported false negatives because world-origin float arithmetic cancelled for small meshes far from origin; centroid-relative float64 arithmetic corrected the measurement and was rerun on unchanged geometry.

The case supports a method: inspect construction at the camera scale, test surprising measurements before repairing geometry, and keep media bound to immutable revisions. It is not an executable model, CAD package, vendor selection, or production design in this public repository.

## Next-component checklist

1. Declare purpose, one site scale, shared axes/units, source-backed or provisional envelope, and named external ports.
2. Fill the brief's mechanical-source, shape, attachment, station, and coverage rows before detail work.
3. Build and independently review the highest-risk native family at its target apparent scale.
4. Verify the installed assembly: endpoint position, tangent, bore, contact, display access, scene environment, and declared collision pairs.
5. Freeze hashes and manually inspect every critical proof at final density before an HQ batch. Record the actual launch route and preserve any prior media.

Do not report an efficiency, cost, quality, engineering, or manufacture claim unless the current artifact and check directly support it.

# CK-001 revision-B final engineering review

Date: 2026-09-17

Scope: independent review of the current revision-B digital prototype and the
`verification-B02` receipts. This is an engineering/digital-verification verdict,
not a physical compatibility, electrical, material, load, process or manufacture
approval.

## Verdict

**Digital prototype verification: PASS for the declared revision-B scope.**

The current evidence is internally consistent across the B03 geometry scene, the
Presentation-B02 scene, the representative production gate, full-layout interface
inspection, GLB export and independent GLB reopen comparison. The model is suitable
to continue into final media/package generation.

Physical qualification remains open. In particular, the Gateron-informed switch
interface is a source-guided custom prototype rather than a certified KS-33
interchangeability claim, and the Bourns PEC11R envelope is combined with a custom
carrier, knob receiver, bonded supports and daughterboard rather than vendor CAD.

## Evidence identity

- Geometry B03: `builds/reference-keyboard/runs/geometry-B03/steps/geometry/attempt-0001/model.blend`
  - SHA-256: `e4c54bb1eca1a592787b88af4ee25dbbe50dab91837a95bc47aa87e99909aec8`
- B03 form-gate report:
  - SHA-256: `be5d21972bb2fe567f18dc11f54fc103cf705c357cfdbc9ba672007e8f413e62`
  - checker: production-gate `1.0.1`, Blender 5.2.0 LTS
  - spec SHA-256: `fdcff5dae9873e3db9093780ed729e4e3045714723ffc6b43e5b98d450170434`
  - 8 declared representative part families, `failed=[]`, `required_checks_missing=[]`
- Presentation-B02 source used by final verification:
  - `builds/reference-keyboard/runs/presentation-B02/steps/presentation/attempt-0001/keyboard.blend`
  - SHA-256: `0f3ae17b53f7de4be99e928b20e50ee0ecd4e0ca9e1600ce7c0a4797c6a73e70`
  - provenance binds it to B03 geometry SHA and B03 form-gate SHA above.
- Verification-B02 final gate is bound to the same Presentation-B02 SHA and the
  same spec SHA. Its final sentinel is `AGENT_OK` with 8 families and 0 failed parts.

## Material improvements over the earlier r01 digital asset

1. **Source-guided key/switch interface instead of generic visual overlap.** The
   scene now has 58 modeled cross stems and 58 key receivers. The stem dimensions
   are informed by the selected Gateron KS-33 drawing while the 4.12 / 1.22 / 1.40
   mm receiver remains an explicit local clearance choice. The current inspector
   checks actual evaluated meshes through the full 0..3.0 mm travel range.
2. **Real low-profile control mechanics.** Keycap shells have a reduced visible
   skirt, integral receiver boss and dished top; printed legends are conformed to
   the actual cap surface rather than floating on a planar nominal top.
3. **Spacebar support is no longer center-switch-only.** The 2u key has two custom
   parallel guide interfaces with measured running clearance and full-travel
   collision checks. It is intentionally not labelled as a commercial wire
   stabilizer.
4. **Five PEC11R-based encoder assemblies replace floating knobs.** The model now
   includes the documented 12.5 x 13.4 mm body envelope, M7 bushing/hardware,
   real 6 mm D shaft, staged D receiver, 19.6 x 15 mm custom carrier, prototype
   M1.6 top fastening, bonded brass-standoff reaction path, side-terminal proxies
   and mechanically supported daughterboards.
5. **PCB/chassis/USB load paths are explicit.** The PCB is at Z10.15..11.75 with
   real supports, encoder windows are 20.4 x 16.6 mm with an open-back treatment
   for the rear trio, and the USB connector belongs to a supported daughterboard;
   the acrylic opening is clearance rather than the connector support.
6. **Housing details were made mechanically coherent.** The diffuser USB window
   preserves a nominal 1.3 mm outer-wall roof, the status-light openings are merged
   into one 4.8 x 2.4 mm bar away from the large knob aperture, and chassis clamp
   hardware has explicit analytical engagement regions rather than decorative
   opposing shanks with no stated path.
7. **Lighting is represented by actual emitters.** Presentation-B02 shows a
   restrained blue-to-purple/pink perimeter effect from internal RGB emitter
   geometry through transmissive/diffusing acrylic. This replaces the earlier
   visually uniform emissive-shell shortcut; it still makes no LED/electrical or
   optical-flux qualification claim.

## What the eight-family gates prove — and what they do not

The B03 form gate and Verification-B02 final gate both screen these eight declared
representative manufacturable families:

`RK_BASE`, `RK_DIFFUSER`, `RK_MAIN_PLATE`, `RK_KEY_00`, `RK_KEY_41`,
`RK_KNOB_1`, `RK_FOOT_0`, `RK_GUIDE_SLEEVE_0`.

All eight pass their declared geometry checks; the final gate contains 260 part/check
rows in total, with no failing part and no missing required check. The checker also
records 13 non-failing unchecked notes, primarily undeclared feature bores and
overhang reporting where no overhang acceptance limit was specified.

This must not be read as "781 printable parts individually production-qualified."
The current Presentation-B02 mesh inventory contains **781 meshes, all with `RK_`
names**, whereas the production spec intentionally declares eight representative
part families. Encoder carriers, PCB supports, electronic detail, legends, emitters
and many other assembly meshes are therefore covered by other evidence paths, not
as 781 independent production-gate parts.

The gate itself explicitly excludes load capacity, slicer/print success, complete
assembly-fit proof, thermal/creep behavior, printer shrinkage, material/process
qualification and electrical/device function.

## Full-layout interface evidence

Verification-B02 `inspect` finished `AGENT_OK` with 781 meshes, 58 switch cells,
7 sampled key travels and zero reported switch/keycap collision pairs. The bound
fit report shows:

- 58 evaluated switch housing components and 58 per-cell assemblies;
- switch assembly envelope within the declared 0.05 mm dimensional tolerance;
- key travel samples `[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]` mm;
- zero key/cover, key/flange or key/plate collision pairs across those samples;
- 58 source-guided stem/receiver pairs within the declared dimensional tolerance;
- stem insertion range `[3.0, 3.0]` mm and receiver ceiling reserve
  `[0.2, 0.2]` mm;
- zero key-material/stem and zero stem/static collision indices;
- keycap/switch status `PASS_DIGITAL_PROTOTYPE`, compatibility explicitly
  `NOT_QUALIFIED`;
- two spacebar guides, collision-free through the sampled travel, with
  `[3.65, 3.65]` mm rest engagement;
- five encoder D-shaft/knob pairs, `[5.0, 5.0]` mm engagement, collision-free at
  matching virtual rotations;
- deliberate D-shaft mismatch/offset negative controls detect collision.

The earlier verification-B01 3 mm key/plate failure is superseded by the current
parity-based inside-solid classifier and the current bound verification-B02 receipt.
Before that checker change, an EXACT Boolean probe on the reported pressed-key case
measured 0.0 mm³ key/plate intersection, demonstrating that the older nearest-normal
containment result was a checker false positive rather than a geometry defect.

`layout-checks.json` independently reports status `pass`, `failed=[]`, 29 layout and
envelope checks, the expected 32 mm total height, 58 keys/stems, 5 knobs and current
stack datums. Its `physical_scope_status` remains `not_tested`.

## Export and reopen evidence

Verification-B02 export finished `AGENT_OK` and produced:

- GLB SHA-256: `87a590e1e77408775849e3822907b998af4d2d56d6335e03af0a914dd83c031e`;
- file size: 16,828,568 bytes;
- **781 meshes**, one animation clip and one embedded image;
- active-scene + selection scoping enabled;
- animation mode `SCENE`, force sampling enabled, frame step 1 and
  `export_anim_slide_to_zero=false`.

The reopened GLB finished `AGENT_OK`. It has the exact 781 expected/imported mesh
names and checks frames **1, 7 and 60** at 24 fps. Across **2,343 object-frame
comparisons**:

- every triangle count matches;
- every comparison passes;
- maximum bbox error is **0.0 mm**;
- maximum sampled surface error is **0.0 mm**;
- all 2,343 comparisons use the quantized-triangle-correspondence path;
- mesh-name match is true.

Source-surface evidence SHA-256 is
`ef6667eba7953c3fde3f877319cd68adfbc787ead1be3fd9eb573133f856251d`.
The reopen report correctly limits this evidence: its surface sampling is not a
general mathematical Hausdorff proof and it does not prove material appearance,
physical fit, load, thermal, electrical or manufacturing performance.

## Evidence still missing for physical release

- Physical Gateron switch/keycap coupons: insertion/retention force, repeat fit,
  tolerance stack, wear and process shrinkage. The digital receiver is not a
  factory KS-33 interchangeability certification.
- Physical PEC11R shaft/knob coupon: D-flat tolerance, axial retention and repeated
  assembly. The selected electrical/detent/resolution suffix also remains a product
  decision.
- Carrier and bonded-anchor structural data: M1.6 thread strip margin, tightening
  torque, 0.9 mm carrier ligament strength, epoxy shear/peel/creep, surface
  preparation and environmental aging.
- Exact encoder terminal bending/land geometry and a real PCB electrical design;
  current daughterboards are mechanical envelopes without KiCad/netlist/ESD/power
  qualification.
- A selected USB-C receptacle manufacturer footprint and connector load/cycle test.
- Spacebar guide friction, rattle, wear and off-axis load testing.
- Material/process selection, slicer/support validation, tolerances after the chosen
  fabrication process and any load/thermal qualification required for manufacture.

## Media/readiness boundary

Presentation-B02 was visually reviewed as a verification artifact. The improved
key shapes, legends, hardware and restrained RGB identity are legible and no missing
key/knob family was observed in the reviewed views. This is not a 100% image-reference
fidelity claim.

The Full-HD production code now asserts the PNG IHDR dimensions of every still are
exactly 1920 x 1080; this supersedes the older `render-preflight.md` observation that
still dimensions were not explicitly reopened/checked. Final Full-HD media/package
execution remains owned by the prime workflow and is separate from this engineering
verdict.

## Engineering disposition

Proceed with final verification/media/package generation using the bound revision-B
artifacts. The current digital model has substantially stronger mechanical reasoning,
actual interface geometry and independent export evidence than r01. It should still
be presented as a **digitally verified prototype with specific physical qualification
work remaining**, not as a fully certified, electrically complete or manufacture-
approved commercial keyboard.

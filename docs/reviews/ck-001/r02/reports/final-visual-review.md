# CK-001 revision B — independent visual review

Reviewer scope: read-only visual/claims review. No model, source, gate, or render changes were made by this reviewer.

## Evidence binding

- Current presentation scene: `builds/reference-keyboard/runs/presentation-B03/steps/presentation/attempt-0001/keyboard.blend`
  - SHA-256: `de2251261c7d1c17c4150dd3cccc6e42f5a146036916d223801882c4f61c8e16`.
  - It is a normals/render-preparation revision of the same geometry-B03 physical coordinates/faces. The geometry-B03 source remains SHA-256 `e4c54bb1eca1a592787b88af4ee25dbbe50dab91837a95bc47aa87e99909aec8`.
  - Geometry contract in current project data: 284 × 92 × 32 mm design envelope, 58 installed keys, 5 knobs. Current interface inspection is reported separately as PASS for all 58 keys and 7 travel/interface checks; this review does not repeat those numeric tests.
- Current final production gate: `builds/reference-keyboard/runs/verification-B03/steps/final-gate/attempt-0001/final-gate.json`
  - SHA-256: `64072da6d9f1dbd7dd3e055334047cfe9ac885cb6abaaa5d21d4bf1359a4464f`.
  - It binds the exact B03 presentation scene SHA above and reports `failed: []`, `required_checks_missing: []`.
- Locked 11-view review packet: `builds/reference-keyboard/runs/reference-review-B01/packet.json`
  - SHA-256: `be5bf5f46b9ae4ee9d2b849276b5fdbcf6c439531e209ee36dbbea8710a3cdbf`.
  - Independent critique: `builds/reference-keyboard/runs/reference-review-B01/critique.json`, SHA-256 `92b1e447e02e5ba01139ab9bbf9e56295ffebd9df6c8d5d84821d8209c7df255`, reviewer `worker6`.
- B02 proof renders are verification images at 512 × 384, not Full HD delivery media.
- `builds/reference-keyboard/runs/fullhd-B01/steps/media/attempt-0001` is retained only as superseded failure evidence: it stopped after 8/11 stills on the old D-receiver framing guard.
- Current native media are under `builds/reference-keyboard/runs/fullhd-B02/steps/media/attempt-0001/`: all eleven stills are 1920 × 1080 and are pinned by the locked review packet/stills manifest; the 96-frame movie completed successfully and is bound by `media-manifest.json` SHA-256 `7c1350ef81486e623c3cc5e2416776f31e572d1495c66d6201f30405b4683c8b`.

### B02 image hashes

| View | SHA-256 | Visual role |
|---|---|---|
| `hero.png` | `fb8a258d45a18e0ba295075c7fdf1e33a2080835ad44dc9082036111fe4d09ef` | overall product silhouette/composition |
| `top.png` | `8267556b361507c45a45a2163619dad7813b4784bf043e5a68b9b955939bf398` | layout/count/top-plate coherence |
| `knob-detail.png` | `eed07cc66a08f0e780a9f77e423be37e94ecb55866a2373e9c2e014015b5e613` | external knob form/top slot |
| `key-detail.png` | `43537606827630686006db8018b14589a530bd0a0a7d8c05cc7cfe684c249532` | cap profile/legend/switch exposure |
| `exploded.png` | `9974d0c69126005995b118941abe030ed806e6e53fc5a50005e15ee4e5ae1c08` | stack separation and internal visibility |
| `bottom.png` | `065681bed2c81b59ce00f8c6afc6b1c0a79535dcdf4cc987d6c1bc8c7cacda35` | underside/feet/fastener visibility |

## Reference-file provenance review

The four files now present under `delivery/r01/reference/` must not be treated as equally authoritative merely from their names.

| File | Pixels | SHA-256 | Visual provenance assessment |
|---|---:|---|---|
| `original-work-louder.png` | 2048 × 1534 | `808901aae162bfda8a0fd7fca7d7b50e1c4584fe0b6dcd0f24aa6ca60ca21817` | Plausibly the owner-supplied primary product reference: single coherent product view, dense original-looking board legends/branding, and no infographic framing. Filename alone does not authenticate it, so this is a visual lineage assessment rather than a hash-to-upload proof. |
| `blueprint-rev01.png` | 1536 × 1024 | `a2f2a01b95243e913f3eae8e9632c165364a31bc7f2c3b51781f2c28e4f1e030` | Clearly a later presentation/blueprint derivative. It adds dimensions, section drawings, exploded labels, materials, certification-like marks, and textual claims not visible in the primary single-view image. Treat as secondary design guidance only. |
| `360-product-view.png` | 1536 × 1024 | `f94bd46005ad246b4656e2e6660ed61995b8526b6d05270bca20a996631c8009` | Clearly a later synthetic multi-view presentation sheet. It invents rear/underside viewpoints and close-ups absent from the single primary view. Useful for visual direction, not proof of hidden geometry. |
| `parts-catalog-rev01.png` | 1223 × 1286 | `acf7b869fc4509f904d01453f695a25f1e1377e6fa68e19d12e90036f03166bf` | Clearly a later catalog derivative. It asserts component identities, counts, materials, dimensions and USB/PCB details. It explicitly says approximately 70 keycaps while the current interpreted installed layout has 58; therefore it cannot be treated as an exact installed-parts source. |

Visible lineage supports using `original-work-louder.png` as the primary appearance reference and the other three as derived guidance. Exact authenticity of the primary reference cannot be certified because there is no recorded hash of the original chat upload to compare against this local copy.

## B02 visual findings — historical verification evidence

### Overall form and layout

`hero.png` and `top.png` show a coherent low-profile keyboard assembly with the intended 58-key interpreted layout and five-knob arrangement. The entire product is inside frame with comfortable margins; there is no gross crop. The plate, key field, rear macro row, left-side controls and right-side knob read as one product rather than disconnected pieces. No unintended floating control head is visible in the assembled views.

The silhouette is materially closer to the primary reference than the old thick-cap treatment: the revised cap skirt is visibly low and the key field sits close to the plate. The hero view also shows the translucent middle layer as a continuous side band rather than as a separate floating slab.

The primary reference carries much denser legends and board markings than B02. B02 uses simplified single-character/dot legends and only a small `work / keeb` mark near the right control. This is acceptable for a geometry proof but is a visible fidelity gap for a shareable reference-reconstruction render.

### Knobs and encoder presentation

Five knobs are visible in the overall/top views. `knob-detail.png` clearly shows a cylindrical metal-looking knob and the top indicator slot. It does not expose the underside D receiver or the shaft/carrier interface, so it cannot visually prove the keyed mount or support path by itself. There is no visible gross lateral offset or unsupported-looking knob head in the assembled proof.

The current interface document correctly limits the claim to a source-guided PEC11R-family envelope plus a custom chassis-supported carrier. Nothing in B02 visually establishes Bourns suffix compatibility, thread tolerance, axial retention, carrier bond strength, or electrical behavior.

### Keycap and switch presentation

`key-detail.png` shows the rounded low-profile cap shell, its visible skirt, and the switch body beneath it at useful scale. The cap is not visibly intersecting the neighboring caps or plate. The shot is from above/side, so the true cross receiver inside the cap is not visible. It therefore does not independently prove receiver geometry or stem engagement.

The model remains a source-guided custom low-profile switch/keycap prototype. These renders do not justify a certified KS-33 interchangeability claim, actuation-force claim, wobble/rattle claim, or lifetime claim.

### Stack, PCB, support and RGB

`exploded.png` is the strongest B02 internal view. It visibly separates keycaps, plate, switches, PCB/diffuser and top fasteners. The PCB is present as a continuous supported layer, and the right-side electronics area/USB region is visible rather than omitted. The separation reads as a deliberate assembly stack and does not show a grossly unsupported PCB slab.

Real modeled/emissive RGB points are visibly present behind the translucent middle layer in the exploded view, with a restrained blue-purple-pink/orange side glow. This is useful evidence that the color comes from scene emitters/materials rather than a post-painted flat band. It is still only visual evidence of the lighting concept; it proves no LED electrical netlist, thermal behavior, diffuser efficiency, current budget or manufacturable wiring.

Spacebar guide geometry is not legible enough in the 512 × 384 exploded proof to visually confirm the two parallel guides. The current Full-HD script appropriately adds a dedicated `spacebar-guides` inspection view.

### Underside

`bottom.png` is the weakest B02 evidence. The four feet and corner fastener regions are visible, but the entire plate is rendered near-black on a dark gray field. Small support/fastener details collapse into the surface and there is no readable bottom label comparable to the derived 360/blueprint sheets. The view technically avoids a black frame, yet its contrast is insufficient for a strong underside review.

This is a presentation/evidence problem, not evidence of a geometry defect. The Full-HD script's isolated underside lighting should be inspected specifically for whether the feet, fasteners, USB/support areas and edge stack become readable without flattening the metal surface.

## Specific observable defects / remaining visual gaps

1. B02 underside contrast is too low for dependable inspection of small underside details.
2. B02 close-ups do not expose the cross receiver, D receiver, spacebar guides, encoder carrier or USB mount; those interfaces remain visually unproven at B02 resolution even though numeric/interface checks exist elsewhere.
3. Legends/PCB silkscreen/branding are simplified compared with the primary appearance reference. For social/shareable fidelity this remains a visible delta.
4. The hero shot is compositionally clean but comparatively distant and soft at 512 × 384, so small construction improvements are not judgeable there.

No B02 image shows gross cropping, detached/floating knob heads, a missing main PCB, or a visibly unsupported full-width keyboard stack.

## Full-HD review contract

`scripts/fullhd.py` declares eleven native 1920 × 1080 PNGs from the final-gated scene:

`hero`, `top`, `knob-detail`, `key-detail`, `exploded`, `bottom`, `receiver`, `spacebar-guides`, `D-receiver`, `encoder-mount`, `usb-mount`.

The same script declares a 96-frame, 24 fps Full-HD native Cycles animation and records PNG/frame hashes plus a decoded MP4 probe. Final visual review must bind to the produced `media-manifest.json` / `stills.json`, inspect all eleven PNGs, and inspect representative decoded frames across assembled, control-motion, exploded and reassembled states. The final report must confirm that the media source scene hash matches the final-gated scene before calling the media current.

Required visual falsifiers for the new close-ups:

- `receiver`: fail visual review if the cap underside is still hidden, the cross is not legible, or the receiver appears broken/open through unintended faces.
- `D-receiver`: fail if the keyed flat cannot be seen, the bore appears circular, or the knob wall is visibly paper-thin/intersected.
- `spacebar-guides`: fail if either guide is missing, visibly skewed, or disconnected from the intended cap/guide stack.
- `encoder-mount`: fail if the encoder body/carrier appears to float, penetrate neighboring stack layers unexpectedly, or lacks an understandable support path.
- `usb-mount`: fail if the shell/daughterboard support appears detached, clipped, or visibly unsupported.
- `bottom`: fail if feet/fastener/support details remain too dark to inspect.
- all views: fail if any required subject is cropped, accidental helper/studio geometry appears, or the revised cap/knob stack loses coherence at 1920 × 1080.

## Full-HD B01 attempt-0001 — historical partial review

Eight native 1920 × 1080 PNGs were produced before the pass stopped. Their pixel dimensions were read directly from the PNG files.

| View | SHA-256 | Review |
|---|---|---|
| `CK-001-hero.png` | `6a6a6c0af07cd07f644b5d0c7ca107c82a22225188d691ea6f92bb52dad6468e` | PASS for framing and assembled visual coherence. Full product is in frame; low cap skirts, continuous middle diffuser and all five knobs are readable. |
| `CK-001-top.png` | `dea9034dd6503c2e877e5e8f22d15e4f4aed02be8fb3d42dbab4d2dc8afc91d1` | PASS for count/layout visibility. The interpreted 58-key/5-knob arrangement is clear and uncropped. |
| `CK-001-knob-detail.png` | `12070b9e4c8aab239d305a5f276d6ad5d91990d0c8521700ff946f9b4f76a762` | **FAIL share-quality close-up.** The cylindrical side shows obvious vertical faceting/banding at Full HD, and the top indicator slot terminates at the rim with a visibly notched/jagged edge. The external mount is not floating, but surface finish is visibly under-polished at this scale. |
| `CK-001-key-detail.png` | `a78f695717c1eb0a15e1796f84d38aaed849885eaa612723738dd382ea4e4e1a` | PASS for cap silhouette/clearance; mild skirt faceting is visible at extreme close-up but no intersection or broken surface is apparent. |
| `CK-001-exploded.png` | `3dcb7c8084fcfe9d5480e8db82b4dc9b2350dc42e8bf63e85f4d38f9f6a71bcc` | PASS for readable assembly separation. Plate, switches, PCB, diffuser and fasteners are visibly distinct; real RGB emitter points are visible on the PCB. No grossly unsupported full-width layer is apparent. |
| `CK-001-bottom.png` | `ba184dae0e8c130d82ab913a9220a7fe0dc937d2023089b863a7123e2e69f829` | PASS for basic underside inspection. Four feet, corner fastener regions and support/mount holes are visible. Lighting is materially better than B02, although the strong center hotspot and edge falloff make it less polished than the hero/top views; the derived-sheet bottom label is not present. |
| `CK-001-receiver.png` | `cc1a9228e86cbb0d15b80db4accc3a92c565c5d58517880dbbf26457c53a3096` | PASS for the intended visual proof. The cap underside is exposed and a true cross-shaped receiver is legible; no unintended open shell or gross break is visible. |
| `CK-001-spacebar-guides.png` | `ca86929f96a25f5b131433bd1e5eac365318eb871569ec02fe5073b1f89af8e9` | PASS for the intended visual proof. Two parallel cylindrical guide pins are clearly visible on either side of the central cross receiver; neither appears missing, skewed or detached from the cap underside. |

Attempt-0001 stopped immediately before the planned `D-receiver` still. The last stdout sentinel is `AGENT_FAIL`; `studio.capture()` rejected `RK_KNOB_5` with `AssertionError: ('clipped', 'RK_KNOB_5')`. Consequently no `D-receiver`, `encoder-mount`, `usb-mount`, `stills.json`, `media-manifest.json`, frame sequence or MP4 exists from this attempt. This failure is a camera/framing pipeline failure. It does not establish a D-receiver geometry defect.

That B01 surface/framing finding is superseded by presentation-B03 and FullHD-B02 below. The underlying physical coordinates/faces were preserved; the render update changed shared-control normals/sharp-edge treatment and the close-up framing logic.

## Current Full-HD B02 — locked 11-view review

All eleven current stills are native 1920 × 1080 renders bound by review packet SHA-256 `be5bf5f46b9ae4ee9d2b849276b5fdbcf6c439531e209ee36dbbea8710a3cdbf`. The independent critique marks all seven declared visual feature groups PASS. This is a bounded visual acceptance of the declared revision-B appearance/features, not a physical qualification or 100% likeness claim.

| View | SHA-256 | Current visual finding |
|---|---|---|
| `CK-001-hero.png` | `31e3af589b0557e3fe60d4aae022d8a9500679b450f64300a9b87c557916c4c5` | PASS. Coherent assembled silhouette, low cap skirts, five knobs, layered edge stack and no gross crop/floating control. |
| `CK-001-top.png` | `6f2648af1dfd76afce078e4fadea33eb4e50f7a7c9e7b85f2bdc455e7e4c3742` | PASS. Five-knob left/rear-trio/right arrangement, rear macro strip, left macros and wide spacebar remain readable. |
| `CK-001-knob-detail.png` | `02bbae4a22556f64b8bcf0310a7168c3063904444d3f50b100d4cc55fbd713bb` | PASS. The prior B01 cylindrical faceting/banding is visually gone. The top indicator is a recessed channel. The small channel exit through the beveled rim reads as an intentional sharp boundary, not a smooth-surface failure. |
| `CK-001-key-detail.png` | `f9300de572dbd70a73dff87827c255f77b200ab629199bce7277911180faf3cf` | PASS. Rounded charcoal key form and readable white legends are consistent; no floating type or broken family is visible. |
| `CK-001-exploded.png` | `d05bb35f5390a7b0775de63e9e71a4d1378a138015c186b1997efed5fce993b7` | PASS. Plate, switch layer, PCB, diffuser/lower body and fasteners separate clearly; real emitter points and multi-hue RGB response are visible. |
| `CK-001-bottom.png` | `f5f4aa06a37388ff0cd16fa0dd6d45a6c6a6b9c23cfb34f3acbe905ec574588c` | PASS. Silver underside and four dark feet are fully framed/readable; no gross crop. |
| `CK-001-receiver.png` | `65b439784209c337b27d0aaccb7282fa905b8f59974f13fb5039fed7fd3040a3` | PASS. True cross-shaped receiver is directly visible and unobstructed. |
| `CK-001-spacebar-guides.png` | `bf8d59a8497cdf206c68bc98a10a5c14a2b130ca0bff145c23028f3df12ac63d` | PASS. Two integral guide pins are directly visible beside the central receiver and do not appear skewed or detached. |
| `CK-001-D-receiver.png` | `89457b0484d57fc337e3e3b1c22a0e9f68ebb35d3ee1e38b21d3babe4e5ef44d` | PASS. Stepped D-shaped receiver and keyed flat are fully inside frame after the camera-fit correction; the prior B01 crop is resolved. |
| `CK-001-encoder-mount.png` | `e8117bf7e2bc0b7c752fcc36ffb3a360c048fd7be6a0447813aff5c7e531ea79` | PASS for declared prototype inspectability. D shaft, mounting hardware, carrier/board structure and support posts read as a connected assembly. |
| `CK-001-usb-mount.png` | `e3e6a625d81ed70945024d0a7c17d43204c8cee6e787d4c45820ff2bbade112b` | PASS for declared prototype inspectability. Generic USB-C shell is seated through the side opening with supporting board/chassis geometry visible behind it. |

### Feature-level comparison to the owner targets

- **Control layout:** PASS for the declared layout. The five-knob world arrangement, compact key field, rear macro strip and wide spacebar are retained. The owner primary reference is 2048 × 1534 (approximately 4:3) while the delivery proof is 1920 × 1080 (16:9), and the camera is not reference-matched, so background/crop/perspective composition differs even though the 284 × 92 product proportion is coherent.
- **Key form and legends:** PASS for shape/readability. The current legends are materially simplified relative to the owner image: several secondary symbols, multi-line labels and small board/silkscreen markings are omitted or reduced to single glyphs/dots. This remains the clearest appearance-fidelity delta.
- **Slotted knobs:** PASS. The recessed channels are real geometry and the B01 normal-faceting artifact is gone. No physical geometry change is warranted from the remaining sharp channel/bevel exit alone.
- **Layered body and RGB:** PASS for the declared feature. The owner photo/360 guide uses a more saturated cyan-purple-orange acrylic glow and stronger bloom; FullHD-B02 is more restrained/pale in the assembled hero, though the individual modeled emitters and multi-color response are clearly present in exploded/edge views.
- **Underside:** PASS for declared underside/feet visibility. The secondary 360 sheet includes a centered branding/certification-style label panel that is not present in the current model. Its omission is recorded as a fidelity delta and should not be filled with invented compliance marks.
- **Modeled interfaces:** PASS for visibility of the revision-B cross receiver, two spacebar guides and stepped D receiver. These are deliberate prototype design additions; their visibility does not establish that the owner photo contained the same hidden interfaces.
- **Supported hardware:** PASS for visible prototype support path. Encoder carrier/shaft/mounting parts and the USB support assembly are inspectable. No electrical footprint, adhesive/bond, thread/preload, thermal or vendor-compatibility claim follows from these images.

The secondary blueprint/360/catalog images are treated as owner design guides for dimensions, intended hidden-view presentation and feature direction, not as authenticated evidence of hidden original-product construction. `original-work-louder.png` remains the primary appearance target; exact byte identity to the original chat upload is unavailable.

## Current Full-HD B02 motion review

`CK-001-animation-FullHD.mp4` is SHA-256 `d317aa72ce512dcaf2816384706e9d532170fd1574cd1019317abab69a0ccb20`. The media manifest binds it to presentation-B03 scene SHA-256 `de2251261c7d1c17c4150dd3cccc6e42f5a146036916d223801882c4f61c8e16` and final-gate SHA-256 `64072da6d9f1dbd7dd3e055334047cfe9ac885cb6abaaa5d21d4bf1359a4464f`. The recorded probe reports 1920 × 1080, 24/1 fps, 4.000000 seconds and 96 decoded frames; `full_decode` is `pass`. The Full-HD pass ends with `AGENT_OK` and postconditions `frames: 96`, `stills: 11`, `width: 1920`, `height: 1080`.

Representative rendered frames were inspected directly:

- frame 1: assembled baseline; product is fully in frame with coherent low-profile stack;
- frame 7: key-travel sequence remains visually coherent and uncropped;
- frame 18: knob-motion state remains coherent; no detached control head is visible;
- frame 40: transition into exploded state exposes switches/plate without gross clipping;
- frame 58 and frame 66: full exploded stack remains readable, with plate, switch field, PCB/diffuser, controls and fasteners separated as intended;
- frame 90 and frame 96: reassembled/end states return to a coherent complete product with no visible residual exploded offset.

No representative frame shows accidental helper/studio geometry, gross crop, black/empty output, disconnected full-width layers or an unrecovered final state. This visual review does not replace the separate transform/interface motion checks and does not establish continuous collision, actuation force, friction, encoder feel or physical durability.

## Claims boundary

The current digital evidence can support claims about modeled geometry, nominal clearances, counted components, animation transforms and native-render appearance when bound to the correct scene/hash. It does not establish physical switch force, certified KS-33 interchangeability, exact PEC11R suffix fit, encoder-carrier bond strength, fastener preload, USB/electronics netlist, RGB electrical/thermal performance, material strength, print/process tolerance, or final manufactured-device reliability.

No 100% likeness claim is supported. The primary source is a single oblique view and its original upload hash is unavailable; the blueprint, 360 sheet and parts catalog are derived images with invented hidden views/details and must not be used to close that evidence gap.

## Current verdict

`stop` — the corrected current FullHD-B02 media set is complete and visually ready for the declared revision-B scope: eleven native 1920 × 1080 stills pass the locked seven-feature review, and the 96-frame/24 fps Full-HD movie completed with a successful full decode and coherent representative states. The B01 D-receiver crop and control-surface banding are resolved. Remaining appearance deltas are explicitly recorded (camera/aspect composition, simplified legends/markings, restrained RGB treatment, omitted derived-sheet underside label) and do not falsify the declared visual contract. This verdict closes visual/media review only; manufacture, electronics, force/retention, bond/preload, thermal and vendor-compatibility claims remain outside the evidence and must stay qualified separately.

# AI 3D Generation — Decision Synthesis

**Date:** 2026-07-28
**Question asked:** Do the Hyper3D Rodin / Sketchfab / Hunyuan3D skill sets actually help our
Blender pipeline? What is the secret sauce behind image-to-3D? And — added mid-research —
what open-source options exist so we depend less on commercial platforms?

**Stack context:** Claude + `ahujasid/blender-mcp`, Blender 5.2 LTS, MacBook Pro (Apple Silicon).
Target use cases: game/realtime, character animation, motion graphics, product viz, 3D printing.

Detail reports: `rodin.md` · `hunyuan3d.md` · `marketplaces.md` · `how-image-to-3d-works.md` ·
`pipeline-fit.md` · `oss-models.md` · `oss-tooling.md`

---

## 1. The short answer

**Yes, but not the way the demos suggest.** These platforms are a *concepting and
background-asset* technology, not a hero-asset technology. The generation step costs
cents and takes a minute; the cleanup costs hours. Across every credible source, the
generation fee is **1–3% of the true cost of a usable asset** — so the platform choice
should be made on output quality and API ergonomics, never on price per credit.

Three findings change what we should build:

1. **The blender-mcp integration is crippling all three services.** It hardcodes the
   weakest settings. For Rodin it pins `tier="Sketch"` (Gen-1, the lowest tier) and
   `mesh_mode="Raw"` (triangles) against a legacy host, when the REST API offers
   Gen-2.5, `mesh_mode="Quad"`, and explicit face budgets from 500 to 2,000,000. For
   Hunyuan3D it hardcodes a region, defaults `texture=False`, and exposes no PBR flag.
   **We have been evaluating these models at their worst.** Fixing this is three form
   fields in `addon.py` — the highest-leverage thing in this entire report.

2. **Hunyuan3D's licence is disqualifying for us, and the trap is the output clause.**
   The Tencent Hunyuan3D Community License excludes the EU, UK and South Korea from its
   Territory, and §5.c extends that exclusion to the *generated models themselves* — not
   just the weights. An asset generated with it may not be used or displayed in those
   markets. Combined with 29 GB VRAM and a CUDA-only texture rasterizer, it is out.

3. **TRELLIS.2 (Microsoft, MIT, native PBR) removes the reason to accept that licence.**
   It is the decisive 2026 open-source development: 4B parameters, emits
   BaseColor/Roughness/Metallic/Opacity, MIT-licensed. Renting an H100 puts a textured
   asset at roughly **$0.07**. Rodin's $120/mo API tier buys the equivalent of ~1,800
   H100-hours of self-hosted generation instead.

   One catch worth knowing before anyone celebrates: TRELLIS.2 is MIT but its default
   preprocessing ships **RMBG-2.0 under CC BY-NC 4.0**. The licence trap has moved from
   the headline model to its dependencies. Swap RMBG out of every path.

---

## 2. Verdict per service

| Service | Verdict | Reasoning |
|---|---|---|
| **Hyper3D Rodin** | **Adopt** — but fix the integration first | Deemos Technology (CLAY → BANG lineage, two SIGGRAPH best papers). Gen-2.5 shipped 2026-05-26; heavily funded, actively developed. Not related to Microsoft's same-named avatar paper. Quad mode at 8k–50k faces is genuinely useful for props; PBR maps are its strongest component. Licence is favourable ("we will not limit your use of such Output") though it is a non-limitation, not an assignment — no IP warranty or indemnity. |
| **Tencent Hunyuan3D** | **Reject for production** | Territory-restricted output licence (EU/UK/KR), OSS line stalled at 2.1 (Jun 2025) while 2.5/3.0/3.1 stay API-only, 29 GB VRAM, CUDA-only texture stage, no macOS path, no quads, no normal maps in any open version. Fine for experiments in permitted markets; not something to build on. |
| **Sketchfab** | **Keep, with a licence filter** | Alive. Epic closed only the *Store* (Oct 2024); the site, viewer, free CC corpus and `api.sketchfab.com/v3` — including download and OAuth — were verified serving on 2026-07-28. **But:** an unfiltered search returned 3 of 5 downloadable results under NC/ND terms, and blender-mcp sends no `license` parameter. Adding `license=cc0` to the search params fixes it, and was verified working. Until then, treat every Sketchfab download as legally unclear. |
| **Fab** | **Unusable for automation** | No public API; returns 403 to non-browser clients. The download API Epic promised for 2025 never shipped. |
| **PolyHaven / ambientCG** | **Make these the mandatory first stop** | 2,287 and 2,004 CC0 assets respectively, keyless APIs, zero licence risk. Retrieval beats generation whenever the asset exists. |

---

## 3. The secret sauce, compressed

Full explanation in `how-image-to-3d-works.md`. The compressed version:

**These systems do not reconstruct 3D from your image. They sample from a learned prior
over plausible shapes, conditioned on your image.** Single-image 3D is mathematically
ill-posed — the back of the object is not in the photo — so the model invents it from
what it has seen. Nearly every failure mode follows from that one fact.

Three eras got us here:

- **Per-asset optimisation** (DreamFusion, Magic3D, ~2022–23): optimise a NeRF per object
  using a 2D diffusion model as a critic. 40–90 minutes per asset, Janus-faced blobs.
- **Multi-view diffusion + reconstruction** (Zero-1-to-3, MVDream, LRM/TripoSR/InstantMesh,
  ~2023–24): generate consistent views, then feed-forward reconstruct. Seconds instead of
  hours, but residual view inconsistency shows up as mushy geometry.
- **Native 3D latent diffusion** (TRELLIS, Hunyuan3D, CLAY/Rodin, TripoSG, ~2024–26): learn
  a latent space *of 3D shapes* and diffuse directly in it. This won because it removed the
  2D bottleneck and allowed direct SDF/normal supervision.

The pipeline in practice: background removal and canonicalisation → DINOv2 image
conditioning → a shape VAE that encodes meshes into latents with curvature-importance
surface sampling → a flow-matching diffusion transformer with classifier-free guidance →
isosurface extraction (marching cubes / dual contouring / FlexiCubes) → a separate
multi-view texture stage with delighting to recover true PBR → optional remesh, UV, rig.

**The single most important thing to understand:** the "AI mesh look" — dense triangle
soup, blobby edges, no edge loops — comes from the **isosurface extraction stage**. The
model produces an implicit field; marching cubes turns it into triangles by sampling a
grid. Grid resolution is why thin features vanish and sharp edges round off. There is no
notion of edge flow anywhere in the process, which is why the output can never be
"artist topology" without a separate retopology step.

The rest of the failure modes are equally mechanistic, not incidental:

| Failure | Mechanism |
|---|---|
| Arbitrary scale/units | canonicalisation strips metric scale during preprocessing |
| Hallucinated back sides | occluded regions are prior samples, not observations |
| Text and logos become mush | high-frequency, low-probability detail — the VAE discards it first |
| No interiors | training data is watertight shells |
| Hard-surface/CAD precision fails | the prior is smooth; sharp constraints aren't representable |
| Inconsistent watertightness | isosurfacing guarantees nothing at grid boundaries |

**What is arriving now:** part-level generation (PartCrafter, OmniPart, HoloPart) is
shipping, PBR-native latents are shipping (TRELLIS.2), and quad/mesh-native generation
plus 3D-latent editing are just crossing from research into product.

---

## 4. Per-use-case verdict

| Use case | Verdict | Notes |
|---|---|---|
| **Motion graphics** | **Strong yes** | The standout fit, ~10 min cleanup. Poly count, topology and UV quality all stop mattering when the object spins for 3 seconds behind a title card. |
| **Game / realtime** | **Yes, with mandatory retopo** | Default output is 12.5k–1M triangles against a 500–5,000 tri prop budget. Always remeshing. Viable for background props; not for hero assets. |
| **3D printing** | **Conditional yes — decorative only** | A peer-reviewed study of Meshy output (CAD Journal 22(5) 2025, 8 Reallusion experts) found manifoldness mostly acceptable (1 of 8 models affected) but up to **3,370 zero-area faces and 67 self-intersections per model**. Wall thickness is the real killer. Gate everything on the 3D Print Toolbox. |
| **Product viz** | **No for hero shots** | Plausible ≠ accurate. Logos and text turn to mush; hard-surface precision fails. If the client's actual product is being sold from the image, you need real CAD. Fine for set dressing around the hero. |
| **Character animation** | **No** | Structurally mismatched, not merely immature. No edge loops at joints means deformation tears. Auto-rig output does not survive real animation. Generated meshes are for statues, not performers. |

---

## 5. The open-source answer

Two clean findings from the OSS survey:

**Generation must be rented; cleanup runs locally.** No open 3D *generator* runs properly on
Apple Silicon — all of them bind to CUDA-only `nvdiffrast`/`pytorch3d`. `trellis-mac` does run
on MPS (~3.5 min/asset, ~18 GB peak) but texture baking hits the CUDA rasterizer, so local
output is **geometry + vertex colours only**. Meanwhile every *cleanup* tool runs natively and
fast on M-series. So: rent GPU for generation (~$0.03–0.09/asset on RunPod L40S / Modal), do
all repair, retopo, UV, bake and export on the Mac.

**Retopology is still the weak link, and no learned solution ships.** MeshAnythingV2 is capped
at 1,600 faces *and* non-commercial. The genuinely good quad models — PolyGen, QuadGPT,
PolyFlow — have no released weights. DeepMesh (Apache-2.0) is the only permissive option.
Among conventional tools, Blender's own **QuadriFlow + Voxel Remesh is the only combination
that is simultaneously good, headless-capable and native on arm64**; Instant Meshes has been
dormant since Jan 2022, QuadWild-BiMDF since Oct 2024, AutoRemesher since 2020.

Also worth knowing before anyone plans around it: **ComfyUI-3D-Pack is effectively
unmaintained** (last release Aug 2025, 2026 issues unanswered, absent from the Comfy
Registry), and **no credible open MCP server for 3D generation exists** — the best candidate
has 4 stars. A plain REST backend is the better pattern: `FishWoWater/3DAIGC-API`
(Apache-2.0, Docker, one-click RunPod), wrapped in ~80 lines of FastMCP if we want it as an
agent tool.

### Recommended open stack

| Layer | Choice | Licence |
|---|---|---|
| Shape + PBR | **TRELLIS.2** — local on Mac for geometry iteration, burst to RunPod H100 for final textured output | MIT (⚠ swap out RMBG-2.0, CC BY-NC) |
| Editable parts | PartCrafter | check per repo |
| Texturing an existing mesh | Material Anything / StableGen | check per repo |
| First-pass rig | UniRig (8 GB, exports FBX) | MIT |
| Retopology | Blender QuadriFlow + Voxel Remesh; QuadRemesher if paying | — |
| Repair / validate | trimesh + manifold3d + pymeshfix + pymeshlab | permissive |
| UV | xatlas (measured 0.742 utilisation) | MIT |
| Optimise / export | gltf-transform + gltfpack | MIT |
| Environment | one Python 3.13 venv: `pip install bpy==5.2.0` publishes a `cp313 macosx_11_0_arm64` wheel | — |

Exclude Open3D (no cp313 wheel). Microsoft UVAtlas was archived 2026-04-24 — do not use.

---

## 6. What to actually do

**Immediately (hours, highest leverage):**

1. Fork `blender-mcp` and unpin the three Rodin form fields in `addon.py:1324-1326` —
   expose tier, `mesh_mode` (Quad!) and face budget. We have never seen Rodin's real output.
2. Add `license=cc0` to the Sketchfab search params. One line; removes a live legal risk.
3. Make PolyHaven the mandatory first stop in any asset-acquisition workflow. Retrieval
   beats generation on quality, topology, time, cost and legal risk simultaneously.

**Short term (days):**

4. Stand up the local cleanup venv (`bpy==5.2.0` + trimesh + manifold3d + pymeshfix +
   pymeshlab + xatlas) and write the cleanup chain as a reusable, agent-callable function:
   scale/orientation normalise → manifold repair → remesh/decimate to budget → xatlas UV →
   PBR re-wire (watch the sRGB vs Non-Color trap) → export.
5. Write the Blender-side **acceptance test** for any incoming generated asset: tri count,
   manifold check, bbox/scale sanity, material present, UV coverage, turntable render
   self-critique. This is what makes the loop autonomous rather than supervised.

**Medium term (weeks):**

6. Trial Rodin Creator ($30/mo) *after* step 1, with quad mode at 8k–50k faces, on real
   motion-graphics and background-prop tasks. Judge it then, not now.
7. Stand up `3DAIGC-API` on RunPod with TRELLIS.2 as the open fallback. Compare against
   Rodin on the same prompts, same cleanup chain.

**Do not:**

- Do not use AI generation for character animation or hero product viz.
- Do not build on Hunyuan3D given the output-territory licence.
- Do not plan around ComfyUI-3D-Pack or any current open 3D MCP server.
- Do not auto-download from Objaverse-XL — ODC-By wraps per-object licences including
  NC and academic-only.

---

## 7. Confidence and gaps

Strongly evidenced: licence terms (LICENSE files and ToS read directly), blender-mcp's
hardcoded parameters (source read at commit `da4e16d`), Sketchfab API liveness (verified
serving 2026-07-28), the technical architecture sections (grounded in published papers),
and the OSS tooling examples (executed, not guessed — e.g. verified 31,780 → 6,232 byte GLB,
xatlas utilisation 0.742, PyMeshLab 10,180F → 4,000F watertight).

Weakly evidenced, treat with caution:

- **Independent quality benchmarks barely exist.** Reddit was unreachable this session and
  search results are dominated by press releases and competitor-authored comparisons. The
  most credible negative signal on Rodin is its own CTO admitting in Jan 2026 that output is
  "not that game-ready."
- **All cleanup-time and cost-per-asset figures are estimates**, derived from the operator
  chain rather than measured on our hardware.
- **Vendor architecture claims are unverifiable** where no paper exists — Rodin Gen-2/2.5,
  Meshy and Tripo have published nothing. Those sections are marked as inference.
- **No named commercial game is documented as shipping AI-generated assets.** Industry
  coverage discusses concepting and prototyping only. Draw your own conclusion.
- Repo last-commit dates are partly from a third-party crawler (GitHub API was gated),
  so "actively maintained" judgements carry ±weeks of uncertainty.

Every claim that could not be confirmed against a primary source is marked `[UNVERIFIED]`
in the detail reports.

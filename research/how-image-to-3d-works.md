# How Image-to-3D Actually Works

*A technical explainer for people who need to predict failure modes, not publish papers.*
*Written July 2026. Papers cited with arXiv links and dates.*

---

## 1. The core problem: you are not reconstructing anything

Start with the honest framing, because everything downstream follows from it.

A single photograph is a 2D projection of a 3D scene. The projection destroys depth, and it destroys everything the camera could
not see. There is an infinite family of 3D shapes that produce a pixel-identical image — a fact that has been formally true
since the beginning of computer vision. Single-image 3D is not merely hard; it is **ill-posed** in the strict mathematical
sense. No amount of clever geometry recovers information the image does not contain.

So what are these systems doing? They are doing **conditional generation, not reconstruction**. The model has seen hundreds of
thousands to millions of 3D assets during training (Objaverse and Objaverse-XL,
[arXiv:2212.08051](https://arxiv.org/abs/2212.08051) / [arXiv:2307.05663](https://arxiv.org/abs/2307.05663), were the datasets
that made this possible; commercial systems train on those plus licensed and internally curated data). From that it has learned
a **prior over plausible 3D shapes**: a probability distribution `p(shape)`. The image is a conditioning signal that narrows the
distribution. The output is a *sample*, not a *solution*.

This single fact predicts most of the failure modes in section 5:

- Regions the camera saw are **constrained**. Regions it did not see are **sampled from the prior** — which is to say, invented.
  Plausibly, confidently, and often wrongly.
- The prior is shaped by the training distribution. Objaverse is heavy on game props, characters, furniture, cartoon objects. It
  is light on precision mechanical parts, medical devices, architecture with real tolerances. Ask for something outside the
  prior and the model regresses toward what it knows.
- The model has no concept of *this specific object*. It has a concept of *objects like this*. Fine detail that carries identity
  — a logo, an engraving, a serial number, a specific bolt pattern — is exactly the kind of high-frequency, low-probability
  content a generative prior smooths away.

A useful mental substitution: replace "reconstructs a 3D model from your image" with **"hallucinates a 3D model that would
render to something resembling your image."** That is literally what the loss functions of several generations of these systems
optimized.

---

## 2. The generational arc

Three eras in about four years. Each fixed the previous era's blocking problem and introduced a new one.

### Era 1 (2022–2023): Optimization per asset — SDS and the Janus problem

**DreamFusion** ([arXiv:2209.14988](https://arxiv.org/abs/2209.14988), Sept 2022) is the origin point. There was no large 3D
generative model, but there *was* a very good 2D one. DreamFusion's trick, **Score Distillation Sampling (SDS)**, was to use a
frozen 2D text-to-image diffusion model as a critic: initialize a NeRF, render it from a random camera, ask the 2D diffusion
model "how would you denoise this render?", and backpropagate that signal into the NeRF's weights. Repeat thousands of times.
The NeRF converges toward a shape whose renders look, to the 2D model, like the prompt.

It worked, and it was a genuinely beautiful idea. It was also structurally broken in two ways:

- **Speed.** Every asset is a fresh optimization from scratch. DreamFusion took roughly 1.5 hours per asset. **Magic3D**
  ([arXiv:2211.10440](https://arxiv.org/abs/2211.10440), Nov 2022) added a coarse-to-fine scheme — sparse hash-grid NeRF first,
  then a DMTet-based textured mesh refined with a differentiable renderer at higher resolution — and got it to ~40 minutes with
  better quality. Still 40 minutes.
- **The Janus problem.** This is the *mechanistic* failure and it matters conceptually. The 2D critic is view-agnostic: it
  scores each render independently, and it has a strong prior that "a photo of a rabbit" shows a rabbit's face. So it happily
  rewards a face on the front *and* a face on the back. The optimization has no global constraint tying views together, so it
  converges to a many-faced chimera. Add SDS's mode- seeking behaviour (it collapses toward high-density modes, producing
  over-saturated, over-smoothed "blobs") and you get the characteristic era-1 look. **ProlificDreamer**
  ([arXiv:2305.16213](https://arxiv.org/abs/2305.16213)) later diagnosed this precisely and replaced SDS with Variational Score
  Distillation, which fixed saturation but not speed.

### Era 2 (2023–2024): Generate consistent views, then reconstruct

The insight: don't ask a view-agnostic 2D model to supervise a 3D optimization. Instead, **make the 2D model view-aware**,
generate a small set of mutually consistent views, and reconstruct from those. Two problems get separated: "what does this
object look like from other angles?" and "given several views, what is the mesh?"

- **Zero-1-to-3** ([arXiv:2303.11328](https://arxiv.org/abs/2303.11328), Mar 2023) fine-tuned Stable Diffusion on synthetic
  renders with *relative camera pose* as an additional conditioning input. Give it an image and a rotation, get the object from
  that angle. Novel-view synthesis became a controllable, zero-shot operation.
- **MVDream** ([arXiv:2308.16512](https://arxiv.org/abs/2308.16512), Aug 2023) generated the views *jointly* rather than one at
  a time, using cross-view attention. Because all views are denoised in one process, they are consistent by construction. This
  is the direct structural cure for Janus.
- **SyncDreamer** ([arXiv:2309.03453](https://arxiv.org/abs/2309.03453), Sept 2023) modeled the joint distribution over
  multiview images with a 3D-aware feature attention volume — enforcing consistency in an explicitly spatial way rather than
  just via attention.
- **Wonder3D** ([arXiv:2310.15008](https://arxiv.org/abs/2310.15008), Oct 2023) added a second domain: generate multiview
  **normal maps** alongside colour, then fuse. Normals carry surface orientation, which is what you actually need for geometry —
  colour alone is a weak geometric signal.

In parallel, the reconstruction half got a step change. **LRM** ([arXiv:2311.04400](https://arxiv.org/abs/2311.04400), Nov 2023)
replaced per-scene optimization with a single 500M-parameter transformer trained on ~1M objects that maps an image directly to a
triplane NeRF in about **5 seconds**. **Instant3D** ([arXiv:2311.06214](https://arxiv.org/abs/2311.06214)) combined 4-view
generation with an LRM to hit ~20 seconds end-to-end from text. **TripoSR**
([arXiv:2403.02151](https://arxiv.org/abs/2403.02151), Mar 2024) open-sourced an improved LRM under MIT license running in
**under 0.5 s**. **InstantMesh** ([arXiv:2404.07191](https://arxiv.org/abs/2404.07191), Apr 2024) put a sparse-view LRM together
with **FlexiCubes** differentiable isosurfacing so it could train directly against mesh geometry and depth/normal supervision,
landing at ~10 s with open weights.

Hours became seconds. But a residual problem remained, and it was not fixable within the paradigm: **generated views are only
approximately consistent.** Four or six images that each look right but disagree by a few pixels about where a silhouette edge
is will, when reconstructed, produce a surface that is blurred, wavy, or subtly melted in exactly those regions. The
reconstruction model's job is to find a 3D shape that compromises between mutually contradictory evidence, and the compromise is
mush. Worse, the whole pipeline routes 3D information through 2D bottlenecks — you can only encode as much geometry as survives
a handful of renders.

### Era 3 (2024–present): Native 3D generation

The winning move, and the current state of the art: **stop routing through 2D. Learn a latent space over 3D shapes directly, and
run the diffusion/flow model in that latent space.** Architecturally this is the exact analogue of latent-diffusion for images —
a VAE compresses the modality, a transformer diffuses in the compressed space — except the modality is geometry.

The enabling representation paper is **3DShape2VecSet** ([arXiv:2301.11445](https://arxiv.org/abs/2301.11445), Jan 2023): encode
a shape not as a grid or a single global vector but as an unordered **set of latent vectors**, decoded to a neural field via
cross-attention. That is a transformer-native format — variable length, permutation-invariant, no cubic memory cost. Every major
native-3D system today descends from it. **Michelangelo** ([arXiv:2306.17115](https://arxiv.org/abs/2306.17115)) added the
observation that you should *align* the shape latent space with image and text embeddings before training the generator, because
the raw domain gap between 3D and 2D distributions otherwise causes condition/output mismatch.

Then the scaling:

- **CLAY** ([arXiv:2406.13897](https://arxiv.org/abs/2406.13897), SIGGRAPH 2024) — 1.5B-param multi-resolution neural-field VAE
  + minimalist latent DiT, 2K PBR textures (diffuse/roughness/metallic). From Deemos, the team behind the Rodin product line.
- **Direct3D** ([arXiv:2405.14832](https://arxiv.org/abs/2405.14832), NeurIPS 2024) — image-to-3D latent diffusion transformer
  on a triplane latent, no multiview intermediate.
- **TRELLIS** ([arXiv:2412.01506](https://arxiv.org/abs/2412.01506), Dec 2024, CVPR'25 Spotlight, Microsoft) — **Structured
  LATents (SLAT)**: a *sparse 3D voxel grid* where each active voxel carries a dense feature vector distilled from multiview
  vision-model features. Critically, one latent decodes to **radiance fields, 3D Gaussians, or meshes** — representation
  decoupled from output format. Up to 2B params, 500K objects. The most widely copied design.
- **TripoSG** ([arXiv:2502.06608](https://arxiv.org/abs/2502.06608), Feb 2025) — rectified-flow transformer over a VAE trained
  with hybrid SDF + normal + eikonal supervision, on a 2M-sample curated corpus.
- **Hunyuan3D 2.0 / 2.1** ([arXiv:2501.12202](https://arxiv.org/abs/2501.12202), Jan 2025;
  [arXiv:2506.15442](https://arxiv.org/abs/2506.15442), Jun 2025, Tencent) — the most thoroughly documented open system.
  Vector-set ShapeVAE → flow-matching DiT (3.3B) → separate PBR paint model (2B). Weights on Hugging Face.
- **Step1X-3D** ([arXiv:2505.07747](https://arxiv.org/abs/2505.07747), May 2025) — adapts the **FLUX** image-transformer
  architecture to 1D shape latents, so 2D tricks (LoRA, ControlNet-style conditioning) transfer directly to 3D. ~800K curated
  assets released.
- **Direct3D-S2** ([arXiv:2505.17412](https://arxiv.org/abs/2505.17412), NeurIPS 2025) — Spatial Sparse Attention makes DiT
  tractable on sparse volumes; trains at **1024³** on 8 GPUs where dense 256³ needed 32+.
- **Sparc3D** ([arXiv:2505.14521](https://arxiv.org/abs/2505.14521), May 2025) — sparse deformable marching cubes ("Sparcubes")
  at 1024³ handling open surfaces and disconnected components, plus a fully sparse-conv VAE.
- **Seed3D 1.0** ([arXiv:2510.19944](https://arxiv.org/abs/2510.19944), Oct 2025, ByteDance) — targets *simulation-ready*
  assets: watertight manifold geometry, PBR decomposition, UV inpainting for occluded regions. Volcano Engine API; not
  open-weights.
- **TRELLIS.2** ([arXiv:2512.14692](https://arxiv.org/abs/2512.14692), Dec 2025) — **O-Voxel**, a dual-grid omni-voxel
  representation (Dual Contouring lineage) encoding geometry *and* six material channels (base colour, metallic, roughness,
  opacity) natively. 1024³ into ~9.6K tokens, generation to 1536³, ~4B params, mesh + material decode in tens of milliseconds.
  Model, code and dataset announced for release.

**Why native 3D beat multi-view, concretely:**

1. **No consistency tax.** Geometry is generated as geometry. There is no set of disagreeing 2D images to reconcile, so
   silhouette wobble and melted surfaces simply do not arise from that mechanism.
2. **Supervision is direct.** You can train against SDF, occupancy, normals, and eikonal terms — signals that describe the
   surface itself, rather than rendering losses that only see the surface through a camera.
3. **The 2D bottleneck is gone.** A handful of 512px renders cannot carry 1024³ of geometric detail. Sparse-latent methods carry
   orders of magnitude more.
4. **It scales like image diffusion.** VAE + DiT + flow matching is a known-good recipe with known scaling behaviour, so the
   field could simply spend compute and data. That is what happened between 2024 and 2026.
5. **Topology freedom.** Sparse/voxel latents handle disconnected components, thin shells, and open surfaces that a triplane
   NeRF or an SDF field struggles with.

The cost is that native 3D needs a lot of *clean, watertight, well-normalized 3D data*, which is far scarcer than images. Data
curation pipelines (Step1X-3D filtered 5M assets down to 2M; TripoSG built 2M) are now as much of the moat as architecture.

---

## 3. The representation question

If you only remember one thing: **the latent representation determines the ceiling on output quality, and different vendors sit
at different points on that tradeoff curve.** This is the largest single source of vendor-to-vendor difference.

| Representation | What it is | Good at | Bad at | Used by |
|---|---|---|---|---|
| **Triplane** | 3 orthogonal 2D feature planes; a 3D point is decoded from its 3 projections | Compact, 2D-conv/transformer friendly, fast | Feature ambiguity — distinct 3D points can project to the same plane cells, blurring detail; resolution-bound | LRM, TripoSR, Instant3D, Direct3D |
| **Occupancy / SDF implicit field** | An MLP or decoder returning inside/outside or signed distance at any point | Continuous, resolution-independent, clean watertight surfaces | Requires watertight training data; struggles with open surfaces and thin shells; needs isosurfacing to become a mesh | 3DShape2VecSet, CLAY, Hunyuan3D, TripoSG, Step1X-3D |
| **Vector set / latent set** | Unordered set of latent tokens decoded via cross-attention | Transformer-native, variable capacity, scales with token count, excellent quality-per-parameter | Global — no spatial locality, so local editing is awkward; token count is the hard quality limit | 3DShape2VecSet lineage: CLAY/Rodin, Hunyuan3D, TripoSG, Step1X-3D, Seed3D |
| **Sparse voxel / structured latent** | Active voxels on a coarse grid, each holding a feature vector | Spatial locality (→ local editing), arbitrary topology, scales to 1024³+, decodes to multiple formats | Memory/attention cost needs custom sparse kernels; grid resolution caps the finest features | TRELLIS, TRELLIS.2, Direct3D-S2, Sparc3D |
| **3D Gaussian splats** | Millions of anisotropic Gaussians with colour/opacity | Fast to render, great for view synthesis and fuzzy material (hair, foliage, smoke) | Not a surface — converting to a clean mesh is lossy and awkward; poor for game/DCC pipelines | 3DGS ([arXiv:2308.04079](https://arxiv.org/abs/2308.04079)), DreamGaussian, TRELLIS as one decode target |
| **Mesh-native / token autoregression** | Predict vertices and faces as a token sequence, like a language model | Compact **artist-like** topology, sharp edges, low polycount, sane edge flow | Sequence length limits complexity; slower; harder to condition richly; still maturing | MeshGPT ([arXiv:2311.15475](https://arxiv.org/abs/2311.15475)), QuadGPT, QuadLink, Mesh-Pro |

Two structural observations:

**Implicit fields and voxels give you *shape*; only mesh-native methods give you *topology*.** Everything in the first five rows
has to be converted into triangles by an isosurfacing algorithm, and that algorithm has no idea what an edge loop is. This is
the root cause of the "AI mesh look" (section 4).

**Locality is the axis that decides whether editing is possible.** A vector-set latent is global: change one token and the whole
shape shifts unpredictably. A sparse-voxel latent is spatially indexed, so you can mask a region and re-diffuse only that
region. TRELLIS explicitly advertises local editing for this reason, and the 2026 editing work (section 6) is almost entirely
built on structured/voxel latents rather than vector sets.

**Where vendors sit** — verified vs inferred:

- **Verified (published):** Hunyuan3D uses vector-set ShapeVAE + flow-matching DiT. TRELLIS/TRELLIS.2 use sparse structured
  latents. Direct3D-S2 uses sparse SDF volumes. TripoSG (Tripo's *research* release) uses a rectified-flow transformer on an SDF
  VAE. CLAY, from Deemos, uses a multi-resolution neural-field VAE + DiT.
- **Inference:** Deemos productizes CLAY as the Rodin line, so Rodin's shipping models are very likely CLAY descendants — but
  Deemos has not published the architecture of the current commercial model. Similarly, Tripo's shipping v2.5/v3.x models are
  not documented publicly; TripoSG is the closest published proxy, not a statement about the product.
- **Not published at all:** **Meshy** has published no architecture. From output characteristics (clean closed geometry,
  quad-remesh option, PBR maps) it behaves like a native-3D latent system with a separate texture stage, but that is inference
  from behaviour, not fact.

---

## 4. The pipeline in practice: upload → GLB

Here is what actually runs. Most commercial pipelines are recognizably this shape, even where the model weights differ.

### 4.1 Preprocessing and canonicalization

Background removal first (typically a segmentation model in the RMBG / SAM family). The subject is then recentered, scaled to a
canonical bounding box, and often re-oriented toward a canonical front. This matters more than it sounds: the shape model was
trained on assets normalized into a unit cube with a consistent up- axis, so an off-centre, oddly-cropped, or tilted input is
out-of-distribution and quality degrades. It also means **the canonicalization step destroys real-world scale** — see section 5.

A cut-out with a bad alpha matte (hair, glass, motion blur) poisons everything downstream, because the model treats the
silhouette as hard evidence about the object's outline.

### 4.2 Image conditioning: DINOv2, not CLIP

The conditioning encoder turns the image into tokens the DiT cross-attends to. The field converged on **DINOv2**
([arXiv:2304.07193](https://arxiv.org/abs/2304.07193)) over **CLIP** ([arXiv:2103.00020](https://arxiv.org/abs/2103.00020)).
Hunyuan3D 2.1 states it uses **DINOv2-Giant at 518×518**; Seed3D 1.0 uses a **DINOv2 + RADIO** dual encoder.

The reason is what the two objectives select for. CLIP is trained on image–text contrastive matching, so its features are
optimized to be *semantic and text-alignable* — "a red sports car" — and are deliberately invariant to a lot of spatial detail.
DINOv2 is trained self-supervised with no text, and its patch tokens retain dense, spatially localized structure; the DINOv2
paper and a large body of downstream work show its features are strong for segmentation, depth, and correspondence. Geometry
generation needs to know *where the fender curves*, not *that it is a car*. So CLIP-style features tell the model what to make,
DINOv2 features tell it what shape to make it — and the latter is the harder half.

*(Inference: the "DINOv2 won" framing is my generalization from the pattern across Hunyuan3D, Seed3D and peers. Individual
papers state their choice; I have not found a single canonical head-to-head ablation paper that settles it for the whole
field.)*

### 4.3 The shape VAE

The VAE compresses a mesh into latents. Two details drive quality:

**Surface sampling.** You cannot feed a mesh to a transformer, so you sample points on it. Naive uniform sampling
under-represents exactly the regions that matter — edges, corners, high-curvature features — because those occupy little area.
Hunyuan3D 2.1 samples roughly **50% uniform / 50% importance-sampled toward high- curvature regions**, ~250K points each,
encoding to a latent sequence of up to **3072 tokens**. Step1X-3D calls its version **Sharp Edge Sampling**. If you have ever
wondered why AI-generated hard-surface objects have subtly rounded edges: the sampling strategy is one of the two places that
gets decided (isosurfacing is the other).

**Decode target.** The decoder typically predicts an SDF (Hunyuan3D, TripoSG, Direct3D-S2) or occupancy at arbitrary query
points. TripoSG's hybrid SDF + normal + eikonal supervision is representative of the current recipe — the eikonal term keeps the
field a true distance function, which makes the extracted surface better behaved.

**Token count is the quality ceiling.** More latent tokens = more detail, superlinear attention cost. This is the single biggest
lever on the price/quality curve, and it is very likely what separates vendors' "fast" and "high quality / detailed" modes.
*(Inference — vendors describe these tiers by output quality, not token budget.)*

### 4.4 The generative transformer

A DiT operating on shape latents, cross-attending to DINOv2 image tokens.

Almost everything current uses **flow matching / rectified flow** ([arXiv:2210.02747](https://arxiv.org/abs/2210.02747),
[arXiv:2209.03003](https://arxiv.org/abs/2209.03003)) rather than DDPM-style discrete-time diffusion. The practical reason is
sampling cost: rectified flow learns a near-straight velocity field from noise to data, so an ODE solver reaches good samples in
tens of steps instead of hundreds. For a product that must return a mesh in 30 seconds, that is decisive. Hunyuan3D-DiT, TripoSG
and TRELLIS.2 all use flow matching; Hunyuan3D 2.1 specifies an affine path with an optimal-transport schedule.

**Classifier-free guidance** ([arXiv:2207.12598](https://arxiv.org/abs/2207.12598)) applies here exactly as in image models, and
has the same pathology: the model is run with and without the image condition, and the difference is amplified by a guidance
scale. Low guidance → the prior dominates, output drifts from your image. High guidance → over-adherence, exaggerated features,
artifacts, reduced diversity. When a vendor gives you a "creativity" or "image adherence" slider, this is usually what it moves.
*(Inference on the slider mapping — plausible and consistent with behaviour, but not documented.)*

### 4.5 Isosurface extraction — where the "AI mesh look" is born

The model outputs a field. You need triangles. This stage is under-discussed and is responsible for a disproportionate share of
what people dislike about the output.

- **Marching Cubes** (Lorensen & Cline, SIGGRAPH 1987) — evaluate the field on a grid, emit triangles per cell from a lookup
  table. Robust, universal, and it **cannot represent a sharp feature**: any edge or corner that does not align with the grid
  gets chamfered. It also produces uniform-density triangle soup — the same triangle budget on a flat panel as on a detailed
  face — and stair-step artifacts on shallow-angle surfaces.
- **Dual Contouring** (Ju et al., SIGGRAPH 2002) — place one vertex per cell, positioned by solving a QEF using field
  *gradients*. This recovers sharp edges and corners, at the cost of possible self-intersections and non-manifold output.
  TRELLIS.2's O-Voxel dual-grid design is explicitly in this lineage.
- **FlexiCubes** ([arXiv:2308.05371](https://arxiv.org/abs/2308.05371), SIGGRAPH 2023) — a *differentiable* extractor built on
  Dual Marching Cubes with extra learnable per-cell parameters, so mesh geometry and connectivity can be optimized by gradient
  descent end-to-end. This is why InstantMesh could train directly against mesh geometry. FlexiCubes and DMTet
  ([arXiv:2111.04276](https://arxiv.org/abs/2111.04276)) are the standard differentiable options.
- **Sparse deformable variants** — Sparc3D's Sparcubes pushes to 1024³ by only instantiating cubes near the surface.

**Mechanistically, the "AI mesh look" is:** grid-quantized surface (blobby, chamfered edges) + uniform triangle density
unrelated to shape complexity (soup) + no edge loops, poles, or symmetry (nothing an artist would recognize as topology) +
resolution-limited thin features. It is not a failure of the generative model. It is what happens when you sample a smooth
implicit field on a grid.

### 4.6 Texture and PBR

Geometry and appearance are usually **separate models**. Hunyuan3D splits into Hunyuan3D-DiT (shape) and Hunyuan3D-Paint
(texture); Seed3D splits into MV → PBR → UV stages; Step1X-3D uses an SDXL-derived multiview model conditioned on rendered
normal and position maps.

The standard texture pipeline:

1. **Render the generated mesh** from N viewpoints to get normal/position/depth maps.
2. **Multiview-generate texture** conditioned on those geometry maps plus the input image. Conditioning on geometry is what
   keeps texture aligned to the surface rather than floating.
3. **Enforce cross-view consistency.** Hunyuan3D 2.1 uses 3D-aware RoPE in the multiview attention blocks; Step1X-3D uses
   texture-space synchronization; Seed3D uses positional-encoding-based in-context conditioning. Without this you get visible
   seams where views disagree.
4. **Back-project** the views onto the mesh, weighted by view-surface angle and visibility.
5. **UV-unwrap and bake** into texture maps. Auto-unwrap is typically an xatlas-class algorithm.
6. **Inpaint the holes.** Every mesh has regions no view covered — armpits, undersides, cavities. Seed3D's UV-stage diffusion
   inpainting exists specifically for this.

**True PBR vs baked lighting** is the important distinction for anyone putting assets in a real engine. Early systems produced a
single diffuse/albedo-ish texture with the input photo's lighting *baked in* — highlights and shadows painted onto the surface.
Relight that asset and the fake highlights stay put while the real ones move. Fixing it requires **delighting**: recovering
illumination-invariant albedo, plus separate metallic and roughness (and often normal) maps.

Current approaches:
- **Hunyuan3D 2.1** generates albedo, metallic and roughness simultaneously from multiple views under a Disney Principled BRDF
  assumption, with an **illumination-invariant training strategy**: render the same asset under different lighting and impose a
  consistency loss so the albedo branch must ignore lighting.
- **Seed3D-PBR** uses a two-stream DiT for material decomposition without separate networks per channel.
- **TRELLIS.2** is the cleanest architectural answer: material channels (base colour, metallic, roughness, opacity) live **in
  the latent itself**, so PBR is native rather than a post-hoc estimate.
- **CLAY** produces 2K diffuse/roughness/metallic.

Delighting is still imperfect. A strong directional light or a hard shadow in the input photo will leave a residue in the
albedo.

### 4.7 Post-processing

The final stage is mostly classical geometry processing, and is where vendors differentiate on "production-readiness":

- **Decimation / remeshing** to a target polycount.
- **Quad retopology.** Meshy's Remesh API offers `quad` (quad-dominant) or `triangle` (decimated) topology, 100–300K polys, and
  export to glb/fbx/obj/usdz/blend/stl/3mf. Tripo's API similarly exposes quad topology, PBR, face limits, and post-tasks for
  refine/texture/rig/stylize/convert. Note this is *algorithmic retopology applied after generation*, not generated topology —
  the model did not decide where the edge loops go.
- **Normal baking** from the high-res generated mesh onto the low-poly one, so detail survives decimation.
- **Auto-UV**, **auto-rig / auto-skin** for humanoids and quadrupeds, **auto-LOD**.
- **Format export.** GLB is the default because it is a single self-contained file with PBR materials.

---

## 5. Why the outputs still aren't production-ready

Each of these is a mechanism, not a complaint.

**Topology is not artist topology.** *Mechanism:* the mesh comes from grid-based isosurfacing of an implicit field. The
extractor emits triangles per grid cell. It has no notion of edge loops around a mouth, poles at a shoulder, symmetric flow, or
anisotropic density (dense where detail is, sparse where it isn't). Auto-quad remeshers improve the *look* of the wireframe but
cannot invent deformation-aware edge flow, because that requires knowing how the model will be animated. **Consequence:**
generated characters deform badly when rigged; subdivision produces artifacts; hand-editing is unpleasant.

**UVs are auto-generated.** *Mechanism:* xatlas-class algorithms optimize for low distortion and packing efficiency, not for
human legibility. **Consequence:** dozens to hundreds of small islands, seams in visible places, no consistent texel density, no
UDIM layout, no relationship to how a texture artist would paint. If you want to hand-paint or swap textures later, you will be
re-unwrapping.

**Scale and units are arbitrary.** *Mechanism:* preprocessing normalizes every asset into a canonical unit cube, and the
training data was normalized the same way. Absolute scale is not in the latent because it was removed before the latent existed
— and a single photograph contains no metric scale cue anyway. **Consequence:** every asset lands at an arbitrary size;
"auto-size" features are heuristics over object class, not measurement. Never trust generated dimensions for anything physical.

**Occluded regions are hallucinated.** *Mechanism:* section 1. The back of the object is sampled from the prior, conditioned on
a front view. **Consequence:** it will be plausible, symmetric, and generic. Detail present on the front (a logo, an asymmetric
handle, a specific cable route) will not be correctly continued around the back. The more asymmetric or unusual the object, the
worse this gets. Multi-image conditioning where available directly attacks this and is worth using.

**Thin features and hard-surface precision fail.** *Mechanism:* two compounding limits. The field is stored on a finite grid
(256³–1536³), so a feature thinner than a voxel either disappears or fuses to its neighbour; and the VAE's point sampling
under-represents sharp edges even with importance sampling. Marching-cubes-class extraction then chamfers whatever survives.
**Consequence:** wires, antennae, chain links, spokes, thin fins break or merge; planar faces are slightly wavy; edges that
should be a crisp 90° are radiused; concentric circular features are non-circular. There is no CAD constraint solver anywhere in
the pipeline — the model has no representation of "this is a cylinder of radius r," only a sampled field that looks cylindrical.

**Text and logos become mush.** *Mechanism:* text is high-frequency, low-probability, semantically arbitrary detail.
Geometrically it is below grid resolution; in the latent it is a tiny fraction of the reconstruction loss so the VAE discards it
first; and in texture it must survive multiview generation (each view invents letterforms independently) plus back-projection
blending. **Consequence:** letter-shaped smears. This is the single most reliable giveaway of a generated asset.

**Interiors are absent.** *Mechanism:* training data is watertight *shells*. Supervision is SDF or occupancy relative to an
outer surface, and the loss is dominated by that surface. Nothing in the objective rewards a correct interior, and the
conditioning image contains zero information about one. **Consequence:** a generated mug may be solid; a generated car has no
cabin; a generated building has no rooms. Anything requiring cross-sections, wall thickness, or internal volume needs modelling,
not generating.

**Watertightness for 3D printing is inconsistent.** *Mechanism:* depends on the extractor. Marching Cubes on a clean SDF is
manifold and watertight by construction — that path is fine. Dual Contouring and its descendants can emit self-intersections and
non-manifold edges at sharp features. Then decimation, quad remeshing, and boolean-ish post-steps can each introduce holes or
flipped normals. And even a topologically watertight mesh can be unprintable: zero wall thickness, floating disconnected shells,
degenerate slivers, non-manifold vertices. **Consequence:** always run a mesh repair pass before slicing; do not assume the GLB
is print-safe.

---

## 6. Where the field is going

**Part-level and compositional generation — shipping, early.** A single fused blob is hard to use; separate parts can be moved,
swapped, and rigged. **PartCrafter** ([arXiv:2506.05573](https://arxiv.org/abs/2506.05573), NeurIPS 2025) denoises multiple part
latents jointly with hierarchical attention from a single image, synthesizing occluded parts, with no pre-segmentation.
**OmniPart** ([arXiv:2507.06165](https://arxiv.org/abs/2507.06165)) and **FullPart**
([arXiv:2510.26140](https://arxiv.org/abs/2510.26140), generating each part at full resolution) followed. On the product side,
Deemos ships part decomposition in Rodin. This is the highest-leverage near-term change for practical usability.

**PBR-native generation — shipping.** The move from "estimate materials from a texture afterwards" to "the latent contains
material channels." TRELLIS.2 is the clearest instance (six material channels including opacity, so translucency is
representable at all). Hunyuan3D 2.1 and CLAY ship multi-map PBR today.

**Mesh-native / quad generation — active research, not yet default.** The line from MeshGPT (2023) now includes **QuadGPT**
(native quadrilateral autoregression), **QuadLink** ([arXiv:2605.16813](https://arxiv.org/abs/2605.16813), 2026 — three-stage
anchor prediction / contrastive vertex-centroid linking / quad-first assembly, plus a Tri-to-Quad operator to manufacture 400K
training samples), **Mesh-Pro** ([arXiv:2603.00526](https://arxiv.org/abs/2603.00526), preference optimization for artist-style
quad meshes) and **MeshWeaver** ([arXiv:2606.04688](https://arxiv.org/abs/2606.04688), sparse-voxel-guided surface weaving). The
blocker is sequence length: token-by-token mesh generation does not yet scale to complex assets, so production pipelines still
generate a dense mesh and retopologize. If this line lands at scale it removes the largest single objection to generated assets.

**Higher-resolution latents — shipping.** 256³ → 1024³ (Direct3D-S2, Sparc3D) → 1536³ (TRELLIS.2), enabled by sparse attention
kernels rather than brute force. This directly attacks thin features and sharp edges. Expect continued movement here; it is the
most predictable axis.

**3D-native editing instead of regeneration — just shipping.** Today, changing one thing means regenerating everything and
getting a different asset. The fix is editing in the 3D latent. **3D-LATTE**
([arXiv:2509.00269](https://arxiv.org/abs/2509.00269)) does latent-space editing; **Easy3E**
([arXiv:2602.21499](https://arxiv.org/abs/2602.21499), 2026) does feed-forward editing on the TRELLIS backbone via "Voxel
FlowEdit" in the sparse-voxel latent, with trajectory-consistency correction and regional masking so unedited regions are
preserved, and no per-scene optimization. Commercially, Deemos launched **Rodin Gen-2 Edit** (marketed as "3D Nano Banana") on
31 March 2026: box-select a region, describe the change in text, plus smart low-poly, part decomposition and normal baking.
*(Product claims are from a company press release, not independently verified.)* Note this is the payoff of the representation
choice in section 3 — spatially local latents make masked editing possible; global vector sets do not.

**Not solved, worth watching:** CAD/parametric output (some startups target B-rep or feature-tree generation directly, which is
a different problem, not a better mesh generator); real metric scale; interiors and articulation; and evaluation — there is
still no benchmark that predicts "will an artist accept this asset."

---

## 7. A practical mental model

Rules of thumb for the generate-vs-model-vs-buy decision.

1. **Generate what the prior knows; model what it doesn't.** Organic, mid-detail, game-prop-like objects — rocks, furniture,
   creatures, food, stylized props — are dead centre of the training distribution. Precision mechanical parts, architecture with
   tolerances, and anything with a spec sheet are outside it.

2. **Silhouette carries; identity doesn't.** If your object is recognizable by its overall form, generation will work. If it is
   recognizable by a logo, a text panel, or a specific asymmetric detail, generation will fail at exactly the thing that
   matters.

3. **Assume the far side is fiction.** Budget for the back being generic. If the back matters, use a system that accepts
   multiple input views, or plan to fix it manually.

4. **Ask "will this be deformed?"** Static set dressing tolerates bad topology completely. Anything that gets rigged, animated,
   subdivided, or simulated does not — retopo cost will exceed the generation saving.

5. **Ask "will this be relit?"** If yes, you need genuine PBR with delit albedo, and you should render a test under three
   lighting conditions before committing. Baked highlights are easy to miss in the vendor preview and impossible to miss in your
   engine.

6. **Anything with real dimensions needs measuring, not generating.** Scale is stripped by construction. Anything that must fit,
   mate, thread, or print to size gets modelled.

7. **Treat the output as a high-quality blockout, not a finished asset.** The realistic saving is on silhouette, proportion, and
   concept iteration — the slow, creative part. Retopo, UV, and material work remain. That is still often a large win; just
   price it correctly.

8. **Sharp edges and thin parts are the resolution test.** If your object's defining features are thinner than roughly 1/500th
   of its bounding box, expect them to break. Generate the body, model the thin bits.

9. **Match the vendor to the representation you need.** Want editability and multiple output formats? Look at the
   sparse-structured-latent lineage. Want maximum geometric fidelity on a single object? Look at high- resolution SDF/vector-set
   systems. Want open weights and a pipeline you control? Hunyuan3D 2.1, TRELLIS, Step1X-3D, TripoSG are the credible open
   options.

10. **Never ship a generated mesh to a printer or a physics engine unchecked.** Run mesh analysis for manifoldness, wall
    thickness, floating shells, and flipped normals. Watertightness is inconsistent by mechanism, not by accident.

---

## Comparison table: major systems

Speeds are order-of-magnitude and hardware-dependent; vendor figures come from marketing material or docs rather than
independent benchmarks. "Open weights" means model weights are publicly downloadable.

| System | Year | Representation | Conditioning | Output | PBR | Open weights | Speed (approx.) |
|---|---|---|---|---|---|---|---|
| DreamFusion | 2022 | NeRF (per-asset SDS) | Text | NeRF | No | No | ~1.5 h/asset |
| Magic3D | 2022 | Hash-grid NeRF → DMTet mesh | Text | Textured mesh | No | No | ~40 min |
| Zero-1-to-3 | 2023 | 2D diffusion + pose | Image + rel. pose | Novel views | No | Yes | seconds/view |
| MVDream | 2023 | Multiview 2D diffusion | Text | 4 consistent views | No | Yes | seconds |
| Wonder3D | 2023 | Cross-domain MV (RGB + normals) | Image | Mesh | No | Yes | minutes |
| LRM | 2023 | Triplane NeRF | Image | NeRF | No | No | ~5 s |
| TripoSR | 2024 | Triplane | Image | Mesh | No | Yes (MIT) | <0.5 s |
| InstantMesh | 2024 | MV + sparse-view LRM + FlexiCubes | Image | Mesh | No | Yes | ~10 s |
| CLAY / Rodin | 2024– | Multi-res neural field VAE + DiT | Text/image/3D | Mesh + 2K PBR | Yes | No | seconds–minutes |
| Direct3D | 2024 | Triplane latent diffusion | Image | Mesh | No | Yes | seconds |
| TRELLIS | 2024 | Sparse structured latents (SLAT) | Image/text | Mesh / 3DGS / RF | Partial | Yes | ~10 s |
| Hunyuan3D 2.1 | 2025 | Vector-set ShapeVAE + flow DiT (3.3B) | Image (DINOv2-G) | Mesh + PBR | Yes | Yes | tens of s |
| TripoSG | 2025 | SDF VAE + rectified flow | Image | Mesh | No | Yes | seconds |
| Step1X-3D | 2025 | Perceiver VAE (sharp-edge sampling) + FLUX-style DiT | Image | Mesh + texture | Partial | Yes | tens of s |
| Direct3D-S2 | 2025 | Sparse SDF volume, 1024³, sparse attention | Image | Mesh | No | Yes | tens of s |
| Sparc3D | 2025 | Sparcubes + sparse-conv VAE, 1024³ | Image | Mesh | No | Yes | tens of s |
| Seed3D 1.0 | 2025 | Latent set VAE + DiT (DINOv2 + RADIO) | Image | Watertight mesh + PBR | Yes | No (API) | not stated |
| TRELLIS.2 | 2025 | O-Voxel omni-voxel, 1024³→1536³, ~4B | Image/text | Mesh + 6-channel PBR | Yes | Announced | ms-scale decode |
| Meshy | commercial | **Not published** (inferred native-3D latent) | Image/text | glb/fbx/obj/usdz/blend/stl/3mf; quad or tri remesh, 100–300K polys | Yes | No | ~1 min tier-dependent |
| Tripo (product) | commercial | **Not published** (TripoSG is the closest published proxy) | Image/text | Multiple; quad option, face limits, rig/stylize/convert | Yes | No | ~1 min tier-dependent |

---

## Sources

**Era 1 — optimization / SDS.** [DreamFusion, 2022](https://arxiv.org/abs/2209.14988) · [Magic3D, 2022](https://arxiv.org/abs/2211.10440) · [ProlificDreamer (VSD), 2023](https://arxiv.org/abs/2305.16213)

**Era 2 — multiview diffusion + feed-forward reconstruction.** [Zero-1-to-3, 2023](https://arxiv.org/abs/2303.11328) · [MVDream, 2023](https://arxiv.org/abs/2308.16512) · [SyncDreamer, 2023](https://arxiv.org/abs/2309.03453) · [Wonder3D, 2023](https://arxiv.org/abs/2310.15008) · [LRM, 2023](https://arxiv.org/abs/2311.04400) · [Instant3D, 2023](https://arxiv.org/abs/2311.06214) · [TripoSR, 2024](https://arxiv.org/abs/2403.02151) · [InstantMesh, 2024](https://arxiv.org/abs/2404.07191)

**Era 3 — native 3D latent generation.** [3DShape2VecSet, 2023](https://arxiv.org/abs/2301.11445) · [Michelangelo, 2023](https://arxiv.org/abs/2306.17115) · [CraftsMan3D, 2024](https://arxiv.org/abs/2405.14979) · [Direct3D, NeurIPS 2024](https://arxiv.org/abs/2405.14832) · [CLAY, SIGGRAPH 2024](https://arxiv.org/abs/2406.13897) · [TRELLIS, CVPR 2025](https://arxiv.org/abs/2412.01506) ([code](https://github.com/microsoft/TRELLIS)) · [Hunyuan3D 2.0, 2025](https://arxiv.org/abs/2501.12202) · [TripoSG, 2025](https://arxiv.org/abs/2502.06608) · [Step1X-3D, 2025](https://arxiv.org/abs/2505.07747) · [Sparc3D, 2025](https://arxiv.org/abs/2505.14521) · [Direct3D-S2, NeurIPS 2025](https://arxiv.org/abs/2505.17412) · [Hunyuan3D 2.1, 2025](https://arxiv.org/abs/2506.15442) ([code](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)) · [Seed3D 1.0, 2025](https://arxiv.org/abs/2510.19944) · [TRELLIS.2, 2025](https://arxiv.org/abs/2512.14692)

**Representations, extraction, encoders.** Marching Cubes — Lorensen & Cline, SIGGRAPH 1987 · Dual Contouring of Hermite Data — Ju et al., SIGGRAPH 2002 · [DMTet, 2021](https://arxiv.org/abs/2111.04276) · [FlexiCubes, SIGGRAPH 2023](https://arxiv.org/abs/2308.05371) · [3D Gaussian Splatting, SIGGRAPH 2023](https://arxiv.org/abs/2308.04079) · [MeshGPT, 2023](https://arxiv.org/abs/2311.15475) · [CLIP, 2021](https://arxiv.org/abs/2103.00020) · [DINOv2, 2023](https://arxiv.org/abs/2304.07193) · [Classifier-Free Guidance, 2022](https://arxiv.org/abs/2207.12598) · [Flow Matching, 2022](https://arxiv.org/abs/2210.02747) · [Rectified Flow, 2022](https://arxiv.org/abs/2209.03003)

**Data.** [Objaverse, 2022](https://arxiv.org/abs/2212.08051) · [Objaverse-XL, 2023](https://arxiv.org/abs/2307.05663)

**Frontier: parts, quads, editing.** [PartCrafter, NeurIPS 2025](https://arxiv.org/abs/2506.05573) · [OmniPart, 2025](https://arxiv.org/abs/2507.06165) · [FullPart, 2025](https://arxiv.org/abs/2510.26140) · [3D-LATTE, 2025](https://arxiv.org/abs/2509.00269) · [Easy3E, 2026](https://arxiv.org/abs/2602.21499) · [QuadLink, 2026](https://arxiv.org/abs/2605.16813) · [Mesh-Pro, 2026](https://arxiv.org/abs/2603.00526) · [MeshWeaver, 2026](https://arxiv.org/abs/2606.04688)

**Vendor docs and announcements (primary, but self-reported).** [Meshy Remesh API](https://docs.meshy.ai/en/api/remesh) · [Tripo AI platform docs](https://platform.tripo3d.ai/docs/generation) · [Deemos/Hyper3D "Rodin Gen-2 Edit / 3D Nano Banana" launch, 31 Mar 2026](https://markets.financialcontent.com/observerreporter/article/pressadvantage-2026-3-31-hyper3d-launches-3d-nano-banana-for-ai-powered-3d-model-editing)

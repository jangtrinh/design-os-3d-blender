# Open-Source Glue & Cleanup Layer for an AI → Blender Pipeline

Research date: **2026-07-28**. Target: Blender **5.2 LTS**, MacBook Pro (Apple Silicon), agent driving
`blender --background` and/or `bpy` as a library.

**Verification method.** `api.github.com` is blocked by this session's egress policy, so repo health was taken
from **ecosyste.ms** (`repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/...`) plus direct GitHub HTML reads.
`pypi.org`, `registry.npmjs.org`, `api.comfy.org`, `formulae.brew.sh`, `docs.blender.org` and
`raw.githubusercontent.com` were read directly. Every Python snippet below was **executed** in this container
(Linux x86-64, Python 3.11) unless marked otherwise; Apple-Silicon claims are derived from published wheel tags
and are marked where they are inference rather than observation.

Two caveats worth reading before the tables:
- ecosyste.ms `pushed` values are as-of its own last crawl (`updated`). Where the crawl is stale I say so.
- Star counts differ slightly between ecosyste.ms and the live GitHub page (caching). Treat them as ±10%.

---

## 0. The single most important finding

**Nothing in the generative half of this pipeline runs on Apple Silicon.** TRELLIS, Hunyuan3D, and every
ComfyUI 3D node pack depend on CUDA-only components (`nvdiffrast`, custom CUDA rasterisers, `flash-attn`,
`pytorch3d`, `diso`/`diff-gaussian-rasterization`). ComfyUI-3D-Pack's own prebuilds target
"Windows 10/11, Python 3.12, CUDA 12.4, torch 2.5.1+cu124".

**Everything in the cleanup half runs natively and fast on Apple Silicon**, on CPU, with pip wheels.

So the correct architecture is a split: **generation is rented (RunPod/Modal, GLB out); cleanup, retopo, UV,
bake, export all happen locally on the M-series laptop.** The rest of this document is built around that split.

---

## 1. Orchestration / serving

### 1.1 ComfyUI-3D-Pack — do not build on it

| Signal | Value |
|---|---|
| Repo | `MrForExample/ComfyUI-3D-Pack` |
| Stars | ~3.5k (ecosyste.ms) / 3.8k (page) |
| Licence | MIT |
| Last release | **v0.1.6, 2025-08-07** (~12 months ago) |
| Last push | 2025-12-01 (crawl 2025-12-03) |
| Open issues | 21–33 |
| Comfy Registry | **Not listed** — `api.comfy.org/nodes/comfyui-3d-pack` returns non-JSON/404 |
| Apple Silicon | **No path at all** |

Open issues #567 (2026-04-07), #565 (2026-04-01), #561 (2026-02-04) show no maintainer replies. A pack whose
last release is a year old, that is absent from the official registry, and whose 2026 issues sit unanswered is
**effectively unmaintained for new work**. It still runs if you happen to match its exact CUDA/torch matrix.
Verdict: **not a recommendation.** Do not make it a load-bearing dependency.

### 1.2 What replaced it

There is no single successor. The ecosystem fragmented into per-model wrappers:

| Project | Stars | Last push | Registry downloads | Verdict |
|---|---|---|---|---|
| `kijai/ComfyUI-Hunyuan3DWrapper` | 1,014 | 2026-03-16 (crawl 06-15) | 27,107 | Most-used 3D node pack. 143 open issues — busy, not dead. |
| `if-ai/ComfyUI-IF_Trellis` | 447 | 2025-03-09 | 21,934 (v0.2.5, 2025-03-09) | **Stale** — 16 months, no release since. |
| `Comfy-Org/ComfyUI` (host) | 121,849 | 2026-07-22 | — | Very healthy. |

### 1.3 The better self-hosting pattern: a plain REST backend

**`FishWoWater/3DAIGC-API`** — Apache-2.0, 29★, last push 2026-01-18. Small project, but it is exactly the shape
this pipeline wants and is the only OSS thing found that is *designed* as a backend rather than a GUI:

- FastAPI + Redis + separate scheduler, `docker compose up -d` one-liner, published Docker Hub image
  `fishwowater/3daigc-api`, and a **one-click RunPod template**.
- VRAM-aware GPU scheduling, dynamic model load/unload, async job queue, GLB/OBJ/FBX out.
- Ships TRELLIS (12 GB), TRELLIS.2 (24 GB), Hunyuan3D-2.1 geometry-only (8 GB) / textured (19 GB),
  UltraShape (25 GB), PartPacker (10 GB), UniRig auto-rig (9 GB), P3-SAM segmentation, VoxHammer mesh editing.
  (VRAM figures are the project's own pytest numbers on a single 4090.)

Risk: 29 stars, one maintainer, bus factor 1. Treat it as **a reference implementation to fork**, not a
dependency to pin.

**Model-repo-native servers** (lower risk, less featureful):
- `Tencent-Hunyuan/Hunyuan3D-2.1` (2,277★, last push 2025-10-17) ships both `gradio_app.py` and an
  `api_server.py` with Pydantic request models (`GenerationRequest{image: base64 str, texture: bool, seed: int}`)
  and auto-generated OpenAPI docs. This is the least-glue option: POST base64 image, get GLB.
- `microsoft/TRELLIS` (13,313★, last push 2026-06-26) — actively maintained, Gradio app included.

### 1.4 Cost per generation (verified pricing, 2026-07-28)

RunPod Serverless list prices: H100 80 GB **$4.55/hr**, A100 80 GB **$2.72/hr**, L40/L40S 48 GB **$1.75/hr**,
RTX 5090 **$1.58/hr**, RTX 4090 **$1.10/hr**, L4/A5000 **$0.69/hr**.
Modal per-second: H100 **$0.001097/s** ($3.95/hr), A100 80 GB **$0.000694/s** ($2.50/hr),
L40S **$0.000542/s** ($1.95/hr), A10 **$0.000306/s**, L4 **$0.000222/s**. Modal Starter includes $30/mo credit.

Cost per generation = wall-clock seconds × rate. For a Hunyuan3D-2.1 textured job (19 GB → needs L40S/A100):

| Platform | GPU | 60 s job | 120 s job |
|---|---|---|---|
| RunPod Serverless | L40S ($0.000486/s) | **$0.029** | **$0.058** |
| RunPod Serverless | A100 80 GB ($0.000756/s) | $0.045 | $0.091 |
| Modal | L40S ($0.000542/s) | $0.033 | $0.065 |
| Modal | A100 80 GB | $0.042 | $0.083 |

So **~$0.03–0.09 per asset**, an order of magnitude under commercial per-credit pricing — *provided* you
control cold starts. Loading a 19 GB checkpoint from cold adds 30–90 s of billed time, which can triple the
cost of a single one-off generation. Batch requests, or keep one warm worker during a work session.
`[UNVERIFIED]` — the 60–120 s generation window is an assumption from the models' published VRAM/step counts,
not a measurement I made.

### 1.5 Open MCP servers for 3D generation

**There is no credible one.** Everything found is a weekend project:

| Repo | Stars | Last push | Verdict |
|---|---|---|---|
| `FishWoWater/trellis_mcp` | 4 | 2025-04-06 | Dead. |
| `MubarakHAlketbi/game-asset-mcp` | 110 | 2025-03-23 | Stale 16 months. Wraps HF Spaces, not local models. |
| `Flux159/mcp-game-asset-gen` | 14 | 2025-12-06 | Toy. |

**Recommendation: write your own, it is ~80 lines.** Point a FastMCP server at 3DAIGC-API's or
Hunyuan3D-2.1's REST endpoint and expose two tools (`generate_mesh`, `poll_job`). That is far less risk than
adopting a 4-star repo, and it puts the agent one hop from the GPU instead of two.

---

## 2. Blender-side open-source addons and bridges

| Project | Stars | Last push | Licence | Verdict |
|---|---|---|---|---|
| **`alexisrolland/ComfyUI-Blender`** | 127–167 | **2026-07-22** (registry v4.5.1) | GPL-3.0 | **Pick this.** Only actively-released Blender↔ComfyUI bridge. Blender 5.0+ (v3.3.4 is the last for 4.5). Auto-builds the Blender panel from the workflow's input/output nodes; supports a remote ComfyUI via `--listen`. 8,056 registry downloads. |
| `AIGODLIKE/ComfyUI-BlenderAI-node` | 1,354 | 2025-11-28 | GPL-3.0 | Most popular, but **8 months quiet**. Full node editor inside Blender. Watch, don't depend. |
| `AIGODLIKE/ComfyUI-CUP` | 53 | 2025-10-15 | none | Companion to the above. Same staleness. |
| `gameltb/io_comfyui` | 6 | 2025-02-04 | GPL-3.0 | **Dead.** |
| **`ucupumar/ucupaint`** | 2,195 | **2026-07-27** | GPL-3.0 | **Very healthy.** Layered texturing + bake management inside Blender. The best OSS answer for "combine/bake the AI's texture into a clean channel set". |
| `ksami/QRemeshify` | 1,030 | 2024-10-08 (crawl 2026-05) | GPL-3.0 | Wraps QuadWild-BiMDF as a Blender 4.2+ extension. **Code is ~21 months old** and README says "Windows (still testing Linux and macOS)". Do not rely on it on Apple Silicon. |
| `KhronosGroup/glTF-Blender-IO` | 1,643 | 2026-07-09 | Apache-2.0 | Ships with Blender. Healthy. This is your GLB import/export. |

**On Blender-side wheels (important, verified against the 5.2 manual).** Blender 5.2 bundles **Python 3.13**
(the `bpy` 5.2.0 PyPI wheel is `cp313`; `bpy` 4.5.x is `cp311`). Extensions bundle native dependencies as
wheels declared in `blender_manifest.toml`:

```toml
wheels = [
  "./wheels/pillow-12.1.0-cp313-cp313-macosx_11_0_arm64.whl",
  "./wheels/pillow-12.1.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
]
```
fetched with
```bash
pip download pillow --dest ./wheels --only-binary=:all: \
    --python-version=3.13 --platform=macosx_11_0_arm64
```
This is the supported way to get `trimesh`/`xatlas`/`manifold3d` *inside* Blender. **But see §5.3 — I recommend
the opposite direction.**

**`bpy` as a pip module.** `pip install bpy==5.2.0` gives `bpy-5.2.0-cp313-cp313-macosx_11_0_arm64.whl`
(released 2026-07-14). This means the agent can run Blender **in-process inside a normal venv on the Mac**,
alongside trimesh/xatlas/pymeshlab, with no `--background` subprocess and no wheel bundling. Requires exactly
Python 3.13 (`requires_python: ==3.13.*`). This is the cleanest integration point in the whole stack.

**blender-mcp ecosystem** (user already has research; brief): `ahujasid/blender-mcp` 24,572★, last push
2026-07-21 — dominant and healthy. `sandraschi/blender-mcp` 16★ (2026-07-04), `djeada/blender-mcp-server` 0★
(2026-03-22), `dhakalnirajan/blender-open-mcp` 104★ (2026-04-21), `cwahlfeldt/blender-mcp` 12★ (2025-03-05,
dead). The alternatives are all single-digit-to-low-hundred star projects; none is a safe replacement for the
mainline. `dcc-mcp-blender` was not resolvable via the metadata APIs — `[UNVERIFIED]`.

---

## 3. Retopology — open source (the section that matters)

### Ranked recommendation

**1. Blender QuadriFlow (built in) — use this by default.**
Bundled, GPL, zero install, runs headless, runs native on Apple Silicon, deterministic via `seed`.
Verified signature from the Blender 5.2 API docs:

```python
bpy.ops.object.quadriflow_remesh(*, use_mesh_symmetry=True, use_preserve_sharp=False,
    use_preserve_boundary=False, preserve_attributes=False, smooth_normals=False,
    mode='FACES', target_ratio=1.0, target_edge_length=0.1, target_faces=4000,
    mesh_area=-1.0, seed=0)
```
Note the docstring warning: *"All data layers will be lost"* — UVs and vertex colours are destroyed unless you
pass `preserve_attributes=True`, and even then you should bake from the original, not rely on reprojection.

Quad flow: **good, not great.** Isotropic quads that follow curvature; edge loops do not reliably follow
hard-surface features or anatomical flow. Perfectly adequate for game props and render meshes; not adequate for
a face that needs to deform.

```python
# headless: blender --background --python retopo.py -- in.glb out.glb 6000
import bpy, sys
argv = sys.argv[sys.argv.index("--")+1:]
src, dst, faces = argv[0], argv[1], int(argv[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.quadriflow_remesh(mode='FACES', target_faces=faces,
    use_preserve_sharp=True, use_preserve_boundary=True, smooth_normals=True, seed=0)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB')
```

**2. Blender Voxel Remesh / Remesh modifier — the AI-mesh triage step, not retopo.**
Verified `bpy.types.RemeshModifier` properties: `mode` ∈ `{BLOCKS, SMOOTH, SHARP, VOXEL}` (default `VOXEL`),
`voxel_size` (default 0.1), `adaptivity` (default 0.0 — *"A value greater than 0 disables Fix Poles"*),
`octree_depth` (1–24, default 4), `sharpness` (default 1.0), `use_remove_disconnected` (default True),
`threshold`, `use_smooth_shade`. `bpy.ops.object.voxel_remesh()` takes no arguments — set
`ob.data.remesh_voxel_size` / `remesh_voxel_adaptivity` on the mesh first.

Voxel remesh is **OpenVDB-backed** in Blender and is the single most reliable way to turn a self-intersecting,
non-manifold generated blob into one watertight triangle shell. Output is all-triangles and uniform — it is a
*repair* operation. Correct order is **voxel remesh → QuadriFlow**, never QuadriFlow alone on a raw generation.

**3. Blender Decimate modifier — the cheap path.**
`decimate_type` ∈ `{COLLAPSE, UNSUBDIV, DISSOLVE}`; `ratio` (collapse), `angle_limit` (planar, default
0.0872665 rad = 5°), `use_collapse_triangulate`, `use_symmetry`/`symmetry_axis`, `delimit`. Triangles only, no
flow. Fine for LODs and static props, useless for deformation.

**4. Instant Meshes — best standalone quad flow, but the repo is frozen.**
`wjakob/instant-meshes`, 5,918★, **last push 2022-01-03** — over four years dormant. BSD-style licence
(LICENSE.txt). Precompiled binaries are **Intel-only**; on Apple Silicon you must build from source
(`cmake . && make -j`) and it will run under Rosetta or as an arm64 build depending on your toolchain
`[UNVERIFIED — I could not build it here]`.

The README documents only the GUI, but **batch mode exists** — confirmed by reading `src/main.cpp`, which
`#include "batch.h"` and prints:

```
Syntax: Instant Meshes [options] <input mesh / point cloud / application state snapshot>
   -o, --output <output>     Writes to the specified PLY/OBJ output file in batch mode
   -t, --threads <count>     Number of threads used for parallel computations
   -d, --deterministic       Prefer (slower) deterministic algorithms
   -c, --crease <degrees>    Dihedral angle threshold for creases
   -S, --smooth <iter>       Number of smoothing & ray tracing reprojection steps (default: 2)
   -D, --dominant            Generate a tri/quad dominant mesh instead of a pure tri/quad mesh
   -i, --intrinsic           Intrinsic mode (extrinsic is the default)
   -b, --boundaries          Align to boundaries (only applies when the mesh is not closed)
   -r, --rosy <number>       Specifies the orientation symmetry type (2, 4, or 6)
   -p, --posy <number>       Specifies the position symmetry type (4 or 6)
   -s, --scale <scale>       Desired world space length of edges in the output
   -f, --faces <count>       Desired face count of the output mesh
   -v, --vertices <count>    Desired vertex count of the output mesh
```
Only one of `--scale`/`--faces`/`--vertices` may be given. Invocation:

```bash
"./Instant Meshes" input.obj -o out.obj -f 6000 -c 30 -d -S 2 -b
```

Quality: **noticeably better edge flow than QuadriFlow** on organic shapes; that is why Modo licensed the
algorithm. But: unmaintained repo, no arm64 binary, no Python API, and it needs a clean manifold input (feed it
the voxel-remeshed mesh, never the raw generation). Use it as an *optional quality upgrade*, wrapped in
`subprocess`, with QuadriFlow as the always-available fallback.

**5. QuadWild / QuadWild-BiMDF — best quality, worst ergonomics.**
`nicopietroni/quadwild` 175★ last push 2022-09-09 (**dormant**);
`cgg-bern/quadwild-bimdf` 78★ last push 2024-10-18 (**dormant**). Both GPL-3.0.
BiMDF removes the Gurobi requirement — `QUADRETOPOLOGY_WITH_GUROBI` is an opt-in CMake flag, so a
fully-open build is possible. Two-stage CLI, verbatim from the README:

```bash
./build/Build/bin/quadwild path/to/input/mesh.obj 2 config/prep_config/basic_setup.txt
./build/Build/bin/quad_from_patches path/to/input/mesh_rem_p0.obj 123 config/main_config/flow_noalign_lemon.txt
```
(the `_rem_p0.obj` suffix is the first stage's output). Feature-line-driven quad flow — the best pure-geometry
result available in open source, especially on hard-surface. Cost: heavy CMake build (libigl, CGAL, Eigen,
LEMON), two dormant repos, no macOS CI. `ksami/QRemeshify` packages it for Blender but is Windows-first and
itself 21 months stale. **Recommendation: skip on a MacBook unless you are prepared to maintain a build.**

**6. AutoRemesher (`huxingyi/autoremesher`)** — 1.2k–3.0k★, but **last release 1.0.0-beta.3, 2020-09-26**.
GPL-3.0, GUI-only, no CLI, built on Geogram/libigl/OpenVDB/CGAL. ecosyste.ms reports a recent push
(2026-07-21) that is inconsistent with a six-year-old last release — I could not reconcile these.
**Treat as abandoned.** Not a recommendation.

**7. Learned retopology, 2026.** I found **no** learned quad-retopology method shipping usable, installable,
maintained code. `NeurCross` (neural cross-field computation for quad meshing) is the closest research result;
`Bigger-and-Stronger/quad-meshing-survey` is the tracking list. There are also commercial-adjacent hosted
"AI retopology" services (Neural4D, Tripo) which are not open source and not self-hostable.
**Conclusion: learned retopo is not yet a real option for this pipeline in 2026.** Field-aligned classical
methods remain the state of the practice.

### Summary table

| Tool | Quad flow | Headless/CLI | Licence | Apple Silicon | Health |
|---|---|---|---|---|---|
| Blender QuadriFlow | Good, isotropic | **Yes**, `bpy.ops` | GPL-2/3 | **Native** | Ships with Blender |
| Blender Voxel Remesh (OpenVDB) | N/A (tris) | **Yes** | GPL | **Native** | Ships with Blender |
| Blender Decimate | N/A (tris) | **Yes** | GPL | **Native** | Ships with Blender |
| Instant Meshes | **Very good** | Yes (undocumented) | BSD-style | Build from source | **Dormant since 2022-01** |
| QuadWild-BiMDF | **Best** | Yes (2-stage) | GPL-3.0 | Build from source | **Dormant since 2024-10** |
| AutoRemesher | Good | **No** | GPL-3.0 | Unclear | **Abandoned (2020)** |
| Learned retopo | — | — | — | — | **Does not exist usably** |

---

## 4. UV unwrapping — open source

### xatlas — the default for automated pipelines

`jpcy/xatlas` 2,255★ MIT, last push 2024-06-16 (C++ core is stable/finished rather than abandoned).
Python bindings `mworchel/xatlas-python` 209★ MIT, last push 2025-07-04, PyPI **`xatlas` 0.0.11** (2025-07-04).
**Apple Silicon wheels confirmed**: `cp38`–`cp313` `macosx_11_0_arm64` plus PyPy.

Verified working example (executed here — repaired 1,280-face mesh):

```python
import numpy as np, trimesh, xatlas
mf = trimesh.load("clean.ply")

atlas = xatlas.Atlas()
atlas.add_mesh(np.asarray(mf.vertices), np.asarray(mf.faces))
co = xatlas.ChartOptions(); co.max_cost = 2.0          # lower = more, flatter charts
po = xatlas.PackOptions(); po.resolution = 1024; po.padding = 4
atlas.generate(chart_options=co, pack_options=po)

vmapping, indices, uvs = atlas[0]
print(atlas.width, atlas.height, atlas.utilization, atlas.get_mesh_chart_count(0))
# observed: 852 1350 0.742 6   (0.08 s)

out = trimesh.Trimesh(np.asarray(mf.vertices)[vmapping], indices,
                      visual=trimesh.visual.TextureVisuals(uv=uvs), process=False)
out.export("uv.glb")
```

**Gotchas I hit and you will too:** `parametrize` duplicates vertices along seams (642 → 755 here), so you must
re-index all your attributes through `vmapping`. And `PackOptions.resolution` is a *hint*, not a command — I
asked for 1024 and got an 852×1350 atlas. If you need a fixed square atlas, set `po.resolution` and then
rescale/repack, or do the final pack in Blender.

**Packing efficiency observed: 0.742** on a 6-chart organic mesh. That is competitive with commercial packers
and clearly better than Blender's `smart_project` defaults on the same class of geometry
`[UNVERIFIED — I did not run a head-to-head with Blender in this container]`.

### Blender's own UV tools — verified 5.2 signatures

```python
bpy.ops.uv.smart_project(*, angle_limit=1.15192, margin_method='SCALED',
    rotate_method='AXIS_ALIGNED_Y', island_margin=0.0, area_weight=0.0,
    correct_aspect=True, scale_to_bounds=False)

bpy.ops.uv.pack_islands(*, udim_source='CLOSEST_UDIM', rotate=True, rotate_method='ANY',
    scale=True, merge_overlap=False, margin_method='SCALED', margin=0.001,
    pin=False, pin_method='LOCKED', shape_method='CONCAVE')

bpy.ops.uv.unwrap(*, method='CONFORMAL', fill_holes=False, correct_aspect=True,
    use_subsurf_data=False, use_original_bounds=False, margin_method='SCALED',
    margin=0.001, no_flip=False, iterations=10, use_weights=False,
    weight_group='uv_importance', weight_factor=1.0)
```

Two things worth knowing for 5.2: `unwrap` now defaults to `method='CONFORMAL'` and offers
`'MINIMUM_STRETCH'` (SLIM), which with `iterations=10` gives materially lower stretch than angle-based on
organic meshes. And `pack_islands(shape_method='CONCAVE')` is a genuinely good packer — concave hull packing
beats xatlas's rectangular packing on island-dense meshes.

**Practical rule:** use **xatlas for charting** (it cuts seams intelligently), then **Blender
`pack_islands(shape_method='CONCAVE', rotate_method='ANY', margin=0.002)` for packing**. Best of both.
`bpy.ops.uv.lightmap_pack(PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.1, ...)` covers a second lightmap UV channel.

### UVAtlas — dead, and irrelevant here

`microsoft/UVAtlas`: **"This repository was archived by the owner on Apr 24, 2026. It is now read-only."**
926★, MIT, last release Oct 2025. It is also Windows/DirectXMath-oriented (VS2019/2022, MinGW, WSL).
**Not a recommendation. Do not use.**

### Learned UV methods

Nothing shippable found. Research exists (Nuvo, FlatCAD-family, seam-prediction nets) but no maintained,
installable implementation with a stable API as of 2026-07. `[UNVERIFIED — absence of evidence]`
xatlas remains the state of the practice.

---

## 5. Mesh repair / validation libraries

### 5.1 The table

| Library | Solves | Licence | pip | macOS arm64 | Health (last push / release) |
|---|---|---|---|---|---|
| **trimesh** 4.12.2 | Orchestration, IO, watertight/winding/volume checks, boolean front-end, GLB export | MIT | ✅ `py3-none-any` | ✅ (pure Python) | 3,616★, push **2026-07-12**, rel **2026-05-01**. 488 open issues (large surface, not neglect). |
| **manifold3d** 3.5.2 | **Guaranteed-manifold booleans**, self-intersection removal | Apache-2.0 | ✅ | ✅ `cp39–cp314` arm64 + universal2 | `elalish/manifold` 2,158★, push **2026-07-19**, rel v3.4.1 2026-03-24. Used by Blender, OpenSCAD, Godot, BRL-CAD, Babylon.js, trimesh. **Best-maintained thing in this list.** |
| **pymeshfix** 0.18.1 | Hole filling, degenerate/duplicate removal, forces closed 2-manifold | **GPL-3.0** | ✅ | ✅ `cp310/311/312-abi3` arm64 | 389★, push **2026-07-01**, rel 2026-04-23. Only 2 open issues. |
| **PyMeshLab** 2025.7.post1 | The kitchen sink: non-manifold repair, close holes, isotropic remesh, quadric decimation, parametrisation, texture transfer | **GPL-3.0** | ✅ | ✅ `cp310–cp314` arm64 | 960★, push 2026-02-03. MeshLab core 5,758★ push 2026-06-08. |
| **libigl** 2.6.2 | Geometry-processing primitives (winding number, SDF, harmonic/LSCM params) | MPL-2.0 core; `igl/copyleft/*` is **GPL** (CGAL/tetgen) | ✅ | ✅ arm64 | 5,058★, push **2026-07-15**, rel 2026-03-05. ecosyste.ms labels the repo `gpl-3.0`; the split-licence nuance is real — check which headers you use. |
| **Open3D** 0.19.0 | Point clouds, Poisson/ball-pivot reconstruction, registration, normals | MIT | ✅ | ⚠️ via `macosx_10_15_universal2` (cp310–cp312 only) | 13,813★, repo push 2026-07-21, but **last PyPI release 2025-01-08 (18 months)**. No cp313/cp314 wheels → **incompatible with Blender 5.2's Python 3.13**. |
| **PyVista** 0.48.4 | VTK front-end: visualisation, filtering, `pymeshfix` integration | MIT | ✅ pure Python | ✅ (VTK 9.6.2 has cp39–cp314 arm64 wheels) | 2026-05-18 release. Healthy. Optional. |
| fast-simplification 0.1.13 | Fast quadric decimation (trimesh's backend) | MIT | ✅ | ✅ arm64 | rel 2025-12-19. Install it — `trimesh.simplify_quadric_decimation()` **raises `ModuleNotFoundError` without it** (observed). |

### 5.2 PyMeshLab's headless gotcha (found the hard way)

On a headless Linux box PyMeshLab silently loses half its plugins:

```
Cannot load library .../libfilter_meshing.so: (libOpenGL.so.0: cannot open shared object file...)
```
`meshing_*` and `filter_texture_defragmentation` are among the casualties. Fix: `apt-get install -y libopengl0
libgl1` — after which all 44 relevant filters load. **On macOS this does not occur** (OpenGL framework is part
of the OS), but it will bite you the moment you containerise the pipeline for CI.

### 5.3 Bundled Blender Python vs a separate venv — my recommendation

**Do not install these into Blender's bundled Python.** Blender 5.2 bundles Python 3.13; Open3D has no 3.13
wheel, PyMeshLab pulls Qt libs, and modifying the bundled interpreter breaks on every Blender update.

Instead: **one venv on Python 3.13 containing `bpy==5.2.0` *and* the mesh libraries.** Verified from PyPI:
`bpy-5.2.0-cp313-cp313-macosx_11_0_arm64.whl`, released 2026-07-14, `requires_python: ==3.13.*`. Then
`import bpy` and `import trimesh` live in the same process, no subprocess, no wheel bundling, no IPC.
Drop Open3D (you do not need it for mesh cleanup — it is a point-cloud library).

If you must keep a real Blender.app in the loop (for addons that need the full install), bundle wheels via
`blender_manifest.toml` as shown in §2, or shell out from your venv with `blender --background --python`.

### 5.4 Recipe: "make this AI mesh watertight and printable"

All of the following was **executed and verified**.

**Path A — boolean union of overlapping parts (fastest, best quality when the input is a union of solids):**

```python
import trimesh
a = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
b = trimesh.creation.icosphere(subdivisions=3, radius=0.7); b.apply_translation([0.9,0,0])
fixed = trimesh.boolean.union([a, b], engine='manifold')   # manifold3d backend
print(fixed.is_watertight, fixed.volume, len(fixed.faces))
# -> True 4.9164 2208   (0.01 s)
```

**Path B — general repair of a torn, self-intersecting shell (`pymeshfix`):**

```python
import numpy as np, trimesh, pymeshfix
m = trimesh.load("raw_generated.glb", force='mesh')
print(m.is_watertight, m.is_volume, m.euler_number)     # -> False False 3

v, f = pymeshfix.clean_from_arrays(
    np.ascontiguousarray(m.vertices, dtype=np.float64),   # dtype cast is MANDATORY:
    np.ascontiguousarray(m.faces,    dtype=np.int32))     # TrackedArray is rejected by nanobind
mf = trimesh.Trimesh(v, f, process=False)
print(mf.is_watertight, mf.is_volume)                     # -> True True
```
It may print `MeshFix could not fix everything` and still return a valid closed 2-manifold — check
`is_watertight`/`is_volume`, not stderr.

**Path C — full PyMeshLab chain (verified parameter names, 10,180 F in → 4,000 F out, watertight):**

```python
import pymeshlab as ml
ms = ml.MeshSet(); ms.load_new_mesh("raw_generated.ply")
ms.meshing_remove_duplicate_vertices()
ms.meshing_remove_duplicate_faces()
ms.meshing_remove_null_faces()
ms.meshing_remove_unreferenced_vertices()
ms.meshing_repair_non_manifold_edges(method='Remove Faces')
ms.meshing_repair_non_manifold_vertices(vertdispratio=0)
ms.meshing_close_holes(maxholesize=300, newfaceselected=False, selfintersection=True)
ms.meshing_isotropic_explicit_remeshing(iterations=3, targetlen=ml.PercentageValue(1.5))
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=4000, preservenormal=True,
        preserveboundary=True, planarquadric=True, qualitythr=0.4)
ms.save_current_mesh("clean.ply")
# verified: final watertight=True is_volume=True F=4000
```

**Printability gate before slicing:**

```python
assert mf.is_watertight and mf.is_volume and mf.is_winding_consistent
assert mf.volume > 0                       # negative volume = inverted normals
mf.remove_degenerate_faces(); mf.remove_unreferenced_vertices()
mf.apply_scale(1000.0 / mf.extents.max())  # normalise longest axis to 100 mm (units = mm)
mf.export("print.stl")
```
Thin-wall / minimum-feature checking is **not** covered by any of these libraries — that is a slicer job
(PrusaSlicer/Cura, both open source) and it needs human judgement.

---

## 6. Texture / PBR post-processing

**Delighting: the open-source situation is bad.** Every candidate is dead — `Unity-Technologies/DeLightingTool`
(542★, **last push 2020-05-04**, Unity-editor-bound); `Stable-X/StableDelight` (24★, **2024-09-08**, and it
removes speculars, not lighting); `OpenTexture/Paint3D` (750★, **2024-11-05**, CVPR'24 — generates clean albedo
rather than delighting an existing map).

Practical consequence: **delighting is where you should still expect to intervene by hand**, or sidestep it by
using a generator whose texture path is already PBR/lighting-free (Hunyuan3D-2.1 advertises "production-ready
PBR material"). Agisoft De-Lighter is free-as-in-beer but closed and macOS support is unclear `[UNVERIFIED]`.

**Baking — use Blender, it is the strongest open tool here.** Verified 5.2 signature:

```python
bpy.ops.object.bake(*, type='COMBINED', pass_filter=set(), filepath='', width=512, height=512,
    margin=16, margin_type='EXTEND', use_selected_to_active=False, max_ray_distance=0.0,
    cage_extrusion=0.0, cage_object='', normal_space='TANGENT',
    normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', target='IMAGE_TEXTURES',
    save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False,
    use_automatic_name=False, uv_layer='')
```
High-to-low transfer for AI assets: `use_selected_to_active=True`, `use_cage=True`,
`cage_extrusion≈0.02×bbox`, `type='NORMAL'` then `type='DIFFUSE'` with
`pass_filter={'COLOR'}` (colour only, no lighting — this is your poor-man's delight), then `'AO'`, `'ROUGHNESS'`.
Requires Cycles; works on Apple Silicon via Metal.

**`ucupumar/ucupaint`** (2,195★, push **2026-07-27**, GPL-3.0) is the healthiest OSS layered-texturing/bake
manager for Blender. GUI-oriented, so it is a human-in-the-loop tool, not an agent tool.

**Procedural material authoring / Materialize-alikes:**
- `RodZill4/material-maker` — 5,604★, push 2026-07-14, **MIT**, Godot-based, has a batch/CLI export mode.
  Healthiest option.
- `armory3d/armorpaint` — 3,987★, push 2026-07-23. 3D painting + PBR.
- `njbrown/texturelab` — 799★, push 2026-07-16.
- `hypernewbie/pbr_baker` — 14★, **last push 2019**. Dead.

**Normal map from height:** no maintained standalone OSS tool worth naming. Do it in Blender's compositor or
with a 5-line Sobel in numpy/Pillow — it is not a problem that needs a dependency.

**Texture atlasing:** xatlas (§4) or `gltf-transform unwrap` (which uses an xatlas binding under the hood).

**Texture compression — all healthy:**
- `BinomialLLC/basis_universal` — 3,069★, Apache-2.0, push **2026-07-18**. ETC1S/UASTC.
- `KhronosGroup/KTX-Software` — 1,317★, push **2026-07-24**. `ktx create --encode uastc --zcmp 18 ...`.
- `google/draco` — 7,405★, Apache-2.0, repo push **2026-07-01**; Homebrew `draco` 1.5.7 with
  `arm64_tahoe`/`arm64_sequoia`/`arm64_sonoma` bottles → **`brew install draco` works on Apple Silicon**.
  Note the npm `draco3d` package is stuck at 1.5.7 from **2024-01-17** — the JS binding lags the C++ repo.
- In practice you will never call these directly: `gltfpack -tc` and `gltf-transform etc1s/uastc` wrap them.

---

## 7. glTF / asset optimisation

| Tool | Version (verified) | Licence | Role |
|---|---|---|---|
| **gltfpack** (meshoptimizer) | **1.2.0**, npm 2026-06-30; repo `zeux/meshoptimizer` 8,149★ push **2026-07-25**, only **6 open issues** | MIT | One-shot "make it small and fast". Simplify + quantise + reorder + KTX2 + meshopt compress. |
| **gltf-transform** | **4.4.2**, npm 2026-07-25; repo 1,906★ push 2026-07-02 | MIT | Surgical, scriptable, composable. Also a JS/TS API, not just a CLI. |
| **Draco** | 1.5.7 (npm) / repo active | Apache-2.0 | Geometry codec. Better ratio than meshopt, slower decode, no random access. |

**Verified round-trip run in this container** on the 31,780-byte repaired GLB from §5:

```bash
npm i -g gltfpack @gltf-transform/cli
gltfpack -i repaired.glb -o packed.glb -si 0.5 -cc
# 31,780 bytes -> 6,232 bytes  (5.1x)
gltf-transform inspect packed.glb
# extensionsUsed: KHR_mesh_quantization, EXT_meshopt_compression, KHR_texture_transform
```

Real `gltfpack -h` flags that matter here: `-si R` simplify to ratio R (0..1) · `-se E` limit simplification
error (default 0.01 = 1% deviation) · `-slb` lock border verts to avoid gaps · `-tc` textures → KTX2/BasisU ·
`-tu` UASTC (higher quality, larger) · `-tq N` texture quality 1–10 (default 8) · `-tl N` cap texture dimension ·
`-vp/-vt/-vn N` quantisation bits for positions/UVs/normals (defaults 14/12/8) · `-gt` generate tangent frames ·
`-cc` meshopt compression · `-kn/-km/-ke` keep named nodes / materials / extras.

Texture *classes* are the underused feature: `-tc color,attrib -tu normal -tq normal 10` compresses colour
with ETC1S and normals with high-quality UASTC in one pass.

gltf-transform commands: `optimize`, `simplify`, `weld`, `dedup`, `prune`, `quantize`, `resize`, `draco`,
`meshopt`, `etc1s`, `uastc`, `webp`, `tangents` (MikkTSpace), `unwrap` (generates texcoords), `unlit`, `inspect`.

**Which to use where.** `gltf-transform` for anything you need to reason about or do conditionally (it has a
real API and `inspect` gives you machine-readable stats); `gltfpack` as the final one-shot squeeze. Never run
both simplifiers — pick one. **Always run `-kn -km` if a downstream tool looks up nodes/materials by name**,
otherwise gltfpack merges and renames them and your agent's later `bpy.data.objects["Body"]` lookup fails.

---

## 8. Concrete end-to-end pipelines

Assumed layout: a Python 3.13 venv with `bpy==5.2.0 trimesh xatlas manifold3d pymeshfix pymeshlab
fast-simplification pillow`, plus `npm i -g gltfpack @gltf-transform/cli`. Input: `raw.glb` from a rented GPU.

### Stage 0 — triage (all pipelines, fully automatable)

```python
import trimesh
m = trimesh.load("raw.glb", force='mesh')
report = dict(F=len(m.faces), V=len(m.vertices), watertight=m.is_watertight,
              volume_ok=m.is_volume, winding=m.is_winding_consistent,
              euler=m.euler_number, bodies=len(m.split(only_watertight=False)),
              extents=m.extents.tolist())
```
Gate: if `bodies > 1` and the parts overlap → `trimesh.boolean.union(parts, engine='manifold')`.
If `not watertight` → §5 Path B or C. Only then proceed.

### (a) Game-ready asset (GLB, ~5–15k tris, one 2K PBR set)

```bash
# 1. repair + decimate to a mid-poly base
python clean.py raw.glb mid.ply           # PyMeshLab chain from §5.4 Path C, targetfacenum=60000

# 2. retopo to quads (Blender, headless)
blender --background --python retopo.py -- mid.ply retopo.glb 8000
#    quadriflow_remesh(mode='FACES', target_faces=8000,
#                      use_preserve_sharp=True, use_preserve_boundary=True)

# 3. UV: xatlas charts, Blender concave pack
python uv.py retopo.glb retopo_uv.glb     # §4 recipe, then bpy.ops.uv.pack_islands(
                                          #   shape_method='CONCAVE', rotate_method='ANY', margin=0.002)

# 4. bake raw.glb -> retopo_uv.glb  (Cycles, selected-to-active, cage)
blender --background --python bake.py -- raw.glb retopo_uv.glb 2048
#    passes: NORMAL (TANGENT), DIFFUSE pass_filter={'COLOR'}, AO, ROUGHNESS

# 5. ship
gltf-transform prune baked.glb t1.glb
gltf-transform weld t1.glb t2.glb
gltfpack -i t2.glb -o final.glb -cc -tc color,attrib -tu normal -tq 8 -tq normal 10 -vp 14 -vt 12 -kn -km
gltf-transform inspect final.glb
```
Agent-reliable: 1, 2, 3, 5. **Human needed: 4** — cage extrusion and `max_ray_distance` need eyes on the
result; a bad cage produces smeared normals that no automated check will catch. Also human: judging whether
QuadriFlow's loop placement is acceptable for a mesh that will deform.

### (b) Printable STL

```python
import trimesh, numpy as np, pymeshfix
m = trimesh.load("raw.glb", force='mesh')

parts = m.split(only_watertight=False)
m = trimesh.boolean.union(list(parts), engine='manifold') if len(parts) > 1 else m

if not m.is_watertight:
    v, f = pymeshfix.clean_from_arrays(np.ascontiguousarray(m.vertices, np.float64),
                                       np.ascontiguousarray(m.faces, np.int32))
    m = trimesh.Trimesh(v, f, process=False)

m.remove_degenerate_faces(); m.remove_unreferenced_vertices(); m.fix_normals()
assert m.is_watertight and m.is_volume and m.volume > 0

m.apply_scale(120.0 / m.extents.max())     # 120 mm longest axis
m.export("print.stl")
print("volume cm^3:", m.volume / 1000.0)   # -> filament estimate
```
Optional pre-step for really bad generations: Blender voxel remesh at `remesh_voxel_size = bbox_max/256`,
`remesh_voxel_adaptivity = 0.0`, then the above. **Do not use QuadriFlow for print** — quads buy nothing and
the tri conversion can reintroduce non-planar faces.

Agent-reliable: everything above. **Human needed:** wall thickness, overhang/support strategy, orientation on
the plate, whether the model should be hollowed and drained. No open library answers these.

### (c) Render-ready product-viz asset

```bash
# 1. repair, but keep density — quality over budget
python clean.py raw.glb hi.ply            # skip the decimation call; keep isotropic remesh

# 2. quad retopo at high density, preserve sharp features
blender --background --python retopo.py -- hi.ply retopo.blend 40000

# 3. UVs with low stretch: Blender SLIM rather than xatlas
#    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', iterations=10, margin=0.003)
#    bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate_method='ANY', margin=0.003)

# 4. bake 4K, then hand-authored materials (Principled BSDF / OpenPBR)
# 5. NO gltfpack. Keep .blend + 4K PNG/EXR. Export USD or GLB uncompressed only if handing off.
```
Agent-reliable: 1, 2, 3, and mechanical parts of 4 (creating image datablocks, wiring nodes, running bakes).
**Human needed:** shading intent (which surfaces are metal, what roughness story the product has), lighting,
camera, and the delighting decision. This is the pipeline where automation buys the least.

### What the agent should never decide alone

1. **Delighting** — no working OSS tool (§6); baked lighting silently poisons every downstream render.
2. **Edge flow for deformation** — QuadriFlow is topology-blind; loops around eyes/mouth/joints are a human call.
3. **Scale and units** — generated meshes are unit-normalised; the agent cannot infer "this vase is 30 cm".
4. **Print manufacturability** — thickness, supports, orientation.
5. **Whether the asset is good** — no metric in this document measures that.

### Recommended install, one block

```bash
python3.13 -m venv ~/.venvs/blenderpipe && source ~/.venvs/blenderpipe/bin/activate
pip install "bpy==5.2.0" trimesh xatlas manifold3d pymeshfix pymeshlab \
            fast-simplification pillow numpy
npm i -g gltfpack @gltf-transform/cli
brew install draco                       # optional; gltfpack/gltf-transform cover most cases
# optional quality upgrade, build from source, no arm64 binary published:
#   git clone --recursive https://github.com/wjakob/instant-meshes && cd instant-meshes && cmake . && make -j
```
All pip packages above publish `macosx_11_0_arm64` wheels for cp313 **except** `pymeshlab` (cp310–cp314 arm64 —
covered) and `bpy` (cp313 arm64 — covered). **Open3D is deliberately excluded**: no cp313 wheel, last release
2025-01-08.

---

## Sources

Repo health via ecosyste.ms (`https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/...`), package
metadata via `pypi.org/pypi/<pkg>/json`, `registry.npmjs.org`, `api.comfy.org/nodes/<id>`,
`formulae.brew.sh/api/formula/<f>.json`.

- [MrForExample/ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack) · [issues](https://github.com/MrForExample/ComfyUI-3D-Pack/issues)
- [kijai/ComfyUI-Hunyuan3DWrapper](https://github.com/kijai/ComfyUI-Hunyuan3DWrapper) · [if-ai/ComfyUI-IF_Trellis](https://github.com/if-ai/ComfyUI-IF_Trellis)
- [FishWoWater/3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) ([README](https://raw.githubusercontent.com/FishWoWater/3DAIGC-API/main/README.md)) · [FishWoWater/trellis_mcp](https://github.com/FishWoWater/trellis_mcp)
- [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) ([API_DOCUMENTATION.md](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/API_DOCUMENTATION.md)) · [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS)
- [MubarakHAlketbi/game-asset-mcp](https://github.com/MubarakHAlketbi/game-asset-mcp) · [Flux159/mcp-game-asset-gen](https://github.com/Flux159/mcp-game-asset-gen)
- [RunPod pricing](https://www.runpod.io/pricing) · [Modal pricing](https://modal.com/pricing)
- [alexisrolland/ComfyUI-Blender](https://github.com/alexisrolland/ComfyUI-Blender) · [AIGODLIKE/ComfyUI-BlenderAI-node](https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node) · [AIGODLIKE/ComfyUI-CUP](https://github.com/AIGODLIKE/ComfyUI-CUP) · [gameltb/io_comfyui](https://github.com/gameltb/io_comfyui)
- [ucupumar/ucupaint](https://github.com/ucupumar/ucupaint) · [ksami/QRemeshify](https://github.com/ksami/QRemeshify) · [KhronosGroup/glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO)
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) · [sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp) · [djeada/blender-mcp-server](https://github.com/djeada/blender-mcp-server) · [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp)
- Blender 5.2 API: [bpy.ops.object](https://docs.blender.org/api/current/bpy.ops.object.html) · [bpy.ops.uv](https://docs.blender.org/api/current/bpy.ops.uv.html) · [RemeshModifier](https://docs.blender.org/api/current/bpy.types.RemeshModifier.html) · [DecimateModifier](https://docs.blender.org/api/current/bpy.types.DecimateModifier.html)
- Blender 5.2 manual: [Remeshing](https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html) · [Remesh modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/remesh.html) · [Python Wheels](https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html)
- [wjakob/instant-meshes](https://github.com/wjakob/instant-meshes) ([src/main.cpp](https://raw.githubusercontent.com/wjakob/instant-meshes/master/src/main.cpp)) · [nicopietroni/quadwild](https://github.com/nicopietroni/quadwild) · [cgg-bern/quadwild-bimdf](https://github.com/cgg-bern/quadwild-bimdf) · [huxingyi/autoremesher](https://github.com/huxingyi/autoremesher)
- [Bigger-and-Stronger/quad-meshing-survey](https://github.com/Bigger-and-Stronger/quad-meshing-survey) · [NeurCross](https://qiujiedong.github.io/publications/NeurCross/)
- [jpcy/xatlas](https://github.com/jpcy/xatlas) · [mworchel/xatlas-python](https://github.com/mworchel/xatlas-python) ([README](https://raw.githubusercontent.com/mworchel/xatlas-python/main/README.md)) · [microsoft/UVAtlas](https://github.com/microsoft/UVAtlas) (archived)
- [mikedh/trimesh](https://github.com/mikedh/trimesh) · [elalish/manifold](https://github.com/elalish/manifold) · [pyvista/pymeshfix](https://github.com/pyvista/pymeshfix) · [cnr-isti-vclab/PyMeshLab](https://github.com/cnr-isti-vclab/PyMeshLab) · [cnr-isti-vclab/meshlab](https://github.com/cnr-isti-vclab/meshlab) · [libigl/libigl](https://github.com/libigl/libigl) · [isl-org/Open3D](https://github.com/isl-org/Open3D) · [pyvista/pyvista](https://github.com/pyvista/pyvista)
- [Unity-Technologies/DeLightingTool](https://github.com/Unity-Technologies/DeLightingTool) · [Stable-X/StableDelight](https://github.com/Stable-X/StableDelight) · [OpenTexture/Paint3D](https://github.com/OpenTexture/Paint3D) · [RodZill4/material-maker](https://github.com/RodZill4/material-maker) · [armory3d/armorpaint](https://github.com/armory3d/armorpaint) · [njbrown/texturelab](https://github.com/njbrown/texturelab) · [hypernewbie/pbr_baker](https://github.com/hypernewbie/pbr_baker)
- [zeux/meshoptimizer](https://github.com/zeux/meshoptimizer) ([gltfpack README](https://github.com/zeux/meshoptimizer/blob/master/gltf/README.md)) · [donmccurdy/glTF-Transform](https://github.com/donmccurdy/glTF-Transform) ([CLI docs](https://gltf-transform.dev/cli)) · [google/draco](https://github.com/google/draco) · [BinomialLLC/basis_universal](https://github.com/BinomialLLC/basis_universal) · [KhronosGroup/KTX-Software](https://github.com/KhronosGroup/KTX-Software) · [AcademySoftwareFoundation/openvdb](https://github.com/AcademySoftwareFoundation/openvdb)
- [bpy on PyPI](https://pypi.org/project/bpy/) · [xatlas on PyPI](https://pypi.org/project/xatlas/) · [manifold3d on PyPI](https://pypi.org/project/manifold3d/) · [pymeshlab on PyPI](https://pypi.org/project/pymeshlab/) · [pymeshfix on PyPI](https://pypi.org/project/pymeshfix/)

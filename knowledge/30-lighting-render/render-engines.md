---
name: render-engines
domain: render
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Choosing and configuring Cycles / EEVEE / Workbench in bpy, GPU device setup, denoising traps, and what actually works under blender --background.
loads_with: [lighting, compositing-output, materials-pbr]
tags: [cycles, eevee, workbench, headless, samples, denoise, gpu, ffmpeg, render-settings]
---

# Render Engines

## 1. Mental model

`scene.render.engine` is a string enum. In 5.x the three built-ins are `'CYCLES'`,
`'BLENDER_EEVEE'` and `'BLENDER_WORKBENCH'`. The identifier changed: EEVEE was
`'BLENDER_EEVEE_NEXT'` in 4.2–4.5 and is `'BLENDER_EEVEE'` again from 5.0 — a script
that hardcodes either string breaks on the other side of that boundary.

Cycles is a physically based path tracer: correct by construction, slow, CPU-or-GPU,
noise-limited. EEVEE (rewritten as "EEVEE Next" in 4.2) is a rasteriser with
screen-space raytracing: fast, GPU-only, and approximate in ways that change the image
rather than merely making it noisier. Workbench is a solid/matcap OpenGL preview
renderer with no lights or materials — perfect for turntables, 3D-print checks and
geometry verification screenshots.

For an agent whose only feedback is a rendered image, the decisive constraint is
**headless viability**. Cycles CPU runs anywhere, including a container with no GPU.
EEVEE and Workbench are rasterisers and need a working GPU context; the manual states
plainly that "Headless rendering is not supported on headless Windows systems", and
EEVEE has "no plan to support CPU (software) rendering". So: EEVEE in `--background` is
viable on Linux and macOS *with a GPU and driver* (measured OK on this macOS 5.2.0 /
Apple Silicon install, 0.2 s for a 256 px still - see §4.8), and not viable on headless
Windows or on a GPU-less Linux container.

Second trap: **denoising hides errors**. OpenImageDenoise will happily turn a genuinely
broken, under-sampled, firefly-ridden render into a smooth plausible image. An agent that
verifies its work by looking at a denoised render can miss a light that is 100× too
bright or a material that is producing NaNs.

## 2. Decision first

| Goal | Engine | Why |
|---|---|---|
| Physically correct, GI, caustics, transmission, SSS | `CYCLES` | Only engine that path traces |
| Fast look-dev iteration, motion graphics, previz | `BLENDER_EEVEE` | Seconds per frame, GPU |
| Geometry / topology / 3D-print check, turntable | `BLENDER_WORKBENCH` | No lights or materials needed |
| Anything that must run in a GPU-less container | `CYCLES` with `cycles.device='CPU'` | Only universally headless option |
| Baking textures | `CYCLES` | EEVEE/Workbench have no bake engine |
| Rendering render passes / AOVs / cryptomatte | `CYCLES` (full set) | EEVEE supports fewer, and `BLENDED` materials break passes |
| Deterministic regression images | `CYCLES` CPU, fixed `seed`, denoise off | GPU and denoiser are not bit-reproducible |

| Constraint | Decision |
|---|---|
| Verifying own render for correctness | Denoise **off** first pass; on only for the deliverable |
| Animation, many frames, same scene | `scene.render.use_persistent_data = True` |
| Scene has thousands of small lights | Cycles `use_light_tree = True` (default) |
| Interior with slow convergence | raise `max_bounces` **and** clamp indirect; consider `use_fast_gi` |
| Glass with strong caustics | Cycles; keep `caustics_*` on, or accept the noise |
| Alpha over a plate | `scene.render.film_transparent = True`, PNG/EXR RGBA |
| Video deliverable | render PNG/EXR frames, then encode — not straight to FFmpeg |

## 3. Rules

R1. Read `scene.render.engine`, never assume it.
    Why: identifiers moved (`BLENDER_EEVEE_NEXT` in 4.2–4.5 → `BLENDER_EEVEE` in 5.x).
    Violation: `TypeError: bpy_struct: item.attr = val: enum "BLENDER_EEVEE_NEXT" not
    found in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES')`.

R2. Do not assume EEVEE can render headlessly on the machine you are on.
    Why: EEVEE is GPU-only; headless Windows is unsupported; a GPU-less Linux container
    has no EGL/Vulkan device.
    Violation: `blender --background -E BLENDER_EEVEE` aborts with a GPU/context error
    ("Unable to open a display" on legacy builds), or produces a black image.

R3. Turn denoising **off** for any render you are using to verify correctness.
    Why: OIDN removes fireflies and noise that are the visible symptom of a bad light,
    a NaN material, or too few samples.
    Violation: agent ships a "clean" image built on a broken scene; downstream comp
    reveals the artifacts.

R4. Enable GPU devices explicitly; setting `cycles.device='GPU'` alone is not enough.
    Why: `preferences.addons['cycles'].preferences.compute_device_type` must be set AND
    `device.use = True` for each device, and `get_devices_for_type()` must be called to
    populate the list.
    Violation: render silently falls back to CPU and takes 30× longer, no error.

R5. Access the Cycles preferences through a defensive lookup, not a bare key.
    Why: the key is the add-on module name — `'cycles'` for the bundled core add-on — but
    the 4.2+ extensions system introduced `bl_ext.*` module IDs for other add-ons, and
    builds without Cycles have no entry at all.
    Violation: `KeyError: bpy_prop_collection[key]: key "cycles" not found`.

R6. Clamp indirect, not direct.
    Why: `sample_clamp_indirect` (default 10.0) kills fireflies from indirect paths
    without dimming your key light. `sample_clamp_direct` (default 0.0 = off) darkens
    the actual lighting.
    Violation: scene mysteriously loses contrast and highlights after "fixing noise".

R7. `scene.render.image_settings.media_type` must be set **before** `file_format` in 5.x.
    Why: 5.0 introduced `media_type` (`'IMAGE' | 'MULTI_LAYER_IMAGE' | 'VIDEO'`) and
    `file_format`'s available enum items depend on it.
    Violation: `TypeError: ... enum "OPEN_EXR_MULTILAYER" not found in ('AVIF','JPEG',
    'OPEN_EXR','PNG',...)` or the same for `'FFMPEG'`.

R8. For a still, `bpy.ops.render.render(write_still=True)`; for a sequence,
    `animation=True`.
    Why: `write_still` is ignored when `animation=True`; without either, the result stays
    in memory only.
    Violation: render "succeeds", output directory is empty.

R9. Set `scene.render.filepath` to a directory + prefix, not a full filename, for animations.
    Why: Blender appends the frame number and extension (`use_file_extension`).
    Violation: `/out/movie.png` becomes `/out/movie.png0001.png`.

R10. Do not render straight to FFmpeg for anything you may need to re-do.
    Why: a crash at frame 400 of 500 loses the whole file; frames are resumable.
    Violation: hours of GPU time gone; no partial deliverable.

R11. `use_persistent_data = True` only for animations of a static scene.
    Why: it keeps the whole Cycles scene resident between frames — big speedup, big RAM
    cost, and it can retain stale data if you mutate the scene between frames from Python.
    Violation: OOM kill, or frames that render with the previous frame's data.

R12. EEVEE raytracing is **off** by default; without it there are no ray-traced
    reflections/GI.
    Why: `scene.eevee.use_raytracing` defaults to False.
    Violation: agent concludes "EEVEE has no reflections" and switches to Cycles
    unnecessarily.

R13. `material.surface_render_method = 'BLENDED'` disables render passes and raytracing
    for that material in EEVEE.
    Why: forward rendering path.
    Violation: cryptomatte/AOVs come back empty for exactly the transparent objects you
    needed to isolate.

R14. Workbench renders with `scene.display.shading`, not with `scene.render` samples.
    Why: it is the viewport shading engine; `scene.display.render_aa` controls quality.
    Violation: setting `cycles.samples` has no effect and the agent concludes the render
    settings are ignored.

## 4. bpy patterns

### 4.1 Engine selection that survives 4.5 ↔ 5.2

**`render.engine` is a DYNAMIC enum — never gate on `enum_items`.** Measured on 5.2.0
(macOS, `--factory-startup -b`): `scene.render.bl_rna.properties['engine'].enum_items.keys()`
returns `['BLENDER_EEVEE']` only, because add-on-registered engines (Cycles included) are not
in the static RNA list. Assigning `'CYCLES'` works perfectly. The same is true of
`CyclesPreferences.compute_device_type` and `scene.cycles.denoiser`, whose `enum_items` are
measured **empty (`[]`)**. Gate by try-assign + read-back, never by membership.

```python
import bpy

def set_engine(scene, want):        # want in {'CYCLES','EEVEE','WORKBENCH'}
    table = {
        'CYCLES':    ['CYCLES'],
        'EEVEE':     ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'],   # 5.x first, then 4.2-4.5
        'WORKBENCH': ['BLENDER_WORKBENCH'],
    }
    prev = scene.render.engine
    for cand in table[want]:
        try:
            scene.render.engine = cand          # dynamic enum: invalid id -> TypeError
        except TypeError:
            continue
        if scene.render.engine == cand:         # read back; never trust the write
            return cand
    scene.render.engine = prev
    raise RuntimeError(f"{want} not available in Blender {bpy.app.version_string}")

print(set_engine(bpy.context.scene, 'CYCLES'))
```

Verified 5.2.0: returns `CYCLES` / `BLENDER_EEVEE` / `BLENDER_WORKBENCH`;
`'BLENDER_EEVEE_NEXT'` raises `TypeError` (4.2-4.5 name) and is skipped.

### 4.2 Cycles device selection (verified 5.2)

```python
def enable_cycles_gpu(prefer=('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI')):
    """Enable the first available Cycles GPU backend. Returns the backend id, or 'CPU'."""
    addons = bpy.context.preferences.addons
    cprefs = addons['cycles'].preferences if 'cycles' in addons else None
    if cprefs is None:
        return 'CPU'                                  # build without the Cycles add-on
    for backend in prefer:
        try:
            devs = cprefs.get_devices_for_type(backend)   # MUST be called to populate
        except (TypeError, RuntimeError):
            continue                                      # backend unknown to this build
        if not [d for d in devs if d.type == backend]:
            continue        # list also contains CPU entries -- filter by d.type
        try:
            cprefs.compute_device_type = backend          # dynamic enum -> TypeError if N/A
        except TypeError:
            continue
        if cprefs.compute_device_type != backend:
            continue                                      # read back; never trust the write
        for d in cprefs.devices:
            d.use = (d.type == backend)                   # GPU only, CPU off
        bpy.context.scene.cycles.device = 'GPU'
        return backend
    cprefs.compute_device_type = 'NONE'
    bpy.context.scene.cycles.device = 'CPU'
    return 'CPU'

print("cycles backend:", enable_cycles_gpu())
for d in bpy.context.preferences.addons['cycles'].preferences.devices:
    print(d.type, d.name, d.use)
```

Verified: `CyclesPreferences.bl_idname = __package__`, and the Cycles add-on package is
`cycles` (it lives in `scripts/addons_core/cycles`), so `addons['cycles']` is correct in
5.2. `compute_device_type` accepts `'NONE','CUDA','OPTIX','HIP','METAL','ONEAPI'` **by
assignment**, but its `enum_items` list is empty at runtime — same for `cycles.denoiser`.
`scene.cycles.device` enum: `'CPU','GPU'`.

Measured 2026-09-06, Blender 5.2.0 LTS, Apple M4 Pro, `--factory-startup -b`:
`get_devices_for_type('METAL')` -> `[('Apple M4 Pro (GPU - 16 cores)', 'METAL'),
('Apple M4 Pro', 'CPU')]`; OPTIX/CUDA/HIP/ONEAPI -> `[]`. The helper above returns
`'METAL'`, sets `compute_device_type='METAL'`, `scene.cycles.device='GPU'`, and enables
exactly the one METAL device. The pre-2026-09 version of this helper gated on
`enum_items` and therefore returned `'CPU'` with `compute_device_type='NONE'` on this
machine — silently, with no traceback and a 10-30x slowdown. That failure mode is the
reason for the try-assign + read-back rule above.

CLI equivalents:

```bash
blender -b scene.blend -E CYCLES -o //out_ -F PNG -f 1 -- --cycles-device OPTIX
blender -b scene.blend -E CYCLES -- --cycles-device CPU
blender -b scene.blend --gpu-backend vulkan -E BLENDER_EEVEE -o //e_ -f 1
```

### 4.3 Cycles sampling, denoising, light paths (verified defaults in parentheses)

```python
c = bpy.context.scene.cycles

# Sampling
c.samples = 128                      # (4096) max samples per pixel
c.preview_samples = 32               # (1024) viewport
c.use_adaptive_sampling = True       # (True)
c.adaptive_threshold = 0.01          # (0.01) noise level to stop at; 0 = auto
c.adaptive_min_samples = 0           # (0) 0 = auto
c.time_limit = 0.0                   # (0.0) seconds per frame; 0 = unlimited
c.seed = 0
c.use_animated_seed = False          # True -> noise pattern changes per frame
c.sampling_pattern = 'AUTOMATIC'     # blue-noise

# Denoising  -- OFF while verifying, ON for delivery
c.use_denoising = False              # (True)
c.denoiser = 'OPENIMAGEDENOISE'      # 'OPENIMAGEDENOISE' | 'OPTIX' (NVIDIA+OptiX only)
c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'   # (RGB_ALBEDO_NORMAL)
c.denoising_prefilter = 'ACCURATE'   # (ACCURATE) 'NONE'|'FAST'|'ACCURATE'
c.denoising_quality = 'HIGH'         # (HIGH) 'HIGH'|'BALANCED'|'FAST'
c.denoising_use_gpu = False          # (False) faster but needs extra VRAM

# Light paths
c.max_bounces = 12                   # (12) total
c.diffuse_bounces = 4                # (4)
c.glossy_bounces = 4                 # (4)
c.transmission_bounces = 12          # (12)  glass needs a lot
c.volume_bounces = 0                 # (0)
c.transparent_max_bounces = 8        # (8)   alpha-transparent surfaces
c.min_light_bounces = 0              # (0)   raise to reduce noise in dark areas
c.min_transparent_bounces = 0        # (0)

# Clamping / caustics
c.sample_clamp_direct = 0.0          # (0.0) OFF - do not raise, it dims your key light
c.sample_clamp_indirect = 10.0       # (10.0) firefly control
c.blur_glossy = 1.0                  # (1.0) "filter glossy" - fakes away caustic noise
c.caustics_reflective = True         # (True) set False to kill caustic fireflies
c.caustics_refractive = True         # (True)

# Light sampling
c.use_light_tree = True              # (True) essential with many lights
c.light_sampling_threshold = 0.01    # (0.01)

# Performance
c.tile_size = 2048                   # (2048) memory vs speed
bpy.context.scene.render.use_persistent_data = True   # animation of a static scene
bpy.context.scene.render.use_texture_cache = False    # 5.2: tx cache for huge texture sets
bpy.context.scene.render.use_auto_generate_texture_cache = False
```

Denoiser choice: `OPENIMAGEDENOISE` is CPU-or-GPU, always available in official builds,
and generally higher quality. `OPTIX` only appears in the enum when an OptiX-capable
NVIDIA device is configured — so `c.denoiser = 'OPTIX'` raises a `TypeError` on other
machines. Enumerate first:

```python
print(c.bl_rna.properties['denoiser'].enum_items.keys())
```

### 4.4 EEVEE settings (verified 5.2 RNA)

```python
e = bpy.context.scene.eevee

e.taa_render_samples = 64            # final-render samples
e.taa_samples = 16                   # viewport
e.use_shadows = True
e.shadow_ray_count = 2               # rays per shadow (softness quality)
e.shadow_step_count = 6              # steps per ray
e.shadow_pool_size = '512'           # 5.2 adds '1536' and '2048' MB options
e.shadow_resolution_scale = 1.0
e.use_shadow_jitter_viewport = False

e.use_raytracing = True              # OFF by default - no SSR/SSGI without it
rt = e.ray_tracing_options           # bpy.types.RaytraceEEVEE
rt.resolution_scale = '2'            # '1'|'2'|'4'|... (trace at 1/N res)
rt.screen_trace_quality = 0.25
rt.screen_trace_thickness = 0.2
rt.trace_max_roughness = 0.5
rt.use_denoise = True
rt.denoise_spatial = True; rt.denoise_temporal = True; rt.denoise_bilateral = True
rt.use_backface_hit = False          # 5.2: new Backface option, reduces light leaking
rt.backface_radiance_scale = 1.0

e.use_fast_gi = False                # AO-like GI approximation
e.fast_gi_method = 'GLOBAL_ILLUMINATION'
e.fast_gi_distance = 0.0
e.fast_gi_ray_count = 2; e.fast_gi_step_count = 8

e.volumetric_start = 0.1; e.volumetric_end = 100.0
e.volumetric_tile_size = '8'; e.volumetric_samples = 64
e.volumetric_sample_distribution = 0.8
e.use_volumetric_shadows = True; e.volumetric_shadow_samples = 16
e.volumetric_ray_depth = 1

e.clamp_surface_indirect = 10.0      # firefly control, mirrors Cycles
e.direct_light_intensity = 1.0       # 5.1+: global contribution tweak
e.indirect_light_intensity = 1.0     # 5.1+
e.use_overscan = True; e.overscan_size = 3.0   # fixes screen-space effects at borders
e.light_threshold = 0.01

# Ambient occlusion distance moved to the VIEW LAYER in 5.0:
bpy.context.view_layer.eevee.ambient_occlusion_distance = 0.2
# (scene.eevee.gtao_distance, gtao_quality, use_gtao were removed in 5.0)
```

Light probes are objects, not scene settings:

```python
lp_data = bpy.data.lightprobes.new("Vol", type='VOLUME')   # 'SPHERE'|'PLANE'|'VOLUME'
lp = bpy.data.objects.new("Vol", lp_data)
bpy.context.scene.collection.objects.link(lp)
with bpy.context.temp_override(scene=bpy.context.scene,
                               view_layer=bpy.context.view_layer):
    bpy.ops.object.lightprobe_cache_bake(subset='ALL')     # 'ALL'|'SELECTED'|'ACTIVE'
```

EEVEE limitations that change the image (not just quality): screen-space effects vanish
at frame borders (use overscan); only single-scatter volumetrics; volumetrics do not
appear in reflections; only one refraction event is modelled; ≤128 sphere probes,
≤16 plane probes in frustum; render output is half-precision (16-bit float); Combined
and Light passes clamp negatives to zero; no multi-GPU.

### 4.5 Workbench

```python
set_engine(bpy.context.scene, 'WORKBENCH')
sh = bpy.context.scene.display.shading
sh.light = 'STUDIO'                  # 'FLAT'|'STUDIO'|'MATCAP'
sh.color_type = 'MATERIAL'           # 'MATERIAL'|'OBJECT'|'RANDOM'|'SINGLE'|'TEXTURE'|'VERTEX'
sh.studio_light = 'Default'
sh.show_shadows = True
sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.show_specular_highlight = True
sh.single_color = (0.8, 0.8, 0.8)
sh.background_type = 'THEME'         # 'THEME'|'WORLD'|'VIEWPORT'
bpy.context.scene.display.render_aa = '32'   # antialias samples for FINAL render
bpy.context.scene.display.viewport_aa = '8'
```

Workbench ignores lights, materials' shading, GI and `cycles.samples` entirely.

### 4.6 Resolution, format, output (5.x `media_type` first!)

```python
r = bpy.context.scene.render
r.resolution_x = 1920
r.resolution_y = 1080
r.resolution_percentage = 100
r.pixel_aspect_x = r.pixel_aspect_y = 1.0
r.fps = 24; r.fps_base = 1.0
r.film_transparent = False
r.use_overwrite = True
r.use_placeholder = False
r.use_file_extension = True
r.filepath = "//renders/shot_"        # animation -> shot_0001.png, shot_0002.png ...

imf = r.image_settings
imf.media_type = 'IMAGE'              # 5.0+: SET THIS FIRST
imf.file_format = 'PNG'               # 'PNG','OPEN_EXR','JPEG','WEBP','AVIF','TIFF','HDR',...
imf.color_mode = 'RGBA'               # 'BW'|'RGB'|'RGBA'
imf.color_depth = '16'                # PNG: '8'|'16'   EXR: '16'|'32'
imf.compression = 15                  # PNG %

# Multilayer EXR (passes):
imf.media_type = 'MULTI_LAYER_IMAGE'
imf.file_format = 'OPEN_EXR_MULTILAYER'
imf.color_depth = '32'
imf.exr_codec = 'ZIP'                 # 'NONE','PXR24','ZIP','PIZ','RLE','ZIPS','B44','B44A','DWAA','DWAB'

# Video:
imf.media_type = 'VIDEO'
imf.file_format = 'FFMPEG'
ff = r.ffmpeg
ff.format = 'MPEG4'                   # container
ff.codec = 'H264'
ff.constant_rate_factor = 'HIGH'      # or 'PERC_LOSSLESS','LOSSLESS','MEDIUM','LOW',...
ff.ffmpeg_preset = 'GOOD'
ff.gopsize = 12
ff.audio_codec = 'AAC'
ff.audio_bitrate = 192
```

Verified `media_type` enum: `'IMAGE'`, `'MULTI_LAYER_IMAGE'`, `'VIDEO'`.
Verified ffmpeg property names: `format, codec, video_bitrate, minrate, maxrate,
muxrate, gopsize, max_b_frames, use_max_b_frames, buffersize, packetsize,
constant_rate_factor, ffmpeg_preset, ffmpeg_prores_profile, use_autosplit,
use_lossless_output, audio_codec, audio_bitrate, audio_volume, audio_mixrate,
audio_channels`.

### 4.7 Rendering headlessly

```bash
# Still, frame 1, PNG
blender -b scene.blend -E CYCLES -o //out/frame_ -F PNG -f 1

# Animation range, with format forced from the CLI
blender -b scene.blend -o //out/anim_ -F PNG -x 1 -s 1 -e 120 -a

# Run a script instead of the built-in render pipeline
blender -b scene.blend --python render.py -- --out /renders --samples 128
```

```python
# render.py
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp"
os.makedirs(out, exist_ok=True)

sc = bpy.context.scene
sc.render.filepath = os.path.join(out, "frame_")
sc.render.image_settings.media_type = 'IMAGE'
sc.render.image_settings.file_format = 'PNG'

# Still:
bpy.ops.render.render(write_still=True)

# Animation (5.0+ accepts an explicit range on the operator):
sc.frame_start, sc.frame_end, sc.frame_step = 1, 120, 1
bpy.ops.render.render(animation=True, frame_start=1, frame_end=120)

print("frames on disk:", sorted(os.listdir(out))[:5])
```

Verified `bpy.ops.render.render` arguments in 5.2: `animation`, `write_still`,
`use_viewport`, `use_sequencer_scene`, `layer`, `scene`, `frame_start`, `frame_end`
(the last two added in 5.0).

Viewport ("OpenGL") render — needs a GPU context, same constraints as EEVEE:

```python
bpy.ops.render.opengl(animation=False, write_still=True, view_context=False,
                      render_keyed_only=False, sequencer=False)
```

Useful headless flags:

```bash
--factory-startup            # ignore user prefs/add-ons; reproducible
--enable-autoexec            # allow drivers/scripts in the .blend
-noaudio
--log-level 0 --quiet
--disable-depsgraph-on-file-load   # 5.x: skip depsgraph build on load; you must then
                                   # call context.evaluated_depsgraph_get() yourself
```

5.2 added `gpu.init()` so scripts can initialise the GPU backend explicitly in
`--background` mode — required before using the `gpu` module headlessly, and a useful
probe for whether a GPU context is obtainable at all:

```python
import gpu
try:
    gpu.init()                                    # 5.2+
    print("GPU backend OK:", gpu.platform.backend_type_get())
    eevee_ok = True
except Exception as ex:
    print("no GPU context, EEVEE unavailable:", ex)
    eevee_ok = False
```

### 4.8 Headless viability matrix

| Platform | Cycles CPU | Cycles GPU | EEVEE | Workbench |
|---|---|---|---|---|
| Linux, GPU + driver (EGL/Vulkan) | yes | yes | yes | yes |
| Linux container, no GPU | yes | no | **no** | **no** |
| macOS (Metal) | yes | yes | yes | yes |
| Windows, headless / no session | yes | yes | **no** (documented) | **no** |
| Windows, interactive session | yes | yes | yes | yes |

The Blender manual's EEVEE Limitations page states: "Headless rendering is not supported
on headless Windows systems", "There is no plan to support CPU (software) rendering",
and "There is currently no support for multiple GPU systems." Treat Cycles CPU as the
only unconditionally *portable* engine for an automated agent pipeline, and probe with
`gpu.init()` before committing to EEVEE on an unknown machine.

> **Measured, this machine (2026-09-06).** EEVEE in `--factory-startup -b` **works on
> macOS 5.2.0 / Apple Silicon** — it is not a documented-only "maybe". A 256x256,
> 8-sample EEVEE still (`scene.render.engine` reads back `BLENDER_EEVEE`) renders in
> **0.18-0.20 s**, whole fresh process **0.67-0.81 s wall**, writing a valid 39 KB PNG.
> So the cheap EEVEE preview rung of the verify ladder is available here.
> This is a measurement of *this* Apple M4 Pro / macOS install only — R2 still stands:
> verify on any other machine before assuming it, and keep a Cycles-CPU fallback for
> headless Windows and GPU-less containers.
> Reproduce: `blender --factory-startup -b --python-exit-code 3 --python eevee_bench.py`
> (set engine, `eevee.taa_render_samples = 8`, 256 px, `bpy.ops.render.render(write_still=True)`).

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `TypeError: ... enum "BLENDER_EEVEE_NEXT" not found in ('BLENDER_EEVEE','BLENDER_WORKBENCH','CYCLES')` | engine id changed in 5.0 | resolve against `enum_items.keys()` (`set_engine`) |
| `KeyError: bpy_prop_collection[key]: key "cycles" not found` | build without Cycles, or add-on disabled | defensive scan for `compute_device_type` |
| Render takes 30× longer than expected on a GPU box | `compute_device_type` set but `get_devices_for_type()` never called / `d.use` False | call it, then set `d.use = True`, then `cycles.device='GPU'` |
| `TypeError: ... enum "OPTIX" not found` when setting `denoiser` | no OptiX device configured | enumerate `denoiser` enum items first; fall back to `OPENIMAGEDENOISE` |
| `TypeError: ... enum "OPEN_EXR_MULTILAYER" not found` | `media_type` not set to `'MULTI_LAYER_IMAGE'` first | set `media_type`, then `file_format` |
| `TypeError: ... enum "FFMPEG" not found` | `media_type` not `'VIDEO'` | same |
| Render command exits 0, output directory empty | `bpy.ops.render.render()` without `write_still=True` / `animation=True` | pass one of them |
| Files named `movie.png0001.png` | `filepath` given a full filename for an animation | give directory + prefix only |
| EEVEE in `--background` aborts with a GPU/display error, or writes a black frame | no GPU context (headless Windows / GPU-less container) | probe `gpu.init()`; fall back to Cycles CPU |
| EEVEE render has no reflections or GI | `scene.eevee.use_raytracing` is False by default | `e.use_raytracing = True` |
| EEVEE effects break at the image border | screen-space tracing has no data offscreen | `e.use_overscan = True; e.overscan_size = 3.0` |
| Cryptomatte/AOV empty for glass objects in EEVEE | those materials use `surface_render_method='BLENDED'` | switch to `'DITHERED'` |
| `AttributeError: 'SceneEEVEE' object has no attribute 'gtao_distance'` | removed in 5.0 | `view_layer.eevee.ambient_occlusion_distance` |
| Clean render, but downstream comp shows blown values / NaNs | denoiser smoothed over the evidence | re-render with `use_denoising = False` |
| Fireflies remain after clamping | clamped `direct` instead of `indirect`, or caustics | `sample_clamp_indirect ≈ 10`, `caustics_reflective/refractive = False`, `blur_glossy` up |
| Animation frames render with stale geometry | `use_persistent_data=True` while mutating the scene from Python per frame | disable it, or force `depsgraph.update()` |
| Out-of-memory during a long animation | `use_persistent_data=True` on a heavy scene | disable, or lower `tile_size` |
| Workbench render unaffected by any quality setting changed | Workbench uses `scene.display.*` | `scene.display.render_aa`, `scene.display.shading.*` |
| Render engine reports "does not support baking" | EEVEE/Workbench active | `scene.render.engine = 'CYCLES'` |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Engine | `BLENDER_EEVEE` | `CYCLES` | `BLENDER_EEVEE` | `CYCLES` | `BLENDER_WORKBENCH` |
| Resolution | 1280×720 | 1920×1080 | 1920×1080 | 2560×1440+ | 1024×1024 |
| `cycles.samples` | — | 256–512 | — | 1024–4096 | — |
| `adaptive_threshold` | — | 0.01 | — | 0.005 | — |
| `use_denoising` | — | True (delivery) / False (verify) | — | True | — |
| `denoiser` | — | `OPENIMAGEDENOISE` | — | `OPENIMAGEDENOISE` | — |
| `denoising_quality` | — | `BALANCED` | — | `HIGH` | — |
| `max_bounces` | — | 8 | — | 16 | — |
| `transmission_bounces` | — | 8 | — | 24 (glass) | — |
| `sample_clamp_indirect` | — | 10 | — | 4 | — |
| `caustics_*` | — | False (speed) | — | True | — |
| `eevee.taa_render_samples` | 32 | — | 64–128 | — | — |
| `eevee.use_raytracing` | True | — | True | — | — |
| `eevee.shadow_ray_count` | 1 | — | 2 | — | — |
| `eevee.use_overscan` | True | — | True | — | — |
| `display.render_aa` (Workbench) | — | — | — | — | `32` |
| `use_persistent_data` | n/a | True | True | False | n/a |
| Output format | PNG 8-bit | `OPEN_EXR_MULTILAYER` 16/32-bit | PNG RGBA 16-bit | `OPEN_EXR` 32-bit | PNG 8-bit |
| `film_transparent` | True | False | True | True | False |
| `color_depth` | `8` | `16` | `16` | `32` | `8` |
| Frames → video | direct PNG | frames then encode | frames then encode | still | still |

## 7. Verification checklist

- [ ] `assert bpy.context.scene.render.engine in bpy.context.scene.render.bl_rna.properties['engine'].enum_items.keys()` — engine id valid on this build.
- [ ] `p = bpy.context.preferences.addons['cycles'].preferences; assert any(d.use and d.type != 'CPU' for d in p.devices) == (bpy.context.scene.cycles.device == 'GPU')` — GPU intent matches GPU reality.
- [ ] `assert bpy.context.scene.cycles.use_denoising is False` during a verification render.
- [ ] `assert bpy.context.scene.render.image_settings.media_type == 'MULTI_LAYER_IMAGE'` before setting `OPEN_EXR_MULTILAYER`.
- [ ] `import os; assert os.path.isdir(os.path.dirname(bpy.path.abspath(scene.render.filepath)))` — output directory exists before rendering.
- [ ] `bpy.ops.render.render(write_still=True); assert os.path.getsize(expected_path) > 1024` — a real file landed on disk.
- [ ] `import gpu; gpu.init()` (5.2+) succeeds before choosing EEVEE headlessly.
- [ ] `assert scene.frame_end >= scene.frame_start` — non-empty animation range.
- [ ] `assert len(os.listdir(out)) == scene.frame_end - scene.frame_start + 1` after an animation render — no dropped frames.
- [ ] Load the rendered EXR back and `assert not np.isnan(px).any() and px.max() < 1e6` — no NaN/inf materials or absurd light values that a denoiser would have hidden.
- [ ] Render one frame at `samples=8`, denoise off: visible noise proves the path tracer is actually running (a suspiciously clean image at 8 samples means something is emitting flat colour, not lit geometry).

## 8. Sources

- [Blender 5.0 Release Notes: Python API — EEVEE engine id `BLENDER_EEVEE`, pass renames, `gtao_distance` move, `ImageFormatSettings.media_type`](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.0 Release Notes: EEVEE & Viewport](https://developer.blender.org/docs/release_notes/5.0/eevee/)
- [Blender 5.1 Release Notes: EEVEE & Viewport — light path intensity, Raycast node](https://developer.blender.org/docs/release_notes/5.1/eevee/)
- [Blender 5.2 Release Notes: EEVEE & Viewport — raytracing overhaul, Backface option, shadow pool sizes](https://developer.blender.org/docs/release_notes/5.2/eevee/)
- [Blender 5.2 Release Notes: Cycles — Texture Cache, Simplify texture resolution](https://developer.blender.org/docs/release_notes/5.2/cycles/)
- [Blender 5.2 Release Notes: Python API — `gpu.init()` for background mode](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- [EEVEE Limitations (CPU rendering, multi-GPU, headless Windows) — Blender Manual](https://docs.blender.org/manual/en/latest/render/eevee/limitations/limitations.html)
- [Command Line Arguments (`-E`, `--gpu-backend`, `--cycles-device`, `--disable-depsgraph-on-file-load`) — Blender Manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- Cycles property names and defaults verified against `intern/cycles/blender/addon/properties.py`
  and `ui.py`; EEVEE properties against `source/blender/makesrna/intern/rna_scene.cc`;
  render operator arguments against `source/blender/editors/render/render_internal.cc`,
  all at tag `v5.2.0`.
- `[UNVERIFIED]`: the exact EEVEE failure mode on a GPU-less Linux container (error text
  vs. black frame) is not documented; probe with `gpu.init()` rather than relying on a
  specific traceback.

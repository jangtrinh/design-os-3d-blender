# EEVEE Next Realtime Render Pipeline: Architecture & Shading Mechanics

Blender 4.2 introduced a complete re-architecture of the realtime viewport engine: **EEVEE Next**. Built on a unified forward+/deferred rasterization pipeline, it replaces legacy screen-space hacks with **Virtual Shadow Maps (VSM)**, **Raytraced Screen-Space Reflections (Hi-Z)**, and **Fast Irradiance Cache Volumes**.

---

## 1. The EEVEE Next Core Architecture

```
   [ Geometry Stage ] ──► [ Depth Prepass ] ──► [ Hi-Z Pyramid Generation ]
                                                       │
   [ Clustered Light Assignment ] ◄────────────────────┘
          │
          ▼
   [ G-Buffer Evaluation ] ──► [ Horizon Indirect Lighting ] ──► [ Virtual Shadow Maps ]
                                          │
                                          ▼
   [ Final Forward+ Composite ] ──► [ Temporal Super-Sampling (TAA) ] ──► Viewport Display
```

### 1.1 Forward+ Tile/Cluster Light Culling
Traditional forward rendering evaluates every scene light against every drawn polygon ($O(P \times L)$).
*   **EEVEE Next Cluster Grid:** The view frustum is subdivided into a 3D grid of depth-sliced frustum tiles ("froxels"):
    *   $X \times Y$: $16 \times 16\text{ pixel}$ screen-space tiles.
    *   $Z$: Exponential logarithmic depth slices.
*   *Compute Shader Pass:* A compute shader culls all point, spot, and area light bounding spheres against each froxel.
*   *Shading Pass:* When a pixel is shaded, it only evaluates the short linked list of lights active inside its local 3D cluster, keeping framerates at $60\text{–}120\text{ FPS}$ even with dozens of dynamic lights.

---

## 2. Virtual Shadow Maps (VSM)

Legacy EEVEE used fixed-resolution shadow map textures ($512\text{ to }4096\text{ px}$), which caused severe aliasing or ran out of VRAM when zooming close to objects.

```
       Traditional Shadow Map                     Virtual Shadow Map (VSM)
    ┌───────────────────────────┐              ┌───────────────────────────┐
    │ Low-res pixels stretched  │              │ Sparse Virtual Page Table │
    │ over entire scene;        │              │ High-res 16k page allocated│
    │ Pixelated jagged shadows! │              │ ONLY where camera looks!  │
    └───────────────────────────┘              └───────────────────────────┘
```

### 2.1 Paged Virtual Memory Texture Architecture
1.  **Virtual Address Space:** Shadows are mapped to a massive theoretical $16,384 \times 16,384\text{ pixel}$ texture canvas per light.
2.  **Physical Sparse Allocation:** Physical VRAM memory is allocated only for **$128 \times 128\text{ pixel}$ pages** that are currently visible to the camera frustum.
3.  **Clipmaps:** Directional sun lights use concentric geometric clipmap tiers centered on the camera position, providing razor-sharp contact shadows near the character while smoothly transitioning to lower resolutions in the distant horizon.

---

## 3. Screen-Space Reflections (SSR) & Hierarchical-Z Tracing

EEVEE Next resolves specular reflections using **Hierarchical Z-Buffer (Hi-Z) Ray Marching**:

```
                  Ray Marching Down the Mipmapped Depth Pyramid
                  
        Mip 0 (1920x1080)   Mip 1 (960x540)     Mip 2 (480x270)
        ┌──┬──┬──┬──┐       ┌─────┬─────┐       ┌───────────┐
        │  │  │  │  │  ──►  │     │     │  ──►  │           │
        └──┴──┴──┴──┘       └─────┴─────┘       └───────────┘
        Skip empty space!   Coarse step...      Final intersection!
```

### 3.1 Hi-Z Ray Traversal Algorithm
*   Instead of advancing ray steps by a constant pixel increment $\Delta s$, the ray marches through an image pyramid of downsampled depth buffers.
*   If a large coarse cell at Mip 2 contains no geometry behind the ray, the ray leaps across the entire block in a single step ($O(\log N)$ traversal).
*   When a depth intersection is flagged, traversal drops down to Mip 0 to determine the exact sub-pixel reflection contact.
*   *Fallback Probe:* When a reflection ray exits the screen boundary, EEVEE Next smoothly blends into surrounding **Cubemap Light Probes** or HDRI environment maps to prevent harsh cutoff seams.

---

## 4. Light Probes: Volume Irradiance vs. Screen Tracing

To capture diffuse indirect bounced light (global illumination) in realtime:
*   **Irradiance Grid (Light Probe Volume):**
    A 3D grid of Spherical Harmonic (SH) probes baked across the scene.
    *   Each probe stores $L_{00}, L_{1-1}, L_{10}, L_{11}, L_{2-2}, L_{2-1}, L_{20}, L_{21}, L_{22}$ second-order spherical harmonic coefficients.
    *   Dynamic characters moving through the grid sample trilinearly between the nearest 8 probes, receiving realistic bounce lighting.
*   **Raytraced Horizon-Based Ambient Occlusion (HBAO):**
    Measures the continuous angular horizon of occluding geometry within a screen-space radius, darkening tight crevices and under-chassis contact points.

---

## 5. Headless Automation & Platform Compatibility Warning

> [!WARNING]
> **Headless (CLI) Limitation on macOS:** EEVEE and EEVEE Next rely directly on active GPU OpenGL/Metal window contexts (`NSOpenGLContext` / Metal drawable). Running Blender headless (`blender -b file.blend -f 1`) with `render.engine = 'BLENDER_EEVEE_NEXT'` on macOS without a physical display server will fail or fall back to an unaccelerated software pipeline.
> 
> *Best Practice:* **All automated batch rendering, verification sheets, and CI render checks must specify Cycles with Metal acceleration (`scene.render.engine = 'CYCLES'`). EEVEE Next is strictly reserved for live interactive viewport work.**

---

## 6. References & Standards

1.  **Karis, B. (2013).** *Real Shading in Unreal Engine 4.* ACM SIGGRAPH 2013 Courses: Physically Based Shading in Theory and Practice. (Clustered shading, split-sum approximation, and rough specular integration).
2.  **Bavoil, L., Sainz, M., & Dimitrov, R. (2008).** *Image-space horizon-based ambient occlusion (HBAO).* ACM SIGGRAPH 2008 Talks. (Mathematical derivation of horizon elevation angles for screen-space contact shadowing).
3.  **Mittring, M. (2012).** *The Technology Behind the Unreal Engine 4 Elemental Demo.* ACM SIGGRAPH 2012 Courses. (Hierarchical Z-buffer screen-space reflection ray-tracing).
4.  **Blender Foundation. (2024).** *EEVEE-Next Architecture Specification & Technical Roadmap.* https://developer.blender.org/docs/features/eevee/

# AI Denoising Architectures: OIDN, OptiX & Temporal Animation Stability

Unbiased Monte Carlo path tracing requires tens of thousands of samples per pixel to eliminate high-frequency noise completely. **Deep Learning Denoising** uses Convolutional Neural Networks (U-Nets) to reconstruct clean, noise-free images from raw renders with as few as $32\text{–}128\text{ samples}$.

---

## 1. Denoising Architectures: Intel OIDN vs. NVIDIA OptiX

Blender 5.2 integrates two deep learning denoiser backends:

```
            Raw Noisy Beauty (32 spp)
            Denoising Albedo Pass ───────► [ Deep U-Net Autoencoder ] ──► Clean Final Image
            Denoising Normal Pass
```

### 1.1 Comparative Engine Architecture

| Metric | Intel Open Image Denoise (OIDN 2.x) | NVIDIA OptiX AI Denoiser |
| :--- | :--- | :--- |
| **Hardware Backend** | Universal (CPU AVX-512, Apple Silicon Metal, Intel ARC, AMD ROCm, NVIDIA CUDA). | Dedicated NVIDIA Tensor Cores only. |
| **Model Topology** | Deep Modified U-Net with attention modules. | Shallow Recurrent Convolutional Network. |
| **Reconstruction Quality** | **Highest.** Preserves micro-texture detail and soft geometric edges. | High, but occasionally smudges low-contrast procedural noise textures. |
| **Processing Latency** | Moderate ($0.5\text{–}2.0\text{ seconds}$ per 4K frame). | **Ultra-Fast ($< 0.05\text{ seconds}$)**. Ideal for interactive viewport preview. |
| **Auxiliary Passes** | Supports Color + Albedo + Normal. | Supports Color + Albedo + Normal + Motion Vectors. |

---

## 2. Auxiliary Feature Passes: Albedo & Normal Guidance

A neural network cannot distinguish between high-frequency Monte Carlo noise and real geometric detail (e.g., woven fabric threads or wood grain) using color alone.

```
       Noisy Beauty Pass               Albedo Guide Pass              Normal Guide Pass
     ┌───────────────────┐           ┌───────────────────┐          ┌───────────────────┐
     │ Granular pixel    │           │ Flat albedo colors│          │ Razor-sharp camera│
     │ noise everywhere! │           │ with ZERO noise!  │          │ geometric normals!│
     └───────────────────┘           └───────────────────┘          └───────────────────┘
                                               │                              │
                                               ▼                              ▼
                                     Network uses these noiseless guide maps to anchor
                                     sharp geometric edges while smoothing lighting noise!
```

### 2.1 The Mathematics of Auxiliary Guides
1.  **Denoising Albedo ($\mathbf{A}$):** The direct diffuse and specular color reflectances of materials before illumination integration. It contains **zero stochastic noise**.
2.  **Denoising Normal ($\mathbf{N}$):** The interpolated vertex/bump normals converted to camera space ($[-1, 1] \to [0, 1]$).
3.  **Loss Function Formulation:** The U-Net is trained on supervised loss:
    $$\mathcal{L} = \alpha \|\hat{I} - I_{ground}\|_1 + \beta \|\nabla \hat{I} - \nabla I_{ground}\|_1 + \text{SSIM}(\hat{I}, I_{ground})$$
    The gradient term $\nabla \hat{I}$ penalizes edge blurring, forcing the denoiser to preserve silhouettes guided by $\mathbf{N}$.

---

## 3. The Temporal Instability Problem: "Boiling" Noise in Animations

When denoising single frames independently, Monte Carlo sampling noise varies randomly between frame $t$ and frame $t+1$.
*   **The "Boiling / Crawling" Phenomenon:** The AI network smooths noise into slightly different local patches on each frame. In video playback, these varying patches appear as a sickening, crawling, liquid boil across solid walls.

```
          Frame t (Denoised)                      Frame t+1 (Denoised)
     ┌───────────────────────────┐           ┌───────────────────────────┐
     │ Patch A smoothed slightly │           │ Patch A smoothed slightly │
     │ to the left...            │  ════►    │ to the right...           │
     └───────────────────────────┘           └───────────────────────────┘
     ★ PLAYBACK RESULT: High-frequency "boiling" crawling texture flicker!
```

### 3.1 Solution: Motion-Vector Reprojection & Temporal Clamping
To achieve rock-solid temporal stability across animations:
1.  **Render Optical Flow Motion Vectors:** Output the screen-space velocity vector $\mathbf{v}(x, y) = (\Delta u, \Delta v)$ of every surface pixel.
2.  **Reprojection:** Warp frame $t-1$ forward to frame $t$ along the motion vectors:
    $$\tilde{I}_{t-1}(\mathbf{x}) = I_{t-1}(\mathbf{x} - \mathbf{v}(\mathbf{x}))$$
3.  **Temporal Blending:**
    $$\hat{I}_t = \gamma I_{t, denoised} + (1 - \gamma) \tilde{I}_{t-1}$$
    Where blending factor $\gamma \approx 0.1\text{–}0.2$ eliminates crawling noise while rejecting ghosting across disocclusion boundaries.
4.  *Production Minimum:* Never denoise animation below **$128\text{–}256\text{ samples}$**. AI denoisers can interpolate smooth lighting, but require sufficient baseline path data to prevent structural temporal hallucinations.

---

## 4. Programmatic Compositor Denoising in Blender 5.2

In professional workflows, **never use Viewport Denoising for final disk output**. Always output multi-pass EXRs and apply OIDN via the Compositor Node Tree:

```python
import bpy

def setup_compositor_oidn():
    """Builds a deterministic OIDN compositor tree with Albedo & Normal passes."""
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    
    # Enable Denoising Data passes in Render Layer
    view_layer = scene.view_layers["ViewLayer"]
    view_layer.cycles.use_denoising = True # Emits Denoising Normal and Albedo
    
    # 1. Render Layers node
    rl_node = tree.nodes.new(type='CompositorNodeRLayers')
    
    # 2. Denoise Node (Intel OIDN)
    denoise_node = tree.nodes.new(type='CompositorNodeDenoise')
    denoise_node.prefilter = 'ACCURATE'
    denoise_node.use_hdr = True
    
    # 3. Composite Output
    out_node = tree.nodes.new(type='CompositorNodeComposite')
    
    # Wire passes
    tree.links.new(rl_node.outputs['Noisy Image'], denoise_node.inputs['Image'])
    tree.links.new(rl_node.outputs['Denoising Normal'], denoise_node.inputs['Normal'])
    tree.links.new(rl_node.outputs['Denoising Albedo'], denoise_node.inputs['Albedo'])
    tree.links.new(denoise_node.outputs['Image'], out_node.inputs['Image'])
```

---

## 5. References & Standards

1.  **Chaitanya, C. R. A., et al. (2017).** *Interactive reconstruction of Monte Carlo image sequences using a recurrent denoising autoencoder.* ACM Transactions on Graphics (SIGGRAPH 2017), 36(4), Article 98. [DOI: 10.1145/3072959.3073601] (The seminal paper establishing deep recurrent temporal denoising for CGI).
2.  **Áfra, A. T., et al. (2021).** *Intel Open Image Denoise: High-Performance Denoising Library for Ray Tracing.* IEEE Transactions on Visualization and Computer Graphics.
3.  **Bako, S., et al. (2017).** *Kernel-predicting convolutional networks for denoising Monte Carlo renderings.* ACM Transactions on Graphics (SIGGRAPH 2017), 36(4), Article 97.
4.  **OpenImageDenoise Documentation.** (2024). *OIDN v2.2 Specification and Normal/Albedo Guide Guidelines.* Intel Corporation.

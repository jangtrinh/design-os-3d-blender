# Volumetric Scattering, Radiative Transfer & Atmospheric Simulation

Volumetric rendering simulates participating media (haze, fog, dust, engine exhaust, clouds, fire) where light does not simply reflect off surfaces, but scatters and absorbs continuously through a 3D medium.

---

## 1. The Radiative Transfer Equation (RTE)

The change in radiance $L(\mathbf{x}, \omega)$ along ray path $s$ through a participating medium is governed by the **Subramanyan Chandrasekhar Radiative Transfer Equation**:

$$\frac{dL(s, \omega)}{ds} = -\underbrace{\sigma_a(s) L(s, \omega)}_{\text{Absorption}} - \underbrace{\sigma_s(s) L(s, \omega)}_{\text{Out-Scattering}} + \underbrace{\sigma_a(s) L_e(s, \omega)}_{\text{Emission}} + \underbrace{\sigma_s(s) \int_{4\pi} p(\omega', \omega) L(s, \omega') \, d\omega'}_{\text{In-Scattering}}$$

```
                       In-Scattering from other directions (ω')
                                      \   |   /
                                       \  |  /
   Ray Path s ────────► [ Volumetric Element ] ────────► Transmitted Light
                             │           ▲
                             ▼           │
                         Absorption    Emission (Fire/Plasma)
                         & Out-Scatter
```

### 1.1 Extinction Coefficient ($\sigma_t$) & Optical Thickness ($\tau$)
*   **Total Extinction:**
    $$\sigma_t = \sigma_a + \sigma_s$$
*   **Beer-Lambert Transmittance ($T_r$):** The fraction of radiance that passes through distance $d$ without interacting:
    $$T_r(d) = \exp\left( -\int_0^d \sigma_t(s) \, ds \right) = \exp(-\sigma_t \cdot d) \quad (\text{for homogeneous medium})$$
*   **Scattering Albedo ($\alpha$):**
    $$\alpha = \frac{\sigma_s}{\sigma_t} = \frac{\sigma_s}{\sigma_a + \sigma_s}$$
    *   $\alpha = 0.0$: Pure black smoke / soot (100% absorption, zero bounce light).
    *   $\alpha = 0.99$: Clean white water fog / clouds (near 100% multiple scattering, brilliant internal illumination).

---

## 2. The Henyey-Greenstein Phase Function

The angular redistribution of scattered light is dictated by the **Henyey-Greenstein Phase Function $p(\theta)$**:

$$p(\theta) = \frac{1}{4\pi} \frac{1 - g^2}{(1 + g^2 - 2 g \cos\theta)^{3/2}}$$

Where $\theta$ is the scattering angle ($\cos\theta = \omega \cdot \omega'$) and $g \in (-1, 1)$ is the **Asymmetry Factor**:

```
        Isotropic (g = 0)            Forward Scattering (g = +0.7)        Back-Scattering (g = -0.5)
              ╭───╮                               ╭───────►                        ◄───────╮
             (  •  )                             (  • ───►                        ◄─── •  )
              ╰───╯                               ╰───────►                        ◄───────╯
       Uniform in all directions           God rays, headlight halos         Retro-reflective dust
```

*   **$g > 0$ (Forward Scattering):** Droplets/particles are large relative to light wavelength (Mie scattering, water droplets, fog). Produces intense forward **"God Rays"** and solar halos when looking directly toward the light source.
*   **$g = 0$ (Isotropic):** Microscopic gas molecules; equal scattering in all directions.
*   **$g < 0$ (Back-Scattering):** Porous astronomical regolith or crystalline dust reflecting light straight back toward the emitter.

---

## 3. Woodcock Tracking (Delta Tracking) vs. Equidistant Ray Marching

To sample collision free-paths in heterogeneous media (e.g. OpenVDB smoke grids):

```
       Equidistant Ray Marching                     Woodcock Delta Tracking
     (Evaluates every step uniformly)           (Probabilistic rejection sampling)
     ┌───┬───┬───┬───┬───┬───┬───┐              ├─── ─── ─── ───•─── ─── ─── ───•
       Wasteful in empty space!                  Long leaps in thin air, exact collisions!
```

1.  **Standard Ray Marching:** Advances ray by fixed step size $\Delta x$.
    *   *Trade-off:* If $\Delta x$ is too large $\implies$ **Banding artifacts** across density gradients.
    *   If $\Delta x$ is too small $\implies$ Render times explode.
2.  **Woodcock Null-Collision Tracking (Cycles Integrator):**
    *   Finds maximum majorant density $\bar{\sigma}_{max}$ in the volume bounding box.
    *   Generates random step distance: $t = -\frac{\ln(\xi)}{\bar{\sigma}_{max}}$.
    *   Accepts the interaction point with probability $P_{accept} = \sigma_t(\mathbf{x}) / \bar{\sigma}_{max}$.
    *   *Advantage:* Mathematically unbiased with zero banding artifacts.

---

## 4. Production Volume Configuration in Blender 5.2

```python
import bpy

def setup_atmospheric_haze(density=0.02, anisotropy=0.65):
    """Creates a physically-plausible atmospheric volume scattering box."""
    # Create domain cube
    bpy.ops.mesh.primitive_cube_add(size=100.0, location=(0, 0, 0))
    domain = bpy.context.active_object
    domain.name = "Atmospheric_Volume"
    
    mat = bpy.data.materials.new(name="Atmosphere_Shader")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    
    # Material Output node
    out_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
    
    # Principled Volume node (Socket names 5.x)
    vol_node = tree.nodes.new(type='ShaderNodeVolumePrincipled')
    vol_node.inputs['Density'].default_value = density
    vol_node.inputs['Anisotropy'].default_value = anisotropy # Forward scatter
    vol_node.inputs['Color'].default_value = (0.95, 0.97, 1.0, 1.0) # Slight sky blue tint
    
    # Wire volume to Volume output
    tree.links.new(vol_node.outputs['Volume'], out_node.inputs['Volume'])
    
    domain.data.materials.append(mat)
    
    # Set Cycles volume step size
    scene = bpy.context.scene
    scene.cycles.volume_step_rate = 1.0
    scene.cycles.volume_max_steps = 1024
    scene.cycles.volume_bounces = 2 # Crucial for deep cloud illumination
```

---

## 5. References & Standards

1.  **Chandrasekhar, S. (1960).** *Radiative Transfer.* Dover Publications, New York. (The definitive mathematical formulation of participating media and multiple scattering).
2.  **Henyey, L. G., & Greenstein, J. L. (1941).** *Diffuse radiation in the Galaxy.* The Astrophysical Journal, 93, 70–83. [DOI: 10.1086/144246] (Original derivation of the single-parameter $g$ scattering phase function).
3.  **Woodcock, E. R., et al. (1965).** *Techniques used in the GEM code for Monte Carlo neutronics calculations in reactor geometry.* Proceedings of the Conference on the Application of Computing Methods to Reactor Problems, ANL-7050, 557–579. (The delta tracking / null-collision method used in production volume path tracers).
4.  **Novák, J., Georgiev, I., Hanika, J., & Křivánek, J. (2018).** *Monte Carlo Methods for Volumetric Light Transport Simulation.* Computer Graphics Forum, 37(2), 551–576. (State-of-the-art survey on volume rendering algorithms).

# Subsurface Scattering (SSS): Random Walk Physics & Skin Micro-Optics

Organic materials (human skin, marble, wax, jade, milk, silicone rubber) are semi-translucent dielectrics. Light penetrates beneath the surface, bounces repeatedly through microscopic cellular structures, and re-emerges at a different location. **Subsurface Scattering (SSS)** simulates this subsurface light transport.

---

## 1. Evolution of SSS Models: From Dipole to Random Walk

```
    [ Jensen Dipole (2001) ]           [ Christensen-Burley (2015) ]       [ Random Walk (Cycles 5.2) ]
    Point source approximation;        Normalized diffusion profile;      True brute-force volumetric
    Fails on curved geometry & ears.   Fast, but light leaks across gaps. path tracing inside the mesh!
```

### 1.1 The Dipole Approximation Limitation (Jensen et al., 2001)
Assumed the geometry was an infinitely thick, flat semi-infinite slab. On thin geometric features (human ears, nostrils, thin fingers), the dipole formula severely over-estimated transmission, causing ears to glow unnaturally bright or translucent like red plastic bags.

### 1.2 True Random Walk SSS (Meng et al., 2015 / Cycles Standard)
Cycles simulates true **volumetric path tracing inside the closed boundary of the mesh**:
1.  When a ray enters the surface, it refracts via Snell's Law into the interior.
2.  The ray executes a physical random walk: advancing by mean free path distance $d = -\ln(\xi) / \sigma_t$.
3.  At each internal scatter point, the ray scatters into a new direction according to the Henyey-Greenstein phase function $p(\theta, g)$.
4.  If the ray hits the boundary from the inside, it reflects or refracts back out into the air.
5.  *Geometric Precision:* Because the random walk respects the actual polygonal boundary faces, **thin geometry behaves with 100% physical fidelity**.

---

## 2. Mean Free Path ($l_{mfp}$) & The Subsurface Radius Vector

Light absorption in biological tissue is wavelength-dependent. Human blood (hemoglobin) absorbs green and blue light violently, but lets red light pass with minimal attenuation.

```
       Incoming White Light (R + G + B)
                       │
                       ▼
       ═══════════════════════════════════════════════ Epidermis
       Blue/Green absorbed quickly (l_mfp ≈ 0.2 mm)
       • • •
             Red light scatters deeply (l_mfp ≈ 3.5 mm)
             \       /        \          /
              \_____/          \________/
       ═══════════════════════════════════════════════ Subdermis
```

### 2.1 The Subsurface Radius Vector $[r_R, r_G, r_B]$
The `Subsurface Radius` input in Blender defines the average scattering distance (in millimeters or meters) for Red, Green, and Blue light channels.

| Material | Red Radius ($r_R$) | Green Radius ($r_G$) | Blue Radius ($r_B$) | Visual Appearance |
| :--- | :---: | :---: | :---: | :--- |
| **Caucasian Skin** | **$3.67\text{ mm}$** | **$1.37\text{ mm}$** | **$0.68\text{ mm}$** | Warm peach with deep blood-red edge glows. |
| **Whole Milk** | $2.55\text{ mm}$ | $3.21\text{ mm}$ | $3.77\text{ mm}$ | Opaque cool white/cream. |
| **White Marble** | $8.50\text{ mm}$ | $5.56\text{ mm}$ | $3.95\text{ mm}$ | Deep translucent mineral waxy glow. |
| **Green Jade** | $0.31\text{ mm}$ | $1.82\text{ mm}$ | $0.65\text{ mm}$ | Deep rich green internal dispersion. |

---

## 3. The Scene Scale Trap: Why `Subsurface Scale` Ruins Characters

Subsurface scattering is an **absolute dimensional physical property** (measured in millimeters or meters), not a relative mesh fraction.
*   *The Trap:* If an artist models a character head that is $20\text{ meters}$ tall instead of $0.20\text{ meters}$ ($20\text{ cm}$), setting `Subsurface Scale = 1.0` will make the skin scatter light over only a fraction of a millimeter relative to the giant head $\implies$ **The skin looks like hard, dead, chalky stone!**
*   Conversely, if the head is $2\text{ millimeters}$ tall, the light scatters completely through the entire skull $\implies$ **The head turns into a glowing gummy candy.**
*   *Rule:* Always apply object scale (`Ctrl+A -> Apply Scale`) and verify real-world bounding box dimensions (`head.dimensions.z \approx 0.23\text{ m}`) before tuning SSS!

---

## 4. Random Walk (Skin) in Blender 5.2

Blender features a dedicated **`Random Walk (Skin)`** method:
*   Combines a dual-layer scattering profile: an upper epidermal layer with low scattering and anisotropic forward lobe ($g \approx 0.8$), over a dense subdermal hemoglobin layer.
*   Eliminates the "waxy doll" look of earlier shaders, preserving microscopic pore bump detail while providing warm fleshy backscattering.

```python
import bpy

def configure_human_skin_sss(principled_node, scale_meters=0.002):
    """
    Sets up physically accurate Random Walk (Skin) SSS parameters in Blender 5.2.
    """
    # 1. Select Random Walk (Skin) method
    principled_node.subsurface_method = 'RANDOM_WALK_SKIN'
    
    # 2. SSS Weight = 1.0 (Full skin participation)
    principled_node.inputs['Subsurface Weight'].default_value = 1.0
    
    # 3. Scale factor (2mm average penetration)
    principled_node.inputs['Subsurface Scale'].default_value = scale_meters
    
    # 4. Radius RGB (Blood-rich biological tissue scattering ratios)
    principled_node.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.18)
    
    # 5. Subsurface Anisotropy (Forward scattering through cartilage)
    principled_node.inputs['Subsurface Anisotropy'].default_value = 0.75
    
    # 6. Base Color (Flesh tone)
    principled_node.inputs['Base Color'].default_value = (0.82, 0.58, 0.46, 1.0)
    principled_node.inputs['Roughness'].default_value = 0.42
```

---

## 5. References & Standards

1.  **Meng, J., et al. (2015).** *Physically-Based Subsurface Scattering for Real-Time and Offline Rendering.* ACM Transactions on Graphics. (The foundation of modern Random Walk SSS in production path tracers).
2.  **Christensen, P. H., & Burley, B. (2015).** *Approximate Reflectance Profiles for Efficient Subsurface Scattering.* Pixar Technical Report / Eurographics Symposium on Rendering (EGSR '15). (Normalized diffusion profiles).
3.  **Jensen, H. W., Marschner, S. R., Levoy, M., & Hanrahan, P. (2001).** *A Practical Model for Subsurface Light Transport.* Proceedings of the 28th Annual Conference on Computer Graphics and Interactive Techniques (SIGGRAPH '01), 511–518. (The classic BSSRDF dipole model).
4.  **Blender Foundation. (2024).** *Cycles Subsurface Scattering Algorithms Reference.* https://docs.blender.org/manual/en/latest/render/cycles/render_settings/subsurface_scattering.html

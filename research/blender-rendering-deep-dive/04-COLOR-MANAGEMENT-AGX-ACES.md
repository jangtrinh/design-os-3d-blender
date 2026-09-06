# Color Management Science: AgX, ACES & Spectral Gamut Mapping

In computer graphics, light is linear and unbounded ($[0, \infty)$). Display screens are non-linear and strictly bounded ($[0, 1.0]$). **Color Management** governs how high-dynamic-range (HDR) scene radiance maps down to screen display pixels without clipping colors, destroying saturation, or shifting hues.

---

## 1. The Dynamic Range Failure: Why Standard sRGB Destroys Renders

For decades, software used a naive $1:1$ clamp to map scene radiance to sRGB:

```
                  The 8-Bit sRGB "Notorious 6" Clipping Trap
                  
     Light Intensity (Radiance)
            ▲
       10.0 ┼                       R, G, B saturate to (1.0, 1.0, 0.0)
            │                       Creates hideous solid neon yellow bands
        1.0 ┼───────┬───────────    around fire, lights, and sun reflections!
            │      / \
            │     /   \  Hard Clamp at 1.0: All highlight detail destroyed!
            └────┴─────┴────────► Pixel Position
```

### 1.1 The Abney Effect & Highlight Hue Skewing
When a bright red laser or orange flame enters high intensity in standard sRGB:
1.  The Red channel hits $1.0$ first and clips.
2.  As light intensity doubles, the Green channel continues climbing toward $1.0$.
3.  The color vector $(1.0, G, 0)$ rotates on the chromaticity diagram toward pure yellow!
4.  *The Result:* Bright orange fire renders with ugly neon yellow borders; skin tones under bright sun turn plastic yellow; blue LED lights turn cyan/white.

---

## 2. Evolution: Standard vs. Filmic vs. AgX

Blender 4.0 replaced Filmic with **AgX** as the default display transform.

```
       Filmic (Blender 2.8–3.6)                      AgX (Blender 4.0–5.2 LTS)
    ┌───────────────────────────────┐              ┌───────────────────────────────┐
    │ Logarithmic curve preserves   │              │ Wide gamut inset + perceptual │
    │ 16+ stops of dynamic range,   │              │ highlight desaturation.       │
    │ BUT high-intensity primaries  │              │ Highlights roll off smoothly  │
    │ over-saturate and posterize!  │              │ to pure white (No hue shift!) │
    └───────────────────────────────┘              └───────────────────────────────┘
```

### 2.1 The AgX Pipeline Architecture (Troy Sobotka)
AgX operates in three distinct stages inside OpenColorIO (OCIO):

1.  **Gamut Inset (Rec.2020 / Linear BT.2020):**
    Compresses extreme out-of-gamut spectral colors inward toward the center of the chromaticity diagram, ensuring no individual channel clips prematurely.
2.  **Perceptual Highlight Desaturation:**
    As luminance approaches the clipping ceiling, saturation is progressively attenuated. In the physical world, intense light bleaches the human retinal cones; AgX mimics this by rolling highlights smoothly into **neutral paper white**.
3.  **Sigmoidal S-Curve Mapping:**
    *   **Toe:** Smooth shadow contrast without crushed blacks.
    *   **Midtones:** 18% middle grey ($0.18$) maps exactly to sRGB value $\approx 0.45$.
    *   **Shoulder:** Elegant soft roll-off over $+14\text{ stops}$ of overexposure.

---

## 3. ACES (Academy Color Encoding System) Pipeline

For visual effects (VFX) and cinematic film pipelines integrating with Unreal Engine, Maya, and Nuke:

```
   Scene Linear Cameras ──► [ Input Transform (IDT) ] ──► ACEScg (AP1 Wide Gamut)
                                                                 │
                                                       [ Blender Cycles Render ]
                                                                 │
   Display Monitor      ◄── [ Output Transform (ODT) ] ◄── ACEScc / ACEScct
```

### 3.1 ACES Color Spaces Comparison

| Color Space | Gamut Primaries | White Point | Transfer Function | Primary Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **ACES2065-1 (AP0)** | Ultra-wide (encompasses all visible human vision) | D60 ($0.32168, 0.33767$) | Linear | Long-term archival, master interchange. |
| **ACEScg (AP1)** | Cinema Gamut (wider than P3, tight fit to visible) | D60 | Linear | **The VFX CGI rendering & compositing standard.** |
| **ACEScc / ACEScct** | AP1 | D60 | Logarithmic | Color grading in DaVinci Resolve. |
| **sRGB / Rec.709** | Narrow Display Gamut | D65 ($0.3127, 0.3290$) | sRGB Piecewise | Consumer PC monitors and web graphics. |

---

## 4. Programmatic Color Management in Blender 5.2

To guarantee consistency between viewport, batch renders, and compositor exports:

```python
import bpy

def setup_scientific_color_pipeline(transform='AgX', look='AgX - Medium High Contrast'):
    """
    Configures Blender 5.2 OpenColorIO pipeline for production rendering.
    """
    scene = bpy.context.scene
    color_man = scene.display_settings
    view_man = scene.view_settings
    
    # 1. Display Device (Standard sRGB monitor or Apple Display P3)
    color_man.display_device = 'sRGB'
    
    # 2. View Transform (AgX is the 5.x standard; avoids Filmic hue skews)
    view_man.view_transform = transform
    
    # 3. Contrast Look
    view_man.look = look
    
    # 4. Exposure & Gamma baseline
    view_man.exposure = 0.0
    view_man.gamma = 1.0
    
    # 5. Sequencer color space
    scene.sequencer_colorspace_settings.name = 'sRGB'
```

---

## 5. References & Standards

1.  **Sobotka, T. (2022).** *AgX: Next-Generation Display Rendering Transform for OpenColorIO.* GitHub Repository: https://github.com/sobotka/AgX (Theoretical formulation of gamut insets and highlight desaturation).
2.  **Academy of Motion Picture Arts and Sciences. (2020).** *Specification S-2014-004: ACES Color Encodings Version 1.2.* AMPAS, Los Angeles, CA.
3.  **Fairchild, M. D. (2013).** *Color Appearance Models* (3rd ed.). John Wiley & Sons. (Physiological foundations of human vision, chromatic adaptation, and Abney/Bezold-Brücke hue shifts).
4.  **ISO 12646:2014.** *Graphic technology — Displays for colour proofing — Characteristics.* International Organization for Standardization.
5.  **Selan, J. (2010).** *Cinematic Color: From Your Monitor to the Big Screen.* ACM SIGGRAPH 2010 Courses. (The OpenColorIO architecture specification).

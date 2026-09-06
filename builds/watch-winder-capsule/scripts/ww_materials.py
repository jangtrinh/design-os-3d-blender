"""Named, reusable node materials for the capsule. Sockets are resolved by name at runtime
and asserted to exist (Blender 5.2 Principled names). Hex sRGB -> scene-linear once here.
"""
import bpy

TEMPERATURE_NOTE = "6500K descriptor is descriptive only; #D4EBFF is the visual start target"


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)


def _new(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    mat["ww_material"] = True
    return mat, nt, out


def _principled(nt, out, **values):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    for k, v in values.items():
        assert k in b.inputs, f"Principled has no input {k!r}: {[s.name for s in b.inputs]}"
        b.inputs[k].default_value = v
    return b


def _bump(nt, b, coords_node, scale, strength, distance, detail=3.0, roughness=0.5):
    """Noise micro-bump into the Principled Normal. Scale is in 1/metre (object space)."""
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    nt.links.new(coords_node.outputs["Object"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return bump


def _tangent(nt, b, rotation=0.0):
    t = nt.nodes.new("ShaderNodeTangent")
    t.direction_type, t.axis = "RADIAL", "Z"
    nt.links.new(t.outputs["Tangent"], b.inputs["Tangent"])
    b.inputs["Anisotropic Rotation"].default_value = rotation
    return t


def mat_graphite():
    """Owner decision 2026-09-06 ("chat lieu nhua nham thoi la duoc"): matte dark plastic shell,
    not metallic titanium. Same graphite tone, dielectric, satin-matte, fine moulded grain."""
    mat, nt, out = _new("WW_MAT_GRAPHITE")
    b = _principled(nt, out, **{"Base Color": hex_rgba("#1A1D24"), "Metallic": 0.0, "Roughness": 0.58,
                                "Specular IOR Level": 0.35})
    tc = nt.nodes.new("ShaderNodeTexCoord")
    _bump(nt, b, tc, scale=6000.0, strength=0.08, distance=0.0002, detail=2.0)  # ~0.17 mm moulded matte grain
    mat["ww_note"] = "matte plastic per owner 2026-09-06; metallic titanium (0.9/0.35) retired"
    return mat


def mat_walnut():
    mat, nt, out = _new("WW_MAT_WALNUT")
    b = _principled(nt, out, **{"Metallic": 0.0, "Roughness": 0.38, "Coat Weight": 0.8, "Coat Roughness": 0.25})
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 0.18, 1.0)  # stretch bands along local Y: long grain over the shell
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type, wave.bands_direction = "BANDS", "X"
    wave.inputs["Scale"].default_value = 260.0       # ~3.8 mm band period on a 140 mm shell
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgba("#2E1A0F")
    ramp.color_ramp.elements[1].color = hex_rgba("#7C4A2A")
    mid = ramp.color_ramp.elements.new(0.55)
    mid.color = hex_rgba("#5A3219")
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, b, tc, scale=4500.0, strength=0.03, distance=0.0001, detail=2.0)  # pores under the coat
    return mat


def mat_acrylic():
    mat, nt, out = _new("WW_MAT_ACRYLIC")
    _principled(nt, out, **{"Base Color": (1.0, 1.0, 1.0, 1.0), "Transmission Weight": 1.0, "Roughness": 0.02,
                            "IOR": 1.491, "Metallic": 0.0})
    mat["ww_dispersion"] = "omitted: Principled BSDF in this runtime exposes no dispersion input; no substitute used"
    return mat


def mat_metal(name, roughness=0.15, anisotropic=0.6, rotation=0.0, tangent=True):
    mat, nt, out = _new(name)
    b = _principled(nt, out, **{"Base Color": hex_rgba("#D8D8D8"), "Metallic": 1.0, "Roughness": roughness,
                                "Anisotropic": anisotropic})
    if tangent and anisotropic > 0:
        _tangent(nt, b, rotation)
    return mat


def mat_leather(name, perforated):
    mat, nt, out = _new(name)
    b = _principled(nt, out, **{"Base Color": hex_rgba("#101010"), "Roughness": 0.65, "Specular IOR Level": 0.4,
                                "Metallic": 0.0})
    mat["ww_specular_mapping"] = "brief 'specular 0.4' -> Principled 'Specular IOR Level' (4.x+ name of the specular level control)"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 2500.0  # ~0.4 mm leather grain
    grain.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], grain.inputs["Vector"])
    height = grain.outputs["Fac"]
    if perforated:
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 850.0  # ~1.2 mm dot pitch
        nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
        dots = nt.nodes.new("ShaderNodeMath")
        dots.operation = "LESS_THAN"
        dots.inputs[1].default_value = 0.22
        nt.links.new(vor.outputs["Distance"], dots.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Normal"], sep.inputs["Vector"])
        top = nt.nodes.new("ShaderNodeMath")
        top.operation = "GREATER_THAN"
        top.inputs[1].default_value = 0.9
        nt.links.new(sep.outputs["Z"], top.inputs[0])
        mask = nt.nodes.new("ShaderNodeMath")
        mask.operation = "MULTIPLY"
        nt.links.new(dots.outputs["Value"], mask.inputs[0])
        nt.links.new(top.outputs["Value"], mask.inputs[1])
        mix = nt.nodes.new("ShaderNodeMath")
        mix.operation = "SUBTRACT"
        nt.links.new(grain.outputs["Fac"], mix.inputs[0])
        nt.links.new(mask.outputs["Value"], mix.inputs[1])
        height = mix.outputs["Value"]
        mat["ww_perforation"] = "decorative shader dots on the top face only; not functional ventilation"
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0003
    nt.links.new(height, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_led_emitter():
    mat, nt, out = _new("WW_MAT_LED_EMITTER")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = hex_rgba("#D4EBFF")
    e.inputs["Strength"].default_value = 6.0  # 10 read hot in the 512 px preview; restrained halo per brief
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    mat["ww_temperature"] = TEMPERATURE_NOTE
    return mat


def mat_diffuser():
    mat, nt, out = _new("WW_MAT_LED_DIFFUSER")
    _principled(nt, out, **{"Base Color": (1.0, 1.0, 1.0, 1.0), "Transmission Weight": 1.0, "Roughness": 0.55, "IOR": 1.45})
    return mat


def mat_simple(name, hex_color, roughness, specular=0.5, metallic=0.0):
    mat, nt, out = _new(name)
    _principled(nt, out, **{"Base Color": hex_rgba(hex_color), "Roughness": roughness, "Specular IOR Level": specular,
                            "Metallic": metallic})
    return mat


def mat_dial():
    mat, nt, out = _new("WW_MAT_DIAL")
    b = _principled(nt, out, **{"Base Color": hex_rgba("#C9C9CB"), "Metallic": 0.85, "Roughness": 0.3, "Anisotropic": 0.8})
    _tangent(nt, b, 0.25)  # radial sunburst brushing
    return mat


def mat_crystal():
    mat, nt, out = _new("WW_MAT_CRYSTAL")
    _principled(nt, out, **{"Base Color": (1.0, 1.0, 1.0, 1.0), "Transmission Weight": 1.0, "Roughness": 0.0, "IOR": 1.52})
    return mat


def build_all():
    return {
        "graphite": mat_graphite(), "walnut": mat_walnut(), "acrylic": mat_acrylic(),
        "metal_turned": mat_metal("WW_MAT_METAL_TURNED", 0.15, 0.6, 0.0),
        "metal_radial": mat_metal("WW_MAT_METAL_RADIAL", 0.15, 0.6, 0.25),
        "metal_leg": mat_metal("WW_MAT_METAL_BRUSHED_LEG", 0.15, 0.6, 0.25),
        "metal_polished": mat_metal("WW_MAT_METAL_POLISHED", 0.12, 0.0, 0.0, tangent=False),
        "metal_knurl": mat_metal("WW_MAT_METAL_KNURL", 0.22, 0.0, 0.0, tangent=False),
        "leather": mat_leather("WW_MAT_LEATHER_CUSHION", perforated=True),
        "strap": mat_leather("WW_MAT_LEATHER_STRAP", perforated=False),
        "led": mat_led_emitter(), "diffuser": mat_diffuser(),
        "rubber": mat_simple("WW_MAT_RUBBER", "#111111", 0.85, 0.3),
        "interior": mat_simple("WW_MAT_INTERIOR", "#14161A", 0.55, 0.3),
        "dial": mat_dial(), "crystal": mat_crystal(),
    }


ROLE_MAP = {
    "visor": "acrylic", "front_rim": "metal_turned", "knob_boss": "metal_turned", "hinge_fixed": "metal_polished",
    "hinge_moving": "metal_polished", "finger_tab": "metal_polished", "control": "metal_polished",
    "control_bezel": "metal_turned", "usb_receptacle": "metal_polished", "knob": "metal_polished",
    "knurl": "metal_knurl", "faceplate": "metal_radial", "leg": "metal_leg", "foot": "rubber",
    "rotor_cup": "interior", "inner_liner": "interior", "usb_recess": "interior", "led_diffuser": "diffuser",
    "led_emitter": "led", "cushion": "leather", "watch": "metal_polished", "watch_part": "metal_polished",
    "shaft": "metal_polished",
}
NAME_OVERRIDES = {"WW_WATCH_DIAL": "dial", "WW_WATCH_CRYSTAL": "crystal", "WW_WATCH_STRAP_12": "strap",
                  "WW_WATCH_STRAP_6": "strap"}


def assign(mats, variant):
    """Assign by role; shell + service cover follow the variant. Returns (assigned, unmapped)."""
    assigned, unmapped = {}, []
    for ob in bpy.data.objects:
        if not ob.name.startswith("WW_") or ob.type != "MESH":
            continue
        role = ob.get("ww_role", "")
        if role in ("cutter", "internal_envelope", "studio_ground"):
            continue
        key = NAME_OVERRIDES.get(ob.name) or ("graphite" if variant == "graphite" else "walnut") \
            if role in ("shell", "service_cover") or ob.name in NAME_OVERRIDES else ROLE_MAP.get(role)
        if key is None:
            unmapped.append(ob.name)
            continue
        ob.data.materials.clear()
        ob.data.materials.append(mats[key])
        assigned[ob.name] = mats[key].name
    return assigned, unmapped


def verify(mat):
    """Read back what is actually wired: output linked + Principled/Emission values."""
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    rep = {"output_linked": bool(out and out.inputs["Surface"].is_linked)}
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        for k in ("Metallic", "Roughness", "IOR", "Transmission Weight", "Coat Weight", "Coat Roughness",
                  "Anisotropic", "Anisotropic Rotation", "Specular IOR Level"):
            rep[k] = round(b.inputs[k].default_value, 4)
        rep["Base Color"] = [round(c, 4) for c in b.inputs["Base Color"].default_value[:3]]
        rep["normal_linked"] = b.inputs["Normal"].is_linked
        rep["tangent_linked"] = b.inputs["Tangent"].is_linked
        rep["base_color_linked"] = b.inputs["Base Color"].is_linked
    e = next((n for n in nt.nodes if n.type == "EMISSION"), None)
    if e:
        rep["emission_strength"] = e.inputs["Strength"].default_value
        rep["emission_color"] = [round(c, 4) for c in e.inputs["Color"].default_value[:3]]
    rep["image_textures"] = [n.image.name for n in nt.nodes if n.type == "TEX_IMAGE" and n.image]
    return rep

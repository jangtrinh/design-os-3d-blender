"""Saved state presets on ONE canonical product: hero (closed), rear, open (lid 100 deg +
cushion unit standing beside the housing). Stored as scene custom properties (JSON) and
applied by name. Shell variant is a material swap on identical geometry."""
import json
import math

import bpy
from mathutils import Matrix, Vector

PRESET_KEY = "ww_presets_json"


def _unit_detached_matrix(P):
    """World matrix for the cushion unit standing on the table: 12 o'clock up, dial facing
    the front-left camera. The unit's local origin is the rotor centre, so we solve the
    table contact from the evaluated cushion afterwards (see apply)."""
    o = P["studio"]["open"]
    yaw = math.radians(o["unit_yaw_deg"])
    # local Y (12 o'clock) -> world +Z ; local Z (dial normal) -> horizontal toward -Y rotated by yaw
    rot = Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(math.radians(90), 4, "X")  # +90 about X: local Y -> +Z, local Z -> -Y
    pos = Vector([c * 0.001 for c in o["unit_world_mm"]])
    return Matrix.Translation(pos) @ rot


def define(scene, P):
    # closed-lid base from the DESIGN (pivot at 12 o'clock rim), never from the current pose
    ro, w0 = P["shell"]["opening_radius"], P["shell"]["opening_datum_w0"]
    lid_base = list(map(list, Matrix.Translation(Vector((0.0, (ro + P["visor"]["hinge_setback"]) * 0.001, w0 * 0.001)))))
    lid_open = float(P["studio"]["open"]["lid_deg"])
    presets = {
        "hero": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_HERO"},
        "rear": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_REAR"},
        "open": {"lid_deg": lid_open, "unit": "detached", "camera": "WW_CAM_OPEN"},
        # extra states (owner 2026-09-06 09:40 asked for more states); cameras solved by pass-23
        "hero-right": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_HERO_RIGHT", "solve": (30, 12, 0.88, "product", 2.8)},
        "front": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_FRONT", "solve": (0, 10, 0.88, "product", 4.0)},
        "profile": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_PROFILE", "solve": (90, 8, 0.88, "product", 4.0)},
        "top": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_TOP", "solve": (-20, 60, 0.88, "product", 4.0)},
        "rear-quarter": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_REAR_QUARTER", "solve": (150, 12, 0.88, "product", 4.0)},
        "lid-half": {"lid_deg": 50.0, "unit": "seated", "camera": "WW_CAM_LID_HALF", "solve": (-30, 12, 0.88, "product", 4.0)},
        "open-seated": {"lid_deg": lid_open, "unit": "seated", "camera": "WW_CAM_OPEN_SEATED", "solve": (-25, 22, 0.88, "product", 4.0)},
        "macro-dial": {"lid_deg": lid_open, "unit": "seated", "camera": "WW_CAM_MACRO_DIAL", "solve": (-15, 38, 0.62, "watch", 4.0)},
        "macro-knob": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_MACRO_KNOB", "solve": (-52, 10, 0.72, "knob", 4.0)},  # 3/4 view shows the knurl; head-on read as a flat disc
        "macro-hinge": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_MACRO_HINGE", "solve": (-25, 38, 0.62, "hinge", 11.0)},
        "macro-guilloche": {"lid_deg": lid_open, "unit": "seated", "camera": "WW_CAM_MACRO_GUILLOCHE", "solve": (-12, 48, 0.58, "guilloche", 11.0, 0.32, "ring6")},
        "macro-controls": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_MACRO_CONTROLS", "solve": (172, 42, 0.62, "controls", 11.0)},
        "macro-usb": {"lid_deg": 0.0, "unit": "seated", "camera": "WW_CAM_MACRO_USB", "solve": (180, 6, 0.55, "usb", 11.0)},
        "_lid_base": lid_base,
    }
    scene[PRESET_KEY] = json.dumps(presets)
    return presets


def apply(scene, name, P):
    presets = json.loads(scene[PRESET_KEY])
    pr = presets[name]
    lid = bpy.data.objects["WW_LID_PIVOT"]
    unit = bpy.data.objects["WW_CUSHION_UNIT"]
    lid.matrix_local = Matrix(presets["_lid_base"]) @ Matrix.Rotation(math.radians(-pr["lid_deg"]), 4, "X")
    if pr["unit"] == "seated":
        unit.matrix_local = Matrix.Identity(4)
    elif pr["unit"] == "lifted":
        unit.matrix_local = Matrix.Translation(Vector((0.0, 0.0, 0.070)))  # 70 mm along the rotor axis (validated clear)
    else:
        unit.matrix_world = _unit_detached_matrix(P)
        bpy.context.view_layer.update()
        # drop the unit so its lowest evaluated point (cushion or strap) rests on the table
        deps = bpy.context.evaluated_depsgraph_get()
        zmin = 1e9
        for ob in unit.children_recursive:
            if ob.type != "MESH" or ob.hide_render:
                continue
            ev = ob.evaluated_get(deps)
            me = ev.to_mesh()
            if me.vertices:
                zmin = min(zmin, min((ev.matrix_world @ v.co).z for v in me.vertices))
            ev.to_mesh_clear()
        m = unit.matrix_world.copy()
        m.translation.z -= zmin
        unit.matrix_world = m
    cam = bpy.data.objects.get(pr["camera"])  # cameras are created by pass-18 after the first apply
    if cam is not None:
        scene.camera = cam
    bpy.context.view_layer.update()
    return pr


def set_variant(scene, variant):
    mat = bpy.data.materials["WW_MAT_GRAPHITE" if variant == "graphite" else "WW_MAT_WALNUT"]
    for ob in (bpy.data.objects["WW_SHELL"], bpy.data.objects["WW_REAR_SERVICE_COVER"]):
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    scene["ww_shell_variant"] = variant
    return mat.name


def aim_point(key):
    """Named surface points (world, metres) used to re-aim macro cameras."""
    import bpy as _bpy
    body = _bpy.data.objects["WW_BODY_FRAME"]
    if key == "ring6":  # guilloche ring at 6 o'clock, on the relief surface
        return body.matrix_world @ Vector((0.0, -0.0425, 0.030))
    if key == "dial":
        return _bpy.data.objects["WW_WATCH_DIAL"].matrix_world.translation
    raise KeyError(key)

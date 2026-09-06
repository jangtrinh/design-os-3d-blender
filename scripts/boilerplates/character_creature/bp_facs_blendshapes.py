"""
bp_facs_blendshapes.py — FACS 52 ARKit Facial Blendshapes & Corrective Shape Keys Generator.

Standards & Academic Citations:
- Ekman & Friesen (1978): "Facial Action Coding System" — the ~44 anatomical Action Units
  ARKit's blendshape set is INSPIRED BY. The 52 ARKit targets are Apple's product spec, not
  FACS AUs and not an ISO standard; do not cite ISO/IEC 14496-2 (MPEG-4 FAPs) for them.
- Apple Inc.: "ARKit Face Tracking — 52 blend shape locations" (developer documentation).
- Lewis, Cordner & Fong (2000): "Pose space deformation" (combination/corrective shapes).

SCOPE: this module creates all 52 named targets, but only 6 of them carry sculpted vertex
deltas (jawOpen, mouthSmileLeft/Right, eyeBlinkLeft/Right, browInnerUp). The other 46 are
correctly-named identity keys — placeholders for a sculpt or a capture solve, not a
performance-ready face rig.

Target: Blender 5.2 LTS (Data-API ShapeKeys & Drivers, Headless-Safe).

Runtime-verified 2026-09-06 on Blender 5.2.0 LTS: shape_key_add / slider_min / slider_max /
ShapeKey.driver_add("value") and DriverTarget.id_type == 'KEY' all behave as used here; the
product driver evaluates to w_a * w_b after a depsgraph update.
"""

from __future__ import annotations
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from typing import Optional, List, Dict, Any


ARKIT_52_NAMES = [
    # Eye Group (14)  -- plus the Brow Group below, ARKit's eye/brow block is 19
    "eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft",
    "eyeSquintLeft", "eyeWideLeft",
    "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight",
    "eyeSquintRight", "eyeWideRight",
    # Jaw Group (4)
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    # Mouth Group (23)
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    # Brow Group (5)
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    # Cheek & Nose Group (5)
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight",
    # Tongue (1)
    "tongueOut"
]


def create_procedural_head_mesh(
    radius: float = 0.10,
    col: Optional[bpy.types.Collection] = None
) -> bpy.types.Object:
    """Creates a scaled UV-sphere head PROXY in BMesh.

    Not an all-quad face mesh and not a modelled head: a 24x16 UV sphere has triangle fans
    at both poles and no eye sockets, lips, or nostrils. It exists so the shape-key and
    driver plumbing below can be exercised headlessly on real geometry.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm, u_segments=24, v_segments=16, radius=radius,
        matrix=Matrix.Diagonal((0.85, 1.05, 1.15, 1.0))
    )
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new("Character_Head_FACS")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(mesh.name, mesh)
    target_col = col or bpy.context.scene.collection
    target_col.objects.link(obj)
    return obj


def initialize_arkit_52_shape_keys(
    head_obj: bpy.types.Object
) -> Dict[str, bpy.types.ShapeKey]:
    """
    Initializes the Basis and all 52 ARKit FACS shape keys on the head object.
    Applies mathematical vertex displacements for primary Action Units:
    - jawOpen: lowers vertices in the lower jaw region (Z < -0.02, Y > 0)
    - mouthSmileLeft / Right: lifts and widens the mouth corners
    - eyeBlinkLeft / Right: pulls upper eyelid margin downward
    - browInnerUp: elevates medial brow region
    """
    mesh = head_obj.data
    # 1. Ensure Basis shape key
    if not mesh.shape_keys:
        head_obj.shape_key_add(name="Basis", from_mix=False)

    basis_key = mesh.shape_keys.key_blocks["Basis"]
    keys_dict = {"Basis": basis_key}

    # 2. Add all 52 keys
    for name in ARKIT_52_NAMES:
        if name not in mesh.shape_keys.key_blocks:
            sk = head_obj.shape_key_add(name=name, from_mix=False)
            sk.value = 0.0
            sk.slider_min = 0.0
            sk.slider_max = 1.0
            keys_dict[name] = sk
        else:
            keys_dict[name] = mesh.shape_keys.key_blocks[name]

    # 3. Apply geometric delta offsets for core Action Units
    # jawOpen (AU26): Lower mandible depression
    sk_jaw = keys_dict["jawOpen"]
    for i, v in enumerate(basis_key.data):
        co = v.co
        # Lower jaw criteria: below center and in the anterior/chin region
        if co.z < -0.02 and co.y > -0.03:
            drop_factor = (-co.z - 0.02) / 0.08
            sk_jaw.data[i].co = co + Vector((0.0, -0.005 * drop_factor, -0.025 * drop_factor))

    # mouthSmileLeft / Right (AU12): Zygomaticus major pull
    for side, s_name in [(-1.0, "mouthSmileRight"), (1.0, "mouthSmileLeft")]:
        sk_smile = keys_dict[s_name]
        for i, v in enumerate(basis_key.data):
            co = v.co
            if co.z > -0.06 and co.z < -0.01 and co.y > 0.04:
                # Modiolus corner on the respective side
                if (side > 0 and co.x > 0.01) or (side < 0 and co.x < -0.01):
                    dist = abs(co.x)
                    sk_smile.data[i].co = co + Vector((
                        side * 0.008 * dist,
                        -0.003,
                        0.012 * dist
                    ))

    # eyeBlinkLeft / Right: Upper eyelid depression
    for side, b_name in [(-1.0, "eyeBlinkRight"), (1.0, "eyeBlinkLeft")]:
        sk_blink = keys_dict[b_name]
        for i, v in enumerate(basis_key.data):
            co = v.co
            # Upper orbit zone
            if co.z > 0.01 and co.z < 0.05 and co.y > 0.05:
                if (side > 0 and co.x > 0.015) or (side < 0 and co.x < -0.015):
                    sk_blink.data[i].co = co + Vector((0.0, 0.002, -0.015))

    # browInnerUp (AU1): Medial frontalis pull
    sk_brow_up = keys_dict["browInnerUp"]
    for i, v in enumerate(basis_key.data):
        co = v.co
        if co.z > 0.04 and co.z < 0.08 and co.y > 0.04 and abs(co.x) < 0.035:
            lift = (0.035 - abs(co.x)) / 0.035
            sk_brow_up.data[i].co = co + Vector((0.0, 0.002, 0.012 * lift))

    return keys_dict


def add_combination_corrective_shape_key(
    head_obj: bpy.types.Object,
    corr_name: str,
    driver_var_a: str,
    driver_var_b: str
) -> bpy.types.ShapeKey:
    """
    Creates a combination corrective shape key (CSK) driven by the product of two
    blendshape activations: value = var_a * var_b.
    Resolves non-linear superposition tearing (e.g. jawOpen + mouthSmile).
    """
    mesh = head_obj.data
    sk_corr = head_obj.shape_key_add(name=corr_name, from_mix=False)
    sk_corr.slider_min = -1.0
    sk_corr.slider_max = 1.0

    # Add scripted driver to the corrective key's value property
    driver_fcurve = sk_corr.driver_add("value")
    drv = driver_fcurve.driver
    drv.type = 'SCRIPTED'
    drv.expression = "var_a * var_b"

    # Driver variable A
    va = drv.variables.new()
    va.name = "var_a"
    va.type = 'SINGLE_PROP'
    va.targets[0].id_type = 'KEY'
    va.targets[0].id = mesh.shape_keys
    va.targets[0].data_path = f'key_blocks["{driver_var_a}"].value'

    # Driver variable B
    vb = drv.variables.new()
    vb.name = "var_b"
    vb.type = 'SINGLE_PROP'
    vb.targets[0].id_type = 'KEY'
    vb.targets[0].id = mesh.shape_keys
    vb.targets[0].data_path = f'key_blocks["{driver_var_b}"].value'

    return sk_corr


if __name__ == '__main__':
    print("Testing bp_facs_blendshapes.py headless...")
    head = create_procedural_head_mesh()
    keys = initialize_arkit_52_shape_keys(head)
    blocks = head.data.shape_keys.key_blocks
    print(f"Created Head with {len(blocks)} shape keys.")

    assert len(ARKIT_52_NAMES) == 52, f"ARKit inventory is {len(ARKIT_52_NAMES)}, must be 52"
    assert len(set(ARKIT_52_NAMES)) == 52, "duplicate name in the ARKit inventory"
    assert len(blocks) == 53, f"expected Basis + 52 keys, got {len(blocks)}"
    assert all(n in blocks for n in ARKIT_52_NAMES), "an ARKit target is missing"
    assert all(blocks[n].slider_min == 0.0 and blocks[n].slider_max == 1.0
               for n in ARKIT_52_NAMES), "ARKit targets must be clamped to [0, 1]"

    # Exactly the six sculpted AUs must displace vertices; the rest are identity keys.
    basis = blocks["Basis"]
    sculpted = {k.name for k in blocks if k.name != "Basis"
                and any((k.data[i].co - basis.data[i].co).length > 1e-9
                        for i in range(len(basis.data)))}
    assert sculpted == {"jawOpen", "mouthSmileLeft", "mouthSmileRight",
                        "eyeBlinkLeft", "eyeBlinkRight", "browInnerUp"}, sorted(sculpted)

    # Add corrective key for JawOpen + Smile and prove the driver actually multiplies.
    corr_key = add_combination_corrective_shape_key(
        head, "jawOpen_mouthSmileLeft_corr", "jawOpen", "mouthSmileLeft"
    )
    print(f"Created Corrective Key: {corr_key.name} with scripted driver.")
    assert corr_key.name in head.data.shape_keys.key_blocks
    blocks["jawOpen"].value = 1.0
    blocks["mouthSmileLeft"].value = 0.5
    bpy.context.view_layer.update()
    evaluated = head.data.shape_keys.evaluated_get(bpy.context.evaluated_depsgraph_get())
    driven = evaluated.key_blocks["jawOpen_mouthSmileLeft_corr"].value
    assert abs(driven - 0.5) < 1e-5, f"corrective driver evaluated to {driven}, expected 0.5"

    print(f"Asserts OK: 52 unique targets + Basis, {len(sculpted)} sculpted AUs, "
          f"corrective driver = {driven:.3f} (1.0 * 0.5).")
    print("bp_facs_blendshapes verified successfully.")

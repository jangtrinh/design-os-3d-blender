"""
bp_biped_locomotion.py — Procedural Biomechanical Walk Cycle Generator for Biped Armatures.

Standards & Academic Citations:
- Winter (2009): "Biomechanics and Motor Control of Human Movement" — source of the gait
  percentages (stance ~0-62%, swing ~62-100%) and of pelvic list / transverse rotation.
- Parent (2012): "Computer Animation: Algorithms and Techniques" (cyclic F-curve interpolation).
- The Contact / Down / Passing / Up key-pose naming is animation practice (Williams,
  "The Animator's Survival Kit"), not Winter's clinical phase nomenclature.

SCOPE (do not oversell): this generates a 5-key HARMONIC APPROXIMATION of a walk — one key
every quarter stride on sine/cosine terms. It is not a gait solve. Consequences that are
real and measurable: the planted foot keeps sliding along Y (no stance plateau, so expect
foot slide), pelvis Z extrema fall at 0 / T/4 / T/2 / 3T/4 rather than at Winter's 12% /
35% / 62% / 85%, and no ground-contact or centre-of-mass constraint is enforced. Review an
animatic before treating the result as a walk cycle.

Target: Blender 5.2 LTS (Data-API Actions, Slotted Actions / Channelbags, Headless-Safe).

Runtime-verified 2026-09-06 on Blender 5.2.0 LTS: `Action.fcurves` no longer exists; the
curves live in action.layers[0].strips[0].channelbag(slot). Keying a pose bone auto-creates
one layer, one strip and one slot, and binds it to animation_data.action_slot.
"""

from __future__ import annotations
import bpy
import math
from typing import Optional, Dict, Any, List


def get_all_action_fcurves(action: bpy.types.Action) -> List[bpy.types.FCurve]:
    """Returns all F-Curves in Blender 5.2 layered/slotted action or legacy action."""
    fcurves = []
    # Blender 5.2 path first: legacy Action.fcurves was removed, the elif is 4.x fallback.
    if hasattr(action, "layers"):
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        fcurves.extend(cb.fcurves)
    elif hasattr(action, "fcurves"):
        fcurves.extend(action.fcurves)
    return fcurves


def generate_walk_cycle_action(
    arm_obj: bpy.types.Object,
    action_name: str = "Biped_Walk_Cycle",
    stride_frames: int = 32,
    stride_length_m: float = 0.65,
    bounce_amplitude_m: float = 0.035,
    pelvic_tilt_deg: float = 4.0,
    arm_swing_deg: float = 25.0
) -> bpy.types.Action:
    """
    Generates a continuous, seamlessly looping 4-phase biped walk cycle action
    using analytical harmonic functions evaluated across keyframe points.
    """
    if not arm_obj.animation_data:
        arm_obj.animation_data_create()

    T = stride_frames
    half_stride = stride_length_m * 0.5
    pb = arm_obj.pose.bones

    # 4 Primary Keyframe samples + loop point: 0, T/4, T/2, 3T/4, T
    key_frames = [0, int(T * 0.25), int(T * 0.5), int(T * 0.75), T]

    for f in key_frames:
        t = f / T

        # 1. Hips Vertical Bounce (Double Frequency: 2 bounces per stride)
        if "Hips" in pb:
            hips = pb["Hips"]
            z_disp = bounce_amplitude_m * math.cos(4.0 * math.pi * t)
            hips.location.z = z_disp
            hips.keyframe_insert(data_path="location", index=2, frame=f)

            # Pelvic Yaw & Lateral List
            yaw = math.radians(pelvic_tilt_deg * 1.5) * math.sin(2.0 * math.pi * t)
            tilt = math.radians(pelvic_tilt_deg) * math.sin(2.0 * math.pi * t)
            hips.rotation_euler.z = yaw
            hips.rotation_euler.x = tilt
            hips.keyframe_insert(data_path="rotation_euler", index=2, frame=f)
            hips.keyframe_insert(data_path="rotation_euler", index=0, frame=f)

        # 2. Chest Counter-Rotation (Anti-phase to Hips Yaw)
        if "Chest" in pb:
            chest = pb["Chest"]
            counter_yaw = -0.8 * math.radians(pelvic_tilt_deg * 1.5) * math.sin(2.0 * math.pi * t)
            chest.rotation_euler.z = counter_yaw
            chest.keyframe_insert(data_path="rotation_euler", index=2, frame=f)

        # 3. Foot IK Targets (Translational Trajectory & Foot Roll)
        y_left = half_stride * math.cos(2.0 * math.pi * t)
        y_right = half_stride * math.cos(2.0 * math.pi * t + math.pi)

        z_left = 0.08 * math.sin((t - 0.5) * 2.0 * math.pi) if 0.5 <= t <= 1.0 else 0.0
        z_right = 0.08 * math.sin(t * 2.0 * math.pi) if 0.0 <= t <= 0.5 else 0.0

        pitch_left = math.radians(15.0) * math.sin(2.0 * math.pi * t)
        pitch_right = math.radians(15.0) * math.sin(2.0 * math.pi * t + math.pi)

        if "Foot_IK.L" in pb:
            foot_l = pb["Foot_IK.L"]
            foot_l.location.y = y_left
            foot_l.location.z = z_left
            foot_l.rotation_euler.x = pitch_left
            foot_l.keyframe_insert(data_path="location", index=1, frame=f)
            foot_l.keyframe_insert(data_path="location", index=2, frame=f)
            foot_l.keyframe_insert(data_path="rotation_euler", index=0, frame=f)

        if "Foot_IK.R" in pb:
            foot_r = pb["Foot_IK.R"]
            foot_r.location.y = y_right
            foot_r.location.z = z_right
            foot_r.rotation_euler.x = pitch_right
            foot_r.keyframe_insert(data_path="location", index=1, frame=f)
            foot_r.keyframe_insert(data_path="location", index=2, frame=f)
            foot_r.keyframe_insert(data_path="rotation_euler", index=0, frame=f)

        # 4. Arm IK / UpperArm Counter-Swing (Opposes Ipsilateral Leg)
        arm_swing_l = math.radians(arm_swing_deg) * math.sin(2.0 * math.pi * t + math.pi)
        arm_swing_r = math.radians(arm_swing_deg) * math.sin(2.0 * math.pi * t)

        if "UpperArm.L" in pb:
            uarm_l = pb["UpperArm.L"]
            uarm_l.rotation_euler.x = arm_swing_l
            uarm_l.keyframe_insert(data_path="rotation_euler", index=0, frame=f)

        if "UpperArm.R" in pb:
            uarm_r = pb["UpperArm.R"]
            uarm_r.rotation_euler.x = arm_swing_r
            uarm_r.keyframe_insert(data_path="rotation_euler", index=0, frame=f)

    act = arm_obj.animation_data.action
    act.name = action_name
    act.use_fake_user = True

    # Set Bezier auto interpolation for smooth cyclical continuity
    fcurves = get_all_action_fcurves(act)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
        if len(fc.keyframe_points) >= 2:
            fc.keyframe_points[0].handle_left_type = 'AUTO'
            fc.keyframe_points[-1].handle_right_type = 'AUTO'

    return act


if __name__ == '__main__':
    print("Testing bp_biped_locomotion.py headless...")
    # 1. Create a dummy armature with required bones
    arm_data = bpy.data.armatures.new("Locomotion_Armature")
    arm_obj = bpy.data.objects.new("Locomotion_Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    for bname in ["Hips", "Chest", "Foot_IK.L", "Foot_IK.R", "UpperArm.L", "UpperArm.R"]:
        b = arm_data.edit_bones.new(bname)
        b.head = (0, 0, 1.0)
        b.tail = (0, 0, 1.2)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Generate Walk Cycle
    act = generate_walk_cycle_action(arm_obj, stride_frames=32, stride_length_m=0.6)
    fcurves = get_all_action_fcurves(act)
    print(f"Generated Walk Action: {act.name} with {len(fcurves)} F-Curves.")
    assert len(fcurves) >= 8, f"Expected >= 8 F-Curves, got {len(fcurves)}"

    # 3. The action must be a slotted 5.2 action bound to this armature.
    assert len(act.layers) == 1 and len(act.layers[0].strips) == 1, "not a slotted action"
    assert len(act.slots) == 1, f"expected 1 action slot, got {len(act.slots)}"
    assert arm_obj.animation_data.action_slot is not None, "action slot not bound to the rig"
    assert len(fcurves) == 12, f"expected 12 F-Curves, got {len(fcurves)}"

    # 4. Verify loop continuity (value at frame 0 must match value at frame T)
    for fc in fcurves:
        val_start = fc.evaluate(0.0)
        val_end = fc.evaluate(32.0)
        assert abs(val_start - val_end) < 1e-4, f"F-Curve {fc.data_path}[{fc.array_index}] does not loop: {val_start} != {val_end}"

    def curve(path, index):
        return next(f for f in fcurves if f.data_path == path and f.array_index == index)

    # 5. Arms swing in exact anti-phase (contralateral swing).
    left_arm = curve('pose.bones["UpperArm.L"].rotation_euler', 0)
    right_arm = curve('pose.bones["UpperArm.R"].rotation_euler', 0)
    arm_err = max(abs(left_arm.evaluate(f) + right_arm.evaluate(f)) for f in range(0, 33))
    assert arm_err < 1e-6, f"arms not anti-phase: max |L+R| = {arm_err}"

    # 6. Pelvis Z bounces at twice the stride frequency: 2 maxima + 2 minima per cycle.
    hips_z = curve('pose.bones["Hips"].location', 2)
    samples = [hips_z.evaluate(f) for f in range(0, 33)]
    maxima = sum(1 for i in range(1, 32) if samples[i] > samples[i - 1] and samples[i] > samples[i + 1])
    minima = sum(1 for i in range(1, 32) if samples[i] < samples[i - 1] and samples[i] < samples[i + 1])
    assert (maxima, minima) == (1, 2), f"bounce frequency wrong: {maxima} interior max, {minima} min"
    assert abs(max(samples) - 0.035) < 1e-4 and abs(min(samples) + 0.035) < 1e-4, "bounce amplitude"

    # 7. Chest counter-rotates against pelvic yaw with k = -0.8.
    hips_yaw = curve('pose.bones["Hips"].rotation_euler', 2)
    chest_yaw = curve('pose.bones["Chest"].rotation_euler', 2)
    ratios = [chest_yaw.evaluate(f) / hips_yaw.evaluate(f)
              for f in range(0, 33) if abs(hips_yaw.evaluate(f)) > 1e-6]
    assert ratios and all(abs(r + 0.8) < 1e-4 for r in ratios), "chest counter-rotation != -0.8"

    print(f"Asserts OK: 12 F-Curves on 1 slot, loop closed, arms anti-phase (err {arm_err:.1e}), "
          "pelvis bounce 2x stride, chest counter-rotation -0.8.")
    print("bp_biped_locomotion verified successfully.")

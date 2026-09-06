# Procedural Mechanical Rigging: Hydraulic Pistons, Drivers & Bendy Bones

Unlike organic characters, mechanical robots, industrial vehicles, and articulated mechanisms obey rigid geometric constraints: pistons must slide coaxially, gears must mesh without slipping, and cables must stretch along tension vectors.

---

## 1. The Hydraulic Piston Rig: Dual Damped Track Architecture

A hydraulic cylinder consists of two interlocking rigid bodies: the **Cylinder Barrel** (outer tube) and the **Piston Rod** (inner shaft).

```
   Cylinder Base Pivot (A)                                    Rod End Pivot (B)
             • ═════════════════════════════════► Track B ◄════ •
             │   Cylinder Barrel              Piston Rod       │
             └──────────────────────┐    ┌─────────────────────┘
                                    │    │
                              Sliding Interface
```

### 1.1 The Classical Rigging Flaw
Novice riggers use `Track To` constraints, which require a secondary Up-vector axis. When the arm swings past the vertical axis, the piston violently snaps $180^\circ$ around its longitudinal axis.

### 1.2 The Production Solution: `Damped Track`
The `DAMPED_TRACK` constraint calculates the shortest arc quaternion rotation from the bone's primary axis to the target point, **completely eliminating roll snapping**:

```python
def setup_hydraulic_piston_pair(armature_obj, cylinder_bone="Cylinder", rod_bone="Rod"):
    """
    Configures a dual Damped Track constraint pair for a hydraulic actuator.
    Cylinder base is at A, tracking toward Rod base at B.
    Rod base is at B, tracking toward Cylinder base at A.
    """
    pbones = armature_obj.pose.bones
    p_cyl = pbones[cylinder_bone]
    p_rod = pbones[rod_bone]
    
    # 1. Cylinder tracks the Rod's head
    con_cyl = p_cyl.constraints.new(type='DAMPED_TRACK')
    con_cyl.target = armature_obj
    con_cyl.subtarget = rod_bone
    con_cyl.track_axis = 'TRACK_Y' # Bone local +Y points from head to tail
    
    # 2. Rod tracks the Cylinder's head
    con_rod = p_rod.constraints.new(type='DAMPED_TRACK')
    con_rod.target = armature_obj
    con_rod.subtarget = cylinder_bone
    con_rod.track_axis = 'TRACK_Y'
```

---

## 2. Programmatic Python Drivers for Mechanical Transmissions

In complex gear trains, planetary drives, or steering linkages, manual keyframing causes drift. Motion must be locked mathematically using **Animation Drivers**.

```
    Motor Input Gear (Driver Source)                  Driven Output Gear (Target)
              ↺ θ_in                                            ↻ θ_out
          [ Z_in Teeth ]           ─────────────►           [ Z_out Teeth ]
                               Driver Formula:
                         θ_out = -θ_in · (Z_in / Z_out)
```

### 2.1 Programmatic Driver Creation in Blender 5.2
To couple the Y-axis rotation of a driven gear to a driving motor shaft:

```python
def add_gear_ratio_driver(armature_obj, driver_bone="Motor_Shaft", driven_bone="Planet_Gear", ratio=0.25):
    """Couples rotation of driven_bone to driver_bone via an exact mathematical driver."""
    p_driven = armature_obj.pose.bones[driven_bone]
    
    # Add driver to Rotation Euler Y channel (index 1)
    # If using Quaternions, use Euler for simple rotational gearing
    p_driven.rotation_mode = 'XYZ'
    driver = p_driven.driver_add("rotation_euler", 1).driver
    
    driver.type = 'SCRIPTED'
    
    # Create variable reading Driver bone's Y rotation
    var = driver.variables.new()
    var.name = "rot_in"
    var.type = 'TRANSFORMS'
    
    target = var.targets[0]
    target.id = armature_obj
    target.bone_target = driver_bone
    target.transform_type = 'ROT_Y'
    target.transform_space = 'LOCAL_SPACE'
    
    # Set exact kinematic formula (e.g. reverse rotation with gear ratio)
    driver.expression = f"-rot_in * {ratio}"
```

---

## 3. Tendon & Cable Rigging: `Stretch To` Constraints

For robotics cable transmissions or synthetic tendon cords:
*   A bone's tail must stretch elastically to pin itself to an end-effector anchor while preserving its cross-sectional volume or maintaining constant thickness:

```python
def setup_cable_tendon(armature_obj, tendon_bone="Tendon.01", anchor_bone="Finger_Tip"):
    """Configures a bone to stretch dynamically between two points."""
    p_tendon = armature_obj.pose.bones[tendon_bone]
    
    con = p_tendon.constraints.new(type='STRETCH_TO')
    con.target = armature_obj
    con.subtarget = anchor_bone
    # 'NO_VOLUME' preserves cable thickness; 'VOLUME_XZ' mimics elastic rubber
    con.volume = 'NO_VOLUME'
    con.rest_length = (p_tendon.tail - p_tendon.head).length
```

---

## 4. Bendy Bones (B-Bones) & Cubic Spline Interpolation

Standard bones deform geometry as rigid linear segments. **Bendy Bones (B-Bones)** subdivide a single bone into $N$ micro-segments curved along a 3D **cubic Hermite spline**:

```
        Standard Linear Bone                     B-Bone (16 Subdivisions)
       ┌─────────────────────┐                 ╭─────────────────────────╮
       │                     │       ════►    (   Smooth Organic Curve    )
       └─────────────────────┘                 ╰─────────────────────────╯
       Rigid linear segment                     Curved cubic Hermite spline!
```

### 4.1 Curvature Mathematics
The spine of a B-Bone is interpolated between `head` and `tail` tangent vectors using cubic polynomial blending:
$$\mathbf{p}(u) = (2u^3 - 3u^2 + 1)\mathbf{p}_0 + (u^3 - 2u^2 + u)\mathbf{m}_0 + (-2u^3 + 3u^2)\mathbf{p}_1 + (u^3 - u^2)\mathbf{m}_1$$
Where:
*   $\mathbf{p}_0, \mathbf{p}_1$: Head and tail positions.
*   $\mathbf{m}_0, \mathbf{m}_1$: Tangent vectors driven by the parent bone orientation and next-child bone orientation.
*   *Blender 5.2 B-Bone Properties:*
    *   `bbone_segments`: Number of spline subdivisions ($8\text{ to }16$ for flexible rubber hoses, cables, and robot tentacles).
    *   `bbone_easein`, `bbone_easeout`: Adjusts tangent acceleration curves.
    *   `bbone_custom_handle_start`, `bbone_custom_handle_end`: Explicitly targets other bones as curve tangent handles.

---

## 5. References & Standards

1.  **Parent, R. (2012).** *Computer Animation: Algorithms and Techniques* (3rd ed.). Morgan Kaufmann. (Constraint systems, damping algorithms, and transformation matrices).
2.  **Blender Foundation. (2024).** *Blender Documentation: Pose Bone Constraints & Drivers.* https://docs.blender.org/manual/en/latest/animation/armatures/posing/bone_constraints/
3.  **Farin, G. (2002).** *Curves and Surfaces for CAGD: A Practical Guide* (5th ed.). Morgan Kaufmann. (Hermite cubic splines and B-spline tangent interpolation for B-Bones).
4.  **Maestri, G. (1999).** *Digital Character Animation 2: Advanced Techniques.* New Riders. (Piston rigging, mechanical inverse kinematics, and cable routing principles).

# Arm V2 — natural work sequence

Main artifact: **`videos/arm-v2-natural-tasks.mp4`**, 30 seconds at24fps,960×720, **without subtitles or overlays**, following the user's final direction. Editable scene: **`arm-v2-task-demo.blend` → `ARM2-Task-demo`**. The user asked for purposeful work that also reveals flexibility, replacing the isolated joint exercise as the main presentation.

## What the robot does

1. Approaches the blue workpiece, closes the gripper on its tab and lifts it clear.
2. Reaches upright and rotates the wrist to present the part for inspection.
3. Turns toward the rear station, lowers the part, releases and withdraws.
4. Picks the orange workpiece from the other source station, transfers it and stacks it on the blue part.
5. Opens the gripper, withdraws and folds into its parked pose.

All six joints animate through their actual mesh hierarchy. The base and camera stay fixed. Quintic easing joins authored waypoints. Workpieces follow the hand only during their carrying intervals; before pickup and after release they remain at their station. This attachment is an animation constraint represented by keyed transforms, **not a force/friction simulation**.

## Grasp and scene geometry

Each purpose-designed workpiece has a20×28×8mm gripping tab, connecting neck, and a30×28×24mm body beyond the fingertips. This keeps rigid material clear of the tapered jaws while making the task and final stack visible. This demonstration does **not** establish that the current hand can grip an arbitrary20mm cube.

The grip datum is(14.48,24,76)mm in the gripper-fixed frame, at the upper part of the72mm TPU pad. Pickup and placement targets come from an analytical side-grasp solution that includes the12mm wrist offset. Supports are elevated to suit this continuous wrist range; no unsupported top-down tabletop grasp is depicted.

Robot geometry matches the prior flexibility revision. Only the task scene, workpieces, stands, animation and camera presentation are added. The previous baseline and flexibility files remain separate. [FLEXIBILITY.md](FLEXIBILITY.md) records the robot's clearance revisions and their limitations.

## Verification and limits

- `reports/task-path-check.json`: all720 actual keyed poses screened for cross-group triangle intersections, including the moving workpieces and supports. Only internal servo/output proxies, same-rigid-group pairs and workpiece/TPU72 contact are excluded. This does not prove continuous swept clearance, solid containment or physical compliance.
- `reports/task-presentation-check.json`: actual joint-angle agreement, camera margins, held-object transform agreement, final stack gap and support gap. Numerical registration is not manufacturing tolerance.
- `reports/independent-task-demo-review.md`: independent saved-file and visual review. `reports/task-video-check.json` records the final encoded-video checks.

**This is a task animation, not a250g loaded-operation validation.** The existing wrist torque deficit, small shoulder margin, unverified cable travel, exact adapters/thread depths, revised bridge strength and multi-minute thermal tests remain open. The movie's timing is not a servo command program. These scene props are not a rated payload test or an object-recognition implementation.

## Reproduce

Open `arm-v2-flexibility.blend`, run `create-task-scene.py`, and save separately as `arm-v2-task-demo.blend`. This loads `task-motion-plan.py`, `task-props.py` and `task-camera.py`. Run `check-task-path.py` and `verify-task-presentation.py` before `render-task-demo.py`. The final render uses Cycles,6samples and denoising at960×720. Encode the raw `videos/task-frames/frame-%04d.png` images as H.264/yuv420p at24fps. The caption script and captioned preview are superseded and are not used for the delivered movie.

The older diagnostic scene still contains a40second joint-range animation, but its full video render was stopped when the user requested this natural task presentation. Only `videos/flexibility-first-10-seconds.mp4` is an encoded preview of that earlier exercise.

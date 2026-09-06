# Brainstorm Contract: Robotics & Precision Mechanical CAD Suite

**Date:** 2026-09-05  
**Topic:** Precision Mechanical Engineering, Robotics Hardware Design, CAD Standards, and Blender-to-Physics Workflow Integration  
**Framework:** `ak:brainstorm` contract (Outcome, Constraints, Non-goals, Acceptance criteria)

---

## 1. Outcome
A permanent, comprehensive engineering knowledge base and executable toolkit stored directly in the repository to power future AI agent skills and automated workflows for precision 3D mechanical and robotics design.

Specifically, it delivers:
1. **Authoritative Engineering Foundations:** Rigorous syntheses covering kinematics, dynamics, actuator sizing, bearing systems, exact constraint design (kinematic mounts, Abbe principle), ISO/ASME GD&T, and DFMA (CNC, 3D printing, sheet metal).
2. **CAD-to-Mesh Bridge:** Definitive guidelines distinguishing analytical B-Rep geometry (STEP, IGES, Parasolid) from polygonal mesh geometry (Blender, SubD, vertex attributes), with precise tolerances for tessellation and non-destructive modeling.
3. **Robotics Simulation Pipeline:** Industry-standard representations (ROS REP 103/120, URDF, SDF, MuJoCo MJCF), visual vs. collision mesh separation, coordinate frame alignment, and physical properties calculation.
4. **Agent-Loadable KB Modules:** Ready-to-load 8-section guides in `knowledge/70-cad-precision-robotics/` indexed in `knowledge/INDEX.md`.
5. **Headless Verification Tools:** Python script (`scripts/compute-mesh-inertia.py`) using the Mirtich-Eberly algorithm to compute volume, mass, Center of Mass (CoM), and full $3 \times 3$ inertia tensor directly from Blender meshes.

---

## 2. Constraints
1. **Software Versions:** Built against Blender 5.2 LTS (`/Applications/Blender.app/Contents/MacOS/Blender`), Python 3.11+, and ROS REP 103 standards.
2. **Execution Integrity:** Follow the repository's binding rules in `.project-agent.md`: prefer Blender Data API and bmesh over `bpy.ops`; zero flaky context dependencies.
3. **Mathematical Rigor:** No hand-waving or vague approximations. All formulas (inertia integrals, Abbe offset, gear ratios, tolerance stacks, K-factors) must be mathematically sound.
4. **Native Asset Policy:** All workflows must be reproducible natively in Blender or using local, open-source programmatic CAD (e.g., CadQuery, build123d, OpenCASCADE) without closed, hosted vendor model dependencies.
5. **Structure Consistency:** Knowledge base modules must strictly follow the repository's 8-section architecture (`Mental model`, `Decision first`, `Rules`, `Recipes`, `Anti-patterns`, `Verification ladder`, `Production edge cases`, `Next steps`).

---

## 3. Non-Goals
1. **Immediate Physical Fabrication:** We are establishing the digital design intelligence, geometric rules, and verification pipelines; physical CNC milling or hardware procurement is outside this scope.
2. **Full CAD Kernel Re-implementation:** Blender is a polygonal mesh modeler; we do not attempt to write a native B-Rep NURBS geometric modeling kernel inside Blender, but rather bridge parametric CAD solvers (CAD Sketcher, OpenCASCADE) and exact bmesh modeling.
3. **Monolithic Humanoid Assembly in Turn 1:** The goal is creating the foundational knowledge, standards, and tools first, which will then be used to generate specific robotic mechanisms in subsequent sessions.

---

## 4. Acceptance Criteria
1. **Completeness:** All 5 core research modules authored with detailed specifications, tables, and equations:
   - `01-MECHANICAL-ROBOTICS-FUNDAMENTALS.md`
   - `02-PRECISION-ENGINEERING-GDT.md`
   - `03-DFMA-STANDARDS.md`
   - `04-CAD-VS-POLY-BLENDER-BRIDGE.md`
   - `05-ROBOTICS-SIMULATION-PIPELINE.md`
2. **KB Integration:** `knowledge/70-cad-precision-robotics/` populated with:
   - `cad-precision-modeling.md`
   - `robotics-urdf-mechanisms.md`
   - `knowledge/INDEX.md` updated with the new domain.
3. **Executable Sense Organ:** `scripts/compute-mesh-inertia.py` implemented and verified headless against Blender primitives (analytical comparison).
4. **Actionability:** Clear roadmap defining how future skills (`blender-cad-precision`, `robotics-urdf-rigging`) consume this knowledge base.

---
id: cad-step-roundtrip-and-dfm
name: cad-step-roundtrip-and-dfm
title: "CAD STEP Round-Trip, Hybrid Parametric Batch Editing & DFM Zero-Collision Pipeline"
category: 70-cad-precision-robotics
domain: "cad_precision_robotics"
description: "Ingest Fusion 360 and SolidWorks STEP assemblies with ISO-10303-21 Vietnamese Unicode decoding, lock 1:1 B-Rep geometry while batch-editing named hardware parts, enforce DFM butt-weld and CNC slot clearances, and export multi-body STEP compounds."
when: ["step-import", "step-export", "fusion-360", "3d-edit", "butt-weld", "cnc-slot", "dfm-collision"]
loads_with: ["cad-precision-modeling", "export-interchange", "fasteners-seals-mechanics"]
tags: ["step", "cad", "build123d", "opencascade", "fusion360", "dfm", "butt-weld", "cnc-plywood", "multi-body"]
trust_tier: "verified"
version: "1.0.0"
source_attribution:
  - uri: "scripts/boilerplates/bp_cad_step_roundtrip.py"
    sha256: "9c0cf9430306380766a769aa6841a7da79786eac38600e6e118d5a3c017e8267"
---

# CAD STEP Round-Trip, Hybrid Parametric Batch Editing & DFM Zero-Collision Pipeline

## Purpose

Provide a verified, production-grade CAD ingestion and round-trip pipeline between mechanical CAD software (Autodesk Fusion 360, SolidWorks, Siemens NX) and Blender 5.2 LTS. The pipeline guarantees 100% geometry preservation (zero uncommanded re-extrusion), decodes ISO-10303-21 hexadecimal Vietnamese Unicode part identifiers, automates assembly collection hierarchies, enables parametric batch scaling of fastener components, verifies DFM zero-collision and coplanar butt-weld interfaces, and exports clean multi-body STEP compounds without Browser clutter.

## When to Use / When NOT

### ALLOWED (When to Use)
- When ingesting multi-solid STEP assemblies (`.step` / `.stp`) originating from Autodesk Fusion 360 or SolidWorks with encoded Vietnamese Unicode names (`\X2\...\X0\` or `\X\...`).
- When hardware fasteners (socket head cap screws, bolts, hex nuts, washers) need parametric resizing across large assemblies while locking all primary structural profiles and CNC panels.
- When performing automated DFM clearance audits to enforce zero volume collision ($V_{\text{intersect}} == 0.000\text{ mm}^3$) and coplanar butt-weld flush contacts ($\le 10^{-4}\text{ m}$) before manufacturing or rendering.
- When packaging multiple Blender meshes into single-container STEP multi-body assemblies grouped as `TopoDS_Compound` wrapped in `Part` entities.

### NOT ALLOWED (When NOT to Use)
- Do not use for organic high-poly sculpt retopology or character mesh decimation (use `bp_organic_scaffold_splitter.py` or native Remesh modifiers).
- Do not manually re-extrude or redraw 2D profiles of standard CAD components (e.g. T-slot aluminum extrusions, bearings, bolts); always preserve original B-Rep geometry.
- Do not use for lighting setup or camera framing passes (delegate to `bp_studio_catalogue_render.py`).

## Core Knowledge Content

### 1. ISO-10303-21 Vietnamese Unicode String Decoding

Observed: Autodesk Fusion 360 and SolidWorks encode international character strings in STEP file entity attributes using ISO-10303-21 encoding. Two-byte characters (such as accented Vietnamese characters) are formatted as `\X2\<HEX4>\X0\`, while single-byte Latin extensions use `\X\<HEX2>`.

```python
def decode_step_string(s: str) -> str:
```
<!-- ease:source uri="scripts/boilerplates/bp_cad_step_roundtrip.py" sha256="9c0cf9430306380766a769aa6841a7da79786eac38600e6e118d5a3c017e8267" quote="def decode_step_string(s: str) -> str:" -->

Decision: The string decoder unpacks each 4-hex-digit sequence into a 16-bit Unicode codepoint via `chr(int(chunk, 16))`. Testing confirms that input `"\\X2\\004D1EB70074\\X0\\_B\\X2\\00E0\\X0\\n_Plywood"` decodes deterministically to `"Mặt_Bàn_Plywood"`, and `"\\X2\\1ED00063\\X0\\_L\\X2\\1EE5\\X0\\c_Gi\\X2\\00E1\\X0\\c_M8"` decodes to `"Ốc_Lục_Giác_M8"`.

### 2. Hierarchical CAD Assembly Collection Organization

Derived: When importing CAD assemblies containing dozens of discrete components, placing all objects into the root Scene Collection causes navigational clutter and breaks batch modifier operations. The assembly must be structured into dedicated functional sub-collections.

```python
def build_hierarchical_cad_assembly(
```
<!-- ease:source uri="scripts/boilerplates/bp_cad_step_roundtrip.py" sha256="9c0cf9430306380766a769aa6841a7da79786eac38600e6e118d5a3c017e8267" quote="def build_hierarchical_cad_assembly(" -->

Decision: Organize assemblies into a two-tier hierarchy under `01_Assembly_Main`: `Comp_Primary_Structure` (structural columns, main frames), `Comp_Framing_Profiles` (aluminum T-slot extrusions, tubular stretchers), `Comp_Hardware_Fasteners` (bolts, nuts, screws), and `Comp_Panels` (plywood tabletops, sheet metal covers). A separate `00_CAD_Reference` collection retains locked reference copies.

### 3. Parametric Batch Editing of Fasteners (Solving Case 1)

Observed: In engineering design revisions (e.g. Case 1), bolt sizes frequently change (e.g. from M8 to M10) across assemblies containing dozens of instances. Manually selecting and editing each fastener risks accidental displacement or distortion of mating T-slot profiles.

```python
def batch_edit_parts_by_pattern(
```
<!-- ease:source uri="scripts/boilerplates/bp_cad_step_roundtrip.py" sha256="9c0cf9430306380766a769aa6841a7da79786eac38600e6e118d5a3c017e8267" quote="def batch_edit_parts_by_pattern(" -->

Decision: Apply pattern-matched parametric editing (`fnmatch.fnmatch(obj.name, "Ốc_Lục_Giác*")`). When resizing M8 to M10 fasteners, apply a scale transformation of `(1.25, 1.25, 1.0)` directly to the mesh data coordinates via `obj.data.transform()`, maintaining object transform scale at unity `(1.0, 1.0, 1.0)` to preserve modifier stability.

### 4. DFM Zero-Collision and Coplanar Butt-Weld Verification

Derived: Physical manufacturability requires that mating solid components never penetrate each other in 3D space ($V_{\text{intersect}} == 0.000\text{ mm}^3$). Furthermore, welded frame members and tabletop-to-leg interfaces must meet at coplanar flush boundaries with tangential deviation $\le 10^{-4}\text{ m}$ ($0.1\text{ mm}$).

```python
def audit_dfm_zero_collision_and_butt_weld(
```
<!-- ease:source uri="scripts/boilerplates/bp_cad_step_roundtrip.py" sha256="9c0cf9430306380766a769aa6841a7da79786eac38600e6e118d5a3c017e8267" quote="def audit_dfm_zero_collision_and_butt_weld(" -->

Decision: Audit all pairwise interactions using world-space bounding box overlap checks followed by evaluated exact boolean intersection volume computation. For flush coplanar contacts (such as leg top faces mating with tabletop underside at $Z = 0.720\text{ m}$), verify that overlap volume evaluates to exactly $0.000\text{ mm}^3$ and record coplanar contact count.

## Failure Modes (Mandatory)

1. **`MANIFOLD_SOLID_BREP` regex index drift on multi-instance XCAF STEP files**:
   - *Cause*: Parsing STEP files by regular expression indexing of `MANIFOLD_SOLID_BREP` assumes a 1:1 sequential alignment between names and solid bodies. In multi-instance or nested sub-assembly files, OpenCASCADE's XCAF tree traverses components in document graph order, causing names to drift from their corresponding geometry.
   - *Prevention*: When OpenCASCADE / `build123d` is available, read entity labels directly from `TDataStd_Name` attributes attached to each `TDF_Label` in the XCAF shape tool rather than relying on sequential regex string matching.

2. **Re-extruding CAD T-slot profiles instead of locking 1:1 B-Rep geometry**:
   - *Cause*: Agents attempting to "clean up" or "lighten" imported CAD geometry often select an end face of an aluminum profile and extrude it along an axis, or regenerate a 3030 profile procedurally. This destroys micron-accurate internal screw bosses, center holes, and T-slot undercut lip geometry.
   - *Prevention*: Enforce strict 1:1 B-Rep mesh lockdown. Structural members must retain their analytical mesh boundaries. Only rigid transformations (translation and rotation) or designated parametric scale operations on hardware fasteners are permitted.

3. **Exporting ungrouped solids to STEP causing Fusion 360 Browser clutter instead of `TopoDS_Compound` -> `Part`**:
   - *Cause*: Exporting individual `Solid` instances directly into the top-level assembly compound causes CAD tools (Fusion 360, SolidWorks) to instantiate each solid as an independent root-level component, producing dozens or hundreds of unorganized browser entries.
   - *Prevention*: Group related solids into a `TopoDS_Compound` using `BRep_Builder().MakeCompound(comp)` and wrap them in a single `build123d.Part(comp)` entity. This ensures Fusion 360 represents the group as one clean Component containing an internal `Bodies` folder.

4. **Overlapping butt-weld tubes ($V_{\text{intersect}} > 0$) instead of coplanar trim**:
   - *Cause*: Placing structural stretcher tubes or crossbars spanning between table legs by centering their endpoints on leg centerlines results in physical penetration equal to the tube cross-section.
   - *Prevention*: Always trim tube endpoints flush at the exterior boundary face of the receiving profile ($z_{\text{top}} = z_{\text{mating\_face}}$). Enforce automated pre-export validation with `audit_dfm_zero_collision_and_butt_weld`, failing any build where $V_{\text{intersect}} > 0.000\text{ mm}^3$.

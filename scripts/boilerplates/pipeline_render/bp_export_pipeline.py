"""
bp_export_pipeline.py — Headless Interchange & Export Pipeline Boilerplate.

Standards & Academic Citations:
- ISO/IEC 12113:2022: "Information technology — glTF 2.0 specification."
- ISO/ASTM 52915:2020: "Specification for Additive Manufacturing File Format (AMF / 3MF / STL)."
- Blender Foundation (2026): "Blender 5.2 Python API: bpy.ops.export_scene.gltf, bpy.ops.wm.stl_export."

Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
import os
from typing import Optional


def export_gltf_pbr(
    filepath: str,
    export_selected: bool = False,
    apply_modifiers: bool = True
) -> bool:
    """
    Exports scene or selected objects to standard glTF 2.0 (.glb) with PBR materials.
    """
    res = bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=export_selected,
        export_apply=apply_modifiers,
        export_yup=True
    )
    return 'FINISHED' in res


def export_binary_stl(
    filepath: str,
    export_selected: bool = True,
    apply_modifiers: bool = True
) -> bool:
    """
    Exports 3D printable watertight geometry to binary STL.
    Blender 5.2 uses the high-performance C++ wm.stl_export operator.
    """
    res = bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=export_selected,
        apply_modifiers=apply_modifiers,
        ascii_format=False
    )
    return 'FINISHED' in res


if __name__ == '__main__':
    print("Testing bp_export_pipeline.py headless...")
    
    # Create test cube
    bpy.ops.mesh.primitive_cube_add(size=0.05)
    cube = bpy.context.active_object
    
    tmp_glb = "/tmp/test_export_52.glb"
    tmp_stl = "/tmp/test_export_52.stl"

    gltf_ok = export_gltf_pbr(tmp_glb, export_selected=True)
    stl_ok = export_binary_stl(tmp_stl, export_selected=True)

    print(f"glTF Export: {gltf_ok} ({os.path.getsize(tmp_glb)} bytes)")
    print(f"STL Export: {stl_ok} ({os.path.getsize(tmp_stl)} bytes)")

    assert gltf_ok and os.path.exists(tmp_glb)
    assert stl_ok and os.path.exists(tmp_stl)

    # Cleanup temp files
    if os.path.exists(tmp_glb): os.remove(tmp_glb)
    if os.path.exists(tmp_stl): os.remove(tmp_stl)

    print("bp_export_pipeline verified successfully.")

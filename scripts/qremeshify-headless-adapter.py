"""Headless, hash-pinned QRemeshify adapter for local Blender mesh salvage."""
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import bmesh
import bpy

EXPECTED_LIBRARIES = {
    "liblib_quadpatches.dylib": "d674b048681e381a3363931bfa5736c08b0c2978c4b8c2482781ef33981aaef0",
    "liblib_quadwild.dylib": "0223c656de8b5497e8731caf5b8c1f586550ff7ead3b99d7e5efe03600c6b29e",
}


def log(stage, **details):
    print("QREMESHIFY_STAGE " + json.dumps(
        {"stage": stage, **details}, sort_keys=True), flush=True)


def load_qremeshify():
    addon = Path(os.environ.get("QREMESHIFY_PATH", "/Users/jang/Downloads/QRemeshify"))
    assert (addon / "blender_manifest.toml").is_file(), addon
    for name, expected in EXPECTED_LIBRARIES.items():
        library = addon / "lib" / name
        digest = hashlib.sha256(library.read_bytes()).hexdigest()
        assert digest == expected, f"unverified QRemeshify binary: {name}"
        quarantine = subprocess.run(
            ["xattr", "-p", "com.apple.quarantine", str(library)],
            capture_output=True, check=False).returncode == 0
        if quarantine:
            raise RuntimeError(
                f"macOS quarantined QRemeshify binary: {library}")
    sys.path.insert(0, str(addon.parent))
    package = importlib.import_module(addon.name)
    assert package.bl_info["version"] == (1, 1, 0), package.bl_info
    return package, importlib.import_module(f"{addon.name}.lib"), addon


def triangle_count(mesh):
    return sum(len(poly.vertices) - 2 for poly in mesh.polygons)


def input_bmesh(obj, target_tris):
    base_tris = triangle_count(obj.data)
    if base_tris > target_tris:
        raise RuntimeError(
            f"input has {base_tris} tris; preflight budget is {target_tris}")
    log("input-copy", source_tris=base_tris, target_tris=target_tris)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    transform = obj.matrix_basis.copy()
    transform.translation = (0.0, 0.0, 0.0)
    bmesh.ops.transform(bm, matrix=transform, verts=list(bm.verts))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method="SHORT_EDGE",
                          ngon_method="BEAUTY")
    log("input-ready", faces=len(bm.faces))
    return bm, base_tris


def mark_features(bm, angle_degrees):
    threshold = math.radians(angle_degrees)
    for edge in bm.edges:
        edge.smooth = not (edge.is_boundary or edge.calc_face_angle(0.0) > threshold)


def close_output_holes(mesh, symmetry_x):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    boundary = [edge for edge in bm.edges if edge.is_boundary]
    fill_edges = [edge for edge in boundary if not (
        symmetry_x and all(abs(vert.co.x) < 1e-5 for vert in edge.verts))]
    result = bmesh.ops.holes_fill(bm, edges=fill_edges, sides=0) if fill_edges else {}
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-10)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    remaining = sum(edge.is_boundary and not (
        symmetry_x and all(abs(vert.co.x) < 1e-5 for vert in edge.verts))
                    for edge in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return len(result.get("faces", [])), remaining


def run_pipeline(obj, qlib, addon, target_tris, density, symmetry_x):
    exporter = importlib.import_module(f"{addon.name}.util.exporter")
    importer = importlib.import_module(f"{addon.name}.util.importer")
    bisect = importlib.import_module(f"{addon.name}.util.bisect")
    bm, source_tris = input_bmesh(obj, target_tris)
    if symmetry_x:
        log("bisect", axis="X")
        bisect.bisect_on_axes(bm, True, False, False)
        log("bisect-complete", faces=len(bm.faces))
    sharp_angle = float(os.environ.get("QREMESHIFY_SHARP_ANGLE", "35"))
    enable_sharp = os.environ.get("QREMESHIFY_ENABLE_SHARP", "1") == "1"
    if enable_sharp:
        mark_features(bm, sharp_angle)
    temp_prefix = f"qremeshify-{os.getpid()}-{obj.name}"
    mesh_path = Path(bpy.app.tempdir) / f"{temp_prefix}.obj"
    quadwild = qlib.Quadwild(str(mesh_path))
    start = time.monotonic()
    log("export", path=str(mesh_path))
    exporter.export_mesh(bm, str(mesh_path))
    log("export-complete", bytes=mesh_path.stat().st_size)
    input_faces = len(bm.faces)
    sharp_features = (exporter.export_sharp_features(
        bm, quadwild.sharp_path, sharp_angle) if enable_sharp else 0)
    bm.free()
    preprocess = os.environ.get("QREMESHIFY_PREPROCESS", "1") == "1"
    log("field", enable_sharp=enable_sharp, input_faces=input_faces,
        preprocess=preprocess, sharp_features=sharp_features)
    quadwild.remeshAndField(remesh=preprocess, enableSharp=enable_sharp,
                            sharpAngle=sharp_angle)
    assert Path(quadwild.remeshed_path).is_file(), "remesh stage produced no mesh"
    log("trace")
    assert quadwild.trace(), "trace stage failed"
    time_limit = int(os.environ.get("QREMESHIFY_TIME_LIMIT", "120"))
    log("quadrangulate", density=density, time_limit=time_limit)
    result_code = quadwild.quadrangulate(
        True, density, 0, 0.005, "LEASTSQUARES", time_limit, 0.0, 0.4,
        True, True, True, 0.9, True, 0.1, True, False, False, True, True,
        "SIMPLE", "DEFAULT", [3, 5, 10, 20, 30, 60, 90, 120],
        [0.005, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    final_path = Path(quadwild.output_smoothed_path)
    assert final_path.is_file(), f"quadrangulation failed: {result_code}"
    log("import", result_code=result_code)
    mesh = importer.import_mesh(str(final_path))
    closed_hole_faces, remaining_boundaries = close_output_holes(
        mesh, symmetry_x)
    output = bpy.data.objects.new("drone-silhouette-qremesh", mesh)
    obj.users_collection[0].objects.link(output)
    output.location = obj.location
    if obj.data.materials:
        output.data.materials.append(obj.data.materials[0])
    output.data.shade_smooth()
    if symmetry_x:
        mirror = output.modifiers.new("qremeshify-symmetry", "MIRROR")
        mirror.use_axis[0] = True
        mirror.use_clip = True
        mirror.merge_threshold = 0.001
    output["qremeshify-version"] = "1.1.0"
    output["qremeshify-density"] = density
    output["qremeshify-input-target-tris"] = target_tris
    obj.hide_render = True
    obj.hide_set(True)
    elapsed = round(time.monotonic() - start, 3)
    for candidate in mesh_path.parent.glob(f"{temp_prefix}*"):
        candidate.unlink(missing_ok=True)
    stats = {"elapsed_seconds": elapsed, "input_faces": input_faces,
             "closed_hole_faces": closed_hole_faces,
             "output_faces": len(mesh.polygons), "output_tris": triangle_count(mesh),
             "quad_ratio": round(sum(len(p.vertices) == 4 for p in mesh.polygons) /
                                 max(len(mesh.polygons), 1), 6),
             "result_code": result_code, "sharp_features": sharp_features,
             "remaining_non_seam_boundaries": remaining_boundaries,
             "source_tris": source_tris}
    return output, stats


def main():
    package, qlib, addon = load_qremeshify()
    obj = bpy.data.objects[os.environ.get(
        "QREMESHIFY_OBJECT", "drone-silhouette-repaired")]
    log("preflight", object=obj.name)
    output, stats = run_pipeline(
        obj, qlib, addon,
        int(os.environ.get("QREMESHIFY_TARGET_TRIS", "60000")),
        float(os.environ.get("QREMESHIFY_DENSITY", "1.0")),
        os.environ.get("QREMESHIFY_SYMMETRY_X", "1") == "1")
    output["qremeshify-stats"] = json.dumps(stats, sort_keys=True)
    bpy.context.scene["retopology-tool"] = "QRemeshify 1.1.0 local GPL-3.0-or-later"
    bpy.context.scene["external-service-calls"] = 0
    destination = Path(os.environ.get(
        "QREMESHIFY_OUTPUT", str(Path(bpy.data.filepath).with_name(
            "fpv-drone-qremesh-experiment.blend"))))
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    print("QREMESHIFY_OK " + json.dumps({"addon": str(addon),
                                          "blend": str(destination),
                                          "object": output.name,
                                          **stats}, sort_keys=True))


if __name__ == "__main__":
    main()

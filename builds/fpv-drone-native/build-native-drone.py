"""Deterministic native Blender rebuild of the FPV drone reference."""
import json
import os
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
OUTPUT = PROJECT / "output" / "drone-native"
BLEND = ROOT / "fpv-drone-native.blend"


def load(name):
    return runpy.run_path(str(ROOT / name))


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                       bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def collections():
    result = {}
    for name in ("DRONE_HERO", "DRONE_PARTS", "CAMERAS", "LIGHTS", "STUDIO"):
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        result[name] = collection
    return result


def build():
    assert bpy.app.version >= (5, 2, 0), bpy.app.version
    clear_scene()
    lib = load("drone-mesh-library.py")
    frame_module = load("drone-frame-geometry.py")
    detail_module = load("drone-detail-components.py")
    presentation = load("drone-presentation.py")
    cols = collections()
    mats = {
        "body-clay": presentation["material"](
            "MAT-Body-Clay", (0.38, 0.41, 0.45), 0.38),
        "mechanical-grey": presentation["material"](
            "MAT-Mechanical-Grey", (0.17, 0.19, 0.21), 0.30, 0.12),
        "prop-blade": presentation["material"](
            "MAT-Prop-Blade", (0.32, 0.34, 0.37), 0.34),
        "lens-dark": presentation["material"](
            "MAT-Lens-Dark", (0.008, 0.012, 0.018), 0.10, 0.15),
        "studio-white": presentation["material"](
            "MAT-Studio-White", (0.24, 0.24, 0.24), 0.72),
    }
    frame = frame_module["build_frame"](lib, cols, mats)
    detail_module["build_details"](lib, cols, mats, frame)
    root = bpy.data.objects.new("drone-asset-root", None)
    cols["DRONE_HERO"].objects.link(root)
    for collection_name in ("DRONE_HERO", "DRONE_PARTS"):
        for obj in cols[collection_name].objects:
            if obj is not root:
                obj.parent = root
    presentation["setup_presentation"](lib, cols, mats, False)
    bpy.context.scene["asset-source"] = "native-blender-no-vendor"
    bpy.context.scene["reference-count"] = 2
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    return cols


def render(view):
    scene = bpy.context.scene
    camera_name = {
        "hero": "CAM-Drone-Hero", "top": "CAM-Drone-Top",
        "opposite": "CAM-Drone-Opposite", "underside": "CAM-Drone-Underside",
    }[view]
    scene.camera = bpy.data.objects[camera_name]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pass_name = os.environ.get("DRONE_PASS", "native-pass-1")
    scene.render.filepath = str(OUTPUT / f"{pass_name}-{view}.png")
    saved = (scene.render.resolution_x, scene.render.resolution_y,
             scene.cycles.samples)
    if os.environ.get("DRONE_PREVIEW", "1") == "1":
        width = int(os.environ.get("DRONE_PREVIEW_WIDTH", "960"))
        scene.render.resolution_x = width
        scene.render.resolution_y = round(width * 9 / 16)
        scene.cycles.samples = int(os.environ.get("DRONE_PREVIEW_SAMPLES", "32"))
    result = bpy.ops.render.render(write_still=True)
    scene.render.resolution_x, scene.render.resolution_y, scene.cycles.samples = saved
    assert result == {"FINISHED"}, result
    return scene.render.filepath


if __name__ == "__main__":
    cols = build()
    output = None
    if os.environ.get("DRONE_RENDER", "1") == "1":
        output = render(os.environ.get("DRONE_VIEW", "hero"))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    print("AGENT_OK " + json.dumps({
        "blend": str(BLEND), "render": output, "meshes": len(meshes),
        "hero": len(cols["DRONE_HERO"].objects),
        "parts": len(cols["DRONE_PARTS"].objects),
        "source": bpy.context.scene["asset-source"],
    }, sort_keys=True))

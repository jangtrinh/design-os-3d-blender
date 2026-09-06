"""Render a controlled QRemeshify candidate view without mutating the blend."""
import json
import os
from pathlib import Path

import bpy


def main():
    view = os.environ.get("QREMESHIFY_VIEW", "hero")
    camera_name = {"hero": "CAM-Drone-Hero", "top": "CAM-Drone-Top",
                   "opposite": "CAM-Drone-Opposite",
                   "underside": "CAM-Drone-Underside"}[view]
    output = Path(os.environ["QREMESHIFY_RENDER_OUTPUT"])
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.camera = bpy.data.objects[camera_name]
    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(os.environ.get("QREMESHIFY_RENDER_SAMPLES", "16"))
    scene.cycles.use_denoising = True
    scene.render.resolution_x = int(os.environ.get("QREMESHIFY_RENDER_WIDTH", "960"))
    scene.render.resolution_y = round(scene.render.resolution_x * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
    print("QREMESHIFY_RENDER_OK " + json.dumps(
        {"camera": camera_name, "output": str(output), "view": view},
        sort_keys=True))


if __name__ == "__main__":
    main()

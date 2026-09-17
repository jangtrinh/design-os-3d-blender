"""Bounded Blender 5.2 Metal/full-HD renderer probe on immutable geometry-B01."""
from __future__ import annotations

import json
import platform
import socket
import sys
import time
from pathlib import Path

import bpy


BUILD = Path(__file__).resolve().parents[1]
ROOT = BUILD.parents[1]
SOURCE = BUILD / "runs/geometry-B01/steps/geometry/attempt-0001/model.blend"
OUT = BUILD / "runs/render-device-probe-B01"

assert Path.cwd().resolve() == ROOT.resolve(), (Path.cwd(), ROOT)
assert socket.gethostname() == "jangtrinhs-MacBook-Pro-2.local", socket.gethostname()
assert Path(bpy.data.filepath).resolve() == SOURCE.resolve(), (bpy.data.filepath, SOURCE)
assert OUT.parent == BUILD / "runs" and OUT.name == "render-device-probe-B01"
assert not OUT.exists(), f"refuse non-fresh probe output: {OUT}"
OUT.mkdir()

sys.path.insert(0, str(BUILD / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
import fullhd  # noqa: E402
import studio  # noqa: E402


scene = bpy.context.scene
pre = {
    "camera": scene.camera.name if scene.camera else None,
    "materials": sorted(m.name for m in bpy.data.materials),
    "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
}

studio_error = None
try:
    studio.setup()
except Exception as exc:  # preserve the actual Blender 5.2 integration finding
    studio_error = {"type": type(exc).__name__, "message": str(exc)}
    raise

settings = fullhd.renderer()
cycles = bpy.context.preferences.addons["cycles"].preferences
supports_refresh = callable(getattr(cycles, "refresh_devices", None))
supports_adaptive = hasattr(scene.cycles, "use_adaptive_sampling")
all_devices = [{"name": d.name, "type": d.type, "use": bool(d.use)} for d in cycles.devices]

# Probe only: deliberately override full-HD settings after testing renderer().
scene.render.resolution_x = 256
scene.render.resolution_y = 144
scene.render.resolution_percentage = 100
scene.cycles.samples = 8
scene.frame_set(1)
studio.aim(scale=.365)
path = OUT / "device-probe.png"
scene.render.filepath = str(path)
started = time.monotonic()
result = bpy.ops.render.render(write_still=True)
elapsed = time.monotonic() - started
assert result == {"FINISHED"}, result
assert path.is_file() and path.stat().st_size > 0

image = bpy.data.images.load(str(path), check_existing=False)
pixels = [int(image.size[0]), int(image.size[1])]
bpy.data.images.remove(image)
assert pixels == [256, 144], pixels

probe = {
    "schema_version": 1,
    "source": str(SOURCE),
    "source_size_bytes": SOURCE.stat().st_size,
    "hostname": socket.gethostname(),
    "platform": platform.platform(),
    "blender_version": list(bpy.app.version),
    "fullhd_renderer_settings_before_probe_override": settings,
    "supports_refresh_devices": supports_refresh,
    "supports_use_adaptive_sampling": supports_adaptive,
    "observed_cycles_devices": all_devices,
    "probe": {
        "resolution": pixels,
        "samples": scene.cycles.samples,
        "device": scene.cycles.device,
        "elapsed_seconds": round(elapsed, 4),
        "file": path.name,
        "bytes": path.stat().st_size,
    },
    "pre_studio": pre,
    "studio_error": studio_error,
    "claim_limit": "256x144 samples=8 device probe only; not Full HD delivery evidence",
}
(OUT / "probe.json").write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
print("FULLHD_DEVICE_PROBE", json.dumps(probe, sort_keys=True), flush=True)

#!/usr/bin/env python3
"""Run the local QRemeshify Blender adapter with a hard wall-clock limit."""
import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--object", default="drone-silhouette-repaired")
    parser.add_argument("--addon", type=Path, default=Path(
        os.environ.get("QREMESHIFY_PATH", "/Users/jang/Downloads/QRemeshify")))
    parser.add_argument("--target-tris", type=int, default=60000)
    parser.add_argument("--density", type=float, default=1.0)
    parser.add_argument("--solver-seconds", type=int, default=120)
    parser.add_argument("--wall-seconds", type=int, default=300)
    parser.add_argument("--sharp-angle", type=float, default=35.0)
    parser.add_argument("--no-sharp", action="store_true")
    parser.add_argument("--no-preprocess", action="store_true")
    parser.add_argument("--no-symmetry-x", action="store_true")
    return parser.parse_args()


def main():
    args = arguments()
    project = Path(__file__).resolve().parents[1]
    blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    adapter = project / "scripts" / "qremeshify-headless-adapter.py"
    for required in (args.input, args.addon, blender, adapter):
        if not required.exists():
            raise SystemExit(f"missing required path: {required}")
    quarantined = []
    for name in ("liblib_quadwild.dylib", "liblib_quadpatches.dylib"):
        library = args.addon / "lib" / name
        result = subprocess.run(
            ["xattr", "-p", "com.apple.quarantine", str(library)],
            capture_output=True, check=False)
        if result.returncode == 0:
            quarantined.append(str(library))
    if quarantined:
        raise SystemExit("macOS quarantined QRemeshify binaries:\n" +
                         "\n".join(quarantined))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({
        "QREMESHIFY_PATH": str(args.addon.resolve()),
        "QREMESHIFY_OBJECT": args.object,
        "QREMESHIFY_TARGET_TRIS": str(args.target_tris),
        "QREMESHIFY_DENSITY": str(args.density),
        "QREMESHIFY_TIME_LIMIT": str(args.solver_seconds),
        "QREMESHIFY_SHARP_ANGLE": str(args.sharp_angle),
        "QREMESHIFY_ENABLE_SHARP": "0" if args.no_sharp else "1",
        "QREMESHIFY_PREPROCESS": "0" if args.no_preprocess else "1",
        "QREMESHIFY_SYMMETRY_X": "0" if args.no_symmetry_x else "1",
        "QREMESHIFY_OUTPUT": str(args.output.resolve()),
    })
    command = [str(blender), "--factory-startup", "-b",
               str(args.input.resolve()), "--python", str(adapter)]
    process = subprocess.Popen(command, env=environment, start_new_session=True)
    try:
        return process.wait(timeout=args.wall_seconds)
    except subprocess.TimeoutExpired:
        print(f"QREMESHIFY_TIMEOUT wall_seconds={args.wall_seconds}",
              file=sys.stderr, flush=True)
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        return 124


if __name__ == "__main__":
    raise SystemExit(main())

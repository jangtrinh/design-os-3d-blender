#!/usr/bin/env python3
"""Audit rendered image sequences for luminance jumps, channel drops, and blackout frames.

    python3 scripts/check-sequence-continuity.py --frames-dir builds/mochi-rb5320-companion/film/frames/seq-04
    python3 scripts/check-sequence-continuity.py --frames-dir path/to/frames --emit-rerun-json rerun.json

Why this exists: During headless Cycles Metal rendering with `scene.render.use_persistent_data = True`,
material shaders (such as ShaderNodeBevel or procedural metals) intermittently fail on intermediate
frames while endpoint frames look clean. Traditional file existence and size checks pass, but the
actual rendered frames drop to black silhouettes. This checker computes per-frame perceived luma
(0.299 R + 0.587 G + 0.114 B) and per-channel means to detect sudden inter-frame jumps or floor drops,
emitting a precise rerun JSON to satisfy Backlog E4 (partial-frame recovery).

Exit: 0 on PASS, 1 on continuity failure or blackout, 2 on input/config error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageStat
except ImportError:
    Image = None
    ImageStat = None


def natural_sort_key(s):
    """Sort strings with embedded numbers naturally (e.g. f_2 before f_10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def collect_frame_paths(directory: Path, extensions=("*.png", "*.jpg", "*.jpeg", "*.webp")):
    """Collect and naturally sort all image paths in a directory."""
    frames = []
    for ext in extensions:
        frames.extend(directory.glob(ext))
    return sorted(frames, key=natural_sort_key)


def compute_frame_stats(image_path: Path):
    """Compute channel means (R, G, B) and perceived luma for an image."""
    with Image.open(image_path) as img:
        rgb_img = img.convert("RGB")
        stat = ImageStat.Stat(rgb_img)
        r, g, b = stat.mean[0], stat.mean[1], stat.mean[2]
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        return {"r": r, "g": g, "b": b, "luma": luma}


def check_sequence_continuity(
    frames_dir: Path,
    min_frames: int = 1,
    max_delta_luma: float = 50.0,
    max_delta_channel: float = 60.0,
    min_luma: float = 1.0,
    min_channels: dict = None,
    allowed_jump_indices: set = None,
):
    """Audit image sequence continuity.
    
    Returns a dict with:
        status: 'pass' | 'fail'
        total_frames: int
        failed_indices: list of int (0-based)
        failed_files: list of str (filenames)
        violations: list of dict
        frames: list of dict (stats per frame)
    """
    if Image is None:
        raise RuntimeError("PIL (Pillow) is required for check-sequence-continuity.py")

    min_channels = min_channels or {}
    allowed_jump_indices = allowed_jump_indices or set()

    frames = collect_frame_paths(frames_dir)
    if len(frames) < min_frames:
        return {
            "status": "fail",
            "error": f"Found {len(frames)} frames in {frames_dir}, expected at least {min_frames}",
            "total_frames": len(frames),
            "failed_indices": [],
            "failed_files": [],
            "violations": [{"type": "insufficient_frames", "count": len(frames), "expected": min_frames}],
            "frames": [],
        }

    frame_records = []
    violations = []
    failed_indices = set()

    for idx, path in enumerate(frames):
        try:
            stats = compute_frame_stats(path)
        except Exception as exc:
            violations.append({
                "index": idx,
                "file": path.name,
                "type": "unreadable_image",
                "error": str(exc),
            })
            failed_indices.add(idx)
            continue

        record = {"index": idx, "file": path.name, **stats}
        frame_records.append(record)

        # 1. Blackout floor check
        if stats["luma"] < min_luma:
            violations.append({
                "index": idx,
                "file": path.name,
                "type": "blackout_luma",
                "measured_luma": stats["luma"],
                "min_luma": min_luma,
            })
            failed_indices.add(idx)

        # 2. Channel floor check
        for ch_name, floor_val in min_channels.items():
            if stats.get(ch_name, 0.0) < floor_val:
                violations.append({
                    "index": idx,
                    "file": path.name,
                    "type": f"channel_floor_{ch_name}",
                    "measured": stats.get(ch_name, 0.0),
                    "min_required": floor_val,
                })
                failed_indices.add(idx)

        # 3. Inter-frame continuity jump check
        if idx > 0 and (idx not in allowed_jump_indices):
            prev = frame_records[idx - 1]
            delta_luma = abs(stats["luma"] - prev["luma"])
            delta_r = abs(stats["r"] - prev["r"])
            delta_g = abs(stats["g"] - prev["g"])
            delta_b = abs(stats["b"] - prev["b"])
            max_channel_delta = max(delta_r, delta_g, delta_b)

            if delta_luma > max_delta_luma:
                violations.append({
                    "index": idx,
                    "file": path.name,
                    "type": "luma_jump",
                    "delta_luma": delta_luma,
                    "max_allowed": max_delta_luma,
                    "prev_file": prev["file"],
                })
                failed_indices.add(idx)
            elif max_channel_delta > max_delta_channel:
                violations.append({
                    "index": idx,
                    "file": path.name,
                    "type": "channel_jump",
                    "delta_channel": max_channel_delta,
                    "max_allowed": max_delta_channel,
                    "prev_file": prev["file"],
                })
                failed_indices.add(idx)

    sorted_failed_indices = sorted(failed_indices)
    failed_files = [frames[i].name for i in sorted_failed_indices if i < len(frames)]

    status = "pass" if not violations else "fail"
    return {
        "status": status,
        "frames_dir": str(frames_dir),
        "total_frames": len(frames),
        "failed_indices": sorted_failed_indices,
        "failed_files": failed_files,
        "violations": violations,
        "frames": frame_records,
    }


def parse_min_channel_arg(arg_list):
    """Parse list of strings formatted as 'ch:val' (e.g. ['b:5.0', 'r:2.0'])."""
    res = {}
    if not arg_list:
        return res
    for item in arg_list:
        parts = item.split(":")
        if len(parts) == 2 and parts[0].lower() in ("r", "g", "b", "luma"):
            res[parts[0].lower()] = float(parts[1])
        else:
            raise ValueError(f"Invalid channel threshold '{item}', expected 'r:val', 'g:val', or 'b:val'")
    return res


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames-dir", required=True, type=Path, help="Directory containing sequence frames")
    parser.add_argument("--min-frames", type=int, default=1, help="Minimum expected frame count (default: 1)")
    parser.add_argument("--max-delta-luma", type=float, default=50.0, help="Max allowed luma jump between adjacent frames")
    parser.add_argument("--max-delta-channel", type=float, default=60.0, help="Max allowed R/G/B channel jump between adjacent frames")
    parser.add_argument("--min-luma", type=float, default=1.0, help="Min average luma floor (blackout filter)")
    parser.add_argument("--min-channel", action="append", default=[], help="Channel floor filter 'ch:val' (e.g. --min-channel b:3.0)")
    parser.add_argument("--allow-jump", action="append", type=int, default=[], help="Allow deliberate jump at frame index (e.g. cut)")
    parser.add_argument("--emit-rerun-json", type=Path, help="Path to write rerun JSON with failed_indices")
    parser.add_argument("--json-report", type=Path, help="Path to write complete audit JSON report")
    parser.add_argument("--verbose", action="store_true", help="Print per-frame stats")

    args = parser.parse_args(argv)

    if not args.frames_dir.is_dir():
        sys.stderr.write(f"Error: --frames-dir '{args.frames_dir}' is not a directory\n")
        return 2

    try:
        min_channels = parse_min_channel_arg(args.min_channel)
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2

    result = check_sequence_continuity(
        frames_dir=args.frames_dir,
        min_frames=args.min_frames,
        max_delta_luma=args.max_delta_luma,
        max_delta_channel=args.max_delta_channel,
        min_luma=args.min_luma,
        min_channels=min_channels,
        allowed_jump_indices=set(args.allow_jump),
    )

    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(result, indent=2))

    if args.emit_rerun_json:
        args.emit_rerun_json.parent.mkdir(parents=True, exist_ok=True)
        rerun_payload = {
            "frames_dir": str(args.frames_dir),
            "status": result["status"],
            "failed_indices": result["failed_indices"],
            "failed_files": result["failed_files"],
            "total_frames": result["total_frames"],
        }
        args.emit_rerun_json.write_text(json.dumps(rerun_payload, indent=2))

    if result["status"] == "pass":
        print(f"CONTINUITY_PASS: {result['total_frames']} frames verified in {args.frames_dir}. 0 violations.")
        return 0
    else:
        print(f"CONTINUITY_FAIL: {len(result['violations'])} violations across {len(result['failed_indices'])} frames in {args.frames_dir}.")
        for v in result["violations"][:10]:
            print(f"  - Frame {v.get('index', '?')} ({v.get('file', '?')}): {v.get('type')} ({v})")
        if len(result["violations"]) > 10:
            print(f"  ... and {len(result['violations']) - 10} more violations.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

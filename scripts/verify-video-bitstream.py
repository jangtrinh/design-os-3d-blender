#!/usr/bin/env python3
"""Strict video bitstream & distinct-state verification gate for product cinematics.

    python3 scripts/verify-video-bitstream.py --video builds/mochi-rb5320-companion/film/out/motion-16x9.mp4 --silent
    python3 scripts/verify-video-bitstream.py --video path/to/movie.mp4 --with-audio --min-distinct-ratio 0.95

Why this exists:
1. Video delivery specs (e.g. ROB-AD §7) require strict H.264 high-profile, yuv420p, tv color range,
   bt709 color space, faststart, and no audio track for web hero loops.
2. The DC-01 incident (docs/native-build-pipeline-lessons.md) showed an agent rendered 120 poses
   at 5 poses/sec and repeated frames to 30 fps, passing numerical checks but failing owner review.
   Running `ffmpeg -f framemd5` inspects the exact decoded pixel stream to compute the true distinct-state
   ratio (unique_framemd5 / total_frames).
3. The Mochi incident showed headless Chrome seek-capture pipes can output deprecated `yuvj420p` (pc range),
   causing gamma shifts in QuickTime and Safari.

Exit: 0 on PASS, 1 on verification failure, 2 on input/environment error.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def find_binary(name: str):
    """Find binary on PATH or common macOS brew locations."""
    found = shutil.which(name)
    if found:
        return found
    brew_path = Path("/opt/homebrew/bin") / name
    if brew_path.is_file():
        return str(brew_path)
    return None


def probe_video_streams(video_path: Path):
    """Run ffprobe -show_streams -show_format -print_format json."""
    ffprobe = find_binary("ffprobe")
    if not ffprobe:
        raise FileNotFoundError("ffprobe not found on PATH or /opt/homebrew/bin/ffprobe")

    cmd = [
        ffprobe,
        "-v", "error",
        "-show_streams",
        "-show_format",
        "-print_format", "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed ({proc.returncode}): {proc.stderr}")
    return json.loads(proc.stdout)


def extract_framemd5_hashes(video_path: Path):
    """Run ffmpeg -f framemd5 on video stream 0 to get per-frame MD5 hashes."""
    ffmpeg = find_binary("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg not found on PATH or /opt/homebrew/bin/ffmpeg")

    cmd = [
        ffmpeg,
        "-v", "error",
        "-i", str(video_path),
        "-map", "0:v:0",
        "-f", "framemd5",
        "-",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg framemd5 failed ({proc.returncode}): {proc.stderr}")

    hashes = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Line format: stream_index, pts, dts, duration, size, hash
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            hashes.append(parts[5])
    return hashes


def verify_video_bitstream(
    video_path: Path,
    expected_codec: str = "h264",
    expected_pix_fmt: str = "yuv420p",
    expected_color_range: str = "tv",
    expected_colorspace: str = "bt709",
    expected_width: int = None,
    expected_height: int = None,
    min_fps: float = None,
    min_distinct_ratio: float = 0.85,
    audio_policy: str = "any",  # 'silent', 'with-audio', 'any'
):
    """Verify bitstream properties, color range, and distinct-frame count."""
    if not video_path.is_file():
        return {"status": "fail", "error": f"File not found: {video_path}", "violations": ["file_not_found"]}

    probe = probe_video_streams(video_path)
    streams = probe.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    a_streams = [s for s in streams if s.get("codec_type") == "audio"]

    violations = []
    if not v_streams:
        return {"status": "fail", "error": "No video streams found", "violations": ["no_video_stream"]}

    v = v_streams[0]
    
    # 1. Codec check
    codec_name = v.get("codec_name", "")
    if expected_codec and codec_name.lower() != expected_codec.lower():
        violations.append(f"codec_mismatch: got {codec_name}, expected {expected_codec}")

    # 2. Pixel format check (reject yuvj420p)
    pix_fmt = v.get("pix_fmt", "")
    if expected_pix_fmt and pix_fmt.lower() != expected_pix_fmt.lower():
        violations.append(f"pix_fmt_mismatch: got {pix_fmt}, expected {expected_pix_fmt}")

    # 3. Color range check (must be tv/limited, not pc/full)
    color_range = v.get("color_range", "")
    if expected_color_range and color_range.lower() != expected_color_range.lower():
        violations.append(f"color_range_mismatch: got '{color_range}', expected '{expected_color_range}'")

    # 4. Color space check
    colorspace = v.get("color_space") or v.get("color_primaries") or ""
    if expected_colorspace and expected_colorspace.lower() not in colorspace.lower():
        violations.append(f"colorspace_mismatch: got '{colorspace}', expected '{expected_colorspace}'")

    # 5. Dimensions check
    w = v.get("width")
    h = v.get("height")
    if expected_width and w != expected_width:
        violations.append(f"width_mismatch: got {w}, expected {expected_width}")
    if expected_height and h != expected_height:
        violations.append(f"height_mismatch: got {h}, expected {expected_height}")

    # 6. Audio policy check
    if audio_policy == "silent" and len(a_streams) > 0:
        violations.append(f"audio_policy_violation: audio track present ({len(a_streams)} streams), expected silent (-an)")
    elif audio_policy == "with-audio" and len(a_streams) == 0:
        violations.append("audio_policy_violation: expected audio track, but video is silent (-an)")

    # 7. Framemd5 distinct state analysis
    hashes = extract_framemd5_hashes(video_path)
    total_frames = len(hashes)
    unique_hashes = len(set(hashes))
    distinct_ratio = (unique_hashes / total_frames) if total_frames > 0 else 0.0

    if total_frames == 0:
        violations.append("zero_frames_decoded")
    elif distinct_ratio < min_distinct_ratio:
        violations.append(
            f"insufficient_distinct_states: distinct_ratio={distinct_ratio:.3f} "
            f"({unique_hashes}/{total_frames} unique frames), minimum required is {min_distinct_ratio:.3f}"
        )

    status = "pass" if not violations else "fail"
    return {
        "status": status,
        "video": str(video_path),
        "codec_name": codec_name,
        "pix_fmt": pix_fmt,
        "color_range": color_range,
        "colorspace": colorspace,
        "width": w,
        "height": h,
        "total_frames_decoded": total_frames,
        "unique_framemd5_count": unique_hashes,
        "distinct_ratio": round(distinct_ratio, 4),
        "audio_stream_count": len(a_streams),
        "violations": violations,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", required=True, type=Path, help="Path to video file to verify")
    parser.add_argument("--codec", default="h264", help="Expected video codec (default: h264)")
    parser.add_argument("--pix-fmt", default="yuv420p", help="Expected pixel format (default: yuv420p)")
    parser.add_argument("--color-range", default="tv", help="Expected color range (default: tv)")
    parser.add_argument("--colorspace", default="bt709", help="Expected colorspace (default: bt709)")
    parser.add_argument("--width", type=int, help="Expected video width (e.g. 1920)")
    parser.add_argument("--height", type=int, help="Expected video height (e.g. 1080)")
    parser.add_argument("--min-distinct-ratio", type=float, default=0.85, help="Min unique framemd5 ratio (default: 0.85)")
    
    audio_group = parser.add_mutually_exclusive_group()
    audio_group.add_argument("--silent", action="store_true", help="Assert video has NO audio tracks (-an)")
    audio_group.add_argument("--with-audio", action="store_true", help="Assert video HAS audio track")

    parser.add_argument("--json-report", type=Path, help="Path to write verification report JSON")
    args = parser.parse_args(argv)

    if not args.video.is_file():
        sys.stderr.write(f"Error: Video file '{args.video}' does not exist\n")
        return 2

    audio_policy = "any"
    if args.silent:
        audio_policy = "silent"
    elif args.with_audio:
        audio_policy = "with-audio"

    try:
        report = verify_video_bitstream(
            video_path=args.video,
            expected_codec=args.codec,
            expected_pix_fmt=args.pix_fmt,
            expected_color_range=args.color_range,
            expected_colorspace=args.colorspace,
            expected_width=args.width,
            expected_height=args.height,
            min_distinct_ratio=args.min_distinct_ratio,
            audio_policy=audio_policy,
        )
    except Exception as exc:
        sys.stderr.write(f"Error during video verification: {exc}\n")
        return 2

    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, indent=2))

    if report["status"] == "pass":
        print(
            f"VIDEO_BITSTREAM_PASS: {args.video.name} verified ({report['codec_name']}, "
            f"{report['pix_fmt']}, {report['color_range']}, {report['colorspace']}, "
            f"{report['unique_framemd5_count']}/{report['total_frames_decoded']} distinct frames, "
            f"ratio={report['distinct_ratio']:.3f})"
        )
        return 0
    else:
        print(f"VIDEO_BITSTREAM_FAIL: {len(report['violations'])} violations in {args.video.name}:")
        for v in report["violations"]:
            print(f"  - {v}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

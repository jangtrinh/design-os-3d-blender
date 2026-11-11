#!/usr/bin/env python3
"""Tests for scripts/verify-video-bitstream.py."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = ROOT / "scripts" / "verify-video-bitstream.py"

spec = importlib.util.spec_from_file_location("verify_video_bitstream", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestVideoBitstream(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = mod.find_binary("ffmpeg")
        cls.ffprobe = mod.find_binary("ffprobe")

    def setUp(self):
        if not self.ffmpeg or not self.ffprobe:
            self.skipTest("ffmpeg or ffprobe not available on this machine")
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_video_bitstream_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _generate_synthetic_video(self, filename: str, frames: int = 10, pix_fmt: str = "yuv420p", with_audio: bool = False, static: bool = False):
        out_path = self.test_dir / filename
        # Generate video with testsrc or color
        src = "color=c=blue:s=160x120:d=1" if static else "testsrc=size=160x120:rate=10:duration=1"
        cmd = [
            self.ffmpeg,
            "-y",
            "-f", "lavfi",
            "-i", src,
        ]
        if with_audio:
            cmd.extend([
                "-f", "lavfi",
                "-i", "sine=frequency=440:duration=1",
                "-c:a", "aac",
            ])
        else:
            cmd.append("-an")

        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", pix_fmt,
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-frames:v", str(frames),
            str(out_path),
        ])
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg synthetic video generation failed: {proc.stderr}")
        return out_path

    def test_valid_video_passes(self):
        vid = self._generate_synthetic_video("valid.mp4", frames=10, with_audio=False, static=False)
        res = mod.verify_video_bitstream(
            vid,
            expected_codec="h264",
            expected_pix_fmt="yuv420p",
            expected_color_range="tv",
            expected_colorspace="bt709",
            expected_width=160,
            expected_height=120,
            min_distinct_ratio=0.80,
            audio_policy="silent",
        )
        self.assertEqual(res["status"], "pass")
        self.assertEqual(len(res["violations"]), 0)
        self.assertEqual(res["total_frames_decoded"], 10)
        self.assertGreaterEqual(res["distinct_ratio"], 0.80)

    def test_audio_policy_violation(self):
        vid_audio = self._generate_synthetic_video("audio.mp4", frames=10, with_audio=True)
        res = mod.verify_video_bitstream(vid_audio, audio_policy="silent")
        self.assertEqual(res["status"], "fail")
        self.assertTrue(any("audio_policy_violation" in v for v in res["violations"]))

    def test_static_repeated_frames_rejected(self):
        # A static 10-frame video has 1 unique frame (ratio 0.10)
        vid_static = self._generate_synthetic_video("static.mp4", frames=10, static=True)
        res = mod.verify_video_bitstream(vid_static, min_distinct_ratio=0.85)
        self.assertEqual(res["status"], "fail")
        self.assertTrue(any("insufficient_distinct_states" in v for v in res["violations"]))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for scripts/check-sequence-continuity.py."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

_SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "check-sequence-continuity.py"
_spec = importlib.util.spec_from_file_location("check_sequence_continuity", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

check_sequence_continuity = _mod.check_sequence_continuity
collect_frame_paths = _mod.collect_frame_paths
natural_sort_key = _mod.natural_sort_key


class TestSequenceContinuity(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_seq_continuity_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_frame(self, filename: str, color: tuple):
        p = self.test_dir / filename
        img = Image.new("RGB", (64, 64), color=color)
        img.save(p)
        return p

    def test_natural_sort(self):
        names = ["f_10.jpg", "f_1.jpg", "f_2.jpg", "f_0.jpg"]
        sorted_names = sorted(names, key=natural_sort_key)
        self.assertEqual(sorted_names, ["f_0.jpg", "f_1.jpg", "f_2.jpg", "f_10.jpg"])

    def test_clean_sequence_passes(self):
        # 5 smooth frames
        for i in range(5):
            val = 100 + i * 2  # luma changes by 2 per frame
            self._create_frame(f"f_{i:03d}.png", (val, val, val))

        res = check_sequence_continuity(self.test_dir, min_frames=5, max_delta_luma=10.0)
        self.assertEqual(res["status"], "pass")
        self.assertEqual(res["total_frames"], 5)
        self.assertEqual(len(res["failed_indices"]), 0)

    def test_blackout_frame_detected(self):
        for i in range(4):
            self._create_frame(f"f_{i:03d}.png", (120, 120, 120))
        # Frame 4 is black
        self._create_frame("f_004.png", (0, 0, 0))

        res = check_sequence_continuity(self.test_dir, min_luma=2.0)
        self.assertEqual(res["status"], "fail")
        self.assertIn(4, res["failed_indices"])
        self.assertIn("f_004.png", res["failed_files"])

    def test_luma_jump_and_channel_drop(self):
        self._create_frame("f_000.png", (100, 100, 100))
        self._create_frame("f_001.png", (102, 102, 102))
        # Sudden drop on frame 2 (simulate missing shader)
        self._create_frame("f_002.png", (10, 10, 10))
        self._create_frame("f_003.png", (102, 102, 102))

        res = check_sequence_continuity(self.test_dir, max_delta_luma=40.0)
        self.assertEqual(res["status"], "fail")
        self.assertIn(2, res["failed_indices"])

    def test_allow_intentional_jump(self):
        self._create_frame("f_000.png", (50, 50, 50))
        # Frame 1 is a deliberate camera cut from dark to bright
        self._create_frame("f_001.png", (180, 180, 180))
        self._create_frame("f_002.png", (182, 182, 182))

        # Without allowed jump, fails
        res_fail = check_sequence_continuity(self.test_dir, max_delta_luma=50.0)
        self.assertEqual(res_fail["status"], "fail")

        # With allowed jump on index 1, passes
        res_pass = check_sequence_continuity(self.test_dir, max_delta_luma=50.0, allowed_jump_indices={1})
        self.assertEqual(res_pass["status"], "pass")

    def test_channel_floor_filter(self):
        # Frame with normal red/green but 0 blue
        self._create_frame("f_000.png", (100, 100, 1))
        res = check_sequence_continuity(self.test_dir, min_channels={"b": 10.0})
        self.assertEqual(res["status"], "fail")
        self.assertIn(0, res["failed_indices"])


if __name__ == "__main__":
    unittest.main()

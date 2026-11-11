#!/usr/bin/env python3
"""Tests for scripts/sanitize-delivery-assets.py."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = ROOT / "scripts" / "sanitize-delivery-assets.py"

spec = importlib.util.spec_from_file_location("sanitize_delivery_assets", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestSanitizeDeliveryAssets(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_sanitize_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_strip_png_metadata_bytes(self):
        # Create minimal PNG
        img_path = self.test_dir / "test.png"
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.save(img_path)
        raw = img_path.read_bytes()

        # Inject fake tEXt chunk
        # Chunk format: 4 bytes length, 4 bytes type (tEXt), data, 4 bytes CRC
        text_data = b"Software\x00Blender 5.2.0"
        import binascii
        crc = binascii.crc32(b"tEXt" + text_data) & 0xffffffff
        chunk = len(text_data).to_bytes(4, "big") + b"tEXt" + text_data + crc.to_bytes(4, "big")
        
        # Insert after signature (8 bytes)
        injected = raw[:8] + chunk + raw[8:]
        img_path.write_bytes(injected)

        # Check mode detects it
        self.assertTrue(mod.strip_image_file_metadata(img_path, write=False))

        # Write mode strips it
        self.assertTrue(mod.strip_image_file_metadata(img_path, write=True))
        self.assertFalse(mod.strip_image_file_metadata(img_path, write=False))

        # Verify image is still readable
        with Image.open(img_path) as reloaded:
            self.assertEqual(reloaded.size, (10, 10))

    def test_sanitize_json_paths(self):
        json_path = self.test_dir / "report.json"
        data = {
            "scene": "/Users/someone/Products/design-os-3d-blender/builds/test/test.blend",
            "other_build": "/Users/someone/work/builds/test/parts/foo.stl",
            "sha256": "abcdef1234567890",
        }
        json_path.write_text(json.dumps(data, indent=2))

        # Check mode
        dirty = mod.sanitize_json_paths(json_path, repo_root=Path("/Users/someone/Products/design-os-3d-blender"), write=False)
        self.assertTrue(dirty)

        # Write mode
        mod.sanitize_json_paths(json_path, repo_root=Path("/Users/someone/Products/design-os-3d-blender"), write=True)
        sanitized = json.loads(json_path.read_text())
        self.assertEqual(sanitized["scene"], "builds/test/test.blend")
        self.assertEqual(sanitized["other_build"], "builds/test/parts/foo.stl")
        self.assertEqual(sanitized["sha256"], "abcdef1234567890")


if __name__ == "__main__":
    unittest.main()

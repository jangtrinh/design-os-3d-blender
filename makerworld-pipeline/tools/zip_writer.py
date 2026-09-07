"""Deterministic ZIP (.3mf) assembly: [Content_Types].xml, _rels/.rels,
1x1 PNG plate thumbnails, and sorted, fixed-metadata ZIP entries so two
generator runs produce byte-identical output (same sha256).
"""
from __future__ import annotations

import struct
import zipfile
import zlib
from io import BytesIO

# Fixed timestamp for every ZipInfo entry -- removes the host clock as a
# source of non-determinism between runs.
FIXED_DATE_TIME = (2026, 1, 1, 0, 0, 0)

CONTENT_TYPES_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
    ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
    ' <Default Extension="png" ContentType="image/png"/>\n'
    "</Types>"
)


def build_root_rels_xml(thumbnail_target: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
        f' <Relationship Target="{thumbnail_target}" Id="rel-2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>\n'
        "</Relationships>"
    )


def make_1x1_png() -> bytes:
    """Build a minimal valid 1x1 transparent PNG from scratch (stdlib zlib
    only) -- no binary asset is embedded/downloaded, satisfying the Native
    Asset Policy."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)  # 1x1, 8-bit RGBA
    raw_scanline = b"\x00" + b"\x00\x00\x00\x00"  # filter=none, one transparent pixel
    idat = zlib.compress(raw_scanline, level=9)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def write_deterministic_zip(out_path: str, members: dict[str, bytes]) -> None:
    """Write `members` (path -> bytes) sorted by name, with fixed per-entry
    metadata, so repeated calls with identical `members` are byte-identical."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 0  # FAT, not host-OS-dependent (3 = Unix)
            zf.writestr(info, members[name], compresslevel=6)
    with open(out_path, "wb") as f:
        f.write(buffer.getvalue())

"""Minimal, strict PNG dimension and payload checker for proof receipts."""
import binascii
import struct
import zlib

SIGNATURE = b'\x89PNG\r\n\x1a\n'
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}


class PngError(ValueError):
    pass


def dimensions(path):
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PngError('cannot read PNG: %s' % exc) from exc
    if not data.startswith(SIGNATURE):
        raise PngError('not a PNG signature')
    offset = len(SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    idat = []
    ended = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise PngError('truncated chunk')
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise PngError('truncated %s chunk' % kind.decode('latin1'))
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', data[offset + 8 + length:end])[0]
        if binascii.crc32(kind + payload) & 0xffffffff != crc:
            raise PngError('CRC mismatch in %s' % kind.decode('latin1'))
        if kind == b'IHDR':
            if width is not None or length != 13:
                raise PngError('invalid IHDR')
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            if not width or not height or compression or filtering or interlace or color_type not in CHANNELS:
                raise PngError('unsupported IHDR')
        elif kind == b'IDAT':
            idat.append(payload)
        elif kind == b'IEND':
            if length or ended:
                raise PngError('invalid IEND')
            ended = True
            if end != len(data):
                raise PngError('trailing bytes after IEND')
            break
        offset = end
    if width is None or not idat or not ended:
        raise PngError('missing IHDR, IDAT, or IEND')
    if bit_depth not in DEPTHS.get(color_type, ()):
        raise PngError('unsupported bit depth')
    row_bytes = (width * CHANNELS[color_type] * bit_depth + 7) // 8
    try:
        raw = zlib.decompress(b''.join(idat))
    except zlib.error as exc:
        raise PngError('invalid IDAT zlib stream: %s' % exc) from exc
    if len(raw) != height * (row_bytes + 1):
        raise PngError('decoded payload size does not match IHDR')
    if any(raw[row * (row_bytes + 1)] > 4 for row in range(height)):
        raise PngError('invalid PNG row filter')
    return width, height

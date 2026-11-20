"""Colour formats of game files to and from RGBA ints 0xRRGGBBAA (the colours of parsed palettes and images), on whole
arrays (numpy). A channel of n bits decodes as `transform_bitness` scales it (value * 255 / (2^n - 1), rounded) and
encodes to its high n bits. Formats:
- packed (`PACKED_FORMATS`), alpha in the highest bits, blue in the lowest: `argb1555`, `rgb565`, `argb4444`, `rgb888`
  (0xRRGGBB), `argb8888` (0xAARRGGBB); no alpha bits: opaque
- `bgr555`: bits 0-4 red, 5-9 green, 10-14 blue (PSX, Saturn; bit 15 left out), opaque
- `dos666`: 0x00RRGGBB with 6-bit channels (the VGA DAC's), each shifted up by 2 bits, opaque"""

from functools import lru_cache
from typing import List

import numpy as np

from library.utils import transform_bitness

# (alpha, red, green, blue) bits
PACKED_FORMATS = {
    'argb1555': (1, 5, 5, 5),
    'rgb565': (0, 5, 6, 5),
    'argb4444': (4, 4, 4, 4),
    'rgb888': (0, 8, 8, 8),
    'argb8888': (8, 8, 8, 8),
}


@lru_cache(maxsize=None)
def _scale_table(bits: int) -> np.ndarray:
    return np.array([transform_bitness(v, bits) for v in range(1 << bits)], dtype=np.uint32)


def _uint32(values) -> np.ndarray:
    # the low 32 bits of ints of any size, as bit operations on Python ints take them
    values = np.asarray(values)
    if values.size and (values.dtype == object or values.dtype.kind == 'i' or values.dtype.itemsize > 4):
        values = values & 0xFFFFFFFF
    return values.astype(np.uint32)


def _channel(values: np.ndarray, bits: int, shift: int) -> np.ndarray:
    return _scale_table(bits)[(values >> shift) & ((1 << bits) - 1)]


def decode_colors(fmt: str, values) -> np.ndarray:
    """RGBA (uint32 0xRRGGBBAA) of the colour values `values` stored in format `fmt`"""
    v = _uint32(values)
    if fmt == 'bgr555':
        return _channel(v, 5, 0) << 24 | _channel(v, 5, 5) << 16 | _channel(v, 5, 10) << 8 | 0xFF
    if fmt == 'dos666':
        return (v & 0x3F3F3F) << 10 | 0xFF
    a, r, g, b = PACKED_FORMATS[fmt]
    alpha = _channel(v, a, r + g + b) if a else np.uint32(0xFF)
    return _channel(v, r, g + b) << 24 | _channel(v, g, b) << 16 | _channel(v, b, 0) << 8 | alpha


def encode_colors(fmt: str, rgba) -> np.ndarray:
    """The values (uint32) of RGBA colours `rgba` (0xRRGGBBAA) stored in format `fmt` (not `bgr555`)"""
    c = _uint32(rgba)
    if fmt == 'dos666':
        return (c & 0xFCFCFC00) >> 10
    a, r, g, b = PACKED_FORMATS[fmt]
    alpha = (c & 0xFF) >> (8 - a)
    red = (c & 0xFF000000) >> (32 - r)
    green = (c & 0xFF0000) >> (24 - g)
    blue = (c & 0xFF00) >> (16 - b)
    return alpha << (r + g + b) | red << (g + b) | green << b | blue


def rgba_image(width: int, height: int, colors):
    """RGBA PIL image of RGBA ints (0xRRGGBBAA), row by row"""
    from PIL import Image

    return Image.frombytes('RGBA', (width, height), np.asarray(colors, dtype='>u4').tobytes())


def image_rgba(image) -> List[int]:
    """RGBA ints (0xRRGGBBAA) of the pixels of a PIL image, row by row"""
    return np.frombuffer(image.convert('RGBA').tobytes(), dtype='>u4').tolist()


def rgb_palette(colors) -> bytes:
    """PIL palette (`putpalette`, RGB) of RGBA ints"""
    return np.asarray(colors, dtype='>u4').view(np.uint8).reshape(-1, 4)[:, :3].tobytes()

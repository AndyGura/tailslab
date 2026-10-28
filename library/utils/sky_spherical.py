"""
Shared helpers for the sky sphere textures `spherical.png` of NFS5 and NFS6 (same layout as the TNFS one, see
`nfs1_panorama_to_spherical.py`): 2048x1024 RGBA equirectangular image, eye level on the middle row, top row straight
up, bottom row straight down. The centre column looks along the game's +X axis, a quarter width right of it along -Z,
a quarter width left of it along +Z (game axes X right, Y up, Z forward, the axes of the track data). Columns run left
to right as a viewer standing in the game world sees the panorama.
"""

import math
from typing import Tuple

OUT_WIDTH = 2048
OUT_HEIGHT = 1024


def output_angles(width: int = OUT_WIDTH, height: int = OUT_HEIGHT):
    """(heading, elevation) in radians of the output pixel centres: heading 0 at the centre column, growing to the
    right (towards -Z), elevation +pi/2 at the top"""
    import numpy as np

    heading = ((np.arange(width) + 0.5) / width - 0.5) * 2 * math.pi
    elevation = (0.5 - (np.arange(height) + 0.5) / height) * math.pi
    return heading, elevation


def output_directions(width: int = OUT_WIDTH, height: int = OUT_HEIGHT):
    """Unit view direction (game axes) of every output pixel, array (height, width, 3)"""
    import numpy as np

    heading, elevation = output_angles(width, height)
    h, e = np.meshgrid(heading, elevation)
    return np.stack([np.cos(h) * np.cos(e), np.sin(e), -np.sin(h) * np.cos(e)], axis=-1)


def direction_to_pixel(direction: Tuple[float, float, float], width: int = OUT_WIDTH, height: int = OUT_HEIGHT):
    """Output pixel (column, row, fractional) a game direction falls on"""
    x, y, z = direction
    heading = math.atan2(-z, x)
    elevation = math.atan2(y, math.hypot(x, z))
    return (heading / (2 * math.pi) + 0.5) * width, (0.5 - elevation / math.pi) * height


def sample_bilinear(texture, u, v, wrap: bool = True):
    """Bilinear sample of an RGBA float image (H, W, 4) at texture coordinates u, v (0..1 over the image, texel
    centres at (i + 0.5) / size, like Direct3D), repeated outside 0..1 with `wrap`, clamped to the edge otherwise"""
    import numpy as np

    h, w = texture.shape[:2]
    x = np.asarray(u, dtype=np.float64) * w - 0.5
    y = np.asarray(v, dtype=np.float64) * h - 0.5
    x0 = np.floor(x)
    y0 = np.floor(y)
    tx = (x - x0)[..., None]
    ty = (y - y0)[..., None]
    x0 = x0.astype(np.int64)
    y0 = y0.astype(np.int64)
    if wrap:
        x1, y1 = (x0 + 1) % w, (y0 + 1) % h
        x0, y0 = x0 % w, y0 % h
    else:
        x1, y1 = np.clip(x0 + 1, 0, w - 1), np.clip(y0 + 1, 0, h - 1)
        x0, y0 = np.clip(x0, 0, w - 1), np.clip(y0, 0, h - 1)
    top = texture[y0, x0] * (1 - tx) + texture[y0, x1] * tx
    bottom = texture[y1, x0] * (1 - tx) + texture[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def blend_over(dst, src, mask=None):
    """Alpha blending (SRCALPHA, INVSRCALPHA) of RGBA float colours (0..255) `src` onto `dst` in place (only where
    `mask`); the destination alpha becomes opaque where something was drawn"""
    import numpy as np

    if mask is None:
        mask = np.ones(dst.shape[:-1], dtype=bool)
    a = src[..., 3:4] / 255
    dst[mask, :3] = src[..., :3] * a + dst[mask, :3] * (1 - a)
    dst[mask, 3] = 255


def save_rgba(image, path: str):
    import numpy as np
    from PIL import Image

    Image.fromarray(np.round(np.clip(image, 0, 255)).astype(np.uint8), 'RGBA').save(path)

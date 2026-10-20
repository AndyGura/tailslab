"""
The horizon of a PlayStation TNFS track at a time of day (images `hrz0`..`hrz7` of `Z<track><time>.PSH`, settings
`Z<track><time>.INF`) on an equirectangular sky sphere texture, like `nfs1_panorama_to_spherical` does for the PC FAM
`horz` (same output: 2048x1024, eye level in the middle, heading 0 at the centre, headings growing to the right),
placed as the PSX game draws it. Verified in the PSX executable (SLUS-00204, tnfs-1995 Ghidra project):

- Settings: FUN_80034adc parses the INF (`TnfsPsxHorizonInfo`), halving ring y offset and ring height (C division):
  they are px of the 320x240 screen. It builds the ring with `tnfs_hr_ring` 0x800348c0. The PSX has no scrolling
  bitmap: every track gets the ring, drawn when "height far" is not 0 (`tnfs_horizon_position` 0x80035bd8).
- Ring (`tnfs_hr_ring`): points at radius far around the camera at height "vert offset far" (0 in every file), one
  every 0x1000 of the 0x10000 angle units (22.5 degrees, 16 per turn; 32 points, the second turn repeats the first).
  The quad from point i to i + 1 shows `hrz{i % 8}`: `hrz0`..`hrz7` cover 180 degrees, starting at heading 0. With the
  mirror flag (last INF value) the sectors 8..15 show `hrz{7 - i % 8}` and `tnfs_horizon_2` 0x80034e14 swaps the
  left and right vertices of their quads: the second half is the first one mirrored.
- Vertical placement (`tnfs_horizon_2`): every quad goes from `y_offset - height` to `y_offset + height` screen px
  below the projected ring point (the horizon line at eye level), texel rows 0 to H - 1 (the UVs of the loader
  FUN_80044330 span the whole image; raw texture POLY_FT4, not semi-transparent). The projection is the GTE one,
  focal length (320 / 2) / tan(90 / 2) = 160 px for both axes (FUN_800af64c with the 90 degrees FOV of every camera
  config, 0x800bd090; window scale 1.0, 0x800bcf50).
- Above the ring: a quad of "colour top" from the ring top up to the top of the screen, and over it a gradient quad
  (GPU gouraud, dithered with the dithering flag) from "colour top" at `ratio of the blend` % of `height - y_offset`
  px above the ring top down to "colour bottom" at the ring top.
- Below the ring: one texel of `hrz0` (column 0, row H - 2 as shown: FUN_80043fb8 with the UV rectangle at
  0x800bd728) stretched over `height - y_offset` px under the ring, gouraud-shaded from the texel color to black.
  The game draws nothing further down (terrain covers it).

Conversion choice (not the game's): below the ring the converter fades from that `hrz0` texel to the average color of
the ring's bottom line instead of black, and fills everything further down with that average, so the sphere has no
black band. The bottom line is texel row H - 2 of every sector image (as shown): with UVs from 0 to H - 1 over the
quad, the GPU's last drawn pixel row samples row H - 2 (row H - 1 lies on the bottom edge, which is not drawn). The
average is over the 360 degrees: the mean of each sector's row (columns 0..W - 2, the ones the quad shows the same
way), the 8 sectors weighted alike (each covers 22.5 degrees, twice per turn, mirrored or not).

Not modelled: the camera roll (the game rotates the quads' vertical offsets with it), and ring "vert offset far" /
"z offset far" other than 0 (none in the game files).
"""

import math
import os
from typing import List, Optional

from library.utils.nfs1_panorama_to_spherical import OUT_HEIGHT, OUT_WIDTH

# GTE focal length of the PSX game: (320 / 2) / tan(90 degrees / 2)
PSX_FOCAL_PX = 160 / math.tan(math.radians(45))
SECTORS_PER_TURN = 16
SECTOR_IMAGES = 8


def _c_div(a: int, b: int) -> int:
    """Integer division rounding towards 0, as C does"""
    quotient = abs(a) // abs(b)
    return quotient if (a >= 0) == (b > 0) else -quotient


def _sample(source, rows, columns):
    """Bilinear samples of an HxWx4 array at texel coordinates (texel i spans i..i+1), clamped to the image"""
    import numpy as np

    height, width = source.shape[:2]
    rows = np.clip(rows - 0.5, 0, height - 1)
    columns = np.clip(columns - 0.5, 0, width - 1)
    r0 = np.floor(rows).astype(int)
    c0 = np.floor(columns).astype(int)
    r1 = np.minimum(r0 + 1, height - 1)
    c1 = np.minimum(c0 + 1, width - 1)
    tr = (rows - r0)[..., None]
    tc = (columns - c0)[..., None]
    top = source[r0, c0] * (1 - tc) + source[r0, c1] * tc
    bottom = source[r1, c0] * (1 - tc) + source[r1, c1] * tc
    return top * (1 - tr) + bottom * tr


def bottom_line_average(sources):
    """RGBA (alpha 255) average of the ring's bottom line around the 360 degrees: texel row H - 2 of each sector image
    (HxWx4 arrays as shown), columns 0..W - 2, every sector weighted alike"""
    import numpy as np

    means = []
    for source in sources:
        height, width = source.shape[:2]
        row = source[max(0, height - 2), : max(1, width - 1), :3]
        means.append(row.mean(axis=0))
    return np.array([*np.mean(means, axis=0), 255], dtype=np.float32)


def tnfs_psx_horizon_to_spherical(sectors: List, settings, out_file_name: str):
    """
    Writes the sky sphere texture of the horizon images `hrz0`..`hrz7` (`sectors`, PIL images as the game shows them)
    with the settings of the INF file (`PsxHorizonSettings`)
    """
    import numpy as np
    from PIL import Image

    if len(sectors) != SECTOR_IMAGES:
        raise ValueError(f'The PSX horizon has {SECTOR_IMAGES} images, not {len(sectors)}')
    sources = [np.asarray(x.convert('RGBA'), dtype=np.float32) for x in sectors]
    y_offset, height = settings.screen_y_offset, settings.screen_ring_height
    top, bottom = y_offset - height, y_offset + height
    gradient_top = top + _c_div((y_offset - height) * settings.blend_ratio, 100)
    fade_bottom = bottom + (height - y_offset)

    # px below the eye level horizon line of the output rows, from the top (+90 deg) to the bottom
    elevation = (0.5 - (np.arange(OUT_HEIGHT) + 0.5) / OUT_HEIGHT) * math.pi
    screen_y = -PSX_FOCAL_PX * np.tan(elevation)

    # output columns: heading from the image centre to the right, sector 0 starts at heading 0
    heading = np.mod((np.arange(OUT_WIDTH) + 0.5) / OUT_WIDTH * 360 - 180, 360)
    sector_position = heading / 360 * SECTORS_PER_TURN
    sector = np.floor(sector_position).astype(int) % SECTORS_PER_TURN
    fraction = sector_position - np.floor(sector_position)
    mirrored = bool(settings.mirror) & (sector >= SECTOR_IMAGES)
    image_index = np.where(mirrored, SECTOR_IMAGES - 1 - sector % SECTOR_IMAGES, sector % SECTOR_IMAGES)
    # the u of a quad goes from 0 to W - 1, from its left point to its right one (swapped in mirrored sectors)
    u_fraction = np.where(mirrored, 1 - fraction, fraction)

    colour_top = np.array([*settings.colour_top, 255], dtype=np.float32)
    colour_bottom = np.array([*settings.colour_bottom, 255], dtype=np.float32)
    out = np.zeros((OUT_HEIGHT, OUT_WIDTH, 4), dtype=np.float32)
    out[..., 3] = 255
    out[screen_y < gradient_top] = colour_top
    gradient = (screen_y >= gradient_top) & (screen_y < top)
    if gradient.any():
        t = ((screen_y[gradient] - gradient_top) / (top - gradient_top))[:, None, None]
        out[gradient] = colour_top * (1 - t) + colour_bottom * t

    band = (screen_y >= top) & (screen_y < bottom)
    band_y = screen_y[band]
    for index, source in enumerate(sources):
        columns = np.nonzero(image_index == index)[0]
        if not len(columns) or not len(band_y):
            continue
        source_height, source_width = source.shape[:2]
        rows = (band_y - top) / (bottom - top) * (source_height - 1)
        u = u_fraction[columns] * (source_width - 1)
        samples = _sample(source, rows[:, None], u[None, :])
        out[np.ix_(np.nonzero(band)[0], columns)] = samples

    ground = bottom_line_average(sources)
    out[screen_y >= bottom] = ground
    fade = (screen_y >= bottom) & (screen_y < fade_bottom)
    if fade.any():
        below = sources[0][max(0, sources[0].shape[0] - 2), 0].copy()
        below[3] = 255
        t = ((screen_y[fade] - bottom) / (fade_bottom - bottom))[:, None, None]
        out[fade] = below * (1 - t) + ground * t
    Image.fromarray(np.round(out).astype(np.uint8), 'RGBA').save(out_file_name)


def horizon_info_path(psh_path: str) -> Optional[str]:
    """The horizon settings file of a PSX track textures file `Z<track><time>.PSH`: `Z<track><time>.INF` next to it
    (the game builds both names the same way, `z%s%c.psh` / `z%s%c.inf`, `tnfs_game_init_800485d0`), any case. The
    German textures `ZG<track><time>.PSH` have no INF of their own: the one of `Z<track><time>` (not verified in the
    game). None when there is none"""
    directory, name = os.path.split(psh_path)
    stem = os.path.splitext(name)[0]
    candidates = [f'{stem}.inf'.lower()]
    if stem.lower().startswith('zg'):
        candidates.append(f'z{stem[2:]}.inf'.lower())
    try:
        names = {x.lower(): x for x in os.listdir(directory or '.')}
    except OSError:
        return None
    for candidate in candidates:
        if candidate in names:
            return os.path.join(directory, names[candidate])
    return None


def read_horizon_settings(info_path: str):
    """`PsxHorizonSettings` of a PSX `.INF` file, None when it has fewer values than the game reads"""
    from resources.eac.psx import TnfsPsxHorizonInfo, parse_psx_horizon_settings

    with open(info_path, 'rb') as f:
        data = TnfsPsxHorizonInfo().unpack_from_bytes(f.read())
    return parse_psx_horizon_settings(data['text'])

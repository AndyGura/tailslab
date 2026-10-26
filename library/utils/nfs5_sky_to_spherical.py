"""
The sky of an NFS5 (Porsche Unleashed) track (`GameData/Track/Sky/<track>.fsh`, `.txt`, `.bin`, picked by the track
name: `alps.crp` -> `Alps.*`, `monaco1.crp` -> `Monaco1.*`) on an equirectangular sky sphere texture
(`sky_spherical.py`).

UNVERIFIED: the executable's code is encrypted (SafeDisc: `PORSCHE.ICD`, `Porsche.exe` is only the loader), so nothing
here was checked against the game's renderer. The reading of the files:
- `<track>.txt` (`parse_nfs5_sky_text`): sky levels by computer capability; the first one (HIGH) is used, weather
  region A (region B is another set of the same values, probably for another part of the track). "The number of
  textures determines how many layers you have": layer i is cloud texture i (`flat` = untextured) coloured by sky
  map i, drawn one over the other, alpha blended. Wind, move ratio and warp only animate them: left out (a static
  frame).
- The sky maps (16x16, ARGB) are top-down maps of the whole dome: Foothills' darkest blue in the middle, pale at the
  edges, Monaco's and Industrial's dark middle and light edges, Alps' sun glow near an edge. A sky map spans the
  dome once, `u = 0.5 + 0.5 * x`, `v = 0.5 + 0.5 * z` of the unit view direction (orthographic projection of a
  hemisphere: the texture edge on the horizon); the layer's texture repeats `scale_x` / `scale_y` times over the
  same projection, which is why Coastal's 2 x 6 do nothing (its only layer is `flat`). Guessed: a hemisphere (no
  dome height found in the `.bin`), u along +X, v along +Z (Alps' sun glow lands 39 degrees right of the centre
  column, about 30 degrees up).
- The horizon: `horz` cut into `strips_per_bitmap` horizontal strips (`.bin` header, `Nfs5SkySettings`: 2 strips of
  256x128, Monaco 1 of 256x256), drawn on a cylinder around the camera of radius `horizon_radius` from
  `horizon_bottom` to `horizon_top` (world units relative to the eye), in `horizon_segments` equal segments around
  it, segment i showing strip `horizon_strips_a[i] & 0xFF` (modulo the strip count) mirrored with bit 0x100.
  Segment 0 starts at the centre column (+X) and the strips run to the right. The last texel row of every strip is
  transparent padding (like the TNFS horizon rows 1..H-2): the band spans the rows above it. All of this is read from
  value patterns of the `.bin` header, not verified. The other horizon bitmaps (`hor0`, `hor1`...) are copies of
  `horz` with other details and are not used (the Foothills table 2, 3, 2, 3 may mean that strips count on through
  them: same picture there).
- `hzcl` (16x2, two colours, white in most tracks, matching neither the band's bottom nor the sky's edge) is not
  used: its role is unknown (a tint?).
- Below the horizon: one flat colour, the mean of the band's lowest drawn row with opaque texels (the game's terrain
  covers it; its clear colour is unknown), also behind the transparent parts of the band there.
"""

import math
import re
import struct
from typing import Dict, List, NamedTuple, Optional, Tuple

from library.utils.sky_spherical import OUT_HEIGHT, OUT_WIDTH, blend_over, output_angles, sample_bilinear


class Nfs5SkyLayer(NamedTuple):
    """A sky layer: its sky map (colour and alpha over the whole dome) and texture (None: `flat`, untextured),
    repeated `scale_x` / `scale_y` times over the dome"""

    sky_map: Optional[str]
    texture: Optional[str]
    scale_x: float
    scale_y: float


class Nfs5SkySettings(NamedTuple):
    """The `.bin` header values used here (see `Nfs5SkyBin` in `resources/eac/maps/nfs5_sky.py`)"""

    horizon_segments: int
    strips_per_bitmap: int
    horizon_bottom: float
    horizon_top: float
    horizon_radius: float
    horizon_strips_a: Tuple[int, ...]


def _is_texture(name: str) -> bool:
    return name.lower() not in ('none', 'flat', 'noise', 'speed')


def parse_nfs5_sky_text(text: str) -> List[Nfs5SkyLayer]:
    """Layers of weather region A of the first sky level of a `GameData/Track/Sky/*.txt` file. MULTINORMAL levels:
    capability, type, blocks the sun, then per region 3 sky maps, 3 X scales, 3 Y scales, move ratio, 3 wind speeds,
    3 wind directions, warp speed, warp amount, then 3 cloud textures. basic levels: capability, type, blocks the sun,
    then per region sky map, sky map alpha, cloud texture, X scale, Y scale, move ratio, wind speed, wind direction,
    warp speed, warp amount"""
    blocks = re.findall(r'BEGIN(.*?)END', text, re.S)
    if not blocks:
        return []
    tokens = [token for line in blocks[0].splitlines() if not line.strip().startswith('#') for token in line.split()]
    if len(tokens) < 3:
        return []
    level_type = tokens[1].lower()
    values = tokens[3:]
    layers = []
    if level_type == 'basic':
        sky_map, _, texture, scale_x, scale_y = values[:5]
        if texture.lower() != 'none':
            layers.append(
                Nfs5SkyLayer(
                    sky_map if _is_texture(sky_map) else None,
                    texture if _is_texture(texture) else None,
                    float(scale_x),
                    float(scale_y),
                )
            )
    else:
        region_a = values[:18]
        textures = values[36:39]
        # "the number of textures determines how many layers you have"
        for i, texture in enumerate(textures):
            if texture.lower() == 'none':
                continue
            sky_map = region_a[i]
            layers.append(
                Nfs5SkyLayer(
                    sky_map if _is_texture(sky_map) else None,
                    texture if _is_texture(texture) else None,
                    float(region_a[3 + i]),
                    float(region_a[6 + i]),
                )
            )
    return layers


def read_nfs5_sky_settings(data: bytes) -> Optional[Nfs5SkySettings]:
    """Horizon values of a `GameData/Track/Sky/<track>.bin` (`Nfs5SkyBin`), None for another format"""
    from resources.eac.maps.nfs5_sky import Nfs5SkyBin

    if len(data) < 0x54 or struct.unpack_from('<I', data, 0)[0] not in (7, 9):
        return None
    values = Nfs5SkyBin().unpack_from_bytes(data)
    settings = Nfs5SkySettings(
        values['horizon_segments'],
        values['strips_per_bitmap'],
        values['horizon_bottom'],
        values['horizon_top'],
        values['horizon_radius'],
        tuple(values['horizon_strips_a']),
    )
    if not 0 < settings.horizon_segments <= 8 or not 0 < settings.strips_per_bitmap <= 8:
        return None
    if settings.horizon_radius <= 0 or settings.horizon_top <= settings.horizon_bottom:
        return None
    return settings


def horizon_strips(textures: Dict[str, object], strips_per_bitmap: int) -> List[object]:
    """Horizon strips (RGBA float arrays): `horz` cut into `strips_per_bitmap` rows. The other horizon bitmaps
    (`hor0`, `hor1`...) are copies of it with other details (Industrial `hor0`: opaque water, `horz`: transparent
    water with the reflections of the lights): not used"""
    image = next((textures[n] for n in textures if n.lower() == 'horz'), None)
    if image is None:
        return []
    height = image.shape[0] // strips_per_bitmap
    return [image[i * height : (i + 1) * height] for i in range(strips_per_bitmap)]


def _fill_colour(strips) -> Tuple[float, float, float]:
    """Mean colour of the lowest drawn texel row of the strips that has opaque texels (alpha weighted): the colour
    below the horizon band"""
    import numpy as np

    for row in range(strips[0].shape[0] - 2, -1, -1):
        texels = np.concatenate([strip[min(row, strip.shape[0] - 2)] for strip in strips])
        weights = texels[:, 3]
        if weights.sum() >= 0.5 * 255 * len(texels):
            return tuple((texels[:, :3] * weights[:, None]).sum(0) / weights.sum())
    return 0.0, 0.0, 0.0


def nfs5_sky_to_spherical(
    layers: List[Nfs5SkyLayer],
    textures: Dict[str, object],
    settings: Optional[Nfs5SkySettings],
    out_file_name: Optional[str] = None,
    width: int = OUT_WIDTH,
    height: int = OUT_HEIGHT,
):
    import numpy as np

    heading, elevation = output_angles(width, height)
    h, e = np.meshgrid(heading, np.maximum(elevation, 0))
    # unit view directions, game axes: their horizontal position is the dome point's over the dome radius
    dx = (np.cos(h) * np.cos(e)).reshape(-1)
    dz = (-np.sin(h) * np.cos(e)).reshape(-1)
    out = np.zeros((height * width, 4))
    out[:, 3] = 255
    white = np.full((height * width, 4), 255.0)
    # sky dome: per layer the sky map spans the dome once, the texture repeats `scale` times over it
    for layer in layers:
        sky_map = textures.get(layer.sky_map) if layer.sky_map else None
        texture = textures.get(layer.texture) if layer.texture else None
        colour = sample_bilinear(sky_map, 0.5 + 0.5 * dx, 0.5 + 0.5 * dz) if sky_map is not None else white
        if texture is not None:
            colour = (
                colour * sample_bilinear(texture, 0.5 + 0.5 * layer.scale_x * dx, 0.5 + 0.5 * layer.scale_y * dz) / 255
            )
        blend_over(out, colour)
    out = out.reshape(height, width, 4)
    strips = horizon_strips(textures, settings.strips_per_bitmap) if settings else []
    if strips:
        # below the horizon: one flat colour, under the band where it is transparent too
        below = elevation < 0
        out[below, :, :3] = _fill_colour(strips)
        # horizon band on a cylinder around the eye
        y = settings.horizon_radius * np.tan(elevation)
        rows = (settings.horizon_top - y) / (settings.horizon_top - settings.horizon_bottom)
        turn = np.mod(heading / (2 * math.pi), 1.0) * settings.horizon_segments
        segment = np.minimum(np.floor(turn).astype(int), settings.horizon_segments - 1)
        u = turn - segment
        band = np.zeros((height, width, 4))
        for s in range(settings.horizon_segments):
            entry = settings.horizon_strips_a[s]
            strip = strips[(entry & 0xFF) % len(strips)]
            columns = segment == s
            su = 1 - u[columns] if entry & 0x100 else u[columns]
            # the last texel row of every strip is transparent padding: the band spans the rows above it
            rows_in_strip = strip.shape[0]
            sv = np.clip(rows * (rows_in_strip - 1), 0.5, rows_in_strip - 1.5) / rows_in_strip
            vv, uu = np.meshgrid(sv, su, indexing='ij')
            band[:, columns] = sample_bilinear(strip, uu, vv, False)
        drawn = np.broadcast_to(((rows >= 0) & (rows <= 1))[:, None], (height, width))
        blend_over(out, band[drawn], drawn)
    if out_file_name:
        from library.utils.sky_spherical import save_rgba

        save_rgba(out, out_file_name)
    return out


def _sibling(path: str, extension: str) -> Optional[str]:
    """`<name>.<extension>` next to `path`, any case (Forest.fsh has forest.txt)"""
    import os

    directory, base = os.path.split(path)
    wanted = os.path.splitext(base)[0].lower() + extension
    try:
        return next((os.path.join(directory, n) for n in os.listdir(directory) if n.lower() == wanted), None)
    except OSError:
        return None


def is_nfs5_sky_archive(id: Optional[str]) -> bool:
    """`GameData/Track/Sky/<track>.fsh` of NFS5 (a file of its own, with the `.txt` next to it)"""
    if not id or '__' in id:
        return False
    from library.loader import id_to_path

    path = id_to_path(id).replace('\\', '/')
    return re.search(r'/track/sky/[^/]+\.fsh$', path, re.I) is not None and _sibling(path, '.txt') is not None


def serialize_nfs5_sky(items, path: str, id: str) -> List[str]:
    """`spherical.png` in the folder of the exported sky FSH (`items`: (alias, data, block) of its images)"""
    import numpy as np

    from library.loader import id_to_path
    from library.utils import path_join
    from library.utils.id import join_id
    from resources.eac.bitmaps import EacImage
    from serializers import ImageSerializer

    fsh_path = id_to_path(id)
    with open(_sibling(fsh_path, '.txt'), 'r', errors='replace') as f:
        layers = parse_nfs5_sky_text(f.read())
    bin_path = _sibling(fsh_path, '.bin')
    settings = None
    if bin_path:
        with open(bin_path, 'rb') as f:
            settings = read_nfs5_sky_settings(f.read())
    textures = {}
    for i, (alias, data, block) in enumerate(items):
        if isinstance(block, EacImage) and alias not in textures and not isinstance(data, Exception):
            image = ImageSerializer().to_image(data, block, join_id(id, 'children', str(i), 'item', 'data'))
            textures[alias] = np.asarray(image, dtype=np.float64)
    if not layers and settings is None:
        return []
    out_path = path_join(path, 'spherical.png')
    nfs5_sky_to_spherical(layers, textures, settings, out_file_name=out_path)
    return [out_path]

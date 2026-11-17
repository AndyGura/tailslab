"""
The sky of an NFS5 (Porsche Unleashed) track (`GameData/Track/Sky/<track>.fsh`, `.txt`, `.bin`, picked by the track
name: `alps.crp` -> `Alps.*`, `monaco1.crp` -> `Monaco1.*`) on an equirectangular sky sphere texture
(`sky_spherical.py`: column u looks at the heading 360 u - 180 degrees clockwise from +Z, game axes, Y up).

Checked against the unprotected Porsche.exe (nfs-web `decomp/nfs5`; the retail one is SafeDisc encrypted). `bin[o]` is
the `.bin` file at byte offset o (`Nfs5SkyBin`, loaded as it is: the sky object's settings pointer +0x104):
- Sky levels (`.txt`, FUN_0045fb80): the block of the computer's capability (`all` matches every one); HIGH is used.
  `basic` makes a BasicSky (FUN_0045adf0), `multinormal` a MultinormalSky (FUN_0045b5a0, one layer per texture that is
  not `none`, layer i: sky map i, texture i, scales i; `flat` takes a default texture). Weather region A is used
  (the sky map mesh is built from the maps of both regions, FUN_0045dd90: how it mixes them is not traced). The
  `...water` level types (flag 0x200: the second dome set bin[0xB3C..0xB48], scale 1, a dome hanging below the eye)
  are in no track's file.
- Dome (FUN_00460ec0 / FUN_00460f40): a 16x16 vertex grid, side S = bin[0x40], row i at a = -S/2 + i S/15, column j
  at b = S/2 - j S/15, height y = h - k (a^2 + b^2) (h = bin[0x48], k = bin[0x44]), turned by R = bin[0x3C] turns:
  x = sin R a + cos R b, z = cos R a - sin R b; everything times bin[0xCE4], which changes no direction from the eye.
  It is centred on the eye with the world's axes (FUN_0045d4f0). Pixel (column j, row i) of the 16x16 sky map is the
  colour (alpha included) of vertex (i, j) (FUN_0045dd90), Gouraud interpolated; the layer texture's UV is
  (j su, i sv) (FUN_0045ec40, su / sv the X / Y scale factors; the wind scroll is 0 in a still frame). Here every
  ray is cast against the paraboloid itself (the game draws its 15x15 flat quads) and the vertex values are
  interpolated bilinearly over the grid at the hit; rays missing the grid square see nothing of that layer.
- Horizon (SkyHorizon: FUN_00459b50, geometry FUN_00459d30, draw FUN_0045a1a0, after the levels): 16 flat quads on a
  cylinder of radius 400 around the eye, point k at (400 sin 2 pi (A + k / 16), y, 400 cos 2 pi (A + k / 16)),
  A = bin[0x04] turns; from y = bin[0x14] to bin[0x14] + bin[0x18]. Quad i shows cell `bin[0x1C + 2 i] & 0xFF` of
  `horz` (column idx % bin[0x0C], row idx // bin[0x0C], bin[0x10] rows), u from the cell's left edge at point i to
  its right edge at point i + 1 (swapped with a high byte), v from (row + 0.01) / rows at the top to
  (row + 0.98) / rows at the bottom. Vertex colours from `hzcl` (16x2): top vertices row 0, bottom vertices row 1, at
  column (bin[0x08] + k) % 16 for point k (the copy for the draw's wrap-around takes column k + 1 for the right top
  vertex: an EA slip, left out). Their blend with the texture (modulate assumed) and the colour interpolation across
  the quad's two triangles (bilinear here) are not traced. The draw culls to the camera heading +-0.125 turn:
  irrelevant for a panorama.
- Not traced: the layers' blend states (alpha blending, one over the other in the file's order), the sky map alpha
  `noise` / `speed` of basic levels, the sun, wind, warp and move ratio. Below the horizon: one flat colour, the
  alpha weighted mean of the band's bottom edge (the game's terrain covers it; its clear colour is unknown), also
  behind the band's transparent parts there.
"""

import math
import re
import struct
from typing import Dict, List, NamedTuple, Optional, Tuple

from library.utils.sky_spherical import (
    OUT_HEIGHT,
    OUT_WIDTH,
    blend_over,
    output_angles,
    output_directions,
    sample_bilinear,
)

HORIZON_RADIUS = 400.0  # Porsche.exe 0x5b25c4
HORIZON_SEGMENTS = 16
DOME_GRID = 15  # quads per side, 16x16 vertices


class Nfs5SkyLayer(NamedTuple):
    """A sky layer: its sky map (colour and alpha of the dome's 16x16 vertices) and texture (None: `flat`,
    untextured), its UV `scale_x` / `scale_y` per vertex step"""

    sky_map: Optional[str]
    texture: Optional[str]
    scale_x: float
    scale_y: float


class Nfs5SkySettings(NamedTuple):
    """The `.bin` values used here (see `Nfs5SkyBin` in `resources/eac/maps/nfs5_sky.py`)"""

    horizon_rotation: float
    horizon_colour_start: int
    horizon_cell_columns: int
    horizon_cell_rows: int
    horizon_bottom: float
    horizon_height: float
    horizon_cells: Tuple[int, ...]
    dome_rotation: float
    dome_size: float
    dome_curvature: float
    dome_height: float


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
    """Horizon and dome values of a `GameData/Track/Sky/<track>.bin` (`Nfs5SkyBin`), None for another format"""
    if len(data) < 0x4C or struct.unpack_from('<I', data, 0)[0] not in (7, 9):
        return None
    rotation, colour_start, columns, rows, bottom, height = struct.unpack_from('<fIIIff', data, 0x04)
    cells = struct.unpack_from('<16H', data, 0x1C)
    dome = struct.unpack_from('<4f', data, 0x3C)
    if not 0 < columns <= 16 or not 0 < rows <= 16 or height <= 0:
        return None
    return Nfs5SkySettings(rotation, colour_start, columns, rows, bottom, height, cells, *dome)


def _texture(textures: Dict[str, object], name: str):
    return next((textures[n] for n in textures if n.lower() == name), None)


def dome_hits(directions, settings: Nfs5SkySettings):
    """Grid coordinates (fi = row, fj = column, 0..15) where the rays (unit directions, game axes) hit the dome, and
    the mask of the rays hitting it within the grid square"""
    import numpy as np

    dx, dy, dz = directions[..., 0], directions[..., 1], directions[..., 2]
    sin_r = math.sin(2 * math.pi * settings.dome_rotation)
    cos_r = math.cos(2 * math.pi * settings.dome_rotation)
    # the rotation (a, b) -> (x, z) is its own inverse
    da = sin_r * dx + cos_r * dz
    db = cos_r * dx - sin_r * dz
    # t dy = h - k t^2 (da^2 + db^2): the smallest positive t
    qa = settings.dome_curvature * (da * da + db * db)
    h = settings.dome_height
    with np.errstate(divide='ignore', invalid='ignore'):
        disc = dy * dy + 4 * qa * h
        root = np.sqrt(np.maximum(disc, 0))
        small = np.abs(qa) < 1e-12
        t_lin = h / dy
        t1 = np.where(small, t_lin, (-dy - root) / (2 * qa))
        t2 = np.where(small, t_lin, (-dy + root) / (2 * qa))
        valid = small | (disc >= 0)
        t1 = np.where(valid & (t1 > 0), t1, np.inf)
        t2 = np.where(valid & (t2 > 0), t2, np.inf)
        t = np.minimum(t1, t2)
        step = settings.dome_size / DOME_GRID
        fi = (t * da + settings.dome_size / 2) / step
        fj = (settings.dome_size / 2 - t * db) / step
        hit = np.isfinite(t) & (fi >= 0) & (fi <= DOME_GRID) & (fj >= 0) & (fj <= DOME_GRID)
    return np.where(hit, fi, 0), np.where(hit, fj, 0), hit


def _horizon(settings: Nfs5SkySettings, textures, heading, elevation):
    """(band colours (height, width, 4), drawn mask, the band's bottom edge colours per column), None without `horz`"""
    import numpy as np

    horz = _texture(textures, 'horz')
    if horz is None:
        return None
    hzcl = _texture(textures, 'hzcl')
    delta = 2 * math.pi / HORIZON_SEGMENTS
    turn = np.mod(heading / (2 * math.pi) - settings.horizon_rotation, 1.0) * HORIZON_SEGMENTS
    segment = np.minimum(np.floor(turn).astype(int), HORIZON_SEGMENTS - 1)
    phi = (turn - segment) * delta
    # where the ray crosses the flat quad: chord parameter from point i, horizontal distance
    t = np.sin(phi) / (np.sin(phi) + np.sin(delta - phi))
    distance = HORIZON_RADIUS * math.cos(delta / 2) / np.cos(phi - delta / 2)
    columns, rows = settings.horizon_cell_columns, settings.horizon_cell_rows
    cells = np.array(settings.horizon_cells)[segment]
    index = cells & 0xFF
    col, row = index % columns, index // columns
    swapped = (cells >> 8) != 0
    u0 = np.where(swapped, col + 1, col) / columns
    u1 = np.where(swapped, col, col + 1) / columns
    u = u0 + t * (u1 - u0)
    v_top, v_bottom = (row + 0.01) / rows, (row + 0.98) / rows
    top = settings.horizon_bottom + settings.horizon_height
    y = distance[None, :] * np.tan(elevation)[:, None]
    s = (top - y) / settings.horizon_height
    drawn = (s >= 0) & (s <= 1)
    tint = hzcl is not None and hzcl.shape[0] >= 2 and hzcl.shape[1] >= HORIZON_SEGMENTS

    def colours(s_rows):
        v = v_top + s_rows * (v_bottom - v_top)
        colour = sample_bilinear(horz, np.broadcast_to(u, v.shape), v)
        if tint:
            k0 = (settings.horizon_colour_start + segment) % HORIZON_SEGMENTS
            k1 = (k0 + 1) % HORIZON_SEGMENTS
            top_c = hzcl[0, k0] + t[:, None] * (hzcl[0, k1] - hzcl[0, k0])
            bottom_c = hzcl[1, k0] + t[:, None] * (hzcl[1, k1] - hzcl[1, k0])
            colour = colour * (top_c + s_rows[..., None] * (bottom_c - top_c)) / 255
        return colour

    band = colours(np.clip(s, 0, 1))
    edge = colours(np.ones((1, len(heading))))[0]
    return band, drawn, edge


def nfs5_sky_to_spherical(
    layers: List[Nfs5SkyLayer],
    textures: Dict[str, object],
    settings: Nfs5SkySettings,
    out_file_name: Optional[str] = None,
    width: int = OUT_WIDTH,
    height: int = OUT_HEIGHT,
):
    import numpy as np

    heading, elevation = output_angles(width, height)
    out = np.zeros((height, width, 4))
    out[..., 3] = 255
    fi, fj, hit = dome_hits(output_directions(width, height), settings)
    for layer in layers:
        sky_map = textures.get(layer.sky_map) if layer.sky_map else None
        texture = textures.get(layer.texture) if layer.texture else None
        if sky_map is not None:
            # vertex (i, j) has pixel (column j, row i): the vertices sit on the texel centres
            map_h, map_w = sky_map.shape[:2]
            colour = sample_bilinear(sky_map, (fj[hit] + 0.5) / map_w, (fi[hit] + 0.5) / map_h, False)
        else:
            colour = np.full((int(hit.sum()), 4), 255.0)
        if texture is not None:
            colour = colour * sample_bilinear(texture, fj[hit] * layer.scale_x, fi[hit] * layer.scale_y) / 255
        blend_over(out, colour, hit)
    horizon = _horizon(settings, textures, heading, elevation)
    if horizon is not None:
        band, drawn, edge = horizon
        weights = edge[:, 3]
        fill = (edge[:, :3] * weights[:, None]).sum(0) / weights.sum() if weights.sum() > 0 else np.zeros(3)
        out[elevation < 0, :, :3] = fill
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
    """`spherical.png` in the folder of the exported sky FSH (`items`: (alias, data, block) of its images); none
    without a readable `.bin` (the dome and horizon geometry)"""
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
    if settings is None:
        return []
    textures = {}
    for i, (alias, data, block) in enumerate(items):
        if isinstance(block, EacImage) and alias not in textures and not isinstance(data, Exception):
            image = ImageSerializer().to_image(data, block, join_id(id, 'children', str(i), 'item', 'data'))
            textures[alias] = np.asarray(image, dtype=np.float64)
    out_path = path_join(path, 'spherical.png')
    nfs5_sky_to_spherical(layers, textures, settings, out_file_name=out_path)
    return [out_path]

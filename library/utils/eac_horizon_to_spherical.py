"""
The skies of NFS2 SE (3D accelerated version), NFS3 and NFS4 on an equirectangular sky sphere texture `spherical.png`,
placed as the games draw them. Same output as `nfs1_panorama_to_spherical` (TNFS): 2048x1024 RGBA, eye level on the
middle row, top row straight up, bottom row straight down; the centre column looks along the game's +X axis, a quarter
width right of it along -Z, a quarter width left of it along +Z (game axes X right, Y up, Z forward); columns run left
to right as a viewer standing in the game world sees the panorama. Headings below are turns clockwise from +Z seen from
above (+X at 0.25), as the games measure them (`atan2(x, z)`).

All three games draw the sky with the same horizon code (`hrzsku.c`, settings `resources/eac/horizons.py`), in this
order, every part centred on the camera (rotation only, no translation):

1. Clear the screen to the SKY top colour (black with the black horizon flag; NFS2 SE then draws nothing else).
2. SKY quads: 16 sectors of 22.5 degrees from `base + middle` up to `base + height` (heights relative to the eye),
   Gouraud shaded from the ring colour of their vertices at the bottom to the SKY top colour at the top. Ring vertex k
   (k = 0..15, 16 = 0) has colour sun + (opposite - sun) * k / 8 for k = 0..7 and vertex 15 - k the same: the sun
   colour around vertices 15..0, the opposite colour around 7..8.
3. Sun sprite (NFS3, NFS4) unless it is drawn in front of the clouds, then the cloud dome, then the sun in front.
4. EARTH quads from `base` to `base + middle`, Gouraud shaded from the EARTH base colour to the EARTH top colour.
5. Horizon pixmap: sector k shows strip k % 8 (with the mirror flag sectors 8..15 show strips 7..0 mirrored) from
   `base + pixmap bottom` up to `base + pixmap bottom + (pixmap top - pixmap bottom) * strip height / tallest strip
   height` (shorter strips end lower, the texel size is the same for all), texture alpha blended.

Verified in the executables (nfs-web `decomp/`: nfs2sea.exe, nfs3.exe, nfs4.exe; addresses in the functions below).
How each game places the ring:

- NFS2 SE (`Hrz_Init2DRing` 0x42e750, draw 0x42daf0): ring point k at heading `angle + k / 16` (angle in degrees,
  `(deg << 16) / 360`), `(R sin, y, R cos)`. Every point is projected as if it were `flat projection distance` D deep
  (0x42e660 overwrites the depth before projecting): a world height h is at screen height `f * h / D`, so the band is
  straight on the screen. The texture keeps the view centre's mapping: heading psi shows the ring at psi, height h at
  elevation `atan(h / D)`. Heights are fractions of the Gouraud height in 16.16 integer maths (`0x10000 / height`
  truncated), as the game computes them.
- NFS3 (0x479160, 0x479500) and NFS4 (0x4ca730, 0x4cb1b0): no ring around the camera but a straight wall of sectors
  across the view direction at distance R, one sector `2 pi R / 16` wide (the arc of 22.5 degrees), scrolled with the
  heading: the sector coordinate at the view centre is `16 * (psi + 0.53127 + angle) + 3.5` with 8 sectors (NFS3) or
  `16 * (psi + 0.5 + angle) + 8` with 16 sectors (NFS4), angle in turns (NFS3: degrees as `(deg << 16) / 360 /
  65536`). The texture keeps the view centre's mapping (one sector per 22.5 degrees there, exactly as the game shows
  it), height h at elevation `atan(h / R)`. So NFS3 sector k starts at heading `k / 16 + 0.25 - angle`, NFS4 sector k
  at `k / 16 - angle`.
- Cloud dome: a 13 x 13 grid of points around the camera, y = `offset + height * cos(2 pi r / period)` at horizontal
  distance r, drawn in true perspective: NFS2 SE 0x42d930 (x, z from -1000 to 800 in steps of 150, period 4000,
  texture `CLD<track>` of `SKY.FSH` once per grid cell, white; poly type 0xb, added: `grAlphaBlendFunction(SRC_ALPHA,
  ONE)` in its handler 0x42bba0; track 7: type 0xa with alpha 0x7f, the normal alpha blending); NFS3 0x47ae10 / NFS4
  0x4c95a0 (x, z from -3000 to 2400 in steps of 450, period 12000, NFS3 height = 3 * the file's, texture `CLDD` of
  `SKY.FSH` / `sky.qfs` with u = i * U scale, v = j * V scale at grid point (i, j), vertex colour and alpha = a
  brightness: bright minus a random value below variance, put through `(sign * sqrt(|b - 128| / 128) + 1) * 127.5`,
  smoothed 20 times over the 5 x 5 neighbours, clamped to 0..bright, the point lowered by `height * 0.5 * nimbus *
  b / 255`; NFS3 nimbus = trunc(percent / 100)). The texture also scrolls with the camera position and the wind:
  for a static frame at the origin it does not.
- Sun (NFS3 0x47a970 / 0x479ed0, NFS4 0x4c9c30): a square sprite at `3000 * (cos A, cos B, sin A)` (A, B in degrees
  in NFS3, from the text `A<a> B<b> R<r>` of the `SUN*` image; in turns in NFS4 `Tr.ini` `[sun]`), corners `size`
  from its centre (size = 10 * R, NFS4 `radius`), upright, additive unless `NOADD` / `additive=0`.

Not verified, converter choices (marked in the report too):
- Blend modes of the NFS3 / NFS4 clouds (their Direct3D states are in the driver DLL): additive read as NFS2 SE's
  verified one, Glide (source alpha, one): `colour + texel * vertex colour * vertex alpha` (NFS3 / NFS4 set both
  colour and alpha to the brightness), type 2 ("blend") as alpha blending. The brightness of the NFS3 / NFS4 cloud
  vertices is random in the game (a new pattern per race): a fixed seed here.
- Fog is not applied (NFS3 without hardware fog mixes the EARTH colours and the pixmap with the fog colour by the
  "effect on pixmap" percentage, with hardware fog the card fogs them by depth; NFS4 has only the hardware fog).
- Below the band the game shows the clear colour (terrain covers it); the converter does the same.
"""

import math
import os
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from library.utils.nfs1_panorama_to_spherical import OUT_HEIGHT, OUT_WIDTH

SECTORS = 16
STRIPS = 8
# the sun sprite of NFS3 / NFS4 is 3000 units away along its direction vector
SUN_DISTANCE = 3000.0
# the random cloud brightness pattern of NFS3 / NFS4: a new one in every race in the game, a fixed one here
CLOUD_SEED = 1


def _c_div(a: int, b: int) -> int:
    """Integer division rounding towards 0, as C does"""
    quotient = abs(a) // abs(b)
    return quotient if (a >= 0) == (b > 0) else -quotient


def _rgb(color):
    import numpy as np

    return np.array(color[:3], dtype=np.float64)


def ring_colors(sun, opposite):
    """The 17 SKY base colours of the ring vertices (vertex 16 = vertex 0), as the games build them in 16.16 steps of
    1/8 (NFS2 SE 0x42e910, NFS3 0x478340, NFS4 0x4c9c30)"""
    import numpy as np

    colors = np.zeros((SECTORS + 1, 3))
    for channel in range(3):
        value = int(sun[channel]) << 16
        step = (int(opposite[channel]) - int(sun[channel])) * 0x2000
        for k in range(8):
            colors[k, channel] = colors[15 - k, channel] = (value >> 16) & 0xFF
            value += step
    colors[16] = colors[0]
    return colors


@dataclass
class CloudDome:
    """The cloud dome: points (13 x 13) of the grid with their heights (relative to the eye), texture coordinates and
    colour (RGBA 0..1 per point), the texture (H x W x 4, 0..255) and the blend mode ('add' or 'blend')"""

    xs: Sequence[float]
    zs: Sequence[float]
    heights: object
    us: object
    vs: object
    colors: object
    texture: object
    mode: str


@dataclass
class SunSprite:
    direction: Sequence[float]
    half_size: float
    texture: object
    additive: bool
    in_front: bool


@dataclass
class HorizonSky:
    """Everything the horizon code draws, in world units relative to the eye"""

    # heading (turns) -> sector coordinate 0..16 at that heading
    sector_at: Callable
    # depth the band heights are projected at: elevation of height h is atan(h / distance)
    distance: float
    clear_color: Sequence[float]
    sky_top_color: Sequence[float]
    ring: object
    earth_top_color: Sequence[float]
    earth_bottom_color: Sequence[float]
    base_y: float
    middle_y: float
    top_y: float
    # the 8 strips (H x W x 4, 0..255) or None without a pixmap
    strips: Optional[List[object]] = None
    mirror: bool = False
    pixmap_bottom_y: float = 0.0
    # top of the pixmap of each strip
    pixmap_top_y: Sequence[float] = ()
    draw_band: bool = True
    clouds: Optional[CloudDome] = None
    sun: Optional[SunSprite] = None


def _sample(texture, u, v, wrap: bool):
    """Bilinear samples of an H x W x 4 float array at texture coordinates u, v (0..1 over the texture, texel i spans
    i / size .. (i + 1) / size), repeated with `wrap`, clamped to the edge texels otherwise"""
    import numpy as np

    height, width = texture.shape[:2]
    x = np.asarray(u, dtype=np.float64) * width - 0.5
    y = np.asarray(v, dtype=np.float64) * height - 0.5
    x0 = np.floor(x)
    y0 = np.floor(y)
    tx = (x - x0)[..., None]
    ty = (y - y0)[..., None]
    x0 = x0.astype(np.int64)
    y0 = y0.astype(np.int64)
    if wrap:
        x1, y1 = (x0 + 1) % width, (y0 + 1) % height
        x0, y0 = x0 % width, y0 % height
    else:
        x1, y1 = np.clip(x0 + 1, 0, width - 1), np.clip(y0 + 1, 0, height - 1)
        x0, y0 = np.clip(x0, 0, width - 1), np.clip(y0, 0, height - 1)
    top = texture[y0, x0] * (1 - tx) + texture[y0, x1] * tx
    bottom = texture[y1, x0] * (1 - tx) + texture[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def output_headings(width: int = OUT_WIDTH):
    """Heading (turns clockwise from +Z) of the output columns: +X (0.25) at the centre, growing to the right"""
    import numpy as np

    return (np.arange(width) + 0.5) / width - 0.25


def output_elevations(height: int = OUT_HEIGHT):
    import numpy as np

    return (0.5 - (np.arange(height) + 0.5) / height) * math.pi


def _directions(headings, elevations):
    """Unit view directions (rows x columns x 3, game axes)"""
    import numpy as np

    psi = headings[None, :] * 2 * math.pi
    e = elevations[:, None]
    return np.stack(np.broadcast_arrays(np.sin(psi) * np.cos(e), np.sin(e) + 0 * psi, np.cos(psi) * np.cos(e)), axis=-1)


def _draw_clouds(out, dome: CloudDome, headings, elevations):
    """Adds the cloud dome to `out` (rows x columns x 3, 0..255): the first point of the dome's surface along each
    view ray (bilinear height field over the grid, found by marching and bisection)"""
    import numpy as np

    xs = np.asarray(dome.xs, dtype=np.float64)
    zs = np.asarray(dome.zs, dtype=np.float64)
    heights = np.asarray(dome.heights, dtype=np.float64)
    n = len(xs)
    step_x = xs[1] - xs[0]
    step_z = zs[1] - zs[0]
    texture = np.asarray(dome.texture, dtype=np.float64)

    def grid_coords(px, pz):
        return (px - xs[0]) / step_x, (pz - zs[0]) / step_z

    def interpolate(values, gi, gj):
        i0 = np.clip(np.floor(gi).astype(np.int64), 0, n - 2)
        j0 = np.clip(np.floor(gj).astype(np.int64), 0, n - 2)
        ti = gi - i0
        tj = gj - j0
        if values.ndim == 3:
            ti, tj = ti[..., None], tj[..., None]
        return (
            values[i0, j0] * (1 - ti) * (1 - tj)
            + values[i0 + 1, j0] * ti * (1 - tj)
            + values[i0, j0 + 1] * (1 - ti) * tj
            + values[i0 + 1, j0 + 1] * ti * tj
        )

    if heights[n // 2, n // 2] <= 0:
        # the dome does not arch over the eye: not modelled
        return
    steps = 160
    for row in range(len(elevations)):
        if elevations[row] < -0.5:
            continue
        d = _directions(headings, elevations[row : row + 1])[0]
        # ray length until it leaves the grid square
        with np.errstate(divide='ignore', invalid='ignore'):
            limits = np.stack(
                [
                    np.where(d[:, 0] > 0, xs[-1] / d[:, 0], np.where(d[:, 0] < 0, xs[0] / d[:, 0], np.inf)),
                    np.where(d[:, 2] > 0, zs[-1] / d[:, 2], np.where(d[:, 2] < 0, zs[0] / d[:, 2], np.inf)),
                ]
            ).min(axis=0)
        t = np.linspace(0, 1, steps + 1)[None, 1:] * limits[:, None]
        px, py, pz = t * d[:, 0:1], t * d[:, 1:2], t * d[:, 2:3]
        gi, gj = grid_coords(px, pz)
        above = py - interpolate(heights, gi, gj) >= 0
        hit = above.any(axis=1)
        if not hit.any():
            continue
        first = np.argmax(above, axis=1)
        columns = np.nonzero(hit)[0]
        t_hi = t[columns, first[columns]]
        t_lo = np.where(first[columns] > 0, t[columns, np.maximum(first[columns] - 1, 0)], 0.0)
        dc = d[columns]
        for _ in range(16):
            t_mid = (t_lo + t_hi) / 2
            gi, gj = grid_coords(t_mid * dc[:, 0], t_mid * dc[:, 2])
            is_above = t_mid * dc[:, 1] - interpolate(heights, gi, gj) >= 0
            t_hi = np.where(is_above, t_mid, t_hi)
            t_lo = np.where(is_above, t_lo, t_mid)
        gi, gj = grid_coords(t_hi * dc[:, 0], t_hi * dc[:, 2])
        u = interpolate(np.asarray(dome.us, dtype=np.float64), gi, gj)
        v = interpolate(np.asarray(dome.vs, dtype=np.float64), gi, gj)
        color = interpolate(np.asarray(dome.colors, dtype=np.float64), gi, gj)
        texel = _sample(texture, u, v, wrap=True)[:, :3]
        source = texel * color[:, :3]
        if dome.mode == 'add':
            out[row, columns] = np.minimum(out[row, columns] + source * color[:, 3:4], 255)
        else:
            alpha = color[:, 3:4]
            out[row, columns] = out[row, columns] * (1 - alpha) + source * alpha


def _draw_sun(out, sun: SunSprite, headings, elevations):
    """Draws the sun sprite: a square of half size `half_size / sqrt(2)` (the game puts its corners `half_size`
    from the centre, turned by 45 degrees) facing the eye, upright, at `SUN_DISTANCE * direction`"""
    import numpy as np

    center = np.asarray(sun.direction, dtype=np.float64) * SUN_DISTANCE
    distance = np.linalg.norm(center)
    if distance == 0:
        return
    forward = center / distance
    up = np.array([0.0, 1.0, 0.0]) - forward[1] * forward
    if np.linalg.norm(up) < 1e-6:
        up = np.array([0.0, 0.0, 1.0])
    up /= np.linalg.norm(up)
    right = np.cross(up, forward)
    half_side = sun.half_size / math.sqrt(2)
    reach = math.atan2(half_side * math.sqrt(2), distance) * 1.2
    texture = np.asarray(sun.texture, dtype=np.float64)
    d = _directions(headings, elevations)
    cosine = d @ forward
    mask = cosine > math.cos(reach)
    if not mask.any():
        return
    rays = d[mask]
    points = rays * (distance / cosine[mask])[:, None]
    x = points @ right / half_side
    y = points @ up / half_side
    inside = (np.abs(x) <= 1) & (np.abs(y) <= 1)
    texel = _sample(texture, (x + 1) / 2, (1 - y) / 2, wrap=False)
    alpha = np.where(inside, texel[:, 3] / 255, 0)[:, None]
    target = out[mask]
    if sun.additive:
        target = np.minimum(target + texel[:, :3] * alpha, 255)
    else:
        target = target * (1 - alpha) + texel[:, :3] * alpha
    out[mask] = target


def render_horizon_sky(sky: HorizonSky, width: int = OUT_WIDTH, height: int = OUT_HEIGHT):
    """The sky sphere texture (height x width x 4 uint8 array) of the horizon settings"""
    import numpy as np

    headings = output_headings(width)
    elevations = output_elevations(height)
    out = np.empty((height, width, 3))
    out[:] = _rgb(sky.clear_color)
    if sky.draw_band:
        # world height at the projection distance of every row, sector coordinate of every column
        h = sky.distance * np.tan(elevations)
        sector = np.mod(sky.sector_at(headings), SECTORS)
        k = np.floor(sector).astype(int) % SECTORS
        f = sector - np.floor(sector)
        ring = np.asarray(sky.ring, dtype=np.float64)
        bottom_color = ring[k] * (1 - f[:, None]) + ring[k + 1] * f[:, None]

        rows = (h >= sky.middle_y) & (h <= sky.top_y)
        if rows.any() and sky.top_y > sky.middle_y:
            t = ((h[rows] - sky.middle_y) / (sky.top_y - sky.middle_y))[:, None, None]
            out[rows] = bottom_color[None] * (1 - t) + _rgb(sky.sky_top_color)[None, None] * t

        if sky.sun is not None and not sky.sun.in_front:
            _draw_sun(out, sky.sun, headings, elevations)
        if sky.clouds is not None:
            _draw_clouds(out, sky.clouds, headings, elevations)
        if sky.sun is not None and sky.sun.in_front:
            _draw_sun(out, sky.sun, headings, elevations)

        rows = (h >= sky.base_y) & (h < sky.middle_y)
        if rows.any():
            t = ((h[rows] - sky.base_y) / (sky.middle_y - sky.base_y))[:, None]
            out[rows] = (_rgb(sky.earth_bottom_color) * (1 - t) + _rgb(sky.earth_top_color) * t)[:, None, :]

        if sky.strips:
            mirrored = sky.mirror & (k >= STRIPS)
            strip = np.where(mirrored, STRIPS - 1 - k % STRIPS, k % STRIPS)
            u = np.where(mirrored, 1 - f, f)
            for index, source in enumerate(sky.strips):
                columns = np.nonzero(strip == index)[0]
                top = sky.pixmap_top_y[index]
                rows = np.nonzero((h >= sky.pixmap_bottom_y) & (h <= top))[0]
                if not len(columns) or not len(rows) or top <= sky.pixmap_bottom_y:
                    continue
                v = (top - h[rows]) / (top - sky.pixmap_bottom_y)
                texel = _sample(
                    np.asarray(source, dtype=np.float64),
                    u[columns][None, :],
                    v[:, None] + 0 * u[columns][None, :],
                    False,
                )
                alpha = texel[..., 3:4] / 255
                block = out[np.ix_(rows, columns)]
                out[np.ix_(rows, columns)] = block * (1 - alpha) + texel[..., :3] * alpha
    image = np.empty((height, width, 4), dtype=np.uint8)
    image[..., :3] = np.round(np.clip(out, 0, 255))
    image[..., 3] = 255
    return image


def _cloud_brightness(bright: int, variance: int, rng):
    """NFS3 0x47ae10 / NFS4 0x4c95a0: brightness 0..bright of the 13 x 13 cloud grid points"""
    import numpy as np

    n = 13
    b = np.zeros((n, n))
    for j in range(n):
        for i in range(n):
            b[i, j] = bright - (rng.getrandbits(32) % variance) if variance else bright
    for j in range(n):
        for i in range(n):
            x = (b[i, j] - 128) * (1 / 128)
            sign = 1.0 if x >= 0 else -1.0
            b[i, j] = (math.sqrt(x * sign) * sign + 1) * 0.5 * 255
    for _ in range(20):
        for j in range(n):
            for i in range(n):
                total = 0.0
                count = 0.0
                for dj in range(-2, 3):
                    for di in range(-2, 3):
                        if (di or dj) and 0 <= i + di < n and 0 <= j + dj < n:
                            neighbour = b[i + di, j + dj]
                            weight = (abs(neighbour - 128) * (1 / 128)) ** 2
                            total += (neighbour - b[i, j]) * weight
                            count += 1
                delta = total / count
                if delta != 0:
                    value = delta * 0.5 + b[i, j]
                    b[i, j] = min(max(value, 0.0), float(bright))
    return b


def nfs34_cloud_dome(
    texture,
    cloud_type: int,
    offset: float,
    dome_height: float,
    bright: int,
    variance: int,
    nimbus: float,
    u_scale=1.0,
    v_scale=1.0,
) -> Optional[CloudDome]:
    """The NFS3 / NFS4 cloud dome (`dome_height`: NFS3's file value * 3, NFS4's `cloudHeight`), None for cloud type 0"""
    import numpy as np
    import random

    if cloud_type == 0 or texture is None:
        return None
    n = 13
    coords = np.array([(i * 0x1C20000 - 0xBB80000) / 65536 for i in range(n)])
    b = _cloud_brightness(bright, variance, random.Random(CLOUD_SEED))
    x, z = np.meshgrid(coords, coords, indexing='ij')
    heights = np.cos(np.hypot(x, z) * 0.25 / 3000 * 2 * math.pi) * dome_height + offset
    heights = heights - dome_height * 0.5 * nimbus * b * (1 / 255)
    level = np.floor(b) / 255
    colors = np.stack([level, level, level, level], axis=-1)
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
    return CloudDome(
        coords, coords, heights, i * u_scale, j * v_scale, colors, texture, 'add' if cloud_type == 1 else 'blend'
    )


def _strip_tops(strips, bottom, top):
    tallest = max(1, max(s.shape[0] for s in strips))
    return [bottom + (top - bottom) * s.shape[0] / tallest for s in strips]


def nfs2se_sky(settings, strips, cloud_texture, track: int) -> HorizonSky:
    """NFS2 SE sky of a `3TR<nn>.HRZ` (`Nfs2SeHorizonSettings`), the strips (first 8 images of `TR<nn>0.QFS`) and `CLD<track>` of
    `SKY.FSH` (RGBA arrays)"""
    import numpy as np

    s = settings
    height = s.gouraud_height if s.gouraud_height else 1
    unit = _c_div(0x10000, height)
    middle16 = s.gouraud_middle * unit
    top16 = s.pixmap_top * unit
    bottom16 = s.pixmap_bottom * unit
    tallest = max([1] + [x.shape[0] for x in strips])
    tops16 = [x.shape[0] * _c_div(top16 - bottom16, tallest) + bottom16 for x in strips]

    def y(fraction16):
        return s.base_y + height * fraction16 / 65536

    rotation = _c_div(s.angle_degrees << 16, 360) / 65536

    clouds = None
    # clouds on tracks 2..7 (nfs2sea 0x42da20), CLD<track>, added (poly type 0xb, handler 0x42bba0), alpha blended
    # at half alpha on track 7 (type 0xa, 0x42b970)
    if 2 <= track <= 7 and cloud_texture is not None:
        coords = np.array([-1000.0 + 150 * i for i in range(13)])
        x, z = np.meshgrid(coords, coords, indexing='ij')
        heights = np.cos(np.hypot(x, z) * 0.25 * 0.001 * 2 * math.pi) * s.cloud_dome_height + s.cloud_dome_offset
        colors = np.ones((13, 13, 4))
        colors[..., 3] = 0x7F / 255 if track == 7 else 1.0
        i, j = np.meshgrid(np.arange(13), np.arange(13), indexing='ij')
        clouds = CloudDome(coords, coords, heights, j, i, colors, cloud_texture, 'blend' if track == 7 else 'add')

    black = bool(s.black_horizon)
    return HorizonSky(
        sector_at=lambda psi: (psi - rotation) * SECTORS,
        distance=s.flat_projection_distance or 1,
        clear_color=(0, 0, 0) if black else s.sky_top_color,
        sky_top_color=s.sky_top_color,
        ring=ring_colors(s.sun_color, s.opposite_sun_color),
        earth_top_color=s.earth_top_color,
        earth_bottom_color=s.earth_bottom_color,
        base_y=s.base_y,
        middle_y=y(middle16),
        top_y=s.base_y + height,
        strips=strips if len(strips) == STRIPS else None,
        mirror=bool(s.mirror),
        pixmap_bottom_y=y(bottom16),
        pixmap_top_y=[y(t) for t in tops16],
        draw_band=not black,
        clouds=clouds,
    )


def _turns_in_0_1(value: float) -> float:
    # NFS3 0x478340, NFS4 0x4c9c30: while < 0 add 1, while > 1.0 subtract 1
    while value < 0:
        value += 1.0
    while value > 1.0:
        value -= 1.0
    return value


def parse_sun_text(text: str):
    """(azimuth degrees, B degrees, R, rotate, additive, in front) of the text of an NFS3 `SUN*` image
    (`A200 B45 R25 ROTATE`; nfs3.exe 0x47a970 reads the numbers after `A`, `B`, `R` and looks for the words
    `ROTATE`, `NOADD`, `INFRONT`), None without the three numbers"""
    numbers = {}
    for letter in 'ABR':
        match = re.search(letter + r'\s*(-?\d+)', text)
        if not match:
            return None
        numbers[letter] = int(match.group(1))
    return numbers['A'], numbers['B'], numbers['R'], 'ROTATE' in text, 'NOADD' not in text, 'INFRONT' in text


def _sun_direction(azimuth_turns: float, b_turns: float):
    return (
        math.cos(azimuth_turns * 2 * math.pi),
        math.cos(b_turns * 2 * math.pi),
        math.sin(azimuth_turns * 2 * math.pi),
    )


def nfs3_sky(settings, strips, cloud_texture, sun_texture, sun_text: Optional[str]) -> HorizonSky:
    """NFS3 sky of a `3TR<nn>.HRZ` (`Nfs3HorizonSettings`), the strips (first 8 images of `TR<nn>0.QFS`), `CLDD` and
    `SUND` (with its text) of `SKY.FSH`"""
    s = settings
    rotation = _turns_in_0_1(_c_div(s.angle_degrees << 16, 360) * (1 / 65536))
    bottom = s.base_y + s.pixmap_bottom
    sun = None
    parsed = parse_sun_text(sun_text) if sun_text and sun_texture is not None else None
    if parsed:
        a, b, r, _rotate, additive, in_front = parsed
        sun = SunSprite(_sun_direction(a / 360, b / 360), r * 10.0, sun_texture, additive, in_front)
    return HorizonSky(
        sector_at=lambda psi: SECTORS * (psi + 0.5312700271606445 + rotation) + 3.5,
        distance=s.radius or 1,
        clear_color=(0, 0, 0) if s.black_horizon else s.sky_top_color,
        sky_top_color=s.sky_top_color,
        ring=ring_colors(s.sun_color, s.opposite_sun_color),
        earth_top_color=s.earth_top_color,
        earth_bottom_color=s.earth_bottom_color,
        base_y=s.base_y,
        middle_y=s.base_y + s.gouraud_middle,
        top_y=s.base_y + s.gouraud_height,
        strips=strips if s.has_pixmap and len(strips) == STRIPS else None,
        mirror=bool(s.mirror),
        pixmap_bottom_y=bottom,
        pixmap_top_y=_strip_tops(strips, bottom, s.base_y + s.pixmap_top) if strips else (),
        clouds=nfs34_cloud_dome(
            cloud_texture,
            s.cloud_type,
            s.cloud_dome_offset,
            s.cloud_dome_height * 3,
            min(max(s.cloud_bright, 0), 255),
            max(s.cloud_variance, 0),
            math.trunc(s.cloud_nimbus_percent * 0.01),
        ),
        sun=sun,
    )


def nfs4_sky(settings, strips, cloud_texture, sun_texture, sun_text: Optional[str] = None) -> HorizonSky:
    """NFS4 sky of a `Tr.ini` (`Nfs4SkySettings`), the strips `HDC0`..`HDC7`, `CLDD` and `SUND` (with its text) of
    `sky.qfs`. The sun (0x4c9050): none without a `SUND` image, the `[sun]` keys with `hasSun=1`, else the text of
    the image as NFS3 reads it (degrees / 360, size 10 * R)"""
    s = settings
    rotation = _turns_in_0_1(s.hrzAngle)
    bottom = s.hrzBottomYOff + s.hrzPmxBottom
    sun = None
    if sun_texture is not None:
        parsed = parse_sun_text(sun_text) if sun_text else None
        if s.hasSun:
            sun = SunSprite(
                _sun_direction(s.angleTheta, s.angleRho), s.radius, sun_texture, bool(s.additive), bool(s.inFront)
            )
        elif parsed:
            a, b, r, _rotate, additive, in_front = parsed
            sun = SunSprite(_sun_direction(a / 360, b / 360), r * 10.0, sun_texture, additive, in_front)
    return HorizonSky(
        sector_at=lambda psi: SECTORS * (psi + 0.5 + rotation) + 8,
        distance=s.hrzfRadius or 1,
        clear_color=(0, 0, 0) if s.hrzShouldDrawBlack else s.hrzSkyTopColor,
        sky_top_color=s.hrzSkyTopColor,
        ring=ring_colors(s.hrzSunColor, s.hrzOppositeSunColor),
        earth_top_color=s.hrzEarthTopColor,
        earth_bottom_color=s.hrzEarthBotColor,
        base_y=s.hrzBottomYOff,
        middle_y=s.hrzBottomYOff + s.hrzGouraudMiddle,
        top_y=s.hrzBottomYOff + s.hrzGouraudHeight,
        strips=strips if s.hrzHasPMX and len(strips) == STRIPS else None,
        mirror=bool(s.hrzMirror),
        pixmap_bottom_y=bottom,
        pixmap_top_y=_strip_tops(strips, bottom, s.hrzBottomYOff + s.hrzPmxTop) if strips else (),
        clouds=nfs34_cloud_dome(
            cloud_texture,
            s.cloudType,
            s.cloudYOffset,
            s.cloudHeight,
            s.cloudBright,
            s.cloudVariance,
            s.cloudNimbus,
            s.cloudUscale or 1.0,
            s.cloudVscale or 1.0,
        ),
        sun=sun,
    )


def save_spherical(image, out_file_name: str):
    from PIL import Image

    Image.fromarray(image, 'RGBA').save(out_file_name)


# Archives with a horizon, by path (upper case, '/' separators)
NFS2SE_TEXTURES = re.compile(r'/TRACKS/SE/TR(\d\d)0M?\.QFS$')
NFS3_TEXTURES = re.compile(r'/TRK\d{3}/TR(\d\d)0\.QFS$')
NFS4_SKY = re.compile(r'/SKY\.QFS$')


def _sibling(path: str, name: str) -> Optional[str]:
    """`name` next to `path`, ignoring letter case, None when there is none"""
    directory = os.path.dirname(path)
    try:
        names = {x.lower(): x for x in os.listdir(directory or '.')}
    except OSError:
        return None
    found = names.get(name.lower())
    return os.path.join(directory, found) if found else None


def horizon_archive_kind(id: str) -> Optional[str]:
    """'nfs2se', 'nfs3' or 'nfs4' for the texture archive of a track whose sky this module draws (by the archive's
    path in `id`), None otherwise. NFS2 SE: the `GAMEDATA/TRACKS/SE/TR<nn>0.QFS` / `TR<nn>0M.QFS` with a
    `3TR<nn>.HRZ` next to it; NFS3: `TRK<nnn>/TR<nn>0.QFS` with `3TR<nn>.HRZ`; NFS4: `sky.qfs` with `Tr.ini`"""
    if not id:
        return None
    from library.loader import id_to_path

    path = id_to_path(id)
    upper = path.replace('\\', '/').upper()
    match = NFS2SE_TEXTURES.search(upper)
    if match and _sibling(path, f'3TR{match.group(1)}.HRZ'):
        return 'nfs2se'
    match = NFS3_TEXTURES.search(upper)
    if match and _sibling(path, f'3TR{match.group(1)}.HRZ'):
        return 'nfs3'
    if NFS4_SKY.search(upper) and _sibling(path, 'Tr.ini'):
        return 'nfs4'
    return None


def _image_entries(items, id: str, keep_repeated: bool = False):
    """{alias: (RGBA float array, text or None)} of the images among archive `items` (alias, data, block) of the SHPI
    loaded under `id` (the first of repeated aliases; with `keep_repeated` keyed by item index instead, every image)"""
    import numpy as np

    from library.utils.id import join_id
    from serializers.bitmaps import ImageSerializer

    entries = {}
    for i, (alias, item, item_block) in enumerate(items):
        key = i if keep_repeated else alias
        if not isinstance(item, dict) or 'bitmap' not in item or key in entries:
            continue
        try:
            image = ImageSerializer().to_image(item, item_block, join_id(id, 'children', str(i), 'item', 'data'))
        except Exception:
            continue
        text = item.get('text') or None
        entries[key] = (np.asarray(image.convert('RGBA'), dtype=np.float64), text['text'] if text else None)
    return entries


def _shpi_entries(path: Optional[str]):
    """`_image_entries` of an SHPI file (`SKY.FSH`), {} when there is none or it can't be read"""
    if not path:
        return {}
    from library import require_file

    try:
        file_id, block, data = require_file(path, lazy=False)
        items = [
            (x['alias'], x['item']['data'], block.item_block.possible_blocks[x['item']['choice_index']])
            for x in data['children']
        ]
    except Exception:
        return {}
    return _image_entries(items, file_id)


def serialize_horizon_sky(items, path: str, id: str) -> List[str]:
    """Writes `spherical.png` of an archive `horizon_archive_kind` accepts into `path` (where its images were just
    exported), returns the written files"""

    from library.loader import id_to_path
    from library.utils import path_join
    from resources.eac import horizons

    kind = horizon_archive_kind(id)
    if kind is None:
        return []
    archive_path = id_to_path(id)
    upper = archive_path.replace('\\', '/').upper()
    if kind == 'nfs4':
        # nfs4.exe picks the strips by name
        entries = _image_entries(items, id)
        names = [f'HDC{i}' for i in range(STRIPS)]
        strips = [entries[name][0] for name in names] if all(name in entries for name in names) else []
    else:
        # nfs2sea.exe 0x42e8f0, nfs3.exe 0x478b70: the first 8 textures of the track's texture archive, whatever
        # their names (`0000`..`0007`, NFS3 TRK004 / TRK006 `HOR1`..`HOR8`, NFS2 SE TR08 `MONO`)
        strips = list(entry[0] for entry in _image_entries(items[:STRIPS], id, keep_repeated=True).values())
        if len(strips) < STRIPS:
            strips = []

    def read_text(file_path):
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')

    if kind == 'nfs2se':
        track = int(NFS2SE_TEXTURES.search(upper).group(1))
        settings = horizons.parse_nfs2se_horizon_settings(read_text(_sibling(archive_path, f'3TR{track:02}.HRZ')))
        if settings is None:
            return []
        sky_fsh = _shpi_entries(_sibling(archive_path, 'SKY.FSH'))
        cloud = sky_fsh.get(f'CLD{track}', (None, None))[0]
        sky = nfs2se_sky(settings, strips, cloud, track)
    elif kind == 'nfs3':
        track = NFS3_TEXTURES.search(upper).group(1)
        settings = horizons.parse_nfs3_horizon_settings(read_text(_sibling(archive_path, f'3TR{track}.HRZ')))
        if settings is None:
            return []
        sky_fsh = _shpi_entries(_sibling(archive_path, 'SKY.FSH'))
        cloud = sky_fsh.get('CLDD', (None, None))[0]
        sun, sun_text = sky_fsh.get('SUND', (None, None))
        sky = nfs3_sky(settings, strips, cloud, sun, sun_text)
    else:
        settings = horizons.parse_nfs4_sky_settings(read_text(_sibling(archive_path, 'Tr.ini')))
        textures = _image_entries(items, id)
        sun, sun_text = textures.get('SUND', (None, None))
        sky = nfs4_sky(settings, strips, textures.get('CLDD', (None,))[0], sun, sun_text)
    out_path = path_join(path, 'spherical.png')
    save_spherical(render_horizon_sky(sky), out_path)
    return [out_path]

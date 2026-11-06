"""`car_colors.json` of a PSX TNFS car model (the PSH of a `.VSM` / `.WSM` car archive), with the keys of the PC one
(`tnfs_car_colors.py`): the colors the game writes over CLUT entries of the car textures, as replacements of colors
of the exported PNGs. From the PSX executable (SLUS-00204): the car texture upload 0x8004e72c looks at the first 16
CLUT entries of every image and `gfx_draw_car_model` 0x80050024 writes the colors"""

from typing import Dict, List, Tuple

from resources.eac.psx_bitmaps import psx_color_to_rgba
from serializers.misc.tnfs_car_colors import SIREN_SWAP_INTERVAL_MS

# brake lights (colors at 0x800c1744 / 0x800c1714, the same for every car slot): written while `brake` < 0xb / >= 0xb
TAIL_LIGHTS_OFF = 0x0008
TAIL_LIGHTS_ON = 0x001F
# the cop's light bar: its red and its blue entries get 0x800db680 / 0x800db684, exchanged every 16 clock units
SIREN_RED = 0x001F
SIREN_BLUE = 0x7C00
CLUT_ENTRIES_CHECKED = 16


def _components(color: int) -> Tuple[int, int, int]:
    return color & 0x1F, (color >> 5) & 0x1F, (color >> 10) & 0x1F


def is_tail_light_color(color: int) -> bool:
    """A brake light CLUT entry: pure green"""
    red, green, blue = _components(color)
    return red < 2 and green > 29 and blue < 2


def is_siren_red_color(color: int) -> bool:
    red, green, blue = _components(color)
    return red > 29 and green == 0 and blue == 0


def is_siren_blue_color(color: int) -> bool:
    red, green, blue = _components(color)
    return red == 0 and green == 0 and blue > 29


def _png_hex(color: int) -> str:
    return f'#{psx_color_to_rgba(color) >> 8:06x}'


def tnfs_psx_car_colors(items: List[Tuple[str, dict, object]]) -> Dict:
    """car_colors.json of the textures of a PSX car model, the same for every car (which role a car has is up to the
    game). `items` are (alias, data, block) of the PSH children.
    - `tail_lights`: PNG color of the pure green CLUT entries, the textures having them and the unlit / lit colors.
      The game does it for the high-poly textures of the racers, 5 entries at most
    - `light_bar`: PNG colors of the pure red and pure blue CLUT entries, the textures having them, the colors the
      cop's light bar gets during a chase (its own) and the exchanged ones with the swap interval. Other cars and a
      cop out of a chase keep the texture colors"""
    found = {}
    for kind, check in (
        ('tail_light', is_tail_light_color),
        ('red', is_siren_red_color),
        ('blue', is_siren_blue_color),
    ):
        colors, textures = [], []
        for name, data, _ in items:
            clut = data.get('clut') if isinstance(data, dict) else None
            if not clut:
                continue
            matched = [c for c in clut['colors'][:CLUT_ENTRIES_CHECKED] if check(c)]
            if matched:
                textures.append(name)
                colors.extend(c for c in matched if c not in colors)
        found[kind] = (colors, textures)
    result = {}
    colors, textures = found['tail_light']
    # one green in every model of the game: a model with several would need a PNG color each
    if len(colors) == 1:
        result['tail_lights'] = {
            'texture_color': _png_hex(colors[0]),
            'textures': textures,
            'off': _png_hex(TAIL_LIGHTS_OFF),
            'on': _png_hex(TAIL_LIGHTS_ON),
        }
    (reds, red_textures), (blues, blue_textures) = found['red'], found['blue']
    if len(reds) == 1 and len(blues) == 1:
        result['light_bar'] = {
            'texture_colors': [_png_hex(reds[0]), _png_hex(blues[0])],
            'textures': red_textures + [x for x in blue_textures if x not in red_textures],
            'siren_colors': [_png_hex(SIREN_RED), _png_hex(SIREN_BLUE)],
            'siren_colors_swapped': [_png_hex(SIREN_BLUE), _png_hex(SIREN_RED)],
            'swap_interval_ms': SIREN_SWAP_INTERVAL_MS,
        }
    return result

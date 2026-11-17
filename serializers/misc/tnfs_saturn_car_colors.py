"""`car_colors.json` of a Sega Saturn TNFS car texture bank (Over Drivin' GT-R `CARS/<car>.ALL`, `CAR2/<car>.ALL`), with
the keys of the PC and PSX ones (`tnfs_car_colors.py`, `tnfs_psx_car_colors.py`). Not from the Saturn executable (not
disassembled): the brake light marker is the PSX one (pure green CLUT entries, which the PSX game overwrites with the
brake light colours, `tnfs_psx_car_colors.py`), found in the rear light texture of five cars, always at colour 0; the
off / on colours are the PSX game's"""

from typing import Dict, List

from resources.eac.tnfs_saturn import saturn_color_to_rgba
from serializers.misc.tnfs_psx_car_colors import TAIL_LIGHTS_OFF, TAIL_LIGHTS_ON, _png_hex


def is_saturn_tail_light_color(color: int) -> bool:
    """A brake light marker colour: pure green. Green from 29 up: the BCNR33's marker is 29 (the PSX game wants more
    than 29)"""
    red, green, blue = color & 0x1F, (color >> 5) & 0x1F, (color >> 10) & 0x1F
    return red < 2 and green >= 29 and blue < 2


def tnfs_saturn_car_colors(textures: List[tuple]) -> Dict:
    """car_colors.json of the textures of a bank: (exported name, the 16 colours, colour indices used) of each.
    `tail_lights`: the PNG colour of the pure green colours used by a texture, the textures having it and the PSX
    game's unlit / lit colours; only when one green is found (as in every file)"""
    colors, names = [], []
    for name, clut, used in textures:
        matched = [c for i, c in enumerate(clut) if i in used and is_saturn_tail_light_color(c)]
        if matched:
            names.append(name)
            colors.extend(c for c in matched if c not in colors)
    if len(colors) != 1:
        return {}
    return {
        'tail_lights': {
            'texture_color': f'#{saturn_color_to_rgba(colors[0]) >> 8:06x}',
            'textures': names,
            'off': _png_hex(TAIL_LIGHTS_OFF),
            'on': _png_hex(TAIL_LIGHTS_ON),
        }
    }

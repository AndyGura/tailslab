"""`car_colors.json` of a Sega Saturn TNFS car texture bank (Over Drivin' GT-R `CARS/<car>.ALL`, `CAR2/<car>.ALL`), with
the keys of the PC and PSX ones (`tnfs_car_colors.py`, `tnfs_psx_car_colors.py`). From the Saturn executable `0`
(loaded at 0x06010000): the high-poly bank's colour tables are loaded into VDP1 VRAM by 0x06041720, which sets colour 0
of textures 0 and 1 to the unlit brake light colour; the car draw 0x060333bc writes colour 0 of both textures (the
car's high-poly texture list at car + 0x530, its colour table address at list + 0xc) with the unlit colour while
`brake` (car + 0x3bc) < 0xb, the lit one from 0xb, as the PSX game. Texture 0 is the rear light texture (the
`bkll` / `bklr` polygons' in seven cars, the 300ZX's `Side` J015); texture 1 (`null`) is drawn by no polygon. Five
cars have pure green there (the PSX convention for the brake light CLUT entry), the 300ZX, the Silvia and the 240ZG
red: the game overwrites it whatever it is"""

from typing import Dict, List

from resources.eac.tnfs_saturn import saturn_color_to_rgba

# brake light colours, 0x060335c4 / 0x06033464 (16-bit RGB, bit 15 set): red 6, red 31 green 1
TAIL_LIGHTS_OFF = 0x8006
TAIL_LIGHTS_ON = 0x803F


def _png_hex(color: int) -> str:
    return f'#{saturn_color_to_rgba(color) >> 8:06x}'


def tnfs_saturn_car_colors(textures: List[tuple], high_poly: bool) -> Dict:
    """car_colors.json of the textures of a bank: (exported name, the 16 colours, colour indices used) of each, in bank
    order. `tail_lights`: colour 0 of texture 0 of the high-poly bank (the low-poly one keeps its colours), the texture
    and the game's unlit / lit colours; only when the PNG colour is drawn by no other colour of the bank's textures
    (as in every file), so that nfs-web can replace it by colour"""
    if not high_poly or not textures:
        return {}
    name, clut, used = textures[0]
    if 0 not in used:
        return {}
    color = _png_hex(clut[0])
    for other_name, other_clut, other_used in textures:
        if any(_png_hex(other_clut[i]) == color for i in other_used if other_name != name or i != 0):
            return {}
    return {
        'tail_lights': {
            'texture_color': color,
            'textures': [name],
            'off': _png_hex(TAIL_LIGHTS_OFF),
            'on': _png_hex(TAIL_LIGHTS_ON),
        }
    }

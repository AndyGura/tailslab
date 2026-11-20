"""Serializers of the Sega Saturn TNFS port Over Drivin' GT-R (`resources/eac/tnfs_saturn.py`)"""

import json
import os
from io import BytesIO
from typing import Dict, List, Optional

from library.utils import path_join
from library.utils.file_utils import find_file_case_insensitive
from serializers import BaseFileSerializer
from serializers.base import DIRECTORY_UI, PNG_UI


def tnfs_saturn_texture_file_name(name: str) -> str:
    """Exported (PNG, GLB image) name of a texture of a Saturn texture bank: the tyre textures `Tir1`..`Tir4`
    (`Tyr1`..`Tyr4` in the PGC10) as `tyr1`..`tyr4` (`tnfs_tyre_texture_file_name`)"""
    from serializers.geometries import tnfs_tyre_texture_file_name

    return tnfs_tyre_texture_file_name(name)


def tnfs_saturn_bank_textures(bank: dict) -> Dict[str, tuple]:
    """Exported name -> (PIL image, the 16 colours, set of colour indices drawn) of every texture of a bank"""
    from resources.eac.tnfs_saturn import (
        SATURN_DRAW_MODE_INDEX_0_DRAWN,
        tnfs_saturn_texture_image,
        tnfs_saturn_texture_name,
        tnfs_saturn_texture_pixels,
    )

    result = {}
    for i, entry in enumerate(bank['textures']):
        name = tnfs_saturn_texture_file_name(tnfs_saturn_texture_name(entry))
        _, _, indices, colors = tnfs_saturn_texture_pixels(bank, i)
        used = set(indices)
        if not entry['draw_mode'] & SATURN_DRAW_MODE_INDEX_0_DRAWN:
            # colour 0 of a cut-out texture is not drawn (a key colour, green in the Warrior's tyres)
            used.discard(0)
        result[name] = (tnfs_saturn_texture_image(bank, i), colors, used)
    return result


def export_tnfs_saturn_texture_bank(bank: dict, path: str) -> List[str]:
    """PNGs of every texture of a bank (indexed, colour 0 transparent where the draw mode says so) and
    `car_colors.json` (`tnfs_saturn_car_colors`) when it finds colours, in folder `path`"""
    from serializers.misc.tnfs_saturn_car_colors import tnfs_saturn_car_colors

    os.makedirs(path, exist_ok=True)
    output = []
    textures = tnfs_saturn_bank_textures(bank)
    for name, (image, _, _) in textures.items():
        file_path = path_join(path, f'{name}.png')
        image.save(file_path, 'PNG')
        output.append(file_path)
    car_colors = tnfs_saturn_car_colors([(name, colors, used) for name, (_, colors, used) in textures.items()])
    if car_colors:
        file_path = path_join(path, 'car_colors.json')
        with open(file_path, 'w') as file:
            json.dump(car_colors, file, indent=2)
        output.append(file_path)
    return output


def _write_json(path: str, block, data) -> str:
    from serializers import JsonSerializer

    return JsonSerializer().serialize(data, path, block=block)[0]


class TnfsSaturnCarBundleSerializer(BaseFileSerializer):
    """`CARS/<car>.ALL` / `CAR2/<car>.ALL` to a folder: `physics.PBS.json` (the PC PBS JSON keys and values),
    `textures/` and `low_poly_textures/` (the PNGs of the two texture banks, named as the images of the models'
    gg-web-engine export, with `car_colors.json`), and from `CARS` `dashboard.png` and `steering_wheel.png` (colour 0
    transparent)"""

    ui = DIRECTORY_UI

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.tnfs_saturn import tnfs_saturn_rle_image

        super().serialize(data, path)
        output = [_write_json(path_join(path, 'physics.PBS'), block.field_blocks_map['physics'], data['physics'])]
        output += export_tnfs_saturn_texture_bank(data['textures'], path_join(path, 'textures'))
        output += export_tnfs_saturn_texture_bank(data['low_poly_textures'], path_join(path, 'low_poly_textures'))
        if data.get('cockpit'):
            for name in ('dashboard', 'steering_wheel'):
                file_path = path_join(path, f'{name}.png')
                tnfs_saturn_rle_image(data['cockpit'][name]).save(file_path, 'PNG')
                output.append(file_path)
        return output


class TnfsSaturnGtrExecutableSerializer(BaseFileSerializer):
    """The car AI records of the executable `0` to `<slot>.PDN.json` (`SUPRA`.. `RX7`, `WARRIOR`): the keys of the PC
    PDN JSON, top speeds in the PC's m/s (`TnfsSaturnCarAiAndCrashBody.pc_data`)"""

    ui = DIRECTORY_UI

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.car_specs import CarAiAndCrashBody
        from resources.eac.tnfs_saturn import TnfsSaturnCarAiAndCrashBody, tnfs_saturn_gtr_car_ai_records

        super().serialize(data, path)
        pc_block = CarAiAndCrashBody()
        output = []
        for slot, index in tnfs_saturn_gtr_car_ai_records(data).items():
            pc_data = TnfsSaturnCarAiAndCrashBody.pc_data(data['car_ai_records'][index])
            output.append(_write_json(path_join(path, f'{slot}.PDN'), pc_block, pc_data))
        return output


class TnfsSaturnPcxListSerializer(BaseFileSerializer):
    """`UIDATA/*.DAT` picture lists to a folder of `<index>.png`"""

    ui = DIRECTORY_UI

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from PIL import Image

        super().serialize(data, path)
        output = []
        for i, picture in enumerate(data['pictures']):
            file_path = path_join(path, f'{i}.png')
            Image.open(BytesIO(picture['pcx'])).convert('RGBA').save(file_path, 'PNG')
            output.append(file_path)
        return output


def tnfs_saturn_car_bundle_path(orix_path: str) -> Optional[str]:
    """`CARS/<car>.ALL` of a model `MODELS/<car>/high.orix` / `low.orix` (letter case of the folder as found)"""
    car_dir = os.path.dirname(orix_path)
    game_dir = os.path.dirname(os.path.dirname(car_dir))
    return find_file_case_insensitive(path_join(game_dir, 'CARS', f'{os.path.basename(car_dir)}.ALL'))


def tnfs_saturn_sprite_bank_files(bank: dict, bank_index: int, path: str, palettes: dict) -> List[str]:
    """`<bank index>_<sprite index>.png` of every sprite of a sprite bank, with its palette of the palette table
    (`tnfs_saturn_sprite_palette`)"""
    from resources.eac.tnfs_saturn import (
        tnfs_saturn_palette_colors,
        tnfs_saturn_sprite_image,
        tnfs_saturn_sprite_palette,
    )

    output = []
    for i, entry in enumerate(bank['sprites']):
        colors = tnfs_saturn_palette_colors(palettes, tnfs_saturn_sprite_palette(entry))
        file_path = path_join(path, f'{bank_index}_{i}.png')
        tnfs_saturn_sprite_image(bank, i, colors).save(file_path, 'PNG')
        output.append(file_path)
    return output


class TnfsSaturnFrontendArtSerializer(BaseFileSerializer):
    """`UIDATA/FRONTEND.DAT` to a folder of PNGs (RGBA, colour index 0 transparent): `<bank>_<index>.png` for the
    sprites of banks 0..3, `4_<index>.png` for the font glyphs (their own width and height, palette
    `TNFS_SATURN_FONT_PALETTE`), `5_<index>.png` for the title screen's sprites, each sprite with its palette
    (`TNFS_SATURN_SCREEN_PALETTE` for none); `pcx_<index>.png` for the PCX files with the palettes of
    `TNFS_SATURN_FRONTEND_PCX_PALETTES`, `pcx_<index>_<palette>.png` for the other palettes of
    `TNFS_SATURN_FRONTEND_PCX_TINTS`"""

    ui = DIRECTORY_UI

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.tnfs_saturn import (
            TNFS_SATURN_FONT_PALETTE,
            TNFS_SATURN_FRONTEND_PCX_PALETTES,
            TNFS_SATURN_FRONTEND_PCX_TINTS,
            tnfs_saturn_palette_colors,
            tnfs_saturn_pcx_image,
            tnfs_saturn_sprite_image,
        )

        super().serialize(data, path)
        palettes = data['palettes']
        banks = list(data['sprite_banks'])
        output = []
        for bank_index, bank in enumerate(banks):
            output += tnfs_saturn_sprite_bank_files(bank, bank_index, path, palettes)
        font_colors = tnfs_saturn_palette_colors(palettes, TNFS_SATURN_FONT_PALETTE)
        font_index = len(banks)
        for i in range(len(data['font']['glyphs'])):
            file_path = path_join(path, f'{font_index}_{i}.png')
            tnfs_saturn_sprite_image(data['font'], i, font_colors).save(file_path, 'PNG')
            output.append(file_path)
        output += tnfs_saturn_sprite_bank_files(data['title_sprites'], font_index + 1, path, palettes)
        for i, picture in enumerate(data['pictures']):
            palette = TNFS_SATURN_FRONTEND_PCX_PALETTES[i] if i < len(TNFS_SATURN_FRONTEND_PCX_PALETTES) else 0
            names = [(f'pcx_{i}.png', palette)] + [
                (f'pcx_{i}_{tint}.png', tint) for tint in TNFS_SATURN_FRONTEND_PCX_TINTS.get(i, [])
            ]
            for name, palette in names:
                file_path = path_join(path, name)
                tnfs_saturn_pcx_image(picture['pcx'], tnfs_saturn_palette_colors(palettes, palette)).save(
                    file_path, 'PNG'
                )
                output.append(file_path)
        return output


def tnfs_saturn_frontend_art_path(file_path: str) -> Optional[str]:
    """`FRONTEND.DAT` (or the German `GRONTEND.DAT`) in the folder of `file_path`, any case"""
    folder = os.path.dirname(file_path)
    found = (find_file_case_insensitive(path_join(folder, name)) for name in ('FRONTEND.DAT', 'GRONTEND.DAT'))
    return next((x for x in found if x), None)


class TnfsSaturnSpriteBanksSerializer(BaseFileSerializer):
    """`UIDATA/SHOWCASE.DAT` (`TnfsSaturnSpriteBanks`) to a folder of `<bank>_<index>.png` (RGBA, colour index 0
    transparent), each sprite with its palette of the palette table of `FRONTEND.DAT` in the same folder"""

    ui = DIRECTORY_UI

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from library import require_file
        from library.exceptions import DataIntegrityException
        from library.loader import id_to_path
        from resources.eac.tnfs_saturn import TnfsSaturnFrontendArt

        frontend_path = tnfs_saturn_frontend_art_path(id_to_path(id)) if id else None
        if frontend_path is None:
            raise DataIntegrityException('The palettes of the sprites are in FRONTEND.DAT, not found next to the file')
        _, frontend_block, frontend = require_file(frontend_path)
        if not isinstance(frontend_block, TnfsSaturnFrontendArt):
            raise DataIntegrityException(f'{frontend_path} is not the menu art file with the palettes')
        super().serialize(data, path)
        output = []
        for bank_index, bank in enumerate(data['sprite_banks']):
            output += tnfs_saturn_sprite_bank_files(bank, bank_index, path, frontend['palettes'])
        return output


class TnfsSaturnRlePictureSerializer(BaseFileSerializer):
    """A word run-length encoded picture (`TnfsSaturnRlePicture`: `ELOAD/<car>/<n>.BIN`, `ECREDITS/0<n>.BIN`) to an
    RGB PNG, `<name>.png`"""

    ui = PNG_UI

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.tnfs_saturn import tnfs_saturn_rle_picture_image
        from serializers.misc.path_utils import escaped_file_path

        super().serialize(data, path, id=id, block=block)
        file_path = escaped_file_path(path, '.png')
        tnfs_saturn_rle_picture_image(data).save(file_path, 'PNG')
        return [file_path]

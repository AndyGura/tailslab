"""Serializers of the Sega Saturn TNFS port Over Drivin' GT-R (`resources/eac/tnfs_saturn.py`)"""

import json
import os
import re
from io import BytesIO
from typing import Dict, List, Optional

from library.utils import path_join
from serializers import BaseFileSerializer

# tyre textures `Tir1`..`Tir4` (`Tyr1`..`Tyr4` in the PGC10) are exported as `tyr1`..`tyr4`, the names of the PC and PSX
# exports, which nfs-web's TnfsCarMeshController loads
_TYRE_TEXTURE_NAME = re.compile(r'^t[iy]r([1-4])$', re.IGNORECASE)


def tnfs_saturn_texture_file_name(name: str) -> str:
    """Exported (PNG, GLB image) name of a texture of a Saturn texture bank"""
    match = _TYRE_TEXTURE_NAME.match(name)
    return f'tyr{match.group(1)}' if match else name


def tnfs_saturn_bank_textures(bank: dict) -> Dict[str, tuple]:
    """Exported name -> (PIL image, the 16 colours, set of colour indices used) of every texture of a bank"""
    from resources.eac.tnfs_saturn import (
        tnfs_saturn_texture_image,
        tnfs_saturn_texture_name,
        tnfs_saturn_texture_pixels,
    )

    result = {}
    for i, entry in enumerate(bank['textures']):
        name = tnfs_saturn_texture_file_name(tnfs_saturn_texture_name(entry))
        _, _, indices, colors = tnfs_saturn_texture_pixels(bank, i)
        result[name] = (tnfs_saturn_texture_image(bank, i), colors, set(indices))
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

    def __init__(self):
        super().__init__(is_dir=True)

    def ui_serialization(self):
        return {
            'file_type': 'directory',
            'is_directory': True,
            'output_file_name_suffix': None,
            'reversible': False,
            'reversible_settings_patch': {},
        }

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

    def __init__(self):
        super().__init__(is_dir=True)

    def ui_serialization(self):
        return {
            'file_type': 'directory',
            'is_directory': True,
            'output_file_name_suffix': None,
            'reversible': False,
            'reversible_settings_patch': {},
        }

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

    def __init__(self):
        super().__init__(is_dir=True)

    def ui_serialization(self):
        return {
            'file_type': 'directory',
            'is_directory': True,
            'output_file_name_suffix': None,
            'reversible': False,
            'reversible_settings_patch': {},
        }

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
    slot = os.path.basename(car_dir)
    for cars in ('CARS', 'cars', 'Cars'):
        for name in (f'{slot}.ALL', f'{slot}.all'):
            candidate = path_join(game_dir, cars, name)
            if os.path.isfile(candidate):
                return candidate
    return None

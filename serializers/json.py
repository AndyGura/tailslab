import json
from collections import defaultdict
from copy import deepcopy
from typing import List

from library.read_blocks import CompoundBlock
from serializers import BaseFileSerializer
from serializers.misc.json_utils import convert_bytes


def rec_dd():
    return defaultdict(rec_dd)


class JsonSerializer(BaseFileSerializer):
    # data is already valid dict, but we want to filter out unknown fields here
    def __make_dict(self, block, data):
        res = rec_dd()
        for key, value in data.items():
            try:
                usage = block.field_extras_map[key].get('usage', 'everywhere')
                show_by_usage = usage == 'everywhere' or 'ui' in usage
            except AttributeError:
                show_by_usage = True
            if isinstance(block, CompoundBlock) and (
                block.field_extras_map[key].get('is_unknown') or not show_by_usage
            ):
                continue
            try:
                value_block, value = block.get_child_block_with_data(data, key)
            except AttributeError:
                value_block = None
            if isinstance(value_block, CompoundBlock):
                res[key] = self.__make_dict(value_block, value)
            else:
                res[key] = value
        return res

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        super().serialize(data, path)
        json_str = json.dumps(convert_bytes(self.__make_dict(block, data)), indent=4)
        with open(f'{path}.json', 'w') as file:
            file.write(json_str)
        return [f'{path}.json']


class TnfsPsxHorizonInfoSerializer(BaseFileSerializer):
    """Values of a PSX TNFS `.INF` horizon settings file (`TnfsPsxHorizonInfo`) as JSON, named as in the file"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': False,
            'reversible_settings_patch': {},
        }

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.psx import parse_psx_horizon_settings

        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        super().serialize(data, path)
        settings = parse_psx_horizon_settings(data['text'])
        if settings is None:
            raise Exception('Not a PSX horizon settings file: fewer values than the game reads')
        with open(f'{path}.json', 'w') as file:
            json.dump(settings.as_dict(), file, indent=4)
        return [f'{path}.json']


class Nfs3CarPhysicsSerializer(JsonSerializer):
    """NFS3 / NFS4 `carp.txt` (`Nfs3CarPhysics`, `Nfs4CarPhysics`): the named values as `<name>.json`, plus the file
    itself as `<name>.bin` (byte-identical when unchanged), the raw copy the converter wrote before the format was
    parsed"""

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        output = super().serialize(data, path, id=id, block=block, **kwargs)
        with open(f'{path}.bin', 'wb') as file:
            file.write(block.pack(data))
        return output + [f'{path}.bin']

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs) -> dict:
        """The values of `<name>.json` put over the carp loaded under `id` (its text keeps its labels and number
        styles: the JSON it exported imports back to the same bytes), else over a new text; fields the JSON lacks
        keep their values"""
        data = _current_resource(id) or block.new_data()
        data = deepcopy(data)
        values = _read_json(file_paths)
        for name, *_ in block.carp_fields:
            if name in values:
                data[name] = values[name]
        return data


class CarFeDataSerializer(JsonSerializer):
    """NFS3 / NFS4 `fedata.<lang>` (`Nfs3CarFeData`, `Nfs4CarFeData`): every field as `<name>.json` (its texts a list
    in file order), plus the file itself as `<name>.bin`, the raw copy the converter wrote before the format was
    parsed. The JSON imports back to the same bytes"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        output = super().serialize(data, path, id=id, block=block, **kwargs)
        with open(f'{path}.bin', 'wb') as file:
            file.write(block.pack(data))
        return output + [f'{path}.bin']

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs) -> dict:
        data = block.new_data()
        values = _read_json(file_paths)
        for name, _ in block.field_blocks:
            if name in values:
                data[name] = values[name]
        return data


def _read_json(file_paths: List[str]) -> dict:
    from serializers.misc.json_utils import revert_bytes

    path = next((p for p in file_paths if p.lower().endswith('.json')), None)
    if path is None:
        raise Exception('No .json file given')
    with open(path, encoding='utf-8') as file:
        return revert_bytes(json.load(file))


def _current_resource(id: str):
    """The data loaded under `id`, which an import replaces (None without one)"""
    if not id:
        return None
    from library import require_resource

    try:
        (_, _, current), _ = require_resource(id)
        return current if isinstance(current, dict) else None
    except Exception:
        return None

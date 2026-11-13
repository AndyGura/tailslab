import json
from typing import List

from serializers.json import JsonSerializer


class IniFileSerializer(JsonSerializer):
    """Typed INI files (`IniFile`, `resources/eac/ini.py`): every value as `<name>.json`, sections as objects (keys by
    field name, a missing key null, arrays of numbered keys as lists), section groups and `other_sections` as lists,
    keys the definition lacks in `other_keys`. Comments and layout stay out. The JSON imports back: its values over
    the file loaded under `id` (layout kept), or a new file in the definition's key order"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        from resources.eac.ini import ini_data_from_json

        if len(file_paths) != 1:
            raise Exception('IniFileSerializer imports one JSON file')
        with open(file_paths[0], encoding='utf-8') as file:
            json_data = json.load(file)
        return ini_data_from_json(block, json_data, _current_data(id, block))


class BlockJsonSerializer(JsonSerializer):
    """A binary block whose every field (unknown ones too) is in its JSON export `<name>.json`, imported back into the
    same block (`block.from_json`): the file it writes is the original's when the JSON is unchanged"""

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from serializers.base import BaseFileSerializer
        from serializers.misc.json_utils import convert_bytes

        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        BaseFileSerializer.serialize(self, data, path)
        with open(f'{path}.json', 'w') as file:
            json.dump(convert_bytes(data), file, indent=4)
        return [f'{path}.json']

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        if len(file_paths) != 1:
            raise Exception('BlockJsonSerializer imports one JSON file')
        with open(file_paths[0], encoding='utf-8') as file:
            json_data = json.load(file)
        return block.from_json(json_data, _current_data(id, block))


def _current_data(id, block):
    if not id:
        return None
    try:
        from library import require_resource

        (_, current_block, current), _ = require_resource(id)
    except Exception:
        return None
    return current if isinstance(current, dict) and type(current_block) is type(block) else None

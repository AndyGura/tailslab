import json
from typing import List

from serializers import BaseFileSerializer
from serializers.misc.json_utils import convert_bytes, revert_bytes


class EaFieldDescriptionsSerializer(BaseFileSerializer):
    """EA's field descriptions (`.DES`, `EaFieldDescriptions`) as `<name>.json`: `data_size` and `fields` (the fields
    the file describes, groups flattened: `des_fields`, path, type, name, offset, size, value in its data copy), and
    `body`, every parsed field with the memory garbage (bytes as `{"$bytes": [...]}`), from which the JSON imports back
    to the same file"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from resources.eac.field_descriptions import des_fields, DES_UI_KEYS

        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        super().serialize(data, path)
        body = {key: value for key, value in data.items() if key not in DES_UI_KEYS}
        res = {'data_size': len(data['data']), 'fields': des_fields(data), 'body': convert_bytes(body)}
        with open(f'{path}.json', 'w') as file:
            json.dump(res, file, indent=4)
        return [f'{path}.json']

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        json_path = next((p for p in file_paths if p.lower().endswith('.json')), file_paths[0])
        with open(json_path) as f:
            value = json.load(f)
        if 'body' not in value:
            raise ValueError('Not a .DES export: no "body"')
        return revert_bytes(value['body'])

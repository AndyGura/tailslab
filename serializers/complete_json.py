import json
import math
from typing import List

from library.read_blocks import DataBlock, DecimalBlock
from library.read_blocks.array import ArrayBlock
from library.read_blocks.compound import CompoundBlock
from serializers.json import JsonSerializer
from serializers.misc.json_utils import convert_bytes, revert_bytes


class CompleteJsonSerializer(JsonSerializer):
    """Every parsed field of a record file as `<name>.json` (`JsonSerializer`'s file, with the fields it leaves out
    too: unknown ones, the ones hidden from the editor), in field order; bytes as `{"$bytes": [...]}`, a NaN float as
    "NaN". Reversible: the JSON imports back over the resource (`deserialize`), and a file exported and imported again
    writes back byte-exact. Used by the NFS5 car data files (`.sim`, `.ais`, `nfs5.car`, `nfs5.prt`...)"""

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
        # BaseFileSerializer: makes the folder
        super(JsonSerializer, self).serialize(data, path)
        with open(f'{path}.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(convert_bytes(data), indent=4, ensure_ascii=False))
        return [f'{path}.json']

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        if len(file_paths) != 1:
            raise Exception('Import one JSON file')
        with open(file_paths[0], encoding='utf-8') as file:
            value = revert_bytes(json.load(file))
        data = complete_json_value(block, value)
        # refuses values the block cannot write (a text too long, a missing field) before anything changes
        block.pack(data)
        return data


def complete_json_value(block: DataBlock, value):
    """`value` read from JSON as the block's data: "NaN" back to a float NaN where the block reads a float, every
    compound field present (missing ones: the block's new data)"""
    if isinstance(block, DecimalBlock):
        return math.nan if value == 'NaN' else value
    if isinstance(block, CompoundBlock) and isinstance(value, dict):
        result = {}
        for name, child in block.field_blocks_map.items():
            result[name] = complete_json_value(child, value[name]) if name in value else child.new_data()
        return result
    if isinstance(block, ArrayBlock) and isinstance(value, list) and block.child is not None:
        return [complete_json_value(block.child, item) for item in value]
    return value

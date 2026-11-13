import json
from typing import List

from library.read_blocks import ArrayBlock, CompoundBlock, DataBlock
from serializers.json import JsonSerializer
from serializers.misc.json_utils import revert_bytes


def merge_json_values(block: DataBlock, data, value):
    """`data` (the block's data) with the values of `value` (the block's JSON export) put over it: compound fields
    by name, array items by index; fields the JSON lacks (left out by the export, e.g. not shown in the GUI) keep
    their values"""
    if isinstance(block, CompoundBlock) and isinstance(value, dict) and isinstance(data, dict):
        res = dict(data)
        for name, field in block.field_blocks:
            if name in value:
                res[name] = merge_json_values(field, data.get(name), value[name])
        return res
    if isinstance(block, ArrayBlock) and isinstance(value, list) and isinstance(data, list):
        res = list(data)
        for i, item in enumerate(value):
            if i < len(res):
                res[i] = merge_json_values(block.child, res[i], item)
            else:
                res.append(merge_json_values(block.child, block.child.new_data(), item))
        return res[: len(value)]
    return revert_bytes(value)


class Nfs2DataJsonSerializer(JsonSerializer):
    """NFS2 / NFS2 SE fixed-layout data files (`Nfs2CarPhysics`, `Nfs2SimTune`, `Nfs2CarAi`, `Nfs2TrafficConfig`,
    `Nfs2Personalities`; also inside a `.QDA`) as `<name>.json`, every field by name (JsonSerializer's output). The JSON
    imports back: its values over the resource's data (or a new one), so an export imports back to the same bytes"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': True,
            'reversible_settings_patch': {},
        }

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        json_path = next((p for p in file_paths if p.lower().endswith('.json')), file_paths[0])
        with open(json_path) as f:
            value = json.load(f)
        current = None
        if id is not None:
            try:
                from library import require_resource

                (_, _, current), _ = require_resource(id)
            except Exception:
                current = None
        return merge_json_values(block, current if current is not None else block.new_data(), value)

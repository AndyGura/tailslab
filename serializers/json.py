import json
from collections import defaultdict
from typing import List

from library.read_blocks import ArrayBlock, CompoundBlock, DataBlock
from serializers import BaseFileSerializer
from serializers.base import REVERSIBLE_JSON_UI, current_resource
from serializers.misc.json_utils import convert_bytes, revert_bytes


def rec_dd():
    return defaultdict(rec_dd)


class JsonSerializer(BaseFileSerializer):
    """The resource as `<name>.json` (`json_value`): the fields the GUI shows but the unknown ones, or every field with
    `all_fields`; bytes as `{"$bytes": [...]}`, a NaN float as "NaN". `indent` and `ensure_ascii` go to `json.dumps`;
    with `with_bin` also `<name>.bin`, the resource as its block writes it"""

    all_fields = False
    indent = 4
    ensure_ascii = True
    with_bin = False

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

    def json_value(self, data, block):
        """What `<name>.json` holds"""
        return convert_bytes(data if self.all_fields else self.__make_dict(block, data))

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        path = self.output_path(path, id)
        super().serialize(data, path)
        json_str = json.dumps(self.json_value(data, block), indent=self.indent, ensure_ascii=self.ensure_ascii)
        with open(f'{path}.json', 'w', encoding='utf-8') as file:
            file.write(json_str)
        output = [f'{path}.json']
        if self.with_bin:
            with open(f'{path}.bin', 'wb') as file:
                file.write(block.pack(data))
            output.append(f'{path}.bin')
        return output


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


def read_json_file(file_paths: List[str]):
    """The value of the JSON file among `file_paths` (the `.json` one, else the only file), bytes reverted"""
    path = next((p for p in file_paths if p.lower().endswith('.json')), None)
    if path is None and len(file_paths) == 1:
        path = file_paths[0]
    if path is None:
        raise Exception('No .json file given')
    with open(path, encoding='utf-8') as file:
        return revert_bytes(json.load(file))


class ReversibleJsonSerializer(JsonSerializer):
    """A `JsonSerializer` whose JSON imports back (`deserialize`): `json_to_data` makes the block's data from the JSON
    and the data the import replaces. As it is: NFS2 / NFS2 SE fixed-layout data files (`Nfs2CarPhysics`,
    `Nfs2SimTune`, `Nfs2CarAi`, `Nfs2TrafficConfig`, `Nfs2Personalities`; also inside a `.QDA`), whose export imports
    back to the same bytes"""

    ui = REVERSIBLE_JSON_UI

    def json_to_data(self, block: DataBlock, value, current):
        """The block's data from the JSON `value` (bytes reverted) and `current` (the data the import replaces, None
        without one): the JSON's values over `current` or over new data (`merge_json_values`)"""
        return merge_json_values(block, current if current is not None else block.new_data(), value)

    def deserialize(self, file_paths: List[str], id=None, block=None, current=None, **kwargs):
        """`current`: the data the import replaces, by default the data loaded under `id`"""
        if current is None:
            current = current_resource(id, block)
        return self.json_to_data(block, read_json_file(file_paths), current)


class Nfs3CarPhysicsSerializer(ReversibleJsonSerializer):
    """NFS3 / NFS4 `carp.txt` (`Nfs3CarPhysics`, `Nfs4CarPhysics`): the named values as `<name>.json`, plus the file
    itself as `<name>.bin` (byte-identical when unchanged), the raw copy the converter wrote before the format was
    parsed. The import puts the values over the carp loaded under `id` (its text keeps its labels and number styles:
    the JSON it exported imports back to the same bytes), else over a new text; fields the JSON lacks keep their
    values"""

    with_bin = True


class CarFeDataSerializer(ReversibleJsonSerializer):
    """NFS3 / NFS4 `fedata.<lang>` (`Nfs3CarFeData`, `Nfs4CarFeData`): every field as `<name>.json` (its texts a list
    in file order), plus the file itself as `<name>.bin`, the raw copy the converter wrote before the format was
    parsed. The JSON imports back to the same bytes"""

    with_bin = True

import copy
import json
import os
from typing import List, Optional

from library.utils import path_join
from resources.blackbox.chunks import find_chunk
from serializers.base import BaseFileSerializer, UiSerialization, current_resource
from serializers.json import merge_json_values, read_json_file
from serializers.misc.json_utils import convert_bytes

# NFS Hot Pursuit 2 (PS2) car spec data of a chunk bundle (GLOBAL/GLOBALB): the car types table (chunk 0x34600) and the
# paints (chunk 0x34601), every parsed value of every entry, bytes as {"$bytes": [...]}
CAR_TYPES_JSON = 'car_types.json'
CAR_SKINS_JSON = 'car_skins.json'
_CHUNKS = {CAR_TYPES_JSON: (0x00034600, 'car_types'), CAR_SKINS_JSON: (0x00034601, 'skins')}


def _bundle_chunks(data: dict) -> list:
    from serializers.maps import nfs6_ps2_bundle_chunks

    return nfs6_ps2_bundle_chunks(data)


def nfs6_ps2_car_spec_chunk(data: dict, chunk_id: int) -> Optional[dict]:
    """The data of the chunk `chunk_id` of an NFS Hot Pursuit 2 (PS2) bundle (also of a COMP-compressed one), or None"""
    return find_chunk(_bundle_chunks(data), chunk_id)


def nfs6_ps2_car_spec_json(entries: list) -> list:
    """Car types / paints as written to JSON: every field, bytes as {"$bytes": [...]}"""
    return convert_bytes(entries)


def _chunk_field_block(chunk_id: int, key: str):
    from resources.blackbox.maps.nfs6_ps2 import Nfs6Ps2CarSkins, Nfs6Ps2CarTypeInfos

    block_class = Nfs6Ps2CarTypeInfos if chunk_id == _CHUNKS[CAR_TYPES_JSON][0] else Nfs6Ps2CarSkins
    return block_class().field_blocks_map[key]


class Nfs6Ps2ChunkBundleSerializer(BaseFileSerializer):
    """NFS Hot Pursuit 2 (PS2) chunk bundle without a world or a car model (GLOBAL/GLOBALB, INGAMEB, FRONTEND/FRONTB,
    texture packs): the car spec data it holds as JSON in the output folder, `car_types.json` ({"car_types": [...]},
    the 64 car types of chunk 0x34600) and `car_skins.json` ({"skins": [...]}, chunk 0x34601). A bundle without them
    writes nothing. The import puts these files' values back (keys a file lacks keep theirs): unchanged files write
    the bundle back byte-exact"""

    ui = UiSerialization('directory', is_directory=True, suffix='', reversible=True)

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        path = self.output_path(path, id)
        written = []
        for file_name, (chunk_id, key) in _CHUNKS.items():
            chunk = nfs6_ps2_car_spec_chunk(data, chunk_id)
            if chunk is None:
                continue
            os.makedirs(path, exist_ok=True)
            out = path_join(path, file_name)
            with open(out, 'w') as f:
                json.dump({key: nfs6_ps2_car_spec_json(chunk[key])}, f, indent=2)
            written.append(out)
        return written

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        current = current_resource(id)
        if current is None:
            raise Exception(f'No bundle loaded under {id}')
        return self.apply_json(current, file_paths)

    @staticmethod
    def apply_json(current: dict, file_paths: List[str]) -> dict:
        """A copy of the bundle data `current` with the values of the JSON files (car_types.json, car_skins.json, or
        a folder holding them)"""
        files = []
        for p in file_paths:
            if os.path.isdir(p):
                files += [path_join(p, x) for x in _CHUNKS if os.path.isfile(path_join(p, x))]
            else:
                files.append(p)
        updated = copy.deepcopy(current)
        applied = 0
        for p in files:
            name = os.path.basename(p).lower()
            if name not in _CHUNKS:
                continue
            chunk_id, key = _CHUNKS[name]
            chunk = nfs6_ps2_car_spec_chunk(updated, chunk_id)
            if chunk is None:
                raise Exception(f'The bundle has no chunk {hex(chunk_id)} for {name}')
            values = read_json_file([p])[key]
            chunk[key] = merge_json_values(_chunk_field_block(chunk_id, key), chunk[key], values)
            applied += 1
        if not applied:
            raise Exception(f'No {" or ".join(_CHUNKS)} among the files')
        return updated

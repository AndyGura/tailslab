import json
from typing import List

from serializers import BaseFileSerializer


class EacHorizonSettingsSerializer(BaseFileSerializer):
    """Sky settings of a track (NFS2 / NFS2 SE / NFS3 `.HRZ`, NFS4 `Tr.ini`, `resources/eac/horizons.py`) as JSON:
    the values named as the block's `parse` names them"""

    def ui_serialization(self):
        return {
            'file_type': 'json',
            'is_directory': False,
            'output_file_name_suffix': '.json',
            'reversible': False,
            'reversible_settings_patch': {},
        }

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        if path.endswith('/') or path.endswith('\\'):
            path += id[id.rindex('/') + 1 :]
        super().serialize(data, path)
        settings = block.parse(data['text'])
        if settings is None:
            raise Exception('Fewer values than the game reads')
        with open(f'{path}.json', 'w') as file:
            json.dump(settings.as_dict(), file, indent=4)
        return [f'{path}.json']

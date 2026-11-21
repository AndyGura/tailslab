from serializers.base import JSON_UI
from serializers.json import JsonSerializer


class EacHorizonSettingsSerializer(JsonSerializer):
    """Sky settings of a track (NFS2 / NFS2 SE / NFS3 `.HRZ`, NFS4 `Tr.ini`, `resources/eac/horizons.py`; PSX TNFS
    `.INF`, `TnfsPsxHorizonInfo`) as JSON: the values named as the block's `parse` names them"""

    ui = JSON_UI

    def json_value(self, data, block):
        settings = block.parse(data['text'])
        if settings is None:
            raise Exception('Fewer values than the game reads')
        return settings.as_dict()

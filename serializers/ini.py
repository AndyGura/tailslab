from serializers.json import ReversibleJsonSerializer


class IniFileSerializer(ReversibleJsonSerializer):
    """Typed INI files (`IniFile`, `resources/eac/ini.py`): every value as `<name>.json`, sections as objects (keys by
    field name, a missing key null, arrays of numbered keys as lists), section groups and `other_sections` as lists,
    keys the definition lacks in `other_keys`. Comments and layout stay out. The JSON imports back: its values over
    the file loaded under `id` (layout kept), or a new file in the definition's key order"""

    def json_to_data(self, block, value, current):
        from resources.eac.ini import ini_data_from_json

        return ini_data_from_json(block, value, current)

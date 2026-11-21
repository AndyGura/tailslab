from serializers.json import ReversibleJsonSerializer
from serializers.misc.json_utils import convert_bytes


class EaFieldDescriptionsSerializer(ReversibleJsonSerializer):
    """EA's field descriptions (`.DES`, `EaFieldDescriptions`) as `<name>.json`: `data_size` and `fields` (the fields
    the file describes, groups flattened: `des_fields`, path, type, name, offset, size, value in its data copy), and
    `body`, every parsed field with the memory garbage (bytes as `{"$bytes": [...]}`), from which the JSON imports back
    to the same file"""

    def json_value(self, data, block):
        from resources.eac.field_descriptions import des_fields, DES_UI_KEYS

        body = {key: value for key, value in data.items() if key not in DES_UI_KEYS}
        return {'data_size': len(data['data']), 'fields': des_fields(data), 'body': convert_bytes(body)}

    def json_to_data(self, block, value, current):
        if 'body' not in value:
            raise ValueError('Not a .DES export: no "body"')
        return value['body']

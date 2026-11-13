import json
import os
import tempfile
import unittest
from io import BytesIO

from library.loader import probe_block_class
from resources.eac.car_specs import Nfs3CarPhysics, Nfs4CarPhysics
from resources.eac.fedata import Nfs3CarFeData, Nfs4CarFeData, NFS3_FEDATA_TEXTS, NFS4_FEDATA_TEXTS
import serializers.json as json_serializers

_NFS3 = 'test/samples/nfs3_fedata'
_NFS4 = 'test/samples/nfs4_fedata'


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


class TestCarFeData(unittest.TestCase):
    def test_samples_round_trip(self):
        for folder, cls in ((_NFS3, Nfs3CarFeData), (_NFS4, Nfs4CarFeData)):
            for name in sorted(os.listdir(folder)):
                raw = _read(os.path.join(folder, name))
                block = cls()
                data = block.unpack_from_bytes(raw)
                self.assertEqual(block.pack(data), raw, name)
                self.assertEqual(block.estimate_packed_size(data), len(raw), name)

    def test_nfs3_fields(self):
        data = Nfs3CarFeData().unpack_from_bytes(_read(f'{_NFS3}/Diab.eng'))
        self.assertEqual(data['car_id'], 'Diab')
        self.assertEqual(data['format_version'], 9)
        self.assertEqual((data['bonus'], data['filter_flag'], data['car_class'], data['police']), (0, 1, 0, 0))
        self.assertEqual(data['serial_number'], 16)
        self.assertEqual(data['interior_view_heading'], 311)
        self.assertEqual([data[k] for k in ('acceleration', 'top_speed', 'handling', 'braking')], [18, 17, 13, 15])
        self.assertEqual(len(data['texts']), len(NFS3_FEDATA_TEXTS))
        self.assertEqual(data['texts'][2], 'Lamborghini Diablo SV')
        self.assertEqual(data['texts'][21], '5 speed')
        self.assertEqual(data['texts'][30], 'Giallo')
        spa = Nfs3CarFeData().unpack_from_bytes(_read(f'{_NFS3}/Amd7.spa'))
        self.assertEqual(spa['driver_seat'], 1)  # right-hand drive
        self.assertTrue(any('ñ' in t for t in spa['texts']))  # Latin-1

    def test_nfs4_fields(self):
        data = Nfs4CarFeData().unpack_from_bytes(_read(f'{_NFS4}/Mcf1.eng'))
        self.assertEqual((data['game'], data['car_id'], data['serial_number']), (4, 'Mcf1', 2))
        self.assertEqual((data['car_class'], data['format_version'], data['engine_position']), (0, 10, 1))
        self.assertEqual(data['acceleration'], [20, 20, 20, 20])
        self.assertEqual(data['overall_rating'], [19, 19, 19, 19])
        self.assertEqual((data['price'], data['upgrade_prices']), (500000, [5000, 3000, 7000]))
        self.assertTrue(data['flags']['no_upgrades'])
        self.assertFalse(data['flags']['police'])
        self.assertEqual(len(data['texts']), len(NFS4_FEDATA_TEXTS))
        self.assertEqual(data['texts'][17], '')  # special
        self.assertEqual(data['texts'][31], 'Orange')
        b911 = Nfs4CarFeData().unpack_from_bytes(_read(f'{_NFS4}/B911.ger'))
        self.assertTrue(b911['flags']['bonus'] and b911['flags']['fixed_color'])
        self.assertEqual(b911['engine_position'], 2)

    def test_first_empty_text_points_into_the_offset_table(self):
        # the shipped layout: an empty first text points at the offset table's last byte
        raw = _read(f'{_NFS4}/Elni.eng')
        data = Nfs4CarFeData().unpack_from_bytes(raw)
        self.assertEqual(data['texts'][0], '')
        self.assertEqual(int.from_bytes(raw[0x3C0:0x3C4], 'little'), 0x463)
        self.assertEqual(data['texts'][1], 'La Niña')

    def test_text_edits_rebuild_the_table(self):
        block = Nfs3CarFeData()
        data = block.unpack_from_bytes(_read(f'{_NFS3}/Diab.eng'))
        data['texts'][3] = 'Priceless — no'.replace('—', '-')
        data['texts'][4] = ''
        data['texts'].append('extra')
        raw = block.pack(data)
        again = block.unpack_from_bytes(raw)
        self.assertEqual(again['texts'], data['texts'])
        self.assertEqual(int.from_bytes(raw[0x2D:0x2F], 'little'), 41)

    def test_loader_picks_by_name_and_content(self):
        for path, cls in (
            (f'{_NFS3}/Diab.eng', Nfs3CarFeData),
            (f'{_NFS4}/Mcf1.eng', Nfs4CarFeData),
        ):
            raw = _read(path)
            item = f'games/x/car.viv__children/3_fedata.{path.rsplit(".", 1)[1]}'
            self.assertIs(probe_block_class(BytesIO(raw), item, len(raw)), cls)

    def test_json_imports_back_byte_exact(self):
        for path, cls in ((f'{_NFS3}/Amd7.spa', Nfs3CarFeData), (f'{_NFS4}/Elni.eng', Nfs4CarFeData)):
            raw = _read(path)
            block = cls()
            data = block.unpack_from_bytes(raw)
            serializer = block.serializer_class()()
            with tempfile.TemporaryDirectory() as folder:
                outputs = serializer.serialize(data, os.path.join(folder, 'fedata.eng'), block=block)
                self.assertEqual([os.path.basename(p) for p in outputs], ['fedata.eng.json', 'fedata.eng.bin'])
                self.assertEqual(_read(outputs[1]), raw)
                with open(outputs[0], encoding='utf-8') as f:
                    self.assertEqual(json.load(f)['texts'], data['texts'])
                back = serializer.deserialize(outputs, block=block)
            self.assertEqual(block.pack(back), raw)


class TestCarpPlacAndJson(unittest.TestCase):
    def test_plac_carp_is_read(self):
        for path, cls, item in (
            (
                'test/samples/carp_plac/nfs3_carp.txt',
                Nfs3CarPhysics,
                'games/nfs3/FeData/Plac/CAR.VIV__children/0_carp.txt',
            ),
            ('test/samples/carp_plac/nfs4_carp.txt', Nfs4CarPhysics, 'games/nfs4/Data/Plac.viv__children/0_carp.txt'),
        ):
            raw = _read(path)
            self.assertIs(probe_block_class(BytesIO(raw), item, len(raw)), cls)
            block = cls()
            data = block.unpack_from_bytes(raw)
            self.assertEqual(data['serial_number'], 0)
            self.assertEqual(data['mass'], 1000.0)  # the default carp
            self.assertEqual(block.pack(data), raw)

    def test_carp_json_imports_back(self):
        for path, cls in (
            ('test/samples/nfs3_carp/Diab.txt', Nfs3CarPhysics),
            ('test/samples/nfs4_carp/B911.txt', Nfs4CarPhysics),
        ):
            raw = _read(path)
            block = cls()
            data = block.unpack_from_bytes(raw)
            serializer = block.serializer_class()()
            original = json_serializers._current_resource
            try:
                with tempfile.TemporaryDirectory() as folder:
                    outputs = serializer.serialize(data, os.path.join(folder, 'carp.txt'), block=block)
                    self.assertEqual(_read(outputs[1]), raw)
                    # over the loaded file: the same bytes
                    json_serializers._current_resource = lambda id: data
                    self.assertEqual(block.pack(serializer.deserialize(outputs, id='x', block=block)), raw)
                    # without one: a new text the game reads the same values from
                    json_serializers._current_resource = lambda id: None
                    fresh = serializer.deserialize(outputs, id=None, block=block)
                    again = block.unpack_from_bytes(block.pack(fresh))
                    for name, *_ in block.carp_fields:
                        self.assertEqual(again[name], data[name], name)
            finally:
                json_serializers._current_resource = original


if __name__ == '__main__':
    unittest.main()

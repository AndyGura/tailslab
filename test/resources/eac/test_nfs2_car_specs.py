import os
import tempfile
from copy import deepcopy
import unittest
from io import BytesIO

from library import require_file
from resources.eac.archives import EacCompressedBlock
from resources.eac.field_descriptions import (
    EaFieldDescriptions,
    block_layout,
    des_check,
    des_fields,
    described_block,
)
from serializers import get_serializer

SAMPLES = 'test/samples/nfs2_car_specs'


def _uncompressed(path):
    with open(path, 'rb') as f:
        raw = f.read()
    return EacCompressedBlock._compression_for_header(raw[0], raw[1]).uncompress(BytesIO(raw), len(raw))


def _viv_items():
    (name, block, res) = require_file('test/samples/CARDATA.VIV', lazy=False)
    return [
        (child['alias'], block.item_block.possible_blocks[child['item']['choice_index']], child['item']['data'])
        for child in res['children']
    ]


def _json_round_trip(test, block, data, name='item'):
    """Export with the block's serializer, import the JSON back, compare the bytes"""
    serializer = get_serializer(block, data)
    with tempfile.TemporaryDirectory() as out:
        paths = serializer.serialize(data, os.path.join(out, name), id=name, block=block)
        test.assertTrue(paths and paths[0].endswith('.json'), paths)
        restored = serializer.deserialize(paths, id=None, block=block)
    test.assertEqual(block.pack(data), block.pack(restored))


class TestNfs2CompressedCopies(unittest.TestCase):
    def test_qda_files_open_with_the_dat_blocks(self):
        for file, class_name in [
            ('PCALA.QDA', 'Nfs2CarPhysics'),  # QFS3
            ('PCHEV.QDA', 'Nfs2CarPhysics'),  # RefPack
            ('SIMTUNE.QDA', 'Nfs2SimTune'),
            ('CALA.QDA', 'Nfs2CarAi'),  # NFS2 SIM/AICARDT
        ]:
            path = f'{SAMPLES}/{file}'
            (name, block, data) = require_file(path, lazy=False)
            self.assertEqual(block.__class__.__name__, 'EacCompressedBlock')
            inner = block.possible_blocks[data['choice_index']]
            self.assertEqual(inner.__class__.__name__, class_name, file)
            self.assertEqual(inner.pack(data['data']), _uncompressed(path), file)
            with open(path, 'rb') as f:
                self.assertEqual(block.pack(data), f.read(), file)
            _json_round_trip(self, inner, data['data'], file)

    def test_changed_qda_is_compressed_again(self):
        (name, block, data) = require_file(f'{SAMPLES}/PCALA.QDA', lazy=False)
        data = deepcopy(data)
        data['data']['mass'] = 1400.0
        packed = block.pack(data)
        # written back with the algorithm it was read with (QFS3)
        self.assertEqual(packed[:2], b'\x30\xfb')
        uncompressed = EacCompressedBlock._compression_for_header(0x30, 0xFB).uncompress(BytesIO(packed), len(packed))
        again = block.possible_blocks[data['choice_index']].unpack_from_bytes(uncompressed)
        self.assertEqual(again['mass'], 1400.0)


class TestNfs2DataJson(unittest.TestCase):
    def test_viv_items_export_to_json_and_import_back(self):
        kinds = set()
        for alias, block, data in _viv_items():
            if block.__class__.__name__.startswith('Nfs2'):
                kinds.add(block.__class__.__name__)
                _json_round_trip(self, block, data, alias)
        self.assertEqual(
            kinds, {'Nfs2CarPhysics', 'Nfs2SimTune', 'Nfs2CarAi', 'Nfs2TrafficConfig', 'Nfs2Personalities'}
        )

    def test_json_import_takes_the_changed_values(self):
        alias, block, data = next(x for x in _viv_items() if x[0] == 'pcala.DAT')
        serializer = get_serializer(block, data)
        with tempfile.TemporaryDirectory() as out:
            paths = serializer.serialize(data, os.path.join(out, alias), id=alias, block=block)
            import json

            with open(paths[0]) as f:
                value = json.load(f)
            value['torque_curve'][3] = 333.5
            value['spin_velocity_cap'] = 0.5
            with open(paths[0], 'w') as f:
                json.dump(value, f)
            restored = serializer.deserialize(paths, id=None, block=block)
        self.assertEqual(restored['torque_curve'][3], 333.5)
        self.assertEqual(restored['spin_velocity_cap'], 0.5)
        self.assertEqual(restored['mass'], data['mass'])


class TestEaFieldDescriptions(unittest.TestCase):
    def test_des_files_round_trip_and_match_the_dat_blocks(self):
        for file, class_name, size in [
            ('PCALA.DES', 'Nfs2CarPhysics', 356),
            ('MCF1.DES', 'Nfs2CarAi', 524),
            ('SIMTUNE.DES', 'Nfs2SimTune', 232),
            ('TRAFCFG.DES', 'Nfs2TrafficConfig', 452),
        ]:
            path = f'{SAMPLES}/{file}'
            (name, block, data) = require_file(path, lazy=False)
            self.assertEqual(block.__class__.__name__, 'EaFieldDescriptions', file)
            with open(path, 'rb') as f:
                self.assertEqual(block.pack(data), f.read(), file)
            self.assertEqual(len(data['data']), size)
            self.assertEqual(data['dat_block'], class_name)
            target = described_block(size, file)
            self.assertEqual(des_check(des_fields(data), block_layout(target)), [], file)
            _json_round_trip(self, block, data, file)

    def test_fields_are_flattened_with_offsets_and_values(self):
        (name, block, data) = require_file(f'{SAMPLES}/MCF1.DES', lazy=False)
        fields = {x['path']: x for x in des_fields(data)}
        self.assertEqual(fields['AI']['type'], 'Chain')
        self.assertEqual(fields['AI/Redline']['offset'], 4)
        self.assertEqual(fields['AI/Redline']['value'], 7500.0)
        self.assertEqual(fields['AI/Top Speed in each gear (m/s)']['shape'], [1, 7, 7])
        self.assertEqual(fields['AI/Arcade Mode Levers/Grip']['offset'], 0x10C + 0xE0)
        self.assertEqual(fields['AI/Lane Slack Prob']['offset'], 0x208)

    def test_physics_des_names_and_types(self):
        (name, block, data) = require_file(f'{SAMPLES}/PCALA.DES', lazy=False)
        fields = des_fields(data)
        self.assertEqual([x['type'] for x in fields[:4]], ['Fixed', 'Integer', 'Integer', 'Array'])
        self.assertEqual(fields[3]['shape'], [1, 8, 8])
        # the file order of the swapped specs pair
        self.assertEqual(
            [x['name'] for x in fields if x['offset'] in (0x140, 0x144)], ['gas off factor', 'g transfer factor']
        )

    def test_renamed_record_keeps_the_field_size(self):
        blk = EaFieldDescriptions()
        with open(f'{SAMPLES}/SIMTUNE.DES', 'rb') as f:
            raw = f.read()
        data = blk.unpack_from_bytes(raw)
        data['records'][1]['name'] = 'a longer name for the initial jump roll attenuate field'
        data['records'][2]['name'] = 'short'
        packed = blk.pack(data)
        self.assertEqual(len(packed), len(raw))
        again = blk.unpack_from_bytes(packed)
        self.assertEqual(again['records'][1]['name'], 'a longer name for the initial jump roll attenuate field')
        self.assertEqual(again['records'][2]['name'], 'short')
        self.assertEqual(again['records'][3], data['records'][3])

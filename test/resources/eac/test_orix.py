import os
import unittest
from io import BytesIO

from library import require_file
from library.context import ReadContext
from resources.eac.geometries import OrixGeometry
from resources.eac.psx import psx_crc16

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')


class TestOrixGeometry(unittest.TestCase):
    def test_car_archive_models(self):
        path = os.path.join(SAMPLES, 'ZTSUPRA.VSM')
        name, block, data = require_file(path, lazy=False)
        children = {x['alias']: x['item'] for x in data['children']}
        for alias in ('tsupra.por', 'tsupral.por'):
            item = children[alias]
            self.assertIsInstance(block.item_block.possible_blocks[item['choice_index']], OrixGeometry)
        model = children['tsupra.por']['data']
        self.assertEqual(model['version'], 800)
        self.assertEqual(model['name'].rstrip('\0'), '_SUPRA')
        self.assertEqual((model['num_vrtx'], model['num_shape_vrtx'], len(model['polygons'])), (118, 102, 65))
        self.assertEqual(len(model['polygon_textures']), 55)
        self.assertEqual(model['polygon_textures'][0], {'polygon_index': 0, 'file_name': 'J000'})
        self.assertEqual({x['draw_type'] for x in model['polygons']}, {12})
        # 32:7 fixed point, as the PC car models: the car is 1.89 m wide and 4.55 m long
        self.assertEqual(model['vertices']['choice_index'], 0)
        shape = model['vertices']['data'][: model['num_shape_vrtx']]
        self.assertAlmostEqual(max(v['x'] for v in shape) - min(v['x'] for v in shape), 242 / 128)
        self.assertAlmostEqual(max(v['z'] for v in shape) - min(v['z'] for v in shape), 582 / 128)
        material = model['materials'][0]
        self.assertEqual(
            material['textures'],
            {
                'unknown': 1,
                'num_polygon_textures': 10,
                'first_polygon_texture': 0,
                'per_polygon_textures': True,
                'unknown_bit_0': True,
            },
        )
        self.assertFalse(model['materials'][5]['textures']['per_polygon_textures'])
        self.assertEqual(model['materials'][5]['name'], b'rertires')
        self.assertEqual([x['name'] for x in model['morphs']], ['left_tur', 'right_tu'])
        self.assertEqual([x['name'] for x in model['partitions']], ['NON-SORT', 'inside', 'surface', 'outside'])
        # every item of a car archive ends with its own CRC footer
        self.assertIsNotNone(model['crc_footer'])
        with open(path, 'rb') as f:
            original = f.read()
        self.assertEqual(block.pack(data), original)

    def test_changed_model_gets_new_size_and_crc(self):
        name, block, data = require_file(os.path.join(SAMPLES, 'ZTSUPRA.VSM'), lazy=False)
        item = next(x['item'] for x in data['children'] if x['alias'] == 'tsupra.por')
        orix = block.item_block.possible_blocks[item['choice_index']]
        model = item['data']
        original = orix.pack(model)
        model['labels'].append({'name': 'test', 'offset': [0, 0, 0], 'index': 1})
        packed = orix.pack(model)
        self.assertEqual(len(packed), len(original) + 12)
        self.assertEqual(int.from_bytes(packed[4:8], 'little'), len(packed) - 12)
        self.assertEqual(packed[-12:-8], b'CRCF')
        self.assertEqual(int.from_bytes(packed[-4:], 'little'), psx_crc16(packed[:-12]))
        # the vertex format follows the file name
        buffer = BytesIO(packed)
        buffer.name = 'tsupra.por'
        again = orix.unpack(ReadContext(buffer), read_bytes_amount=len(packed))
        self.assertEqual(again['vertices'], model['vertices'])
        self.assertEqual(again['num_lbl'], 7)
        self.assertEqual(again['labels'][-1]['name'], 'test')
        self.assertEqual(again['vmap'], model['vmap'])
        self.assertEqual(again['lbl_ptr'] + 7 * 12, again['vrtx_ptr'])

    def test_track_props(self):
        path = os.path.join(SAMPLES, 'ZAL1_POR.FAM')
        name, block, data = require_file(path, lazy=False)
        item = data['children'][0]['item']
        self.assertIsInstance(block.item_block.possible_blocks[item['choice_index']], OrixGeometry)
        model = item['data']
        self.assertEqual(model['name'].rstrip('\0'), '_TRESTLE')
        # 32:4 fixed point, as the PC props; the footer after it is the one of the FAM
        self.assertEqual(model['vertices']['choice_index'], 1)
        self.assertIsNone(model['crc_footer'])
        with open(path, 'rb') as f:
            original = f.read()
        self.assertEqual(block.pack(data), original)

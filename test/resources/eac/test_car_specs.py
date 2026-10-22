import unittest

from library import require_file


class TestPlayerCarPhysics(unittest.TestCase):
    def test_pbs_hash_can_be_reconstructed(self):
        (name, block, data) = require_file('test/samples/LDIABL.PBS__uncompressed')
        data['checksum'] = None
        output = block.pack(data, name=name)
        with open('test/samples/LDIABL.PBS__uncompressed', 'rb') as bdata:
            original = bdata.read()
            self.assertEqual(len(original), len(output))
            for i, x in enumerate(original):
                self.assertEqual(x, output[i], f'Wrong value at index {i}')


class TestTnfs3doCarPhysics(unittest.TestCase):
    def test_round_trip(self):
        (name, block, data) = require_file('test/samples/LDIABLO.bigSpecsFam')
        self.assertEqual(block.__class__.__name__, 'Tnfs3doCarPhysics')
        self.assertEqual(data['mass'], 1753)
        self.assertEqual(data['max_brake_force'], 11.299987792968750)
        self.assertEqual(data['num_torques'], 51)
        self.assertEqual(data['rear_grip_mult'], 1.796875)
        self.assertEqual(len(data['grip_table_f']), 512)
        for key in ['mass', 'inv_mass', 'brake_bias_r', 'front_grip_mult_inv', 'rear_grip_mult_inv', 'items_descr']:
            data[key] = None
        with open('test/samples/LDIABLO.bigSpecsFam', 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))


class TestNfs2CarPhysics(unittest.TestCase):
    def test_viv_items_parse_and_round_trip(self):
        (name, block, res) = require_file('test/samples/CARDATA.VIV', lazy=False)
        physics = {
            child['alias']: (block.item_block.possible_blocks[child['item']['choice_index']], child['item']['data'])
            for child in res['children']
            if child['alias'].lower().startswith('p') and child['alias'].lower().endswith('.dat')
        }
        # every p<car>.DAT but the 3012-byte prsonal.dat
        self.assertEqual(35, len([x for x in physics.values() if x[0].__class__.__name__ == 'Nfs2CarPhysics']))
        car_block, car = physics['pcala.DAT']
        self.assertEqual(car_block.__class__.__name__, 'Nfs2CarPhysics')
        self.assertEqual(car['mass'], 1350.0)
        self.assertEqual(car['num_gears'], 8)
        self.assertEqual(car['engine_redline_rpm'], 7550)
        self.assertEqual(car['max_velocity'], 81.0)
        self.assertEqual(car['brake_increasing_curve'], [64, 32, 16, 8, 4, 2, 1, 1])
        self.assertEqual(car['turn_in_ramp'], 16)
        self.assertEqual(car['push_factor'], 9000)
        self.assertEqual(car['high_turn_factor'], 0x6A7 / 0x10000)
        with open('test/samples/CARDATA.VIV', 'rb') as f:
            original = f.read()
        offset = original.index(b'pcala.DAT') - 8
        start = int.from_bytes(original[offset : offset + 4], 'big')
        self.assertEqual(car_block.pack(car), original[start : start + 356])

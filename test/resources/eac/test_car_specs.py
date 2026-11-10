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
        self.assertEqual(car['torque_curve'][:3], [310.0, 310.0, 315.0])
        self.assertEqual(car['brake_increasing_curve'], [64, 32, 16, 8, 4, 2, 1, 1])
        self.assertEqual(car['turn_in_ramp'], 16)
        self.assertEqual(car['push_factor'], 9000)
        self.assertEqual(car['high_turn_factor'], 0x6A7 / 0x10000)
        with open('test/samples/CARDATA.VIV', 'rb') as f:
            original = f.read()
        offset = original.index(b'pcala.DAT') - 8
        start = int.from_bytes(original[offset : offset + 4], 'big')
        self.assertEqual(car_block.pack(car), original[start : start + 356])


class TestNfs2SimTune(unittest.TestCase):
    def test_viv_item_parses_and_round_trips(self):
        (name, block, res) = require_file('test/samples/CARDATA.VIV', lazy=False)
        child = next(x for x in res['children'] if x['alias'] == 'simtune.dat')
        tune_block = block.item_block.possible_blocks[child['item']['choice_index']]
        tune = child['item']['data']
        self.assertEqual(tune_block.__class__.__name__, 'Nfs2SimTune')
        self.assertEqual(tune['simulation']['telepole_launch_value'], 95.0)
        self.assertEqual(tune['simulation']['extra_flight_gravity'], 0.5)
        self.assertEqual(tune['simulation']['bad_collision_reset_ticks'], 700)
        self.assertEqual(tune['simulation']['bounce_threshold'], 0xB333 / 0x10000)
        self.assertEqual(tune['arcade']['telepole_launch_value'], 175.0)
        self.assertEqual(tune['arcade']['collision_reset_launch_speed'], 30.0)
        self.assertEqual(
            [(x['slice_distance'], x['speed_boost_multiplier']) for x in tune['arcade']['glue_logic']],
            [(5, 0x11333 / 0x10000), (10, 0x12666 / 0x10000), (30, 0x13333 / 0x10000), (60, 1.25)],
        )
        with open('test/samples/CARDATA.VIV', 'rb') as f:
            original = f.read()
        offset = original.index(b'simtune.dat') - 8
        start = int.from_bytes(original[offset : offset + 4], 'big')
        self.assertEqual(int.from_bytes(original[offset + 4 : offset + 8], 'big'), 232)
        self.assertEqual(tune_block.pack(tune), original[start : start + 232])


class TestNfs2CarAi(unittest.TestCase):
    def test_viv_items_parse_and_round_trip(self):
        (name, block, res) = require_file('test/samples/CARDATA.VIV', lazy=False)
        ai = [
            (child['alias'], block.item_block.possible_blocks[child['item']['choice_index']], child['item']['data'])
            for child in res['children']
            if block.item_block.possible_blocks[child['item']['choice_index']].__class__.__name__ == 'Nfs2CarAi'
        ]
        # 17 cars, each listed twice
        self.assertEqual(34, len(ai))
        self.assertEqual(17, len({alias for alias, _, _ in ai}))
        ai_block, cala = next((b, d) for alias, b, d in ai if alias == 'cala.dat')
        self.assertEqual(cala['ai_shift_duration'], 14)
        self.assertEqual(cala['redline'], 7500.0)
        self.assertEqual(len(cala['gear_top_speeds']), 7)
        self.assertEqual(cala['gear_top_speeds'][6], 0)
        self.assertEqual(len(cala['simulation']['acceleration_table']), 112)
        self.assertEqual(cala['simulation']['acceleration_table'][0], 872 / 256)
        self.assertEqual(cala['simulation']['grip'], 37.0)
        self.assertEqual(cala['arcade']['grip'], 60.0)
        self.assertEqual(cala['arcade']['turn_rate'], 0xCCCC / 0x10000)
        self.assertEqual(cala['hi_handling_yaw'], 10)
        self.assertEqual(cala['low_handling_yaw'], 3)
        self.assertEqual(cala['speed_factor_2'], 1.0)
        self.assertEqual(cala['lane_slack_prob'], 40)
        with open('test/samples/CARDATA.VIV', 'rb') as f:
            original = f.read()
        offset = original.index(b'cala.dat') - 8
        start = int.from_bytes(original[offset : offset + 4], 'big')
        self.assertEqual(int.from_bytes(original[offset + 4 : offset + 8], 'big'), 524)
        self.assertEqual(ai_block.pack(cala), original[start : start + 524])


def _viv_items(class_name):
    (name, block, res) = require_file('test/samples/CARDATA.VIV', lazy=False)
    return [
        (child['alias'], block.item_block.possible_blocks[child['item']['choice_index']], child['item']['data'])
        for child in res['children']
        if block.item_block.possible_blocks[child['item']['choice_index']].__class__.__name__ == class_name
    ]


def _viv_item_bytes(alias, size):
    with open('test/samples/CARDATA.VIV', 'rb') as f:
        original = f.read()
    offset = original.index(alias.encode() + b'\0') - 8
    start = int.from_bytes(original[offset : offset + 4], 'big')
    assert int.from_bytes(original[offset + 4 : offset + 8], 'big') == size
    return original[start : start + size]


class TestNfs2TrafficConfig(unittest.TestCase):
    def test_viv_items_parse_and_round_trip(self):
        items = _viv_items('Nfs2TrafficConfig')
        # trafcfg.dat and TRAFCFG.DAT, identical copies
        self.assertEqual({'trafcfg.dat', 'TRAFCFG.DAT'}, {alias for alias, _, _ in items})
        for alias, cfg_block, cfg in items:
            self.assertEqual(cfg['opp_desired_ahead'], 21.0)
            self.assertEqual(cfg['traffic_density'], 500)
            self.assertEqual(cfg['num_traffic_cars'], 4)
            self.assertEqual(cfg['traffic_speed_factors'][0], 1.0)
            self.assertEqual(cfg['traffic_base_speed'], 150.0)
            self.assertEqual(cfg['lane_slack'], [-1.5, 1.5, -0.5, 0.5])
            self.assertEqual(cfg['single_race_glue']['four_laps']['speed_glue'], 0xF851 / 0x10000)
            self.assertEqual(cfg['single_race_glue']['eight_laps']['speed_glue'], 0xF333 / 0x10000)
            self.assertEqual(cfg['knockout_glue']['multi_opponents']['acceleration_glue'], 1.0)
            self.assertEqual(cfg['latvelcalc_lookahead'], 4)
            self.assertEqual(cfg['simulation_look_ahead']['max_lookahead'], 6)
            self.assertEqual(cfg['arcade_look_ahead']['look_ahead_factor'], 1.5)
            self.assertEqual(cfg['skid_value'], 11.0)
            self.assertEqual(cfg['in_control']['max_dlvel'], 32.0)
            self.assertEqual(cfg['out_of_control']['dav_to_aa'], 10.0)
            self.assertEqual(cfg_block.pack(cfg), _viv_item_bytes(alias, 452))


class TestNfs2Personalities(unittest.TestCase):
    def test_viv_item_parses_and_round_trips(self):
        items = _viv_items('Nfs2Personalities')
        self.assertEqual(['prsonal.dat'], [alias for alias, _, _ in items])
        (alias, pers_block, pers) = items[0]
        self.assertEqual(pers['grid']['knockout'], 'abcdefghijkl')
        self.assertEqual(pers['grid']['single_race_one_opponent'], 'm' * 12)
        for letter in 'abcdefghijklm':
            self.assertEqual(pers[f'car_{letter}']['letter'], letter)
            self.assertEqual(len(pers[f'car_{letter}']['speed_glue']), 21)
        car_a = pers['car_a']
        self.assertEqual(car_a['speed_glue'][0], 183500 / 0x10000)
        self.assertEqual(car_a['speed_glue'][10], 1.0)
        self.assertEqual(car_a['acceleration_glue'][0], 9.0)
        self.assertEqual(car_a['block_look_behind'], 20)
        self.assertEqual(car_a['look_ahead'], 30)
        self.assertEqual(car_a['psycho_trigger_count'], 200)
        self.assertEqual(pers['car_c']['lane_slack'][1], 26214 / 0x10000)
        self.assertEqual(pers['car_g']['psycho_time'], 250)
        self.assertEqual(pers_block.pack(pers), _viv_item_bytes(alias, 3012))


class TestNfs5CarFiles(unittest.TestCase):
    def test_sim_should_read_physics_fields_and_write_back(self):
        import struct
        from io import BytesIO
        from library.loader import probe_block_class

        raw = bytearray(328)
        raw[:24] = b'1950 356 coupe 1.1L \x001950)'[:24]
        struct.pack_into('<ff', raw, 0x40, 830.0, 2100.0)
        struct.pack_into('<ii', raw, 0x50, 4, 8)
        struct.pack_into('<8f', raw, 0x60, -3.6, 0, 3.09, 1.765, 1.227, 0.96, 0, 0)
        struct.pack_into('<f', raw, 0x94, 5500.0)
        raw = bytes(raw)
        block_class = probe_block_class(BytesIO(raw), 'GameData/Simulation/CarData/356coupe11.sim', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs5CarPhysics')
        block = block_class()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(data['mass'], 830.0)
        self.assertEqual(data['forward_gears'], 4)
        self.assertEqual(data['shift_time'], 8)
        self.assertEqual(data['redline'], 5500.0)
        self.assertAlmostEqual(data['gear_ratios'][2], 3.09, places=5)
        self.assertEqual(block.pack(data), raw)

    def test_car_record_should_read_latin1_names(self):
        import struct
        from resources.eac.car_specs import Nfs5Cars

        raw = bytearray(0x670)
        struct.pack_into('<h', raw, 0, 77)
        raw[2 : 2 + 11] = "'50 Coupé A".encode('latin-1')
        raw[0xB1 : 0xB1 + 10] = b'356coupe11'
        struct.pack_into('<hhh', raw, 0x3BC, 2, 629, 42)
        raw = bytes(raw)
        block = Nfs5Cars()
        data = block.unpack_from_bytes(raw)
        car = data['cars'][0]
        self.assertEqual(car['id'], 77)
        self.assertEqual(car['display_name'], "'50 Coupé A")
        self.assertEqual(car['spec'], '356coupe11')
        self.assertEqual(car['stock_parts'][: car['num_stock_parts']], [629, 42])
        self.assertEqual(block.pack(data), raw)

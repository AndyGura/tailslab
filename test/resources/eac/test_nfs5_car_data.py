import os
import tempfile
import unittest
from io import BytesIO

from library.loader import probe_block_class
from resources.eac.car_specs import Nfs5CarAi, Nfs5CarParts, Nfs5CarPhysics, Nfs5Cars
from resources.eac.nfs5_ai import (
    Nfs5AiGlue,
    Nfs5AiPersonalityTraits,
    Nfs5AiRacingLine,
    Nfs5AiScripts,
    Nfs5TrafficConfig,
)
from resources.eac.nfs5_career import Nfs5FactoryMissions, Nfs5Personalities, Nfs5Tournaments
from serializers import CompleteJsonSerializer

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'nfs5')

# cut-down copies of the game files: two .sim, one .ais, 4 nfs5.car records (car, cop, traffic, 959), 16 nfs5.prt
# records (one per type and the stock parts of car 76), the whole nfs5.fac and nfs5.per, 2 nfs5.trn records; the AI
# files prsonal.bin, SCRIPTS.BIN, GLUE.BIN, TRAFCFG.DAT and the skid pad's forward racing line, whole
FILES = [
    ('993coupe36.sim', Nfs5CarPhysics),
    ('GT1race.sim', Nfs5CarPhysics),
    ('993.ais', Nfs5CarAi),
    ('nfs5.car', Nfs5Cars),
    ('nfs5.prt', Nfs5CarParts),
    ('nfs5.fac', Nfs5FactoryMissions),
    ('nfs5.trn', Nfs5Tournaments),
    ('nfs5.per', Nfs5Personalities),
]
AI_FILES = [
    ('GameData/Simulation/AI/prsonal.bin', Nfs5AiPersonalityTraits),
    ('GameData/Simulation/AI/SCRIPTS.BIN', Nfs5AiScripts),
    ('GameData/Simulation/AI/GLUE.BIN', Nfs5AiGlue),
    ('GameData/Simulation/AI/TRAFCFG.DAT', Nfs5TrafficConfig),
    ('GameData/Track/racer/work/skidpad0.lsp', Nfs5AiRacingLine),
]


def _read(name):
    with open(os.path.join(SAMPLES, name), 'rb') as f:
        return f.read()


class TestNfs5CarData(unittest.TestCase):
    def test_every_file_writes_back_byte_exact(self):
        for name, block_class in FILES + [(os.path.basename(path), c) for path, c in AI_FILES]:
            with self.subTest(name):
                raw = _read(name)
                block = block_class()
                self.assertEqual(block.pack(block.unpack_from_bytes(raw)), raw)

    def test_json_export_imports_back_byte_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, block_class in FILES + [(os.path.basename(path), c) for path, c in AI_FILES]:
                with self.subTest(name):
                    raw = _read(name)
                    block = block_class()
                    data = block.unpack_from_bytes(raw)
                    serializer = block.serializer_class()()
                    self.assertIsInstance(serializer, CompleteJsonSerializer)
                    self.assertTrue(serializer.ui_serialization()['reversible'])
                    out = serializer.serialize(data, os.path.join(tmp, name), id=name, block=block)
                    self.assertEqual(out, [os.path.join(tmp, name) + '.json'])
                    back = serializer.deserialize(out, id=name, block=block)
                    self.assertEqual(block.pack(back), raw)

    def test_loader_picks_the_front_end_files_by_name(self):
        for name, block_class in FILES[3:]:
            with self.subTest(name):
                raw = _read(name)
                found = probe_block_class(BytesIO(raw), f'FEData/Data/{name}', len(raw))
                self.assertIs(found, block_class)

    def test_loader_picks_the_ai_files_by_name_and_size(self):
        for path, block_class in AI_FILES:
            with self.subTest(path):
                raw = _read(os.path.basename(path))
                self.assertIs(probe_block_class(BytesIO(raw), path, len(raw)), block_class)
        # the NFS2 SE TRAFCFG.DAT is another size
        raw = _read('TRAFCFG.DAT') + bytes(4)
        with self.assertRaises(NotImplementedError):
            probe_block_class(BytesIO(raw), 'GameData/Simulation/AI/TRAFCFG.DAT', len(raw))

    def test_ai_fields(self):
        traits = Nfs5AiPersonalityTraits().unpack_from_bytes(_read('prsonal.bin'))
        self.assertEqual(len(traits['personalities']), 9)
        # prsonal.csv: Nemesis has an extreme cornering ability and a low wipe out frequency
        self.assertEqual(traits['personalities'][0]['cornering_ability'], 3)
        self.assertEqual(traits['personalities'][0]['wipe_out_frequency'], 0)
        scripts = Nfs5AiScripts().unpack_from_bytes(_read('SCRIPTS.BIN'))
        # SCRIPTS.CSV, Nemesis: Collision HONK_HORN 2, END; Opp wizzed by PAUSE 2, SWIPE 2, END
        self.assertEqual(scripts['personalities'][0]['collision']['steps'][0], {'reaction': 3, 'time': 2})
        self.assertEqual([s['reaction'] for s in scripts['personalities'][0]['opp_wizzed_by']['steps']], [7, 5, 1, 1])
        glue = Nfs5AiGlue().unpack_from_bytes(_read('GLUE.BIN'))
        self.assertEqual((glue['factors'][0], glue['factors'][10]), (1.25, 1.0))
        config = Nfs5TrafficConfig().unpack_from_bytes(_read('TRAFCFG.DAT'))
        self.assertEqual((config['min_lookahead'], config['max_lookahead']), (12, 30))
        # max_dav 52428 and ang_vel_limit_factor 851 read as x 1/1024
        self.assertAlmostEqual(config['in_control']['max_dav'], 51.2, places=2)
        self.assertAlmostEqual(config['out_of_control']['ang_vel_limit_factor'], 0.831, places=3)
        line = Nfs5AiRacingLine().unpack_from_bytes(_read('skidpad0.lsp'))
        # one point per slice of skidpad.crp
        self.assertEqual((line['header'], len(line['points'])), (1, 234))

    def test_sim_fields(self):
        d = Nfs5CarPhysics().unpack_from_bytes(_read('GT1race.sim'))
        self.assertEqual(d['engine_position'], 1)
        self.assertEqual(d['aspiration'], 1)
        self.assertAlmostEqual(d['ai_steer_lookahead'], 0.8, places=5)
        self.assertEqual(d['ai_speed_slot_scale'], 1.0)
        self.assertEqual(d['torque_curve'][12], 527.0)

    def test_ais_fields(self):
        d = Nfs5CarAi().unpack_from_bytes(_read('993.ais'))
        self.assertEqual(len(d['lookahead_slices']), 24)
        self.assertEqual(d['lookahead_slices'], sorted(d['lookahead_slices']))
        self.assertEqual(d['speeds'], sorted(d['speeds'], reverse=True))
        self.assertEqual(d['unused'], [0.0] * 4)

    def test_car_record_fields(self):
        cars = Nfs5Cars().unpack_from_bytes(_read('nfs5.car'))['cars']
        car, cop, traffic, c959 = cars
        self.assertEqual(car['id'], 76)
        self.assertEqual(car['body_text'], 'Cabrio')
        self.assertEqual(car['convertible'], 1)
        self.assertEqual((car['class_string_id'], car['era_string_id']), (501, 521))
        self.assertEqual((car['first_year'], car['last_year'], car['price']), (1950, 1954, 11000))
        self.assertEqual(car['num_paints'], 19)
        # stored ff f3 ff cc: 0xAARRGGBB
        self.assertEqual(car['paints'][0]['body'], 0xFFF3FFCC)
        self.assertEqual(car['tachometer']['total_units'], 600)
        self.assertEqual(cop['kind'], 2)
        self.assertEqual(traffic['kind'], 1)
        self.assertEqual(c959['availability'], 2)
        self.assertEqual(c959['abs_available'], 1)

    def test_part_fields(self):
        parts = Nfs5CarParts().unpack_from_bytes(_read('nfs5.prt'))['parts']
        brakes = next(p for p in parts if p['type'] == 2)
        self.assertGreaterEqual(brakes['name_string_id'], 5000)
        self.assertGreater(brakes['sort_key'], 0)
        self.assertGreater(brakes['durability'], 0)
        self.assertEqual(len(brakes['zones']), 10)

    def test_career_fields(self):
        missions = Nfs5FactoryMissions().unpack_from_bytes(_read('nfs5.fac'))['missions']
        self.assertEqual(len(missions), 34)
        self.assertEqual((missions[0]['level'], missions[0]['car_id']), (1, 161))
        self.assertEqual(missions[0]['map_picture'], '0M01')
        tournaments = Nfs5Tournaments().unpack_from_bytes(_read('nfs5.trn'))['tournaments']
        first = tournaments[0]
        self.assertEqual((first['id'], first['era'], first['race_count']), (1, 521, 2))
        self.assertEqual(first['prize_money'][0], 5000)
        self.assertEqual(first['opponents'][0]['car_id'], 76)
        personalities = Nfs5Personalities().unpack_from_bytes(_read('nfs5.per'))['personalities']
        self.assertEqual(len(personalities), 35)
        self.assertAlmostEqual(personalities[0]['skill_slow'], 0.6, places=5)

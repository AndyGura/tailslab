import glob
import json
import os
import tempfile
import unittest

from library.loader import probe_block_class
from resources.eac.ini import IniFile, format_ini_float, parse_ini
from resources.eac.nfs6_car_specs import (
    NFS6_CAR_INI_FILES,
    Nfs6CarIni,
    Nfs6EngineAudioTable,
    Nfs6VehicleIni,
    nfs6_car_ini_class,
)
from serializers import get_serializer

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'nfs6_cars', 'Cars')


def _read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    with open(path, 'rb') as f:
        block = probe_block_class(f, path, len(raw))()
    return raw, block, block.unpack_from_bytes(raw)


class TestIniParser(unittest.TestCase):
    def test_cini_rules(self):
        text = parse_ini(
            b" [skipped]\r\na=1\r\n[s]\r\n  Key = 5 \r\nkey=6\r\nKey=7\r\n' c=d\r\nnoequals\r\n[]\r\nx=1\r\n[s]\r\nKey=9\r\n"
        )
        # the first line counts only when its first byte is '['; an empty name is skipped with its keys
        self.assertEqual([s.name for s in text.sections], ['s', 's'])
        section = text.section('S')
        # a repeated spelling replaces the value, lookups ignore case and find the first key
        key = section.lookup('KEY')
        self.assertEqual(key.name, 'Key')
        self.assertEqual(len(key.lines), 2)
        self.assertEqual(text.raw[key.line.value_start : key.line.end], b'7')
        self.assertEqual([k.name for k in section.keys], ['Key', 'key', "' c"])

    def test_float_style(self):
        self.assertEqual(format_ini_float(2.5, '1.00'), '2.50')
        self.assertEqual(format_ini_float(3.0, '8'), '3')
        self.assertEqual(format_ini_float(0.35), '0.35')


class TestNfs6CarSpecs(unittest.TestCase):
    def test_detection(self):
        self.assertIs(nfs6_car_ini_class('x/Cars/911t/car.ini'), Nfs6CarIni)
        self.assertIs(nfs6_car_ini_class('x/Cars/911t/VEHICLE.INI'), Nfs6VehicleIni)
        self.assertIsNone(nfs6_car_ini_class('Data/Tracks/Snowy/car.ini'))
        self.assertIsNone(nfs6_car_ini_class('x/Cars/car.ini'))
        self.assertIsNone(nfs6_car_ini_class('Data/Tracks/Snowy/Tr.ini'))

    def test_round_trip(self):
        paths = glob.glob(os.path.join(SAMPLES, '**', '*.ini'), recursive=True)
        self.assertEqual({os.path.basename(p).lower() for p in paths}, set(NFS6_CAR_INI_FILES))
        for path in paths:
            raw, block, data = _read(path)
            self.assertIsInstance(block, IniFile)
            self.assertEqual(block.pack(data), raw, path)

    def test_values(self):
        _, _, data = _read(os.path.join(SAMPLES, '911t', 'car.ini'))
        self.assertEqual(data['basic']['Mass'], 1439.0)
        self.assertEqual(data['basic']['driveWheels'], [1, 1, 1, 1])
        self.assertEqual(data['engineblock']['torqueCurve'][5], 520.0)
        self.assertIsNone(data['engineblock']['torqueCurve'][24])
        self.assertEqual(data['engineblock']['dbAudio'][1], 'snx')
        self.assertEqual(data['transmission']['GearRatios'][2], 3.82)
        self.assertEqual(data['tire_front']['attach'], 10)
        self.assertEqual(data['basic']['other_keys'], [])
        # m5: UnderBodyDragCoefficient twice, the later line wins
        _, _, m5 = _read(os.path.join(SAMPLES, 'm5', 'car.ini'))
        self.assertEqual(m5['basic']['UnderBodyDragCoefficient'], 8.0)
        # cl55amg: a second [damage] section, not read by the game
        _, _, cl = _read(os.path.join(SAMPLES, 'cl55amg', 'vehicle.ini'))
        self.assertEqual([s['section'] for s in cl['other_sections']], ['damage'])
        self.assertEqual(cl['damage']['bouncetrunk'], 10.0)
        self.assertEqual(cl['skins'][0]['section'], 'skin00')
        self.assertEqual(cl['skins'][0]['other_keys'], [])

    def test_edit(self):
        raw, block, data = _read(os.path.join(SAMPLES, '911t', 'car.ini'))
        data['basic']['Mass'] = 1500.25
        data['engineblock']['torqueCurve'][24] = 10.0
        data['basic']['other_keys'].append({'key': 'Extra', 'value': 'abc'})
        data['audio']['enginetype'] = None
        out = block.pack(data)
        text = out.decode('latin-1')
        self.assertIn('Mass=1500.25\r\n', text)
        self.assertIn('torqueCurve_23=0.0\r\ntorqueCurve_24=10.0\r\n', text)
        self.assertNotIn('enginetype', text)
        again = block.unpack_from_bytes(out)
        self.assertEqual(again['basic']['Mass'], 1500.25)
        self.assertEqual(again['basic']['other_keys'], [{'key': 'Extra', 'value': 'abc'}])
        self.assertIsNone(again['audio']['enginetype'])
        # only the edited lines changed
        self.assertEqual(len(out.splitlines()), len(raw.splitlines()) + 1)

    def test_groups(self):
        raw, block, data = _read(os.path.join(SAMPLES, '911t', 'vehicle.ini'))
        self.assertEqual(len(data['skins']), 12)
        data['skins'].append({**block.get_child_block('skins').child.new_data(), 'specular_red': 1})
        data['light_glows'].pop()
        out = block.pack(data)
        again = block.unpack_from_bytes(out)
        self.assertEqual(again['skins'][-1]['section'], 'skin12')
        self.assertEqual(again['skins'][-1]['specular_red'], 1)
        self.assertEqual(len(again['light_glows']), len(data['light_glows']))

    def test_json(self):
        for path in glob.glob(os.path.join(SAMPLES, '**', '*.ini'), recursive=True):
            raw, block, data = _read(path)
            serializer = get_serializer(block, data)
            with tempfile.TemporaryDirectory() as tmp:
                files = serializer.serialize(data, os.path.join(tmp, 'out'), id='x/out', block=block)
                with open(files[0]) as f:
                    exported = json.load(f)
                self.assertNotIn('source_text', exported)
                # a new file from the JSON alone: the same values
                new_data = serializer.deserialize(files, block=block)
                written = block.pack(new_data)
                self.assertEqual(block.unpack_from_bytes(written)['other_sections'], data['other_sections'])
                for name, _ in block.sections_and_groups():
                    self.assertEqual(block.unpack_from_bytes(written)[name], data[name], (path, name))

    def test_engine_audio_tables(self):
        raw, block, data = _read(os.path.join(SAMPLES, 'cartable.viv'))
        self.assertEqual(block.pack(data), raw)
        tables = {c['alias']: c['item']['data'] for c in data['children']}
        ctb = tables['engine.ctb']
        self.assertEqual(ctb['slots'], [6, 7, 8, -1, 9, 10, 11, -1])
        self.assertEqual(len(ctb['tables']), 12)
        self.assertEqual(Nfs6EngineAudioTable.table_index('pitch_table_offsets', 1, ctb['pitch_table_offsets'][1]), 3)
        table_block = Nfs6EngineAudioTable()
        serializer = get_serializer(table_block, ctb)
        with tempfile.TemporaryDirectory() as tmp:
            files = serializer.serialize(ctb, os.path.join(tmp, 'engine.ctb'), id='x/engine.ctb', block=table_block)
            back = serializer.deserialize(files, block=table_block)
        self.assertEqual(table_block.pack(back), table_block.pack(ctb))


if __name__ == '__main__':
    unittest.main()

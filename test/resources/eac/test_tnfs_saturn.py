import json
import os
import struct
import tempfile
import unittest
import wave
from io import BytesIO

from PIL import Image

from library import require_file
from library.loader import probe_block_class
from resources.common.audios import SaturnToneBank
from resources.common.audios.saturn_tone_bank import saturn_tone_layer_sample_rate, saturn_tone_layer_samples
from resources.common.bitmaps import PcxImage
from resources.eac.car_specs import CarAiAndCrashBody, PlayerCarPhysics
from resources.eac.fields.byte_order import big_endian_copy
from resources.eac.geometries import TnfsSaturnOrixGeometry
from resources.eac.tnfs_saturn import (
    TNFS_SATURN_GTR_CAR_AI_OFFSET,
    TNFS_SATURN_GTR_CAR_AI_POINTERS_OFFSET,
    TNFS_SATURN_GTR_LOAD_ADDRESS,
    TnfsSaturnCarAiAndCrashBody,
    TnfsSaturnCarBundle,
    TnfsSaturnPcxList,
    is_tnfs_saturn_gtr_executable,
    tnfs_saturn_gtr_car_ai_records,
    tnfs_saturn_rle_pixels,
    tnfs_saturn_texture_image,
    tnfs_saturn_texture_name,
)
from serializers.audios import SaturnToneBankSerializer, saturn_tone_stereo_pair
from serializers.geometries import TnfsSaturnOrixGeometrySerializer, tnfs_wheel_labels_by_position
from serializers.tnfs_saturn import export_tnfs_saturn_texture_bank, tnfs_saturn_texture_file_name

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'tnfs_saturn_gtr')
BUNDLE = os.path.join(SAMPLES, 'CARS', 'VIPER.ALL')
HIGH_POLY = os.path.join(SAMPLES, 'MODELS', 'VIPER', 'high.orix')
OPPONENT_BANK = os.path.join(SAMPLES, 'SOUNDS', 'OPPVIPER.BIN')


def _read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


def _probe(path):
    with open(path, 'rb') as f:
        return probe_block_class(f, path, os.path.getsize(path))


class TestBigEndianCopy(unittest.TestCase):
    def test_integers_become_big_endian(self):
        block = big_endian_copy(PlayerCarPhysics.Fields.mass_front[0])
        self.assertEqual(block.byte_order, 'big')
        self.assertEqual(PlayerCarPhysics.Fields.mass_front[0].byte_order, 'little')


class TestTnfsSaturnCarBundle(unittest.TestCase):
    def test_detected_and_written_back(self):
        self.assertIs(_probe(BUNDLE), TnfsSaturnCarBundle)
        name, block, data = require_file(BUNDLE, lazy=False)
        self.assertEqual(block.pack(data), _read_bytes(BUNDLE))

    def test_physics_big_endian_pbs(self):
        name, block, data = require_file(BUNDLE, lazy=False)
        physics = data['physics']
        self.assertEqual(physics['mass'], 1430.0)
        self.assertAlmostEqual(physics['body_len'], 4.525, places=3)
        raw = _read_bytes(BUNDLE)
        self.assertEqual(physics['checksum'], sum(raw[:1880]))
        self.assertEqual(int.from_bytes(raw[1908:1912], 'big'), physics['checksum'])

    def test_texture_banks(self):
        name, block, data = require_file(BUNDLE, lazy=False)
        bank = data['textures']
        names = [tnfs_saturn_texture_name(x) for x in bank['textures']]
        self.assertEqual(names[:6], ['J032', 'null', 'Tir1', 'Tir2', 'Tir3', 'Tir4'])
        self.assertEqual(len(bank['colors']), 16 * len(names))
        self.assertEqual(len(data['low_poly_textures']['textures']), 7)
        tyre = tnfs_saturn_texture_image(bank, names.index('Tir1'))
        self.assertEqual(tyre.size, (24, 24))
        # draw mode without SPD: colour index 0 (the magenta key colour) is transparent
        self.assertEqual(tyre.convert('RGBA').getpixel((0, 0)), (255, 0, 255, 0))
        lights = tnfs_saturn_texture_image(bank, 0).convert('RGBA')
        self.assertEqual(lights.getpixel((0, 0))[3], 255)

    def test_texture_export_names_and_car_colors(self):
        self.assertEqual(tnfs_saturn_texture_file_name('Tir1'), 'tyr1')
        self.assertEqual(tnfs_saturn_texture_file_name('Tyr4'), 'tyr4')
        self.assertEqual(tnfs_saturn_texture_file_name('J000'), 'J000')
        name, block, data = require_file(BUNDLE, lazy=False)
        with tempfile.TemporaryDirectory() as tmp:
            files = export_tnfs_saturn_texture_bank(data['textures'], tmp)
            self.assertIn(os.path.join(tmp, 'tyr1.png').replace('\\', '/'), [f.replace('\\', '/') for f in files])
            with open(os.path.join(tmp, 'car_colors.json')) as f:
                colors = json.load(f)
        self.assertEqual(
            colors,
            {'tail_lights': {'texture_color': '#00ff00', 'textures': ['J032'], 'off': '#420000', 'on': '#ff0000'}},
        )

    def test_cockpit(self):
        name, block, data = require_file(BUNDLE, lazy=False)
        cockpit = data['cockpit']
        self.assertEqual((cockpit['dashboard']['width'], cockpit['dashboard']['height']), (352, 240))
        self.assertEqual((cockpit['steering_wheel']['width'], cockpit['steering_wheel']['height']), (176, 176))
        # the wheel's size field counts itself: it ends the file
        self.assertEqual(cockpit['steering_wheel_size'], 520 + len(cockpit['steering_wheel']['data']))
        self.assertEqual(len(tnfs_saturn_rle_pixels(cockpit['dashboard'])), 352 * 240)


class TestTnfsSaturnOrixGeometry(unittest.TestCase):
    def test_detected_and_written_back(self):
        for lod in ('high', 'low'):
            path = os.path.join(SAMPLES, 'MODELS', 'VIPER', f'{lod}.orix')
            self.assertIs(_probe(path), TnfsSaturnOrixGeometry)
            name, block, data = require_file(path, lazy=False)
            self.assertEqual(block.pack(data), _read_bytes(path))

    def test_fields(self):
        name, block, data = require_file(HIGH_POLY, lazy=False)
        self.assertEqual(data['version'], 800)
        self.assertEqual(data['name'].rstrip('\0'), '_KBNR32B')
        self.assertEqual({x['draw_type'] for x in data['polygons']}, {12})
        self.assertEqual({x['polygon_type'] for x in data['polygons']}, {0x84, 0x8C})
        self.assertEqual(data['polygon_textures'][0], {'polygon_index': 0, 'file_name': 'J000'})
        shape = data['vertices']['data'][: data['num_shape_vrtx']]
        self.assertAlmostEqual(max(v['z'] for v in shape) - min(v['z'] for v in shape), 584 / 128)
        self.assertEqual([x['name'] for x in data['partitions']], ['NON-SORT', 'inside', 'surface', 'outside'])
        self.assertEqual(sorted(x['name'] for x in data['morphs']), ['left_tur', 'right_tu'])
        self.assertEqual(data['materials'][8]['name'], b'frntires')

    def test_wheel_labels_by_position(self):
        name, block, data = require_file(HIGH_POLY, lazy=False)
        same, renamed = tnfs_wheel_labels_by_position(data)
        self.assertIs(same, data)
        self.assertEqual(renamed, [])
        # the PGC10's fault: its left front wheel labelled rt_frnt
        broken = {**data, 'labels': [dict(x) for x in data['labels']]}
        label = next(x for x in broken['labels'] if x['name'] == 'lt_frnt')
        label['name'] = 'rt_frnt'
        fixed, renamed = tnfs_wheel_labels_by_position(broken)
        self.assertEqual(renamed, [(label['index'], 'rt_frnt', 'lt_frnt')])
        self.assertEqual(
            sorted(x['name'] for x in fixed['labels'] if x['name'].endswith(('frnt', 'rear'))),
            ['lt_frnt', 'lt_rear', 'rt_frnt', 'rt_rear'],
        )

    def test_meshes_as_pc_models(self):
        name, block, data = require_file(HIGH_POLY, lazy=False)
        serializer = TnfsSaturnOrixGeometrySerializer()
        _, _, _, sub_models = serializer.build_mesh(data, name)
        names = set(sub_models)
        for wheel in ('lbl__lt_frnt__tyr4', 'lbl__rt_frnt__tyr4', 'lbl__lt_rear__tyr4', 'lbl__rt_rear__tyr4'):
            self.assertIn(wheel, names)
        self.assertEqual(set(sub_models['lbl__lt_frnt__tyr4'].morph_targets), {'left_turn'})
        self.assertEqual(serializer.mesh_partitions['lbl__lt_frnt__tyr4'], 'outside')
        self.assertIn('lbl__bkll__J032', names)


class TestTnfsSaturnCarAi(unittest.TestCase):
    def test_pc_units(self):
        pc_block = CarAiAndCrashBody()
        pc = pc_block.new_data()
        pc['top_speeds'] = [0, 54 * 29124 / 65536, 0, 0, 0, 192 * 29124 / 65536]
        pc['gear_count'] = 5
        pc['handling_factor'] = 0xFF0000
        saturn = {**pc, 'top_speeds': [0, 54.0, 0, 0, 0, 192.0], 'gear_count': 5.0}
        saturn_block = TnfsSaturnCarAiAndCrashBody()
        raw = saturn_block.pack(saturn)
        self.assertEqual(len(raw), 460)
        self.assertEqual(struct.unpack('>i', raw[108 * 4 : 109 * 4])[0], 54 * 65536)
        self.assertEqual(struct.unpack('>i', raw[114 * 4 :])[0], 5 * 65536)
        converted = TnfsSaturnCarAiAndCrashBody.pc_data(saturn_block.unpack_from_bytes(raw))
        self.assertEqual(pc_block.pack(converted), pc_block.pack(pc))

    def test_records_by_pointer_table(self):
        records = [{} for _ in range(9)]
        first = TNFS_SATURN_GTR_LOAD_ADDRESS + TNFS_SATURN_GTR_CAR_AI_OFFSET
        indices = [7] * 13 + [7, 4, 2, 6, 3, 5, 1, 8, 0, 0]
        pointers = [first + 460 * i for i in indices]
        result = tnfs_saturn_gtr_car_ai_records({'car_ai_records': records, 'car_ai_pointers': pointers})
        self.assertEqual(
            result,
            {
                'SUPRA': 7,
                'DIABLO': 4,
                'PORSCHE': 2,
                'VETTE': 6,
                'TESTA': 3,
                'VIPER': 5,
                'NSX': 1,
                'RX7': 8,
                'WARRIOR': 0,
            },
        )
        head = bytearray(TNFS_SATURN_GTR_CAR_AI_POINTERS_OFFSET) + b''.join(p.to_bytes(4, 'big') for p in pointers)
        self.assertTrue(is_tnfs_saturn_gtr_executable(bytes(head)))
        head[-4:] = (first + 1).to_bytes(4, 'big')
        self.assertFalse(is_tnfs_saturn_gtr_executable(bytes(head)))


class TestSaturnToneBank(unittest.TestCase):
    def test_detected_and_written_back(self):
        self.assertIs(_probe(OPPONENT_BANK), SaturnToneBank)
        name, block, data = require_file(OPPONENT_BANK, lazy=False)
        self.assertEqual(block.pack(data), _read_bytes(OPPONENT_BANK))

    def test_layers(self):
        name, block, data = require_file(OPPONENT_BANK, lazy=False)
        voice = data['voices'][0]
        self.assertEqual(voice['mode']['bend_range'], 12)
        horn, engine = voice['layers']
        self.assertEqual((horn['start_note'], engine['start_note']), (40, 41))
        self.assertFalse(horn['sample_control']['pcm_8bit'])
        self.assertTrue(engine['sample_control']['pcm_8bit'])
        self.assertEqual(engine['sample_control']['loop_control'], 'normal_loop')
        self.assertEqual(horn['base_note'], 60)
        self.assertAlmostEqual(saturn_tone_layer_sample_rate(horn), 44100 * 2 ** (-20 / 12))
        self.assertEqual(len(saturn_tone_layer_samples(data, engine)), engine['loop_end'] + 1)
        self.assertFalse(saturn_tone_stereo_pair(voice['layers']))

    def test_export(self):
        name, block, data = require_file(OPPONENT_BANK, lazy=False)
        with tempfile.TemporaryDirectory() as tmp:
            SaturnToneBankSerializer().serialize(data, tmp, id=name, block=block)
            self.assertEqual(
                sorted(os.listdir(tmp)), ['engine_on.meta.json', 'engine_on.wav', 'honk.meta.json', 'honk.wav']
            )
            with wave.open(os.path.join(tmp, 'engine_on.wav')) as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, 14717))
            with open(os.path.join(tmp, 'honk.meta.json')) as f:
                meta = json.load(f)
        self.assertEqual(meta['loop'], True)
        self.assertEqual(meta['bend_range_semitones'], 12)
        self.assertAlmostEqual(meta['loop_start_time_ms'], 1000 * 1192 / 13891)


class TestTnfsSaturnPcx(unittest.TestCase):
    @staticmethod
    def _pcx(color) -> bytes:
        image = Image.new('P', (8, 4), 0)
        image.putpalette(list(color) * 256)
        buffer = BytesIO()
        image.save(buffer, format='PCX')
        return buffer.getvalue()

    def test_list(self):
        pictures = [self._pcx((255, 0, 0)), self._pcx((0, 0, 255))]
        raw = b''.join(len(x).to_bytes(4, 'big') + x for x in pictures)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'VIPGEN.DAT')
            with open(path, 'wb') as f:
                f.write(raw)
            self.assertIs(_probe(path), TnfsSaturnPcxList)
            pcx_path = os.path.join(tmp, 'MAIN.PCX')
            with open(pcx_path, 'wb') as f:
                f.write(pictures[0])
            self.assertIs(_probe(pcx_path), PcxImage)
        block = TnfsSaturnPcxList()
        data = block.unpack_from_bytes(raw)
        self.assertEqual([x['pcx'] for x in data['pictures']], pictures)
        self.assertEqual(block.pack(data), raw)

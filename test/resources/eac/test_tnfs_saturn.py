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
    TNFS_SATURN_FONT_PALETTE,
    TNFS_SATURN_FRONTEND_PCX_PALETTES,
    TNFS_SATURN_GTR_CAR_AI_OFFSET,
    TNFS_SATURN_GTR_CAR_AI_POINTERS_OFFSET,
    TNFS_SATURN_GTR_COCKPIT_RECORDS_OFFSET,
    TNFS_SATURN_GTR_EXECUTABLE_LENGTH,
    TNFS_SATURN_GTR_LOAD_ADDRESS,
    TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET,
    TNFS_SATURN_SCREEN_PALETTE,
    TnfsSaturnCarAiAndCrashBody,
    TnfsSaturnCarBundle,
    TnfsSaturnFrontendArt,
    TnfsSaturnGtrExecutable,
    TnfsSaturnPcxList,
    TnfsSaturnRlePicture,
    TnfsSaturnSizedRleImage,
    TnfsSaturnSizedRleImageList,
    TnfsSaturnSpriteBanks,
    is_tnfs_saturn_gtr_executable,
    is_tnfs_saturn_rle_picture,
    is_tnfs_saturn_sized_rle_image,
    saturn_color_to_rgba,
    tnfs_saturn_gtr_car_ai_records,
    tnfs_saturn_palette_colors,
    tnfs_saturn_rle_end,
    tnfs_saturn_rle_picture_image,
    tnfs_saturn_rle_pixels,
    tnfs_saturn_sprite_image,
    tnfs_saturn_sprite_pixels,
    tnfs_saturn_texture_image,
    tnfs_saturn_texture_name,
)
from serializers.audios import SaturnToneBankSerializer, saturn_tone_stereo_pair
from serializers.geometries import TnfsSaturnOrixGeometrySerializer, tnfs_wheel_labels_by_position
from serializers.tnfs_saturn import (
    TnfsSaturnFrontendArtSerializer,
    TnfsSaturnRlePictureSerializer,
    TnfsSaturnSizedRleImageListSerializer,
    TnfsSaturnSizedRleImageSerializer,
    TnfsSaturnSpriteBanksSerializer,
    export_tnfs_saturn_texture_bank,
    tnfs_saturn_bank_textures,
    tnfs_saturn_texture_file_name,
)

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


def _rgba(color):
    rgba = saturn_color_to_rgba(color)
    return (rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF, (rgba >> 8) & 0xFF, 0xFF


class TestTnfsSaturnTextureBankCarColors(unittest.TestCase):
    @staticmethod
    def _bank(draw_mode):
        # one 8x2 texture, colour 0 pure green (the brake light marker colour), pixels of colours 0 and 1
        return {
            'textures': [
                {
                    'name_start': 'J0',
                    'width_8': 1,
                    'height': 2,
                    'draw_mode': draw_mode,
                    'pixel_offset': 0,
                    'name_end': '00',
                }
            ],
            'pixels': bytes([0x01] * 8),
            'colors': [0x83E0, 0x801F] + [0x8000] * 14,
        }

    def test_key_colour_of_a_cut_out_texture_is_no_brake_light(self):
        # drawn (0x10C8): colour 0 is the marker; cut-out (0x1088): colour 0 is a key colour, not drawn
        self.assertEqual(tnfs_saturn_bank_textures(self._bank(0x10C8))['J000'][2], {0, 1})
        self.assertEqual(tnfs_saturn_bank_textures(self._bank(0x1088))['J000'][2], {1})
        with tempfile.TemporaryDirectory() as tmp:
            export_tnfs_saturn_texture_bank(self._bank(0x10C8), os.path.join(tmp, 'drawn'))
            export_tnfs_saturn_texture_bank(self._bank(0x1088), os.path.join(tmp, 'cut_out'))
            self.assertTrue(os.path.isfile(os.path.join(tmp, 'drawn', 'car_colors.json')))
            self.assertFalse(os.path.isfile(os.path.join(tmp, 'cut_out', 'car_colors.json')))


def _sprite_entry(width, height, draw_mode, pixel_offset, palette, flags=0x8000):
    return struct.pack('>6H', flags, width, height, draw_mode, pixel_offset, palette)


def _sprite_bank(entries, pixels):
    return struct.pack('>I', len(entries)) + b''.join(entries) + struct.pack('>I', len(pixels)) + pixels


# palette p of the synthetic palette table: colour i = (p * 7 + i) & 0x7FFF
def _palette_color(p, i):
    return (p * 7 + i) & 0x7FFF


def _palette_table(palettes=276, extra=16):
    colors = [_palette_color(p, i) for p in range(palettes) for i in range(256)]
    colors += [_palette_color(palettes, i) for i in range(extra)]
    return struct.pack('>I', len(colors)) + struct.pack(f'>{len(colors)}H', *colors)


def _pcx(width, height, value):
    image = Image.new('L', (width, height), value)
    image.putpixel((0, 0), 0)
    buffer = BytesIO()
    image.save(buffer, format='PCX')
    return buffer.getvalue()


# bank: an 8x2 8-bit sprite of palette 3 (pixels 0..15) and an 8x2 4-bit sprite without a palette sharing them
SPRITES = _sprite_bank(
    [_sprite_entry(1, 2, 0x10A0, 0, 3), _sprite_entry(1, 2, 0x1080, 0, 0xFFFF)],
    bytes(range(16)),
)
# font: a glyph 5 pixels wide, 3 high: rows of 8 pixels, 4 rows stored (the height rounded up to even)
FONT = _sprite_bank([_sprite_entry(5, 3, 0x1080, 0, 0)], bytes([0x12, 0x34, 0x56, 0x78] * 4))


def _frontend_art():
    pictures = b''.join(len(x).to_bytes(4, 'big') + x for x in [_pcx(8, 4, 5 + i) for i in range(19)])
    return SPRITES * 4 + pictures + _palette_table() + FONT + SPRITES


def _rle_picture(colors, runs):
    """`runs`: (literal, count) pairs over `colors` in order"""
    out = bytearray(struct.pack('>HHI', 0x0408, 0, 2 * len(colors)))
    pos = 0
    for literal, count in runs:
        if literal:
            out += struct.pack('>h', -count) + struct.pack(f'>{count}H', *colors[pos : pos + count])
        else:
            out += struct.pack('>hH', count - 2, colors[pos])
        pos += count
    assert pos == len(colors)
    return bytes(out)


class TestTnfsSaturnMenuArt(unittest.TestCase):
    def _write(self, folder, name, raw):
        path = os.path.join(folder, name)
        with open(path, 'wb') as f:
            f.write(raw)
        return path

    def test_detected_and_written_back(self):
        frontend, showcase = _frontend_art(), SPRITES * 3
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIs(_probe(self._write(tmp, 'FRONTEND.DAT', frontend)), TnfsSaturnFrontendArt)
            self.assertIs(_probe(self._write(tmp, 'SHOWCASE.DAT', showcase)), TnfsSaturnSpriteBanks)
        for block, raw in ((TnfsSaturnFrontendArt(), frontend), (TnfsSaturnSpriteBanks(), showcase)):
            self.assertEqual(block.pack(block.unpack_from_bytes(raw)), raw)

    def test_palette_table(self):
        data = TnfsSaturnFrontendArt().unpack_from_bytes(_frontend_art())
        table = data['palettes']
        self.assertEqual((len(table['palettes']), len(table['extra_colors'])), (276, 16))
        self.assertEqual(tnfs_saturn_palette_colors(table, 60)[5], _palette_color(60, 5))
        self.assertEqual(tnfs_saturn_palette_colors(table, 276), [_palette_color(276, i) for i in range(16)])
        self.assertEqual(data['font']['glyphs'][0]['width'], 5)
        self.assertEqual(len(data['pictures']), 19)

    def test_sprites(self):
        bank = TnfsSaturnSpriteBanks().unpack_from_bytes(SPRITES)['sprite_banks'][0]
        colors = [_palette_color(3, i) for i in range(256)]
        image = tnfs_saturn_sprite_image(bank, 0, colors)
        self.assertEqual(image.size, (8, 2))
        # 8 bits: one byte per pixel, colour 0 transparent (no SPD)
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        self.assertEqual(image.getpixel((5, 1)), _rgba(_palette_color(3, 13)))
        # 4 bits, the high nibble first: byte 1 = pixels 0 and 1, the first 16 colours of the palette
        width, height, indices = tnfs_saturn_sprite_pixels(bank, 1)
        self.assertEqual((width, height), (8, 2))
        self.assertEqual(indices[:4], [0, 0, 0, 1])
        self.assertEqual(tnfs_saturn_sprite_image(bank, 1, colors).getpixel((3, 0)), _rgba(_palette_color(3, 1)))

    def test_font_glyph(self):
        font = TnfsSaturnFrontendArt().unpack_from_bytes(_frontend_art())['font']
        width, height, indices = tnfs_saturn_sprite_pixels(font, 0)
        self.assertEqual((width, height), (5, 3))
        # rows of 8 pixels cut to 5
        self.assertEqual(indices[:5], [1, 2, 3, 4, 5])
        self.assertEqual(indices[5:10], [1, 2, 3, 4, 5])

    def test_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend_path = self._write(tmp, 'FRONTEND.DAT', _frontend_art())
            showcase_path = self._write(tmp, 'SHOWCASE.DAT', SPRITES)
            name, block, data = require_file(frontend_path, lazy=False)
            out = os.path.join(tmp, 'out')
            files = TnfsSaturnFrontendArtSerializer().serialize(data, out, id=name, block=block)
            names = {os.path.basename(x) for x in files}
            for expected in ('0_0.png', '3_1.png', '4_0.png', '5_1.png', 'pcx_0.png', 'pcx_18.png', 'pcx_16_55.png'):
                self.assertIn(expected, names)
            self.assertEqual(len(files), 4 * 2 + 1 + 2 + 19 + 2)
            # the sprite without a palette takes the screen palette, the glyph the font palette, the PCX its own
            sprite = Image.open(os.path.join(out, '0_1.png'))
            self.assertEqual(sprite.getpixel((3, 0)), _rgba(_palette_color(TNFS_SATURN_SCREEN_PALETTE, 1)))
            glyph = Image.open(os.path.join(out, '4_0.png'))
            self.assertEqual(glyph.size, (5, 3))
            self.assertEqual(glyph.getpixel((0, 0)), _rgba(_palette_color(TNFS_SATURN_FONT_PALETTE, 1)))
            pcx = Image.open(os.path.join(out, 'pcx_1.png'))
            self.assertEqual(pcx.getpixel((0, 0))[3], 0)
            self.assertEqual(pcx.getpixel((1, 0)), _rgba(_palette_color(TNFS_SATURN_FRONTEND_PCX_PALETTES[1], 6)))
            # SHOWCASE.DAT takes the palettes of FRONTEND.DAT next to it
            name, block, data = require_file(showcase_path, lazy=False)
            files = TnfsSaturnSpriteBanksSerializer().serialize(
                data, os.path.join(tmp, 'showcase'), id=name, block=block
            )
            self.assertEqual(sorted(os.path.basename(x) for x in files), ['0_0.png', '0_1.png'])


class TestTnfsSaturnRlePicture(unittest.TestCase):
    COLORS = [0x1F] * 300 + list(range(0x400, 0x400 + 20)) + [0x7C00] * 320

    def test_runs(self):
        raw = _rle_picture(self.COLORS, [(False, 300), (True, 20), (False, 320)])
        self.assertTrue(is_tnfs_saturn_rle_picture(raw))
        # a byte more or a run less: not a picture of that size
        self.assertFalse(is_tnfs_saturn_rle_picture(raw + b'\0\0'))
        self.assertFalse(is_tnfs_saturn_rle_picture(raw[:-4]))
        block = TnfsSaturnRlePicture()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(block.pack(data), raw)
        image = tnfs_saturn_rle_picture_image(data)
        self.assertEqual(image.size, (320, 2))
        self.assertEqual(image.getpixel((299, 0)), (255, 0, 0))
        self.assertEqual(image.getpixel((300, 0)), _rgba(0x400)[:3])
        self.assertEqual(image.getpixel((319, 1)), (0, 0, 255))

    def test_detected_and_exported(self):
        raw = _rle_picture(self.COLORS, [(True, 2), (False, 298), (True, 20), (False, 320)])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, '1.BIN')
            with open(path, 'wb') as f:
                f.write(raw)
            self.assertIs(_probe(path), TnfsSaturnRlePicture)
            name, block, data = require_file(path, lazy=False)
            files = TnfsSaturnRlePictureSerializer().serialize(
                data, os.path.join(tmp, 'out', '1.BIN'), id=name, block=block
            )
            self.assertEqual([os.path.basename(x) for x in files], ['1.BIN.png'])


# palette of the synthetic 8-bit pictures: colour 0 green 0x03E0 (as in every `.IM` file), colour i = i * 3
SIZED_PALETTE = [0x03E0] + [i * 3 for i in range(1, 256)]


def _sized_rle_image(width, height, rows, padding=b''):
    """A `TnfsSaturnSizedRleImage`: `rows` are the runs (bytes) of each row"""
    body = struct.pack('>HH', width, height) + struct.pack('>256H', *SIZED_PALETTE) + b''.join(rows) + padding
    return struct.pack('>I', 4 + len(body)) + body


class TestTnfsSaturnSizedRleImage(unittest.TestCase):
    # 4x2: row 0 a run of 5 (cut at the row end, as the game's loader does), row 1 two literal pixels and a run of 2
    ROWS = [bytes([0xC5, 7]), bytes([0, 2, 0xC2, 3])]

    def _write(self, folder, name, raw):
        path = os.path.join(folder, name)
        with open(path, 'wb') as f:
            f.write(raw)
        return path

    def test_rows_decoded_one_by_one(self):
        raw = _sized_rle_image(4, 2, self.ROWS)
        data = TnfsSaturnSizedRleImage().unpack_from_bytes(raw)
        self.assertEqual(tnfs_saturn_rle_pixels(data['image']), [7, 7, 7, 7, 0, 2, 3, 3])
        self.assertEqual(tnfs_saturn_rle_end(b''.join(self.ROWS), 4, 2), 6)
        self.assertIsNone(tnfs_saturn_rle_end(b''.join(self.ROWS)[:-1], 4, 2))

    def test_detected_written_back_and_exported(self):
        # an odd length: no zeros after the runs (HORIZON/AL1RISE.IM)
        raw = _sized_rle_image(4, 2, self.ROWS)
        self.assertTrue(is_tnfs_saturn_sized_rle_image(raw))
        padded = _sized_rle_image(4, 2, self.ROWS, b'\0\0')
        self.assertTrue(is_tnfs_saturn_sized_rle_image(padded))
        # not a picture: other bytes after the runs, a size other than the length, runs short of the picture
        self.assertFalse(is_tnfs_saturn_sized_rle_image(_sized_rle_image(4, 2, self.ROWS, b'\1')))
        self.assertFalse(is_tnfs_saturn_sized_rle_image(_sized_rle_image(4, 2, self.ROWS, b'\0' * 4)))
        self.assertFalse(is_tnfs_saturn_sized_rle_image(raw + b'\0'))
        self.assertFalse(is_tnfs_saturn_sized_rle_image(_sized_rle_image(4, 3, self.ROWS)))
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, 'AL1RISE.IM', padded)
            self.assertIs(_probe(path), TnfsSaturnSizedRleImage)
            name, block, data = require_file(path, lazy=False)
            self.assertEqual(block.pack(data), padded)
            self.assertEqual(data['size'], len(padded))
            files = TnfsSaturnSizedRleImageSerializer().serialize(
                data, os.path.join(tmp, 'out', 'AL1RISE.IM'), id=name, block=block
            )
            self.assertEqual([os.path.basename(x) for x in files], ['AL1RISE.IM.png'])
            image = Image.open(files[0])
            self.assertEqual(image.size, (4, 2))
            # colour 0 transparent
            self.assertEqual(image.getpixel((0, 1))[3], 0)
            self.assertEqual(image.getpixel((3, 1)), _rgba(SIZED_PALETTE[3]))

    def test_list(self):
        # `DASH/EMEM3.DAT`: two pictures back to back
        raw = _sized_rle_image(4, 2, self.ROWS, b'\0\0') + _sized_rle_image(2, 1, [bytes([5, 6])])
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, 'EMEM3.DAT', raw)
            self.assertIs(_probe(path), TnfsSaturnSizedRleImageList)
            name, block, data = require_file(path, lazy=False)
            self.assertEqual(block.pack(data), raw)
            self.assertEqual([(x['image']['width'], x['image']['height']) for x in data['images']], [(4, 2), (2, 1)])
            files = TnfsSaturnSizedRleImageListSerializer().serialize(
                data, os.path.join(tmp, 'out', 'EMEM3.DAT'), id=name, block=block
            )
            self.assertEqual([os.path.basename(x) for x in files], ['0.png', '1.png'])
            self.assertEqual(Image.open(files[1]).getpixel((1, 0)), _rgba(SIZED_PALETTE[6]))
            # a picture cut short: no list
            with self.assertRaises(NotImplementedError):
                _probe(self._write(tmp, 'CUT.DAT', raw[:-1]))


class TestTnfsSaturnGtrExecutableCockpit(unittest.TestCase):
    def test_cockpit_records_and_speedometer_tops(self):
        raw = bytearray(TNFS_SATURN_GTR_EXECUTABLE_LENGTH)
        # model 1 (BCNR33): red needles, lengths 10 / 10, tachometer (184, 168) 620 -174, speedometer (142, 168)
        # 675 128, wheel at 72, 128 turning about 89, 89
        record = struct.pack(
            '>HBBhhhhBBhhhhhhhhH', 0x16, 10, 10, 184, 168, 620, -174, 10, 10, 142, 168, 675, 128, 72, 128, 89, 89, 0
        )
        offset = TNFS_SATURN_GTR_COCKPIT_RECORDS_OFFSET + 0x20
        raw[offset : offset + 0x20] = record
        tops = struct.pack('>8i', 240, 180, 180, 240, 180, 180, 180, 180)
        raw[TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET : TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET + 32] = tops
        block = TnfsSaturnGtrExecutable()
        data = block.unpack_from_bytes(bytes(raw))
        self.assertEqual(len(data['cockpit_records']), 9)
        cockpit = data['cockpit_records'][1]
        self.assertEqual(cockpit['needle_color'], 0x16)
        self.assertEqual((cockpit['tachometer_x_length'], cockpit['tachometer_y_length']), (10, 10))
        self.assertEqual((cockpit['tachometer_x'], cockpit['tachometer_y']), (184, 168))
        self.assertEqual((cockpit['tachometer_scale'], cockpit['tachometer_offset']), (620, -174))
        self.assertEqual((cockpit['speedometer_scale'], cockpit['speedometer_offset']), (675, 128))
        self.assertEqual((cockpit['steering_wheel_left'], cockpit['steering_wheel_top']), (72, 128))
        self.assertEqual((cockpit['steering_wheel_pivot_x'], cockpit['steering_wheel_pivot_y']), (89, 89))
        self.assertEqual(data['speedometer_tops'], [240, 180, 180, 240, 180, 180, 180, 180])
        self.assertEqual(block.pack(data), bytes(raw))

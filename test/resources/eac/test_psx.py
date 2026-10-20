import os
import shutil
import struct
import tempfile
import unittest

import numpy as np
from PIL import Image

from library import require_file
from library.loader import clear_file_cache
from resources.eac.archives import ShppBlock, WwwwBlock
from resources.eac.psx import (
    PsxHorizonSettings,
    TnfsPsxHorizonInfo,
    parse_psx_horizon_settings,
    psx_crc16,
)
from serializers.bitmaps import PsxImageSerializer

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')


def psx_image(type_id, width, height, rows, clut=None, vram_x=0, vram_y=0):
    """Bytes of a PSX image item: header, rows (already padded to 16-bit words), 4-byte alignment, CLUT"""
    pixels = b''.join(rows)
    pad = b'\0' * (-(16 + len(pixels)) % 4) if clut is not None else b''
    next_offset = 16 + len(pixels) + len(pad) if clut is not None else 0
    header = struct.pack('<I6H', type_id | next_offset << 8, width, height, 0, 0, vram_x, vram_y)
    result = header + pixels + pad
    if clut is not None:
        result += struct.pack('<I6H', 0x23, len(clut), 1, len(clut), 0, 0, 240) + struct.pack(f'<{len(clut)}H', *clut)
    return result


def shpp(items, footer=True):
    """Bytes of an SHPP of (name, item bytes), items padded to 4 bytes, with a CRC footer"""
    directory_length = 16 + 8 * len(items)
    offsets, data = [], b''
    for _, item in items:
        offsets.append(directory_length + len(data))
        data += item + b'\0' * (-len(item) % 4)
    body = struct.pack('<4sII4s', b'SHPP', directory_length + len(data), len(items), b'GIMX')
    body += b''.join(struct.pack('<4sI', name.encode(), offset) for (name, _), offset in zip(items, offsets))
    body += data
    if footer:
        body += b'CRCF' + struct.pack('<II', 12, psx_crc16(body))
    return body


# 3x2 4-bit image: rows of 1 word, pixels 1, 2, 3 / 4, 5, 0 (low nibble first)
FOUR_BIT = psx_image(0x40, 3, 2, [bytes([0x21, 0x03]), bytes([0x54, 0x00])], clut=list(range(16)))
# 2x3 8-bit image stored rotated (shown 3 wide, 2 high): 3 words of pixels, the CLUT (4 colors) aligned to 4 bytes
EIGHT_BIT_ROTATED = psx_image(
    0x41,
    2,
    3,
    [bytes([0, 1]), bytes([2, 3]), bytes([0, 1])],
    clut=[0, 0x001F, 0x03E0, 0x7C00],
    vram_x=0x4100,
    vram_y=0x4010,
)
# 1x1 16-bit image: 2 bytes of pixels, no CLUT, 2 bytes of alignment after it in the archive
SIXTEEN_BIT = psx_image(0x42, 1, 1, [struct.pack('<H', 0x801F)])


class TestPsxCrc(unittest.TestCase):
    def test_crc_of_the_sample_matches_its_footer(self):
        with open(os.path.join(SAMPLES, 'ZAL1A.INF'), 'rb') as f:
            raw = f.read()
        self.assertEqual(raw[-12:-8], b'CRCF')
        self.assertEqual(psx_crc16(raw[:-12]), struct.unpack('<I', raw[-4:])[0])


class TestTnfsPsxHorizonInfo(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(SAMPLES, 'ZAL1A.INF'), 'rb') as f:
            self.raw = f.read()

    def test_reads_text_and_footer_and_writes_back(self):
        block = TnfsPsxHorizonInfo()
        data = block.unpack_from_bytes(self.raw)
        self.assertTrue(data['text'].startswith('#vert offset near'))
        self.assertNotIn('CRCF', data['text'])
        self.assertEqual(data['crc_footer']['crc'], 0x1C5E)
        self.assertEqual(block.pack(data), self.raw)

    def test_edited_text_gets_a_new_crc(self):
        block = TnfsPsxHorizonInfo()
        data = block.unpack_from_bytes(self.raw)
        data['text'] = data['text'].replace('-50', '-40')
        packed = block.pack(data)
        self.assertEqual(struct.unpack('<I', packed[-4:])[0], psx_crc16(packed[:-12]))
        self.assertEqual(parse_psx_horizon_settings(block.unpack_from_bytes(packed)['text']).ring_y_offset, -40)

    def test_file_without_footer(self):
        block = TnfsPsxHorizonInfo()
        data = block.unpack_from_bytes(self.raw[:-12])
        self.assertIsNone(data['crc_footer'])
        self.assertEqual(block.pack(data), self.raw[:-12])

    def test_settings(self):
        settings = parse_psx_horizon_settings(TnfsPsxHorizonInfo().unpack_from_bytes(self.raw)['text'])
        self.assertEqual(
            settings,
            PsxHorizonSettings(0, 0, 0, 0, 0, 48, 0, 96, (50, 58, 58), (57, 65, 65), 1, 30, -50, 112, 0),
        )
        # halved by the game, towards 0
        self.assertEqual((settings.screen_y_offset, settings.screen_ring_height), (-25, 56))
        self.assertEqual(settings._replace(ring_y_offset=-57).screen_y_offset, -28)

    def test_too_few_values(self):
        self.assertIsNone(parse_psx_horizon_settings('#a\n1\n2\n'))


class TestShppBlock(unittest.TestCase):
    def setUp(self):
        self.raw = shpp([('img4', FOUR_BIT), ('img8', EIGHT_BIT_ROTATED), ('i16', SIXTEEN_BIT)])

    def test_reads_images_cluts_and_footer(self):
        block = ShppBlock()
        data = block.unpack_from_bytes(self.raw)
        self.assertEqual([c['alias'] for c in data['children']], ['img4', 'img8', 'i16'])
        image_choice = block.item_block.get_choice_index_by_class_name('PsxImage')
        self.assertTrue(all(c['item']['choice_index'] == image_choice for c in data['children']))
        four, eight, sixteen = [c['item']['data'] for c in data['children']]
        self.assertEqual(four['resource_id'], '4Bit PSX')
        self.assertEqual(four['clut']['colors'], list(range(16)))
        self.assertEqual(eight['pad'], b'\0\0')
        self.assertEqual(eight['clut']['colors'], [0, 0x001F, 0x03E0, 0x7C00])
        self.assertIsNone(sixteen['clut'])
        self.assertEqual(data['children'][2]['post_offset_payload'], b'\0\0')
        self.assertEqual(data['crc_footer']['crc'], psx_crc16(self.raw[:-12]))

    def test_writes_back_byte_exact(self):
        block = ShppBlock()
        self.assertEqual(block.pack(block.unpack_from_bytes(self.raw)), self.raw)

    def test_new_crc_after_a_change(self):
        block = ShppBlock()
        data = block.unpack_from_bytes(self.raw)
        data['children'][0]['item']['data']['clut']['colors'][1] = 0x7FFF
        packed = block.pack(data)
        self.assertNotEqual(packed, self.raw)
        self.assertEqual(struct.unpack('<I', packed[-4:])[0], psx_crc16(packed[:-12]))
        self.assertEqual(struct.unpack('<I', packed[4:8])[0], len(packed) - 12)

    def test_inside_wwww_the_footer_stays_after_the_last_item(self):
        inner = shpp([('img4', FOUR_BIT)], footer=False)
        body = b'wwww' + struct.pack('<II', 1, 12) + inner
        raw = body + b'CRCF' + struct.pack('<II', 12, psx_crc16(body))
        block = WwwwBlock()
        data = block.unpack_from_bytes(raw)
        child = data['children'][0]
        self.assertEqual(block.item_block.possible_blocks[child['item']['choice_index']].__class__, ShppBlock)
        self.assertIsNone(child['item']['data']['crc_footer'])
        self.assertEqual(child['post_offset_payload'], raw[-12:])
        self.assertEqual(block.pack(data), raw)


class TestPsxImageSerializer(unittest.TestCase):
    def setUp(self):
        block = ShppBlock()
        data = block.unpack_from_bytes(shpp([('img4', FOUR_BIT), ('img8', EIGHT_BIT_ROTATED), ('i16', SIXTEEN_BIT)]))
        self.four, self.eight, self.sixteen = [c['item']['data'] for c in data['children']]

    def test_4bit_low_nibble_first_and_indexed(self):
        image = PsxImageSerializer().to_png_image(self.four)
        self.assertEqual(image.mode, 'P')
        self.assertEqual(list(image.getdata()), [1, 2, 3, 4, 5, 0])

    def test_rotated_image_is_shown_upright_and_0000_is_transparent(self):
        image = PsxImageSerializer().to_image(self.eight)
        # stored 2x3 [[0, 1], [2, 3], [0, 1]]: shown 3x2, the left column bottom to top is the top row
        self.assertEqual(image.size, (3, 2))
        pixels = np.asarray(image)
        red, green, blue, clear = [255, 0, 0, 255], [0, 255, 0, 255], [0, 0, 255, 255], [0, 0, 0, 0]
        self.assertEqual(pixels[0].tolist(), [clear, green, clear])
        self.assertEqual(pixels[1].tolist(), [red, blue, red])

    def test_16bit_stp_black_red_is_opaque(self):
        image = PsxImageSerializer().to_png_image(self.sixteen)
        self.assertEqual(image.mode, 'RGBA')
        self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))


class TestShppExport(unittest.TestCase):
    """A track's textures at a time of day: PNGs and the sky sphere texture made with the INF of the same name"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        sector = psx_image(0x41, 2, 4, [bytes([1, 1])] * 4, clut=[0, 0x001F])
        items = [(f'hrz{i}', sector) for i in range(8)] + [('img4', FOUR_BIT)]
        self.psh = os.path.join(self.tmp, 'ZAL1A.PSH')
        with open(self.psh, 'wb') as f:
            f.write(shpp(items))
        shutil.copy(os.path.join(SAMPLES, 'ZAL1A.INF'), os.path.join(self.tmp, 'ZAL1A.INF'))

    def tearDown(self):
        clear_file_cache(self.psh)
        shutil.rmtree(self.tmp)

    def test_export(self):
        name, block, data = require_file(self.psh)
        serializer = block.serializer_class()()
        serializer.patch_settings({'maps__save_spherical_skybox_texture': True})
        out = os.path.join(self.tmp, 'out')
        files = serializer.serialize(data, out, id=name, block=block)
        names = {os.path.basename(x) for x in files}
        self.assertTrue({'hrz0.png', 'img4.png', 'spherical.png'} <= names)
        sky = np.asarray(Image.open(os.path.join(out, 'spherical.png')))
        self.assertEqual(sky.shape, (1024, 2048, 4))
        # colour top above, the red sectors at eye level
        self.assertEqual(sky[10, 0].tolist(), [50, 58, 58, 255])
        self.assertEqual(sky[512, 1024].tolist(), [255, 0, 0, 255])
        # below: the average of the ring's bottom line, no black
        self.assertEqual(sky[1023, 0].tolist(), [255, 0, 0, 255])

    def test_no_sky_without_settings(self):
        os.remove(os.path.join(self.tmp, 'ZAL1A.INF'))
        name, block, data = require_file(self.psh)
        serializer = block.serializer_class()()
        serializer.patch_settings({'maps__save_spherical_skybox_texture': True})
        files = serializer.serialize(data, os.path.join(self.tmp, 'out'), id=name, block=block)
        self.assertNotIn('spherical.png', {os.path.basename(x) for x in files})


if __name__ == '__main__':
    unittest.main()

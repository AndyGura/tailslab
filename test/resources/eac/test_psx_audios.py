import json
import os
import shutil
import struct
import tempfile
import unittest
import wave
from io import BytesIO

import numpy as np

from library import require_file
from library.loader import probe_block_class
from resources.eac.psx import psx_crc16
from resources.eac.psx_audios import (
    TnfsPsxPatchBank,
    TnfsPsxVagBank,
    TnfsPsxVagSample,
    psx_spu_sample_rate,
    tnfs_psx_bank_patches,
    tnfs_psx_vag_bank_samples_by_offset,
)
from serializers import TnfsPsxVagBankSerializer
from serializers.misc.tnfs_psx_car_sounds import TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_VOLUMES, tnfs_psx_car_bank


def frame(nibble: int, flags: int = 0, shift: int = 12, filter_index: int = 0) -> bytes:
    """A PS-ADPCM frame of 28 equal nibbles"""
    return bytes([filter_index << 4 | shift, flags]) + bytes([nibble | nibble << 4]) * 14


SILENT = bytes(16)
# looped: frame 1 the loop start, frame 3 the loop end
LOOPED = SILENT + frame(1, 2) + frame(2, 6) + frame(3, 2) + frame(4, 3)
# one-shot: ends after frame 2, then the terminator frame
ONE_SHOT = SILENT + frame(5, 4) + frame(6, 1) + bytes([0, 7]) + b'\x77' * 14


def footer(body: bytes) -> bytes:
    return body + b'CRCF' + struct.pack('<II', 12, psx_crc16(body))


def vag(name: str, data: bytes, rate: int = 44100, size: int = None, leftovers: bytes = b'') -> bytes:
    header = b'VAGp' + struct.pack('>IIII', 3, 0, len(data) if size is None else size, rate) + bytes(12)
    return header + name.encode().ljust(16, b'\0') + data + leftovers


def vb(samples) -> bytes:
    """Bytes of a `.VB` of "VAGp" samples, and the offset of each"""
    offsets, data = [], b''
    for sample in samples:
        offsets.append(16 + len(data))
        data += sample
    return footer(b'Bgav' + struct.pack('<III', 16 + len(data), len(samples), len(data)) + data), offsets


def patch(offset, pitch=0x1000, right_offset=-1, bend=12, volume=0x7F, random_pitch=0, reverb=1) -> bytes:
    channels = 2 if right_offset >= 0 else 1
    return struct.pack(
        '<iiHHHHBBBBBBBB',
        offset,
        right_offset,
        pitch,
        pitch if channels == 2 else 0,
        0,
        random_pitch,
        channels,
        volume,
        0x40,
        bend,
        0,
        0,
        0,
        reverb,
    )


def vh(patches_by_id, sample_count, spu_size) -> bytes:
    """Bytes of a `.VH` of {sample id: patch bytes}"""
    table = [-1] * 128
    for index, sample_id in enumerate(patches_by_id):
        table[sample_id] = index
    body = b'BXSP' + struct.pack('<III', len(patches_by_id), sample_count, spu_size)
    body += struct.pack('<128b', *table) + b''.join(patches_by_id.values())
    return footer(body)


def car_bank(names=('engine_a', 'engine_b', 'horn', 'shift')):
    """`.VB` and `.VH` bytes of a car bank: ids 1 (stereo), 2, 3 looped, 0x20 a one-shot at half rate"""
    samples = [vag(f'{names[0]}L', LOOPED), vag(f'{names[0]}R', LOOPED), vag(names[1], LOOPED)]
    samples += [vag(names[2], LOOPED), vag(names[3], ONE_SHOT, rate=22050)]
    vb_bytes, offsets = vb(samples)
    patches = {
        1: patch(offsets[0], right_offset=offsets[1], pitch=0x2000),
        2: patch(offsets[2], bend=16),
        3: patch(offsets[3], pitch=1486, bend=0),
        0x20: patch(offsets[4], pitch=0x800, random_pitch=150, reverb=0),
    }
    return vb_bytes, vh(patches, len(samples), len(vb_bytes) - 28)


class TestTnfsPsxSoundBanks(unittest.TestCase):
    def setUp(self):
        # a folder of its own per test: the file cache keys by path
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def test_detected_and_written_back(self):
        vb_bytes, vh_bytes = car_bank()
        for data, block_class in ((vb_bytes, TnfsPsxVagBank), (vh_bytes, TnfsPsxPatchBank)):
            self.assertIs(probe_block_class(BytesIO(data), 'ZCAR.X', len(data)), block_class)
            block = block_class()
            self.assertEqual(block.pack(block.unpack_from_bytes(data)), data)

    def test_patch_bank(self):
        _, vh_bytes = car_bank()
        data = TnfsPsxPatchBank().unpack_from_bytes(vh_bytes)
        patches = tnfs_psx_bank_patches(data)
        self.assertEqual(list(patches), [1, 2, 3, 0x20])
        self.assertEqual(patches[1]['channels'], 2)
        self.assertEqual(patches[0x20]['random_pitch_range'], 150)
        self.assertEqual(data['crc_footer']['resource_id'], 'CRCF')
        # a changed value gets a new CRC
        data['patches'][0]['volume'] = 100
        packed = TnfsPsxPatchBank().pack(data)
        self.assertEqual(struct.unpack('<I', packed[-4:])[0], psx_crc16(packed[:-12]))

    def test_samples_up_to_the_next_header(self):
        # the second sample's size runs into the third one (CarHorn of ZCOLLISN), the first has leftovers
        samples = [
            vag('a', LOOPED, leftovers=frame(9) * 2),
            vag('b', ONE_SHOT, size=len(ONE_SHOT) + 32),
            vag('c', LOOPED),
        ]
        vb_bytes, offsets = vb(samples)
        data = TnfsPsxVagBank().unpack_from_bytes(vb_bytes)
        self.assertEqual([len(x['wave_data']) for x in data['samples']], [len(LOOPED), len(ONE_SHOT), len(LOOPED)])
        self.assertEqual(len(data['samples'][0]['leftovers']), 32)
        self.assertEqual(data['samples'][1]['data_size'], len(ONE_SHOT) + 32)
        self.assertEqual(list(tnfs_psx_vag_bank_samples_by_offset(data)), offsets)
        self.assertEqual(TnfsPsxVagBank().pack(data), vb_bytes)

    def test_sample_file_of_its_own(self):
        data = footer(vag('SFX_Level', ONE_SHOT, rate=22050))
        self.assertIs(probe_block_class(BytesIO(data), 'ZSFXLEVL.VAG', len(data)), TnfsPsxVagSample)
        parsed = TnfsPsxVagSample().unpack_from_bytes(data)
        self.assertEqual((parsed['name'], parsed['leftovers']), ('SFX_Level', b''))
        self.assertIsNotNone(parsed['crc_footer'])
        self.assertEqual(TnfsPsxVagSample().pack(parsed), data)

    def _export(self, name, vb_bytes, vh_bytes, executable=None):
        vb_path = self._write(f'{name}.VB', vb_bytes)
        self._write(f'{name}.VH', vh_bytes)
        if executable:
            self._write(executable, b'')
        id, block, data = require_file(vb_path)
        out = os.path.join(self.tmp, 'out', f'{name}.VB')
        files = TnfsPsxVagBankSerializer().serialize(data, out, id=id, block=block)
        return out, sorted(os.path.basename(x) for x in files)

    def test_us_car_bank_export(self):
        out, files = self._export('ZDIABLO', *car_bank())
        names = ['engine_on', 'engine_off', 'honk', 'gear']
        self.assertEqual(files, sorted([f'{x}.wav' for x in names] + [f'{x}.meta.json' for x in names]))
        with wave.open(os.path.join(out, 'engine_on.wav')) as f:
            # two channels at the patch's pitch 0x2000
            self.assertEqual((f.getnchannels(), f.getframerate(), f.getnframes()), (2, 88200, 5 * 28))
        with open(os.path.join(out, 'engine_on.meta.json')) as f:
            meta = json.load(f)
        self.assertTrue(meta['loop'])
        self.assertAlmostEqual(meta['loop_start_time_ms'], 1000 * 2 * 28 / 88200)
        self.assertAlmostEqual(meta['loop_end_time_ms'], 1000 * (5 * 28 - 1) / 88200)
        self.assertEqual(
            (meta['bend_range_semitones'], meta['volume'], meta['pan'], meta['reverb']), (12, 127, 64, True)
        )
        self.assertEqual(meta['max_playback_rate'], 2.0)
        self.assertNotIn('volume_by_pitch_value', meta)
        with wave.open(os.path.join(out, 'honk.wav')) as f:
            self.assertEqual(f.getframerate(), round(psx_spu_sample_rate(1486)))
        with open(os.path.join(out, 'gear.meta.json')) as f:
            meta = json.load(f)
        with wave.open(os.path.join(out, 'gear.wav')) as f:
            # the one-shot plays up to its end frame, at the patch's pitch, not the header's rate
            self.assertEqual((f.getframerate(), f.getnframes()), (22050, 3 * 28))
        self.assertFalse(meta['loop'])
        self.assertEqual(meta['random_range'], 150)

    def test_japanese_car_bank_export(self):
        out, files = self._export('ZKPGC', *car_bank(), executable='SLPS_010.24')
        self.assertIn('engine_low.wav', files)
        self.assertIn('engine_high.meta.json', files)
        self.assertNotIn('honk.wav', files)
        with open(os.path.join(out, 'engine_mid.meta.json')) as f:
            meta = json.load(f)
        self.assertEqual(meta['volume_by_pitch_value'], list(TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_VOLUMES['KPGC'][1]))
        with open(os.path.join(out, 'gear.meta.json')) as f:
            self.assertNotIn('volume_by_pitch_value', json.load(f))

    def test_other_bank_export(self):
        vb_bytes, offsets = vb([vag('Bump', ONE_SHOT), vag('Radar', ONE_SHOT)])
        vh_bytes = vh({0x21: patch(offsets[0]), 0x67: patch(offsets[1], pitch=0x200), 0x62: patch(-1)}, 2, 0)
        out, files = self._export('ZCOLLISN', vb_bytes, vh_bytes)
        self.assertEqual(files, ['0x21.meta.json', '0x21.wav', '0x67.meta.json', '0x67.wav'])
        with wave.open(os.path.join(out, '0x67.wav')) as f:
            # 5512.5 Hz, rounded half to even as nfs-web's hand-made copy (custom PSX/ZCOLLISN.VB/0x67.wav)
            self.assertEqual(f.getframerate(), 5512)

    def test_car_bank_names(self):
        self.assertIsNone(tnfs_psx_car_bank('games/x/ZFRNTEND.VB', range(1, 8)))
        # split screen banks lack the gear shift; ZS54B is the player bank of the S54B
        self.assertEqual(
            list(tnfs_psx_car_bank('ZSSUPRA.VB', [1, 2, 3]).names.values()), ['engine_on', 'engine_off', 'honk']
        )
        bank = tnfs_psx_car_bank('ZS54B.VB', [1, 2, 3, 0x20])
        self.assertEqual(bank.names[3], 'engine_high')
        self.assertEqual(len(bank.layer_volumes[1]), 128)
        # the Warrior's banks of the US disc
        self.assertEqual(tnfs_psx_car_bank('ZWARRIOR.VB', [1, 2, 3, 0x20]).names[3], 'honk')


class TestSpuLoops(unittest.TestCase):
    def test_loop_is_decoded_as_played_again(self):
        from library.utils.audio_ps_adpcm_codec import decode_spu_sample

        # filter 1 frames carry the previous sample on: the loop start depends on the history
        data = SILENT + frame(1, 6, filter_index=1) + frame(0, 3, filter_index=1)
        played = decode_spu_sample(data)
        self.assertEqual(played.loop_start, 28)
        once = np.array(decode_spu_sample(SILENT + frame(1, 6, filter_index=1)).samples[28:])
        # the first loop sample continues from the loop's last one, not from silence
        self.assertGreater(played.samples[28], once[0])

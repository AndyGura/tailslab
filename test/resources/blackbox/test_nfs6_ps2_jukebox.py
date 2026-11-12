import json
import os
import tempfile
import unittest
import wave

from library import require_file, require_resource
from library.lazy import is_loaded
from library.loader import clear_file_cache
from library.utils.id import join_id
from resources.blackbox.audios.nfs6_ps2 import Nfs6Ps2Jukebox
from serializers import get_serializer
from test.library.utils.test_audio_ps_adpcm_codec import END_FRAME, TERMINATOR, frame

# blocks of one sector per channel
INTERLEAVE = 2048


def track(left: bytes, right: bytes, gap: int) -> bytes:
    """A jukebox track of two equally long channel streams, interleaved, then `gap` zeros"""
    data = b''
    for start in range(0, len(left), INTERLEAVE):
        for stream in (left, right):
            part = stream[start : start + INTERLEAVE]
            data += part + bytes(INTERLEAVE - len(part))
    header = (
        b'VAGp'
        + (2).to_bytes(4, 'big')
        + bytes(4)
        + (2 * len(left)).to_bytes(4, 'big')
        + (32000).to_bytes(4, 'big')
        + bytes(16)
        + b'VAGx'
        + bytes(4)
        + (2).to_bytes(4, 'big')
    )
    return header + data + bytes(gap)


def entry(offset: int, length: int, name: bytes, padding: bytes) -> bytes:
    return (
        offset.to_bytes(4, 'little')
        + (0x30).to_bytes(2, 'little')
        + (length >> 16).to_bytes(2, 'little')
        + bytes(4)
        + name
        + b'\0'
        + padding
    )


def jukebox() -> bytes:
    """Two tracks: the first with whole blocks and a half one per channel (left samples 1, right 2), the second
    shorter than a block (left 3, right 4). Names with leftovers after them"""
    tracks = [
        track(frame(0, 12, 1) * 150 + END_FRAME + TERMINATOR, frame(0, 12, 2) * 150 + END_FRAME + TERMINATOR, 0xFD0),
        track(frame(0, 12, 3) * 10 + END_FRAME + TERMINATOR, frame(0, 12, 4) * 10 + END_FRAME + TERMINATOR, 0x800),
    ]
    names = [
        (b'Artist-Song (Inst)-Album-Rock-2 ', b'wav\0' + b'\xcc' * 46 + b'\0'),
        (b'Artist-Song--Techno-0', bytes(62)),
    ]
    header = (
        (INTERLEAVE // 2048).to_bytes(4, 'little')
        + (2).to_bytes(4, 'little')
        + (32000).to_bytes(4, 'little')
        + (1).to_bytes(4, 'little')
        + (0x1000).to_bytes(4, 'little')
        + bytes(12)
        + (2).to_bytes(4, 'little')
        + b'InGame\0'
        + b'\xcc' * 53
    )
    leftovers = b'\x00\x08\x04\x13' * 4
    offset = len(header) + 2 * 0x60 + len(leftovers)
    entries = b''
    for (name, padding), data in zip(names, tracks):
        entries += entry(offset, len(data), name, padding)
        offset += len(data)
    return header + entries + leftovers + b''.join(tracks)


class TestNfs6Ps2Jukebox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw = jukebox()
        self.path = os.path.join(self.tmp.name, 'JUKEBOXM.JBC').replace('\\', '/')
        with open(self.path, 'wb') as f:
            f.write(self.raw)
        self.addCleanup(clear_file_cache, self.path)

    def test_jukebox_should_be_read_and_remain_the_same(self):
        data = Nfs6Ps2Jukebox().unpack_from_bytes(self.raw)
        self.assertEqual(data['group']['name'], 'InGame')
        self.assertEqual(
            [x['alias'] for x in data['children']], ['Artist-Song (Inst)-Album-Rock-2 ', 'Artist-Song--Techno-0']
        )
        self.assertEqual(data['name_paddings'][0], b'wav\0' + b'\xcc' * 46 + b'\0')
        first = data['children'][0]['item']['data']
        self.assertEqual(first['data_size'], 2 * (152 * 16))
        self.assertEqual(first['channels'], 2)
        self.assertEqual(Nfs6Ps2Jukebox().pack(data), self.raw)

    def test_renamed_track_should_keep_its_entry_length(self):
        block = Nfs6Ps2Jukebox()
        data = block.unpack_from_bytes(self.raw)
        data['children'][1]['alias'] = 'Other'
        packed = block.pack(data)
        self.assertEqual(len(packed), len(self.raw))
        self.assertEqual(block.unpack_from_bytes(packed)['children'][1]['alias'], 'Other')

    def test_file_should_be_read_lazily_and_remain_the_same(self):
        name, block, data = require_file(self.path)
        self.assertIsInstance(block, Nfs6Ps2Jukebox)
        self.assertFalse(is_loaded(data['children'][0]))
        self.assertEqual(block.pack(data), self.raw)
        self.assertEqual(data['children'][1]['item']['data']['resource_id'], 'VAGp')
        self.assertEqual(block.pack(data), self.raw)

    def _wav(self, path):
        with wave.open(path) as wf:
            return wf.getnchannels(), wf.getframerate(), wf.readframes(wf.getnframes())

    def test_serializer_should_write_a_wav_per_track(self):
        name, block, data = require_file(self.path)
        out = os.path.join(self.tmp.name, 'out', 'JUKEBOXM.JBC')
        paths = get_serializer(block, data).serialize(data, out, id=name, block=block)
        self.assertEqual(
            sorted(os.path.basename(x) for x in paths),
            [
                'Artist-Song (Inst)-Album-Rock-2.meta.json',
                'Artist-Song (Inst)-Album-Rock-2.wav',
                'Artist-Song--Techno-0.meta.json',
                'Artist-Song--Techno-0.wav',
            ],
        )
        channels, rate, frames = self._wav(os.path.join(out, 'Artist-Song (Inst)-Album-Rock-2.wav'))
        self.assertEqual((channels, rate), (2, 32000))
        self.assertEqual(frames, b'\x01\x00\x02\x00' * 150 * 28)
        self.assertEqual(self._wav(os.path.join(out, 'Artist-Song--Techno-0.wav'))[2], b'\x03\x00\x04\x00' * 10 * 28)
        with open(os.path.join(out, 'Artist-Song--Techno-0.meta.json')) as f:
            self.assertEqual(
                json.load(f), {'loop': False, 'loop_start_time_ms': 0.0, 'loop_end_time_ms': 1000 * 279 / 32000}
            )

    def test_track_should_be_converted_alone_with_the_interleave_of_its_file(self):
        name, _, _ = require_file(self.path)
        track_id = join_id(name, 'children', '1', 'item', 'data')
        (_, block, data), _ = require_resource(track_id)
        out = os.path.join(self.tmp.name, 'out', 'track')
        paths = get_serializer(block, data).serialize(data, out, id=track_id, block=block)
        self.assertEqual(self._wav(paths[0])[2], b'\x03\x00\x04\x00' * 10 * 28)

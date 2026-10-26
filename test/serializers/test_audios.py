import json
import os
import subprocess
import tempfile
import unittest
import wave
from unittest import mock

from library import require_file
from library.loader import clear_file_cache
from serializers import get_serializer
from test.resources.eac.test_audios import ea_audio_stream, ea_music_map


def _fake_ffmpeg(args, input=None, **kwargs):
    """Decodes a stream to 2 stereo frames per SCDl chunk, each frame holding the amount of chunks"""
    num_chunks = input.count(b'SCDl')
    return subprocess.CompletedProcess(args, 0, stdout=num_chunks.to_bytes(4, 'little') * 2 * num_chunks, stderr=b'')


def _wav_frames(path: str) -> bytes:
    with wave.open(path) as wf:
        return wf.readframes(wf.getnframes())


class TestEaAudioStreamsSerializer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _serialize(self, file_name: str, content: bytes):
        path = os.path.join(self.tmp.name, file_name).replace('\\', '/')
        with open(path, 'wb') as f:
            f.write(content)
        self.addCleanup(clear_file_cache, path)
        name, block, data = require_file(path)
        serializer = get_serializer(block, data)
        out = os.path.join(self.tmp.name, 'out', file_name)
        with mock.patch('serializers.audios.subprocess.run', side_effect=_fake_ffmpeg) as run:
            paths = serializer.serialize(data, out, id=name, block=block)
        return serializer.is_dir(block, data), out, paths, run

    def test_single_stream_goes_to_a_wav_with_loop_meta(self):
        is_dir, out, paths, run = self._serialize('TRACK0.ASF', ea_audio_stream(3, num_samples=6))
        self.assertFalse(is_dir)
        self.assertEqual(paths, [f'{out}.wav', f'{out}.meta.json'])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(_wav_frames(f'{out}.wav'), (3).to_bytes(4, 'little') * 6)
        with open(f'{out}.meta.json') as f:
            meta = json.load(f)
        self.assertFalse(meta['loop'])
        self.assertAlmostEqual(meta['loop_end_time_ms'], 1000 * 5 / 22050)

    def test_stream_without_codec_is_16_bit_pcm_decoded_without_ffmpeg(self):
        # NFS3 show1.mus: v0 header without codec tag, each SCDl chunk = amount of samples + interleaved stereo samples
        frames = [[(1, -1), (2, -2)], [(3, -3)]]
        patch = b'PT\0\0\x06\x01\x65\xfd\x85\x01\x03\x82\x01\x02\xff\0'
        stream = b'SCHl' + (8 + len(patch)).to_bytes(4, 'little') + patch
        stream += b'SCCl' + (12).to_bytes(4, 'little') + (2).to_bytes(4, 'little')
        for chunk in frames:
            samples = b''.join(v.to_bytes(2, 'little', signed=True) for frame in chunk for v in frame)
            stream += b'SCDl' + (12 + len(samples)).to_bytes(4, 'little') + len(chunk).to_bytes(4, 'little') + samples
        stream += b'SCEl' + (8).to_bytes(4, 'little')
        _, out, _, run = self._serialize('SHOW1.MUS', stream + stream)
        run.assert_not_called()
        expected = b''.join(v.to_bytes(2, 'little', signed=True) for chunk in frames for frame in chunk for v in frame)
        self.assertEqual(_wav_frames(f'{out}/0.wav'), expected)
        self.assertEqual(_wav_frames(f'{out}/playthrough.wav'), expected * 2)

    def test_mus_streams_are_named_by_map_node_and_played_through_the_map(self):
        streams = [ea_audio_stream(1), ea_audio_stream(2), ea_audio_stream(3)]
        offsets = [0, len(streams[0]) + 2, len(streams[0]) + 2 + len(streams[1])]
        # node 1 is the third stream of the file, node 2 the second one
        music_map = ea_music_map(
            0,
            [(0, [(0, 49, 1), (50, 100, 2)]), (0, [(0, 100, 0)]), (0, [(0, 100, 2)])],
            [[0, 0, 0, 0]],
            [offsets[0], offsets[2], offsets[1]],
        )
        with open(os.path.join(self.tmp.name, 'himrock.map'), 'wb') as f:
            f.write(music_map)
        is_dir, out, paths, _ = self._serialize('HIMROCK.MUS', streams[0] + b'\0\0' + streams[1] + streams[2])
        self.assertTrue(is_dir)
        self.assertEqual(paths[:2], [f'{out}/playthrough.wav', f'{out}/playthrough.meta.json'])
        for node, num_chunks in [(0, 1), (1, 3), (2, 2)]:
            self.assertEqual(_wav_frames(f'{out}/{node}.wav'), num_chunks.to_bytes(4, 'little') * 2 * num_chunks)
        # value 50: node 0, then node 2, which plays again and again
        self.assertEqual(
            _wav_frames(f'{out}/playthrough.wav'),
            (1).to_bytes(4, 'little') * 2 + (2).to_bytes(4, 'little') * 4,
        )
        with open(f'{out}/playthrough.meta.json') as f:
            meta = json.load(f)
        self.assertEqual(meta['nodes'], [0, 2])
        self.assertEqual(meta['map'], 'himrock.map')
        self.assertTrue(meta['loop'])
        self.assertAlmostEqual(meta['loop_start_time_ms'], 1000 * 2 / 22050)
        self.assertAlmostEqual(meta['loop_end_time_ms'], 1000 * 5 / 22050)

    def test_mus_played_through_the_linear_map_when_there_is_one(self):
        streams = [ea_audio_stream(1), ea_audio_stream(2), ea_audio_stream(3)]
        offsets = [0, len(streams[0]), len(streams[0]) + len(streams[1])]
        interactive_map = ea_music_map(
            0, [(1, [(0, 49, 1), (50, 100, 1)]), (1, [(0, 100, 0)]), (1, [])], [[0] * 4, [0] * 4], offsets
        )
        # NFS3 .lin: the same streams, played one after another from node 1, without a loop
        linear_map = ea_music_map(1, [(0, [(0, 100, 2)]), (0, [(0, 100, 0)]), (0, [])], [[0] * 4], offsets)
        for name, content in [('ALPIROCK.MAP', interactive_map), ('ALPIROCK.LIN', linear_map)]:
            with open(os.path.join(self.tmp.name, name), 'wb') as f:
                f.write(content)
        _, out, _, _ = self._serialize('ALPIROCK.MUS', b''.join(streams))
        with open(f'{out}/playthrough.meta.json') as f:
            meta = json.load(f)
        self.assertEqual((meta['map'], meta['nodes'], meta['loop']), ('ALPIROCK.LIN', [1, 0, 2], False))

    def test_mus_without_map_plays_streams_in_file_order(self):
        _, out, _, _ = self._serialize('SHOW.MUS', ea_audio_stream(1) + ea_audio_stream(2))
        self.assertEqual(
            _wav_frames(f'{out}/playthrough.wav'), (1).to_bytes(4, 'little') * 2 + (2).to_bytes(4, 'little') * 4
        )
        with open(f'{out}/playthrough.meta.json') as f:
            meta = json.load(f)
        self.assertEqual(meta['nodes'], [0, 1])
        self.assertFalse(meta['loop'])


if __name__ == '__main__':
    unittest.main()

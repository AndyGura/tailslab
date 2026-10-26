import unittest
from io import BytesIO

from library.loader import probe_block_class
from resources.eac.audios import EaAudioStreams, EaMusicMap, EaSoundPatch
from resources.eac.videos import FfmpegSupportedVideo


def _tag(tag: int, value: int, length: int) -> bytes:
    return bytes([tag, length]) + value.to_bytes(length, 'big')


def ea_audio_stream(num_data_chunks: int, num_samples: int = 100, header_padding: int = 3) -> bytes:
    """SCHl stream as in NFS2 SE: v0 header (stereo EA-XA), SCCl, SCDl chunks, SCEl"""
    patch = (
        b'PT\0\0'
        + _tag(0x00, 2, 1)
        + _tag(0x06, 0x65, 1)
        + b'\xfd'
        + _tag(0x85, num_samples, 3)
        + _tag(0x82, 2, 1)
        + _tag(0x83, 7, 1)
        + _tag(0x8A, 0, 4)
        + b'\xff'
        + b'\0' * header_padding
    )
    res = b'SCHl' + (8 + len(patch)).to_bytes(4, 'little') + patch
    res += b'SCCl' + (12).to_bytes(4, 'little') + num_data_chunks.to_bytes(4, 'little')
    for i in range(num_data_chunks):
        res += b'SCDl' + (24).to_bytes(4, 'little') + bytes(range(i, i + 16))
    return res + b'SCEl' + (8).to_bytes(4, 'little')


def ea_music_map(start_node: int, nodes, events, stream_offsets, num_events: int = 4) -> bytes:
    """PFDx map: nodes are (section, [(min value, max value, next node)])"""
    res = b'PFDx' + bytes([0, start_node, len(nodes), num_events]) + b'\0\0\0' + bytes([len(events)])
    for section, branches in nodes:
        slots = b''.join(bytes(x) for x in branches)
        res += bytes([section, len(branches)]) + b'\xff\xff' + slots + b'\0' * (24 - len(slots))
    for row in events:
        res += bytes(row)
    return res + b''.join(x.to_bytes(4, 'big') for x in stream_offsets)


class TestEaAudioStreams(unittest.TestCase):
    def test_loader_tells_audio_streams_from_videos(self):
        stream = ea_audio_stream(2)
        self.assertEqual(probe_block_class(BytesIO(stream), 'HIMROCK.ASF', len(stream)), EaAudioStreams)
        # NFS2 SE DCT movie: picture chunks between the audio ones
        header_length = int.from_bytes(stream[4:8], 'little')
        video = stream[:header_length] + b'mTCD' + (12).to_bytes(4, 'little') + b'\0' * 4 + stream[header_length:]
        self.assertEqual(probe_block_class(BytesIO(video), 'DEMOAV0.DCT', len(video)), FfmpegSupportedVideo)
        music_map = ea_music_map(0, [(0, [(0, 100, 0)])], [[0] * 4], [0])
        self.assertEqual(probe_block_class(BytesIO(music_map), 'SHOW.MAP', len(music_map)), EaMusicMap)

    def test_reads_every_stream_with_its_padding_and_writes_back_byte_exact(self):
        streams = [ea_audio_stream(1, 50), ea_audio_stream(3, 150, header_padding=1), ea_audio_stream(2, 100)]
        # MUS files align streams to 4 bytes, the last one can have bytes after it as well
        mus = streams[0] + b'\0\0' + streams[1] + streams[2] + b'\0\0\0'
        block = EaAudioStreams()
        data = block.unpack_from_bytes(mus)
        self.assertEqual(len(data['streams']), 3)
        self.assertEqual([len(x['padding']) for x in data['streams']], [2, 0, 3])
        self.assertEqual([len(x['data']) for x in data['streams']], [12 + 24 + 8, 12 + 3 * 24 + 8, 12 + 2 * 24 + 8])
        layer = EaSoundPatch.layers(data['streams'][1]['header'])[0]
        self.assertEqual((layer['num_samples'], layer['channels'], layer['codec']), (150, 2, 7))
        self.assertEqual(layer['unk_0x00'], 2)
        self.assertEqual(block.pack(data), mus)

    def test_stream_without_end_chunk_reads_up_to_end_of_file(self):
        stream = ea_audio_stream(2)[:-8]
        block = EaAudioStreams()
        data = block.unpack_from_bytes(stream)
        self.assertEqual(len(data['streams']), 1)
        self.assertEqual(block.pack(data), stream)


class TestEaMusicMap(unittest.TestCase):
    def test_reads_nodes_events_and_offsets_and_writes_back_byte_exact(self):
        raw = ea_music_map(
            1,
            [(0, [(0, 49, 1), (50, 100, 2)]), (1, [(0, 100, 0)]), (1, [])],
            [[0, 2, 0, 0], [0, 2, 1, 0]],
            [0, 300, 120],
        )
        block = EaMusicMap()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(
            (data['start_node'], data['num_nodes'], data['num_events'], data['num_sections']), (1, 3, 4, 2)
        )
        node = data['nodes'][0]
        self.assertEqual(node['num_branches'], 2)
        self.assertEqual(
            [(b['min_value'], b['max_value'], b['next_node']) for b in node['branches'][:2]], [(0, 49, 1), (50, 100, 2)]
        )
        self.assertEqual(data['nodes'][2]['num_branches'], 0)
        self.assertEqual(data['events'], [[0, 2, 0, 0], [0, 2, 1, 0]])
        self.assertEqual(data['stream_offsets'], [0, 300, 120])
        self.assertEqual(block.pack(data), raw)


if __name__ == '__main__':
    unittest.main()

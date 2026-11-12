import unittest

from library.utils.audio_ps_adpcm_codec import decode, decode_interleaved, deinterleave

END_FRAME = bytes([0x0C, 0x01]) + bytes(14)
TERMINATOR = bytes([0x00, 0x07]) + b'\x77' * 14


def frame(filter_index: int, shift: int, nibble: int, flags: int = 0) -> bytes:
    """A frame of 28 equal nibbles"""
    return bytes([filter_index << 4 | shift, flags]) + bytes([nibble | nibble << 4]) * 14


class TestPsAdpcmCodec(unittest.TestCase):
    def test_nibbles_should_be_scaled_by_shift(self):
        self.assertEqual(decode(frame(0, 12, 3)).tolist(), [3] * 28)
        self.assertEqual(decode(frame(0, 12, 0xF)).tolist(), [-1] * 28)
        self.assertEqual(decode(frame(0, 0, 0x8)).tolist(), [-32768] * 28)
        # shifts 13..15 are taken as 9
        self.assertEqual(decode(frame(0, 13, 1)).tolist(), [8] * 28)

    def test_filters_should_use_previous_samples(self):
        # s = 1 + (s1 * 60 + 32 >> 6)
        self.assertEqual(decode(frame(1, 12, 1)).tolist()[:6], [1, 2, 3, 4, 5, 6])
        # s = 0 + (s1 * 115 - s2 * 52 + 32 >> 6), history carried over from the frame before
        samples = decode(frame(0, 0, 1) + frame(2, 12, 0)).tolist()
        self.assertEqual(samples[27], 4096)
        self.assertEqual(samples[28], (4096 * 115 - 4096 * 52 + 32) >> 6)

    def test_samples_should_be_clamped(self):
        self.assertEqual(decode(frame(0, 0, 7) + frame(1, 0, 7)).tolist()[28:30], [32767, 32767])

    def test_stream_should_end_before_the_end_flag(self):
        self.assertEqual(len(decode(frame(0, 12, 1) * 3 + END_FRAME + TERMINATOR + frame(0, 12, 1))), 3 * 28)

    def test_interleaved_channels_should_be_split_with_the_last_round_halved(self):
        left = bytes(range(0, 48))
        right = bytes(range(100, 148))
        # blocks of 32 bytes, the last round holds 16 bytes of each channel
        data = left[:32] + right[:32] + left[32:] + bytes(16) + right[32:] + bytes(16)
        self.assertEqual(deinterleave(data, 2, 32, 96), [left, right])

    def test_interleaved_streams_should_decode_to_interleaved_pcm(self):
        left = frame(0, 12, 1) * 2 + END_FRAME + TERMINATOR
        right = frame(0, 12, 2) * 2 + END_FRAME + TERMINATOR
        data = left[:32] + right[:32] + left[32:] + right[32:]
        pcm = decode_interleaved(data, 2, 32, len(data))
        self.assertEqual(pcm, (b'\x01\x00\x02\x00') * 56)

import struct
import unittest

from library.utils.ps2 import as_float, csm1_index, lfsr_next, unswizzle, vif_packets


def _unswizzle8_formula(data: bytes, width: int, height: int) -> bytes:
    """The common closed form of PSMCT32 -> PSMT8 for whole GS pages"""
    out = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            block_location = (y & ~0xF) * width + (x & ~0xF) * 2
            swap_selector = (((y + 2) >> 2) & 1) * 4
            pos_y = (((y & ~3) >> 1) + (y & 1)) & 7
            column_location = pos_y * width * 2 + ((x + swap_selector) & 7) * 4
            byte_num = ((y >> 1) & 1) + ((x >> 2) & 2)
            out[y * width + x] = data[block_location + column_location + byte_num]
    return bytes(out)


class TestPs2(unittest.TestCase):
    def test_8bit_unswizzle_should_match_closed_form(self):
        for width, height in [(128, 64), (256, 64), (256, 256), (512, 256)]:
            data = bytes((i * 7 + (i >> 8) * 13) & 0xFF for i in range(width * height))
            self.assertEqual(unswizzle(data, width, height, 8), _unswizzle8_formula(data, width, height))

    def test_4bit_unswizzle_should_be_a_permutation(self):
        width, height = 128, 128
        # every nibble value of the 16 KB once per 16 nibbles: count them back
        data = bytes((i & 0xFF) for i in range(width * height // 2))
        out = unswizzle(data, width, height, 4)
        self.assertEqual(len(out), width * height)
        self.assertEqual(sorted(out), sorted(x for b in data for x in (b & 15, b >> 4)))

    def test_csm1_index_should_swap_entries_8_15_and_16_23(self):
        self.assertEqual(
            [csm1_index(i) for i in range(32)],
            list(range(8)) + list(range(16, 24)) + list(range(8, 16)) + list(range(24, 32)),
        )
        self.assertEqual(csm1_index(0x48), 0x50)

    def test_lfsr_next(self):
        self.assertEqual(lfsr_next(0x6000), 0xC000)
        # bit 22 and bit 4 are fed back into bit 0
        self.assertEqual(lfsr_next(0x400000), 1)
        self.assertEqual(lfsr_next(0x400010), 0x20)

    def test_vif_packets_should_unpack_into_vu_memory(self):
        stream = b''.join(
            [
                struct.pack('<I', 0x6E018000),
                bytes([3, 0, 9, 0]),  # V4-8 at 0
                struct.pack('<I', 0x6801C002),
                struct.pack('<3f', 1.0, 2.0, 3.0),  # V3-32 at 2
                struct.pack('<I', 0x6F01C034),
                struct.pack('<H', 0x801F),  # V4-5 at 0x34
                b'\0\0',
                struct.pack('<I', 0x14000000),  # MSCAL
            ]
        )
        packets = vif_packets(stream)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0][0], [3, 0, 9, 0])
        self.assertEqual([as_float(x) for x in packets[0][2][:3]], [1.0, 2.0, 3.0])
        self.assertEqual(packets[0][0x34], [0xF8, 0, 0, 0x80])


if __name__ == '__main__':
    unittest.main()

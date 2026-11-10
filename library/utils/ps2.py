"""
PlayStation 2 helpers: VIF packets unpacked into VU memory, the R register LFSR of the VU, GS local memory swizzling of
textures and the CSM1 order of 256-colour palettes.

GS local memory: 8 KB pages of 32 blocks of 256 bytes, 4 columns of 64 bytes per block. A page holds 64x32 pixels of
PSMCT32, 128x64 of PSMT8 and 128x128 of PSMT4; the tables give the block of a page and the word / byte / nibble of a
block for a pixel (GS User's Manual, chapter 8, as GSdx / PCSX2 `GSTables.cpp`). Textures are often stored as they lie
in GS memory after an upload as PSMCT32 ("swizzled"), and read back by the GS as PSMT8 / PSMT4: `unswizzle` reads them
like the GS does.
"""

import struct
from typing import Dict, List

_BLOCK32 = [
    [0, 1, 4, 5, 16, 17, 20, 21],
    [2, 3, 6, 7, 18, 19, 22, 23],
    [8, 9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]
_BLOCK8 = _BLOCK32
_BLOCK4 = [
    [0, 2, 8, 10],
    [1, 3, 9, 11],
    [4, 6, 12, 14],
    [5, 7, 13, 15],
    [16, 18, 24, 26],
    [17, 19, 25, 27],
    [20, 22, 28, 30],
    [21, 23, 29, 31],
]
_COLUMN32 = [
    [0, 1, 4, 5, 8, 9, 12, 13],
    [2, 3, 6, 7, 10, 11, 14, 15],
    [16, 17, 20, 21, 24, 25, 28, 29],
    [18, 19, 22, 23, 26, 27, 30, 31],
    [32, 33, 36, 37, 40, 41, 44, 45],
    [34, 35, 38, 39, 42, 43, 46, 47],
    [48, 49, 52, 53, 56, 57, 60, 61],
    [50, 51, 54, 55, 58, 59, 62, 63],
]
_COLUMN8_HALF = [
    [0, 4, 16, 20, 32, 36, 48, 52, 2, 6, 18, 22, 34, 38, 50, 54],
    [8, 12, 24, 28, 40, 44, 56, 60, 10, 14, 26, 30, 42, 46, 58, 62],
    [33, 37, 49, 53, 1, 5, 17, 21, 35, 39, 51, 55, 3, 7, 19, 23],
    [41, 45, 57, 61, 9, 13, 25, 29, 43, 47, 59, 63, 11, 15, 27, 31],
    [96, 100, 112, 116, 64, 68, 80, 84, 98, 102, 114, 118, 66, 70, 82, 86],
    [104, 108, 120, 124, 72, 76, 88, 92, 106, 110, 122, 126, 74, 78, 90, 94],
    [65, 69, 81, 85, 97, 101, 113, 117, 67, 71, 83, 87, 99, 103, 115, 119],
    [73, 77, 89, 93, 105, 109, 121, 125, 75, 79, 91, 95, 107, 111, 123, 127],
]
_COLUMN8 = _COLUMN8_HALF + [[v + 128 for v in row] for row in _COLUMN8_HALF]
_COLUMN4_HALF = [
    [
        0,
        8,
        32,
        40,
        64,
        72,
        96,
        104,
        2,
        10,
        34,
        42,
        66,
        74,
        98,
        106,
        4,
        12,
        36,
        44,
        68,
        76,
        100,
        108,
        6,
        14,
        38,
        46,
        70,
        78,
        102,
        110,
    ],
    [
        16,
        24,
        48,
        56,
        80,
        88,
        112,
        120,
        18,
        26,
        50,
        58,
        82,
        90,
        114,
        122,
        20,
        28,
        52,
        60,
        84,
        92,
        116,
        124,
        22,
        30,
        54,
        62,
        86,
        94,
        118,
        126,
    ],
    [
        65,
        73,
        97,
        105,
        1,
        9,
        33,
        41,
        67,
        75,
        99,
        107,
        3,
        11,
        35,
        43,
        69,
        77,
        101,
        109,
        5,
        13,
        37,
        45,
        71,
        79,
        103,
        111,
        7,
        15,
        39,
        47,
    ],
    [
        81,
        89,
        113,
        121,
        17,
        25,
        49,
        57,
        83,
        91,
        115,
        123,
        19,
        27,
        51,
        59,
        85,
        93,
        117,
        125,
        21,
        29,
        53,
        61,
        87,
        95,
        119,
        127,
        23,
        31,
        55,
        63,
    ],
    [
        192,
        200,
        224,
        232,
        128,
        136,
        160,
        168,
        194,
        202,
        226,
        234,
        130,
        138,
        162,
        170,
        196,
        204,
        228,
        236,
        132,
        140,
        164,
        172,
        198,
        206,
        230,
        238,
        134,
        142,
        166,
        174,
    ],
    [
        208,
        216,
        240,
        248,
        144,
        152,
        176,
        184,
        210,
        218,
        242,
        250,
        146,
        154,
        178,
        186,
        212,
        220,
        244,
        252,
        148,
        156,
        180,
        188,
        214,
        222,
        246,
        254,
        150,
        158,
        182,
        190,
    ],
    [
        129,
        137,
        161,
        169,
        193,
        201,
        225,
        233,
        131,
        139,
        163,
        171,
        195,
        203,
        227,
        235,
        133,
        141,
        165,
        173,
        197,
        205,
        229,
        237,
        135,
        143,
        167,
        175,
        199,
        207,
        231,
        239,
    ],
    [
        145,
        153,
        177,
        185,
        209,
        217,
        241,
        249,
        147,
        155,
        179,
        187,
        211,
        219,
        243,
        251,
        149,
        157,
        181,
        189,
        213,
        221,
        245,
        253,
        151,
        159,
        183,
        191,
        215,
        223,
        247,
        255,
    ],
]
_COLUMN4 = _COLUMN4_HALF + [[v + 256 for v in row] for row in _COLUMN4_HALF]


def _tables():
    import numpy as np

    global _NP_TABLES
    if _NP_TABLES is None:
        _NP_TABLES = tuple(
            np.array(t, dtype=np.int64) for t in (_BLOCK32, _BLOCK8, _BLOCK4, _COLUMN32, _COLUMN8, _COLUMN4)
        )
    return _NP_TABLES


_NP_TABLES = None


def _word_address_32(x, y, buffer_width: int):
    """Word of GS memory of PSMCT32 pixels (x, y) (numpy arrays), buffer width in 64-pixel units"""
    block32, _, _, column32, _, _ = _tables()
    page = (y // 32) * buffer_width + x // 64
    return page * 2048 + block32[(y % 32) // 8, (x % 64) // 8] * 64 + column32[y % 8, x % 8]


def _byte_address_8(x, y, buffer_width: int):
    """Byte of GS memory of PSMT8 pixels (x, y) (numpy arrays), buffer width in 64-pixel units (a page is 2 of them
    wide)"""
    _, block8, _, _, column8, _ = _tables()
    page = (y // 64) * (buffer_width // 2) + x // 128
    return page * 8192 + block8[(y % 64) // 16, (x % 128) // 16] * 256 + column8[y % 16, x % 16]


def _nibble_address_4(x, y, buffer_width: int):
    """Nibble of GS memory of PSMT4 pixels (x, y) (numpy arrays), buffer width in 64-pixel units (a page is 2 of them
    wide)"""
    _, _, block4, _, _, column4 = _tables()
    page = (y // 128) * (buffer_width // 2) + x // 128
    return page * 16384 + block4[(y % 128) // 16, (x % 128) // 32] * 512 + column4[y % 16, x % 32]


def unswizzle(data: bytes, width: int, height: int, bits_per_pixel: int) -> bytes:
    """Palette indexes (one byte per pixel, row by row) of a 8-bit or 4-bit texture stored as uploaded to GS memory as
    PSMCT32 (width / 2 x height / 2 for 8-bit, width / 2 x height / 4 for 4-bit pixels) and read back by the GS as
    PSMT8 / PSMT4"""
    import numpy as np

    width32 = width // 2
    height32 = height // 2 if bits_per_pixel == 8 else height // 4
    buffer_width32 = max(1, (width32 + 63) // 64)
    ys, xs = np.mgrid[0:height32, 0:width32]
    addresses = _word_address_32(xs, ys, buffer_width32).reshape(-1) * 4
    memory = np.zeros(int(addresses.max()) + 4 if len(addresses) else 4, dtype=np.uint8)
    words = np.frombuffer(data[: width32 * height32 * 4].ljust(width32 * height32 * 4, b'\0'), dtype=np.uint8)
    for k in range(4):
        memory[addresses + k] = words[k::4]
    buffer_width = max(2, (width + 63) // 64)
    ys, xs = np.mgrid[0:height, 0:width]
    if bits_per_pixel == 8:
        source = _byte_address_8(xs, ys, buffer_width).reshape(-1)
        return memory[np.clip(source, 0, len(memory) - 1)].tobytes()
    nibbles = _nibble_address_4(xs, ys, buffer_width).reshape(-1)
    values = memory[np.clip(nibbles >> 1, 0, len(memory) - 1)]
    return ((values >> ((nibbles & 1) * 4)) & 15).astype(np.uint8).tobytes()


def csm1_index(index: int) -> int:
    """Palette entry of colour index `index` in a 256-colour palette stored in CSM1 order (the GS reads palette entries
    by blocks of 8: entries 8..15 and 16..23 of every 32 are swapped)"""
    return (index & ~0x18) | ((index & 0x08) << 1) | ((index & 0x10) >> 1)


def lfsr_next(r: int) -> int:
    """The VU's RNEXT: next value of the 23-bit R register (left shift, new bit 0 = bit 4 xor bit 22)"""
    return ((r << 1) ^ ((r >> 4) & 1) ^ ((r >> 22) & 1)) & 0x7FFFFF


# VIF UNPACK formats: cmd & 0x0F -> (components, bits per component)
_UNPACK_FORMATS = {
    0x0: (1, 32),
    0x1: (1, 16),
    0x2: (1, 8),
    0x4: (2, 32),
    0x5: (2, 16),
    0x6: (2, 8),
    0x8: (3, 32),
    0x9: (3, 16),
    0xA: (3, 8),
    0xC: (4, 32),
    0xD: (4, 16),
    0xE: (4, 8),
    0xF: (4, 5),
}
# VIF commands which start a VU microprogram: MSCAL, MSCALF, MSCNT
_VIF_MSCAL = (0x14, 0x15, 0x17)


def vif_packets(data: bytes) -> List[Dict[int, List[int]]]:
    """VU memory (qword address -> 4 integer fields) written by the UNPACK commands of a VIF code stream, one dict per
    microprogram call (MSCAL / MSCALF / MSCNT). 32-bit components are kept as raw 32-bit values, 16 and 8-bit ones
    are sign or zero extended (the UNPACK's USN bit), V4-5 colours are expanded to 4 fields of 8 bits (alpha 0 or
    0x80). Addresses ignore the FLG bit (double buffering), only UNPACK, NOP and MSCAL* commands are expected"""
    packets = []
    memory = {}
    i = 0
    while i + 4 <= len(data):
        (code,) = struct.unpack_from('<I', data, i)
        i += 4
        cmd = (code >> 24) & 0x7F
        num = (code >> 16) & 0xFF or 256
        imm = code & 0xFFFF
        if cmd & 0x60 == 0x60:
            components, bits = _UNPACK_FORMATS[cmd & 0x0F]
            # a V4-5 element is 16 bits: RGBA 5551
            element_bits = 16 if bits == 5 else bits * components
            size = (element_bits * num + 31) // 32 * 4
            raw = data[i : i + size]
            i += size
            address = imm & 0x3FF
            unsigned = bool(imm & 0x4000)
            for k in range(num):
                field = memory.setdefault(address + k, [0, 0, 0, 0])
                if bits == 32:
                    values = struct.unpack_from(f'<{components}I', raw, k * 4 * components)
                elif bits == 16:
                    values = struct.unpack_from(f'<{components}{"H" if unsigned else "h"}', raw, k * 2 * components)
                elif bits == 8:
                    values = struct.unpack_from(f'<{components}{"B" if unsigned else "b"}', raw, k * components)
                else:
                    (color,) = struct.unpack_from('<H', raw, k * 2)
                    values = (
                        (color & 31) << 3,
                        ((color >> 5) & 31) << 3,
                        ((color >> 10) & 31) << 3,
                        (color >> 15) << 7,
                    )
                field[: len(values)] = values
        elif cmd in _VIF_MSCAL:
            packets.append(memory)
            memory = {}
    return packets


def as_float(value: int) -> float:
    """IEEE single of a raw 32-bit VU memory field"""
    return struct.unpack('<f', struct.pack('<I', value & 0xFFFFFFFF))[0]

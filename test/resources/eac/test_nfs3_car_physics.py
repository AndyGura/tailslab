import math
import os
import struct
import unittest

from resources.eac.car_specs import Nfs3CarPhysics, _NFS3_CARP_FIELDS
from library.read_blocks import ArrayBlock

# nfs3.exe's carp (0x4ac bytes, the game's struct, little endian) as its parser 0x4b1380 fills it from
# test/samples/nfs3_carp/<car>.txt, dumped by the port of the parser in nfs-web (src/nfs3/nfs3-physics/src/carp.c)
_NFS3_EXE_CARP_DIAB = (
    '000000000020cb440700000007000000060000000000000000000000fa000000fa000000c8000000960000006400000064000000'
    '00000000000000000e010000fa000000c800000096000000640000006400000000000840000000000ad713405c8fc23f295c8f3f'
    'ae47613f7b142e3f0000000000000840000000000ad713405c8fc23f295c8f3fae47613f7b142e3f00000000ced460c300000000'
    'a16774430bd22043a4ffec429336ba425be48f4200000000ced460c300000000a16774430bd22043a4ffec429336ba425be48f42'
    '00000000cdcc4c3f0000000048e17a3fd7a3703fcdcc4c3f6666663fcdcc8c3f00000000cdcc4c3f000000008fc2753f1f856b3f'
    '14ae473fae47613fae47813f000000000000484333337b439a9996436666a3435839b043ae47bd432f5dc9430c82cf4333b3d543'
    '9a19dc430000e1430000e14352b8e143ae47e443b89eea4333b3f843146e0244f6e806449ad90a44cd0c0e440040114400001644'
    '8f0215440a171344e1ba0f4400400b449a9905446666fe439a99f143cdcce4430000d8433333cb436666be439a99b143cdcca443'
    '0000984333338b43cdcc7c43333363439a99494300003043d93d7540d93d754006040000841c0000721cba42721cba420000003f'
    '01000000f6282841bf650e3f10101010101010102020202020202020000080420000004200008041000000410000804000000040'
    '0000803f0000803f00000042000000420000004200000042000000420000004200000042000000429a992940d7a3f03e01000000'
    '000098410000904100000042cdcc5c40b3ef0a3b3333b33e1f85eb3ecdcc4841f500000028000000110000004f01000023000000'
    '12000000000000000000a03f0532b33e0798993e80000000282300000360bc3c6891ed3c14ae473f50df3a3f000000000000a040'
    '370000005f000000960000003333733f7b146e3f6666663f03000000004000000000000000000000000000000000803f00000000'
    '0000803f0000803f0000803f0000803f0000803f898888404c4fb640d1fad540acfde640eb6eed40c012f04010b1f24034e7f340'
    '2530f2404f2fee409adfe8400131e440942ee2409826e340e50ce740a942ed40b8bdf3407ddcf940e1dd0041e9910541801a0941'
    '89390b414fdf0c4109f90b41818e04411754ed40009ecf4016ccb94055cfac4032aea5409744a240126ba14017aaa140228aa140'
    'cb9e9f40a009994010878c40aab97b4003056440709a55409b1e4f401d024e4053914f40240b514074d0504092cc4e4058c64b40'
    'c4cd4840145f46409ce14340028440403e213c4071e53640a12c3140a7b22a40c32a22408603194022c71340abea13401f831640'
    'f67f18400d8d1840bea316404b5a134015530f40ff030b40dc9d06401100024020ebf93ff871ee3f5855e13f679dd53f0456d03f'
    '97add13f5ce6d43f0341d63f6ebfd43f63d5d03fb726cb3f4fc9c33fbed9ba3f22ffb03f3acba63fc4419c3fda3b913f58c7853f'
    '2ee2733f93535b3f90dd413fbb7c273f18440c3f9622e13eb378a93e2a8e633e6b2bd63d00000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
)

_NFS3_EXE_CARP_KNOC = (
    '0300000000409c450700000007000000100000000000000000000000dc000000b40000008c000000640000003c00000000000000'
    '0000000000000000dc000000b40000008c000000640000003c000000000000000000b040000000000000a0409a9939406666e63f'
    '6666a63f0000803f000000000000b040000000000000a0409a9939406666e63f6666a63f0000803f00000000d2dd51c400000000'
    'a7c93e445150dd43fe5d8943526b464353a1184300000000d2dd51c400000000a7c93e445150dd43fe5d8943526b464353a11843'
    '000000000000803f000000006666863f6666863f6666863f6666863f6666863f000000000000803f000000006666863f6666863f'
    '6666863f6666863f6666863f000000000000e0429a990743a4702143f6284043e17a5c439a996143a470674314ae7143cdcc7e43'
    '33338c4366669843d7a3a2431f85ac43e17ab543b81ec0433333ce43f628d34385ebc84314aebe43a470b4433333aa43c3f59f43'
    '8fc2914314ae7f43713d6a43000060438fc255431f854b43ae4741433d0a3743cdcc2c435c8f2243ec5118437b140e430ad70343'
    '3333f34252b8de42713dca428fc2b542ae47a142cdcc8c426666f6406666f640d0020000c0120000b258fa41b258fa4100000000'
    '000000000000b040f9f4283f10101010101010102020202020202020000080420000004200008041000000410000804000000040'
    '0000803f0000803f0000004200000042000000420000004200000042000000420000004200000042000040400266e63e01000000'
    '0000204100000041000080416666e63f6f12033ba470bd3e6dfeff3e000070411801000046000000170000001801000046000000'
    '170000000000000015c8cc3d0532b33e0000003f800000001027000038c0cc3c944f0f3d6666663fcdcc4c3f0000000000000000'
    '2000000030000000500000006a32333f6799193f9fcbcc3e01000000004000000000000000000000000000000000803f00000000'
    '0000803f0000803f0000803f0000803f0000803fe8758640dfa3fc3f328e44407ac7664086ca7540a5316c40eca24e406ff34240'
    '2f164b4014cf514031ea57406ced604010946c40215873405a66734060af7240679d5940f91523405e65f53f1406df3f1920e93f'
    'aa2afe3fffb30740d8470c4016350c4061a60b405917ff3f0134ce3f9b56bc3f7dcac73f9414d03ff222d33f1ec6d03f8848bd3f'
    '4b57a23f5beca23f3084b43f5803be3f1e52c03fa2d1bf3f1e54be3f9581bb3f1cceb83f43e5b53f4016b23f4016b23f00000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
)

_NFS3_CARP_SAMPLES = 'test/samples/nfs3_carp'


def _nfs3_carp_struct(data) -> bytes:
    """The game's carp of parsed data: floats rounded to float32, the camera arm as 16.16, bytes, ints"""
    res = bytearray(0x4AC)
    for name, _, offset, block, _, _ in _NFS3_CARP_FIELDS:
        if offset is None:
            continue
        values = data[name] if isinstance(block, ArrayBlock) else [data[name]]
        for k, v in enumerate(values):
            reader = block.reader
            if reader == 'float':
                struct.pack_into('<f', res, offset + 4 * k, v)
            elif reader == 'fixed':
                f32 = struct.unpack('<f', struct.pack('<f', v))[0]
                struct.pack_into('<i', res, offset + 4 * k, round(f32 * 65536))
            elif reader == 'byte':
                res[offset + k] = v
            else:
                struct.pack_into('<i', res, offset + 4 * k, v)
    return bytes(res)


class TestNfs3CarPhysics(unittest.TestCase):
    def test_all_cars_round_trip(self):
        files = sorted(os.listdir(_NFS3_CARP_SAMPLES))
        self.assertEqual(len(files), 16)
        block = Nfs3CarPhysics()
        for file in files:
            with open(os.path.join(_NFS3_CARP_SAMPLES, file), 'rb') as f:
                raw = f.read()
            data = block.unpack_from_bytes(raw)
            self.assertEqual(block.pack(data), raw, file)
            self.assertEqual(block.estimate_packed_size(data), len(raw), file)

    def test_values_as_the_game_reads_them(self):
        block = Nfs3CarPhysics()
        for car, expected in (('Diab', _NFS3_EXE_CARP_DIAB), ('Knoc', _NFS3_EXE_CARP_KNOC)):
            with open(os.path.join(_NFS3_CARP_SAMPLES, f'{car}.txt'), 'rb') as f:
                data = block.unpack_from_bytes(f.read())
            ours = _nfs3_carp_struct(data)
            game = bytes.fromhex(expected)
            for i in range(0, 0x4AC, 4):
                self.assertEqual(ours[i : i + 4].hex(), game[i : i + 4].hex(), f'{car} carp+0x{i:03x}')

    def test_named_values(self):
        with open(os.path.join(_NFS3_CARP_SAMPLES, 'Diab.txt'), 'rb') as f:
            data = Nfs3CarPhysics().unpack_from_bytes(f.read())
        self.assertEqual(data['serial_number'], 16)
        self.assertEqual(data['mass'], 1625.0)
        self.assertEqual(data['num_gears'], 7)
        self.assertEqual(data['redline'], 7300)
        self.assertEqual(data['slide_assist'], 128)  # `128.000000` read as an integer
        self.assertEqual(data['abs'], 1)
        self.assertEqual(data['tire_rear'], [335, 35, 18])
        self.assertEqual(len(data['torque']), 41)
        self.assertEqual(data['torque'][1], 251.199997)
        self.assertEqual(data['ai_acc0'][0], 4.266667)
        self.assertEqual(len(data['ai_acc7']), 14)

    def test_edits_keep_the_file_style(self):
        block = Nfs3CarPhysics()
        with open(os.path.join(_NFS3_CARP_SAMPLES, 'Diab.txt'), 'rb') as f:
            raw = f.read()
        data = block.unpack_from_bytes(raw)
        data['mass'] = 1700
        data['torque'][3] = 330.25
        data['slide_assist'] = 100
        data['camera_arm'] = 0.3
        out = block.pack(data)
        expected = (
            raw.replace(b'\r\n1625.000000\r\n', b'\r\n1700.000000\r\n')
            .replace(b',326.799988,', b',330.250000,')
            .replace(b'Factor(41)\r\n128.000000\r\n', b'Factor(41)\r\n100.000000\r\n')
            .replace(b'arm(56)\r\n0.250000\r\n', b'arm(56)\r\n0.300000\r\n')
        )
        self.assertEqual(out, expected)
        again = block.unpack_from_bytes(out)
        self.assertEqual((again['mass'], again['torque'][3], again['slide_assist']), (1700.0, 330.25, 100))

    def test_missing_fields_take_the_game_defaults(self):
        block = Nfs3CarPhysics()
        with open(os.path.join(_NFS3_CARP_SAMPLES, 'Diab.txt'), 'rb') as f:
            raw = f.read()
        cut = raw.replace(b'wheel base(24)\r\n2.650000\r\n', b'')
        data = block.unpack_from_bytes(cut)
        self.assertEqual(data['wheel_base'], 2.5)
        self.assertEqual(block.pack(data), cut)
        data['wheel_base'] = 2.7
        again = block.unpack_from_bytes(block.pack(data))
        self.assertEqual(again['wheel_base'], 2.7)

    def test_game_parser_rules(self):
        block = Nfs3CarPhysics()
        text = (
            b'MASS [KG] (2)\r\n'  # spaces removed, letters lower-cased
            b'1200.5\r\n'
            b'mass [kg](2)\r\n'  # a field already read keeps its first value
            b'999\r\n'
            b'nothing(99)\r\n'  # selects nothing: the next value line is skipped
            b'7\r\n'
            b'engine redline in rpm(13)\r\n'
            b'\r\n\r\n'  # empty lines are skipped
            b'6500.9,0,0,0,0,0,0,0,0,0,0,44,55\r\n'  # an integer reader stops at the '.'
            b'shiftbli(5)\r\n'
            b'1,2,3\r\n'  # too short: the other numbers come from the line buffer (the label's '5')
        )
        data = block.unpack_from_bytes(text)
        self.assertEqual(data['mass'], 1200.5)
        self.assertEqual(data['redline'], 6500)
        self.assertEqual(data['shift_blip'], [1, 2, 3, 0, 0, 0, 5, 0])
        self.assertEqual(data['num_gears'], 8)  # missing: the default carp's
        self.assertEqual(block.pack(data), text)

    def test_new_file(self):
        block = Nfs3CarPhysics()
        data = block.new_data()
        raw = block.pack(data)
        self.assertTrue(
            raw.startswith(b'Serial Number(0)\r\n0\r\nCar Classification(1)\r\n0\r\nmass [kg](2)\r\n1000.000000')
        )
        again = block.unpack_from_bytes(raw)
        for name, value in data.items():
            if name != 'source_text':
                self.assertTrue(
                    value == again[name] or all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(value, again[name])),
                    name,
                )

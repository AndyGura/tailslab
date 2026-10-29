import math
import os
import struct
import unittest
from io import BytesIO

from library.read_blocks import ArrayBlock
from resources.eac.car_specs import Nfs4CarPhysics, _NFS4_CARP_FIELDS

# nfs4.exe's carp (0x464 bytes, the game's struct, little endian) as its parser 0x503480 fills it from
# test/samples/nfs4_carp/<car>.txt, dumped by the port of the parser for nfs-web (nfs4 carp.c, Carp_Parse)
_NFS4_EXE_CARP_B911 = (
    '2a0000000000000000609f4408000000080000000400000000000000000000002c010000fa000000c80000009600000064000000'
    '3200000000000000000000002c010000fa000000c80000009600000064000000320000006edb364000000000185d74409a990940'
    '9a99b93f7b148e3f1f856b3f6666263f6edb364000000000185d74409a9909409a99b93f7b148e3f1f856b3f6666263ffb9895c3'
    '00000000b2eac743f524614370d717438379e84283aec04241228842fb9895c300000000b2eac743f524614370d717438379e842'
    '83aec04241228842cdcc4c3f00000000d7a3703fd7a3703fcdcc8c3fcdcc8c3fcdcc8c3f0000a03fcdcc4c3f00000000ae47613f'
    'ae47613f6666663f0000803f0000803f0000a03f0000000000004d4300007043008089430080ac430080e3430000fa4300400344'
    '00c005440000074400c000440000fa430080e3430000cd430000b44300009b430000000000000000000000000000000000000000'
    'c5715c40c5715c40cf03000064190000342eba42342eba420000000001000000cdcc3c41986e223f101010101010101020202020'
    '202020200000804200000042000080410000004100008040000000400000803f0000803f00000042000000420000004200000042'
    '00000042000000420000004200000042736811406666e63e01000000cdcc92410000804100000042b81e75400000803fa67b1d3b'
    'e17ad43e8fc2d53e00003041e100000028000000120000001d0100001e00000012000000000000000399193f03cccc3ecdcccc3e'
    '96000000282300006380c43c76c0f53c7b142e3f0b0a173f01000000000000006400000096000000aa00000048e17a3f3333733f'
    '6666663f030000000000803e0000000000000000000000000000803f000000000000803f0000803f6154803f0000803f0000803f'
    '8c2eba400894f4405dfb0c419c0f16417baa1a4104be1e41bd38224117222341c18521412f4920413edb2041cda91f4130351741'
    'a5e007417441f340912ce640cd30e740390eee40e7f1f440c4ddf940edd6fc407f75fe40dfa5fe40438cfa409efeed400ecdda40'
    'dd51c940e71abf404c27bb4054c3ba40f1d7bc40c9aec040b7d3c440351bc84065d6c9400f43c9401775c54014aebc40d6d4ae40'
    'ccb2a0405d5e9740f828934080d89140f5b091406ada9140850792404e26924020fe91406f37904089798a406dbc804045f26d40'
    '240b62406adf5d4063085d4009545c4081ea5a4046965840ab415540e9ee4f4082e44540c22f37406f67294096952140e84b1f40'
    '5a461f405b281f40410e1e4023db1b40f9db18404b3b1540b70a114004ac0c406d540840d9eb0340ddebfe3fe9d2f53fab5cec3f'
    '95b6e23f57ebd83f62a3ce3f8aacc33f9df1b73f0553ab3f39ef9d3f7920903f2524823f79e8673f64cf4a3f3eed2c3f8cba0e3f'
    'e659e13eaa7ea53e94164e3e00000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
)

_NFS4_EXE_CARP_TRAFFIC_BUS = (
    '000000000000000000e0124607000000070000001000000000000000000000002c010000fa000000c8000000960000007d000000'
    '0000000000000000000000002c010000fa000000c8000000960000007d0000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004341cac3'
    '000000004666f04300809d4300005c4323e616431699dc42000000004341cac3000000004666f04300809d4300005c4323e61643'
    '1699dc42000000000000803f0000803f0000803f0000803f0000803f0000803f0000803f0000803f0000803f0000803f0000803f'
    '0000803f0000803f0000803f0000803f0000803f00000000000007430000874300009e430080a7430000ae430080c4430080c443'
    '0000c3430080c4430080bb430000b5430000aa430080984300008243000000000000000000000000000000000000000000000000'
    '0000804000008040390300007c150000a3d13242a3d132420000003f000000000000d0400000003f101010101010101020202020'
    '202020200000804200000042000080410000004100008040000000400000803f0000803f00000042000000420000004200000042'
    '00000042000000420000004200000042333343400266e63e0100000000006041000020410000a041cdcc2c400ad7833fa69bc43a'
    '03cccc3e0399193f0000c841ff0000004600000010000000ff0000004600000010000000000000000000803f0399193f0000803f'
    '800000001027000038c0cc3c944f0f3d0000803f0000803f00000000000000004000000060000000a000000003cc4c3f0133333f'
    '0399193f030000000000803e0000000000000000000000000000803f000000000000803f0000803f0000803f0000803f0000803f'
    'cd3d4d40e3c52940c18e3540c66b4840662f6840ebb6854095bb9e40a4fcb540b7b5c240a89bc840bbd0d0406402e1401295f040'
    'a5f8df4044c0ab4071908940329c8740221b8a400baa8c400aad8240b4223d40bd8ef03f2f17b33fc8969b3f9dbc963f89ec973f'
    '399b983f52639a3f95f49e3f6f64a23f172da43f3753a73f18cfaa3f17f5ab3fe482ab3feb53aa3f4912a83faaf0a53fdc11a43f'
    'c6a8a13f68e99e3f00739b3fc807973f000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000000000000000000000000000000000'
)

_NFS4_CARP_SAMPLES = 'test/samples/nfs4_carp'


def _nfs4_carp_struct(data) -> bytes:
    """The game's carp of parsed data: floats rounded to float32, bytes, ints"""
    res = bytearray(0x464)
    for name, _, offset, block, _, _ in _NFS4_CARP_FIELDS:
        values = data[name] if isinstance(block, ArrayBlock) else [data[name]]
        for k, v in enumerate(values):
            if block.reader == 'float':
                struct.pack_into('<f', res, offset + 4 * k, v)
            elif block.reader == 'byte':
                res[offset + k] = v
            else:
                struct.pack_into('<i', res, offset + 4 * k, v)
    return bytes(res)


def _read(file: str) -> bytes:
    with open(os.path.join(_NFS4_CARP_SAMPLES, file), 'rb') as f:
        return f.read()


class TestNfs4CarPhysics(unittest.TestCase):
    def test_samples_round_trip(self):
        files = sorted(os.listdir(_NFS4_CARP_SAMPLES))
        self.assertEqual(len(files), 6)
        block = Nfs4CarPhysics()
        for file in files:
            raw = _read(file)
            data = block.unpack_from_bytes(raw)
            self.assertEqual(block.pack(data), raw, file)
            self.assertEqual(block.estimate_packed_size(data), len(raw), file)

    def test_values_as_the_game_reads_them(self):
        block = Nfs4CarPhysics()
        for car, expected in (('B911', _NFS4_EXE_CARP_B911), ('traffic_bus', _NFS4_EXE_CARP_TRAFFIC_BUS)):
            data = block.unpack_from_bytes(_read(f'{car}.txt'))
            ours = _nfs4_carp_struct(data)
            game = bytes.fromhex(expected)
            for i in range(0, 0x464, 4):
                self.assertEqual(ours[i : i + 4].hex(), game[i : i + 4].hex(), f'{car} carp+0x{i:03x}')

    def test_named_values(self):
        data = Nfs4CarPhysics().unpack_from_bytes(_read('B911.txt'))
        self.assertEqual(data['serial_number'], 42)
        self.assertEqual(data['mass'], 1275.0)
        self.assertEqual(data['num_gears'], 8)
        self.assertEqual(data['redline'], 6500)
        self.assertEqual(data['abs'], 1)
        self.assertEqual(len(data['torque']), 21)
        self.assertEqual(data['torque'][1], 205.0)
        self.assertEqual(data['understeer_gradient'], 1.0)
        self.assertEqual(data['camera_arm'], 0.25)
        bus = Nfs4CarPhysics().unpack_from_bytes(_read('traffic_bus.txt'))
        self.assertEqual(bus['slide_assist'], 128)  # `128.000000` read with "%d"

    def test_loader_should_pick_nfs4_carp_by_path(self):
        from library.loader import probe_block_class

        raw = _read('B911.txt')
        for path in ('games/nfs4/Data/Cars/B911/car.viv__0_carp.txt', 'Data/Cars/Bmw5/car.viv__3_carp1.txt'):
            self.assertEqual(probe_block_class(BytesIO(raw), path, len(raw)).__name__, 'Nfs4CarPhysics', path)
        nfs3 = probe_block_class(BytesIO(raw), 'GameData/CarModel/Diab/car.viv__0_carp.txt', len(raw))
        self.assertEqual(nfs3.__name__, 'Nfs3CarPhysics')

    def test_edits_keep_the_file_style(self):
        block = Nfs4CarPhysics()
        raw = _read('B911.txt')
        data = block.unpack_from_bytes(raw)
        data['mass'] = 1300
        data['torque'][2] = 250.5
        data['understeer_gradient'] = 0.95
        data['tire_front'] = [235, 40, 18]
        out = block.pack(data)
        expected = (
            raw.replace(b'\r\n1275.000000\r\n', b'\r\n1300.000000\r\n')
            .replace(b'205.000000,240.000000,', b'205.000000,250.500000,')
            .replace(b'gradient(80)\r\n1.000000\r\n', b'gradient(80)\r\n0.950000\r\n')
            .replace(b'tire specs front(35)\r\n225,40,18', b'tire specs front(35)\r\n235,40,18')
        )
        self.assertNotEqual(out, raw)
        self.assertEqual(out, expected)
        again = block.unpack_from_bytes(out)
        self.assertEqual((again['mass'], again['torque'][2], again['understeer_gradient']), (1300.0, 250.5, 0.95))

    def test_missing_fields_take_the_game_defaults(self):
        block = Nfs4CarPhysics()
        raw = _read('B911.txt')
        cut = raw.replace(b'understeer gradient(80)\r\n1.000000\r\n', b'').replace(
            b'Car Classification(1)\r\n0\r\n', b''
        )
        data = block.unpack_from_bytes(cut)
        self.assertEqual((data['understeer_gradient'], data['car_class']), (1.0, 0))
        self.assertEqual(block.pack(data), cut)
        data['understeer_gradient'] = 1.05
        again = block.unpack_from_bytes(block.pack(data))
        self.assertEqual(again['understeer_gradient'], 1.05)

    def test_game_parser_rules(self):
        block = Nfs4CarPhysics()
        text = (
            b'MASS [KG] (2)\r\n'  # spaces removed, letters lower-cased; only the "(n)" is looked for
            b'1200.5\r\n'
            b'whatever(13)\r\n'
            b'6500.9\r\n'  # "%d" stops at the '.'
            b'nothing(99)\r\n'  # matches no field: skipped, the next line too as it matches nothing
            b'7\r\n'
            b'shift blip(5)\r\n'
            b'\r\n\r\n'  # empty lines are skipped
            b'1, 2,,\t3,x,9\r\n'  # ", " and tabs separate, empty items skipped, "x" ends the line
            b'mass [kg](2)\r\n'  # read again: the later values
            b'1300\r\n'
            b'final gear(11)\r\n'
            b'gear shift delay(4)\r\n'  # the line after a label is its value line, whatever it holds
            b'5\r\n'
        )
        data = block.unpack_from_bytes(text)
        self.assertEqual(data['mass'], 1300.0)
        self.assertEqual(data['redline'], 6500)
        self.assertEqual(data['shift_blip'], [1, 2, 3, 250, 200, 175, 150, 0])  # the rest: the default carp's
        self.assertEqual(data['final_gear'], 4.0)
        self.assertEqual(data['shift_delay'], 8)  # its label was the value line of (11): never selected
        self.assertEqual(data['num_gears'], 8)
        self.assertEqual(block.pack(data), text)

    def test_new_file(self):
        block = Nfs4CarPhysics()
        data = block.new_data()
        raw = block.pack(data)
        self.assertTrue(raw.startswith(b'Serial Number(0)\r\n0\r\nCar Classification(1)\r\n0\r\nmass [kg](2)'))
        self.assertIn(b'torque curve (size 21) in 500 rpm increments(10)\r\n10.000000,20.000000', raw)
        again = block.unpack_from_bytes(raw)
        for name, value in data.items():
            if name != 'source_text':
                self.assertTrue(
                    value == again[name] or all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(value, again[name])),
                    name,
                )

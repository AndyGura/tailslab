import math
import struct
import unittest
from io import BytesIO

from library.context import ReadContext
from library.exceptions import DataIntegrityException, EndOfBufferException, IntegerOutOfRangeException
from library.read_blocks import (
    ArrayBlock,
    BitFlagsBlock,
    BytesBlock,
    CompoundBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    EnumByteBlock,
    FixedPointBlock,
    IntegerBlock,
)
from library.read_blocks.misc.value_validators import Eq
from resources.eac.fields.byte_order import big_endian_copy
from resources.eac.fields.misc import Point3D
from resources.eac.fields.numbers import Nfs1Angle8


class Vertex(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        position = Point3D(child=DecimalBlock(length=4))
        uv = ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True), length=2)
        kind = EnumByteBlock(enum_names=[(0, 'plain'), (1, 'lit')])
        flags = BitFlagsBlock(length=1, flag_names=[(0, 'visible'), (7, 'last')])
        angle = Nfs1Angle8()
        index = IntegerBlock(length=2, is_signed=True)
        ui_only = (IntegerBlock(length=4), {'usage': 'ui'})


VERTEX_BYTES = struct.pack('<3f2hBBBh', 1.5, -2.0, 0.25, 0x180, -0x40, 1, 0x81, 64, -7)
VERTEX = {
    'position': {'x': 1.5, 'y': -2.0, 'z': 0.25},
    'uv': [1.5, -0.25],
    'kind': 'lit',
    'flags': {
        'last': True,
        '6': False,
        '5': False,
        '4': False,
        '3': False,
        '2': False,
        '1': False,
        'visible': True,
    },
    'angle': math.pi / 2,
    'index': -7,
}


def read(block, raw: bytes):
    return block.unpack(ReadContext(BytesIO(raw), read_bytes_amount=len(raw)), read_bytes_amount=len(raw))


class TestStructRecord(unittest.TestCase):
    def test_record_of_number_leaves_is_one_struct(self):
        block = Vertex()
        self.assertEqual(block.struct_format, ('<', 'fffhhBBBh'))
        self.assertEqual(block.fixed_size, len(VERTEX_BYTES))
        self.assertIsNotNone(block.struct_record)

    def test_read_and_write(self):
        block = Vertex()
        self.assertEqual(read(block, VERTEX_BYTES), VERTEX)
        self.assertEqual(block.pack(VERTEX), VERTEX_BYTES)
        self.assertEqual(block.estimate_packed_size(VERTEX), len(VERTEX_BYTES))

    def test_array_of_records(self):
        block = ArrayBlock(child=Vertex(), length=lambda ctx: 3)
        self.assertIsNone(block.struct_format)
        self.assertEqual(read(block, VERTEX_BYTES * 3), [VERTEX] * 3)
        self.assertEqual(block.pack([VERTEX] * 3), VERTEX_BYTES * 3)
        self.assertEqual(block.estimate_packed_size([VERTEX] * 5), len(VERTEX_BYTES) * 5)

    def test_array_of_numbers(self):
        block = ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=3)
        self.assertEqual(read(block, bytes([0, 1, 0, 2, 1, 0])), [1, 2, 256])
        self.assertEqual(block.pack([1, 2, 256]), bytes([0, 1, 0, 2, 1, 0]))

    def test_end_of_buffer_raises_with_context(self):
        with self.assertRaises(EndOfBufferException) as ex:
            read(Vertex(), VERTEX_BYTES[:-1])
        self.assertIsNotNone(ex.exception.ctx_path)

    def test_value_out_of_range_raises_from_field(self):
        with self.assertRaises(IntegerOutOfRangeException) as ex:
            Vertex().pack({**VERTEX, 'index': 40000})
        self.assertIn('index = 40000', str(ex.exception))

    def test_wrong_array_length_writes_as_given(self):
        block = Vertex()
        data = {**VERTEX, 'uv': [1.5, -0.25, 1.0]}
        self.assertEqual(len(block.pack(data)), len(VERTEX_BYTES) + 2)

    def test_mixed_byte_orders_have_no_struct_format(self):
        block = CompoundBlock(
            fields=[
                ('a', IntegerBlock(length=2, byte_order='big'), {}),
                ('b', IntegerBlock(length=2), {}),
                ('c', IntegerBlock(length=1), {}),
            ]
        )
        self.assertIsNone(block.struct_format)
        self.assertEqual(block.fixed_size, 5)
        self.assertEqual(read(block, bytes([0, 1, 1, 0, 9])), {'a': 1, 'b': 1, 'c': 9})

    def test_validated_field_is_read_field_by_field(self):
        block = CompoundBlock(fields=[('magic', IntegerBlock(length=2, value_validator=Eq(7)), {})])
        self.assertIsNone(block.struct_format)
        self.assertEqual(read(block, bytes([7, 0])), {'magic': 7})
        with self.assertRaises(DataIntegrityException):
            read(block, bytes([8, 0]))

    def test_programmatic_field_is_written_field_by_field(self):
        block = CompoundBlock(
            fields=[
                ('count', IntegerBlock(length=1, programmatic_value=lambda ctx: len(ctx.data('items'))), {}),
                ('items', ArrayBlock(child=IntegerBlock(length=1), length=2), {}),
            ]
        )
        self.assertIsNone(block.struct_format)
        self.assertEqual(block.fixed_size, 3)
        self.assertEqual(block.pack({'count': 0, 'items': [4, 5]}), bytes([2, 4, 5]))

    def test_bytes_and_overridden_read_have_no_fixed_size(self):
        class CustomRead(CompoundBlock):
            def read(self, ctx, name='', read_bytes_amount=None):
                return super().read(ctx, name, read_bytes_amount)

        self.assertIsNone(CompoundBlock(fields=[('raw', BytesBlock(length=4), {})]).fixed_size)
        block = CustomRead(fields=[('a', IntegerBlock(length=4), {})])
        self.assertIsNone(block.fixed_size)
        self.assertIsNone(block.struct_format)

    def test_normalized_point_is_written_field_by_field(self):
        block = Point3D(child=DecimalBlock(length=4), normalized=True)
        self.assertIsNone(block.struct_format)
        self.assertEqual(block.pack({'x': 0.0, 'y': 0.0, 'z': 2.0}), struct.pack('<3f', 0, 0, 1))
        self.assertIsNotNone(Point3D(child=DecimalBlock(length=4)).struct_format)

    def test_big_endian_copy_of_a_used_block(self):
        block = Vertex()
        self.assertEqual(read(block, VERTEX_BYTES), VERTEX)
        copy = big_endian_copy(block)
        self.assertEqual(copy.struct_format[0], '>')
        raw = struct.pack('>3f2hBBBh', 1.5, -2.0, 0.25, 0x180, -0x40, 1, 0x81, 64, -7)
        self.assertEqual(read(copy, raw), VERTEX)
        self.assertEqual(copy.pack(VERTEX), raw)
        self.assertEqual(block.pack(VERTEX), VERTEX_BYTES)


class TestRawConversions(unittest.TestCase):
    def test_fixed_point(self):
        block = FixedPointBlock(length=2, fraction_bits=8, is_signed=True)
        self.assertEqual(block.from_raw(-0x40), -0.25)
        self.assertEqual(block.to_raw(-0.25), -0x40)
        self.assertEqual(block.to_raw(1000.0), 0x7FFF)

    def test_enum(self):
        block = EnumByteBlock(enum_names=[(3, 'three')])
        self.assertEqual(block.from_raw(3), 'three')
        self.assertEqual(block.from_raw(4), '4')
        self.assertEqual(block.to_raw('three'), 3)

    def test_angle(self):
        block = Nfs1Angle8()
        self.assertEqual(block.from_raw(64), math.pi / 2)
        self.assertEqual(block.to_raw(-math.pi / 2), 192)


if __name__ == '__main__':
    unittest.main()

import unittest
from io import BytesIO

from library.context import ReadContext
from library.exceptions import DataIntegrityException
from library.read_blocks import REMAINING, UTF8Block
from library.read_blocks.array import ArrayBlock, LengthPrefixedArrayBlock, SubByteArrayBlock
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.numbers import IntegerBlock


class TestArray(unittest.TestCase):
    def test_byte_length(self):
        item = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        field = ArrayBlock(child=item, byte_length=(lambda ctx: 5, 'five bytes'))
        val = field.unpack(ReadContext(BytesIO(bytes([2, 7, 8, 1, 9, 99]))))
        self.assertEqual(val, [[7, 8], [9]])
        self.assertEqual(field.pack(val), bytes([2, 7, 8, 1, 9]))
        self.assertEqual((field.length_doc_str, field.size_doc_str), ('five bytes', 'five bytes'))
        self.assertNotIn('length', field.schema)
        self.assertEqual(field.new_data(), [])

    def test_byte_length_items_past_it(self):
        item = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        field = ArrayBlock(child=item, byte_length=4)
        with self.assertRaises(DataIntegrityException):
            field.unpack(ReadContext(BytesIO(bytes([2, 7, 8, 1, 9]))))

    def test_byte_length_fixed_size_items(self):
        # as many as fit, the rest stays for the next field
        field = ArrayBlock(child=IntegerBlock(length=2), byte_length=(REMAINING, 'rest'))
        buffer = BytesIO(bytes([1, 0, 2, 0, 3, 99, 99]))
        self.assertEqual(field.unpack(ReadContext(buffer), read_bytes_amount=5), [1, 2])
        self.assertEqual(buffer.tell(), 4)
        self.assertEqual((field.length_doc_str, field.size_doc_str), ('rest / 2', 'rest'))

    def test_stop_after(self):
        field = ArrayBlock(child=IntegerBlock(length=1), stop_after=(lambda item: item == 0xFF, 'up to 0xFF'))
        self.assertEqual(field.unpack(ReadContext(BytesIO(bytes([4, 5, 0xFF, 6])))), [4, 5, 0xFF])
        # no terminator: up to the end of the bytes it may read
        self.assertEqual(field.unpack(ReadContext(BytesIO(bytes([4, 5, 6, 7]))), read_bytes_amount=3), [4, 5, 6])
        self.assertEqual(field.pack([4, 5, 0xFF]), bytes([4, 5, 0xFF]))
        self.assertEqual((field.length_doc_str, field.size_doc_str), ('up to 0xFF', 'up to 0xFF'))
        self.assertNotIn('length', field.schema)

    def test_stop_before(self):
        field = ArrayBlock(
            child=IntegerBlock(length=2),
            stop_before=(lambda ctx: ctx.peek(2) == b'\xff\xff', 'up to 0xFFFF'),
        )
        buffer = BytesIO(bytes([1, 0, 2, 0, 0xFF, 0xFF, 3, 0]))
        self.assertEqual(field.unpack(ReadContext(buffer)), [1, 2])
        self.assertEqual(buffer.tell(), 4)
        self.assertEqual((field.length_doc_str, field.size_doc_str), ('up to 0xFFFF', 'up to 0xFFFF*2'))

    def test_read_end(self):
        buffer = BytesIO(bytes(10))
        ctx = ReadContext(buffer)
        self.assertEqual(ctx.read_end, 10)
        buffer.seek(2)
        child = ctx.get_or_create_child('a', read_bytes_amount=5)
        self.assertEqual(child.get_or_create_child('b').read_end, 7)
        buffer.seek(6)
        self.assertEqual(child.peek(4), bytes(1))
        self.assertEqual(buffer.tell(), 6)

    def test_array_unpack(self):
        field = ArrayBlock(length=3, child=IntegerBlock(length=1))
        val = field.unpack(ReadContext(BytesIO(bytes([92, 129, 13]))))
        self.assertListEqual(val, [92, 129, 13])

    def test_array_pack(self):
        field = ArrayBlock(length=3, child=IntegerBlock(length=1))
        data = field.pack([92, 129, 13])
        self.assertEqual(data, bytes([92, 129, 13]))

    def test_array_value_validator(self):
        field = ArrayBlock(length=3, child=IntegerBlock(length=1), value_validator=Eq([10, 20, 30]))
        field.unpack(ReadContext(buffer=BytesIO(bytes([10, 20, 30]))))
        with self.assertRaises(DataIntegrityException):
            field.unpack(ReadContext(BytesIO(bytes([90, 12, 30]))))

    def test_get_child_block_with_data(self):
        child_block = IntegerBlock(length=1)
        field = ArrayBlock(length=3, child=child_block)
        block, data = field.get_child_block_with_data([123, 456, 789], '1')
        self.assertEqual(block, child_block)
        self.assertEqual(data, 456)

    def test_estimate_packed_size(self):
        field = ArrayBlock(length=3, child=IntegerBlock(length=3))
        self.assertEqual(field.estimate_packed_size([1, 2, 3]), 9)

    def test_estimate_packed_size_variable_child_length(self):
        field = ArrayBlock(length=3, child=UTF8Block(length=lambda ctx: exec('raise Exception()')))
        self.assertEqual(field.estimate_packed_size(['abc', '0', 'qwerty']), 10)

    def test_offset_to_child_when_packed(self):
        field = ArrayBlock(length=3, child=UTF8Block(length=lambda ctx: exec('raise Exception()')))
        self.assertEqual(field.offset_to_child_when_packed(['abc', '0', 'qwerty'], '1'), 3)

    def test_size_doc_str(self):
        field = ArrayBlock(length=3, child=IntegerBlock(length=1))
        self.assertEqual(field.size_doc_str, '3')
        field = ArrayBlock(length=3, child=IntegerBlock(length=2))
        self.assertEqual(field.size_doc_str, '6')
        field = ArrayBlock(length=lambda ctx: 5, child=IntegerBlock(length=1))
        self.assertEqual(field.size_doc_str, '5')
        field = ArrayBlock(length=(2, '2 items'), child=IntegerBlock(length=4))
        self.assertEqual(field.size_doc_str, '2 items*4')


class TestLengthPrefixedArray(unittest.TestCase):
    def test_array_unpack(self):
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        val = field.unpack(ReadContext(BytesIO(bytes([3, 92, 129, 13, 252]))))
        self.assertListEqual(val, [92, 129, 13])

    def test_array_unpack_different_length_block(self):
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=4, byte_order='big'), child=IntegerBlock(length=1)
        )
        self.assertListEqual(field.unpack(ReadContext(BytesIO(bytes([0, 0, 0, 2, 92, 129, 254])))), [92, 129])
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=4, byte_order='little'), child=IntegerBlock(length=1)
        )
        self.assertListEqual(field.unpack(ReadContext(BytesIO(bytes([2, 0, 0, 0, 92, 129, 254])))), [92, 129])
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=3, byte_order='big'), child=IntegerBlock(length=1)
        )
        self.assertListEqual(field.unpack(ReadContext(BytesIO(bytes([0, 0, 3, 92, 129, 254, 127])))), [92, 129, 254])

    def test_array_pack(self):
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        data = field.pack([92, 129, 13])
        self.assertEqual(data, bytes([3, 92, 129, 13]))

    def test_array_pack_different_length_block(self):
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=4, byte_order='big'), child=IntegerBlock(length=1)
        )
        self.assertEqual(field.pack([92, 129]), bytes([0, 0, 0, 2, 92, 129]))
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=4, byte_order='little'), child=IntegerBlock(length=1)
        )
        self.assertEqual(field.pack([92, 129]), bytes([2, 0, 0, 0, 92, 129]))
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=3, byte_order='big'), child=IntegerBlock(length=1)
        )
        self.assertEqual(field.pack([92, 129, 13, 12, 15]), bytes([0, 0, 5, 92, 129, 13, 12, 15]))

    def test_array_value_validator(self):
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=1), child=IntegerBlock(length=1), value_validator=Eq([10, 20, 30])
        )
        field.unpack(ReadContext(BytesIO(bytes([3, 10, 20, 30]))))
        with self.assertRaises(DataIntegrityException):
            field.unpack(ReadContext(BytesIO(bytes([3, 90, 12, 30]))))

    def test_get_child_block_with_data(self):
        child_block = IntegerBlock(length=1)
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=child_block)
        block, data = field.get_child_block_with_data([123, 456, 789], '1')
        self.assertEqual(block, child_block)
        self.assertEqual(data, 456)

    def test_estimate_packed_size(self):
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=3))
        self.assertEqual(field.estimate_packed_size([1, 2, 3]), 10)
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=4), child=IntegerBlock(length=3))
        self.assertEqual(field.estimate_packed_size([1, 2, 3]), 13)

    def test_estimate_packed_size_variable_child_length(self):
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=1), child=UTF8Block(length=lambda ctx: exec('raise Exception()'))
        )
        self.assertEqual(field.estimate_packed_size(['abc', '0', 'qwerty']), 11)

    def test_offset_to_child_when_packed(self):
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=1), child=UTF8Block(length=lambda ctx: exec('raise Exception()'))
        )
        self.assertEqual(field.offset_to_child_when_packed(['abc', '0', 'qwerty'], '1'), 4)
        field = LengthPrefixedArrayBlock(
            length_block=IntegerBlock(length=4), child=UTF8Block(length=lambda ctx: exec('raise Exception()'))
        )
        self.assertEqual(field.offset_to_child_when_packed(['abc', '0', 'qwerty'], '1'), 7)

    def test_new_data(self):
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        self.assertEqual(field.new_data(), [])
        self.assertEqual(field.pack(field.new_data()), bytes([0]))

    def test_size_doc_str(self):
        field = LengthPrefixedArrayBlock(length_block=IntegerBlock(length=1), child=IntegerBlock(length=1))
        self.assertEqual(field.size_doc_str, '1..?')


class TestSubByteArray(unittest.TestCase):
    def test_subbyte_array_unpack(self):
        field = SubByteArrayBlock(length=4, bits_per_value=6)
        val = field.unpack(ReadContext(BytesIO(bytes([253, 253, 253]))))
        self.assertListEqual(val, [63, 31, 55, 61])

    def test_subbyte_array_pack(self):
        field = SubByteArrayBlock(length=4, bits_per_value=6)
        data = field.pack([63, 31, 55, 61])
        self.assertEqual(data, bytes([253, 253, 253]))

    def test_subbyte_array_unpack_padding(self):
        field = SubByteArrayBlock(length=5, bits_per_value=5)
        val = field.unpack(ReadContext(BytesIO(bytes([255, 255, 255, 128]))))
        self.assertListEqual(val, [31, 31, 31, 31, 31])

    def test_subbyte_array_pack_padding(self):
        field = SubByteArrayBlock(length=5, bits_per_value=5)
        data = field.pack([31, 31, 31, 31, 31])
        self.assertEqual(data, bytes([255, 255, 255, 128]))

    def test_get_child_block_with_data(self):
        field = SubByteArrayBlock(length=5, bits_per_value=5)
        block, data = field.get_child_block_with_data([29, 26, 13], '1')
        self.assertIsNone(block)
        self.assertEqual(data, 26)

    def test_estimate_packed_size(self):
        field = SubByteArrayBlock(length=5, bits_per_value=5)
        self.assertEqual(field.estimate_packed_size([1, 2, 3]), 2)

    def test_size_doc_str(self):
        field = SubByteArrayBlock(length=4, bits_per_value=6)
        self.assertEqual(field.size_doc_str, '3')
        field = SubByteArrayBlock(length=5, bits_per_value=5)
        self.assertEqual(field.size_doc_str, '4')

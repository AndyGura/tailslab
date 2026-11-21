import unittest
from copy import deepcopy
from io import BytesIO

from library.context import ReadContext, WriteContext
from library.exceptions import IntegerOutOfRangeException
from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    CompoundBlock,
    CountOf,
    DeclarativeCompoundBlock,
    IntegerBlock,
    OffsetOf,
    OwnSize,
    Padding,
    SizeOf,
    UTF8Block,
)
from library.read_blocks.references import is_static_param, param_doc, param_value


class Header(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        size = IntegerBlock(length=4, programmatic_value=OwnSize())
        num_items = IntegerBlock(length=1, programmatic_value=CountOf('items'))
        items_ptr = IntegerBlock(length=2, programmatic_value=OffsetOf('items'))
        name_size = IntegerBlock(length=1, programmatic_value=CountOf('name'))
        rest_size = IntegerBlock(length=2, programmatic_value=SizeOf('name', 'items') + 2)
        name = UTF8Block(length='name_size')
        pad = Padding(to='items_ptr')
        items = ArrayBlock(child=IntegerBlock(length=2), length='num_items')


RAW = bytes([20, 0, 0, 0, 3, 14, 0, 2, 10, 0]) + b'ab' + bytes([0, 0]) + bytes([1, 0, 2, 0, 3, 0])
DATA = {
    'size': 20,
    'num_items': 3,
    'items_ptr': 14,
    'name_size': 2,
    'rest_size': 10,
    'name': 'ab',
    'pad': b'\0\0',
    'items': [1, 2, 3],
}


def read(block, raw: bytes):
    return block.unpack(ReadContext(BytesIO(raw), read_bytes_amount=len(raw)), read_bytes_amount=len(raw))


class TestBlockParameters(unittest.TestCase):
    def test_field_path_lengths_read(self):
        self.assertEqual(read(Header(), RAW), DATA)

    def test_parent_path(self):
        block = CompoundBlock(
            fields=[
                ('count', IntegerBlock(length=1), {}),
                ('inner', CompoundBlock(fields=[('values', BytesBlock(length='../count'), {})]), {}),
            ]
        )
        self.assertEqual(read(block, bytes([2, 7, 8])), {'count': 2, 'inner': {'values': bytes([7, 8])}})

    def test_docs_show_the_path(self):
        self.assertEqual(ArrayBlock(child=IntegerBlock(length=2), length='num_items').length_doc_str, 'num_items')
        self.assertEqual(BytesBlock(length='../size').size_doc_str, '^size')
        self.assertEqual(UTF8Block(length=('name_size', 'len(name)')).size_doc_str, 'len(name)')
        self.assertEqual(Padding(to='items_ptr').size_doc_str, 'up to offset items_ptr')
        self.assertEqual(param_doc(lambda ctx: ctx.data('a') * 2), 'a*2')

    def test_static_parameters(self):
        self.assertTrue(is_static_param(4))
        self.assertTrue(is_static_param((0, 'custom')))
        self.assertFalse(is_static_param('num_items'))
        self.assertFalse(is_static_param((lambda ctx: 1, 'one')))
        self.assertNotIn('length', ArrayBlock(child=IntegerBlock(length=1), length='n').schema)
        self.assertEqual(ArrayBlock(child=IntegerBlock(length=1), length='n').new_data(), [])
        self.assertEqual(BytesBlock(length='n').new_data(), b'')
        self.assertIsNone(UTF8Block(length='n')._get_static_length())
        self.assertEqual(param_value('a/1', WriteContext(data={'a': [5, 6]})), 6)


class TestFieldReferences(unittest.TestCase):
    def test_write_fills_references(self):
        block = Header()
        self.assertEqual(set(block.back_patched_fields), {'size', 'items_ptr', 'rest_size'})
        data = {**DATA, 'size': 0, 'num_items': 0, 'items_ptr': 0, 'name_size': 0, 'rest_size': 0}
        self.assertEqual(block.pack(data), RAW)

    def test_references_follow_edits(self):
        data = {**DATA, 'name': 'abcd', 'items': [1, 2, 3, 4]}
        raw = Header().pack(data)
        self.assertEqual(raw[:10], bytes([24, 0, 0, 0, 4, 16, 0, 4, 14, 0]))
        self.assertEqual(
            read(Header(), raw), {**data, 'size': 24, 'num_items': 4, 'items_ptr': 16, 'name_size': 4, 'rest_size': 14}
        )

    def test_called_references_estimate(self):
        block = Header()
        ctx = WriteContext(data=DATA, block=block)
        for name, value in (('size', 20), ('num_items', 3), ('items_ptr', 14), ('rest_size', 10)):
            self.assertEqual(block.field_blocks_map[name].programmatic_value(ctx), value)

    def test_constants(self):
        reference = OwnSize() - 8
        self.assertEqual((reference.add, OwnSize().add), (-8, 0))
        self.assertEqual((2 + CountOf('a')).add, 2)

    def test_class_sizing_otherwise_estimates_own_size(self):
        class WithFooter(CompoundBlock):
            def estimate_packed_size(self, data, ctx=None):
                return super().estimate_packed_size(data, ctx) + 4

            def write(self, data, ctx=None, name=''):
                return super().write(data, ctx, name) + b'FOOT'

        block = WithFooter(
            fields=[
                ('size', IntegerBlock(length=1, programmatic_value=OwnSize()), {}),
                ('data', BytesBlock(length=2), {}),
            ]
        )
        self.assertEqual(block.back_patched_fields, {})
        self.assertEqual(block.pack({'size': 0, 'data': b'xy'}), bytes([7]) + b'xyFOOT')

    def test_references_to_ui_fields_estimate(self):
        block = CompoundBlock(
            fields=[
                ('size', IntegerBlock(length=1, programmatic_value=SizeOf('shown')), {}),
                ('shown', BytesBlock(length=2), {'usage': 'ui'}),
            ]
        )
        self.assertEqual(block.back_patched_fields, {})
        self.assertEqual(block.pack({'size': 0, 'shown': b'xy'}), bytes([2]))

    def test_value_out_of_range_raises(self):
        block = CompoundBlock(
            fields=[
                ('size', IntegerBlock(length=1, programmatic_value=SizeOf('data')), {}),
                ('data', BytesBlock(length='size'), {}),
            ]
        )
        with self.assertRaises(IntegerOutOfRangeException):
            block.pack({'size': 0, 'data': bytes(300)})

    def test_nested_sizes(self):
        inner = CompoundBlock(
            fields=[
                ('length', IntegerBlock(length=4, programmatic_value=OwnSize() - 4), {}),
                ('payload', BytesBlock(length=(lambda ctx: ctx.data('length'), 'length')), {}),
            ]
        )
        outer = CompoundBlock(
            fields=[
                ('length', IntegerBlock(length=4, programmatic_value=SizeOf('chunks')), {}),
                ('chunks', ArrayBlock(child=inner, length=2), {}),
            ]
        )
        data = {'length': 0, 'chunks': [{'length': 0, 'payload': b'abc'}, {'length': 0, 'payload': b''}]}
        self.assertEqual(outer.pack(data), bytes([11, 0, 0, 0, 3, 0, 0, 0]) + b'abc' + bytes(4))

    def test_copies(self):
        block = Header()
        block.pack(DATA)
        copy = deepcopy(block)
        self.assertEqual(copy.pack(DATA), RAW)
        self.assertIsNot(
            copy.field_blocks_map['size'].programmatic_value, block.field_blocks_map['size'].programmatic_value
        )


if __name__ == '__main__':
    unittest.main()

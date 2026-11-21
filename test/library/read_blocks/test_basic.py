import unittest
from io import BytesIO

from library.context import ReadContext
from library.exceptions import DataIntegrityException
from library.read_blocks import DeclarativeCompoundBlock, FittedBytesBlock
from library.read_blocks.basic import BytesBlock
from library.read_blocks.strings import NullTerminatedUTF8Block
from library.read_blocks.numbers import IntegerBlock
from serializers import JsonSerializer, PlainBinarySerializer


class DescribedInteger(IntegerBlock):
    block_description = 'A described integer'


class DescribedIntegerSubclass(DescribedInteger):
    pass


class DescribedIntegerSchemaOverride(DescribedInteger):
    @property
    def schema(self):
        return {**super().schema, 'block_description': 'Described by the schema override'}


class SerializedInteger(IntegerBlock):
    serializer = 'JsonSerializer'


class SerializedIntegerSubclass(SerializedInteger):
    pass


class DescribedIntegerWithSchema(IntegerBlock):
    block_description = 'A described integer with more schema'

    @property
    def schema(self):
        return {**super().schema, 'block_description': 'Described by its own schema', 'extra': 1}


class TestBasicBlocks(unittest.TestCase):
    def test_bytes_block_size_doc_str(self):
        # Static length
        field = BytesBlock(length=10)
        self.assertEqual(field.size_doc_str, '10')

        # Callable length
        field = BytesBlock(length=lambda ctx: 5)
        self.assertEqual(field.size_doc_str, '5')

        # Tuple length (doc override)
        field = BytesBlock(length=(lambda ctx: 5, 'custom length'))
        self.assertEqual(field.size_doc_str, 'custom length')


class TestClassBlockDescription(unittest.TestCase):
    def test_over_base_class_description(self):
        schema = DescribedInteger(length=1).schema
        self.assertEqual(schema['block_description'], 'A described integer')
        self.assertEqual(schema['block_class_mro'], 'DescribedInteger__IntegerBlock__DataBlock')
        self.assertEqual(schema['max_value'], 255)

    def test_inherited(self):
        self.assertEqual(DescribedIntegerSubclass(length=1).schema['block_description'], 'A described integer')

    def test_subclass_schema_override(self):
        schema = DescribedIntegerSchemaOverride(length=1).schema
        self.assertEqual(schema['block_description'], 'Described by the schema override')

    def test_over_own_schema(self):
        schema = DescribedIntegerWithSchema(length=1).schema
        self.assertEqual(schema['block_description'], 'A described integer with more schema')
        self.assertEqual(schema['extra'], 1)

    def test_base_class_untouched(self):
        self.assertEqual(IntegerBlock(length=1).schema['block_description'], '1-byte unsigned integer')


class TestSerializerAttribute(unittest.TestCase):
    def test_none_by_default(self):
        self.assertIsNone(IntegerBlock(length=1).serializer_class())

    def test_named_serializer(self):
        self.assertIs(SerializedInteger(length=1).serializer_class(), JsonSerializer)
        self.assertIs(SerializedIntegerSubclass(length=1).serializer_class(), JsonSerializer)

    def test_framework_serializer(self):
        self.assertIs(BytesBlock(length=1).serializer_class(), PlainBinarySerializer)


class NameField(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        name = NullTerminatedUTF8Block(length=8)
        name_padding = FittedBytesBlock(length=(lambda ctx: 7 - len(ctx.data('name').encode('utf-8')), '7 - len(name)'))


class TestFittedBytes(unittest.TestCase):
    def test_leftovers_kept_and_refitted(self):
        block = NameField()
        raw = b'abc\x00xyz\xcc'
        data = block.unpack(ReadContext(BytesIO(raw)))
        self.assertEqual(data, {'name': 'abc', 'name_padding': b'xyz\xcc'})
        self.assertEqual(block.pack(data), raw)
        self.assertEqual(block.pack({**data, 'name': 'abcde'}), b'abcde\x00xy')
        self.assertEqual(block.pack({**data, 'name': 'a'}), b'a\x00xyz\xcc\x00\x00')
        self.assertEqual(block.estimate_packed_size({**data, 'name': 'a'}), 8)
        with self.assertRaises(DataIntegrityException):
            block.pack({**data, 'name': 'abcdefghi'})

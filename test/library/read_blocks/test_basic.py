import unittest
from library.read_blocks.basic import BytesBlock
from library.read_blocks.numbers import IntegerBlock


class DescribedInteger(IntegerBlock):
    block_description = 'A described integer'


class DescribedIntegerSubclass(DescribedInteger):
    pass


class DescribedIntegerSchemaOverride(DescribedInteger):
    @property
    def schema(self):
        return {**super().schema, 'block_description': 'Described by the schema override'}


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

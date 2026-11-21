import unittest
from io import BytesIO

from library.context import ReadContext
from library.exceptions import BlockDefinitionException
from library.read_blocks import DeclarativeCompoundBlock, IntegerBlock, MagicDispatchBlock, UTF8Block
from library.read_blocks.misc.value_validators import Eq, Or


class IndexedPart(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        index = IntegerBlock(length=2)
        identifier = UTF8Block(length=2, value_validator=Or(['ab', 'cd']))
        value = IntegerBlock(length=4)


class NamedPart(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = UTF8Block(length=4, value_validator=Or(['Name', '']))
        value = IntegerBlock(length=4)


class OtherPart(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        index = IntegerBlock(length=2)
        identifier = UTF8Block(length=2, value_validator=Eq('cd'))
        value = IntegerBlock(length=4)


class UnknownPart(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = UTF8Block(length=4)
        value = IntegerBlock(length=4)


class TestMagicDispatchBlock(unittest.TestCase):
    def _choice(self, block, raw: bytes):
        ctx = ReadContext(BytesIO(raw), read_bytes_amount=len(raw))
        data = block.unpack(ctx)
        # the parts are 8 bytes
        self.assertEqual(ctx.buffer.tell(), 8)
        return data['choice_index']

    def test_first_block_accepting_the_identifier(self):
        block = MagicDispatchBlock(possible_blocks=[NamedPart(), IndexedPart(), OtherPart()])
        self.assertEqual(self._choice(block, b'Name' + bytes(4)), 0)
        self.assertEqual(self._choice(block, b'\x01\x00ab' + bytes(4)), 1)
        # both IndexedPart and OtherPart accept `cd`: the first one in order
        self.assertEqual(self._choice(block, b'\x02\x00cd' + bytes(4)), 1)
        # zeros: an empty 4-character identifier
        self.assertEqual(self._choice(block, bytes(8)), 0)

    def test_unknown_identifier_raises_or_takes_the_fallback(self):
        raw = b'\x01\x00xy' + bytes(4)
        with self.assertRaises(BlockDefinitionException):
            self._choice(MagicDispatchBlock(possible_blocks=[NamedPart(), IndexedPart()]), raw)
        # the fallback: a block without an identifier validator, read when no other block accepts the bytes
        block = MagicDispatchBlock(possible_blocks=[NamedPart(), IndexedPart(), UnknownPart()], fallback=2)
        self.assertEqual(self._choice(block, raw), 2)
        self.assertEqual(self._choice(block, b'\x01\x00cd' + bytes(4)), 1)
        # not UTF-8
        with self.assertRaises(BlockDefinitionException):
            self._choice(MagicDispatchBlock(possible_blocks=[NamedPart()]), b'\xff\xfe\xfd\xfc' + bytes(4))

    def test_round_trip(self):
        block = MagicDispatchBlock(possible_blocks=[NamedPart(), IndexedPart()])
        raw = b'\x05\x00cd\x07\x00\x00\x00'
        data = block.unpack(ReadContext(BytesIO(raw), read_bytes_amount=len(raw)))
        self.assertEqual(data['data'], {'index': 5, 'identifier': 'cd', 'value': 7})
        self.assertEqual(block.pack(data), raw)

    def test_definition_errors(self):
        class NoValidator(DeclarativeCompoundBlock):
            class Fields(DeclarativeCompoundBlock.Fields):
                identifier = UTF8Block(length=4)

        class NoIdentifier(DeclarativeCompoundBlock):
            class Fields(DeclarativeCompoundBlock.Fields):
                value = IntegerBlock(length=4)

        with self.assertRaises(BlockDefinitionException):
            MagicDispatchBlock(possible_blocks=[NoValidator()])
        with self.assertRaises(BlockDefinitionException):
            MagicDispatchBlock(possible_blocks=[NoIdentifier()])

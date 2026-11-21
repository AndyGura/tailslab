import unittest
from io import BytesIO

from library.context import ReadContext
from library.read_blocks import DeclarativeCompoundBlock, IntegerBlock, ParsedByParent, TextFileBlock, f32_text


class TextNumber(ParsedByParent, IntegerBlock):
    parsed_by = 'NumbersText'
    size_doc = '1 line'


class NumbersText(TextFileBlock):
    """Lines of numbers"""

    class Fields(DeclarativeCompoundBlock.Fields):
        first = TextNumber(length=4)
        second = TextNumber(length=4)

    def parse_text(self, raw: bytes) -> dict:
        first, second = raw.split(b'\n')
        return {'first': int(first), 'second': int(second)}

    def render(self, data):
        first = str(data['first']).encode()
        return first + b'\n' + str(data['second']).encode(), {'first': 0, 'second': len(first) + 1}


class TestTextFile(unittest.TestCase):
    def test_read_write(self):
        block = NumbersText()
        data = block.unpack(ReadContext(BytesIO(b'12\n345 tail')), read_bytes_amount=6)
        self.assertEqual(data, {'first': 12, 'second': 345})
        self.assertEqual(block.pack({'first': 7, 'second': 345}), b'7\n345')
        self.assertEqual(block.estimate_packed_size(data), 6)
        self.assertEqual(block.offset_to_child_when_packed(data, 'second'), 3)

    def test_parsed_by_parent(self):
        value = TextNumber(length=4)
        self.assertEqual(value.size_doc_str, '1 line')
        with self.assertRaises(NotImplementedError):
            value.unpack(ReadContext(BytesIO(bytes(4))))
        with self.assertRaises(NotImplementedError):
            value.pack(1)

    def test_f32_text(self):
        self.assertEqual(f32_text(1625.0, 6), '1625.000000')
        self.assertEqual(f32_text(0.1, 1), '0.1')
        # more decimals until the text reads back as the same 32-bit float
        self.assertEqual(f32_text(0.123456789, 2), '0.12345679')
        self.assertIsNone(f32_text(float('inf'), 1))

import struct
import unittest
from io import BytesIO
from types import SimpleNamespace

from library.context import ReadContext
from library.exceptions import DataIntegrityException
from library.read_blocks import ArrayBlock, DeclarativeCompoundBlock, IntegerBlock, UTF8Block
from resources.blackbox.chunks import (
    ChunkBlock,
    RecordsChunk,
    UnknownChunk,
    chunk_choice_index,
    chunk_length_field,
    chunk_rest,
    chunks_field,
    count_records,
    is_name_bytes,
    peek_chunk_payload,
    peek_sub_chunk_payload,
    peek_sub_chunks,
    records_to_chunk_end,
    walk_chunks,
    walk_nfsu_chunk_ids,
)


def chunk(chunk_id: int, payload: bytes) -> bytes:
    return struct.pack('<II', chunk_id, len(payload)) + payload


class Pairs(ChunkBlock):
    CHUNK_ID = 0x34001
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        pairs = (records_to_chunk_end(ArrayBlock(child=IntegerBlock(length=2), length=2), 4), {})


class Named(ChunkBlock):
    CHUNK_ID = 0x34002
    ALIGNMENT = 0x10
    CHECK_ELEVENS = True

    class Fields(ChunkBlock.Fields):
        value = IntegerBlock(length=4)
        rest = (chunk_rest(), {})


class Name(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        size = IntegerBlock(length=1)
        text = UTF8Block(length='size')


class Names(RecordsChunk):
    """Records of a length byte and that many characters"""

    CHUNK_ID = 0x34003
    RECORD_HEADER_SIZE = 1
    MIN_RECORDS = 1

    @staticmethod
    def record_size(payload, pos):
        return 1 + payload[pos] if payload[pos] else None

    class Fields(RecordsChunk.Fields):
        names = (records_to_chunk_end(Name()), {})


class Container(ChunkBlock):
    CHUNK_ID = 0x80034000

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field([Pairs(), Named()], 'Sub-chunks')


def read(block, raw: bytes):
    return block.unpack(ReadContext(BytesIO(raw), read_bytes_amount=len(raw)), read_bytes_amount=len(raw))


PAIRS = chunk(0x34001, b'\x11' * 8 + struct.pack('<4H', 1, 2, 3, 4))


class TestChunkFields(unittest.TestCase):
    def test_header_fields(self):
        self.assertEqual(
            [name for name, _ in Named().field_blocks], ['chunk_id', 'chunk_length', 'elevens', 'value', 'rest']
        )
        self.assertEqual(Named().field_blocks_map['chunk_id'].value_validator.expected_value, 0x34002)

        class FixedLength(ChunkBlock):
            CHUNK_ID = 0x34004

            class Fields(ChunkBlock.Fields):
                chunk_length = (IntegerBlock(length=4), {})
                value = IntegerBlock(length=4)

        block = FixedLength()
        self.assertEqual([name for name, _ in block.field_blocks], ['chunk_id', 'chunk_length', 'value'])
        self.assertIsNone(block.field_blocks_map['chunk_length'].programmatic_value)
        self.assertIsNotNone(chunk_length_field()[0].programmatic_value)

    def test_aligned_records(self):
        data = read(Pairs(), PAIRS)
        self.assertEqual(
            data, {'chunk_id': 0x34001, 'chunk_length': 16, 'elevens': b'\x11' * 8, 'pairs': [[1, 2], [3, 4]]}
        )
        self.assertEqual(Pairs().pack(data), PAIRS)

    def test_length_follows_edits(self):
        data = read(Pairs(), PAIRS)
        raw = Pairs().pack({**data, 'pairs': [[1, 2], [3, 4], [5, 6]]})
        self.assertEqual(raw[4:8], struct.pack('<I', 20))
        self.assertEqual(read(Pairs(), raw)['pairs'], [[1, 2], [3, 4], [5, 6]])

    def test_rest_and_filler_check(self):
        raw = chunk(0x34002, b'\x11' * 8 + struct.pack('<I', 7) + b'tail')
        self.assertEqual(
            read(Named(), raw),
            {'chunk_id': 0x34002, 'chunk_length': 16, 'elevens': b'\x11' * 8, 'value': 7, 'rest': b'tail'},
        )
        with self.assertRaises(DataIntegrityException):
            read(Named(), chunk(0x34002, b'\x11' * 7 + b'\x00' + struct.pack('<I', 7) + b'tail'))


class TestRecordsAndSubChunks(unittest.TestCase):
    def test_variable_size_records(self):
        raw = chunk(0x34003, b'\x02ab\x01c')
        data = read(Names(), raw)
        self.assertEqual(data['names'], [{'size': 2, 'text': 'ab'}, {'size': 1, 'text': 'c'}])
        self.assertEqual(Names().pack(data), raw)
        for payload, matches in ((b'\x02ab\x01c', True), (b'\x02ab\x02c', False), (b'', False)):
            self.assertEqual(Names().matches_chunk(SimpleNamespace(buffer=BytesIO(chunk(0x34003, payload)))), matches)

    def test_sub_chunks_up_to_the_end(self):
        raw = chunk(0x80034000, PAIRS + chunk(0x77, b'xyz'))
        data = read(Container(), raw)
        self.assertEqual([x['choice_index'] for x in data['sub_chunks']], [0, 2])
        self.assertEqual(data['sub_chunks'][1]['data']['payload'], b'xyz')
        self.assertEqual(Container().pack(data), raw)


class TestTextureLocations(unittest.TestCase):
    def test_nfsu_and_nfsu2_layouts_of_0x33310003(self):
        from resources.blackbox.bitmaps.nfsu import NfsuCompressedTextures, NfsuTextureLocations, NfsuTexturePackInfo

        nfsu = struct.pack('<5I', 0x0272FD80, 0x7480, 0x1421C, 0x100, 0) * 2
        nfsu2 = struct.pack('<6I', 0x09FE5E81, 0x35E80, 0x4842, 0x4009C, 0x100, 0)
        for payload, block_class in ((nfsu, NfsuTextureLocations), (nfsu2, NfsuCompressedTextures)):
            raw = chunk(0xB3310000, chunk(0x33310003, payload))
            container = NfsuTexturePackInfo()
            data = read(container, raw)
            item = data['sub_chunks'][0]
            chosen = container.field_blocks_map['sub_chunks'].child.possible_blocks[item['choice_index']]
            self.assertIsInstance(chosen, block_class)
            self.assertEqual(len(item['data']['textures']), 2 if block_class is NfsuTextureLocations else 1)
            self.assertEqual(container.pack(data), raw)


class TestChunkDispatch(unittest.TestCase):
    def test_matches_chunk_first(self):
        class Variant(Named):
            def matches_chunk(self, ctx):
                return peek_chunk_payload(ctx, 12)[8] == 1

        blocks = [Named(), Variant(), Pairs()]
        pick = chunk_choice_index(blocks, fallback=None)
        variant = chunk(0x34002, b'\x11' * 8 + struct.pack('<I', 1))
        for raw, expected in ((variant, 1), (variant.replace(b'\x01\0\0\0', b'\x02\0\0\0'), 0), (PAIRS, 2)):
            ctx = SimpleNamespace(buffer=BytesIO(raw))
            self.assertEqual(pick(ctx), expected)
            self.assertEqual(ctx.buffer.tell(), 0)

    def test_id_ranges_and_unknown_chunks(self):
        class Ranged(UnknownChunk):
            chunk_ids = [0x34100 | i for i in range(4)]

        pick = chunk_choice_index([Ranged()], fallback=None)
        self.assertEqual(pick(SimpleNamespace(buffer=BytesIO(chunk(0x34103, b'')))), 0)
        with self.assertRaises(Exception):
            pick(SimpleNamespace(buffer=BytesIO(chunk(0x34104, b''))))


class TestChunkWalks(unittest.TestCase):
    def test_walk_chunks(self):
        raw = chunk(1, b'ab') + chunk(2, b'') + b'\0\0\0'
        headers = walk_chunks(BytesIO(raw), 0, len(raw))
        self.assertEqual([(h.id, h.offset, h.length) for h in headers], [(1, 8, 2), (2, 18, 0)])
        self.assertEqual(walk_nfsu_chunk_ids(BytesIO(raw), len(raw) - 3), [1, 2])
        self.assertIsNone(walk_nfsu_chunk_ids(BytesIO(raw), len(raw)))
        self.assertIsNone(walk_nfsu_chunk_ids(BytesIO(raw), 9))
        self.assertEqual(walk_nfsu_chunk_ids(BytesIO(raw), 0), [])

    def test_sub_chunks(self):
        container = chunk(0x80000001, chunk(1, b'ab') + chunk(0x34102, b'infos'))
        ctx = SimpleNamespace(buffer=BytesIO(b'??' + container))
        ctx.buffer.seek(2)
        self.assertEqual([h.id for h in peek_sub_chunks(ctx)], [1, 0x34102])
        self.assertEqual(peek_sub_chunk_payload(ctx, 0x34102), b'infos')
        self.assertIsNone(peek_sub_chunk_payload(ctx, 3))
        self.assertEqual(ctx.buffer.tell(), 2)
        # a sub-chunk running past its container is cut at the container's end
        ctx = SimpleNamespace(buffer=BytesIO(chunk(0x80000001, chunk(5, b'abcd')[:10]) + b'next'))
        self.assertEqual(peek_sub_chunk_payload(ctx, 5), b'ab')

    def test_count_records(self):
        def size(payload, pos):
            return payload[pos] if payload[pos] else None

        self.assertEqual(count_records(bytes([2, 0, 3, 0, 0]), 1, size), 2)
        self.assertIsNone(count_records(bytes([2, 0, 3, 0]), 1, size))
        self.assertIsNone(count_records(bytes([0]), 1, size))
        self.assertEqual(count_records(b'', 1, size), 0)

    def test_names(self):
        self.assertTrue(is_name_bytes(b'ABC\0\0'))
        self.assertFalse(is_name_bytes(b'ABC\0x'))
        self.assertTrue(is_name_bytes(b'ABC\0x', leftovers=True))
        self.assertFalse(is_name_bytes(b'ABCD', leftovers=True))


if __name__ == '__main__':
    unittest.main()

from io import SEEK_CUR
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional

from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DataBlock,
    DeclarativeCompoundBlock,
    DelegateBlock,
    IntegerBlock,
    OwnSize,
)
from library.read_blocks.misc.value_validators import Eq, ValueValidator

# Black Box bundles (NFS Underground *.BUN, *.BIN, uncompressed *.lzc; NFS Hot Pursuit 2 PS2) are trees of chunks:
# 32-bit chunk id, 32-bit payload length, payload. Chunks with the highest bit of id set are containers of other
# chunks. A payload often starts with 0x11 bytes up to an offset aligned to 16 (vertices, textures: 128) bytes from the
# beginning of the file.
#
# A chunk block is a `ChunkBlock`: its `CHUNK_ID` and `ALIGNMENT` give the header fields (id, length, 0x11 filler),
# its `Fields` the rest, often records up to the end of the payload (`records_to_chunk_end`) or raw bytes
# (`chunk_rest`). `chunk_delegate` / `chunk_choice_index` pick the block of a chunk by its id.

CHUNK_ID_DESCRIPTION = 'Chunk ID'
CHUNK_LENGTH_DESCRIPTION = 'Length of the chunk payload in bytes (everything after this field)'
ELEVENS_DESCRIPTION = (
    'Alignment filler: a run of 0x11 bytes before the actual payload, so that the payload starts at an aligned offset'
)


def elevens_length(ctx, alignment: int = 0x10):
    """Length of 0x11 alignment filler: chunk payloads start at an offset aligned to 16 (vertices: 128) bytes from
    the beginning of the file"""
    return -ctx.buffer.tell() % alignment


class ElevensValidator(ValueValidator):
    """The filler holds 0x11 bytes only"""

    def validate(self, value) -> bool:
        return value == b'\x11' * len(value)

    def schema(self):
        return {'type': 'elevens'}

    def new_data(self):
        return b''

    def __str__(self):
        return 'only 0x11 bytes'


def chunk_id_field(chunk_id: int = None, description: str = CHUNK_ID_DESCRIPTION):
    """`chunk_id` field: the 32-bit id, `Eq(chunk_id)` (`chunk_delegate` picks the block by it)"""
    return (
        IntegerBlock(length=4, value_validator=Eq(chunk_id) if chunk_id is not None else None),
        {'description': description},
    )


def chunk_length_field(description: str = CHUNK_LENGTH_DESCRIPTION):
    """`chunk_length` field: length of the payload (everything after it), written from the written fields"""
    return (
        IntegerBlock(length=4, programmatic_value=OwnSize() - 8),
        {'usage': 'io,doc', 'description': description},
    )


def elevens_field(alignment: int = 0x10, check: bool = False):
    """`elevens` field: 0x11 filler up to the next offset aligned to `alignment` bytes from the beginning of the file;
    `check`: reading other bytes there raises"""
    return (
        BytesBlock(
            length=(lambda ctx: elevens_length(ctx, alignment), f'up to {alignment}-bytes alignment'),
            value_validator=ElevensValidator() if check else None,
        ),
        {'usage': 'io,doc', 'description': ELEVENS_DESCRIPTION},
    )


def chunk_payload_remaining(ctx) -> int:
    """Payload bytes of the chunk after the buffer position; `ctx`: the chunk block's read context"""
    return ctx.data('chunk_length') + 8 - ctx.local_buffer_pos


def records_to_chunk_end(child: DataBlock, record_size: int = None, doc: str = 'until the end of chunk') -> ArrayBlock:
    """Records from the field up to the end of the chunk payload: `record_size` bytes each, or read one by one until
    the end (records of any size)"""
    if record_size is None:
        return ArrayBlock(child=child, byte_length=(chunk_payload_remaining, doc))
    return ArrayBlock(child=child, length=(lambda ctx: chunk_payload_remaining(ctx) // record_size, doc))


def chunk_rest() -> BytesBlock:
    """Bytes from the field up to the end of the chunk payload"""
    return BytesBlock(length=(chunk_payload_remaining, 'up to the end of chunk'))


class ChunkBlock(DeclarativeCompoundBlock):
    """A chunk: the fields `chunk_id` (`Eq(CHUNK_ID)`, none for None), `chunk_length` (written from the written
    fields) and, with `ALIGNMENT`, `elevens` (0x11 filler up to that alignment, `CHECK_ELEVENS`: other bytes raise)
    come before the fields of its `Fields` class. A header field the `Fields` class declares itself (a length with a
    validator) is taken from it"""

    CHUNK_ID: Optional[int] = None
    ALIGNMENT: Optional[int] = None
    CHECK_ELEVENS = False

    @classmethod
    def declared_fields(cls):
        declared = super().declared_fields()
        by_name = {field[0]: field for field in declared}
        header = [
            by_name.get('chunk_id') or ('chunk_id', *chunk_id_field(cls.CHUNK_ID)),
            by_name.get('chunk_length') or ('chunk_length', *chunk_length_field()),
        ]
        if 'elevens' in by_name:
            header.append(by_name['elevens'])
        elif cls.ALIGNMENT:
            header.append(('elevens', *elevens_field(cls.ALIGNMENT, cls.CHECK_ELEVENS)))
        return header + [field for field in declared if field[0] not in _CHUNK_HEADER_FIELDS]


_CHUNK_HEADER_FIELDS = ('chunk_id', 'chunk_length', 'elevens')


class ZeroChunk(ChunkBlock):
    block_description = (
        'Padding chunk with id 0: filler between meaningful chunks, used for alignment. Payload has no meaning'
    )
    CHUNK_ID = 0

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length='chunk_length'), {'usage': 'io,doc', 'description': 'Filler bytes'})


class UnknownChunk(ChunkBlock):
    block_description = 'A chunk not decoded by the parser: header + raw payload'

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length='chunk_length'), {'description': 'Raw chunk payload'})


class ChunkHeader(NamedTuple):
    id: int
    # absolute offset of the payload
    offset: int
    length: int

    @property
    def end(self) -> int:
        return self.offset + self.length


def iter_chunks(buffer, start: int, end: int) -> Iterator[ChunkHeader]:
    """Headers of the chunks stored back to back from `start` up to `end` (absolute offsets): every chunk whose 8-byte
    header lies before `end` (the last payload may run past it). Seeks from header to header without reading
    payloads; leaves the buffer anywhere"""
    pos = start
    while pos + 8 <= end:
        buffer.seek(pos)
        header = buffer.read(8)
        if len(header) < 8:
            return
        chunk = ChunkHeader(int.from_bytes(header[:4], 'little'), pos + 8, int.from_bytes(header[4:], 'little'))
        yield chunk
        pos = chunk.end


def walk_chunks(buffer, start: int, end: int) -> List[ChunkHeader]:
    """`iter_chunks` as a list (check `headers[-1].end` against `end` for chunks filling the range exactly)"""
    return list(iter_chunks(buffer, start, end))


def walk_nfsu_chunk_ids(buffer, length: int) -> Optional[List[int]]:
    """Ids of the top-level chunks if the `length` bytes at the buffer position are a chunk bundle (chunk lengths add
    up to `length` exactly), else None. Buffer position is not changed"""
    pos = buffer.tell()
    try:
        chunks = walk_chunks(buffer, pos, pos + length)
        return [chunk.id for chunk in chunks] if (chunks[-1].end if chunks else pos) == pos + length else None
    finally:
        buffer.seek(pos)


def peek_chunk_id(ctx) -> int:
    chunk_id = int.from_bytes(ctx.buffer.read(4), 'little')
    ctx.buffer.seek(-4, SEEK_CUR)
    return chunk_id


def peek_chunk_length(ctx) -> int:
    pos = ctx.buffer.tell()
    try:
        ctx.buffer.seek(4, SEEK_CUR)
        return int.from_bytes(ctx.buffer.read(4), 'little')
    finally:
        ctx.buffer.seek(pos)


def peek_bytes(ctx, length: int, offset: int = None) -> bytes:
    """Up to `length` bytes at `offset` (absolute, default the buffer position). Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        if offset is not None:
            ctx.buffer.seek(offset)
        return ctx.buffer.read(length)
    finally:
        ctx.buffer.seek(pos)


def peek_chunk_payload(ctx, length: int) -> bytes:
    """Up to `length` first bytes of payload of the chunk at the buffer position. Buffer position is not changed"""
    return peek_bytes(ctx, min(length, peek_chunk_length(ctx)), ctx.buffer.tell() + 8)


def peek_sub_chunks(ctx) -> List[ChunkHeader]:
    """`walk_chunks` over the payload of the container chunk at the buffer position. Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        return walk_chunks(ctx.buffer, pos + 8, pos + 8 + peek_chunk_length(ctx))
    finally:
        ctx.buffer.seek(pos)


def peek_sub_chunk_payload(ctx, chunk_id: int) -> Optional[bytes]:
    """Payload of the first sub-chunk with `chunk_id` of the container chunk at the buffer position (cut at the end of
    the container), None if there is none. Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        end = pos + 8 + peek_chunk_length(ctx)
        for chunk in iter_chunks(ctx.buffer, pos + 8, end):
            if chunk.id == chunk_id:
                ctx.buffer.seek(chunk.offset)
                return ctx.buffer.read(min(chunk.length, end - chunk.offset))
        return None
    finally:
        ctx.buffer.seek(pos)


def count_records(
    payload: bytes, header_size: int, record_size: Callable[[bytes, int], Optional[int]]
) -> Optional[int]:
    """Number of variable-size records back to back in `payload`: `record_size(payload, pos)` is the size of the record
    at `pos` (at least `header_size` bytes left there), None if it is not one. None unless they fill the payload"""
    pos = count = 0
    while pos + header_size <= len(payload):
        size = record_size(payload, pos)
        if size is None:
            return None
        pos += size
        count += 1
    return count if pos == len(payload) else None


def is_name_bytes(b: bytes, leftovers: bool = False) -> bool:
    """Fixed-length text field: printable ASCII, then zero bytes only (`leftovers`: a zero, then any bytes)"""
    text = b.split(b'\0', 1)[0]
    if leftovers:
        return len(text) < len(b) and all(0x20 <= x < 0x7F for x in text)
    return all(0x20 <= x < 0x7F for x in text) and not any(b[len(text) :])


def chunk_blocks_by_id(blocks: List[DataBlock]) -> Dict[int, List[int]]:
    """Chunk id -> indexes of blocks, from `Eq` validators of `chunk_id` fields, or the block's `chunk_ids` (a block
    taking a range of ids)"""
    blocks_by_id = {}
    for i, block in enumerate(blocks):
        ids = getattr(block, 'chunk_ids', None)
        if ids is None:
            # NfsuBinGeometry names its chunk id field "header"
            fields = getattr(block, 'field_blocks_map', {})
            chunk_id_block = fields.get('chunk_id') or fields.get('header')
            validator = chunk_id_block.value_validator if chunk_id_block else None
            ids = [validator.expected_value] if validator is not None and hasattr(validator, 'expected_value') else []
        for chunk_id in ids:
            blocks_by_id.setdefault(chunk_id, []).append(i)
    return blocks_by_id


def chunk_choice_index(blocks: List[DataBlock], fallback: Optional[int]):
    """`choice_index` of a `DelegateBlock` of chunks: the block for the chunk id at the buffer position. Blocks with
    `matches_chunk(ctx)` (peeks the chunk) are tried first and picked only if it returns True: that's how chunks with
    the same id but different layout (NFSU, NFSU2, NFSMW) are told apart. Unknown ids: `fallback`, or an exception"""
    blocks_by_id = {
        chunk_id: sorted(indexes, key=lambda i: getattr(blocks[i], 'matches_chunk', None) is None)
        for chunk_id, indexes in chunk_blocks_by_id(blocks).items()
    }

    def choice_index(ctx, **_) -> int:
        chunk_id = peek_chunk_id(ctx)
        for i in blocks_by_id.get(chunk_id, []):
            matches_chunk = getattr(blocks[i], 'matches_chunk', None)
            if matches_chunk is None or matches_chunk(ctx):
                return i
        if fallback is None:
            raise Exception(f'Unknown chunk: Chunk{chunk_id:08X}')
        return fallback

    return choice_index


def _chunk_seed(ctx, block: DataBlock) -> Dict:
    # chunk id is known without parsing: lets code pick chunks by id without loading all of them
    fields = getattr(block, 'field_blocks_map', {})
    id_field = 'chunk_id' if 'chunk_id' in fields else 'header' if 'header' in fields else None
    return {id_field: peek_chunk_id(ctx)} if id_field else {}


def chunk_delegate(possible_blocks: List[DataBlock]) -> DelegateBlock:
    """One chunk of any of given kinds, picked by chunk id. Unknown chunks are read as `UnknownChunk`. Chunks are
    lazy parts: in lazy read context, the chosen block is parsed on first access"""
    blocks = list(possible_blocks) + [UnknownChunk()]
    return DelegateBlock(
        possible_blocks=blocks,
        choice_index=(
            chunk_choice_index(blocks[:-1], fallback=len(blocks) - 1),
            'by chunk id (and layout, if several kinds share the id), `UnknownChunk` for unknown ids',
        ),
        part_length=lambda ctx: 8 + peek_chunk_length(ctx),
        part_seed=_chunk_seed,
    )


def chunks_field(
    possible_blocks: List[DataBlock],
    description: str,
    byte_length=(chunk_payload_remaining, 'until the end of chunk'),
):
    """Field with chunks (`chunk_delegate`) back to back up to the end of the chunk payload (sub-chunks of a container
    chunk), or in `byte_length` bytes (a block parameter)"""
    return (
        ArrayBlock(byte_length=byte_length, child=chunk_delegate(possible_blocks)),
        {'description': description},
    )


def bytes_remaining(ctx) -> int:
    """`byte_length` of chunks up to the end of the file (or the part read)"""
    return ctx.read_bytes_remaining


class RecordsChunk(ChunkBlock):
    """A chunk of variable-size records back to back up to the end of its payload (its field:
    `records_to_chunk_end(child)`). `RECORD_HEADER_SIZE` and `record_size(payload, pos)` measure them
    (`count_records`): `matches_chunk` takes a payload they fill exactly, with at least `MIN_RECORDS` records"""

    RECORD_HEADER_SIZE: int = None
    MIN_RECORDS = 0

    @staticmethod
    def record_size(payload: bytes, pos: int) -> Optional[int]:
        raise NotImplementedError

    @classmethod
    def records_amount(cls, payload: bytes) -> Optional[int]:
        return count_records(payload, cls.RECORD_HEADER_SIZE, cls.record_size)

    def matches_chunk(self, ctx) -> bool:
        amount = self.records_amount(peek_chunk_payload(ctx, peek_chunk_length(ctx)))
        return amount is not None and amount >= self.MIN_RECORDS

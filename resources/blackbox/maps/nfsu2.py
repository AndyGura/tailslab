from typing import Dict, Optional

from library.read_blocks import ArrayBlock, BytesBlock, DeclarativeCompoundBlock, DecimalBlock, IntegerBlock
from library.read_blocks.misc.value_validators import Eq
from library.context import WriteContext
from library.exceptions import DataIntegrityException
from library.read_blocks.strings import NullTerminatedUTF8Block
from resources.blackbox.chunks import peek_chunk_length, peek_chunk_payload
from resources.blackbox.geometries.nfsu import _CHUNK_ID_DESCR, _CHUNK_LENGTH_DESCR
from resources.eac.fields.misc import Point2D

# NFS Underground 2 road network: roads chunk 0x34121 of TRACKS/ROUTESLxRx/Routes*.bin (RoutesAll.bin: every road of
# the location), with NFSU's chunk id but a shorter layout (140-byte road headers, 56-byte nodes, no heights)


class Nfsu2RoadNode(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Node of a road: a point of its centre line, 4..40 m apart'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Position on the ground plane (world X, Y; Z up): the nodes have no heights'},
        )
        route_distance = (
            DecimalBlock(length=4),
            {
                'description': 'Distance along the race route of Routes<race>F.bin (forward) / B.bin (backward: the '
                'lap length minus the forward one), 0 in RoutesAll.bin and RoutesFreeRoam.bin'
            },
        )
        unk0 = (BytesBlock(length=4), {'is_unknown': True})
        unk1 = (ArrayBlock(child=IntegerBlock(length=2), length=4), {'is_unknown': True})
        direction = (
            Point2D(child=IntegerBlock(length=2, is_signed=True)),
            {'description': 'Unit direction to the next node on the ground plane, x 32767'},
        )
        unk2 = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=2),
            {'is_unknown': True, 'description': 'Mostly -1'},
        )
        unk3 = (BytesBlock(length=4), {'is_unknown': True})
        unk4 = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=True), length=8),
            {'is_unknown': True, 'description': 'Mostly -1'},
        )
        unk5 = (
            BytesBlock(length=12),
            {'is_unknown': True, 'description': 'Mostly F7 EF 06 06 06 06 06 06 06 06 00 00'},
        )


NFSU2_ROAD_HEADER_SIZE = 140
NFSU2_ROAD_NODE_SIZE = 56


class Nfsu2Road(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Road of the location: a polyline of nodes on the ground plane. Roads meet at '
            'their ends, a road ending on another one ends at one of its nodes or within a few meters of it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True, 'description': 'Always 11'})
        unk1 = (IntegerBlock(length=2), {'is_unknown': True, 'description': 'Always 1'})
        road_id = (IntegerBlock(length=2), {'description': 'Id of the road, from 101'})
        unk2 = (IntegerBlock(length=4), {'is_unknown': True, 'description': 'Always 0'})
        name = (
            NullTerminatedUTF8Block(length=32),
            {'description': 'Name of the source the road was made of ("TrackRoutesA32"), up to 31 bytes'},
        )
        name_padding = (
            BytesBlock(length=(lambda ctx: 31 - len(ctx.data('name').encode('utf-8')), '31 - len(name)')),
            {'description': 'Rest of the 32-byte name field: zeros, or leftovers of other texts'},
        )
        unk3 = (DecimalBlock(length=4), {'is_unknown': True, 'description': 'Always 1.0'})
        num_nodes = (
            IntegerBlock(length=2, programmatic_value=lambda ctx: len(ctx.data('nodes'))),
            {'usage': 'io,doc', 'description': 'Amount of nodes'},
        )
        unk4 = (IntegerBlock(length=2), {'is_unknown': True, 'description': 'Always `num_nodes`'})
        unk5 = (BytesBlock(length=8), {'is_unknown': True})
        length = (DecimalBlock(length=4), {'description': 'Length of the road: sum of the distances between nodes'})
        race_ids = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=8),
            {
                'is_unknown': True,
                'description': 'Probably ids of races using the road, -1 for none (4211 .. 4223 in L4RB, which hosts '
                'the races 42xx; 4000 in L4RA)',
            },
        )
        unk6 = (DecimalBlock(length=4), {'is_unknown': True, 'description': 'Mostly 0, else 6..40'})
        unk7 = (BytesBlock(length=8), {'is_unknown': True, 'description': 'Zeros, a few text bytes in some roads'})
        bounding_box_min = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Minimum x, y of the road (a few meters beyond its nodes: its width included)'},
        )
        bounding_box_max = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Maximum x, y of the road (a few meters beyond its nodes: its width included)'},
        )
        flags = (BytesBlock(length=4), {'is_unknown': True})
        unk8 = (
            ArrayBlock(child=DecimalBlock(length=4), length=4),
            {'is_unknown': True, 'description': 'Always 0, 999, 0, 999'},
        )
        unk9 = (BytesBlock(length=8), {'is_unknown': True, 'description': 'Bytes 0 or 1'})
        nodes = (
            ArrayBlock(child=Nfsu2RoadNode(), length=lambda ctx: ctx.data('num_nodes')),
            {'description': 'Nodes'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        # the name field stays 32 bytes long whatever the name
        padding_length = 31 - len(data['name'].encode('utf-8'))
        if padding_length < 0:
            raise DataIntegrityException(f'Road name "{data["name"]}" is longer than 31 bytes', ctx=ctx)
        padding = (bytes(data['name_padding']) + bytes(padding_length))[:padding_length]
        return super().write({**data, 'name_padding': padding}, ctx, name)


def _peek_bytes(ctx, length: int) -> bytes:
    """`length` bytes at the buffer position. Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        return ctx.buffer.read(length)
    finally:
        ctx.buffer.seek(pos)


def _is_name(b: bytes) -> bool:
    """Null-terminated printable ASCII text (leftover bytes after it allowed)"""
    return b'\0' in b and all(0x20 <= x < 0x7F for x in b.split(b'\0', 1)[0])


def nfsu2_roads_amount(payload: bytes) -> Optional[int]:
    """Amount of roads in a roads chunk payload, None if it is not a whole number of NFSU2 roads"""
    pos = count = 0
    while pos + NFSU2_ROAD_HEADER_SIZE <= len(payload):
        if payload[pos : pos + 8] != b'\x0b\0\0\0\x0b\0\0\0' or not _is_name(payload[pos + 16 : pos + 48]):
            return None
        pos += NFSU2_ROAD_HEADER_SIZE + NFSU2_ROAD_NODE_SIZE * int.from_bytes(payload[pos + 52 : pos + 54], 'little')
        count += 1
    return count if pos == len(payload) else None


class Nfsu2Roads(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Roads of an NFS Underground 2 location (TRACKS/ROUTESLxRx/RoutesAll.bin: every '
            'road; RoutesFreeRoam.bin, Routes<race>F.bin / B.bin: a part of them). Chunks 0x34122 / 0x34123 '
            'next to it (links between roads?) are not decoded',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034121)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: sum(
                    NFSU2_ROAD_HEADER_SIZE + NFSU2_ROAD_NODE_SIZE * len(x['nodes']) for x in ctx.data('roads')
                ),
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        roads = (
            ArrayBlock(
                child=Nfsu2Road(),
                length=(
                    lambda ctx: nfsu2_roads_amount(_peek_bytes(ctx, ctx.data('chunk_length'))),
                    'until the end of chunk',
                ),
            ),
            {'description': 'Roads'},
        )

    def matches_chunk(self, ctx) -> bool:
        return bool(nfsu2_roads_amount(peek_chunk_payload(ctx, peek_chunk_length(ctx))))

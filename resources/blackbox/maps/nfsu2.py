from typing import Optional

from library.read_blocks import ArrayBlock, BytesBlock, DeclarativeCompoundBlock, DecimalBlock, IntegerBlock, CountOf
from library.context import WriteContext
from library.exceptions import DataIntegrityException
from library.read_blocks.strings import NullTerminatedUTF8Block
from resources.eac.fields.misc import Point2D
from resources.blackbox.chunks import RecordsChunk, is_name_bytes, records_to_chunk_end

# NFS Underground 2 road network: roads chunk 0x34121 of TRACKS/ROUTESLxRx/Routes*.bin (RoutesAll.bin: every road of
# the location), with NFSU's chunk id but a shorter layout (140-byte road headers, 56-byte nodes, no heights)


class Nfsu2RoadNode(DeclarativeCompoundBlock):
    block_description = 'Node of a road: a point of its centre line, 4..40 m apart'

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
    block_description = (
        'Road of the location: a polyline of nodes on the ground plane. Roads meet at '
        'their ends, a road ending on another one ends at one of its nodes or within a few meters of it'
    )

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
            IntegerBlock(length=2, programmatic_value=CountOf('nodes')),
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
            ArrayBlock(child=Nfsu2RoadNode(), length='num_nodes'),
            {'description': 'Nodes'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        # the name field stays 32 bytes long whatever the name
        padding_length = 31 - len(data['name'].encode('utf-8'))
        if padding_length < 0:
            raise DataIntegrityException(f'Road name "{data["name"]}" is longer than 31 bytes', ctx=ctx)
        padding = (bytes(data['name_padding']) + bytes(padding_length))[:padding_length]
        return super().write({**data, 'name_padding': padding}, ctx, name)


class Nfsu2Roads(RecordsChunk):
    block_description = (
        'Roads of an NFS Underground 2 location (TRACKS/ROUTESLxRx/RoutesAll.bin: every '
        'road; RoutesFreeRoam.bin, Routes<race>F.bin / B.bin: a part of them). Chunks 0x34122 / 0x34123 '
        'next to it (links between roads?) are not decoded'
    )

    CHUNK_ID = 0x00034121
    RECORD_HEADER_SIZE = NFSU2_ROAD_HEADER_SIZE
    MIN_RECORDS = 1

    @staticmethod
    def record_size(payload: bytes, pos: int) -> Optional[int]:
        # the name: null-terminated, leftover bytes after it
        if payload[pos : pos + 8] != b'\x0b\0\0\0\x0b\0\0\0' or not is_name_bytes(
            payload[pos + 16 : pos + 48], leftovers=True
        ):
            return None
        return NFSU2_ROAD_HEADER_SIZE + NFSU2_ROAD_NODE_SIZE * int.from_bytes(payload[pos + 52 : pos + 54], 'little')

    class Fields(RecordsChunk.Fields):
        roads = (records_to_chunk_end(Nfsu2Road()), {'description': 'Roads'})

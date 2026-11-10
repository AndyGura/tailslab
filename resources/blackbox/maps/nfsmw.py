from typing import Dict, List, Optional

from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    DecimalBlock,
    IntegerBlock,
)
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import UTF8Block
from resources.blackbox.chunks import peek_chunk_payload
from resources.blackbox.geometries.nfsu import _CHUNK_ID_DESCR, _CHUNK_LENGTH_DESCR, _ELEVENS_DESCR, elevens_length
from resources.eac.fields.misc import Point3D

# NFS Most Wanted road network (TRACKS/L2RA.BUN chunk 0x3b800): a "CARP" pack, a table of 16-byte entries (a tree of
# tagged containers and data blocks) followed by the data blocks, each padded with 0xAA bytes to 16 bytes. Positions
# are in the simulation axes of the game, Y up: world (scenery) axes are (z, -x, y) of them

# tags of the pack's entries as stored (characters last first), in table order
NFSMW_ROAD_NETWORK_TAGS = [
    'PRAC',
    'taDC',
    ' paM',
    'pgNR',
    'ncGC',
    'drGC',
    '\0\0oc',
    'dhNR',
    'dnNR',
    'fpNR',
    'drNR',
    'gsNR',
]
_CELLS, _GRID, _HEADER, _NODES, _PROFILES, _ROADS, _SEGMENTS = 4, 5, 7, 8, 9, 10, 11
_DATA_ENTRIES = [_CELLS, _GRID, _HEADER, _NODES, _PROFILES, _ROADS, _SEGMENTS]
_ENTRY_SIZE = 16
_FILLER_DESCR = 'Filler (0xAA bytes) up to the next data block'


class NfsmwCarpEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Entry of the table of a "CARP" pack: a container of the entries after it or a data '
            'block of the pack',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        tag = (
            UTF8Block(length=4),
            {
                'description': 'Four-character name, characters stored last first: "PRAC" = CARP (the pack), CDat, '
                'Map, RNgp (the road network), CGcn (grid cells), CGrd (grid), RNhd (road network header), RNnd '
                '(nodes), RNpf (profiles), RNrd (roads), RNsg (segments)'
            },
        )
        kind = (
            IntegerBlock(length=1),
            {'description': '0x1A container (0x7A the pack itself), 2 data block, 1 empty'},
        )
        size = (IntegerBlock(length=3), {'description': 'Size of the data block in bytes, 0 for a container'})
        count = (
            IntegerBlock(length=4),
            {'description': 'Records in the data block; entries in a container (0 in the pack entry)'},
        )
        offset = (
            IntegerBlock(length=4),
            {
                'description': 'Data block: distance in bytes from the start of this entry to the data. Container: '
                'distance in entries to its first entry'
            },
        )


class NfsmwRoadGrid(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Grid over the road network (CGrd): square cells on the ground plane, each listing '
            'the segments in it (CGcn)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        origin = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Corner of the grid with the lowest x and z (simulation axes, Y up)'},
        )
        unk0 = (DecimalBlock(length=4), {'is_unknown': True, 'description': 'Always 1'})
        cell_size = (DecimalBlock(length=4), {'description': 'Side of a cell in meters'})
        inverse_cell_size = (DecimalBlock(length=4), {'description': '1 / `cell_size`'})
        num_columns = (IntegerBlock(length=4), {'description': 'Cells along x'})
        num_rows = (IntegerBlock(length=4), {'description': 'Cells along z'})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})


class NfsmwRoadNetworkHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Road network header (RNhd): amounts of records'}

    class Fields(DeclarativeCompoundBlock.Fields):
        num_profiles = (IntegerBlock(length=2), {'description': 'Amount of profiles'})
        num_nodes = (IntegerBlock(length=2), {'description': 'Amount of nodes'})
        num_segments = (IntegerBlock(length=4), {'description': 'Amount of segments'})
        num_roads = (IntegerBlock(length=4), {'description': 'Amount of roads'})
        unk0 = (IntegerBlock(length=2), {'is_unknown': True})


class NfsmwRoadNode(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Node of the road network (RNnd): an end of segments, on the road surface',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Position in simulation axes (Y up; world axes are (z, -x, y))'},
        )
        index = (IntegerBlock(length=2), {'description': 'Index of the node'})
        profile = (IntegerBlock(length=2), {'description': 'Index of its profile (lanes)'})
        num_segments = (IntegerBlock(length=1), {'description': 'Amount of segments ending at the node, 1..7'})
        filler = (BytesBlock(length=1), {'usage': 'io,doc', 'description': '0xAA'})
        segments = (
            ArrayBlock(child=IntegerBlock(length=2), length=7),
            {'description': 'Indexes of the segments ending at the node, the first `num_segments`; 0xAAAA after them'},
        )


class NfsmwRoadProfile(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Profile of a road cross-section (RNpf): its lanes, referenced by nodes',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        num_lanes = (IntegerBlock(length=1), {'description': 'Amount of lanes, 1..15'})
        unk0 = (
            IntegerBlock(length=1),
            {'is_unknown': True, 'description': 'About half of `num_lanes`: lanes in one direction?'},
        )
        filler = (BytesBlock(length=2), {'usage': 'io,doc', 'description': '0xAA 0xAA'})
        lanes = (
            ArrayBlock(child=IntegerBlock(length=4), length=15),
            {
                'is_unknown': True,
                'description': 'Lanes, the first `num_lanes`: probably a lane kind in the low 16 bits and a lateral '
                'offset in the high 16 bits (symmetric around the middle lane)',
            },
        )


class NfsmwRoad(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Road (RNrd): a group of segments (`road` of the segments)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (BytesBlock(length=2), {'is_unknown': True, 'description': 'Always 00 01'})
        unk1 = (IntegerBlock(length=2), {'is_unknown': True})
        unk2 = (BytesBlock(length=2), {'is_unknown': True, 'description': '0xFF, then flags?'})
        unk3 = (IntegerBlock(length=2), {'is_unknown': True, 'description': '0 or 31'})


class NfsmwRoadSegment(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Segment of the road network (RNsg): a cubic Bezier curve from its start node to '
            'its end node, control points at `start_handle` along `start_direction` from the start node and at '
            '`end_handle` along `end_direction` from the end node',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        start_node = (IntegerBlock(length=2), {'description': 'Index of the node it starts at'})
        end_node = (IntegerBlock(length=2), {'description': 'Index of the node it ends at'})
        length = (
            IntegerBlock(length=2),
            {'description': 'Length of the curve in 1/65536 of 1000 m (meters * 65.536)'},
        )
        road = (IntegerBlock(length=2), {'description': 'Index of its road, 0xFFFF for none'})
        index = (IntegerBlock(length=2), {'description': 'Index of the segment'})
        flags = (IntegerBlock(length=2), {'is_unknown': True})
        end_handle = (
            IntegerBlock(length=2),
            {'description': 'Distance of the second control point from the end node in 1/65536 of 500 m'},
        )
        start_handle = (
            IntegerBlock(length=2),
            {'description': 'Distance of the first control point from the start node in 1/65536 of 500 m'},
        )
        end_direction = (
            Point3D(child=IntegerBlock(length=1, is_signed=True)),
            {
                'description': 'Unit direction from the end node to the second control point (back along the curve), '
                'times 127'
            },
        )
        start_direction = (
            Point3D(child=IntegerBlock(length=1, is_signed=True)),
            {'description': 'Unit direction from the start node to the first control point, times 127'},
        )


NFSMW_ROAD_SEGMENT_LENGTH_UNIT = 65.536
NFSMW_ROAD_SEGMENT_HANDLE_UNIT = 131.072


def peek_bytes(ctx, length: int) -> bytes:
    """`length` bytes at the buffer position. Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        return ctx.buffer.read(length)
    finally:
        ctx.buffer.seek(pos)


def _nfsmw_carp_table_amount(table: bytes) -> int:
    """Amount of entries of a "CARP" table: up to the first data block or the 0xAA filler"""
    end = len(table) // _ENTRY_SIZE
    i = 0
    while i < end:
        entry = table[i * _ENTRY_SIZE : (i + 1) * _ENTRY_SIZE]
        if entry[:4] == b'\xaa' * 4:
            break
        if entry[4] == 2 and int.from_bytes(entry[5:8], 'little'):
            end = min(end, i + int.from_bytes(entry[12:16], 'little') // _ENTRY_SIZE)
        i += 1
    return i


def _entry_data_start(entries: List[dict], i: int) -> int:
    """Position of the data block of entry i from the start of the table"""
    return _ENTRY_SIZE * i + entries[i]['offset']


def _filler_before(ctx, i: int) -> int:
    """Length of the filler before the data block of entry i (`_DATA_ENTRIES`)"""
    entries = ctx.data('entries')
    k = _DATA_ENTRIES.index(i)
    if k == 0:
        end = _ENTRY_SIZE * len(entries)
    else:
        previous = _DATA_ENTRIES[k - 1]
        end = _entry_data_start(entries, previous) + entries[previous]['size']
    return _entry_data_start(entries, i) - end


def _filler_field(i: int, name: str):
    return (
        BytesBlock(length=(lambda ctx: _filler_before(ctx, i), f'up to the {name} (`offset` of its entry)')),
        {'usage': 'io,doc', 'description': _FILLER_DESCR},
    )


def _records_amount(i: int):
    return (lambda ctx: ctx.data('entries')[i]['count'], f'`count` of entry {i}')


def nfsmw_road_network_table_tags(payload: bytes) -> Optional[List[str]]:
    """Tags of the table entries of a "CARP" pack payload (after the 0x11 filler), None if it is not one"""
    start = len(payload) - len(payload.lstrip(b'\x11'))
    table = payload[start:]
    if table[:4] != b'PRAC':
        return None
    amount = _nfsmw_carp_table_amount(table)
    return [table[i * _ENTRY_SIZE : i * _ENTRY_SIZE + 4].decode('latin-1') for i in range(amount)]


class NfsmwRoadNetwork(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFSMW road network of the city (TRACKS/L2RA.BUN), a "CARP" pack: a table of '
            'entries, then the data blocks it points at. Every road of the city as cubic Bezier segments between '
            'nodes on the road surface (with heights), their lane profiles, and a grid of cells listing the '
            'segments. The game routes races, AI and the GPS over it: races keep no route of their own (they list '
            'checkpoints and barriers in GLOBAL/gameplay.bin)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x0003B800)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()) - 8
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = (
            BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        )
        entries = (
            ArrayBlock(
                child=NfsmwCarpEntry(),
                length=(
                    lambda ctx: _nfsmw_carp_table_amount(
                        peek_bytes(ctx, ctx.data('chunk_length') - len(ctx.data('elevens')))
                    ),
                    'up to the first data block',
                ),
            ),
            {'description': 'Table of the pack (12 entries)'},
        )
        cells_filler = _filler_field(_CELLS, 'grid cells')
        grid_cells = (
            BytesBlock(length=(lambda ctx: ctx.data('entries')[_CELLS]['size'], '`size` of entry 4')),
            {
                'is_unknown': True,
                'description': 'Grid cells (CGcn): variable-size records listing the segments in each cell',
            },
        )
        grid_filler = _filler_field(_GRID, 'grid')
        grid = (NfsmwRoadGrid(), {'description': 'Grid (CGrd)'})
        header_filler = _filler_field(_HEADER, 'header')
        header = (NfsmwRoadNetworkHeader(), {'description': 'Road network header (RNhd)'})
        nodes_filler = _filler_field(_NODES, 'nodes')
        nodes = (
            ArrayBlock(child=NfsmwRoadNode(), length=_records_amount(_NODES)),
            {'description': 'Nodes (RNnd)'},
        )
        profiles_filler = _filler_field(_PROFILES, 'profiles')
        profiles = (
            ArrayBlock(child=NfsmwRoadProfile(), length=_records_amount(_PROFILES)),
            {'description': 'Profiles (RNpf)'},
        )
        roads_filler = _filler_field(_ROADS, 'roads')
        roads = (
            ArrayBlock(child=NfsmwRoad(), length=_records_amount(_ROADS)),
            {'description': 'Roads (RNrd)'},
        )
        segments_filler = _filler_field(_SEGMENTS, 'segments')
        segments = (
            ArrayBlock(child=NfsmwRoadSegment(), length=_records_amount(_SEGMENTS)),
            {'description': 'Segments (RNsg)'},
        )
        end_filler = (
            BytesBlock(
                length=(
                    lambda ctx: (
                        ctx.data('chunk_length')
                        - len(ctx.data('elevens'))
                        - _entry_data_start(ctx.data('entries'), _SEGMENTS)
                        - ctx.data('entries')[_SEGMENTS]['size']
                    ),
                    'up to the end of chunk',
                )
            ),
            {'usage': 'io,doc', 'description': 'Filler (0xAA bytes) up to the end of chunk'},
        )

    def matches_chunk(self, ctx) -> bool:
        # the layout of the fields: this table only
        payload = peek_chunk_payload(ctx, 16 + _ENTRY_SIZE * (len(NFSMW_ROAD_NETWORK_TAGS) + 1))
        return nfsmw_road_network_table_tags(payload) == NFSMW_ROAD_NETWORK_TAGS

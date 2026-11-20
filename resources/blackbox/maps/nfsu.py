from typing import Dict, Optional

from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    DecimalBlock,
    FixedPointBlock,
    IntegerBlock,
    CountOf,
)
from library.read_blocks.strings import UTF8Block
from resources.blackbox.bitmaps.nfsu import NfsuTexturePack
from resources.blackbox.geometries.nfsu import NfsuBinGeometry
from resources.blackbox.maps.nfs6_ps2 import Nfs6Ps2TrackPathHeader, Nfs6Ps2TrackPathPoints
from resources.blackbox.maps.nfsu2 import Nfsu2Roads
from resources.blackbox.maps.nfsmw import NfsmwRoadNetwork
from resources.eac.fields.misc import Point2D, Point3D
from resources.blackbox.chunks import (
    ChunkBlock,
    RecordsChunk,
    ZeroChunk,
    bytes_remaining,
    chunks_field,
    is_name_bytes,
    peek_chunk_length,
    peek_chunk_payload,
    peek_sub_chunk_payload,
    peek_sub_chunks,
    records_to_chunk_end,
)


class NfsuScenerySectionHeader(ChunkBlock):
    block_description = 'Scenery header: number of the section it belongs to'

    CHUNK_ID = 0x00034101
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        unk0 = (BytesBlock(length=12), {'is_unknown': True})
        section_number = (
            IntegerBlock(length=4),
            {
                'description': 'Number of the section: letter index (A = 1) * 100 + number, e.g. 2617 for "Z17". '
                'Matches `number` in the streaming sections table (without its 0x10000 flag)'
            },
        )
        unk1 = (BytesBlock(length=44), {'is_unknown': True})


class NfsuSceneryInfo(DeclarativeCompoundBlock):
    block_description = 'Scenery object definition: which mesh to draw'

    class Fields(DeclarativeCompoundBlock.Fields):
        mesh_ids = (
            ArrayBlock(child=IntegerBlock(length=4), length=6),
            {
                'description': 'Mesh ids (hashes of mesh names, `mesh_id` of mesh header chunks). The first one is '
                'the main mesh, others are probably levels of detail'
            },
        )
        far_clip_sizes = (ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=4), {'is_unknown': True})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        model_pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=6),
            {'description': 'Filled by the game in runtime', 'is_unknown': True},
        )
        facade_flags = (BytesBlock(length=6), {'is_unknown': True})
        unk1 = (IntegerBlock(length=2), {'is_unknown': True})
        radius = (DecimalBlock(length=4), {'description': 'Bounding sphere radius'})


class NfsuSceneryInfos(ChunkBlock):
    block_description = 'Scenery object definitions'

    CHUNK_ID = 0x00034102

    class Fields(ChunkBlock.Fields):
        infos = (
            records_to_chunk_end(NfsuSceneryInfo(), 72),
            {'description': 'Definitions'},
        )


class NfsuSceneryInstance(DeclarativeCompoundBlock):
    block_description = 'Placed scenery object'

    class Fields(DeclarativeCompoundBlock.Fields):
        bounding_box_min = (
            Point3D(child=IntegerBlock(length=2, is_signed=True)),
            {'description': 'Minimum corner of the bounding box in world coordinates'},
        )
        bounding_box_max = (
            Point3D(child=IntegerBlock(length=2, is_signed=True)),
            {'description': 'Maximum corner of the bounding box in world coordinates'},
        )
        info_index = (IntegerBlock(length=2), {'description': 'Index of the object definition in this scenery'})
        exclude_flags = (IntegerBlock(length=2), {'is_unknown': True})
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position in world coordinates'})
        rotation = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=13, is_signed=True), length=9),
            {
                'description': 'Rotation and scale matrix 3x3, row by row. World position of a mesh vertex v is '
                'v.x * row0 + v.y * row1 + v.z * row2 + position'
            },
        )
        padding = (IntegerBlock(length=2), {'is_unknown': True})


class NfsuSceneryInstances(ChunkBlock):
    block_description = 'Placed scenery objects'

    CHUNK_ID = 0x00034103
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        instances = (
            records_to_chunk_end(NfsuSceneryInstance(), 48),
            {'description': 'Instances'},
        )


class NfsuScenery(ChunkBlock):
    block_description = (
        'Scenery of a section: object definitions referencing meshes by id, and their placements in the world'
    )

    CHUNK_ID = 0x80034100

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [NfsuScenerySectionHeader(), NfsuSceneryInfos(), NfsuSceneryInstances(), ZeroChunk()],
            'Header, definitions, instances and an unknown chunk 0x00034104',
        )


def _nfsu2_scenery_info_names_ok(infos_payload: bytes) -> bool:
    return (
        len(infos_payload) % 68 == 0
        and len(infos_payload) > 0
        and all(is_name_bytes(infos_payload[i : i + 32]) for i in range(0, len(infos_payload), 68))
    )


class Nfsu2SceneryInfo(DeclarativeCompoundBlock):
    block_description = 'NFSU2 scenery object definition: which mesh to draw'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=32), {'description': 'Object name, e.g. "SKYDOME"'})
        mesh_ids = (
            ArrayBlock(child=IntegerBlock(length=4), length=3),
            {
                'description': 'Mesh ids (hashes of mesh names, `mesh_id` of mesh header chunks). The first one is '
                'the main mesh, others are probably levels of detail'
            },
        )
        flags = (ArrayBlock(child=IntegerBlock(length=2), length=2), {'is_unknown': True})
        model_pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=3),
            {'description': 'Filled by the game in runtime', 'is_unknown': True},
        )
        radius = (DecimalBlock(length=4), {'description': 'Bounding sphere radius'})
        hierarchy_key = (IntegerBlock(length=4), {'is_unknown': True})


class Nfsu2SceneryInfos(ChunkBlock):
    block_description = 'NFSU2 scenery object definitions'

    CHUNK_ID = 0x00034102

    class Fields(ChunkBlock.Fields):
        infos = (
            records_to_chunk_end(Nfsu2SceneryInfo(), 68),
            {'description': 'Definitions'},
        )


class Nfsu2SceneryInstance(DeclarativeCompoundBlock):
    block_description = 'NFSU2 placed scenery object'

    class Fields(DeclarativeCompoundBlock.Fields):
        bounding_box_min = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Minimum corner of the bounding box in world coordinates'},
        )
        bounding_box_max = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Maximum corner of the bounding box in world coordinates'},
        )
        info_index = (IntegerBlock(length=2), {'description': 'Index of the object definition in this scenery'})
        instance_flags = (IntegerBlock(length=2), {'is_unknown': True})
        preculler_info_index = (IntegerBlock(length=4, is_signed=True), {'is_unknown': True})
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position in world coordinates'})
        rotation = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=13, is_signed=True), length=9),
            {
                'description': 'Rotation and scale matrix 3x3, row by row. World position of a mesh vertex v is '
                'v.x * row0 + v.y * row1 + v.z * row2 + position'
            },
        )
        padding = (IntegerBlock(length=2), {'is_unknown': True})


class Nfsu2SceneryInstances(ChunkBlock):
    block_description = 'NFSU2 placed scenery objects'

    CHUNK_ID = 0x00034103
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        instances = (
            records_to_chunk_end(Nfsu2SceneryInstance(), 64),
            {'description': 'Instances'},
        )


class Nfsu2Scenery(ChunkBlock):
    block_description = (
        'NFSU2 scenery of a section: same as in NFSU, with bigger object definitions '
        '(named) and instances (float bounding box). Told apart from NFSU scenery by the definitions: '
        'every NFSU2 one starts with a name'
    )

    CHUNK_ID = 0x80034100

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [NfsuScenerySectionHeader(), Nfsu2SceneryInfos(), Nfsu2SceneryInstances(), ZeroChunk()],
            'Header, definitions, instances and unknown chunks 0x00034104, 0x00034105, 0x00034106',
        )

    def matches_chunk(self, ctx) -> bool:
        infos = peek_sub_chunk_payload(ctx, 0x00034102)
        return infos is not None and _nfsu2_scenery_info_names_ok(infos)


def _nfsmw_scenery_info_names_ok(infos_payload: bytes) -> bool:
    return (
        len(infos_payload) % 72 == 0
        and len(infos_payload) > 0
        and all(is_name_bytes(infos_payload[i : i + 24]) for i in range(0, len(infos_payload), 72))
        and not _nfsu2_scenery_info_names_ok(infos_payload)
    )


class NfsmwSceneryInfo(DeclarativeCompoundBlock):
    block_description = 'NFSMW scenery object definition: which mesh to draw'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=24), {'description': 'Object name, e.g. "XO_StreetLightCb_1b_00"'})
        mesh_ids = (
            ArrayBlock(child=IntegerBlock(length=4), length=4),
            {
                'description': 'Mesh ids (hashes of mesh names, `mesh_id` of mesh header chunks). The first one is '
                'the main mesh, others are probably levels of detail'
            },
        )
        model_pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=4),
            {'description': 'Filled by the game in runtime', 'is_unknown': True},
        )
        radius = (DecimalBlock(length=4), {'description': 'Bounding sphere radius'})
        mesh_checksum = (IntegerBlock(length=4), {'is_unknown': True})
        hierarchy_name_hash = (IntegerBlock(length=4), {'is_unknown': True})
        hierarchy_pointer = (
            IntegerBlock(length=4),
            {'description': 'Filled by the game in runtime', 'is_unknown': True},
        )


class NfsmwSceneryInfos(ChunkBlock):
    block_description = 'NFSMW scenery object definitions'

    CHUNK_ID = 0x00034102

    class Fields(ChunkBlock.Fields):
        infos = (
            records_to_chunk_end(NfsmwSceneryInfo(), 72),
            {'description': 'Definitions'},
        )


class NfsmwSceneryInstance(DeclarativeCompoundBlock):
    block_description = 'NFSMW placed scenery object'

    class Fields(DeclarativeCompoundBlock.Fields):
        bounding_box_min = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Minimum corner of the bounding box in world coordinates'},
        )
        bounding_box_max = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Maximum corner of the bounding box in world coordinates'},
        )
        exclude_flags = (IntegerBlock(length=4), {'is_unknown': True})
        preculler_info_index = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        lighting_context_number = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position in world coordinates'})
        rotation = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=13, is_signed=True), length=9),
            {
                'description': 'Rotation and scale matrix 3x3, row by row. World position of a mesh vertex v is '
                'v.x * row0 + v.y * row1 + v.z * row2 + position'
            },
        )
        info_index = (IntegerBlock(length=2), {'description': 'Index of the object definition in this scenery'})


class NfsmwSceneryInstances(ChunkBlock):
    block_description = 'NFSMW placed scenery objects'

    CHUNK_ID = 0x00034103
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        instances = (
            records_to_chunk_end(NfsmwSceneryInstance(), 64),
            {'description': 'Instances'},
        )


class NfsmwScenery(ChunkBlock):
    block_description = (
        'NFSMW scenery of a section: object definitions (named, 4 mesh ids) and their '
        'placements in the world. Told apart from NFSU and NFSU2 scenery by the definitions: every one starts '
        'with a 24-byte name'
    )

    CHUNK_ID = 0x80034100

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [NfsuScenerySectionHeader(), NfsmwSceneryInfos(), NfsmwSceneryInstances(), ZeroChunk()],
            'Header, instances, definitions and unknown chunks 0x00034105, 0x00034106, 0x00034107',
        )

    def matches_chunk(self, ctx) -> bool:
        infos = peek_sub_chunk_payload(ctx, 0x00034102)
        return infos is not None and _nfsmw_scenery_info_names_ok(infos)


class NfsuStreamingSection(DeclarativeCompoundBlock):
    block_description = 'Location of a streamed section in the STREAM*.BUN file'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=8), {'description': 'Section name, e.g. "A37"'})
        number = (
            IntegerBlock(length=4),
            {'description': 'Section number: letter index (A = 1) * 100 + number. Some have flag 0x10000 set'},
        )
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset of the section in the stream file'})
        size = (IntegerBlock(length=4), {'description': 'Size of the section in the stream file'})
        size2 = (
            IntegerBlock(length=4),
            {'description': 'Equals to `size` unless the section has textures, then a bit smaller', 'is_unknown': True},
        )
        hash = (IntegerBlock(length=4), {'is_unknown': True})
        unk2 = (BytesBlock(length=20), {'is_unknown': True})


class NfsuStreamingSections(ChunkBlock):
    block_description = (
        'Table of streamed sections: where the world sections of the race lie in the '
        'STREAM*.BUN file. NFSU2 has another chunk with this id'
    )

    CHUNK_ID = 0x00034107

    class Fields(ChunkBlock.Fields):
        sections = (
            records_to_chunk_end(NfsuStreamingSection(), 56),
            {'description': 'Sections'},
        )

    def matches_chunk(self, ctx) -> bool:
        # NFSU2 has another chunk with this id (8-byte records), its sections table is chunk 0x00034110
        if peek_chunk_length(ctx) % 56:
            return False
        name = peek_chunk_payload(ctx, 8)
        return len(name) == 8 and name[0] != 0 and is_name_bytes(name)


class Nfsu2StreamingSection(DeclarativeCompoundBlock):
    block_description = 'NFSU2: location of a streamed section in the STREAM*.BUN file'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=8), {'description': 'Section name, e.g. "A37"'})
        number = (
            IntegerBlock(length=4),
            {'description': 'Section number: letter index (A = 1) * 100 + number'},
        )
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4), {'description': '1, except the first section "--"', 'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset of the section in the stream file'})
        size = (
            IntegerBlock(length=4),
            {'description': 'Size of the section in the stream file, without padding to 2048 bytes'},
        )
        size2 = (
            IntegerBlock(length=4),
            {'description': 'Equals to `size` unless the section has textures, then smaller', 'is_unknown': True},
        )
        unk2 = (
            IntegerBlock(length=4),
            {'description': 'Section number + 10000 or 20000 (or 20000 for "--")', 'is_unknown': True},
        )
        center = (
            ArrayBlock(child=DecimalBlock(length=4), length=2),
            {'description': 'Presumably the center of the section (X, Y) in world coordinates', 'is_unknown': True},
        )
        radius = (DecimalBlock(length=4), {'description': 'Presumably radius of the section', 'is_unknown': True})
        hash = (IntegerBlock(length=4), {'is_unknown': True})
        unk3 = (BytesBlock(length=28), {'is_unknown': True})


class Nfsu2StreamingSections(ChunkBlock):
    block_description = (
        'NFSU2 table of streamed sections: where the world sections of the location lie in the STREAM*.BUN file'
    )

    CHUNK_ID = 0x00034110

    class Fields(ChunkBlock.Fields):
        sections = (
            records_to_chunk_end(Nfsu2StreamingSection(), 80),
            {'description': 'Sections'},
        )


def _section_names_ok(ctx, record_size: int) -> bool:
    length = peek_chunk_length(ctx)
    if length == 0 or length % record_size:
        return False
    payload = peek_chunk_payload(ctx, length)
    return all(is_name_bytes(payload[i : i + 8]) for i in range(0, length, record_size))


class NfsmwStreamingSection(DeclarativeCompoundBlock):
    block_description = 'NFSMW: location of a streamed section in the STREAM*.BUN file'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=8), {'description': 'Section name, e.g. "T26"'})
        number = (IntegerBlock(length=4), {'description': 'Section number: letter index (A = 1) * 100 + number'})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4), {'description': 'Always 1', 'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset of the section in the stream file'})
        size = (
            IntegerBlock(length=4),
            {'description': 'Size of the section in the stream file, without padding to 2048 bytes'},
        )
        size2 = (IntegerBlock(length=4), {'description': 'Always equals to `size`', 'is_unknown': True})
        size3 = (
            IntegerBlock(length=4),
            {'description': 'Equals to `size` unless the section has textures, then smaller', 'is_unknown': True},
        )
        unk2 = (
            IntegerBlock(length=4),
            {'description': 'Section number + 2000, 4000 ... 22000 (10, 20, 30 for X0, Z0, Y0)', 'is_unknown': True},
        )
        center = (
            ArrayBlock(child=DecimalBlock(length=4), length=2),
            {'description': 'Presumably the center of the section (X, Y) in world coordinates', 'is_unknown': True},
        )
        radius = (DecimalBlock(length=4), {'description': 'Presumably radius of the section', 'is_unknown': True})
        hash = (IntegerBlock(length=4), {'is_unknown': True})
        unk3 = (BytesBlock(length=36), {'is_unknown': True})


class NfsmwStreamingSections(ChunkBlock):
    block_description = (
        'NFSMW table of streamed sections: where the world sections of the location lie in the STREAM*.BUN file'
    )

    CHUNK_ID = 0x00034110

    class Fields(ChunkBlock.Fields):
        sections = (
            records_to_chunk_end(NfsmwStreamingSection(), 92),
            {'description': 'Sections'},
        )

    def matches_chunk(self, ctx) -> bool:
        return _section_names_ok(ctx, 92) and not _section_names_ok(ctx, 80)


# NFS Underground race paths (TRACKS/TRACKBnnnn.lzc): the race route is path 0 of the track paths chunk 0x80034147,
# laid out as NFS Hot Pursuit 2 (PS2)'s; the roads of the race (with heights and lanes) are chunk 0x34121


def _sub_chunk_lengths(ctx) -> Dict[int, int]:
    """Sub-chunk id -> payload length of the container chunk at the buffer position, empty if its payload is not a
    whole number of chunks"""
    chunks = peek_sub_chunks(ctx)
    end = ctx.buffer.tell() + 8 + peek_chunk_length(ctx)
    if (chunks[-1].end if chunks else end - peek_chunk_length(ctx)) != end:
        return {}
    return {chunk.id: chunk.length for chunk in chunks}


class NfsuTrackPath(ChunkBlock):
    block_description = (
        'Track paths of a race: the race route (path 0) on the ground plane, a point every '
        '20..300 m, in the layout of NFS Hot Pursuit 2 (PS2). Sub-chunk 0x3414a (180-byte records with '
        'positions, directions and quads, one per race checkpoint or zone?) is not decoded'
    )

    CHUNK_ID = 0x80034147

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [Nfs6Ps2TrackPathHeader(), Nfs6Ps2TrackPathPoints()], 'Header, points and chunk 0x3414a (unknown)'
        )

    def matches_chunk(self, ctx) -> bool:
        # NFSMW keeps other sub-chunks in it: fine as long as the path records and points have their sizes
        lengths = _sub_chunk_lengths(ctx)
        return bool(lengths) and lengths.get(0x00034148, 0) % 40 == 0 and lengths.get(0x00034149, 0) % 20 == 0


class NfsuRoadLane(DeclarativeCompoundBlock):
    block_description = 'Lane record of a road (meaning unknown)'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        flags = (BytesBlock(length=4), {'is_unknown': True})
        value = (DecimalBlock(length=4), {'is_unknown': True, 'description': '999 in unused records'})
        name = (
            UTF8Block(length=40),
            {'is_unknown': True, 'description': 'Text padded with spaces ("GUHLER2KW207023"), empty in unused records'},
        )


class NfsuRoadNode(DeclarativeCompoundBlock):
    block_description = 'Node of a road: a point of its centre line, 4..25 m apart'

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position in world coordinates (Z up)'})
        forward = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Unit direction to the next node on the ground plane'},
        )
        backward = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Unit direction to the previous node on the ground plane'},
        )
        next_length = (DecimalBlock(length=4), {'description': 'Distance to the next node, 4 at the last node'})
        previous_length = (
            DecimalBlock(length=4),
            {'description': 'Distance from the previous node, 4 at the first node'},
        )
        widths = (
            ArrayBlock(child=DecimalBlock(length=4), length=2),
            {'is_unknown': True, 'description': 'Probably the road width to the left and to the right'},
        )
        unk0 = (ArrayBlock(child=DecimalBlock(length=4), length=3), {'is_unknown': True})
        route_distance = (
            DecimalBlock(length=4),
            {
                'description': 'Distance along the race route (from 0 again after the finish line of a circuit, '
                'negative before the start)'
            },
        )
        unk1 = (ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=11), {'is_unknown': True})
        unk2 = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=12),
            {'is_unknown': True, 'description': 'Two groups of 6 values, -1 for none: probably lane offsets'},
        )
        unk3 = (BytesBlock(length=23), {'is_unknown': True})
        unk4 = (BytesBlock(length=2), {'is_unknown': True})
        road_id = (IntegerBlock(length=1), {'description': 'Low byte of the road id'})
        flags = (BytesBlock(length=4), {'is_unknown': True})


NFSU_ROAD_HEADER_SIZE = 0x27C
NFSU_ROAD_NODE_SIZE = 136


class NfsuRoad(DeclarativeCompoundBlock):
    block_description = (
        'Road of a race: a polyline of nodes with heights. The roads of the race route '
        'follow it (several roads one after another, an end of a road lies on another road), with its shortcuts '
        'and parallel lanes (drag races); roads with id 100 and above are side streets reaching or crossing them'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True, 'description': 'Always 11'})
        unk1 = (IntegerBlock(length=2), {'is_unknown': True, 'description': 'Always 1'})
        road_id = (IntegerBlock(length=2), {'description': 'Id of the road in the race (not in the city)'})
        is_side_road = (
            IntegerBlock(length=4),
            {
                'description': '1 on roads with id 100 and above: side streets reaching or crossing the roads of the race'
            },
        )
        num_nodes = (
            IntegerBlock(length=2, programmatic_value=CountOf('nodes')),
            {'usage': 'io,doc', 'description': 'Amount of nodes'},
        )
        unk2 = (IntegerBlock(length=2), {'is_unknown': True, 'description': 'Always `num_nodes`'})
        unk3 = (IntegerBlock(length=4), {'is_unknown': True, 'description': 'Always 1'})
        unk4 = (BytesBlock(length=8), {'is_unknown': True})
        bounding_box_min = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Minimum x, y of the node positions'},
        )
        bounding_box_max = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Maximum x, y of the node positions'},
        )
        lanes = (
            ArrayBlock(child=NfsuRoadLane(), length=11),
            {'is_unknown': True, 'description': 'Lane records: 4, a separator, 4, a separator, an end'},
        )
        unk5 = (BytesBlock(length=16), {'is_unknown': True})
        nodes = (ArrayBlock(child=NfsuRoadNode(), length='num_nodes'), {'description': 'Nodes'})


class NfsuRoads(RecordsChunk):
    block_description = 'Roads of a race (AI and traffic roads?): the race route and its shortcuts, side streets'

    CHUNK_ID = 0x00034121
    RECORD_HEADER_SIZE = NFSU_ROAD_HEADER_SIZE

    @staticmethod
    def record_size(payload: bytes, pos: int) -> Optional[int]:
        if payload[pos : pos + 8] != b'\x0b\0\0\0\x0b\0\0\0':
            return None
        return NFSU_ROAD_HEADER_SIZE + NFSU_ROAD_NODE_SIZE * int.from_bytes(payload[pos + 16 : pos + 18], 'little')

    class Fields(RecordsChunk.Fields):
        roads = (records_to_chunk_end(NfsuRoad()), {'description': 'Roads'})


NFSU_BUNDLE_CHUNK_BLOCKS = [
    ZeroChunk(),
    NfsuBinGeometry(whole_file=False),
    NfsuTexturePack(),
    NfsmwScenery(),
    Nfsu2Scenery(),
    NfsuScenery(),
    NfsuStreamingSections(),
    NfsmwStreamingSections(),
    Nfsu2StreamingSections(),
    NfsuTrackPath(),
    NfsuRoads(),
    Nfsu2Roads(),
    NfsmwRoadNetwork(),
]


class NfsuChunkBundle(DeclarativeCompoundBlock):
    block_description = (
        'Chunk bundle (*.BUN, *.BIN, uncompressed *.lzc): a sequence of chunks, each '
        'having 32-bit id, 32-bit payload length and payload; chunks with the highest bit '
        'of id set are containers of other chunks. Geometry packs, texture packs, scenery, '
        'streaming sections table, track paths and roads (NFSU races), roads (NFSU2 Routes*.bin), the road '
        'network (NFSMW L2RA.BUN) are decoded, other chunks are kept as raw bytes'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        chunks = chunks_field(
            NFSU_BUNDLE_CHUNK_BLOCKS, 'Chunks', byte_length=(bytes_remaining, 'until the end of file')
        )


class NfsuTrackBundle(NfsuChunkBundle):
    serializer = 'NfsuTrackBundleSerializer'

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Race bundle (NFSU TRACKS/TRACKBnnnn.lzc, uncompressed) or location bundle (NFSU2 '
            'TRACKS/L4RA.BUN, NFSMW TRACKS/L2RA.BUN): a chunk bundle with the streaming sections table of the world, which is stored in '
            'TRACKS/STREAM*.BUN. ' + super().schema['block_description'],
        }

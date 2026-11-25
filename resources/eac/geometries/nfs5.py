from os import SEEK_CUR

from library.context import ReadContext, WriteContext
from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    BytesBlock,
    DelegateBlock,
    DecimalBlock,
    MagicDispatchBlock,
    SubByteCompoundBlock,
    CountOf,
    SizeOf,
    REMAINING,
)
from library.read_blocks.misc.value_validators import Eq, Or
from library.read_blocks.strings import NullTerminatedUTF8Block
from resources.eac.archives.shpi_block import ShpiBlock
from resources.eac.fields.misc import Point3D

# CRP = an EAGL chunk tree (Porsche.exe, nfs-web `decomp/nfs5/Porsche.exe.gzf`; chunk search 0x59f7c0 / 0x59f5e0,
# children 0x59f870, leaf data 0x43c6d0). Every chunk is 16 bytes {u32 id, u32 info, u32 count, u32 offset}: TailsLab
# splits the id into a 2-char identifier and a 16-bit index (`idx` / `part_info`) or reads a 4-char identifier, and
# the info word into its low byte (`unk0` of the parts) and a 24-bit data length (`len`). Info bit 0x1: the id's low
# 16 bits are an index, the type is `id & 0xffff2020 | 0x2020`; bit 0x2: `offset` is relative to the chunk; bit 0x8
# (containers): children sorted by id, found by binary search (unsigned compare); `info >> 5` (containers): leading
# children that are not searched (the header: its articles). `offset` is in 16-byte units for the children of a
# container (header, article) and in bytes for the data of a leaf (part).
_CHUNK_INFO_DESCRIPTION = (
    'Low byte of the chunk info word: bit 0x1 = the low 16 bits of the id are an index (`idx` / `part_info`), bit 0x2 '
    '= `offset` is relative to this chunk (Porsche.exe 0x59f7c0, 0x43c6d0). The other bits (0x8..0x80, e.g. 3, 11, '
    '19, 27 on track `tv` / `vu` / `fd` parts of the levels of detail 0..3, 0x80 more on some) are not known'
)
_CHUNK_COUNT_DESCRIPTION = 'Count of the chunk (records in its data, the meaning depends on the part type)'

# fields of the parts: `part_info` (the 16-bit index of a mesh part), `unk0` (low byte of the info word), `offset`
_PART_INFO = (
    SubByteCompoundBlock(
        length=2,
        schema=[
            (4, 'damage', 'number', [], 'Damage switch (0x8 means damaged)'),
            (8, 'animation_index', 'number', [], 'animation index'),
            (4, 'lod', 'number', [], 'Level of detail'),
        ],
    ),
    {'description': 'Part matching info. Part should be used with others that have same values'},
)
_PART_UNK0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
_PART_OFFSET = (
    IntegerBlock(length=4),
    {'usage': 'io,doc', 'description': 'Data offset in bytes, relative to this part (the data is 16-byte aligned)'},
)


def crp_array_part_fields(child, count_name: str, count_description: str, data_description: str = None) -> tuple:
    """The fields after the id of a part holding an array of `child` records, to unpack into its `Fields` class:
    `unk0, len, <count_name>, offset, data = crp_array_part_fields(...)` (info byte, data length, record count, data
    offset, the records)"""
    return (
        _PART_UNK0,
        (IntegerBlock(length=3, programmatic_value=SizeOf('data')), {'description': 'Data length in bytes'}),
        (IntegerBlock(length=4, programmatic_value=CountOf('data')), {'description': count_description}),
        _PART_OFFSET,
        (
            ArrayBlock(length=count_name, child=child),
            {'usage': 'ui', **({'description': data_description} if data_description else {})},
        ),
    )


class CrpDamageZone(DeclarativeCompoundBlock):
    block_description = 'The vertices of one damage zone (Porsche.exe R3DCarLOD_Damage 0x43e390)'

    class Fields(DeclarativeCompoundBlock.Fields):
        zone = (
            IntegerBlock(length=4),
            {
                'description': 'Damage zone (car+0x4e4[zone], 0..100): 0..7 the ring around the body (0 front left, '
                "1 front, 2 front right, 3 right, 4 rear right, 5 rear, 6 rear left, 7 left; the left is the CRP's "
                "+x, the driver's side: zone 7 holds `DecalDoorL`; Car_HitDamage 0x494df0 picks them), 8 the roof, "
                '9 the underside'
            },
        )
        num_vertices = (IntegerBlock(length=4), {'description': 'Number of vertices in the zone'})
        first_index = (
            IntegerBlock(length=4),
            {'description': 'First of them in `vertex_indices` (the vertex counts of the zones before)'},
        )


class CrpDamageZonesData(DeclarativeCompoundBlock):
    block_description = (
        'The damage zone of every vertex of a `vt` part (each vertex in one zone). A damaged zone moves its vertices '
        "by the damaged `vt` part's offsets x min(1, zone damage x 0.02) (Porsche.exe R3DCarLOD_Damage 0x43e390)"
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        num_zones = (IntegerBlock(length=4, programmatic_value=CountOf('zones')), {'description': 'Number of zones'})
        zones = (ArrayBlock(child=CrpDamageZone(), length='num_zones'), {'description': 'The zones'})
        vertex_indices = (
            ArrayBlock(child=IntegerBlock(length=4), byte_length=REMAINING),
            {'description': 'Vertex indices (of the `vt` part) of the zones, zone after zone'},
        )


class CrpDamageZonesPart(DeclarativeCompoundBlock):
    block_description = (
        'Part "zd" (cars): the damage zones of the vertices of the `vt` part with the same index '
        '([CrpDamageZonesData](#crpdamagezonesdata)); Porsche.exe finds it by the `vt` part index (0x59f2a0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (
            IntegerBlock(length=2),
            {'description': 'Index of the `vt` part (its `part_info`) whose vertices these are'},
        )
        identifier = (UTF8Block(length=2, value_validator=Eq('zd')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (IntegerBlock(length=3, programmatic_value=SizeOf('data')), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION + ': the number of zones'})
        offset = _PART_OFFSET
        data = (CrpDamageZonesData(), {'usage': 'ui'})


class UnkPart2(DeclarativeCompoundBlock):
    block_description = 'Unknown part with index and 2-chars identifier'

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Eq('ns')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION})
        offset = _PART_OFFSET
        data = (BytesBlock(length='len'), {'usage': 'ui'})


class UnkPart4(DeclarativeCompoundBlock):
    block_description = 'Unknown part with 4-chars identifier'

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (
            UTF8Block(
                length=4,
                value_validator=Or(['PdnB', 'htMR', 'odnW', 'nAmC', 'cseD', ' siV', '', 'minA', 'tqnA']),
            ),
            {
                'description': 'Identifier. `tqnA` ("Anqt", 0x416e7174): the article goes to the animated bundle '
                '(Porsche.exe 0x4777f0)'
            },
        )
        unk0 = _PART_UNK0
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION})
        offset = _PART_OFFSET
        data = (BytesBlock(length='len'), {'usage': 'ui'})


class MaterialPartData(DeclarativeCompoundBlock):
    block_description = (
        'A material, data structure is mostly unknown. Triangle parts reference it by '
        'index (`idx` of [MaterialPart](#materialpart))'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        surface_flags = (
            IntegerBlock(length=4),
            {
                'description': 'Surface flags of the faces drawn with this material, the collision faces keep the '
                'low 16 bits (Porsche.exe 0x4750b0 via the material list 0x44a770): `& 0xf` = the surface type '
                '(0 = not a road face for the face search); faces with only bits 4..7 set (`flags & 0xffffff0f == '
                '0`: 0, 0x10, 0x20, 0x30, 0x50, 0x60) are left out of the collision tree, and these bits are the '
                'flags of the wall edges built from them (`.edg`, [Nfs5WallEdge](#nfs5walledge)); 0x8000 is counted '
                'by the loader. Tracks: 0, 1, 2, 3, 5, 8, 9, 0x10, 0x20, 0x30, 0x50, 0x60, 0xc000, 0xc001, 0xc002, '
                '0xc004, 0xc005, 0xc007; 0 in every car material'
            },
        )
        unk0 = (BytesBlock(length=4), {'is_unknown': True})
        texture_flags = (
            IntegerBlock(length=4),
            {
                'is_unknown': True,
                'description': 'When the low 16 bits are 0, Porsche.exe 0x44a770 uses the 4-char name "XETN" '
                'instead of `tex_page_index` (no game file has such a material). 0x60003 in every car material',
            },
        )
        unk3 = (BytesBlock(length=4), {'is_unknown': True})
        desc = (UTF8Block(length=16), {'description': 'Description'})
        unk1 = (BytesBlock(length=8), {'is_unknown': True})
        tex_page_index = (
            IntegerBlock(length=4),
            {
                'description': "Texture reference. Cars: 0-based texture page index (page N+1 in car's .tpg "
                'file, embedded FSH part with `idx` M is .tpg file M+1). Tracks: 4-char name of the '
                "texture in track's FSH file, stored as integer"
            },
        )
        unk2 = (BytesBlock(length=0x10C), {'is_unknown': True})


class MaterialPart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to [MaterialPartData](#materialpartdata) block'

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier'})
        identifier = (UTF8Block(length=2, value_validator=Eq('tm')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(length=3),
            {
                'description': 'Data length in bytes: 76..312 in the game files; `data` is read as 312 bytes, past a '
                'shorter length into the bytes after it, and written up to the length'
            },
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = _PART_OFFSET
        data = (MaterialPartData(), {'usage': 'ui'})


class FSHPart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to an array of [ShpiBlock](#shpiblock) blocks'

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier'})
        identifier = (UTF8Block(length=2, value_validator=Eq('fs')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(
                length=3,
                programmatic_value=lambda ctx: sum(
                    ShpiBlock().estimate_packed_size(shpi, None) for shpi in ctx.data('data')
                ),
            ),
            {'usage': 'io,doc', 'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=CountOf('data')),
            {'description': 'Number of SHPI blocks'},
        )
        offset = _PART_OFFSET
        data = (ArrayBlock(child=ShpiBlock(), length='num_data'), {'usage': 'ui'})


class TextPart2(DeclarativeCompoundBlock):
    block_description = 'A part referencing to text with index and 2-chars identifier'

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Eq('ns')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) + 1),
            {'description': 'Data length in bytes, equals to `text length + 1` (0x00 terminating byte)'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = _PART_OFFSET
        data = (NullTerminatedUTF8Block(length=None), {'usage': 'ui'})


class TextPart4(DeclarativeCompoundBlock):
    block_description = 'A part referencing to text with 4-chars identifier'

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Or(['emaN', 'cseD'])), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) + 1),
            {'description': 'Data length in bytes, equals to `text length + 1` (0x00 terminating byte)'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = _PART_OFFSET
        data = (NullTerminatedUTF8Block(length=None), {'usage': 'ui'})


class CullingPartData(DeclarativeCompoundBlock):
    block_description = 'Polygon culling rule?'

    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Normalized direction vector (plane normal?)'},
        )
        threshold = (DecimalBlock(length=4), {'description': 'Threshold value (plane distance?)'})


class CullingPart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to an array of [CullingPartData](#cullingpartdata) blocks'

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('n$')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(
            CullingPartData(),
            'num_data',
            'Number of culling part data blocks',
        )


class TransformationPart(DeclarativeCompoundBlock):
    block_description = (
        'A part referencing to a transformation matrix. If exists, matrix should be '
        'applied to the meshes of the same article with the same LOD. Matrix is a 4x4 '
        'matrix in column-major order (elements 12, 13, 14 are the translation), where '
        'each number is stored as 4-bytes float number (little-endian). On tracks, the `rt` part 0 of an '
        'article puts it into the instance bundle (Porsche.exe 0x4781a0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('rt')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (IntegerBlock(length=3, value_validator=Eq(0x40)), {'description': 'Data length in bytes'})
        unk_1 = (
            IntegerBlock(length=4),
            {'is_unknown': True, 'description': 'Always 1? Number of Transformation Matrices?'},
        )
        offset = _PART_OFFSET
        data = (ArrayBlock(length=16, child=DecimalBlock(length=4)), {'usage': 'ui'})


class VertexData(DeclarativeCompoundBlock):
    block_description = 'Represents single vertex'

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position'})
        unk = (DecimalBlock(length=4), {'is_unknown': True})


class VertexPart(DeclarativeCompoundBlock):
    block_description = (
        'A part referencing to an array of [VertexData](#vertexdata) blocks, representing'
        ' mesh vertices. Every vertex part of an article produces a separate mesh, '
        'combined with the triangle, UV and transformation parts of the same LOD. For a '
        'damaged part (damage == 8) vertex positions are offsets, which are added to '
        'vertices of the undamaged part with the same LOD and animation index'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('tv')), {'description': 'Identifier'})
        unk0, len, num_vertices, offset, data = crp_array_part_fields(
            VertexData(),
            'num_vertices',
            'Number of vertices',
        )


class NormalPartData(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (Point3D(child=DecimalBlock(length=4)), {'description': 'Normal vector'})
        unk = (DecimalBlock(length=4), {'is_unknown': True})


class NormalPart(DeclarativeCompoundBlock):
    block_description = (
        'A part referencing to an array of [NormalPartData](#normalpartdata) blocks, describing mesh normals'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('mn')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(NormalPartData(), 'num_data', 'Number of normals')


class UVData(DeclarativeCompoundBlock):
    block_description = 'Texture coordinates of a vertex'

    class Fields(DeclarativeCompoundBlock.Fields):
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})


class UVPart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to an array of [UVData](#uvdata) blocks, representing texture coordinates'

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('vu')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(
            UVData(),
            'num_data',
            'Amount of UVData blocks, equals to len / 8',
        )


_ROW_TYPE_DESCRIPTION = (
    'Data stream of the row (Porsche.exe 0x5a0c50 / 0x5a0bc0): below 0x100 an index into the part types `vt` (0, '
    'vertices), `nm` (1, normals), `uv` (2), `fd` (3, vertex colours), `Base` (4), `pr` (5), `fe` (6); else a 2-char '
    'part type (`n$`). Cars: rows 1 (`nm`), 2 (`uv`), 0 (`vt`) after the culling row; tracks: 3 (`fd`), 2, 0, and 0, '
    '1, 2, 3 in the 4-row parts'
)
_INDEX_STREAM_DESCRIPTION = (
    'Index row of the part whose index table the stream uses: 0 = the first one, 1 = the second one; 0xffff = '
    'consecutive indices: position i of the part is entry i of the stream (Porsche.exe 0x5a0bc0). Cars: `vt` and `nm` '
    'rows 0 (`vI`), `uv` rows 1 (`uI`), or 0 in the parts whose only index row is `uI`; tracks: `vt` 0, `uv` 1, `fd` '
    '0xffff; 0xffff for every row of a part without index rows'
)


class TriangleInfoRowBase(DeclarativeCompoundBlock):
    block_description = (
        'Info row of [TrianglePartData](#trianglepartdata), 16 bytes: the layout of every '
        'row, read for the stream types without a block of their own (4 `Base`, 5 `pr`, 6 `fe`; in no game '
        'file)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {
                'description': 'Offset in the data of the stream, in bytes: `vt` / `nm` rows / 16 = index of the '
                'first vertex / normal, `uv` rows / 8, `fd` rows / 4 = index of the first colour; added to the '
                'values of the index table (Porsche.exe 0x5a0c50)'
            },
        )
        length_used = (IntegerBlock(length=2), {'description': 'Length used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class CullingInfoRow(DeclarativeCompoundBlock):
    block_description = 'Info row referencing the culling data used by the triangle part'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset in culling data'})
        length_used = (IntegerBlock(length=2), {'description': 'Length of culling data used'})
        identifier = (
            UTF8Block(length=2),
            {'description': 'Row type as 2 characters: "n$" (cars). ' + _ROW_TYPE_DESCRIPTION},
        )
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class VertexInfoRow(DeclarativeCompoundBlock):
    block_description = 'Info row referencing the vertex data (`vt` part, `row_type` 0) used by the triangle part'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {
                'description': 'Offset in vertex data in bytes. offset / 16 is the index '
                'of the first vertex used by the part; it is added to all '
                'values of the vertex index table'
            },
        )
        length_used = (IntegerBlock(length=2), {'description': 'Length of vertex data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class NormalInfoRow(DeclarativeCompoundBlock):
    block_description = 'Info row referencing the normals data (`nm` part, `row_type` 1) used by the triangle part'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset in normal data'})
        length_used = (IntegerBlock(length=2), {'description': 'Length of normal data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class UVInfoRow(DeclarativeCompoundBlock):
    block_description = 'Info row referencing the UV data (`uv` part, `row_type` 2) used by the triangle part'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset in uv data'})
        length_used = (IntegerBlock(length=2), {'description': 'Length of uv data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class VertexColorInfoRow(DeclarativeCompoundBlock):
    block_description = (
        'Info row referencing the vertex colours ([CrpVertexColorPart](#crpvertexcolorpart) '
        '`fd`, `row_type` 3, tracks only) used by the triangle part'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {'description': 'Offset in the vertex colours in bytes: offset / 4 is the index of the first colour'},
        )
        length_used = (IntegerBlock(length=2), {'description': 'Length of vertex colour data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


# info row block (index in `info_rows` possible blocks) by row type: 0 `vt`, 1 `nm`, 2 `uv`, 3 `fd`
_INFO_ROW_BLOCKS_BY_TYPE = {0: 3, 1: 1, 2: 2, 3: 4}
(_CULLING_INFO_ROW, _OTHER_INFO_ROW) = (0, 5)


def determine_triangle_info_row_type(ctx, **_):
    """Picks the info row block by the row type (u16 at +10 of the row)"""
    ctx.buffer.seek(10, SEEK_CUR)
    row_type = int.from_bytes(ctx.buffer.read(2), 'little')
    ctx.buffer.seek(-12, SEEK_CUR)
    if row_type >= 0x100:
        return _CULLING_INFO_ROW
    return _INFO_ROW_BLOCKS_BY_TYPE.get(row_type, _OTHER_INFO_ROW)


class IndexRow(DeclarativeCompoundBlock):
    block_description = (
        'Descriptor of an index stream (vertex indices or UV indices) of the triangle part: '
        'the info rows refer to it by its position (`index_stream`)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'Row index'})
        identifier = (UTF8Block(length=2), {'description': 'Identifier "vI"|"Iv" – vertex index, "uI"|"Iu" - uv index'})
        offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of indices: the position of the first index of this stream in the index tables'},
        )


class TrianglePartData(DeclarativeCompoundBlock):
    block_description = (
        'A description of mesh geometry (faces): `num_data` positions forming primitives '
        'of `primitive_type`, each corner taking its vertex, normal, UV and colour from the streams of the info '
        'rows; primitive k uses the positions from step x k on (Porsche.exe 0x5a0bc0). The converter exports '
        'triangle lists as they are, strips with every second triangle reversed (k odd: positions k + 1, k, '
        'k + 2, as Direct3D draws strips; triangles repeating a vertex, the joints of the strips, left out), '
        'quads as the triangles 0 1 2 and 0 2 3 (as the collision splits them, Porsche.exe 0x4750b0), no lines'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        primitive_type = (
            IntegerBlock(length=2, value_validator=Or([1, 2, 3, 4])),
            {
                'description': 'Primitive type (Porsche.exe tables 0x5e5138 / 0x5e514c / 0x5e5160): 1 = triangle '
                'strip (3 indices, step 1), 2 = lines (2 indices, step 2), 3 = triangle list (step 3), 4 = quad list '
                '(4 indices, step 4). Primitive count from `num_data` n of the part: ((n - indices per primitive) '
                '>> log2(step)) + 1, n / 3 for type 3. Cars: 3 only; tracks: 3, 1 (506 parts), 4 (435 parts, none with '
                'index rows)'
            },
        )
        flags = (
            IntegerBlock(length=2),
            {'is_unknown': True, 'description': 'Flags: 0, 1, 2, 4, 0x200, 0x201, 0x202, 0x204'},
        )
        material_index = (
            IntegerBlock(length=2),
            {'description': 'Material index: the [MaterialPart](#materialpart) with this `idx`'},
        )
        unk0 = (IntegerBlock(length=2), {'is_unknown': True})
        unk_floats = (ArrayBlock(length=4, child=DecimalBlock(length=4)), {'is_unknown': True})
        unk_zeros = (BytesBlock(length=16), {'is_unknown': True})
        num_info_rows = (
            IntegerBlock(length=4),
            {'programmatic_value': lambda ctx: len(ctx.data('info_rows')), 'description': 'Number of info rows'},
        )
        num_index_rows = (
            IntegerBlock(length=4),
            {'programmatic_value': lambda ctx: len(ctx.data('index_rows')), 'description': 'Number of index rows'},
        )
        info_rows = (
            ArrayBlock(
                length='num_info_rows',
                child=DelegateBlock(
                    possible_blocks=[
                        CullingInfoRow(),
                        NormalInfoRow(),
                        UVInfoRow(),
                        VertexInfoRow(),
                        VertexColorInfoRow(),
                        TriangleInfoRowBase(),
                    ],
                    choice_index=(determine_triangle_info_row_type, 'by `row_type` (u16 at +10 of the row)'),
                ),
            ),
            {
                'description': 'Descriptors of the data streams used by this part (Porsche.exe 0x5a0c50), the row '
                'block picked by `row_type`: cars have `n$`, `nm`, `uv`, `vt` and `nm`, `uv`, `vt`; tracks `fd`, '
                '`uv`, `vt` (73527 parts) and `vt`, `nm`, `uv`, `fd` (773 parts, without index rows; their `nm` rows '
                'point at no `nm` part). Position i of the part: vertex index = (byte i of the index table of the `vt` '
                "row's `index_stream`, or i for 0xffff) + `vt` row offset / 16, the same for UVs (offset / 8) and "
                'colours (offset / 4); the collision reads only the `vt` and `fd` rows'
            },
        )
        index_rows = (
            ArrayBlock(length='num_index_rows', child=IndexRow()),
            {
                'description': 'Descriptors of the index streams, one per index table: `vI` (vertex and normal '
                'indices) and `uI` (UV indices); cars also have parts with `uI` alone (129) and tracks with `vI` '
                'alone (224), 1233 parts have none (their streams use consecutive indices)'
            },
        )
        index_table = (
            ArrayBlock(
                length=(
                    lambda ctx: ctx.data('../num_data') if ctx.data('num_index_rows') >= 1 else 0,
                    '^num_data if num_index_rows > 0, else 0',
                ),
                child=IntegerBlock(length=1),
            ),
            {
                'description': 'Index table of the first index row (`vI`, or `uI` when it is the only one): one byte '
                'per position, used by the info rows with `index_stream` 0'
            },
        )
        uv_index_table = (
            ArrayBlock(
                length=(
                    lambda ctx: ctx.data('../num_data') if ctx.data('num_index_rows') >= 2 else 0,
                    '^num_data if num_index_rows > 1, else 0',
                ),
                child=IntegerBlock(length=1),
            ),
            {
                'description': 'Index table of the second index row (`uI`): one byte per position, used by the info '
                'rows with `index_stream` 1 (the UV row: index of the UV in the UV part of the same LOD)'
            },
        )


class TrianglePart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to [TrianglePartData](#TrianglePartData) block, describes mesh faces'

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
            SubByteCompoundBlock(
                length=2,
                schema=[
                    (4, 'lod', 'number', [], 'Level of detail'),
                    (8, 'unk', 'number', [], 'unknown'),
                    (4, 'part_index', 'number', [], 'part index'),
                ],
            ),
            {'description': 'Part matching info. Part should be used with others that have same values'},
        )
        identifier = (UTF8Block(length=2, value_validator=Eq('rp')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (IntegerBlock(length=3, programmatic_value=SizeOf('data')), {'description': 'Data length in bytes'})
        num_data = (IntegerBlock(length=4), {'description': 'Number of indices (size of each index table in the data)'})
        offset = _PART_OFFSET
        data = (TrianglePartData(), {'usage': 'ui'})


class EffectPartData(DeclarativeCompoundBlock):
    block_description = (
        'An effect of an article. Type 5 is a light glare of a car, drawn while its light is on (Porsche.exe '
        "R3DCarLOD_DrawGlares 0x43d800, the sprite 0x43cdd0): the light is the article's `light` (base part, "
        "[CrpBasePartData](#crpbasepartdata)), the glare follows the article's pivot"
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (
            IntegerBlock(length=4),
            {
                'is_unknown': True,
                'description': 'Effect type: 5 = a light glare (Porsche.exe 0x43d800 draws only these on cars)',
            },
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position'})
        unk_scale = (DecimalBlock(length=4), {'is_unknown': True})
        width = (Point3D(child=DecimalBlock(length=4)), {'description': 'Width relative to position'})
        unk2 = (DecimalBlock(length=4), {'is_unknown': True})
        height = (Point3D(child=DecimalBlock(length=4)), {'description': 'Height relative to position'})
        unk3 = (DecimalBlock(length=4), {'is_unknown': True})
        depth = (Point3D(child=DecimalBlock(length=4)), {'description': 'Depth relative to position'})
        unk4 = (DecimalBlock(length=4), {'is_unknown': True})
        glow_color = (IntegerBlock(length=4), {'description': 'Color of glow (BGRA)'})
        source_color = (IntegerBlock(length=4), {'description': 'Color of source (BGRA)'})
        mirror = (
            IntegerBlock(length=4),
            {
                'description': 'Flags: bit 3 (8) = the glare is drawn a second time mirrored to the other side (x, '
                'the width / height / depth x negated), for the light `mirror_light` (Porsche.exe 0x43d800)'
            },
        )
        info_unk0 = (IntegerBlock(length=1), {'is_unknown': True})
        info_unk1 = (IntegerBlock(length=1), {'is_unknown': True})
        mirror_light = (
            IntegerBlock(length=1),
            {
                'description': 'Light index of the mirrored copy (`mirror` bit 3; car lights: see `light` of the base part)'
            },
        )
        night_flare = (
            IntegerBlock(length=1),
            {
                'description': 'Not 0: in a race at night the glare also draws its flare on the road (Porsche.exe '
                '0x43d4f0, while 0x628a28 > 0)'
            },
        )


class EffectPart(DeclarativeCompoundBlock):
    block_description = 'A part referencing to an array of [EffectPartData](#effectpartdata) blocks'

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = _PART_INFO
        identifier = (UTF8Block(length=2, value_validator=Eq('fe')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(length=3),
            {
                'description': 'Data length in bytes: 44, 56, 72 or 88 in the game files; `data` is read as 88 bytes, '
                'past a shorter length into the bytes after it, and written up to the length'
            },
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = _PART_OFFSET
        data = (EffectPartData(), {'usage': 'ui'})


class CrpBaseLodRecord(DeclarativeCompoundBlock):
    block_description = (
        'A level of detail of an article: the `pr` parts drawn at it and their vertex '
        'data, 12 bytes (Porsche.exe 0x4750b0, 0x474cb0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        has_faces = (
            IntegerBlock(length=1),
            {'description': 'Not 0: the level has faces (the collision builds them from it). 1 on every track record'},
        )
        unk0 = (
            IntegerBlock(length=1),
            {'is_unknown': True, 'description': '0 or 1 (1 on the car effect articles, flags 0x600)'},
        )
        unk1 = (IntegerBlock(length=2), {'is_unknown': True, 'description': '0 in every file'})
        first_part = (
            IntegerBlock(length=2),
            {
                'description': 'First `pr` part of the level: the 16-bit index of a [TrianglePart](#trianglepart) '
                '(its `part_info`, the level in the high 4 bits): 0x1000 x level'
            },
        )
        end_part = (
            IntegerBlock(length=2),
            {
                'description': 'End of the `pr` part range (`part_info` values up to this one, 0x0fff + 0x1000 x '
                'level; Porsche.exe takes the first part with index <= it)'
            },
        )
        vertex_part = (
            IntegerBlock(length=2),
            {'description': 'Index of the `vt` / `fd` part of the level (`part_info` index)'},
        )
        unk2 = (
            IntegerBlock(length=2),
            {
                'is_unknown': True,
                'description': 'Track levels: 30..10000 (150, 250, 1000, 10000 the most common), 0xffff on cars: '
                'probably the distance the level is drawn to',
            },
        )


class CrpBasePartData(DeclarativeCompoundBlock):
    block_description = (
        "Base data of an article: flags, bounds, object tag and the article's levels of "
        'detail; what Porsche.exe reads from it is cited per field (world loading 0x4750b0, 0x474cb0, 0x477f40, '
        '0x4781a0, 0x47cce0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        flags = (
            IntegerBlock(length=4),
            {
                'description': 'Article flags: 0x40 = no collision (Porsche.exe 0x4750b0); 0x2000 / 0x4000 = the '
                'mid-ground bundle, no collision (0x47cce0); 0x8000 on an article with a `rt` part 0: a scene '
                'instance, no collision (0x4781a0, 0x482970). The other bits are not known (tracks: 0x601, 0x610, '
                '0x611, 0x701, 0x711, 0x10610...; cars 0, 1, 0x600)'
            },
        )
        unk0 = (IntegerBlock(length=4), {'is_unknown': True, 'description': '0 in every file'})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True, 'description': '0 in every file'})
        num_lods = (
            IntegerBlock(length=4, programmatic_value=CountOf('lods')),
            {'description': 'Number of `lods` records (1..7)'},
        )
        unk2 = (IntegerBlock(length=4), {'is_unknown': True, 'description': '1 on tracks, 0 or 1 on cars'})
        box_min = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Minimum corner of the bounding box (Porsche.exe 0x477f40)'},
        )
        box_max = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Maximum corner of the bounding box (Porsche.exe 0x477f40)'},
        )
        centre = (
            Point3D(child=DecimalBlock(length=4)),
            {'is_unknown': True, 'description': 'A point inside the box (bounding sphere centre?)'},
        )
        unk3 = (DecimalBlock(length=4), {'is_unknown': True, 'description': '1.0 (0.0 on most car articles)'})
        radius = (
            ArrayBlock(child=DecimalBlock(length=4), length=2),
            {'is_unknown': True, 'description': 'Two equal values: a radius around `centre`?'},
        )
        tag = (
            BytesBlock(length=4),
            {
                'description': 'Object tag on tracks, 4 ASCII characters in memory order (`BUSH`, `SIGN`, `PILR`, '
                '`GAS` + 0), zeros for none: the name of its `section:anim` definition in `animdefs.txt` (Porsche.exe '
                '0x47ed90; an unknown tag gets the first definition), which gives a collidable article its '
                'collision type (cylinder, box, smackable). On cars four bytes: the geometry slot (0..59), the slot '
                'value that draws the article (a car level of detail lists the articles with car+0x56c[slot] == '
                'value: R3DCarLOD_Build 0x43c1b0; the slots come from the `.tpg` style, the race and the parts: '
                'R3DCar_SetBodyStyle 0x437b00, R3DCar_SetupGeometry 0x43ae50), the draw order (a signed byte, '
                "sorted ascending by 0x43c1b0 with a signed compare, 0x43e910: the inside articles' 0x81.. = "
                "-127.. are drawn first, a trunk lid's 0xF6 = -10 before the body's 0, lamps and decals 2 over "
                'the body) and a sequential article id'
            },
        )
        car_wheel = (
            IntegerBlock(length=1, is_signed=True),
            {
                'description': 'Cars: the wheel (0 front left, 1 front right, 2 rear left, 3 rear right) whose '
                'offset R3DCar+0x6d0 moves the article (R3DCarLOD_Draw 0x43c830; the offsets stay 0), -1 none'
            },
        )
        car_unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': 'Cars: 0, 0x80, 1 or 0xff'})
        car_unk1 = (
            IntegerBlock(length=1, is_signed=True),
            {'is_unknown': True, 'description': 'Cars: 0, -3 (lights, decals), -2 (needles), -10, 1, 3, 5...'},
        )
        car_pivot = (
            IntegerBlock(length=1),
            {
                'description': 'Cars: the pivot that turns the article about its origin (its `rt` part), 0 none; '
                "three angles in turns, x, then y, then z in the article's axes (R3DCarLOD_Draw 0x43c830; set each "
                'frame by R3DCar_UpdatePivots 0x438440): 1..4 the wheels (rotation, steering, camber), 5 the '
                'steering wheel, 6 / 7 the doors (about the `.tpg` `dooraxis`), 8 the hood, 9 the trunk, 0xb the '
                'rev counter needle, 0xc the speedometer needle, 0x10 the moving spoiler, 0x11 the pop-up '
                'headlights, 0x12..0x15 the wheels without their rotation (wheel shadows, treads), 0x16 a '
                'rotating light'
            },
        )
        car_frames = (
            IntegerBlock(length=1),
            {'description': 'Cars: number of animation frames (`vt` parts of the level: animation index 0..n - 1)'},
        )
        car_animation = (
            IntegerBlock(length=1),
            {
                'description': 'Cars: the animation that picks the frame, 0 none (R3DCarLOD_Build 0x43c1b0, the '
                'frames blended by R3DCarLOD_Animate 0x43e120): 1 the convertible top, 2 the speed wing, 3 a wiper, '
                "4 the right arm, 5 the left arm, 6 the driver's body, 7 the antenna"
            },
        )
        car_draw_flags = (
            IntegerBlock(length=1),
            {
                'description': 'Cars: the draw passes that draw the article (R3DCar_Draw 0x444e00 masks them): 0x10 '
                'the body, 0x20 the wheels, 0x40 the steering wheel, 0x80 the driver; 0x08: dented by damage (its '
                '`vt` parts have damaged copies and `zd` zones, R3DCarLOD_Damage 0x43e390); 0x01, 0x02, 0x04 not '
                'known (0x01 on the interior, 0x02 on the outside)'
            },
        )
        car_unk2 = (IntegerBlock(length=1), {'is_unknown': True, 'description': '0 in every car'})
        light = (
            IntegerBlock(length=1),
            {
                'description': 'Glare articles (flags 0x600, effect parts): the car light drawing the glare '
                '(R3DCar+0x2d4 flags, +0x2d8 intensities, set by R3DCar_UpdateLights 0x439360): 0 / 1 headlights, '
                '2 / 3 brake lights, 4 / 5 front indicators, 6 / 7 rear indicators, 8 reverse light, 9 off in '
                'races, 10 / 11 brake lights (blinking with the indicators), 12 / 13 on (roof lights)'
            },
        )
        car_cockpit = (
            IntegerBlock(length=1),
            {'description': 'Cars: not 0: drawn in the in-car view (R3DCar_Draw 0x444e00 with inside 1, 0x43c830)'},
        )
        car_inside_only = (
            IntegerBlock(length=1),
            {'description': "Cars: not 0: not drawn outside the in-car view (the driver's hands; 0x43c830)"},
        )
        unk4 = (BytesBlock(length=17), {'is_unknown': True, 'description': 'Zeros in every file'})
        lods = (
            ArrayBlock(child=CrpBaseLodRecord(), length='num_lods'),
            {'description': 'Levels of detail of the article'},
        )


class CrpBasePart(DeclarativeCompoundBlock):
    block_description = 'Base part "esaB" of an article, referencing a [CrpBasePartData](#crpbasepartdata) block'

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('esaB')), {'description': 'Identifier'})
        unk0 = _PART_UNK0
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: 0x64 + 12 * len(ctx.data('data/lods'))),
            {'description': 'Data length in bytes: 0x64 + 12 x levels of detail'},
        )
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION + ': 0'})
        offset = _PART_OFFSET
        data = (CrpBasePartData(), {'usage': 'ui'})


class CrpVertexColorPart(DeclarativeCompoundBlock):
    block_description = (
        'Part "fd" (tracks only): vertex colours, one u32 per entry (B, G, R, A from the '
        'low byte), one part per level of detail. The `fd` info rows of [TrianglePartData](#trianglepartdata) '
        'index them; the collision faces keep each corner as 15-bit (b >> 3) << 10 | (g >> 3) << 5 | r >> 3 '
        '(Porsche.exe 0x4750b0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Eq('fd')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(
            IntegerBlock(length=4),
            'num_data',
            'Number of colours',
            'Colours (BGRA)',
        )


class CrpSplineSlice(DeclarativeCompoundBlock):
    block_description = 'A slice of the road spline, 0x50 bytes, copied as it is by Porsche.exe 0x480140'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4, is_signed=True), {'is_unknown': True, 'description': '0, -1 on 232 slices'})
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Road centre. The spline searches use x and z (Alps slice 0: (-132.1, 1.3, 488.0), '
                'the next slices 6 m apart)'
            },
        )
        up = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Up vector (about (0, 1, 0)), copied to the car (car+0x3c4, Porsche.exe 0x499520)'},
        )
        forward = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Forward vector, the travel direction (slice i to i + 1): the sign test of the car '
                'heading (Porsche.exe 0x49af70), copied to car+0x3d0; the car reset placement (0x49b090) uses it'
            },
        )
        right = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Right (lateral) vector, perpendicular to `forward` in xz: heading = asin(car forward '
                '. this) (Porsche.exe 0x49af70), copied to car+0x3b8'
            },
        )
        lane_bits = (
            IntegerBlock(length=4),
            {
                'description': "The AI's lanes of the slice, one bit per lane: lane k (2..11) is bit 22 - k "
                '(Porsche.exe 0x40ea00 / 0x40ea50 build the bit, 0x40ea90 tests it). The AI numbers lanes by the '
                'lateral offset along `right`: lane 6 the first one left of the spline (offset < 0: 6 + '
                'round(offset / `left_lane_width`)), lane 7 the first one right of it (7 + round(offset / '
                '`right_lane_width`), clamped to 2..11; 0x40eb20 / 0x40ebb0). On all 23863 slices of the 15 '
                'tracks exactly the bits of lanes 7 - `left_lanes` .. 6 + `right_lanes` are set (0x18000 for 1 + 1 '
                "lanes). The traffic's lane choice scores down a lane whose bit is clear at its slice or ahead "
                "(0x401760), the traffic's target point goes past the road on a side only where the bits of the "
                'lanes 4 m and 8 m to that side are set (0x4090c0)'
            },
        )
        left_lanes = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Number of lanes left of the spline (negative lateral offset; 0..3, 1 on most '
                'slices): the AI lanes 7 - n .. 6, the left road edge at -(n x `left_lane_width`) (Porsche.exe '
                '0x409570, 0x4090c0, the AI racers 0x40c6cf), lane 6 - n the left shoulder (0x401b70, 0x401c60, '
                '0x402a40); a traffic car is on the road while its lane is at least 7 - n (0x40a5a0)'
            },
        )
        right_lanes = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Number of lanes right of the spline (positive lateral offset; 0..3): the AI lanes '
                '7 .. 6 + n, the right road edge at n x `right_lane_width` (0x409570, 0x40c729), lane 7 + n the right '
                'shoulder, as `left_lanes`. The traffic looks less far ahead on slices where both edges are less than '
                '18 m apart (0x4090c0)'
            },
        )
        left_half_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of the road left of the spline in meters (3 .. 18; at least `left_lanes` x '
                "`left_lane_width` on every slice): the traffic's target lateral offset stays at least its half "
                'width inside it (0x402a40), the left shoulder is this - `left_lanes` x `left_lane_width` '
                '(0x401c60); an AI-driven car more than 35 m beyond it is put back on the road (0x408750). The AI '
                "racers' road width factor is (this + `right_half_width`) / 12 m (10 m castle, 9 m forest), at most "
                '1: it scales their target speed and steering look-ahead (0x40b650, 0x40bfe0)'
            },
        )
        right_half_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of the road right of the spline in meters (3 .. 20), as `left_half_width` (0x402a40: '
                'the target offset at most this - the half width; 0x401c60; the road width factor)'
            },
        )
        left_lane_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of a lane left of the spline in meters (0 where `left_lanes` is 0): left lane '
                'k (k <= 6) spans (k - 6) x this - this .. (k - 6) x this (0x402920, 0x402a40); the lane of an '
                'offset divides it by this rounded to whole meters (0x40eb20). 2.5 .. 10.5 (6 on most slices)'
            },
        )
        right_lane_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of a lane right of the spline in meters (0 where `right_lanes` is 0; 1.8 .. '
                '11.25): right lane k (k >= 7) spans (k - 7) x this .. (k - 6) x this (0x402920, 0x402a40, 0x40eb20)'
            },
        )


class CrpSimDPart(DeclarativeCompoundBlock):
    block_description = (
        'Common part "DmiS" (`SimD`, tracks only): the road spline, an array of '
        '[CrpSplineSlice](#crpsplineslice) (Porsche.exe 0x480080)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('DmiS')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(
            CrpSplineSlice(),
            'num_data',
            'Number of slices',
            'Slices',
        )


class CrpSimTPart(DeclarativeCompoundBlock):
    block_description = (
        'Common part "TmiS" (`SimT`, tracks only): the sections of the road spline, an int32 '
        'slice count per section, the sections following each other over the slices of "DmiS" (Alps: 1795 + '
        '272 + 22 + 16 = 2105 slices). Without it (or with less than 2) the spline is one section. Porsche.exe '
        '0x480080 reads it, then splits sections where another one ends within 16 m of it, more than 5 slices '
        'from its ends (0x480900), and joins section ends within 16 m of each other into junctions (0x480b40), '
        'whose branch weights come from `<track>.jnc` ([Nfs5Junctions](#nfs5junctions)). A section is driven '
        'from its first slice to its last. The race goes from junction 0 (slice 0) along the longest walk '
        'through the sections (0x481910 / 0x4819e0: the race length and progress, 0x416290) to the junction at '
        'its end, or back to junction 0 on a circuit; the other sections are alternative roads, shortcuts and '
        'branches. The HUD map (0x432230 / 0x433690) draws every section alike, each end linked to its '
        'junction centre (the average of its end slices)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('TmiS')), {'description': 'Identifier'})
        unk0, len, num_data, offset, data = crp_array_part_fields(
            IntegerBlock(length=4, is_signed=True),
            'num_data',
            'Number of sections',
            'Slice count of each section',
        )


# parts of an article, picked by identifier (`MagicDispatchBlock`: the first block in order whose `identifier`
# validator accepts it; an unknown identifier raises)
def crp_part_block() -> MagicDispatchBlock:
    return MagicDispatchBlock(
        possible_blocks=[
            TextPart4(),
            CullingPart(),
            TextPart2(),
            EffectPart(),
            NormalPart(),
            TrianglePart(),
            TransformationPart(),
            UVPart(),
            VertexPart(),
            UnkPart4(),
            CrpDamageZonesPart(),
            UnkPart2(),
            CrpBasePart(),
            CrpVertexColorPart(),
        ]
    )


class ArticlePart(DeclarativeCompoundBlock):
    block_description = (
        'Article is a single logical part of a car or track. Contains meshes of the same '
        'entity for various levels of details, damage status, animation indexes etc.'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('itrA'), length=4), {'description': 'Resource ID'})
        header_info = (
            IntegerBlock(length=4, value_validator=Eq(0x1A)),
            {
                'description': 'Chunk info: 0x1A = bits 0x2 (offset relative to the chunk) and 0x8 (parts sorted by '
                'id: Porsche.exe finds a part by binary search, 0x59f7c0 / 0x59f5e0), 0x10 not known'
            },
        )
        num_parts = (
            IntegerBlock(length=4),
            {
                'description': 'An amount of parts, linked to this article. Porsche.exe finds them by id: the `rt` '
                'part 0 (TransformationPart) puts the article into the instance bundle, `tqnA` into the animated '
                'one; collidable articles are those of the static bundle without the no-collision flags of their '
                'base part ([CrpBasePartData](#crpbasepartdata))'
            },
        )
        local_offset = (
            IntegerBlock(length=4),
            {
                'description': 'A local offset from the beginning of this article to the first linked part, '
                'divided by 16. So the first part index in parts array for this article is: '
                'local_offset + this article index - len(articles) - len(common_parts)'
            },
        )
        parts = (ArrayBlock(child=crp_part_block(), length=(0, '?')), {'usage': 'ui'})


def determine_num_parts(ctx, **_):
    """Parts up to the last one of an article: article i's parts start at chunk 1 + i + `local_offset`"""
    part_ends = [a['local_offset'] + a['num_parts'] + i for (i, a) in enumerate(ctx.data('articles'))]
    return max(part_ends) - len(ctx.data('articles')) - len(ctx.data('common_parts'))


# CRP part data starting at a 4 KB boundary, and the file end
_CRP_PAGE = 0x1000


class CrpGeometry(DeclarativeCompoundBlock):
    block_description = (
        'A set of 3D meshes, used for cars and tracks. Materials are parsed only partially. '
        'Contains many part blocks, '
        '16-bytes each, splitted into 3 sections: articles, common_parts, parts, followed '
        "by raw data. Each part, except articles, have an offset and length of it's data,"
        ' located in "raw_data" byte array. The converter builds one mesh per vertex part '
        'and texture of each article, named `<article name>_LOD<lod>_ai<animation index>_<texture>`, using '
        'triangle, UV and transformation parts of the article with the same LOD (tracks: the first animation '
        'frame, `ai0`, only; the frames are vertex parts of the same LOD). Car textures: every '
        'FSH part is composed into a texture page (images are placed by their atlas position), '
        "material references the page by index; mapping of FSH parts to pages is described in car's "
        '.tpg file. Track textures: material references the texture by 4-char name in the FSH file, '
        'which name is stored in TextPart2 "ns". Porsche.exe reads it as a tree of 16-byte EAGL chunks '
        '{id, info, count, offset} (unpacked by 0x5713a0 from RefPack: byte 0 0x10, or 0x11 with 3 more header '
        'bytes, byte 1 0xfb, the unpacked size big-endian at +2): the children of a container chunk (the '
        'header, an article) are at offset x 16, the data of a part at offset bytes, both relative to the '
        'chunk; parts are found by id (0x59f7c0 / 0x59f5e0). Track CRPs also hold the road spline ("DmiS", '
        '"TmiS"), the collision faces (from the `pr` parts of collidable articles, with the `mt` surface '
        'flags) and the object tags (`animdefs.txt`)'
    )
    serializer = 'CrpGeometrySerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (
            UTF8Block(value_validator=Or([' raC', 'karT']), length=4),
            {'description': 'Resource ID. " raC" ("Car ") for cars, "karT" for tracks'},
        )
        header_info = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: 0x1A | (len(ctx.data('articles')) << 5)),
            {
                'description': 'Chunk info: 27 higher bits: number of articles (the children the chunk search '
                'skips); 5 lower bits 0x1A: bits 0x2 (offsets relative to the chunk) and 0x8 (common parts sorted by '
                'id, binary search, Porsche.exe 0x59f7c0 / 0x59f5e0), 0x10 not known'
            },
        )
        num_common_parts = (
            IntegerBlock(length=4, programmatic_value=CountOf('common_parts')),
            {'description': 'Number of common parts: the children the chunk search looks through'},
        )
        articles_offset = (
            IntegerBlock(length=4, value_validator=Eq(1)),
            {
                'description': 'Offset to articles block / 16, relative to the header (children of a container chunk '
                'are at offset x 16, Porsche.exe 0x59f870)'
            },
        )
        articles = (
            ArrayBlock(child=ArticlePart(), length=(lambda ctx: ctx.data('header_info') >> 5)),
            {'description': 'Array of articles'},
        )
        common_parts = (
            ArrayBlock(
                child=MagicDispatchBlock(
                    possible_blocks=[
                        TextPart4(),
                        MaterialPart(),
                        FSHPart(),
                        TextPart2(),
                        UnkPart4(),
                        UnkPart2(),
                        CrpSimDPart(),
                        CrpSimTPart(),
                    ]
                ),
                length='num_common_parts',
            ),
            {
                'description': 'Array of common parts. They are ordered by type (identifier). The order is:<br/>'
                + '- "PdnB" - ?, cars only<br/>'
                '- "nAmC" - camera animations? tracks only<br/>'
                '- [TextPart4](#textpart4) "cseD" - seems to be a path to original development source file, tracks only<br/>'
                '- "htMR" - ?<br/>'
                '- "odnW" - ?, cars only<br/>'
                '- [CrpSimDPart](#crpsimdpart) "DmiS" - the road spline, tracks only<br/>'
                '- [CrpSimTPart](#crpsimtpart) "TmiS" - the sections of the road spline, tracks only<br/>'
                '- " siV" - ?, tracks only<br/>'
                '- [MaterialPart](#materialpart)<br/>'
                '- [FSHPart](#fshpart)<br/>'
                '- [TextPart2](#textpart2) "ns" - a path to fsh file with textures, tracks only'
            },
        )
        parts = (
            ArrayBlock(
                child=crp_part_block(),
                length=(determine_num_parts, '1 + index of the last article part'),
            ),
            {
                'usage': 'io,doc',
                'description': 'Array of parts, ordered by article, for each article it is also ordered by type (identifier):<br/>'
                '- "minA" - animations? tracks only<br/>'
                '- "tqnA" - the article is animated (animated bundle), tracks only<br/>'
                '- [CullingPart](#cullingpart) - ?, cars only<br/>'
                '- [CrpBasePart](#crpbasepart) "esaB" - flags, bounds, object tag, levels of detail<br/>'
                '- [TextPart4](#textpart4) "emaN" - name of the mesh<br/>'
                '- [CrpVertexColorPart](#crpvertexcolorpart) "fd" - vertex colours, tracks only<br/>'
                '- [EffectPart](#effectpart) - ?<br/>'
                '- [CrpDamageZonesPart](#crpdamagezonespart) "zd" - damage zones of the vertices, cars only<br/>'
                '- [NormalPart](#normalpart) - ?, cars only<br/>'
                '- [TrianglePart](#trianglepart) - mesh indexes (faces)<br/>'
                '- [TransformationPart](#transformationpart) - position/rotation of the mesh<br/>'
                '- [UVPart](#uvpart) - vertex UV-s<br/>'
                '- [VertexPart](#vertexpart) - vertices',
            },
        )
        raw_data = (
            BytesBlock(length=REMAINING),
            {
                'usage': 'doc',
                'description': 'Data of the parts, at the offset and length of each part: 16-byte aligned, in no fixed '
                'order, some starting at a 4 KB boundary, zeros between; the file ends on a 4 KB boundary. The '
                'converter writes the data in the order of the offsets read, aligned the same way',
            },
        )

    def _part_chunks(self, data) -> list:
        """(chunk index, path, part block, part data) of every common part and part, in chunk order: the header is
        chunk 0, the articles follow; each chunk is 16 bytes"""
        res = []
        chunk = 1 + len(data['articles'])
        for field in ('common_parts', 'parts'):
            delegate = self.field_blocks_map[field].child
            for i, part in enumerate(data[field]):
                res.append((chunk, f'{field}/{i}', delegate.possible_blocks[part['choice_index']], part['data']))
                chunk += 1
        return res

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        start = ctx.buffer.tell()
        data = super().read(ctx, name, read_bytes_amount)
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount)
        end = ctx.buffer.tell() + ctx.read_bytes_remaining
        for chunk, path, block, part in self._part_chunks(data):
            ctx.buffer.seek(start + 16 * chunk + part['offset'])
            part['data'] = block.field_blocks_map['data'].read(
                self_ctx.child(path), 'data', read_bytes_amount=part['len']
            )
        for i, article in enumerate(data['articles']):
            offs = article['local_offset'] - len(data['articles']) - len(data['common_parts']) + i
            article['parts'] = data['parts'][offs : offs + article['num_parts']]
        ctx.buffer.seek(end)
        return data

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        """The chunks, then the data of the parts in the order of the offsets read (`raw_data`): 16-byte aligned,
        data read at a 4 KB boundary starting at one again, the file padded to 4 KB. A part's data takes its `len`
        bytes (a material or effect reads past a shorter `len`)"""
        res = bytearray(super().write(data, ctx, name))
        self_ctx = WriteContext(data=data, name=name, block=self, parent=ctx)
        for chunk, path, block, part in sorted(self._part_chunks(data), key=lambda x: 16 * x[0] + x[3]['offset']):
            header = 16 * chunk
            # the data length as written: the 24 bits above the info byte `unk0`
            length = int.from_bytes(res[header + 5 : header + 8], 'little')
            alignment = _CRP_PAGE if (header + part['offset']) % _CRP_PAGE == 0 else 16
            position = -(-len(res) // alignment) * alignment
            res += bytes(position - len(res))
            part_ctx = WriteContext(data=part, name=path, block=block, parent=self_ctx)
            packed = block.field_blocks_map['data'].pack(part['data'], ctx=part_ctx, name='data')
            res += packed[:length].ljust(length, b'\0')
            res[header + 12 : header + 16] = (position - header).to_bytes(4, 'little')
        res += bytes(-len(res) % _CRP_PAGE)
        return bytes(res)

    def estimate_packed_size(self, data, ctx: WriteContext = None) -> int:
        return len(self.write(data, ctx))

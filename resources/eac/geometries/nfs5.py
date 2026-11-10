from os import SEEK_CUR
from typing import Dict

from library.context import ReadContext
from library.exceptions import BlockDefinitionException
from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    BytesBlock,
    DelegateBlock,
    DecimalBlock,
    SubByteCompoundBlock,
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


class UnkPart2(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Unknown part with index and 2-chars identifier'}

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Or(['zd', 'ns'])), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (BytesBlock(length=lambda ctx: ctx.data('len')), {'usage': 'ui'})


class UnkPart4(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Unknown part with 4-chars identifier'}

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
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (BytesBlock(length=lambda ctx: ctx.data('len')), {'usage': 'ui'})


class MaterialPartData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A material, data structure is mostly unknown. Triangle parts reference it by '
            'index (`idx` of [MaterialPart](#materialpart))',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to [MaterialPartData](#materialpartdata) block',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier'})
        identifier = (UTF8Block(length=2, value_validator=Eq('tm')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (MaterialPartData(), {'usage': 'ui'})


class FSHPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [ShpiBlock](#shpiblock) blocks',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier'})
        identifier = (UTF8Block(length=2, value_validator=Eq('fs')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
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
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of SHPI blocks'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(child=ShpiBlock(), length=lambda ctx: ctx.data('num_data')), {'usage': 'ui'})


class TextPart2(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A part referencing to text with index and 2-chars identifier'}

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Eq('ns')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) + 1),
            {'description': 'Data length in bytes, equals to `text length + 1` (0x00 terminating byte)'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (NullTerminatedUTF8Block(length=None), {'usage': 'ui'})


class TextPart4(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A part referencing to text with 4-chars identifier'}

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Or(['emaN', 'cseD'])), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) + 1),
            {'description': 'Data length in bytes, equals to `text length + 1` (0x00 terminating byte)'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (NullTerminatedUTF8Block(length=None), {'usage': 'ui'})


class CullingPartData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Polygon culling rule?'}

    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (
            Point3D(child=DecimalBlock(length=4), is_normalized=True),
            {'description': 'Normalized direction vector (plane normal?)'},
        )
        threshold = (DecimalBlock(length=4), {'description': 'Threshold value (plane distance?)'})


class CullingPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [CullingPartData](#cullingpartdata) blocks',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('n$')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) * 16),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of culling part data blocks'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=CullingPartData()), {'usage': 'ui'})


class TransformationPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to a transformation matrix. If exists, matrix should be '
            'applied to the meshes of the same article with the same LOD. Matrix is a 4x4 '
            'matrix in column-major order (elements 12, 13, 14 are the translation), where '
            'each number is stored as 4-bytes float number (little-endian). On tracks, the `rt` part 0 of an '
            'article puts it into the instance bundle (Porsche.exe 0x4781a0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('rt')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (IntegerBlock(length=3, value_validator=Eq(0x40)), {'description': 'Data length in bytes'})
        unk_1 = (
            IntegerBlock(length=4),
            {'is_unknown': True, 'description': 'Always 1? Number of Transformation Matrices?'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(length=16, child=DecimalBlock(length=4)), {'usage': 'ui'})


class VertexData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Represents single vertex'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position'})
        unk = (DecimalBlock(length=4), {'is_unknown': True})


class VertexPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [VertexData](#vertexdata) blocks, representing'
            ' mesh vertices. Every vertex part of an article produces a separate mesh, '
            'combined with the triangle, UV and transformation parts of the same LOD. For a '
            'damaged part (damage == 8) vertex positions are offsets, which are added to '
            'vertices of the undamaged part with the same LOD and animation index',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('tv')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) * 16),
            {'usage': 'io,doc', 'description': 'Data length in bytes'},
        )
        num_vertices = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of vertices'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(length=lambda ctx: ctx.data('num_vertices'), child=VertexData()), {'usage': 'ui'})


class NormalPartData(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (Point3D(child=DecimalBlock(length=4)), {'description': 'Normal vector'})
        unk = (DecimalBlock(length=4), {'is_unknown': True})


class NormalPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [NormalPartData](#normalpartdata) blocks, describing mesh normals',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('mn')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: ctx.data('num_data') * 16),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of normals'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=NormalPartData()), {'usage': 'ui'})


class UVData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Texture coordinates of a vertex'}

    class Fields(DeclarativeCompoundBlock.Fields):
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})


class UVPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [UVData](#uvdata) blocks, representing texture coordinates',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('vu')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: ctx.data('num_data') * 8),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Amount of UVData blocks, equals to len / 8'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=UVData()), {'usage': 'ui'})


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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row of [TrianglePartData](#trianglepartdata), 16 bytes: the layout of every '
            'row, read for the stream types without a block of their own (4 `Base`, 5 `pr`, 6 `fe`; in no game '
            'file)',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row referencing the culling data used by the triangle part',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row referencing the vertex data (`vt` part, `row_type` 0) used by the '
            'triangle part',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row referencing the normals data (`nm` part, `row_type` 1) used by the '
            'triangle part',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset in normal data'})
        length_used = (IntegerBlock(length=2), {'description': 'Length of normal data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class UVInfoRow(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row referencing the UV data (`uv` part, `row_type` 2) used by the triangle part',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (IntegerBlock(length=4), {'description': 'Offset in uv data'})
        length_used = (IntegerBlock(length=2), {'description': 'Length of uv data used'})
        row_type = (IntegerBlock(length=2), {'description': _ROW_TYPE_DESCRIPTION})
        level_index = (IntegerBlock(length=2), {'description': 'Level index'})
        index_stream = (IntegerBlock(length=2), {'description': _INDEX_STREAM_DESCRIPTION})


class VertexColorInfoRow(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Info row referencing the vertex colours ([CrpVertexColorPart](#crpvertexcolorpart) '
            '`fd`, `row_type` 3, tracks only) used by the triangle part',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Descriptor of an index stream (vertex indices or UV indices) of the triangle part: '
            'the info rows refer to it by its position (`index_stream`)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'Row index'})
        identifier = (UTF8Block(length=2), {'description': 'Identifier "vI"|"Iv" – vertex index, "uI"|"Iu" - uv index'})
        offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of indices: the position of the first index of this stream in the index tables'},
        )


class TrianglePartData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A description of mesh geometry (faces): `num_data` positions forming primitives '
            'of `primitive_type`, each corner taking its vertex, normal, UV and colour from the streams of the info '
            'rows; primitive k uses the positions from step x k on (Porsche.exe 0x5a0bc0). The converter exports '
            'triangle lists as they are, strips with every second triangle reversed (k odd: positions k + 1, k, '
            'k + 2, as Direct3D draws strips; triangles repeating a vertex, the joints of the strips, left out), '
            'quads as the triangles 0 1 2 and 0 2 3 (as the collision splits them, Porsche.exe 0x4750b0), no lines',
        }

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
                length=lambda ctx: ctx.data('num_info_rows'),
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
            ArrayBlock(length=lambda ctx: ctx.data('num_index_rows'), child=IndexRow()),
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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to [TrianglePartData](#TrianglePartData) block, describes mesh faces',
        }

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
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        # TODO setup programmatic value for length fields. Here it should be (48 + data.num_info_rows*16 + data.num_index_rows*8 + num_data*2)
        len = (IntegerBlock(length=3), {'description': 'Data length in bytes'})
        num_data = (IntegerBlock(length=4), {'description': 'Number of indices (size of each index table in the data)'})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (TrianglePartData(), {'usage': 'ui'})


class EffectPartData(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
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
        mirror = (IntegerBlock(length=4), {'description': 'Mirror'})
        info = (IntegerBlock(length=4), {'is_unknown': True, 'description': 'Information'})


class EffectPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A part referencing to an array of [EffectPartData](#effectpartdata) blocks',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        part_info = (
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
        identifier = (UTF8Block(length=2, value_validator=Eq('fe')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (IntegerBlock(length=3, programmatic_value=lambda ctx: 0x58), {'description': 'Data length in bytes'})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (EffectPartData(), {'usage': 'ui'})


class CrpBaseLodRecord(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A level of detail of an article: the `pr` parts drawn at it and their vertex '
            'data, 12 bytes (Porsche.exe 0x4750b0, 0x474cb0)',
        }

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
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Base data of an article: flags, bounds, object tag and the article's levels of "
            'detail; what Porsche.exe reads from it is cited per field (world loading 0x4750b0, 0x474cb0, 0x477f40, '
            '0x4781a0, 0x47cce0)',
        }

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
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('lods'))),
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
                'collision type (cylinder, box, smackable). Other values on cars'
            },
        )
        unk4 = (BytesBlock(length=28), {'is_unknown': True, 'description': 'Zeros on tracks, data on cars'})
        lods = (
            ArrayBlock(child=CrpBaseLodRecord(), length=lambda ctx: ctx.data('num_lods')),
            {'description': 'Levels of detail of the article'},
        )


class CrpBasePart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Base part "esaB" of an article, referencing a [CrpBasePartData](#crpbasepartdata) '
            'block',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('esaB')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: 0x64 + 12 * len(ctx.data('data/lods'))),
            {'description': 'Data length in bytes: 0x64 + 12 x levels of detail'},
        )
        unk1 = (IntegerBlock(length=4), {'description': _CHUNK_COUNT_DESCRIPTION + ': 0'})
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (CrpBasePartData(), {'usage': 'ui'})


class CrpVertexColorPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Part "fd" (tracks only): vertex colours, one u32 per entry (B, G, R, A from the '
            'low byte), one part per level of detail. The `fd` info rows of [TrianglePartData](#trianglepartdata) '
            'index them; the collision faces keep each corner as 15-bit (b >> 3) << 10 | (g >> 3) << 5 | r >> 3 '
            '(Porsche.exe 0x4750b0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        idx = (IntegerBlock(length=2), {'description': 'A part index of the same identifier (in the same article)'})
        identifier = (UTF8Block(length=2, value_validator=Eq('fd')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) * 4),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of colours'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (
            ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=IntegerBlock(length=4)),
            {'usage': 'ui', 'description': 'Colours (BGRA)'},
        )


class CrpSplineSlice(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A slice of the road spline, 0x50 bytes, copied as it is by Porsche.exe 0x480140',
        }

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
        lanes = (
            IntegerBlock(length=4),
            {
                'is_unknown': True,
                'description': 'Not read by the ported code. Looks like a mask of one bit per lane: bits 16 and up '
                'for the `lanes_a` lanes, bits 15 and down for the `lanes_b` lanes (0x18000 for 1 + 1, 0x38000 for '
                '2 + 1, 0x1c000 for 1 + 2)',
            },
        )
        lanes_a = (
            IntegerBlock(length=4),
            {'is_unknown': True, 'description': '0..3 (1 on most slices): lanes on one side?'},
        )
        lanes_b = (
            IntegerBlock(length=4),
            {'is_unknown': True, 'description': '0..3 (1 on most slices): lanes on the other side?'},
        )
        widths = (
            ArrayBlock(child=DecimalBlock(length=4), length=4),
            {'is_unknown': True, 'description': 'Four floats, 5.0 on Alps, 6.0 on Autobahn: lane widths?'},
        )


class CrpSimDPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Common part "DmiS" (`SimD`, tracks only): the road spline, an array of '
            '[CrpSplineSlice](#crpsplineslice) (Porsche.exe 0x480080)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('DmiS')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) * 0x50),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of slices'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (
            ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=CrpSplineSlice()),
            {'usage': 'ui', 'description': 'Slices'},
        )


class CrpSimTPart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Common part "TmiS" (`SimT`, tracks only): the sections of the road spline, an int32 '
            'slice count per section, the sections following each other over the slices of "DmiS" (Alps: 1795 + '
            '272 + 22 + 16 = 2105 slices). Without it (or with less than 2) the spline is one section. Porsche.exe '
            '0x480080 reads it, then splits sections where another one ends within 16 m of it, more than 5 slices '
            'from its ends (0x480900), and joins section ends within 16 m of each other into junctions (0x480b40), '
            'whose branch weights come from `<track>.jnc` ([Nfs5Junctions](#nfs5junctions)). A section is driven '
            'from its first slice to its last. The race goes from junction 0 (slice 0) along the longest walk '
            'through the sections (0x481910 / 0x4819e0: the race length and progress, 0x416290) to the junction at '
            'its end, or back to junction 0 on a circuit; the other sections are alternative roads, shortcuts and '
            'branches. The HUD map (0x432230 / 0x433690) draws every section alike, each end linked to its '
            'junction centre (the average of its end slices)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        identifier = (UTF8Block(length=4, value_validator=Eq('TmiS')), {'description': 'Identifier'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True, 'description': _CHUNK_INFO_DESCRIPTION})
        len = (
            IntegerBlock(length=3, programmatic_value=lambda ctx: len(ctx.data('data')) * 4),
            {'description': 'Data length in bytes'},
        )
        num_data = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('data'))),
            {'description': 'Number of sections'},
        )
        offset = (
            IntegerBlock(length=4),
            {'usage': 'io,doc', 'description': 'Data offset (Relative from current block offset)'},
        )
        data = (
            ArrayBlock(length=lambda ctx: ctx.data('num_data'), child=IntegerBlock(length=4, is_signed=True)),
            {'usage': 'ui', 'description': 'Slice count of each section'},
        )


class PartBlock(DelegateBlock):
    def __init__(self, **kwargs):
        super().__init__(
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
                UnkPart2(),
                CrpBasePart(),
                CrpVertexColorPart(),
            ],
            choice_index=lambda ctx, **_: _determine_part_type(ctx),
            **kwargs,
        )


class ArticlePart(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Article is a single logical part of a car or track. Contains meshes of the same '
            'entity for various levels of details, damage status, animation indexes etc.',
        }

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
        parts = (ArrayBlock(child=PartBlock(), length=(0, '?')), {'usage': 'ui'})


def determine_common_part_type(ctx):
    (TEXT4, MAT, FSH, TEXT2, UNK4, UNK2, SIM_D, SIM_T) = range(8)
    try:
        first_part = ctx.buffer.read(2).decode('utf-8')
    except UnicodeDecodeError:
        first_part = None
    try:
        second_part = ctx.buffer.read(2).decode('utf-8')
    except UnicodeDecodeError:
        second_part = None
    ctx.buffer.seek(-4, SEEK_CUR)
    if second_part == 'tm':
        return MAT
    elif second_part == 'fs':
        return FSH
    elif second_part == 'ns':
        return TEXT2
    elif first_part is not None:
        id = first_part + second_part
        if id == 'cseD':
            return TEXT4
        if id == 'DmiS':
            return SIM_D
        if id == 'TmiS':
            return SIM_T
    return UNK4


def _determine_part_type(ctx):
    (TEXT4, CULL, TEXT2, FX, NRML, TRNGL, TRANSF, UV, VRTX, UNK4, UNK2, BASE, COLORS) = range(13)
    try:
        first_part = ctx.buffer.read(2).decode('utf-8')
    except UnicodeDecodeError:
        first_part = None
    try:
        second_part = ctx.buffer.read(2).decode('utf-8')
    except UnicodeDecodeError:
        second_part = None
    ctx.buffer.seek(-4, SEEK_CUR)

    if second_part == 'n$':
        return CULL
    elif second_part == 'rt':
        return TRANSF
    elif second_part == 'tv':
        return VRTX
    elif second_part == 'mn':
        return NRML
    elif second_part == 'vu':
        return UV
    elif second_part == 'rp':
        return TRNGL
    elif second_part == 'fe':
        return FX
    elif second_part == 'ns':
        return TEXT2
    elif second_part == 'fd':
        return COLORS
    elif second_part == 'zd':
        return UNK2
    elif first_part is not None:
        id = first_part + second_part
        if id == 'esaB':
            return BASE
        if id == '\x00\x00\x00\x00' or id == 'minA' or id == 'tqnA':
            return UNK4
        elif id == 'emaN':
            return TEXT4
    raise BlockDefinitionException(f'Unknown part type: {first_part}{second_part}')


def determine_num_parts(ctx):
    last_used_part_indices = [a['local_offset'] + a['num_parts'] + i for (i, a) in enumerate(ctx.data('articles'))]
    return max(last_used_part_indices) - len(ctx.data('articles')) - len(ctx.data('common_parts')) + 1


class CrpGeometry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A set of 3D meshes, used for cars and tracks. Materials are parsed only partially. '
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
            'flags) and the object tags (`animdefs.txt`)',
        }

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
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('common_parts'))),
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
                child=DelegateBlock(
                    possible_blocks=[
                        TextPart4(),
                        MaterialPart(),
                        FSHPart(),
                        TextPart2(),
                        UnkPart4(),
                        UnkPart2(),
                        CrpSimDPart(),
                        CrpSimTPart(),
                    ],
                    choice_index=lambda ctx, **_: determine_common_part_type(ctx),
                ),
                length=lambda ctx: ctx.data('num_common_parts'),
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
                child=PartBlock(),
                length=(lambda ctx: determine_num_parts(ctx), '1 + last referenced part index in articles data'),
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
                '- "zd" - ?, cars only<br/>'
                '- [NormalPart](#normalpart) - ?, cars only<br/>'
                '- [TrianglePart](#trianglepart) - mesh indexes (faces)<br/>'
                '- [TransformationPart](#transformationpart) - position/rotation of the mesh<br/>'
                '- [UVPart](#uvpart) - vertex UV-s<br/>'
                '- [VertexPart](#vertexpart) - vertices',
            },
        )
        raw_data = (
            BytesBlock(length=lambda ctx: ctx.read_bytes_remaining),
            {
                'usage': 'doc',
                'description': 'Raw data region, where part data is stored. Part data offset and lengthes are stored in the PartBlock.',
            },
        )

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        data = super().read(ctx, name, read_bytes_amount)
        misc_part_block = self.field_blocks_map.get('common_parts').child
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount)

        raw_data_offset = ctx.buffer.tell()
        raw_data_len = ctx.read_bytes_remaining

        for i, misc_part in enumerate(data['common_parts']):
            misc_block = misc_part_block.possible_blocks[misc_part['choice_index']]
            data_block = misc_block.field_blocks_map.get('data')
            if not data_block:
                continue
            ctx.buffer.seek(
                raw_data_offset
                + misc_part['data']['offset']
                - 16 * (len(data['parts']) + len(data['common_parts']) - i)
            )
            misc_part['data']['data'] = data_block.read(
                self_ctx.child(f'common_parts/{i}'), 'data', read_bytes_amount=misc_part['data']['len']
            )
        part_block = self.field_blocks_map.get('parts').child
        for i, part in enumerate(data['parts']):
            block = part_block.possible_blocks[part['choice_index']]
            data_block = block.field_blocks_map.get('data')
            if not data_block:
                continue
            ctx.buffer.seek(raw_data_offset + part['data']['offset'] - 16 * (len(data['parts']) - i))
            part['data']['data'] = data_block.read(
                self_ctx.child(f'parts/{i}'), 'data', read_bytes_amount=part['data']['len']
            )
        for i, article in enumerate(data['articles']):
            offs = article['local_offset'] - len(data['articles']) - len(data['common_parts']) + i
            article['parts'] = data['parts'][offs : offs + article['num_parts']]
        ctx.buffer.seek(raw_data_offset + raw_data_len)
        return data

    def serializer_class(self):
        from serializers import CrpGeometrySerializer

        return CrpGeometrySerializer

from io import SEEK_CUR
from typing import List

from library.context import ReadContext
from library.exceptions import BlockDefinitionException
from library.read_blocks import (
    DeclarativeCompoundBlock,
    IntegerBlock,
    BytesBlock,
    ArrayBlock,
    DelegateBlock,
    DecimalBlock,
    CompoundBlock,
    SizeOf,
)
from library.read_blocks.misc.value_validators import Eq, Or
from library.read_blocks.strings import NullTerminatedUTF8Block, UTF8Block
from resources.eac.fields.misc import Point3D
from resources.blackbox.chunks import (
    CHUNK_LENGTH_DESCRIPTION,
    ChunkBlock,
    ZeroChunk,
    chunk_length_field,
    chunk_payload_remaining,
    chunk_rest,
    chunks_field,
    elevens_field,
    is_name_bytes,
    records_to_chunk_end,
)


class NfsuVec3(DeclarativeCompoundBlock):
    block_description = 'A 3D vector padded to 16 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        vector = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vector components'})
        pad = (DecimalBlock(length=4, value_validator=Eq(0.0)), {'description': 'Padding, always 0'})


class Chunk80034020(ChunkBlock):
    block_description = 'The last chunk of the file, purpose unknown'

    CHUNK_ID = 0x80_03_40_20

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length='chunk_length'), {'is_unknown': True})


class NfsuMeshChunk(ChunkBlock):
    block_description = (
        'Mesh info chunk: amounts of faces and vertices of the mesh, used to read the '
        'faces and vertices chunks of the same mesh data container'
    )

    CHUNK_ID = 0x00_13_49_00
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length=36), {'description': 'Unknown data', 'is_unknown': True})
        faces_amount = (IntegerBlock(length=4), {'description': 'Amount of faces (triangles) of the mesh'})
        unk_v = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        unk_w = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        unk_x = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        vertex_amount = (IntegerBlock(length=4), {'description': 'Amount of vertices of the mesh'})
        unk_y = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        unk_z = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        unk_tail = (
            records_to_chunk_end(IntegerBlock(length=4, value_validator=Eq(0)), 4, '0 in NFSU, 1 in NFSU2'),
            {'description': 'NFSU2 only: one more zero value', 'is_unknown': True},
        )


class NfsuMeshFacesChunk(ChunkBlock):
    block_description = (
        'Mesh faces: a triangle list. Amount of faces is defined by the mesh info chunk '
        '(the first chunk of the same mesh data container)'
    )

    CHUNK_ID = 0x00_13_4B_03
    ALIGNMENT = 0x10
    CHECK_ELEVENS = True

    class Fields(ChunkBlock.Fields):
        faces = (
            ArrayBlock(child=ArrayBlock(child=IntegerBlock(length=2), length=3), length='../0/data/faces_amount'),
            {'description': 'Triangles: 3 vertex indexes each, pointing to the vertices chunk of the same mesh'},
        )
        padding = (chunk_rest(), {'description': 'Padding to the end of the chunk'})


_VERTEX_COLOR_DESCRIPTION = (
    'Vertex colour, 32-bit ARGB (Direct3D D3DCOLOR: bytes B, G, R, A): world meshes the baked lighting, car meshes '
    'mostly white with black or grey parts (NFSU: whole parts black, such as engines, brake lights and mirrors, and '
    'odd colours such as 0xff99105f). Exported as the vertex colours of the track and car models (OBJ `v` colours, '
    'GLB COLOR_0: RGBA / 255); how the game draws them is not traced'
)


class NfsuVertex(DeclarativeCompoundBlock):
    block_description = 'A single mesh vertex with normal (36 bytes). The most common vertex layout'

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex position'})
        unk0 = (
            IntegerBlock(length=4),
            {'description': 'Presumably X component of the vertex normal, stored as 32-bit float', 'is_unknown': True},
        )
        unk1 = (
            IntegerBlock(length=4),
            {'description': 'Presumably Y component of the vertex normal, stored as 32-bit float', 'is_unknown': True},
        )
        unk2 = (
            IntegerBlock(length=4),
            {'description': 'Presumably Z component of the vertex normal, stored as 32-bit float', 'is_unknown': True},
        )
        color = (IntegerBlock(length=4), {'description': _VERTEX_COLOR_DESCRIPTION})
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (
            DecimalBlock(length=4),  # hmm, Bin2Ase renders different values, though x,y,z,u are identical
            {'description': 'V texture coordinate'},
        )


class NfsuVertexNoNormal(DeclarativeCompoundBlock):
    block_description = (
        'A single mesh vertex without normal (24 bytes). Used by a few meshes, e.g. '
        'SUPRA_STYLE02_HEADLIGHT_C. Same layout as the 36-byte vertex with the normal '
        'omitted (Direct3D FVF order: position, diffuse color, texture coordinates)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex position'})
        color = (IntegerBlock(length=4), {'description': _VERTEX_COLOR_DESCRIPTION})
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})


class NfsuVertexSkinned(DeclarativeCompoundBlock):
    block_description = (
        'A single mesh vertex with normal and skinning data (60 bytes). Used by a few '
        'world meshes (flags 0x4081 in the mesh info chunk)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex position'})
        normal = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex normal'})
        color = (IntegerBlock(length=4), {'description': _VERTEX_COLOR_DESCRIPTION})
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})
        blend_weights = (Point3D(child=DecimalBlock(length=4)), {'description': 'Blend weights', 'is_unknown': True})
        blend_indices = (Point3D(child=DecimalBlock(length=4)), {'description': 'Blend indices', 'is_unknown': True})


# Size in bytes of each vertex layout, in the order of MeshVerticesChunk.Fields.vertices possible blocks
_NFSU_VERTEX_SIZES = [36, 24, 60]


def _vertex_layout_index(ctx):
    # The vertex layout is not stored explicitly (or not found yet): it is the vertex size that fills the payload
    # after the alignment filler. Raw bytes (the last choice) if there are no vertices, or the size is not known
    vertex_amount = ctx.data('../0/data/vertex_amount')
    payload_length = chunk_payload_remaining(ctx)
    for i, size in enumerate(_NFSU_VERTEX_SIZES):
        if vertex_amount and payload_length == vertex_amount * size:
            return i
    return len(_NFSU_VERTEX_SIZES)


class MeshVerticesChunk(ChunkBlock):
    block_description = (
        'Mesh vertices. Amount of vertices is defined by the mesh info chunk (the first '
        'chunk of the same mesh data container). Vertex size (36, 24 or 60 bytes) is '
        'determined by the chunk length'
    )

    CHUNK_ID = 0x00_13_4B_01
    ALIGNMENT = 0x80
    CHECK_ELEVENS = True

    class Fields(ChunkBlock.Fields):
        vertices = (
            DelegateBlock(
                possible_blocks=[
                    ArrayBlock(child=NfsuVertex(), length='../0/data/vertex_amount'),
                    ArrayBlock(child=NfsuVertexNoNormal(), length='../0/data/vertex_amount'),
                    ArrayBlock(child=NfsuVertexSkinned(), length='../0/data/vertex_amount'),
                    chunk_rest(),
                ],
                choice_index=(lambda ctx, **_: _vertex_layout_index(ctx), 'depends on chunk_length'),
            ),
            {
                'description': 'Vertices: 36-byte vertices with normal, 24-byte vertices without normal or 60-byte '
                'vertices with normal and skinning data, whichever fills the chunk. Raw bytes if the mesh '
                'has no vertices'
            },
        )


class NfsuMeshMaterial(DeclarativeCompoundBlock):
    block_description = 'A part of the mesh drawn with one texture: a range of the triangle list'

    class Fields(DeclarativeCompoundBlock.Fields):
        bounding_box_min = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box minimum corner'})
        indices_amount = (IntegerBlock(length=4), {'description': 'Amount of vertex indexes (3 per triangle)'})
        bounding_box_max = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box maximum corner'})
        texture_index = (
            IntegerBlock(length=4),
            {'description': 'Index of texture id in the texture ids chunk (0x00134012) of the mesh'},
        )
        light_material_index = (IntegerBlock(length=4, is_signed=True), {'is_unknown': True})
        unk = (ArrayBlock(child=IntegerBlock(length=4), length=4), {'is_unknown': True})
        indices_offset = (
            IntegerBlock(length=4),
            {'description': 'Index of the first vertex index in the faces chunk: sum of previous `indices_amount`'},
        )
        flags = (IntegerBlock(length=4), {'is_unknown': True})


class NfsuMeshMaterialsChunk(ChunkBlock):
    block_description = 'Mesh materials: the triangle list of the mesh split into ranges with their own texture'

    CHUNK_ID = 0x00_13_4B_02
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        materials = (
            records_to_chunk_end(NfsuMeshMaterial(), 60),
            {'description': 'Materials, in the order of their ranges in the faces chunk'},
        )


# NFS Most Wanted: same chunk ids with other layouts. A mesh may have several vertex buffers (one 0x00134B01 chunk
# each); a new buffer starts at every material whose effect differs from the previous material's one. Vertex indexes
# of a material point to its buffer. Told apart from NFSU/NFSU2 chunks by layout (see `matches_chunk` methods)

NFSMW_EFFECTS = [
    'WorldShader',
    'WorldReflectShader',
    'WorldBoneShader',
    'WorldNormalMap',
    'CarShader',
    'GlossyWindow',
    'billboardshader',
    'WorldMinShader',
    'WorldNoFogShader',
    'FEShader',
    'FEMaskShader',
    'FilterShader',
    'OverbrightShader',
    'ScreenFilterShader',
    'RainDropShader',
    'RunwayLightShader',
    'VisualTreatmentShader',
    'WorldPrelitShader',
    'ParticlesShader',
    'skyshader',
    'shadow_map_mesh',
    'SkyboxCurrentGen',
    'ShadowPolyCurrentGen',
    'CarShadowMapShader',
    'WorldDepthShader',
    'WorldNormalMapDepth',
    'CarShaderDepth',
    'GlossyWindowDepth',
    'TreeDepthShader',
    'shadow_map_mesh_depth',
    'NormalMapNoFog',
]


def _peek_aligned_payload(ctx, alignment: int = 0x10) -> bytes:
    """Payload of the chunk at the buffer position without the 0x11 alignment filler. Buffer position is not changed"""
    pos = ctx.buffer.tell()
    try:
        ctx.buffer.seek(4, SEEK_CUR)
        length = int.from_bytes(ctx.buffer.read(4), 'little')
        filler = -ctx.buffer.tell() % alignment
        return ctx.buffer.read(length)[filler:]
    finally:
        ctx.buffer.seek(pos)


def _in_nfsmw_mesh_container(ctx) -> bool:
    """Whether the chunk at the buffer position is in NFSMW mesh data container: its first chunk (mesh info) has MW
    layout. `ctx` is context of the container's sub-chunks array"""
    items = ctx._data
    return bool(items) and isinstance(items[0]['data'], dict) and 'vertex_buffers_amount' in items[0]['data']


def nfsmw_vertex_buffer_materials(materials: list) -> List[List[int]]:
    """Indexes of materials per vertex buffer: a new buffer starts at every change of effect"""
    groups = []
    for i, material in enumerate(materials):
        if not groups or material['effect'] != materials[i - 1]['effect']:
            groups.append([])
        groups[-1].append(i)
    return groups


class NfsmwMeshHeaderChunk(ChunkBlock):
    block_description = (
        'NFSMW mesh header: id, name, bounding box and transformation of a single mesh. '
        'Same id as in NFSU, the name is null-terminated'
    )

    CHUNK_ID = 0x00_13_40_11
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=3), {'is_unknown': True})
        version = (IntegerBlock(length=2, value_validator=Eq(0x16)), {'description': 'Version of the mesh header'})
        flags = (IntegerBlock(length=2), {'is_unknown': True})
        mesh_id = (IntegerBlock(length=4), {'description': 'Mesh id (hash of the name), listed in the mesh ids chunk'})
        faces_amount = (IntegerBlock(length=2), {'description': 'Amount of faces (triangles) of the mesh'})
        vertex_amount = (IntegerBlock(length=2), {'description': 'Amount of vertices, usually 0', 'is_unknown': True})
        bones_amount = (IntegerBlock(length=1), {'is_unknown': True})
        textures_amount = (IntegerBlock(length=1), {'description': 'Amount of items in the texture ids chunk'})
        light_materials_amount = (
            IntegerBlock(length=1),
            {'description': 'Amount of items in the light materials chunk'},
        )
        position_markers_amount = (IntegerBlock(length=1), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        bounding_box_min = (NfsuVec3(), {'description': 'Minimum corner of the axis-aligned bounding box of the mesh'})
        bounding_box_max = (NfsuVec3(), {'description': 'Maximum corner of the axis-aligned bounding box of the mesh'})
        transform = (
            ArrayBlock(child=DecimalBlock(length=4), length=16),
            {'description': 'Transformation matrix 4x4, row by row'},
        )
        unk2 = (ArrayBlock(child=IntegerBlock(length=4), length=6), {'is_unknown': True})
        unk3 = (ArrayBlock(child=DecimalBlock(length=4), length=2), {'is_unknown': True})
        mesh_name = (
            NullTerminatedUTF8Block(length=None),
            {'description': 'Mesh name, e.g. "BMWM3GTR_BASE_A". Used as the name of exported mesh'},
        )
        name_padding = (chunk_rest(), {'usage': 'io,doc', 'description': 'Zero bytes up to 4-bytes alignment'})

    def matches_chunk(self, ctx) -> bool:
        # NFSU2 header (same version): fixed 28-byte name at offset 164, zeros before it
        payload = _peek_aligned_payload(ctx)
        if len(payload) < 161 or payload[12] != 0x16:
            return False
        return not (len(payload) == 192 and not any(payload[156:164]) and is_name_bytes(payload[164:]))


class NfsmwMeshChunk(ChunkBlock):
    block_description = 'NFSMW mesh info chunk: amounts of materials, vertex buffers and vertex indexes'

    CHUNK_ID = 0x00_13_49_00
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4), {'description': 'Usually 0x12', 'is_unknown': True})
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        materials_amount = (IntegerBlock(length=4), {'description': 'Amount of materials'})
        unk2 = (IntegerBlock(length=4), {'is_unknown': True})
        vertex_buffers_amount = (IntegerBlock(length=4), {'description': 'Amount of vertices chunks'})
        unk3 = (ArrayBlock(child=IntegerBlock(length=4), length=4), {'is_unknown': True})
        indices_amount = (IntegerBlock(length=4), {'description': 'Amount of vertex indexes in the faces chunk'})

    def matches_chunk(self, ctx) -> bool:
        return len(_peek_aligned_payload(ctx)) == 48


class NfsmwMeshMaterial(DeclarativeCompoundBlock):
    block_description = 'NFSMW mesh material: a range of the triangle list drawn with one texture and effect'

    class Fields(DeclarativeCompoundBlock.Fields):
        bounding_box_min = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box minimum corner'})
        bounding_box_max = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box maximum corner'})
        texture_index = (
            IntegerBlock(length=1),
            {'description': 'Index of diffuse texture id in the texture ids chunk (0x00134012) of the mesh'},
        )
        normal_texture_index = (IntegerBlock(length=1), {'description': 'Index of normal map texture id'})
        height_texture_index = (IntegerBlock(length=1), {'description': 'Index of height map texture id'})
        specular_texture_index = (IntegerBlock(length=1), {'description': 'Index of specular map texture id'})
        opacity_texture_index = (IntegerBlock(length=1), {'description': 'Index of opacity map texture id'})
        light_material_index = (IntegerBlock(length=1), {'description': '0xFF if none', 'is_unknown': True})
        unk0 = (IntegerBlock(length=2), {'is_unknown': True})
        unk1 = (BytesBlock(length=16), {'is_unknown': True})
        effect = (
            IntegerBlock(length=4),
            {
                'description': 'Effect (shader), defines vertex layout: '
                + ', '.join(f'{i}: {name}' for i, name in enumerate(NFSMW_EFFECTS))
            },
        )
        effect_pointer = (IntegerBlock(length=4), {'description': 'Filled by the game in runtime', 'is_unknown': True})
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        vertex_amount = (IntegerBlock(length=4), {'description': 'Amount of vertices of the material'})
        faces_amount = (IntegerBlock(length=4), {'description': 'Amount of triangles of the material'})
        unk2 = (BytesBlock(length=24), {'is_unknown': True})
        indices_amount = (IntegerBlock(length=4), {'description': 'Amount of vertex indexes (3 per triangle)'})
        unk3 = (BytesBlock(length=8), {'is_unknown': True})


class NfsmwMeshMaterialsChunk(ChunkBlock):
    block_description = 'NFSMW mesh materials: the triangle list split into ranges with their own texture and effect'

    CHUNK_ID = 0x00_13_4B_02
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        materials = (
            records_to_chunk_end(NfsmwMeshMaterial(), 104),
            {'description': 'Materials, in the order of their ranges in the faces chunk'},
        )

    def matches_chunk(self, ctx) -> bool:
        return _in_nfsmw_mesh_container(ctx)


class NfsmwMeshFacesChunk(ChunkBlock):
    block_description = 'NFSMW mesh faces: a triangle list. Amount of vertex indexes is defined by the mesh info chunk'

    CHUNK_ID = 0x00_13_4B_03
    ALIGNMENT = 0x10

    class Fields(ChunkBlock.Fields):
        faces = (
            ArrayBlock(
                child=ArrayBlock(child=IntegerBlock(length=2), length=3),
                length=lambda ctx: ctx.data('../0/data/indices_amount') // 3,
            ),
            {
                'description': 'Triangles: 3 vertex indexes each, pointing to the vertex buffer of the material the '
                'triangle belongs to'
            },
        )
        padding = (chunk_rest(), {'usage': 'io,doc', 'description': 'Padding to 4 bytes'})

    def matches_chunk(self, ctx) -> bool:
        return _in_nfsmw_mesh_container(ctx)


class NfsmwVertex44(DeclarativeCompoundBlock):
    block_description = 'NFSMW vertex with two texture coordinates (44 bytes), skyshader'

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex position'})
        normal = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex normal'})
        color = (IntegerBlock(length=4), {'description': _VERTEX_COLOR_DESCRIPTION})
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})
        uv2 = (ArrayBlock(child=DecimalBlock(length=4), length=2), {'is_unknown': True})


class NfsmwVertex60(DeclarativeCompoundBlock):
    block_description = 'NFSMW vertex with tangent (60 bytes), WorldReflectShader and WorldNormalMap effects'

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex position'})
        normal = (Point3D(child=DecimalBlock(length=4)), {'description': 'Vertex normal'})
        color = (IntegerBlock(length=4), {'description': _VERTEX_COLOR_DESCRIPTION})
        u = (DecimalBlock(length=4), {'description': 'U texture coordinate'})
        v = (DecimalBlock(length=4), {'description': 'V texture coordinate'})
        uv2 = (ArrayBlock(child=DecimalBlock(length=4), length=2), {'is_unknown': True})
        tangent = (ArrayBlock(child=DecimalBlock(length=4), length=4), {'description': 'Tangent (x, y, z, w)'})


def _nfsmw_vertex_buffer(ctx):
    """(vertex amount, effect) of the vertices chunk being read: its index among vertices chunks of the container picks
    the group of materials. `ctx`: the chunk's context, named by its index in the container (the chunks before it,
    whether it is read in place or as a lazy part later)"""
    items = ctx.parent._data[: int(ctx.name)]
    buffer_index = sum(1 for x in items if isinstance(x['data'], dict) and x['data'].get('chunk_id') == 0x00_13_4B_01)
    materials = next(
        (x['data']['materials'] for x in items if isinstance(x['data'], dict) and 'materials' in x['data']), []
    )
    groups = nfsmw_vertex_buffer_materials(materials)
    if buffer_index >= len(groups):
        return 0, None
    group = [materials[i] for i in groups[buffer_index]]
    return sum(m['vertex_amount'] for m in group), group[0]['effect']


def _nfsmw_vertex_layout_index(ctx):
    vertex_amount, effect = _nfsmw_vertex_buffer(ctx)
    payload_length = chunk_payload_remaining(ctx)
    if vertex_amount and payload_length == vertex_amount * 36:
        return 0
    if vertex_amount and payload_length == vertex_amount * 44:
        return 1
    if vertex_amount and payload_length == vertex_amount * 60:
        return 3 if effect == 2 else 2
    return 4


class NfsmwMeshVerticesChunk(ChunkBlock):
    block_description = (
        'NFSMW vertex buffer. A mesh has one per group of consecutive materials with the same '
        'effect; amount of vertices is the sum of `vertex_amount` of these materials. Vertex size (36, 44 or 60 '
        'bytes) depends on the effect'
    )

    CHUNK_ID = 0x00_13_4B_01
    ALIGNMENT = 0x80

    class Fields(ChunkBlock.Fields):
        vertices = (
            DelegateBlock(
                possible_blocks=[
                    ArrayBlock(child=NfsuVertex(), length=lambda ctx: _nfsmw_vertex_buffer(ctx)[0]),
                    ArrayBlock(child=NfsmwVertex44(), length=lambda ctx: _nfsmw_vertex_buffer(ctx)[0]),
                    ArrayBlock(child=NfsmwVertex60(), length=lambda ctx: _nfsmw_vertex_buffer(ctx)[0]),
                    ArrayBlock(child=NfsuVertexSkinned(), length=lambda ctx: _nfsmw_vertex_buffer(ctx)[0]),
                    chunk_rest(),
                ],
                choice_index=(lambda ctx, **_: _nfsmw_vertex_layout_index(ctx), 'depends on effect and chunk_length'),
            ),
            {
                'description': 'Vertices: 36-byte vertices with normal, 44-byte vertices with two texture coordinates, '
                '60-byte vertices with tangent or 60-byte vertices with skinning data (WorldBoneShader), whichever '
                'fills the chunk. Raw bytes if the layout is unknown'
            },
        )

    def matches_chunk(self, ctx) -> bool:
        return _in_nfsmw_mesh_container(ctx)


class NfsmwMeshMaterialName(ChunkBlock):
    block_description = 'NFSMW material name, one chunk per material in the order of materials'

    CHUNK_ID = 0x00_13_4C_02

    class Fields(ChunkBlock.Fields):
        name = (NullTerminatedUTF8Block(length=None), {'description': 'Material name, e.g. "BMWM3GTR_BADGING"'})
        padding = (chunk_rest(), {'usage': 'io,doc', 'description': 'Zero bytes up to 4-bytes alignment'})


class Chunk80134100(ChunkBlock):
    block_description = (
        'Mesh data container: holds the mesh info chunk (always first), vertices chunk and faces chunk of a single mesh'
    )

    CHUNK_ID = 0x80_13_41_00

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [
                NfsuMeshChunk(),
                NfsuMeshFacesChunk(),
                MeshVerticesChunk(),
                NfsuMeshMaterialsChunk(),
                NfsmwMeshChunk(),
                NfsmwMeshFacesChunk(),
                NfsmwMeshVerticesChunk(),
                NfsmwMeshMaterialsChunk(),
                NfsmwMeshMaterialName(),
            ],
            'Child chunks, read until the payload is exhausted. Block class picked according to the chunk id',
        )


class Chunk00134002(ChunkBlock):
    block_description = 'File info: original path of the file and unknown values'

    CHUNK_ID = 0x00_13_40_02

    class Fields(ChunkBlock.Fields):
        chunk_length = (
            IntegerBlock(length=4, value_validator=Or([128, 144])),
            {'usage': 'io,doc', 'description': CHUNK_LENGTH_DESCRIPTION + ': 128 in NFSU, 144 in NFSU2'},
        )
        unk_0 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_1 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_2 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_3 = (
            IntegerBlock(length=4),
            {
                'description': 'Amount of meshes in the file? Equals to the amount of items in the mesh ids chunk',
                'is_unknown': True,
            },
        )
        file_path = (
            UTF8Block(length=56),
            {
                'description': 'Path of this file in the original development environment, e.g. '
                '"..\\PC\\CD\\CARS\\S2000\\GEOMETRY.BIN"'
            },
        )
        unk = (UTF8Block(length=32), {'description': 'Some name, e.g. "DEFAULT"', 'is_unknown': True})
        unk_4 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_5 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_6 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_7 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_8 = (IntegerBlock(length=4), {'is_unknown': True})
        unk_9 = (IntegerBlock(length=4), {'is_unknown': True})
        nfsu2_padding = (
            BytesBlock(length=(lambda ctx: ctx.data('chunk_length') - 128, '0 in NFSU, 16 in NFSU2')),
            {'description': 'NFSU2 only: zero bytes', 'is_unknown': True},
        )


class Chunk00134003(ChunkBlock):
    block_description = 'List of mesh ids contained in the file, one item per mesh descriptor chunk'

    CHUNK_ID = 0x00_13_40_03

    class Fields(ChunkBlock.Fields):
        items = (
            records_to_chunk_end(
                CompoundBlock(
                    fields=[
                        ('value', IntegerBlock(length=4), {}),
                        ('unk', IntegerBlock(length=4, value_validator=Eq(0)), {}),
                    ],
                    inline_description='Two 32-bit unsigned integers (little-endian): value, then unk (always 0)',
                ),
                8,
            ),
            {'description': 'Mesh ids: `value` equals to `mesh_id` of the corresponding mesh header chunk'},
        )


class Chunk00134011(ChunkBlock):
    block_description = 'Mesh header: id, name, bounding volume and flags of a single mesh'

    CHUNK_ID = 0x00_13_40_11

    class Fields(ChunkBlock.Fields):
        chunk_length = chunk_length_field(
            CHUNK_LENGTH_DESCRIPTION + ': 176 (NFSU) or 192 (NFSU2) + length of alignment filler'
        )
        elevens = elevens_field()
        unk2 = (IntegerBlock(length=4, value_validator=Eq(0x00_00_00_00)), {'is_unknown': True})
        unk3 = (IntegerBlock(length=4, value_validator=Eq(0x00_00_00_00)), {'is_unknown': True})
        unk4 = (IntegerBlock(length=4, value_validator=Eq(0x00_00_00_00)), {'is_unknown': True})
        version = (
            IntegerBlock(length=2, value_validator=Or([0x13, 0x16])),
            {'description': 'Version of the mesh header: 0x13 in NFSU, 0x16 in NFSU2'},
        )
        unk6 = (
            IntegerBlock(length=2),
            {'description': 'Flags? 0x40 or 0 in NFSU, also 0x80 in NFSU2', 'is_unknown': True},
        )
        mesh_id = (IntegerBlock(length=4), {'description': 'Mesh id (hash), listed in the mesh ids chunk of the file'})
        unk7 = (
            IntegerBlock(length=4),
            {'description': 'Amount of faces? Equals to `faces_amount` of the mesh info chunk', 'is_unknown': True},
        )
        mesh_flags = (
            IntegerBlock(length=4),  # maybe contains stream count / LOD / material count
            {'description': 'Mesh flags. Maybe contains stream count / LOD / material count', 'is_unknown': True},
        )
        unk10 = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        bounding_box_min = (NfsuVec3(), {'description': 'Minimum corner of the axis-aligned bounding box of the mesh'})
        bounding_box_max = (NfsuVec3(), {'description': 'Maximum corner of the axis-aligned bounding box of the mesh'})
        obb_axis0 = (NfsuVec3(), {'description': 'First axis of the oriented bounding box'})
        obb_axis1 = (NfsuVec3(), {'description': 'Second axis of the oriented bounding box'})
        obb_axis2 = (NfsuVec3(), {'description': 'Third axis of the oriented bounding box'})

        # is it a quaternion?
        unk_float0 = (
            DecimalBlock(length=4),
            {'description': 'Is it a quaternion (with the next 3 floats)?', 'is_unknown': True},
        )
        unk_float1 = (DecimalBlock(length=4), {'is_unknown': True})
        unk_float2 = (DecimalBlock(length=4), {'is_unknown': True})
        unk_U = (DecimalBlock(length=4, value_validator=Eq(1.0)), {'is_unknown': True})

        unk_V = (DecimalBlock(length=4, value_validator=Eq(0.0)), {'is_unknown': True})
        unk_W = (DecimalBlock(length=4, value_validator=Eq(0.0)), {'is_unknown': True})
        unk_X = (IntegerBlock(length=4), {'description': 'Always 0x0012F800 in NFSU', 'is_unknown': True})
        unk_Y = (IntegerBlock(length=4), {'description': 'Always equals to `unk_X`', 'is_unknown': True})
        unk_Z = (IntegerBlock(length=4, value_validator=Eq(0x00_00_00_00)), {'is_unknown': True})
        nfsu2_unk_floats = (
            ArrayBlock(
                child=DecimalBlock(length=4),
                length=(lambda ctx: 2 if ctx.data('version') == 0x16 else 0, '0 in NFSU, 2 in NFSU2'),
            ),
            {'description': 'NFSU2 only', 'is_unknown': True},
        )
        nfsu2_unk_ints = (
            ArrayBlock(
                child=IntegerBlock(length=4),
                length=(lambda ctx: 2 if ctx.data('version') == 0x16 else 0, '0 in NFSU, 2 in NFSU2'),
            ),
            {'description': 'NFSU2 only', 'is_unknown': True},
        )
        mesh_name = (
            UTF8Block(length=28),
            {'description': 'Mesh name, e.g. "S2000_KIT08_FRONT_BUMPER_A". Used as the name of exported mesh'},
        )


class Chunk00134012(ChunkBlock):
    block_description = 'A list of 32-bit values (hashes) of the mesh, presumably texture ids'

    CHUNK_ID = 0x00_13_40_12

    class Fields(ChunkBlock.Fields):
        items = (
            records_to_chunk_end(
                CompoundBlock(
                    fields=[
                        ('value', IntegerBlock(length=4), {}),
                        ('unk', IntegerBlock(length=4, value_validator=Eq(0)), {}),
                    ],
                    inline_description='Two 32-bit unsigned integers (little-endian): value, then unk (always 0)',
                ),
                8,
            ),
            {'description': 'Items', 'is_unknown': True},
        )


class Chunk00134013(ChunkBlock):
    block_description = 'A list of 32-bit values (hashes) of the mesh, presumably shader/material ids'

    CHUNK_ID = 0x00_13_40_13

    class Fields(ChunkBlock.Fields):
        items = (
            records_to_chunk_end(
                CompoundBlock(
                    fields=[
                        ('value', IntegerBlock(length=4), {}),
                        ('unk', IntegerBlock(length=4, value_validator=Eq(0)), {}),
                    ],
                    inline_description='Two 32-bit unsigned integers (little-endian): value, then unk (always 0)',
                ),
                8,
            ),
            {'description': 'Items', 'is_unknown': True},
        )


class Chunk001340XX(DeclarativeCompoundBlock):
    block_description = (
        'Unknown chunk with id 0x001340XX, kept as raw bytes. Known ids: 0x00134004 in '
        'the file info container (20-byte records per mesh, starting with mesh id); '
        '0x00134017, 0x00134018, 0x00134019, 0x0013401A in mesh descriptors'
    )

    # the lowest byte of the id is `index`: picked for 0x001340XX ids but those of the other mesh chunks
    chunk_ids = [0x00134000 | i for i in range(0x100) if i not in (0x02, 0x03, 0x11, 0x12, 0x13)]

    class Fields(DeclarativeCompoundBlock.Fields):
        index = (
            IntegerBlock(length=1, value_validator=Or([4, 23, 24, 25, 0x1A])),
            {'description': 'Lowest byte of the chunk id'},
        )
        chunk_id = (
            IntegerBlock(length=3, is_signed=False, value_validator=Eq(0x00_13_40)),
            {'description': 'Upper 3 bytes of the chunk id'},
        )
        chunk_length = chunk_length_field()
        payload = (BytesBlock(length='chunk_length'), {'is_unknown': True})

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        data = super().read(ctx, name, read_bytes_amount)
        if data['index'] == 23 and len(data['payload']) != 12:
            raise BlockDefinitionException(f'Chunk 0x00134017: {len(data["payload"])} bytes of payload, 12 expected')
        return data


class Chunk80134008(ChunkBlock):
    block_description = 'Unknown chunk of the file info container, usually empty'

    CHUNK_ID = 0x80_13_40_08

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length='chunk_length'), {'is_unknown': True})


class NfsuMeshDescriptorChunk(ChunkBlock):
    block_description = (
        'Mesh descriptor: everything about a single mesh (a car part). Contains the mesh '
        'header chunk, lists of hashes and the mesh data container with vertices and '
        'faces. The converter exports every descriptor as a separate mesh, named after '
        '`mesh_name` of the header'
    )

    CHUNK_ID = 0x80_13_40_10

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [
                NfsmwMeshHeaderChunk(),
                Chunk00134011(),
                Chunk00134012(),
                Chunk00134013(),
                Chunk80134100(),
                Chunk001340XX(),
            ],
            'Child chunks, read until the payload is exhausted. Block class picked according to the chunk id',
        )


class Chunk80134001(ChunkBlock):
    block_description = (
        'File info container: the first meaningful chunk of the file. Holds file info, '
        'the list of mesh ids and a per-mesh table'
    )

    CHUNK_ID = 0x80_13_40_01

    class Fields(ChunkBlock.Fields):
        # always 3 or 4 blocks
        sub_chunks = chunks_field(
            [Chunk00134002(), Chunk00134003(), Chunk001340XX(), Chunk80134008()],
            'Child chunks (always 3 or 4), read until the payload is exhausted. Block class '
            'picked according to the chunk id',
        )


class Chunk80134020(ChunkBlock):
    block_description = 'Unknown top-level chunk, kept as raw bytes'

    CHUNK_ID = 0x80_13_40_20

    class Fields(ChunkBlock.Fields):
        payload = (BytesBlock(length='chunk_length'), {'is_unknown': True})


# top-level chunks of a geometry pack, and of the rest of a car GEOMETRY.BIN after it
NFSU_GEOMETRY_PACK_CHUNK_BLOCKS = [ZeroChunk(), NfsuMeshDescriptorChunk(), Chunk80134001(), Chunk80034020()]


class NfsuBinGeometry(DeclarativeCompoundBlock):
    block_description = (
        'Geometry pack: car geometry file (GEOMETRY.BIN), also a chunk of track bundles. '
        'A sequence of chunks, each having 32-bit id and 32-bit payload length; chunks with id '
        'starting with 0x80 are containers of other chunks. The pack starts with a file info '
        'container, followed by a mesh descriptor per mesh (car part, scenery object), '
        'interleaved with zero-id padding chunks'
    )
    serializer = 'NfsuBinGeometrySerializer'

    def __init__(self, whole_file: bool = True, **kwargs):
        # car GEOMETRY.BIN: the chunks after the pack (e.g. 0x80034020) are read as `trailing_chunks`, up to the end
        # of the file
        super().__init__(**kwargs)
        self.whole_file = whole_file

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (
            IntegerBlock(length=4, value_validator=Eq(0x80134000)),
            {'description': 'Resource ID (chunk id of the whole file)'},
        )
        data_length = (
            IntegerBlock(length=4, programmatic_value=SizeOf('chunks')),
            {'description': "Length of the pack's chunks (`chunks`) in bytes"},
        )
        chunks = chunks_field(
            NFSU_GEOMETRY_PACK_CHUNK_BLOCKS,
            'Chunks of the pack: the file info container, mesh descriptors and zero-id padding chunks. Block class '
            'picked according to the chunk id',
            byte_length=('data_length', 'up to data_length bytes'),
        )
        trailing_chunks = chunks_field(
            NFSU_GEOMETRY_PACK_CHUNK_BLOCKS,
            'Car GEOMETRY.BIN: the chunks after the pack, up to the end of the file (zero-id padding, 0x80034020; '
            'none in a pack of a bundle)',
            byte_length=(
                lambda ctx: ctx.read_bytes_remaining if ctx.block.whole_file else 0,
                'up to the end of the file (car GEOMETRY.BIN), else 0',
            ),
        )

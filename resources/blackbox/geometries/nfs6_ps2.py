from typing import Dict

from library.read_blocks import ArrayBlock, BytesBlock, DecimalBlock, DeclarativeCompoundBlock, IntegerBlock
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import UTF8Block
from resources.blackbox.chunks import container_chunk_length, nfsu_sub_chunks_field
from resources.blackbox.geometries.nfsu import _CHUNK_ID_DESCR, _CHUNK_LENGTH_DESCR, _ELEVENS_DESCR, elevens_length
from resources.eac.fields.misc import Point3D

# NFS Hot Pursuit 2 (PS2, Black Box) meshes ("solids"): loader SLUS_203.62 0x1036c8. Vertex data is a VIF code stream
# for the VU1 microprogram of the game (.vutext, uploaded at VU1 address 0): see `nfs6_ps2_mesh` in
# serializers/geometries.py for its layout


def _elevens_field():
    return (
        BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
        {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
    )


class Nfs6Ps2SolidPackHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Mesh pack header: path of the pack in the development tools'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034001)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (IntegerBlock(length=4), {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR})
        file_path = (
            UTF8Block(length=lambda ctx: ctx.data('chunk_length')),
            {'description': 'Path of the pack, e.g. "TRACK11\\Pipeline\\Scenery\\eLabScenery0.bin"'},
        )


class Nfs6Ps2MeshHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Mesh header: id, name, amounts, bounding box and the transformation of the mesh in '
            'the modelling tool',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034003)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + 192),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        runtime_pointers = (
            BytesBlock(length=8),
            {'description': 'List links, written by the game when the mesh is loaded', 'is_unknown': True},
        )
        mesh_id = (
            IntegerBlock(length=4),
            {
                'description': 'Mesh id: Black Box hash of the name (`bin_hash`) in most meshes, used by scenery '
                'definitions'
            },
        )
        version = (IntegerBlock(length=4), {'description': 'Always 11', 'is_unknown': True})
        name = (UTF8Block(length=24), {'description': 'Mesh name, e.g. "TRN_SECTION50_CHOP1"'})
        unk_hash = (IntegerBlock(length=4), {'description': 'A hash in some meshes, else 0', 'is_unknown': True})
        unk_zero = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        num_draw_groups = (
            IntegerBlock(length=2),
            {'description': 'Amount of draw groups (records of the draw groups chunk)'},
        )
        unk0 = (ArrayBlock(child=IntegerBlock(length=2), length=3), {'is_unknown': True})
        unk1 = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        bounding_box_min = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the vertices'})
        pad0 = (IntegerBlock(length=4, value_validator=Eq(0)), {'description': 'Padding'})
        bounding_box_max = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the vertices'})
        pad1 = (IntegerBlock(length=4, value_validator=Eq(0)), {'description': 'Padding'})
        transform = (
            ArrayBlock(child=DecimalBlock(length=4), length=16),
            {
                'description': 'Transformation matrix 4x4, row by row, the position in the last row: where the mesh '
                'was in the modelling tool. Not used to draw it: scenery instances place meshes'
            },
        )
        unk4 = (BytesBlock(length=32), {'is_unknown': True})


class Nfs6Ps2MeshTextures(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Textures of the mesh, referenced by index by draw groups'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034006)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('textures')) * 8),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        textures = (
            ArrayBlock(
                child=ArrayBlock(child=IntegerBlock(length=4), length=2),
                length=lambda ctx: ctx.data('chunk_length') // 8,
            ),
            {
                'description': 'Texture name hash (`name_hash` of the texture in a texture pack) and a value written '
                'by the game, per texture'
            },
        )


class Nfs6Ps2MeshDrawGroup(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A run of VIF packets drawn with one texture: one call of the VU1 microprogram per '
            'packet, each packet a set of triangle strips of up to 40 vertices',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        texture_index = (IntegerBlock(length=4), {'description': 'Index of the texture in the textures chunk'})
        unk0 = (IntegerBlock(length=4), {'description': 'Always 0x80008000', 'is_unknown': True})
        data_offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of the VIF packets in the VIF data (after its alignment filler)'},
        )
        num_qwords = (IntegerBlock(length=2), {'description': 'Length of the VIF packets in 16-byte units'})
        vu_flags = (
            IntegerBlock(length=2),
            {
                'description': 'The VIF ITOP value of the packets: bits choose what the VU1 microprogram does '
                '(lighting, environment map...); 0x4100 when the packets have vertex normals'
            },
        )
        bounding_box_min = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the vertices'})
        unk1 = (IntegerBlock(length=1), {'is_unknown': True})
        num_vertices = (IntegerBlock(length=1), {'description': 'Amount of vertices of all packets'})
        num_triangles = (IntegerBlock(length=1), {'description': 'Amount of triangles of all packets'})
        unk2 = (IntegerBlock(length=1), {'is_unknown': True})
        bounding_box_max = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the vertices'})
        vu_flags_2 = (IntegerBlock(length=4), {'description': 'The same as `vu_flags`', 'is_unknown': True})
        unk3 = (BytesBlock(length=16), {'is_unknown': True})


class Nfs6Ps2MeshDrawGroups(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Draw groups of the mesh'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034004)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + len(ctx.data('draw_groups')) * 64
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        draw_groups = (
            ArrayBlock(
                child=Nfs6Ps2MeshDrawGroup(),
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // 64,
            ),
            {'description': 'Draw groups'},
        )


class Nfs6Ps2MeshVifData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Vertex data: a VIF code stream (UNPACK commands, MSCAL starting the VU1 '
            'microprogram after every packet)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034005)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + len(ctx.data('data'))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        data = (
            BytesBlock(length=lambda ctx: ctx.data('chunk_length') - len(ctx.data('elevens'))),
            {'description': 'VIF codes and their data'},
        )


class Nfs6Ps2Mesh(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Mesh: header, textures, draw groups and VIF data'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034002)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field(
            [Nfs6Ps2MeshHeader(), Nfs6Ps2MeshTextures(), Nfs6Ps2MeshDrawGroups(), Nfs6Ps2MeshVifData()],
            'Child chunks. Unknown ones: 0x3401D (8-byte records), 0x34007, 0x34012, 0x34011',
        )


class Nfs6Ps2SolidPack(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Mesh pack (Black Box "solid list"): a header and meshes, found by their mesh id',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034000)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field([Nfs6Ps2SolidPackHeader(), Nfs6Ps2Mesh()], 'Header and meshes')

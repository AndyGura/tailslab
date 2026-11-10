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
                'description': 'The VIF ITOP value of the packets, bits of what the VU1 microprogram does (SLUS_203.62 '
                '.vutext 0x3d): 0x80 lighting (0x333: the vertex colours become ambient + diffuse + specular of 3 '
                'directional lights from the vertex normals, scaled by the vertex colours, see '
                '`Nfs6Ps2LightingParameters`), 0x100 environment map pass (0x42b: every triangle drawn again with a '
                'sphere map of the reflection vector, added by an alpha from the material), 0x40 an unused third '
                'pass, 0x200 clipping (set by the game). 0x4000: the packets have vertex normals. The game removes '
                '0x100 when environment maps are off and 0x80 / 0x100 for a mesh drawn without lights, skips draw '
                'groups with 0x400 in the normal draw (0x10dd58) and adds 4 for textures with `vertex_lit_env` set'
            },
        )
        bounding_box_min = (Point3D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the vertices'})
        unk1 = (IntegerBlock(length=1), {'is_unknown': True})
        num_vertices = (IntegerBlock(length=1), {'description': 'Amount of vertices of all packets'})
        num_triangles = (IntegerBlock(length=1), {'description': 'Amount of triangles of all packets'})
        material_index = (
            IntegerBlock(length=1),
            {
                'description': 'Index of the lighting material in the lighting materials chunk of the mesh '
                '(0x3401D), 255: the material "Default"'
            },
        )
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


class Nfs6Ps2MeshLightingMaterials(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Lighting materials of the mesh (`Nfs6Ps2LightingMaterial` of GLOBAL/GLOBALB), '
            'referenced by index by draw groups (`material_index`). Looked up by name hash when the mesh is loaded '
            '(SLUS_203.62 0x10c458), an unknown hash takes the material "Default"',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x0003401D)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + len(ctx.data('materials')) * 8
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        materials = (
            ArrayBlock(
                child=ArrayBlock(child=IntegerBlock(length=4), length=2),
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // 8,
            ),
            {
                'description': 'Material name hash (`bin_hash`, the `name_hash` of a lighting material) and a value '
                'written by the game (the material pointer), per material'
            },
        )


class Nfs6Ps2Mesh(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Mesh: header, textures, draw groups and VIF data'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034002)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field(
            [
                Nfs6Ps2MeshHeader(),
                Nfs6Ps2MeshTextures(),
                Nfs6Ps2MeshDrawGroups(),
                Nfs6Ps2MeshVifData(),
                Nfs6Ps2MeshLightingMaterials(),
            ],
            'Child chunks. Unknown ones: 0x34007, 0x34012, 0x34011',
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


class Nfs6Ps2LightingParameters(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Lighting parameters of a material, turned into the 4 VU1 vectors of the draw by '
            'SLUS_203.62 0x116828. The VU1 lighting (.vutext 0x333, `vu_flags` 0x80) per vertex: colour = ambient + '
            'sum of the 3 lights of light colour * (diffuse * max(N.L, 0) + specular * S(max(R.L, 0.1))), times '
            '1 + (vertex colour - 255) * vertex_colors / 255, clamped to 0..255; N the vertex normal, L the direction '
            'to the light, R the camera ray reflected by N, S(d) = specular_scale * d ^ specular_exponent computed '
            'with the float bit pattern (bits(S) = bits(scale) + exponent * (bits(d) - bits(1.0)))',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        specular_exponent = (DecimalBlock(length=4), {'description': 'Exponent of the specular highlight'})
        specular_scale = (DecimalBlock(length=4), {'description': 'Scale of the specular highlight'})
        specular_exponent_factor = (DecimalBlock(length=4), {'description': 'Multiplies specular_exponent'})
        specular_scale_factor = (DecimalBlock(length=4), {'description': 'Multiplies specular_scale'})
        diffuse_color = (
            ArrayBlock(child=DecimalBlock(length=4), length=3),
            {'description': 'RGB multipliers of the light colours for the diffuse light'},
        )
        env_facing = (
            DecimalBlock(length=4),
            {
                'description': 'Environment map pass (`vu_flags` 0x100, .vutext 0x42b): its vertex alpha / 128 where '
                'the reflected camera ray comes back towards the camera, env_grazing where it goes away from it, '
                'linear in between (the z of the ray in the environment map view)'
            },
        )
        specular_color = (
            ArrayBlock(child=DecimalBlock(length=4), length=3),
            {'description': 'RGB multipliers of the light colours for the specular light'},
        )
        env_grazing = (DecimalBlock(length=4), {'description': 'See env_facing'})
        paint_specular_exponent = (
            DecimalBlock(length=4),
            {'description': 'Specular exponent instead of specular_exponent for a texture with `vertex_lit_env`'},
        )
        paint_specular_scale = (
            DecimalBlock(length=4),
            {'description': 'Specular scale instead of specular_scale for a texture with `vertex_lit_env`'},
        )
        paint_specular_exponent_factor = (DecimalBlock(length=4), {'description': 'Multiplies paint_specular_exponent'})
        paint_specular_scale_factor = (DecimalBlock(length=4), {'description': 'Multiplies paint_specular_scale'})
        paint_alpha = (
            DecimalBlock(length=4),
            {
                'description': 'Texture with `vertex_lit_env`: the lighting writes the vertex alpha paint_alpha + '
                '(paint_alpha_specular - paint_alpha) * the specular of the first light, which masks the environment '
                'map pass in a race (destination alpha)'
            },
        )
        paint_alpha_specular = (DecimalBlock(length=4), {'description': 'See paint_alpha'})
        vertex_colors = (
            DecimalBlock(length=4),
            {'description': 'How much the vertex colours scale the light: 1 fully, 0 not at all'},
        )
        unk = (BytesBlock(length=4), {'is_unknown': True})


class Nfs6Ps2LightingMaterial(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Lighting material: two parameter sets, the front end one and the race one '
            '(SLUS_203.62 0x10a438 uploads the race set while a race is loaded, 0x169168)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        runtime_links = (BytesBlock(length=8), {'description': 'List links, written by the game', 'is_unknown': True})
        name_hash = (IntegerBlock(length=4), {'description': 'Black Box hash of the name (`bin_hash`)'})
        name = (UTF8Block(length=20), {'description': 'Material name, e.g. "RegPaintRed"'})
        frontend = (Nfs6Ps2LightingParameters(), {'description': 'Parameters in the front end (car showroom)'})
        race = (Nfs6Ps2LightingParameters(), {'description': 'Parameters in a race'})
        runtime_vu_vectors = (
            BytesBlock(length=128),
            {'description': 'The VU1 vectors of both sets, written by the game (0x1169f8)', 'is_unknown': True},
        )


class Nfs6Ps2LightingMaterials(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Lighting materials (GLOBAL/GLOBALB, loader SLUS_203.62 0x114f38), found by name '
            'hash by the meshes (`Nfs6Ps2MeshLightingMaterials`)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x0003401E)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: len(ctx.data('elevens')) + 16 + 0x140 * len(ctx.data('materials')),
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        unk = (BytesBlock(length=8), {'is_unknown': True})
        version = (IntegerBlock(length=4, value_validator=Eq(1)), {'description': 'Always 1, the game checks it'})
        num_materials = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('materials'))),
            {'description': 'Amount of materials'},
        )
        materials = (
            ArrayBlock(child=Nfs6Ps2LightingMaterial(), length=lambda ctx: ctx.data('num_materials')),
            {'description': 'Materials'},
        )

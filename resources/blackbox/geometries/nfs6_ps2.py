from typing import Dict

from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    FixedPointBlock,
    IntegerBlock,
)
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


# Collision volumes (chunk 0x80034020: car hulls "<model>_CV" in CARS/<car>/GEOMETRY, the props' in the track bundles,
# GLOBAL/INGAMEB's): V-Clip polyhedra as memory images, LoaderCollisionVolumes SLUS_203.62 0x218e10. The loader takes
# the sub-chunks five by five in this order, without checking their ids: the polyhedron, its vertices, edges, faces
# and Voronoi planes. Pointers between the features are indexes in the images (ConvertToPointers 0x1d3e68)


def _collision_elements_fields(chunk_id: int, items_field: str, item_block, item_size: int, items_description: str):
    return {
        'chunk_id': (IntegerBlock(length=4, value_validator=Eq(chunk_id)), {'description': _CHUNK_ID_DESCR}),
        'chunk_length': (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: len(ctx.data('elevens')) + item_size * len(ctx.data(items_field)),
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        ),
        'elevens': _elevens_field(),
        items_field: (
            ArrayBlock(
                child=item_block,
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // item_size,
            ),
            {'description': items_description},
        ),
    }


class Nfs6Ps2Polyhedron(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A collision polyhedron (PipelinePolyhedron object, 0x60 bytes, used in place; '
            'PipelinePolyhedron::MemoryImageLoad). Its features are the next four sub-chunks',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034021)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + 0x60),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = _elevens_field()
        list_node = (
            ArrayBlock(child=IntegerBlock(length=4), length=2),
            {
                'description': 'Written by the game: next and previous of the polyhedra list (0x331a18); leftover '
                'pointers in the files'
            },
        )
        owns_arrays = (
            IntegerBlock(length=4),
            {'description': '1 in the files: the arrays are its own (VCPolyhedron::Init 0x1d3148 / 0x1d3200)'},
        )
        debug_object = (IntegerBlock(length=4), {'description': 'Debug drawing object, 0 in the files'})
        counts = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=4),
            {
                'description': 'Amounts of vertices, edges, faces and Voronoi planes: the loader sets them from the '
                "sub-chunks' sizes (equal in the files)"
            },
        )
        maxima = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=4),
            {
                'description': "Room for vertices, edges, faces and planes: the tool's (200, 400, 100, 2400 for the "
                'cars); the loader sets them to the counts'
            },
        )
        pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=4),
            {'description': "Written by the game: the arrays' addresses; leftovers of the tool in the files"},
        )
        name_hash = (
            IntegerBlock(length=4),
            {
                'description': 'bStringHash of the name (h = -1, h = h x 33 + byte): FindPipelinePolyhedron 0x219078 '
                'finds a car\'s hull by it ("<model name>_CV", CarCollisionBody::CarCollisionBody 0x1d7e48)'
            },
        )
        name = (
            UTF8Block(length=32),
            {'description': 'Name, e.g. "CORVETTE_CV" (36 vertices, 102 edges, 68 triangles); not read by the game'},
        )
        cog_moved = (
            IntegerBlock(length=4),
            {
                'description': "0 in the files, 1 once moved by a car type's centre of gravity "
                '(PipelinePolyhedron::MoveCenterOfGravity 0x2190e0): car types sharing a model share its hull, moved '
                'by the first one'
            },
        )
        padding = (BytesBlock(length=8), {'description': 'Leftover bytes', 'is_unknown': True})


class Nfs6Ps2PolyhedronVertex(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A vertex of a collision polyhedron (VCVertex, 0x14 bytes)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        feature_type = (IntegerBlock(length=1, is_signed=True), {'description': 'Feature type: 0, a vertex'})
        num_planes = (
            IntegerBlock(length=1, is_signed=True),
            {'description': 'Its Voronoi planes, one per edge at the vertex (VCVertex::SetVoronoiPlanes 0x1d2800)'},
        )
        unk = (IntegerBlock(length=2), {'description': 'Leftover bytes', 'is_unknown': True})
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': "Position in the model's coordinates (X forward, Y left, Z up), before the move by the "
                'centre of gravity'
            },
        )
        first_plane = (
            IntegerBlock(length=4, is_signed=True),
            {'description': 'Index of its first Voronoi plane; its num_planes planes follow it'},
        )


class Nfs6Ps2PolyhedronEdge(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An edge of a collision polyhedron (VCEdge, 12 bytes). Its 4 Voronoi planes border '
            'its tail vertex, head vertex and its two faces',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        feature_type = (IntegerBlock(length=1, is_signed=True), {'description': 'Feature type: 1, an edge'})
        num_planes = (IntegerBlock(length=1, is_signed=True), {'description': 'Its Voronoi planes: 4'})
        direction = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=13, is_signed=True)),
            {'description': 'Unit direction, tail to head (stored x 8192, truncated: VCPolyhedron::NewEdge 0x1d3498)'},
        )
        first_plane = (
            IntegerBlock(length=4, is_signed=True),
            {'description': 'Index of its first Voronoi plane; its num_planes planes follow it'},
        )


class Nfs6Ps2PolyhedronFace(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A face of a collision polyhedron (VCFace, 0x18 bytes)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        feature_type = (IntegerBlock(length=1, is_signed=True), {'description': 'Feature type: 2, a face'})
        num_planes = (
            IntegerBlock(length=1, is_signed=True),
            {'description': 'Its Voronoi planes, one per edge: 3 in every polyhedron of the files (triangles)'},
        )
        unk = (IntegerBlock(length=2), {'description': 'Leftover bytes', 'is_unknown': True})
        normal = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Outward unit normal (VCFace::Move 0x1d30a8)'},
        )
        d = (DecimalBlock(length=4), {'description': 'normal . p = d on the face'})
        first_plane = (
            IntegerBlock(length=4, is_signed=True),
            {'description': 'Index of its first Voronoi plane; its num_planes planes follow it'},
        )


class Nfs6Ps2PolyhedronPlane(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A Voronoi plane of a feature of a collision polyhedron (VCVoronoiPlane, 0x18 '
            'bytes): the border of its region towards a neighbouring feature',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk = (IntegerBlock(length=4), {'description': 'Leftover bytes', 'is_unknown': True})
        normal = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': '(0, 0, 1) in the files: the game computes the planes after loading '
                '(SetVoronoiPlanes of the features)'
            },
        )
        d = (DecimalBlock(length=4), {'description': '0 in the files, computed as the normal'})
        neighbor = (
            IntegerBlock(length=4),
            {
                'description': 'The feature beyond the plane as a feature code: index << 4 | feature type (0 vertex, '
                '1 edge, 2 face), 0xffffffff none (VCPolyhedron::GetFeature 0x1d3c60)'
            },
        )


class Nfs6Ps2PolyhedronVertices(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Vertices of a collision polyhedron'}

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _collision_elements_fields(0x00034024, 'vertices', Nfs6Ps2PolyhedronVertex(), 0x14, 'Vertices'),
    )


class Nfs6Ps2PolyhedronEdges(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Edges of a collision polyhedron'}

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _collision_elements_fields(0x00034023, 'edges', Nfs6Ps2PolyhedronEdge(), 0xC, 'Edges'),
    )


class Nfs6Ps2PolyhedronFaces(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Faces of a collision polyhedron'}

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _collision_elements_fields(0x00034022, 'faces', Nfs6Ps2PolyhedronFace(), 0x18, 'Faces'),
    )


class Nfs6Ps2PolyhedronPlanes(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Voronoi planes of a collision polyhedron, the planes of each feature one after the '
            'other',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _collision_elements_fields(0x00034025, 'planes', Nfs6Ps2PolyhedronPlane(), 0x18, 'Voronoi planes'),
    )


class Nfs6Ps2CollisionVolumes(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Collision volumes: convex polyhedra for V-Clip collision tests, five sub-chunks per '
            'polyhedron (LoaderCollisionVolumes SLUS_203.62 0x218e10). A car\'s GEOMETRY has its hull "<model>_CV"; '
            "the track bundles and GLOBAL/INGAMEB the props' (CS_BarrelA_L, CS_SMOKEBOMB...). Without a hull the "
            'game takes a box (RectPolyhedron)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034020)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field(
            [
                Nfs6Ps2Polyhedron(),
                Nfs6Ps2PolyhedronVertices(),
                Nfs6Ps2PolyhedronEdges(),
                Nfs6Ps2PolyhedronFaces(),
                Nfs6Ps2PolyhedronPlanes(),
            ],
            'For each polyhedron: the polyhedron, its vertices, edges, faces and Voronoi planes',
        )

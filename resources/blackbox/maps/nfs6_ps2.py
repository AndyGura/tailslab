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
from resources.blackbox.bitmaps.nfs6_ps2 import Nfs6Ps2TexturePack
from resources.blackbox.chunks import chunk_delegate, container_chunk_length, nfsu_sub_chunks_field
from resources.blackbox.geometries.nfs6_ps2 import Nfs6Ps2LightingMaterials, Nfs6Ps2SolidPack
from resources.blackbox.geometries.nfsu import (
    _CHUNK_ID_DESCR,
    _CHUNK_LENGTH_DESCR,
    _ELEVENS_DESCR,
    ZeroChunk,
    determine_chunks_amount,
    elevens_length,
)
from resources.eac.fields.misc import Point2D, Point3D

# NFS Hot Pursuit 2 (PS2) sceneries: loader SLUS_203.62 0x14ecdc. The world of a track is the scenery instances of
# TRACKS/TRACKB<track>.LZC (track = location * 10 + variant), meshes of its mesh packs, textures of
# TRACKS/TEX<track>LOCATION.BIN and TEX<track>TRACK.BIN


class Nfs6Ps2SceneryHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Scenery header: number of the section it belongs to'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034101)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + 56),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = (
            BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        )
        runtime_pointers = (BytesBlock(length=8), {'description': 'Written by the game', 'is_unknown': True})
        section_number = (
            IntegerBlock(length=4),
            {'description': "Number of the section: index in the game's table of sceneries (0x2f8fe8)"},
        )
        unk = (BytesBlock(length=44), {'is_unknown': True})


class Nfs6Ps2SceneryInfo(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Scenery object definition: which mesh to draw'}

    class Fields(DeclarativeCompoundBlock.Fields):
        mesh_ids = (
            ArrayBlock(child=IntegerBlock(length=4), length=3),
            {
                'description': 'Mesh ids (`mesh_id` of mesh headers), 0 for none. The first one is the drawn mesh, '
                'the others probably levels of detail'
            },
        )
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        model_pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=3),
            {'description': 'Written by the game: models of the meshes', 'is_unknown': True},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        radius = (DecimalBlock(length=4), {'is_unknown': True})


class Nfs6Ps2SceneryInfos(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Scenery object definitions'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034102)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('infos')) * 40),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        infos = (
            ArrayBlock(child=Nfs6Ps2SceneryInfo(), length=lambda ctx: ctx.data('chunk_length') // 40),
            {'description': 'Definitions'},
        )


class Nfs6Ps2SceneryInstance(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Placed scenery object: world vertex = mesh vertex x rotation + position (rows '
            'of the matrix the game builds, 0x11c450)',
        }

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
        flags = (IntegerBlock(length=2), {'is_unknown': True})
        position = (Point3D(child=DecimalBlock(length=4)), {'description': 'Position in world coordinates'})
        rotation = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=14, is_signed=True), length=9),
            {'description': 'Rotation matrix 3x3, row by row (2.14 fixed point)'},
        )
        pad = (IntegerBlock(length=2), {'is_unknown': True})


class Nfs6Ps2SceneryInstances(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Placed scenery objects'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034103)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + len(ctx.data('instances')) * 48
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = (
            BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        )
        instances = (
            ArrayBlock(
                child=Nfs6Ps2SceneryInstance(),
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // 48,
            ),
            {'description': 'Instances'},
        )


class Nfs6Ps2Scenery(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Scenery of a section: object definitions referencing meshes by id, and their '
            'instances',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034100)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field(
            [Nfs6Ps2SceneryHeader(), Nfs6Ps2SceneryInfos(), Nfs6Ps2SceneryInstances()],
            'Header, definitions, instances and chunk 0x34104 (24-byte records, unknown)',
        )


class Nfs6Ps2TrackPathRecord(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A path of the track: the race route or a branch of it'}

    class Fields(DeclarativeCompoundBlock.Fields):
        path_index = (IntegerBlock(length=1), {'description': 'Index of the path, 0 for the race route'})
        is_closed = (IntegerBlock(length=1), {'description': '1: the path is a loop (circuit tracks)'})
        first_point = (IntegerBlock(length=2), {'description': 'Index of the first point of the path'})
        end_point = (
            IntegerBlock(length=2),
            {'description': 'Index after its last point; the closing point of a loop, which repeats the first one'},
        )
        num_points = (IntegerBlock(length=2), {'description': 'Amount of points'})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        length = (DecimalBlock(length=4), {'description': 'Length of the path'})
        unk1 = (DecimalBlock(length=4), {'is_unknown': True})
        start = (Point2D(child=DecimalBlock(length=4)), {'description': 'The first point'})
        next = (Point2D(child=DecimalBlock(length=4)), {'description': 'The last point of a loop, else another one'})
        unk2 = (IntegerBlock(length=4), {'is_unknown': True})


class Nfs6Ps2TrackPathHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Track paths: one record per path'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034148)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: 40 * len(ctx.data('paths'))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        paths = (
            ArrayBlock(child=Nfs6Ps2TrackPathRecord(), length=lambda ctx: ctx.data('chunk_length') // 40),
            {'description': 'Paths'},
        )


class Nfs6Ps2TrackPathPoint(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Point of a track path, on the ground plane'}

    class Fields(DeclarativeCompoundBlock.Fields):
        x = (DecimalBlock(length=4), {'description': 'X in world coordinates'})
        y = (DecimalBlock(length=4), {'description': 'Y in world coordinates'})
        path = (
            IntegerBlock(length=2),
            {'description': 'Path index in the low byte; 0x100 set on points of a branch away from the other paths'},
        )
        near_points = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=3),
            {'description': 'Indexes of near points of other paths, -1 for none'},
        )
        distance = (
            DecimalBlock(length=4),
            {
                'description': 'Distance along the race route (a branch: of the route where it starts; 0 at the closing '
                'point of a loop)'
            },
        )


class Nfs6Ps2TrackPathPoints(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Points of the track path'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034149)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: 20 * len(ctx.data('points'))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        points = (
            ArrayBlock(child=Nfs6Ps2TrackPathPoint(), length=lambda ctx: ctx.data('chunk_length') // 20),
            {'description': 'Points'},
        )


class Nfs6Ps2TrackPath(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track paths: the race route (path 0) and its branches on the ground plane, a point '
            'every 20..150 m (loader SLUS_203.62 0x207b28)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x80034147)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field([Nfs6Ps2TrackPathHeader(), Nfs6Ps2TrackPathPoints()], 'Header and points')


class Nfs6Ps2CarWheel(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A wheel of a car type'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Wheel centre in car coordinates (X forward, Y left, Z up)'},
        )
        radius = (DecimalBlock(length=4), {'description': 'Wheel radius'})
        unk0 = (DecimalBlock(length=4), {'is_unknown': True})
        index = (
            IntegerBlock(length=4),
            {'description': 'Index of the wheel: front left, front right, rear right, rear left'},
        )
        unk1 = (DecimalBlock(length=4), {'is_unknown': True})
        unk2 = (IntegerBlock(length=4), {'is_unknown': True})


class Nfs6Ps2CarTypeInfo(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Car type: names, model files, wheels and physics values (0x560 bytes, the game's car "
            'type table, indexed by car type: SLUS_203.62 0x11e860, 0x188790)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=32), {'description': 'Car type name, e.g. "CORVETTEHP" (the HP version of a car)'})
        model_name = (
            UTF8Block(length=32),
            {'description': 'Car model name: folder of the model and prefix of its texture names, e.g. "CORVETTE"'},
        )
        geometry_path = (UTF8Block(length=32), {'description': 'Model file, e.g. "CARS\\CORVETTE\\GEOMETRY.BIN"'})
        compressed_geometry_path = (
            UTF8Block(length=32),
            {'description': 'Compressed model file, e.g. "CARS\\CORVETTE\\GEOMETRY.LZC"'},
        )
        unk0 = (BytesBlock(length=160), {'is_unknown': True})
        wheels = (ArrayBlock(child=Nfs6Ps2CarWheel(), length=4), {'description': 'Wheels'})
        unk1 = (BytesBlock(length=920), {'description': 'Physics values and more', 'is_unknown': True})
        car_class = (IntegerBlock(length=4), {'description': '0 racer, 1 police, 2 traffic'})
        unk2 = (BytesBlock(length=36), {'is_unknown': True})


class Nfs6Ps2CarTypeInfos(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Car types table (GLOBAL/GLOBALB.LZC)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034600)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + 0x560 * len(ctx.data('car_types'))
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = (
            BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        )
        car_types = (
            ArrayBlock(
                child=Nfs6Ps2CarTypeInfo(),
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // 0x560,
            ),
            {'description': 'Car types'},
        )


class Nfs6Ps2CarSkin(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A paint of a car type (SLUS_203.62 0x188180 finds it by car type and paint number; '
            'CarModel_Init 0x11e860 takes its lighting material for the meshes\' material "CARSKIN")',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        car_type_index = (IntegerBlock(length=4), {'description': 'Index of the car type in the car types table'})
        skin_number = (IntegerBlock(length=4), {'description': 'Paint number n of the textures <model>_SKIN<n>'})
        name = (UTF8Block(length=32), {'description': 'Paint name, e.g. "Guards Red"'})
        color_bit = (IntegerBlock(length=4), {'description': 'A single bit: the colour group', 'is_unknown': True})
        lighting_material_hash = (
            IntegerBlock(length=4),
            {'description': 'Name hash of the lighting material of the paint (`Nfs6Ps2LightingMaterial`)'},
        )
        swatch_hash = (
            IntegerBlock(length=4),
            {'description': 'Name hash of the colour swatch texture shown in the menus, e.g. "COLORSWATCH_SILVER"'},
        )
        unk = (BytesBlock(length=12), {'is_unknown': True})


class Nfs6Ps2CarSkins(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Paints of the car types (GLOBAL/GLOBALB.LZC, 0x187f98)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034601)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: 0x40 * len(ctx.data('skins'))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        skins = (
            ArrayBlock(child=Nfs6Ps2CarSkin(), length=lambda ctx: ctx.data('chunk_length') // 0x40),
            {'description': 'Paints'},
        )


NFS6_PS2_BUNDLE_CHUNK_BLOCKS = [
    ZeroChunk(),
    Nfs6Ps2SolidPack(),
    Nfs6Ps2TexturePack(),
    Nfs6Ps2Scenery(),
    Nfs6Ps2TrackPath(),
    Nfs6Ps2CarTypeInfos(),
    Nfs6Ps2LightingMaterials(),
    Nfs6Ps2CarSkins(),
]


class Nfs6Ps2ChunkBundle(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 (PS2) chunk bundle (*.BUN, *.BIN, uncompressed *.LZC): a '
            'sequence of chunks, each having 32-bit id, 32-bit payload length and payload; chunks with the highest '
            'bit of id set are containers of other chunks. Mesh packs, texture packs and sceneries are decoded, '
            'other chunks are kept as raw bytes',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunks = (
            ArrayBlock(
                length=(lambda ctx: determine_chunks_amount(ctx), 'until the end of file'),
                child=chunk_delegate(NFS6_PS2_BUNDLE_CHUNK_BLOCKS),
            ),
            {'description': 'Chunks'},
        )


class Nfs6Ps2TrackBundle(Nfs6Ps2ChunkBundle):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track bundle (TRACKS/TRACKB<track>.LZC, uncompressed; TRACKB<track>.BUN): '
            'sceneries and meshes of the world of the track, with its race data (AI paths, collision, ...). '
            'Textures are in TRACKS/TEX<track>LOCATION.BIN and TEX<track>TRACK.BIN. '
            + super().schema['block_description'],
        }

    def serializer_class(self):
        from serializers.maps import Nfs6Ps2TrackBundleSerializer

        return Nfs6Ps2TrackBundleSerializer


def is_nfs6_ps2_bundle(chunk_ids) -> bool:
    """Whether top-level chunk ids are of an NFS Hot Pursuit 2 (PS2) chunk bundle: one with a mesh pack (NFSU's is
    0x80134000) or a texture pack (NFSU's is 0xB3300000)"""
    return 0x80034000 in chunk_ids or 0xB0300001 in chunk_ids


def is_nfs6_ps2_track_bundle(chunk_ids) -> bool:
    return 0x80034000 in chunk_ids and 0x80034100 in chunk_ids


class Nfs6Ps2CarGeometry(Nfs6Ps2ChunkBundle):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Car model (CARS/<car>/GEOMETRY.LZC, uncompressed; GEOMETRY.BIN): its meshes. Textures are '
            'in CARS/TEXTURES.BIN and GLOBAL/GLOBALB.LZC, wheel positions in the car types table of GLOBALB. '
            + super().schema['block_description'],
        }

    def serializer_class(self):
        from serializers.geometries import Nfs6Ps2CarSerializer

        return Nfs6Ps2CarSerializer


def is_nfs6_ps2_car_bundle(chunk_ids) -> bool:
    """A car model bundle starts with chunk 0x34013 and has a mesh pack"""
    return bool(chunk_ids) and chunk_ids[0] == 0x00034013 and 0x80034000 in chunk_ids

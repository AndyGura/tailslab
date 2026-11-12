from typing import Dict

from library.read_blocks import (
    ArrayBlock,
    BitFlagsBlock,
    BytesBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    EnumByteBlock,
    FixedPointBlock,
    IntegerBlock,
)
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import UTF8Block
from resources.blackbox.bitmaps.nfs6_ps2 import Nfs6Ps2TexturePack
from resources.blackbox.chunks import chunk_delegate, container_chunk_length, nfsu_sub_chunks_field
from resources.blackbox.geometries.nfs6_ps2 import Nfs6Ps2CollisionVolumes, Nfs6Ps2LightingMaterials, Nfs6Ps2SolidPack
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
        return {
            **super().schema,
            'block_description': 'A path of the track: the race route or a branch of it (TrackPath, 40 bytes; '
            'TrackPathManager::Loader SLUS_203.62 0x207b28)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        path_index = (IntegerBlock(length=1), {'description': 'Index of the path, 0 for the race route'})
        is_closed = (
            IntegerBlock(length=1),
            {'description': '1: the path is a loop (circuit tracks): its spline wraps around'},
        )
        first_point = (IntegerBlock(length=2), {'description': 'Index of the first point of the path'})
        end_point = (
            IntegerBlock(length=2),
            {
                'description': 'Index after its last point. The closing point of a loop (a copy of the first one, '
                'distance 0) is not part of the path'
            },
        )
        num_points = (IntegerBlock(length=2), {'description': 'Amount of points: end_point - first_point'})
        start_distance = (
            DecimalBlock(length=4),
            {'description': 'Distance along the race route at the start of the path (0 for the race route)'},
        )
        end_distance = (
            DecimalBlock(length=4),
            {
                'description': 'Distance along the race route at the end of the path; of path 0: the length of the '
                'race route (TrackPathManager::Init 0x2078e8)'
            },
        )
        scale = (
            DecimalBlock(length=4),
            {
                'description': "Metres of the race route per metre of the path (1 for the race route): a car's "
                "route distance = start_distance + distance along the path's spline x scale"
            },
        )
        first_position = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Position of the first point (= points[first_point]; not read by the physics)'},
        )
        last_position = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'Position of the last point (= points[end_point - 1]; not read by the physics)'},
        )
        spline = (
            IntegerBlock(length=4),
            {
                'description': 'Written by the game: pointer to the QuickSpline (Catmull-Rom) made through the points '
                'by TrackPathManager::Init, 0 in the files'
            },
        )


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
            {
                'description': 'Path index in the low byte (read as a signed byte by '
                'TrackPathManager::FindClosestAdjacentPointOnSamePath 0x207ed0); 0x100 set on some points of a '
                'branch, away from the other paths (the high byte is not read by the physics)'
            },
        )
        near_points = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=3),
            {
                'description': 'Indexes of near points of other paths, -1 for none (TrackPathManager::UpdatePosition '
                '0x208048)'
            },
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


# The track's ground for the physics: a quad tree over the track (chunks 0x34130..0x34133, TopologyTree::Loader
# SLUS_203.62 0x152c10, called by LoaderTrackGeometry 0x153608). Node 0 is the root over -16384..16384 m in x and y,
# 10 levels deep (TopologyTree::GetSquare 0x152e08); its leaves are 32 m squares listing the polygons over them
NFS6_PS2_TERRAIN_TYPES = [
    (0, 'NONE'),
    (1, 'ROAD'),
    (2, 'DIRT'),
    (3, 'DIRTROAD'),
    (4, 'PUDDLE'),
    (5, 'DEEP_WATER'),
    (6, 'GRASS'),
    (7, 'SAND'),
    (8, 'SNOW'),
    (9, 'DIRT_SHOULDER'),
    (10, 'SAND_SHOULDER'),
    (11, 'SNOW_SHOULDER'),
    (12, 'SIDEWALK'),
    (13, 'SNOW_SIDEWALK'),
    (14, 'ROCK'),
    (15, 'WOOD_WALL'),
    (16, 'CACTUS_WALL'),
    (17, 'SOLID_WALL'),
    (18, 'BOARDWALK'),
    (19, 'COBBLESTONE'),
    (20, 'MUD_PUDDLE'),
    (21, 'ROUGH_ROAD'),
    (22, 'GRASS_SHOULDER'),
    (23, 'AUTUMN_LEAVES'),
    (24, 'AUTUMN_LEAVES_SHOULDER'),
    (25, 'MULCH'),
    (26, 'MULCH_SHOULDER'),
    (27, 'ROAD_AUTUMN'),
    (28, 'PLANT'),
    (29, 'POST'),
    (30, 'METAL_GRATE'),
    (31, 'POTHOLE'),
    (32, 'CAR'),
]


def _aligned_chunk_fields(chunk_id: int, items_field: str, item_block, item_size: int, items_description: str):
    """Fields of a chunk whose records start at the first 16-byte aligned offset of the payload (0x11 filler before
    them: the loader takes `(chunk + 0x17) & ~15`)"""
    return {
        'chunk_id': (IntegerBlock(length=4, value_validator=Eq(chunk_id)), {'description': _CHUNK_ID_DESCR}),
        'chunk_length': (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: len(ctx.data('elevens')) + item_size * len(ctx.data(items_field)),
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        ),
        'elevens': (
            BytesBlock(length=(lambda ctx: elevens_length(ctx), 'up to 16-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        ),
        items_field: (
            ArrayBlock(
                child=item_block,
                length=lambda ctx: (ctx.data('chunk_length') - len(ctx.data('elevens'))) // item_size,
            ),
            {'description': items_description},
        ),
    }


def _plain_chunk_fields(chunk_id: int, items_field: str, item_block, item_size: int, items_description: str):
    """Fields of a chunk of records right after its header"""
    return {
        'chunk_id': (IntegerBlock(length=4, value_validator=Eq(chunk_id)), {'description': _CHUNK_ID_DESCR}),
        'chunk_length': (
            IntegerBlock(length=4, programmatic_value=lambda ctx: item_size * len(ctx.data(items_field))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        ),
        items_field: (
            ArrayBlock(child=item_block, length=lambda ctx: ctx.data('chunk_length') // item_size),
            {'description': items_description},
        ),
    }


class Nfs6Ps2TopologyTreeNode(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Node of the quad tree of the track (TopologyTreeNode)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        children = (
            ArrayBlock(child=IntegerBlock(length=2), length=4),
            {
                'description': 'Children by quadrant, index (x >= centre) + 2 (y >= centre): node indexes at levels '
                '10..2, square indexes at level 1; 0 for none (TopologyTree::GetSquare 0x152e08)'
            },
        )


class Nfs6Ps2TopologyTreeNodes(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Nodes of the quad tree over the track, node 0 the root over -16384..16384 m in x '
            'and y, every node reached from it once (TopologyTree::Loader SLUS_203.62 0x152c10)',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _aligned_chunk_fields(0x00034130, 'nodes', Nfs6Ps2TopologyTreeNode(), 8, 'Nodes'),
    )


class Nfs6Ps2TopologyTreeSquare(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A 32 m square of the track, a leaf of the quad tree (TopologyTreeSquare): the '
            'polygons over it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        centre = (
            Point2D(child=DecimalBlock(length=4)),
            {
                'description': "The square's centre (its corner + 16 m; not read by the game's physics). Square 0 is "
                'a dummy at (999999, 999999)'
            },
        )
        first_index = (
            IntegerBlock(length=2),
            {'description': 'First of its entries in the polygon indexes chunk 0x34133'},
        )
        num_indexes = (
            IntegerBlock(length=2, is_signed=True),
            {'description': "Amount of its polygon indexes. The squares' ranges are back to back in square order"},
        )


class Nfs6Ps2TopologyTreeSquares(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Squares of the quad tree over the track (TopologyTree::Loader SLUS_203.62 0x152c10)',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _aligned_chunk_fields(0x00034131, 'squares', Nfs6Ps2TopologyTreeSquare(), 12, 'Squares'),
    )


class Nfs6Ps2TopologyTreePolygon(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A polygon of the ground or of a wall for the physics (TopologyTreePolygon, 32 bytes; '
            'TrackPolygon::TrackPolygon SLUS_203.62 0x1514a8). Vertex i = (x[i], y[i], z_base + z[i]), the height '
            'times 4 with `heights_x4`. Its plane: normal = normalize((v1 - v0) x (v2 - v0)), ground normals point '
            'up. A point is over it when (b - a) x (p - a) <= 0 for the edges v0 v1, v1 v2, v3 v0 and, for a quad, '
            'v2 v3 (TopologyCoordinate::GetElevation)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        visited = (
            IntegerBlock(length=1),
            {
                'description': 'Written by the game while collecting the polygons of several squares once '
                '(BuildTrackPolygons 0x1531f8), 0 in the files'
            },
        )
        bbox_select = (
            IntegerBlock(length=1),
            {
                'description': 'Vertex indexes of the bounding box: bits 0-1 the vertex of the smallest x, 2-3 '
                'smallest y, 4-5 largest x, 6-7 largest y'
            },
        )
        terrain = (
            EnumByteBlock(enum_names=NFS6_PS2_TERRAIN_TYPES),
            {
                'description': "Terrain type: index of the executable's terrain types table 0x318c00 (grip, road "
                'noise, skid marks, effects; TrackPolygonCollisionBody::GetTerrainType 0x1d8b28)'
            },
        )
        flags = (
            BitFlagsBlock(
                length=1,
                flag_names=[(0, 'not_last_ground'), (1, 'wall'), (2, 'heights_x4'), (3, 'ceiling'), (4, 'quad')],
            ),
            {
                'description': "not_last_ground: never kept as GetElevation's last ground polygon; wall (always a "
                'quad; yaw control inducing, IsYawControlInducingCollisionBody 0x1d65b0); heights_x4: heights times '
                '4; ceiling: kept after the walls, ConstrainToTopology puts a point under it; quad: 4 vertices, else '
                'a triangle (vertex 3 = vertex 2)'
            },
        )
        z_base = (IntegerBlock(length=2, is_signed=True), {'description': 'Height base, m'})
        slot = (
            IntegerBlock(length=2, is_signed=True),
            {
                'description': 'Written by the game: slot of its TrackPolygon in the slot pool, -1 none (set to -1 by '
                'the loader; leftover values in the files)'
            },
        )
        x = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=3, is_signed=True), length=4),
            {'description': 'X of the vertices, m (stored in 1/8 m)'},
        )
        y = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=3, is_signed=True), length=4),
            {'description': 'Y of the vertices, m (stored in 1/8 m)'},
        )
        z = (
            ArrayBlock(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True), length=4),
            {'description': 'Heights of the vertices above z_base, m (stored in 1/256 m)'},
        )


class Nfs6Ps2TopologyTreePolygons(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Polygons of the ground and the walls for the physics (TopologyTree::Loader '
            'SLUS_203.62 0x152c10)',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _plain_chunk_fields(0x00034132, 'polygons', Nfs6Ps2TopologyTreePolygon(), 32, 'Polygons'),
    )


class Nfs6Ps2TopologyTreeIndexes(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Polygon indexes of the quad tree's squares, the squares' ranges back to back; their "
            'sum is the amount of indexes or one less (an unused last index: 4-bytes padding) (TopologyTree::Loader '
            'SLUS_203.62 0x152c10)',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _plain_chunk_fields(0x00034133, 'indexes', IntegerBlock(length=2), 2, 'Indexes of polygons of chunk 0x34132'),
    )


class Nfs6Ps2TrackPositionMarker(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A named position on the track (TrackPositionMarker, 24 bytes, used in place)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        list_node = (
            ArrayBlock(child=IntegerBlock(length=4), length=2),
            {
                'description': 'Written by the game: next and previous of the markers list (0x330310); leftover '
                'pointers in the files'
            },
        )
        name_hash = (
            IntegerBlock(length=4),
            {
                'description': 'Name hash (bStringHash: h = -1, h = h x 33 + byte): every track has '
                '"ForwardStartingPosition" (0x8e55c895) and "BackwardStartingPosition" (0x8f90f7bf) indexes 0..7, '
                'and 2..5 markers of other names'
            },
        )
        index = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Index of the marker of its name: the grid slot of a starting position '
                '(CalculateRacerPositions 0x14a020: racer i starts at the marker of index i of the race direction)'
            },
        )
        position = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': 'X, y; the height is the ground under it (TopologyCoordinate::GetElevation)'},
        )


class Nfs6Ps2TrackPositionMarkers(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Named positions on the track: the start grids (LoaderTrackGeometry SLUS_203.62 '
            '0x153608)',
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _plain_chunk_fields(0x00034146, 'markers', Nfs6Ps2TrackPositionMarker(), 24, 'Markers'),
    )


class Nfs6Ps2TrackRoutePoint(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Point of a track route (TrackRoutePoint, 0x70 bytes)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Position; a car reset onto the route is put there (Car::ResetToRoutePoint 0x132f20)'},
        )
        direction = (
            Point2D(child=DecimalBlock(length=4)),
            {
                'description': "Unit direction of the route (TrackRoute::FindClosestPoint 0x1c1b48; the reset car's "
                'heading)'
            },
        )
        unk0 = (DecimalBlock(length=4), {'is_unknown': True})
        width_left = (
            DecimalBlock(length=4),
            {'description': "The point's lateral limits (TrackedController::FindWhereIAm 0x23a1c8)"},
        )
        width_right = (DecimalBlock(length=4), {'description': "The point's lateral limits"})
        unk1 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True})
        distance = (
            DecimalBlock(length=4),
            {'description': 'Distance along the race route (TrackRoute::GetDistanceAway 0x1c16a0)'},
        )
        flags = (
            IntegerBlock(length=4),
            {
                'description': 'Low byte: index of the signpost of the point, 0xff none; bits 14 and 15 are tested by '
                'TrackRoute::FindClosestPoint 0x1c1b48; other bits unknown'
            },
        )
        unk2 = (BytesBlock(length=63), {'is_unknown': True})
        route_number = (
            IntegerBlock(length=1),
            {'description': 'Number of its route (TrackedController::FindWhereIAm 0x23a1c8)'},
        )


def _track_routes_amount(ctx) -> int:
    """Routes are back to back, each 0x428 bytes and its points: amount of them up to the end of the chunk"""
    start = ctx.buffer.tell()
    pos, end, amount = start, start + ctx.data('chunk_length'), 0
    try:
        while pos < end:
            ctx.buffer.seek(pos + 0x10)
            pos += 0x428 + int.from_bytes(ctx.buffer.read(4), 'little') * 0x70
            amount += 1
    finally:
        ctx.buffer.seek(start)
    return amount


class Nfs6Ps2TrackRoute(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A route: a lane of the roads (numbers 1..49) or a racing line (50..; forward under '
            '60, backward from 60) (TrackRoute, 0x428 bytes and its points; TrackRouteManager::Loader SLUS_203.62 '
            '0x1c2900)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        list_node = (
            ArrayBlock(child=IntegerBlock(length=4), length=2),
            {'description': "Written by the game: next and previous in the route manager's list of its type"},
        )
        unk0 = (IntegerBlock(length=2, is_signed=True), {'description': '1 in the files', 'is_unknown': True})
        number = (
            IntegerBlock(length=2, is_signed=True),
            {'description': 'Route number (forward under 60: TrackRouteManager::GetNearestRoutePoint 0x1cb7a0)'},
        )
        route_type = (IntegerBlock(length=4), {'description': '0 a lane, 1 a racing line'})
        num_points = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('points'))),
            {'usage': 'io,doc', 'description': 'Amount of points'},
        )
        capacity = (
            IntegerBlock(length=4),
            {'description': 'Room for points: = num_points in the files (0x400 for a route the game makes)'},
        )
        flags = (
            IntegerBlock(length=4),
            {
                'description': '1: loaded from the chunk (not deleted by the unloader); 4: skipped by '
                'GetNearestRoutePoint, set by InitTrackRoutes 0x1c3250 (a route a signpost of kind 5 leads to). 1 '
                'in the files (with other high bits in 6 of the 742 routes)'
            },
        )
        unk1 = (IntegerBlock(length=4), {'description': '0 in the files', 'is_unknown': True})
        first_distance = (
            DecimalBlock(length=4),
            {
                'description': 'Written by the game: the range of route distances of the points (SetFirstAndLast '
                '0x1c2600); 0 in the files but in 6 of the 742 routes'
            },
        )
        last_distance = (DecimalBlock(length=4), {'description': 'Written by the game, as first_distance'})
        unk2 = (BytesBlock(length=0x3F0), {'is_unknown': True})
        bbox_min = (
            Point2D(child=DecimalBlock(length=4)),
            {'description': "Bounding box of the points (TrackRoute::FindClosestPoint 0x1c1b48's first test)"},
        )
        bbox_max = (Point2D(child=DecimalBlock(length=4)), {'description': 'Bounding box of the points'})
        points = (
            ArrayBlock(child=Nfs6Ps2TrackRoutePoint(), length=lambda ctx: ctx.data('num_points')),
            {'description': 'Points'},
        )


class Nfs6Ps2TrackRoutes(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Routes of the track: lanes and racing lines, used by the AI and to put a car back '
            'on the road (LoaderTrackRoutes SLUS_203.62 0x1c2f18)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x00034121)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: ctx.block.field_blocks_map['routes'].estimate_packed_size(
                    ctx.data('routes')
                ),
            ),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        routes = (
            ArrayBlock(
                child=Nfs6Ps2TrackRoute(),
                length=(lambda ctx: _track_routes_amount(ctx), 'until the end of chunk'),
            ),
            {'description': 'Routes, back to back'},
        )


class Nfs6Ps2Signpost(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A signpost: where a route point leads to another route (Signpost, 12 bytes)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        route = (
            IntegerBlock(length=1),
            {'description': 'Number of the route it leads to (Signpost::GetNewRoute 0x1c0ff8)'},
        )
        kind = (
            IntegerBlock(length=1),
            {
                'description': 'Low 3 bits: the kind (InitTrackRoutes 0x1c3250 flags the route of a kind 5 signpost '
                'with 4); the other bits unknown'
            },
        )
        point = (
            IntegerBlock(length=2),
            {'description': 'The route point it leads to (Signpost::GetNewRoutePoint 0x1c1020)'},
        )
        distance = (
            DecimalBlock(length=4),
            {
                'description': 'Written by the game: the route distance of the point (InitTrackRoutes 0x1c3250); 0 '
                'or leftovers in the files'
            },
        )
        unk = (IntegerBlock(length=4), {'description': '0, 1 or 2', 'is_unknown': True})


class Nfs6Ps2Signposts(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Signposts of the track's routes (LoaderTrackRoutes SLUS_203.62 0x1c2f18)",
        }

    Fields = type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        _plain_chunk_fields(0x00034122, 'signposts', Nfs6Ps2Signpost(), 12, 'Signposts'),
    )


def _floats(n: int) -> ArrayBlock:
    return ArrayBlock(child=DecimalBlock(length=4), length=n)


class Nfs6Ps2CarWheel(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A wheel of a car type (WheelInfo, 0x20 bytes; Wheel::Wheel SLUS_203.62 0x1a3f10)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Wheel centre in car coordinates (X forward, Y left, Z up): Suspension::Calibrate '
                '0x1a5f88 (rest position = it - centre of gravity), CarState::CalculateWheelMatrices 0x1c0d78, '
                'TwoWheelAckermanSteering::SetSteering 0x1a5d60 (wheelbase = wheels[0].x - wheels[3].x, track = '
                'wheels[0].y - wheels[1].y)'
            },
        )
        radius = (
            DecimalBlock(length=4),
            {
                'description': 'Wheel radius, m (0.299..0.57): Wheel::GetRadius 0x1a5b68, Suspension::'
                'ComputeAuxiliaries 0x1a5fc0, Wheel::GuessGroundForce, CheckForBrakeLock'
            },
        )
        width = (
            DecimalBlock(length=4),
            {
                'description': 'Tyre width, m (0.175..0.345, rear >= front): half the skid mark width = width x '
                "terrain's skid width factor x max(|cos|, 0.5) / 2 (Wheel::MaybeMakeSkids 0x1a5520)"
            },
        )
        index = (
            IntegerBlock(length=4),
            {
                'description': 'Index of the wheel: 0 front left, 1 front right, 2 rear right, 3 rear left; < 2 '
                'steering wheels, >= 2 driven wheels (Wheel::SetState 0x1a4170, IsSteeringWheel, IsDriveWheel)'
            },
        )
        geometry_y_offset = (
            DecimalBlock(length=4),
            {
                'description': "Added to the drawn wheel's (and brake's) y (CarState::CalculateWheelMatrices "
                "0x1c0d78): -0.07..0.07, towards the car's centre line (left wheels negative), 0 on traffic"
            },
        )
        unk = (IntegerBlock(length=4), {'description': '0 in every car type, not read', 'is_unknown': True})


class Nfs6Ps2CarTire(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Tyre grip of an axle of a car type (TireInfo, 0x20 bytes; read by Wheel '
            "SLUS_203.62 0x1a3f10..). The racing cars' HP versions have a little more grip",
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        max_slip_angle = (
            DecimalBlock(length=4),
            {
                'description': '12 in every car type. Wheel::GetLateralForce 0x1a4d28 picks the lateral force table '
                '(one per 2 degrees of slip angle) by slip angle in degrees x 12 / it / 2; '
                'Wheel::GuessGroundForce 0x1a4930 compares it with the slip angle in radians (the tyre slides above '
                'it: never, an exe quirk)'
            },
        )
        load_scale = (
            DecimalBlock(length=4),
            {
                'description': 'Load scale of the lateral force table: table x = load x 0.8 / it (1; 4 on the BUS; '
                'Wheel::GetLateralForce 0x1a4d28)'
            },
        )
        lateral_scale = (
            DecimalBlock(length=4),
            {
                'description': 'Lateral force = it x 2.5 x table value (1; 2 on the BUS; Wheel::GetLateralForce '
                '0x1a4d28)'
            },
        )
        lateral_grip = (
            DecimalBlock(length=4),
            {
                'description': "Lateral grip (1.4..2): friction circle radius = load x it x terrain's lateral grip "
                'x catch-up x traction boost (Wheel::FinalizeGroundForce 0x1a4ee0)'
            },
        )
        longitudinal_grip = (
            DecimalBlock(length=4),
            {
                'description': "Sliding grip (1.01..1.59): sliding force = load x it x terrain's longitudinal "
                'grip x catch-up x traction boost (Wheel::GuessGroundForce 0x1a4930)'
            },
        )
        unk = (_floats(3), {'description': '0 in every car type, not read', 'is_unknown': True})


class Nfs6Ps2CarRigidBody(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Mass and inertia of a car type (RigidBodyInfo, 0x50 bytes; RigidBody::RigidBody '
            'SLUS_203.62 0x19c9b0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        mass = (
            DecimalBlock(length=4),
            {
                'description': 'Mass, tonnes (1.5 Corvette, 0.71 Elise, 3.5 bus; RigidBody::CalculateInertiaTensor '
                '0x19cc58)'
            },
        )
        dimensions = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Length, width and height of the body, m (Corvette 4.6, 1.9, 1.2): the inertia tensor '
                'of every car type is made of them (the box formula, yaw doubled); not read by the physics'
            },
        )
        inertia_tensor = (
            _floats(16),
            {
                'description': 'Inertia tensor, 4x4 row by row, t m^2, in car coordinates (X forward, Y left, Z up), '
                'inverted into the body by RigidBody::CalculateInertiaTensor 0x19cc58. Diagonal in every car type: '
                'mass / 12 x (width^2 + height^2), mass / 12 x (length^2 + height^2), 2 x mass / 12 x (length^2 + '
                'width^2), 1'
            },
        )


class Nfs6Ps2CarSuspension(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Suspension of an axle of a car type (SuspensionInfo, 0x20 bytes; '
            'Suspension::ComputeAuxiliaries SLUS_203.62 0x1a5fc0). The force: static load + height x stiffness x '
            '(1 + progression x max(height, 0)) + velocity x damping + sway bar stiffness x (height - the other '
            "wheel's height), 0 when negative; heights in m, forces in the game's own scale",
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        progression = (
            DecimalBlock(length=4),
            {'description': 'Spring progression (1..6.5; Suspension::GetProgression 0x1a6558)'},
        )
        stiffness = (
            DecimalBlock(length=4),
            {'description': 'Spring rate (24..100; Suspension::GetStiffness 0x1a6548)'},
        )
        bump_damping = (
            DecimalBlock(length=4),
            {'description': 'Damping while compressing (4.2..6.4; Suspension::GetDamping 0x1a6518)'},
        )
        rebound_damping = (
            DecimalBlock(length=4),
            {'description': 'Damping while extending (4..6; Suspension::GetDamping 0x1a6518)'},
        )
        sway_bar_stiffness = (
            DecimalBlock(length=4),
            {
                'description': "Force per metre of height difference to the axle's other wheel (0..85; "
                'Suspension::GetSwayBarStiffness 0x1a6508)'
            },
        )
        max_height = (
            DecimalBlock(length=4),
            {
                'description': 'Bump stop, m (0.11..0.15): the height is clamped to it, the excess is the overflow '
                '(Suspension::IsBottomedOut 0x1a6600: height == it)'
            },
        )
        min_height = (
            DecimalBlock(length=4),
            {
                'description': 'Full droop, m (-0.15..-0.1): a ground below it leaves the wheel in the air '
                '(Suspension::ComputeAuxiliaries 0x1a5fc0)'
            },
        )
        compression_hack = (
            DecimalBlock(length=4),
            {
                'description': 'The drawn wheel compresses at most this far, m (0.04..0.15): offset = min(0, it - '
                'height) (Suspension::GetCompressionHackOffset 0x1a6570, PhysicsCar::UpdateCar 0x139188)'
            },
        )


class Nfs6Ps2CarDriveTrain(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Clutch, differentials and gearbox of a car type (DriveTrainInfo, 0x40 bytes; '
            'DriveTrain::DriveTrain SLUS_203.62 0x18ae70)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        shift_up_fraction = (
            DecimalBlock(length=4),
            {
                'description': 'Automatic shift up at idle + it x (redline - idle) rpm, only when the global '
                'UseOptimalShiftPoints (0x3308b4) is 0: it is 1, the computed optimum is used (CalculateShiftPoints '
                '0x18ac38). 0.8 in every car type'
            },
        )
        unk = (
            DecimalBlock(length=4),
            {'description': '500 in every car type, not read by the drive train', 'is_unknown': True},
        )
        front_final_drive = (
            DecimalBlock(length=4),
            {
                'description': 'Front differential ratio: clutch side angular velocity = wheel angular velocity x it '
                'x gear ratio (DriveTrain::GetDifferentialAngularVelocity 0x18b008, ApplyClutchTorque 0x18b6c8)'
            },
        )
        rear_final_drive = (
            DecimalBlock(length=4),
            {'description': 'Rear differential ratio, as the front one (the same in rear wheel drive cars)'},
        )
        rear_torque_split = (
            DecimalBlock(length=4),
            {
                'description': 'Share of the clutch torque sent to the rear axle: 1 rear wheel drive, 0.6 the four '
                'wheel drive cars (911TURBO, DIABLO, MURCIELAGO, LAMBOCOP); rear wheels driven when >= 0.001, front '
                'ones when <= 0.999 (DriveTrain::RearWheelDrive 0x18c080, FrontWheelDrive 0x18c0a8)'
            },
        )
        clutch_stiffness = (
            DecimalBlock(length=4),
            {
                'description': 'Clutch torque per rad/s of slip while the clutch engages or disengages '
                '(0.032..0.055; DriveTrain::GuessClutchTorque 0x18b948)'
            },
        )
        num_gears = (
            IntegerBlock(length=4),
            {
                'description': 'Number of forward gears (4 CROWNVIC, 5 or 6): the top gear is num_gears + 1 '
                '(DriveTrain::GetTopGear 0x18c0d0; the manual shift up stops there, JoyHandler_ShiftUp 0x13be88)'
            },
        )
        clutch_rate = (
            DecimalBlock(length=4),
            {
                'description': "Speed of the clutch: d(clutch)/dt = it x the clutch state's rate (-3, 0, 1.5, 0 at "
                '0x310050): opens in 1/12 s, closes in 1/6 s (DriveTrain::GetDerivative 0x18b698). 4 in every car type'
            },
        )
        gear_ratios = (
            _floats(8),
            {
                'description': 'Gear ratios: [0] reverse (negative), [1] neutral (0), [2] first .. [num_gears + 1] '
                'top gear, 0 after it'
            },
        )


class Nfs6Ps2CarEngine(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Engine of a car type (EngineInfo, 0x40 bytes; Engine::Engine SLUS_203.62 0x18a7e8). '
            'The curves are tables over evenly spaced rpm from idle_rpm to max_rpm, linear between the points '
            '(Table::GetValue 0x18f838). The HP version of a car differs in its torque curve only; the engine adds 5 % '
            '(0x3308a4) for is_hp',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        idle_rpm = (
            DecimalBlock(length=4),
            {
                'description': "Idle rpm (850..1000): the engine's lower limit (Engine::ComputeAuxiliaries 0x18a988, "
                'GetIdleRPM 0x18c2b0)'
            },
        )
        redline_rpm = (
            DecimalBlock(length=4),
            {
                'description': 'Redline rpm (6000..8500; Engine::GetRedLineRPM 0x18c2a0): only the automatic shift '
                'points use it, with UseOptimalShiftPoints 0 (CalculateShiftPoints 0x18ac38)'
            },
        )
        max_rpm = (
            DecimalBlock(length=4),
            {
                'description': 'Maximum rpm (6600..9300): the upper limit; from max_rpm - 100 the torque is -15 times '
                "the curve's (rev limiter; Engine::GetTorque 0x18aa28, GetMaxRPM 0x18c290)"
            },
        )
        inertia = (
            DecimalBlock(length=4),
            {
                'description': 'Moment of inertia of the engine: d(angular velocity)/dt = torque / it '
                '(0.00025..0.000565; Engine::GetDerivative 0x18a9d8)'
            },
        )
        torque_curve = (
            _floats(9),
            {'description': 'Full throttle torque at 9 rpm points, idle_rpm..max_rpm (Engine::GetTorque 0x18aa28)'},
        )
        friction_curve = (
            _floats(3),
            {
                'description': 'Engine braking torque at 3 rpm points, idle_rpm..max_rpm: total torque -= it x (1 - '
                'throttle) (Engine::GetTotalEngineTorque 0x18aab0)'
            },
        )


class Nfs6Ps2CarAero(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Aerodynamics of a car type (AeroInfo, 0x10 bytes; Aerodynamics::ResolveForces '
            'SLUS_203.62 0x1add70)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        drag = (
            DecimalBlock(length=4),
            {
                'description': 'Drag coefficient (0.00022..0.0006): drag force = -v x |v| x it x (2 - throttle), '
                'scaled by the catch-up boost and the draft'
            },
        )
        front_downforce = (
            DecimalBlock(length=4),
            {
                'description': 'Front downforce per m/s (0.0685..0.21), at (1, 0, 0) in car coordinates '
                '(Aerodynamics::GetDownforceAtSpeed 0x1adfb8)'
            },
        )
        rear_downforce = (
            DecimalBlock(length=4),
            {'description': 'Rear downforce per m/s (0.0805..0.25), at (-1, 0, 0) in car coordinates'},
        )
        downforce_factor = (
            DecimalBlock(length=4),
            {
                'description': "Share of the downforce in the suspensions' static load: weight + it x "
                'Aerodynamics::GetDownforceAtSpeed (0..0.7; PhysicsCar::Calibrate 0x1375f0)'
            },
        )


class Nfs6Ps2CarControls(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Steering, brakes and limits of a car type (the start of ControlInfo; Wheel::Wheel '
            'SLUS_203.62 0x1a3f10, PhysicsCar::PhysicsCar 0x137100, PhysicsCar::Move)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        steering_scale = (
            DecimalBlock(length=4),
            {
                'description': 'Front wheel angle = steering degrees x it (0.8 Elise, Opel, Vauxhall; 1 most cars; '
                '1.1..1.25 sports cars; 1.5 bus; DoSteering 0x13b630)'
            },
        )
        brake_torque = (
            DecimalBlock(length=4),
            {
                'description': 'Wheel brake torque = 4 x brake pedal x it (0.98..1.36; Wheel::CheckForBrakeLock '
                '0x1a4778, GuessGroundForce)'
            },
        )
        handbrake_torque = (
            DecimalBlock(length=4),
            {'description': 'Hand brake torque = 10 x hand brake x it (0.26..0.8; Wheel::CheckForBrakeLock 0x1a4778)'},
        )
        brake_balance = (
            DecimalBlock(length=4),
            {'description': 'Brake balance (0.5..0.65; PhysicsCar::GetBrakeSettings)'},
        )
        yaw_boost = (
            DecimalBlock(length=4),
            {'description': '4th argument of YawFrictionBoost in PhysicsCar::Move (0 in every car type)'},
        )
        yaw_boost_ebrake = (
            DecimalBlock(length=4),
            {'description': '5th argument of YawFrictionBoost in PhysicsCar::Move (2.5 in every car type)'},
        )
        max_moment_z = (
            DecimalBlock(length=4),
            {
                'description': "The rigid body's maximum yaw moment in driving style 0 (PhysicsCar::Move; 17 in "
                'every car type)'
            },
        )
        max_moment_z_sim = (
            DecimalBlock(length=4),
            {
                'description': "The rigid body's maximum yaw moment in driving style 1 (PhysicsCar::Move; 0 in every "
                'car type)'
            },
        )
        speed_limiter = (
            DecimalBlock(length=4),
            {
                'description': "Top speed, mph: the rigid body's speed limiter (PhysicsCar::PhysicsCar 0x137100, "
                "RigidBody::GetDerivative 0x19d4d0; x 1.03 with is_hp). The cars' real ones (McLaren F1 240, Elise "
                '125, Corvette 173), cops 150 (CROWNVIC)..211.15, 0 (none) on traffic'
            },
        )


class Nfs6Ps2CarTypeInfo(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Car type: names, model files, wheels and physics values (0x560 bytes, the game's car "
            'type table, indexed by car type: SLUS_203.62 0x11e860, 0x188790; used in place by the physics, '
            'PhysicsCar::PhysicsCar 0x137100)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (UTF8Block(length=32), {'description': 'Car type name, e.g. "CORVETTEHP" (the HP version of a car)'})
        model_name = (
            UTF8Block(length=32),
            {
                'description': 'Car model name: folder of the model and prefix of its texture names, e.g. "CORVETTE"; '
                'its collision hull is the polyhedron "<model name>_CV" (CarCollisionBody::CarCollisionBody 0x1d7e48)'
            },
        )
        geometry_path = (UTF8Block(length=32), {'description': 'Model file, e.g. "CARS\\CORVETTE\\GEOMETRY.BIN"'})
        compressed_geometry_path = (
            UTF8Block(length=32),
            {'description': 'Compressed model file, e.g. "CARS\\CORVETTE\\GEOMETRY.LZC"'},
        )
        unk0 = (
            BytesBlock(length=100),
            {
                'description': 'Not read by the physics code (as far as ported). Holds two more file names in some '
                'car types (e.g. "CARS\\SPIDER\\DASHGEOM.BIN" and ".LZC"), the make (e.g. "CHEVROLET") and floats',
                'is_unknown': True,
            },
        )
        is_hp = (
            IntegerBlock(length=1),
            {
                'description': '1 for the HP versions of the cars (CORVETTEHP...), 0 otherwise: != 0 sets is_hp of '
                'the rigid body (speed limiter x 1.03) and of the engine (5 % more torque) (PhysicsCar::PhysicsCar '
                '0x137100)'
            },
        )
        unk1 = (IntegerBlock(length=1), {'is_unknown': True})
        tier = (
            IntegerBlock(length=1),
            {
                'description': 'Read by RealDriver::Drive 0x13b3f8, passed to the track route editor '
                '(MaybeAddTrackRoutePoint); 0..4 (McLaren, CLK, Lamborghini cop 0; Corvette, F50, Diablo 1; Mustang, '
                'Z8 2; M5, Jaguar 3; Elise, TS50, Crown Vic and traffic 4): perhaps a performance tier',
                'is_unknown': True,
            },
        )
        unk2 = (IntegerBlock(length=1), {'is_unknown': True})
        unk3 = (
            BytesBlock(length=40),
            {'description': 'Not read by the physics code (as far as ported)', 'is_unknown': True},
        )
        center_of_gravity = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': "Centre of gravity in the model's coordinates (X forward, Y left, Z up), e.g. "
                'CORVETTE (0.24, 0, 0.3), BUS (1, 0, 1.5): RigidBody::Calibrate 0x19cc40; the model is drawn at the '
                'position - it (CarState::CalculateGeometryPosition 0x1c0f40); the collision hull is moved by -it '
                'once (PipelinePolyhedron::MoveCenterOfGravity 0x2190e0)'
            },
        )
        center_of_gravity_w = (
            DecimalBlock(length=4),
            {'description': 'W of the centre of gravity vector, 1 in every car type'},
        )
        wheels = (
            ArrayBlock(child=Nfs6Ps2CarWheel(), length=4),
            {'description': 'Wheels: front left, front right, rear right, rear left'},
        )
        tires = (ArrayBlock(child=Nfs6Ps2CarTire(), length=2), {'description': 'Tyres: front, rear'})
        rigid_body = (Nfs6Ps2CarRigidBody(), {'description': 'Mass and inertia'})
        suspensions = (ArrayBlock(child=Nfs6Ps2CarSuspension(), length=2), {'description': 'Suspensions: front, rear'})
        drive_train = (Nfs6Ps2CarDriveTrain(), {'description': 'Clutch, differentials and gears'})
        engine = (Nfs6Ps2CarEngine(), {'description': 'Engine'})
        aero = (Nfs6Ps2CarAero(), {'description': 'Aerodynamics'})
        controls = (Nfs6Ps2CarControls(), {'description': 'Steering, brakes and speed limiter'})
        unk4 = (
            BytesBlock(length=532),
            {
                'description': 'The rest of ControlInfo (zeros up to 0x330; its size is not known) and more data, '
                'not read by the physics code (as far as ported)',
                'is_unknown': True,
            },
        )
        car_class = (
            IntegerBlock(length=4),
            {
                'description': '0 racer, 1 police (siren on the horn, nitro in Be a Cop), 2 traffic (no car damage: '
                'Car::Car 0x130a48)'
            },
        )
        unk5 = (BytesBlock(length=36), {'is_unknown': True})


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
    Nfs6Ps2TrackPositionMarkers(),
    Nfs6Ps2TrackRoutes(),
    Nfs6Ps2Signposts(),
    Nfs6Ps2TopologyTreeNodes(),
    Nfs6Ps2TopologyTreeSquares(),
    Nfs6Ps2TopologyTreePolygons(),
    Nfs6Ps2TopologyTreeIndexes(),
    Nfs6Ps2CollisionVolumes(),
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
            'bit of id set are containers of other chunks. Mesh packs, texture packs, sceneries, the physics data '
            '(track paths and routes, start grid markers, ground polygons, collision volumes, car types) and the '
            'lighting materials and paints are decoded, other chunks are kept as raw bytes',
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
            'sceneries and meshes of the world of the track, with its race data (track paths, routes, start grid, '
            'the ground and wall polygons of the physics, collision volumes of the props, ...). '
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
            'block_description': 'Car model (CARS/<car>/GEOMETRY.LZC, uncompressed; GEOMETRY.BIN): its meshes and '
            'its collision hull. Textures are in CARS/TEXTURES.BIN and GLOBAL/GLOBALB.LZC, wheel positions and '
            'physics values in the car types table of GLOBALB. ' + super().schema['block_description'],
        }

    def serializer_class(self):
        from serializers.geometries import Nfs6Ps2CarSerializer

        return Nfs6Ps2CarSerializer


def is_nfs6_ps2_car_bundle(chunk_ids) -> bool:
    """A car model bundle starts with chunk 0x34013 and has a mesh pack"""
    return bool(chunk_ids) and chunk_ids[0] == 0x00034013 and 0x80034000 in chunk_ids

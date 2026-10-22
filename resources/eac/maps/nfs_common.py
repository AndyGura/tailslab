from io import BytesIO

from library.context import ReadContext
from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    EnumByteBlock,
    EnumLookupDelegateBlock,
    BytesBlock,
    FixedPointBlock,
    SubByteCompoundBlock,
)
from library.read_blocks.misc.value_validators import Eq
from resources.eac.fields.misc import RGBBlock, Point3D, Quaternion


class TexturesMapExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'Texture reference. Polygons of the track (TRK) and of props refer to items of '
            'this table by index, the item defines the actual texture in the QFS archive '
            'and its orientation on the polygon',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        texture_number = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Index of the texture in the track QFS file (<track>0.QFS)'},
        )
        unk = (IntegerBlock(length=1), {'is_unknown': True})
        alignment = (
            EnumByteBlock(
                enum_names=[
                    (1, 'rotate_180'),
                    (3, 'rotate_270'),
                    (5, 'normal'),
                    (9, 'rotate_90'),
                    (16, 'flip_v'),
                    (18, 'rotate_270_2'),
                    (20, 'flip_h'),
                    (24, 'rotate_90_2'),
                ]
            ),
            {
                'description': 'Orientation of the texture on the polygon, which game uses instead of UV-s. '
                'The converter uses base UV-s (0,1), (1,1), (1,0), (0,0) for the 4 polygon '
                'vertices and modifies them according to the enum value: rotate_* shift them '
                'by 1, 2 or 3 vertices, flip_h/flip_v mirror them'
            },
        )
        luminosity = (RGBBlock(), {'description': 'Luminosity color'})
        black = (RGBBlock(), {'description': 'Unknown, usually black', 'is_unknown': True})


class PolygonMapExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A record of the polygon_map extrablock (NFS2, NFS2 SE TRK blocks): road vector and '
            "surface of a polygon of the block's `road_polygons`, one record per polygon (in every block of the NFS2 "
            'and NFS2 SE tracks)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        vectors_idx = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'An index of entry in road_vectors extrablock'},
        )
        surface = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (1, 'barriers', 'boolean', [], 'The car checks barriers while on this polygon'),
                    (1, 'objects', 'boolean', [], 'Track objects are checked while a car is on this polygon'),
                    (
                        6,
                        'type',
                        'number',
                        [],
                        'Surface type (0..15 in the NFS2 and NFS2 SE tracks), indexes the grip / surface tables of '
                        'the physics. 0 = barrier / wall',
                    ),
                ],
            ),
            {
                'description': 'Road surface byte, as NFS2 SE uses it: low 6 bits `type` the surface type, which '
                "indexes the physics' grip / surface tables; bit 0x80 `barriers`: a car standing on the polygon checks "
                'barriers (nfs2sen.exe 0x44e8e0), bit 0x40 `objects`: track objects are checked. Value 0x0e is not '
                'road: the road polygon search (0x4384c0) skips it. A polygon whose `type` is 0 is a barrier / wall '
                'for the barrier check',
            },
        )


class MedianExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A record of the median_polygons extrablock (NFS2, NFS2 SE TRK blocks): the road '
            "polygons of a slice, one record per slice of the block (record index = slice - the block's "
            '`first_slice`). NFS2 SE searches the run of `road_polygons` for the polygon under a car (nfs2sen.exe '
            '0x4384c0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        first_polygon = (
            IntegerBlock(length=2, is_signed=False),
            {'description': "Index of the slice's first polygon in the block's `road_polygons`"},
        )
        num_polygons = (
            IntegerBlock(length=1, is_signed=False),
            {'description': "Number of the slice's polygons in `road_polygons`, from `first_polygon` on"},
        )
        unk = (
            IntegerBlock(length=1, is_signed=False),
            {'description': '2..6 in the NFS2 and NFS2 SE tracks', 'is_unknown': True},
        )
        alt_slice_1 = (
            IntegerBlock(length=2, is_signed=True),
            {
                'description': 'A slice of an alternative route (track fork), -1 when none. When no polygon is found '
                'under a car, NFS2 SE retries the search from the nearer of `alt_slice_1` and `alt_slice_2` '
                '(nfs2sen.exe 0x438d80)'
            },
        )
        alt_slice_2 = (
            IntegerBlock(length=2, is_signed=True),
            {'description': 'A slice of another alternative route, -1 when none, used like `alt_slice_1`'},
        )


class AnimatedPropPositionFrame(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {**super().schema, 'block_description': 'A single keyframe of animated prop movement'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Object position in 3D space'},
        )
        orientation = (
            Quaternion(child=FixedPointBlock(length=2, fraction_bits=14, is_signed=True)),
            {
                'description': "Object orientation at this keyframe. Prop vertices are rotated by it (v' = q v "
                'q^-1), then moved to `position`'
            },
        )


class AnimatedPropPosition(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {**super().schema, 'block_description': 'Animation of prop position: a sequence of keyframes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        num_frames = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('frames'))),
            {'description': 'An amount of frames'},
        )
        anim_delay = (
            IntegerBlock(length=2),
            {
                'description': 'Delay between frames (animation speed). Unit is not confirmed, the converter '
                'assumes 1/64 of a second',
                'is_unknown': True,
            },
        )
        frames = (
            ArrayBlock(length=lambda ctx: ctx.data('num_frames'), child=AnimatedPropPositionFrame()),
            {'description': 'Animation frames, played in a loop'},
        )


class SpecialPropPosition(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'Positioning of a special prop: a static prop which is also a track object the car '
            'collides with (NFS2, NFS2 SE TRK blocks)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Object position in 3D space'},
        )
        special_idx = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Index of a record in the track_objects extrablock (type 11) of the same TRK block: '
                'the object the car collides with, at the same position. In the NFS2 and NFS2 SE tracks every '
                "track_objects record is referenced by exactly one special_prop of the block's props_7"
            },
        )


class PropExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': '3D model placement (prop). Same 3D model can be used few times on the track. '
            'Records of props_7 (in TRK blocks and COL file) and props_18 (in TRK blocks) extrablocks have this '
            'structure; the 3D model itself is in the prop_descriptions extrablock of the same block/file',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        block_size = (
            IntegerBlock(
                length=2,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Block size in bytes'},
        )
        type = (
            EnumByteBlock(
                enum_names=[
                    (1, 'static_prop'),
                    (3, 'animated_prop'),
                    (4, 'special_prop'),
                ]
            ),
            {'description': 'Object type. special_prop is a static prop with a reference to a track_objects record'},
        )
        prop_descr_idx = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'An index of 3D model in "prop_descriptions" extrablock'},
        )
        position = (
            EnumLookupDelegateBlock(
                enum_field='type',
                blocks=[
                    Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
                    AnimatedPropPosition(),
                    SpecialPropPosition(),
                    BytesBlock(length=lambda ctx: ctx.data('block_size') - 4),
                ],
            ),
            {
                'description': 'Object positioning in 3D space: a single point for static_prop, a sequence of '
                'keyframes for animated_prop. Block class picked according to `type`'
            },
        )


class ColPolygon(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {**super().schema, 'block_description': 'A single polygon of terrain or prop'}

    class Fields(DeclarativeCompoundBlock.Fields):
        texture = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Texture number. It is not a number of texture in QFS file. Instead, it is an index '
                'of mapping entry in corresponding COL file, which contains real texture number'
            },
        )
        texture2 = (
            IntegerBlock(length=2, is_signed=True),
            {'description': '255 (texture number for the other side == none ?)', 'is_unknown': True},
        )
        vertices = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=False), length=4),
            {
                'description': 'Polygon vertices (indexes from vertex table). NFS2 SE reads them at bytes +4..+7 of '
                'TRK road polygons (nfs2sen.exe 0x439130, 0x439200)'
            },
        )


class PropDescriptionExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': '3D model of a prop. Placed on the track by records of props_* extrablocks, '
            'which reference this model by index',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        block_size = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Block size in bytes'},
        )
        num_vertices = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Amount of vertices'},
        )
        num_polygons = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('polygons'))),
            {'description': 'Amount of polygons'},
        )
        vertices = (
            ArrayBlock(
                child=Point3D(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True)),
                length=lambda ctx: ctx.data('num_vertices'),
            ),
            {'description': 'Vertices, relative to the prop position'},
        )
        polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_polygons')),
            {
                'description': 'Polygons. Textures are referenced through the textures_map of the COL file, '
                'the same way as for terrain polygons'
            },
        )
        padding = (
            BytesBlock(length=lambda ctx: ctx.data('block_size') - ctx.local_buffer_pos),
            {'description': 'Unused space'},
        )


class LanesExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A lane marker: ties a vertex and a polygon of the block terrain to a position '
            'on a lane',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        vertex_idx = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Vertex number (inside background 3D structure : 0 to nv1+nv8)'},
        )
        track_pos = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Position along track inside block (0 to 7)'},
        )
        lat_pos = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Lateral position ? (constant in each lane), -1 at the end)'},
        )
        polygon_idx = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Polygon number (inside full-res background 3D structure : 0 to np1)'},
        )


class TrackObjectExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A record of the track_objects extrablock (type 11, NFS2, NFS2 SE TRK blocks): a '
            'track object the car collides with, placed by a special_prop of the block (`special_idx` = record '
            'index). NFS2 SE reads the records (nfs2sen.exe 0x4383f0), collides cars with them (0x441ec0), knocks '
            'them over (0x435160) and resets their state table of 256 objects (0x435310)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {
                'description': 'Global position of the object in meters, the same as the position of the '
                'special_prop referencing it'
            },
        )
        radius = (
            FixedPointBlock(length=2, fraction_bits=8, is_signed=False),
            {
                'description': 'Collision radius in meters (NFS2 SE reads it as a signed 16-bit value `<< 8`, '
                '16.16). A car hits the object when it is closer than its bounding radius + `radius`, and only if '
                "2 * `radius` is more than the car's height above the ground. 0.035..14.09 m in the NFS2 and NFS2 "
                'SE tracks; for most knockable objects (947 of 980) the horizontal extent of the prop model'
            },
        )
        object_idx = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': "Object number, the index in the game's object state table (standing / knocked "
                'away, 256 entries). In the NFS2 and NFS2 SE tracks the objects of a track are numbered 0..n-1 in '
                'block order'
            },
        )
        height = (
            FixedPointBlock(length=1, fraction_bits=1, is_signed=False),
            {
                'description': 'The top of the prop model (its highest vertex) in meters, unit 0.5 m rounded down, '
                'in every record of the NFS2 and NFS2 SE tracks (0.5..26 m). Its use in the game is unknown',
                'is_unknown': True,
            },
        )
        unk0 = (IntegerBlock(length=1, is_signed=False), {'description': 'Always 0', 'is_unknown': True})
        unk1 = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': "0..16. Mostly the index of the referencing special_prop in the block's props_7 "
                '(all but 21 of the 1504 records of the NFS2 and NFS2 SE tracks, the others in TR06)',
                'is_unknown': True,
            },
        )
        type = (
            EnumByteBlock(enum_names=[(1, 'solid'), (2, 'knockable')]),
            {
                'description': 'Object behaviour (NFS2 SE: nfs2sen.exe 0x441ec0, 0x435160): knockable (2) is knocked '
                'away when hit at abs(vx) + abs(vz) >= 11 m/s and stops being solid then; every other value is solid. '
                'The NFS2 and NFS2 SE tracks have 1 and 2 only'
            },
        )


class RoadVectorsExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'Orientation of the road surface: normal + forward vectors pair. Referenced by '
            'index from polygon_map records',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True), normalized=True),
            {'description': 'A normal vector of the road surface'},
        )
        forward = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True), normalized=True),
            {'description': 'A forward vector of the road (direction of the track)'},
        )


class CollisionExtraDataRecord(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A point of the track collision spline (road centre line) with road orientation '
            'vectors and distances to the road borders, 8 points per track block. These are the track slices the '
            'car physics walks: NFS2 SE keeps the array at `DAT_004dec18` (count `DAT_004dec10`, 0x24 bytes per '
            'record) and finds the slice of a car as the one with the nearest centre by xz distance (nfs2sen.exe '
            '0x439470)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'A global position of track collision spline point (slice centre). The unit is meter'},
        )
        normal = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True), normalized=True),
            {'description': 'A normal vector of road surface. NFS2 SE reads each signed byte as `value << 9` (16.16)'},
        )
        forward = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True), normalized=True),
            {'description': 'A forward vector, read like `normal`'},
        )
        right = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True), normalized=True),
            {'description': 'A right vector, read like `normal`'},
        )
        unk0 = (IntegerBlock(length=1), {'is_unknown': True})
        block_idx = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Index of the TRK block (chunk) this point belongs to (NFS2 SE: nfs2sen.exe 0x438f90, '
                '0x4395c0)'
            },
        )
        unk1 = (IntegerBlock(length=2), {'is_unknown': True})
        left_border = (
            FixedPointBlock(length=2, is_signed=False, fraction_bits=8),
            {
                'description': 'Distance to left track border in meters (NFS2 SE reads it as `value * 0x100`, '
                '16.16). The NFS2 SE physics takes the larger of the two borders (nfs2sen.exe 0x441720)'
            },
        )
        right_border = (
            FixedPointBlock(length=2, is_signed=False, fraction_bits=8),
            {'description': 'Distance to right track border in meters, read like `left_border`'},
        )
        flags = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Two 4-bit wall types (NFS2, NFS2 SE: 0x11, 0x44, 0x22 most often): high nibble the '
                'left road edge, low nibble the right one. NFS2 SE (nfs2sen.exe 0x458650): 0 = no wall on that side, '
                'otherwise the car hits a wall at `left_border` / `right_border` (0.25 m inside) and the nibble becomes '
                'its crash type; 6 = a car more than 3 m above the ground gets a tumble kick instead; 7 = a fast car '
                'is thrown up (tracks 6 and 7 only, switched off in the shipped game). When either nibble is 2 the '
                'vertical dynamics (newton, 0x44e170) treat the slice as having a ceiling: a car more than 10 m above '
                'the ground hits it',
            },
        )
        lanes = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (
                        4,
                        'unk',
                        'number',
                        [],
                        'Unknown. In the NFS2 and NFS2 SE files it is 0 in (nearly) exactly the slices whose '
                        '`left_lane_width` is 0 (all of TR00, TR06, TR08)',
                    ),
                    (4, 'count', 'number', [], "The slice's lane count (NFS2 SE start grid, nfs2sen.exe 0x43ea40)"),
                ],
            ),
            {
                'description': "Low nibble `count`: the slice's lane count. The NFS2 SE start grid (car start "
                'position, nfs2sen.exe 0x43ea40) puts the cars (count / 2) lane widths (`left_lane_width` / '
                '`right_lane_width`) from the centre, only on tracks whose grid side flag is set. High nibble `unk` '
                'unknown. Always 0 in the NFS3 files',
            },
        )
        left_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {
                'description': 'Lane width on the left side in meters, unit 0.5 m: NFS2 SE reads it as `value << 15` '
                '(16.16; start grid, nfs2sen.exe 0x43ea40). The NFS3 files have other values here (over the whole '
                'byte range), meaning unknown',
            },
        )
        right_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {
                'description': 'Lane width on the right side in meters, read like `left_lane_width`. The NFS3 files '
                'have other values here (over the whole byte range), meaning unknown',
            },
        )
        unk3 = (IntegerBlock(length=2), {'is_unknown': True})


class ColExtraBlock(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'A typed container of data records. The same structure is used for extrablocks '
            'inside TRK blocks and in the COL file; record type is defined by `type`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        block_size = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Block size in bytes'},
        )
        type = (
            EnumByteBlock(
                enum_names=[
                    (2, 'textures_map'),
                    (4, 'block_numbers'),
                    (5, 'polygon_map'),
                    (6, 'median_polygons'),
                    (7, 'props_7'),
                    (8, 'prop_descriptions'),
                    (9, 'lanes'),
                    (11, 'track_objects'),
                    (13, 'road_vectors'),
                    (15, 'collision_data'),
                    (18, 'props_18'),
                    (19, 'props_19'),
                ]
            ),
            {
                'description': 'Type of the data records. textures_map, props_7, prop_descriptions and '
                'collision_data are found in COL file; polygon_map, block_numbers, median_polygons, '
                'props_18, prop_descriptions, lanes, track_objects and road_vectors in TRK blocks. NFS2 and NFS2 SE '
                'TRK blocks also have types 10, 14 and 17 (meaning unknown, kept as raw bytes)'
            },
        )
        unk = (IntegerBlock(length=1, value_validator=Eq(0)), {'is_unknown': True})
        num_data_records = (
            IntegerBlock(length=2, programmatic_value=lambda ctx: len(ctx.data('data_records'))),
            {'description': 'Amount of data records'},
        )
        data_records = (
            EnumLookupDelegateBlock(
                enum_field='type',
                blocks=[
                    ArrayBlock(child=TexturesMapExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=IntegerBlock(length=2), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PolygonMapExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=MedianExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropDescriptionExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=LanesExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=TrackObjectExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=RoadVectorsExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=CollisionExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    BytesBlock(length=lambda ctx: ctx.data('block_size') - 8),
                ],
            ),
            {
                'description': 'Data records, block class picked according to `type`. Records of unknown '
                'types are kept as raw bytes'
            },
        )


class MapColFile(DeclarativeCompoundBlock):
    @property
    def schema(self):
        return {
            **super().schema,
            'block_description': 'Track additional data (COL file), a list of extrablocks: textures map (used by '
            'polygons of the TRK file), track-wide props with their 3D models and collision '
            'data (road centre line for the physics engine)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('COLL')), {'description': 'Resource ID'})
        unk = (IntegerBlock(length=4, value_validator=Eq(11)), {'is_unknown': True})
        block_size = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'File size in bytes'},
        )
        num_extrablocks = (IntegerBlock(length=4, is_signed=False), {'description': 'Number of extrablocks'})
        extrablock_offsets = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: ctx.data('num_extrablocks')),
            {'description': 'Offset to each of the extrablocks'},
        )
        extrablocks_bytes = (
            BytesBlock(length=lambda ctx: ctx.data('block_size') - 16 - 4 * ctx.data('num_extrablocks')),
            {
                'description': 'A part of block, where extra blocks data is located. Offsets are defined in '
                'previous "extrablock_offsets" field. Item type:'
                '<br/>- [ColExtraBlock](#colextrablock)',
                'usage': 'io,doc',
            },
        )
        extrablocks = (
            ArrayBlock(length=(0, 'num_extrablocks'), child=ColExtraBlock()),
            {
                'description': 'Extrablocks. The first one is always textures_map, which TRK polygons refer '
                'to. Then typically prop_descriptions, props_7 and collision_data',
                'usage': 'ui',
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        data = super().read(ctx, name, read_bytes_amount)
        data['extrablocks'] = []
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, data)
        child_block = self.field_blocks_map.get('extrablocks').child
        for i, offset in enumerate(data['extrablock_offsets']):
            self_ctx.buffer.seek(self_ctx.read_start_offset + offset + 16)
            data['extrablocks'].append(child_block.unpack(self_ctx, name=str(i)))
        return data

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


# Bits of the NFS2 COL textures_map `alignment` byte (record byte +3), most significant first, as nfs2sen.exe's
# BWorld_SetupTextureOrders (0x4356e0) reads them: a mirror (`mirror_u`, else `mirror_v`), then a turn (`rotate_90`,
# else `rotate_180`, else `rotate_270`) of the texture corners, Tex_OrientCorners (0x475164) ops 0 .. 4.
# The serializer computes the UVs from it (`nfs2_texture_uvs`, serializers/maps.py)
NFS2_TEXTURE_ALIGNMENT_BITS = [
    (0x80, 'unk_80', 'Unknown, not read by nfs2sen.exe (BWorld_SetupTextureOrders 0x4356e0)'),
    (
        0x40,
        'mirror_v',
        'Texture mirrored top to bottom (Tex_OrientCorners 0x475164 op 1: corner order [o3, o2, o1, o0]), unless '
        '`mirror_u` is set. Not set in the NFS2 and NFS2 SE tracks',
    ),
    (0x20, 'unk_20', 'Unknown, not read by nfs2sen.exe (BWorld_SetupTextureOrders 0x4356e0)'),
    (
        0x10,
        'mirror_u',
        'Texture mirrored left to right (Tex_OrientCorners 0x475164 op 0: corner order [o1, o0, o3, o2])',
    ),
    (
        0x08,
        'rotate_270',
        'Texture turned a quarter turn counterclockwise after the mirror (Tex_OrientCorners 0x475164 op 4), unless '
        '`rotate_90` or `rotate_180` is set',
    ),
    (
        0x04,
        'rotate_180',
        'Texture turned a half turn after the mirror (Tex_OrientCorners 0x475164 op 3: corner order [o2, o3, o0, '
        'o1]), unless `rotate_90` is set',
    ),
    (
        0x02,
        'rotate_90',
        'Texture turned a quarter turn clockwise after the mirror (Tex_OrientCorners 0x475164 op 2)',
    ),
    (0x01, 'unk_01', 'Unknown, set in most records, not read by nfs2sen.exe (BWorld_SetupTextureOrders 0x4356e0)'),
]


class TexturesMapExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'Texture reference of the NFS2 / NFS2 SE COL file (10 bytes). Polygons of the track '
        '(TRK) and of the props refer to items of this table by index; the item names the image in the track '
        'QFS archive and its orientation on the polygon. nfs2sen.exe reads the table at 0x4358c0 '
        '(BWorld_ReadTextureMap: count u16 at extrablock +6, records from +8), makes the texture entries of '
        'every record and animation frame at 0x4356e0 (BWorld_SetupTextureOrders) and draws the polygons with '
        'them (BWorld_AddTrackPolys 0x436ba0: road blocks of every level of detail and the props)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        texture_number = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Index of the image in the track QFS file (<track>0.QFS): an index into the SHPI '
                'items, whose names repeat (NFS2 SE TR060.QFS has 16 images named `CLIF`, ignoring case). An '
                'animated texture is this image and the next `animation_frames` - 1 ones'
            },
        )
        flags = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (1, 'unk_80', 'boolean', [], 'Unknown, not set in the NFS2 and NFS2 SE tracks'),
                    (
                        1,
                        'cull_mode_0',
                        'boolean',
                        [],
                        'Draw record field +0xa = 0 instead of 1 (meaning not verified), unless `double_sided` is set',
                    ),
                    (1, 'color_keyed', 'boolean', [], 'Drawn color keyed (polygon type 9 instead of 8)'),
                    (
                        1,
                        'double_sided',
                        'boolean',
                        [],
                        'Drawn without back face culling (draw record field +0xa = 2)',
                    ),
                    (1, 'unk_08', 'boolean', [], 'Unknown, not set in the NFS2 and NFS2 SE tracks'),
                    (
                        1,
                        'animated',
                        'boolean',
                        [],
                        'Animated: frame (simulation tick / `animation_delay`) % `animation_frames`',
                    ),
                    (1, 'unk_02', 'boolean', [], 'Unknown, not set in the NFS2 and NFS2 SE tracks'),
                    (1, 'unk_01', 'boolean', [], 'Unknown, not set in the NFS2 and NFS2 SE tracks'),
                ],
            ),
            {
                'description': 'Drawing flags, as nfs2sen.exe reads them (BWorld_AddTrackPolys 0x436ba0): 0x04 '
                '`animated`, 0x10 `double_sided` (draw record +0xa = 2: no back face culling), else 0x40 '
                '`cull_mode_0` (+0xa = 0), otherwise +0xa = 1; 0x20 `color_keyed` (polygon type 9 instead of 8)'
            },
        )
        alignment = (
            SubByteCompoundBlock(
                length=1,
                schema=[(1, name, 'boolean', [], description) for _, name, description in NFS2_TEXTURE_ALIGNMENT_BITS],
            ),
            {
                'description': 'Orientation of the texture on the polygon (the game has no UVs), as nfs2sen.exe '
                'reads it (BWorld_SetupTextureOrders 0x4356e0): without any bit of 0x5e the texture corners k0 (0, 0), '
                'k1 (1, 0), k2 (1, 1), k3 (0, 1) (image space, v down) go to the polygon slots in order o = [0, 1, 2, '
                '3], else the order is first mirrored (0x10 `mirror_u`, else 0x40 `mirror_v`), then turned (0x02 '
                '`rotate_90`, else 0x04 `rotate_180`, else 0x08 `rotate_270`) by Tex_OrientCorners (0x475164). Slot '
                'o[k] gets corner k (renderer 0x472290, 0x471540, 0x471710); slots 0..3 are the polygon vertices [v1, '
                'v0, v3, v2] (BWorld_AddTrackPolys 0x436ba0), so polygon vertex j gets corner k where o[k] = j ^ 1. '
                'Bits 0x01, 0x20, 0x80 are not read there',
            },
        )
        luminosity = (RGBBlock(), {'description': 'Luminosity color'})
        animation_frames = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Frame count of an animated texture (`flags.animated`): the images `texture_number` '
                '.. `texture_number` + this - 1. nfs2sen.exe makes the texture entries of at least one frame '
                '(BWorld_SetupTextureOrders 0x4356e0). 0 when not animated, 2..12 in the NFS2 and NFS2 SE tracks'
            },
        )
        animation_delay = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Duration of a frame of an animated texture in simulation ticks (NFS2 simulates 64 '
                'ticks per second): frame = (tick / this) % `animation_frames` (BWorld_AddTrackPolys 0x436ba0). 0 '
                'when not animated, 1..20 in the NFS2 and NFS2 SE tracks'
            },
        )
        unk = (IntegerBlock(length=1, is_signed=False), {'description': 'Always 0', 'is_unknown': True})


class PolygonMapExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'A record of the polygon_map extrablock (NFS2, NFS2 SE TRK blocks): road vector and '
        "surface of a polygon of the block's `high_polygons`, one record per polygon (in every block of the NFS2 "
        'and NFS2 SE tracks)'
    )

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
    block_description = (
        'A record of the median_polygons extrablock (NFS2, NFS2 SE TRK blocks): the road '
        "polygons of a slice, one record per slice of the block (record index = slice - the block's "
        '`first_slice`). NFS2 SE searches the run of `high_polygons` for the polygon under a car (nfs2sen.exe '
        '0x4384c0)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        first_polygon = (
            IntegerBlock(length=2, is_signed=False),
            {'description': "Index of the slice's first polygon in the block's `high_polygons`"},
        )
        num_polygons = (
            IntegerBlock(length=1, is_signed=False),
            {'description': "Number of the slice's polygons in `high_polygons`, from `first_polygon` on"},
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
    block_description = 'A single keyframe of animated prop movement'

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
    block_description = 'Animation of prop position: a sequence of keyframes'

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
    block_description = (
        'Positioning of a special prop: a static prop which is also a track object the car '
        'collides with (NFS2, NFS2 SE TRK blocks)'
    )

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
    block_description = (
        '3D model placement (prop). Same 3D model can be used few times on the track. '
        'Records of props_7 (in TRK blocks and COL file) and props_18 (in TRK blocks) extrablocks have this '
        'structure; the 3D model itself is in the prop_descriptions extrablock of the same block/file'
    )

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
    block_description = 'A single polygon of terrain or prop'

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
    block_description = (
        '3D model of a prop. Placed on the track by records of props_* extrablocks, which reference this model by index'
    )

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


class RoadLineExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'A record of the road_lines extrablock (type 9, NFS2, NFS2 SE TRK blocks): a point '
        'of the road lines (lane and edge lines) nfs2sen.exe paints over the road of the nearest blocks '
        '(BWorld_AddExtrablock9Strips 0x436d70, called by the block drawing 0x4361a0 at the highest level of '
        "detail only). Record k and record k + 1 make the strip quad k, unless record k's `line_type` is 0xff: "
        "from the slices' vectors (COL collision_data, units 1/128) the game places P0 = vertex A - forward A / "
        '2, P1 = vertex A + right A - forward A / 2, P2 = vertex B + forward A / 2, P3 = vertex B + right B + '
        'forward A / 2 (vertex units 1/256: the forward bytes are halved, the right bytes taken as they are), '
        'and the line drawing (0x44a510) cuts the quad into the shapes of the line type. The converter exports '
        'them with the track (`nfs2_road_lines`, serializers/maps.py)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        vertex_idx = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': "Index of a vertex of the block's `vertices` (0 .. nv8 + nv1 - 1; one below nv8 is "
                'relative to the next block, as for the polygons)'
            },
        )
        slice = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': "Slice of the point, relative to the block's `first_slice` (0 to 7): its forward and "
                'right vectors place the strip'
            },
        )
        line_type = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Line of the strip quad from this record to the next one, 0xff for none (ends a '
                'strip). nfs2sen.exe 0x44a510 draws types 0..4 yellow (lin2, lin4, lin6 of RENDER/PC/DTEXTURE.FSH) '
                'and 5..9 white (lin3, lin5, lin7) with the shape of type % 5: 0 a line in the middle 6/16 of the '
                'strip, 1 its second half only (dashes), 2 two lines on the outer 5/16 of each side, 3 the right '
                "line whole and the left one's second half, 4 the left whole and the right one's second half (handlers "
                "0x44bb00, 0x44b6e0, 0x44b250, 0x44a760, 0x44ace0; right = the side of the slice's right vector). "
                'All ten in the NFS2 and NFS2 SE tracks (TR04, TR06, TR07, TR08 have no road lines). Far from the '
                'camera a single quad of the whole strip (lin0 / lin1)'
            },
        )
        polygon_idx = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': "Index of a polygon of the block's `high_polygons`: nfs2sen.exe copies its `texture2` "
                'into the strip record (+4, 0x436d70), which the line drawing (0x44a510 and its handlers) does not '
                'read. Some records of the NFS2 SE tracks point past the set'
            },
        )


class TrackObjectExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'A record of the track_objects extrablock (type 11, NFS2, NFS2 SE TRK blocks): a '
        'track object the car collides with, placed by a special_prop of the block (`special_idx` = record '
        'index). NFS2 SE reads the records (nfs2sen.exe 0x4383f0), collides cars with them (0x441ec0), knocks '
        'them over (0x435160) and resets their state table of 256 objects (0x435310)'
    )

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
    block_description = (
        'Orientation of the road surface: normal + forward vectors pair. Referenced by index from polygon_map records'
    )

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
    block_description = (
        'A point of the track collision spline (road centre line) with road orientation '
        'vectors and distances to the road borders, 8 points per track block. These are the track slices the '
        'car physics walks: NFS2 SE keeps the array at `DAT_004dec18` (count `DAT_004dec10`, 0x24 bytes per '
        'record) and finds the slice of a car as the one with the nearest centre by xz distance (nfs2sen.exe '
        '0x439470)'
    )

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
                'unknown',
            },
        )
        left_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {
                'description': 'Lane width on the left side in meters, unit 0.5 m: NFS2 SE reads it as `value << 15` '
                '(16.16; start grid, nfs2sen.exe 0x43ea40)',
            },
        )
        right_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {
                'description': 'Lane width on the right side in meters, read like `left_lane_width`',
            },
        )
        unk3 = (IntegerBlock(length=2), {'is_unknown': True})


class Nfs3TexturesMapExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'Texture reference of the NFS3 COL file (8 bytes; NFS2 and NFS2 SE have 10-byte '
        'records): polygons of the COL props refer to items of this table by index. nfs3.exe reads the '
        'textures_map extrablock at load (0x41dcc0) and sets byte 7 to 0x1f where it is 0 and byte 6 to 1 '
        'where it is 0'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        texture_number = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Index of the texture in the track QFS file (TR<nn>0.QFS): below its image count in '
                'every NFS3 COL'
            },
        )
        unk0 = (IntegerBlock(length=2, is_signed=False), {'description': 'Always 0', 'is_unknown': True})
        unk1 = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': '0 mostly, else 4, 16, 32, 48, 64, 80 or 96: the values of the NFS2 textures_map '
                '`flags` (not verified in nfs3.exe)',
                'is_unknown': True,
            },
        )
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
                'description': 'Orientation of the texture on the polygon, not verified in nfs3.exe. The values are '
                'those of the NFS2 textures_map `alignment` (a bit field in nfs2sen.exe, see the NFS2 '
                '`TexturesMapExtraDataRecord`), also 64, 66, 68, 72, 82 (0x40 with 0, 2, '
                '4, 8, 0x12). The converter keeps these names and gives the COL props the UVs (0,1), (1,1), (1,0), '
                '(0,0) for the 4 polygon vertices shifted by 1, 2 or 3 vertices for rotate_* or mirrored for '
                'flip_h / flip_v, the identity for other values: for 1, 3, 5, 9, 16, 20 the UVs nfs2sen.exe gives '
                'these values, for 18 and 24 not (no mirror)',
                'is_unknown': True,
            },
        )
        unk2 = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Mostly 0; nfs3.exe makes 0 a 1 at load (0x41dcc0). Possibly the animation frame '
                'count, like NFS2 textures_map `animation_frames` (not verified)',
                'is_unknown': True,
            },
        )
        unk3 = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Mostly 0; nfs3.exe makes 0 a 0x1f at load (0x41dcc0). Possibly the animation frame '
                'delay, like NFS2 textures_map `animation_delay` (not verified)',
                'is_unknown': True,
            },
        )


class Nfs3CollisionExtraDataRecord(DeclarativeCompoundBlock):
    block_description = (
        'A track slice of NFS3 (the collision_data extrablock of the COL file, 0x24 '
        'bytes, another layout than the NFS2 one): a point of the road centre line with the road orientation '
        'vectors, the distances to the road borders, walls and lanes. One slice per FRD '
        'position record ([FrdPositionBlock](#frdpositionblock)) and per float of SIMHTS.DAT '
        '([Nfs3SimHeights](#nfs3simheights)). nfs3.exe loads the array at 0x41e370 and reads it in 0x420230, '
        '0x420bf0, 0x4a0140, 0x428d60, 0x4304b0, 0x4a2690'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Global position of the slice centre in meters (16.16)'},
        )
        unk0 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'One run of set bits in every record of the NFS3 tracks (0x03c0, 0x07c0, 0x03e0 '
                'most often; TR00 starts with 0x0ff8)',
                'is_unknown': True,
            },
        )
        walls = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (4, 'left', 'number', [], 'Wall type of the left border (where right · (p - centre) <= 0)'),
                    (4, 'right', 'number', [], 'Wall type of the right border'),
                ],
            ),
            {
                'description': 'Two 4-bit wall types: high nibble `left` the left border (the side where `right` · '
                '(p - centre) <= 0), low nibble `right` the right one. Non-zero: a wall at that border '
                '(`left_border` / `right_border`), the nibble is its crash type (0x40000 OR the nibble; nfs3.exe '
                '0x4a0140, 0x4304b0). 2: the slice is covered on that side (tunnel): the ceiling height comes from '
                "SIMHTS.DAT and no weather falls (0x420bf0, which takes the other side's nibble when the car's side "
                'has 0)',
            },
        )
        unk1 = (
            IntegerBlock(length=1, is_signed=False),
            {'description': '0, or 3 in every record of TR04', 'is_unknown': True},
        )
        normal = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True)),
            {'description': 'Normal vector of the road surface, signed bytes, unit 1/128'},
        )
        lanes = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (4, 'left', 'number', [], 'Lane count on the left side'),
                    (4, 'right', 'number', [], 'Lane count on the right side'),
                ],
            ),
            {'description': 'Lane counts: high nibble `left` the left side, low nibble `right` the right side'},
        )
        forward = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True)),
            {'description': 'Forward vector (direction of the track), read like `normal`'},
        )
        left_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {'description': 'Lane width on the left side in meters, unit 0.5 m (read as `value << 15`, 16.16)'},
        )
        right = (
            Point3D(child=FixedPointBlock(length=1, fraction_bits=7, is_signed=True)),
            {'description': 'Right vector (up x forward), read like `normal`'},
        )
        right_lane_width = (
            FixedPointBlock(length=1, is_signed=False, fraction_bits=1),
            {'description': 'Lane width on the right side in meters, read like `left_lane_width`'},
        )
        left_border = (
            FixedPointBlock(length=4, fraction_bits=16, is_signed=True),
            {'description': 'Distance from the centre to the left road border in meters (16.16)'},
        )
        right_border = (
            FixedPointBlock(length=4, fraction_bits=16, is_signed=True),
            {'description': 'Distance from the centre to the right road border in meters (16.16)'},
        )


class ColExtraBlock(DeclarativeCompoundBlock):
    block_description = (
        'A typed container of data records. The same structure is used for extrablocks '
        'inside TRK blocks and in the COL file; record type is defined by `type`'
    )

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
                    (9, 'road_lines'),
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
                'props_18, prop_descriptions, road_lines, track_objects and road_vectors in TRK blocks. NFS2 and NFS2 SE '
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
                    ArrayBlock(child=RoadLineExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
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
    block_description = (
        'Track additional data (COL file), a list of extrablocks: textures map (used by '
        'polygons of the TRK file), track-wide props with their 3D models and collision '
        'data (road centre line for the physics engine)'
    )

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


class Nfs3ColExtraBlock(ColExtraBlock):
    block_description = (
        'A typed container of data records of the NFS3 COL file: the extrablock of NFS2 '
        '(ColExtraBlock), with the NFS3 layouts of textures_map and collision_data records'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        block_size = ColExtraBlock.Fields.block_size
        type = (
            EnumByteBlock(enum_names=ColExtraBlock.Fields.type[0].enum_names),
            {
                'description': 'Type of the data records. The NFS3 COL files have textures_map, prop_descriptions, '
                'props_7, collision_data and (TR02) props_18; nfs3.exe reads only types 2 (textures_map), 7 '
                '(props_7), 8 (prop_descriptions) and 15 (collision_data) (0x41dcc0)'
            },
        )
        unk = ColExtraBlock.Fields.unk
        num_data_records = ColExtraBlock.Fields.num_data_records
        data_records = (
            EnumLookupDelegateBlock(
                enum_field='type',
                blocks=[
                    ArrayBlock(child=Nfs3TexturesMapExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=IntegerBlock(length=2), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PolygonMapExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=MedianExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=PropDescriptionExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=RoadLineExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=TrackObjectExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=RoadVectorsExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
                    ArrayBlock(child=Nfs3CollisionExtraDataRecord(), length=lambda ctx: ctx.data('num_data_records')),
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


class Nfs3MapColFile(MapColFile):
    block_description = (
        'Track additional data of NFS3 (COL file), a list of extrablocks: textures map '
        '(used by the polygons of the COL props), track-wide props with their 3D models and the track slices '
        '(collision_data). The layout of the NFS2 COL file (MapColFile), with the NFS3 records: the textures_map '
        'records are 8 bytes long (10 in NFS2), which tells the two apart (`is_nfs3_col_file`)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = MapColFile.Fields.resource_id
        unk = MapColFile.Fields.unk
        block_size = MapColFile.Fields.block_size
        num_extrablocks = MapColFile.Fields.num_extrablocks
        extrablock_offsets = MapColFile.Fields.extrablock_offsets
        extrablocks_bytes = (
            MapColFile.Fields.extrablocks_bytes[0],
            {
                'description': 'A part of block, where extra blocks data is located. Offsets are defined in '
                'previous "extrablock_offsets" field. Item type:'
                '<br/>- [Nfs3ColExtraBlock](#nfs3colextrablock)',
                'usage': 'io,doc',
            },
        )
        extrablocks = (
            ArrayBlock(length=(0, 'num_extrablocks'), child=Nfs3ColExtraBlock()),
            {
                'description': 'Extrablocks: textures_map first, then typically prop_descriptions, props_7 and '
                'collision_data',
                'usage': 'ui',
            },
        )


def is_nfs3_col_file(buffer) -> bool:
    """A COL file of NFS3: its first extrablock (textures_map) has 8-byte records (NFS2, NFS2 SE: 10 bytes). Peeks at
    the buffer and seeks back"""
    pos = buffer.tell()
    try:
        header = buffer.read(20)
        if len(header) < 20 or header[:4] != b'COLL':
            return False
        num_extrablocks = int.from_bytes(header[12:16], 'little')
        if num_extrablocks == 0:
            return False
        first_offset = int.from_bytes(header[16:20], 'little')
        buffer.seek(pos + 16 + first_offset)
        extrablock_header = buffer.read(8)
        if len(extrablock_header) < 8 or extrablock_header[4] != 2:
            return False
        block_size = int.from_bytes(extrablock_header[0:4], 'little')
        num_records = int.from_bytes(extrablock_header[6:8], 'little')
        return num_records > 0 and block_size == 8 + 8 * num_records
    finally:
        buffer.seek(pos)

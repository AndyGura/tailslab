from math import atan2, cos, hypot, sin
from typing import Dict, List, Optional

from library.read_blocks import (
    BitFlagsBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    BytesBlock,
    ArrayBlock,
    UTF8Block,
    SubByteArrayBlock,
    EnumByteBlock,
    EnumLookupDelegateBlock,
    FixedPointBlock,
    SubByteCompoundBlock,
)
from library.read_blocks.misc.value_validators import Eq
from library.spatial_edit import SpatialEditable, stored_value
from resources.eac.fields.misc import Point3D
from resources.eac.fields.numbers import Nfs1Angle14, Nfs1Angle8, Nfs1TimeField


class RoadSplinePoint(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'The description of one single point of road spline. Thank you jeff-1amstudios for'
            ' your [OpenNFS1](https://github.com/jeff-1amstudios/OpenNFS1) project',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        left_verge = (
            FixedPointBlock(length=1, fraction_bits=3),
            {'description': 'The distance to the left edge of road. After this point the grip decreases'},
        )
        right_verge = (
            FixedPointBlock(length=1, fraction_bits=3),
            {'description': 'The distance to the right edge of road. After this point the grip decreases'},
        )
        left_barrier = (
            FixedPointBlock(length=1, fraction_bits=3),
            {'description': 'The distance to invisible wall on the left'},
        )
        right_barrier = (
            FixedPointBlock(length=1, fraction_bits=3),
            {'description': 'The distance to invisible wall on the right'},
        )
        num_lanes = (
            SubByteArrayBlock(length=2, bits_per_value=4),
            {
                'description': 'Amount of lanes. First number is amount of oncoming lanes, second number is '
                'amount of ongoing ones'
            },
        )
        fence_flag = (
            SubByteArrayBlock(length=2, bits_per_value=4),
            {
                'description': 'Flags whether there is fence or not. First number is fence on left side, '
                'second number is fence on right side. Used for physics simulation: only the fence collision '
                '(Win95 SE 0x430600) and `tnfs_collision_main` read it. Rendering ignores it: fences are drawn from '
                'the `fence` byte of the terrain chunks'
            },
        )
        shoulder_surface_type = (
            SubByteArrayBlock(length=2, bits_per_value=4),
            {
                'description': 'Surface type of the road shoulders, the areas between the verge distance and the '
                'barrier: first number for the left shoulder, second number for the right one (the game takes '
                '`>> 4` and `& 0xf` of this byte). The car gets this surface while it is between `left_verge` / '
                "`right_verge` and the barrier, 0 elsewhere. It is an index into the game's road surface table "
                '(grip, drag, is_unpaved): 0 is tarmac like the road, 1 and 2 are unpaved shoulders with 20 times '
                'the velocity drag. Higher values read past the table: values above 3 cause unbearable slide in the '
                'game and make it impossible to return back to road, values around the maximum (15) cause lags and '
                "even crashes. Also used for sound: a non-zero value turns the player's wind loop into a gravel "
                'rumble (pitch value 0x18, volume +25%), an unpaved surface picks the gravel tyre squeal and dust. '
                'Decoded by [tnfs-1995](https://github.com/marcos2250/tnfs-1995) (`shoulder_surface_type`; DOS '
                'sound code 0x668ab)'
            },
        )
        item_mode = (
            EnumByteBlock(
                enum_names=[
                    (0, 'lane_split'),
                    (1, 'default_0'),
                    (2, 'lane_merge'),
                    (3, 'default_1'),
                    (4, 'tunnel'),
                    (5, 'cobbled_road'),
                    (7, 'right_tunnel_A9_A2'),
                    (8, 'no_sky'),
                    (9, 'left_tunnel_A4_A7'),
                    (11, 'unk_autumn_valley_tribunes'),
                    (12, 'left_tunnel_A4_A8'),
                    (13, 'left_tunnel_A5_A8'),
                    (14, 'waterfall_audio_left_channel'),
                    (15, 'waterfall_audio_right_channel'),
                    (16, 'unk_al1_uphill'),
                    (17, 'transtropolis_noise_audio'),  # OpenNFS1: water left channel
                    (18, 'water_audio'),  # OpenNFS1: water right channel
                ]
            ),
            {
                'description': 'Modifier of this point. Affects terrain geometry and/or some gameplay features. '
                'Effects found in the game code ([tnfs-1995](https://github.com/marcos2250/tnfs-1995) '
                "`tnfs_track_item_mode_flags`, PSX 0x80030fe8, DOS 0x5b2b9): 4, 7, 9, 12 and 13 set the car's "
                'in-tunnel flag (wind loop +20 volume and pitch value 0x5e; on PSX the voices whose patch has the '
                'reverb flag get the SPU reverb; the police siren plays `NFS_FMMB.BNK` sample 0x64 along with 0x62; '
                'the DOS camera 0x6b5a5 skips the horizon for 4, 7, 9 and 8). 5 is cobbles: the wind loop pitch '
                'wobbles between 0x40 and 0x5e with speed; a side with a fence (`fence_flag`) also gets a different '
                'fence offset in 3D crash collisions unless the mode is 5. 14 / 15 are a waterfall to the left / '
                'right: they play the waterfall loop (collision bank sample 0x3e on mixer channel 0xb), panned hard '
                'left / right and fading in and out by 5 per tick. 8 only means "no sky": the DOS camera skips the '
                'horizon, the PSX sky drawing (0x800357ec) hides the sky when the slices -0xe and -9 from the camera '
                'are both mode 8; the road renders like plain road, and the second engine flag 8 sets next to the '
                'in-tunnel one is never read. Values in the game tracks besides 1 and 3: 0 / 2 at single '
                'points, 4 in most tracks, 5 in AL2, TR4, TR7, 7 in CL2, 8 in CL3, 9 in AL3, 11 in TR2, 12 and 13 in '
                'TR3, 14 in TR2 and TR3, 15 in TR3, 16 in AL1 and TR3, 17 in TR7, 18 in TR6'
            },
        )
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Coordinates of this point in 3D space. The unit is meter'},
        )
        slope = (Nfs1Angle14(), {'description': 'Slope of the road at this point (angle if road goes up or down)'})
        slant = (Nfs1Angle14(), {'description': 'Perpendicular angle of road'})
        orientation = (
            Nfs1Angle14(),
            {'description': 'Rotation of road path, if view from the top. Equals to atan2(next_x - x, next_z - z)'},
        )
        police_spot = (
            SubByteCompoundBlock(
                length=2,
                schema=[
                    (11, 'unused', 'number', [], 'Never read, 0 in every game track'),
                    (
                        2,
                        'chance',
                        'enum',
                        ['33/128', '65/128', '97/128', 'always'],
                        'Chance that the cop shows up at this spot (mask 0x18, index into the table {0x20, 0x40, '
                        '0x60, 0x80}: a 7-bit random number must not exceed the value)',
                    ),
                    (1, 'drives_off', 'boolean', [], 'Value 4: the cop drives off, else it stays parked'),
                    (1, 'is_left', 'boolean', [], 'Value 2: the spot is at the left barrier, else at the right one'),
                    (1, 'is_spot', 'boolean', [], 'Value 1: this road point is a police spot'),
                ],
            ),
            {
                'description': 'Police spot flags, read only by the cop respawn `tnfs_ai_police_parked_respawn` '
                '(DOS 0x78f5d, PSX 0x80055014, Win95 SE 0x46b950; '
                '[tnfs-1995](https://github.com/marcos2250/tnfs-1995) `police_spot`; Ghidra labels the short '
                '`wall_normal_x` in DOS and `side_normal_x` in SE). The cop is out of play (not updated, collided or '
                'drawn) after its start respawn and after a chase it gave up. In a single player race with traffic, '
                'every tick, for each slice the player passed since the last check, the game looks at the road point '
                '0x31 (49) slices ahead: at a spot (`is_spot`) it draws the `chance`, and either the cop comes back '
                'there or the spot is passed for good. The cop is placed at the `left_barrier` / `right_barrier` of '
                'the spot (`is_left`), inset by half its width, driving the way of the player when slice 0 is one-way '
                'or the spot is on the right, else oncoming; unless it `drives_off` it stays parked (speed target 0) '
                'until it starts a chase. Every open road track has 7 to 12 spots, the circuits none. AL1: slices '
                '145, 440, 690, 1073, 1154, 1340, 1423, chance 97/128 except 440 and 1154; the other tracks: always '
                '65/128'
            },
        )
        side_normal = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=16, is_signed=True)),
            {
                'description': 'Unit vector pointing to the right side of the road, perpendicular to the road '
                'direction and tilted with the road bank (y < 0 where the right side is lower, the sign opposite to '
                '`slant`): three signed int16, 1.0 = 0x8000, so the values shown here (16.16) are half the vector. '
                'The game builds the road plane of each slice from it to place the cars on the road '
                '([tnfs-1995](https://github.com/marcos2250/tnfs-1995) `tnfs_height_road_position`: node A, '
                'B = A + 2 * side normal and the next node C)'
            },
        )
        unk2 = (IntegerBlock(length=2, value_validator=Eq(0)), {'is_unknown': True})

    @staticmethod
    def side_normal_for(orientation: float, side_normal_y: float) -> Dict:
        """`side_normal` of a point heading `orientation`, keeping its tilt `side_normal_y`: the stored values are
        half the unit vector"""
        from math import cos, sin, sqrt

        horizontal = sqrt(max(0.25 - side_normal_y**2, 0))
        return {'x': horizontal * cos(orientation), 'y': side_normal_y, 'z': -horizontal * sin(orientation)}

    def update_orientations(self, read_data, next_spline_point):
        from math import atan2

        orientation = atan2(
            next_spline_point['position']['x'] - read_data['position']['x'],
            next_spline_point['position']['z'] - read_data['position']['z'],
        )
        read_data['orientation'] = orientation
        read_data['side_normal'] = self.side_normal_for(orientation, read_data['side_normal']['y'])


class ModelPropDescrData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Map prop settings if it is a 3D model'}

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (IntegerBlock(length=1), {'description': 'An index of prop in the track FAM file'})
        resource_id_2 = (
            IntegerBlock(length=1, programmatic_value=lambda ctx: ctx.data('resource_id')),
            {
                'description': 'Seems to always be equal to `resource_id`, except for one prop on map CL1, '
                'which is not used on map'
            },
        )
        unk0 = (FixedPointBlock(length=4, fraction_bits=16, value_validator=Eq(1.5)), {'is_unknown': True})
        unk1 = (
            FixedPointBlock(length=4, fraction_bits=16, programmatic_value=lambda _: 1.5),
            {
                'is_unknown': True,
                'description': 'The purpose is unknown. Every single entry in TNFS files equals to 1.5 '
                '(0x00_80_01_00) just like `unk0`, except for one prop on CL1, which has broken '
                'texture palette and which is not used on the map anyways',
            },
        )
        unk2 = (FixedPointBlock(length=4, fraction_bits=16, value_validator=Eq(3)), {'is_unknown': True})


class BitmapPropDescrData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Map prop settings if it is a bitmap'}

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (
            IntegerBlock(length=1),
            {
                'description': 'Represents texture id. How to get texture name from this value [explained]'
                '(http://www.math.polytechnique.fr/cmat/auroux/nfs/nfsspecs.txt) well '
                'by Denis Auroux'
            },
        )
        resource_id_2 = (
            IntegerBlock(length=1),
            {'description': 'Oftenly equals to `resource_id`, but can be different'},
        )
        width = (FixedPointBlock(length=4, fraction_bits=16, is_signed=True), {'description': 'Width in meters'})
        frame_count = (
            IntegerBlock(length=1),
            {'description': 'Frame amount for animated object. Ignored if flag `is_animated` not set'},
        )
        animation_interval = (Nfs1TimeField(length=1), {'description': 'Interval between animation frames in seconds'})
        unk0 = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        unk1 = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        height = (FixedPointBlock(length=4, fraction_bits=16, is_signed=True), {'description': 'Height in meters'})


class TwoSidedBitmapPropDescrData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Map prop settings if it is a two-sided bitmap (fake 3D model)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (
            IntegerBlock(length=1),
            {
                'description': 'Represents texture id. How to get texture name from this value [explained]'
                '(http://www.math.polytechnique.fr/cmat/auroux/nfs/nfsspecs.txt) well '
                'by Denis Auroux'
            },
        )
        resource_id_2 = (
            IntegerBlock(length=1),
            {
                'description': 'Texture id of second sprite, rotated 90 degrees. Logic to determine texture '
                'name is the same as for resource_id'
            },
        )
        width = (FixedPointBlock(length=4, fraction_bits=16, is_signed=True), {'description': 'Width in meters'})
        width_2 = (
            FixedPointBlock(length=4, fraction_bits=16, is_signed=True),
            {'description': 'Width in meters of second bitmap'},
        )
        height = (FixedPointBlock(length=4, fraction_bits=16, is_signed=True), {'description': 'Height in meters'})


class PropDescr(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'The description of map prop: everything except terrain (road signs, '
            'buildings etc.) Thanks to jeff-1amstudios and his [OpenNFS1](https://github.com'
            '/jeff-1amstudios/OpenNFS1/blob/357fe6c3314a6f5bae47e243ca553c5491ecde79/OpenNFS1'
            '/Parsers/TriFile.cs#L202) project',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        flags = (BitFlagsBlock(length=1, flag_names=[(2, 'is_animated')]), {'description': 'Different modes of prop'})
        type = (
            EnumByteBlock(enum_names=[(1, 'model'), (4, 'bitmap'), (6, 'two_sided_bitmap')]),
            {'description': 'Type of prop'},
        )
        data = (
            EnumLookupDelegateBlock(
                enum_field='type',
                blocks=[
                    ModelPropDescrData(),
                    BitmapPropDescrData(),
                    TwoSidedBitmapPropDescrData(),
                    BytesBlock(length=14),
                ],
            ),
            {'description': 'Settings of the prop. Block class picked according to `type`'},
        )


class MapProp(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'The prop on the map. For instance: exactly the same road sign used 5 '
            'times on the map. In this case file will have 1 PropDescr for this road sign '
            'and 5 MapProps. The game engine refers to a prop (road object) by its index in the TRI `props` array: '
            '`SignStatus` has 2 bytes per object, nonzero once a car knocked it down',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        road_point_idx = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Index of point of the road path spline, where prop is located. Sometimes '
                'has too big value, I skip those instances for now and it seems to look good.'
                ' Probably should consider this value to be 16-bit integer, having some '
                'unknown 16-integer as next field. Also, why it is '
                'signed?'
            },
        )
        prop_descr_idx = (
            IntegerBlock(length=1),
            {
                'description': 'Index of prop description, which should be used for this prop. '
                'Sometimes has too big value, I use object index % amount of prop '
                'descriptions for now and it seems to look good'
            },
        )
        rotation = (
            Nfs1Angle8(),
            {
                'description': 'Y-rotation, relative to rotation of referenced road spline vertex. A bitmap or '
                'two-sided bitmap prop knocked down is drawn lying flat, falling to the other side when the raw byte '
                'is > 64 (DOS tnfs_render_terrain_vertex_list 0x627f3, Win95 SE 0x43eea5). 3D model props are never '
                'drawn knocked down'
            },
        )
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        position = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True)),
            {
                'description': 'Position in 3D space, relative to position of referenced road spline vertex. '
                'The unit is meter'
            },
        )


class TerrainEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'The terrain model around 4 spline points. It has good explanation in original '
            '[Denis Auroux NFS file specs](http://www.math.polytechnique.fr/cmat/auroux/nfs/'
            'nfsspecs.txt)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('TRKD')), {'description': 'Resource ID'})
        block_length = (IntegerBlock(length=4, is_signed=False), {'description': 'Block length in bytes'})
        block_number = (
            IntegerBlock(length=4, is_signed=False, value_validator=Eq(0)),
            {'description': 'Block number, always 0'},
        )
        unknown = (IntegerBlock(length=1, value_validator=Eq(0)), {'is_unknown': True})
        fence = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (1, 'has_left_fence', 'boolean', [], 'Fence on the left side (A6..A10)'),
                    (1, 'has_right_fence', 'boolean', [], 'Fence on the right side (A1..A5)'),
                    (1, 'is_low', 'boolean', [], 'Low fence: 0.9 m high instead of 2 m'),
                    (5, 'texture_id', 'number', [], 'Fence texture id - 32'),
                ],
            ),
            {
                'description': 'Fence of this chunk, as the game draws it (`tnfs_render_track_fence`: Win95 SE 0x44a2b4, '
                'DOS 0x69719, PSX 0x80046484). It is the only thing that decides fence drawing: the road spline '
                "points' `fence_flag` is for collisions. One vertical quad per node to the next node (the last one to "
                "the next chunk's first node) on each side with a flag, from terrain vertices up by 2 m, or by 0.9 m "
                '(0xe666 in 16.16) for a low fence. The bottom vertex is picked by the `item_mode` of the '
                "chunk's first node: the right fence stands on A2; the left one on A7 for item modes 3, 4, 5, 6, 8, "
                '10 and 11, on A8 for 1 and 14..18, on A7 at the first node and A8 after it for 0 (lane split), on A8 '
                "and at the next chunk's first node on A7 for 2 (lane merge). Tunnel modes 7, 9, 12 and 13 draw no "
                'fence near the camera (SE draws A2 / A8 at mid and far distance only). The texture id is '
                '`texture_id` + 32 (same id space as `texture_ids`; on closed tracks the ids of '
                '`fence_texture_id` // 3 are replaced by the `ga00` / `ga10` / `ga20` bitmaps); SE draws no fence '
                "when the track's FAM has no bitmap for it (TR4's 0xb7 chunks, id 55 = `18B0`). The fence maps the "
                'texture like the road polygon of its node: half the texture width per node, full height'
            },
        )
        texture_ids = (
            ArrayBlock(child=IntegerBlock(length=1), length=10),
            {'description': 'Texture ids to be used for terrain'},
        )
        rows = (
            ArrayBlock(
                child=ArrayBlock(
                    child=Point3D(child=FixedPointBlock(length=2, fraction_bits=7, is_signed=True)), length=11
                ),
                length=4,
            ),
            {'description': 'Terrain vertex positions. The unit is meter'},
        )


class AIEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'The record describing AI behavior at given terrain chunk'}

    class Fields(DeclarativeCompoundBlock.Fields):
        top_speed = (IntegerBlock(length=1), {'description': 'Max speed among all AI drivers in m/s'})
        legal_speed = (IntegerBlock(length=1), {'description': 'Minimum speed in m/s that makes cops start pursuit'})
        safe_speed = (
            IntegerBlock(length=1),
            {'description': 'Max traffic speed in m/s. Oncoming traffic does not obey it'},
        )


class TriMap(DeclarativeCompoundBlock, SpatialEditable):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'custom_actions': [
                {
                    'method': 'reverse_track',
                    'title': 'Reverse track',
                    'description': 'Makes this track to go backwards',
                    'is_pure': False,
                    'args': [],
                },
                {
                    'method': 'flatten_track',
                    'title': 'Flatten track',
                    'description': 'Makes track super flat: going forward without turns, slopes and slants',
                    'is_pure': False,
                    'args': [],
                },
                {
                    'method': 'scale_track',
                    'title': 'Scale track length',
                    'description': 'Makes track shorter or longer by scaling it. Does not affect objects and terrain size',
                    'is_pure': False,
                    'args': [{'id': 'scale', 'title': 'Scale', 'type': 'number'}],
                },
            ],
            'spatial_edit': [
                {
                    'kind': 'prop',
                    'title': 'Props',
                    'description': 'Move props and turn them around the vertical axis. A prop is stored relative to '
                    'a road point (8.8 fixed point offset, 8-bit angle relative to the road heading): it is '
                    're-anchored to the road point nearest to it',
                    'translate_axes': 'xyz',
                    'rotate_axes': 'z',
                    'pick_entities': True,
                },
                {
                    'kind': 'terrain_vertex',
                    'title': 'Terrain',
                    'description': 'Move terrain vertices. Each one is stored relative to the previous one of its '
                    'row (9.7 fixed point), so the next vertices keep their places',
                    'translate_axes': 'xyz',
                    'rotate_axes': '',
                    'deforms_mesh': True,
                },
                {
                    'kind': 'road_point',
                    'title': 'Road',
                    'description': 'Move road spline points. The terrain row and the props of the point move with '
                    'it; the heading, slope and side normal of the point and of the previous one are recomputed',
                    'translate_axes': 'xyz',
                    'rotate_axes': '',
                },
            ],
            'block_description': 'Map TRI file, represents terrain mesh, road itself, props locations etc.',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (IntegerBlock(length=4, value_validator=Eq(0x11)), {'description': 'Resource ID'})
        loop_chunk = (
            IntegerBlock(length=2),
            {
                'description': 'Index of chunk, on which game should use chunk #0 again. So for closed tracks '
                'this value should be equal to `num_chunks`, for open tracks it is 0'
            },
        )
        num_chunks = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('terrain'))),
            {'description': 'number of terrain chunks (max 600)'},
        )
        unk0 = (IntegerBlock(length=2, value_validator=Eq(6)), {'is_unknown': True})
        position = (Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)), {'is_unknown': True})
        unknowns0 = (ArrayBlock(child=IntegerBlock(length=1, value_validator=Eq(0)), length=12), {'is_unknown': True})
        chunks_size = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('terrain')) * 0x120),
            {'description': 'Size of terrain array in bytes (num_chunks * 0x120)'},
        )
        fence_texture_id = (
            IntegerBlock(length=4),
            {
                'description': "The texture id of the track's fence (`fence.texture_id` + 32 of the terrain chunks "
                'with a fence, or of most of them). The texture loader (Win95 SE `tnfs_render_load_track_textures` '
                '0x44c36c, reading the low 16 bits) uses it on closed tracks only: it gives the ids '
                '(value // 3) * 3 + 0, 1 and 2 the FAM bitmaps `ga00`, `ga10` and `ga20` instead of `%02d%c0`'
            },
        )
        lookup_table = (
            ArrayBlock(child=IntegerBlock(length=4), length=600),
            {
                'description': '600 consequent numbers, each value is previous + 288. Looks like a space '
                'needed by the original NFS engine'
            },
        )
        road_spline = (
            ArrayBlock(child=RoadSplinePoint(), length=2400),
            {
                'description': 'Road spline is a series of points in 3D space, located at the center of '
                'road. Around this spline the track terrain mesh is built. TRI always has '
                '2400 elements, however it uses only amount of vertices, equals to '
                '(num_chunks * 4), after them records filled with zeros. For opened '
                'tracks, finish line will be always located at spline point '
                '(num_chunks * 4 - 179)'
            },
        )
        ai_info = (
            ArrayBlock(child=AIEntry(), length=600),
            {
                'description': 'AI behaviour settings per terrain chunk. Always has 600 items, only the first '
                '`num_chunks` are used'
            },
        )
        num_prop_descr = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('prop_descr'))),
            {'description': 'Amount of prop descriptions'},
        )
        num_props = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('props'))),
            {'description': 'Amount of props'},
        )
        objs_hdr = (UTF8Block(length=4, value_validator=Eq('SJBO')), {'description': 'Header of the props section'})
        unk1 = (IntegerBlock(length=4, value_validator=Eq(0x428C)), {'is_unknown': True})
        unk2 = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True})
        prop_descr = (
            ArrayBlock(child=PropDescr(), length=lambda ctx: ctx.data('num_prop_descr')),
            {
                'description': 'Prop descriptions: 3D models, bitmaps and two-sided bitmaps, which can be '
                'placed on the map'
            },
        )
        props = (
            ArrayBlock(child=MapProp(), length=lambda ctx: ctx.data('num_props')),
            {
                'description': 'Props placed on the map. Unused trailing items have `road_point_idx` == -1. The '
                'game engine refers to props (road objects) by their index in this array: `SignStatus` has 2 bytes '
                'per object, nonzero once a car knocked it down'
            },
        )
        terrain = (
            ArrayBlock(child=TerrainEntry(), length=lambda ctx: ctx.data('num_chunks')),
            {'description': 'Terrain chunks, one per 4 road spline points'},
        )

    def serializer_class(self):
        from serializers import TriMapSerializer

        return TriMapSerializer

    def action_reverse_track(self, read_data, **kwargs):
        # FIXME lanes are a bit off: CY1.TRI now has both lanes oncoming, and racers drive on right verge. Traffic never appears
        # FIXME lane merge/split are broken. Is it possible to fix?
        # FIXME tunnel walls are broken. Is it possible to fix?
        # FIXME preserve 3D effect from two sided bitmaps (add math.pi to rotation, move base, switch side of side bitmap)
        # FIXME render order of props
        from math import cos, sin, pi, atan2

        def rotate_point(origin, point, angle):
            ox, oy = origin
            px, py = point
            qx = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
            qy = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)
            return qx, qy

        road_spline_length = len(read_data['terrain']) * 4
        # start happens at 18th road spline vertex
        new_start_position = read_data['road_spline'][road_spline_length - 19]['position']
        new_start_next_position = read_data['road_spline'][road_spline_length - 20]['position']
        # Y - up; X - left; Z - forward;
        y_angle_to_rotate = pi - atan2(
            new_start_position['x'] - new_start_next_position['x'],
            new_start_position['z'] - new_start_next_position['z'],
        )

        lane_effects = []
        start_x_road_offset = read_data['road_spline'][18]['position']['x']
        for i, vertex in enumerate(read_data['road_spline'][:road_spline_length]):
            # rotate so road at new start goes forward
            vertex['position']['z'], vertex['position']['x'] = rotate_point(
                (0, 0), (vertex['position']['z'], vertex['position']['x']), y_angle_to_rotate
            )

        # translate so new start ==
        # -old_start.x (aligning car position for tracks, where road spline located at the side, like CY1)
        # 0,
        # 6.25 * 18 (average value for start position on original tracks)
        position_offset = [
            read_data['road_spline'][road_spline_length - 19]['position']['x'] + start_x_road_offset,
            read_data['road_spline'][road_spline_length - 19]['position']['y'],
            read_data['road_spline'][road_spline_length - 19]['position']['z'] - 6.25 * 18,
        ]
        for i, vertex in enumerate(read_data['road_spline'][:road_spline_length]):
            vertex['position']['x'] -= position_offset[0]
            vertex['position']['y'] -= position_offset[1]
            vertex['position']['z'] -= position_offset[2]
            # swap left and right
            (vertex['left_verge'], vertex['right_verge']) = (vertex['right_verge'], vertex['left_verge'])
            (vertex['left_barrier'], vertex['right_barrier']) = (vertex['right_barrier'], vertex['left_barrier'])
            # swap lanes
            vertex['num_lanes'] = [vertex['num_lanes'][1], vertex['num_lanes'][0]]
            vertex['fence_flag'] = [vertex['fence_flag'][1], vertex['fence_flag'][0]]
            vertex['shoulder_surface_type'] = [vertex['shoulder_surface_type'][1], vertex['shoulder_surface_type'][0]]
            if vertex['police_spot']['is_spot']:
                vertex['police_spot']['is_left'] = not vertex['police_spot']['is_left']
            # change sign of slope/slant values
            vertex['slope'] = -vertex['slope']
            vertex['slant'] = -vertex['slant']
            vertex['side_normal']['y'] = -vertex['side_normal']['y']

            if vertex['item_mode'] == 'lane_split':
                vertex['item_mode'] = 'lane_merge'
                lane_effects.append(i)
            elif vertex['item_mode'] == 'lane_merge':
                vertex['item_mode'] = 'lane_split'
                # lane_effects.append(i)
            elif vertex['item_mode'] == 'waterfall_audio_left_channel':
                vertex['item_mode'] = 'waterfall_audio_right_channel'
            elif vertex['item_mode'] == 'waterfall_audio_right_channel':
                vertex['item_mode'] = 'waterfall_audio_left_channel'

        for index in lane_effects:
            (read_data['road_spline'][index]['item_mode'], read_data['road_spline'][index - 1]['item_mode']) = (
                read_data['road_spline'][index - 1]['item_mode'],
                read_data['road_spline'][index]['item_mode'],
            )

        for chunk in read_data['terrain']:
            (chunk['fence']['has_left_fence'], chunk['fence']['has_right_fence']) = (
                chunk['fence']['has_right_fence'],
                chunk['fence']['has_left_fence'],
            )
            chunk['texture_ids'] = chunk['texture_ids'][5:] + chunk['texture_ids'][:5]
            chunk['rows'] = chunk['rows'][::-1]
            for i in range(4):
                chunk['rows'][i] = [chunk['rows'][i][0]] + chunk['rows'][i][6:] + chunk['rows'][i][1:6]
                for j in range(11):
                    chunk['rows'][i][j]['z'], chunk['rows'][i][j]['x'] = rotate_point(
                        (0, 0), (chunk['rows'][i][j]['z'], chunk['rows'][i][j]['x']), y_angle_to_rotate
                    )

        amount_of_instances = [x['road_point_idx'] for x in read_data['props']].index(-1)
        for prop in read_data['props'][:amount_of_instances]:
            prop['road_point_idx'] = road_spline_length - 1 - prop['road_point_idx']
            prop['rotation'] += pi
            prop['position']['z'], prop['position']['x'] = rotate_point(
                (0, 0), (prop['position']['z'], prop['position']['x']), y_angle_to_rotate
            )

        read_data['road_spline'] = (
            read_data['road_spline'][:road_spline_length][::-1] + read_data['road_spline'][road_spline_length:]
        )
        read_data['ai_info'] = (
            read_data['ai_info'][: read_data['num_chunks']][::-1] + read_data['ai_info'][read_data['num_chunks'] :]
        )
        read_data['terrain'] = read_data['terrain'][::-1]
        read_data['props'] = read_data['props'][:amount_of_instances][::-1] + read_data['props'][amount_of_instances:]
        # update rotations
        v_block = RoadSplinePoint()
        for i, vertex in enumerate(read_data['road_spline'][:road_spline_length]):
            v_block.update_orientations(vertex, read_data['road_spline'][i + 1 if i < road_spline_length else 0])

    def action_flatten_track(self, read_data, **kwargs):
        from math import cos, sin, pi

        for i, terrain_chunk in enumerate(read_data['terrain']):
            for j in range(4):
                terrain_chunk['rows'][j][0]['y'] = 0.0
                # rotate terrain mesh around first point
                angle = read_data['road_spline'][i * 4 + j]['orientation']
                cosine = cos(angle)
                sine = sin(angle)
                for k in range(1, 11):
                    terrain_chunk['rows'][j][k]['x'] -= terrain_chunk['rows'][j][0]['x']
                    terrain_chunk['rows'][j][k]['z'] -= terrain_chunk['rows'][j][0]['z']
                    x_new = terrain_chunk['rows'][j][k]['x'] * cosine - terrain_chunk['rows'][j][k]['z'] * sine
                    z_new = terrain_chunk['rows'][j][k]['x'] * sine + terrain_chunk['rows'][j][k]['z'] * cosine
                    terrain_chunk['rows'][j][k]['x'] = x_new + terrain_chunk['rows'][j][0]['x']
                    terrain_chunk['rows'][j][k]['z'] = z_new + terrain_chunk['rows'][j][0]['z']
        # fix props
        for prop in read_data['props']:
            road_vertex = read_data['road_spline'][prop['road_point_idx']]
            prop['rotation'] -= road_vertex['orientation']
            if prop['rotation'] < 0:
                prop['rotation'] += 2 * pi
            sine, cosine = sin(road_vertex['orientation']), cos(road_vertex['orientation'])
            prop['position']['x'], prop['position']['z'] = (
                prop['position']['x'] * cosine - prop['position']['z'] * sine,
                prop['position']['x'] * sine + prop['position']['z'] * cosine,
            )

        for i, road_vertex in enumerate(read_data['road_spline'][: len(read_data['terrain']) * 4]):
            road_vertex['position']['x'] = road_vertex['position']['y'] = 0
            road_vertex['position']['z'] = i * 6.25
            road_vertex['slope'] = 0
            road_vertex['slant'] = 0
            road_vertex['side_normal']['y'] = 0
        # update rotations
        v_block = RoadSplinePoint()
        for i, vertex in enumerate(read_data['road_spline'][: len(read_data['terrain']) * 4]):
            v_block.update_orientations(
                vertex, read_data['road_spline'][i + 1 if i < len(read_data['terrain']) * 4 else 0]
            )

    def action_scale_track(self, read_data, scale: float, **kwargs):
        scale = float(scale)
        for i, vertex in enumerate(read_data['road_spline']):
            vertex['position']['x'] *= scale
            vertex['position']['y'] *= scale
            vertex['position']['z'] *= scale

    # Spatial edits (library/spatial_edit.py). Export space = the game's axes with y and z swapped, as the
    # TriMapSerializer writes the chunks: [x, z, y]

    @staticmethod
    def _to_export(p: Dict) -> List[float]:
        return [p['x'], p['z'], p['y']]

    @staticmethod
    def _from_export(v: List[float]) -> Dict:
        return {'x': float(v[0]), 'y': float(v[2]), 'z': float(v[1])}

    @staticmethod
    def _road_length(read_data) -> int:
        return len(read_data['terrain']) * 4

    def _field_block(self, *path):
        block = self
        for key in path:
            block = block.child if key == '*' else block.field_blocks_map[key]
        return block

    def spatial_handles(self, read_data, kind: str, chunks: Optional[List[int]] = None) -> List[Dict]:
        chunk_set = None if chunks is None else set(chunks)
        in_chunks = lambda chunk: chunk_set is None or chunk in chunk_set
        if kind == 'prop':
            return [
                self.spatial_handle(read_data, kind, str(k))
                for k, prop in enumerate(read_data['props'])
                if 0 <= prop['road_point_idx'] < self._road_length(read_data) and in_chunks(prop['road_point_idx'] // 4)
            ]
        if kind == 'terrain_vertex':
            return [
                self.spatial_handle(read_data, kind, f'{i}/{row}/{column}')
                for i in range(len(read_data['terrain']))
                if in_chunks(i)
                for row in range(4)
                for column in range(11)
            ]
        if kind == 'road_point':
            return [
                self.spatial_handle(read_data, kind, str(n))
                for n in range(self._road_length(read_data))
                if in_chunks(n // 4)
            ]
        raise ValueError(f'Unknown spatial edit kind {kind}')

    def spatial_handle(self, read_data, kind: str, handle_id: str) -> Dict:
        if kind == 'prop':
            k = int(handle_id)
            prop = read_data['props'][k]
            point = read_data['road_spline'][prop['road_point_idx']]
            yaw = -(prop['rotation'] + point['orientation'])
            descr = read_data['prop_descr'][prop['prop_descr_idx'] % len(read_data['prop_descr'])]
            return {
                'id': handle_id,
                'chunk': prop['road_point_idx'] // 4,
                'position': [
                    a + b for a, b in zip(self._to_export(point['position']), self._to_export(prop['position']))
                ],
                'rotation': [0.0, 0.0, sin(yaw / 2), cos(yaw / 2)],
                'label': f'Prop #{k} ({descr["type"].replace("_", " ")}, description {prop["prop_descr_idx"]})',
                'data_path': f'props/{k}',
                'match': {'object_index': k},
            }
        if kind == 'terrain_vertex':
            i, row, column = (int(x) for x in handle_id.split('/'))
            vertices = self._terrain_row_vertices(read_data, i, row)
            side = 'center' if column == 0 else ('right' if column <= 5 else 'left')
            return {
                'id': handle_id,
                'chunk': i,
                'position': self._to_export(vertices[column]),
                'rotation': None,
                'label': f'Terrain chunk {i}, road point {i * 4 + row}, vertex A{column} ({side})',
                'data_path': f'terrain/{i}/rows/{row}/{column}',
            }
        if kind == 'road_point':
            n = int(handle_id)
            return {
                'id': handle_id,
                'chunk': n // 4,
                'position': self._to_export(read_data['road_spline'][n]['position']),
                'rotation': None,
                'label': f'Road point {n} (terrain chunk {n // 4})',
                'data_path': f'road_spline/{n}',
            }
        raise ValueError(f'Unknown spatial edit kind {kind}')

    @staticmethod
    def _terrain_chain_previous(column: int) -> Optional[int]:
        """Stored terrain row vertices are offsets: A0 from the road point, A1 and A6 from A0, A2..A5 and A7..A10
        from the previous one. None = the road point"""
        if column == 0:
            return None
        return 0 if column in (1, 6) else column - 1

    @staticmethod
    def _terrain_chain_next(column: int) -> List[int]:
        if column == 0:
            return [1, 6]
        return [] if column in (5, 10) else [column + 1]

    def _terrain_row_vertices(self, read_data, chunk: int, row: int) -> List[Dict]:
        """Absolute positions (game axes) of the 11 vertices of a terrain row, in stored order A0, A1..A5, A6..A10"""
        offsets = read_data['terrain'][chunk]['rows'][row]
        base = read_data['road_spline'][chunk * 4 + row]['position']
        vertices = [None] * 11
        for column in range(11):
            previous = self._terrain_chain_previous(column)
            origin = base if previous is None else vertices[previous]
            vertices[column] = {c: origin[c] + offsets[column][c] for c in 'xyz'}
        return vertices

    def _nearest_road_point(self, read_data, position: Dict) -> int:
        spline = read_data['road_spline'][: self._road_length(read_data)]
        return min(
            range(len(spline)),
            key=lambda n: sum((spline[n]['position'][c] - position[c]) ** 2 for c in 'xyz'),
        )

    def spatial_move(self, read_data, kind: str, handle_id: str, position, rotation) -> Dict:
        target = self._from_export(position)
        if kind == 'prop':
            k = int(handle_id)
            prop = read_data['props'][k]
            n = self._nearest_road_point(read_data, target)
            point = read_data['road_spline'][n]
            changes = {
                f'props/{k}/road_point_idx': n,
                f'props/{k}/position': stored_value(
                    self._field_block('props', '*', 'position'),
                    {c: target[c] - point['position'][c] for c in 'xyz'},
                ),
            }
            if rotation is not None:
                # heading of the rotated x axis around the vertical (export z) axis
                qx, qy, qz, qw = rotation
                yaw = atan2(2 * (qx * qy + qw * qz), 1 - 2 * (qy * qy + qz * qz))
                changes[f'props/{k}/rotation'] = stored_value(
                    self._field_block('props', '*', 'rotation'), -yaw - point['orientation']
                )
            else:
                # keep the heading in the world when the road point changes
                changes[f'props/{k}/rotation'] = stored_value(
                    self._field_block('props', '*', 'rotation'),
                    prop['rotation']
                    + read_data['road_spline'][prop['road_point_idx']]['orientation']
                    - point['orientation'],
                )
            return changes
        if kind == 'terrain_vertex':
            i, row, column = (int(x) for x in handle_id.split('/'))
            vertices = self._terrain_row_vertices(read_data, i, row)
            point_block = self._field_block('terrain', '*', 'rows', '*', '*')
            previous = self._terrain_chain_previous(column)
            origin = read_data['road_spline'][i * 4 + row]['position'] if previous is None else vertices[previous]
            offset = stored_value(point_block, {c: target[c] - origin[c] for c in 'xyz'})
            moved = {c: origin[c] + offset[c] for c in 'xyz'}
            changes = {f'terrain/{i}/rows/{row}/{column}': offset}
            # the next vertices of the chain stay where they are
            for next_column in self._terrain_chain_next(column):
                changes[f'terrain/{i}/rows/{row}/{next_column}'] = stored_value(
                    point_block, {c: vertices[next_column][c] - moved[c] for c in 'xyz'}
                )
            return changes
        if kind == 'road_point':
            n = int(handle_id)
            spline = read_data['road_spline']
            length = self._road_length(read_data)
            is_closed = read_data['loop_chunk'] != 0
            new_position = stored_value(self._field_block('road_spline', '*', 'position'), target)
            if new_position == spline[n]['position']:
                # the game's angles differ a bit from recomputed ones: leave them when nothing moved
                return {}
            positions = {n: new_position}
            changes = {f'road_spline/{n}/position': new_position}
            # heading, slope and side normal of a point look at the next point
            for m in (n - 1, n):
                if m < 0 and not is_closed:
                    continue
                m %= length
                next_m = m + 1
                if next_m >= length:
                    if not is_closed:
                        continue
                    next_m = 0
                a = positions.get(m, spline[m]['position'])
                b = positions.get(next_m, spline[next_m]['position'])
                dx, dy, dz = (b[c] - a[c] for c in 'xyz')
                orientation = atan2(dx, dz)
                changes[f'road_spline/{m}/orientation'] = stored_value(
                    self._field_block('road_spline', '*', 'orientation'), orientation
                )
                changes[f'road_spline/{m}/slope'] = stored_value(
                    self._field_block('road_spline', '*', 'slope'), atan2(dy, hypot(dx, dz))
                )
                changes[f'road_spline/{m}/side_normal'] = stored_value(
                    self._field_block('road_spline', '*', 'side_normal'),
                    RoadSplinePoint.side_normal_for(orientation, spline[m]['side_normal']['y']),
                )
            return changes
        raise ValueError(f'Unknown spatial edit kind {kind}')

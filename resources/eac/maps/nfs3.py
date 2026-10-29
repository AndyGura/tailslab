from typing import Dict

from library.read_blocks import (
    DeclarativeCompoundBlock,
    IntegerBlock,
    BytesBlock,
    ArrayBlock,
    EnumByteBlock,
    DelegateBlock,
    LengthPrefixedArrayBlock,
    DecimalBlock,
    FixedPointBlock,
    OptionalBlock,
    SubByteCompoundBlock,
)
from library.read_blocks.misc.value_validators import Eq
from resources.eac.fields.misc import Point3D, Quaternion


def _resize_bytes(value: bytes, length: int) -> bytes:
    return (value + bytes(max(length - len(value), 0)))[:length]


class FrdPositionBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A track slice: the row of consecutive high-res track polygons (chunk 4) across '
            'the road at one slice, one COL collision_data record each ([Nfs3CollisionExtraDataRecord]'
            '(#nfs3collisionextradatarecord), the same index among all blocks of the track). A track block usually '
            'has 8 of them, together covering all polygons of the high-res track chunk',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        polygon = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Index of the first polygon of this group in the high-res track polygon chunk '
                '(`polygons[4]` of the corresponding [FrdPolyBlock](#frdpolyblock))'
            },
        )
        num_polygons = (IntegerBlock(length=1, is_signed=False), {'description': 'Amount of polygons in this group'})
        unk = (
            IntegerBlock(length=1, is_signed=False),
            {'description': '4..9 in the NFS3 tracks', 'is_unknown': True},
        )
        alt_slice_1 = (
            IntegerBlock(length=2, is_signed=True),
            {
                'description': 'A slice of an alternative route (track fork), -1 (0xFFFF) when none. nfs3.exe '
                'searches the fork from them (0x41f330)'
            },
        )
        alt_slice_2 = (
            IntegerBlock(length=2, is_signed=True),
            {'description': 'A slice of another alternative route, -1 when none, used like `alt_slice_1`'},
        )


class FrdBlockPolygonData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Per-polygon data of the high-res track polygons: one record per polygon of '
            '`polygons[4]` chunk of the corresponding [FrdPolyBlock](#frdpolyblock)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        vroad_idx = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Index of entry in `vroad` array of the block: orientation of the road surface '
                'at this polygon'
            },
        )
        flags = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (1, 'barriers', 'boolean', [], 'The barrier / wall check runs on this polygon (nfs3.exe 0x4304b0)'),
                    (1, 'objects', 'boolean', [], 'Track objects on this polygon are tested (0x4311d0)'),
                    (
                        6,
                        'surface',
                        'number',
                        [],
                        'Road surface type, the index in the grip table (0x55ed30). Polygons whose low 4 bits are '
                        '0xe are never found by the road search (0x41e990)',
                    ),
                ],
            ),
            {
                'description': 'Road surface byte: bits 0x3f `surface` the surface type, the index in the grip table '
                '(nfs3.exe 0x55ed30); bit 0x40 `objects`: objects on this polygon are tested (0x4311d0); bit 0x80 '
                '`barriers`: the barrier / wall check (0x4304b0). The road search (0x41e990) never finds a polygon '
                'with flags & 0xf == 0xe'
            },
        )
        unk = (BytesBlock(length=6), {'is_unknown': True})


class FrdBlockVroadData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Virtual road entry: orientation of the road surface, referenced by index from '
            '`polygons[].vroad_idx` of the block',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        normal = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True)),
            {'description': 'A normal vector of the surface, unit length (or zero)'},
        )
        forward = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True)),
            {'description': 'A forward vector of the surface, unit length (or zero)'},
        )


class FrdXobjRef(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Reference to an extra object (XOBJ) placed in the block. Animated extra objects '
            'are not always listed',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Position of the object, equals to its reference point (`pt_ref`)'},
        )
        radius = (
            FixedPointBlock(length=2, fraction_bits=8, is_signed=True),
            {
                'description': 'Collision radius in meters, unit 1/256 m (nfs3.exe reads it as a signed 16-bit value '
                '`<< 8`, 16.16), halved for `type` 1 and doubled for `type` 2 (the low nibble of `type`; 0x41ff20). '
                'The object collision (0x41d350, 0x430da0) uses the result'
            },
        )
        global_no = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Sequence number of the object among all extra objects of the track: the index in '
                "the game's object state table (0x5dd230, 512 entries of 3 bytes: standing / knocked away)"
            },
        )
        unk1 = (IntegerBlock(length=2, is_signed=False), {'is_unknown': True})
        cross_index = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Index of the object in `polyobj` of the block (the first POLYOBJ chunk), 0 if '
                'the object is in another chunk'
            },
        )
        type = (
            EnumByteBlock(enum_names=[(1, 'solid'), (2, 'knockable'), (3, 'no_collision')]),
            {
                'description': 'Object type (nfs3.exe 0x41d350): knockable (2) is knocked away when the car hits it '
                'at round(abs(vx) + abs(vz)) >= 11 m/s and is a solid wall otherwise; 3: no collision response, '
                '0x41d350 returns 2 for it and the hit counts as a crash when the car speed is above 2; other '
                'values (1) are solid. The low nibble also scales `radius` (0x41ff20). The NFS3 tracks have 1, 2 and 3'
            },
        )


class FrdPolyObjRef(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Reference to an object of the first POLYOBJ chunk of the block '
            '(`polyobj[0]` of the corresponding [FrdPolyBlock](#frdpolyblock)), same order. '
            'Variable size: 16 bytes, or 20 for an extra object (XOBJ)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        size = (
            IntegerBlock(
                length=2,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Record size in bytes'},
        )
        type = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Object type: 1 - polygons of the block, 4 - extra object (XOBJ)'},
        )
        objno = (IntegerBlock(length=1, is_signed=False), {'description': 'Object number', 'is_unknown': True})
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Reference point of the object'},
        )
        xobj_idx = (
            OptionalBlock(
                child=IntegerBlock(length=4, is_signed=False),
                criteria=(lambda ctx: ctx.data('type') == 4, 'type == 4'),
            ),
            {
                'description': 'Index of the extra object in its chunk (`extraobject_blocks[4 * block_index]` of '
                'the track file)'
            },
        )


class FrdSoundSource(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A sound source placed in the block'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Position of the sound source'},
        )
        type = (IntegerBlock(length=4, is_signed=False), {'description': 'Sound type', 'is_unknown': True})


class FrdLightSource(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A light source placed in the block'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Position of the light source'},
        )
        type = (IntegerBlock(length=4, is_signed=False), {'description': 'Light type', 'is_unknown': True})


class FrdBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track block: a segment of the track. Contains terrain vertices with shading, '
            'road orientation data and references to objects placed in this segment. '
            'Polygons of the block are stored separately, in the [FrdPolyBlock](#frdpolyblock) '
            'with the same index',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Position of the block in the world: a point on the road at the block start. '
                'Positions of all blocks form the track path'
            },
        )
        bounds = (
            ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length=4),
            {'description': 'Block bounding rectangle'},
        )
        num_vertices = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Total amount of vertices'},
        )
        num_vertices_high = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'End of the vertices used by high-res terrain polygons. `vertices` are ordered: '
                'POLYOBJ object vertices (up to `num_vertices_obj`), terrain vertices of low-res, then '
                'medium-res, then high-res polygons (up to `num_vertices_low`, `num_vertices_med`, '
                '`num_vertices_high`), then vertices of the lanes polygons'
            },
        )
        num_vertices_low = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'End of the vertices used by low-res terrain polygons'},
        )
        num_vertices_med = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'End of the vertices used by medium-res terrain polygons'},
        )
        num_vertices_dup = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Equals to `num_vertices`'},
        )
        num_vertices_obj = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices used by POLYOBJ objects of the block, they go first in `vertices`'},
        )
        vertices = (
            ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length=lambda ctx: ctx.data('num_vertices')),
            {'description': 'Vertices. Coordinates are global (not relative to block position)'},
        )
        vertex_shading = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: ctx.data('num_vertices')),
            {'description': 'Per-vertex shading color, 32-bit ARGB (0xFFRRGGBB), one item per vertex'},
        )
        neighbour_data = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=False), length=2 * 0x12C),
            {
                'description': '300 pairs of 16-bit values: (neighbouring block index, unknown). '
                'Unused pairs have index 0xFFFF'
            },
        )
        num_start_pos = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Index of the first `positions` entry of this block among all blocks of the '
                'track (sum of `num_positions` of all previous blocks): its first slice, the index of its COL '
                'collision_data record'
            },
        )
        num_positions = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('positions'))),
            {'description': 'Amount of items in `positions`'},
        )
        num_polygons = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('polygons'))),
            {
                'description': 'Amount of items in `polygons`. Equals to the amount of high-res track '
                'polygons (`polygons[4]` chunk of the [FrdPolyBlock](#frdpolyblock))'
            },
        )
        num_vroad = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('vroad'))),
            {'description': 'Amount of items in `vroad`'},
        )
        num_xobj = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('xobj'))),
            {'description': 'Amount of items in `xobj`'},
        )
        num_polyobj = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('polyobj'))),
            {'description': 'Amount of items in `polyobj`'},
        )
        num_soundsrc = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('soundsrc'))),
            {'description': 'Amount of items in `soundsrc`'},
        )
        num_lightsrc = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('lightsrc'))),
            {'description': 'Amount of items in `lightsrc`'},
        )
        positions = (
            ArrayBlock(child=FrdPositionBlock(), length=lambda ctx: ctx.data('num_positions')),
            {'description': 'Groups of high-res track polygons ("rows" across the road)'},
        )
        polygons = (
            ArrayBlock(child=FrdBlockPolygonData(), length=lambda ctx: ctx.data('num_polygons')),
            {'description': 'Per-polygon data (road orientation reference + flags) for the high-res track polygons'},
        )
        vroad = (
            ArrayBlock(child=FrdBlockVroadData(), length=lambda ctx: ctx.data('num_vroad')),
            {'description': 'Virtual road: orientation vectors of the road surface, referenced from `polygons`'},
        )
        xobj = (
            ArrayBlock(child=FrdXobjRef(), length=lambda ctx: ctx.data('num_xobj')),
            {'description': 'References to extra objects (XOBJ) placed in this block'},
        )
        polyobj = (
            ArrayBlock(child=FrdPolyObjRef(), length=lambda ctx: ctx.data('num_polyobj')),
            {'description': 'References to the objects of the first POLYOBJ chunk of the block'},
        )
        polyobj_unused = (
            BytesBlock(
                length=(
                    lambda ctx: sum(4 for x in ctx.data('polyobj') if x['type'] != 4),
                    '4 * (amount of `polyobj` items with type != 4)',
                ),
                programmatic_value=lambda ctx: _resize_bytes(
                    ctx.data('polyobj_unused'), sum(4 for x in ctx.data('polyobj') if x['type'] != 4)
                ),
            ),
            {
                'description': 'Unused space: `polyobj` area is 20 * `num_polyobj` bytes long, 16-byte records '
                'leave 4 bytes each at the end',
                'is_unknown': True,
            },
        )
        soundsrc = (
            ArrayBlock(child=FrdSoundSource(), length=lambda ctx: ctx.data('num_soundsrc')),
            {'description': 'Sound sources'},
        )
        lightsrc = (
            ArrayBlock(child=FrdLightSource(), length=lambda ctx: ctx.data('num_lightsrc')),
            {'description': 'Light sources'},
        )


class FrdPolygonRecord(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A single quad polygon of terrain or object'}

    class Fields(DeclarativeCompoundBlock.Fields):
        vertices = (
            ArrayBlock(child=IntegerBlock(length=2), length=4),
            {
                'description': 'Indexes of the 4 vertices in the vertex table of the enclosing track block '
                '(terrain polygons) or extra object (object polygons)'
            },
        )
        tex_id = (
            IntegerBlock(length=2),
            {
                'description': 'Index of entry in `texture_blocks` table of the track file, which defines the real '
                'texture index in the QFS archive and UV coordinates of polygon corners'
            },
        )
        tex_flags = (
            IntegerBlock(length=2),
            {
                'description': 'Texture flags. Zero for terrain polygons, non-zero only in the lanes chunk',
                'is_unknown': True,
            },
        )
        flags = (
            IntegerBlock(length=1),
            {'description': 'Usually 0, observed values 0x20, 0x30, 0x40', 'is_unknown': True},
        )
        unk = (IntegerBlock(length=1), {'description': 'Always 0xF9?', 'is_unknown': True})


class FrdPolygonsBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A chunk of terrain polygons of a track block'}

    class Fields(DeclarativeCompoundBlock.Fields):
        sz = (
            IntegerBlock(length=4),
            {'description': 'Amount of polygons in this chunk. 0 means the chunk is absent and no data follows'},
        )
        data = (
            DelegateBlock(
                possible_blocks=[
                    LengthPrefixedArrayBlock(length_block=IntegerBlock(length=4), child=FrdPolygonRecord()),
                    BytesBlock(length=0),
                ],
                choice_index=lambda ctx, **_: 0 if ctx.data('sz') != 0 else 1,
            ),
            {
                'description': 'Polygons. This data is presented only if sz != 0. The array length prefix '
                'duplicates `sz`'
            },
        )


class FrdPolyObjPolygonsBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Polygons of a single per-block object (POLYOBJ)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        type = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Object type: 1 - polygons follow; 4 - the object is an extra object (XOBJ), its '
                'geometry is stored in the corresponding chunk of `extraobject_blocks` and nothing '
                'follows here'
            },
        )
        data = (
            DelegateBlock(
                possible_blocks=[
                    LengthPrefixedArrayBlock(length_block=IntegerBlock(length=4), child=FrdPolygonRecord()),
                    BytesBlock(length=0),
                ],
                choice_index=lambda ctx, **_: 0 if ctx.data('type') == 1 else 1,
            ),
            {'description': 'Polygons of the object. This data is presented only if type == 1'},
        )


class FrdPolyObjBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A chunk of per-block objects (POLYOBJ)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        sz = (
            IntegerBlock(length=4),
            {
                'description': 'Total amount of polygons of all objects in this chunk. 0 means the chunk is absent and '
                'no data follows'
            },
        )
        data = (
            DelegateBlock(
                possible_blocks=[
                    LengthPrefixedArrayBlock(child=FrdPolyObjPolygonsBlock(), length_block=IntegerBlock(length=4)),
                    BytesBlock(length=0),
                ],
                choice_index=lambda ctx, **_: 0 if ctx.data('sz') > 0 else 1,
            ),
            {
                'description': 'Objects. This data is presented only if sz > 0. The array length prefix is the '
                'amount of objects, including the XOBJ references (type == 4)'
            },
        )


class FrdPolyBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Polygons of a track block (the [FrdBlock](#frdblock) with the same index): 7 '
            'chunks of terrain polygons + 4 chunks of per-block objects',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        polygons = (
            ArrayBlock(child=FrdPolygonsBlock(), length=7),
            {
                'description': 'Terrain polygon chunks: 0 - low-res track, 1 - low-res misc (non-track), '
                '2 - medium-res track, 3 - medium-res misc, 4 - high-res track, 5 - high-res misc, '
                '6 - lanes (helper polygons, not rendered). Low/medium/high-res chunks are '
                'alternative levels of detail of the same terrain (roughly 1/4, 1/2 and full '
                'amount of polygons)'
            },
        )
        polyobj = (
            ArrayBlock(child=FrdPolyObjBlock(), length=4),
            {
                'description': '4 chunks of per-block objects. Extra objects (XOBJ) referenced from chunk N are '
                'stored in `extraobject_blocks[4 * block_index + N]` of the track file'
            },
        )


class ExtraObjectDataCrossType4(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Extra data of a static extra object (cross_type == 4)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        pt_ref = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Reference point: position of the object in the world. Object vertices are relative to it'},
        )
        animation_size = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('animation'))),
            {
                'description': 'Size of `animation` in bytes. nfs3.exe reads every extra object as `pt_ref`, this '
                'size and that many bytes. 0 in every static object of the NFS3 tracks'
            },
        )
        animation = (
            BytesBlock(length=(lambda ctx: ctx.data('animation_size'), '`animation_size`')),
            {'description': 'Animation data, empty in every static object of the NFS3 tracks'},
        )


class AnimData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Animation keyframe of an extra object'}

    class Fields(DeclarativeCompoundBlock.Fields):
        pt = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Object position at this keyframe'},
        )
        orientation = (
            Quaternion(child=FixedPointBlock(length=2, fraction_bits=14, is_signed=True)),
            {
                'description': "Object orientation at this keyframe. Object vertices are rotated by it (v' = q v "
                'q^-1), then moved to `pt`'
            },
        )


class ExtraObjectDataCrossType3(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Extra data of an animated extra object (cross_type == 3)'}

    class Fields(DeclarativeCompoundBlock.Fields):
        pt_ref = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Reference point, read like the one of static objects (`pt_ref` of '
                '[ExtraObjectDataCrossType4](#extraobjectdatacrosstype4)). The animated objects of the NFS3 tracks '
                'hold no position here (six 16-bit values, or zeros), the keyframes place them',
                'is_unknown': True,
            },
        )
        animation_size = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: 8 + 20 * len(ctx.data('animdata'))),
            {
                'description': 'Size of the animation (the fields after this one) in bytes: 8 + 20 * `num_animdata`. '
                'nfs3.exe reads every extra object as `pt_ref`, this size and that many bytes'
            },
        )
        animation_size_2 = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: 8 + 20 * len(ctx.data('animdata'))),
            {
                'description': 'The animation header (like the NFS2 animated prop record) starts with its size '
                'again: equals `animation_size` in every animated object of the NFS3 tracks'
            },
        )
        type = (IntegerBlock(length=1, value_validator=Eq(3)), {'description': 'Animation type, always 3'})
        objno = (IntegerBlock(length=1), {'description': 'Object number', 'is_unknown': True})
        num_animdata = (
            IntegerBlock(length=2, programmatic_value=lambda ctx: len(ctx.data('animdata'))),
            {'description': 'Amount of keyframes'},
        )
        anim_delay = (
            IntegerBlock(length=2),
            {
                'description': 'Delay between keyframes (animation speed). Unit is not confirmed, the converter '
                'assumes 1/64 of a second'
            },
        )
        animdata = (
            ArrayBlock(child=AnimData(), length=lambda ctx: ctx.data('num_animdata')),
            {
                'description': 'Animation keyframes, played in a loop. Object vertices are relative to the position '
                'and orientation of the current keyframe'
            },
        )


class ExtraObjectBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Extra object (XOBJ): a standalone mesh placed on the track, e.g. a billboard, '
            'a building or an animated object',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        cross_type = (IntegerBlock(length=4), {'description': 'Object type: 4 - static object, 3 - animated object'})
        cross_no = (IntegerBlock(length=4), {'description': 'Object number', 'is_unknown': True})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        data = (
            DelegateBlock(
                possible_blocks=[ExtraObjectDataCrossType4(), ExtraObjectDataCrossType3()],
                choice_index=lambda ctx, **_: 0 if ctx.data('cross_type') == 4 else 1,
            ),
            {'description': 'Type-specific data (position or animation), block class picked according to `cross_type`'},
        )
        num_vertices = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Amount of vertices'},
        )
        vertices = (
            ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length=lambda ctx: ctx.data('num_vertices')),
            {
                'description': 'Vertices, relative to the object position (reference point for static objects, '
                'current keyframe for animated ones)'
            },
        )
        vertex_shading = (
            ArrayBlock(child=IntegerBlock(length=4), length=lambda ctx: ctx.data('num_vertices')),
            {'description': 'Per-vertex shading color, 32-bit ARGB (0xFFRRGGBB), one item per vertex'},
        )
        polygons = (
            LengthPrefixedArrayBlock(length_block=IntegerBlock(length=4), child=FrdPolygonRecord()),
            {'description': 'Polygons of the object. Vertex indexes point to `vertices` of this object'},
        )


class TextureBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Texture reference. Polygons refer to items of this table by `tex_id`, the item '
            'defines the actual texture in the QFS archive and UV coordinates of the polygon '
            'corners',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        width = (IntegerBlock(length=2, is_signed=False), {'description': 'Texture width'})
        height = (IntegerBlock(length=2, is_signed=False), {'description': 'Texture height'})
        unk0 = (
            IntegerBlock(length=4),
            {'description': 'Blending related, hometown covered bridges godrays', 'is_unknown': True},
        )
        corners = (
            ArrayBlock(child=DecimalBlock(length=4), length=8),
            {
                'description': 'UV coordinates of the 4 polygon corners (u0, v0, u1, v1, u2, v2, u3, v3), '
                'in the same order as polygon vertices'
            },
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})
        is_lane = (
            EnumByteBlock(
                enum_names=[
                    (0, 'default'),
                    (1, 'lane'),
                ]
            ),
            {'description': '1 if not a real texture (lane), 0 usually', 'is_unknown': True},
        )
        texture_id = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Index of the texture in the track QFS archive (<track>0.QFS)'},
        )


class FrdMap(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Main track file. The track is split into blocks (segments). Each block has its '
            'own vertex table ([FrdBlock](#frdblock)) and polygons at 3 levels of detail '
            '([FrdPolyBlock](#frdpolyblock)). Standalone objects (billboards, animated '
            'objects) are stored as extra objects. Polygon textures are referenced through '
            'the `texture_blocks` table, which points to images in <track>0.QFS',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk = (BytesBlock(length=28), {'description': 'Unknown header', 'is_unknown': True})
        num_blocks = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('blocks')) - 1),
            {'description': 'Number of blocks. Block arrays below have `num_blocks + 1` items'},
        )
        blocks = (
            ArrayBlock(child=FrdBlock(), length=lambda ctx: ctx.data('num_blocks') + 1),
            {'description': 'Track blocks: vertices, road data and object references of each track segment'},
        )
        polygon_blocks = (
            ArrayBlock(child=FrdPolyBlock(), length=lambda ctx: ctx.data('num_blocks') + 1),
            {'description': 'Polygons of the track blocks, same index as in `blocks`'},
        )
        extraobject_blocks = (
            ArrayBlock(
                child=LengthPrefixedArrayBlock(child=ExtraObjectBlock(), length_block=IntegerBlock(length=4)),
                length=lambda ctx: 4 * (ctx.data('num_blocks') + 1) + 1,
            ),
            {
                'description': 'Chunks of extra objects (XOBJ): 4 chunks per track block (matching '
                'the 4 `polyobj` chunks of the block), followed by one global chunk with '
                'objects not attached to any block. Each chunk is prefixed with the '
                'amount of objects in it'
            },
        )
        texture_blocks = (
            LengthPrefixedArrayBlock(child=TextureBlock(), length_block=IntegerBlock(length=4)),
            {
                'description': 'Texture references table, used by all polygons of the track. Texture '
                'images are in <track>0.QFS'
            },
        )

    def serializer_class(self):
        from serializers import FrdMapSerializer

        return FrdMapSerializer


class Nfs3SimHeights(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Ceiling heights of the track slices (GameData/Tracks/TRK<nnn>/SIMHTS.DAT, loaded '
            'by nfs3.exe 0x41e2f0): one float per COL collision_data record ([Nfs3CollisionExtraDataRecord]'
            '(#nfs3collisionextradatarecord)), the file is 4 bytes per slice in every NFS3 track',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        heights = (
            ArrayBlock(
                child=DecimalBlock(length=4),
                length=(lambda ctx: ctx.read_bytes_remaining // 4, 'file size / 4'),
            ),
            {
                'description': 'Ceiling height of each slice in meters, used where the slice is covered (wall '
                'type 2 in its collision_data record; newton, nfs3.exe 0x4a21a0). 4.25..33.75 in the NFS3 tracks'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


class Nfs3CanKeyframe(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A keyframe of a CAN animation path, 20 bytes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        position = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Position in meters (16.16)'},
        )
        orientation = (
            Quaternion(child=FixedPointBlock(length=2, fraction_bits=14, is_signed=True)),
            {
                'description': 'Orientation quaternion, signed 16-bit values read as `(v << 2) / 65536` '
                '(unit 1/16384); unit length in every keyframe of the NFS2, NFS2 SE, NFS3 and NFS4 files'
            },
        )


def _can_size(ctx):
    return 8 + 20 * len(ctx.data('keyframes'))


class Nfs3CanAnimation(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Animation path (GameData/Tracks/TRK<nnn>/TR<nn><k>.CAN, TR<nn>00A.CAN). '
            'nfs3.exe plays them as the paths of knocked-away objects (TR<nn>00A.CAN as path 1, TR<nn>0<k>.CAN as '
            'path k + 1; the renderer 0x41ca40 -> 0x40f940 -> 0x40f4b0). NFS4 (Data/Tracks/<track>/Tr<nn>.can, any '
            'case) has the same files: nfs4.exe 0x41e760 loads `Tr00a.can` as path 0 and `Tr01.can` .. `Tr06.can` '
            'as paths 1..6 (`Tr00.can` is not loaded) and multiplies their positions by 1 / 1.3 (rounded to 16.16 '
            'again); a knocked object (`collision.type` 2 of [Nfs4RefExtraObject](#nfs4refextraobject)) plays path 2 '
            'below 25 m/s, else path 3 (0x437ed0). The `.CAN` files of NFS2 and NFS2 SE (GAMEDATA/TRACKS/DATA) have '
            'the same layout (their use there is not verified)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        size = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=_can_size),
            {'description': 'File size in bytes, 8 + 20 * `num_keyframes` in every NFS2, NFS2 SE, NFS3 and NFS4 file'},
        )
        unk = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'The same in the same file of every NFS3 track (01: 0x0164, 02: 0x828e, 03: 0x8357, '
                '04, 05: 0x8320, 06: 0x0269, 00A: 0 but TR0200A 0x41), other values in the 00 files; the same values '
                'in the NFS4 files (00A: 0 or 0x41)',
                'is_unknown': True,
            },
        )
        num_keyframes = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('keyframes'))),
            {'description': 'Number of keyframes'},
        )
        ticks_per_frame = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Game ticks per keyframe; the game uses 6 when it is 0 or above 400. 6 in every file'},
        )
        keyframes = (
            ArrayBlock(child=Nfs3CanKeyframe(), length=lambda ctx: ctx.data('num_keyframes')),
            {'description': 'Keyframes'},
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer

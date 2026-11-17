from typing import Dict

from library.context import ReadContext
from library.read_blocks import (
    DeclarativeCompoundBlock,
    IntegerBlock,
    UTF8Block,
    BytesBlock,
    ArrayBlock,
    FixedPointBlock,
    Padding,
)
from library.read_blocks.misc.value_validators import Eq
from resources.eac.fields.misc import Point3D
from resources.eac.maps.nfs_common import ColPolygon, ColExtraBlock


class TrkBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track block (NFS2, NFS2 SE): a segment of the track (8 slices of the COL '
            'collision data) with its terrain at 3 levels of detail and extrablocks (props, road lines, road vectors '
            'etc.). Vertex coordinates are relative to the block position, defined in `block_positions` of the '
            'track file. The polygon records after the vertices are 6 consecutive sets, a main and an extra set '
            '(rails, fences) per level of detail: `low_polygons`, `low_extra_polygons`, `medium_polygons`, '
            '`medium_extra_polygons`, `high_polygons` (also the road surface of the physics), '
            '`high_extra_polygons` (the NFS2 SE slot loader 0x437420 sets their pointers one after the other, '
            'slot +0x484..+0x498). The block drawing (0x4361a0) picks the level by distance (0x437ee0: 2 the '
            'nearest, 0 the farthest) and draws its main set, then its extra set. NFS2 SE keeps the raw block '
            'bytes in memory (track reader nfs2sen.exe 0x461b00..)',
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
        block_size_2 = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Block size in bytes (duplicated)'},
        )
        num_extrablocks = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of extrablocks'})
        first_slice = (
            IntegerBlock(length=2, is_signed=True),
            {
                'description': "Index of the block's first slice (track collision spline point) in the "
                '`collision_data` extrablock of the COL file: `block_idx` * 8 in every NFS2 and NFS2 SE track. '
                'NFS2 SE reads it as a signed 16-bit value (nfs2sen.exe 0x461b30)'
            },
        )
        block_idx = (IntegerBlock(length=4, is_signed=False), {'description': 'Block index (serial number)'})
        bounds = (
            ArrayBlock(child=Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)), length=4),
            {'description': 'Block bounding rectangle'},
        )
        extrablocks_offset = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'An offset to "extrablock_offsets" block from here'},
        )
        nv8 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of stick-to-next vertices: vertices shared with the next block, stored '
                'relative to the position of the next block. Every level of detail uses them'
            },
        )
        nv4 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of own vertices of the low level of detail: `low_polygons` and '
                "`low_extra_polygons` use the vertices below nv8 + nv4 (vertex count of level 0 in nfs2sen.exe's "
                'level table 0x4c515c; a few polygons of the NFS2 tracks use one or more past it, none in NFS2 SE)'
            },
        )
        nv2 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of own vertices of the medium level of detail: `medium_polygons` and '
                '`medium_extra_polygons` use the vertices below nv8 + nv2 (level 1 of the table 0x4c515c)'
            },
        )
        nv1 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of own vertices of the high level of detail: `high_polygons` and '
                '`high_extra_polygons` use every vertex (level 2 of the table 0x4c515c). The vertices of lower '
                'levels come first: nv4 <= nv2 <= nv1'
            },
        )
        num_low_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `low_polygons` (polygon set 0)'},
        )
        num_low_extra_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `low_extra_polygons` (polygon set 1)'},
        )
        num_medium_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `medium_polygons` (polygon set 2)'},
        )
        num_medium_extra_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `medium_extra_polygons` (polygon set 3)'},
        )
        num_high_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `high_polygons` (polygon set 4)'},
        )
        num_high_extra_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of polygons in `high_extra_polygons` (polygon set 5; 0..16 in the NFS2 and '
                'NFS2 SE tracks)'
            },
        )
        vertices = (
            ArrayBlock(
                child=Point3D(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True)),
                length=lambda ctx: ctx.data('nv8') + ctx.data('nv1'),
            ),
            {
                'description': 'Vertices. The first nv8 items are relative to the position of the next block '
                '(`block_positions[block_idx + 1]`, or of block 0 for the last block), the '
                'remaining nv1 items are relative to the position of this block'
            },
        )
        low_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_low_polygons')),
            {
                'description': 'Polygon set 0: the terrain of the low level of detail (level 0, the farthest blocks), '
                'drawn with `low_extra_polygons` (block drawing nfs2sen.exe 0x4361a0: set 2 * level, then set 2 * '
                'level + 1, through BWorld_AddTrackPolys 0x436ba0). Vertex indexes point to `vertices`, below nv8 '
                '+ nv4 (see `nv4`)'
            },
        )
        low_extra_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_low_extra_polygons')),
            {
                'description': 'Polygon set 1: what the low level of detail draws over its terrain: guard rails, '
                'trusses, fences (textures such as RGRA, TRUS, FENC), about a tenth of `low_polygons`. Vertex '
                'indexes below nv8 + nv4'
            },
        )
        medium_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_medium_polygons')),
            {
                'description': 'Polygon set 2: the terrain of the medium level of detail (level 1), twice as many '
                'polygons as `low_polygons`, drawn with `medium_extra_polygons`. Vertex indexes below nv8 + nv2'
            },
        )
        medium_extra_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_medium_extra_polygons')),
            {
                'description': 'Polygon set 3: rails, trusses and fences of the medium level of detail, like '
                '`low_extra_polygons`. Vertex indexes below nv8 + nv2'
            },
        )
        high_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_high_polygons')),
            {
                'description': 'Polygon set 4: the terrain of the high level of detail (level 2, the nearest '
                'blocks, full detail), twice as many polygons as `medium_polygons`, drawn with '
                '`high_extra_polygons` and the road lines of the `road_lines` extrablock (0x436d70). It is also the road '
                'surface the physics searches for the polygon under a car (NFS2 SE: nfs2sen.exe 0x4384c0): '
                '`median_polygons` records point to runs of them per slice, `polygon_map` has one record per '
                'polygon of this set (road vector and surface). Vertex indexes point to `vertices`, so indexes '
                'below nv8 are vertices of the next block'
            },
        )
        high_extra_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_high_extra_polygons')),
            {
                'description': 'Polygon set 5: rails, trusses and fences of the high level of detail, like '
                '`low_extra_polygons`'
            },
        )
        padding = (
            Padding(to=(lambda ctx: 64 + ctx.data('extrablocks_offset'), 'extrablocks_offset + 64')),
            {
                'description': '0 or 2 bytes up to `extrablock_offsets`. In NFS2 SE zeros, which align '
                '`extrablock_offsets` to 4 bytes from the block start; some NFS2 blocks have other bytes here'
            },
        )
        extrablock_offsets = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: ctx.data('num_extrablocks')),
            {'description': 'Offset to each of the extrablocks'},
        )
        extrablocks = (
            ArrayBlock(length=(0, 'num_extrablocks'), child=ColExtraBlock()),
            {
                'description': 'Extrablocks of the block. Typically: polygon_map, block_numbers, '
                'prop_descriptions + props_18 (props placed in this block), median_polygons, '
                'road_vectors, road_lines. The NFS2 SE slot loader (nfs2sen.exe 0x437420) looks up the types 5, 6, 7, '
                '8, 10, 11, 13, 17, 18 and 19',
                'usage': 'ui',
            },
        )
        extrablocks_bytes = (
            BytesBlock(length=lambda ctx: ctx.data('block_size') - ctx.local_buffer_pos),
            {
                'description': 'A part of block, where extrablocks data is located. Offsets to the entries '
                'are defined in `extrablock_offsets` block. Item type:'
                '<br/>- [ColExtraBlock](#colextrablock)',
                'usage': 'io,doc',
            },
        )

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        data = super().read(ctx, name, read_bytes_amount)
        data['extrablocks'] = []
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, data)
        array_ctx = self_ctx.get_or_create_child('extrablocks', self, read_bytes_amount, data)
        end_pos = ctx.buffer.tell()
        child_block = self.field_blocks_map.get('extrablocks').child
        for i, offset in enumerate(data['extrablock_offsets']):
            ctx.buffer.seek(self_ctx.read_start_offset + offset)
            data['extrablocks'].append(child_block.unpack(array_ctx, name=str(i)))
        ctx.buffer.seek(end_pos)
        return data


class TrkSuperBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A group of up to 8 consecutive track blocks'}

    class Fields(DeclarativeCompoundBlock.Fields):
        block_size = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: ctx.block.estimate_packed_size(ctx.get_full_data()),
            ),
            {'description': 'Superblock size in bytes'},
        )
        num_blocks = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Number of blocks in this superblock. Usually 8 or less in the last superblock'},
        )
        unk = (IntegerBlock(length=4), {'is_unknown': True})
        block_offsets = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: ctx.data('num_blocks')),
            {'description': 'Offset to each of the blocks'},
        )
        blocks = (ArrayBlock(child=TrkBlock(), length=lambda ctx: ctx.data('num_blocks')), {'description': 'Blocks'})


class TrkMap(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Main track file. The track is split into blocks (segments), grouped by 8 into '
            'superblocks. Each block has a terrain mesh at 3 resolutions and extrablocks '
            'with props. Polygon texture values index the textures_map extrablock of the '
            'accompanying COL file, which points to images in <track>0.QFS',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('TRAC')), {'description': 'Resource ID'})
        unk0 = (BytesBlock(length=20), {'is_unknown': True})
        num_superblocks = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('superblock_offsets'))),
            {'description': 'Number of superblocks (nsblk)'},
        )
        num_blocks = (IntegerBlock(length=4, is_signed=False), {'description': 'Number of blocks (nblk)'})
        superblock_offsets = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: ctx.data('num_superblocks')),
            {'description': 'Offset to each of the superblocks'},
        )
        block_positions = (
            ArrayBlock(
                child=Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
                length=lambda ctx: ctx.data('num_blocks'),
            ),
            {
                'description': 'Positions of blocks in the world: a point on the road at the start of each '
                'block. Block vertices are relative to these points, and all positions '
                'together form the track path (closed loop)'
            },
        )
        skip_bytes = (
            Padding(to=(lambda ctx: ctx.data('superblock_offsets/0'), 'superblock_offsets[0]')),
            {'description': 'Useless padding'},
        )
        superblocks = (
            ArrayBlock(child=TrkSuperBlock(), length=lambda ctx: ctx.data('num_superblocks')),
            {'description': 'Superblocks'},
        )

    def serializer_class(self):
        from serializers import TrkMapSerializer

        return TrkMapSerializer

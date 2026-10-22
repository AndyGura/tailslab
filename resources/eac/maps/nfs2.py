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
            'collision data) with terrain mesh at 3 resolutions, the road polygons the physics uses and '
            'extrablocks (props, lanes, road vectors etc.). Vertex coordinates are relative '
            'to the block position, defined in `block_positions` of the track file. The polygon records '
            'after the vertices are 6 consecutive sets: `polygons` (3 levels of detail), `extra_polygons`, '
            '`road_polygons` and `unk_polygons`. NFS2 SE keeps the raw block bytes in memory (track reader '
            'nfs2sen.exe 0x461b00..)',
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
                'relative to the position of the next block'
            },
        )
        nv4 = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of own vertices for 1/4 resolution'})
        nv2 = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of own vertices for 1/2 resolution'})
        nv1 = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of own vertices for full resolution. Vertex sets of lower resolutions are '
                'subsets of it: nv4 <= nv2 <= nv1'
            },
        )
        np4 = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of polygons for 1/4 resolution'})
        np2 = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of polygons for 1/2 resolution'})
        np1 = (IntegerBlock(length=2, is_signed=False), {'description': 'Number of polygons for full resolution'})
        num_extra_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `extra_polygons`'},
        )
        num_road_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `road_polygons`'},
        )
        num_unk_polygons = (
            IntegerBlock(length=2, is_signed=False),
            {'description': 'Number of polygons in `unk_polygons` (0..16 in the NFS2 and NFS2 SE tracks)'},
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
        polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('np4') + ctx.data('np2') + ctx.data('np1')),
            {
                'description': 'Polygons: np4 polygons of the 1/4 resolution mesh, then np2 polygons of the 1/2 '
                'resolution mesh, then np1 polygons of the full resolution mesh. The three sets '
                'are alternative levels of detail of the same terrain; the converter exports the '
                'full resolution one. Vertex indexes point to `vertices`'
            },
        )
        extra_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_extra_polygons')),
            {
                'description': 'A 4th polygon set, purpose unknown. NFS2 SE keeps a pointer to it per loaded block '
                '(slot loader nfs2sen.exe 0x437420)',
                'is_unknown': True,
            },
        )
        road_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_road_polygons')),
            {
                'description': 'The road surface polygons the physics searches for the polygon under a car (NFS2 SE: '
                'nfs2sen.exe 0x4384c0, pointer set by the slot loader 0x437420). `median_polygons` records point '
                'to runs of them per slice, `polygon_map` has one record per polygon of this set (road vector and '
                'surface). Vertex indexes point to `vertices`, so indexes below nv8 are vertices of the next block'
            },
        )
        unk_polygons = (
            ArrayBlock(child=ColPolygon(), length=lambda ctx: ctx.data('num_unk_polygons')),
            {
                'description': 'A 6th set of polygon records (vertex indexes within `vertices`), purpose unknown. '
                'The NFS2 SE slot loader (nfs2sen.exe 0x437420) only computes where it starts (the end of '
                '`road_polygons`)',
                'is_unknown': True,
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
                'road_vectors, lanes. The NFS2 SE slot loader (nfs2sen.exe 0x437420) looks up the types 5, 6, 7, '
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

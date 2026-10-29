from typing import Dict

from library.read_blocks import (
    DeclarativeCompoundBlock,
    CompoundBlock,
    IntegerBlock,
    BytesBlock,
    ArrayBlock,
    DecimalBlock,
    FixedPointBlock,
    OptionalBlock,
    SubByteCompoundBlock,
)
from resources.eac.fields.misc import Point3D, Quaternion

# NFS4 (High Stakes) uses the same overall "TRK" family of formats as NFS3, but the file layout
# differs in several places: virtual road (vroad) data moved from per-block to a single global
# array referenced by index, block headers are stored in one contiguous array followed by a
# separate contiguous array of block bodies (rather than being interleaved per block like NFS3),
# and each block's own polygon/extra-object chunks are sized from counts already read as part of
# its header instead of being self-length-prefixed. See `library/loader.py`'s `.FRD` detection
# branch for how NFS3 vs NFS4 files (same extension) are told apart.


def _ancestor(ctx, levels: int):
    # Guards against the standalone, parent-less `DocumentationContext()` used when rendering a
    # criteria/length lambda's string representation for the auto-generated docs (see
    # `OptionalBlock.schema`/`ArrayBlock.length_doc_str`) - real read/write contexts always have
    # enough real parents for the `levels` this module calls with.
    for _ in range(levels):
        if ctx is None or ctx.parent is None:
            return ctx
        ctx = ctx.parent
    return ctx


def _block_header_field(*path: str):
    # For use inside Nfs4TrkBlock.Fields: looks up a field of the corresponding entry (same
    # array index) of the top-level `blocks_headers` array, 2 context levels above this block
    # (Nfs4TrkBlock's own context -> the `blocks` array context -> FrdMap's own context).
    suffix = '/'.join(path)
    return lambda ctx: _ancestor(ctx, 2).data(f'blocks_headers/{ctx.name}/{suffix}')


def _block_header_chunk_count(chunk_index: int):
    # For use as the `length` of a Nfs4XObjChunk nested directly inside Nfs4TrkBlock.Fields:
    # looks up `object_chunk_counts[chunk_index].num` of the enclosing block's header. 3 levels
    # above the chunk's own context: Nfs4XObjChunk's context -> Nfs4TrkBlock's own context (whose
    # name is the block index) -> the `blocks` array context -> FrdMap's own context.
    return lambda ctx: _ancestor(ctx, 3).data(f'blocks_headers/{ctx.parent.name}/object_chunk_counts/{chunk_index}/num')


def _object_header_field(*path: str):
    # For use inside Nfs4ExtraObject.Fields: looks up a field of the corresponding entry (same
    # array index) of the enclosing Nfs4XObjChunk's own `object_headers` array, 2 context levels
    # above this object (Nfs4ExtraObject's own context -> the `objects` array context ->
    # Nfs4XObjChunk's own context).
    suffix = '/'.join(path)
    return lambda ctx: _ancestor(ctx, 2).data(f'object_headers/{ctx.name}/{suffix}')


class Nfs4VRoadBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Virtual road record of a track slice: the slice centre on the road with the road '
            'frame, distances to the road edges, lanes and side types. One per slice, 8 slices per track block: block '
            'b has the slices b * 8 .. b * 8 + `num_slices` - 1 of its header (nfs4.exe 0x439d60). nfs4.exe reads '
            'these records in place from the loaded file (0x64f1a4); NFS4 has no COL file, this is its '
            '`collision_data`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        ref_point = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'The slice centre on the road (nfs4.exe 0x4f63d0, 0x4395f0): the road frame origin, '
                'the point a car is placed from (0x4f4590)'
            },
        )
        normal = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Road normal (up), row 1 of the road frame (0x4395f0, 0x4f63d0)'},
        )
        forward = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Road forward vector, row 2 of the road frame (0x4395f0, 0x4f4590)'},
        )
        right = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Road right vector, row 0 of the road frame. A point p is left of the centre when '
                'right . (p - ref_point) <= 0 (nfs4.exe 0x4399d0, the wall type choice of 0x45cf20)'
            },
        )
        left_wall = (
            DecimalBlock(length=4),
            {
                'description': 'Distance from the slice centre to the left wall/edge in meters: the lateral offset '
                'of an AI lane is kept at least a margin (2 m for the AI line the game makes when the speed file is '
                'short) inside it (nfs4.exe 0x41e0d0)'
            },
        )
        right_wall = (
            DecimalBlock(length=4),
            {'description': 'Distance from the slice centre to the right wall/edge in meters, as `left_wall`'},
        )
        left_lane_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of the lanes left of the centre in meters (0..10 in the NFS4 tracks). Lane '
                'centres: -i x width - width / 2 (nfs4.exe 0x448c20, the car reset), the grid (0x444700); a lateral '
                'offset < 0 is lane 6 + round((width / 2 + offset) / width) (0x41cce0)'
            },
        )
        right_lane_width = (
            DecimalBlock(length=4),
            {
                'description': 'Width of the lanes right of the centre in meters (2..10): lane centres i x width + '
                'width / 2 (0x448c20, 0x444700), offset >= 0 is lane 7 + round((offset - width / 2) / width) '
                '(0x41cce0)'
            },
        )
        unk0 = (
            IntegerBlock(length=4, is_signed=False),
            {'description': '0xFFFFFFFF in nearly all records of the NFS4 tracks', 'is_unknown': True},
        )
        left_lanes = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Number of lanes left of the centre (0..4): the car reset tries their centres for a '
                'free spot (nfs4.exe 0x448c20). AI lane 6 - this, the first past them, is an edge lane for 0x41e0d0 '
                '(its offset is the boundary of the outer lane minus the margin instead of a lane centre)'
            },
        )
        right_lanes = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Number of lanes right of the centre (1..4), as `left_lanes` (0x448c20); AI lane 7 + '
                'this is the edge lane on the right (0x41e0d0)'
            },
        )
        lane_open_bits = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Usable lanes: lane i (0..13, 6 and 7 the lanes either side of the centre, see '
                '`left_lane_width`) is open when bit 15 - clamp(i + 1, 0, 15) is set (nfs4.exe 0x41cc00); '
                'a car is reset only onto an open lane (0x448870). 0x3c0 (lanes 5..8) the most common'
            },
        )
        left_side_type = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Type of the road side left of the centre (0..5). Two code-verified uses of this '
                'byte: 2 = covered (tunnel, roof: no weather there, the ceiling of heights.sim applies; nfs4.exe '
                '0x4399d0 / 0x439ab0, with polygon surface bit 0x20); and the wall crash type of a wall hit on this '
                'side, crash type 0x40000 | value, 0 or above 7 counting as 4 (0x45cf20)'
            },
        )
        right_side_type = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Type of the road side right of the centre, as `left_side_type` (0x4399d0, 0x45cf20)'},
        )
        unk1 = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=False), length=2),
            {'description': 'Values 0..5, often equal to each other', 'is_unknown': True},
        )


class Nfs4BlockCount(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Amount of items of an array of the track block and the slot the loader writes '
            "the array's address into",
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        num = (IntegerBlock(length=4, is_signed=False), {'description': 'Amount of items'})
        pointer = (
            IntegerBlock(length=4),
            {
                'description': "Run-time pointer slot: nfs4.exe's FRD loader (0x4327b0, 0x4325f0) writes the "
                "items' address here (when `num` is not 0). The files hold leftovers of the tool's memory"
            },
        )


class Nfs4NeighbourData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Reference to a neighbouring track block'}

    class Fields(DeclarativeCompoundBlock.Fields):
        block = (IntegerBlock(length=2, is_signed=True), {'description': 'Neighbouring block index, or -1'})
        unk = (IntegerBlock(length=2, is_signed=True), {'description': '-1, 0, 1 or 2', 'is_unknown': True})


class Nfs4TrkBlockHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Metadata of a track block (segment of the track): position, bounds, neighbours '
            'and the counts which define sizes of all arrays in the [Nfs4TrkBlock]'
            '(#nfs4trkblock) with the same index. nfs4.exe copies the 0x5e8 bytes as they are (0x4327b0, 300 blocks '
            'at most) and writes the addresses of the block arrays into the pointer slots',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        polygon_chunk_sizes = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=11),
            {
                'description': 'Amount of polygons in each of the 11 polygon chunks (see Nfs4TrkBlock) of this block. '
                'Chunk 4 (high-res track) holds the road polygons of the track position search (nfs4.exe 0x439fe0)'
            },
        )
        polygon_chunk_pointers = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=11),
            {
                'description': "Run-time pointer slots: the loader (nfs4.exe 0x4327b0) writes each polygon chunk's "
                "address here, 0 for an empty chunk. The files hold leftovers of the tool's memory"
            },
        )
        num_vertices = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Total amount of vertices stored for this block'},
        )
        num_vertices_high = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices used by high-res terrain polygons'},
        )
        num_vertices_low = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices used by low-res terrain polygons'},
        )
        num_vertices_med = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices used by medium-res terrain polygons'},
        )
        num_vertices_dup = (IntegerBlock(length=4, is_signed=False), {'description': 'Equals to `num_vertices`'})
        num_vertices_obj = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices used by per-block objects?', 'is_unknown': True},
        )
        vertex_pointers = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=2),
            {
                'description': 'Run-time pointer slots of `vertices` and `vertex_shading`, written by the loader '
                '(nfs4.exe 0x4327b0); leftovers in the files'
            },
        )
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
        neighbour_data = (
            ArrayBlock(child=Nfs4NeighbourData(), length=300),
            {'description': 'Neighbouring blocks. Unused items have block index -1'},
        )
        object_chunk_counts = (
            ArrayBlock(child=Nfs4BlockCount(), length=4),
            {
                'description': 'Amount of extra objects in each of the 4 per-block '
                'extra object chunks (see Nfs4TrkBlock)'
            },
        )
        num_polygons = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Amount of items in `polygon_vroad_data` (0x18-byte polygon records, nfs4.exe '
                'block +0x584)'
            },
        )
        bounds_min = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Minimum corner of the axis-aligned bounding box of the block. Its x / z range is the '
                "block test of the track position search and the span of the polygon records' cells (nfs4.exe "
                '0x439fe0); also the box centre of the nearest block (0x439ea0)'
            },
        )
        bounds_max = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Maximum corner of the axis-aligned bounding box of the block, see `bounds_min`'},
        )
        polygon_vroad_data_pointer = (
            IntegerBlock(length=4),
            {
                'description': 'Run-time pointer slot of `polygon_vroad_data`, written by the loader (nfs4.exe '
                '0x4327b0); leftovers in the files'
            },
        )
        num_slices = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Number of track slices (`vroad` records) of the block: 8, the last block fewer. '
                'Block b owns the vroad records b * 8 .. b * 8 + this - 1 (nfs4.exe 0x439d60); the sum over all '
                'blocks is `num_vroad`'
            },
        )
        num_xobj = (Nfs4BlockCount(), {'description': 'Amount of items in `xobj`'})
        num_polyobj = (Nfs4BlockCount(), {'description': 'Amount of items in `xobj2`'})
        num_soundsrc = (Nfs4BlockCount(), {'description': 'Amount of items in `soundsrc`'})
        num_lightsrc = (Nfs4BlockCount(), {'description': 'Amount of items in `lightsrc`'})
        neighbors = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {
                'description': 'Neighbouring block numbers, -1 unused (4 to 6 of them in the NFS4 tracks): a block '
                'is near another when it is that block or one of its 8 neighbours (nfs4.exe 0x4392d0: the wall '
                'test of the car collisions, 0x45cde0)'
            },
        )


class Nfs4PolygonVroadData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Road data of a high-res track polygon (chunk 4) of the block, 0x18 bytes: where '
            "the polygon lies in the block's cell grid, its wall edges and surface, its normal and forward vectors. "
            "nfs4.exe's track position search (0x439fe0) scans these records for the one whose cell range holds the "
            'point and whose polygon holds it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        cell_z_min = (
            IntegerBlock(length=1, is_signed=False),
            {
                'description': 'Lowest z cell of the polygon: the x / z box of the block (`bounds_min` .. '
                '`bounds_max` of its header) is split into 256 cells per axis, cell = trunc((p - min) x 255 / (max - '
                'min)) (nfs4.exe 0x439fe0)'
            },
        )
        cell_z_max = (IntegerBlock(length=1, is_signed=False), {'description': 'Highest z cell of the polygon'})
        cell_x_min = (IntegerBlock(length=1, is_signed=False), {'description': 'Lowest x cell of the polygon'})
        cell_x_max = (IntegerBlock(length=1, is_signed=False), {'description': 'Highest x cell of the polygon'})
        edge_walls = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=False), length=4),
            {
                'description': 'Wall flag of each polygon edge: corners 0-1, 1-2, 2-3, 3-0 (edge bits 1, 2, 4, 8 of '
                'nfs4.exe 0x4393e0). 0 or 255 (rarely 1) in the NFS4 tracks. A car box point beyond the edges of '
                'its polygon is pushed back by the mean of the normals of those edges whose flag is not 0 (the road '
                'edge walls, 0x45cf20, on polygons with `surface.walls`)'
            },
        )
        surface = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (1, 'walls', 'boolean', [], 'The road edge wall check runs on this polygon (nfs4.exe 0x45cf20)'),
                    (1, 'objects', 'boolean', [], 'Track objects of the block are tested here (0x45d8c0)'),
                    (1, 'covered', 'boolean', [], 'Covered (tunnel, roof): no weather, heights.sim ceiling (0x439ab0)'),
                    (
                        5,
                        'surface_type',
                        'number',
                        [],
                        'Road surface type, the index in the grip table (32 entries, nfs4.exe 0x5c0820); 0 and 0xe '
                        'are not drivable: off the road for the walls (0x45cde0), the car is put back (0x4f3e40)',
                    ),
                ],
            ),
            {
                'description': 'Surface byte: bits 0x1f `surface_type` (the grip table index of nfs4.exe 0x5c0820, '
                '0 and 0xe not drivable: 0x45cde0, 0x4f3e40), bit 0x20 `covered` (0x439ab0), bit 0x40 `objects` (the '
                'track object collisions, 0x45e2b0), bit 0x80 `walls` (the road edge walls, 0x45e2b0). The car keeps '
                'it as car+0x1d4'
            },
        )
        unk = (IntegerBlock(length=1), {'is_unknown': True})
        polygon = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Number of the polygon in the high-res track chunk (`polygons_high_res_track`, chunk '
                '4) of the block, which this record describes (nfs4.exe 0x439fe0)'
            },
        )
        normal = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True)),
            {
                'description': 'Normal vector of the polygon, unit 1/32768: the road frame on this polygon (nfs4.exe '
                '0x439fe0, 0x4395f0)'
            },
        )
        forward = (
            Point3D(child=FixedPointBlock(length=2, fraction_bits=15, is_signed=True)),
            {'description': 'Forward vector of the polygon, unit 1/32768 (0x439fe0)'},
        )


class Nfs4RefExtraObject(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Reference to an extra object (XOBJ) placed in the track block: what the car '
            'collisions test (nfs4.exe 0x45d8c0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        pt = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {'description': 'Position of the object'},
        )
        radius = (
            FixedPointBlock(length=2, fraction_bits=8, is_signed=True),
            {
                'description': 'Collision radius in meters, unit 1/256 m (nfs4.exe 0x439520 reads it as a signed '
                '16-bit value, `<< 8` makes it 16.16), halved for `collision.type` 1 and doubled for 2. The object '
                'collision (0x45d8c0) uses the result: within the car radius + it, taller (2 x radius) than the car '
                'is above the ground'
            },
        )
        global_index = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Sequence number of this object among all extra objects of the track: the index in '
                "the game's object state table (nfs4.exe 0x64f3c8, 512 entries of 3 bytes: standing / knocked away)"
            },
        )
        unk1 = (BytesBlock(length=3), {'is_unknown': True})
        collision = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (6, 'unk', 'number', [], 'Unknown (0, 5, 8, 10, 30, 44...)'),
                    (
                        2,
                        'type',
                        'enum',
                        ['none', 'solid', 'knockable', 'crash_only'],
                        'Collision type (nfs4.exe 0x45d8c0, 0x437ed0)',
                    ),
                ],
            ),
            {
                'description': 'Collision byte. Bits 0..1 `type` (nfs4.exe 0x45d8c0, 0x437ed0): 0 none (skipped); 1 '
                'solid; 2 knockable: knocked away when the car (not AI) hits it at round(|vx| + |vz|) >= 11 m/s, '
                'played along CAN path 2 below 25 m/s, else 3 (a solid wall slower); 3 crash only: no response, a '
                'crash of 15 above 2 m/s. Type 1 also halves `radius`, 2 doubles it (0x439520). Other bits: unknown'
            },
        )


class Nfs4RefExtraObject2(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Reference to a per-block object (POLYOBJ) placed in the track block',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=2), {'is_unknown': True})
        type = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        id = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        pt = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=24, is_signed=True)),
            {'description': 'Position of the object'},
        )
        crossindex = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        unk1 = (BytesBlock(length=3), {'is_unknown': True})


class Nfs4XObjHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Header of an extra object: type, position and the counts which define the '
            'sizes of the corresponding [Nfs4ExtraObject](#nfs4extraobject) arrays. nfs4.exe keeps the 0x34 bytes '
            'in place and writes the addresses of the object data into the pointer slots (0x4325f0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        type = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Object type. One of: 1, 2, 4 (normal static object), 3 (animated object, has '
                '`anim_data`), 6 (special/physics prop, has `special_data`). Objects of type 6 '
                'are placed in global chunks of the track file, not in track blocks: nfs4.exe makes rigid bodies '
                'of them (0x432e40, 0x431550; 306 in the NFS4 tracks, all in `global_objects_1`)'
            },
        )
        index = (IntegerBlock(length=4, is_signed=False), {'is_unknown': True})
        unk0 = (IntegerBlock(length=4), {'is_unknown': True})
        pt = (Point3D(child=DecimalBlock(length=4)), {'description': 'Object position'})
        size = (
            IntegerBlock(length=4, is_signed=False),
            {
                'description': 'Size in bytes of the type data at the start of the object (`anim_data`: 8 + 20 x '
                'keyframes for type 3, `special_data`: 0x48 for type 6, 0 for the others): nfs4.exe 0x4325f0 reads '
                'that many bytes before the vertices'
            },
        )
        data_pointer = (
            IntegerBlock(length=4),
            {
                'description': 'Run-time pointer slot of the type data (0 when `size` is 0), written by the loader '
                '(nfs4.exe 0x4325f0); leftovers in the files'
            },
        )
        num_vertices = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of vertices of the corresponding entry in `objects`'},
        )
        vertex_pointers = (
            ArrayBlock(child=IntegerBlock(length=4), length=2),
            {
                'description': 'Run-time pointer slots of `vertices` and `vertex_shading`, written by the loader '
                '(nfs4.exe 0x4325f0); leftovers in the files'
            },
        )
        num_polygons = (
            IntegerBlock(length=4, is_signed=False),
            {'description': 'Amount of polygons of the corresponding entry in `objects`'},
        )
        polygons_pointer = (
            IntegerBlock(length=4),
            {
                'description': 'Run-time pointer slot of `polygons`, written by the loader (nfs4.exe 0x4325f0); '
                'leftovers in the files'
            },
        )


class Nfs4AnimKeyframe(DeclarativeCompoundBlock):
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
                'description': 'Object orientation at this keyframe. Presumably the same as in NFS3: object vertices '
                "are rotated by it (v' = q v q^-1), then moved to `pt`"
            },
        )


class Nfs4AnimExtra(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Animation of an extra object: a sequence of keyframes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (IntegerBlock(length=2), {'is_unknown': True})
        anim_type = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        anim_id = (IntegerBlock(length=1, is_signed=False), {'is_unknown': True})
        num_keyframes = (
            IntegerBlock(length=2, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('keyframes'))),
            {'usage': 'io,doc', 'description': 'Amount of keyframes'},
        )
        delay = (IntegerBlock(length=2, is_signed=False), {'description': 'Animation delay/period'})
        keyframes = (
            ArrayBlock(child=Nfs4AnimKeyframe(), length=lambda ctx: ctx.data('num_keyframes')),
            {'description': 'Animation keyframes'},
        )


class Nfs4SpecialExtra(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Physics properties of a special extra object (movable prop, e.g. a barrel or a '
            "cone), 0x48 bytes: nfs4.exe 0x431550 makes the object's rigid body of them",
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        location = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': 'Position of the object. Equals to `pt` of the object header'},
        )
        mass = (DecimalBlock(length=4), {'description': 'Mass of the object'})
        transform = (
            ArrayBlock(child=DecimalBlock(length=4), length=9),
            {
                'description': "3x3 rotation matrix of the object. Rotates its vertices as row vectors: v' = v M "
                '(verified by roadside boards facing the oncoming traffic)'
            },
        )
        collision_dimensions = (
            Point3D(child=DecimalBlock(length=4)),
            {'description': "Half extents of the object's collision box (its body, nfs4.exe 0x431550)"},
        )
        slice = (
            IntegerBlock(length=4),
            {
                'description': 'Track slice (`vroad` record) the object stands at: its track position is searched '
                'from there and it is placed with its offset from the slice centre (nfs4.exe 0x431550)'
            },
        )
        shape = (
            IntegerBlock(length=2, is_signed=True),
            {
                'description': '0 or 2: 2 gives the body shape 2 (body+0xa0: the ground tests of 0x4f5320 / '
                '0x4f52c0 instead of the box tests; nfs4.exe 0x431550)'
            },
        )
        material = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Material 0..3 of the body (nfs4.exe 0x431550): the elasticity and body+0x30 value: '
                '0 (0.87, 0), 1 (0.67, 2), 2 (0.75, 1), 3 (0.8, 3), others as 0'
            },
        )


class Nfs4Polygon(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A single quad polygon of terrain or extra object. UV coordinates are not '
            'stored: the texture is mapped to the whole polygon, oriented according to '
            '`tex_flags`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        vertices = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=False), length=4),
            {
                'description': 'Indexes of the 4 vertices in the vertex table of the enclosing track block '
                '(terrain polygons) or extra object (object polygons)'
            },
        )
        texture = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'Bits 0-10: index of the texture in the track QFS archive '
                "(<file>0.QFS), not counting the archive's mirrored texture copies (images with a "
                '"<mirrored>" text attachment). Other bits: rendering flags'
            },
        )
        tex_flags = (
            IntegerBlock(length=2, is_signed=False),
            {
                'description': 'UV orientation of the texture on this polygon. Base UV-s of the 4 vertices are '
                '(0,1), (1,1), (1,0), (0,0); bit 4 mirrors them horizontally, bits 7-8 rotate '
                'them by 90 degrees x value. Other bits unknown.'
            },
        )
        anim_flags = (
            IntegerBlock(length=1, is_signed=False),
            {'description': 'Used for animated textures: length/period', 'is_unknown': True},
        )


class Nfs4ExtraObject(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Extra object mesh: a standalone object placed on the track (billboard, animated '
            'object, physics prop). Type, position and array sizes are defined by the '
            '[Nfs4XObjHeader](#nfs4xobjheader) with the same index in the enclosing chunk',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        anim_data = (
            OptionalBlock(
                child=Nfs4AnimExtra(), criteria=lambda ctx: _object_header_field('type')(ctx) == 3, default_value=None
            ),
            {'description': 'Present when the corresponding `object_headers` entry has type == 3 (animated)'},
        )
        special_data = (
            OptionalBlock(
                child=Nfs4SpecialExtra(),
                criteria=lambda ctx: _object_header_field('type')(ctx) == 6,
                default_value=None,
            ),
            {'description': 'Present when the corresponding `object_headers` entry has type == 6 (special)'},
        )
        vertices = (
            ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length=_object_header_field('num_vertices')),
            {
                'description': 'Vertices, relative to the object position `pt` of the header (rotated by '
                '`special_data.transform` for special objects)'
            },
        )
        vertex_shading = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Per-vertex shading color, 32-bit ARGB (0xFFRRGGBB), one item per vertex'},
        )
        polygons = (
            ArrayBlock(child=Nfs4Polygon(), length=_object_header_field('num_polygons')),
            {'description': 'Polygons of this object'},
        )


class Nfs4XObjChunk(CompoundBlock):
    def __init__(self, length, **kwargs):
        super().__init__(
            fields=[
                ('object_headers', ArrayBlock(child=Nfs4XObjHeader(), length=length), {}),
                (
                    'objects',
                    ArrayBlock(child=Nfs4ExtraObject(), length=lambda ctx: len(ctx.data('object_headers'))),
                    {},
                ),
            ],
            inline_description='A group of extra (out-of-terrain) objects: e.g. billboards, animated '
            'objects, physics props',
            **kwargs,
        )


class Nfs4TrkBlock(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track block body: terrain vertices and polygons at 3 levels of detail, plus '
            'objects placed in this segment of the track. All array sizes come from the '
            '[Nfs4TrkBlockHeader](#nfs4trkblockheader) with the same index',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        vertices = (
            ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length=_block_header_field('num_vertices')),
            {'description': 'Vertices, global coordinates'},
        )
        vertex_shading = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=False), length=lambda ctx: len(ctx.data('vertices'))),
            {'description': 'Per-vertex shading color, 32-bit ARGB (0xFFRRGGBB), one item per vertex'},
        )
        polygon_vroad_data = (
            ArrayBlock(child=Nfs4PolygonVroadData(), length=_block_header_field('num_polygons')),
            {
                'description': 'Road data of the high-res track polygons (chunk 4): cell range, wall edges, surface, '
                'normal and forward vectors'
            },
        )
        xobj = (
            ArrayBlock(child=Nfs4RefExtraObject(), length=_block_header_field('num_xobj/num')),
            {'description': 'References to extra objects placed in this block'},
        )
        xobj2 = (
            ArrayBlock(child=Nfs4RefExtraObject2(), length=_block_header_field('num_polyobj/num')),
            {'description': 'References to per-block objects placed in this block'},
        )
        soundsrc = (
            ArrayBlock(child=BytesBlock(length=16), length=_block_header_field('num_soundsrc/num')),
            {
                'description': 'Sound sources. Each 16-byte item: position (3 x 32-bit fixed point with 16 '
                'fraction bits) + 32-bit sound type'
            },
        )
        lightsrc = (
            ArrayBlock(child=BytesBlock(length=16), length=_block_header_field('num_lightsrc/num')),
            {
                'description': 'Light sources. Each 16-byte item: position (3 x 32-bit fixed point with 16 '
                'fraction bits) + 32-bit light type'
            },
        )
        polygons_low_res_track = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/0')),
            {'description': 'Low-res track polygons'},
        )
        polygons_low_res_misc = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/1')),
            {'description': 'Low-res misc (non-track) polygons'},
        )
        polygons_med_res_track = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/2')),
            {'description': 'Medium-res track polygons'},
        )
        polygons_med_res_misc = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/3')),
            {'description': 'Medium-res misc (non-track) polygons'},
        )
        polygons_high_res_track = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/4')),
            {'description': 'High-res track polygons'},
        )
        polygons_high_res_misc = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/5')),
            {'description': 'High-res misc (non-track) polygons'},
        )
        lanes = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/6')),
            {'description': 'Lane helper polygons, not meant to be rendered'},
        )
        polygons_high_res_misc_1 = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/7')),
            {
                'description': 'Additional polygon chunk, purpose unknown. Not rendered by the converter',
                'is_unknown': True,
            },
        )
        polygons_high_res_misc_2 = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/8')),
            {
                'description': 'Additional polygon chunk, purpose unknown. Not rendered by the converter',
                'is_unknown': True,
            },
        )
        polygons_high_res_misc_3 = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/9')),
            {
                'description': 'Additional polygon chunk, purpose unknown. Not rendered by the converter',
                'is_unknown': True,
            },
        )
        polygons_high_res_misc_4 = (
            ArrayBlock(child=Nfs4Polygon(), length=_block_header_field('polygon_chunk_sizes/10')),
            {
                'description': 'Additional polygon chunk, purpose unknown. Not rendered by the converter',
                'is_unknown': True,
            },
        )
        extra_objects_0 = (
            Nfs4XObjChunk(length=_block_header_chunk_count(0)),
            {
                'description': 'Extra objects chunk #0 of this block. Amount of objects is '
                '`object_chunk_counts[0].num` of the block header'
            },
        )
        extra_objects_1 = (
            Nfs4XObjChunk(length=_block_header_chunk_count(1)),
            {
                'description': 'Extra objects chunk #1 of this block. Amount of objects is '
                '`object_chunk_counts[1].num` of the block header'
            },
        )
        extra_objects_2 = (
            Nfs4XObjChunk(length=_block_header_chunk_count(2)),
            {
                'description': 'Extra objects chunk #2 of this block. Amount of objects is '
                '`object_chunk_counts[2].num` of the block header'
            },
        )
        extra_objects_3 = (
            Nfs4XObjChunk(length=_block_header_chunk_count(3)),
            {
                'description': 'Extra objects chunk #3 of this block. Amount of objects is '
                '`object_chunk_counts[3].num` of the block header'
            },
        )


class Nfs4FrdMap(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Main track file (NFS4 High Stakes). The track is split into blocks (segments): '
            'block headers with all counts come first, then block bodies with vertices, '
            'polygons at 3 levels of detail and objects. Polygon textures index the track '
            'QFS archive (<track>0.QFS), skipping its mirrored texture copies; UV-s are not stored, texture orientation '
            'is defined by polygon flags',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk = (
            BytesBlock(length=28),
            {
                'description': 'Unknown header, not read by nfs4.exe (the FRD loader 0x4327b0 reads only '
                '`num_blocks` and `num_vroad` of the first 36 bytes)',
                'is_unknown': True,
            },
        )
        num_blocks = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('blocks_headers')) - 1),
            {'description': 'Number of the last track block: the number of blocks - 1'},
        )
        num_vroad = (
            IntegerBlock(length=4, is_signed=False, programmatic_value=lambda ctx: len(ctx.data('vroad'))),
            {'description': 'Number of virtual road records: the number of track slices'},
        )
        vroad = (
            ArrayBlock(child=Nfs4VRoadBlock(), length=lambda ctx: ctx.data('num_vroad')),
            {
                'description': 'Virtual road: one record per track slice, 8 slices per block (`num_slices` of the '
                'block headers). heights.sim, spdFA.bin and spdRA.bin have one value per record'
            },
        )
        blocks_headers = (
            ArrayBlock(child=Nfs4TrkBlockHeader(), length=lambda ctx: ctx.data('num_blocks') + 1),
            {
                'description': 'Metadata for every track block, incl. the counts used to size '
                'the corresponding entry of `blocks`'
            },
        )
        blocks = (
            ArrayBlock(child=Nfs4TrkBlock(), length=lambda ctx: ctx.data('num_blocks') + 1),
            {'description': 'Track block geometry and extra data'},
        )
        num_global_objects_0 = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: len(ctx.data('global_objects_0/object_headers')),
            ),
            {'usage': 'io,doc', 'description': 'Amount of objects in `global_objects_0`'},
        )
        global_objects_0 = (
            Nfs4XObjChunk(length=lambda ctx: ctx.parent.data('num_global_objects_0')),
            {'description': 'Extra objects not attached to any track block'},
        )
        num_global_objects_1 = (
            IntegerBlock(
                length=4,
                is_signed=False,
                programmatic_value=lambda ctx: len(ctx.data('global_objects_1/object_headers')),
            ),
            {'usage': 'io,doc', 'description': 'Amount of objects in `global_objects_1`'},
        )
        global_objects_1 = (
            Nfs4XObjChunk(length=lambda ctx: ctx.parent.data('num_global_objects_1')),
            {'description': 'Extra objects not attached to any track block. Special/physics props (type 6) live here'},
        )

    def serializer_class(self):
        from serializers import Nfs4FrdMapSerializer

        return Nfs4FrdMapSerializer


class Nfs4HeightsSim(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Ceiling heights of the track slices (Data/Tracks/<track>/heights.sim, loaded by '
            'nfs4.exe 0x439c10): one float per `vroad` record of the FRD ([Nfs4VRoadBlock](#nfs4vroadblock)), the '
            'file is 4 bytes per slice in every NFS4 track. Without the file the game uses 10.0 for every slice',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        heights = (
            ArrayBlock(
                child=DecimalBlock(length=4),
                length=(lambda ctx: ctx.read_bytes_remaining // 4, 'file size / 4'),
            ),
            {
                'description': 'Ceiling height above the ground of each slice in meters, used where the car is '
                'covered (polygon surface bit 0x20, or side type 2 of its slice): a car higher than the slice centre '
                '+ this hits the plane of the reversed road normal there (newton, nfs4.exe 0x4f5fd0). 3.27..25.96 in '
                'the NFS4 tracks'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


def _spd_num_slices(size: int) -> int:
    """Slices of a speed file of `size` bytes: size = ceil(n / 2) + 5 n"""
    return 2 * size // 11


def is_nfs4_speed_file_size(size: int) -> bool:
    n = _spd_num_slices(size)
    return n > 0 and (n + 1) // 2 + 5 * n == size


class Nfs4SpeedFile(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'AI line of the track (Data/Tracks/<track>/spdFA.bin forward, spdRA.bin reversed '
            'track; any case on disk), loaded by nfs4.exe 0x41c360 (0x41c4c0 picks the file): three arrays over the '
            'n track slices (`vroad` records of the FRD), the file is ceil(n / 2) + 5 n bytes in every NFS4 track. A '
            'shorter file is "Invalid speed file in track": the game then makes the AI line offsets itself from the '
            '(missing) lanes, 0x41c550 / 0x41e0d0; without the file it uses speed 64, lane 7 and offset 0. France also '
            'has a `spdB.bin` of the same layout that nfs4.exe does not load',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        speeds = (
            ArrayBlock(
                child=IntegerBlock(length=1, is_signed=False),
                length=(
                    lambda ctx: (_spd_num_slices(ctx.read_bytes_remaining) + 1) // 2,
                    'ceil(n / 2), n = 2 x file size // 11',
                ),
            ),
            {
                'description': 'AI target speed, one byte per two slices (slice s reads byte s / 2; nfs4.exe '
                '0x41c500), in m/s by its uses (the AI and the unused driving aid 0x4fd580 compare it with the car '
                "speed; 0x41d3c0 keeps the track's highest). 17..119 in the NFS4 tracks (one 254 in Summit's spdRA)"
            },
        )
        lanes = (
            ArrayBlock(
                child=SubByteCompoundBlock(
                    length=1,
                    schema=[
                        (4, 'lane', 'number', [], 'AI lane (nfs4.exe 0x41c550)'),
                        (4, 'unk', 'number', [], '0 in every NFS4 file; not read'),
                    ],
                ),
                length=(lambda ctx: ctx.read_bytes_remaining // 5, 'n'),
            ),
            {
                'description': 'A byte per slice: the high 4 bits are the AI lane of the slice (nfs4.exe 0x41c550, 7 '
                'without the file; 1..10 in the NFS4 tracks), lanes numbered as in [Nfs4VRoadBlock](#nfs4vroadblock) '
                '(6 and 7 either side of the centre). When the file is short the game makes `line_offsets` from them '
                '(0x41e0d0: the lane centre, (lane - 6) x left lane width - width / 2 or (lane - 7) x right width + '
                'width / 2, kept 2 m inside the walls). The low 4 bits are 0 and not read'
            },
        )
        line_offsets = (
            ArrayBlock(child=DecimalBlock(length=4), length=(lambda ctx: len(ctx.data('lanes')), 'n')),
            {
                'description': 'Lateral offset of the AI line from the slice centre in meters (along the `right` '
                'vector of the vroad record), a float per slice (nfs4.exe 0x41c590, 0 without the file): read by the '
                'AI cars and by the car reset when no lane of the slice is free (0x448c20)'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer

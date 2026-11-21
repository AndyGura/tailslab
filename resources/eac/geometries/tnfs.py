from math import floor

from library.context import ReadContext, WriteContext
from library.exceptions import DataIntegrityException
from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    BytesBlock,
    DelegateBlock,
    BitFlagsBlock,
    FixedPointBlock,
    Padding,
    SubByteCompoundBlock,
    TrailingOptionalBlock,
    CountOf,
    OffsetOf,
    OwnSize,
)
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import NullTerminatedUTF8Block
from resources.eac.fields.byte_order import big_endian_copy, derive_fields
from resources.eac.fields.misc import Point3D
from resources.eac.psx import PsxCrcFooter, PsxItemCrcFooterMixin

# "Verified" in the descriptions below: read in the game code (TNFS DOS, PSX and Win95 SE executables, tnfs-1995
# Ghidra projects; DOS `gfx_oriload` 0xa1148, `gfx_orilocatemorph` 0xa14d0, `gfx_oriapplymorph` 0xa16a4,
# `gfx_ori_init_material_colours` 0xa0f98, `gfx_ori_sort_polys` 0xa1a00, `gfx_draw_car_model` 0x74766) or checked
# against every ORIP of the game files (CFM car models, FAM track props)


class OripPolygon(DeclarativeCompoundBlock):
    block_description = 'A geometry polygon'

    class Fields(DeclarativeCompoundBlock.Fields):
        polygon_type = (
            IntegerBlock(length=1),
            {
                'description': 'Polygon type (verified). Bits 0-2: number of vertices (3 triangle, 4 quad, 2 a line: '
                'the only ones in the game files are in the TR6 mine prop, the converter skips them). Bit 0x08: '
                'colour-keyed, texel 0xFF is transparent (else opaque). Bit 0x80: textured (else filled with the '
                "flat colour of the material). Bits 3-6 together pick the game's rasterizer. Values in the files: "
                '0x84 / 0x83 textured opaque quad / triangle, 0x8C / 0x8B textured colour-keyed quad / triangle, '
                '0x04 flat colour quad, 0x02 line'
            },
        )
        mapping = (
            BitFlagsBlock(
                length=1,
                flag_names=[
                    (0, 'two_sided'),
                    (1, 'flip_normal'),
                    (2, 'not_in_draw_list'),
                    (3, 'chain'),
                    (4, 'use_uv'),
                    (5, 'alt_rasterizer'),
                ],
            ),
            {
                'description': 'Polygon flags (verified): 0x01 `two_sided`, no backface culling; 0x02 '
                '`flip_normal`, reversed winding; 0x04 `not_in_draw_list`: not culled and left out of the default '
                'draw list (drawn only through a chain); 0x08 `chain`: after drawing this polygon the game draws '
                'the polygon whose index follows the vertex indices in `vmap` (vmap[offset_3d + vertex count]), '
                'only in the CY1 tunnel prop; 0x10 `use_uv`: has texture coordinates (without it `offset_2d` is '
                'garbage and the texture is mapped to the corners of the quad); 0x20 `alt_rasterizer`: another '
                'rasterizer, only in two polygons of the AL1 trestle prop'
            },
        )
        material_index = (
            IntegerBlock(length=1),
            {'description': "Index of the polygon's material in `materials` (verified)"},
        )
        unk = (
            IntegerBlock(length=1),
            {
                'description': 'Masked off and never read by the draw code (verified). Values 0, 1, 2, 4',
                'is_unknown': True,
            },
        )
        offset_3d = (
            IntegerBlock(length=4),
            {
                'description': 'Index in `vmap` of the first vertex index of this polygon: the polygon has as '
                'many vertices as bits 0-2 of `polygon_type` tell, their indices in `vertices` are the vmap items '
                'from this one on'
            },
        )
        offset_2d = (
            IntegerBlock(length=4),
            {
                'description': 'The same as offset_3d for texture coordinates: index in `vmap` of the index '
                'in `vertex_uvs` of the first vertex. Garbage when `use_uv` is off'
            },
        )


class OripVertexUV(DeclarativeCompoundBlock):
    inline_description = (
        'Texture coordinates for vertex, where each coordinate is: '
        + IntegerBlock(length=4).schema['block_description']
        + '. The unit is a pixels amount of assigned texture. So it should be changed when selecting '
        'texture with different size'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        u = IntegerBlock(length=4, is_signed=True)
        v = IntegerBlock(length=4, is_signed=True)


class OripMaterial(DeclarativeCompoundBlock):
    block_description = 'A material: FSH bitmap and flat colour of the polygons that use it'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            BytesBlock(length=8),
            {
                'description': 'Material name, 8 bytes, NUL-padded when shorter, empty in most materials. The game '
                'looks materials up by name (verified): `frntires` and `rertires` (the front and rear wheel quads, '
                'which get the animated tyre textures `tyr1`..`tyr4`), `tire1`..`tire4`. Other names in the files, '
                'never looked up: `pal`, `rtir1`..`rtir4` / `rty1`..`rty4` (Warrior rear tyres, never shown), '
                'traffic car part names (`side`, `front`, `rear`, `tires`...) and a few garbage values'
            },
        )
        file_name = (
            UTF8Block(length=4),
            {'description': 'Name of the bitmap in the FSH archive next to this ORIP (verified)'},
        )
        color = (
            IntegerBlock(length=3),
            {
                'description': 'Flat colour 0xRRGGBB (the game reads the 4 bytes as 0x00RRGGBB, little-endian), '
                'matched to the nearest palette entry; untextured polygons are filled with it (verified)'
            },
        )
        unknown_0x0f = (
            IntegerBlock(length=1),
            {
                'description': 'High byte of the colour, never read by the game (verified). 0, 0x80, 0x81 or 0x82 in '
                'the files',
                'is_unknown': True,
            },
        )
        unknown_0x10 = (
            IntegerBlock(length=4),
            {'description': 'Never read by the game (verified)', 'is_unknown': True},
        )


class OripMorph(DeclarativeCompoundBlock):
    block_description = (
        'A morph (verified): vertices moved by delta vectors times a weight, '
        '`vertex = base + round(delta * weight / 0x10000)` per component (weight in 16.16 fixed point, linear)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            UTF8Block(length=8),
            {
                'description': 'Morph name, 8 bytes without NUL: the game compares 8 characters of the names it '
                'looks up, `left_turn` and `right_turn`, so the files hold `left_tur` and `right_tu`'
            },
        )
        num_vertices = (IntegerBlock(length=4), {'description': 'Number of moved vertices'})
        vmap_offset = (
            IntegerBlock(length=4),
            {'description': 'Index in `vmap` where the indices (in `vertices`) of the moved vertices start'},
        )
        first_delta = (
            IntegerBlock(length=4),
            {
                'description': 'Index in `vertices` of the delta vector of the first moved vertex, the deltas of '
                'the others follow it in the order of the vertex indices in vmap. They have the format of vertices '
                'and are stored after the `num_shape_vrtx` shape vertices'
            },
        )


class OripPartition(DeclarativeCompoundBlock):
    block_description = (
        'A partition: a named list of polygons, depth-sorted and drawn as a whole. The game '
        'draws a car as its `inside`, then `surface`, then `outside` partition (verified), each sorted on its '
        'own and painted completely over the previous one: `inside` (the inner tyre faces `circ`, the tyre '
        "bottoms `shad`, the Warrior's `bott` and `tire`, some body parts) is always under the body, "
        '`outside` (the 4 wheel quads in every full car model) always over it'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            UTF8Block(length=8),
            {
                'description': 'Partition name. Every ORIP has `NON-SORT`, car models also `inside` and '
                '`surface`, full car models and the M*.CFM models `outside`, COPMUST `badge`. The game looks up '
                '`inside`, `surface`, `outside` and `convex` (never present); `NON-SORT` and `badge` are never drawn '
                'by the car code (verified)'
            },
        )
        unknown_0x08 = (
            IntegerBlock(length=4),
            {
                'description': 'Never read by the game (verified). 0, or a large value equal in all partitions of '
                "the model; in traffic and M*.CFM models `inside`'s is the others' + 1",
                'is_unknown': True,
            },
        )
        unknown_0x0c = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Never read by the game (verified). In the full car models 1 for `inside`, 0 for '
                '`surface`, -1 for `outside`; 0 in the other models (PICKUP: -1 for `surface`)',
                'is_unknown': True,
            },
        )
        polygons_start = (
            IntegerBlock(length=4),
            {'description': 'Index in `vmap` where the indices (in `polygons`) of the polygons of the partition start'},
        )
        num_polygons = (IntegerBlock(length=4), {'description': 'Number of polygons in the partition'})
        unknown_0x18 = (
            IntegerBlock(length=4),
            {'description': 'Never read by the game (verified), always 0', 'is_unknown': True},
        )


class NamedIndex(DeclarativeCompoundBlock):
    inline_description = (
        '12-bytes record, first 8 bytes is null-terminated UTF-8 string, last'
        ' 4 bytes is an unsigned integer (little-endian). Used by ORIP `fx_polys` (index is a vertex index) and '
        '`labels` (index is a polygon index)'
    )

    @property
    def size_doc_str(self):
        return '12'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            NullTerminatedUTF8Block(length=8, errors='surrogateescape'),
            {
                'description': 'Name of the entry (up to 7 bytes). A few entries have a garbage name, like the bytes '
                '80 02 of a DVIPER `fx_polys` entry (kept as is: a byte which is not UTF-8 is read as U+DC80..U+DCFF)'
            },
        )
        offset = ArrayBlock(
            child=IntegerBlock(length=1),
            length=(lambda ctx: 8 - ctx.buffer.tell() + ctx.read_start_offset, '7 - len(name)'),
            programmatic_value=lambda ctx: [0] * (7 - len(NamedIndex.name_bytes(ctx.data('name')))),
        )
        index = (IntegerBlock(length=4), {'description': 'Index of the vertex (`fx_polys`) or polygon (`labels`)'})

    @staticmethod
    def name_bytes(name: str) -> bytes:
        return name.encode('utf-8', errors='surrogateescape')

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        # always 12: `offset` is written from the name, whatever it was read with (ORIP `block_size` counts on it)
        return 12

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        if len(self.name_bytes(data['name'])) > 7:
            raise DataIntegrityException(
                f'Name "{data["name"]}" is longer than 7 bytes, the most a {name or "named index"} entry can hold',
                ctx=ctx,
            )
        return super().write(data, ctx, name)


# TODO check additional info in http://3dodev.com/documentation/file_formats/games/nfs
class OripGeometry(DeclarativeCompoundBlock):
    block_description = (
        'Geometry block for 3D model with few materials: TNFS car models (CFM) and track '
        'props (FAM). Exported to OBJ + MTL, and imported from them: the polygons, labels and partitions of the OBJ '
        'replace the geometry, the rest (material names and colours, morphs, fx points) follows the replaced '
        'model and the wheel quads'
    )
    serializer = 'OripGeometrySerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('ORIP'), length=4), {'description': 'Resource ID'})
        block_size = (
            IntegerBlock(length=4, programmatic_value=OwnSize()),
            {'description': 'Total ORIP block size in bytes'},
        )
        version = (
            IntegerBlock(length=4, value_validator=Eq(0x02BC)),
            {
                'description': 'Format version (verified): 700 (0x2BC) on PC, the game warns about any other value. '
                'The PSX version expects 800, the 3DO version reportedly has 500 (0x1F4)'
            },
        )
        instance_counter = (
            IntegerBlock(length=4, value_validator=Eq(0)),
            {
                'description': 'Number of instances of the model: zeroed by the game at load and incremented per '
                'instance at run time (verified). Always 0 in the files'
            },
        )
        num_vrtx = (
            IntegerBlock(length=4, programmatic_value=CountOf('vertices/data')),
            {'description': 'Number of items in `vertices`: the shape vertices and the morph delta vectors'},
        )
        num_shape_vrtx = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: (
                    len(ctx.data('vertices/data')) - sum(m['num_vertices'] for m in ctx.data('morphs'))
                ),
            ),
            {
                'description': 'Number of shape vertices: `vertices` without the morph delta vectors (`num_vrtx` - '
                'the vertices of all morphs). The game takes the bounding box of a car from these (verified)'
            },
        )
        vrtx_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('vertices')),
            {'description': 'An offset to vertices'},
        )
        num_uvs = (
            IntegerBlock(length=4, programmatic_value=CountOf('vertex_uvs')),
            {'description': 'Amount of vertex UV-s (texture coordinates). Not read by the game (verified)'},
        )
        uvs_ptr = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: 112 + len(ctx.data('polygons')) * 12),
            {'description': 'An offset to vertex_uvs. Always equals to `112 + num_polygons*12`'},
        )
        num_polygons = (
            IntegerBlock(length=4, programmatic_value=CountOf('polygons')),
            {'description': 'Amount of polygons'},
        )
        polygons_ptr = (
            IntegerBlock(length=4, is_signed=False, value_validator=Eq(112)),
            {'description': 'An offset to polygons block'},
        )
        name = (
            UTF8Block(length=12),
            {'description': 'Model name, like "_SUPRA" or "_TRESTLE". Never read by the game (verified)'},
        )
        num_materials = (
            IntegerBlock(length=4, programmatic_value=CountOf('materials')),
            {'description': 'Amount of materials'},
        )
        materials_ptr = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: 112 + len(ctx.data('polygons')) * 12 + len(ctx.data('vertex_uvs')) * 8,
            ),
            {'description': 'An offset to materials. Always equals to `112 + num_polygons*12 + num_uvs*8`'},
        )
        num_morphs = (
            IntegerBlock(length=4, programmatic_value=CountOf('morphs')),
            {'description': 'Amount of morphs'},
        )
        morphs_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('morphs')),
            {
                'description': 'An offset to morphs. Equals to `materials_ptr + num_materials*20`, except in the '
                'far model of LDIABLO.CFM (see `unk_morphs`)'
            },
        )
        num_partitions = (
            IntegerBlock(length=4, programmatic_value=CountOf('partitions')),
            {'description': 'Amount of partitions'},
        )
        partitions_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('partitions')),
            {'description': 'An offset to partitions. Always equals to `morphs_ptr + num_morphs*20`'},
        )
        vmap_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('vmap')),
            {'description': 'Offset of polygon_vertex_map block'},
        )
        num_fxp = (
            IntegerBlock(length=4, programmatic_value=CountOf('fx_polys')),
            {'description': 'Amount of items in fx_polys block'},
        )
        fxp_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('fx_polys')),
            {'description': 'Offset of fx_polys block. Always equals to `partitions_ptr + num_partitions*28`'},
        )
        num_lbl = (
            IntegerBlock(length=4, programmatic_value=CountOf('labels')),
            {'description': 'Amount of items in labels block'},
        )
        lbl_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('labels')),
            {'description': 'Offset of labels block. Always equals to `fxp_ptr + num_fxp*12`'},
        )
        num_jld = (
            IntegerBlock(length=4),
            {
                'description': 'Number of JLD items (verified: when not 0, the game allocates num_jld * 0x24 bytes of '
                'inverse matrices at `jld_runtime_ptr`, "InitJLD"). What JLD is is unknown. 0 in every file',
            },
        )
        jld_ptr = (
            IntegerBlock(length=4),
            {'description': 'Offset of the JLD items. 112 (the end of the header) in every file, where there are none'},
        )
        jld_runtime_ptr = (
            IntegerBlock(length=4),
            {'description': 'Run time pointer to the JLD inverse matrices (verified), 0 in the files'},
        )
        polygons = (
            ArrayBlock(child=OripPolygon(), length='num_polygons'),
            {
                'description': 'A block with polygons of the geometry. Probably should be a start point when '
                'building model from this file'
            },
        )
        unk_uvs = (
            Padding(to='uvs_ptr'),
            {'description': 'Padding up to `uvs_ptr`, normally empty'},
        )
        vertex_uvs = (
            ArrayBlock(child=OripVertexUV(), length='num_uvs'),
            {'description': 'A table of texture coordinates. Items are retrieved by index, located in vmap'},
        )
        unk_materials = (
            Padding(to='materials_ptr'),
            {'description': 'Padding up to `materials_ptr`, normally empty'},
        )
        materials = (
            ArrayBlock(child=OripMaterial(), length='num_materials'),
            {'description': 'A table of materials. Items are retrieved by index, located in polygon item'},
        )
        unk_morphs = (
            Padding(to='morphs_ptr', allow_negative_length=True),
            {
                'description': 'Padding up to `morphs_ptr`, empty in every file but one: in the far model of '
                'LDIABLO.CFM (no morphs) its length is -3, the morph and partition tables start 3 bytes before the '
                'end of the materials, so the last 3 bytes of the materials are the start of the first partition '
                'name. Written back as 0 bytes, so that model is not written byte-exact'
            },
        )
        morphs = (
            ArrayBlock(child=OripMorph(), length='num_morphs'),
            {
                'description': 'Morphs (verified). Only full car models have them: `left_turn` and `right_turn`, '
                'each moving the 4 vertices of its front wheel quad (labels `lt_frnt` / `rt_frnt`) and the 4 of '
                "that wheel's inner `circ` quad (TRAFFC, WARRIOR, WARIOR: the wheel quad only), no body vertex. "
                'Both turn their wheel left at a positive weight. The game applies the weight '
                '-steer_angle / 0x200000 (weight 1.0 is about 30 degrees of wheel turn), `left_turn` only when the '
                "camera sees the car's left side, `right_turn` only the right side. The gg-web-engine export writes "
                'them as glTF morph targets `left_turn` / `right_turn` of the meshes with moved vertices'
            },
        )
        unk_partitions = (
            Padding(to='partitions_ptr'),
            {'description': 'Padding up to `partitions_ptr`, normally empty'},
        )
        partitions = (
            ArrayBlock(child=OripPartition(), length='num_partitions'),
            {
                'description': 'Partitions, the draw order of the polygons (verified). The gg-web-engine export '
                'writes the partition of each mesh (`inside`, `surface` or `outside`) to its node extras '
                '(`partition`)'
            },
        )
        unk_fxp = (
            Padding(to='fxp_ptr'),
            {'description': 'Padding up to `fxp_ptr`, normally empty'},
        )
        fx_polys = (
            ArrayBlock(child=NamedIndex(), length='num_fxp'),
            {
                'description': 'Named points of the model for visual effects, in high-poly car models (CFM). Despite '
                'the name, `index` is the index of an item of `vertices`, not of a polygon. The game looks up `smok` '
                'and `fl0`, `fl1`, `fr0`, `fr1`, `rl0`, `rl1`, `rr0`, `rr1`, ignoring case (verified; F512M, F512TR, '
                'TRAFFC and WARRIOR use lower case, the other cars upper case). `FL0`..`RR1` are the ground contact '
                'points of the wheels (front/rear, left/right), 0 at the front edge of the wheel, 1 at the rear '
                'edge (the bottom corners of the wheel polygon labelled `lt_frnt`, `rt_rear`...); guess: sources of '
                'tyre smoke, dust and skid marks. `smok` is a point at the engine: on the hood of front-engined '
                'cars (DVIPER, CZR1, MRX7, TSUPRA), at the exhaust or the engine lid of the others; guess: source '
                'of engine smoke and fire of a wrecked car. Never looked up: `d` (only in the M*.CFM models, a point '
                'near the bottom of the front left wheel) and the garbage name (bytes 80 02) of one more DVIPER entry '
                '(the top of a wheel polygon). The gg-web-engine export writes every entry as a dummy "fx_<name>" at '
                'the vertex, with properties `fx` (the name) and `vertex` (the index), skipping entries with a name '
                'which is not printable ASCII'
            },
        )
        unk_lbl = (
            Padding(to='lbl_ptr'),
            {'description': 'Padding up to `lbl_ptr`, normally empty'},
        )
        labels = (
            ArrayBlock(child=NamedIndex(), length='num_lbl'),
            {
                'description': 'Named polygons of high-poly car models (CFM), `index` is the index of an item of '
                '`polygons`. The game looks up `lt_frnt`, `rt_frnt`, `lt_rear`, `rt_rear` only (verified): the '
                'outer side of the wheels (left/right, front/rear), quads of the `outside` partition with the '
                'materials `frntires` / `rertires`, which get the animated tyre textures. Never looked up: '
                '`bkll` / `bklr` (left / right rear light), `bott` (a horizontal quad over the whole underside of '
                'the body of the simple traffic car models, texture `bott`), `bacr` (P911, the centre part of the '
                'rear light bar), `mm` (LDIABLO; garbage name, bytes e0 01, on the same polygon of LDIABL, left out of the exported mesh '
                'names: a two-sided quad at the inner side of the front right wheel, texture `circ`), `W` (TRAFFC, WARRIOR: a triangle '
                'at the top rear left corner of the body, texture `abox`) and the COPMUST lights `hll0` / `hlr0` '
                '(headlights), `bkl0` / `bkr0` (rear lights), `lfl0` / `lfr0` and `lrl0` / `lrr0` (front and rear '
                'left / right parts of the siren light bar on the roof). Brake and siren lights are palette '
                'animations in the game, not label lookups (verified): the brake light is one palette entry, lit '
                'when the brake is at 11 or more; the siren swaps the 4 palette entries from 0xFA every 16 clock '
                'units. Parts known by their texture: `circ`, four two-sided colour-keyed quads at the inner side '
                'of the tyres (`inside` partition); `shad`, two vertical two-sided colour-keyed quads across the car '
                'at each axle (from the ground up to 0.24 m, 4x1 texture, no UVs), not the shadow of the car (the '
                'game draws that as a separate flat quad on the road); guess: the tyre bottoms seen from the front '
                'and the rear'
            },
        )
        unk_vrtx = (
            Padding(to='vrtx_ptr'),
            {'description': 'Padding up to `vrtx_ptr`, normally empty'},
        )
        vertices = (
            DelegateBlock(
                choice_index=lambda ctx, **_: 0 if ctx.buffer.name.endswith('.CFM') else 1,
                possible_blocks=[
                    ArrayBlock(
                        child=Point3D(child=FixedPointBlock(length=4, fraction_bits=7, is_signed=True)),
                        length='num_vrtx',
                    ),
                    ArrayBlock(
                        child=Point3D(child=FixedPointBlock(length=4, fraction_bits=4, is_signed=True)),
                        length='num_vrtx',
                    ),
                ],
            ),
            {
                'description': 'A table of mesh vertices 3D coordinates. For cars uses 32:7 points, else 32:4. '
                'The unit is meter. The first `num_shape_vrtx` items are the vertices of the model, the others are '
                'the delta vectors of the morphs'
            },
        )
        unk_vmap = (
            Padding(to='vmap_ptr'),
            {'description': 'Padding up to `vmap_ptr`, normally empty'},
        )
        vmap = (
            ArrayBlock(
                child=IntegerBlock(length=4),
                length=(
                    lambda ctx: floor((ctx.data('block_size') + ctx.read_start_offset - ctx.buffer.tell()) / 4),
                    '?',
                ),
            ),
            {
                'description': 'A table of indices the other blocks point into: the vertex indices (in `vertices`) '
                'and texture coordinate indices (in `vertex_uvs`) of the polygons (`offset_3d`, `offset_2d`), the '
                'indices of chained polygons, the moved vertices of the morphs and the polygon lists of the '
                'partitions'
            },
        )


# "Verified" in the ORIX descriptions below: read in the PSX executable (SLUS-00204, tnfs-1995 Ghidra project:
# `oriload` 0x80081610, `tnfs_ori_inst` 0x800819ac, `orisetdefaulmaterialtextures` 0x80081e28, `buildprimlist`
# 0x80084c08, material texture setter 0x80085e74, car model setup 0x8004ea54, car texture upload 0x8004e72c,
# `gfx_draw_car_model` 0x80050024) or checked against every ORIX of the game files (62 car models, 37 track props)


class OrixPolygon(DeclarativeCompoundBlock):
    block_description = (
        'A polygon of a PSX geometry: the ORIP polygon with the type of the GPU primitive the game draws it with'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        polygon_type = (
            IntegerBlock(length=1),
            {
                'description': 'Polygon type, as in ORIP: bits 0-2 number of vertices, bit 0x08 colour-keyed, bit 0x80 '
                'textured. The PSX draw code reads only bits 0x78 (verified): 0x10 or 0x18 there makes the polygon '
                'semi-transparent (`buildprimlist` SLUS_002.04 0x80084c08 / SLPS_010.24 0x80082a80 sets the GPU '
                "packet's ABE bit, SetSemiTrans FUN_80091050); `draw_type` picks the primitive, and the GPU skips "
                'texels of colour 0x0000 on every textured one. Values in the files: 0x84 and 0x8C (quads), in the '
                "Japanese disc's cars also 0x04 and 0x03 (the windows): none semi-transparent"
            },
        )
        mapping = (
            OripPolygon.Fields.mapping[0],
            {
                'description': 'Polygon flags, as in ORIP (verified): `two_sided` or `not_in_draw_list` = no backface '
                'culling, `flip_normal` = reversed winding, `use_uv` = has texture coordinates (without it the '
                'texture is mapped to the corners of the quad: vertex 0 to its top left texel, 1 top right, 2 bottom '
                'right, 3 bottom left). Bit 0x40 (`6`): Gouraud-shaded, read by the loader of the Japanese disc only '
                "(Over Drivin' Skyline Memorial, SLPS_010.24 FUN_8007f358, the US `oriload` has no such code): such a "
                'polygon, and one of draw type 10, gets draw type 8 (a triangle, untextured), 15 (draw type below 12) '
                "or 16 at load, and the colours of its record in the `<car>.GRO` next to the model (its material's "
                "`color` without one). Set on most polygons of the Japanese disc's high-poly cars, nowhere in the US "
                'disc'
            },
        )
        material_index = (
            IntegerBlock(length=1),
            {'description': "Index of the polygon's material in `materials` (verified)"},
        )
        unk = (IntegerBlock(length=1), {'description': 'Always 0', 'is_unknown': True})
        draw_type = (
            IntegerBlock(length=4),
            {
                'description': 'GPU primitive of the polygon (verified, the low byte is read): 5 textured triangle, 9 '
                'Gouraud-shaded textured triangle, 12 textured quad, 16 Gouraud-shaded textured quad; 1 / 2 lines, 3 / '
                '8 untextured triangles and 10 untextured quad are not drawn (the game only prints their names). '
                "Always 12 in the US files. The Japanese disc's high-poly cars also have 10 and 3 (their untextured "
                'windows, material `window`), which its loader turns into 15 (Gouraud-shaded untextured quad) and 8 '
                '(see `mapping` bit 0x40); it fills the colours of the GPU packets of draw types 8, 15 and 16 from '
                '`<car>.GRO` (SLPS_010.24 FUN_80084944)'
            },
        )
        offset_3d = OripPolygon.Fields.offset_3d
        offset_2d = OripPolygon.Fields.offset_2d


class OrixPolygonTexture(DeclarativeCompoundBlock):
    inline_description = (
        'Texture of one polygon (verified): the PSX version cuts the texture of a material '
        'into one small image per polygon'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        polygon_index = (IntegerBlock(length=4), {'description': 'Index of the polygon in `polygons`'})
        file_name = (
            UTF8Block(length=4),
            {
                'description': 'Name of the image in the PSH archive next to this ORIX (`J000`, `J001`...). Mirrored '
                'polygons of the left and right side share an image'
            },
        )


class OrixMaterial(DeclarativeCompoundBlock):
    block_description = (
        'A material of a PSX geometry: the image of the polygons that use it, or the list of their own images'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            BytesBlock(length=8),
            {
                'description': 'Material name, 8 bytes, NUL-padded when shorter, empty in most materials. The game '
                'looks up `frntires` and `rertires` (the wheel quads, which get the tyre textures `tyr1`..`tyr4`) '
                'and `tire1`..`tire4` (verified)'
            },
        )
        file_name = (
            UTF8Block(length=4),
            {
                'description': 'Name of the image in the PSH archive next to this ORIX, used when '
                '`per_polygon_textures` is off (verified). With it on: the name of the PC texture that was cut into '
                'the polygon images, or garbage. Empty in `frntires` / `rertires` of most cars: the game sets their '
                'texture at run time'
            },
        )
        textures = (
            SubByteCompoundBlock(
                length=4,
                schema=[
                    (10, 'unknown', 'number', [], 'Bit 22 is set in every material of some models, never read'),
                    (
                        10,
                        'num_polygon_textures',
                        'number',
                        [],
                        'Number of items of `polygon_textures` of this material',
                    ),
                    (
                        10,
                        'first_polygon_texture',
                        'number',
                        [],
                        'Index of the first item of this material in `polygon_textures`. Set in every material, '
                        'also the ones without items',
                    ),
                    (
                        1,
                        'per_polygon_textures',
                        'boolean',
                        [],
                        'The polygons of the material have their own images, listed in `polygon_textures`',
                    ),
                    (1, 'unknown_bit_0', 'boolean', [], 'Always set, never read'),
                ],
            ),
            {'description': 'Where the textures of the polygons come from (verified)'},
        )
        color = (
            IntegerBlock(length=4),
            {
                'description': 'Colour 0x00RRGGBB: the corner colour of the polygons of the material drawn with Gouraud '
                'colours which have no record in `<car>.GRO` (the instance setup SLPS_010.24 FUN_8007fe30 / '
                'SLUS_002.04 FUN_80082128 hands it to FUN_80084944 / FUN_80086948; see `draw_type` of '
                "[OrixPolygon](#orixpolygon)). 0 in every US file, different per material in the Japanese disc's "
                "high-poly cars (`window` 0x0096c8, the KHGC211's `Number` 0: its plate drawn black)"
            },
        )
        unknown_0x14 = (
            IntegerBlock(length=4),
            {
                'description': 'Never read by the game (verified). One value per model, the same in all of its '
                'materials',
                'is_unknown': True,
            },
        )


class OrixGeometry(PsxItemCrcFooterMixin, DeclarativeCompoundBlock):
    block_description = (
        'Geometry block of the PSX TNFS: car models (`<car>.por` / `<car>l.por` of the car '
        'archives `.VSM` / `.WSM`) and track props (`Z<track>_POR.FAM`). The PSX counterpart of ORIP: the same '
        'header with 8 more bytes, 16-byte polygons, 24-byte materials and a table of per-polygon textures. '
        'Textures are the images of the PSH archive of the same name in the car archive (`<car>.psh`, the item '
        'after it in the US disc; in a `_POR.FAM`: the item of the same index in `Z<track>_PSH.FAM`); the wheel '
        'quads (materials `frntires` / `rertires`) get the texture of material `tire4` at load (`tyr4`, `Tir4` '
        'in the Japanese disc). Brake lights are no part of the model: in the high-poly '
        'textures of a racer the game takes every CLUT entry of pure green (5-bit red < 2, green > 29, blue < '
        '2, at most 5) and writes 0x0008 (dark red) to it, 0x001F (red) while the brake is at 11 or more; the '
        "cop's pure red and pure blue entries exchange red (0x001F) and blue (0x7C00) every 16 clock units "
        'during a chase (verified). Exported to OBJ + MTL'
    )
    serializer = 'OrixGeometrySerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('ORIX'), length=4), {'description': 'Resource ID'})
        block_size = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: ctx.block.size_without_footer(ctx.get_full_data())),
            {'description': 'Total ORIX block size in bytes, without the CRC footer'},
        )
        version = (
            IntegerBlock(length=4, value_validator=Eq(800)),
            {'description': 'Format version (verified): 800, the game warns about any other value (PC ORIP: 700)'},
        )
        instance_counter = (
            IntegerBlock(length=4),
            {
                'description': 'Number of instances of the model: zeroed by the game at load and incremented per '
                'instance at run time (verified). The files have leftovers of a path string here (`SX_C`, `IPER`...)'
            },
        )
        num_vrtx = OripGeometry.Fields.num_vrtx
        num_shape_vrtx = (
            OripGeometry.Fields.num_shape_vrtx[0],
            {
                'description': 'Number of shape vertices: `vertices` without the morph delta vectors (`num_vrtx` - '
                'the vertices of all morphs)'
            },
        )
        vrtx_ptr = OripGeometry.Fields.vrtx_ptr
        num_uvs = (
            IntegerBlock(length=4, programmatic_value=CountOf('vertex_uvs')),
            {'description': 'Amount of vertex UV-s (texture coordinates)'},
        )
        uvs_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('vertex_uvs')),
            {'description': 'An offset to vertex_uvs'},
        )
        num_polygons = OripGeometry.Fields.num_polygons
        polygons_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('polygons')),
            {'description': 'An offset to polygons block. Always equals to `120 + num_polygon_textures*8`'},
        )
        name = (
            UTF8Block(length=12),
            {'description': 'Model name, like "_SUPRA", "_TINYSUPR" (low-poly) or "_TRESTLE". Never read by the game'},
        )
        num_materials = OripGeometry.Fields.num_materials
        materials_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('materials')),
            {'description': 'An offset to materials. Always equals to `uvs_ptr + num_uvs*8`'},
        )
        num_morphs = OripGeometry.Fields.num_morphs
        morphs_ptr = (
            OripGeometry.Fields.morphs_ptr[0],
            {'description': 'An offset to morphs. Always equals to `materials_ptr + num_materials*24`'},
        )
        num_partitions = OripGeometry.Fields.num_partitions
        partitions_ptr = OripGeometry.Fields.partitions_ptr
        vmap_ptr = OripGeometry.Fields.vmap_ptr
        num_fxp = OripGeometry.Fields.num_fxp
        fxp_ptr = OripGeometry.Fields.fxp_ptr
        num_lbl = OripGeometry.Fields.num_lbl
        lbl_ptr = OripGeometry.Fields.lbl_ptr
        num_jld = (
            IntegerBlock(length=4),
            {
                'description': 'Number of JLD items (verified: when not 0, the game allocates num_jld * 0x24 bytes '
                '"INVMATRX" at `jld_runtime_ptr`). 0 in every file',
            },
        )
        jld_ptr = (
            IntegerBlock(length=4, programmatic_value=OffsetOf('polygons')),
            {'description': 'Offset of the JLD items. Equals to `polygons_ptr` in every file, where there are none'},
        )
        num_polygon_textures = (
            IntegerBlock(length=4, programmatic_value=CountOf('polygon_textures')),
            {'description': 'Amount of items in polygon_textures block'},
        )
        polygon_textures_ptr = (
            IntegerBlock(length=4, value_validator=Eq(120)),
            {'description': 'Offset of polygon_textures block (the end of the header)'},
        )
        jld_runtime_ptr = (
            IntegerBlock(length=4),
            {'description': 'Run time pointer to the JLD inverse matrices (verified), 0 in the files'},
        )
        polygon_textures = (
            ArrayBlock(child=OrixPolygonTexture(), length='num_polygon_textures'),
            {
                'description': 'Images of single polygons, grouped by material: a material with '
                '`per_polygon_textures` has `num_polygon_textures` items from `first_polygon_texture` on (verified). '
                'Polygons of other materials have none'
            },
        )
        polygons = (
            ArrayBlock(child=OrixPolygon(), length='num_polygons'),
            {'description': 'A block with polygons of the geometry'},
        )
        vertex_uvs = (
            ArrayBlock(child=OripVertexUV(), length='num_uvs'),
            {
                'description': 'A table of texture coordinates, in texels of the image as shown (the game turns '
                'them for an image stored rotated, and clamps them to the image; verified). Items are retrieved by '
                'index, located in vmap. Only polygons with `use_uv` have them: the low-poly models and a few '
                'polygons of the others'
            },
        )
        materials = (
            ArrayBlock(child=OrixMaterial(), length='num_materials'),
            {'description': 'A table of materials. Items are retrieved by index, located in polygon item'},
        )
        morphs = (
            ArrayBlock(child=OripMorph(), length='num_morphs'),
            {
                'description': 'Morphs, as in ORIP: `left_turn` and `right_turn` of the racer models, the front '
                "wheel steering. The game applies them to the player's car only (verified)"
            },
        )
        partitions = (
            ArrayBlock(child=OripPartition(), length='num_partitions'),
            {
                'description': 'Partitions, as in ORIP: the game draws `inside`, then `surface`, then `outside` '
                '(then `convex`, never present), each depth-sorted on its own (verified)'
            },
        )
        fx_polys = (
            ArrayBlock(child=NamedIndex(), length='num_fxp'),
            {
                'description': 'Named vertices, as in ORIP: the game looks up `smok` and the wheel ground points '
                "`FL0`..`RR1` of the player's car (verified)"
            },
        )
        labels = (
            ArrayBlock(child=NamedIndex(), length='num_lbl'),
            {
                'description': 'Named polygons, as in ORIP: the game looks up the wheel quads `lt_frnt`, `rt_frnt`, '
                "`lt_rear`, `rt_rear` of the player's car (verified)"
            },
        )
        vertices = (
            DelegateBlock(
                choice_index=lambda ctx, **_: (
                    0 if str(getattr(ctx.buffer, 'name', '')).upper().endswith(('.VSM', '.WSM', '.POR')) else 1
                ),
                possible_blocks=[
                    ArrayBlock(
                        child=Point3D(child=FixedPointBlock(length=4, fraction_bits=7, is_signed=True)),
                        length='num_vrtx',
                    ),
                    ArrayBlock(
                        child=Point3D(child=FixedPointBlock(length=4, fraction_bits=4, is_signed=True)),
                        length='num_vrtx',
                    ),
                ],
            ),
            {
                'description': 'A table of mesh vertices 3D coordinates, as in ORIP: for cars 32:7 points, else '
                '32:4, in meters (the game reads the low 16 bits of each coordinate; verified). The first '
                '`num_shape_vrtx` items are the vertices of the model, the others are the delta vectors of the morphs'
            },
        )
        vmap = (
            ArrayBlock(
                child=IntegerBlock(length=4),
                length=(
                    lambda ctx: floor((ctx.data('block_size') + ctx.read_start_offset - ctx.buffer.tell()) / 4),
                    '?',
                ),
            ),
            {
                'description': 'A table of indices the other blocks point into, as in ORIP: vertex and texture '
                'coordinate indices of the polygons, the moved vertices of the morphs and the polygon lists of the '
                'partitions'
            },
        )
        crc_footer = (
            TrailingOptionalBlock(child=PsxCrcFooter()),
            {
                'usage': 'ui,doc',
                'description': 'CRC footer after the ORIX (`block_size` does not count it) in a car archive item: '
                'inside a FAM archive it follows the last item of the FAM',
            },
        )


# "Checked" in the Saturn descriptions below: against every ORIX of Over Drivin' GT-R (the 8 cars' high and low-poly
# models, `games/tnfs_saturn_gtr/MODELS`, sliced from the executable). The field meanings are the PSX ORIX's, verified
# in the PSX executable; the Saturn executable is not disassembled


class TnfsSaturnOrixPolygon(DeclarativeCompoundBlock):
    block_description = (
        'A polygon of a Sega Saturn geometry: the PSX ORIX polygon, its first 8 bytes in reverse '
        'order (the GPU primitive word first, then the bytes `unk`, `material_index`, `mapping`, `polygon_type`), '
        'the offsets big-endian'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        draw_type = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'The PSX GPU primitive of the polygon (`OrixPolygon.draw_type`): 12 in every file (checked)'
            },
        )
        unk = (IntegerBlock(length=1), {'description': 'Always 0 (checked)', 'is_unknown': True})
        material_index = (
            IntegerBlock(length=1),
            {'description': "Index of the polygon's material in `materials`"},
        )
        mapping = (
            OripPolygon.Fields.mapping[0],
            {
                'description': 'Polygon flags, as in ORIP / ORIX: `two_sided`, `flip_normal`, `use_uv`... Values 0..3 '
                'in the files (checked)'
            },
        )
        polygon_type = (
            IntegerBlock(length=1),
            {
                'description': 'Polygon type, as in ORIP / ORIX: bits 0-2 number of vertices, bit 0x08 colour-keyed, bit '
                '0x80 textured. 0x84 and 0x8C (quads) in the files (checked)'
            },
        )
        offset_3d = (IntegerBlock(length=4, byte_order='big'), OripPolygon.Fields.offset_3d[1])
        offset_2d = (IntegerBlock(length=4, byte_order='big'), OripPolygon.Fields.offset_2d[1])


class TnfsSaturnOrixMaterial(DeclarativeCompoundBlock):
    block_description = 'A material of a Sega Saturn geometry: the PSX ORIX material, big-endian'

    class Fields(DeclarativeCompoundBlock.Fields):
        name = (
            OrixMaterial.Fields.name[0],
            {
                'description': 'Material name, 8 bytes, NUL-padded when shorter: `frntires` and `rertires` (the wheel '
                'quads), `tire1`..`tire4` (their textures `Tir1`..`Tir4`, `Tyr1`..`Tyr4` in the PGC10), part names of '
                'the body (`side`, `top`, `front`, `rear`, `bottom`, `Circ`, `Shad`, `Topp`, `Wing`, `Numb`...) or '
                'empty (low-poly). The executable holds the names `frntires`, `rertires` and `tire1`..`tire4` next '
                'to the model loader strings (0x223e4, 0x222c4..0x222d4): the names it looks up'
            },
        )
        file_name = (
            OrixMaterial.Fields.file_name[0],
            {
                'description': 'Name of the texture in the texture bank of the car (`CARS/<car>.ALL`: the first bank for '
                'the high-poly model, the second for the low-poly one), used when `per_polygon_textures` is off: '
                '`Tir1`..`Tir4` for `tire1`..`tire4`. With it on: a part name (`Side`, `Topp`, `Undr`...). Empty in '
                '`frntires` / `rertires`: the wheels get a tyre texture at run time'
            },
        )
        textures = (
            big_endian_copy(OrixMaterial.Fields.textures[0]),
            {'description': 'Where the textures of the polygons come from, as in the PSX ORIX (big-endian bit field)'},
        )
        unknown_0x10 = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'A colour 0x00RRGGBB per material, different in most materials of a model (grey `Shad`, '
                'red `front`, green `rear`, yellow `top`...; 0 in the tyre and the low-poly materials): the colour '
                'of the PC ORIP material, it seems. Not known whether the Saturn game reads it (0 in every US PSX ORIX, the '
                "Gouraud polygons' colour in the Japanese PSX disc, `color` of the PSX `OrixMaterial`)",
                'is_unknown': True,
            },
        )
        unknown_0x14 = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'Values 0..0xF3, mostly different per material (one value per model in the PSX ORIX)',
                'is_unknown': True,
            },
        )


def _tnfs_saturn_orix_fields():
    # PSX ORIX layout, big-endian: own polygons, materials and descriptions, 32:7 vertices, no CRC footer
    replaced = {
        'version': (
            IntegerBlock(length=4, byte_order='big', value_validator=Eq(800)),
            {'description': 'Format version: 800 (0x320), as on PSX'},
        ),
        'instance_counter': (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'Number of instances of the model at run time (as on PSX). The files have leftovers of a '
                'text here (`RAC_`, `NIT\\`, `LIS\\`, `003\\`)'
            },
        ),
        'name': (
            UTF8Block(length=12),
            {
                'description': 'Model name: "_KBNR32B", "_BCNR33W", "_PGC10S"... (high-poly), "_T" + a short name '
                '("_TBCNRW", "_T180SXR") for the low-poly ones'
            },
        ),
        'polygon_textures': (
            ArrayBlock(child=big_endian_copy(OrixPolygonTexture()), length='num_polygon_textures'),
            {
                'description': 'Textures of single polygons, grouped by material, as in the PSX ORIX: a material with '
                '`per_polygon_textures` has `num_polygon_textures` items from `first_polygon_texture` on. The names '
                '(`J000`, `J001`...) are textures of the texture bank of the car (`CARS/<car>.ALL`: the first bank for '
                'the high-poly model, the second for the low-poly one); polygons of the left and right side share a '
                'texture'
            },
        ),
        'polygons': (
            ArrayBlock(child=TnfsSaturnOrixPolygon(), length='num_polygons'),
            {'description': 'A block with polygons of the geometry'},
        ),
        'vertex_uvs': (
            big_endian_copy(OrixGeometry.Fields.vertex_uvs[0]),
            {'description': 'A table of texture coordinates, as in the PSX ORIX. Empty in every file (checked)'},
        ),
        'materials': (
            ArrayBlock(child=TnfsSaturnOrixMaterial(), length='num_materials'),
            {'description': 'A table of materials. Items are retrieved by index, located in polygon item'},
        ),
        'morphs': (
            big_endian_copy(OrixGeometry.Fields.morphs[0]),
            {
                'description': 'Morphs, as in ORIP / ORIX: `left_turn` and `right_turn` (the files hold `left_tur` and '
                '`right_tu`; the executable has the strings `left_turn` / `right_turn`, 0x22410) of the high-poly '
                'models, each moving 8 vertices: the front wheel steering. None in the low-poly models'
            },
        ),
        'partitions': (
            big_endian_copy(OrixGeometry.Fields.partitions[0]),
            {
                'description': 'Partitions, as in ORIP / ORIX: high-poly models have `NON-SORT` (empty), `inside`, '
                '`surface` and `outside` (the 4 wheel quads and a few body parts), low-poly models `NON-SORT` with every '
                'polygon (checked). The executable has the names `inside`, `surface`, `outside`, `convex` (0x223ac)'
            },
        ),
        'fx_polys': (
            big_endian_copy(OrixGeometry.Fields.fx_polys[0]),
            {
                'description': 'Named vertices, as in ORIP / ORIX: the wheel ground points `fl0`..`rr1` (lower case) '
                'and the engine point `smok` of the high-poly models (checked; the executable has these names, '
                '0x222fc..0x2231c and 0x22428, and the message "!!! error not Found wheel points")'
            },
        ),
        'labels': (
            big_endian_copy(OrixGeometry.Fields.labels[0]),
            {
                'description': 'Named polygons, as in ORIP / ORIX: the wheel quads `lt_frnt`, `rt_frnt`, `lt_rear`, '
                '`rt_rear` (names the executable holds, 0x222dc..0x222f4), the rear lights `bkll` / `bklr` (not in '
                'the executable: the game does not look them up) and in some models one part name per body polygon '
                '(`Side`, `Topp`, `Undr`, `Circ`, `Shad`, `Frnt`, `Rear`, `Nmbr`, `Pnl1`, `Pnl2`, `Wing`, `Mark`, '
                '`Numb`, `Bmpf`; the low-poly models of some cars too). Faults in the files (checked): the PGC10 '
                '(`SUPRA`) labels its left front wheel `rt_frnt` too (two `rt_frnt`, no `lt_frnt`); the BCNR33 '
                '(`DIABLO`) has a garbage name (bytes e0 01) on polygon 29, `bklr` in the BNR32. The gg-web-engine '
                'export names each wheel by its position (see `TnfsSaturnOrixGeometrySerializer`)'
            },
        ),
        'vertices': (
            DelegateBlock(
                choice_index=lambda ctx, **_: 0,
                possible_blocks=[
                    ArrayBlock(
                        child=Point3D(
                            child=FixedPointBlock(length=4, fraction_bits=7, is_signed=True, byte_order='big')
                        ),
                        length='num_vrtx',
                    ),
                ],
            ),
            {
                'description': 'A table of mesh vertices 3D coordinates: 32:7 points (1/128 m units, the BNR32 is 584 '
                'units = 4.56 m long), big-endian. The first `num_shape_vrtx` items are the vertices of the model, the '
                'others are the delta vectors of the morphs. X right, Y up, Z forward (the wheel points `fl*` at '
                'negative x and positive z)'
            },
        ),
    }
    return derive_fields(OrixGeometry.Fields, replace=replaced, drop={'crc_footer'})


class TnfsSaturnOrixGeometry(OrixGeometry):
    block_description = (
        "Car model of the Sega Saturn TNFS port Over Drivin' GT-R: the PSX ORIX, big-endian (SH-2), "
        'version 800, without the CRC footer, with its own polygon and material layouts (`TnfsSaturnOrixPolygon`, '
        '`TnfsSaturnOrixMaterial`). The models are not files of the disc: the executable `0` holds them (pointer '
        'table at 0x84f14: 9 high-poly models, the 8 cars and the Warrior, 13 zeros, the 9 low-poly ones; car '
        'model ids 0..7 = the PC car order SUPRA, DIABLO, PORSCHE, VETTE, TESTA, VIPER, NSX, RX7), sliced to '
        "`MODELS/<car>/high.orix` / `low.orix`. Textures: the texture banks of the car's `CARS/<car>.ALL` "
        '(`TnfsSaturnCarBundle`). Exported to OBJ + MTL / gg-web-engine GLB as the PC and PSX models'
    )

    Fields = _tnfs_saturn_orix_fields()
    serializer = 'TnfsSaturnOrixGeometrySerializer'

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        return DeclarativeCompoundBlock.read(self, ctx, name, read_bytes_amount)

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        return DeclarativeCompoundBlock.write(self, data, ctx, name)

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return DeclarativeCompoundBlock.estimate_packed_size(self, data, ctx)

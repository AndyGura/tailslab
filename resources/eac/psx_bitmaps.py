"""
Images of the PlayStation TNFS (SLUS-00204) `SHPP` archives (`.PSH` files): the PSX counterpart of the PC `EacImage` /
`EacPalette`. Pixels are kept as stored (VRAM rows); `serializers.bitmaps.PsxImageSerializer` decodes them.

Read by the PSX texture loader FUN_80044330 (looks the image up by name in the SHPP directory, `tnfs_front_image`
0x80010334), which uploads it to VRAM (FUN_800b5628) with its CLUT in a slot it allocates (FUN_80044794) and builds the
UVs of a POLY_FT4 for it.
"""

from io import SEEK_CUR
from typing import Dict

from library.context import ReadContext
from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    EnumByteBlock,
    IntegerBlock,
    TrailingOptionalBlock,
)
from library.read_blocks.misc.value_validators import Eq
from library.utils import transform_bitness
from resources.eac.fields.misc import Point2D

PSX_IMAGE_IDS = [(0x40, '4Bit PSX'), (0x41, '8Bit PSX'), (0x42, '16Bit PSX')]
PSX_CLUT_ID = 0x23
PSX_BITS_PER_PIXEL = {'4Bit PSX': 4, '8Bit PSX': 8, '16Bit PSX': 16}
# bit of `vram_x` (and `vram_y`): the image is stored rotated (`PsxImage.vram_x`)
PSX_VRAM_ROTATED = 0x4000
PSX_VRAM_COORDINATE_MASK = 0x3FFF


def psx_row_bytes(resource_id, width: int) -> int:
    """Bytes of one pixel row: VRAM rows are whole 16-bit words"""
    bits = PSX_BITS_PER_PIXEL.get(resource_id, 0)
    return (width * bits + 15) // 16 * 2


def psx_color_to_rgba(color: int) -> int:
    """A PSX 16-bit color (bits 0-4 red, 5-9 green, 10-14 blue, 15 STP) as RGBA (0xRRGGBBAA). 0x0000 is transparent:
    the GPU does not draw texels of that value on any textured primitive. Every other value is opaque (STP makes a
    texel semi-transparent only on primitives drawn semi-transparent, which the image does not tell)"""
    if color == 0:
        return 0
    red = transform_bitness(color, 5)
    green = transform_bitness(color >> 5, 5)
    blue = transform_bitness(color >> 10, 5)
    return red << 24 | green << 16 | blue << 8 | 0xFF


def psx_image_is_rotated(data: dict) -> bool:
    return bool(data['vram_x'] & PSX_VRAM_ROTATED)


class PsxClut(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'CLUT (color look-up table) of a PSX 4-bit or 8-bit image, attached to it (the image '
            '`next_offset` points to it). The colors are PSX 16-bit colors: bits 0-4 red, 5-9 green, 10-14 blue, 15 '
            'STP (semi-transparency). 0x0000 is transparent: the GPU does not draw such texels',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (IntegerBlock(length=1, value_validator=Eq(PSX_CLUT_ID)), {'description': 'Resource ID'})
        next_offset = (
            IntegerBlock(length=3),
            {'description': 'Offset to the next block attached to the image: 0 in every file, the CLUT is the last'},
        )
        num_colors = (
            IntegerBlock(
                length=2, programmatic_value=lambda ctx: len(ctx.data('colors')) // max(1, ctx.data('height'))
            ),
            {
                'usage': 'io,doc',
                'description': 'Amount of colors (the width of the CLUT in VRAM): 16 for 4-bit images, 256 for 8-bit '
                'ones (a few 8-bit images use only 16 or 64)',
            },
        )
        height = (IntegerBlock(length=2), {'description': 'Rows of colors: 1 in every file'})
        num_colors_2 = (
            IntegerBlock(
                length=2, programmatic_value=lambda ctx: len(ctx.data('colors')) // max(1, ctx.data('height'))
            ),
            {'usage': 'io,doc', 'description': 'Equals `num_colors`'},
        )
        unk = (IntegerBlock(length=2), {'is_unknown': True, 'description': '0 in every file'})
        vram_position = (
            Point2D(child=IntegerBlock(length=2)),
            {
                'description': 'VRAM position (0, 240 in every file). The game does not use it: the loader puts '
                'the CLUT in a free VRAM slot (FUN_80044794)'
            },
        )
        colors = (
            ArrayBlock(child=IntegerBlock(length=2), length=lambda ctx: ctx.data('num_colors') * ctx.data('height')),
            {'description': 'PSX 16-bit colors. Color models are described [here](eac_colors.md)'},
        )


def _clut_offset(ctx):
    # the CLUT follows the pixels and the padding
    if ctx.data('clut') is None:
        return 0
    return 16 + len(ctx.data('bitmap')) + len(ctx.data('pad') or b'')


def _pad_length(ctx):
    next_offset = ctx.data('next_offset')
    if not next_offset or ctx.read_bytes_remaining is None:
        return 0
    return max(0, min(next_offset - ctx.local_buffer_pos, ctx.read_bytes_remaining))


def _clut_criteria(ctx, **kwargs):
    if not isinstance(ctx, ReadContext) or ctx.read_bytes_remaining is None:
        return False
    if not ctx.data('next_offset') or ctx.data('next_offset') != ctx.local_buffer_pos or ctx.read_bytes_remaining < 16:
        return False
    head = ctx.buffer.read(1)
    ctx.buffer.seek(-len(head), SEEK_CUR)
    return len(head) == 1 and head[0] == PSX_CLUT_ID


class PsxImage(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An image of a PSX SHPP archive: 4-bit or 8-bit indexed with its CLUT, or 16-bit '
            'PSX colors. The rows are stored as uploaded to VRAM (whole 16-bit words, 4-bit pixels low nibble '
            'first). An image with the rotated flag in `vram_x` is stored rotated by 90 degrees: the game maps it so '
            'that it shows `height` texels wide and `width` texels high (stored left column, bottom to top = shown '
            'top row, left to right). The converter exports images as they are shown',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (
            EnumByteBlock(enum_names=PSX_IMAGE_IDS),
            {
                'description': 'Resource ID: its low 2 bits are the PSX texture color mode the loader uses (0 '
                '4-bit, 1 8-bit, 2 16-bit)'
            },
        )
        next_offset = (
            IntegerBlock(length=3, programmatic_value=_clut_offset),
            {
                'description': 'Offset from the start of the image to its CLUT (4-bit and 8-bit images), 0 when '
                'nothing is attached (16-bit images). Recomputed on save'
            },
        )
        width = (
            IntegerBlock(length=2),
            {'usage': 'io,doc', 'description': 'Width in pixels, as stored (shown height when rotated)'},
        )
        height = (
            IntegerBlock(length=2),
            {'usage': 'io,doc', 'description': 'Height in pixels, as stored (shown width when rotated)'},
        )
        pivot = (
            Point2D(child=IntegerBlock(length=2, is_signed=True)),
            {
                'description': 'At the place of the SHPI `pivot`. 0 in track textures; front end images and the '
                'rear-view mirror horizon `rhrz` have values. Not read by the horizon code, purpose not verified',
                'is_unknown': True,
            },
        )
        vram_x = (
            IntegerBlock(length=2),
            {
                'description': 'Bits 0-13: x of the image in VRAM in 16-bit words, where the tool that made the '
                'file packed it (the loader uploads it there, FUN_800b5628; the UVs are its offset in the 64-word '
                'texture page). Bit 14: the image is stored rotated (FUN_80044330 swaps its UVs)'
            },
        )
        vram_y = (
            IntegerBlock(length=2),
            {
                'description': 'Bits 0-13: y of the image in VRAM. Bit 14 is set together with the rotated bit of '
                '`vram_x`, the loader does not read it'
            },
        )
        bitmap = (
            BytesBlock(
                length=(
                    lambda ctx: psx_row_bytes(ctx.data('resource_id'), ctx.data('width')) * ctx.data('height'),
                    'height * ceil(width * bits_per_pixel / 16) * 2',
                )
            ),
            {
                'usage': 'io,doc',
                'description': 'Pixels, row by row, each row padded to whole 16-bit words: CLUT indexes (4-bit: '
                'the first pixel in the low nibble) or PSX 16-bit colors (bits 0-4 red, 5-9 green, 10-14 blue, 15 '
                'STP). 0x0000 colors are transparent. Color models are described [here](eac_colors.md)',
            },
        )
        pad = (
            BytesBlock(length=(_pad_length, 'up to `next_offset`')),
            {
                'description': 'Zeros aligning the CLUT to 4 bytes (images with an odd amount of 16-bit words)',
                'is_unknown': True,
            },
        )
        clut = (
            TrailingOptionalBlock(child=PsxClut(), criteria=(_clut_criteria, '`next_offset` points to a CLUT (0x23)')),
            {'description': 'The CLUT of a 4-bit or 8-bit image'},
        )

    def serializer_class(self):
        from serializers import PsxImageSerializer

        return PsxImageSerializer

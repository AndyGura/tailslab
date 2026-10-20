"""
PlayStation TNFS (SLUS-00204) files: the `CRCF` footer most of its files end with, and the horizon settings
`Z<track><time>.INF`.
"""

from io import SEEK_CUR
from typing import Dict, NamedTuple, Optional, Tuple

from library.context import ReadContext, WriteContext
from library.read_blocks import DeclarativeCompoundBlock, IntegerBlock, TrailingOptionalBlock, UTF8Block
from library.read_blocks.misc.value_validators import Eq

CRCF_FOOTER_LENGTH = 12


def _crc16_table():
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
        table.append(crc)
    return table


_CRC16_TABLE = _crc16_table()


def psx_crc16(data: bytes) -> int:
    """CRC of the `CRCF` footer (PSX `math_func_010` 0x800b4850): reflected CRC-16 (polynomial 0x8005, table at
    0x800d9c58) starting from 0xFBEA, without final xor"""
    crc = 0xFBEA
    for byte in data:
        crc = _CRC16_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc


class PsxCrcFooter(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Footer of most PSX TNFS files (PSH, INF, LGT, LGS, TRI, FAM, VB, VH, PFN...): the '
            'file loader FUN_8001577c checks it (callback 0x80015958: FUN_80015858 finds the footer, FUN_800158d4 '
            'compares the CRC) and loads the file again when it does not match. Inside a FAM (wwww) archive it '
            'follows the last item, in the bytes after it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('CRCF')), {'description': 'Resource ID'})
        length = (IntegerBlock(length=4, value_validator=Eq(CRCF_FOOTER_LENGTH)), {'description': 'Footer length'})
        crc = (
            IntegerBlock(length=4),
            {
                'description': 'CRC-16 of every byte of the file before the footer: reflected, polynomial 0x8005, '
                'initial value 0xFBEA, no final xor (PSX `math_func_010` 0x800b4850). Recomputed on save'
            },
        )


def crc_footer_at(ctx: ReadContext, offset: int) -> bool:
    """Whether a `CRCF` footer starts `offset` bytes after the buffer position and ends the read bytes"""
    if not isinstance(ctx, ReadContext) or ctx.read_bytes_remaining is None:
        return False
    if offset < 0 or ctx.read_bytes_remaining - offset != CRCF_FOOTER_LENGTH:
        return False
    position = ctx.buffer.tell()
    try:
        ctx.buffer.seek(offset, SEEK_CUR)
        return ctx.buffer.read(4) == b'CRCF'
    finally:
        ctx.buffer.seek(position)


def with_crc_footer(packed: bytes, footer: Optional[dict]) -> bytes:
    """The packed file bytes followed by the footer with the CRC of these bytes, when the file has a footer"""
    if footer is None:
        return packed
    return packed + PsxCrcFooter().pack({**footer, 'crc': psx_crc16(packed)})


class PsxHorizonSettings(NamedTuple):
    """Values of a PSX `.INF` horizon settings file, in file order (FUN_80034adc)"""

    vert_offset_near: int
    vert_offset_far: int
    z_offset_near: int
    z_offset_far: int
    height_near: int
    height_far: int
    radius_near: int
    radius_far: int
    colour_top: Tuple[int, int, int]
    colour_bottom: Tuple[int, int, int]
    dithering: int
    blend_ratio: int
    ring_y_offset: int
    ring_height: int
    mirror: int

    @property
    def screen_y_offset(self) -> int:
        """`ring_y_offset` in px of the 320x240 PSX screen: halved by the game (C division, towards 0)"""
        return int(self.ring_y_offset / 2)

    @property
    def screen_ring_height(self) -> int:
        """`ring_height` in px of the 320x240 PSX screen: halved by the game (C division, towards 0)"""
        return int(self.ring_height / 2)

    def as_dict(self) -> dict:
        return {
            **self._asdict(),
            'colour_top': list(self.colour_top),
            'colour_bottom': list(self.colour_bottom),
            'screen_y_offset': self.screen_y_offset,
            'screen_ring_height': self.screen_ring_height,
        }


def _atoi(text: str) -> int:
    digits = len(text) - len(text.lstrip('+-0123456789'))
    try:
        return int(text[:digits])
    except ValueError:
        return 0


def parse_psx_horizon_settings(text: str) -> Optional[PsxHorizonSettings]:
    """Settings of the text of a PSX `.INF` file: the numbers of the lines which are not `#` comments, in order. None
    when there are fewer than the 18 values the game reads before the mirror flag (0 when missing)"""
    values = [
        _atoi(token)
        for line in text.replace('\r', '\n').split('\n')
        if line.strip() and not line.strip().startswith('#')
        for token in line.split()
    ]
    if len(values) < 18:
        return None
    values += [0] * (19 - len(values))
    return PsxHorizonSettings(
        *values[:8],
        tuple(values[8:11]),
        tuple(values[11:14]),
        *values[14:19],
    )


def _text_length(ctx):
    remaining = ctx.read_bytes_remaining
    if crc_footer_at(ctx, remaining - CRCF_FOOTER_LENGTH):
        return remaining - CRCF_FOOTER_LENGTH
    return remaining


def _footer_criteria(ctx, **kwargs):
    return crc_footer_at(ctx, 0)


class TnfsPsxHorizonInfo(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Horizon settings of a PSX TNFS track at a time of day, `Z<track><A|B|C>.INF` '
            '(A morning, B midday, C evening), the counterpart of the PC `SIMDATA/MISC/<track>INFO`. Plain text: '
            '`#` comment lines, then one value per line (colors: 3 on a line). Read by FUN_80034adc in this order: 8 '
            'ring geometry values (vert offset near / far, z offset near / far, height near / far, radius near / '
            'far; the ring points are at radius far around the camera, at height vert offset far and z offset far, '
            '0 in every file; a horizon is drawn only when height far is not 0, 48 in every file), colour top and '
            'colour bottom (RGB 0..255), dithering flag (GPU dithering of the sky gradient), ratio of the blend, '
            'ring y offset, ring height (both halved by the game: px of the 320x240 screen; the PC uses them as px '
            'of 640x480), and a last value without a comment, the mirror flag (sectors 8..15 of the ring show '
            '`hrz7`..`hrz0` mirrored). Unlike the PC there is no ring type (the PSX always draws the ring) and no '
            'time of day values. See `library/utils/tnfs_psx_horizon_to_spherical.py` for how the game draws them',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        text = (
            UTF8Block(length=(_text_length, 'up to the CRCF footer')),
            {'description': 'The settings text'},
        )
        crc_footer = (
            TrailingOptionalBlock(child=PsxCrcFooter(), criteria=(_footer_criteria, 'the file ends with "CRCF"')),
            {'description': 'CRC footer'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        packed = super().write({**data, 'crc_footer': None}, ctx, name)
        return with_crc_footer(packed, data.get('crc_footer'))

    def serializer_class(self):
        from serializers import TnfsPsxHorizonInfoSerializer

        return TnfsPsxHorizonInfoSerializer

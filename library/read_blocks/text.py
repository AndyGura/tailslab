"""Text files a block parses and renders whole (NFS3 / NFS4 `carp.txt`, NFS HP2 INI files): `TextFileBlock` reads the
text and writes it again from the values, keeping the file as read in the `source_text` field; the blocks of its
fields only type the values for the GUI and the docs (`ParsedByParent`)."""

import math
import struct
from typing import Dict, Optional, Tuple

from library.read_blocks.compound import DeclarativeCompoundBlock
from library.read_blocks.strings import UTF8Block


class ParsedByParent:
    """Mixin of a block typing a value of a text file for the GUI and the docs: the text file block (`parsed_by`)
    reads and writes it, its own read / write / size raise"""

    parsed_by = 'its text file block'
    size_doc = '?'

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return self.size_doc

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError(f'{type(self).__name__} is read by {self.parsed_by}')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError(f'{type(self).__name__} is written by {self.parsed_by}')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError(f'{type(self).__name__} is written by {self.parsed_by}')


class TextFileBlock(DeclarativeCompoundBlock):
    """A text file read whole (the bytes it is read with, else the rest of the buffer) into values by `parse_text(raw)`
    and written by `render(data)` -> (bytes, {field name: offset of its text}). Its `Fields` hold a `source_text_field`"""

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return '?'

    def parse_text(self, raw: bytes) -> dict:
        raise NotImplementedError

    def render(self, data) -> Tuple[bytes, Dict[str, int]]:
        raise NotImplementedError

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        res = {}
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        remaining = self_ctx.read_bytes_remaining
        raw = ctx.buffer.read() if remaining is None else ctx.buffer.read(remaining)
        res.update(self.parse_text(raw))
        return res

    def write(self, data, ctx=None, name: str = '') -> bytes:
        return self.render(data)[0]

    def estimate_packed_size(self, data, ctx=None):
        return len(self.render(data)[0])

    def offset_to_child_when_packed(self, data, child_name: str, ctx=None):
        return self.render(data)[1].get(child_name, 0)


def source_text_field(kept: str):
    """The hidden `source_text` field of a `TextFileBlock`: the file as read, Latin-1. `kept`: what a write keeps"""
    return (
        UTF8Block(length=0),
        {
            'description': 'The file as read (bytes as Latin-1 characters). Writing puts the values over it: '
            f'{kept} stay as they are, a changed number is written in the style of the one it replaces',
            'usage': 'io',
        },
    )


def _f32(value: float) -> float:
    return struct.unpack('<f', struct.pack('<f', value))[0]


def f32_text(value: float, min_decimals: int, max_decimals: int = 12) -> Optional[str]:
    """`value` in fixed-point notation with the fewest decimals from `min_decimals` on that a game reads back as the
    same 32-bit float; None when none does (and for infinities and NaN)"""
    value = float(value)
    if not math.isfinite(value):
        return None
    target = _f32(value)
    for decimals in range(min_decimals, max_decimals + 1):
        text = f'{value:.{decimals}f}'
        if _f32(float(text)) == target:
            return text
    return None

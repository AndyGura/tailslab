import struct
from typing import Iterable, List, Optional, Tuple

from library.exceptions import EndOfBufferException

# `struct` format characters of integers by (length, is_signed)
INTEGER_STRUCT_CODES = {
    (1, False): 'B',
    (1, True): 'b',
    (2, False): 'H',
    (2, True): 'h',
    (4, False): 'I',
    (4, True): 'i',
    (8, False): 'Q',
    (8, True): 'q',
}


def struct_byte_order(byte_order: str) -> str:
    return '<' if byte_order == 'little' else '>'


def join_struct_formats(blocks: Iterable) -> Optional[Tuple[str, str]]:
    """`struct_format` of blocks packed one after another, None when one has none or their byte orders differ"""
    byte_order, codes = '', ''
    for block in blocks:
        block_format = block.struct_format
        if block_format is None:
            return None
        if block_format[0]:
            if byte_order and byte_order != block_format[0]:
                return None
            byte_order = block_format[0]
        codes += block_format[1]
    return byte_order, codes


class StructRecord:
    """Values of a block with a `struct_format` (a record of fixed-size number leaves: nested records and arrays of a
    fixed length of them included) read and written with one precompiled `struct.Struct`, without a context per field.
    Raises on anything it can't do the way the field by field read / write does (end of buffer, a value out of range):
    callers then fall back to that read / write, which raises the error with its context"""

    def __init__(self, block):
        byte_order, codes = block.struct_format
        self.block = block
        self.byte_order = byte_order or '<'
        self.codes = codes
        self.struct = struct.Struct(self.byte_order + codes)
        self.size = self.struct.size
        # the value is the one unpacked value as it is (plain numbers): arrays of them are unpacked in one go
        self.is_raw_value = block.struct_raw

    def read(self, buffer):
        raw = buffer.read(self.size)
        if len(raw) < self.size:
            raise EndOfBufferException()
        return self.block.from_struct(self.struct.unpack(raw), 0)[0]

    def read_many(self, buffer, count: int) -> List:
        raw = buffer.read(self.size * count)
        if len(raw) < self.size * count:
            raise EndOfBufferException()
        if self.is_raw_value:
            return list(struct.unpack(f'{self.byte_order}{count}{self.codes}', raw))
        from_struct = self.block.from_struct
        return [from_struct(values, 0)[0] for values in self.struct.iter_unpack(raw)]

    def write(self, data) -> bytes:
        values = []
        self.block.to_struct(data, values)
        return self.struct.pack(*values)

    def write_many(self, items) -> bytes:
        if self.is_raw_value:
            return struct.pack(f'{self.byte_order}{len(items)}{self.codes}', *items)
        to_struct, pack = self.block.to_struct, self.struct.pack
        parts = []
        for item in items:
            values = []
            to_struct(item, values)
            parts.append(pack(*values))
        return b''.join(parts)

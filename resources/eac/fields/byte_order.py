from copy import deepcopy

from library.read_blocks import (
    ArrayBlock,
    CompoundBlock,
    DataBlock,
    DecimalBlock,
    DelegateBlock,
    IntegerBlock,
    OptionalBlock,
)


def big_endian_copy(block: DataBlock) -> DataBlock:
    """A deep copy of a block with every integer block in it (fixed point numbers, bit fields, angles...) read and
    written big-endian: the layout of a little-endian PC structure as a big-endian console (3DO, Sega Saturn) stores
    it. Byte arrays and strings are unchanged"""
    block = deepcopy(block)
    stack = [block]
    while stack:
        current = stack.pop()
        if isinstance(current, (IntegerBlock, DecimalBlock)):
            current.byte_order = 'big'
        elif isinstance(current, ArrayBlock):
            stack.append(current.child)
        elif isinstance(current, CompoundBlock):
            stack.extend(child for _, child in current.field_blocks)
        elif isinstance(current, DelegateBlock):
            stack.extend(current.possible_blocks)
        elif isinstance(current, OptionalBlock):
            stack.append(current.child)
    return block
